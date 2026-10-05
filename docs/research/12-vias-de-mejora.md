# Investigación 12 — Vías de mejora desde siete ángulos: hallazgos, lo implementado y los experimentos para la máquina local

- **Fecha**: 2026-10-05
- **Pedido del director**: «continúes el desarrollo complementando lo que ya
  se ha hecho y continuando la mejora y perfeccionamiento de LabeSAT,
  atacándolo desde varios puntos de vista […] encuentres muchas vías de
  mejora para luego ser validadas en la sesión local corriendo los conjuntos
  de benchmark correspondientes […] deja documentados los experimentos que
  se realizarán luego».
- **Punto de partida**: la cabeza del PR #32 (`a5429c7`), es decir:
  - X1, X1s y PGO + LTO adoptadas;
  - B3 descartada; B4 en EXP-023;
  - D-020 abierta: dos variantes, «siempre» y «nunca».
- **Método**:
  1. Siete ángulos, de los que salen las candidatas (§1).
  2. Lectura del código de los paquetes oficiales de 2026, **solo para
     saber qué técnica usan**. El paquete `zheng` (Kissat_MAB 4.0.2 y su
     variante SATLUTION) es MIT, con la licencia de Kissat. De `anders` y de
     cliquer no se abrió nada (sala limpia de mclique, D-005).
  3. **Análisis estático** del Kissat base:
     - `gcc -Wshadow=local`;
     - el analizador de `clang`.
  4. Datos oficiales de 2026 (`data/competition/scores_2026.csv`).
  5. Implementación de lo barato **detrás de opciones apagadas**, con la
     búsqueda idéntica cuando están a 0. En la nube solo se comprobó la
     **corrección**, no el rendimiento (CLAUDE.md §6: los experimentos van
     en la máquina local).
  6. Un preregistro por vía: EXP-024 a EXP-034.

---

## 0. Resumen

**Hallazgos** (no dependen de ningún experimento):

1. **Fallo en Kissat 4.0.4, en `eliminate.c`.**
   - Dentro del bucle de rondas, `last_round_eliminated` se vuelve a
     declarar y tapa la variable exterior, que se queda siempre en 0.
   - Al final, `complete = !remain && !last_round_eliminated` ignora lo que
     eliminó la última ronda. Además, `remain` vale siempre 0 en ese punto,
     porque el bucle libera la planificación antes de salir. Resultado:
     Kissat da **siempre** la eliminación por completa, sube la cota y
     nunca descarta candidatas.
   - Está desde la 3.1.0 (2023) y sigue en la 4.0.4, en la rama
     `development` y en sc2026.
   - Lo señaló el ciclo 6 de SATLUTION; aquí se confirma con
     `-Wshadow=local`.
   - Arreglarlo **cambia la búsqueda**, así que va detrás de una opción
     (M9, EXP-028). La conducta con el fallo es la que ganó competiciones
     de 2023 a 2026: el arreglo no es automáticamente una mejora.
2. **Otro fallo en `vivify.c`, y frecuente.** En
   `swap_first_literal_with_best_watch`, otra sombra (`value`) hace que la
   guarda del bucle no cambie nunca. Tras un literal no falso puede elegirse
   como vigilante uno falso de nivel mayor.
   - En 29 instancias de calib y calib2, a 20 000 conflictos, el **9,5 %**
     de las vivificaciones (4114 de 43 514, en 19 instancias) acaban con un
     par vigilado **peor** (menos literales no falsos) que con el arreglo.
   - Va detrás de una opción (M10), con una estadística diagnóstica que
     solo existe con `--stats`.
3. **El resto del análisis estático está limpio.** `-Wshadow=local` da 15
   sombras locales: 2 son fallos (los de arriba) y 13 son inofensivas. El
   analizador de clang da 3 avisos, los 3 falsos positivos: suponen
   `size = 0` donde un `assert` lo descarta.
4. **SATLUTION no replicó en la competición.**
   - Su `RESULTS.md` afirma −61 s de PAR-2 y +4 resueltas en su banco por
     el cambio de `probe.c` (ciclos 42 y 51).
   - En 2026, `zheng_kissat-mab-hypre-satlution` quedó **por detrás** de su
     base, `zheng_kissat-mab-hypre`: 253 frente a 255 resueltas y
     PAR-2 4066,8 frente a 3996,3 (+70 s).
   - Era una mejora medida en la misma muestra en la que se eligió (aceptación
     codiciosa con α = 0). Es justo el sesgo que el preregistro de ADR-0003
     existe para evitar, y un buen material para el artículo metodológico
     (research/07, N7). M8 lo replica fuera de muestra (EXP-029).
