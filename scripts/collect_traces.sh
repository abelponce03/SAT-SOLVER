#!/usr/bin/env bash
#
# collect_traces.sh — recoge una traza de cambios de modo por instancia
# (EXP-005 paso 0: validar la señal de recompensa antes de escribir el
# planificador adaptativo).
#
# Cada traza lleva en el nombre el resultado de la corrida (SOLVED/TIMEOUT),
# porque la prueba V2 consiste precisamente en ver si la señal distingue una
# cosa de la otra.
#
# Uso: ./scripts/collect_traces.sh -b <banco> -o <dir> [-t timeout] [-j jobs]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BENCH="$ROOT/bench/calib"
OUT="$ROOT/results/exp005/traces"
TIMEOUT=180
JOBS=4
SEED=1

while getopts "b:o:t:j:s:h" o; do
    case "$o" in
        b) BENCH="$OPTARG" ;; o) OUT="$OPTARG" ;; t) TIMEOUT="$OPTARG" ;;
        j) JOBS="$OPTARG" ;;  s) SEED="$OPTARG" ;;
        h|*) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
    esac
done

BIN="$ROOT/solver/kissat/build/kissat"
[ -x "$BIN" ] || { echo "Falta el binario; ejecuta ./scripts/build.sh"; exit 1; }
mkdir -p "$OUT"

trace_one() {
    local f="$1" out="$2" bin="$3" timeout="$4" seed="$5"
    local name tmp code status
    name="$(basename "$f" .cnf.xz)"
    tmp="$out/$name.partial.csv"
    KISSAT_TRACE="$tmp" "$bin" -q -n --seed="$seed" --time="$timeout" "$f" >/dev/null 2>&1
    code=$?
    case "$code" in 10|20) status=SOLVED ;; *) status=TIMEOUT ;; esac
    # el nombre final lleva el desenlace: es lo que separa los dos grupos en V2
    [ -s "$tmp" ] && mv "$tmp" "$out/$name.$status.csv" || rm -f "$tmp"
    printf "%-40s %s\n" "$name" "$status"
}
export -f trace_one

find "$BENCH" -name '*.cnf.xz' | sort | \
    xargs -P "$JOBS" -I{} bash -c 'trace_one "$@"' _ {} "$OUT" "$BIN" "$TIMEOUT" "$SEED"

echo ""
echo "Trazas en $OUT: $(ls "$OUT" | wc -l)"
echo "Valida con:  python3 scripts/validate_reward.py $OUT/*.csv"
