# EXP-004 — B3″: que `kissat_lucky` ceda el control al límite de presupuesto

- **Estado**: implementado y verificado · A/B de no-regresión en ejecución
- **Fecha**: 2026-09-22
- **Origen**: hallazgo lateral de [EXP-001](EXP-001-diversidad-intrinseca-kissat.md), superviviente del cierre de [EXP-003](EXP-003-validacion-luckyminvars.md)
- **Naturaleza**: **corrección de un fallo**, no una mejora heurística. Se documenta aparte precisamente por eso.

---

## 1. El fallo

`kissat_lucky` es la única rutina larga de Kissat **sin comprobaciones de
terminación**. Todas las demás (`backbone`, `congruence`, `eliminate`, `sweep`,
`vivify`, `walk`, `transitive`, `factor`…) tienen sus `TERMINATED (…)`
repartidos por sus bucles; `lucky` no tenía ninguno, y ni siquiera bits
asignados en `src/terminate.h`.

Consecuencia medida sobre una instancia de 3.56 M variables y 7.12 M cláusulas
(`baseball-lineup`, Main Track 2026):

| límite pedido | tiempo real hasta terminar | exceso |
|---:|---:|---:|
| `--time=30` | 348.5 s | **11.6×** |
| `--time=60` | 356.5 s | 5.9× |

El solver ejecuta `kissat_lucky` **dos veces** (`luckyearly` antes del
preprocesado y `luckylate` después) y cada llamada recorre todas las variables
asumiendo y propagando. Con millones de variables eso son ~175 s por llamada
durante los cuales **ningún presupuesto la detiene**: ni el de tiempo ni el de
conflictos.

### Por qué importa más allá de la estética

1. **Rompe la medición.** Cualquiera que mida Kissat con presupuesto acotado
   —nosotros, y los organizadores de la competición— obtiene corridas que se
   pasan del límite. En nuestro harness disparó la guarda externa y produjo un
   `HARDKILL` contado como no resuelta.
2. **Bloquea A4.** Un mecanismo de reparto adaptativo de presupuesto entre
   configuraciones necesita que el solver **ceda el control en la frontera del
   turno**. Con 350 s de latencia, no cede.
3. **Es un fallo de upstream**, reportable y útil para terceros.

## 2. La corrección

Se sigue exactamente el patrón que upstream ya usa en el resto de rutinas
largas: bits propios en `src/terminate.h` y una comprobación `TERMINATED` en
cada bucle, que al dispararse **retrocede a nivel 0** y devuelve "no resuelto".

| fichero | cambio |
|---|---|
| `src/terminate.h` | 6 bits nuevos: `lucky_terminated_1..6` |
| `src/lucky.c` | `#include "terminate.h"` + una comprobación en cada uno de los 6 bucles |

El cuidado está en los **dos bucles en línea** de `kissat_lucky` (los que
asignan todas las variables a verdadero o a falso). Salir a mitad deja la
fórmula parcialmente asignada, de modo que los `assert (!solver->unassigned)`
que siguen **no se cumplirían**. Por eso la salida por terminación retrocede a
nivel 0 y se salta el `res = 10`, en lugar de simplemente romper el bucle.

En los cuatro ayudantes (`forward_false`, `forward_true`, `backward_false`,
`backward_true`) la salida por terminación reutiliza el camino que ya existía
para el caso de inconsistencia: `kissat_backtrack_without_updating_phases
(solver, 0); return 0;`.

Diff contra upstream: **68 líneas en 2 ficheros**.

## 3. Verificación

### 3.1 El límite ahora se respeta

Misma instancia, mismo binario recompilado:

| límite | antes | después | exceso |
|---:|---:|---:|---:|
| `--time=20` | ~355 s | **20.8 s** | +0.8 s (1.0×) |
| `--time=30` | 348.5 s | **30.6 s** | +0.6 s (1.0×) |
| `--time=60` | 356.5 s | **60.9 s** | +0.9 s (1.0×) |

La latencia de terminación baja de **318 s a menos de 1 s**.

### 3.2 Sin terminación, el comportamiento es idéntico

Es la comprobación que de verdad importa: el parche debe ser un **no-op** cuando
no se agota el presupuesto.

| instancia | conflictos antes | conflictos después |
|---|---:|---:|
| `php_8_7` (seed 7) | 2592 | **2592** |
| `rand3_160_s2` (seed 7) | 12203 | **12203** |
| `rand3_120_s1` (seed 7) | 1457 | **1457** |
| `ntil/e305def3…` (seed 1, 306 vars) | 2 631 330 | **2 631 330** |

El último es el caso interesante: es la instancia que hizo fracasar a B3′
(EXP-003), la que **solo se resuelve gracias a las fases lucky**. Reproduce el
recuento de conflictos de EXP-003 **exactamente**, y sigue resolviéndose con
modelo verificado.

> Nota de método: en la primera comparación esa instancia dio 994 625
> conflictos en vez de 2 631 330 y pareció un cambio de comportamiento. No lo
> era: el harness pasa `--seed=1` y la prueba manual usaba la semilla por
> defecto (0). Queda anotado porque una discrepancia así, dada por buena, habría
> «demostrado» una regresión inexistente — o peor, tapado una real.

### 3.3 Corrección bajo asertos y sanitizers

El camino nuevo (terminar **dentro** de `kissat_lucky` y retroceder) se ejerció
a propósito con `--time=25` sobre la instancia grande:

- build `--debug` (con asertos y comprobación de propagación): termina limpio,
  `s UNKNOWN`, sin abortar ningún aserto;
- build `--sanitize` (ASan + UBSan): **0 errores**.

### 3.4 Suite de no-regresión

`./scripts/smoke_test.sh` completa en verde: 869 tests de Kissat, los 10
estados esperados de `bench/smoke`, modelos SAT verificados, **pruebas DRAT
verificadas con drat-trim** y determinismo con semilla fija.

### 3.5 A/B de PAR-2

Aunque el parche sea un no-op sin terminación, la regla del repositorio es que
nada toca el solver sin A/B (CONTRIBUTING §1). Se corre sobre `bench/calib` y
`bench/calib2` contra las corridas de EXP-001.

**Expectativa declarada de antemano**: PAR-2 **neutro**. Esto no es una mejora
heurística; la única diferencia de resultado posible es que una corrida que
antes se pasaba del límite y moría por la guarda externa ahora pare limpiamente
dentro del presupuesto — en ambos casos cuenta como no resuelta.

_Resultados pendientes._

## 4. Qué NO es esto

No es una mejora de PAR-2 y no se va a presentar como tal. Es infraestructura:
hace que el presupuesto signifique lo que dice, que es condición previa para
poder construir A4 encima.

## 5. Reportar a upstream

El fallo merece un issue en https://github.com/arminbiere/kissat con la
reproducción de §1 y el parche de §2. **Pendiente de que lo revise el autor del
repositorio antes de enviarlo**: es un mensaje público en su nombre.
