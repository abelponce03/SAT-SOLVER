# Investigación 10 — ¿A qué distancia está LabeSAT de los ganadores de 2026, y qué hacen ellos que podamos integrar?

- **Fecha**: 2026-10-01; **actualizado el 2026-10-03** con el cierre de
  EXP-009, EXP-020 y EXP-021 (§0b), y el **2026-10-04** con los datos de
  2025 (§0c).
- **Pedido del director**: un análisis actual de lo lejos que está LabeSAT de
  vencer a los ganadores de la SAT Competition 2026 y de lo que hacen ellos
  que podamos integrar.
- **Método**: `scripts/distancia_2026.py` (salida en
  `results/estrategia/distancia_2026.md`). Con los tiempos **oficiales** de
  2026 (mismas máquinas, T = 5000 s), compone instancia a instancia las
  configuraciones de LabeSAT a partir de piezas que la competición sí midió:
  - **K**: el Kissat de Biere. Es nuestra base; EXP-008 no encontró
    diferencia con Kissat 4.0.4.
  - **S**: satsuma + Kissat 4.0.4, que es la entrada ganadora y la misma
    tubería que `labesat --symmetry`.
  - **B3**: la ruptura con retraso de 2 s (EXP-009).
  - **X1**: refuta las *lights-out* UNSAT (research/09).
  - **PGO + LTO**: ×1,030 de velocidad (EXP-017).
- **Es un contrafactual, no una medición de LabeSAT en 2026**: §2.2 dice
  qué puede fallar.

---

## 0. Resumen

1. **Hoy, por defecto, LabeSAT quedaría 16.º** de la Main Track de 2026
   (PAR-2 4611, 238 resueltas), a **+964 s** del ganador. La ruptura de
   simetrías está apagada por defecto hasta que EXP-009 decida cómo
   activarla. Ese único interruptor es toda la distancia.
2. **Con todo lo que tenemos o tenemos en camino** (B3 + X1 + PGO/LTO),
   LabeSAT quedaría **1.º, con PAR-2 3572 frente a 3647 (−75 s) y 278
   resueltas frente a 276**:
   - B3 aporta −2,5 s;
   - X1 aporta −56 s, con dos *lights-out* UNSAT que **nadie** resolvió en
     2026;
   - PGO/LTO aporta −15 s.
3. **El margen es estrecho**: un 2 % del PAR-2, y medido sobre el banco con
   el que se diseñaron B3 y X1. En 2027 los rivales tendrán satsuma (es
   público), y la línea de salida será la nuestra.
4. **Qué hacen los de arriba**:
   - el 1.º es exactamente nuestra tubería (satsuma + Kissat 4.0.4);
   - el 3.º y del 4.º al 7.º añaden un bandido VSIDS/CHB (MAB), que da
     **más SAT y menos UNSAT**;
   - el 8.º usa un solver específico por familia;
   - el resto, variantes de Kissat.

   La única técnica de peso que no tenemos es el **MAB**. Repartir el tiempo
   entre LabeSAT y la variante MAB **no compensa** (§3.2); su valor solo se
   cobraría eligiendo la configuración por instancia.
5. **El hueco cobrable**: 56 instancias que resuelve algún solver del top-10
   y LabeSAT no.
   - ~10 tienen estructura de paridad (X1b o fases de Gauss).
   - ~20 son SAT combinatorias simétricas que solo resuelven las variantes
     MAB.
   - 12 son *linear-equations* SAT que solo resolvió `lymphosat`. **No** son
     XOR sobre GF(2) (§4), así que Gauss no sirve.

## 0b. Actualización del 2026-10-03

- **EXP-009 descarta B3.** En 153 instancias industriales frescas, el
  retraso de 2 s empeora frente a «nunca» (+9,9 s, Wilcoxon p = 2,9·10⁻⁸).
  La simulación que lo eligió (−2,4 s) era optimista, como advertía §2.2.3.
