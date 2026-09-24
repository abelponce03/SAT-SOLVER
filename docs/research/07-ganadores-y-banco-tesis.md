# Investigación 07 — Qué hicieron los ganadores (2021–2026), qué dice el banco de la tesis y qué probar en LabeSAT

- **Fecha**: 2026-09-24
- **Pedido del director**: revisar todo el trabajo hecho, integrar el banco
  industrial de su tesis (≈ 1900 instancias y los resultados de Kissat) y
  profundizar en ideas nuevas **tomando como referencia a los ganadores de la
  Main Track**.
- **Fuentes primarias**:
  - diapositivas oficiales de resultados de 2025;
  - actas de 2025 (descripciones de los solvers);
  - **paquetes de código** de los solvers de 2026 (`anders`, `zheng`),
    leídos solo para saber qué técnica usan. No se copió código: el paquete
    ganador es GPLv3 por cliquer, y de cliquer no se abrió ningún fichero,
    para mantener la sala limpia de mclique (D-005);
  - `results/tesis-kissat.reference.csv` (955 instancias × 3 semillas).

---

## 0. Resumen

1. **Los tres primeros de 2026 son satsuma + una variante de Kissat.** La
   idea B2 del catálogo («hiper-resolución binaria», por el nombre
   `kissat-mab-hypre`) partía de una suposición falsa. Ese solver es
   **satsuma + Kissat_MAB 4.0.2** (§2). La palanca P1 del plan queda más
   respaldada que antes, y B2 desaparece como línea independiente.
2. **El ganador de 2025 (AE-Kissat-MAB) es un solver evolucionado con LLM**,
   y dos variantes de 2026 salen de SATLUTION, otro marco de evolución con
   LLM. Los solvers con IA **ya encabezan el ranking**. Esto cambia el
   contexto de D-002 (§2.3).
3. **En la tesis, a Kissat le quedan pocas instancias que otros solvers sí
   resuelven**: 29 de 883 válidas (3,3 %), sobre todo SAT de criptografía
   (8) y UNSAT de hardware (5). En cambio, la **variación entre semillas** es
   grande: el oráculo de semilla baja el PAR-2 un 8,3 % (§3).
4. **Esa variación no se puede cobrar a ciegas.** Simulado con los datos de
   la tesis, repartir el tiempo entre 2 o 3 semillas **empeora** el PAR-2
   (683 → 713 → 744 s). Los reinicios fríos «ciegos» se descartan sin
   implementarlos (§3.3).
5. **Líneas nuevas**, por relación coste/evidencia (§4):
   - **N1 · VSA**: implementada detrás de una opción y verificada;
     EXP-015 preregistrado;
   - **N2 · bandido VSIDS/CHB**: se reabre como candidata para V3 (D-018);
   - **N3 · predicción SAT/UNSAT**: se fusiona con B3;
   - el resto, aparcado o descartado con motivo.

---

## 1. Los ganadores de la Main Track, año a año

| Año | 1.º (general) | Qué aporta | Base |
|---|---|---|---|
| 2021 | Kissat_MAB (Cherif, Habet, Terrioux) | Bandido UCB que elige **VSIDS o CHB** en cada reinicio | Kissat |
| 2022 | Kissat_MAB-HyWalk | Lo anterior más búsqueda local híbrida para las fases | Kissat_MAB |
| 2023 | SBVA-CaDiCaL (Haberlandt, Green, Heule) | **BVA estructurada** como preproceso | CaDiCaL 1.5.3 |
| 2024 | kissat-sc2024 (Biere et al.) | Cierre por congruencia, *sweeping* de equivalencias, BVA (`factor`), fases *lucky* con *look-ahead*, vivificación revisada | Kissat |
| 2025 | **AE-Kissat-MAB** (Ding, Luo, Li et al.) | Kissat_MAB con `bump` y `restart_mab` **evolucionados con LLM** (DeepSeek-R1, Claude 3.7 y GPT-4.5): decaimiento dinámico y momento en el UCB | Kissat 4.0.2 + MAB |
| 2026 | **satsuma-iter-kissat** (Anders et al.) | Ruptura de simetrías (satsuma 1.3 con cliquer) + Kissat | Kissat 4.0.4 |

