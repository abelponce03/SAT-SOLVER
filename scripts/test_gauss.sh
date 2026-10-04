#!/usr/bin/env bash
# test_gauss.sh — X1 (research/09): refutación de sistemas XOR por Gauss con
# prueba DRAT.  Comprueba, con Kissat compilado con 'configure --gauss':
#
#   1. Refuta familias de paridad UNSAT (Tseitin en malla y en grafo regular,
#      lights-out irresoluble, paridad en dos órdenes) y los verificadores
#      disponibles (dsr-trim actual, dsr-trim de SC2026, drat-trim) aceptan la
#      prueba.  Sin borrados: el de SC2026 falla con ellos (research/09 §4.3).
#   2. No refuta nunca la variante SATISFACIBLE de esas familias, y en ellas la
#      búsqueda es la misma con --gauss=1 que con --gauss=0 (81 contadores de
#      --statistics idénticos): clase E con salida temprana.
#   3. Por componentes conexas, refuta un subsistema pequeño inconsistente
#      aunque el sistema entero no quepa en el tope de memoria.
#   4. X1 está activa por defecto (EXP-019 y EXP-021) y --gauss=0 la apaga:
#      sin ningún mensaje de X1.
#   5. X1s (research/09 §3.5, --gausslucky=1): en las variantes satisfacibles
#      la solución de Gauss es un modelo; 'lucky' la asigna, sin conflictos,
#      y verify_model.py acepta el modelo contra la CNF.  Con una cláusula
#      ajena que la solución no cumple, X1s se rechaza y la búsqueda es la
#      misma que con --gausslucky=0.
#
# Uso: [TOOLS=dir] ./scripts/test_gauss.sh [kissat-con-gauss]
# Sin argumento compila solver/kissat/build-gauss/ si no existe ('build.sh'
# compila con 'configure --gauss' por defecto).  TOOLS es el
# directorio de los verificadores (por defecto tools/, scripts/get_tools.sh).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
K="${1:-$ROOT/solver/kissat/build-gauss/kissat}"
if [ ! -x "$K" ]; then
    "$ROOT/scripts/build.sh" --dir=build-gauss --gauss >/dev/null
fi
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
"$K" --range > "$TMP/range" 2>&1 || true
grep -q "^gauss " "$TMP/range" || { echo "FALLO $K no tiene --gauss (¿configure --gauss?)"; exit 1; }
fail=0
bad() { echo "FALLO $*"; fail=1; }
# Guardar la salida antes de buscar en ella (ver test_symmetry.sh: SIGPIPE).
# drat-trim escribe un retorno de carro delante del veredicto ("\rs VERIFIED").
verified() { "$1" "$2" "$3" > "$TMP/check.out" 2>&1 || true; grep -aqE $'(^|\r)s VERIFIED' "$TMP/check.out"; }
TOOLS="${TOOLS:-$ROOT/tools}"
CHECKERS=()
for c in dsr-trim dsr-trim-sc2026 drat-trim; do
    if [ -x "$TOOLS/$c" ]; then CHECKERS+=("$TOOLS/$c"); fi
