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
| **A4** | Reparto adaptativo del presupuesto entre configuraciones | entre A1 y A2 | medio | **bajo** | **Diferencial** |
| **B1** | Ruptura de simetrías **condicional** | −964 s incond. / **−1287 s** cond. | alto | alto (satsuma) | Solo condicional |
| **B2** | Hiper-resolución binaria condicional (hypre) | −615 s | medio-alto | alto | Alternativa a B1 |
| **B3** | Detector barato de estructura para condicionar B1/B2 | habilita +322 s sobre B1 | medio | **bajo** | **Diferencial** |
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