5. **Kissat 4.0.x ya trae el desempate estructurado de SBVA.** `factor.c`
   puntúa las candidatas por vecindad a `factorhops` = 3 saltos.
   - N5 («SBVA», research/07) no es una línea pendiente: está en la base.
   - Corrige la lectura de research/07 §4 y research/09 §6 (B1).
6. **La ruptura de satsuma y la fase inicial de Kissat tiran en direcciones
   opuestas.**
   - El predicado lex-leader de satsuma (`predicate.h`, primera cláusula
     `{-l, σ(l)}`) favorece el **falso** en las primeras variables del
     orden.
   - Kissat empieza con fase **verdadera** (`phase` = 1).
   - En CP se sabe que unas restricciones de ruptura contrarias a la
     heurística de búsqueda pueden esconder las soluciones (Gent, Harvey y
     Kelsey, 2002).
   - Encaja con el dato de D-020: de las 13 instancias de 2026 que solo
     resuelve «nunca», 10 son SAT. Es M1 (EXP-026) y no requiere código.
7. **En 2026 hubo 12 «checker-timeout» entre las entradas de cabeza**:
   - 8 de las cuatro variantes de `zheng`, con prueba VeriPB;
   - 3 de las de `oertel`;
   - 1 de `reeves`.

   El ganador no tuvo ninguno. Un UNSAT sin prueba verificada no cuenta, y
   nuestras pruebas mezclan SR, DRAT y variables de extensión de X1: M12
   (EXP-034) mide si verifican a escala y cuánto tardan.

**Lo implementado** (todo apagado por defecto, CLAUDE.md §5):

| Pieza | Dónde | Para |
|---|---|---|
| `--decayramp` | `bump.c` | M5 |
| `--eliminatefix` | `eliminate.c` | M9 |
| `--probeiterate` (y `kissat_transitive_reduction` devuelve si redujo) | `probe.c`, `transitive.c/h` | M8 |
| `--vivifywatchfix` y la estadística `vivify_watch_mismatch` (solo con `--stats`: pares vigilados peores que con el arreglo) | `vivify.c`, `statistics.h` | M10 |
| `--gaussphase` | `gauss.c` | X2 |
| Topes de satsuma: `scripts/satsuma_topes.sh` (envoltorio para `LABESAT_SATSUMA`) y `LABESAT_SYMM_ARGS` en el binario integrado | `scripts/`, `symmetry.c`, `scan_symmetry.py --satsuma-args`, `compare_satsuma_builds.py --build-args` | M2 |
| `--proof-dir-a/-b` en el arnés A/B (tamaño en `<out>.pruebas.csv`, sin tocar el CSV principal) | `run_ab_interleaved.py`, `run_experiment.py` | M11 |
| `x1b_potencial.py`: unidades y equivalencias que daría Gauss-Jordan y no ve la propagación | `scripts/` | M4 |
| `research12.py`: muestras y reglas de cribado y confirmación | `scripts/` | todas |
| `test_opciones_m.sh`: valores por defecto, búsqueda intacta y respuestas verificadas | `scripts/`, CI | todas |

**Verificación en la nube** (corrección, no rendimiento):

- Con todas las opciones a 0, los contadores son idénticos a los del
  binario de `a5429c7` en 50 de 50 instancias, a 20 000 conflictos.
- Con cada opción encendida, todas las respuestas son correctas: los
  modelos los acepta `verify_model.py` y las pruebas, `drat-trim` y los dos
  `dsr-trim`.
- `test_opciones_m.sh` pasa también bajo ASan/UBSan.

Detalle en §11.

**Los experimentos**: once preregistros (EXP-024 a EXP-034), con el orden
y el coste de §10.

- Las opciones de búsqueda usan un diseño en **dos etapas**:
  - un cribado de 40 instancias, sin contraste;
  - una confirmación con 60 instancias que el cribado no ha visto.

  Así una vía sin señal cuesta unas 3 h y no 10.
- Se proponen dos decisiones nuevas para el director:
  - **D-021**: ¿avisar a Biere del fallo de `eliminate.c`?
  - **D-022**: ¿hacer del cribado en dos etapas la norma de ADR-0003?

---

## 1. Siete ángulos

| Ángulo | Pregunta | Vías |
|---|---|---|
| A. Simetrías | La palanca de 2026: ¿se puede abaratar «siempre» o cobrar las SAT que pierde? | M1, M2, M7 |
| B. Razonamiento algebraico | ¿Queda algo de Gauss que X1 y X1s no cobren? | M4 (X1b), X2 |
| C. Heurística de búsqueda | ¿Qué ideas de los ganadores no tenemos? | M5, M6 (MAB) |
| D. Inprocesado | ¿Qué cambios de los ganadores son replicables? | M8 |
| E. Calidad del código base | ¿Hay fallos en Kissat que cambien la búsqueda? | M9, M10 |
| F. Pruebas y robustez | ¿Contarán nuestros UNSAT en 2027? | M11, M12 |
| G. Metodología | ¿Cómo medir doce vías con 4 núcleos? | M13 (cribado en dos etapas) |

