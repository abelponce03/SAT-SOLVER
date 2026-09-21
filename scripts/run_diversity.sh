#!/usr/bin/env bash
#
# run_diversity.sh — EXP-001: ejecuta el mismo binario de Kissat con varias
# configuraciones sobre el mismo banco, para medir si hay complementariedad
# entre ellas (ver docs/experiments/EXP-001-diversidad-intrinseca-kissat.md).
#
# Uso:
#   ./scripts/run_diversity.sh [-b banco] [-t timeout_s] [-j jobs] [-o dir_salida]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BENCH="$ROOT/bench/downloaded/gbd"
TIMEOUT=30
JOBS=3
OUT="$ROOT/results/exp001"

while getopts "b:t:j:o:h" o; do
    case "$o" in
        b) BENCH="$OPTARG" ;; t) TIMEOUT="$OPTARG" ;;
        j) JOBS="$OPTARG" ;;  o) OUT="$OPTARG" ;;
        h|*) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
    esac
done

BIN="$ROOT/solver/kissat/build/kissat"
[ -x "$BIN" ] || { echo "Falta el binario; ejecuta ./scripts/build.sh"; exit 1; }
mkdir -p "$OUT"

# id:opciones — el id acaba en el nombre del CSV y en la columna 'label'
CONFIGS=(
    "c0-default-s1:--seed=1"
    "c1-default-s2:--seed=2"
    "c2-sat:--seed=1 --sat"
    "c3-unsat:--seed=1 --unsat"
    "c4-focused:--seed=1 --stable=0"
    "c5-stable:--seed=1 --stable=2"
    "c6-plain:--seed=1 --plain"
)

for entry in "${CONFIGS[@]}"; do
    id="${entry%%:*}"; opts="${entry#*:}"
    csv="$OUT/$id.csv"
    if [ -s "$csv" ]; then echo "== $id ya está ($csv), se salta"; continue; fi
    echo "== $id   opciones: $opts"
    python3 "$ROOT/scripts/run_experiment.py" \
        --solver "$BIN" --bench "$BENCH" --out "$csv" \
        --timeout "$TIMEOUT" --seeds 1 --jobs "$JOBS" \
        --label "$id" --opts "$opts" | tail -2
done

echo ""
echo "Analiza con:  python3 scripts/analyze_diversity.py $OUT/*.csv"
