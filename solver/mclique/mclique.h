/*
 * mclique — clique máxima en grafos no dirigidos (LabeSAT, licencia MIT).
 *
 * Sustituye a cliquer (GPLv2) en satsuma, que usa una sola búsqueda de clique
 * máxima para reordenar las columnas de una simetría de fila (D-005, opción c).
 * Implementación en «sala limpia»: se escribió a partir de los algoritmos
 * publicados (ramificación y poda con cota por coloreado voraz: Tomita y Seki,
 * 2003; representación con conjuntos de bits: San Segundo et al., 2011) y SIN
 * leer el código de cliquer.  De satsuma (MIT) solo se toma la interfaz: los
 * nombres de tipos y funciones que usa su fichero src/reorder.h.
 *
 * Interfaz compatible (lo único que satsuma necesita):
 *   graph_t, graph_new, GRAPH_ADD_EDGE, graph_free,
 *   clique_options, cliquer_default_options,
 *   clique_unweighted_find_single, set_t, set_return_next, set_free,
 *   boolean, TRUE, FALSE.
 *
 * Semántica de clique_unweighted_find_single(g, min, max, maximal, opts):
 *   - min = 0 y max = 0: devuelve UNA clique de tamaño máximo (que siempre es
 *     maximal), salvo que se agote el presupuesto (ver abajo).  Es la única
 *     llamada de satsuma.
 *   - min > 0 y max = 0: la clique máxima si tiene al menos 'min' vértices;
 *     si no, NULL.
 *   - max > 0: no se admite; devuelve NULL.
 *   - Grafo vacío (0 vértices): NULL.
 * Los campos de clique_options se aceptan y se ignoran: el orden de búsqueda
 * es siempre el propio (grado no creciente), y no hay salida.
 *
 * Presupuesto (desde la versión 2, tras EXP-010): la búsqueda exacta tiene un
 * presupuesto de trabajo determinista (mclique_set_work_limit).  Si se agota,
 * se devuelve la mayor clique encontrada hasta entonces, ampliada hasta ser
 * maximal, que puede no ser máxima.  Motivo: en grafos densos y muy regulares
 * encontrar la clique máxima es rápido y DEMOSTRAR que lo es puede ser
 * exponencial (EXP-010: 896 vértices, densidad 0,76, sin terminar en 5 min).
 * Para satsuma es seguro: usa la clique solo para ordenar las columnas antes
 * de romper la simetría, y cualquier orden da predicados y pruebas correctos
 * (sin cliques, satsuma ni siquiera reordena).
 *
 * El resultado es determinista: mismo grafo y mismo presupuesto, misma clique.
 */
#ifndef MCLIQUE_H
#define MCLIQUE_H

#include <stdint.h>
#include <stdio.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef int boolean;
#ifndef TRUE
#define TRUE 1
#endif
#ifndef FALSE
#define FALSE 0
#endif

/* Grafo no dirigido con vértices 0..n-1: matriz de adyacencia en bits. */
typedef struct mclique_graph {
  int n;         /* número de vértices */
  int words;     /* palabras de 64 bits por fila */
  uint64_t *adj; /* n filas de 'words' palabras */
} graph_t;

/* Conjunto de vértices 0..n-1 (el resultado de la búsqueda). */
typedef struct mclique_set {
  int n;
  int words;
  uint64_t *bits;
} *set_t;

typedef struct clique_options clique_options;
struct clique_options {
  int *(*reorder_function) (graph_t *, boolean); /* se ignora */
  int *reorder_map;                              /* se ignora */
  boolean (*time_function) (int, int, int, int, double, double,
                            clique_options *);   /* se ignora */
  FILE *output;                                  /* se ignora */
  boolean (*user_function) (set_t, graph_t *, clique_options *); /* se ignora */
  void *user_data;                               /* se ignora */
};

extern clique_options *cliquer_default_options;

/* Presupuesto de trabajo por búsqueda (unidades: |P| · palabras de 64 bits por
 * nodo).  Un valor <= 0 restaura el valor por defecto. */
#define MCLIQUE_DEFAULT_WORK_LIMIT 500000000LL
void mclique_set_work_limit (long long limit);

graph_t *graph_new (int n);
void graph_free (graph_t *g);
void mclique_graph_add_edge (graph_t *g, int i, int j);
int mclique_graph_is_edge (const graph_t *g, int i, int j);
#define GRAPH_ADD_EDGE(g, i, j) mclique_graph_add_edge ((g), (i), (j))

set_t clique_unweighted_find_single (graph_t *g, int min_size, int max_size,
                                     boolean maximal, clique_options *opts);

/* Siguiente elemento de 's' mayor que 'i' (empieza con i = -1); -1 al final. */
int set_return_next (set_t s, int i);
int mclique_set_size (set_t s);
void set_free (set_t s);

#ifdef __cplusplus
}
#endif

#endif
