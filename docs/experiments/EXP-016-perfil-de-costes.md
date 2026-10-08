# EXP-016 — Perfil de costes de LabeSAT (descriptivo, preregistrado)

- **Estado**: **cerrado (2026-10-01)**. Resultados en §7 y datos en
  `results/exp016/`. Se commiteó antes de ejecutar, junto con
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

- **2026-10-01, carga concurrente.** Mientras se perfilaban las instancias
  5–9, se compiló y entrenó un binario de prueba de EXP-017 (PGO+LTO), con
  `nice -n 19` y fijado a los núcleos 6 y 7: unos 13 min de CPU. Afecta a los
  tiempos absolutos de esas instancias más que a sus fracciones por fase; se
  anota por transparencia.
- **2026-10-01, guion de análisis.** `scripts/exp016_analisis.py` se
  escribió con la tanda en marcha (22 de 105 instancias) y se probó sobre
  esos datos parciales para depurarlo. El análisis es descriptivo y el único
  umbral que se usa después (p < 5 %, §4) estaba fijado antes; el guion solo
  respeta la jerarquía de fases de Kissat (`profile.h`): parse, search y
  simplify son disjuntas y el resto anida dentro. Lo ejecuta el paso
  `exp016-informe` de la cola.
- **2026-10-01, fallo del guion en Q4.** El primer informe no listaba
  `propagate` ni `decide`. `DataFrame.join` con `lsuffix`/`rsuffix` solo
  renombra las columnas que existen en los dos niveles, y esas dos solo
  existen en el nivel 4. Se corrigió con `add_suffix` en las dos tablas y se
  regeneró el informe. Los datos no cambian; solo la tabla de Q4 gana esas
  dos filas.
- **2026-10-01, 03:15–04:00, tercera carga concurrente.** Validación de X1
  (research/09): el prototipo en Python, los tres verificadores, Kissat con
  120 s por familia sintética y la compilación de X1. Todo en los núcleos 6
  y 7, a prioridad mínima. Coincidió con las instancias 35 a 60 de la
  muestra, aproximadamente. Afecta, como las anteriores, más a los tiempos
  absolutos que a las fracciones.
- **2026-10-01, 02:26–02:45, segunda carga concurrente.** Compilación de K1
  (11 s, 2 núcleos) y su comprobación de equivalencia: 6 instancias de
  `calib2` × 2 binarios, 20 000 conflictos, en los núcleos 6 y 7. Coincidió
  con el perfilado de las instancias 26 a 32 de la muestra. El proceso de la
  sesión tenía *niceness* −8, así que `nice -n 19` dejó esas corridas en 11:
  menos prioridad que la tanda (5), pero no la mínima. Como en la primera
  incidencia, afecta más a los tiempos absolutos que a las fracciones.

## 7. Resultados

Informe completo: `results/exp016/informe.md`
(`scripts/exp016_analisis.py`). Muestra: 105 instancias (45 industriales y
60 de 2026). Estados a 200 s: 45 sin resolver, 36 SAT, 23 UNSAT y un error
de lectura.

**Q1. Fracción ponderada por tiempo** (industria / 2026):

| Fase | Industria | 2026 |
|---|---|---|
| Búsqueda (`search`) | 77,1 % | 76,2 % |
| — búsqueda sin hijos (propagación + decisión + retroceso) | **56,7 %** | **58,7 %** |
| — análisis de conflictos (`analyze`) | 18,6 % | 16,0 % |
| — — `shrink` | 5,7 % | 4,1 % |
| — — `deduce` | 3,4 % | 3,5 % |
| — — `bump` | 2,7 % | 2,5 % |
| — `reduce` | 1,3 % | 1,2 % |
| Simplificación (`simplify`) | 21,7 % | 17,9 % |
| — sondeo (`probe`) | 18,5 % | 15,0 % |
| — — vivificación | 8,6 % | 7,9 % |
| — eliminación | 3,6 % | 3,0 % |
| Lectura (`parse`) | 0,2 % | 1,0 % |

**Q2. Por duración.**

- En las corridas de ≥ 100 s (53 instancias), la búsqueda sin hijos llega
  al 58,6 % y la lectura es el 0,1 %.
- En las de < 10 s (20 instancias), la lectura es el 36 %: es un coste fijo
  de instancias que se resuelven igual.

**Q3. Descompresión.** Σ xz = 61 s frente a 11 746 s de Kissat (0,5 %). En
la competición las CNF llegan sin comprimir (research/08 C6).

**Q4. Nivel 4, mismo trabajo** (200 000 conflictos, 20 instancias de 2026,
20/20 con contadores idénticos entre niveles):

- **`propagate`: 56,6 % ponderado** (mediana 51,1 %, p90 65,7 %). Este
  temporizador cuenta también la propagación del sondeo, por eso supera a
  la «búsqueda sin hijos» (52,8 %).
- `decide`: 1,0 %.
- `analyze`: 13,6 %.
- Los temporizadores de nivel 4 cuestan ×1,145 (media geométrica; de ×1,03
  a ×1,44). Por eso las fracciones de nivel 4 sobrestiman un poco las fases
  muy cortas y repetidas como `propagate`.

**Conclusión (regla de §4: solo se optimiza lo que pesa ≥ 5 %).**

- **Propagación, ≈ 50–57 %.** Es la candidata principal. Su techo de
  Amdahl es 1/(1 − 0,57) ≈ 2,3×. Ya está en la cola **K1** (precarga,
  EXP-018); K2 y K4 son variantes de lo mismo (research/08 §6.2).
- **Análisis, 14–19 %.** Por el Lema 1 de research/08, cualquier cambio
  que visite otras razones cambia los ticks y es de clase S. Solo caben
  micro-optimizaciones de clase E.
- **Sondeo y vivificación, 15–19 %.** Su presupuesto lo fijan los ticks
  (`SET_EFFORT_LIMIT`). Acelerarlos sin cambiar su cuenta de ticks es de
  clase E y reduce su tiempo sin tocar la búsqueda. Es candidata para
  después de K1.
- **Fuera**, por pesar < 5 %: eliminación, `reduce`, `collect`, `restart`,
  la lectura y la descompresión.
