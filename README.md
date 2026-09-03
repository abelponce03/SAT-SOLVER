# SAT-SOLVER — CaDiCaL fork para la SAT Competition 2027

Repositorio de trabajo para preparar una entrada a la **Main Track** de la
[SAT Competition](https://satcompetition.github.io/). La estrategia: partir de
un **fork de CaDiCaL** (solver CDCL de referencia, MIT) y aportar una mejora
algorítmica medible, con vista a la edición **2027**.

Todo el trabajo vive en [`competition/`](competition/):

```
competition/
├── cadical/        Fork de CaDiCaL (base sobre la que hacemos los cambios)
├── benchmarks/     Instancias de prueba (muestra + suites oficiales descargadas)
├── scripts/        build.sh, gen_benchmarks.py, run_baseline.sh, par2.py
├── results/        CSV de las corridas de baseline / A-B
└── README.md       Metodología, requisitos de la Main Track y plan de trabajo
```

Empieza por [`competition/README.md`](competition/README.md).

## Arranque rápido

```bash
cd competition
./scripts/build.sh                          # compila el fork
./scripts/run_baseline.sh -s cadical/build/cadical -b benchmarks/sample \
    -o results/baseline.csv -t 60 -n vanilla
python3 scripts/par2.py results/baseline.csv
```

## Estado

- [x] Fork de CaDiCaL vendorizado y compilando
- [x] Harness de baseline (runner con timeout + métrica PAR-2 + comparación A/B)
- [x] Baseline sobre subconjunto de benchmarks oficiales (SATLIB) — ver `competition/docs/baseline.md` (PAR-2 = 31.74 s, 30/34)
- [x] Investigación de la contribución — ver `competition/docs/research/01-panorama-modificaciones-cadical.md`
- [x] **Fase 0**: caracterizar dinámica restart/LBD — ver `competition/docs/research/02-fase0-caracterizacion.md` (hallazgo: reinicios degeneran a ~99.7% reuse en pigeonhole)
- [x] **Fase 0 (datos reales de tesis)** — ver `competition/docs/research/03-fase0-datos-tesis.md` (gap vs Kissat es estructural/miter; el reset-bandit debe apuntar a la inestabilidad por seed: 62 instancias flaky, varianza temporal hasta 102×)
- [x] **Conseguir las instancias `.cnf.xz`** — descargadas de GBD por hash (62 flaky + 27 control) vía `scripts/fetch_gbd.py`
- [x] **Fase 0.5**: instrumentación de trazas (`CADICAL_TRACE`) + caracterización real — ver `competition/docs/research/04-fase05-instrumentacion-trazas.md` (hallazgo: el thrashing es family-dependent y NO predice el fallo → la señal del bandit debe ser progreso genérico, no reuso)
- [ ] **Fase 1**: implementar y validar A/B el reset-bandit (métrica: flaky→resuelta + ↓varianza por seed), en hardware capaz
