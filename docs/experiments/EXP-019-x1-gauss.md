# EXP-019 — X1: refutación de sistemas XOR por Gauss con prueba (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con:
  - la implementación (`solver/kissat/src/gauss.c`, detrás de
    `configure --gauss`, y la opción `--gauss`, apagada);
  - `scripts/exp019.py`, `scripts/test_gauss.sh` y `scripts/gen_paridad.py`;
  - la muestra (`results/exp019/muestra.csv`).
- **Ejecuciones previas** (no forman parte de los datos):
  - el prototipo en Python y la implementación en C sobre familias
    sintéticas (research/09 §4);
  - la comprobación de equivalencia en 5 instancias de 2026, que destapó que
    X1 refuta `667341ee` (*lights-out*, `bench/calib2`) en 0,02 s, con prueba
    verificada por los dos `dsr-trim`;
  - una prueba del arnés en 3 instancias.
- **Fecha**: 2026-10-01
- **Decide**: si LabeSAT activa X1 por defecto (`configure --gauss` y
  `--gauss=1`) en los experimentos siguientes y en el paquete de competición
  (research/09 §7, paso 3).

---

## 1. Qué se quiere saber

X1 (research/09 §3) extrae el subsistema XOR de la CNF y le aplica Gauss
sobre GF(2). Si es inconsistente, refuta la fórmula con una prueba DRAT con
variables de extensión. El Teorema 1 garantiza que la prueba es correcta y
acota su tamaño. Si no refuta, no toca el estado del solver (research/09 §3,
observaciones).

Quedan tres cosas por medir:

- que **no se equivoca** en instancias reales (seguridad);
- que **no cambia la búsqueda** cuando no refuta;
- **cuánto cuesta** en las instancias en las que no sirve, que son casi
  todas.

## 2. Hipótesis

> **H0 (seguridad, vinculante).**
> - X1 no refuta ninguna instancia cuyo resultado conocido sea SAT.
> - Toda refutación lleva una prueba que verifican los dos `dsr-trim`: el
>   del commit de SC2026 y el actual.
>
> **H1 (equivalencia, vinculante).** En las instancias que X1 no refuta,
> `--gauss=1` y `--gauss=0` dan los mismos contadores de `--statistics`
> (con 20 000 conflictos y la semilla 1).
>
> **H2 (coste).** El tiempo de X1 por instancia tiene p95 ≤ 1 s y máximo
> ≤ 10 s.
>
> **H3 (efecto, descriptivo).** Qué instancias refuta, en cuánto tiempo, con
> qué tamaño de prueba y cuánto tarda su verificación.

**Justificación de H2.** Un coste fijo c por instancia sube el PAR-2 a lo
sumo en la media de c, salvo las instancias que caigan justo en el límite de
tiempo (research/08 §2). Con p95 ≤ 1 s y máximo ≤ 10 s, el coste es menor
que el ruido entre semillas.

**Predicción honesta**:

- H0 y H1 se cumplen: lo exigen el Teorema 1 y el diseño, y ya pasan en
  `test_gauss.sh`.
- H2 es la incertidumbre real: la extracción recorre todas las cláusulas
  cortas y las ordena, y en instancias industriales con millones de
  cláusulas puede costar segundos.
- H3: refuta `667341ee` y las sintéticas UNSAT; en el banco industrial,
  probablemente ninguna.

## 3. Diseño

- **Binario**: `solver/kissat/build-x1/kissat`, compilado con
  `./scripts/build.sh --dir=build-x1 --gauss` desde el commit de este
  preregistro (paso `exp019-construir`).
- **Muestra** (`exp019.py muestra`, `results/exp019/muestra.csv`):
  - las instancias únicas de `bench/calib`, `bench/calib2`,
    `bench/symm2026` y `bench/tesis-dev`;
  - 8 sintéticas de `gen_paridad.py` con semilla 7: 4 familias, cada una en
    su versión UNSAT y SAT;
  - **nunca** `bench/test`.

  El resultado conocido sale de las listas de 2026 (`resultado`) y de
  Kissat en la tesis (`k_resultado`).
- **Paso 1** (`exp019.py correr`): en cada instancia se ejecuta
  `kissat --gauss=1 --conflicts=0 --preprocess=false --lucky=false`, que
  corre X1 y nada más. Se anotan:
  - el resultado de X1 (refutada, consistente, sin XOR o saltada por
    límites);
  - su tiempo, medido por el propio X1;
  - el tamaño del sistema.

  Si refuta, se repite con prueba y se verifica con los dos `dsr-trim`
  (tope de 3600 s cada uno).
