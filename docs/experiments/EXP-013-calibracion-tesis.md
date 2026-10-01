# EXP-013 — Calibración frente al Kissat de la tesis: misma búsqueda y velocidad de la máquina (preregistrado)

- **Estado**: **cerrado (2026-09-30)**: ambos grupos de máquinas son calibrables (factor 0,26 en pc1 y 0,47 en pc2). Preregistrado: se escribió y se commiteó **antes** de ejecutar
  (ADR-0003 §6). La selección de instancias y el guion de análisis
  (`scripts/exp013_calibracion.py`) van en el mismo commit.
- **Fecha**: 2026-09-24
- **Decide**: cómo se comparan los resultados de LabeSAT en esta máquina con
  los de Kissat en la tesis del director (D-017), sin volver a correr ese
  Kissat.

---

## 1. Qué se quiere saber

El director aportó los resultados de Kissat de su tesis sobre 955 instancias
industriales (3 semillas, T = 800 s) y pide comparar LabeSAT con ellos en vez
de volver a correr Kissat. Esa comparación mezcla tres cosas:

1. **La máquina**. La tesis corrió en `pc1` (argumentation, bitvector,
   cryptography y station-repacking) y en `pc2` (el resto). Esta máquina es un
   portátil i5-1135G7 de 4 núcleos.
2. **La versión**. La tesis usó una 4.0.x con congruencia y *factor*, pero no
   la 4.0.4. En un sondeo de 8 instancias con la misma semilla, los conflictos
   coinciden en 1 (station-repacking, 3825 = 3825) y difieren en 7, casi
   siempre por poco (8630 frente a 8569) y a veces por mucho (544 141 frente a
   89 822).
3. **LabeSAT**, que es lo único que interesa medir.

Sin separar 1 y 2 de 3, cualquier «LabeSAT gana a la tesis» puede ser la
máquina. Este experimento mide 1 y 2 con LabeSAT en su configuración **por
defecto**, que hoy hace la misma búsqueda que Kissat 4.0.4 (las features
están apagadas y B3″ solo cambia cuándo se cede el control).

## 2. Hipótesis

> **H1 (misma búsqueda, descriptiva).** Proporción de instancias resueltas en
> las que el recuento de conflictos con semilla 42 coincide **exactamente** con
> el de la tesis. Predicción, a partir del sondeo: minoritaria (< 50 %).
>
> **H2 (velocidad).** Factor por conflicto
> `f = (t_local / conflictos_local) / (t_tesis / conflictos_tesis)`, en media
> geométrica con IC95 % por bootstrap, para cada grupo de máquinas (`pc1` y
> `pc2`). Predicción: f < 1 (esta máquina más rápida por conflicto), a partir
> del sondeo (miter 0.88, hardware 0.79).

## 3. Diseño

- **Banco**: `bench/tesis-calib/`, 54 instancias (6 por familia) de la
  partición **dev**, estratos `facil` y `media`, en las que la corrida de la
  tesis con semilla 42 resolvió en [10, 400] s. Se eligen por orden de
  `md5(hash + sal)`, sin mirar nada más (`exp013_calibracion.py seleccionar`).
  Suma de tiempos de la tesis: 5956 s.
- **Solver**: `solver/kissat/build/kissat` sin opciones (el SHA-1 que vigila la
  cadena de EXP-008: `28b587cf…`).
- **Corrida**:

  ```bash
  python3 scripts/run_experiment.py --solver solver/kissat/build/kissat \
      --bench bench/tesis-calib --out results/exp013/local.csv \
      --timeout 800 --seeds 42 --label labesat-defecto --jobs 1
  python3 scripts/exp013_calibracion.py analizar
  ```

- **Cuándo**: después de la cadena `reanudar_experimentos.sh` (EXP-008, 010,
  011 y 012), con la máquina sin otras tandas de tiempo. Una tanda concurrente
  contaminaría justo lo que se mide.
- La tesis mide tiempo de **reloj** con descompresión incluida; aquí se
  compara con `wall_s`, que incluye lo mismo.

## 4. Criterio de decisión