## 2. Catálogo

**Evidencia previa**: A = de un ganador o de un experimento nuestro;
B = de la literatura o de un envío sin ablación; C = solo un argumento.

| # | Vía | Evidencia previa | Predicción honesta | Coste de código | Experimento |
|---|---|---|---|---|---|
| **M1** | Fase inicial falsa cuando hay ruptura (`--phase=0` con `--symmetry`) | B: CP; el dato de las SAT de D-020 | Pequeña en el total; puede notarse en las SAT simétricas | Ninguno | **EXP-026** |
| **M2** | Topes internos de satsuma (los de `zheng`: componentes, modelos de orden y densos) | A: el 3.º a 6.º de 2026 los usan | Abaratan station-repacking; no cambian la ruptura de las combinatorias | Hecho (`satsuma_topes.sh`) | **EXP-024** |
| M3 = **X2** | La solución de Gauss como fase guardada inicial | C (research/06 la descartó por ~6 s) | Nula o pequeña; ahora cuesta 0 líneas nuevas de extracción | Hecho (`--gaussphase`) | **EXP-032** (prioridad baja) |
| **M4** | X1b: unidades y equivalencias de Gauss-Jordan | C (research/09 §5) | Probablemente casi nada en la industria | Diagnóstico hecho (`x1b_potencial.py`) | **EXP-025** (determinista) |
| **M5** | Rampa del decaimiento VSIDS en modo estable (0,80 → 0,95, como Glucose) | B: Glucose; AE-Kissat-MAB evolucionó un decaimiento dinámico | Pequeña | Hecho (`--decayramp`) | **EXP-030** |
| **M6** | Bandido VSIDS/CHB (Kissat_MAB) | A: ganó 2021, 2022 y 2025 | Solo con selector (research/10 §3.2) | ~300 líneas en 12 ficheros (§5.2) | Condicionado a **D-018** |
| **M7** | Configuración `--sat` de Kissat cuando hay ruptura | B: el hueco SAT de las variantes MAB (research/10 §4) | Recupera SAT y pierde algo de UNSAT | Ninguno | **EXP-027** |
| **M8** | Congruencia y reducción transitiva otra vez tras una reducción con éxito (SATLUTION, ciclos 42 y 51) | B, en contra: no replicó en 2026 (§0.4) | Nula | Hecho (`--probeiterate`) | **EXP-029** |
| **M9** | Arreglo de la eliminación | C (es un fallo; la conducta con el fallo ganó) | Incierta: menos eliminación agresiva | Hecho (`--eliminatefix`) | **EXP-028** |
| **M10** | Arreglo del vigilante en `vivify` | C (el fallo es frecuente: 9,5 % de las vivificaciones en 19 de 29 instancias de calib) | Efecto pequeño: el vigilante falso solo estorba hasta que la vivificación retrocede | Hecho (`--vivifywatchfix`) | **EXP-031** (diagnóstico primero) |
| **M11** | Coste de escribir la prueba | — | < 3 % | Hecho (`--proof-dir-b`) | **EXP-033** |
| **M12** | Verificación de las pruebas a escala | A: 12 *checker-timeout* en 2026 | Todas verifican; el tiempo es la incógnita | Hecho | **EXP-034** |
| **M13** | Cribado en dos etapas | — | Ahorra ~60 % del cómputo en las vías nulas | Hecho (`research12.py`) | **D-022** |
| — | Calibración de los topes de memoria de satsuma con los datos de M2 | — | — | — | Dentro de EXP-024 |

## 3. Ángulo A — Simetrías

### M1. La fase inicial contra la ruptura

**Mecanismo.**

- El predicado lex-leader que añade satsuma (`predicate.h`,
  `add_lex_leader_predicate`) exige, para cada generador σ y en el orden
  global de variables, que la asignación sea lexicográficamente ≤ que su
  imagen.
  - La primera cláusula de la cadena es `{-l, σ(l)}`: si l es verdadera,
    σ(l) también.
  - La ruptura por unidades fija l a falso.
- Entre las asignaciones simétricas, la que sobrevive es la que tiene
  **falsos al principio**.
- Kissat decide con la fase inicial **verdadera** (`phase` = 1) hasta que
  guarda otra. En las primeras decisiones va hacia las asignaciones que la
  ruptura acaba de eliminar.

**Por qué puede importar.**

- En CP es un problema conocido: la ruptura estática con un orden
  contrario a la heurística de búsqueda empeora la búsqueda de soluciones
  (Gent, Harvey y Kelsey, 2002; Puget, 2005).
