#ifndef _mode_h_INCLUDED
#define _mode_h_INCLUDED

#include <stdbool.h>
#include <stdint.h>

struct kissat;

typedef struct mode mode;

/* [SOLVER] A4: estado del reparto adaptativo, dos brazos.
   Índice 0 = focused, 1 = stable (coincide con 'solver->stable').

   Todo en aritmética entera por milésimas: el planificador está en el camino
   caliente del solver y debe ser determinista y portable bit a bit entre
   compiladores, cosa que los dobles no garantizan.
   Ver docs/experiments/EXP-005-a4-reparto-adaptativo.md.  */

#define KISSAT_ADAPTIVE_ARMS 2

struct adaptive_arm {
  uint64_t ema_glr;      /* EMA del GLR del brazo, en milésimas */
  uint64_t ema_success;  /* EMA de la recompensa 0/1, en milésimas */
  bool seeded;           /* la primera fase solo siembra el EMA */
};

typedef struct adaptive_arm adaptive_arm;

struct mode {
  uint64_t ticks;

  /* [SOLVER] A4: contadores al entrar en la fase actual y estado por brazo.
     Fuera de los '#ifndef QUIET' de abajo a propósito: el planificador tiene
     que funcionar en el binario '--competition', que se compila con --quiet.  */
  uint64_t adaptive_conflicts;
  uint64_t adaptive_decisions;
  adaptive_arm arm[KISSAT_ADAPTIVE_ARMS];
#ifndef QUIET
  double entered;
  uint64_t conflicts;
#ifdef METRICS
  uint64_t propagations;
  uint64_t visits;
#endif
#endif
};

void kissat_init_mode_limit (struct kissat *);
void kissat_adaptive_finish_phase (struct kissat *);   /* [SOLVER] A4 */
bool kissat_switching_search_mode (struct kissat *);
void kissat_switch_search_mode (struct kissat *);

#endif
