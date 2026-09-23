# Investigación 02 — Catálogo de ideas de mejora, priorizado por techo medido

> Cada idea de este catálogo lleva un **techo empírico**: cuánto PAR-2 habría
> ganado, como máximo, sobre las 400 instancias reales del Main Track 2026, según
> los resultados oficiales (ver [`01-analisis-empirico-sc2026.md`](01-analisis-empirico-sc2026.md)).
> Eso no demuestra que la idea funcione —lo demuestra el A/B— pero sí permite
> **descartar las que ni en el mejor caso pagan el esfuerzo**, que es la
> decisión más rentable de todo el proyecto.
>
> Referencia en todas las tablas: Kissat de fábrica, **238/400 resueltas,
> PAR-2 = 4611.5 s**. Reglas 2026 = reglas previstas 2027: 1 núcleo, T = 5000 s,
> 32 GB, **certificado obligatorio en SAT y en UNSAT**.

## Tabla de decisión (resumen)

| # | Idea | Techo medido (ΔPAR-2) | Coste | Riesgo "ya hecho" | Veredicto |
|---|---|---:|---|---|---|
| **A1** | Cartera secuencial de configuraciones en un binario | **−798 s** (sin oráculo) | bajo | medio | **Primera** |
| **A2** | Conmutación de configuración en caliente (sin reinicio) | ≤ −2257 s (oráculo) | medio | bajo | **Segunda** |
| **A3** | Selección por instancia con features baratos | ≤ −2257 s (oráculo) | medio-alto | alto (SATzilla) | Tercera |
| **A4.1** | Reparto adaptativo entre los 2 modos existentes | **−2.2 s en dev, IC incluye el 0** | medio | bajo | **Implementado; sin confirmar** |
| **B1** | Ruptura de simetrías **condicional** | −964 s incond. / **−1287 s** cond. | alto | alto (satsuma) | Solo condicional |
| **B2** | Hiper-resolución binaria condicional (hypre) | −615 s | medio-alto | alto | Alternativa a B1 |
| **B3** | Detector barato de estructura para condicionar B1/B2 | habilita +322 s sobre B1 | medio | **bajo** | **Diferencial** |
| ~~**B3'**~~ | ~~Condicionar las fases *lucky* por tamaño de fórmula~~ | **+2.3 s en el banco reservado** | muy bajo | — | **CERRADA: no replicó (EXP-003)** |
| **B3''** | Hacer que `kissat_lucky` **ceda el control** al límite de tiempo | latencia 318 s → <1 s | bajo | ninguno (es un bug) | **HECHA (EXP-004)** |
| **C1** | Robustez: ↓varianza por seed, flaky→estable | no medible en PAR-2 solo | bajo | **muy bajo** | Métrica, no técnica |
| **D1** | Bandit sobre rephase/restart | **+25 a +280 s (PEOR)** | medio | muy alto | **Descartada como idea principal** |
| **D2** | Gestión de cláusulas más allá de LBD | desconocido | medio | medio | Aparcada |
| **D3** | Predicción de fases offline (ML) | desconocido | alto | medio | Moonshot |

---

# Línea A — Explotar la diversidad entre configuraciones

**La evidencia que abre esta línea es la más fuerte del análisis.** Las 12
variantes de Kissat de 2026 que quedaron **individualmente peores** que el
Kissat de fábrica tienen, juntas, un Virtual Best Solver de:

| conjunto | resueltas | PAR-2 | Δ vs base |
|---|---:|---:|---:|
| Kissat de fábrica (base) | 238 | 4611.5 | 0.0 |
| **Ganador de 2026** (`satsuma-iter-kissat`) | **276** | **3647.0** | **−964.5** |
| VBS de las 12 variantes *peores que la base* | **277** | **3540.3** | **−1071.2** |
| VBS de esas 12 + la base | 287 | 3352.3 | −1259.3 |
| VBS de las 21 variantes de Kissat | 321 | 2354.8 | −2256.7 |

