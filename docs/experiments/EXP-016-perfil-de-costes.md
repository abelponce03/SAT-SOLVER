# EXP-016 — Perfil de costes de LabeSAT (descriptivo, preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con
  `scripts/perfil_costes.py`, `scripts/exp016_seleccion.py` y la muestra
  (`results/exp016/*.txt`). Única ejecución previa: una prueba del arnés con
  2 instancias a 10 s, que no forma parte de los datos.
- **Fecha**: 2026-10-01
- **Decide**: qué partes de LabeSAT merece la pena optimizar
  (research/08 §3). No hay rama B: es una medida descriptiva que fija las
  fracciones *p* de la ley de Amdahl.

---

## 1. Qué se quiere saber

Por la ley de Amdahl, acelerar por *k* una parte que ocupa una fracción *p*
del tiempo acelera el total como mucho por 1 / ((1 − p) + p/k) < 1/(1 − p).
research/08 §2 mide cuánto vale en PAR-2 cada factor de aceleración: un 10 %
equivale a ~1,5 % de PAR-2. Para decidir qué optimizar hace falta saber
**dónde se va el tiempo**:

- en Kissat, por fases: búsqueda, eliminación, sondeo, vivificación,
  barrido, congruencia, parseo…;
- en la tubería: la descompresión, que con `--symmetry` se paga dos veces;
- en el binario con los temporizadores más finos (nivel 4): propagación y
  decisión, con su sobrecoste medido.

## 2. Preguntas (descriptivas, sin umbral)

> **Q1.** Fracción del tiempo de proceso de Kissat en cada fase,
> **ponderada por tiempo** (Σ segundos de la fase / Σ segundos totales), en la
> industria y en 2026 por separado, y su variación entre instancias
> (mediana y p90 de la fracción por instancia).
>
> **Q2.** Cómo cambian esas fracciones con la duración de la corrida
> (instancias que terminan en < 10 s, entre 10 y 100 s y en ≥ 100 s), para
> extrapolar con cautela a T = 5000 s.
>
> **Q3.** Coste de la descompresión `xz` frente al tiempo total.
>
> **Q4.** Con presupuesto **determinista** de 200 000 conflictos en la
> submuestra (20 de 2026): fracción de `propagate` (nivel 4) y sobrecoste de
> los temporizadores de nivel 4 frente al 3. Como el trabajo es idéntico, el
> sobrecoste es el cociente de tiempos totales.

## 3. Diseño

- **Muestra** (`exp016_seleccion.py`): 105 instancias.
  - 45 industriales: 5 por familia de tesis-dev, fuera del estrato trivial,
    por orden de md5.
  - 60 de la Main Track de 2026: `bench/calib` y `bench/calib2` enteros.
- **Binario**: `solver/kissat/build/kissat` (SHA-1 `28b587cf…`), sin opciones
  de búsqueda.
- **Corridas**: pasos `exp016-perfil` y `exp016-sobrecoste` de
  `scripts/cola.toml`:

  ```bash
  python3 scripts/perfil_costes.py --lista results/exp016/muestra.txt \
      --bench bench/tesis-dev bench/calib bench/calib2 \
      --out results/exp016/perfil.csv --timeout 200 --profile 3 --seed 42
  python3 scripts/perfil_costes.py --lista results/exp016/submuestra.txt \
      --bench bench/calib bench/calib2 --out results/exp016/nivel3.csv \
      --conflicts 200000 --profile 3 --seed 1
  python3 scripts/perfil_costes.py --lista results/exp016/submuestra.txt \
      --bench bench/calib bench/calib2 --out results/exp016/nivel4.csv \
      --conflicts 200000 --profile 4 --seed 1
  ```

- **Cuándo**: lo ejecuta la cola **antes** de reanudar EXP-009. La cola se
  detiene, entra este paso y luego sigue EXP-009 donde iba, conservando las
  parejas completas (ADR-0008). Así no hay dos tandas a la vez.
- **Coste**: ≤ 105 × 200 s ≈ 5,8 h en el peor caso, más el sobrecoste (20 × 2
  corridas cortas).

## 4. Cómo se usa el resultado

- Una parte con fracción ponderada *p* < 5 % **no se optimiza**, salvo que el
  cambio sea trivial y su equivalencia esté demostrada: su techo es un 5 % de
  velocidad, ≈ 0,8 % de PAR-2 (research/08 §2).
- Las partes con *p* grande pasan al análisis de complejidad de research/08
  §4, con prueba de corrección y de equivalencia antes de implementar nada.

## 5. Amenazas a la validez

- **T = 200 s frente a 5000 s**: en corridas cortas pesan más el preproceso y
  el parseo. Q2 lo cuantifica.
- **Temporizadores**: el nivel 3 cuesta poco; el nivel 4 se mide aparte (Q4)
  y no se mezcla con Q1.
- **Una semilla**: las fracciones varían poco con la semilla frente a lo que
  varían entre instancias. No se estima esa varianza.
- **Carga ajena**: servicios Docker del director. Afecta a los tiempos
  absolutos más que a las fracciones.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
