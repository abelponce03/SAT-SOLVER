# Investigación 03 — Fase 0 con datos reales de la tesis

> El autor aportó `results_enriched.csv`: su estudio comparativo de tesis con
> **4 solvers × 955 instancias de aplicación reales × 3 seeds** (timeout 800 s).
> Esto llena el hueco que el dev set sintético no cubría (doc 02, §5): régimen
> **industrial/aplicado**, el terreno de la Main Track. Aquí se recalibra el
> plan con evidencia real.

Dataset: solvers `kissat, cadical, cryptominisat, minisat`; familias `miter,
scheduling, station-repacking, hardware-verification, cryptography, bitvector,
planning, argumentation, software-verification`; métricas internas completas de
CaDiCaL por instancia (en `solver_metrics_json`) + derivadas
(`conflicts_per_restart`, `rephase_per_restart`, `chronological_ratio`, …).

---

## 1. La foto general

Tasa de resolución (instancias válidas, descartando `CORRUPT_XZ`):

| solver | solved |
|---|---:|
| **kissat** | **0.566** |
| cadical | 0.492 |
| cryptominisat | 0.458 |
| minisat | 0.395 |

CaDiCaL va 7.4 pts por debajo de Kissat. **Ese gap es la oportunidad** — pero
hay que ver *dónde* está, porque no todo el gap es atacable con política de
restart.

---

## 2. Dónde pierde CaDiCaL (y por qué importa para elegir la contribución)

Gap Kissat−CaDiCaL por familia:

| familia | cadical | kissat | gap |
|---|---:|---:|---:|
| **miter** | 0.444 | 0.729 | **+0.285** |
| software-verification | 0.707 | 0.804 | +0.097 |
| bitvector | 0.326 | 0.401 | +0.075 |
| argumentation | 0.280 | 0.330 | +0.050 |
| scheduling | 0.509 | 0.558 | +0.049 |
| station-repacking | 0.742 | 0.782 | +0.040 |
| cryptography | 0.388 | 0.398 | +0.010 |
| planning | 0.785 | 0.786 | +0.001 |
| hardware-verification | 0.820 | 0.804 | **−0.016** |

**El gap se concentra en `miter` (+28.5%)** — verificación de equivalencia de
circuitos. Y eso es precisamente donde Kissat gana por **congruence closure +
SAT sweeping** (sus 3 oros de 2024, doc 01 §2), es decir **preprocesado
estructural**, NO política de búsqueda. De las 94 instancias que Kissat resuelve
y CaDiCaL no, **37 son miter**.

> Conclusión dura: una contribución de restart/reset **no** cerrará el gap de
> miter. Cerrarlo exige el territorio pesado (sweeping/congruence) que el doc 01
> recomienda evitar en solitario. Hay que buscar el valor del reset-bandit en
> **otro** sitio.

---

## 3. Donde SÍ hay territorio para el reset-bandit: inestabilidad por seed

Con 3 seeds por instancia podemos medir algo que el dev set no permitía: la
**estabilidad de CaDiCaL frente a la aleatorización de la búsqueda**.

Sobre 866 instancias con ≥2 seeds:

| categoría | nº | interpretación |
|---|---:|---|
| siempre resuelve | 437 | robustas; la política ya va bien |
| nunca resuelve | 367 | núcleo duro (parte estructural) |
| **FLAKY** (unas seeds sí, otras no) | **62** | **al borde: sensibles a la búsqueda → territorio del reset** |

Además, entre las que siempre resuelve (no triviales, >1 s), el **ratio
max/min de tiempo entre seeds** tiene mediana 1.30, **p90 = 4.83 y máximo 102×**:
la misma instancia puede tardar 100 veces más solo por cambiar la seed. Eso es
**inestabilidad de búsqueda pura** — exactamente lo que una política adaptativa
puede amortiguar.

Y lo importante: las 62 flaky **no** están dominadas por miter, sino por familias
de régimen de búsqueda — cryptography (13), bitvector (13), argumentation (9),
scheduling (8), software-verification (8)…

---

## 4. Firma de restart de las inestables (señal correlacional)

Comparando corridas resueltas, medianas flaky vs always-solved:

| métrica | always-solved | flaky-solved |
|---|---:|---:|
| conflicts_per_restart | 475 | **672** |
| rephase_per_restart | 0.062 | **0.038** |
| chronological_ratio | 0.215 | 0.142 |

Las inestables reinician **menos seguido** y **resetean (rephase) menos por
restart**. Es decir: la política actual **resetea poco justo donde la búsqueda es
más inestable**. Es una señal *correlacional* y modesta (de runs resueltos, no de
los timeouts, que no imprimen stats), pero apunta en la dirección del bandit:
disparar más/mejores resets en el régimen inestable.

---

## 5. Recalibración del plan (honesta)

1. **El objetivo del reset-bandit NO es "ganarle a Kissat en general"** (el gap
   grande es estructural/miter, fuera de alcance). El objetivo realista y
   medible es **robustecer la búsqueda al borde**: convertir instancias *flaky →
   resueltas* y **reducir la varianza por seed**. Métrica de éxito Fase 1:
   - ↑ nº de instancias flaky que pasan a resueltas en todas las seeds,
   - ↓ ratio p90 de tiempo entre seeds,
   - PAR-2 igual o mejor (no regresar en las robustas).
2. **Esta es una historia de tesis/paper defendible por sí sola**: "estabilidad
   de solvers CDCL frente a aleatorización y una política de reset que la mejora"
   — y encaja con tu tesis de eficiencia temporal (ya mediste 4 solvers).
3. **Integrar estos benchmarks reales** al flujo: las familias del CSV
   (miter/bitvector/crypto/…) deben entrar al banco local de pruebas — muchísimo
   más representativas que uf/uuf250. *Necesitamos las instancias `.cnf.xz`*, no
   solo el CSV (ver §7).
4. **Alternativa a considerar** si el reset-bandit rinde poco: dado que el gap
   real está en miter, una línea de mayor impacto —pero más costosa— sería
   trabajar detección de puertas/equivalencias ligera. Queda anotada, no elegida.

---

## 6. Qué aportó concretamente este dataset

- Confirmó el ranking (Kissat > CaDiCaL) y **localizó** la debilidad de CaDiCaL
  (miter estructural) → evitó que persiguiéramos el gap equivocado con la
  herramienta equivocada.
- Aportó la **evidencia real** de inestabilidad por seed (62 flaky, 102× de
  varianza temporal) que **sí** justifica el reset-bandit, con métrica de éxito
  clara.
- Dio un banco de 9 familias de aplicación reales para el resto del proyecto.

---

## 7. Pendiente para avanzar

- [ ] Conseguir las **instancias** referenciadas en el CSV (`benchmark/.../*.cnf.xz`)
  para correrlas localmente; con el CSV solo tenemos las métricas agregadas, no
  los ficheros para experimentar el bandit.
- [ ] Seleccionar un subconjunto de las 62 flaky + una muestra de robustas como
  **banco de validación del bandit** (Fase 1).
- [ ] Fase 0.5 (doc 02 §6): instrumentación ligera para la serie temporal de
  reuse/LBD durante la búsqueda, ahora priorizando familias reales inestables.

---

## Datos

- Fuente: `results_enriched.csv` (estudio de tesis del autor; no versionado en el
  repo por tamaño/procedencia — vive fuera del árbol).
- Scripts de análisis: reproducibles con pandas sobre ese CSV (ver historial de
  esta sesión); si se desea, se puede añadir un `scripts/analyze_thesis.py`.