Doce configuraciones que **fracasaron** —ninguna batió a la base— resuelven
juntas *más* que el campeón del año. La conclusión es incómoda para la práctica
habitual del campo: **la comunidad está optimizando la media de una
configuración cuando el recurso disponible está en la varianza entre
configuraciones.**

## A1 · Cartera secuencial con reparto de tiempo

**Mecanismo.** Un único binario que ejecuta k configuraciones de sí mismo, una
tras otra, con T/k segundos cada una. Si una resuelve, termina. Es la forma más
simple de convertir diversidad en PAR-2 y cumple las reglas de la Main Track
secuencial (un núcleo, un proceso).

**Techo medido.** Simulación con las reglas reales (`analyze_competition.py portfolio`):

| k | resueltas | PAR-2 | Δ vs base |
|---:|---:|---:|---:|
| 1 | 238 | 4611.5 | 0.0 |
| 2 | 264 | 4074.0 | −537.5 |
| **3** | **274** | **3813.1** | **−798.4** |
| 4 | 273 | 3811.5 | −800.0 |

El coste del reparto es asumible porque **el 79.4 % de lo que la base resuelve,
lo resuelve en menos de T/3** (p50 = 298 s, p75 = 1409 s). Dividir el tiempo en
tres pierde poco y compra mucho.

**Lo que falta por saber (y es el experimento EXP-001).** Esa simulación usa
*motores ajenos* como miembros. La pregunta abierta: ¿basta con diversificar
**Kissat consigo mismo** (seeds distintas, `--sat`/`--unsat`, `stable=0/1/2`,
`--plain`, parámetros de reinicio)? Si la respuesta es sí, la idea se implementa
en menos de 200 líneas. Si es no, hay que construir diversidad real, y eso
convierte A1 en A2/A4.

**Restricción de ingeniería que hay que resolver (y que la literatura de
carteras suele ignorar): el certificado.** La Main Track exige prueba en SAT y
en UNSAT. Si el intento 1 escribe media prueba DRAT y se aborta, esa prueba es
basura que invalida la del intento 2. Solución: la prueba se escribe a fichero y
en cada reinicio se hace `truncate`/`seek(0)`, de modo que solo sobreviva la del
intento que resuelve. Hay que verificarlo con `scripts/check_proof.sh` en la
suite de no-regresión — es justo el tipo de fallo que no aparece midiendo tiempos.

**Riesgo.** Las carteras están inventadas (ppfolio, SATzilla, ManySAT). Lo que
**no** está hecho es una cartera *interna a Kissat* afinada con el criterio de
abajo (A4). A1 por sí sola es ingeniería, no contribución publicable: es la
**línea base fuerte** sobre la que medir A2/A4.

**Experimento**: EXP-001 (diversidad intrínseca de Kissat) → EXP-002 (A/B de la
cartera k=2,3 en `bench/dev`).

## A2 · Conmutación de configuración en caliente

**Mecanismo.** En vez de reiniciar el solver desde cero en cada porción de
tiempo (que tira todas las cláusulas aprendidas), **cambiar la configuración sin
perder el estado**: mantener la base de cláusulas aprendidas y conmutar
heurística de decisión, política de reinicio, agresividad de inprocesado.
Kissat ya hace una versión de esto al alternar los modos `stable` y `focused`;
la idea es generalizarlo a un espacio de configuraciones mayor y con un criterio
de cambio explícito.

**Por qué puede batir a A1.** Una cartera secuencial paga el reinicio completo:
k−1 veces tira todo lo aprendido. La conmutación en caliente conserva el
aprendizaje y mantiene la diversidad de *política*, no de *proceso*. Su techo es
el VBS del conjunto de configuraciones (**−2256.7 s** con oráculo), no el de la
cartera con reparto.

**Riesgo.** Es donde vive la investigación de "adaptive/hybrid configuration"; hay
que revisar qué hizo exactamente `kissat-mab-hypre` (2º de 2026) antes de
reivindicar novedad. El fuerte del proyecto aquí es el criterio de conmutación,
no el mecanismo.

