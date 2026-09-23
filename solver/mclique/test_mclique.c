/*
 * test_mclique.c — pruebas de mclique (LabeSAT, licencia MIT).
 *
 * Contrasta la clique devuelta con dos referencias independientes:
 *   - fuerza bruta sobre todos los subconjuntos (n <= 16);
 *   - búsqueda exhaustiva sencilla, sin cotas por coloreado (n <= 60).
 * Además comprueba casos con respuesta conocida (completo, vacío, uniones
 * disjuntas, complemento de un emparejamiento, clique plantada en un grafo
 * grande y disperso, como los de satsuma) y la semántica de la interfaz.
 *
 * Uso: scripts/test_mclique.sh (compila con sanitizers y lo ejecuta).
 */
#include "mclique.h"

#include <stdlib.h>
#include <string.h>

static int fails = 0;
#define CHECK(c, ...)                                                          \
  do {                                                                         \
    if (!(c)) {                                                                \
      fprintf (stderr, "FALLO %s:%d: ", __FILE__, __LINE__);                   \
      fprintf (stderr, __VA_ARGS__);                                           \
      fprintf (stderr, "\n");                                                  \
      fails++;                                                                 \
    }                                                                          \
  } while (0)

static uint64_t rng_state = 0x9e3779b97f4a7c15ull;
static uint64_t rng (void) { /* xorshift64* */
  rng_state ^= rng_state >> 12;
  rng_state ^= rng_state << 25;
  rng_state ^= rng_state >> 27;
  return rng_state * 0x2545f4914f6cdd1dull;
}

static graph_t *random_graph (int n, double p) {
  graph_t *g = graph_new (n);
  for (int i = 0; i < n; i++)
    for (int j = i + 1; j < n; j++)
      if ((rng () >> 11) * (1.0 / 9007199254740992.0) < p)
        GRAPH_ADD_EDGE (g, i, j);
  return g;
}

/* Tamaño de la clique devuelta; -1 si no es clique o tiene vértices fuera. */
static int checked_size (graph_t *g, set_t c) {
  int v[4096], k = 0, x = -1;
  while ((x = set_return_next (c, x)) >= 0) {
    if (x >= g->n || k >= 4096)
      return -1;
    v[k++] = x;
  }
  for (int i = 0; i < k; i++)
    for (int j = i + 1; j < k; j++)
      if (!mclique_graph_is_edge (g, v[i], v[j]))
        return -1;
  if (k != mclique_set_size (c))
    return -1;
  return k;
}

static int brute_force (graph_t *g) {
  int best = 0;
  for (unsigned m = 1; m < (1u << g->n); m++) {
    int k = __builtin_popcount (m), ok = 1;
    if (k <= best)
      continue;
    for (int i = 0; i < g->n && ok; i++)
      if (m >> i & 1)
        for (int j = i + 1; j < g->n && ok; j++)
          if (m >> j & 1)
            ok = mclique_graph_is_edge (g, i, j);
    if (ok)
      best = k;
  }
  return best;
}

/* Referencia exhaustiva sin coloreado: poda solo por |C| + |P| <= mejor. */
static void simple_rec (graph_t *g, int *P, int np, int size, int *best) {
  if (size > *best)
    *best = size;
  for (int i = 0; i < np; i++) {
    if (size + np - i <= *best)
      return;
    int *Q = malloc (sizeof *Q * (np ? np : 1)), nq = 0;
    for (int j = i + 1; j < np; j++)
      if (mclique_graph_is_edge (g, P[i], P[j]))
        Q[nq++] = P[j];
    simple_rec (g, Q, nq, size + 1, best);
    free (Q);
  }
}

static int simple_max (graph_t *g) {
  int *P = malloc (sizeof *P * g->n), best = 0;
  for (int i = 0; i < g->n; i++)
    P[i] = i;
  simple_rec (g, P, g->n, 0, &best);
  free (P);
  return best;
}

static int find (graph_t *g) {
  clique_options opts = *cliquer_default_options; /* como satsuma */
  opts.output = NULL;
  opts.time_function = NULL;
  opts.reorder_function = NULL;
  opts.reorder_map = NULL;
  set_t c = clique_unweighted_find_single (g, 0, 0, TRUE, &opts);
  int k = c ? checked_size (g, c) : 0;
  CHECK (!c || k >= 0, "el resultado no es una clique válida (n=%d)", g->n);
  set_free (c);
  return k;
}

