/*
 * mclique.c — clique máxima por ramificación y poda (LabeSAT, licencia MIT).
 * Interfaz y procedencia en mclique.h.
 *
 * Algoritmo (Tomita y Seki 2003, con conjuntos de bits como en San Segundo et
 * al. 2011):
 *   1. Se renumeran los vértices por grado no creciente.  Con ese orden, el
 *      coloreado voraz da cotas más ajustadas.
 *   2. Cota inferior inicial: una clique voraz en ese orden.
 *   3. expand(C, P): colorea P de forma voraz.  El número de color de un
 *      vértice acota el tamaño de la mayor clique que puede aportar desde P.
 *      Se ramifica del último vértice coloreado al primero y se poda en cuanto
 *      |C| + color <= |mejor|.  Los vértices con color < kmin, con
 *      kmin = |mejor| - |C| + 1, no se ramifican (no pueden mejorar), pero
 *      siguen en P para los subproblemas.
 */
#include "mclique.h"

#include <stdlib.h>
#include <string.h>

/* Con -DMCLIQUE_TRACE, cada búsqueda imprime en stderr su tamaño, los nodos
 * del árbol y el tiempo.  Solo para diagnóstico; no se compila por defecto. */
#ifdef MCLIQUE_TRACE
#include <time.h>
static long mclique_nodes;
#define TRACE_NODE() (mclique_nodes++)
#else
#define TRACE_NODE() ((void) 0)
#endif

static clique_options mclique_default_options = {NULL, NULL, NULL,
                                                 NULL, NULL, NULL};
clique_options *cliquer_default_options = &mclique_default_options;

static void *xcalloc (size_t n, size_t size) {
  void *p = calloc (n ? n : 1, size ? size : 1);
  if (!p) {
    fprintf (stderr, "mclique: sin memoria\n");
    abort ();
  }
  return p;
}

/* ---------------------------------------------------------------- grafo */

graph_t *graph_new (int n) {
  graph_t *g = xcalloc (1, sizeof *g);
  g->n = n < 0 ? 0 : n;
  g->words = (g->n + 63) / 64;
  g->adj = xcalloc ((size_t) g->n * g->words, sizeof *g->adj);
  return g;
}

void graph_free (graph_t *g) {
  if (!g)
    return;
  free (g->adj);
  free (g);
}

static inline uint64_t *row (const graph_t *g, int v) {
  return g->adj + (size_t) v * g->words;
}

void mclique_graph_add_edge (graph_t *g, int i, int j) {
  if (i == j || i < 0 || j < 0 || i >= g->n || j >= g->n)
    return;
  row (g, i)[j >> 6] |= (uint64_t) 1 << (j & 63);
  row (g, j)[i >> 6] |= (uint64_t) 1 << (i & 63);
}

int mclique_graph_is_edge (const graph_t *g, int i, int j) {
  if (i < 0 || j < 0 || i >= g->n || j >= g->n)
    return 0;
  return (int) ((row (g, i)[j >> 6] >> (j & 63)) & 1);
}

/* ------------------------------------------------------------ conjuntos */

static set_t set_new (int n) {
  set_t s = xcalloc (1, sizeof *s);
  s->n = n;
  s->words = (n + 63) / 64;
  s->bits = xcalloc (s->words, sizeof *s->bits);
  return s;
}

int set_return_next (set_t s, int i) {
  if (!s)
    return -1;
  int v = i < 0 ? 0 : i + 1;
  while (v < s->n) {
    uint64_t w = s->bits[v >> 6] >> (v & 63);
    if (w)
      return v + __builtin_ctzll (w);
    v = (v | 63) + 1;
  }
  return -1;
}

int mclique_set_size (set_t s) {
  int k = 0;
  if (s)
    for (int w = 0; w < s->words; w++)
      k += __builtin_popcountll (s->bits[w]);
  return k;
}

void set_free (set_t s) {
  if (!s)
    return;
  free (s->bits);
  free (s);
}

/* ------------------------------------------------------------- búsqueda */

typedef struct {
  int n, words;
  uint64_t *adj;   /* adyacencia en la numeración nueva (por grado) */
  int *cur, ncur;  /* clique en construcción */
  int *best, nbest;
  uint64_t *scratch_u, *scratch_q; /* auxiliares del coloreado */
  long long work, limit; /* trabajo gastado y presupuesto */
  int aborted;
} search;

