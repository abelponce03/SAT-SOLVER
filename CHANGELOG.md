# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Este proyecto no versiona releases todavía; se versionan **hitos** del solver.

## [No publicado]

### Añadido (2026-09-22 → 2026-09-23)
- **Ruptura de simetrías verificable** (ADR-0004):
  - `solver/labesat` ejecuta satsuma (MIT, `CLIQUES=OFF`) y después kissat;
    si satsuma falla, cae a kissat solo;
  - nueva opción de aplicación `--append-proof` en kissat, que continúa la
    prueba SR de satsuma;
  - las pruebas se verifican con dsr-trim, tanto con la versión actual como con
    la exacta de la SAT Competition 2026 (`scripts/test_symmetry.sh`, en CI y
    con control negativo).
- `scripts/get_tools.sh` descarga satsuma, dejavu, dsr-trim (dos versiones) y
  drat-trim, cada uno fijado a un commit.
- Arnés de experimentos:
  - A/B intercalado (`run_ab_interleaved.py`) con guardas de SHA-1 (`--guard`)
    y procedencia en `meta.json`;
  - `analyze_speedup.py`, `select_symm_bench.py`, `verify_symm_answers.py`
    y `compare_satsuma_builds.py`.
- **B3″**: las fases *lucky* devuelven el control al terminador, de modo que se
  respetan los límites de tiempo y de conflictos.
- **A4.1**: planificador adaptativo stable/focused, **desactivado**
  (`modeadaptive=0`) tras EXP-006.
- Gobernanza y documentación:
  - `CLAUDE.md`, ADR-0005 (autoría y decisiones) y ADR-0006 (documentación
    multiformato);
  - registro de decisiones y metodología con bitácora;
  - `LICENSE` (MIT), `THIRD_PARTY_NOTICES.md` y `CITATION.cff`;
  - manual de usuario (LaTeX), descripción para la competición (IEEEtran) y
    página `labesat(1)`;
  - `scripts/check_authorship.sh`.

### Experimentos cerrados (2026-09-22 → 2026-09-23)
- **EXP-004**: el terminador de B3″ es neutro (39/39 trayectorias idénticas).
  Se midió una deriva de ~4 % entre sesiones.
- **EXP-005**: A4.1 en dev da ΔPAR-2 −2.2 s, con el IC incluyendo el 0.
- **EXP-006** (preregistrado): A4.1 **no acelera**. Factor 0.983×,
  p = 0.69; las propagaciones no cambian (0.999×). Se cierra.
- **research/03**: satsuma sin cliques produce una salida distinta en 8 de 74
  instancias; con cliques es idéntico al ganador de 2026.

### Plan (2026-09-23)
- **Plan Main Track 2027 con declaración honesta de IA**
  (`docs/plan/plan-main-track-2027.md`):
  - objetivos O1–O3 frente al ranking de 2026;
  - palancas P1–P5 y variantes V1–V4;
  - hitos H1–H11, presupuesto de cómputo y riesgos.
- `scripts/declaracion_ia.sh`: las cifras de la declaración obligatoria salen
  de git y CI las regenera. Corrige la estimación anterior («~460 líneas»):
  son **+390 líneas de C** (1,0 %), **+105 activas**.

### En curso
- **EXP-007** (preregistrado): A/B de la ruptura de simetrías sobre 74
  instancias estratificadas de 2026.

### Nombre
- El solver pasa a llamarse **LabeSAT**. El banner imprime el nombre, una línea
  de copyright para las modificaciones y **conserva las dos líneas de copyright
  de Armin Biere**, como exige la licencia MIT de Kissat.
- `--id` imprime ahora el commit exacto del que sale el binario (antes
  `unknown`: el script de Kissat buscaba `.git` solo en el directorio actual y
  el padre, y vendorizado con `git subtree` está tres niveles más arriba).

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

### Experimentos cerrados
- **EXP-003**: la regla B3′ (condicionar las fases *lucky* al tamaño de la
  fórmula) **no replicó** sobre el banco reservado: ΔPAR-2 = +2.254 s, IC95 %
  [−3.79, +11.17], Wilcoxon p = 0.98. Se retiró del catálogo y **se eliminó del
  solver**; el diff contra upstream vuelve a ser solo documentación.

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