- **La configuración candidata pasa a ser «siempre» + X1 + PGO/LTO.** Con
  los tiempos de 2026: 278 resueltas, PAR-2 3575, **1.º por −72 s**.
  - Es casi lo mismo que la cuenta anterior con B3 (−75 s): en 2026, B3 y
    «siempre» solo se distinguían en 2,5 s.
  - El coste industrial de «siempre» ya está dentro de los tiempos del
    ganador.
- **Sin simetrías**, con X1 y PGO/LTO: 240 resueltas, **15.º** (+887 s).
- **Cómo se activa en el paquete** lo decide el director: **D-020**. Se
  recomiendan dos variantes (D-014): V1 «siempre» y V2 «nunca».
- **Un selector perfecto** entre «siempre» y «nunca» daría 291 resueltas y
  PAR-2 3252 (−395 s).
  - Es una cota de oráculo: aprovecha también la variación entre dos
    corridas.
  - De las 13 instancias que solo resuelve «nunca», **10 son SAT**
    (*allowable-sequence*, *boxfolding*, *ntil*, *sorting-networks*,
    *coloring*…) y 3 UNSAT. De las 51 que solo resuelve «siempre», **43 son
    UNSAT**. Es lo que predice la teoría: los predicados de ruptura acortan
    las refutaciones y quitan soluciones, que en SAT pueden estorbar.
  - Es la línea B4 (D-020, opción d).
- **EXP-020**: el tope de 60 s se mantiene. El de 300 s resuelve las mismas
  y cuesta +24,6 s, y el riesgo de las 11 instancias no medibles (§2.2) se
  declara.
- **EXP-021**: X1 v2, por componentes, se activa por defecto. Procesa 56 de
  los 103 sistemas que la v1 saltaba, sin cambiar la búsqueda.
- **Probado en los datos de 2026 y descartado** (exploratorio): carteras
  secuenciales entre «nunca» y «siempre».
  - «Nunca» X s y luego «siempre»: empeora con cualquier X ≥ 10 s.
  - «Siempre» X s y luego «nunca»: con X = 300 s da 279 resueltas y −18 s,
    pero en la muestra de diseño, igual que B3. Con X ≥ 600 s empeora.

## 0c. Fuera de muestra: 2025 (2026-10-04)

`scripts/fuera_de_muestra_2025.py` (salida en
`results/estrategia/fuera_de_muestra_2025.md`). 2025 no publica resultados
por instancia: solo las curvas de cactus de las diapositivas. De ellas salen
las resueltas y el PAR-2 de cada solver, y la cuenta coincide con las cifras
oficiales.

**En 2025, «siempre» quedó 15.º de 22.**

| Solver | Puesto | Resueltas (SAT / UNSAT) | PAR-2 |
|---|---|---|---|
| AE-Kissat2025-MAB (ganador) | 1 | 327 (173 / 154) | 2264,7 |
| Kissat-public (Biere, sin simetrías) | 2 | 321 (163 / 158) | 2423,4 |
| Kissat-sc2025 (Biere, sin simetrías) | 10 | 308 (161 / 147) | 2694,3 |
| **Satsuma-Kissat-sc («siempre»)** | **15** | **290 (154 / 136)** | **3007,6** |

- La entrada de satsuma resolvió 18 menos que `Kissat-sc2025` y 31 menos
  que `Kissat-public`, **también en UNSAT**, donde la ruptura debería ayudar.
- **Esa entrada no era nuestra configuración** (paquete oficial
  `satsuma-kissat-sc.tar.xz`, leído el 2026-10-04 sin ejecutarlo):
  - **Kissat 4.0.2** modificado para escribir la prueba en **VeriPB**
    (`rup … >= 1 ;`, `--no-binary`); satsuma 1.2 también la escribía en
    VeriPB. Nosotros y el ganador de 2026 usamos Kissat 4.0.4 y prueba SR,
    verificada por `dsr-trim`.
  - **Satsuma sin tope de tiempo**. Solo se saltaba con 5 millones de
    variables o más «para no llegar al límite de 32 GB», con topes
    internos de componentes y modelos.
  - Las diapositivas de 2025 hablan de problemas al verificar las pruebas
    grandes, y un UNSAT sin prueba verificada no cuenta.
  - Las 11 UNSAT de menos frente a Kissat-sc2025 pueden deberse, en parte,
    a la verificación VeriPB. Las 7 SAT de menos, al tiempo de satsuma sin
    tope o a la perturbación de la búsqueda. **El 15.º no se puede atribuir
    solo a «siempre».**

