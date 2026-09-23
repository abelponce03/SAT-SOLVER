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
#   ./scripts/build.sh --symmetry      # satsuma integrado en el binario (D-016, ADR-0007)
#   ./scripts/build.sh --dir=NOMBRE    # compila en solver/kissat/NOMBRE en vez de build/
#                                      # (p. ej. mientras un experimento vigila build/kissat)
#
# Cualquier otro argumento se pasa tal cual a `./configure` de Kissat.
#
# El binario queda en solver/kissat/build/kissat (o en NOMBRE/kissat con --dir).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
KISSAT_DIR="$ROOT/solver/kissat"

CONFIGURE_ARGS=()
CLEAN=0
DIR=build
for arg in "$@"; do
    case "$arg" in
        --clean)    CLEAN=1 ;;
        # Los nombres de la izquierda son NUESTROS; a la derecha van las opciones
        # que el `configure` de Kissat acepta de verdad (ver ./configure --help).
        --debug)       CONFIGURE_ARGS+=("-g") ;;                     # implica -c -s -l
        --sanitize)    CONFIGURE_ARGS+=("-s" "-fsanitize=address,undefined") ;;
        --stats)       CONFIGURE_ARGS+=("--statistics") ;;
        --competition) CONFIGURE_ARGS+=("--competition") ;;
        --symmetry)    CONFIGURE_ARGS+=("--symmetry") ;;
        --dir=*)       DIR="${arg#--dir=}" ;;
        *)          CONFIGURE_ARGS+=("$arg") ;;
    esac
done

cd "$KISSAT_DIR"

case "$DIR" in */*|""|.|..) echo "build.sh: --dir espera un nombre, no una ruta" >&2; exit 1 ;; esac
if [ "$CLEAN" = "1" ]; then
    echo "== limpiando $DIR/"
    rm -rf "$DIR" makefile
fi

# El configure de Kissat compila en el directorio desde el que se le llama
# si no es la raíz: así se puede tener más de un build a la vez.
if [ "$DIR" = build ]; then CONF=./configure; else mkdir -p "$DIR"; cd "$DIR"; CONF=../configure; fi
if [ ${#CONFIGURE_ARGS[@]} -eq 0 ]; then
    echo "== configure (release por defecto) en $DIR/"
    $CONF >/dev/null
else
    echo "== configure ${CONFIGURE_ARGS[*]} en $DIR/"
    $CONF "${CONFIGURE_ARGS[@]}" >/dev/null
fi
cd "$KISSAT_DIR/$DIR"

echo "== make -j$(nproc 2>/dev/null || echo 4)"
make -j"$(nproc 2>/dev/null || echo 4)" >/dev/null 2>&1

BIN="$KISSAT_DIR/$DIR/kissat"
echo ""
echo "Binario:  $BIN"
printf "Versión:  "; "$BIN" --version
printf "Commit:   "; git -C "$ROOT" rev-parse --short HEAD
