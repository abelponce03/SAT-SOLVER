# Investigación 06 — Estado del arte: modificaciones a solvers CDCL (Kissat/CaDiCaL) y bandits

> Encargo: estado del arte exhaustivo de las modificaciones hechas a los solvers
> ganadores de SAT Competition (2024–2026), en especial los basados en CaDiCaL y
> los que usan **multi-armed bandit (MAB)** — para decidir **qué implementar** y
> **cómo diferenciarnos**. Documento de estudio; todas las afirmaciones con
> fuente al final.

Aviso de fechas: **SAT Competition 2026 ya se celebró** (resultados en FLoC/SAT
2026, Lisboa, julio 2026). La 2025 es la edición completa mejor documentada; la
usamos como base y añadimos lo conocido de 2026.

---

## 0. TL;DR estratégico (léelo primero)

1. **El Main Sequential 2025 lo ganan los bandits sobre Kissat.** Ranking ALL:
   1º **AE-Kissat-MAB** (327 resueltas), 2º Kissat-public, 3º Kissat-VSA. El
   ganador es un **bandit** que modifica `restart_mab()`.
2. **En UNSAT gana CaDiCaL** — pero **sin bandits**: **CaDiCaL-SC2025** (Biere
   et al.) ganó UNSAT con ingeniería pura (portó de Kissat: congruence closure,
   sweeping, vivification). Nada de aprendizaje.
3. **Nuestro nicho (reset/rephase-bandit) ya está poblado… en Kissat.** Existen
   Kissat-MAB-rephasing (2022), **Kissat_MAB_CoRephase** y
   **Kissat-CoRephase-CoReward** (2025), MapleSSV (restart-bandit). El reward de
   la validación (GLR) es esencialmente el de MapleSSV/Li-2024.
4. **Dónde está el hueco real**: (a) casi todo el trabajo de bandits es sobre
   **Kissat**; **CaDiCaL como host de bandits está poco explorado**; (b) el
   **diseño de la recompensa** es una pregunta abierta y activa (CoReward,
   recompensas compuestas). Nuestra diferenciación creíble vive ahí.
5. **Consecuencia**: un "reset-bandit genérico sobre CaDiCaL" sería *incremental*
   frente a lo publicado. Para que valga como contribución hay que aportar algo
   nuevo: una recompensa mejor justificada/validada (ya empezamos, doc 05), o
   una combinación (bandit + una capacidad que Kissat no tiene, p.ej.
   incremental/proofs de CaDiCaL), o un ángulo de robustez (flaky→resuelta,
   doc 03) que la literatura de "más resueltas" no mide.

---

## 1. Resultados de la competición (quién gana y con qué)

### Main Sequential Track 2025 (400 benchmarks, PAR-2, timeout 5000s)

| Track | 1º | 2º | 3º |
|---|---|---|---|
| **ALL** | AE-Kissat-MAB (327) | Kissat-public (321) | Kissat-VSA (317) |
| **SAT** | AE-Kissat-MAB (173) | Kissat-public (163) | Kissat-CURE (159) |
| **UNSAT** | **CaDiCaL-SC2025 (161)** | Kissat-VSA (160) | AE-Kissat-bump (159) |

26 solvers secuenciales compitieron. Muchos son variantes de Kissat con una
modificación puntual (MAB, rephase, predicción, rescale de scores, SBVA…).

### Main Sequential Track 2026

- Ganador: **satsuma-iter+kissat** (276 inputs) — Kissat + preprocesado de
  ruptura de simetrías (Satsuma) integrado vía Mallob. La línea Kissat sigue
  dominando; el añadido ganador de 2026 es **simetrías**, no bandits.

### Lectura

- **SAT ⇒ bandits/heurística de búsqueda; UNSAT ⇒ ingeniería estructural.** Esto
  concuerda con nuestros datos de tesis (doc 03): el gap de CaDiCaL vs Kissat es
  estructural (miter), no de política de búsqueda.

---

## 2. CaDiCaL ganador (CaDiCaL-SC2025): qué le añadieron

En vez de mejorar Kissat, Freiburg **portó features de Kissat a CaDiCaL** (para
mantener incremental solving y proofs). Añadido (~3 KLOC C):

- **clausal congruence closure** (detección/colapso de puertas lógicas),
- **revisited vivification**,
- **clausal equivalence sweeping**,
- (bounded variable addition asociada),
- un **formato de prueba clausal nuevo** para la congruence closure (más difícil
  de producir que las pruebas de Kissat).

Resultado: ganó UNSAT; sigue por detrás de Kissat en SAT salvo en instancias que
requieren BVA/congruence. **Nuestra base (CaDiCaL 3.0.1) ya contiene
`congruence.cpp`, `sweep.cpp`, `vivify.cpp`** — estamos cerca de esa versión.

