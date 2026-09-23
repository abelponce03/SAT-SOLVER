# Investigación 01 — Modificaciones a CaDiCaL: estado del arte y frontera

> Objetivo: decidir **qué contribución** aportar sobre el fork de CaDiCaL con
> vista a la **SAT Competition 2027**. Este documento mapea (a) dónde se puede
> tocar CaDiCaL, (b) qué ya se ha hecho y ganó, (c) dónde está la frontera y qué
> podría ser disruptivo pero abordable por un investigador individual, y (d) una
> lista corta de candidatos rankeados con un plan de experimento.

Fecha: 2026-09. Todas las afirmaciones llevan fuente al final.

---

## 0. TL;DR / recomendación

- **No** intentes ganarle a Kissat en ingeniería bruta (congruence closure, SAT
  sweeping, BVA, vivification): es donde el grupo de Freiburg lleva años y
  medallas. Competir ahí de frente no es realista en solitario.
- **Sí** hay una franja fértil y abordable: **políticas adaptativas guiadas por
  datos/aprendizaje ligero** dentro de un único solver — reinicios/resets,
  fases (phasing), y gestión de cláusulas más allá de LBD. Son cambios
  **localizados**, medibles con nuestro harness A/B, y con precedentes que ya
  demostraron mejora *sobre CaDiCaL mismo*.
- **Candidato principal recomendado**: una **política de reset/restart adaptativa
  tipo multi-armed bandit (UCB/Thompson)** — ver §5. Tiene el mejor balance
  impacto × factibilidad × novedad × encaje con tu perfil (tesis en eficiencia
  temporal ⇒ sabes medir y comparar políticas).
- **Candidato "moonshot"** (más riesgo, más recompensa): **predicción de fase
  offline de una sola pasada** al estilo NeuroBack pero con un modelo barato
  (no-GNN, CPU-only), entrenado con tus propios benchmarks. Ver §6.

---

## 1. Anatomía de CaDiCaL: dónde se toca

CaDiCaL es un CDCL moderno con **inprocessing**. Los "puntos calientes"
modificables, con el archivo aproximado en `cadical/src/`:

| Componente | Qué decide | Archivos (aprox.) |
|---|---|---|
| **Branching / VSIDS-EVSIDS** | qué variable decidir | `decide.cpp`, `score.cpp`, `bump` en `analyze.cpp` |
| **Phasing** | qué valor (true/false) probar primero | `phases.cpp`, `decide.cpp` (`target`, `saved`, `best`) |
| **Restart** | cuándo reiniciar la búsqueda | `restart.cpp` |
| **Rephasing** | cada cuánto y cómo resetear/rotar fases | `rephase.cpp` |
| **Reduce (clause DB)** | qué cláusulas aprendidas conservar/borrar | `reduce.cpp`, `reap.cpp`, tiers en `tier.cpp` |
| **Conflict analysis** | cómo aprender (1UIP, minimización, shrink) | `analyze.cpp`, `minimize.cpp`, `shrink.cpp` |
| **Chronological backtracking** | retroceder poco vs mucho tras conflicto | `backtrack.cpp` |
| **Inprocessing** | vivify, subsume, elim, probe, sweep, congruence | `vivify.cpp`, `subsume.cpp`, `elim.cpp`, `probe.cpp`, `sweep.cpp`, `congruence.cpp` |
| **Modos stable/focused** | alterna régimen de restart/phase | `stable.cpp`, `unstable.cpp`, `averages.cpp` |

Para una contribución de investigación conviene **un** componente localizado con
una señal de decisión clara (restart, rephase, reduce): son los que permiten un
experimento A/B limpio y una historia de paper defendible.

---

## 2. Lo que ya se hizo y ganó (no reinventar)

Evolución de CaDiCaL/Kissat, para no repetir trabajo:

- **Chronological backtracking** (Nadel & Ryvchin 2018; Möhle & Biere 2019):
  retroceder al nivel del conflicto en vez de al nivel del 1UIP cuando el salto
  sería enorme. Ya integrado en CaDiCaL (umbral ~100 niveles).
