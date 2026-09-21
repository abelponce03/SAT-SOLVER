#!/usr/bin/env bash
#
# get_tools.sh — descarga y compila las herramientas externas de verificación en
# tools/ (ignorado por git: son de terceros y se regeneran).
#
#   - drat-trim (Marijn Heule): verificador de pruebas DRAT, el mismo que usa la
#     SAT Competition para validar las respuestas UNSAT.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/tools"
cd "$ROOT/tools"

if [ ! -x drat-trim ]; then
    echo "== drat-trim"
    rm -rf drat-trim-src
    git clone --quiet --depth 1 https://github.com/marijnheule/drat-trim.git drat-trim-src
    gcc -O2 -o drat-trim drat-trim-src/drat-trim.c
    echo "   tools/drat-trim listo"
else
    echo "== drat-trim ya está"
fi
