# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Este proyecto no versiona releases todavía; se versionan **hitos** del solver.

## [No publicado]

### Añadido
- **Análisis empírico** de los resultados oficiales SC2026 (`docs/research/01`) y
  **catálogo de ideas** priorizado por techo medido (`docs/research/02`).
- `analyze_competition.py` (ranking / familias / VBS / cartera / techo),
  `build_dev_set.py` (bancos dev y test estratificados y disjuntos),
  `analyze_diversity.py` y `run_diversity.sh` (EXP-001).
- Listas de instancias `bench/dev.list.csv` y `bench/test.list.csv`.
- Base del solver: fork de **Kissat 4.0.4** (`rel-4.0.4`, commit upstream
  `8af8e56`) vendorizado en `solver/kissat/` con `git subtree` (ADR-0002).
- Harness de experimentación: `run_experiment.py` (presupuesto por tiempo o por
  conflictos, seeds, métricas internas, metadatos de reproducibilidad),
  `par2.py` (PAR-2 + Wilcoxon + bootstrap + McNemar + métricas de robustez),
  `verify_model.py`, `check_proof.sh` (drat-trim), `smoke_test.sh`.
- Registros de decisión ADR-0001 (migración a Kissat), ADR-0002 (estructura y
  vendorizado), ADR-0003 (protocolo experimental).
- CI en GitHub Actions: release + sanitizers + clang + scripts.

### Corregido
- `scripts/build.sh` pasaba a `./configure` opciones que Kissat no tiene
  (`--symbols`, `--asan`, `--debug`), por lo que el trabajo de sanitizers de la
  CI fallaba desde el primer día. Ahora usa las reales (`-g`,
  `-s -fsanitize=address,undefined`, `--statistics`, `--competition`).

### Cambiado
- **Estructura del repositorio** aplanada: desaparece `competition/`.

### Eliminado
- **Fork de CaDiCaL 3.0.1** y su instrumentación `CADICAL_TRACE` (ADR-0001).
  La investigación de esa etapa se conserva en `docs/archive/cadical-era/`.
