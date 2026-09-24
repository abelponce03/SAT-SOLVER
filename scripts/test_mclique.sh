#!/usr/bin/env bash
#
# test_mclique.sh — pruebas de mclique, la clique máxima MIT que sustituye a
# cliquer en satsuma (D-005, opción c).
#
#   1. Pruebas unitarias con ASan y UBSan (solver/mclique/test_mclique.c).
#   2. Compatibilidad de interfaz: una unidad C++20 que usa mclique exactamente
#      como lo hace src/reorder.h de satsuma (cabeceras cliquer/cliquer.h y
#      cliquer/graph.h dentro de extern "C") tiene que compilar sin avisos.
#
# Uso: scripts/test_mclique.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/solver/mclique"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CC="${CC:-gcc}"
CXX="${CXX:-g++}"

echo "== pruebas unitarias (ASan/UBSan)"
"$CC" -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined \
    -fno-omit-frame-pointer -I"$SRC" \
    "$SRC/mclique.c" "$SRC/test_mclique.c" -o "$TMP/test_mclique"
UBSAN_OPTIONS=halt_on_error=1 "$TMP/test_mclique"

echo "== compatibilidad con la interfaz que usa satsuma"
mkdir -p "$TMP/src/cliquer"
cp "$SRC/mclique.h" "$SRC"/satsuma/cliquer.h "$SRC"/satsuma/graph.h "$TMP/src/cliquer/"
cat > "$TMP/src/uso.cpp" <<'CPP'
extern "C" {
#include "cliquer/cliquer.h"
#include "cliquer/graph.h"
}
int uso() {
    graph_t* g = graph_new(3);
    GRAPH_ADD_EDGE(g, 0, 1);
    clique_options opts = *cliquer_default_options;
    opts.output = NULL;
    opts.time_function = NULL;
    opts.reorder_function = NULL;
    opts.reorder_map = NULL;
    set_t C = clique_unweighted_find_single(g, 0, 0, TRUE, &opts);
    int k = 0;
    if (C) {
        int v = -1;
        while ((v = set_return_next(C, v)) >= 0) ++k;
        set_free(C);
    }
    graph_free(g);
    return k;
}
CPP
"$CXX" -std=c++20 -Wall -Wextra -Werror -c "$TMP/src/uso.cpp" -o "$TMP/uso.o"
echo "   interfaz compatible"
echo "test_mclique: OK"