- En nuestros datos, «siempre» pierde sobre todo **SAT**: 10 de las 13
  instancias de 2026 que solo resuelve «nunca» (research/10 §0b).
- En UNSAT la fase importa poco: la ruptura acorta la refutación.

**Por qué puede no importar.**

- Kissat cambia de fase muy pronto: *warmup*, fases objetivo, *rephase*
  (original, invertida, mejor y *walk*).
- La fase inicial solo decide las primeras decisiones y el refaseo
  «original».

**Coste**: ninguno. `labesat` pasa `--phase=0` a Kissat. Si funciona, el
despliegue es una línea en `labesat`: añadir `--phase=0` solo cuando
satsuma se aplica.

**Experimento**: EXP-026.

### M2. Los topes internos de satsuma

- **Qué hacen ellos.** `zheng_kissat-mab-hypre` (puestos 3.º a 6.º en 2026)
  llama a satsuma con `--component-limit 500000 --order-model-limit 750000
  --dense-model-limit 20000000`. El ganador no pone ninguno, y nosotros
  tampoco (solo los topes de tiempo y de tamaño de `labesat`).
- **Qué importa.**
  - EXP-014 y EXP-009 mostraron que, en la industria, «siempre» cuesta casi
    solo el tiempo fijo de satsuma. En station-repacking, 39 s de mediana,
    casi todo en la fase de Schreier.
  - Si los topes internos lo abaratan sin quitar la ruptura de las
    combinatorias, la V1 de D-020 cuesta menos en la industria sin perder
    nada en lo simétrico.
- **Qué no sabemos.**
  - Si esos topes cortan la fase de Schreier o solo la construcción de
    predicados.
  - En `satsuma.h`, `dense_model_budget` y `order_model_budget` limitan los
    modelos de ruptura, y `graph_component_size_limit` el tamaño de
    componente del grafo.
- **Hecho**:
  - `scripts/satsuma_topes.sh` añade los topes y se pasa a `labesat` como
    `LABESAT_SATSUMA`. `solver/labesat` no se toca: EXP-023 vigila su
    SHA-1 con `--guard`.
  - `LABESAT_SYMM_ARGS` hace lo mismo en el binario integrado. Vacío por
    defecto: los argumentos de siempre.
- **Experimento**: EXP-024. Primero satsuma solo (determinista, salvo el
  reloj); el A/B, solo si cambia algo.

### M7. La configuración `--sat` cuando hay ruptura

- **El hueco.** ~20 de las 56 instancias que resuelve el top-10 de 2026 y
  nosotros no son SAT combinatorias simétricas, resueltas casi solo por las
  variantes MAB (research/10 §4).
- **La idea.** Kissat trae la configuración `--sat` (`--target=2
  --restartint=50`), pensada para SAT. Cuando satsuma rompe simetría, las
  UNSAT suelen caer pronto: si `--sat` cuesta poco en ellas y ayuda en las
  SAT, la combinación compensa.
- **El riesgo.** `--sat` en UNSAT grandes.
- **Experimento**: EXP-027, con las mismas listas que M1.

## 4. Ángulo B — Razonamiento algebraico

### X2. La solución de Gauss como fase inicial

- research/06 la descartó por efecto pequeño: ~6 s de PAR-2 en 2026, sin
  cambiar el estado de ninguna instancia. Solo la veía razonable «como
  subproducto de X1, a coste marginal».
- Con X1s, ya lo es: σ ya se calcula. `--gaussphase` la copia en las fases
  guardadas de las variables del sistema cuando X1s la rechaza. Son 30
  líneas sin estructuras nuevas, y no tocan la prueba.
- Dónde podría notarse: en las 250 instancias de EXP-022 con sistema
  consistente y σ rechazada, casi todas industriales.
- **Prioridad baja** por la evidencia previa: va al final de la cola
  (EXP-032).

### M4. X1b: medir antes de construir

- research/09 §5 diseñó X1b: unidades y equivalencias implicadas por el
  sistema, con prueba DRAT. Tiene un coste real:
  - registrar variables de extensión en Kissat;
  - una prueba sin borrados que encarece la verificación.
- Su valor está **sin estimar**. En 2026, ningún solver con Gauss ganó en
  las familias de paridad mezclada.
- `x1b_potencial.py` lo estima sin tocar el solver:
  1. propagación unitaria en la raíz;
  2. extracción de X1;
  3. Gauss-Jordan por componentes;
  4. recuento de las filas reducidas con una o dos variables que la
     propagación no da y que no estaban en la CNF.
- En las *lights-out* sintéticas da 5 unidades y 10 equivalencias. En tres
  instancias de `calib` con XOR, 0. Esto es solo una prueba del guion, no
  un dato.
