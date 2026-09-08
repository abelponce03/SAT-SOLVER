# Investigación 07 — Enfoques probabilísticos y GNN para SAT

> Encargo: estado del arte de modificaciones con **enfoques probabilísticos** y
> **redes neuronales de grafos (GNN)** en solvers CDCL, para estudiarlas como
> posible contribución. Documento de estudio; fuentes al final.

Contexto del proyecto: buscamos algo **tratable en solitario, sin GPU/cluster, y
diferenciado** (ver doc 06). Estos dos enfoques son atractivos pero tienen una
trampa recurrente que este documento hace explícita.

---

## 0. TL;DR (la lección que se repite)

Tanto GNN como métodos probabilísticos comparten el **mismo patrón de viabilidad**
que ya vimos con los bandits (docs 03–06):

1. **Brillan en instancias aleatorias/uniformes; flojean en estructuradas/
   industriales** — que son el pan de la Main Track. Es el mismo eje
   random↔estructurado que atraviesa todo el proyecto.
2. **La integración viable es de bajo coste: una sola pasada o "gated"**, no
   consultar un modelo en el bucle caliente. Predecir algo barato *una vez*
   (fases iniciales, marginales BP, literales de alta concordancia) y pasarlo a
   CDCL como **inicialización o assumptions** — nunca por decisión.
3. **Un "gate" por features que decida CUÁNDO aplicar la técnica es, en sí mismo,
   un patrón ganador** (el paper p-bit usa un random forest; nosotros lo hemos
   llamado "selector estilo-SATzilla-de-un-autor").

Consecuencia para nosotros: la contribución diferenciada no es "meter una GNN"
(no es competitivo, §2.5) ni "reimplementar survey propagation" (ya existe y es
para random). Es el **patrón gate + inicialización de una pasada**, que además
compone con el eje de robustez (doc 03) y con la instrumentación que ya tenemos.

---

## 1. Enfoques probabilísticos

### 1.1 Survey Propagation (SP) y Belief Propagation (BP)
Sobre el *factor graph* de la fórmula se propagan mensajes que aproximan
**marginales** (probabilidad de que cada variable sea True/False en las
asignaciones satisfactorias). SP (Braunstein–Mézard–Zecchina) añade un tercer
estado "joker" (podría ir de cualquier forma).
- **Fortaleza**: domina el **3-SAT aleatorio en la transición de fase**; resuelve
  instancias de **millones de variables** en tiempo casi lineal en la región dura.
- **Debilidad**: en instancias **estructuradas/industriales** BP/SP **no
  converge o no ayuda** — justamente el régimen de la competición. Por eso ningún
  ganador reciente de la Main Track usa SP como motor.
- Familia unificada: cualquier fórmula se asocia a una familia de MRF
  parametrizada por ρ∈[0,1]; ρ=1 = SP puro, ρ=0 = BP sobre la uniforme.

### 1.2 Estimación de backbone / bias para branching (Hsu et al., CP'08)
Usa BP para estimar el **bias** de cada variable (sesgo hacia True/False) y el
**backbone** (variables fijas en todas las soluciones), y sesga el branching hacia
ahí. Precursor directo del patrón "predecir fase/estructura y sesgar la búsqueda".

### 1.3 p-bit / Ising guiando CDCL (arXiv:2605.04033, 2026) — el más relevante
Un **muestreador Ising de p-bits** propone **literales de alta concordancia** que
se pasan a CDCL **como assumptions temporales**; si no son productivas, CDCL hace
*fallback* (se preserva la corrección).
- **Resultados**: en 3-SAT aleatorio controlado reduce la **mediana de conflictos
  80.8–85.5%** y de propagaciones 80–85% frente a CDCL puro.
- **Pero es instance-dependent**: solo ayuda en ciertas clases → entrenan un
  **random forest** que decide cuándo activar el híbrido (**retiene el 94.8% de
  las victorias**). Ese *gate* es la pieza clave y transferible.
