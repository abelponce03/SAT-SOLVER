# 05 — Enfoques probabilísticos para mejorar un solver SAT: revisión y recomendaciones

- **Fecha**: 2026-09-23
- **Pregunta del director**: revisar a fondo los enfoques probabilísticos que
  complementan el rendimiento de los solvers SAT y mejoran las métricas del
  campo (PAR-2 y afines). La revisión se hace para **documentar**; no obliga a
  aplicar nada.
- **Regla del director**: se aplica solo lo que recomiende esta revisión. Lo
  que, por sí solo, quedaría **por debajo del ruido** de nuestra medición se
  descarta.
- **Estado**: revisión cerrada. Las recomendaciones están en §6. Ninguna se ha
  implementado: cada una necesitaría su experimento preregistrado (ADR-0003).

---

## 1. Qué cuenta como «probabilístico» aquí

Todo lo que usa **aleatoriedad, distribuciones de probabilidad o inferencia
estadística** para decidir algo dentro del solver o alrededor de él:

1. **Búsqueda estocástica**: búsqueda local (SLS), paseos aleatorios y
   decisiones aleatorias.
2. **Reinicios y colas pesadas**: distribuciones del tiempo de ejecución (RTD)
   y estrategias de reinicio.
3. **Aprendizaje en línea**: bandidos multibrazo (MAB) y refuerzo (RL) para
   ramificar, reiniciar o cambiar de fase.
4. **Inferencia probabilística**: propagación de creencias (BP), survey
   propagation (SP) y *Bayesian moment matching* (BMM).
5. **Predicción con aprendizaje automático**: redes de grafos (GNN) para fases
   o núcleos, y clasificadores de «ayuda / no ayuda».
6. **Modelos de dureza empírica** y selección o configuración de algoritmos
   (SATzilla, SMAC).
7. **Métodos estadísticos de evaluación**: supervivencia, remuestreo y
   variabilidad entre semillas. Es la parte de «mejorar las métricas».

## 2. Método

### Fuentes, el 2026-09-23

| Fuente | Qué cubre | Resultado |
|---|---|---|
| **Consensus** (Semantic Scholar, arXiv, Scopus) | ~220 M artículos | 20 consultas, 10 resultados cada una (límite del plan gratuito). La fuente principal |
| **Scholar Gateway** (texto completo) | Sobre todo el corpus de Wiley | 4 consultas. **Cobertura pobre** de las sedes de SAT (SAT, AAAI, IJCAI, JAIR, LNCS). Útil solo para Braunstein et al. (2005) y Hamadi y Wintersteiger (2013) |
| **Búsqueda web** | arXiv, OpenReview, páginas de autores | Datos concretos de NeuroBack, NeuroCore, Horvitz et al. (2001) y SATLUTION |

**Consultas**:
- búsqueda local y CDCL;
- colas pesadas y reinicios;
- bandidos y aprendizaje en la ramificación;
- reinicios con aprendizaje automático;
- BP y SP;
- modelos de dureza empírica y selección;
- borrado de cláusulas con aprendizaje automático;
- evaluación con supervivencia y significación;
- variabilidad entre semillas y rankings;
- MCTS;
- configuración automática (SMAC);
- probSAT;
- la estrategia de Luby;
- BMM;
- predicción de si un preproceso ayuda;
- Kissat_MAB y fases;
- SP en instancias industriales;
- diferencias entre SAT y UNSAT.

**Límites de la revisión**:
- Se leyeron los **resúmenes** y algunos pasajes, no todos los textos
  completos.
- Las cifras de efecto son **las que dan los autores**, en su hardware, con su
  presupuesto y su banco, y **no son comparables entre sí**.
- El plan gratuito de Consensus devuelve 10 resultados por consulta. Para
  compensarlo se hicieron más consultas, más estrechas.

### Criterio de ruido (la regla del director, hecha operativa)

- Nuestra capacidad de medir, según ADR-0003, EXP-004, EXP-006 y EXP-007:
  - 4 núcleos y T = 180 s;
  - bancos de 60 a 74 instancias;
  - deriva de ~4 % entre sesiones, controlada con el A/B intercalado.
- Con eso detectamos:
  - efectos que **cambian el estado** (resuelta o no) en varias instancias;
  - aceleraciones de ≥ ~10–15 % sostenidas en un subconjunto.
- **Precedente**: EXP-006. A4.1, un planificador adaptativo en la línea de
  los bandidos, dio 0,983× (p = 0,69), sin efecto medible.
- **Regla**: una técnica cuya ganancia publicada sea de pocos puntos
  porcentuales **sobre el conjunto completo de una competición**, y que además
  se solape con algo que Kissat ya hace, se clasifica como **descartada por
  ruido**. No decimos que no funcione; decimos que **no podríamos
  demostrarlo**, y sin demostración no entra (ADR-0003).

## 3. Lo que Kissat 4.0.4 ya hace (no se puede volver a «añadir»)

Tomado de `solver/kissat/src/options.h` y de sus fuentes.

