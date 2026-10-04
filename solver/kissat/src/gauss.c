/* [SOLVER] X1 (research/09 §3): refutación de sistemas XOR inconsistentes.

   1. Extracción (Lema 0): grupos de 2^(k-1) cláusulas irredundantes sobre
      las mismas k <= 'gaussmaxsize' variables con la misma paridad de
      negaciones.  Las variables fijadas en la raíz salen de la fila y
      ajustan su paridad.
   2. Gauss sobre GF(2) con historial (Lema 1).  Si una fila queda 0 = 1,
      su historial es el certificado S, que se vuelve a sumar antes de
      afirmar nada.
   3. Prueba DRAT del Teorema 1, sin borrados (§4.3: el dsr-trim de SC2026
      falla con ciertos borrados):
        - z nueva con la unitaria -z;
        - todas las definiciones de las cadenas (RAT, Lema 2) primero;
        - lemas de las hojas (Lema 4) y barridos (Lema 5), RUP por casos;
        - la unitaria z de la raíz (conjunto vacío, paridad 1) y la vacía.
      Las variables de extensión solo existen en la prueba: sus índices
      empiezan en SIZE_STACK (solver->import), por encima de cualquier
      variable externa que Kissat haya usado.

   Si el sistema es consistente, o algún límite no se cumple, no se emite
   nada ni se modifica el estado del solver: la búsqueda que sigue es la
   misma que sin X1.

   X1s (research/09 §3.5, opción 'gausslucky'): si todas las componentes son
   consistentes, una solución particular σ (sustitución hacia atrás, Lema 7)
   se comprueba contra todas las cláusulas irredundantes sin escribir nada.
   Solo si las satisface se guarda, y 'kissat_lucky' la asigna la primera
   (Proposición 4: sin conflicto). */

#ifdef LABESAT_GAUSS

#include "gauss.h"
#include "allocate.h"
#include "inline.h"
#include "internal.h"
#include "logging.h"
#include "decide.h"
#include "error.h"
#include "print.h"
#include "proprobe.h"
#include "proof.h"
#include "resources.h"

#include <inttypes.h>
#include <stdlib.h>
#include <string.h>

#define GAUSS_MAX_K 8

typedef struct gauss_candidate gauss_candidate;

struct gauss_candidate {
  unsigned size, signs;
  unsigned vars[GAUSS_MAX_K];
};

typedef struct gauss_node gauss_node;

struct gauss_node {
  size_t start;
  unsigned size, parity;
  int out;
};

typedef STACK (gauss_candidate) gauss_candidates;
typedef STACK (gauss_node) gauss_nodes;

static int compare_candidates (const void *p, const void *q) {
  const gauss_candidate *a = p, *b = q;
  if (a->size != b->size)
    return a->size < b->size ? -1 : 1;
  for (unsigned i = 0; i != a->size; i++)
    if (a->vars[i] != b->vars[i])
      return a->vars[i] < b->vars[i] ? -1 : 1;
  if (a->signs != b->signs)
    return a->signs < b->signs ? -1 : 1;
  return 0;
}

static bool make_candidate (kissat *solver, gauss_candidate *c,
                            unsigned size, const unsigned *lits) {
  (void) solver; // 'IDX' lo usa solo con asertos (configure -g)
  unsigned sorted[GAUSS_MAX_K];
  for (unsigned i = 0; i != size; i++) {
    unsigned lit = lits[i], j = i;
    while (j && IDX (sorted[j - 1]) > IDX (lit)) {
      sorted[j] = sorted[j - 1];
      j--;
    }
    sorted[j] = lit;
  }
  c->size = size;
  c->signs = 0;
  for (unsigned i = 0; i != size; i++) {
    if (i && IDX (sorted[i - 1]) == IDX (sorted[i]))
      return false;
    c->vars[i] = IDX (sorted[i]);
    if (NEGATED (sorted[i]))
      c->signs |= 1u << i;
  }
  return true;
}

static unsigned parity_of (unsigned x) {
  return (unsigned) __builtin_popcount (x) & 1u;
}

/* Escritura de la prueba: líneas con literales externos. */

static void emit (kissat *solver, unsigned size, const int *lits) {
  kissat_add_external_lits_to_proof (solver, size, lits);
}

