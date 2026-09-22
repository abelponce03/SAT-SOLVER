#include "bump.h"
#include "decide.h"
#include "inline.h"
#include "print.h"
#include "report.h"
#include "resources.h"
#include "restart.h"
#include "modetrace.h"   /* [SOLVER] A4 paso 0 */

#include <inttypes.h>

#ifndef QUIET

static const char *mode_string (kissat *solver) {
  return solver->stable ? "stable" : "focused";
}

#endif

/*------------------------------------------------------------------------*/
/* [SOLVER] A4 — reparto adaptativo del presupuesto entre los dos modos.

   Upstream reparte a ciegas: al entrar en 'stable' le da tantos ticks como
   consumió el 'focused' anterior, y al entrar en 'focused' una progresión
   creciente fijada de antemano.  Ningún término mira si el modo está
   progresando.  Esto no cambia el MECANISMO, solo la POLÍTICA.

   Señal y su justificación empírica (EXP-005 paso 0, 48 trazas y 1660 fases
   de instancias reales del Main Track 2026):

   - La recompensa es "esta fase ha superado al EMA del PROPIO brazo", no el
     nivel absoluto del GLR.  El nivel no solo no discrimina: se INVIERTE
     (las corridas estancadas tienen GLR más alto; Δ = -0.209, p = 0.062),
     mientras que la tendencia sí separa (Δ pendiente = +0.568, p = 0.022).
     Una recompensa "más GLR = mejor" sería activamente errónea.

   - El EMA es POR BRAZO porque los dos viven en escalas distintas:
     stable 0.810 de GLR mediano frente a focused 0.462, un 75 % más.  Con un
     EMA común, 'stable' ganaría por construcción y el bandit dejaría morir de
     hambre al 'focused', no por peor sino por estar en otra escala.

   - El factor está ACOTADO entre x0.5 y x2 del presupuesto que upstream daría.
     Es deliberado: convierte el cambio en una perturbación acotada de una
     política que ya funciona, en lugar de una política nueva sin garantías.

   Todo en aritmética entera por milésimas: determinista y portable, sin
   depender de cómo redondee cada compilador.  */

#define ADAPTIVE_SCALE 1000u
#define ADAPTIVE_NEUTRAL 500u /* tasa de éxito que deja el presupuesto intacto */

static unsigned adaptive_arm_index (kissat *solver) {
  return solver->stable ? 1 : 0;
}

void kissat_adaptive_finish_phase (kissat *solver) {
  mode *mode = &solver->mode;
  statistics *statistics = &solver->statistics;

  const uint64_t d_conflicts = statistics->conflicts - mode->adaptive_conflicts;
  const uint64_t d_decisions = statistics->decisions - mode->adaptive_decisions;

  mode->adaptive_conflicts = statistics->conflicts;
  mode->adaptive_decisions = statistics->decisions;

  if (!GET_OPTION (modeadaptive))
    return;
  if (!d_decisions)
    return; /* fase vacía: no informa de nada */

  adaptive_arm *arm = mode->arm + adaptive_arm_index (solver);
  const uint64_t glr = (d_conflicts * ADAPTIVE_SCALE) / d_decisions;
  const uint64_t decay = GET_OPTION (modeadaptivedecay);

  if (!arm->seeded) {
    /* La primera fase de cada brazo solo siembra su EMA: sin historial no hay
       "mejor que antes" que medir.  */
    arm->ema_glr = glr;
    arm->ema_success = ADAPTIVE_NEUTRAL;
    arm->seeded = true;
    return;
  }

  const uint64_t reward = (glr > arm->ema_glr) ? ADAPTIVE_SCALE : 0;
  arm->ema_glr = (decay * arm->ema_glr +
                  (ADAPTIVE_SCALE - decay) * glr) / ADAPTIVE_SCALE;
  arm->ema_success = (decay * arm->ema_success +
                      (ADAPTIVE_SCALE - decay) * reward) / ADAPTIVE_SCALE;

  kissat_very_verbose (solver,
                       "adaptive %s phase glr %.3f ema %.3f -> %s "
                       "(success rate %.1f%%)",
                       mode_string (solver), glr / (double) ADAPTIVE_SCALE,
                       arm->ema_glr / (double) ADAPTIVE_SCALE,
                       reward ? "reward" : "no reward",
                       arm->ema_success * 100.0 / ADAPTIVE_SCALE);
}

/* Factor por milésimas en [500, 2000] a aplicar al presupuesto que upstream
   daría al brazo en el que estamos ENTRANDO.  Centrado en 1000 (sin cambio)
   para una tasa de éxito del 50 %: por encima se premia hasta duplicar, por
   debajo se castiga hasta la mitad, nunca más -- ese suelo es la exploración:
   un brazo con mala racha conserva turno suficiente para demostrar lo
   contrario más tarde.  */

