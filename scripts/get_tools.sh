#!/usr/bin/env bash
#
# get_tools.sh — descarga y compila las herramientas externas en tools/
# (ignorado por git: son de terceros y se regeneran).  Todas se fijan a un
# commit concreto para que los experimentos sean reproducibles.
#
#   - drat-trim (Marijn Heule): verificador de pruebas DRAT, el mismo que usa la
#     SAT Competition para validar las respuestas UNSAT.
#   - satsuma (Markus Anders, MIT): preprocesador de ruptura de simetrías.  Emite
#     la CNF con los predicados añadidos y el prefijo de la prueba en formato SR.
#     Se compila con CLIQUES=OFF (el valor por defecto): así no entra cliquer,
#     que es GPLv2, y todo el binario queda bajo MIT (ADR-0004).
#   - dejavu (Markus Anders, MIT): detector de automorfismos que usa satsuma.
#   - dsr-trim (Cayden Codel, Apache 2.0): verificador de pruebas SR/DSR.  Hace
#     falta porque la prueba combinada satsuma+LabeSAT no es DRAT puro.
#
# Uso: scripts/get_tools.sh [--jobs N]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
JOBS=2
[ "${1:-}" = "--jobs" ] && JOBS="$2"

SATSUMA_URL=https://github.com/markusa4/satsuma.git
SATSUMA_REV=c6ad1b59f29fa32dae587ef369135735f40d498a
DEJAVU_URL=https://github.com/markusa4/dejavu.git
DEJAVU_REV=4c275e9ebac4fe51a26aac406682b9bcbfd03a9d
DSRTRIM_URL=https://github.com/ccodel/dsr-trim.git
DSRTRIM_REV=c3119d8570b881d0179a8ae46f1974a32d41d9fc

mkdir -p "$ROOT/tools"
cd "$ROOT/tools"

# fetch_rev DIR URL REV — clon superficial de un commit exacto
fetch_rev() {
    rm -rf "$1"
    git init --quiet "$1"
    git -C "$1" fetch --quiet --depth 1 "$2" "$3"
    git -C "$1" checkout --quiet FETCH_HEAD
}

if [ ! -x drat-trim ]; then
    echo "== drat-trim"
    rm -rf drat-trim-src
    git clone --quiet --depth 1 https://github.com/marijnheule/drat-trim.git drat-trim-src
    gcc -O2 -o drat-trim drat-trim-src/drat-trim.c
    echo "   tools/drat-trim listo"
else
    echo "== drat-trim ya está"
fi

if [ ! -x satsuma ]; then
    echo "== satsuma ${SATSUMA_REV:0:7} + dejavu ${DEJAVU_REV:0:7} (CLIQUES=OFF, solo MIT)"
    fetch_rev satsuma-src "$SATSUMA_URL" "$SATSUMA_REV"
    fetch_rev satsuma-src/src/dejavu "$DEJAVU_URL" "$DEJAVU_REV"
    # FETCHCONTENT_SOURCE_DIR_DEJAVU evita que CMake descargue la rama main de
    # dejavu (el CMakeLists de satsuma no la fija).
    cmake -S satsuma-src -B satsuma-src/build -DCMAKE_BUILD_TYPE=Release \
        -DCLIQUES=OFF -DFETCHCONTENT_SOURCE_DIR_DEJAVU="$PWD/satsuma-src/src/dejavu" \
        >/dev/null
    nice -n 10 cmake --build satsuma-src/build -j "$JOBS" >/dev/null
    cp satsuma-src/build/satsuma satsuma
    if ! grep -q 'CLIQUES:BOOL=OFF' satsuma-src/build/CMakeCache.txt \
        || grep -q cliquer satsuma-src/build/CMakeFiles/satsuma.dir/link.txt; then
        echo "   ERROR: satsuma se compiló con cliquer (GPL)" >&2; exit 1
    fi
    echo "   tools/satsuma listo"
else
    echo "== satsuma ya está"
fi

if [ ! -x dsr-trim ]; then
    echo "== dsr-trim ${DSRTRIM_REV:0:7}"
    fetch_rev dsr-trim-src "$DSRTRIM_URL" "$DSRTRIM_REV"
    nice -n 10 make -C dsr-trim-src -j "$JOBS" >/dev/null
    cp dsr-trim-src/bin/dsr-trim dsr-trim
    echo "   tools/dsr-trim listo"
else
    echo "== dsr-trim ya está"
fi