static void define_xor (kissat *solver, int t, int p, int x) {
  const int c1[3] = {-t, p, x}, c2[3] = {-t, -p, -x};
  const int c3[3] = {t, -p, x}, c4[3] = {t, p, -x};
  emit (solver, 3, c1);
  emit (solver, 3, c2);
  emit (solver, 3, c3);
  emit (solver, 3, c4);
}

/* Lema 3: cada cláusula E de la XOR sobre 'vars' (multiconjunto) con
   paridad 'b' se añade vía E ∨ v, E ∨ ¬v y E.  La unitaria -z ya existe. */
static void derive_xor_by_cases (kissat *solver, unsigned n,
                                 const int *vars_in, unsigned b, int v,
                                 int z) {
  int vars[GAUSS_MAX_K + 1];
  unsigned k = 0;
  for (unsigned i = 0; i != n; i++) {
    unsigned j = 0;
    while (j != k && vars[j] != vars_in[i])
      j++;
    if (j == k)
      vars[k++] = vars_in[i];
    else
      vars[j] = vars[--k];
  }
  assert (k <= GAUSS_MAX_K + 1);
  int clause[GAUSS_MAX_K + 2];
  for (unsigned m = 0; m != (1u << k); m++) {
    if (parity_of (m) == b)
      continue;
    for (unsigned i = 0; i != k; i++)
      clause[i] = (m >> i) & 1 ? -vars[i] : vars[i];
    if (k == 1 && clause[0] == -z)
      continue;
    clause[k] = v;
    emit (solver, k + 1, clause);
    clause[k] = -v;
    emit (solver, k + 1, clause);
    emit (solver, k, clause);
  }
}

static gauss_node new_node (kissat *solver, ints *vars, ints *chain,
                            unsigned size, const int *elements,
                            unsigned parity, int z, int *next) {
  gauss_node node;
  node.start = SIZE_STACK (*vars);
  node.size = size;
  node.parity = parity;
  int prev = z;
  for (unsigned i = 0; i != size; i++) {
    const int t = (*next)++;
    define_xor (solver, t, prev, elements[i]);
    PUSH_STACK (*vars, elements[i]);
    PUSH_STACK (*chain, t);
    prev = t;
  }
  node.out = prev;
  return node;
}

/* Lema 4: de las cláusulas originales de la fila a la unitaria de su
   salida.  L_j = XOR (c_j, x_{j+1}, ..., x_k) = b, por casos sobre x_j. */
static void derive_leaf (kissat *solver, ints *vars, ints *chain,
                         const gauss_node *node, int z) {
  const int *x = BEGIN_STACK (*vars) + node->start;
  const int *c = BEGIN_STACK (*chain) + node->start;
  int tmp[GAUSS_MAX_K + 1];
  for (unsigned j = 0; j != node->size; j++) {
    unsigned n = 0;
    tmp[n++] = c[j];
    for (unsigned i = j + 1; i != node->size; i++)
      tmp[n++] = x[i];
    derive_xor_by_cases (solver, n, tmp, node->parity, x[j], z);
  }
}

/* Lema 5: barrido por las variables de A ∪ B y unitaria de la salida de
   C = A Δ B. */
static void derive_sum (kissat *solver, ints *vars, ints *chain,
                        const gauss_node *A, const gauss_node *B,
                        const gauss_node *C, int z) {
  const int *av = BEGIN_STACK (*vars) + A->start;
  const int *ac = BEGIN_STACK (*chain) + A->start;
  const int *bv = BEGIN_STACK (*vars) + B->start;
  const int *bc = BEGIN_STACK (*chain) + B->start;
  const int *cv = BEGIN_STACK (*vars) + C->start;
  const int *cc = BEGIN_STACK (*chain) + C->start;
  unsigned ia = 0, ib = 0, ic = 0;
  int a = z, b = z, c = z;
  while (ia != A->size || ib != B->size) {
    int v;
    if (ib == B->size || (ia != A->size && av[ia] < bv[ib]))
      v = av[ia];
    else
      v = bv[ib];
    const bool in_a = ia != A->size && av[ia] == v;
    const bool in_b = ib != B->size && bv[ib] == v;
    if (in_a)
      a = ac[ia++];
    if (in_b)
      b = bc[ib++];
    if (in_a != in_b) {
      assert (ic != C->size && cv[ic] == v);
      (void) cv;
      c = cc[ic++];
    }
    const int triple[3] = {a, b, c};
    derive_xor_by_cases (solver, 3, triple, 0, v, z);
  }
  assert (ic == C->size);
  const int unit = C->parity ? C->out : -C->out;
  if (unit != -z)
    emit (solver, 1, &unit);
}