**Por qué 2026 fue distinto.** De las 44 instancias netas que «siempre» ganó
a «nunca» en 2026, **40 son de familias que no estaban en 2025**:
*graph-coloring* (+12), *exam-scheduling* (+11), *chnl* (+6), *count* (+6) y
*boxfolding* (+4). 2025 traía, en cambio, 20 *argumentation* y 20
*oddball-weighing*, donde la ruptura perdió en 2026.

**Lectura**:

- El «1.º» de §0b es un resultado **de 2026**, y depende de unas pocas
  familias combinatorias simétricas que en 2025 no estaban. Lo que no
  sabemos es cuánto habría perdido **nuestra** «siempre» en 2025: el 15.º
  es de otra configuración. EXP-023 lo mide con nuestra tubería sobre las
  instancias de 2025.
- El valor de «siempre» cambia de signo de un año a otro. Eso refuerza la
  opción a de D-020 (dos variantes) y hace la V2 («nunca») mucho más que
  una cobertura.
- Lo que cobraría los dos regímenes es un **selector estructural** (B4): que
  decida por la estructura que encuentra satsuma (filas intercambiables,
  tamaño del grupo), no por SAT/UNSAT. Los rasgos de EXP-014 ya existen
  para la industria; faltan los del banco simétrico.
- **Ninguna configuración gana los dos años**:

  | Configuración | 2025 | 2026 |
  |---|---|---|
  | satsuma + Kissat («siempre») | 15.º | **1.º** |
  | satsuma + AE-Kissat-MAB | no participó | 2.º (+50 s) |
  | AE-Kissat-MAB, sin satsuma | **1.º** | 19.º o peor (`ding_kissat-mab-eae*`), por debajo de Kissat |
  | Kissat sin simetrías (Kissat-public / kissat-biere) | 2.º | 16.º |

  Con las cuatro variantes de D-014, la rejilla {con / sin simetrías} ×
  {Kissat / MAB} tiene una variante cerca del primer puesto en cada uno de
  los dos regímenes. Para las dos variantes con MAB hace falta D-018
  (portar el bandido), y cada variante necesita su propia validación.
- **Robustez**: hay que poder limitar la **memoria** de satsuma, no solo el
  tamaño de la CNF. En competición, una explosión de memoria de satsuma
  puede matar la corrida entera en vez de caer al respaldo.
  - Hecho: `LABESAT_SYMM_MEM`, en `labesat` y en el binario integrado
    (RLIMIT_AS solo para satsuma).
  - Por defecto vale 0, sin tope, porque así se midieron todos los A/B:
    `run_ab_interleaved.py` no pone tope, y la máquina tiene 15 GB.
  - Su valor se fija con el límite de memoria que anuncien las reglas de
    2027 (P5).

## 1. El campo de 2026 (Main Track, 400 instancias, T = 5000 s)

| Puesto | Entrada | Resueltas (SAT / UNSAT) | PAR-2 | Qué hace |
|---|---|---|---|---|
| 1 | `anders_satsuma-iter-kissat` | 276 (127 / 149) | 3647 | satsuma 1.3 (con cliquer, sin topes) + Kissat 4.0.4 |
| 2 | `anders_satsuma-iter-ae-kissat-mab` | 269 (136 / 133) | 3697 | satsuma + AE-Kissat-MAB (ganador de 2025, MAB evolucionado con LLM) |
| 3–6 | `zheng_kissat-mab-hypre` (y v2, *evolve*, *satlution*) | 253–255 | 3996–4067 | satsuma con topes propios + Kissat_MAB 4.0.2; dos variantes evolucionadas con LLM |
| 7 | `green_lymphosat` (*main-ai*) | 251 (146 / 105) | 4177 | Un solver distinto por familia (hiperespecialización) |
| 8 | `oertel_satsuma-lex-kissat` | 249 | 4280 | satsuma con *lex-leader* + Kissat |
| 9 | `zhenwei_mergesat-l` (*main-ai*) | 245 | 4386 | MergeSat (otro motor) |
| … | | | | |
| 16 | `biere_kissat-biere` (**nuestra base**) | 238 (129 / 109) | 4612 | Kissat de fábrica |