**2025 en detalle** (400 instancias, T = 5000 s):

| | 1.º | 2.º | 3.º |
|---|---|---|---|
| General | AE-Kissat-MAB (2264,7; 327) | Kissat-public (2423,4; 321) | Kissat-VSA (2478,5; 317) |
| SAT | AE-Kissat-MAB | Kissat-public | Kissat-CURE |
| UNSAT | CaDiCaL-sc2025 | **Kissat-VSA** | AE-Kissat-bump |

Otras técnicas presentes en 2025:

- **Kissat-Pred**: árboles de decisión sobre *features* de grafos, entrenados
  con instancias públicas, que predicen SAT/UNSAT y ajustan reinicios y
  cambio de modo.
- **Kissat-CURE**: bandido sobre parámetros (DCT) y **reinicios fríos** que
  olvidan orden, fases o cláusulas.
- **ULC/XLC** (Reeves): recodificar restricciones *exactly-one* con
  contadores secuenciales.
- **amSAT**: BVA dinámica guiada por actividad.

**Constantes en seis años**: todos los ganadores salvo el de 2023 son Kissat
con **una** idea añadida, y la idea es de tres tipos:

1. **preproceso estructural** (BVA en 2023, congruencia en 2024, simetrías en
   2026);
2. **elegir entre dos heurísticas de decisión** (VSIDS/CHB en 2021, 2022 y
   2025);
3. **ajuste fino de fórmulas internas** (2025, con LLM).

## 2. Correcciones al catálogo y al plan

### 2.1 B2 no era hiper-resolución binaria

`zheng/kissat-mab-hypre/src/run.sh` (paquete oficial de 2026) hace:

1. `satsuma` con topes propios:
   - `--component-limit 500000`;
   - `--order-model-limit 750000`;
   - `--dense-model-limit 20000000`;
   - solo si la fórmula tiene menos de 5 M de variables;
   - pruebas en VeriPB.
2. Después, un Kissat **4.0.2 con MAB VSIDS/CHB** (`options.h`: `heuristic`,
   `mab`, `stepchb`).

Consecuencias:

- **Los tres primeros de 2026 llevan satsuma**:
  - `satsuma-iter-kissat`: 276 resueltas;
  - `satsuma-iter-ae-kissat-mab`: 269;
  - `kissat-mab-hypre`: 255.

  La diferencia entre ellos (21 instancias) viene de cómo se configura
  satsuma y de qué Kissat va detrás. Eso respalda **P5** (topes de satsuma)
  como palanca, y no solo como detalle.
- **B2 se retira del catálogo** como línea propia: su techo (−615 s) era el
  de satsuma + MAB.
- El paquete de 2026 incluye además `kissat-mab-hypre-satlution`, con un
  `CHANGELOG` de cambios generados por SATLUTION (p. ej., añadir una segunda
  `transitive_reduction` tras `congruence` en `probe.c`).

### 2.2 Qué satsuma usó el ganador

- `satsuma-iter-kissat` lleva un «satsuma-dev» con la cabecera
  *satsuma 1.3* y cliquer. El nuestro es el upstream (*1.4*, `c6ad1b5`, MIT),
  con mclique como sustituto (EXP-010 y EXP-011).
- Los argumentos de `satsuma fix` son **los mismos** que usa `solver/labesat`
  (`--full-skip-limit 100000000 --add-reduced-as-unit --bsr`). El ganador **no
  pone tope de tiempo ni de tamaño** (los tenía comentados).
- Nuestro tope de 60 s importa en la industria: en station-repacking, satsuma
  gasta 35–50 s en la fase de Schreier (EXP-014, parte 1).

### 2.3 La IA ya gana la Main Track

- AE-Kissat-MAB (1.º en 2025) declara un marco de evolución con varios LLM.
- `kissat-mab-hypre-evolve` y `-satlution` (2026) salen de marcos de
  evolución de código con LLM.
- El artículo de SATLUTION afirma superar a los ganadores de 2025.