| Técnica probabilística | En Kissat | Literatura |
|---|---|---|
| Búsqueda local con distribución de probabilidad en el *break* (probSAT) | `walk`, `walkeffort`; `walk.c` ajusta el parámetro CB | Balint y Schöning (2012) |
| Fases guiadas por búsqueda local y fases objetivo | `target`, `rephase` (best / original / inverted / walk) | Cai y Zhang (2021); Cai et al. (2022, JAIR); Biere y Fleury (2020) |
| Decisiones aleatorias para salir de zonas estancadas | `randec`, `randecfocused`, `randeclength` | — |
| Reinicios de Luby («reluctant doubling») en modo estable | `reluctant`, `reluctantint` | Luby, Sinclair y Zuckerman (1993) |
| Reinicios por medias móviles exponenciales (tipo Glucose) en modo focused | `restartint`, `restartmargin` | Biere y Fröhlich (2019); Audemard y Simon (2012) |
| Alternancia stable/focused | `stable`, `modeinit`, `modeint` | Oh (2015): SAT y UNSAT necesitan cosas distintas |
| Semilla, orden aleatorio de índices e inicialización de fases por propagación | `seed`, `tumble`, `warmup` | — |
| Barrido SAT con volteos aleatorios | `sweep`, `sweepfliprounds`, `sweeprand` | — |
| Borrado de cláusulas por LBD y uso reciente | `reduce*`, niveles (tiers) | Audemard y Simon (2009); Gstrein et al. («Learn to Unlearn», sobre Kissat) |

**Consecuencia**: buena parte de la literatura probabilística «clásica» ya
está dentro de Kissat, y afinada por sus autores. Las mejoras publicadas sobre
Kissat son, por eso, **incrementales**.

## 4. Catálogo

Veredictos:
- **R**: recomendada.
- **A**: aparcada; tiene potencial, pero el coste o el riesgo son altos ahora.
- **D-ruido**: descartada porque el efecto quedaría por debajo de lo que
  podemos medir.
- **D-no aplica**: descartada porque no encaja con el problema, la
  competición o las reglas.

### 4.1 Búsqueda local y CDCL

| Técnica | Evidencia | Efecto publicado | Veredicto |
|---|---|---|---|
| Cooperación profunda CDCL + SLS: fases de SLS y frecuencia de conflicto en la ramificación | Cai y Zhang (2021); Cai et al. (2022, JAIR) | +10 instancias en Kissat (SC2020); ganador de SAT en SC2020 | **Ya en Kissat** (`walk`/`target`/`rephase`) |
| Mejoras de probSAT: multinivel, PNF, Sparrow | Balint et al. (2010, 2014); Fu et al. (2020) | Grandes, pero en **k-SAT aleatorio** | D-no aplica: el Main Track es sobre todo industrial |
| Inicialización de SLS con una red neuronal (NLocalSAT) | Zhang et al. (2020) | +27–62 % en el random track de 2018 | D-no aplica |
| *Deep restart*: reinicio que aleatoriza actividades y fases | Li et al. (2025) | +14 SAT (352→366, McNemar p < 0,05); −2,1 % en UNSAT | D-ruido: ~4 % en SAT y un coste en UNSAT |

### 4.2 Colas pesadas y reinicios

| Técnica | Evidencia | Efecto publicado | Veredicto |
|---|---|---|---|
| Colas pesadas en la RTD, y reinicios aleatorizados para romperlas | Gomes et al. (1997, 2000); Chen et al. (2001); Williams et al. (2003) | Hasta dos órdenes de magnitud en DPLL | **Ya en Kissat**. Base teórica de todo lo demás |
| Estrategia universal de Luby y sus mejoras | Luby et al. (1993); Scaman (2023); Lorenz (2021) | Óptima hasta un log; Scaman reduce el log | Ya en Kissat (`reluctant`). Mejora teórica, sin evidencia en CDCL: **D-ruido** |
| RTD de CDCL multimodales (mezclas de Weibull) | Krüger et al. (2022, PLoS ONE); Lorenz y Wörz (2022) | Explica por qué hace falta olvidar y reiniciar | Sirve para **evaluar** (§4.7), no como heurística |
| Reinicios con aprendizaje automático (predicción del LBD) | Liang et al. (2018) | Mejor que las políticas de su momento (SC2014–17) | D-ruido: Kissat ya tiene reinicios EMA y Luby afinados |
| *Resets* con bandidos (UCB, Thompson) | Li et al. (2024) | Mejor que la base en Satcoin y SC | D-ruido: efecto modesto y concentrado en Satcoin |
| **Reinicios dinámicos bayesianos**: predecir la longitud de la corrida a partir de su comienzo | Horvitz et al. (2001, UAI); Kautz et al. (2002, AAAI) | Mejor que el corte fijo óptimo en CSP estructurados | Como heurística interna: D-ruido. Como **marco de decisión para B3**: **R** (§6, R1) |

### 4.3 Bandidos y aprendizaje en línea