- **Paso 2** (`exp019.py equivalencia`): contadores con `--gauss=0` y
  `--gauss=1` en:
  - todas las instancias con un sistema XOR no refutado;
  - las 45 industriales de la muestra de EXP-016.
- **Análisis** (`exp019.py analizar`): H0 a H3 tal como están escritas, sin
  más pruebas estadísticas. Es un experimento de seguridad y coste, no un
  A/B de PAR-2.
- **Cuándo**: en la cola, después de EXP-018 y antes de reanudar EXP-009.
  Coste estimado: ~600 corridas de X1 solo (lectura de la CNF más X1),
  ~100 parejas de equivalencia y las verificaciones de las refutadas,
  unas 2 h.

## 3b. Ampliación: instancias de paridad de 2026 (preregistrada el 2026-10-01)

El director autorizó descargar de GBD (`scripts/fetch_gbd.py`) las cinco
instancias de paridad de `bench/dev.list.csv`. Se guardan en `bench/dev/`,
fuera de git; son 0,9 MB en total. Se miden con el mismo arnés, con la
muestra en `results/exp019/muestra-dev.csv`, la salida en
`results/exp019/x1-dev.csv` y el paso `exp019-ampliacion` de la cola.

| Instancia | Familia | Resultado conocido | 2026 | Variables / cláusulas | Predicción |
|---|---|---|---|---|---|
| `3a840939` | *xor-chain* | desconocido | ninguno de los 33 solvers | 23 815 / 47 691 | X1 la refuta si es una paridad inconsistente en cadena de XOR cortas, que es lo que sugiere el nombre. Incierto |
| `7e218509` | *tseitin-formulas* | desconocido | ninguno de los 33 solvers | 18 601 / 37 462 | La refuta si es una Tseitin con carga impar y vértices de grado ≤ 6. Incierto |
| `22c8d6aa` | *ordering-principle-xor* | UNSAT | 24 solvers (el ganador, en 141 s); la base Kissat, no | 3 120 / 477 680 | **No** la refuta: la contradicción viene del principio de orden, no del álgebra lineal, y las XOR son la sustitución que la endurece. El sistema XOR solo es consistente |
| `a60a1383` | *xor-shifting* | SAT | ningún solver de la Main Track; solo `kissat-sup` (track experimental, 1088 s) | 2 651 / 9 500 | No la refuta (es SAT) |
| `01d6fa8e` | *lights-out* | SAT | 28 solvers; la base Kissat, en 600 s | 625 / 9 216 | No la refuta (es SAT; X1 no busca modelos) |

- **No cambia el criterio de decisión** (§4).
- La seguridad sí cuenta: una refutación de las dos SAT, o una prueba que
  no verifique, es un fallo de H0. Ese tipo de fallo no se tolera en ningún
  banco.
- Las tres de resultado desconocido o UNSAT son descriptivas. Si X1 refuta
  una desconocida con prueba verificada por los dos `dsr-trim`, su resultado
  pasa a ser **UNSAT demostrado**.

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| H0, H1 y H2 | X1 se activa por defecto: `build.sh` compila con `--gauss` y la opción pasa a valer 1. Se documenta en el manual y en la descripción para la competición |
| H0 y H1, pero no H2 | Se ajustan los límites (`gaussops`, `gaussbits` y un tope de cláusulas candidatas) y se repite el paso 1 en un experimento nuevo |
| H0 o H1 fallan | **No se adopta.** Contradice el Teorema 1 o el diseño: se busca el fallo antes de nada |

**Ampliación**: §3b.

## 5. Amenazas a la validez

- **Pocas instancias de paridad** en los bancos locales: H3 dice dónde actúa
  X1, no cuánto vale en la competición de 2027. El valor esperado sale de
  research/06 §5 con los datos de 2026.
- **El tiempo de X1 se mide con el reloj del proceso**, dentro de Kissat. No
  incluye la lectura de la CNF, que se paga igual sin X1.
- **Las equivalencias usan 20 000 conflictos**: X1 actúa antes de la
  búsqueda, así que si no cambia el estado inicial, la búsqueda es la misma
  a cualquier presupuesto.

## 6. Incidencias de ejecución

- **2026-10-01, antes de ejecutar.** La primera versión de la muestra
  (commit `71da9ae`) daba «unknown» a las 450 de `tesis-dev`: la lista de la
  tesis escribe el resultado en mayúsculas (`SAT`, `UNSAT`). Se corrigió
  `exp019.py` y se regeneró la muestra. Las instancias son las mismas; solo
  cambia la columna `known`, que H0 usa para comprobar que X1 no refuta
  instancias SAT.

## 7. Resultados

(pendiente)