---

## 3. Taxonomía de bandits en SAT (del survey SOCS'25)

El survey de Shanghai Jiao Tong (2025) organiza *dónde* se aplica un MAB en un
CDCL. Para cada punto: arms, algoritmo y recompensa.

| # | Dónde | Solver de referencia | Arms | Recompensa | Algoritmo |
|---|---|---|---|---|---|
| 1 | **Selección de branching** | Kissat_MAB (2021, ganó) | {VSIDS, CHB} en cada restart | learning-rate por variable | UCB1 / MOSS |
| 2 | **Rephasing** | Kissat-MAB-rephasing (2022) | {B, I, O, W} | métricas `decisions_t`, `decidedVars_t` reset por periodo | UCB |
| 2b| **Rephasing + reward** | **Kissat_MAB_CoRephase (2025)** | rephasing heuristics | **compuesta** αR_conflict+βR_clause+γR_variable | MAB |
| 3 | **Restart policy** | MapleSSV; Kissat-adaptive-restart | {uniform, linear, Luby, geom} / {stable, unstable} | **Xt = Δconflicts / LBD** | UCB1 (c=0.4, decay 0.95) |
| 3b| **Restart/reset** | RL-reset (Li 2024) | {no-reset, reset} | **rw_glr = Δlearned/Δdecisions vs EMA** | UCB / Thompson |
| 4 | **Local search (SLS)** | BandSAT / BandMaxSAT | cláusulas falsificadas como arms | Xt = Δcost / (cost+1), reward diferido | UCB1 (c=0.1) |
| 5 | **Algorithm selection** | SATzilla (portfolio) | solvers/config | tiempo/éxito predicho por features | — |

Observaciones clave para nosotros:
- **El GLR que validamos (doc 05) = el reward de MapleSSV/Li-2024.** No es
  novedoso por sí solo.
- **La recompensa "compuesta" (CoRephase) es la frontera de 2025**: mezclar
  señales de conflicto + cláusula + variable. El diseño de recompensa es donde
  hay margen de contribución, no el "poner un bandit".
- Los arms clásicos son {VSIDS,CHB}, rephasing types, restart policies. Un arm
  nuevo/mejor definido es otra vía de novedad.

---

## 4. Detalle de los competidores directos de nuestra idea

### Kissat-MAB-rephasing (Chen et al., 2022)
Bandit de 4 brazos que elige el tipo de rephasing {best, inverted, original,
walk}, guiado por UCB, **independiente de los restarts**, con métricas
`decisions_t` y `decidedVars_t` reseteadas cada periodo. → Es, casi literalmente,
"bandit sobre `rephasing()`" que teníamos planeado, pero en Kissat y desde 2022.

### Kissat_MAB_CoRephase / Kissat-CoRephase-CoReward (2025)
Combina distintas heurísticas de rephasing con MAB y una **recompensa
compuesta**:
`R_hybrid = α·R_conflict + β·R_clause + γ·R_variable`
(α=0.5·300, β=0.4·1, γ=0.1·10). Código público. Compitió en Main Sequential 2025.
→ Estado del arte de "bandit + rephasing + reward design". Nuestro competidor más
directo.

### AE-Kissat-MAB (Ding, Luo, Li et al., 2025) — GANADOR ALL
Modifica `restart_mab()` (línea Kissat_MAB): bandit en la selección de heurística
durante restarts, con framework de ajuste dinámico de configuración por iteración.
Variantes hermanas: AE-Kissat-rescale / -bump modifican `rescale_scores()` (VSIDS)
con estrategias de escalado y selección pseudoaleatoria.

### MapleSSV (Nejati et al., 2021)
Restart-bandit con reward `Δconflicts/LBD` — la raíz del reward que validamos.

---

## 5. Otras líneas ganadoras (no-bandit) para tener en el radar

- **Congruence closure / SAT sweeping / BVA / vivification** — el motor de
  Kissat 2024 (3 oros) y de CaDiCaL-SC2025 (UNSAT 2025). Ingeniería pesada,
  Freiburg-dominada. Evitar como contribución en solitario.
- **Simetrías (Satsuma)** — añadido ganador de 2026 (preprocesado). Área con
  recorrido pero es un mundo aparte (teoría de grupos).
- **Predicción/ML offline** — Kissat-pred / -pred-aggressive (2025), NeuroBack
  (fase offline). ML de una pasada; prometedor y menos saturado que los bandits
  online.
- **Gestión de cláusulas más allá de LBD** — sigue siendo cuestión abierta
  (doc 01 §3.3).

---

## 6. Matriz de decisión — opciones de contribución