## A3 · Selección por instancia con features baratos

**Mecanismo.** Tras el preprocesado, calcular features baratos (nº variables y
cláusulas, ratio, fracción de binarias/ternarias, grado medio, presencia de
XOR/cardinalidad, tamaño del grupo de simetrías detectado en 1 s…) y **elegir
una sola configuración** para todo el presupuesto. Es SATzilla, pero dentro del
binario y sin modelos pesados.

**Techo**: el mismo VBS (−2256.7 s) y sin pagar reparto de tiempo — pero solo si
el predictor acierta, y ahí es donde se pierde casi todo en la práctica.

**Riesgo alto**: SATzilla y sucesores llevan 15 años en esto; el aprendizaje
supervisado sobre pocos cientos de instancias sobreajusta con facilidad.
**Viable como capa fina sobre A1**: elegir el *orden* de la cartera en vez de
elegir una sola configuración. Un predictor mediocre sigue ayudando si solo
decide quién va primero, porque el error no cuesta la instancia, cuesta un turno.

## A4 · Reparto adaptativo del presupuesto — **la propuesta diferencial**

**Mecanismo.** No repartir T/k a ciegas: **asignar el presupuesto en función del
progreso observado**. Se ejecutan las configuraciones en rondas cortas y, tras
cada ronda, se decide a quién dar la siguiente en función de una señal de
productividad de la búsqueda. Es un problema de bandido, pero **el bandit ya no
elige heurísticas: reparte tiempo**, que es donde su decisión tiene consecuencia
medible y donde el fracaso de 2026 (D1) no aplica.

**Por qué esto sí y D1 no.** En 2026, cuatro grupos pusieron bandits a elegir
heurísticas *dentro* de una búsqueda y ninguno batió a la base: la señal es
ruidosa y el efecto de cada brazo se diluye en millones de conflictos. Aquí el
brazo es una configuración completa con su propia trayectoria, el horizonte es
de minutos y la recompensa —¿está progresando esta trayectoria?— es exactamente
la que el proyecto ya validó empíricamente en la etapa anterior: **GLR relativo
a su EMA**, no su nivel absoluto (ver
[`../archive/cadical-era/05-fase1-validacion-recompensa.md`](../archive/cadical-era/05-fase1-validacion-recompensa.md)).
Ese resultado, que sobre CaDiCaL era un detalle de diseño, aquí es el núcleo de
la contribución y hay que **reproducirlo sobre trazas de Kissat**.

**Techo**: entre A1 (−798 s, reparto ciego) y el VBS (−2257 s, oráculo). El
margen que A4 disputa es esa franja de ~1460 s de PAR-2.

**Novedad**: la combinación (reparto adaptativo de presupuesto entre
configuraciones de un mismo motor + recompensa validada + objetivo de robustez)
no aparece en las entradas de 2025/2026 revisadas. Es la candidata a
contribución principal.

---

# Línea B — Preprocesado estructural condicional

## B1 · Ruptura de simetrías condicional

**Evidencia.** El ganador de 2026 es Kissat + satsuma: **−964.5 s, +38
instancias**. Todo su margen está en familias simétricas que la base **no
resuelve en absoluto** (`chnl` 0/6, `clique-coloring` 0/2, `count` 0/6,
`relativized-pigeon-hole` 0/1) y que con simetrías caen en **décimas de segundo**.

**Pero rompe cosas**: hace perder 13 instancias (`oddball-weighing`,
`st-connectivity-principle`, `fermat`, `sorting-networks`, `argumentation`).
El oráculo que decide *cuándo* aplicarla vale **−322.3 s adicionales** sobre
aplicarla siempre:

| estrategia | PAR-2 | Δ vs base |
|---|---:|---:|
| base | 4611.5 | 0.0 |
| satsuma siempre | 3647.0 | −964.5 |
| **satsuma solo cuando ayuda (oráculo)** | **3324.7** | **−1286.9** |

