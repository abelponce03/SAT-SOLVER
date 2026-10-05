#!/usr/bin/env bash
# test_opciones_m.sh — opciones de búsqueda de research/12 (M5, M8, M9, M10 y
# X2), todas APAGADAS por defecto (CLAUDE.md §5).  Comprueba, con un Kissat
# compilado desde el árbol:
#
#   1. Valen 0 por defecto (decayramp, eliminatefix, probeiterate,
#      vivifywatchfix y, si hay X1, gaussphase).
#   2. Escribir la opción con su valor por defecto no cambia la búsqueda:
#      contadores de --statistics idénticos a no escribirla.
#   3. Con cada opción ENCENDIDA, todas las respuestas son correctas:
#      los modelos los acepta verify_model.py contra la CNF y las pruebas
#      DRAT de los UNSAT, los verificadores de tools/ (drat-trim y los dos
#      dsr-trim, los que haya; scripts/get_tools.sh).
#   4. Informa (no falla) de si cada opción cambia la trayectoria en alguna
#      instancia de la muestra: una opción que no actúa nunca no se puede
#      medir, pero en instancias pequeñas es normal que algunas no actúen.
#
# Instancias: bench/smoke (versionado), 3-SAT aleatorio generado y familias
# de paridad de gen_paridad.py (satisfacibles e insatisfacibles), donde
# actúan X1 y X2.
#
# Uso: [TOOLS=dir] ./scripts/test_opciones_m.sh [kissat]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
K="${1:-$ROOT/solver/kissat/build-m/kissat}"
if [ ! -x "$K" ]; then
    "$ROOT/scripts/build.sh" --dir=build-m >/dev/null
fi
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
fail=0
bad() { echo "FALLO $*"; fail=1; }
TOOLS="${TOOLS:-$ROOT/tools}"
CHECKERS=()
for c in drat-trim dsr-trim dsr-trim-sc2026; do
    if [ -x "$TOOLS/$c" ]; then CHECKERS+=("$TOOLS/$c"); fi