`zhenwei_kissat-sup` (130 SAT, PAR-2 3686) es del **track experimental** y no
entra en el ranking de la Main Track.

**La ventaja del ganador es casi toda UNSAT**: 149 frente a 109 de la base
(+40), y en SAT empata (127 frente a 129). Es lo que predice la teoría: la
ruptura de simetrías acorta las pruebas de insatisfacibilidad
(research/09 §1.2).

## 2. Dónde quedaría LabeSAT

### 2.1 Contrafactual con los tiempos oficiales

| Configuración | Resueltas | PAR-2 | Δ frente al ganador | Puesto |
|---|---|---|---|---|
| LabeSAT por defecto hoy (sin simetrías) ≈ K | 238 | 4611,5 | +964,5 | 16 |
| `--symmetry` siempre ≈ S | 276 | 3647,0 | 0 | empate |
| B3 (retraso de 2 s) | 276 | 3644,5 | −2,5 | 1 |
| B3 + X1 | 278 | 3587,9 | −59,1 | 1 |
| B3 + X1 + PGO/LTO (**descartada por EXP-009**) | 278 | 3572,3 | −74,7 | 1 |
| Referencia: el ganador con X1 | 278 | 3590,5 | −56,5 | — |
| **«Siempre» + X1 + PGO/LTO (V1 propuesta, D-020)** | **278** | **3574,7** | **−72,3** | **1** |
| «Nunca» + X1 + PGO/LTO (V2 propuesta, D-020) | 240 | 4533,8 | +886,8 | 15 |
| Selector perfecto entre las dos (cota) | 291 | 3252,4 | −394,6 | 1 |

Detalle:

- **X1** actúa en las cuatro *lights-out* UNSAT de 2026:
  - `667341ee` y `0efcbd10` las resuelven también K y S, más despacio;
  - `32e344a5` y `80b163b7` **no las resolvió nadie en 2026**.
- Frente al ganador, LabeSAT final gana esas 2 y **no pierde ninguna**.

### 2.2 Qué puede fallar en esta cuenta

1. **Nuestro satsuma no es el suyo.** Usamos upstream 1.4 con mclique v2
   (MIT) en lugar de 1.3 con cliquer (GPL). EXP-011 mostró que mclique v2
   recupera 6/6 de lo que aportaba cliquer en nuestro banco. No hay medida
   sobre las 400 de 2026.
2. **Nuestros topes** (60 s y 512 MiB) frente a los del ganador (ninguno):
   - En el banco simétrico (EXP-011, 84 instancias), satsuma con mclique v2
     llega al tope en 3. En las 3, Kissat solo resuelve en 1–4 s y el
     ganador tardó 99–1042 s. **Ahí el tope y B3 nos favorecen.**
   - **Lo que no podemos medir**: de las 51 instancias que el ganador
     resuelve y Kissat solo no, 11 le llevan más de 60 s en total. Si en
     alguna satsuma se pasara de nuestro tope, caeríamos a Kissat sin
     simetrías y la perderíamos.
   - Cota superior del daño: ~11 × 10 000 / 400 ≈ **+270 s de PAR-2, más
     que todo nuestro margen**. 10 de esas 11 no están en disco (una está en
     `bench/test`).
   - Es la incertidumbre más grande de este análisis. Ver §5, acción 4.
3. **Sesgo de diseño**: B3 (X = 2 s) y X1 se diseñaron mirando 2026.
4. **2027 no es 2026**: las familias cambian; 2026 era rico en combinatoria
   simétrica (research/01). Y los rivales tendrán satsuma, porque es MIT y
   público.