- Integración: "assumptions" es exactamente la interfaz **IPASIR de CaDiCaL** →
  este patrón es **implementable en nuestro fork sin tocar el core del solver**.

### 1.4 Clause weighting probabilístico (SLS: SAPS, PAWS)
En búsqueda local, pesos de cláusula actualizados estocásticamente. Relevante
solo para la parte "walk" de CDCL modernos; no es nuestra vía principal.

---

## 2. Enfoques GNN

Se representa la CNF como grafo (literal–cláusula, o variable–cláusula) y una GNN
de paso de mensajes produce una señal. Taxonomía por **cómo** se acopla al solver:

### 2.1 End-to-end (NeuroSAT, 2018)
La GNN predice SAT/UNSAT y se intenta extraer una asignación. **Prueba de
concepto**, no competitivo: no escala ni generaliza a industriales.

### 2.2 Guía online por RL (Graph-Q-SAT 2020; Yolcu & Poczos 2019)
La GNN se consulta **en cada decisión** de branching, entrenada por RL.
**Inviable en instancias grandes**: el coste por paso domina; las heurísticas
clásicas corren en tiempo constante.

### 2.3 Predicción de unsat-core para branching (NeuroCore, 2019)
Predice qué variables están en el unsat-core y las prioriza. Mejora real, pero
**consultas periódicas de la GNN y dependencia de GPU**. Versión 2026:
predicción de unsat-core sobre *hipergrafos cláusula-literal polaridad-aware
(arXiv:2605.04819)*.

### 2.4 Predicción de fase offline de UNA pasada (NeuroBack, ICLR'24) — el patrón viable
Predice, **una sola vez antes de resolver**, la fase (valor) de cada variable en
la mayoría de asignaciones satisfactorias ("backbone"); **inferencia offline en
CPU, sin GPU**. Mejora a Kissat en **+5.2% (SATCOMP'22) y +7.4% (SATCOMP'23)**
instancias resueltas. Dataset *DataBack* (120k muestras) público.
- Es el único patrón GNN con historia de mejora sobre un solver top **sin** el
  problema del overhead — porque el modelo se consulta una vez y alimenta
  `phases.cpp` (que ya instrumentamos).
- Variante 2026: *Learning to Rank the Initial Branching Order* (arXiv:2603.07176)
  — mismo espíritu, ranking del orden de branching inicial.

### 2.5 Por qué las GNN NO ganan competiciones (evaluación crítica honesta)
De *Neural Approaches to SAT Solving: Design Choices and Interpretability*
(arXiv:2504.01173, 2025) y *On the Hardness of Learning GNN-based SAT Solvers*
(arXiv:2508.21513, 2025):
- **No competitivas** con el SOTA en benchmarks reales; los solvers manejan
  millones de variables, inviable para la GNN actual.
- **Overhead**: incorporar una GNN solo compensa si la mejora supera su coste;
  en CPU (nuestro caso) el forward pass es un cuello de botella.
- **Generalización**: el rendimiento cae fuerte cuando el test tiene más
  variables que el entrenamiento.
- **Límite teórico**: *oversquashing* (curvatura negativa) impide modelar
  dependencias de largo alcance — limitación fundamental, no solo de ingeniería.

> En la Main Track 2025 el único guiño "ML" fue **Kissat-pred / -pred-aggressive**
> (predicción ligera), no una GNN de propósito general. La señal del mercado es
> clara: **ligero y de una pasada, o nada**.

---

## 3. Qué de esto encaja con nuestro proyecto (y qué no)

