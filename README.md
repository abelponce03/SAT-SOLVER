# SAT-SOLVER — fork de Kissat para la SAT Competition 2027

Repositorio de trabajo para preparar una entrada a la **Main Track** de la
[SAT Competition 2027](https://satcompetition.github.io/). La base es un
**fork de [Kissat](https://github.com/arminbiere/kissat) 4.0.4** (MIT, Armin
Biere), el solver secuencial sobre el que se construyen las entradas ganadoras
recientes; encima van nuestras mejoras, cada una validada con un A/B propio.

> **Por qué Kissat y no CaDiCaL** (el proyecto arrancó como fork de CaDiCaL):
> ver [ADR-0001](docs/adr/0001-migracion-cadical-a-kissat.md). Resumen: sobre
> 955 instancias de aplicación reales, Kissat resuelve el 56.6 % y CaDiCaL el
> 49.2 %, y el hueco es estructural (familia `miter`), no de política de
> búsqueda. Además la Main Sequential 2025 y 2026 las ganan variantes de Kissat.

## Estructura

```
solver/kissat/      fork de Kissat (git subtree; UPSTREAM.md fija el punto base)
scripts/            harness: build, runner, PAR-2 + estadística, verificación
bench/              instancias (smoke versionado; dev/test se reconstruyen por hash)
results/            CSV de corridas (solo se versionan los *.reference.csv)
docs/adr/           decisiones de arquitectura e investigación
docs/research/      estudio de literatura y caracterización
docs/experiments/   un documento por experimento A/B (hipótesis antes, resultado después)
docs/paper/         material para artículos
docs/archive/       etapa CaDiCaL (jul–sep 2026), conservada como histórico
```

## Arranque rápido

```bash
./scripts/build.sh                 # compila el fork -> solver/kissat/build/kissat
./scripts/get_tools.sh             # drat-trim, para verificar respuestas UNSAT
./scripts/smoke_test.sh            # build + tests + modelos + pruebas DRAT + determinismo

# una corrida completa sobre el banco de humo
python3 scripts/run_experiment.py --solver solver/kissat/build/kissat \
    --bench bench/smoke --out results/smoke.csv --timeout 60 --seeds 1,2,3 \
    --label kissat-4.0.4-vanilla
python3 scripts/par2.py results/smoke.csv --by-family

# comparación A/B con contraste estadístico
python3 scripts/par2.py results/A.csv results/B.csv --md
```

## Cómo se mide aquí

La métrica de ranking de la competición es **PAR-2** (tiempo si resuelve,
2×timeout si no; menor es mejor). Este repositorio añade dos exigencias sobre
la práctica habitual, porque con 4 núcleos no se puede imitar la competición a
lo bruto:

1. **Cribado determinista**: presupuesto por conflictos (`--conflicts`) en vez
   de por tiempo. Con seed fija el resultado no depende del ruido de la máquina,
   así que una idea mala se descarta en minutos y sin medir relojes.
2. **Contraste estadístico obligatorio**: Wilcoxon emparejado, IC95% por
   bootstrap del ΔPAR-2 y McNemar sobre el cambio de resueltas, con ≥3 seeds por
   instancia. `par2.py` avisa cuando el tamaño de muestra no permite concluir.

El protocolo completo, incluida la separación dev/test para no auto-engañarse,
está en [ADR-0003](docs/adr/0003-protocolo-experimental-y-metricas.md).

## Estado

- [x] Migración de CaDiCaL a Kissat 4.0.4 ([ADR-0001](docs/adr/0001-migracion-cadical-a-kissat.md))
- [x] Estructura, vendorizado y convenciones ([ADR-0002](docs/adr/0002-estructura-repo-y-vendorizado.md))
- [x] Protocolo experimental y métricas ([ADR-0003](docs/adr/0003-protocolo-experimental-y-metricas.md))
- [x] Harness: runner, PAR-2 + estadística, verificación de modelos y pruebas DRAT
- [x] CI: release, sanitizers, clang, scripts
- [x] **Análisis empírico de la SAT Competition 2026** — [`docs/research/01`](docs/research/01-analisis-empirico-sc2026.md)
- [x] **Catálogo de ideas priorizado por techo medido** — [`docs/research/02`](docs/research/02-catalogo-de-ideas.md)
- [x] Bancos `dev`/`test` estratificados y disjuntos del banco oficial 2026
- [ ] **EXP-001**: diversidad intrínseca de Kissat (en ejecución)
- [ ] EXP-002: A/B de la cartera secuencial
- [ ] EXP-003: reparto adaptativo del presupuesto

### El hallazgo que orienta el proyecto

Sobre las 400 instancias del Main Track 2026 (datos oficiales):

| | resueltas | PAR-2 |
|---|---:|---:|
| Kissat de fábrica (nuestra base) | 238 | 4611.5 s |
| Ganador de 2026 (`satsuma-iter-kissat`) | 276 | 3647.0 s |
| **VBS de 21 variantes de Kissat** (oráculo) | **321** | **2354.8 s** |
| Cartera secuencial k=3, sin oráculo | 274 | 3813.1 s |

Las **12 variantes que quedaron individualmente peores** que el Kissat de fábrica
resuelven **juntas 277 instancias — más que el campeón del año**. La
complementariedad entre configuraciones es un recurso mayor que la mejor técnica
nueva publicada, y nadie lo está cobrando. Detalle en
[`docs/research/01`](docs/research/01-analisis-empirico-sc2026.md).

## Licencia

El código bajo `solver/kissat/` es de Armin Biere y se distribuye bajo licencia
MIT (ver `solver/kissat/LICENSE`); nuestras modificaciones se publican bajo la
misma licencia. El harness y la documentación son originales de este proyecto.