Para D-002: la etiqueta «AI-generated» no deja a LabeSAT fuera del grupo de
cabeza; lo sitúa entre los que marcan el ritmo. Refuerza el plan de
**declaración honesta** (D-015) sin cambiar su contenido.

## 3. Lo que dice el banco de la tesis

Datos: `results/tesis-kissat.reference.csv`, 883 instancias válidas (sin
`.xz` dañados), 3 semillas, T = 800 s.

### 3.1 Dónde es débil Kissat

Una corrida sin resultado (`TIMEOUT`, `UNKNOWN` o ausente) cuenta como 2T.

| Familia | PAR-2 medio por semilla (T = 800 s) | Tasa de resolución (tabla de la tesis) |
|---|---:|---:|
| argumentation | 1159,5 | 37,6 % |
| bitvector | 1058,7 | 47,3 % |
| cryptography | 1015,4 | 45,9 % |
| scheduling | 770,4 | 59,6 % |
| miter | 479,0 | 75,4 % |
| software-verification | 425,2 | 82,1 % |
| station-repacking | 397,7 | 80,0 % |
| planning | 393,8 | 78,7 % |
| hardware-verification | 384,5 | 82,4 % |

### 3.2 Complementariedad con otros solvers: pequeña

Instancias que CaDiCaL, CryptoMiniSat o MiniSat resuelven en alguna semilla y
Kissat en **ninguna**: **29**.

- cryptography: 8, todas SAT (MiniSat resuelve 5);
- software-verification: 6;
- hardware-verification: 5, todas UNSAT (CMS resuelve 5);
- bitvector: 5;
- argumentation, scheduling y station-repacking: 1–2.

Lectura: en esta industria, el hueco de Kissat no está en «otro solver lo
haría mejor». Las 8 SAT de criptografía que resuelve hasta MiniSat son un
indicio de que la búsqueda de Kissat, más pesada, estorba en algunas SAT.
Son una muestra pequeña: la anotamos, sin línea propia.

### 3.3 Variación entre semillas: grande, pero no se puede cobrar a ciegas

- **62 instancias inestables** (1 o 2 de 3 semillas); razón máx/mín del
  tiempo entre semillas: mediana 1,35, p90 4,34, máximo 130.
- **Oráculo de semilla** (la mejor de las 3 por instancia): PAR-2 683,2 →
  626,6 (**−8,3 %**). Por familia, entre −4,4 % (planning) y −15,4 %
  (software-verification).
- **Cartera de semillas desde cero** con reparto de tiempo (simulación exacta
  con los tiempos de la tesis, media de todos los órdenes):

  | Estrategia | PAR-2 (T = 800 s) |
  |---|---:|
  | una semilla | 683,2 |
  | 2 semillas, T/2 cada una | 713,4 |
  | 3 semillas, T/3 cada una | 743,5 |
  | oráculo de semilla | 626,6 |

  Repartir **empeora**. Es la misma conclusión que research/05 sacó con la
  ruptura sí/no: la ganancia del oráculo está en **predecir**, no en repartir.
- **Consecuencia**: se descartan los reinicios fríos a ciegas (Kissat-CURE,
  políticas FO/FP/FC) como línea propia. Solo tendrían sentido con un
  criterio que prediga cuándo una trayectoria está atascada, y eso es A4, que
  ya dio nulo (EXP-006).

### 3.4 Cautelas para comparar con la tesis

- **Otra versión.** Con la misma semilla, los conflictos coinciden en 1 de 8
  instancias del sondeo.
- **Otras máquinas**, según la familia.
- **Reloj con descompresión**.

La comparación se calibra en EXP-013 (D-017). Las decisiones sobre *features*
se toman con A/B intercalado en esta máquina.

## 4. Líneas para LabeSAT, priorizadas