static unsigned merge_difference (const int *a, unsigned na, const int *b,
                                  unsigned nb, int *out) {
  unsigned i = 0, j = 0, n = 0;
  while (i != na || j != nb) {
    if (j == nb || (i != na && a[i] < b[j]))
      out[n++] = a[i++];
    else if (i == na || b[j] < a[i])
      out[n++] = b[j++];
    else
      i++, j++;
  }
  return n;
}

static int compare_ints (const void *p, const void *q) {
  const int a = *(const int *) p, b = *(const int *) q;
  return a < b ? -1 : a > b;
}

static uint64_t emit_proof (kissat *solver, const unsigneds *rows,
                            const unsigneds *starts, const unsigneds *sizes,
                            const unsigneds *parities,
                            const unsigneds *certificate) {
  int next = (int) SIZE_STACK (solver->import);
  const int z = next++;
  const int not_z = -z;
  emit (solver, 1, &not_z);
  ints vars, chain, scratch;
  INIT_STACK (vars);
  INIT_STACK (chain);
  INIT_STACK (scratch);
  gauss_nodes nodes;
  INIT_STACK (nodes);
  // Fase 1: hojas y nodos internos, con todas sus definiciones (RAT).
  for (all_stack (unsigned, r, *certificate)) {
    const unsigned size = PEEK_STACK (*sizes, r);
    const unsigned *row = BEGIN_STACK (*rows) + PEEK_STACK (*starts, r);
    CLEAR_STACK (scratch);
    for (unsigned i = 0; i != size; i++)
      PUSH_STACK (scratch, kissat_export_literal (solver, LIT (row[i])));
    qsort (BEGIN_STACK (scratch), size, sizeof (int), compare_ints);
    gauss_node node =
        new_node (solver, &vars, &chain, size, BEGIN_STACK (scratch),
                  PEEK_STACK (*parities, r), z, &next);
    PUSH_STACK (nodes, node);
  }
  const size_t leaves = SIZE_STACK (nodes);
  size_t begin = 0, end = leaves;
  while (end - begin > 1) {
    for (size_t i = begin; i + 1 < end; i += 2) {
      const gauss_node A = PEEK_STACK (nodes, i);
      const gauss_node B = PEEK_STACK (nodes, i + 1);
      CLEAR_STACK (scratch);
      for (unsigned j = 0; j != A.size + B.size; j++)
        PUSH_STACK (scratch, 0);
      const unsigned size = merge_difference (
          BEGIN_STACK (vars) + A.start, A.size, BEGIN_STACK (vars) + B.start,
          B.size, BEGIN_STACK (scratch));
      gauss_node C = new_node (solver, &vars, &chain, size,
                               BEGIN_STACK (scratch),
                               A.parity ^ B.parity, z, &next);
      PUSH_STACK (nodes, C);
    }
    if ((end - begin) & 1) {
      const gauss_node last = PEEK_STACK (nodes, end - 1);
      PUSH_STACK (nodes, last);
    }
    begin = end;
    end = SIZE_STACK (nodes);
  }
  // Fase 2: lemas de las hojas.
  for (size_t i = 0; i != leaves; i++)
    derive_leaf (solver, &vars, &chain, BEGIN_STACK (nodes) + i, z);
  // Fase 3: sumas, nivel a nivel, en el mismo orden en que se crearon.
  begin = 0, end = leaves;
  while (end - begin > 1) {
    size_t parent = end;
    for (size_t i = begin; i + 1 < end; i += 2, parent++)
      derive_sum (solver, &vars, &chain, BEGIN_STACK (nodes) + i,
                  BEGIN_STACK (nodes) + i + 1, BEGIN_STACK (nodes) + parent,
                  z);
    if ((end - begin) & 1)
      parent++; // la copia del nodo impar no necesita lemas
    begin = end;
    end = parent;
  }
  const gauss_node *root = &TOP_STACK (nodes);
  assert (!root->size);
  assert (root->parity);
  (void) root;
  kissat_add_external_lits_to_proof (solver, 0, 0);
  const uint64_t fresh = (uint64_t) (next - z);
  RELEASE_STACK (vars);
  RELEASE_STACK (chain);
  RELEASE_STACK (scratch);
  RELEASE_STACK (nodes);
  return fresh;
}

