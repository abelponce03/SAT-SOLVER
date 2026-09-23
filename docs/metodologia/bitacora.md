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
- **EXP-007 cerrado**:
  - H1 se confirma con mucha fuerza (H: 8 → 37 de 45); H2 no se cumple (1.42×
    en N); seguridad sin fallos;
  - veredicto preregistrado: **solo condicional**, así que la ruptura pasa a
    ser opcional en `labesat`;
  - el script de análisis se commiteó antes de que terminara la tanda;
  - lectura exploratoria, etiquetada como tal: el coste en N viene de la
    búsqueda de kissat sobre la fórmula modificada.
- **Cliques medidos**: mantener MIT cuesta 6 instancias. D-005 pasa a tener
  datos.
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

## 2026-09-23 (continuación) — EXP-008 y clique máxima MIT

- **Se pidió**: «procede con la opción c y empieza EXP-008». D-005 se resuelve
  con la opción c: reimplementar en MIT la clique máxima que satsuma toma de
  cliquer.
- **Se hizo**:
  - EXP-008 lanzado según su preregistro, con el binario recompilado desde
    cero para que `--id` coincida con HEAD;
  - **mclique** (`solver/mclique/`): clique máxima por ramificación y poda,
    escrita en sala limpia con la interfaz que usa satsuma;
  - `tools/satsuma-mclique` en `get_tools.sh`, pruebas en CI, y EXP-010
    preregistrado **antes** de ejecutar satsuma-mclique sobre el banco;
  - arnés A/B con entorno por rama e `--instances`.
- **Decisiones**:
  - **Sala limpia**: de cliquer no se leyó ningún fichero, ni siquiera sus
    cabeceras. La interfaz sale de las llamadas de `src/reorder.h` (satsuma,
    MIT). Cuando hay varias cliques máximas, mclique puede elegir otra que
    cliquer; por eso la adopción la decide un experimento y no solo las
    pruebas de corrección.
  - mclique va en un binario aparte y **no cambia nada por defecto** hasta
    EXP-010 (CLAUDE.md §5).
  - Para no tocar el CMake de satsuma, las cabeceras y unidades de
    compatibilidad ocupan los nombres de fichero que espera
    (`src/cliquer/{cliquer,graph,reorder}.c`), y `get_tools.sh` comprueba que
    lo que compila ahí es byte a byte nuestro.
  - La parte 1 de EXP-010 (solo satsuma, métrica SHA-1 determinista) se
    ejecuta junto a EXP-008; la parte 2 (tiempos de kissat) espera a que
    EXP-008 acabe.
- **Salió mal**:
  - `./scripts/build.sh` sin `--clean` dejó un binario con el `--id` del commit
    anterior. Se recompiló desde cero antes de lanzar. Moraleja: la
    procedencia se comprueba justo antes de lanzar, no se supone.
- **EXP-010, parte 1**: mclique coincide con cliquer en 72 de 74, pero tiene
  un tope nuevo en una instancia. El criterio preregistrado lo descarta tal
  cual, y así se anota.
  - El diagnóstico se hizo con una build de traza aparte, sin tocar el binario
    del experimento. Encontrar la clique (90) es inmediato; demostrar que es
    máxima no termina ni con mclique ni con un prototipo de Östergård.
  - La corrección (un presupuesto de trabajo) se preregistró como EXP-011
    **antes** de mirar la traza de todas las instancias. El valor se fijó por
    tiempo, no por resultados, y esa amenaza quedó escrita.
- **Corte de EXP-008** (hacia las 17:46 UTC): al quedar la sesión inactiva,
  el contenedor se suspendió y se reinició. Murieron todos los procesos en
  segundo plano, incluidos los lanzados con `nohup`. Quedaron 60 de 120
  parejas.
  - Se añadió `--resume` al arnés y se relanzó.
  - La secuencia pendiente (EXP-008, EXP-011 parte 1 y las partes 2) pasó a
    un único guion idempotente, ejecutado como tarea del propio entorno.
  - Otro fallo propio: los guiones que esperaban con `pgrep -f patrón` se
    encontraban a sí mismos (el patrón aparecía en su propia línea de
    órdenes), así que la cadena no habría arrancado nunca.
- **Aprendido (entorno)**: un experimento de horas necesita la sesión activa,
  y cada paso debe poder reanudarse. Para esperar a un proceso: su PID o una
  secuencia en un solo guion, nunca `pgrep -f` con un patrón que aparezca en
  la línea de órdenes del propio vigilante.
- **Aprendido**: una reimplementación compatible se valida en dos capas:
  corrección del algoritmo (contra fuerza bruta) y equivalencia del efecto en
  el sistema completo (CNF de salida y resultados de kissat). Y una garantía
  que el original da «gratis» (terminar pronto) también hay que medirla.

## 2026-09-23 (tarde) — Un solo binario: simetrías montadas sobre Kissat (D-016)

- **Se pidió**: primero un resumen de lo hecho y lo pendiente. Al leerlo, el
  director aclaró su objetivo: «tomar los algoritmos y montarlos sobre kissat,
  no tener un selector de solucionadores». Eligió la opción c (por fases) y
  dijo «procede».
- **Se hizo**: fase 1 de ADR-0007.
  - satsuma, dejavu y tsl vendorizados sin modificar, con comprobación en CI.
  - Una unión C++ de 20 líneas.
  - `src/symmetry.c` en Kissat: proceso hijo, topes y respaldo.
  - La opción `--symmetry` en la aplicación.
  - `configure --symmetry` y `build.sh --dir`.
  - `test_symmetry_integrada.sh`: CNF intermedia idéntica a la del satsuma
    externo, pruebas aceptadas por los dos dsr-trim y respaldo. Pasa con gcc,
    con clang y en la configuración de competición.
- **Decisiones**:
  - Satsuma corre en un **proceso hijo** del propio binario, no en una llamada
    directa. Así la salida es idéntica a la de la tubería (EXP-007 sigue
    valiendo), y un `exit()` o un tope de satsuma no tumban al solver.
  - Todo va detrás de `configure --symmetry` más la opción `--symmetry`: el
    build por defecto no cambia.
  - Sin `-march=native` en satsuma, pensando en la máquina de la competición.
- **Salió mal**:
  - `kissat_looks_like_a_compressed_file` solo existe en builds sin
    compresión. Se detecta la compresión con el campo `compressed` de la
    apertura.
  - Un patrón con `^` no encontraba el «s VERIFIED» de drat-trim, que lo
    escribe tras caracteres de control de su barra de progreso.
  - Tres compilaciones con `make -j4` durante EXP-008. Tenían `nice` y se
    hicieron en directorios aparte, pero son carga concurrente y se anotan
    en su §8.
- **Aprendido**:
  - Antes de cambiar de arquitectura hay que explicar lo que hay y
    confirmarlo con el director. La confusión venía de que «programa externo»
    (lo que se pidió) y «un solo solver» (lo que se quería) no son lo mismo.
  - Compilar aparte (`--dir`) permite seguir desarrollando sin invalidar un
    experimento en curso.