**Coste**: alto. Detección de simetrías es teoría de grupos + un detector de
automorfismos de grafo (saucy/bliss). Reimplementarlo es un proyecto en sí.
**Ruta realista**: integrar una herramienta existente (satsuma/BreakID, ambas
públicas) como fase de preprocesado y aportar **el criterio de activación**.

**Aviso de sobreajuste al banco**: el banco de 2026 fue inusualmente rico en
combinatoria simétrica. Apostarlo todo a B1 es apostar a la composición del
banco de 2027, que se compone con el mismo script pero con otras sumisiones.

## B2 · Hiper-resolución binaria condicional (hypre)

`kissat-mab-hypre` (2º y 3º de 2026, −615.3 s) gana en **las mismas familias**
que satsuma con una técnica distinta y mucho más barata de implementar. Eso dice
que esas familias están **infra-atacadas por el preprocesado por defecto de
Kissat**, y que hay más de una puerta de entrada. B2 es la versión de menor
coste de la línea B.

## B3 · Detector barato de estructura — **segundo diferencial**

B1 y B2 comparten una pregunta sin responder en la literatura: **¿cómo saber, en
un segundo y sin ejecutar nada, si esta fórmula merece preprocesado agresivo?**
Los −322.3 s que separan "siempre" de "cuando conviene" son la medida exacta del
valor de responderla, y son casi un tercio de lo que ganó el campeón entero.

Es una contribución pequeña, autocontenida, medible, y **útil para cualquier
solver**, no solo para el nuestro — buen material de artículo corto.

## ~~B3' · Condicionar las fases *lucky*~~ — **CERRADA: no replicó**

> **Resultado final**: validada sobre el banco reservado `bench/test` (60
> instancias nunca usadas), la regla da **ΔPAR-2 = +2.254 s — peor, no mejor**,
> con IC95 % `[−3.79, +11.17]` y Wilcoxon p = 0.98. Se retira del catálogo y se
> elimina del solver. Detalle y post-mortem en
> [`EXP-003`](../experiments/EXP-003-validacion-luckyminvars.md).
>
> **Por qué falló**: una instancia de **306 variables** —tres órdenes de
> magnitud por debajo del umbral— solo se resuelve *gracias* a las fases lucky.
> El valor de éstas no está correlacionado con el tamaño: depende de que la
> fórmula admita una asignación trivial, y eso el recuento de variables no lo
> captura. El −13.4 s de EXP-002 era un umbral ajustado sobre las 60 instancias
> en las que se midió, no un mecanismo.

Lo que se midió en su momento (y que sigue siendo cierto *en aquel banco*,
detalle en [`EXP-002`](../experiments/EXP-002-fases-lucky.md)):

- `kissat_lucky` **no consulta el límite de tiempo**: con `--time=30` una
  instancia de 3.56 M variables terminó a los **348.5 s** (11.6× el límite).
  Desactivando las fases lucky, a los 20.0 s exactos.
- Desactivarlas **siempre** es mala idea: en fórmulas de decenas de millones de
  variables son **la razón de que se resuelvan** (dos instancias pasan de SAT a
  TIMEOUT al quitarlas). En el banco fácil empeoran el PAR-2 un 92.8 %
  (Wilcoxon p = 0.0019).
- Desactivarlas **en las pequeñas** sí: `variables ≤ 50 000` da **−13.4 s de
  PAR-2 (−10.5 %)** sobre 60 instancias reales, capturando el **64 %** del hueco
  del oráculo, con todo el barrido de umbrales en ese sentido en negativo.

Coste de implementación: un `if` en `src/search.c`. Se implementó (commit
`589c853`), se validó, y **no replicó**. La línea queda cerrada.

## B3'' · Que `kissat_lucky` ceda el control — **viva, e independiente de B3'**

Lo único que sobrevive de esta línea, y no depende de si conviene saltarse las
fases lucky: **`kissat_lucky` no consulta el límite de tiempo ni el de
conflictos**. Medido: `--time=30` termina a los **348.5 s** (11.6× el límite),
y con las fases lucky desactivadas, a los 20.0 s exactos.

