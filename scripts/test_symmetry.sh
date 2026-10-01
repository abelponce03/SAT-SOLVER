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

# Ruptura con retraso (B3, EXP-009).  (a) Si kissat resuelve en la fase 1, la
# respuesta y la prueba son las de kissat sobre la CNF original (DRAT pura).
cnf="$ROOT/bench/smoke/rand3_120_r4.26_s1.cnf"    # UNSAT en < 1 s
"$W" --symmetry --symmetry-delay=5 "$cnf" "$TMP/d1" > "$TMP/out"; code=$?
if [ $code = 20 ] && grep -q "resuelto en la fase 1" "$TMP/out" &&
   [ "$(grep -c '^s ' "$TMP/out")" = 1 ] &&
   out=$("$DRAT" "$cnf" "$TMP/d1" 2>/dev/null) && grep -q "s VERIFIED" <<< "$out"; then
    echo "OK    retraso, fase 1: UNSAT sin satsuma, una sola línea s, prueba DRAT verificada"
else bad "retraso, fase 1 (código $code)"; fi
# (b) Si la fase 1 no resuelve, su prueba se descarta y la combinada de satsuma
# + kissat debe verificarse contra la CNF original con los dos dsr-trim.
cnf="$ROOT/bench/symm/php_12_11.cnf"              # kissat solo no lo resuelve en 1 s
"$W" --symmetry --symmetry-delay=1 "$cnf" "$TMP/d2" > "$TMP/out"; code=$?
if [ $code = 20 ] && grep -q "fase 1 sin respuesta" "$TMP/out" &&
   [ "$(grep -c '^s ' "$TMP/out")" = 1 ] &&
   verified "$DSR" "$cnf" "$TMP/d2" && verified "$DSR_SC" "$cnf" "$TMP/d2"; then
    echo "OK    retraso, fase 2: satsuma tras la fase 1, prueba SR verificada (actual y SC2026)"
else bad "retraso, fase 2 (código $code)"; fi
# (c) Un presupuesto total que no llega al retraso: kissat solo.
"$W" --symmetry --symmetry-delay=5 --time=3 "$ROOT/bench/smoke/php_5_4.cnf" > "$TMP/out"; code=$?
if [ $code = 20 ] && grep -q "presupuesto total" "$TMP/out"; then
    echo "OK    retraso mayor que --time: kissat solo"
else bad "retraso mayor que --time (código $code)"; fi
[ $fail = 0 ] && echo "test_symmetry: todo correcto" || echo "test_symmetry: HAY FALLOS"
exit $fail
