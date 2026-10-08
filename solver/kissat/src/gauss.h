#ifndef _gauss_h_INCLUDED
#define _gauss_h_INCLUDED

/* [SOLVER] X1 (research/09): refutación de sistemas XOR inconsistentes por
   eliminación de Gauss, con prueba DRAT con variables de extensión.
   Devuelve 20 si refuta la fórmula y 0 si no (entonces no ha cambiado nada
   del estado del solver). */

struct kissat;

int kissat_gauss (struct kissat *);
int kissat_gauss_lucky (struct kissat *);

#endif
