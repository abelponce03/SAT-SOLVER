# Baseline de referencia — CaDiCaL 3.0.1 (vanilla)

Línea base contra la que se mide **cualquier** modificación del fork. Regenerable;
los tiempos absolutos dependen del hardware, pero la **metodología A/B** y las
diferencias relativas son lo que importa.

## Entorno de la corrida de referencia

| | |
|---|---|
| Solver | CaDiCaL 3.0.1 (sin modificar) |
| CPU | Intel Xeon @ 2.80 GHz |
| Timeout | 120 s por instancia |
| Métrica | PAR-2 (tiempo real si resuelve; `2×timeout` si no) |
| Benchmark | `benchmarks/dev` (34 instancias; ver `scripts/setup_benchmarks.sh`) |

> ⚠️ Este entorno de referencia (nube) NO es tu hardware en Cuba. Regenera tu
> propio baseline localmente (`run_baseline.sh`) y compara **siempre** tu versión
> modificada contra TU baseline en TU máquina, no contra estos números.

## Resultado

**30/34 resueltas** (SAT=15, UNSAT=15), **4 timeouts**, **PAR-2 = 31.737 s**.

| familia | instancias | comportamiento | rol en el set |
|---|---|---|---|
| aim200 (SAT/UNSAT) | 8 | ~0.006 s | trivial (sanity) |
| par16 (SAT) | 3 | 0.02–0.09 s | fácil |
| uf250 (SAT) | 8 | 0.06–3.6 s | medio, variable |
| uuf250 (UNSAT) | 8 | 4–8 s | medio, estable |
| php_9/10 (UNSAT) | 2 | 0.44 s / 4.6 s | medio crafted |
| **php_11 (UNSAT)** | 1 | **62.8 s** | **borde** (detector de mejora/regresión) |
| par32 (SAT) | 2 | timeout | cola dura |
| php_12/13 (UNSAT) | 2 | timeout | cola dura |

Los 4 timeouts (par32×2, php_12, php_13) anclan la métrica: una mejora que
resuelva **una** de ellas dentro del tiempo se refleja de inmediato en el PAR-2.
`php_11_10` (62.8 s, justo bajo el timeout) es el canario más sensible.

## Reproducir

```bash
cd competition
./scripts/build.sh
./scripts/setup_benchmarks.sh          # descarga + arma benchmarks/dev
./scripts/run_baseline.sh -s cadical/build/cadical -b benchmarks/dev \
    -o results/baseline_dev.csv -t 120 -n cadical-3.0.1-vanilla
python3 scripts/par2.py results/baseline_dev.csv
```

El CSV de esta corrida de referencia está versionado en
`results/baseline_dev.reference.csv` para comparación histórica.
