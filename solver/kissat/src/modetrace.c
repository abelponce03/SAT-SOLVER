#include "modetrace.h"
#include "internal.h"

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

/* [SOLVER] Tiempo de CPU con clock(), de C99, y NO con 'kissat_process_time':
   esa función se compila fuera en builds '--quiet', que es justo la
   configuración de entrega ('--competition' = '--no-options --quiet'), y el
   módulo dejaba de enlazar.  Lo cazó el trabajo `entrega` de la CI.  */

static double modetrace_cpu_seconds (void) {
  return (double) clock () / CLOCKS_PER_SEC;
}

static FILE *modetrace_file;
static uint64_t modetrace_phase;
static uint64_t modetrace_conflicts;
static uint64_t modetrace_decisions;
static uint64_t modetrace_ticks;
static uint64_t modetrace_learned;

void kissat_init_modetrace (struct kissat *solver) {
  const char *path = getenv ("KISSAT_TRACE");
  if (!path || !*path)
    return;
  modetrace_file = fopen (path, "w");
  if (!modetrace_file)
    return;
  fputs ("phase,mode,d_conflicts,d_decisions,d_ticks,d_learned,glr,time\n",
         modetrace_file);
  modetrace_phase = 0;
  modetrace_conflicts = solver->statistics.conflicts;
  modetrace_decisions = solver->statistics.decisions;
  modetrace_ticks = solver->statistics.search_ticks;
  modetrace_learned = solver->statistics.clauses_learned;
}

void kissat_modetrace_switch (struct kissat *solver) {
  if (!modetrace_file)
    return;

  const statistics *s = &solver->statistics;
  const uint64_t d_conflicts = s->conflicts - modetrace_conflicts;
  const uint64_t d_decisions = s->decisions - modetrace_decisions;
  const uint64_t d_ticks = s->search_ticks - modetrace_ticks;
  const uint64_t d_learned = s->clauses_learned - modetrace_learned;

  /* GLR = cláusulas aprendidas por decisión.  Se usa 'conflicts' y no
     'clauses_learned' como numerador en el análisis porque el segundo solo
     se actualiza en builds con estadísticas; aquí se escriben los dos y el
     análisis decide.  */
  const double glr = d_decisions ? (double) d_conflicts / d_decisions : 0.0;

  fprintf (modetrace_file,
           "%" PRIu64 ",%s,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
           ",%.6f,%.2f\n",
           modetrace_phase++, solver->stable ? "stable" : "focused",
           d_conflicts, d_decisions, d_ticks, d_learned, glr,
           modetrace_cpu_seconds ());
  fflush (modetrace_file);

  modetrace_conflicts = s->conflicts;
  modetrace_decisions = s->decisions;
  modetrace_ticks = s->search_ticks;
  modetrace_learned = s->clauses_learned;
}

void kissat_close_modetrace (struct kissat *solver) {
  (void) solver;
  if (!modetrace_file)
    return;
  fclose (modetrace_file);
  modetrace_file = 0;
}