Ejes: novedad (¿hueco real?), factibilidad (solo + hardware modesto), encaje
(perfil del autor: eficiencia temporal, ya midió 4 solvers), riesgo de "ya hecho".

| Opción | Novedad | Factib. | Encaje | "ya hecho?" | Veredicto |
|---|---|---|---|---|---|
| **A. Reset/rephase-bandit genérico en CaDiCaL** | 2 | 5 | 5 | **Alto** (CoRephase, RL-reset) | Solo si aporta algo nuevo (B o C) |
| **B. Recompensa nueva/mejor validada para el bandit** | 4 | 4 | 5 | Medio (CoReward existe, pero el diseño es abierto) | **Fuerte** — extiende doc 05 |
| **C. Bandit-search-control sobre CaDiCaL aprovechando lo que Kissat NO tiene** (incremental/proofs) | 4 | 3 | 4 | Bajo | **Fuerte** pero más ingeniería |
| **D. Robustez/estabilidad como objetivo** (flaky→resuelta, ↓varianza seed) | 4 | 4 | 5 | **Bajo** (la lit. mide "más resueltas", no varianza) | **Muy prometedor** — es nuestro doc 03 |
| **E. Predicción de fase offline barata** (NeuroBack sin GNN) | 4 | 3 | 4 | Bajo | Alternativa moonshot (doc 01 §6) |
| **F. Congruence/sweeping/simetrías** | 3 | 1 | 2 | — | Evitar en solitario |

### Recomendación de síntesis
Combinar **B + D sobre CaDiCaL**: un bandit de reset/rephase en CaDiCaL cuya
**contribución no es "poner un bandit"** (eso ya está), sino:
1. una **recompensa mejor fundamentada** (extender la validación del doc 05: por
   qué la mejora-relativa y no el nivel; comparar rewards GLR vs compuesto vs uno
   nuevo con evidencia), y
2. un **objetivo de robustez** que la literatura no optimiza: convertir
   instancias *flaky→resueltas* y **reducir la varianza por seed** (doc 03),
   reportándolo como métrica primaria además del PAR-2.

Eso nos separa de AE-Kissat-MAB y CoRephase (que persiguen "más resueltas" en
Kissat) y aprovecha nuestro activo único: el estudio de tesis con seeds y
métricas internas.

---

## 7. Qué estudiar a continuación (lecturas priorizadas)

1. **Kissat_MAB_CoRephase** (código + descripción) — el competidor directo;
   entender su recompensa compuesta y sus arms exactos.
   https://github.com/2317891476/Kissat_MAB_CoRephase
2. **Survey MAB-in-SAT (SOCS'25)** — el mapa completo; releer secciones de reward.
3. **RL-reset (Li 2024, arXiv:2404.03753)** — nuestra base de reward (ya usada).
4. **Proceedings SAT Competition 2025** — descripciones de AE-Kissat-MAB,
   Kissat-pred, Kissat-VSA, Dynamiccadical.
   https://repositum.tuwien.at/bitstream/20.500.12708/218424/2/Codel-2025-Proceedings...pdf
5. **"Reward Defining in MAB SAT Strategy"** (IEEE 2025) — diseño de recompensa.

---

## Fuentes

- Resultados SAT Competition 2025 (slides): https://satcompetition.github.io/2025/satcomp25slides.pdf
- Resultados SAT Competition 2026 (KIT/FLoC): https://satres.kikit.kit.edu/news/2026-07-28-floc/
- CaDiCaL/Kissat entering SAT Competition 2025 (Freiburg): https://cca.informatik.uni-freiburg.de/papers/BiereFallerFleuryFroleyksPollitt-SAT-Competition-2025-solvers.pdf
- Survey: Multi-armed Bandit Algorithms for the Boolean Satisfiability Problem (SOCS'25): https://ojs.aaai.org/index.php/SOCS/article/view/35997
- Kissat_MAB (Cherif, Habet, Terrioux, CP'21 / DROPS): https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CP.2021.20
- Kissat_MAB_CoRephase (código): https://github.com/2317891476/Kissat_MAB_CoRephase · (figshare) https://figshare.com/articles/code/Kissat_MAB_CoRephase_Combining_DifferentRephasing_Heuristics_Using_MAB_in_SAT/27264291
- RL-based Reset Policy (Li et al. 2024): https://arxiv.org/abs/2404.03753
- Reward Defining in Multi-armed Bandit SAT Strategy (IEEE 2025): https://ieeexplore.ieee.org/document/11010289/
- Proceedings SAT Competition 2025: https://repositum.tuwien.at/bitstream/20.500.12708/218424/2/Codel-2025-Proceedings%20of%20SAT%20Competition%202025%20%20Solver%20and%20Benchmark%20Desc...-vor.pdf