static uint64_t adaptive_factor (kissat *solver) {
  if (!GET_OPTION (modeadaptive))
    return ADAPTIVE_SCALE;

  const adaptive_arm *arm = solver->mode.arm + adaptive_arm_index (solver);
  if (!arm->seeded)
    return ADAPTIVE_SCALE;

  const uint64_t gain = GET_OPTION (modeadaptivegain);
  const uint64_t s = arm->ema_success;
  uint64_t factor;

  if (s >= ADAPTIVE_NEUTRAL)
    factor = ADAPTIVE_SCALE + (2 * (s - ADAPTIVE_NEUTRAL) * gain) / ADAPTIVE_SCALE;
  else
    factor = ADAPTIVE_SCALE - ((ADAPTIVE_NEUTRAL - s) * gain) / ADAPTIVE_SCALE;

  if (factor < ADAPTIVE_SCALE / 2)
    factor = ADAPTIVE_SCALE / 2;
  if (factor > 2 * ADAPTIVE_SCALE)
    factor = 2 * ADAPTIVE_SCALE;
  return factor;
}

static uint64_t adaptive_budget (kissat *solver, uint64_t base) {
  const uint64_t factor = adaptive_factor (solver);
  if (factor == ADAPTIVE_SCALE)
    return base;
  uint64_t scaled = (base * factor) / ADAPTIVE_SCALE;
  if (!scaled)
    scaled = 1; /* nunca un turno vacío */
  kissat_very_verbose (solver, "adaptive %s budget %s -> %s (factor %.3f)",
                       mode_string (solver), FORMAT_COUNT (base),
                       FORMAT_COUNT (scaled), factor / (double) ADAPTIVE_SCALE);
  return scaled;
}

/*------------------------------------------------------------------------*/

void kissat_init_mode_limit (kissat *solver) {
  kissat_init_modetrace (solver);   /* [SOLVER] A4 paso 0 */

  /* [SOLVER] A4: estado del reparto adaptativo, explícito y no por confianza
     en que la estructura llegue a cero.  */
  solver->mode.adaptive_conflicts = solver->statistics.conflicts;
  solver->mode.adaptive_decisions = solver->statistics.decisions;
  for (unsigned i = 0; i < KISSAT_ADAPTIVE_ARMS; i++) {
    solver->mode.arm[i].ema_glr = 0;
    solver->mode.arm[i].ema_success = ADAPTIVE_NEUTRAL;
    solver->mode.arm[i].seeded = false;
  }

  limits *limits = &solver->limits;

  if (GET_OPTION (stable) == 1) {
    assert (!solver->stable);

    const uint64_t conflicts_delta = GET_OPTION (modeinit);
    const uint64_t conflicts_limit = CONFLICTS + conflicts_delta;

    assert (conflicts_limit);

    limits->mode.conflicts = conflicts_limit;
    limits->mode.ticks = 0;
    limits->mode.count = 0;

    kissat_very_verbose (solver,
                         "initial %s mode switching limit "
                         "at %s after %s conflicts",
                         mode_string (solver),
                         FORMAT_COUNT (conflicts_limit),
                         FORMAT_COUNT (conflicts_delta));

    solver->mode.ticks = solver->statistics.search_ticks;
#ifndef QUIET
    solver->mode.conflicts = CONFLICTS;
#ifdef METRICS
    solver->mode.propagations = solver->statistics.search_propagations;
#endif
    // clang-format off
      solver->mode.entered = kissat_process_time ();
      kissat_very_verbose (solver,
        "starting %s mode at %.2f seconds "
        "(%" PRIu64 " conflicts, %" PRIu64 " ticks"
#ifdef METRICS
	", %" PRIu64 " propagations, %" PRIu64 " visits"
#endif
	")", mode_string (solver),
        solver->mode.entered, solver->mode.conflicts, solver->mode.ticks
#ifdef METRICS
        , solver->mode.propagations, solver->mode.visits
#endif
	);
// clang-format on
#endif
  } else
    kissat_very_verbose (solver,
                         "no need to set mode limit (only %s mode enabled)",
                         mode_string (solver));
}