| Técnica | Evidencia | Efecto publicado | Veredicto |
|---|---|---|---|
| LRB y CHB: ramificación como bandido (ERWA) | Liang et al. (2016a, 2016b, 2017) | CHB: +16 % en MiniSat y +5,6 % en Glucose frente a VSIDS | D-ruido **sobre Kissat**, que ya combina VSIDS en stable y VMTF en focused |
| **Kissat_MAB**: el bandido elige entre VSIDS y CHB en cada reinicio | Cherif et al. (2021); Liu et al. (2025, MAB-DC, 2.º en SC2024); Xie et al. (2025, revisión) | Buenos puestos en competición; mejoras incrementales sobre Kissat | **A**. Hay evidencia de competición: el mejor solver con etiqueta IA en 2026, `kissat-mab-hypre-evolve`, es de esta familia. Pero nuestro precedente (EXP-006, nulo) y un efecto incremental la dejan por debajo de nuestro ruido. Solo como **variante V3/V4** si sobra tiempo (D-014) |
| Bandidos en MaxSAT (BandHS) | Zheng et al. (2024, AIJ) | Ganador en MaxSAT Evaluation | D-no aplica |

### 4.4 Inferencia probabilística

| Técnica | Evidencia | Efecto publicado | Veredicto |
|---|---|---|---|
| Survey propagation y decimación | Braunstein, Mézard y Zecchina (2005); Schwimmer et al. (2019, *streamlining*) | Cerca del umbral de satisfacibilidad en k-SAT aleatorio | D-no aplica: industrial ≠ aleatorio |
| **BMM**: posterior de la asignación para iniciar fases y orden | Duan et al. (2020); Vallade et al. (2022, diversificación en paralelo) | +12 instancias sobre MapleCOMSPS (SC2018); supera a SP, a Jeroslow-Wang y al azar en criptografía | **A**. Coste moderado (una pasada antes de resolver), pero se solapa con `warmup`, `walk` y `target` de Kissat. Probablemente por debajo de nuestro ruido |
| p-bits / Ising | Bino (2026, arXiv) | −80 % de conflictos, pero solo en 3-SAT aleatorio con *backbone* controlado | D-no aplica. Pero su **puerta con bosque aleatorio** (retiene el 94,8 % de las victorias) respalda R1 |
| Probabilidades condicionales en circuitos (CASCAD) | Zhu et al. (2025) | Hasta 10× en LEC | D-no aplica: necesita el circuito (AIG), no la CNF |

### 4.5 Predicción con redes neuronales

| Técnica | Evidencia | Efecto publicado | Veredicto |
|---|---|---|---|
| **NeuroBack**: una sola inferencia GNN antes de resolver predice las fases del *backbone* | Wang et al. (2024, ICLR) | **+5,2 % y +7,4 %** de instancias resueltas por Kissat en SC2022 y SC2023; solo CPU | **A**, con el mayor efecto publicado **sobre Kissat**. Coste alto: modelo entrenado (DataBack, 120 000 muestras), inferencia dentro del binario de competición, riesgo de generalización y licencia por revisar. Estudiar solo tras H5 |
| NeuroCore: la GNN predice el núcleo UNSAT y reemplaza periódicamente la actividad | Selsam y Bjørner (2019) | +10 % en MiniSat y +11 % en Glucose (SC2018); menos en Z3 | A/D: sobre solvers antiguos. En Kissat el margen es menor y hace falta una GPU o un modelo pequeño |
| Orden inicial aprendido; fases con una GRU | Eriksson et al. (2026); Wang (2026) | Falla en industriales difíciles, porque las heurísticas dinámicas **sobrescriben** la inicialización; +1,5–2,5 % sobre NeuroBack | D-ruido |
| Predecir SAT/UNSAT de extremo a extremo (NeuroSAT, TG-SAT, DeepSAT) | Chang et al. (2024); Li et al. (2023) | Precisión en aleatorias y AIG | D-no aplica como solver |

### 4.6 Borrado de cláusulas con aprendizaje

| Técnica | Evidencia | Efecto publicado | Veredicto |
|---|---|---|---|
| NeuroSelect: el aprendizaje automático elige la política de borrado por instancia | Liu et al. (2024, DAC) | **−5,8 %** de tiempo en Kissat, sobre industriales grandes | D-ruido: 5,8 % queda por debajo de nuestro umbral |
| Borrado con RL; top-k no dominadas; comunidad | Vaezipoor et al. (2020); Lonlac et al. (2017, 2022); Ansótegui et al. (2015, 2016) | Preliminar o modesto | D-ruido |

### 4.7 Selección, configuración y evaluación: la parte de las métricas