Es un fallo de upstream con consecuencias para cualquiera que mida con
presupuesto acotado — incluidos los organizadores de la competición. La
corrección correcta **no es saltarse las fases** (eso ya se probó y falló):
es que **cedan el control**, comprobando el terminador dentro de sus bucles.

**Implementada y verificada** en [`EXP-004`](../experiments/EXP-004-lucky-terminator.md):
6 bits en `terminate.h` y una comprobación en cada uno de los 6 bucles de
`lucky.c`, 68 líneas. La latencia baja de **318 s a menos de 1 s** y el
comportamiento sin terminación es **idéntico bit a bit** (mismos conflictos en
cuatro instancias, incluida la de 2 631 330 conflictos que hizo fracasar a B3′).

Importa además para A4: un mecanismo de reparto de presupuesto necesita que el
solver suelte el control en la frontera del turno. Con 350 s de latencia, no lo
hace.

---

# Línea C — Robustez como objetivo de evaluación

No es una técnica: es **qué se mide**. Los datos de tesis (866 instancias × 3
seeds) mostraron 62 instancias *flaky* y varianza temporal entre seeds de hasta
**102×**. La literatura de competición reporta "instancias resueltas" y PAR-2 de
**una sola corrida**, así que esa inestabilidad no se ve y nadie la optimiza.

Las líneas A1–A4 son, por construcción, máquinas de reducir varianza: si tres
configuraciones distintas atacan la instancia, el resultado depende menos de que
una tenga suerte. **Predicción falsable**: la cartera debe reducir el p90 del
ratio de tiempo entre seeds además de bajar el PAR-2. `par2.py` ya calcula esa
métrica, así que sale gratis en cada A/B.

Esto da al proyecto un eje de evaluación propio y defendible en un artículo
—"estabilidad de solvers CDCL frente a la aleatorización"— que no compite de
frente con los grupos que solo persiguen "más resueltas".

---

# Línea D — Ideas con techo medido bajo o desconocido

## D1 · Bandit sobre rephase/restart — descartada como idea principal

**Evidencia de 2026, cuatro grupos independientes, todos por debajo de la base:**

| solver | resueltas | PAR-2 | vs base |
|---|---:|---:|---:|
| guo_kissat-ae-eg | 235 | 4636.5 | **+25.0** |
| liang_kissat-mab-da | 236 | 4640.4 | **+28.8** |
| ding_kissat-mab-eae1 | 228 | 4709.9 | **+98.4** |
| gopalan_kissat-evolve-rb | 228 | 4726.0 | **+114.5** |
| guo_kissat-ae-hucb | 227 | 4744.3 | **+132.7** |
| liang_kissat-lr-ds | 221 | 4868.9 | **+257.3** |
| ding_kissat-mab-eae3 | 219 | 4891.3 | **+279.8** |

Esto **revoca** la recomendación del documento archivado
[`06-estado-del-arte-modificaciones.md`](../archive/cadical-era/06-estado-del-arte-modificaciones.md),
escrito con datos de 2025, que proponía un bandit de rephase con recompensa
mejorada. Con los datos de 2026, el margen de esa familia de ideas es negativo.

**Qué se salva**: la *recompensa validada* (GLR relativo al EMA) y el aparato
conceptual del bandit, reubicados en A4, donde el brazo es una trayectoria
completa y no una heurística interna.

## D2 · Gestión de cláusulas más allá de LBD
Sigue siendo una cuestión abierta del campo, pero no hay en los datos de 2026
ninguna entrada que aísle su efecto, así que **no hay techo medible**. Aparcada
hasta que A y B se agoten.

## D3 · Predicción de fases offline (NeuroBack-lite)
Coste alto, techo desconocido, y el fracaso de las variantes `evolve`/`eae`
(todas con componente aprendido) invita a la cautela. Moonshot.

---

# Plan de trabajo que se deriva

