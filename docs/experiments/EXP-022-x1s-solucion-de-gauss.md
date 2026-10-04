# EXP-022 — X1s: la solución de Gauss como asignación afortunada (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con la
  implementación (`gauss.c` y `lucky.c`, opción `--gausslucky`, apagada),
  `scripts/exp022.py` y la ampliación de `scripts/test_gauss.sh`.
- **Ejecuciones previas** (no forman parte de los datos):
  - el prototipo en Python (`scripts/x1s_prototipo.py`) sobre 4 instancias
    (research/09 §3.5);
  - `test_gauss.sh` sobre las familias sintéticas de `gen_paridad.py` (semilla
    3, distinta de la de la muestra, 7), en release, ASan/UBSan y
    depuración.
- **Fecha**: 2026-10-03
- **Decide**: si `--gausslucky` se activa por defecto.

---

## 1. Qué se quiere saber

X1 (EXP-019 y EXP-021) refuta los sistemas XOR inconsistentes. X1s usa la
misma eliminación en el caso contrario (research/09 §3.5):

- toma una solución particular σ del sistema consistente;
- comprueba, sin escribir nada en el solver, si σ satisface **todas** las
  cláusulas;
- si las satisface, `kissat_lucky` la asigna la primera, y la
  Proposición 4 garantiza que no hay conflicto.

Por construcción, X1s solo cambia algo cuando σ es un modelo. Hay que
medir lo mismo que en EXP-019:

- que no se equivoca;
- que no cambia la búsqueda cuando no actúa;
- que no cuesta más de lo admitido;
- y dónde actúa.

## 2. Hipótesis

> **H0 (seguridad, vinculante).** Todo SAT que dé X1s tiene un modelo que
> `scripts/verify_model.py` acepta contra la CNF **original**. X1s nunca
> actúa en una instancia UNSAT conocida (sería imposible: actuar exige un
> modelo).
>
> **H1 (equivalencia, vinculante).** En todas las instancias en las que el
> sistema es consistente y X1s **no** actúa (σ calculada y rechazada), los
> contadores de `--statistics` son idénticos con `--gausslucky=0` y
> `--gausslucky=1` (2000 conflictos, semilla 1).
>
> **H2 (coste).** El tiempo de X1s (sustitución hacia atrás y comprobación
> de σ) tiene p95 ≤ 0,1 s y máximo ≤ 2 s por instancia.
>
> **H3 (efecto, descriptivo).** En qué instancias actúa, y cuánto tarda
> Kissat sin X1s en ellas (tiempos oficiales de 2026 o de EXP-019).

**Predicción honesta**:

- H0 y H1 se cumplen, por la comprobación de σ y la Proposición 4.
- H2 se cumple: la comprobación se detiene en la primera cláusula falsa.
- H3: X1s actúa en las instancias de paridad **puras** y satisfacibles:
  - `75429ff7` (*random-graph-xorsat*, calib);
  - `28dcc411` (*lights-out*, symm2026);
  - `01d6fa8e` (*lights-out*, dev);
  - las 4 variantes satisfacibles del conjunto sintético.

  En la industria, en ninguna: las XOR son una parte de la fórmula.

## 3. Diseño

- **Binario**: `solver/kissat/build-x1s/kissat`, con
  `./scripts/build.sh --dir=build-x1s --jobs=4`, compilado por la cola desde
  el commit de este preregistro. Compila con `--gauss` por defecto, sin
  PGO, como los binarios de EXP-019 y EXP-021.
- **Muestra**: la de EXP-019 (`results/exp019/muestra.csv`, 577 instancias
  de calib, calib2, symm2026, tesis-dev y sintéticas) más su ampliación
  (`muestra-dev.csv`, 5 de paridad de `bench/dev`). No se usa `bench/test`.
- **Paso 1** (`exp022.py correr`, `results/exp022/x1s.csv`): en cada
  instancia,

  ```bash
  kissat --gauss=1 --gausslucky=1 --verbose=1 --conflicts=0 --preprocess=false <cnf>
  ```

  - Con `--conflicts=0` no hay búsqueda: solo X1, X1s y los intentos
    `lucky` anteriores al preproceso.
  - Se anota el resultado de X1s, que sale de su propio mensaje:
    - «actúa», con el tiempo;
    - «rechazada», con el tiempo;
    - «no aplica»: X1 refuta, se salta alguna componente o no hay XOR.
  - Si X1s actúa, el modelo se verifica con `verify_model.py` contra la CNF
    original.
- **Paso 2** (`exp022.py equivalencia`, `results/exp022/equivalencia.csv`):
  - Instancias con X1s «rechazada».
  - Contadores con `--gausslucky=0` y `--gausslucky=1`, 2000 conflictos,
    semilla 1.
  - EXP-019 y EXP-021 usaron 20 000 conflictos. Aquí 2000, por coste: en
    EXP-021, las instancias más grandes llevaron ~38 h. Un cambio de estado
    (fases, traza o cláusulas) alteraría ya las primeras decisiones, así que
    2000 conflictos bastan para verlo.
- **Análisis** (`exp022.py analizar`): H0 a H3.
- **Cuándo**: en la cola. Coste estimado: el paso 1 como el de EXP-019
  (~10 min); el paso 2, ~255 parejas a 2000 conflictos, unas horas.

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| H0, H1 y H2 | `--gausslucky` vale 1 por defecto |
| H0 y H1, pero no H2 | Se acota la comprobación (p. ej., solo si las XOR cubren casi toda la fórmula), y se repite solo H2 |
| H0 o H1 fallan | No se activa, y se busca el fallo |

## 5. Amenazas a la validez

- **Pocas instancias donde actúa** (3 reales y 4 sintéticas): H3 es
  descriptivo. El valor esperado en 2026, con los tiempos oficiales, es de
  −2,3 a −2,7 s de PAR-2 (research/09 §3.5).
- **H1 a 2000 conflictos**, no a 20 000 (§3).
- **La muestra es la de EXP-019**: X1s depende de X1, y el diseño se hizo
  mirando instancias de esa muestra. H0 y H1 no dependen de eso: son
  propiedades por construcción que aquí se comprueban.
- **Carga ajena**: la noche del preregistro la máquina tenía procesos del
  director (navegador sin pantalla, ffmpeg) con carga de ~13. Afecta a los
  tiempos de H2, no a H0 ni a H1. Si la carga sigue, se anota en §6.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