- **Experimento**: EXP-025. Es determinista y barato, y decide si X1b se
  construye o se descarta.

## 5. Ángulo C — Heurística de búsqueda

### M5. Rampa de decaimiento

- En modo estable, Kissat usa EVSIDS con decaimiento fijo (`decay` = 50 por
  mil, es decir, 0,95).
- Glucose empieza en 0,80 y sube 0,01 cada 5000 conflictos hasta 0,95. Así
  la heurística es más reactiva al principio, cuando las puntuaciones
  todavía no significan nada.
- AE-Kissat-MAB (1.º en 2025) evolucionó con LLM un decaimiento dinámico
  (research/07 §1).
- `--decayramp=N`: el decaimiento empieza en N por mil y baja 10 cada 5000
  conflictos hasta `decay`. Con N = 200 es la rampa de Glucose. Solo actúa
  en el modo estable, porque el enfocado usa VMTF.
- **Experimento**: EXP-030.

### M6. El bandido VSIDS/CHB (D-018)

Ahora se sabe con exactitud qué costaría portarlo. El código de Kissat_MAB
4.0.2 del paquete oficial de 2026 (`zheng`, MIT) toca **12 ficheros**:

- `analyze`: cuenta conflictos para la recompensa;
- `backtrack`, `compact`, `decide`, `flags` y `resize`: un segundo montículo
  `scores_chb`;
- `bump`: la actualización de CHB y su decaimiento;
- `propsearch`: recompensa a las variables asignadas en el nivel actual;
- `restart`: el UCB al reiniciar en modo estable;
- `internal`, `options` y `application`.

**Lo que se encontró al leerlo:**

- La versión de `kissat-mab-hypre` no es la de 2021. Añade un segundo
  bandido sobre `strategy`, con estado en variables `static` (momento y
  ganancias recientes), y un comentario `// MAB bug?` sobre el bumping.
  Portarla tal cual importaría código evolucionado sin ablación.
- La variante SATLUTION corrige un caso:
  - CHB actualizaba puntuaciones también durante el sondeo (`probing`);
  - SATLUTION lo excluye, señal de que el original lo hacía sin querer.
- **Recomendación**:
  - si D-018 se reabre, portar el **Kissat_MAB de 2021** (UCB simple, una
    sola estrategia), detrás de `configure --mab`, con la búsqueda idéntica
    sin la macro, como X1;
  - el bandido «evolucionado» no.
  - Sigue valiendo la conclusión de research/10 §3.2: sin un selector,
    repartir no compensa. Nada de esto se implementa sin D-018.

## 6. Ángulo D — Inprocesado

### M8. Congruencia iterada (SATLUTION)

- **El cambio**, en `probe()`:
  - si la reducción transitiva quitó binarias, congruencia otra vez (ciclo
    42 de SATLUTION);
  - después, una segunda reducción transitiva, que limpia las binarias de
    equivalencia nuevas (ciclo 51).
- **Evidencia a favor**: su propio banco, −61 s, con σ ≈ 22 entre corridas.
- **Evidencia en contra**: la competición, +70 s (§0.4).
- Replicarlo cuesta poco y aporta material al artículo, porque es un caso
  limpio de mejora dentro de la muestra que no sale fuera de ella.
- `--probeiterate` lo implementa. `kissat_transitive_reduction` pasa a
  devolver si redujo algo, como en su código. Kissat no usaba el resultado:
  la búsqueda no cambia con la opción a 0.
- **Experimento**: EXP-029, con predicción nula declarada.

## 7. Ángulo E — Calidad del código base

### M9. El fallo de `eliminate.c`

- **Qué hace hoy Kissat.** Al final de `eliminate_variables`, la decisión de
  si la eliminación quedó **completa** lee una variable que nunca cambia.
  - Kissat cree siempre que terminó.
  - Dobla la cota de cláusulas añadidas (`eliminatebound`: 0, 1, 2, 4, 8,
    16) y vuelve a programar todas las variables.
  - No descarta nunca las candidatas pendientes.
- **Qué haría el código si funcionara como está escrito.**
  - Si la última ronda eliminó algo (por ejemplo, porque se agotaron las
    `eliminaterounds` = 2), la eliminación queda **incompleta**.
  - La cota no sube y las candidatas se descartan hasta que cambien sus
    cláusulas.
- **Lectura.**
  - Con el fallo, Kissat sube la cota antes de lo que sus autores
    pretendían.
  - Puede que eso sea **bueno**: es la conducta que ganó, y nadie la ha
    medido arreglada.
  - Por eso no se arregla, se mide.
- `--eliminatefix` copia en la variable exterior lo eliminado en cada
  ronda. Con 0, la máquina hace lo mismo que antes.