/* Raíz de la unión-búsqueda, con compresión de caminos a la mitad. */
/* X1s, Lema 7: R en forma escalonada (filas 0..rank-1, pivote de la fila i
   en pivcol[i], creciente).  Las columnas libres valen 'initial'; cada pivote
   se fija de la última fila a la primera.  La fila i solo tiene columnas
   >= pivcol[i], y 'sol' no tiene bits a partir de m, así que el AND ya
   descarta la paridad y el historial. */
static void gauss_back_substitute (kissat *solver, uint64_t **R, unsigned rank,
                                   const unsigned *pivcol, unsigned m,
                                   const unsigned *colvar, value initial,
                                   value *sigma) {
  const unsigned cw = (m + 63) / 64;
  uint64_t *sol = kissat_calloc (solver, cw, 8);
  if (initial > 0)
    for (unsigned col = 0; col != m; col++)
      sol[col / 64] |= (uint64_t) 1 << (col % 64);
  for (unsigned i = 0; i != rank; i++) // los pivotes se calculan, no se fijan
    sol[pivcol[i] / 64] &= ~((uint64_t) 1 << (pivcol[i] % 64));
  for (unsigned i = rank; i-- != 0;) {
    const uint64_t *row = R[i];
    unsigned acc = (unsigned) (row[m / 64] >> (m % 64)) & 1u;
    for (unsigned w = pivcol[i] / 64; w != cw; w++)
      acc ^= (unsigned) __builtin_popcountll (row[w] & sol[w]) & 1u;
    if (acc)
      sol[pivcol[i] / 64] |= (uint64_t) 1 << (pivcol[i] % 64);
  }
  for (unsigned col = 0; col != m; col++)
    sigma[colvar[col]] = (sol[col / 64] >> (col % 64)) & 1 ? 1 : -1;
  kissat_dealloc (solver, sol, cw, 8);
}

/* X1s: ¿satisface σ todas las cláusulas irredundantes?  Solo lee. */
static bool gauss_satisfies_all (kissat *solver, const value *sigma,
                                 size_t *checked) {
  size_t n = 0;
  for (all_literals (lit)) {
    const value a = NEGATED (lit) ? -sigma[IDX (lit)] : sigma[IDX (lit)];
    watches *ws = &WATCHES (lit);
    for (all_binary_blocking_watches (watch, *ws)) {
      if (!watch.type.binary)
        continue;
      const unsigned other = watch.binary.lit;
      if (lit > other)
        continue;
      n++;
      const value b =
          NEGATED (other) ? -sigma[IDX (other)] : sigma[IDX (other)];
      if (a < 0 && b < 0) {
        *checked = n;
        return false;
      }
    }
  }
  for (all_clauses (c)) {
    if (c->garbage || c->redundant)
      continue;
    n++;
    bool satisfied = false;
    for (all_literals_in_clause (lit, c)) {
      const value v = NEGATED (lit) ? -sigma[IDX (lit)] : sigma[IDX (lit)];
      if (v > 0) {
        satisfied = true;
        break;
      }
    }
    if (!satisfied) {
      *checked = n;
      return false;
    }
  }
  *checked = n;
  return true;
}

/* X1s, Proposición 4: con σ ⊨ F, asumir σ variable a variable y propagar no
   produce conflicto y deja todas asignadas.  Se llama desde 'kissat_lucky',
   con 'probing' puesto. */
