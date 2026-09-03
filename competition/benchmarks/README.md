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