/* Presupuesto de trabajo de una búsqueda.  Cada nodo cuesta |P| · palabras,
 * que es el orden del coloreado voraz: así el presupuesto sigue al tiempo real
 * y el resultado no depende de la máquina (es determinista).  Con el valor por
 * defecto, en el grafo más difícil visto en bench/symm2026 (896 vértices,
 * densidad 0,76) la búsqueda se corta a los ~0,7 s. */
static long long work_limit = MCLIQUE_DEFAULT_WORK_LIMIT;

void mclique_set_work_limit (long long limit) {
  work_limit = limit > 0 ? limit : MCLIQUE_DEFAULT_WORK_LIMIT;
}

static inline int popcount_bits (const uint64_t *b, int words) {
  int k = 0;
  for (int w = 0; w < words; w++)
    k += __builtin_popcountll (b[w]);
  return k;
}

static inline int first_bit (const uint64_t *b, int words) {
  for (int w = 0; w < words; w++)
    if (b[w])
      return (w << 6) + __builtin_ctzll (b[w]);
  return -1;
}

/* Coloreado voraz de P en clases independientes, en orden de vértice.  Guarda
 * en order/color, con color no decreciente, solo los vértices de color >=
 * kmin.  Devuelve cuántos guardó. */
static int color (search *s, const uint64_t *P, int kmin, int *order,
                  int *col) {
  const int words = s->words;
  uint64_t *U = s->scratch_u, *Q = s->scratch_q;
  memcpy (U, P, words * sizeof *U);
  int k = 0, m = 0;
  for (;;) {
    int any = 0;
    for (int w = 0; w < words && !any; w++)
      any = U[w] != 0;
    if (!any)
      break;
    k++;
    memcpy (Q, U, words * sizeof *Q);
    int v;
    while ((v = first_bit (Q, words)) >= 0) {
      const uint64_t bit = (uint64_t) 1 << (v & 63);
      U[v >> 6] &= ~bit;
      Q[v >> 6] &= ~bit;
      const uint64_t *a = s->adj + (size_t) v * words;
      for (int w = 0; w < words; w++)
        Q[w] &= ~a[w];
      if (k >= kmin) {
        order[m] = v;
        col[m] = k;
        m++;
      }
    }
  }
  return m;
}

static void expand (search *s, uint64_t *P) {
  TRACE_NODE ();
  const int words = s->words;
  const int size = popcount_bits (P, words);
  s->work += (long long) size * words;
  if (s->work > s->limit) {
    s->aborted = 1;
    return;
  }
  int *order = xcalloc (size, sizeof *order);
  int *col = xcalloc (size, sizeof *col);
  uint64_t *NP = xcalloc (words, sizeof *NP);

  int kmin = s->nbest - s->ncur + 1;
  if (kmin < 1)
    kmin = 1;
  const int m = color (s, P, kmin, order, col);

  for (int i = m - 1; i >= 0; i--) {
    if (s->ncur + col[i] <= s->nbest)
      break;
    const int v = order[i];
    s->cur[s->ncur++] = v;
    const uint64_t *a = s->adj + (size_t) v * words;
    int any = 0;
    for (int w = 0; w < words; w++)
      any |= (NP[w] = P[w] & a[w]) != 0;
    if (any) {
      expand (s, NP);
      if (s->aborted) {
        s->ncur--;
        break;
      }
    }
    else if (s->ncur > s->nbest) {
      memcpy (s->best, s->cur, s->ncur * sizeof *s->best);
      s->nbest = s->ncur;
    }
    s->ncur--;
    P[v >> 6] &= ~((uint64_t) 1 << (v & 63));
  }

  free (NP);
  free (col);
  free (order);
}

typedef struct {
  int vertex, degree;
} by_degree;

static int cmp_degree (const void *a, const void *b) {
  const by_degree *x = a, *y = b;
  if (x->degree != y->degree)
    return x->degree > y->degree ? -1 : 1;
  return x->vertex - y->vertex;
}

