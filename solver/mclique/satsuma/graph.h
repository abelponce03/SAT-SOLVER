/*
 * graph.h — cabecera de compatibilidad (LabeSAT, licencia MIT).
 *
 * satsuma incluye "cliquer/graph.h" desde src/reorder.h cuando se compila con
 * CLIQUES=ON.  scripts/get_tools.sh copia este directorio en src/cliquer/ para
 * que esa inclusión encuentre mclique (clique máxima MIT) en lugar de cliquer
 * (GPLv2).  No contiene código de cliquer.
 */
#include "mclique.h"
