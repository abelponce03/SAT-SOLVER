#ifndef _bandit_trace_hpp_INCLUDED
#define _bandit_trace_hpp_INCLUDED

// ---------------------------------------------------------------------------
// Instrumentación ligera para el proyecto SAT Competition 2027 (Fase 0.5).
//
// NO forma parte del CaDiCaL original. Vuelca una traza CSV de los eventos de
// restart y rephase con las señales que observará la futura política de
// reset adaptativa (bandit): glue fast/slow EMA, nivel, reuso de trail, modo.
//
// Activación: variable de entorno CADICAL_TRACE=<fichero>. Si no está definida,
// la sobrecarga es una única lectura de getenv por corrida (cero coste en el
// bucle de búsqueda). Es aditiva: no cambia ninguna decisión del solver.
// ---------------------------------------------------------------------------

#include <cstdio>
#include <cstdlib>

namespace CaDiCaL {

inline FILE *bandit_trace_file () {
  static bool tried = false;
  static FILE *file = nullptr;
  if (!tried) {
    tried = true;
    const char *path = getenv ("CADICAL_TRACE");
    if (path) {
      file = fopen (path, "w");
      if (file)
        fprintf (file,
                 "event,conflicts,restarts,level,cum_reusedlevels,"
                 "glue_fast,glue_slow,stable,rephase_total,rephase_type,"
                 "learned,decisions\n");
    }
  }
  return file;
}

} // namespace CaDiCaL

#endif
