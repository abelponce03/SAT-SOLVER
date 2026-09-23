#!/usr/bin/env bash
#
# run_diversity.sh — EXP-001: ejecuta el mismo binario de Kissat con varias
# configuraciones sobre el mismo banco, para medir si hay complementariedad
# entre ellas (ver docs/experiments/EXP-001-diversidad-intrinseca-kissat.md).
#
# Uso:
#   ./scripts/run_diversity.sh [-b banco] [-t timeout_s] [-j jobs] [-o dir_salida] [-c ids]
#
# -c limita a un subconjunto de configuraciones: -c c0-default-s1,c2-sat
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BENCH="$ROOT/bench/downloaded/gbd"
TIMEOUT=30
JOBS=3
OUT="$ROOT/results/exp001"

ONLY=""
while getopts "b:t:j:o:c:h" o; do
    case "$o" in
        b) BENCH="$OPTARG" ;; t) TIMEOUT="$OPTARG" ;;
        j) JOBS="$OPTARG" ;;  o) OUT="$OPTARG" ;;
        c) ONLY="$OPTARG" ;;   # lista de ids separada por comas; vacío = todas
        h|*) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
    esac
done

BIN="$ROOT/solver/kissat/build/kissat"
[ -x "$BIN" ] || { echo "Falta el binario; ejecuta ./scripts/build.sh"; exit 1; }
mkdir -p "$OUT"

# id|seed|opciones — el id acaba en el nombre del CSV y en la columna 'label'.
# c0 y c1 solo se diferencian en la seed: son el contraste que separa la
# diversidad por aleatorización de la diversidad por configuración (H2).
CONFIGS=(
    "c0-default-s1|1|"
    "c1-default-s2|2|"
    "c2-sat|1|--sat"
    "c3-unsat|1|--unsat"
    "c4-focused|1|--stable=0"
    "c5-stable|1|--stable=2"
    "c6-plain|1|--plain"
)

for entry in "${CONFIGS[@]}"; do
    IFS='|' read -r id seed opts <<< "$entry"
    if [ -n "$ONLY" ] && ! printf '%s' ",$ONLY," | grep -q ",$id,"; then continue; fi
    csv="$OUT/$id.csv"
    if [ -s "$csv" ]; then echo "== $id ya está ($csv), se salta"; continue; fi
    echo "== $id   seed=$seed   opciones: ${opts:-(ninguna)}"
    python3 "$ROOT/scripts/run_experiment.py" \
        --solver "$BIN" --bench "$BENCH" --out "$csv" \
        --timeout "$TIMEOUT" --seeds "$seed" --jobs "$JOBS" \
        --label "$id" --opts="$opts" | tail -2
done

echo ""
echo "Analiza con:  python3 scripts/analyze_diversity.py $OUT/*.csv"