int main (void) {
  /* 1. Aleatorios pequeños frente a fuerza bruta. */
  for (int t = 0; t < 3000; t++) {
    int n = 1 + (int) (rng () % 16);
    double p = 0.05 + 0.9 * (double) (rng () % 1000) / 1000.0;
    graph_t *g = random_graph (n, p);
    int a = find (g), b = brute_force (g);
    CHECK (a == b, "n=%d p=%.2f: mclique %d, fuerza bruta %d", n, p, a, b);
    graph_free (g);
  }
  /* 2. Aleatorios medianos frente a la referencia exhaustiva. */
  for (int t = 0; t < 300; t++) {
    int n = 17 + (int) (rng () % 44);
    double p = 0.1 + 0.8 * (double) (rng () % 1000) / 1000.0;
    graph_t *g = random_graph (n, p);
    int a = find (g), b = simple_max (g);
    CHECK (a == b, "n=%d p=%.2f: mclique %d, referencia %d", n, p, a, b);
    graph_free (g);
  }
  /* 3. Casos con respuesta conocida. */
  {
    graph_t *g = graph_new (300); /* completo */
    for (int i = 0; i < 300; i++)
      for (int j = i + 1; j < 300; j++)
        GRAPH_ADD_EDGE (g, i, j);
    CHECK (find (g) == 300, "K300");
    graph_free (g);
  }
  {
    graph_t *g = graph_new (50); /* sin aristas: un vértice */
    CHECK (find (g) == 1, "grafo sin aristas");
    graph_free (g);
  }
  {
    graph_t *g = graph_new (15); /* K3 + K7 + K5 disjuntos, desordenados */
    int perm[15];
    for (int i = 0; i < 15; i++)
      perm[i] = i;
    for (int i = 14; i > 0; i--) {
      int j = (int) (rng () % (unsigned) (i + 1)), x = perm[i];
      perm[i] = perm[j];
      perm[j] = x;
    }
    int start[3] = {0, 3, 10}, len[3] = {3, 7, 5};
    for (int b = 0; b < 3; b++)
      for (int i = 0; i < len[b]; i++)
        for (int j = i + 1; j < len[b]; j++)
          GRAPH_ADD_EDGE (g, perm[start[b] + i], perm[start[b] + j]);
    CHECK (find (g) == 7, "K3+K7+K5");
    graph_free (g);
  }
  {
    graph_t *g = graph_new (80); /* complemento de un emparejamiento perfecto */
    for (int i = 0; i < 80; i++)
      for (int j = i + 1; j < 80; j++)
        if (j != (i ^ 1))
          GRAPH_ADD_EDGE (g, i, j);
    CHECK (find (g) == 40, "complemento de emparejamiento");
    graph_free (g);
  }
  {
    /* Tamaño y forma de satsuma: hasta 10000 vértices, grafo disperso, con
     * una clique de 15 vértices distintos plantada. */
    const int n = 10000;
    graph_t *g = graph_new (n);
    for (int e = 0; e < 5 * n; e++)
      GRAPH_ADD_EDGE (g, (int) (rng () % n), (int) (rng () % n));
    int planted[15];
    for (int i = 0; i < 15; i++)
      planted[i] = (i * 617 + 13) % n;
    for (int i = 0; i < 15; i++)
      for (int j = i + 1; j < 15; j++)
        GRAPH_ADD_EDGE (g, planted[i], planted[j]);
    int k = find (g);
    CHECK (k >= 15, "clique plantada en n=10000: %d", k);
    graph_free (g);
  }
  /* 4. Semántica de la interfaz. */
  {
    graph_t *g = graph_new (0);
    CHECK (clique_unweighted_find_single (g, 0, 0, TRUE, NULL) == NULL,
           "grafo vacío -> NULL");
    graph_free (g);
    g = graph_new (6);
    GRAPH_ADD_EDGE (g, 1, 4);
    GRAPH_ADD_EDGE (g, 4, 1); /* repetida: sin efecto */
    GRAPH_ADD_EDGE (g, 2, 2); /* bucle: se ignora */
    set_t c = clique_unweighted_find_single (g, 0, 0, TRUE, NULL);
    CHECK (set_return_next (c, -1) == 1 && set_return_next (c, 1) == 4 &&
               set_return_next (c, 4) == -1,
           "iteración de set_return_next");
    set_free (c);
    CHECK (clique_unweighted_find_single (g, 3, 0, TRUE, NULL) == NULL,
           "min_size mayor que la clique máxima -> NULL");
    c = clique_unweighted_find_single (g, 2, 0, TRUE, NULL);
    CHECK (mclique_set_size (c) == 2, "min_size alcanzable");
    set_free (c);
    CHECK (clique_unweighted_find_single (g, 0, 2, TRUE, NULL) == NULL,
           "max_size > 0 no se admite -> NULL");
    graph_free (g);
  }
  /* 5. Determinismo. */
  {
    graph_t *g = random_graph (120, 0.5);
    set_t a = clique_unweighted_find_single (g, 0, 0, TRUE, NULL);
    set_t b = clique_unweighted_find_single (g, 0, 0, TRUE, NULL);
    int x = -1, y = -1, same = 1;
    do {
      x = set_return_next (a, x);
      y = set_return_next (b, y);
      same &= x == y;
    } while (x >= 0 && y >= 0);
    CHECK (same, "dos llamadas iguales dan cliques distintas");
    set_free (a);
    set_free (b);
    graph_free (g);
  }
  if (fails) {
    fprintf (stderr, "test_mclique: %d fallos\n", fails);
    return 1;
  }
  printf ("test_mclique: todo correcto\n");
  return 0;
}
