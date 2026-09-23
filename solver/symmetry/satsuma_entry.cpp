// satsuma_entry.cpp — satsuma dentro del binario de Kissat (LabeSAT, MIT).
//
// D-016, fase 1 (ADR-0007): la ruptura de simetrías de satsuma se compila
// dentro de Kissat en lugar de ejecutarse como programa aparte.  Esta unidad
// es el único punto de unión: incluye satsuma.cpp (vendorizado sin modificar
// en solver/satsuma) renombrando su 'main', y expone a C la función que hace
// lo mismo que la línea de órdenes de satsuma.
//
// Kissat la llama en un proceso hijo (src/symmetry.c), con los mismos
// argumentos que usaba el guion solver/labesat.  Así el resultado es
// idéntico al del programa externo, y un fallo, un 'exit' o un tope de tiempo
// dentro de satsuma no pueden tumbar al solver: se cae a la CNF original.

#define main labesat_satsuma_upstream_main
#include "satsuma.cpp"
#undef main

extern "C" int labesat_satsuma_main (int argc, char **argv) {
  return commandline_mode (argc, argv);
}
