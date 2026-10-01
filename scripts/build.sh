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
#   ./scripts/build.sh --lto           # optimización en tiempo de enlace (-flto)
#   ./scripts/build.sh --march=X       # -march=X y SIEMPRE -ffp-contract=off (research/08,
#                                      # Teorema 5: sin él, GCC fusiona a*b+c en FMA y la
#                                      # búsqueda puede cambiar)
#   ./scripts/build.sh --pgo           # compilación guiada por perfil en dos fases: binario
#                                      # instrumentado, entrenamiento con las instancias de
#                                      # scripts/pgo_entrenamiento.txt y recompilación con el
#                                      # perfil (ADR-0009, clase E)
#   ./scripts/build.sh --jobs=N        # procesos de make (por defecto, nproc)
#   ./scripts/build.sh --control-fma=X # SOLO para el control negativo de EXP-017: -march=X
#                                      # SIN -ffp-contract=off. Puede cambiar la búsqueda;
#                                      # no usar para nada más
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
PGO=0
JOBS="$(nproc 2>/dev/null || echo 4)"
for arg in "$@"; do
    case "$arg" in
        --clean)    CLEAN=1 ;;
        --lto)      CONFIGURE_ARGS+=("-flto") ;;
        --march=*)  CONFIGURE_ARGS+=("CC=gcc -march=${arg#--march=}" "-ffp-contract=off") ;;
        --pgo)      PGO=1 ;;
        --control-fma=*) CONFIGURE_ARGS+=("CC=gcc -march=${arg#--control-fma=}") ;;
        --jobs=*)   JOBS="${arg#--jobs=}" ;;
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
    rm -rf "$DIR" "$DIR.pgo-perfil" makefile
fi

# El configure de Kissat compila en el directorio desde el que se le llama
# si no es la raíz: así se puede tener más de un build a la vez.
configurar_y_compilar() {   # $@: argumentos extra para configure
    cd "$KISSAT_DIR"
    if [ "$DIR" = build ]; then CONF=./configure; else mkdir -p "$DIR"; cd "$DIR"; CONF=../configure; fi
    local args=("${CONFIGURE_ARGS[@]}" "$@")
    if [ ${#args[@]} -eq 0 ]; then
        echo "== configure (release por defecto) en $DIR/"
        $CONF >/dev/null
    else
        echo "== configure ${args[*]} en $DIR/"
        $CONF "${args[@]}" >/dev/null
    fi
    cd "$KISSAT_DIR/$DIR"
    echo "== make -j$JOBS"
    make -j"$JOBS" >/dev/null 2>&1
}

if [ "$PGO" = 1 ]; then
    # La PGO borra y recompila el directorio dos veces: nunca sobre build/
    # mientras la cola de experimentos lo vigila (ADR-0008).
    if [ "$DIR" = build ] && systemctl --user is-active --quiet labesat-experimentos 2>/dev/null; then
        echo "build.sh: --pgo sobre build/ con la cola en marcha; usa --dir=OTRO" >&2; exit 1
    fi
    # Fase 1: binario instrumentado.  El perfil va a un directorio absoluto
    # propio, que sobrevive a la limpieza de los objetos entre fases.
    PERFIL="$KISSAT_DIR/$DIR.pgo-perfil"
    LISTA="$ROOT/scripts/pgo_entrenamiento.txt"
    [ -f "$LISTA" ] || { echo "build.sh: falta $LISTA" >&2; exit 1; }
    rm -rf "$PERFIL" "$KISSAT_DIR/$DIR"
    configurar_y_compilar "-fprofile-generate=$PERFIL" "-fprofile-update=single"
    # Entrenamiento: presupuesto determinista, para que el perfil no dependa
    # de la velocidad de la máquina.  Las instancias son DISJUNTAS de los
    # bancos de evaluación (EXP-017).
    echo "== entrenamiento PGO ($(grep -cv '^#' "$LISTA") instancias)"
    while read -r linea; do
        case "$linea" in ''|'#'*) continue ;; esac
        set -- $linea
        f="$ROOT/$1"; conf="${2:-50000}"
        [ -r "$f" ] || { echo "build.sh: no encuentro $f (scripts/pgo_entrenamiento.txt)" >&2; exit 1; }
        "$KISSAT_DIR/$DIR/kissat" --seed=1 --conflicts="$conf" -q -n "$f" >/dev/null 2>&1 || true
    done < "$LISTA"
    # Fase 2: recompilar con el perfil.
    rm -rf "$KISSAT_DIR/$DIR"
    configurar_y_compilar "-fprofile-use=$PERFIL" "-fprofile-correction"
else
    configurar_y_compilar
fi
BIN="$KISSAT_DIR/$DIR/kissat"
echo ""
echo "Binario:  $BIN"
printf "Versión:  "; "$BIN" --version
printf "Commit:   "; git -C "$ROOT" rev-parse --short HEAD