| # | Idea | Evidencia | Coste | Estado |
|---|---|---|---|---|
| **P1+P5** | Ruptura de simetrías condicional y **topes de satsuma** | Top-3 de 2026 (§2.1); EXP-007 | hecho / bajo | EXP-014 mide el coste en la industria; los topes se deciden con sus datos |
| **B3** | Activación condicional | EXP-007; el oráculo vale −322 s | medio | EXP-014 aporta ejemplos industriales de daño (`b3-industrial.csv`) |
| **N1** | **VSA**: vivificación programada por actividad | 2.º en UNSAT de 2025, sobre sc2024 | **bajo** (~60 líneas) | **Implementada** (`vivifyactivity`, apagada); **EXP-015** preregistrado |
| **N2** | **Bandido VSIDS/CHB** (línea Kissat_MAB) | 1.º en 2021, 2022 y 2025; en 2026, detrás de satsuma en el 3.º | medio (CHB + UCB; Kissat_MAB es MIT) | research/05 lo aparcó por EXP-006. **Se propone reabrirla como V3** (D-018) |
| **N3** | Predicción SAT/UNSAT con *features* baratos (Kissat-Pred) | 2025, puesto medio | medio | Se **fusiona con B3**: los mismos *features* deciden simetrías y ajustes |
| N4 | Recodificación ULC/XLC (Reeves) | 2025, puestos bajos | alto | Aparcada |
| N5 | SBVA | 2023; Kissat ya trae `factor` (BVA) | medio | Aparcada: solapa con Kissat |
| N6 | Reinicios fríos a ciegas (CURE) | 3.º SAT en 2025 | bajo | **Descartada por simulación** (§3.3) |
| N7 | Evolución de código con LLM (AE, SATLUTION) | Ganadores 2025 y variantes 2026 | cómputo masivo | **No se persigue**: choca con el preregistro y con 4 núcleos. Se documenta como contraste metodológico para el artículo |
| X1 | Refutar en la raíz sistemas XOR inconsistentes | research/06 | medio | Aparcada con prioridad (ADR-0007, fase 2) |

### Por qué N1 va primero

Es la única idea de un ganador reciente que:

1. es un cambio **local**: el orden de un planificador que ya existe, sin
   estructuras nuevas;
2. deja la búsqueda **idéntica** con la opción apagada (verificado);
3. se puede medir en una tanda de ~6 h.

Si sale nula, cuesta poco. Si sale positiva, es una palanca que se suma a
satsuma sin interferir: una actúa antes de buscar y la otra durante.

### Por qué reabrir N2 (D-018)

- La línea VSIDS/CHB ha ganado **tres** Main Track (2021, 2022, 2025).
- En 2026, `kissat-mab-hypre` (satsuma + MAB) quedó 3.º, pero por detrás de
  satsuma + Kissat 4.0.4. Sobre la misma base de Kissat, el MAB no está
  aislado en los datos oficiales.
- El nulo de A4.1 (EXP-006) era sobre el reparto entre modos, no sobre la
  heurística de decisión.

**Propuesta**: portar CHB y el UCB de Kissat_MAB (MIT) detrás de una opción,
**después** de EXP-008 (la base decide dónde se porta). Queda como variante
V3 si un A/B la respalda.

## 5. Decisiones que abre este documento

- **D-018**: reabrir la línea VSIDS/CHB (N2) como candidata a V3.
- La corrección de B2 se aplica directamente en research/02 y en el plan: es
  un error de hecho, no una decisión.

## Fuentes

- Resultados de 2025: https://satcompetition.github.io/2025/satcomp25slides.pdf
- Actas de 2025: https://repositum.tuwien.at/bitstream/20.500.12708/218424/2/ (Codel et al., eds.)
- CaDiCaL, Gimsatul, IsaSAT y Kissat en 2025: https://cca.informatik.uni-freiburg.de/papers/BiereFallerFleuryFroleyksPollitt-SAT-Competition-2025-solvers.pdf
- Paquetes de 2026: https://satcompetition.github.io/2026/downloads/solvers/ (`anders.tar.xz`, `zheng.tar.xz`)
- Ganadores 2021–2023: diapositivas oficiales de cada edición (satcompetition.github.io)
- SATLUTION: https://arxiv.org/abs/2509.07367
- Cherif, Habet y Terrioux (2021), *Combining VSIDS and CHB using restarts in SAT*, CP.