| resultado | decisión (D-017) |
|---|---|
| IC95 % de `f` con semiancho relativo ≤ 15 % en un grupo | Ese grupo es **calibrable**: los tiempos de la tesis se escalan por `f` para estimar el PAR-2 que habría dado Kissat en esta máquina, y se informa siempre con el IC |
| Semiancho > 15 % | **No calibrable**: con la tesis solo se comparan instancias resueltas y no resueltas a T con un margen (resuelta aquí en < T/2 y no resuelta allí, o al revés), nunca tiempos |
| Cualquier resultado | Las decisiones sobre **features** de LabeSAT se siguen tomando con A/B intercalado en esta máquina (ADR-0003 §4b). La tesis sirve para seleccionar instancias y como referencia externa, no como brazo A |

## 5. Amenazas a la validez

- **Versión.** Si las trayectorias difieren, `f` mezcla máquina y versión: un
  cambio de versión que mejore la búsqueda baja los conflictos, no el tiempo
  por conflicto, pero el tiempo por conflicto también depende del tamaño de la
  fórmula en cada momento. Por eso se informan aparte la razón de conflictos y
  la de tiempo total.
- **Selección**: solo instancias resueltas en la tesis en 10–400 s. `f` puede
  no trasladarse a instancias de minutos u horas (caché, memoria). Se anota.
- **Una semilla.** Sale barato (≈ 100 min) y basta para el factor; la varianza
  entre semillas no importa aquí porque se compara la misma semilla.
- **Portátil**: frecuencia variable y temperatura. La tanda es corta y va sola.

## 6. Incidencias de ejecución

- Ejecutado por la cola (ADR-0008) el 2026-09-28, de 22:30 a 23:09 UTC, solo
  en la máquina en cuanto a tandas de experimento. Durante esas horas corrían
  servicios Docker del director, con un arranque de contenedor por minuto
  aproximadamente: es carga ajena que puede añadir ruido al tiempo de reloj.

## 7. Resultados

`python3 scripts/exp013_calibracion.py analizar`
(`results/exp013/informe.txt`, `results/exp013/calibracion.csv`).

- **54 de 54 resueltas**, con la misma respuesta que la tesis en todas.

### H1 — misma búsqueda

Conflictos idénticos a los de la tesis con semilla 42 en **8 de 54 (15 %)**,
como se predijo (< 50 %). La tesis usó otra Kissat 4.0.x: la trayectoria
cambia, aunque el número de conflictos sale parecido (razón geométrica
0,97, IC95 [0,84; 1,13]).

### H2 — velocidad de la máquina

| grupo | n | factor por conflicto (local/tesis) | IC95 % | semiancho | ¿calibrable? |
|---|---:|---:|---|---:|---|
| todas | 53 | 0,361 | [0,328; 0,396] | 9 % | sí |
| `pc1` | 24 | **0,262** | [0,242; 0,283] | 8 % | **sí** |
| `pc2` | 29 | **0,470** | [0,436; 0,505] | 7 % | **sí** |

- **Esta máquina es entre 2 y 4 veces más rápida por conflicto** que las de
  la tesis. Es más de lo que sugería el sondeo de 8 instancias cortas
  (~0,8–0,9), en el que pesaba el coste fijo de leer y descomprimir.
- El factor es **estable dentro de cada máquina** sea cual sea la duración de
  la corrida (análisis complementario, no preregistrado): `pc1` ≈ 0,22–0,28 y
  `pc2` ≈ 0,43–0,56, en tramos de 0–30, 30–100 y 100–400 s. Correlación de
  Spearman con la duración: ρ = −0,34. Por familia sigue a la máquina:
  0,23–0,28 en las de `pc1` y 0,41–0,55 en las de `pc2`.
- Hipótesis, no comprobada: la tesis lanzaba varias corridas en paralelo por
  máquina. Es la pregunta 2 de D-017.

### Decisión (§4, D-017)

**Los dos grupos son calibrables.** Para comparar con la tesis:

- se multiplica el tiempo de la tesis por el factor de su máquina (0,262 en
  `pc1` y 0,470 en `pc2`) y se informa siempre del IC;
- cualquier comparación así se etiqueta como **referencia externa
  calibrada**, nunca como A/B.

Las decisiones sobre features siguen tomándose con A/B intercalado en esta
máquina (ADR-0003 §4b).
