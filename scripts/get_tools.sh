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
#   - satsuma-mclique: el mismo satsuma con CLIQUES=ON, donde la clique máxima
#     la pone mclique (solver/mclique, MIT, D-005) en lugar de cliquer.
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
# El commit que usó la SAT Competition 2026 (checker.commits.txt de su web).
# Hay 12 commits de correcciones entre ambos: una prueba que solo pase con el
# nuevo descalificaría en la competición.  Se verifica con los dos.
DSRTRIM_SC_REV=8f857dd6cb34ccff8eb94e2f4ed6cf012d6c8f35
# Kissat «sc2026»: versión posterior a 4.0.4, sin release publicada, que Biere
# presentó a la SAT Competition 2026 (paquete oficial de solvers, MIT).  Solo
# para EXP-008 (D-013): no se distribuye mientras no se decida cambiar de base.
KISSAT_SC_URL=https://satcompetition.github.io/2026/downloads/solvers/biere.tar.xz
KISSAT_SC_SHA256=69fbdae7a9a0a96955ea953976257712388834fca7000a844d3d736b61d8b3f3

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

# satsuma con CLIQUES=ON, pero con mclique (clique máxima MIT, solver/mclique)
# en el hueco de cliquer (GPLv2): D-005, opción c.  Binario aparte hasta que
# EXP-010 lo valide; labesat lo usa con LABESAT_SATSUMA=tools/satsuma-mclique.
if [ ! -x satsuma-mclique ]; then
    echo "== satsuma ${SATSUMA_REV:0:7} con mclique (CLIQUES=ON, sin cliquer, solo MIT)"
    if [ "$(git -C satsuma-src rev-parse HEAD 2>/dev/null)" != "$SATSUMA_REV" ]; then
        fetch_rev satsuma-src "$SATSUMA_URL" "$SATSUMA_REV"
        fetch_rev satsuma-src/src/dejavu "$DEJAVU_URL" "$DEJAVU_REV"
    fi
    rm -rf satsuma-src/src/cliquer satsuma-src/build-mclique
    mkdir -p satsuma-src/src/cliquer
    cp "$ROOT"/solver/mclique/mclique.[ch] "$ROOT"/solver/mclique/satsuma/* satsuma-src/src/cliquer/
    cmake -S satsuma-src -B satsuma-src/build-mclique -DCMAKE_BUILD_TYPE=Release \
        -DCLIQUES=ON -DFETCHCONTENT_SOURCE_DIR_DEJAVU="$PWD/satsuma-src/src/dejavu" \
        >/dev/null
    nice -n 10 cmake --build satsuma-src/build-mclique -j "$JOBS" >/dev/null
    # Lo compilado en src/cliquer tiene que ser exactamente nuestro código.
    for f in satsuma-src/src/cliquer/*; do
        b=$(basename "$f")
        orig="$ROOT/solver/mclique/$b"
        [ -f "$orig" ] || orig="$ROOT/solver/mclique/satsuma/$b"
        if ! cmp -s "$f" "$orig" || grep -qi 'general public license' "$f"; then
            echo "   ERROR: src/cliquer/$b no es de mclique" >&2; exit 1
        fi
    done
    cp satsuma-src/build-mclique/satsuma satsuma-mclique
    echo "   tools/satsuma-mclique listo"
else
    echo "== satsuma-mclique ya está"
fi

# mclique v1 (sin presupuesto de trabajo): el binario de EXP-010, que EXP-011
# parte 1 compara con v2.  Se reconstruye desde el commit que lo introdujo, en
# una copia aparte del árbol de satsuma para no pisar el build de v2.
MCLIQUE_V1_REV=0b4ec1f
# Solo lo usan los experimentos (reanudar_experimentos.sh lo exige); en un
# clon superficial (CI, fetch-depth 1) el commit no está y se omite con aviso.
if [ ! -x satsuma-mclique-v1 ] && ! git -C "$ROOT" cat-file -e "$MCLIQUE_V1_REV^{commit}" 2>/dev/null; then
    echo "== satsuma-mclique-v1 omitido: el commit $MCLIQUE_V1_REV no está en este clon"
    echo "   (clon superficial). Solo hace falta para EXP-010/011: git fetch --unshallow"
elif [ ! -x satsuma-mclique-v1 ]; then
    echo "== satsuma ${SATSUMA_REV:0:7} con mclique v1 (commit $MCLIQUE_V1_REV, EXP-010)"
    rm -rf satsuma-src-v1 && cp -r satsuma-src satsuma-src-v1
    rm -rf satsuma-src-v1/src/cliquer satsuma-src-v1/build-mclique
    mkdir -p satsuma-src-v1/src/cliquer
    git -C "$ROOT" ls-tree -r --name-only "$MCLIQUE_V1_REV" solver/mclique |
        grep -E '^solver/mclique/(mclique\.[ch]|satsuma/[^/]+)$' | while read -r f; do
            git -C "$ROOT" show "$MCLIQUE_V1_REV:$f" > "satsuma-src-v1/src/cliquer/$(basename "$f")"
        done
    if grep -qil 'general public license' satsuma-src-v1/src/cliquer/*; then
        echo "   ERROR: src/cliquer de v1 no es de mclique" >&2; exit 1
    fi
    cmake -S satsuma-src-v1 -B satsuma-src-v1/build-mclique -DCMAKE_BUILD_TYPE=Release \
        -DCLIQUES=ON -DFETCHCONTENT_SOURCE_DIR_DEJAVU="$PWD/satsuma-src-v1/src/dejavu" \
        >/dev/null
    nice -n 10 cmake --build satsuma-src-v1/build-mclique -j "$JOBS" >/dev/null
    cp satsuma-src-v1/build-mclique/satsuma satsuma-mclique-v1
    echo "   tools/satsuma-mclique-v1 listo"
else
    echo "== satsuma-mclique-v1 ya está"
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

if [ ! -x kissat-sc2026 ]; then
    echo "== kissat sc2026 (paquete de la SAT Competition 2026, sha256 ${KISSAT_SC_SHA256:0:12})"
    rm -rf kissat-sc2026-src biere.tar.xz biere
    curl -sSfL -o biere.tar.xz "$KISSAT_SC_URL"
    echo "$KISSAT_SC_SHA256  biere.tar.xz" | sha256sum -c --quiet
    mkdir -p biere && tar -xJf biere.tar.xz -C biere
    mv biere/biere/kissat/src kissat-sc2026-src && rm -rf biere biere.tar.xz
    # El paquete trae un build/ ya compilado y un enlace src/makefile: se
    # eliminan para compilar desde cero, igual que en la competición.
    rm -rf kissat-sc2026-src/build kissat-sc2026-src/src/makefile
    (cd kissat-sc2026-src && ./configure >/dev/null && nice -n 10 make -C build -j "$JOBS" >/dev/null)
    cp kissat-sc2026-src/build/kissat kissat-sc2026
    echo "   tools/kissat-sc2026 listo ($(./kissat-sc2026 --version))"
else
    echo "== kissat-sc2026 ya está"
fi

if [ ! -x dsr-trim-sc2026 ]; then
    echo "== dsr-trim ${DSRTRIM_SC_REV:0:7} (el de la SAT Competition 2026)"
    fetch_rev dsr-trim-sc2026-src "$DSRTRIM_URL" "$DSRTRIM_SC_REV"
    nice -n 10 make -C dsr-trim-sc2026-src -j "$JOBS" >/dev/null
    cp dsr-trim-sc2026-src/bin/dsr-trim dsr-trim-sc2026
    echo "   tools/dsr-trim-sc2026 listo"
else
    echo "== dsr-trim-sc2026 ya está"
fi
