#!/usr/bin/env bash
#
# setup_benchmarks.sh - descarga suites de SATLIB, las normaliza y arma el
# banco de nivel 1 (`bench/satlib`): rapido, offline tras la primera descarga.
#
# AVISO DE ALCANCE: SATLIB es academico/antiguo y NO representa el regimen de la
# Main Track (instancias de aplicacion de cientos de miles de variables). Sirve
# para validar el harness y detectar regresiones groseras, NO para concluir nada
# sobre PAR-2 de competicion. Para eso esta `scripts/build_dev_set.py`, que arma
# bench/dev y bench/test con instancias reales de la Global Benchmark Database.
#
# Idempotente: si ya descargó algo, no vuelve a bajarlo. Reconstruye dev/.
#
# Resultado: bench/satlib/  con instancias reales (SATLIB) +
# crafted duras generadas (pigeonhole), etiquetadas por estado esperado en el
# nombre cuando se conoce. Ninguna de estas requiere red para re-ejecutarse una
# vez descargadas.
#
# Familias incluidas (todas estándar y libremente redistribuibles para
# investigación):
#   - uf250-1065 / uuf250-1065 : random 3-SAT en el umbral (SAT / UNSAT)
#   - aim                       : instancias crafted (SAT y UNSAT)
#   - parity (par16/par32)      : aprendizaje de paridad (SAT; par32 es duro)
#   - pigeonhole PHP            : UNSAT, dificultad exponencial (generadas)
#
# NO se incluyen dubois/pret: usan un formato clausula-por-linea ambiguo que
# rompe la normalizacion estricta (cambiaria la semantica).
#
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
BENCH="$HERE/../bench"
DL="$BENCH/downloaded"
DEV="$BENCH/satlib"
NORM="python3 $HERE/normalize_cnf.py"
GEN="python3 $HERE/gen_benchmarks.py"
BASE_URL="https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT"

mkdir -p "$DL" "$DEV"
rm -f "$DEV"/*.cnf

fetch() {  # fetch <url> <tarball_name> <extract_subdir>
    local url="$1" tgz="$2" sub="$3"
    if [ ! -f "$DL/$tgz" ]; then
        echo "  bajando $tgz ..."
        curl -sS --fail --max-time 120 -o "$DL/$tgz" "$url" || { echo "  FALLO $tgz"; return 1; }
    fi
    mkdir -p "$DL/$sub"
    tar xzf "$DL/$tgz" -C "$DL/$sub" 2>/dev/null || true
}

echo "== 1. Descargando suites SATLIB (solo si faltan)"
fetch "$BASE_URL/RND3SAT/uf250-1065.tar.gz"  uf250-1065.tar.gz  uf250-1065
fetch "$BASE_URL/RND3SAT/uuf250-1065.tar.gz" uuf250-1065.tar.gz uuf250-1065
fetch "$BASE_URL/DIMACS/AIM/aim.tar.gz"       aim.tar.gz         aim
fetch "$BASE_URL/DIMACS/PARITY/parity.tar.gz" parity.tar.gz      parity

echo "== 2. Seleccionando y normalizando instancias hacia dev/"

# helper: copia normalizada con prefijo de estado esperado
take() {  # take <src_cnf> <dest_basename>
    $NORM "$1" "$DEV/$2" >/dev/null 2>&1 || cp "$1" "$DEV/$2"
}

# 8 random SAT + 8 random UNSAT (rápidas, ~0.5s; ancla de "resolver ya")
i=0; for f in $(find "$DL/uf250-1065"  -name '*.cnf' | sort | head -8);  do i=$((i+1)); take "$f" "$(printf 'uf250_sat_%02d.cnf' $i)"; done
i=0; for f in $(find "$DL/uuf250-1065" -name '*.cnf' | sort | head -8);  do i=$((i+1)); take "$f" "$(printf 'uuf250_unsat_%02d.cnf' $i)"; done

# aim crafted: unas SAT y unas UNSAT (200 vars, algo más duras)
i=0; for f in $(find "$DL/aim" -name '*aim-200*yes*.cnf' | sort | head -4); do i=$((i+1)); take "$f" "$(printf 'aim200_sat_%02d.cnf' $i)"; done
i=0; for f in $(find "$DL/aim" -name '*aim-200*no*.cnf'  | sort | head -4); do i=$((i+1)); take "$f" "$(printf 'aim200_unsat_%02d.cnf' $i)"; done

# parity: par16 (fácil, SAT) y par32 (duro, suele agotar el timeout)
for f in $(find "$DL/parity" -name 'par16-*.cnf' ! -name '*-c.cnf' | sort | head -3); do take "$f" "par16_$(basename $f)"; done
for f in $(find "$DL/parity" -name 'par32-*.cnf' ! -name '*-c.cnf' | sort | head -2); do take "$f" "par32_$(basename $f)"; done

echo "== 3. Generando pigeonhole crafted (UNSAT, dificultad escalable)"
TMP_PHP="$(mktemp -d)"
$GEN --out "$TMP_PHP" --php 8,9,10,11,12 --rand-vars "" >/dev/null
for f in "$TMP_PHP"/php_*.cnf; do cp "$f" "$DEV/$(basename $f)"; done
rm -rf "$TMP_PHP"

n=$(find "$DEV" -name '*.cnf' | wc -l)
echo ""
echo "== Listo: $n instancias en $DEV"
echo "   Corre el baseline con:"
echo "   python3 scripts/run_experiment.py --solver solver/kissat/build/kissat \\"
echo "        --bench bench/satlib --out results/satlib.csv --timeout 120 --seeds 1,2,3 \\"
echo "        --label kissat-4.0.4-vanilla"
