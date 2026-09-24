#!/usr/bin/env bash
#
# test_symmetry_integrada.sh — ruptura de simetrías DENTRO del binario de
# Kissat (D-016, fase 1; ADR-0007), sobre bench/symm.
#
# Comprueba, con el binario compilado con 'configure --symmetry':
#   1. Equivalencia: la CNF intermedia es idéntica byte a byte a la del satsuma
#      externo (tools/satsuma) con los mismos argumentos que usaba labesat.
#   2. UNSAT: la prueba (prefijo SR de satsuma + DRAT de kissat) la aceptan
#      los dos dsr-trim, el actual y el de la SAT Competition 2026.
#   3. SAT: el modelo satisface la CNF ORIGINAL.
#   4. Entrada comprimida (.xz).
#   5. Respaldo: si satsuma no se aplica (tope de tamaño), la prueba es DRAT
#      pura y la verifica drat-trim.
#   6. Sin '--symmetry' no hay paso de simetrías, y un binario compilado sin
#      soporte rechaza la opción.
#
# Uso: scripts/test_symmetry_integrada.sh [<binario>]
#      (por defecto solver/kissat/build-symm/kissat; lo compila si falta)
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
K="${1:-solver/kissat/build-symm/kissat}"
if [ ! -x "$K" ]; then
    ./scripts/build.sh --dir=build-symm --symmetry >/dev/null || { echo "no compila"; exit 1; }
fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fail=0
ok()   { echo "OK    $*"; }
bad()  { echo "FALLO $*"; fail=1; }
verified() {  # verified <cnf> <proof>: los dos dsr-trim
    for d in tools/dsr-trim tools/dsr-trim-sc2026; do
        "$d" "$1" "$2" > "$TMP/check.out" 2>&1
        grep -aq '^s VERIFIED' "$TMP/check.out" || return 1
    done
}

for f in bench/symm/*.cnf; do
    b=$(basename "$f" .cnf)
    LABESAT_SYMM_KEEP=1 "$K" --symmetry "$f" "$TMP/$b.proof" > "$TMP/$b.out" 2> "$TMP/$b.err"
    code=$?
    d=$(sed -n 's/.*conservados en //p' "$TMP/$b.err")
    if [ -z "$d" ] || [ ! -s "$d/sb.cnf" ]; then bad "$b: satsuma no se aplicó"; continue; fi
    if [ -x tools/satsuma ]; then
        tools/satsuma fix "$f" --silent --full-skip-limit 100000000 --add-reduced-as-unit \
            --bsr --out-file "$TMP/ref.cnf" >/dev/null 2>&1
        cmp -s "$d/sb.cnf" "$TMP/ref.cnf" && ok "$b: CNF intermedia idéntica a la de satsuma externo" \
            || bad "$b: la CNF intermedia difiere de la de satsuma externo"
    fi
    rm -rf "$d"
    case $code in
        20) verified "$f" "$TMP/$b.proof" && ok "$b: UNSAT, prueba verificada por los dos dsr-trim" \
                || bad "$b: prueba rechazada" ;;
        10) python3 scripts/verify_model.py --model "$TMP/$b.out" "$f" >/dev/null 2>&1 \
                && ok "$b: SAT, el modelo satisface la CNF original" || bad "$b: modelo inválido" ;;
        *)  bad "$b: código $code" ;;
    esac
done

xz -kc bench/symm/php_12_11.cnf > "$TMP/p.cnf.xz"
"$K" --symmetry "$TMP/p.cnf.xz" "$TMP/xz.proof" > "$TMP/xz.out"
if [ $? = 20 ] && grep -q 'aplicado' "$TMP/xz.out" && verified bench/symm/php_12_11.cnf "$TMP/xz.proof"; then
    ok "entrada .xz: satsuma aplicado y prueba verificada"
else bad "entrada .xz"; fi

LABESAT_SYMM_MAXBYTES=10 "$K" --symmetry bench/symm/php9x9_rand160u.cnf "$TMP/fb.proof" > "$TMP/fb.out"
if [ $? = 20 ] && grep -q 'sin simetr' "$TMP/fb.out" \
    && tools/drat-trim bench/symm/php9x9_rand160u.cnf "$TMP/fb.proof" 2>&1 | grep -aq 's VERIFIED'; then
    ok "respaldo (tope de tamaño): prueba DRAT pura verificada por drat-trim"
else bad "respaldo"; fi

"$K" bench/symm/php_9_9.cnf > "$TMP/off.out"
grep -q 'symmetry' "$TMP/off.out" && bad "sin --symmetry hay paso de simetrías" \
    || ok "sin --symmetry no hay paso de simetrías (apagado por defecto)"
if [ -x solver/kissat/build/kissat ]; then
    solver/kissat/build/kissat --symmetry bench/symm/php_9_9.cnf >/dev/null 2>&1
    [ $? = 1 ] && ok "un binario sin soporte rechaza --symmetry" \
        || bad "un binario sin soporte acepta --symmetry"
fi

[ $fail = 0 ] && echo "test_symmetry_integrada: todo correcto" || echo "test_symmetry_integrada: HAY FALLOS"
exit $fail