done
[ ${#CHECKERS[@]} -gt 0 ] || echo "AVISO sin verificadores en tools/ (scripts/get_tools.sh): solo se comprueba la respuesta"

FAMILIAS=("tseitin-malla 6 6" "tseitin-regular 40 3" "lights-out 5" "dos-ordenes 20")

# 1. Refutación con prueba verificada.
for spec in "${FAMILIAS[@]}"; do
    f="$TMP/u.cnf"
    python3 "$ROOT/scripts/gen_paridad.py" $spec --seed 3 > "$f"
    code=0; "$K" --gauss=1 "$f" "$TMP/u.proof" > "$TMP/u.out" 2>&1 || code=$?
    if [ "$code" != 20 ] || ! grep -q "gauss: refuted" "$TMP/u.out"; then
        bad "$spec: X1 no refutó (código $code)"; continue
    fi
    ok=1
    for c in "${CHECKERS[@]}"; do
        verified "$c" "$f" "$TMP/u.proof" || { bad "$spec: $(basename "$c") no verificó la prueba"; ok=0; }
    done
    if [ $ok = 1 ]; then
        echo "OK    $spec: UNSAT por X1, prueba verificada por ${#CHECKERS[@]} verificadores"
    fi
done

# 2. Variantes satisfacibles: ni refuta ni cambia la búsqueda.
# Fuera también 'allocated_*' (solo en builds con métricas, configure -g): es
# el pico de memoria, que X1 sube con sus matrices; no es la búsqueda.
cuenta() { awk '/^c [a-z_0-9]+:[ ]+[0-9]+/ { n=$2; if (n ~ /time|resident|memory|real|process|second|allocated/) next; print n, $3 } /^s / {print}'; }
for spec in "${FAMILIAS[@]}"; do
    f="$TMP/s.cnf"
    python3 "$ROOT/scripts/gen_paridad.py" $spec --seed 3 --sat > "$f"
    "$K" --gauss=1 --verbose=1 "$f" > "$TMP/s1.out" 2>&1 || true
    if grep -q "gauss: refuted" "$TMP/s1.out" || ! grep -q "^s SATISFIABLE" "$TMP/s1.out"; then
        bad "$spec --sat: X1 refutó una instancia satisfacible"; continue
    fi
    # Kissat sale con 10 o 20: a fichero con '|| true', y después se cuenta.
    "$K" --gauss=0 --seed=1 --conflicts=2000 --statistics "$f" > "$TMP/a.out" 2>&1 || true
    "$K" --gauss=1 --seed=1 --conflicts=2000 --statistics "$f" > "$TMP/b.out" 2>&1 || true
    cuenta < "$TMP/a.out" > "$TMP/a"
    cuenta < "$TMP/b.out" > "$TMP/b"
    if cmp -s "$TMP/a" "$TMP/b"; then
        echo "OK    $spec --sat: SAT, sin refutar, contadores idénticos con y sin X1 ($(wc -l < "$TMP/a"))"
    else bad "$spec --sat: la búsqueda cambia con --gauss=1"; fi
done

# 3. Componentes (research/09, Lema 6): un sistema grande y consistente que
#    no cabe en el tope de memoria (Tseitin 40×40 satisfacible, ~7,8 Mbit) y,
#    sin variables en común, uno pequeño e inconsistente (Tseitin 4×4).  Con
#    --gaussbits=1 (1 Mbit), tratar el sistema entero lo saltaría; por
#    componentes, X1 refuta el pequeño, con prueba verificada.
python3 "$ROOT/scripts/gen_paridad.py" tseitin-malla 40 40 --seed 3 --sat > "$TMP/g.cnf"
python3 "$ROOT/scripts/gen_paridad.py" tseitin-malla 4 4 --seed 3 > "$TMP/p.cnf"
python3 - "$TMP/g.cnf" "$TMP/p.cnf" > "$TMP/c.cnf" <<'PY'
import sys
def leer(f):
    n, cls = 0, []
    for l in open(f):
        if l.startswith("p"): n = int(l.split()[2])
        elif l[0] not in "c\n": cls.append([int(x) for x in l.split()[:-1]])
    return n, cls
n1, c1 = leer(sys.argv[1]); n2, c2 = leer(sys.argv[2])
c2 = [[(abs(x) + n1) * (1 if x > 0 else -1) for x in c] for c in c2]
print(f"p cnf {n1 + n2} {len(c1) + len(c2)}")
for c in c1 + c2: print(" ".join(map(str, c)), 0)
PY
code=0; "$K" --gauss=1 --gaussbits=1 "$TMP/c.cnf" "$TMP/c.proof" > "$TMP/c.out" 2>&1 || code=$?
if [ "$code" = 20 ] && grep -q "gauss: refuted" "$TMP/c.out"; then
    ok=1
    for c in "${CHECKERS[@]}"; do
        verified "$c" "$TMP/c.cnf" "$TMP/c.proof" || { bad "componentes: $(basename "$c") no verificó la prueba"; ok=0; }
    done
    if [ $ok = 1 ]; then echo "OK    componentes: refuta la pequeña aunque el sistema entero no quepa (prueba verificada)"; fi
else bad "componentes: X1 no refutó con --gaussbits=1 (código $code)"; fi

# 4. Activa por defecto; --gauss=0 la apaga.
python3 "$ROOT/scripts/gen_paridad.py" lights-out 5 --seed 3 > "$TMP/d.cnf"
code=0; "$K" "$TMP/d.cnf" > "$TMP/d.out" 2>&1 || code=$?
if [ "$code" = 20 ] && grep -q "gauss: refuted" "$TMP/d.out"; then echo "OK    sin opciones, X1 se ejecuta y refuta"
else bad "X1 no se ejecuta por defecto (código $code)"; fi
"$K" --gauss=0 --verbose=1 "$TMP/d.cnf" > "$TMP/d.out" 2>&1 || true
if grep -q "gauss:" "$TMP/d.out"; then bad "X1 se ejecuta con --gauss=0"
else echo "OK    con --gauss=0, X1 no se ejecuta"; fi

# 5. X1s.
for spec in "${FAMILIAS[@]}"; do
    f="$TMP/s.cnf"
    python3 "$ROOT/scripts/gen_paridad.py" $spec --seed 3 --sat > "$f"
    "$K" --gausslucky=1 --statistics "$f" > "$TMP/l.out" 2>&1 || true
    if grep -q "lucky Gauss solution" "$TMP/l.out" && grep -q "^s SATISFIABLE" "$TMP/l.out" &&
       grep -qE "^c conflicts:[[:space:]]+0 " "$TMP/l.out" &&
       python3 "$ROOT/scripts/verify_model.py" --model "$TMP/l.out" "$f" > /dev/null 2>&1; then
        echo "OK    $spec --sat: X1s asigna la solución de Gauss, 0 conflictos, modelo verificado"
    else bad "$spec --sat: X1s no resolvió con un modelo válido"; fi
done
# Rechazo: una cláusula nueva que la solución de Gauss (libres a 1) incumple
# no es XOR; X1s calcula σ, la descarta y no toca el solver.
python3 "$ROOT/scripts/gen_paridad.py" lights-out 5 --seed 3 --sat > "$TMP/s.cnf"
"$K" --gausslucky=1 --verbose=1 --conflicts=0 "$TMP/s.cnf" > "$TMP/r.out" 2>&1 || true
modelo=$(python3 - "$TMP/r.out" <<'PY'
import re, sys
# La solución de Gauss sale en la línea «v» (X1s la asignó): su negación
# sobre las 3 primeras variables es una cláusula que σ incumple.
vals = [int(t) for l in open(sys.argv[1]) if l.startswith("v ") for t in l[2:].split()]
print(" ".join(str(-x) for x in vals[:3]))
PY
)
python3 - "$TMP/s.cnf" "$modelo" > "$TMP/x.cnf" <<'PY'
import sys
lines = open(sys.argv[1]).read().splitlines()
cls = [l for l in lines if l and l[0] not in "cp"]
n = int(next(l for l in lines if l.startswith("p")).split()[2])
print(f"p cnf {n} {len(cls) + 1}")
print("\n".join(cls))
print(sys.argv[2], 0)
PY
"$K" --gausslucky=1 --verbose=1 --conflicts=0 "$TMP/x.cnf" > "$TMP/x.out" 2>&1 || true
"$K" --gausslucky=0 --seed=1 --conflicts=2000 --statistics "$TMP/x.cnf" > "$TMP/a.out" 2>&1 || true
"$K" --gausslucky=1 --seed=1 --conflicts=2000 --statistics "$TMP/x.cnf" > "$TMP/b.out" 2>&1 || true
cuenta < "$TMP/a.out" > "$TMP/a"
cuenta < "$TMP/b.out" > "$TMP/b"
if grep -q "falsifies a clause" "$TMP/x.out" && ! grep -q "lucky Gauss solution" "$TMP/x.out" &&
   cmp -s "$TMP/a" "$TMP/b"; then
    echo "OK    X1s rechazada: σ incumple una cláusula y la búsqueda es idéntica ($(wc -l < "$TMP/a") contadores)"
else bad "X1s rechazada: no se rechazó o la búsqueda cambió"; fi

if [ $fail = 0 ]; then echo "test_gauss: todo correcto"; else echo "test_gauss: HAY FALLOS"; fi
exit $fail