- **Experimento**: EXP-028.
- **Fuera del repositorio**: si se avisa a Biere, lo decide el director
  (D-021).

### M10. La elección del vigilante en `vivify.c`

- **Qué pasa.** En `swap_first_literal_with_best_watch`, el bucle busca el
  mejor vigilante:
  - un literal no falso;
  - o, entre los falsos, el de nivel más alto.

  La guarda es `value < 0`, pero dentro del bucle se declara otro `value`
  que la tapa. La guarda nunca cambia y el bucle no para en el primer
  literal no falso.
- **Consecuencia.** Si después viene un falso de nivel mayor, se elige ese.
  En el caso `[F@1, U1, U2, F@3]` acaban vigilados F@3 y U1 en vez de U1 y
  U2. Un vigilante falso con dos literales libres puede retrasar una
  propagación, aunque nunca hace perder corrección: el conflicto aparece
  igual al asignar el último literal.
- **Medir antes de arreglar.** La estadística `vivify_watch_mismatch` (solo
  con `--stats`, sin cambiar la búsqueda) simula las dos elecciones de cada
  `vivify_watch_clause`, con y sin arreglo, y cuenta las veces en que el par
  vigilado queda con **menos literales no falsos**.
  - La primera versión contaba cualquier diferencia: ~35 %, inflado por
    elecciones entre dos literales no falsos, que dan igual.
  - Un falso en la primera elección puede corregirse en la segunda.
  - Contando solo los pares peores:
    - ≈ 11 % en las tres primeras instancias de calib (328 de 2901, 347 de
      3308 y 356 de 3144);
    - **9,5 %** en las 29 de calib y calib2 (4114 de 43 514), con
      desajustes en 19.
- **Lectura**: no es raro, pero el daño es acotado. El par malo solo
  estorba mientras la vivificación siga en niveles altos; al acabar la ronda
  vuelve al nivel 0 y el invariante se recupera. Sí puede hacer que la
  propia vivificación pierda propagaciones, y por eso vivifique menos.
- **Experimento**: EXP-031. Primero el diagnóstico; el A/B, solo si el
  desajuste no es raro.

### Lo demás que encontró el análisis estático

| Herramienta | Avisos | Fallos | Resto |
|---|---|---|---|
| `gcc -Wshadow=local` (todo `src/`) | 15 | 2 (`eliminate.c:466`, `vivify.c:740`) | 13 inofensivas: la interior se usa solo en su bloque con el mismo significado (`analyze.c`, `dense.c`, `flags.c`, `sweep.c`, `sort.c`, `report.c`, `factor.c`, `definition.c`) |
| `clang --analyze` (todo `src/`) | 3 | 0 | Falsos positivos en `congruence.c:3187` (desplazamiento con `size` = 0, que un `assert` descarta) y `application.c:407` |

`-Wshadow` sin más da 114 000 avisos: el estilo de Kissat nombra las
variables como sus tipos (`statistics *statistics`). Solo `-Wshadow=local`
es útil.

## 8. Ángulo F — Pruebas y robustez

### M11. ¿Cuánto cuesta escribir la prueba?

- En la competición, todo UNSAT escribe su prueba, y ese tiempo cuenta
  (research/08, C5, «por medir»).
- **Diseño**: el mismo binario, con presupuesto de **conflictos**, así que
  las dos ramas hacen exactamente la misma búsqueda (se comprueba). La
  razón de tiempos es el coste de escribir.
  - A, sin prueba;
  - B, con la prueba en disco.
- Si pasa del 3 %, hay una optimización de clase E posible: un búfer mayor,
  o escribir en otro hilo.
- **Experimento**: EXP-033.

### M12. ¿Verifican nuestras pruebas a escala?

Hasta ahora se ha comprobado la **corrección** de cada prueba (los dos
`dsr-trim` en EXP-007, 010, 011, 012, 019 y 022), pero no:

- **cuánto tarda la verificación** frente a la resolución. En 2026, 12
  respuestas del top se perdieron por *checker-timeout*;
- **el tamaño de las pruebas** con satsuma: el prefijo SR del banco
  simétrico llega a 7 MB (`043c9100…`, `results/b4`).

**Experimento**: EXP-034. Es la base de la elección del verificador (fase
5, H8).

## 9. Descartadas o aparcadas, con motivo