done
[ ${#CHECKERS[@]} -gt 0 ] || echo "AVISO sin verificadores en tools/ (scripts/get_tools.sh): solo se comprueban los modelos"
# drat-trim escribe un retorno de carro delante del veredicto ("\rs VERIFIED").
verified() { "$1" "$2" "$3" > "$TMP/check.out" 2>&1 || true; grep -aqE $'(^|\r)s VERIFIED' "$TMP/check.out"; }
# Contadores deterministas de --statistics (sin tiempos ni memoria).
cuenta() { grep -E '^c [a-z_]+: +[0-9]+' | grep -vE 'seconds|time|MB|bytes' | awk '{print $2, $3}'; }

"$K" --range > "$TMP/range"
OPCIONES=(decayramp=200 eliminatefix=1 probeiterate=1 vivifywatchfix=1)
grep -q "^gaussphase " "$TMP/range" && OPCIONES+=(gaussphase=1)

# 1. Apagadas por defecto.
for o in "${OPCIONES[@]}"; do
    n="${o%%=*}"
    if grep -qE "^$n [0-9]+ 0 " "$TMP/range"; then echo "OK    $n vale 0 por defecto"
    else bad "$n no vale 0 por defecto: $(grep "^$n " "$TMP/range")"; fi
done

# Muestra.
INST=()
for f in "$ROOT"/bench/smoke/*.cnf; do INST+=("$f"); done
python3 "$ROOT/scripts/gen_benchmarks.py" --out "$TMP/rand" --rand-vars 200,250 \
    --seeds 1,2 --php 7 > /dev/null
for f in "$TMP"/rand/*.cnf; do INST+=("$f"); done
i=0
for spec in "tseitin-malla 6 6" "lights-out 5" "tseitin-regular 40 3"; do
    for v in "" "--sat"; do
        i=$((i + 1)); f="$TMP/par$i.cnf"
        python3 "$ROOT/scripts/gen_paridad.py" $spec --seed 3 $v > "$f"; INST+=("$f")
    done
done
# Paridad satisfacible más una cláusula que la solución de Gauss incumple:
# X1s la rechaza y ahí X2 pone sus fases (como en test_gauss.sh, paso 5).
# La cláusula es la negación de σ en sus 3 primeras variables (no es XOR).
python3 "$ROOT/scripts/gen_paridad.py" tseitin-malla 12 12 --seed 3 --sat > "$TMP/g.cnf"
"$K" --gausslucky=1 --conflicts=0 "$TMP/g.cnf" > "$TMP/g.out" 2>&1 || true
python3 - "$TMP/g.cnf" "$TMP/g.out" > "$TMP/x2.cnf" <<'PY'
import sys
lines = open(sys.argv[1]).read().splitlines()
cls = [l for l in lines if l and l[0] not in "cp"]
n = int(next(l for l in lines if l.startswith("p")).split()[2])
vals = [int(t) for l in open(sys.argv[2]) if l.startswith("v ") for t in l[2:].split()]
print(f"p cnf {n} {len(cls) + 1}")
print("\n".join(cls))
print(" ".join(str(-x) for x in vals[:3]), 0)
PY
INST+=("$TMP/x2.cnf")
echo "      muestra: ${#INST[@]} instancias"

# 2. Escribir el valor por defecto no cambia nada.
for f in "${INST[@]}"; do
    "$K" --seed=1 --conflicts=3000 --statistics "$f" 2>/dev/null | cuenta > "$TMP/a" || true
    "$K" --seed=1 --conflicts=3000 --statistics --decayramp=0 --eliminatefix=0 \
        --probeiterate=0 --vivifywatchfix=0 "$f" 2>/dev/null | cuenta > "$TMP/b" || true
    cmp -s "$TMP/a" "$TMP/b" || bad "$(basename "$f"): con los valores por defecto escritos la búsqueda cambia"
done
echo "OK    escribir los valores por defecto no cambia la búsqueda"

# 3 y 4. Cada opción encendida: respuestas correctas; ¿actúa?
for o in "${OPCIONES[@]}"; do
    actua=0; sat=0; unsat=0
    for f in "${INST[@]}"; do
        code=0
        "$K" --seed=1 --time=20 "--$o" "$f" "$TMP/p.drat" > "$TMP/o.out" 2>&1 || code=$?
        if [ "$code" = 10 ]; then
            python3 "$ROOT/scripts/verify_model.py" --model "$TMP/o.out" "$f" > /dev/null 2>&1 ||
                bad "--$o $(basename "$f"): modelo inválido"
            sat=$((sat + 1))
        elif [ "$code" = 20 ]; then
            for c in "${CHECKERS[@]}"; do
                verified "$c" "$f" "$TMP/p.drat" || bad "--$o $(basename "$f"): $(basename "$c") rechaza la prueba"
            done
            unsat=$((unsat + 1))
        elif [ "$code" != 0 ]; then
            bad "--$o $(basename "$f"): código $code"
        fi
        "$K" --seed=1 --conflicts=3000 --statistics "$f" 2>/dev/null | cuenta > "$TMP/a" || true
        "$K" --seed=1 --conflicts=3000 --statistics "--$o" "$f" 2>/dev/null | cuenta > "$TMP/b" || true
        cmp -s "$TMP/a" "$TMP/b" || actua=$((actua + 1))
    done
    echo "OK    --$o: $sat SAT con modelo verificado, $unsat UNSAT con prueba verificada; cambia la trayectoria en $actua de ${#INST[@]}"
done

# X2: el mensaje dice cuántas fases puso, y la respuesta es correcta.
if grep -q "^gaussphase " "$TMP/range"; then
    "$K" --gaussphase=1 --verbose=1 --conflicts=0 "$TMP/x2.cnf" > "$TMP/x2.out" 2>&1 || true
    if grep -q "falsifies a clause" "$TMP/x2.out" && grep -qE "gauss: [1-9][0-9]* saved phases" "$TMP/x2.out"; then
        echo "OK    X2: X1s rechazada y la solución de Gauss da las fases ($(grep -oE '[0-9]+ saved phases' "$TMP/x2.out"))"
    else bad "X2 no puso fases en la paridad con una cláusula ajena"; fi
fi

if [ $fail = 0 ]; then echo "test_opciones_m: todo correcto"; else echo "test_opciones_m: HAY FALLOS"; fi
exit $fail