| Técnica | Evidencia | Uso posible | Veredicto |
|---|---|---|---|
| Modelos de dureza empírica y **modelos jerárquicos** (probabilidad de SAT/UNSAT y mezcla de expertos) | Nudelman et al. (2004); Xu et al. (2007, 2008, SATzilla); Hutter et al. (2014, AIJ) | Estimar **por instancia** si la ruptura de simetrías ayudará (B3). La confianza del clasificador se correlaciona con su error | **R** (R1) |
| **Selección con análisis de supervivencia** (datos censurados, aversión al riesgo de timeout) | Tornede et al. (2020, Run2Survive) | Decidir la opción que minimiza el PAR-2 **esperado**, teniendo en cuenta que un timeout cuesta 2T | **R** (R1) |
| Carteras de solvers (SATzilla, MachSMT) | Xu et al. (2008); Scott et al. (2021) | — | D-no aplica: la competición no admite carteras de solvers distintos, y LabeSAT es un solo solver (D-016) |
| Configuración automática (SMAC, ParamILS, SpySMAC, DAC) | Hutter et al. (2009, 2011); Lindauer et al. (2022); Falkner et al. (2015); Adriaensen et al. (2022) | Afinar pocos parámetros (umbrales de B3, topes de satsuma) con validación aparte | **R**, limitada a R3. **D** para afinar Kissat entero: sobreajuste y cientos de horas de CPU |
| Análisis estadístico de las comparaciones | Nikolić (2010); Brglez et al. (2004); Brain et al. (2017) | Lo que ya hace ADR-0003, más curvas de supervivencia | **R** (R2) |
| **Rankings frágiles**: remuestreo de instancias | Fawcett et al. (2023) | Los rankings cambian con pequeñas variaciones del banco; hay empates estadísticos frecuentes | **R** (R2): IC de PAR-2 remuestreando instancias. Ya lo hacemos con el bootstrap; hay que aplicarlo también a los estratos |
| **Variabilidad entre semillas** | Hurley y O'Sullivan (2015): los tres primeros de SC2014 podían quedar en cualquier orden | Justifica usar 2 o más semillas, y hace falta medir cuánta varianza aporta cada una | **R** (R2) |
| Barajar las CNF (*scrambling*) | Biere y Heule (2019) | Cambia el rendimiento de cada solver, pero poco el ranking | R2 (menor): comprobar que las mejoras no dependen del orden de las cláusulas |
| Benchmarking con aprendizaje activo | Fuchs et al. (2025, JAR) | Predice el ranking con el 10 % del tiempo (92 % de acierto) | **A**: útil para cribar ideas baratas antes de un A/B completo |

### 4.8 Otros

| Técnica | Evidencia | Veredicto |
|---|---|---|
| MCTS: UCT-SAT, Monte Carlo Forest Search, AlphaMapleSAT | Schlöter (2017); Keszocze et al. (2019); Cameron et al. (2022); Jha et al. (2024) | D-no aplica: sin evidencia en industriales secuenciales. AlphaMapleSAT es *cube-and-conquer* en 128 núcleos |
| Evolución de solvers con LLM (AutoSAT, SATLUTION) | Sun et al. (2024); Yu et al. (2025, arXiv 2509.07367: supera a los ganadores de SC2025) | Fuera del alcance (no es probabilístico). Se anota por la subcategoría IA: los mejores solvers con etiqueta IA de 2026 vienen de aquí |
| Fases LSIDS (tendencia de polaridad) | Shaw y Meel (2020): +6 instancias, −125 s de PAR-2 sobre MapleLCMDistChronoBTv3 | D-ruido: Kissat ya usa fases objetivo y mejores fases |

## 5. Exploración con nuestros datos: ¿repartir el tiempo o elegir?

> **Exploratorio**: se hizo con los datos de EXP-007 (semilla 1, T = 180 s),
> los mismos que se usarían para decidir. Sirve para orientar, **no** como
> resultado.

La literatura de reinicios y carteras (Luby et al., 1993; Gomes et al., 2000)
sugiere una alternativa a elegir entre aplicar o no la ruptura: **repartir el
tiempo**. Se da un tramo t0 a una opción y el resto a la otra. Simulado sobre
EXP-007 (PAR-2 medio en segundos; H = ayuda, N = neutro, X = daña):

| Política | Total | H (45) | N (22) | X (7) |
|---|---:|---:|---:|---:|
| Sin ruptura (A) | 209,3 | 306,1 | 31,2 | 146,8 |
| Siempre con ruptura (B) | **69,0** | 72,4 | 40,4 | 137,6 |
| Ruptura durante t0 y después sin ella, t0 = 5 s | 79,2 | 89,3 | 35,7 | 150,4 |
| Ídem, t0 = 30 s | 71,4 | 76,1 | 51,1 | 105,3 |
| Sin ruptura durante t0 y después con ella, t0 = 5 s | 72,6 | 76,5 | 45,0 | 134,4 |
| **Oráculo** (la mejor de A y B por instancia) | **57,0** | 65,2 | 29,1 | 92,0 |

**Lectura**:
- Repartir el tiempo **no mejora** a aplicar siempre la ruptura en este banco:
  lo que se gana en N se pierde en H.
- El margen está entre B (69,0) y el oráculo (57,0): **−17 %**, y solo se
  consigue **eligiendo bien por instancia**.
- La recomendación principal (R1) es, por tanto, un **clasificador
  probabilístico** y no un reparto de tiempo.

## 6. Recomendaciones (por orden)

### R1 — B3 como decisión probabilística calibrada (prioridad alta)

- **Qué**: decidir por instancia si Kissat resuelve la CNF con ruptura o la
  original, con:
  - una **probabilidad calibrada** p = P(la ruptura ayuda | rasgos);
  - una **regla de coste esperado**: se aplica si
    p · ganancia esperada > (1 − p) · coste esperado, con el timeout costando
    2T (Tornede et al., 2020; Horvitz et al., 2001).
- **Rasgos baratos**: los que satsuma ya calcula (generadores, filas u
  órbitas, cláusulas y unidades añadidas, refutación directa) y los de la CNF
  (tamaños, proporciones; Nudelman et al., 2004).