5. **Hardware**: la Proposición 1 traslada la velocidad, no la memoria. Una
   instancia que exige más de 6 GB solo falla en nuestro arnés local
   (EXP-016 y EXP-019, *miter* `e85fb114`).

**Lectura honesta**: con lo medido, LabeSAT está **a la altura del ganador
de 2026 y algo por delante gracias a X1**. No tiene un margen que aguante
por sí solo un cambio de banco. Para ganar en 2027 hace falta ensanchar el
margen por donde el ganador es débil.

## 3. Qué hacen ellos y qué podemos integrar

### 3.1 Técnica por técnica

| Técnica | Quién | ¿En LabeSAT? | Evidencia y decisión |
|---|---|---|---|
| Ruptura de simetrías con satsuma | 1.º, 2.º, 3.º–6.º, 8.º | **Sí** (ADR-0004 y ADR-0007; mclique v2) | Toda la ventaja del ganador. EXP-009 descartó B3; cómo se activa en el paquete, **D-020** |
| Topes de satsuma (componentes, modelos, tamaño) | 3.º–6.º | En parte (60 s, 512 MiB) | §2.2: el riesgo y la ventaja de nuestros topes. Acción 4 |
| Bandido VSIDS/CHB (MAB), evolucionado con LLM en 2025 | 2.º, 3.º–6.º | **No** (D-018) | Más SAT (+9) y menos UNSAT (−16) que el 1.º. Ver §3.2 |
| Un solver por familia | 7.º | No | No se generaliza a familias nuevas. Sus 12 *linear-equations* no son GF(2) (§4) |
| Otro motor (MergeSat) | 9.º | No | Complementario en UNSAT de equivalencias (3 instancias). Integrarlo es caro |
| Decisiones sobre el soporte independiente, BreakID + `kmpsym` | `kissat-sup` (exp.) | No | Resolvió las *xor-shifting* SAT; track experimental, sin pruebas. Se mira con EXP-019 §3b |
| **Gauss con prueba (X1)** | **Nadie** | **Sí** (research/09, EXP-019) | **Exclusiva nuestra**: +2 que nadie resolvió y −56 s |
| PGO + LTO | No consta | **Sí** (EXP-017) | ×1,030 |

### 3.2 ¿Merece la pena el MAB?

- **Oráculo** (elegir por instancia entre LabeSAT final y la variante MAB
  del 2.º): 292 resueltas y PAR-2 3201. Son 14 instancias y 371 s mejor que
  LabeSAT final: la diferencia es real.
- **Cartera secuencial** (LabeSAT durante f·T y, si no resuelve, la variante
  MAB desde cero):

  | f | Resueltas | PAR-2 | Δ frente al ganador |
  |---|---|---|---|
  | 0,5 | 259 | 3862 | +215 |
  | 0,8 | 266 | 3744 | +97 |
  | 0,9 | 277 | 3586 | −61 |
  | 1,0 (sin cartera) | 278 | 3572 | −75 |

  **Repartir el tiempo no compensa con ningún f.** Lo que el MAB resuelve
  y nosotros no necesita casi todo el tiempo; partirlo pierde más de lo que
  gana. Coincide con EXP-001/EXP-006 (A4: el reparto no cobra la
  diversidad).
- **Conclusión**: el MAB solo valdría con un **selector** que elija la
  configuración al empezar, a partir de rasgos de la instancia. La lección
  de 2025 es que la predicción SAT/UNSAT (Kissat-Pred) es difícil, y el
  selector tendría que acertar más de lo que le cuesta equivocarse. D-018
  sigue abierta, ahora con este dato: **sin selector, no**.

## 4. El hueco: 56 instancias que resuelve alguien del top-10 y LabeSAT no

