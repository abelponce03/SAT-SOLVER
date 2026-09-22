#!/usr/bin/env bash
#
# build.sh — compila el fork de Kissat.
#
# Uso:
#   ./scripts/build.sh                 # release (-O3 -DNDEBUG), el que se mide
#   ./scripts/build.sh --clean         # borra artefactos y reconfigura
#   ./scripts/build.sh --debug         # símbolos + asserts + logging (NO usar para medir)
#   ./scripts/build.sh --sanitize      # ASan/UBSan (para cazar bugs de nuestros parches)
#   ./scripts/build.sh --stats         # release + contadores de estadísticas completos
#   ./scripts/build.sh --competition   # configuración de entrega (--no-options --quiet)
#
# Cualquier otro argumento se pasa tal cual a `./configure` de Kissat.
#
# El binario queda en solver/kissat/build/kissat.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
KISSAT_DIR="$ROOT/solver/kissat"

CONFIGURE_ARGS=()
CLEAN=0
for arg in "$@"; do
    case "$arg" in
        --clean)    CLEAN=1 ;;
        # Los nombres de la izquierda son NUESTROS; a la derecha van las opciones
        # que el `configure` de Kissat acepta de verdad (ver ./configure --help).
        --debug)       CONFIGURE_ARGS+=("-g") ;;                     # implica -c -s -l
        --sanitize)    CONFIGURE_ARGS+=("-s" "-fsanitize=address,undefined") ;;
        --stats)       CONFIGURE_ARGS+=("--statistics") ;;
        --competition) CONFIGURE_ARGS+=("--competition") ;;
        *)          CONFIGURE_ARGS+=("$arg") ;;
    esac
done

cd "$KISSAT_DIR"

if [ "$CLEAN" = "1" ]; then
    echo "== limpiando build/"
    rm -rf build makefile
fi

if [ ${#CONFIGURE_ARGS[@]} -eq 0 ]; then
    echo "== configure (release por defecto)"
    ./configure >/dev/null
else
    echo "== configure ${CONFIGURE_ARGS[*]}"
    ./configure "${CONFIGURE_ARGS[@]}" >/dev/null
fi

echo "== make -j$(nproc 2>/dev/null || echo 4)"
make -j"$(nproc 2>/dev/null || echo 4)" >/dev/null 2>&1

BIN="$KISSAT_DIR/build/kissat"
echo ""
echo "Binario:  $BIN"
printf "Versión:  "; "$BIN" --version
printf "Commit:   "; git -C "$ROOT" rev-parse --short HEAD