set_t clique_unweighted_find_single (graph_t *g, int min_size, int max_size,
                                     boolean maximal, clique_options *opts) {
  (void) maximal; /* una clique máxima siempre es maximal */
  (void) opts;
  if (!g || g->n == 0 || max_size > 0)
    return NULL;
  const int n = g->n, words = g->words;
#ifdef MCLIQUE_TRACE
  struct timespec t0, t1;
  clock_gettime (CLOCK_MONOTONIC, &t0);
  mclique_nodes = 0;
  {
    long e = 0;
    for (int v = 0; v < n; v++)
      e += popcount_bits (row (g, v), words);
    fprintf (stderr, "mclique: entra n=%d aristas=%ld\n", n, e / 2);
    const char *dump = getenv ("MCLIQUE_DUMP"); /* grafo en formato DIMACS */
    if (dump) {
      static int calls;
      char path[4096];
      snprintf (path, sizeof path, "%s.%d.col", dump, calls++);
      FILE *f = fopen (path, "w");
      if (f) {
        fprintf (f, "p edge %d %ld\n", n, e / 2);
        for (int i = 0; i < n; i++)
          for (int j = i + 1; j < n; j++)
            if ((row (g, i)[j >> 6] >> (j & 63)) & 1)
              fprintf (f, "e %d %d\n", i + 1, j + 1);
        fclose (f);
      }
    }
  }
#endif

  /* 1. Renumerar por grado no creciente (empates: índice menor primero). */
  by_degree *d = xcalloc (n, sizeof *d);
  for (int v = 0; v < n; v++) {
    d[v].vertex = v;
    d[v].degree = popcount_bits (row (g, v), words);
  }
  qsort (d, n, sizeof *d, cmp_degree);
  int *old_of = xcalloc (n, sizeof *old_of), *new_of = xcalloc (n, sizeof *new_of);
  for (int i = 0; i < n; i++) {
    old_of[i] = d[i].vertex;
    new_of[d[i].vertex] = i;
  }
  free (d);

  search s;
  s.n = n;
  s.words = words;
  s.adj = xcalloc ((size_t) n * words, sizeof *s.adj);
  for (int i = 0; i < n; i++) {
    const uint64_t *r = row (g, old_of[i]);
    uint64_t *t = s.adj + (size_t) i * words;
    for (int w = 0; w < words; w++)
      for (uint64_t b = r[w]; b; b &= b - 1) {
        const int j = new_of[(w << 6) + __builtin_ctzll (b)];
        t[j >> 6] |= (uint64_t) 1 << (j & 63);
      }
  }
  s.cur = xcalloc (n, sizeof *s.cur);
  s.best = xcalloc (n, sizeof *s.best);
  s.ncur = s.nbest = 0;
  s.scratch_u = xcalloc (words, sizeof *s.scratch_u);
  s.scratch_q = xcalloc (words, sizeof *s.scratch_q);
  s.work = 0;
  s.limit = work_limit;
  s.aborted = 0;

  /* 2. Cota inferior: clique voraz en el orden nuevo. */
  for (int v = 0; v < n; v++) {
    const uint64_t *a = s.adj + (size_t) v * words;
    int ok = 1;
    for (int k = 0; k < s.nbest && ok; k++)
      ok = (int) ((a[s.best[k] >> 6] >> (s.best[k] & 63)) & 1);
    if (ok)
      s.best[s.nbest++] = v;
  }

  /* 3. Ramificación y poda sobre todos los vértices. */
  uint64_t *P = xcalloc (words, sizeof *P);
  for (int v = 0; v < n; v++)
    P[v >> 6] |= (uint64_t) 1 << (v & 63);
  expand (&s, P);
  free (P);

  /* 4. Si se agotó el presupuesto, la mejor clique puede no ser maximal: se
   * amplía de forma voraz (sin efecto si la búsqueda terminó, porque entonces
   * es máxima). */
  for (int v = 0; v < n; v++) {
    const uint64_t *a = s.adj + (size_t) v * words;
    int ok = 1;
    for (int k = 0; k < s.nbest && ok; k++)
      ok = s.best[k] != v && (int) ((a[s.best[k] >> 6] >> (s.best[k] & 63)) & 1);
    if (ok)
      s.best[s.nbest++] = v;
  }

#ifdef MCLIQUE_TRACE
  clock_gettime (CLOCK_MONOTONIC, &t1);
  long edges = 0;
  for (int v = 0; v < n; v++)
    edges += popcount_bits (row (g, v), words);
  fprintf (stderr,
           "mclique: n=%d aristas=%ld clique=%d nodos=%ld trabajo=%lld%s %.3f s\n",
           n, edges / 2, s.nbest, mclique_nodes, s.work,
           s.aborted ? " (presupuesto agotado)" : "",
           (double) (t1.tv_sec - t0.tv_sec) + 1e-9 * (t1.tv_nsec - t0.tv_nsec));
#endif
  set_t result = NULL;
  if (s.nbest >= min_size) {
    result = set_new (n);
    for (int k = 0; k < s.nbest; k++) {
      const int v = old_of[s.best[k]];
      result->bits[v >> 6] |= (uint64_t) 1 << (v & 63);
    }
  }

  free (s.scratch_q);
  free (s.scratch_u);
  free (s.best);
  free (s.cur);
  free (s.adj);
  free (new_of);
  free (old_of);
  return result;
}