- **Target phases + rephasing** (Biere & Fleury, POS'20, "Chasing Target
  Phases"): guardar el prefijo más largo de trail sin conflicto como fase
  objetivo; mejoras grandes en instancias SAT. Ya integrado.
- **Vivification**: fortalecer/eliminar cláusulas aprendidas por propagación
  durante el inprocessing. Núcleo del rendimiento de Kissat.
- **Bounded Variable Addition (BVA)**: reencodar para reducir cláusulas.
- **Clausal equivalence sweeping** (FMCAD'24) y **congruence closure** (SAT'24):
  detectar equivalencias/puertas lógicas y colapsarlas. Claves de las **3
  medallas de oro de Kissat en 2024**. Muy potentes en verificación de circuitos.
- **LBD / glue clauses** (Audemard & Simon, Glucose): métrica de calidad de
  cláusula aprendida = nº de niveles de decisión distintos; las de LBD=2 ("glue")
  se conservan permanentemente. Base de la gestión de DB actual.

> Moraleja: el preprocesado/inprocessing estructural (sweeping, congruence, BVA)
> es territorio dominado y de ingeniería pesada. **Las políticas dinámicas de
> búsqueda** (cuándo reiniciar/resetear, qué fase, qué cláusula conservar) están
> menos saturadas y son más abordables.

---

## 3. La frontera 2024–2025 (dónde hay hueco)

### 3.1 Aprendizaje de máquina *de bajo coste* acoplado a CDCL
El patrón que funciona no es meter una GNN que se consulta en cada decisión (caro
e inviable en instancias grandes), sino **inferencia offline de una sola pasada**:

- **NeuroBack** (ICLR'24): una GNN predice, *una sola vez antes de resolver*, la
  fase (valor) que la mayoría de asignaciones satisfactorias daría a cada
  variable ("backbone"); corre en **CPU**, sin GPU. Mejoró a Kissat en **+5.2%**
  (SATCOMP'22) y **+7.4%** (SATCOMP'23) de instancias resueltas. Dataset
  *DataBack* (120k muestras) público.
- Lección: el acoplamiento ganador es **predecir una estructura estática barata
  (fase inicial / orden de branching) y dejar que el CDCL haga el resto.**

### 3.2 Políticas adaptativas por bandit / RL (sin red neuronal)
- **Reset policy por multi-armed bandit** (Li et al., 2024, arXiv:2404.03753):
  un *reset* es un restart que además **randomiza las activity scores** para
  forzar exploración global. Deciden *cuándo resetear* modelando el dilema
  explorar/explotar como **MAB con UCB y Thompson sampling**. Implementado en
  **CaDiCaL, SBVA_CaDiCaL, Kissat y MapleSAT**; superó a los baselines en Satcoin
  y en Main Track 2022/2023. **Cero red neuronal, cero GPU, overhead mínimo** —
  ideal para desarrollar y correr en hardware modesto.
- Precedente: restart adaptativo por ML (Liang et al., FLoC'18) sobre MapleSAT.

### 3.3 Gestión de cláusulas más allá de LBD
- LBD es **local** (una misma cláusula tiene distinto LBD según el contexto) y
  empieza a cuestionarse como métrica única de calidad. Líneas abiertas:
  **centralidad** de la cláusula en el grafo, roles de cláusula, y triggers de
  reducción desacoplados del ciclo de restart. Área con menos consenso ⇒ hueco
  para una métrica nueva y un criterio de retención mejor.

### 3.4 Autoconfiguración interna por features (la idea "SATzilla de un solo autor")
- Calcular features baratas al leer el CNF (ratio cláusula/variable, densidad,
  modularidad de comunidad, tamaño medio de cláusula) y **elegir régimen**
  (política de restart, agresividad de reduce, phasing inicial) por instancia,
  todo **dentro de un único solver**. No cae bajo la prohibición de portfolios de
  terceros y es contribución publicable.

---

## 4. Criterios para elegir NUESTRA contribución

Rankeamos por cuatro ejes (1–5, mayor mejor):

| Eje | Qué mide |
|---|---|
| **Impacto** | ganancia PAR-2 plausible / interés para la comunidad |
| **Factibilidad** | cabe en 1 investigador + hardware modesto, sin GPU ni cluster |
| **Novedad** | hueco real, no saturado, tesis/paper defendible |
| **Encaje** | aprovecha tu perfil (análisis de eficiencia temporal, medición) |

---

## 5. Candidato PRINCIPAL — Reset/restart adaptativo por bandit

**Idea**: extender/rehacer la política de restart de CaDiCaL con un controlador
**multi-armed bandit** que decida entre {no reiniciar, restart normal, **reset**
con randomización de activity} según recompensa observada (p.ej. tasa de
aprendizaje de cláusulas glue, caída de LBD medio, profundidad de trail).

| Eje | Nota | Por qué |
|---|---|---|
| Impacto | 4 | Precedente ya batió a CaDiCaL en Main Track benchmarks |
| Factibilidad | 5 | Localizado en `restart.cpp`/`rephase.cpp`; sin GPU; A/B directo |
| Novedad | 3–4 | Publicado en 2024, pero hay espacio: nuevas señales de recompensa, combinación con phasing, tuning por familia de instancias |
| Encaje | 5 | Es *exactamente* medir y comparar políticas temporales — tu tesis |

**Riesgo**: que quede como "réplica incremental". Mitigación: aportar una
**señal de recompensa nueva** o combinar reset-bandit con una política de
**rephase** informada (nadie lo ha unido bien todavía), y validar en un banco
propio + Main Track histórico.

**Primer experimento** (sin escribir aún el bandit): instrumentar CaDiCaL para
loguear, por ventana de conflictos, LBD medio, nº de glues, y decisiones de
restart; correr sobre `benchmarks/dev` y ver cuánta varianza hay que explotar.

---

## 6. Candidato MOONSHOT — Predicción de fase offline barata

**Idea**: al estilo NeuroBack pero **sin GNN**: un modelo ligero (regresión
logística / gradient boosting sobre features por variable: grado, balance de
polaridad, participación en cláusulas cortas, comunidad) que predice la **fase
inicial** de cada variable en **una sola pasada en CPU** antes de resolver.
Inyectar como `saved`/`target` phase inicial en `phases.cpp`.

| Eje | Nota | Por qué |
|---|---|---|
| Impacto | 5 | NeuroBack mostró +5–7% resueltas; techo alto |
| Factibilidad | 3 | Necesita pipeline de datos + entrenar + integrar C++↔modelo; sin GPU si evitas GNN |
| Novedad | 4 | "NeuroBack sin GNN / barato" es un ángulo abierto y atractivo |
| Encaje | 4 | Analítico y medible; requiere subir el listón en ML |

**Riesgo**: el pipeline de datos y la reproducibilidad son costosos; el modelo
puede no generalizar a benchmarks nuevos (el peligro clásico). Mitigación:
entrenar con familias diversas, medir generalización *fuera de distribución*.

---

## 7. Candidato ALTERNATIVO — Retención de cláusulas por centralidad

**Idea**: reemplazar/aumentar el criterio LBD en `reduce.cpp` con una métrica de
**centralidad/uso** (frecuencia de participación en conflictos recientes,
proximidad en el grafo de implicación) para decidir qué aprendidas conservar.

| Eje | Nota |
|---|---|
| Impacto | 3–4 |
| Factibilidad | 4 (localizado, pero medir centralidad barata es delicado) |
| Novedad | 4 (LBD como métrica única está en cuestión) |
| Encaje | 4 |

---

## 8. Recomendación final y siguiente paso

1. **Elegir §5 (reset-bandit) como línea principal** y §6 (fase offline) como
   exploración paralela de bajo compromiso.
2. **Fase 0 (medición, ya):** instrumentar CaDiCaL para caracterizar la dinámica
   de restart/LBD sobre `benchmarks/dev` y sobre un subconjunto Main Track
   histórico. Esto es *tu* terreno (eficiencia temporal) y define la línea base
   cuantitativa contra la que medir cualquier política.
3. **Fase 1:** implementar un bandit UCB simple sobre la decisión de reset, con
   una señal de recompensa clara; A/B con `par2.py` contra el baseline
   `cadical-3.0.1-vanilla`.
4. **Fase 2:** si hay señal, añadir la novedad (recompensa nueva / acople con
   rephase) y escalar el banco de pruebas.

> Con vista a **2027** tenemos margen para hacer Fase 0–1 con rigor, publicar un
> reporte técnico intermedio (buen material para tu CV y para posgrado) y llegar
> a la competición con una contribución validada, no improvisada.

---

## Fuentes

- SAT Competition (oficial): https://satcompetition.github.io/
- Möhle & Biere, "Backing Backtracking", SAT'19: https://fmv.jku.at/papers/MoehleBiere-SAT19.pdf
- Biere & Fleury, "Chasing Target Phases", POS'20: https://fmv.jku.at/papers/BiereFleury-POS20.pdf
- CaDiCaL 2.0, CAV'24: https://cca.informatik.uni-freiburg.de/papers/BiereFallerFazekasFleuryFroleyksPollitt-CAV24.pdf
- Kissat/CaDiCaL SAT Competition 2024 solvers: https://cca.informatik.uni-freiburg.de/papers/BiereFallerFazekasFleuryFroleyksPollitt-SAT-Competition-2024-solvers.pdf
- Kissat gana SAT 2024 (técnicas: congruence closure, sweeping, BVA, vivification): https://news.vm.uni-freiburg.de/en/newsarchive/kissat-triumphs-in-the-sat-2024-competition
- NeuroBack (ICLR'24), fase offline con GNN en CPU: https://arxiv.org/abs/2110.14053 · código: https://github.com/wenxiwang/neuroback
- Li et al., "A Reinforcement Learning based Reset Policy for CDCL SAT Solvers" (2024): https://arxiv.org/abs/2404.03753
- Liang et al., "Machine Learning-Based Restart Policy for CDCL SAT Solvers", FLoC'18: http://t-news.cn/Floc2018/FLoC2018-pages/proceedings_paper_477.pdf
- "Rethinking Clause Management for CDCL SAT Solvers" (2025+): https://arxiv.org/html/2602.20829
- Audemard & Simon, LBD / "Predicting Learnt Clauses Quality" (Glucose): https://www.ijcai.org/Proceedings/09/Papers/074.pdf
- Repositorio de publicaciones del grupo (Freiburg): https://cca.informatik.uni-freiburg.de/papers/
