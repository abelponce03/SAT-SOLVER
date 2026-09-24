# Benchmarks

Esta carpeta contiene las instancias CNF (formato DIMACS) para medir el solver.

## `sample/` — instancias de muestra (versionadas)

Generadas por `../scripts/gen_benchmarks.py`. Son pequeñas y sirven para
**validar el harness**, no para sacar conclusiones de rendimiento (CaDiCaL las
resuelve todas en milisegundos). Dos familias:

- **pigeonhole `php_(n+1)_n.cnf`** — UNSAT, dificultad crece rápido con `n`.
  Buen estrés para la parte de refutación (donde entran las pruebas DRAT).
- **random 3-SAT `rand3_<vars>_r<ratio>_s<seed>.cnf`** — cerca de la razón
  crítica (~4.26 cláusulas/variable), mezcla SAT/UNSAT.

Regenerar o ampliar:

```bash
python3 ../scripts/gen_benchmarks.py --out sample \
    --php 4,5,6,7,8,9,10 --rand-vars 100,150,200,250 --seeds 1,2,3
```

Sube `n` en pigeonhole (p.ej. `--php 10,11,12`) para obtener instancias que
tomen segundos u horas: así la curva de PAR-2 se vuelve informativa.

## `tesis-dev/` y `tesis-test/` — banco industrial de la tesis (enlaces, NO versionados)

El director aportó el banco de su tesis de licenciatura: **1917 instancias**
`.cnf.xz` de 9 familias industriales (argumentation, bitvector, cryptography,
hardware-verification, miter, planning, scheduling, software-verification y
station-repacking), y los resultados de **Kissat** sobre 955 de ellas
(3 semillas: 42, 123 y 777; T = 800 s). Vive fuera del repositorio, en
`benchmark/` junto al checkout principal (o donde diga `LABESAT_TESIS_DIR`).

```bash
python3 scripts/build_thesis_bench.py --links   # listas + referencia + enlaces
```

Qué deja el guion:

| fichero | versionado | contenido |
|---|---|---|
| `bench/tesis.list.csv` | sí | una fila por instancia local: familia, partición, estrato de dificultad, integridad del `.xz`, resumen de Kissat en la tesis |
| `results/tesis-kissat.reference.csv` | sí | las 2865 corridas de Kissat de la tesis (resultado, tiempo, conflictos, decisiones, propagaciones y máquina) |
| `bench/tesis-dev/`, `bench/tesis-test/` | no | enlaces simbólicos por familia, para usarlos con `--bench` |

**Particiones** (fijadas el 2026-09-24, antes de correr LabeSAT en este banco):

| partición | instancias | uso |
|---|---:|---|
| `dev` | 450 | desarrollo, cribado y experimentos |
| `test` | 427 | **reservado**: solo validación final de una idea congelada (ADR-0003 §2) |
| `reserva` | 871 | sin referencia de Kissat; no se usan mientras no haga falta una base propia |
| `excluida` | 169 | `.xz` truncado (159 ficheros locales dañados) |

- La partición es **estratificada** por familia y estrato de dificultad de
  Kissat, y **determinista**: dentro de cada estrato se ordena por
  `md5(hash + sal)` y se alterna dev/test.
- Estratos, según las 3 corridas de Kissat de la tesis: `trivial` (las tres
  resuelven en < 10 s), `facil` (< 100 s), `media` (las tres, alguna ≥ 100 s),
  `inestable` (1 o 2 de 3), `dura` (ninguna en 800 s).
- Las instancias que ya estaban en `bench/test.list.csv` (el banco reservado de
  2026) van siempre a `tesis-test`.

**Cautelas al comparar con la tesis** (detalle en `docs/research/07`):

- La tesis corrió en **otras máquinas** (`pc1`, `pc2`, según la familia) y con
  una versión de Kissat 4.0.x **distinta de la 4.0.4**: con la misma semilla,
  los recuentos de conflictos coinciden en algunas instancias y difieren en
  otras. Una comparación de tiempos entre la tesis y esta máquina exige
  calibración (EXP-013); una comparación entre dos configuraciones de LabeSAT
  se hace siempre en esta máquina, intercalada (ADR-0003 §4b).
- Los tiempos de la tesis son de reloj e incluyen la descompresión: en las
  instancias muy fáciles, el coste fijo domina.

## `downloaded/` — suites oficiales (NO versionadas, ver `.gitignore`)

Para un baseline serio necesitas los benchmarks reales de la SAT Competition.
Son grandes (varios GB) y **no** deben commitearse.

### De dónde bajarlos

- **Benchmarks históricos por año**: https://satcompetition.github.io/2024/
  (y las páginas de cada año) enlazan los conjuntos de la Main Track.
- **Anthology / archivo global**: la comunidad mantiene la *Global Benchmark
  Database (GBD)* — https://benchmark-database.de/ — con metadatos y descargas.
- **Instancias de años previos** también aparecen enlazadas desde el repo
  https://github.com/satcompetition (cada edición).

### Flujo sugerido

```bash
mkdir -p downloaded/satcomp2024
# ... descargar y descomprimir aquí (las instancias suelen venir .cnf.xz) ...

../scripts/run_baseline.sh -s ../cadical/build/cadical \
    -b downloaded/satcomp2024 -o ../results/baseline_2024.csv \
    -t 5000 -n cadical-3.0.1-vanilla
```

> La SAT Competition usa timeout de **5000 s** por instancia en la Main Track.
> Para pruebas locales rápidas usa algo mucho menor (`-t 60`) y un subconjunto.

### Recordatorio de reglas (Main Track)

Para **participar** tú debes aportar además **20 benchmarks nuevos** (no vistos
en competiciones previas), al menos 10 de dificultad media. Documenta su origen
y su generador. Tu tesis de licenciatura es una buena fuente de instancias
propias: guárdalas aquí en su propia subcarpeta (`mine/`) cuando las tengas.
