# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Este proyecto no versiona releases todavía; se versionan **hitos** del solver.

## [No publicado]

### Añadido (2026-09-23): ruptura de simetrías dentro de Kissat (D-016, ADR-0007)
- **Un solo binario**: con `configure --symmetry` (o `build.sh --symmetry`),
  satsuma se compila dentro de Kissat, y `kissat --symmetry <cnf> [<prueba>]`
  hace lo mismo que la tubería `solver/labesat`:
  - satsuma se ejecuta en un proceso hijo del propio Kissat;
  - la prueba SR continúa en el mismo fichero;
  - si satsuma falla, se pasa del tope o la entrada es demasiado grande, se
    resuelve la CNF original con prueba DRAT pura.

  **Apagado por defecto**; sin `configure --symmetry` el build no cambia.
- satsuma, dejavu y tsl van **vendorizados sin modificar** en `solver/satsuma/`
  (`scripts/vendor_satsuma.sh`, con `--check` en CI).
- `scripts/test_symmetry_integrada.sh`, en CI junto al build de competición
  con `--symmetry`:
  - CNF intermedia idéntica byte a byte a la de satsuma externo;
  - pruebas aceptadas por los dos dsr-trim;
  - modelos correctos contra la CNF original;
  - entrada `.xz`;
  - respaldo con prueba DRAT pura.
- `build.sh --dir=NOMBRE`: compila en otro directorio sin tocar
  `build/kissat`, útil mientras un experimento lo vigila.

### En curso (2026-09-23): base de Kissat y clique máxima MIT
- **EXP-008** preregistrado y en ejecución: Kissat 4.0.4 (LabeSAT) frente a
  Kissat «sc2026» en calib + calib2 (decide D-013). `get_tools.sh` compila
  `tools/kissat-sc2026` desde el paquete oficial, comprobando el sha256.
- **mclique** (`solver/mclique/`, MIT): clique máxima por ramificación y poda
  con cota por coloreado voraz, escrita en sala limpia (D-005, opción c).
  Implementa la interfaz de cliquer que usa satsuma, y `get_tools.sh` compila
  con ella `tools/satsuma-mclique` (`CLIQUES=ON`, sin cliquer). **No se usa por
  defecto** hasta que lo valide EXP-010 (preregistrado); se prueba con
  `LABESAT_SATSUMA=tools/satsuma-mclique`.
- **EXP-010, parte 1**: mclique da la misma CNF que cliquer en 72 de 74
  instancias y refuta dentro de satsuma las 6 de R6, pero llega al tope de
  60 s en `9ba8145e` (grafo de 896 vértices y densidad 0,76, donde demostrar la
  optimalidad es exponencial). Con el criterio preregistrado, v1 no se adopta.
- **mclique v2**: presupuesto de trabajo determinista (5·10⁸ unidades, ~0,7 s
  en ese grafo); si se agota, devuelve la mejor clique encontrada, ampliada
  hasta ser maximal. Es seguro porque satsuma solo usa la clique para ordenar
  columnas. Validación preregistrada en **EXP-011**.
- `run_ab_interleaved.py --resume`: reanuda una tanda cortada conservando las
  parejas completas, con comprobación de SHA-1 de los binarios. Nace del corte
  de EXP-008 por un reinicio del contenedor.
- `verify_symm_answers.py` verifica cada prueba UNSAT con **los dos** dsr-trim
  (el actual y el de SC2026), como ya hacía `test_symmetry.sh`.
- `scripts/test_mclique.sh`: pruebas frente a fuerza bruta y a una búsqueda
  exhaustiva de referencia (3300 grafos aleatorios), casos conocidos y la
  compilación de la interfaz tal como la usa satsuma. En CI, junto con la
  tubería de simetrías usando satsuma-mclique.
- `run_ab_interleaved.py`: `--solver-b` (A/B entre dos binarios),
  `--env-a/--env-b` (entorno por rama) e `--instances` (subconjunto
  preregistrado de un banco).

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

### Experimento cerrado: EXP-007 (2026-09-23)
- **Ruptura de simetrías con satsuma MIT, sobre 74 instancias de 2026**:
  - resueltas: 35 → **64**; PAR-2 209.3 → **69.0 s**;
  - estrato H: 8 → 37 de 45 (p = 8·10⁻¹⁰);
  - pero en N ralentiza **1.42×**, y el criterio exigía ≤ 1.10.
  - Seguridad: 19/19 modelos y 42/42 pruebas verificadas, 0 fallos.
  - Veredicto: **solo condicional**.
- **Cambiado**: `solver/labesat` **ya no aplica la ruptura de simetrías por
  defecto**. Se activa con `--symmetry` o `LABESAT_SYMMETRY=1` hasta que B3
  (EXP-009) esté validado. Manual, página man y tests actualizados.
- research/03, segunda parte: sin cliques, satsuma deja sin resolver 6
  instancias de H que con cliques caen en < 2 s.

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