int kissat_gauss_lucky (kissat *solver) {
  value *sigma = solver->gauss_model;
  if (!sigma)
    return 0;
  solver->gauss_model = 0;
  assert (!solver->level);
  for (all_variables (idx)) {
    if (!ACTIVE (idx))
      continue;
    const unsigned lit = LIT (idx);
    if (VALUE (lit))
      continue;
    kissat_internal_assume (solver, sigma[idx] > 0 ? lit : NOT (lit));
    if (kissat_probing_propagate (solver, 0, true))
      kissat_fatal ("gauss: conflict assigning the Gauss solution "
                    "(internal error)");
  }
  kissat_dealloc (solver, sigma, VARS, sizeof (value));
  assert (!solver->unassigned);
  kissat_message (solver, "lucky Gauss solution of the XOR system (X1s)");
  return 10;
}

static inline unsigned gauss_find (unsigned *parent, unsigned x) {
  while (parent[x] != x)
    x = parent[x] = parent[parent[x]];
  return x;
}

int kissat_gauss (kissat *solver) {
  if (solver->inconsistent || solver->level || !solver->watching)
    return 0;
  // El reloj solo se lee para informar: no decide nada (research/08 T5 (c)).
  const double started = kissat_process_time ();
  const unsigned max_size = (unsigned) GET_OPTION (gaussmaxsize);
  assert (2 <= max_size && max_size <= GAUSS_MAX_K);
  // Tope de memoria: cada candidata ocupa sizeof (gauss_candidate) bytes.
  const size_t max_candidates = (size_t) GET_OPTION (gaussclauses);
  bool too_many = false;
  gauss_candidates candidates;
  INIT_STACK (candidates);
  // Binarias (en las listas de vigilancia) y grandes irredundantes.
  for (all_literals (lit)) {
    if (too_many)
      break;
    watches *ws = &WATCHES (lit);
    for (all_binary_blocking_watches (watch, *ws)) {
      if (!watch.type.binary)
        continue;
      const unsigned other = watch.binary.lit;
      if (lit > other)
        continue;
      const unsigned lits[2] = {lit, other};
      gauss_candidate c;
      if (make_candidate (solver, &c, 2, lits))
        PUSH_STACK (candidates, c);
      if (SIZE_STACK (candidates) > max_candidates) {
        too_many = true;
        break;
      }
    }
  }
  for (all_clauses (c)) {
    if (too_many)
      break;
    if (c->garbage || c->redundant || c->size > max_size)
      continue;
    gauss_candidate cand;
    if (make_candidate (solver, &cand, c->size, c->lits))
      PUSH_STACK (candidates, cand);
    if (SIZE_STACK (candidates) > max_candidates)
      too_many = true;
  }
  if (too_many) {
    kissat_verbose (solver,
                    "gauss: skipping, more than %zu candidate clauses "
                    "(%.2f seconds)",
                    max_candidates, kissat_process_time () - started);
    RELEASE_STACK (candidates);
    return 0;
  }
  const size_t num_candidates = SIZE_STACK (candidates);
  qsort (BEGIN_STACK (candidates), num_candidates, sizeof (gauss_candidate),
         compare_candidates);
  // Grupos completos (Lema 0) y reducción por los valores de la raíz.
  unsigneds rows, starts, sizes, parities;
  INIT_STACK (rows);
  INIT_STACK (starts);
  INIT_STACK (sizes);
  INIT_STACK (parities);
  const value *const values = solver->values;
  bool trivial_conflict = false;
  for (size_t i = 0; i != num_candidates;) {
    const gauss_candidate *first = &PEEK_STACK (candidates, i);
    size_t j = i;
    unsigned distinct = 0, q = parity_of (first->signs);
    bool same_parity = true;
    while (j != num_candidates) {
      const gauss_candidate *c = &PEEK_STACK (candidates, j);
      if (c->size != first->size ||
          memcmp (c->vars, first->vars, first->size * sizeof (unsigned)))
        break;
      if (j == i || c->signs != PEEK_STACK (candidates, j - 1).signs) {
        distinct++;
        if (parity_of (c->signs) != q)
          same_parity = false;
      }
      j++;
    }
    if (same_parity && distinct == 1u << (first->size - 1)) {
      unsigned parity = 1u ^ q, size = 0;
      const unsigned start = SIZE_STACK (rows);
      for (unsigned k = 0; k != first->size; k++) {
        const unsigned idx = first->vars[k];
        const value v = values[LIT (idx)];
        if (v)
          parity ^= (v > 0);
        else {
          PUSH_STACK (rows, idx);
          size++;
        }
      }
      if (size) {
        PUSH_STACK (starts, start);
        PUSH_STACK (sizes, size);
        PUSH_STACK (parities, parity);
      } else if (parity)
        trivial_conflict = true; // la búsqueda lo encuentra por propagación
    }
    i = j;
  }
  RELEASE_STACK (candidates);
  int res = 0;
  const unsigned num_rows = SIZE_STACK (sizes);
  if (!num_rows || trivial_conflict) {
    kissat_verbose (solver, "gauss: no XOR rows to eliminate (%.2f seconds)",
                    kissat_process_time () - started);
    RELEASE_STACK (rows);
    RELEASE_STACK (starts);
    RELEASE_STACK (sizes);
    RELEASE_STACK (parities);
    return 0;
  }
  // Componentes conexas (research/09, Lema 6): dos filas están en la misma
  // si comparten variable.  El sistema es inconsistente si y solo si lo es
  // alguna componente, así que cada una se elimina por separado y la
  // memoria la marca la mayor, no el total.
  unsigned *parent = kissat_nalloc (solver, VARS, sizeof (unsigned));
  unsigned *column = kissat_nalloc (solver, VARS, sizeof (unsigned));
  for (unsigned idx = 0; idx != VARS; idx++)
    parent[idx] = column[idx] = INVALID_IDX;
  unsigned num_columns = 0;
  for (all_stack (unsigned, idx, rows))
    if (parent[idx] == INVALID_IDX)
      parent[idx] = idx, num_columns++;
  for (unsigned r = 0; r != num_rows; r++) {
    const unsigned *vars = BEGIN_STACK (rows) + PEEK_STACK (starts, r);
    const unsigned a = gauss_find (parent, vars[0]);
    for (unsigned k = 1; k != PEEK_STACK (sizes, r); k++) {
      const unsigned b = gauss_find (parent, vars[k]);
      if (a != b)
        parent[b] = a;
    }
  }
  // Filas agrupadas por componente (orden estable de primera aparición).
  unsigned *comp_of_root = column; // reutilizado; se restaura más abajo
  unsigned num_components = 0;
  unsigned *row_comp = kissat_nalloc (solver, num_rows, sizeof (unsigned));
  for (unsigned r = 0; r != num_rows; r++) {
    const unsigned *vars = BEGIN_STACK (rows) + PEEK_STACK (starts, r);
    const unsigned root = gauss_find (parent, vars[0]);
    if (comp_of_root[root] == INVALID_IDX)
      comp_of_root[root] = num_components++;
    row_comp[r] = comp_of_root[root];
  }
  for (unsigned idx = 0; idx != VARS; idx++)
    column[idx] = INVALID_IDX;
  unsigned *comp_start =
      kissat_calloc (solver, num_components + 1, sizeof (unsigned));
  for (unsigned r = 0; r != num_rows; r++)
    comp_start[row_comp[r] + 1]++;
  for (unsigned c = 0; c != num_components; c++)
    comp_start[c + 1] += comp_start[c];
  unsigned *comp_rows = kissat_nalloc (solver, num_rows, sizeof (unsigned));
  {
    unsigned *fill = kissat_nalloc (solver, num_components, sizeof (unsigned));
    memcpy (fill, comp_start, num_components * sizeof (unsigned));
    for (unsigned r = 0; r != num_rows; r++)
      comp_rows[fill[row_comp[r]]++] = r;
    kissat_dealloc (solver, fill, num_components, sizeof (unsigned));
  }
  kissat_dealloc (solver, row_comp, num_rows, sizeof (unsigned));
  // Estimaciones en coma flotante solo para decidir si se intenta: no
  // cambian ninguna decisión de la búsqueda.  El presupuesto de trabajo es
  // común a todas las componentes; la memoria se limita por componente.
  const uint64_t max_bits = (uint64_t) GET_OPTION (gaussbits) * 1000000u;
  double budget = 1e6 * GET_OPTION (gaussops);
  unsigned rank_total = 0, skipped = 0, skipped_rows = 0, skipped_columns = 0;
  unsigned largest = 0;
  unsigneds certificate;
  INIT_STACK (certificate);
  // X1s: solo si 'kissat_lucky' la va a usar antes del preproceso.
  const bool x1s = GET_OPTION (gausslucky) && GET_OPTION (lucky) &&
                   GET_OPTION (luckyearly);
  value *sigma = x1s ? kissat_calloc (solver, VARS, sizeof (value)) : 0;
  double x1s_time = 0;
  unsigneds colvars;
  INIT_STACK (colvars);
  for (unsigned c = 0; c != num_components && EMPTY_STACK (certificate); c++) {
    const unsigned *crow = comp_rows + comp_start[c];
    const unsigned n = comp_start[c + 1] - comp_start[c];
    if (n > largest)
      largest = n;
    unsigned m = 0; // columnas locales
    CLEAR_STACK (colvars);
    for (unsigned i = 0; i != n; i++) {
      const unsigned *vars = BEGIN_STACK (rows) + PEEK_STACK (starts, crow[i]);
      for (unsigned k = 0; k != PEEK_STACK (sizes, crow[i]); k++)
        if (column[vars[k]] == INVALID_IDX) {
          column[vars[k]] = m++;
          if (x1s)
            PUSH_STACK (colvars, vars[k]);
        }
    }
    const uint64_t words = ((uint64_t) m + 1 + n + 63) / 64;
    const uint64_t bits = words * 64 * n;
    const double ops = (double) m * n * words;
    if (bits > max_bits || ops > budget) {
      skipped++, skipped_rows += n, skipped_columns += m;
    } else {
      budget -= ops;
      uint64_t *matrix = kissat_nalloc (solver, n * words, 8);
      memset (matrix, 0, n * words * 8);
      uint64_t **R = kissat_nalloc (solver, n, sizeof (uint64_t *));
      for (unsigned i = 0; i != n; i++) {
        const unsigned r = crow[i];
        uint64_t *row = R[i] = matrix + i * words;
        const unsigned *vars = BEGIN_STACK (rows) + PEEK_STACK (starts, r);
        for (unsigned k = 0; k != PEEK_STACK (sizes, r); k++) {
          const unsigned col = column[vars[k]];
          row[col / 64] ^= (uint64_t) 1 << (col % 64);
        }
        if (PEEK_STACK (parities, r))
          row[m / 64] |= (uint64_t) 1 << (m % 64);
        const uint64_t h = (uint64_t) m + 1 + i;
        row[h / 64] |= (uint64_t) 1 << (h % 64);
      }
      unsigned rank = 0;
      unsigned *pivcol = x1s ? kissat_nalloc (solver, n, sizeof (unsigned)) : 0;
      for (unsigned col = 0; col != m && rank != n; col++) {
        const unsigned w = col / 64;
        const uint64_t bit = (uint64_t) 1 << (col % 64);
        unsigned pivot = rank;
        while (pivot != n && !(R[pivot][w] & bit))
          pivot++;
        if (pivot == n)
          continue;
        uint64_t *tmp = R[pivot];
        R[pivot] = R[rank];
        R[rank] = tmp;
        const uint64_t *piv = R[rank];
        for (unsigned i = rank + 1; i != n; i++) {
          uint64_t *row = R[i];
          if (row[w] & bit)
            for (uint64_t k = w; k != words; k++)
              row[k] ^= piv[k];
        }
        if (pivcol)
          pivcol[rank] = col;
        rank++;
      }
      rank_total += rank;
      const uint64_t *inconsistent = 0;
      for (unsigned i = rank; !inconsistent && i != n; i++)
        if (R[i][m / 64] & ((uint64_t) 1 << (m % 64)))
          inconsistent = R[i];
      if (inconsistent) {
        for (unsigned i = 0; i != n; i++) {
          const uint64_t h = (uint64_t) m + 1 + i;
          if (inconsistent[h / 64] & ((uint64_t) 1 << (h % 64)))
            PUSH_STACK (certificate, crow[i]);
        }
        // Comprobación independiente: la suma de las filas de S es 0 = 1.
        unsigned char *mark = kissat_calloc (solver, m, 1);
        unsigned sum_parity = 0, odd = 0;
        for (all_stack (unsigned, r, certificate)) {
          sum_parity ^= PEEK_STACK (parities, r);
          const unsigned *vars = BEGIN_STACK (rows) + PEEK_STACK (starts, r);
          for (unsigned k = 0; k != PEEK_STACK (sizes, r); k++)
            mark[column[vars[k]]] ^= 1;
        }
        for (unsigned col = 0; col != m; col++)
          odd += mark[col];
        kissat_dealloc (solver, mark, m, 1);
        if (odd || !sum_parity)
          kissat_fatal ("gauss: invalid certificate (internal error)");
      } else if (pivcol) {
        const double t = kissat_process_time ();
        gauss_back_substitute (solver, R, rank, pivcol, m,
                               BEGIN_STACK (colvars), INITIAL_PHASE, sigma);
        x1s_time += kissat_process_time () - t;
      }
      if (pivcol)
        kissat_dealloc (solver, pivcol, n, sizeof (unsigned));
      kissat_dealloc (solver, R, n, sizeof (uint64_t *));
      kissat_dealloc (solver, matrix, n * words, 8);
    }
    for (unsigned i = 0; i != n; i++) { // columnas locales a su estado
      const unsigned *vars = BEGIN_STACK (rows) + PEEK_STACK (starts, crow[i]);
      for (unsigned k = 0; k != PEEK_STACK (sizes, crow[i]); k++)
        column[vars[k]] = INVALID_IDX;
    }
  }
  kissat_very_verbose (solver,
                       "gauss: %u components, the largest with %u rows",
                       num_components, largest);
  if (!EMPTY_STACK (certificate)) {
    uint64_t fresh = 0;
    if (solver->proof)
      fresh = emit_proof (solver, &rows, &starts, &sizes, &parities,
                          &certificate);
    kissat_message (solver,
                    "gauss: refuted %u XOR rows over %u variables "
                    "(certificate of %zu rows, %" PRIu64
                    " extension variables in the proof, %.2f seconds)",
                    num_rows, num_columns, SIZE_STACK (certificate), fresh,
                    kissat_process_time () - started);
    solver->inconsistent = true;
    res = 20;
  } else if (skipped)
    kissat_verbose (solver,
                    "gauss: skipping %u rows over %u variables "
                    "(%u of %u components over the limits, %.2f seconds)",
                    skipped_rows, skipped_columns, skipped, num_components,
                    kissat_process_time () - started);
  else {
    kissat_verbose (solver,
                    "gauss: %u XOR rows over %u variables are consistent "
                    "(rank %u, %.2f seconds)",
                    num_rows, num_columns, rank_total,
                    kissat_process_time () - started);
    if (sigma) {
      // σ completa: la raíz en las fijadas, la fase inicial fuera del sistema.
      const double t = kissat_process_time ();
      for (unsigned idx = 0; idx != VARS; idx++) {
        const value v = values[LIT (idx)];
        if (v)
          sigma[idx] = v;
        else if (!sigma[idx])
          sigma[idx] = INITIAL_PHASE;
      }
      size_t checked;
      const bool all = gauss_satisfies_all (solver, sigma, &checked);
      x1s_time += kissat_process_time () - t;
      if (all) {
        kissat_message (solver,
                        "gauss: solution of %u XOR rows over %u variables "
                        "satisfies all %zu clauses (%.2f seconds)",
                        num_rows, num_columns, checked, x1s_time);
        solver->gauss_model = sigma;
        sigma = 0;
      } else
        kissat_verbose (solver,
                        "gauss: solution of %u XOR rows over %u variables "
                        "falsifies a clause (%.2f seconds)",
                        num_rows, num_columns, x1s_time);
    }
  }
  if (sigma)
    kissat_dealloc (solver, sigma, VARS, sizeof (value));
  RELEASE_STACK (colvars);
  RELEASE_STACK (certificate);
  kissat_dealloc (solver, comp_rows, num_rows, sizeof (unsigned));
  kissat_dealloc (solver, comp_start, num_components + 1, sizeof (unsigned));
  kissat_dealloc (solver, parent, VARS, sizeof (unsigned));
  if (column)
    kissat_dealloc (solver, column, VARS, sizeof (unsigned));
  RELEASE_STACK (rows);
  RELEASE_STACK (starts);
  RELEASE_STACK (sizes);
  RELEASE_STACK (parities);
  return res;
}

#else

/* Sin 'configure --gauss' esta unidad no aporta nada al binario. */
typedef int kissat_gauss_disabled;

#endif