- **Modelo**: bosque aleatorio o regresión logística, entrenado con datos de
  2026 **sin** `bench/test`, como en el modelo jerárquico de Xu et al. (2007)
  y la puerta de Bino (2026).
- **Encaje**:
  - es la prioridad n.º 1 del plan (P2, H4, EXP-009);
  - con D-016 va **dentro** de Kissat (fase 2 de ADR-0007);
  - si no hay rasgos suficientes antes de ejecutar satsuma, la decisión se
    toma **después** de satsuma: su coste en N es pequeño; lo caro es la
    búsqueda sobre la fórmula modificada (EXP-007, exploratorio).
- **Medible**: sí. El margen explorado es de −12 s sobre 69 s en EXP-007, en
  instancias donde cambia el estado.
- **Riesgo**: sobreajuste con pocas instancias de X. Se valida en un banco
  aparte, preregistrado.
- **Declaración de IA**: el umbral y el modelo son heurísticas ajustadas con
  IA, y se declaran.

### R2 — Métricas y evaluación más robustas (prioridad alta, coste bajo)

Mejora **cómo medimos**, sin tocar el solver. Todo es análisis sobre datos que
ya generamos:

1. **Curvas de supervivencia** (Kaplan–Meier), además del PAR-2, en cada
   experimento, con los timeouts como datos censurados (Brglez et al., 2004;
   Brain et al., 2017; Tornede et al., 2020).
2. **IC por remuestreo de instancias en cada estrato** para las estimaciones
   post-estratificadas (Fawcett et al., 2023). Hoy se hace para el total.
