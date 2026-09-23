#!/usr/bin/env bash
#
# test_symmetry.sh — comprueba de punta a punta la tubería satsuma → kissat
# (solver/labesat) sobre bench/symm:
#
#   - la respuesta coincide con bench/symm/expected.csv;
#   - UNSAT: la prueba combinada (prefijo SR de satsuma + DRAT de kissat) la
#     verifica dsr-trim contra la CNF ORIGINAL;
#   - SAT: el modelo satisface la CNF ORIGINAL (no la simplificada);
#   - control negativo: sin '--append-proof' kissat sobrescribe el prefijo y
#     dsr-trim debe RECHAZAR la prueba (si no, el test no prueba nada);
#   - ruta de respaldo: si satsuma falla, la prueba es DRAT puro (drat-trim).
#
# Uso: scripts/test_symmetry.sh [ruta/al/kissat]
# Requiere scripts/get_tools.sh (satsuma, dsr-trim, drat-trim en tools/).
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export LABESAT_KISSAT="${1:-$ROOT/solver/kissat/build/kissat}"
W="$ROOT/solver/labesat"
DSR="$ROOT/tools/dsr-trim"
DSR_SC="$ROOT/tools/dsr-trim-sc2026"   # el commit exacto de la competición
DRAT="$ROOT/tools/drat-trim"
for t in "$LABESAT_KISSAT" "$ROOT/tools/satsuma" "$DSR" "$DSR_SC" "$DRAT"; do
    [ -x "$t" ] || { echo "falta $t (¿scripts/get_tools.sh?)"; exit 2; }
done
fail=0
bad() { echo "FALLO $*"; fail=1; }
# verified CHECKER CNF PROOF: guarda la salida ANTES de buscar en ella.  Con
# pipefail, 'checker | grep -q' falla al azar: grep cierra la tubería al
# encontrar la línea y el verificador muere por SIGPIPE si aún escribía.
verified() { "$1" "$2" "$3" > "$TMP/check.out" 2>&1; grep -aq "^s VERIFIED" "$TMP/check.out"; }

# Sin LABESAT_KISSAT, el guion debe encontrar kissat por sí solo: así es como
# lo invocan los experimentos (EXP-007 se lanzó una vez con esto roto).
if [ -z "${1:-}" ]; then
    if (unset LABESAT_KISSAT; "$W" --version >/dev/null 2>&1); then
        echo "OK    labesat encuentra kissat sin LABESAT_KISSAT"
    else bad "labesat no encuentra kissat sin LABESAT_KISSAT"; fi
fi
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

while IFS=, read -r inst expected _; do
    [ "$inst" = instance ] && continue
    cnf="$ROOT/bench/symm/$inst"
    "$W" --symmetry "$cnf" "$TMP/proof" > "$TMP/out"; code=$?
    case "$expected:$code" in
        UNSAT:20)
            if verified "$DSR" "$cnf" "$TMP/proof" && verified "$DSR_SC" "$cnf" "$TMP/proof"; then
                echo "OK    $inst: UNSAT, prueba SR verificada por dsr-trim (actual y el de SC2026)"
            else bad "$inst: dsr-trim (actual o SC2026) no verificó la prueba combinada"; fi ;;
        SAT:10)
            if python3 "$ROOT/scripts/verify_model.py" --model "$TMP/out" "$cnf" >/dev/null; then
                echo "OK    $inst: SAT, el modelo satisface la CNF original"
            else bad "$inst: el modelo NO satisface la CNF original"; fi ;;
        *) bad "$inst: esperado $expected, código $code" ;;
    esac
done < "$ROOT/bench/symm/expected.csv"

# Control negativo: la misma tubería sin '--append-proof' debe dar una prueba
# inválida.  Garantiza que el OK de arriba depende de verdad del prefijo.
cnf="$ROOT/bench/symm/php_12_11.cnf"   # su refutación corta depende del prefijo
"$ROOT/tools/satsuma" fix "$cnf" --silent --full-skip-limit 100000000 \
    --add-reduced-as-unit --bsr --proof-file "$TMP/neg" --out-file "$TMP/sb.cnf" >/dev/null 2>&1
"$LABESAT_KISSAT" --no-binary "$TMP/sb.cnf" "$TMP/neg" >/dev/null
if verified "$DSR" "$cnf" "$TMP/neg" || verified "$DSR_SC" "$cnf" "$TMP/neg"; then
    bad "control negativo: dsr-trim aceptó una prueba sin prefijo"
else
    echo "OK    control negativo: sin --append-proof la prueba se rechaza"
fi

# Ruta de respaldo: satsuma no disponible → kissat sobre la CNF original.
cnf="$ROOT/bench/symm/php9x9_rand160u.cnf"
LABESAT_SATSUMA=/bin/false "$W" --symmetry "$cnf" "$TMP/fb" > "$TMP/out"; code=$?
if [ $code = 20 ] && grep -q "sin simetrías" "$TMP/out" &&
   out=$("$DRAT" "$cnf" "$TMP/fb" 2>/dev/null) && grep -q "s VERIFIED" <<< "$out"; then
    echo "OK    respaldo: satsuma falla → prueba DRAT pura verificada"
else bad "respaldo (código $code)"; fi

[ $fail = 0 ] && echo "test_symmetry: todo correcto" || echo "test_symmetry: HAY FALLOS"
exit $fail