| Orden | Qué | Por qué ahora | Documento |
|---|---|---|---|
| 1 | **EXP-001**: ¿tiene Kissat diversidad intrínseca suficiente? | Es la premisa de toda la línea A. Barato y decide el resto del proyecto. | `docs/experiments/EXP-001-*.md` |
| 2 | **EXP-002**: A/B de la cartera secuencial k=2,3 | Convierte la premisa en PAR-2 medido en nuestro banco | pendiente |
| 3 | **EXP-003**: reparto adaptativo (A4) vs reparto ciego (A1) | Es la contribución candidata; A1 es su línea base honesta | pendiente |
| 4 | **EXP-004**: detector de estructura (B3) sobre las familias de 2026 | Independiente de A; se puede solapar | pendiente |

Las 46 instancias que **nadie** resolvió en 2026 y las 19 que resolvió **un solo
solver** quedan como banco de dificultad extrema para la validación final.

## Fuentes

- Resultados oficiales 2026 y metadatos GBD: ver `01-analisis-empirico-sc2026.md`.
- Reglas Main Track 2026 (T=5000 s, 32 GB, certificado en SAT y UNSAT):
  https://satcompetition.github.io/2026/tracks.html
- Recompensa GLR validada en la etapa anterior:
  `docs/archive/cadical-era/05-fase1-validacion-recompensa.md`
- Inestabilidad por seed (62 flaky, 102× de varianza):
  `docs/archive/cadical-era/03-fase0-datos-tesis.md`

---

# Apéndice · Puntos de enganche en el código de Kissat 4.0.4

Leído el código del fork, estas son las funciones concretas donde aterriza cada
idea. Sirve para estimar coste y para que el diff contra upstream quede
localizado (ADR-0002 §3).

| Idea | Fichero:función | Qué hay hoy | Qué habría que hacer | LOC aprox. |
|---|---|---|---|---:|
| **A1** cartera secuencial | `src/application.c:807` (`kissat_solve`) | una sola llamada a `kissat_solve` | bucle sobre k configuraciones con `kissat_init/release` y límite por config; truncar la prueba DRAT del intento abortado | 150–250 |
| **A2/A4** conmutación y reparto | `src/mode.c` (`kissat_switching_search_mode`, `kissat_switch_search_mode`) + `src/search.c:207` | **ya existe una alternancia de 2 brazos** (`stable`/`focused`) con planificación **ciega**: límites por conflictos y por *ticks*, alternando | generalizar a k brazos y sustituir la planificación ciega por una guiada por progreso | 200–400 |
| **B3** detector estructural | `src/classify.c` (`kissat_classify`) + `src/classify.h` (`struct classification`) | **ya existe un clasificador** con dos bits (`small`, `bigbig`), llamado desde `search.c`, `probe.c`, `eliminate.c`, `reduce.c`; hoy solo lo consume `fastassign.h` | ampliar los features y hacer que condicione el preprocesado agresivo | 150–300 |
| **B1/B2** preprocesado | `src/preprocess.c`, `src/probe.c` | vivify, sweep, congruence, factor | integrar la técnica externa como fase adicional | 300+ (o enlazar una herramienta externa) |
| **D1** bandit de rephase | `src/rephase.c` | heurística fija | (descartada) | — |

Dos hallazgos de esta lectura que cambian el encuadre de la contribución:

1. **Kissat ya hace, con dos brazos y una planificación ciega, lo que A4
   propone hacer con k brazos y una planificación adaptativa.** El `mode.c`
   actual alterna `stable` y `focused` según límites fijos de conflictos y
   *ticks*, sin mirar en ningún momento si la trayectoria está progresando. Eso
   convierte a A4 en una **generalización natural de un mecanismo que el propio
   upstream ya considera correcto**, no en un injerto ajeno — que es la
   diferencia entre un parche que un revisor acepta y uno que rechaza.
2. **Kissat ya tiene un clasificador de instancias** (`classify.c`), con dos
   bits y un único consumidor. La infraestructura para B3 existe; lo que no
   existe es el contenido.