| Idea | Motivo |
|---|---|
| Aprendizaje simétrico dinámico (SEL, Devriendt et al., 2017) | La imagen simétrica de una cláusula aprendida no tiene una justificación DRAT/SR barata. Exigiría VeriPB y otro verificador (research/09) |
| SBVA | **Ya está** en Kissat 4.0.x (`factorhops` = 3, §0.5) |
| BCE, *lookahead*, cubo y conquista | Fuera del alcance de 4 núcleos; cubo y conquista choca con la regla de metodologías (ROADMAP §1.2) |
| Ajuste automático de parámetros (SMAC, irace) | Sobreajuste al banco y riesgo de «AI-tuned» (ROADMAP §1.3); la lección de SATLUTION (§0.4) |
| Evolución de código con LLM | N7 (research/07): cómputo masivo y sin preregistro |
| Portar el MAB «evolucionado» de `kissat-mab-hypre` | Estado en variables `static`, segundo bandido sin ablación (§5.2) |
| Fases desde GNN o modelos aprendidos | research/05 |
| K2 y K4 (precargas) | K1 salió más lenta (EXP-018) |

## 10. Orden de ejecución en la máquina local

Estos experimentos van **detrás de EXP-023** en `scripts/cola.toml`, uno a
uno, con la regla de la máquina (15 GB, una tanda pesada a la vez).

- **Binario.** Todas las opciones nuevas viven en
  `solver/kissat/build-m/kissat`, compilado desde el commit de los
  preregistros con la configuración adoptada (`--pgo --lto`). Así no se toca
  `build/`, que vigila EXP-023 con `--guard`.
- **Comandos.** Cada paso de la cola es el comando de su preregistro.

| Orden | Experimento | Tipo | Coste esperado (peor caso) | Por qué en este orden |
|---|---|---|---|---|
| 1 | **EXP-024** (M2) | satsuma solo, determinista | ~3 h (4 h) | Barato; decide si la V1 de D-020 se abarata |
| 2 | **EXP-025** (M4) | diagnóstico en Python, determinista | ~1 h (3 h) | Barato; decide si X1b se construye |
| 3 | **EXP-031** etapa 0 (M10) | diagnóstico con `--stats`, conflictos fijos | ~1 h | Barato; decide si M10 merece un A/B |
| 4 | **EXP-026** (M1) | A/B, dos etapas | ~3 h + ~6 h (9 h + 17 h) | Ataca la pérdida SAT de «siempre» |
| 5 | **EXP-027** (M7) | A/B, dos etapas, mismas listas que M1 | ~3 h + ~6 h | Ídem, con otro mecanismo |
| 6 | **EXP-028** (M9) | A/B, dos etapas | ~2,5 h + ~6 h (7 h + 20 h) | Toca a todas las instancias |
| 7 | **EXP-029** (M8) | A/B, dos etapas | ídem | Réplica de SATLUTION |
| 8 | **EXP-030** (M5) | A/B, dos etapas | ídem | Evidencia más débil |
| 9 | **EXP-033** (M11) | A/B con conflictos fijos | ~2 h | Informa a H8 |
| 10 | **EXP-034** (M12) | resolución con prueba y verificación | ~10 h (20 h) | Necesario antes de H8 |
| 11 | **EXP-032** (X2) | A/B, dos etapas | ~2 h + ~5 h | Prioridad baja |

**Total**:

- si todas las vías pasan el cribado, ~60 h esperadas;
- si solo pasan dos o tres, ~40 h, que es lo realista con la predicción
  honesta de §2.

Sin el cribado en dos etapas serían ~95 h.

**Regla del cribado** (todas las opciones de búsqueda; `research12.py`):

- **Etapa 1**, con 40 instancias de `results/research12/cribado.txt`,
  T = 300 s y semilla 42.
  - PASA si el ΔPAR-2 medio (B − A) es negativo, o si el factor de
    velocidad B/A en las resueltas por las dos es < 0,97.
  - Si no, se cierra «sin señal».
  - No hay contraste: los p se informan, pero no son evidencia.
- **Etapa 2**, con 60 instancias **distintas**
  (`results/research12/confirmacion.txt`), T = 300 s y semillas 42 y 123.
  - H1: Wilcoxon p < 0,05 y el IC95 % bootstrap del ΔPAR-2 entero por
    debajo de 0.
  - H2: el IC95 % del factor de velocidad entero por debajo de 1.
- Por qué es honesto: la etapa 2 no reutiliza ninguna instancia del
  cribado, y el umbral del cribado se fija aquí, antes de ver nada. El
  cribado solo puede **descartar** una vía, nunca confirmarla.
- **Un error de tipo II**: una vía con efecto real pero pequeño puede no
  pasar el cribado. Se acepta: con 4 núcleos, un efecto que 40 instancias
  no muestran ni en el signo tampoco movería el PAR-2 de la competición
  (research/08 §2).

## 11. Verificación de lo implementado (en la nube, solo corrección)

La regla de CLAUDE.md §6 deja los tiempos para la máquina local. En la nube
solo se comprobó que el código no rompe nada:

