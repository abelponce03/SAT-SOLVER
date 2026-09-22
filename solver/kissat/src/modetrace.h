#ifndef _modetrace_h_INCLUDED
#define _modetrace_h_INCLUDED

/* [SOLVER] A4 paso 0 — instrumento de investigación, no código de competición.

   Escribe una fila por cada cambio de modo 'stable'/'focused' con el progreso
   de la fase que termina, para poder validar la señal de recompensa del
   planificador adaptativo ANTES de escribirlo.
   Ver docs/experiments/EXP-005-a4-reparto-adaptativo.md §4.

   Se activa solo con la variable de entorno KISSAT_TRACE=<fichero>; sin ella
   el coste es una comparación de puntero por cambio de modo (uno cada decenas
   de segundos), así que el camino de competición queda intacto.

   Limitación asumida: el estado es estático de fichero, de modo que solo se
   traza UN solver por proceso.  Es suficiente para el binario stand-alone, que
   es donde se miden las trazas, y evita tocar 'struct kissat'.  */

struct kissat;

void kissat_init_modetrace (struct kissat *);
void kissat_modetrace_switch (struct kissat *);
void kissat_close_modetrace (struct kissat *);

#endif
