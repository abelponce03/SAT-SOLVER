#!/usr/bin/env bash
#
# build.sh - compila el fork de CaDiCaL.
#
# Uso:
#   ./build.sh            # compilacion normal (optimizada, -O3 -DNDEBUG)
#   ./build.sh clean      # limpia artefactos y reconfigura
#
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
CADICAL_DIR="$HERE/../cadical"

cd "$CADICAL_DIR"

if [ "${1:-}" = "clean" ]; then
    echo "== limpiando build/"
    rm -rf build makefile
fi

echo "== configure"
./configure "${@:2}" >/dev/null

echo "== make"
make -j"$(nproc 2>/dev/null || echo 4)" 2>&1 | tail -3

echo ""
echo "Binario listo: $CADICAL_DIR/build/cadical"
"$CADICAL_DIR/build/cadical" --version