| Grupo | Familias (instancias) | Quién las resuelve | Qué podría cobrarlo |
|---|---|---|---|
| **Paridad mezclada con otras restricciones** | *syndrome-decoding* (4), *xor-shifting* (2), *minimal-disagreement-parity* (2), *binary-tree-parity* (1), *equivalence-chain-principle* (1) | MAB, *lymphosat*, *mergesat-l* | **X1b** (unidades y equivalencias implicadas por el sistema XOR) y **fases de Gauss** (research/06, X2). EXP-019 §3b es la primera medida |
| **SAT combinatoria simétrica** | *boxfolding* (3), *allowable-sequence* (3), *cyclic-anti-bandwidth* (3), *ntil* (4), *sorting-networks* (2), *station-repacking* (2), *antibandwidth* (1), *coloring* (1) | Sobre todo las variantes MAB | Diversidad de heurística en SAT (§3.2: solo con selector) |
| **Ecuaciones lineales enteras** | *linear-equations* (12) | Solo *lymphosat* | Nada genérico: tienen equilibrio de signos 0, sin XOR (GBD: 1200 binarias, 400 ternarias, 19 440 de 4 literales, todas monótonas) |
| **UNSAT de circuitos y equivalencias** | *datapath-equivalence* (2), y otras | *mergesat-l* | Otro motor: no se integra |
| Resto | *fermat*, *automata-synchronization*, *circuit-multiplier*, *argumentation* (1 cada una) | varios | — |

## 5. Plan para ensanchar el margen, por valor esperado

| # | Acción | Valor esperado | Estado |
|---|---|---|---|
| 1 | **EXP-009 (B3)**: decide si la ruptura de simetrías se activa y cómo. Es la diferencia entre el puesto 16 y el 1 | −964 s frente a la configuración por defecto de hoy | **Cerrado (2026-10-03): B3 descartado.** El paquete, «siempre» (V1) y «nunca» (V2): **D-020** |
| 2 | **Activar X1** (EXP-019) | −56 s; +2 que nadie resolvió | **EXP-019 cerrado: se adopta.** *xor-chain* y *tseitin-formulas* van codificadas con contadores unarios, sin XOR: X1 no las alcanza (EXP-019 §7) |
| 3 | **PGO + LTO** en el paquete | −15 s | Adoptado (EXP-017) |
| 4 | **Topes de satsuma (P5)**: medir el tiempo de satsuma en las instancias simétricas de 2026 que tengamos y decidir el tope con datos. El de 60 s ayuda en las 3 medidas; el riesgo está en las 11 que no podemos medir | Proteger el margen (hasta +270 s de riesgo) | **EXP-020 cerrado: se mantienen 60 s** (300 s resuelve las mismas y cuesta +24,6 s). El riesgo de las 11 se declara |
| 5 | **Cobertura de X1**: en EXP-019, 103 sistemas XOR se saltan por los topes de memoria. Partirlos en componentes conexas (Gauss por componente) no cambia nada cuando no refuta (clase E con salida temprana) | Más refutaciones posibles a coste casi nulo | **EXP-021 cerrado: X1 v2 activa por defecto.** 56 de 103 pasan a «consistente», 0 refutadas; las 47 restantes tienen una componente gigante (X1 v3) |
| 8 | **Selector entre «siempre» y «nunca» (B4)** | Hasta −395 s (oráculo); real, mucho menos | **research/11** (exploratorio): regla estructural sobre los rasgos de satsuma. **EXP-023 preregistrado y en la cola**: las 374 instancias de 2025 |
| 6 | **X1b y fases de Gauss** para la paridad mezclada | Hasta ~10 instancias del hueco | Tras EXP-019; clase S, con A/B |
| 7 | **Selector para MAB** (D-018) | Hasta 14 instancias (oráculo); sin selector, nada | Solo si hay un predictor con evidencia |
| — | ~~K1, precarga~~ | ×0,931: un 7 % **más lento** (EXP-018) | Descartada |
| — | ~~Cartera secuencial con MAB~~ | Empeora con todos los f (§3.2) | Descartada |

## Referencias y datos

- Resultados oficiales de 2026: `data/competition/scores_2026.csv`; familias
  y rasgos de `data/competition/gbd.db` y `gbd_base.db`.
- research/01 (análisis de 2026), research/06 (XOR), research/07 (ganadores),
  research/09 (X1).
- EXP-007, EXP-008, EXP-011, EXP-014, EXP-016 a EXP-019.
