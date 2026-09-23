# Bitácora del desarrollo

Una entrada por sesión, en orden cronológico. Cada entrada tiene cinco partes:

- **Se pidió**: lo que planteó el director.
- **Se hizo**: el resultado.
- **Decisiones**: las que surgieron por el camino.
- **Salió mal**: los errores y cómo se detectaron.
- **Aprendido**: qué cambia en adelante.

Las entradas previas al 2026-09-23 se reconstruyeron ese día a partir del
historial de git y de los documentos del repositorio. Desde entonces se escriben
al cerrar cada sesión.

---

## Antecedentes (2025-09 → 2026-09-03)

- **Septiembre de 2025**: el director escribe un primer solver propio en
  Python (4 commits, `abelponce03`).
- **2026-09-03, etapa CaDiCaL**:
  - primera sesión con el asistente: fork de CaDiCaL, banco de pruebas y
    caracterización de la dinámica de reinicios;
  - se fusiona como PR #1;
  - hoy está archivada en `docs/archive/`.

## 2026-09-21 — Migración a Kissat y método

- **Se pidió**:
  - eliminar CaDiCaL y hacer un fork de Kissat para la SAT Competition 2027
    (PAR-2);
  - buenas prácticas y documentación de cada paso;
  - demostrar empíricamente toda mejora.
- **Se hizo**:
  - ADR-0001 a ADR-0003, con el protocolo experimental;
  - Kissat 4.0.4 vendorizado con `git subtree`;
  - banco de pruebas: `run_experiment.py`, `par2.py` con Wilcoxon, bootstrap y
    McNemar;
  - análisis de los datos oficiales de 2026 y catálogo de ideas;
  - EXP-001 (diversidad) y EXP-002 (fases *lucky*).
- **Decisiones**:
  - bancos dev y test disjuntos, con test reservado;
  - cribado determinista por conflictos.
- **Salió mal**: opciones inválidas en `build.sh`. Kissat solo acepta enteros
  en `--time`.
- **Aprendido**: el techo medido (VBS 26.7 %) justifica la línea A.

## 2026-09-22 — B3, A4 y PR #2

- **Se pidió**:
  - arreglar CI;
  - B3 y su validación;
  - A4 (trazas, validación y planificador adaptativo);
  - el A/B en dev y abrir el PR.
- **Se hizo**:
  - EXP-003: B3′ **no replica** en test, así que se retira;
  - B3″ (terminador);
  - validación de la señal de recompensa de A4;
  - A4.1 implementado;
  - EXP-005: sin significación;
  - PR #2, fusionado.
- **Decisiones**: el nombre LabeSAT (D-007).
- **Salió mal**:
  - el asistente recompiló el binario **a mitad** de EXP-004. Los datos se
    descartaron y se añadió la guarda de SHA-1;
  - el entorno obligó a cambiar la identidad git a `Claude` (hook de firma).
- **Aprendido**:
  - todo binario en uso se vigila;
  - la deriva entre sesiones (~4 %) hace inválidas las comparaciones entre
    sesiones distintas (ADR-0003 §4b).

## 2026-09-23 — Cierre de A4.1, fase 2 (simetrías), investigación y gobernanza

- **Se pidió**:
  - EXP-006 (A4.1);
  - la hoja de ruta completa;
  - «no hay clúster: empieza la fase 2»;
  - «satsuma como programa externo y mantén MIT»;
  - investigar a fondo las decisiones pendientes y abrir el PR;
  - las **directrices de proceso**: buenas prácticas, documentación continua y
    multiformato, autoría solo humana en git, y decisiones registradas y
    agendadas.
- **Se hizo**:
  - EXP-006: A4.1 **no acelera** (0.983×, p = 0.69). Se cierra;
  - tubería satsuma → kissat con `--append-proof` propio, pruebas SR
    verificadas con dsr-trim y CI con control negativo;
  - EXP-007 preregistrado y lanzado;
  - research/03 (coste de MIT: 8 de 74 instancias difieren) y research/04
    (cuatro decisiones con fuentes primarias);
  - PR #3;
  - gobernanza: CLAUDE.md, ADR-0005, ADR-0006, registro de decisiones y esta
    bitácora.
- **Decisiones**:
  - D-001 a D-005, D-011 y D-012 abiertas, agendadas en la Reunión 1
    (issue #4, con un sub-issue por decisión);
  - D-006, D-008, D-009 y D-010 resueltas;
  - el trabajo se organizó en épicas: fase 2 (#12) y documentación (#16).
- **Salió mal**:
  - Primer lanzamiento de EXP-007: el guion tomaba el directorio
    `solver/kissat` por el binario, porque `-x` es cierto para directorios.
    - Once parejas salieron ERROR en las dos ramas.
    - Se abortó sin datos que sesgaran nada.
    - Ahora hay un test y el arnés aborta si el solver no responde a `--id`.
  - Un test de CI fallaba al azar: con `pipefail`, `grep -q` cierra la tubería
    y el verificador muere por SIGPIPE.
  - Riesgo descubierto: se verificaba con un dsr-trim 12 commits por delante
    del que usó la competición. Ahora se verifica con los dos.
  - Un reinicio del contenedor mató a los vigilantes en segundo plano; el
    experimento siguió vivo. Desde entonces se programa una revisión de
    respaldo con `send_later`.
  - El primer CI de documentación falló: `listings` no admite UTF-8
    multibyte. Se corrigió compilando en local antes de volver a hacer push.
  - La **revisión visual** de los PDF encontró un error que el compilador no
    marca: `--time` salía como «-time», por la ligadura de guiones en la fuente
    monoespaciada. Moraleja: los entregables se revisan mirándolos, no solo
    compilándolos.
  - Las acciones de GitHub desde la sesión llevan la insignia «via Claude»
    (D-012).
- **Resuelto en la sesión**: D-001, opción b.
  - Se reescribió la rama del PR #3 con `git filter-branch`: árbol idéntico y
    fechas conservadas.
  - Se guardó una tabla de correspondencia de SHA para no perder la procedencia
    de EXP-006 y EXP-007.
  - Force-push solo a la rama.
- **Aprendido**:
  - los tests deben ejercitar la ruta por defecto, sin variables de entorno de
    ayuda;
  - hay que verificar con la herramienta **exacta** de la competición;
  - las convenciones del entorno (identidad git) se documentan y se ajustan a
    las del proyecto de forma explícita.
