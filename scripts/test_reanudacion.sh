#!/usr/bin/env bash
#
# test_reanudacion.sh — ¿sobreviven las tandas a un apagón? (ADR-0008)
#
# Simula un corte con `kill -9` a mitad de tanda, deja además una última línea
# CORTADA en el CSV (lo que deja un apagón en pleno write) y comprueba que al
# reanudar:
#   1. run_experiment.py --resume da EXACTAMENTE las mismas corridas que una
#      tanda sin cortes (presupuesto de conflictos: resultado determinista);
#   2. run_ab_interleaved.py --resume completa todas las parejas, sin
#      duplicados ni filas rotas;
#   3. el orquestador, matado con -9 en pleno paso, retoma el paso y lo marca
#      hecho al relanzarlo; un segundo orquestador no arranca mientras hay uno.
#
# Uso: ./scripts/test_reanudacion.sh    (usa bench/smoke y el binario de build/)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
BIN="${LABESAT_KISSAT:-solver/kissat/build/kissat}"
T="$(mktemp -d "${TMPDIR:-/tmp}/test-reanudacion.XXXXXX")"
trap 'rm -rf "$T"' EXIT
ok()   { echo "  OK    $*"; }
fallo(){ echo "  FALLO $*"; exit 1; }
filas(){ python3 -c 'import sys; sys.path.insert(0,"scripts")
from checkpoint import filas_completas; print(len(filas_completas(sys.argv[1])))' "$1"; }
# esperar_filas CSV N PID: hasta que CSV tenga >= N filas o el proceso acabe
esperar_filas() { until [ "$(filas "$1")" -ge "$2" ] || ! kill -0 "$3" 2>/dev/null; do sleep 0.2; done; }
cortar() { printf 'linea,cortada,por,un,apag' >> "$1"; }   # sin salto de línea

echo "== 1. checkpoint.filas_completas descarta la línea cortada"
printf 'a,b\n1,2\n3,4\n5' > "$T/c.csv"
[ "$(filas "$T/c.csv")" = 2 ] && ok "2 filas íntegras de 3" || fallo "filas_completas"

echo "== 2. run_experiment.py --resume"
args=(--solver "$BIN" --bench bench/smoke --conflicts 20000 --seeds 1,2 --label t)
python3 scripts/run_experiment.py "${args[@]}" --out "$T/full.csv" > /dev/null
python3 scripts/run_experiment.py "${args[@]}" --out "$T/cut.csv" > /dev/null &
pid=$!; esperar_filas "$T/cut.csv" 5 $pid; kill -9 $pid 2>/dev/null || true; wait $pid 2>/dev/null || true
cortar "$T/cut.csv"
antes=$(filas "$T/cut.csv")
python3 scripts/run_experiment.py "${args[@]}" --out "$T/cut.csv" --resume > /dev/null
clave() { python3 - "$1" <<'PY'
import csv, sys
filas = list(csv.DictReader(open(sys.argv[1])))
assert filas, "CSV vacío"
print("\n".join(sorted(",".join((r["instance"], r["seed"], r["status"], r["conflicts"])) for r in filas)))
PY
}
k_full=$(clave "$T/full.csv") || fallo "no se pudo leer full.csv"
k_cut=$(clave "$T/cut.csv") || fallo "no se pudo leer cut.csv"
if [ -n "$k_full" ] && [ "$k_full" = "$k_cut" ]; then
  ok "cortada a las $antes corridas, reanudada: mismas $(filas "$T/full.csv") corridas que sin corte"
else fallo "run_experiment: la tanda reanudada difiere"; fi
python3 scripts/run_experiment.py "${args[@]}" --opts="--seed=9" --out "$T/cut.csv" --resume > /dev/null 2>&1 \
  && fallo "--resume aceptó opciones distintas" || ok "--resume rechaza opciones distintas de la tanda original"

echo "== 3. run_ab_interleaved.py --resume"
ab=(--solver "$BIN" --bench bench/smoke --timeout 20 --seeds 1 --out-a "$T/A.csv" --out-b "$T/B.csv")
python3 scripts/run_ab_interleaved.py "${ab[@]}" > /dev/null &
pid=$!; esperar_filas "$T/B.csv" 3 $pid; kill -9 $pid 2>/dev/null || true; wait $pid 2>/dev/null || true
cortar "$T/A.csv"
python3 scripts/run_ab_interleaved.py "${ab[@]}" --resume > /dev/null
n=$(find bench/smoke -name '*.cnf*' | wc -l)
dup=$(python3 -c 'import csv,sys; r=[(x["instance"],x["seed"]) for x in csv.DictReader(open(sys.argv[1]))]; print(len(r)-len(set(r)))' "$T/A.csv")
[ "$(filas "$T/A.csv")" = "$n" ] && [ "$(filas "$T/B.csv")" = "$n" ] && [ "$dup" = 0 ] \
  && ok "$n parejas completas, sin duplicados" || fallo "A/B reanudado: $(filas "$T/A.csv")/$(filas "$T/B.csv") de $n, $dup duplicadas"

echo "== 4. orquestador: kill -9 en pleno paso y relanzar"
cat > "$T/cola.toml" <<EOF
[[paso]]
id = "uno"
descripcion = "run_experiment sobre smoke"
hecho = "[ \$(filas $T/o.csv) -ge 20 ]"
comando = "python3 scripts/run_experiment.py ${args[*]} --out $T/o.csv --resume"
[[paso]]
id = "dos"
descripcion = "paso trivial"
hecho = "[ -f $T/dos.ok ]"
comando = "touch $T/dos.ok"
EOF
orq=(python3 scripts/orquestador.py --cola "$T/cola.toml" --estado-dir "$T/estado")
"${orq[@]}" ejecutar > "$T/orq1.log" 2>&1 &
pid=$!; esperar_filas "$T/o.csv" 6 $pid
"${orq[@]}" ejecutar > "$T/orq-doble.log" 2>&1 && fallo "arrancó un segundo orquestador" \
  || ok "un segundo orquestador no arranca (cerrojo)"
pkill -9 -P $pid 2>/dev/null || true; kill -9 $pid 2>/dev/null || true; wait $pid 2>/dev/null || true
pkill -9 -f "$T/o.csv" 2>/dev/null || true
"${orq[@]}" ejecutar > "$T/orq2.log" 2>&1
[ -f "$T/estado/uno.hecho" ] && [ -f "$T/estado/dos.hecho" ] && [ "$(filas "$T/o.csv")" = 20 ] \
  && ok "relanzado: los dos pasos hechos, 20 corridas" || { cat "$T/orq2.log"; fallo "orquestador"; }
"${orq[@]}" estado | grep -q "uno .*hecho" && ok "'estado' informa del progreso" || fallo "estado"

echo ""
echo "test_reanudacion: todo correcto"
