#!/usr/bin/env bash
#
# run_baseline.sh - corre un solver sobre un directorio de instancias CNF,
# aplicando un timeout por instancia, y registra estado + tiempo en un CSV.
#
# El CSV resultante se compara con par2.py para obtener el PAR-2 (la metrica
# oficial de ranking de la SAT Competition: tiempo real si resuelve, o
# 2*timeout de penalizacion si no).
#
# Uso:
#   ./run_baseline.sh -s <solver_bin> -b <dir_benchmarks> -o <salida.csv> [-t timeout_s] [-n etiqueta]
#
# Ejemplo:
#   ./run_baseline.sh -s ../cadical/build/cadical -b ../benchmarks/sample \
#                     -o ../results/baseline.csv -t 60 -n cadical-3.0.1-vanilla
#
# Convencion de codigos de salida DIMACS: 10 = SAT, 20 = UNSAT, otro = desconocido.
set -u

SOLVER=""
BENCH_DIR=""
OUT_CSV=""
TIMEOUT_S=60
LABEL="solver"
EXTRA_ARGS=""

usage() {
    grep '^#' "$0" | sed 's/^# \{0,1\}//' | head -20
    exit 1
}

while getopts "s:b:o:t:n:a:h" opt; do
    case "$opt" in
        s) SOLVER="$OPTARG" ;;
        b) BENCH_DIR="$OPTARG" ;;
        o) OUT_CSV="$OPTARG" ;;
        t) TIMEOUT_S="$OPTARG" ;;
        n) LABEL="$OPTARG" ;;
        a) EXTRA_ARGS="$OPTARG" ;;
        h|*) usage ;;
    esac
done

[ -z "$SOLVER" ] && { echo "ERROR: falta -s <solver_bin>"; usage; }
[ -z "$BENCH_DIR" ] && { echo "ERROR: falta -b <dir_benchmarks>"; usage; }
[ -z "$OUT_CSV" ] && { echo "ERROR: falta -o <salida.csv>"; usage; }
[ ! -x "$SOLVER" ] && { echo "ERROR: solver no ejecutable: $SOLVER"; exit 1; }
[ ! -d "$BENCH_DIR" ] && { echo "ERROR: no existe el directorio: $BENCH_DIR"; exit 1; }

# 'timeout' de coreutils; en macOS instalar coreutils y usar gtimeout.
TIMEOUT_BIN="timeout"
command -v "$TIMEOUT_BIN" >/dev/null 2>&1 || { echo "ERROR: 'timeout' no encontrado"; exit 1; }

mkdir -p "$(dirname "$OUT_CSV")"
echo "solver,instance,status,wall_time_s,timeout_s,exit_code" > "$OUT_CSV"

echo "== Solver:   $SOLVER ($LABEL)"
echo "== Bench:    $BENCH_DIR"
echo "== Timeout:  ${TIMEOUT_S}s por instancia"
echo "== Salida:   $OUT_CSV"
echo ""
printf "%-30s %-8s %10s\n" "instancia" "estado" "tiempo(s)"
printf "%-30s %-8s %10s\n" "------------------------------" "--------" "----------"

shopt -s nullglob
files=("$BENCH_DIR"/*.cnf "$BENCH_DIR"/*.cnf.xz "$BENCH_DIR"/*.cnf.gz)
[ ${#files[@]} -eq 0 ] && { echo "No hay .cnf en $BENCH_DIR"; exit 1; }

for f in "${files[@]}"; do
    name="$(basename "$f")"
    start="$(date +%s.%N)"
    # shellcheck disable=SC2086
    "$TIMEOUT_BIN" --signal=TERM "${TIMEOUT_S}s" "$SOLVER" -q $EXTRA_ARGS "$f" >/dev/null 2>&1
    code=$?
    end="$(date +%s.%N)"
    wall="$(awk "BEGIN{printf \"%.3f\", $end-$start}")"

    case "$code" in
        10) status="SAT" ;;
        20) status="UNSAT" ;;
        124|137) status="TIMEOUT"; wall="$TIMEOUT_S.000" ;;
        *)  status="UNKNOWN" ;;
    esac

    printf "%-30s %-8s %10s\n" "$name" "$status" "$wall"
    echo "$LABEL,$name,$status,$wall,$TIMEOUT_S,$code" >> "$OUT_CSV"
done

echo ""
echo "Listo. Calcula el PAR-2 con:"
echo "   python3 scripts/par2.py $OUT_CSV"