| Enfoque | Sin GPU | Escala a industriales | Diferenciado | Encaje CaDiCaL | Veredicto |
|---|---|---|---|---|---|
| Survey/Belief Propagation | ✓ | ✗ (solo random) | ✗ (clásico) | bajo | Estudiar, no implementar como motor |
| **p-bit/Ising → assumptions + gate** | ✓* | parcial | ✓ (2026, poco explotado en CaDiCaL) | **alto (IPASIR)** | **Candidato fuerte** |
| BP-bias para branching/fase | ✓ | parcial | medio | medio (`phases.cpp`) | Componible con lo anterior |
| GNN end-to-end / RL online | ✗ | ✗ | — | — | Descartar |
| **NeuroBack (fase offline 1 pasada)** | ✓ | sí (probado en Kissat) | medio (existe) | **alto (`phases.cpp`)** | Moonshot viable (doc 01 §6) |

\* el paper p-bit no fija hardware; el muestreo Ising es simulable en CPU aunque
p-bits físicos lo acelerarían.

### La idea que emerge (síntesis con docs 03/05/06)
Un patrón unificado y tratable: **un gate ligero por features de la instancia que
decide, una sola vez, si (a) inyectar fases/assumptions predichas baratas y (b)
qué régimen de búsqueda usar** — midiéndolo con la métrica de **robustez** (doc 03)
además del PAR-2. Esto:
- toma del p-bit el *gate* (random forest → o algo aún más barato),
- toma de NeuroBack/BP la *inicialización de una pasada* (sin overhead en el bucle),
- se implementa en CaDiCaL vía `phases.cpp` (fase inicial) o IPASIR (assumptions),
- y **no compite de frente** con AE-Kissat-MAB (bandit online) ni con la
  ingeniería estructural de Freiburg.

---

## 4. Riesgos y realidades

- **Datos y entrenamiento**: cualquier predictor (GNN o random forest) necesita un
  banco etiquetado y validación *fuera de distribución* (generalización). Ya
  tenemos un banco real (GBD, doc 03) y features baratas (docs 02/04).
- **Reproducibilidad**: la comunidad penaliza modelos sobreajustados a instancias
  conocidas; medir en benchmarks nuevos es obligatorio.
- **Corrección**: pasar predicciones como *assumptions con fallback* (p-bit) o como
  *fase inicial* (NeuroBack) **no compromete la corrección** — CDCL sigue siendo
  completo. Esto es clave para la Main Track (certificados DRAT intactos).

---

## 5. Lecturas priorizadas

1. **p-bit/Ising guiando CDCL** (arXiv:2605.04033, 2026) — el gate + assumptions.
2. **NeuroBack** (ICLR'24, arXiv:2110.14053) + código https://github.com/wenxiwang/neuroback — fase offline de una pasada.
3. **Neural Approaches to SAT Solving: Design Choices and Interpretability** (arXiv:2504.01173, 2025) — panorama crítico honesto.
4. **Probabilistically Estimating Backbones and Variable Bias** (Hsu et al., CP'08) — BP-bias para branching.
5. **Survey Propagation Revisited / A new look at SP** — fundamentos probabilísticos.
6. **Learning to Rank the Initial Branching Order** (arXiv:2603.07176, 2026).

---

## Fuentes

- p-bit/Ising guided CDCL: https://arxiv.org/abs/2605.04033
- NeuroBack (ICLR'24): https://arxiv.org/abs/2110.14053 · código: https://github.com/wenxiwang/neuroback
- Neural Approaches to SAT Solving: Design Choices and Interpretability: https://arxiv.org/abs/2504.01173
- On the Hardness of Learning GNN-based SAT Solvers: https://arxiv.org/html/2508.21513
- Unsat Core Prediction over Clause-Literal Hypergraphs (2026): https://arxiv.org/pdf/2605.04819
- Learning to Rank the Initial Branching Order (2026): https://arxiv.org/html/2603.07176
- Probabilistically Estimating Backbones and Variable Bias (Hsu et al., CP'08): https://www.cs.toronto.edu/~sheila/publications/hsu-mui-bec-mci-cp08.pdf
- Constraint Satisfaction by Survey Propagation (Braunstein, Mézard, Zecchina): https://arxiv.org/pdf/cond-mat/0212451
- A new look at survey propagation and its generalizations (JACM): https://dl.acm.org/doi/10.1145/1255443.1255445