static void update_mode_limit (kissat *solver, uint64_t delta_ticks) {
  kissat_init_averages (solver, &AVERAGES);

  limits *limits = &solver->limits;
  statistics *statistics = &solver->statistics;

  assert (GET_OPTION (stable) == 1);

  if (limits->mode.count & 1) {
    delta_ticks = adaptive_budget (solver, delta_ticks); /* [SOLVER] A4 */
    limits->mode.ticks = statistics->search_ticks + delta_ticks;
#ifndef QUIET
    assert (solver->stable);
    kissat_phase (solver, "stable", GET (stable_modes),
                  "new stable mode switching limit of %s "
                  "after %s ticks",
                  FORMAT_COUNT (limits->mode.ticks),
                  FORMAT_COUNT (delta_ticks));
#endif
  } else {
    assert (limits->mode.ticks);
    const uint64_t interval = GET_OPTION (modeint);
    const uint64_t count = (statistics->switched + 1) / 2;
    uint64_t scaled = interval * kissat_nlogpown (count, 4);
    scaled = adaptive_budget (solver, scaled); /* [SOLVER] A4 */
    limits->mode.conflicts = statistics->conflicts + scaled;
#ifndef QUIET
    assert (!solver->stable);
    kissat_phase (solver, "focused", GET (focused_modes),
                  "new focused mode switching limit of %s "
                  "after %s conflicts",
                  FORMAT_COUNT (limits->mode.conflicts),
                  FORMAT_COUNT (scaled));
#endif
  }

  solver->mode.ticks = statistics->search_ticks;
#ifndef QUIET
  solver->mode.conflicts = statistics->conflicts;
#ifdef METRICS
  solver->mode.propagations = statistics->search_propagations;
#endif
#endif
}

static void report_switching_from_mode (kissat *solver,
                                        uint64_t *delta_ticks) {
  statistics *statistics = &solver->statistics;
  *delta_ticks = statistics->search_ticks - solver->mode.ticks;

#ifndef QUIET
  if (kissat_verbosity (solver) < 2)
    return;

  const double current_time = kissat_process_time ();
  const double delta_time = current_time - solver->mode.entered;

  const uint64_t delta_conflicts =
      statistics->conflicts - solver->mode.conflicts;
#ifdef METRICS
  const uint64_t delta_propagations =
      statistics->search_propagations - solver->mode.propagations;
#endif
  solver->mode.entered = current_time;

  // clang-format off
  kissat_very_verbose (solver, "%s mode took %.2f seconds "
    "(%s conflicts, %s ticks"
#ifdef METRICS
    ", %s propagations"
#endif
    ")", solver->stable ? "stable" : "focused",
    delta_time, FORMAT_COUNT (delta_conflicts), FORMAT_COUNT (*delta_ticks)
#ifdef METRICS
    , FORMAT_COUNT (delta_propagations)
#endif
    );
  // clang-format on
#else
  (void) solver;
#endif
}

static void switch_to_focused_mode (kissat *solver) {
  assert (solver->stable);
  uint64_t delta;
  report_switching_from_mode (solver, &delta);
  REPORT (0, ']');
  STOP (stable);
  INC (focused_modes);
  kissat_phase (solver, "focus", GET (focused_modes),
                "switching to focused mode after %s conflicts",
                FORMAT_COUNT (CONFLICTS));
  solver->stable = false;
  update_mode_limit (solver, delta);
  START (focused);
  REPORT (0, '{');
  kissat_reset_search_of_queue (solver);
  kissat_update_focused_restart_limit (solver);
}

static void switch_to_stable_mode (kissat *solver) {
  assert (!solver->stable);
  uint64_t delta;
  report_switching_from_mode (solver, &delta);
  REPORT (0, '}');
  STOP (focused);
  INC (stable_modes);
  solver->stable = true;
  kissat_phase (solver, "stable", GET (stable_modes),
                "switched to stable mode after %" PRIu64 " conflicts",
                CONFLICTS);
  update_mode_limit (solver, delta);
  START (stable);
  REPORT (0, '[');
  kissat_init_reluctant (solver);
  kissat_update_scores (solver);
}

bool kissat_switching_search_mode (kissat *solver) {
  assert (!solver->inconsistent);

  if (GET_OPTION (stable) != 1)
    return false;

  limits *limits = &solver->limits;
  statistics *statistics = &solver->statistics;

  if (limits->mode.count & 1)
    return statistics->search_ticks >= limits->mode.ticks;
  else
    return statistics->conflicts >= limits->mode.conflicts;
}

void kissat_switch_search_mode (kissat *solver) {
  assert (kissat_switching_search_mode (solver));

  /* [SOLVER] A4: cerrar la fase que termina ANTES de voltear 'solver->stable',
     para que la recompensa vaya al brazo correcto. */
  kissat_modetrace_switch (solver);
  kissat_adaptive_finish_phase (solver);

  INC (switched);
  solver->limits.mode.count++;

  if (solver->stable)
    switch_to_focused_mode (solver);
  else
    switch_to_stable_mode (solver);

  solver->averages[solver->stable].saved_decisions = DECISIONS;

  kissat_start_random_sequence (solver);
}