1. **Equivalencia con las opciones a 0**: contadores de conflictos,
   decisiones y propagaciones idénticos a los del binario de `a5429c7` en
   **50 de 50** instancias (15 de calib, 10 de calib2, las de smoke y 15 de
   symm2026), a 20 000 conflictos y semilla 1.
2. **`test_opciones_m.sh`** (en CI):
   - las cinco opciones valen 0;
   - escribirlas con su valor por defecto no cambia la búsqueda;
   - con cada una encendida, 11 SAT con modelo verificado y 11 UNSAT con
     prueba aceptada por `drat-trim` y los dos `dsr-trim`;
   - X2 pone fases cuando X1s se rechaza.
3. **Bajo ASan/UBSan**, el mismo guion.
4. **Que cada opción actúa**: en 29 instancias de calib y calib2 a 20 000
   conflictos, §12.

### 11.1 Equivalencia, pruebas y build de competición

- **Equivalencia**: con el binario final, 50 de 50 instancias con los
  mismos contadores que la base. Se repitió tres veces, tras cada cambio
  de código.
- **`test_opciones_m.sh`**:
  - en todas las configuraciones, 11 SAT con modelo verificado y 11 UNSAT
    con prueba aceptada por los tres verificadores;
  - X2 pone 288 fases en una paridad satisfacible con una cláusula ajena.
- **Build de competición** (`--competition`, con y sin `--symmetry`):
  - responde bien en `bench/smoke`;
  - refuta la *lights-out* con prueba aceptada por el `dsr-trim` de SC2026;
  - la prueba de `php_12_11` con satsuma la aceptan los dos `dsr-trim`.

  Antes de este trabajo no enlazaba (§0, CHANGELOG).
- **`smoke_test.sh`**: en verde.
- **`LABESAT_SYMM_ARGS` en el binario integrado**:
  - los topes llegan a satsuma y la prueba se verifica;
  - con un argumento inválido, satsuma falla y se cae al respaldo, como
    debe.
- **`satsuma_topes.sh` con `labesat`**: la prueba de `php_12_11` verifica.

## 12. ¿Actúa cada opción? (comportamiento, no rendimiento)

En 29 instancias de calib y calib2, a 20 000 conflictos y semilla 1, con el
binario `build-m`. `baseball-lineup` se excluyó: su `lucky` tarda 42 s
antes del primer conflicto y, con siete corridas, agotaba el tope de la
tarea.

| Opción | Instancias en las que cambia la trayectoria |
|---|---:|
| `--decayramp=200` | 19 |
| `--vivifywatchfix=1` | 19 |
| `--probeiterate=1` | 11 |
| `--eliminatefix=1` | 10 |
| `--gaussphase=1` | 8 |

- Todas actúan en instancias reales: ninguna es una opción muerta.
- Las instancias en las que nada cambia se resuelven antes de llegar a
  modo estable, eliminación o sondeo, o no tienen XOR (X2).
- **M10**: 9,5 % de las vivificaciones con un par vigilado peor (4114 de
  43 514), con desajustes en 19 de las 29 (§7).
- **M9 actúa en 10 de 29**. Es decir: en un tercio de las instancias, al
  menos una eliminación termina con una ronda que eliminó algo. Ahí la
  conducta de Kissat (subir la cota) y la arreglada (no subirla) difieren.

Nada de esto dice si alguna mejora el PAR-2: lo deciden los A/B.

## Referencias

- Audemard, G., y Simon, L. (2009). Predicting learnt clauses quality in
  modern SAT solvers. *IJCAI 2009* (Glucose; rampa del decaimiento en su
  implementación).
- Cherif, M. S., Habet, D., y Terrioux, C. (2021). Combining VSIDS and CHB
  using restarts in SAT. *CP 2021*.
- Devriendt, J., Bogaerts, B., y Bruynooghe, M. (2017). Symmetric
  explanation learning: effective dynamic symmetry handling for SAT. *SAT
  2017*.
- Gent, I. P., Harvey, W., y Kelsey, T. (2002). Groups and constraints:
  symmetry breaking during search. *CP 2002*.
- Haberlandt, A., Green, H., y Heule, M. J. H. (2023). Effective auxiliary
  variables via structured reencoding. *SAT 2023* (SBVA).
- Puget, J.-F. (2005). Symmetry breaking revisited. *Constraints* 10(1).
- SATLUTION: https://arxiv.org/abs/2509.07367; `CHANGELOG.md`,
  `HYPOTHESIS.md` y `RESULTS.md` del paquete
  `zheng/kissat-mab-hypre-satlution` (SAT Competition 2026).
- Paquetes de 2026: https://satcompetition.github.io/2026/downloads/solvers/
  (`zheng.tar.xz`, leído el 2026-10-05; MIT).
- Resultados oficiales de 2026: `data/competition/scores_2026.csv`.
