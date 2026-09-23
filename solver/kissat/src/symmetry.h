/* [SOLVER] Ruptura de simetrías integrada en el binario (LabeSAT, D-016,
   fase 1; ADR-0007).

   Con 'configure --symmetry', satsuma (vendorizado en solver/satsuma) se
   compila dentro de Kissat.  Antes de leer la CNF, la aplicación lo ejecuta
   en un proceso hijo con los mismos argumentos que usaba el guion
   solver/labesat:

     satsuma fix <cnf> --silent --full-skip-limit 100000000
             --add-reduced-as-unit --bsr --out-file <tmp> [--proof-file <p>]

   Si termina bien, Kissat resuelve la CNF simplificada y continúa la prueba
   SR de satsuma ('--append-proof' implícito).  Si falla, se pasa del tope o
   la entrada es demasiado grande, se resuelve la CNF original con una prueba
   DRAT desde cero: la misma semántica que solver/labesat.

   Topes (los mismos nombres que en solver/labesat):
     LABESAT_SYMM_TIMEOUT   segundos máximos para satsuma (60)
     LABESAT_SYMM_MAXBYTES  tamaño máximo de la CNF sin comprimir (512 MiB)
   Diagnóstico: con LABESAT_SYMM_KEEP=1 no se borra el directorio temporal
   (la CNF simplificada queda en <dir>/sb.cnf y la ruta sale por stderr).

   Sin 'configure --symmetry' todo esto compila a nada y la opción
   '--symmetry' da un error.  */

#ifndef _symmetry_h_INCLUDED
#define _symmetry_h_INCLUDED

#include <stdbool.h>

typedef struct symmetry_outcome symmetry_outcome;

struct symmetry_outcome {
  bool applied;      /* se resuelve la CNF simplificada */
  double seconds;    /* tiempo de pared del paso de satsuma */
  char path[4200];   /* CNF simplificada (si 'applied') */
  char dir[4096];    /* directorio temporal ('' si no hay) */
  char reason[256];  /* resumen o motivo de no aplicarla */
};

bool kissat_symmetry_compiled (void);

/* 'proof' puede ser nulo.  'budget' es el tiempo de pared que queda para
   todo el solver (<= 0: sin límite); el paso de satsuma nunca lo excede. */
void kissat_symmetry_preprocess (const char *input, const char *proof,
                                 double budget, symmetry_outcome *);

/* Borra los temporales (una vez leída la CNF simplificada). */
void kissat_symmetry_cleanup (symmetry_outcome *);

#endif