3. **Varianza entre semillas**: medirla en los bancos de calibración para
   decidir cuántas semillas hacen falta (Hurley y O'Sullivan, 2015).
4. Opcional: ajustar mezclas de Weibull a los tiempos censurados (Krüger et
   al., 2022) para **ilustrar**, nunca para afirmar, cómo se extrapolaría el
   PAR-2 de 180 s a 5000 s. Se declara como modelo, no como medida.

- **Encaje**: amplía ADR-0003 y `par2.py`.
- **Medible**: no aplica; es infraestructura de medida.
- **Ruido**: al contrario, sirve para **reducirlo**.

### R3 — Topes de satsuma por cuantiles de su distribución de tiempos (prioridad media, coste bajo)

- **Qué**: fijar `LABESAT_SYMM_TIMEOUT` (y el presupuesto de mclique) con la
  distribución empírica de tiempos de satsuma que ya tenemos (EXP-010 y
  EXP-011, parte 1).
- **Cómo**: la teoría de cortes de Luby et al. (1993) dice que un corte fijo
  bien elegido es óptimo si la distribución se conoce. Se elige el cuantil que
  minimiza el PAR-2 esperado, contando que pasado el corte se cae a la CNF
  original.
- **Encaje**: P5 del plan. Pocos parámetros, así que es configuración
  «pequeña» (§4.7), con validación aparte.
- **Medible**: solo cambia instancias concretas (las que tocan el tope); se
  cuentan.

### Aparcadas (se revisan después de H5, el 25 de enero de 2027)

| Técnica | Por qué merece la pena | Por qué no ahora |
|---|---|---|
| **NeuroBack** | El mayor efecto publicado **sobre Kissat** (+5–7 % de instancias resueltas) | Modelo, datos de entrenamiento e inferencia dentro del binario; licencia y portabilidad por revisar |
| **BMM** para iniciar fases y orden | +12 instancias sobre la base en SC2018; barato de ejecutar | Se solapa con `warmup`, `walk` y `target`; efecto esperado bajo nuestro ruido |
| **Bandido VSIDS/CHB** (Kissat_MAB) | Buenos puestos en competición en 2021–2026 | Efecto incremental; precedente nulo (EXP-006). Como mucho, una **variante** (D-014) |
| Benchmarking con aprendizaje activo | Criba barata de ideas | Nuestros bancos ya son pequeños |

### Descartadas por ruido (efecto publicado pequeño frente a lo que podemos medir)

- reinicios con aprendizaje automático (Liang et al., 2018);
- *resets* con RL (Li et al., 2024);
- *deep restart* (Li et al., 2025);
- LSIDS (Shaw y Meel, 2020);
- NeuroSelect (Liu et al., 2024);
- LRB, CHB y GLR sobre Kissat;
- orden inicial aprendido (Eriksson et al., 2026);
- la mejora teórica de Luby (Scaman, 2023).

### Descartadas porque no aplican

- SP y BP;
- p-bits (Ising);
- CASCAD;
- mejoras de SLS pensadas para k-SAT aleatorio;
- NLocalSAT;
- MCTS;
- carteras de solvers distintos;
- bandidos para MaxSAT;
- diversificación en paralelo (el Main Track es secuencial).

## 7. Qué cambia en el plan

- **R1** afina el diseño de EXP-009 (B3): pasa a ser una decisión
  probabilística calibrada con una regla de coste esperado, y se implementa
  dentro de Kissat (ADR-0007, fase 2).
- **R2** se incorpora a ADR-0003 y a `par2.py` en un PR aparte.
- **R3** se hace junto con P5, con los datos de EXP-010 y EXP-011.
- Nada de esto cambia los experimentos en curso.

## 8. Referencias

En orden alfabético. Los enlaces son los de la búsqueda: Consensus, arXiv,
OpenReview o la editorial.

- Adriaensen, S., et al. (2022). Automated dynamic algorithm configuration. *JAIR*. https://consensus.app/papers/details/78a40c6d53545395ad430893b0618841/
- Ansótegui, C., et al. (2015). Using community structure to detect relevant learnt clauses. *SAT*. https://consensus.app/papers/details/ce2308c194f95defb069efbbbe8be107/
- Ansótegui, C., et al. (2016). Community structure in industrial SAT instances. *JAIR*. https://consensus.app/papers/details/329cbee03a305832915eb8c5334f203e/
- Audemard, G., y Simon, L. (2009). Predicting learnt clauses quality in modern SAT solvers. *IJCAI*. https://consensus.app/papers/details/4bde78c76c9e54aa9d67a13516865458/
- Audemard, G., y Simon, L. (2012). Refining restarts strategies for SAT and UNSAT. *CP*. https://consensus.app/papers/details/b52b96e19d8350cb9b7341cfb015a3e8/
- Balint, A., y Fröhlich, A. (2010). Improving stochastic local search for SAT with a new probability distribution (Sparrow). *SAT*. https://consensus.app/papers/details/61a432ea87335e33bb72257b5962670c/
- Balint, A., y Schöning, U. (2012). Choosing probability distributions for stochastic local search and the role of make versus break (probSAT). *SAT*. https://consensus.app/papers/details/ca8feba3704051679d6901f92f758202/
- Balint, A., et al. (2014). Improving implementation of SLS solvers for SAT and new heuristics for k-SAT with long clauses. *SAT*. https://consensus.app/papers/details/1c28341ae3df5025a6f903bf4c4244b3/
- Biere, A., y Fleury, M. (2020). Chasing target phases. *POS*. https://consensus.app/papers/details/2fd2e373c6d057ae8f76a7db6f527274/
- Biere, A., y Fröhlich, A. (2019). Evaluating CDCL restart schemes. *POS*. https://consensus.app/papers/details/e816511e586a5db69872fa9886cb26ce/
- Biere, A., y Heule, M. (2019). The effect of scrambling CNFs. *POS*. https://consensus.app/papers/details/658f9fedeed859c983e67cc5d5ff1034/
- Bino, M. (2026). Probabilistic-bit guided CDCL for SAT solving using Ising consensus assumptions. *arXiv*. https://consensus.app/papers/details/acda9a5395155f33a1caea588427e82c/
- Brain, M., et al. (2017). Benchmarking solvers, SAT-style. *SC²*. https://consensus.app/papers/details/be98822a5c685190a9c8f0af3ff01a72/
- Braunstein, A., Mézard, M., y Zecchina, R. (2005). Survey propagation: an algorithm for satisfiability. *Random Structures & Algorithms*, 27(2), 201–226. https://doi.org/10.1002/rsa.20057
- Brglez, F., et al. (2004). On SAT instance classes and a method for reliable performance experiments with SAT solvers. *AMAI*. https://consensus.app/papers/details/0b9cadf4f8ec51bbbc895a2544bddaaa/
- Cai, S., y Zhang, X. (2021). Deep cooperation of CDCL and local search for SAT. *SAT*. https://consensus.app/papers/details/85d8ee4106335645a1837921b9540329/
- Cai, S., et al. (2022). Better decision heuristics in CDCL through local search and target phases. *JAIR*. https://consensus.app/papers/details/02d348bce7e1550389cde6055137121a/
- Cameron, C., et al. (2022). Monte Carlo forest search: UNSAT solver synthesis via reinforcement learning. https://consensus.app/papers/details/bd1d185367bf5f47bf157f97beb58b6e/
- Chen, H., Gomes, C., y Selman, B. (2001). Formal models of heavy-tailed behavior in combinatorial search. *CP*. https://consensus.app/papers/details/43926d34afd45c398b37602c99d98ad4/
- Cherif, M. S., et al. (2021). Combining VSIDS and CHB using restarts in SAT. *CP*. https://consensus.app/papers/details/0ab2865d8087560d91b93addede0a0d4/
- Duan, H., et al. (2020). Online Bayesian moment matching based SAT solver heuristics. *ICML*. https://consensus.app/papers/details/6f3f37afc01a54b4a7f3c5ca062bb39c/
- Eriksson, A., et al. (2026). Learning to rank the initial branching order of SAT solvers. *arXiv* 2603.07176. https://arxiv.org/pdf/2603.07176
- Falkner, S., et al. (2015). SpySMAC: automated configuration and performance analysis of SAT solvers. *SAT*. https://consensus.app/papers/details/176b3fc8c4b25c8c9c606b99f089969b/
- Fawcett, C., et al. (2023). Competitions in AI: robustly ranking solvers using statistical resampling. *arXiv*. https://consensus.app/papers/details/1e7e2edce36d543ab78dc916b65c93d5/
- Froleyks, N., et al. (2021). SAT Competition 2020. *AIJ*. https://consensus.app/papers/details/0825e1e4984f5f4bb9adfd132e4725cc/
- Fu, H., et al. (2020). Focused random walk with probability distribution for SAT with long clauses. *Applied Intelligence*. https://consensus.app/papers/details/cd945c5d0afc5b43af2f5d7ba8693b23/
- Fuchs, T., et al. (2025). Active learning for SAT solver benchmarking. *JAR*. https://consensus.app/papers/details/b2ef4be629a550df967ba1554b64a94e/
- Gomes, C., Selman, B., y Crato, N. (1997). Heavy-tailed distributions in combinatorial search. *CP*. https://consensus.app/papers/details/8bc110891d3c57d483912e4226c9aaf3/
- Gomes, C., Selman, B., Crato, N., y Kautz, H. (2000). Heavy-tailed phenomena in satisfiability and constraint satisfaction problems. *JAR*. https://consensus.app/papers/details/e70ec2f407905a10b7ed51866e6bdff6/
- Gstrein, B., et al. Learn to unlearn (borrado de cláusulas en Kissat). https://consensus.app/papers/details/5757281f624c5447b75efb486bc6e43e/
- Guo, W., et al. (2022). Machine learning methods in solving the Boolean satisfiability problem. *Machine Intelligence Research*. https://consensus.app/papers/details/df8e3830d60951e0b26c33d67fde7e10/
- Hamadi, Y., y Wintersteiger, C. M. (2013). Seven challenges in parallel SAT solving. *AI Magazine*, 34(2). https://doi.org/10.1609/aimag.v34i2.2450
- Horvitz, E., Ruan, Y., Gomes, C., Kautz, H., Selman, B., y Chickering, M. (2001). A Bayesian approach to tackling hard computational problems. *UAI*. https://arxiv.org/abs/1301.2279
- Hurley, B., y O'Sullivan, B. (2015). Statistical regimes and runtime prediction. *IJCAI*. https://consensus.app/papers/details/b66954e34e2655f3bb4855db8550fefc/
- Hutter, F., et al. (2006). Performance prediction and automated tuning of randomized and parametric algorithms. *CP*. https://consensus.app/papers/details/93678bd1d70850219bf35cb41b642d70/
- Hutter, F., et al. (2009). ParamILS: an automatic algorithm configuration framework. *JAIR*. https://consensus.app/papers/details/18eca283bbad533490d238316566aae7/
- Hutter, F., Hoos, H., y Leyton-Brown, K. (2011). Sequential model-based optimization for general algorithm configuration (SMAC). *LION*. https://consensus.app/papers/details/957946f90eb05ddfb56351fc6f0c2dcd/
- Hutter, F., et al. (2014). Algorithm runtime prediction: methods & evaluation. *AIJ*. https://consensus.app/papers/details/3d26c5d351d951e0bfc7b9dfed1d4606/
- Jha, P., et al. (2024). AlphaMapleSAT: an MCTS-based cube-and-conquer SAT solver. *arXiv*. https://consensus.app/papers/details/c70bf621a43357c1b47175804dcdeb02/
- Kautz, H., Horvitz, E., Ruan, Y., Gomes, C., y Selman, B. (2002). Dynamic restart policies. *AAAI*. https://erichorvitz.com/drestart.pdf
- Keszocze, O., et al. (2019). Improving SAT solving using Monte Carlo tree search-based clause learning. https://consensus.app/papers/details/bef45683f14d569984ef442b2762e6f8/
- Krüger, T., et al. (2022). Too much information: why CDCL solvers need to forget learned clauses. *PLoS ONE*. https://consensus.app/papers/details/9343b43bca9857eb94d5e7dabe65cd53/
- Li, C., et al. (2020). Towards a complexity-theoretic understanding of restarts in SAT solvers. *SAT*. https://consensus.app/papers/details/edc1f5ba7d0f5844aa5bbc37a830b10e/
- Li, C., et al. (2024). A reinforcement learning based reset policy for CDCL SAT solvers. *arXiv*. https://consensus.app/papers/details/de3f298a13095778a7d04ad185ca4fa0/
- Li, M., et al. (2023). On EDA-driven learning for SAT solving (DeepSAT). *DAC*. https://consensus.app/papers/details/eebab9a5673d5d6c8b337df70e4d748d/
- Li, Z., et al. (2025). Instance assignment coverage feature for operation control of SAT solver (DR-CDCL). *IJCIS*. https://consensus.app/papers/details/b096d9b4c674577d82a77a4eabd74dac/
- Liang, J. H., et al. (2016a). Exponential recency weighted average branching heuristic for SAT solvers (CHB). *AAAI*. https://consensus.app/papers/details/d174c4cf1db75bafbd25b284ef517c56/
- Liang, J. H., et al. (2016b). Learning rate based branching heuristic for SAT solvers (LRB). *SAT*. https://consensus.app/papers/details/cad1f872b1b05b63b42e240fcf32dd1e/
- Liang, J. H., et al. (2017). An empirical study of branching heuristics through the lens of global learning rate. *SAT*. https://consensus.app/papers/details/6a75a10a1ca050f0b0c2ac612dea6a56/
- Liang, J. H., et al. (2018). Machine learning-based restart policy for CDCL SAT solvers. *SAT*. https://consensus.app/papers/details/2e29b6dbdbbc5889b561637c71b70e5d/
- Lindauer, M., et al. (2022). SMAC3: a versatile Bayesian optimization package for hyperparameter optimization. *JMLR*. https://consensus.app/papers/details/40898e30074057e5ada68b72cff00b62/
- Liu, H., et al. (2024). NeuroSelect: learning to select clauses in SAT solvers. *DAC*. https://consensus.app/papers/details/5111ab4f9ca857faab7be5bab37bf75f/
- Liu, J., et al. (2025). Reward defining in multi-armed bandit SAT strategy (Kissat_MAB-DC). *ISCAIT*. https://consensus.app/papers/details/f4bee374a83f522396f0cece9ea96f67/
- Lorenz, J.-H. (2021). Restart strategies in a continuous setting. *Theory of Computing Systems*. https://consensus.app/papers/details/fd4c26db7534513794d68285bef63472/
- Luby, M., Sinclair, A., y Zuckerman, D. (1993). Optimal speedup of Las Vegas algorithms. *Information Processing Letters*, 47(4), 173–180. https://consensus.app/papers/details/70941bae7e0b5710afe5b14b97ef0952/
- Nikolić, M. (2010). Statistical methodology for comparison of SAT solvers. *SAT*. https://consensus.app/papers/details/886200f5a06153d0891cd068b44b8df3/
- Nudelman, E., et al. (2004). Understanding random SAT: beyond the clauses-to-variables ratio. *CP*. https://consensus.app/papers/details/26f13d2e5b74559d8e601953c040429a/
- Oh, C. (2015). Between SAT and UNSAT: the fundamental difference in CDCL SAT. *SAT*. https://consensus.app/papers/details/cef24087298353a983168fa161f52cda/
- Scaman, K. (2023). Breaking the log barrier: a novel universal restart strategy for faster Las Vegas algorithms. *arXiv*. https://consensus.app/papers/details/c4eaa7b77e7d5f74a1f4b05f4ca082ca/
- Schwimmer, A., et al. (2019). Streamlining constraints y survey propagation. *J. Stat. Mech.* https://consensus.app/papers/details/05ed5e0597c955528ce005395f1fa23a/
- Scott, J., et al. (2021). MachSMT: a machine learning-based algorithm selector for SMT solvers. *TACAS*. https://consensus.app/papers/details/e27a35240e975fd087713a0635cf6be3/
- Selsam, D., y Bjørner, N. (2019). Guiding high-performance SAT solvers with unsat-core predictions (NeuroCore). *SAT*. https://arxiv.org/abs/1903.04671
- Shaw, A., y Meel, K. S. (2020). Designing new phase selection heuristics. *SAT*. https://consensus.app/papers/details/56d79a86f6f35bedb8f4156481d980f0/
- Sun, Y.-W., et al. (2024). AutoSAT: automatically optimize SAT solvers via large language models. *arXiv*. https://consensus.app/papers/details/10edef7249f95397a6baf82b6e13dfe0/
- Tornede, A., et al. (2020). Run2Survive: a decision-theoretic approach to algorithm selection based on survival analysis. *ACML*. https://consensus.app/papers/details/d3095babbf6c5d79a5b9a32199b085d3/
- Vallade, V., et al. (2022). Diversifying a parallel SAT solver with Bayesian moment matching. https://consensus.app/papers/details/ecb46e96ad115c069ea91606c37b321d/
- Wang, W., et al. (2024). NeuroBack: improving CDCL SAT solving using graph neural networks. *ICLR*. https://openreview.net/forum?id=samyfu6G93
- Williams, R., Gomes, C., y Selman, B. (2003). On the connections between backdoors, restarts, and heavy-tailedness in combinatorial search. *SAT*. https://consensus.app/papers/details/c5c1b233331056edb7360662cccc6826/
- Xie, Z., et al. (2025). Multi-armed bandit algorithms for the Boolean satisfiability problem: a survey. https://consensus.app/papers/details/2007739f56d4542ab8298988a4079666/
- Xu, L., Hoos, H., y Leyton-Brown, K. (2007). Hierarchical hardness models for SAT. *CP*. https://consensus.app/papers/details/d6d53c6a55f35c1f9acefe7dbac2aabe/
- Xu, L., Hutter, F., Hoos, H., y Leyton-Brown, K. (2008). SATzilla: portfolio-based algorithm selection for SAT. *JAIR*. https://consensus.app/papers/details/bcbe9eb295255406a34e72c933f3c826/
- Yu, C., Liang, R., Ho, C.-T., y Ren, H. (2025). Autonomous code evolution meets NP-completeness (SATLUTION). *arXiv* 2509.07367. https://arxiv.org/abs/2509.07367
- Zhang, W., et al. (2020). NLocalSAT: boosting local search with solution prediction. *IJCAI*. https://consensus.app/papers/details/5c25d2b08b2b58ef85b4eb35c03a135f/
- Zheng, J., et al. (2024). Integrating multi-armed bandit with local search for MaxSAT. *AIJ*. https://consensus.app/papers/details/de1c04debc37535089f1715193b5312a/
- Zhu, J., et al. (2025). Circuit-aware SAT solving: guiding CDCL via conditional probabilities (CASCAD). *arXiv*. https://consensus.app/papers/details/864f3aa768b553e0b7940877f0fec838/
