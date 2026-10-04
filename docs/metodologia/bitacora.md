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

## 2026-09-23 (noche) — Revisión de enfoques probabilísticos (research/05)

- **Se pidió**:
  - una búsqueda exhaustiva, con conectores académicos, de enfoques
    probabilísticos que mejoren los solvers SAT y sus métricas;
  - documentar sin obligación de aplicar;
  - descartar lo que por sí solo sería ruido.
- **Se hizo**:
  - ~22 consultas en Consensus, Scholar Gateway y web, con ~75 trabajos
    catalogados;
  - un inventario previo de lo que Kissat 4.0.4 ya hace (walk probSAT, fases
    objetivo, rephasing, randec, Luby), para no «descubrirlo» de nuevo;
  - veredictos con un criterio de ruido explícito: el umbral de lo que
    podemos medir y el precedente nulo de EXP-006;
  - una exploración con los datos de EXP-007, etiquetada como tal.
- **Decisiones**:
  - Se recomiendan tres cosas (R1–R3). Las tres encajan en trabajo ya
    planificado (EXP-009, ADR-0003, P5) y no añaden frentes nuevos.
  - NeuroBack queda aparcado a pesar de tener el mayor efecto publicado sobre
    Kissat, por el coste de integrarlo en el binario de competición.
- **Salió mal**:
  - Scholar Gateway cubre sobre todo el corpus de Wiley y casi no indexa las
    sedes de SAT; se compensó con Consensus y la web.
  - Consensus limitó la frecuencia de consultas: hubo que ir en tandas.
- **Aprendido**:
  - Revisar la literatura **contra el código de la base** evita recomendar lo
    que ya existe.
  - Con los datos propios se pueden descartar ideas antes de implementarlas:
    el reparto temporal se descartó con una simulación de 20 líneas.

## 2026-09-23 (noche, 2) — Razonamiento XOR de CryptoMiniSat (research/06)

- **Se pidió**: investigar si el mecanismo de CryptoMiniSat (recuperar XOR y
  aplicar Gauss-Jordan) serviría a LabeSAT; si resulta contraproducente, se
  descarta.
- **Se hizo**:
  - literatura: CMS, BIRD, pruebas con TBUDDY y FRAT, DRAT para XOR, cotas
    inferiores de Tseitin;
  - revisión de lo que Kissat ya hace (XOR en el cierre por congruencia, sin
    Gauss);
  - **medición propia**: un detector de XOR en C sobre 161 instancias, y
    Gauss en GF(2) sobre las puras;
  - cruce con los resultados oficiales de 2026 para estimar el beneficio;
  - lectura de los paquetes de los solvers de 2026 que resolvieron las XOR,
    solo para saber qué técnica usan.
- **Decisiones**: se descarta el Gauss completo; se aparca X1 (refutación en
  la raíz con prueba), condicionado a que dsr-trim acepte esas pruebas; X2 se
  descarta.
- **Salió mal**:
  - La hipótesis inicial («quien resolvió xor-shifting usa Gauss») era falsa:
    fue ruptura de simetrías más decisiones sobre el soporte independiente.
    Lo corrigió mirar el paquete antes de escribir.
  - El escaneo es lento con `nice`: 194 instancias en ~40 min.
- **Aprendido**: medir la estructura de las instancias reales antes de
  estimar el beneficio. Que haya XOR no basta: en la mayoría son puertas de
  circuito, no sistemas lineales.


## 2026-09-23 (noche, 3) — Cambio a ejecución local de los experimentos

- **Se pidió**: «para la ejecución de todos los experimentos la continuidad
  será en un entorno local no usando el hardware de la nube».
- **Se hizo**:
  - se detuvieron los procesos en marcha en la sesión de nube: EXP-008 iba por
    112 de 120 parejas;
  - se descartó ese parcial **sin promocionarlo ni intentar reanudarlo en
    otra máquina**: el diseño A/B intercalado (ADR-0003 §4b) asume una sola
    máquina, y mezclar dos equipos reintroduce la deriva que ese diseño existe
    para anular;
  - se formalizó `scripts/reanudar_experimentos.sh`, que encadena EXP-008, las
    partes pendientes de EXP-010 y EXP-011, y EXP-012, con --resume dentro de
    una misma máquina;
  - se documentó la incidencia en EXP-008 §8 y se cancelaron los vigilantes
    (`send_later`) de la sesión de nube, que ya no aplican.
- **Decisiones**: ninguna de diseño; es un cambio de dónde se ejecuta, no de
  qué se mide. Los preregistros (EXP-008/010/011/012) no cambian: sus
  comandos de "Reproducir" son los mismos, ahora lanzados en local.
- **Aprendido**: el protocolo experimental (una sola máquina por tanda) hay
  que aplicarlo también a los cambios de entorno de ejecución, no solo a los
  cortes por reinicio dentro de la misma sesión.

## 2026-09-24 — Primera sesión local: revisión, banco de la tesis e ideas de los ganadores

- **Se pidió**:
  - verificar todo el repositorio y las líneas de investigación;
  - trabajar con el banco industrial de la tesis del director (≈ 1900
    instancias), comparando LabeSAT con los resultados de Kissat de la tesis
    **sin volver a correr Kissat**;
  - profundizar en ideas nuevas a partir de los ganadores de la Main Track;
  - mantener las prácticas de GitHub, la documentación continua, la autoría
    solo humana y el registro de decisiones.
- **Se hizo**:
  - **Revisión**: la rama de la nube iba 13 commits por delante de `main`
    (EXP-008, mclique, satsuma integrado, research/05 y /06). La rama de la
    sesión se colocó encima de ella. Build, `smoke_test.sh` y `test_symmetry.sh`
    en verde en la máquina local.
  - **Retomar la cadena pendiente** (EXP-008, 010, 011, 012): herramientas y
    bancos bajados. Faltaba `satsuma-mclique-v1`, que solo existía en la
    nube, y ahora `get_tools.sh` lo reconstruye desde su commit.
  - **Banco de la tesis**: `build_thesis_bench.py`, con partición dev/test
    estratificada y fijada antes de medir, y la referencia de Kissat en
    `results/tesis-kissat.reference.csv`.
  - **Hallazgo**: la tesis usó otra 4.0.x y otras máquinas (los conflictos
    coinciden en 1 de 8 instancias con la misma semilla). De ahí D-017 y
    EXP-013.
  - **research/07**, con fuentes primarias (diapositivas y actas de 2025,
    paquetes de 2026): B2 era un error de hecho; se descartan los reinicios
    fríos a ciegas con una simulación sobre la tesis; VSA y VSIDS/CHB, a la
    lista.
  - **VSA** implementada detrás de una opción y verificada. EXP-013, 014 y
    015 preregistrados y encolados.
- **Decisiones**:
  - D-017 (calibrar en vez de usar la tesis como brazo A);
  - D-018 (reabrir VSIDS/CHB, después de EXP-008);
  - EXP-014 parte 1 pasa de «en paralelo» a «sola» tras la caída.
- **Salió mal**:
  - **La máquina se quedó sin RAM** y cayó la sesión. Se solaparon la
    cadena, el escaneo de satsuma, un `make -j8` y la prueba de un prototipo
    de VSA que tenía un fallo. Se perdieron minutos, no datos: los guiones
    son reanudables. Regla nueva: una tanda pesada a la vez, con topes de
    memoria.
  - **El fallo del prototipo de VSA**: una macro de comparación evaluaba dos
    veces un argumento con efectos laterales (`A[++I]` en el quicksort de
    Kissat). Lo detectó un `ulimit -v` en la verificación: el proceso pidió
    4 GB en 5 s. Moraleja: en el código de Kissat, las macros `LESS` reciben
    expresiones, no valores.
  - **La cola esperaba al PID equivocado**: `pgrep -f` encontró el shell
    envoltorio de la sesión, cuya línea de órdenes contenía el nombre del
    guion. Es la misma trampa que ya recogía esta bitácora el 2026-09-23.
    Se corrigió esperando al PID del propio guion, desacoplado con `setsid`.
  - **El CI falló** al abrir el PR: el clon superficial (`fetch-depth` 1) no
    tiene el commit del que `get_tools.sh` reconstruye mclique v1. Ahora se
    omite con aviso si el commit no está; lo exige solo la cadena local.
  - Un permiso denegado por el clasificador del entorno al leer ficheros
    temporales; se usó la herramienta de lectura en su lugar.
- **Aprendido**:
  - En una máquina de escritorio, la memoria es el recurso que manda, no los
    núcleos.
  - Comprobar la **versión** de una referencia externa antes de compararse
    con ella: una sola corrida con la misma semilla lo delata.
  - Leer el paquete de un competidor antes de nombrar su técnica: el nombre
    `hypre` llevó a un error que duró desde el 2026-09-21.

## 2026-09-25 — Experimentos que sobreviven a apagados (ADR-0008) y cierre de EXP-008

- **Se pidió**: «ya ha pasado más de un día». Si se perdieron las
  ejecuciones, idear un mecanismo de checkpoints y de resistencia ante
  apagados, «porque es tiempo que estamos desperdiciando».
- **Se encontró**:
  - EXP-008 había terminado (120/120, a las 00:45).
  - La cadena murió a la 01:13 en EXP-011 parte 1 (80 de 84), sin error en
    los logs: el equipo se apagó o suspendió. Después hubo tres reinicios.
  - La cola de EXP-013–015, lanzada a mano, no sobrevivió y **nunca
    arrancó**. Se perdieron unas 15 h de máquina.
- **Se hizo**:
  - **ADR-0008**, en tres capas:
    - checkpoints duraderos en todos los arneses (`checkpoint.py`, fsync,
      filas íntegras, `--resume` en los tres que no lo tenían);
    - cola declarativa `cola.toml` con un orquestador (cerrojo, latido,
      marcas);
    - servicio systemd de usuario que la relanza al iniciar sesión, impide
      la suspensión (también la de la tapa) y limita la memoria a 12 GB.
  - `test_reanudacion.sh`, también en CI: simula el apagón con `kill -9` y
    una línea cortada, y la tanda reanudada es idéntica a una sin cortes.
  - Servicio instalado y en marcha. EXP-011 parte 1 reanudó en la instancia
    81.
  - **EXP-008 cerrado**: sin diferencia (p = 0,60), se mantiene 4.0.4
    (D-013).
- **Decisiones**:
  - instalar el servicio de usuario (pedido explícito del director);
  - **no** activar `loginctl enable-linger` desde la sesión, porque es una
    opción del sistema: se le propuso al director, que la activó él mismo.
    Desde entonces, la cola arranca al encender el equipo.
- **Salió mal**:
  - La primera versión de la prueba de reanudación daba «OK» sin comparar
    nada: un error de sintaxis dejaba vacías las dos claves, que
    «coincidían». Se detectó leyendo la salida, no el veredicto. Ahora un
    CSV vacío hace fallar la prueba.
  - `grep -c` escribe «0» y además sale con código 1: con `|| echo 0` se
    imprimía «0» dos veces y se rompía la aritmética de la cola.
- **Aprendido**:
  - Un proceso lanzado a mano no es una cola: sin nada que lo relance, un
    apagado cuesta la noche entera.
  - Una prueba que puede pasar por vacío no prueba nada: hay que exigir que
    lo comparado exista.

## 2026-09-28 a 30 — Revisión de la cola y cierre de EXP-010 a EXP-015

- **Se pidió**: «revisa el progreso de los experimentos para continuar la
  investigación» (dos veces, tras días sin sesión).
- **Se encontró**:
  - el 28, la cola llevaba tres días avanzando poco: dos pasos bloqueados por
    fallos de código y el resto frenado por `MemoryHigh`;
  - el 30, toda la cola había terminado el día 29 a las 07:41.
- **Se hizo**:
  - Arreglos de la cola:
    - `verify_symm_answers.py` toleraba mal los bytes no UTF-8 de dsr-trim;
    - `analyze_exp011.py` exigía la build con cliquer y contaba 84 instancias
      en vez de las 74 del preregistro;
    - se quitó `MemoryHigh`, que frena en vez de matar (65 724 eventos `high`).
  - **Cierre de seis experimentos**, cada uno con su criterio preregistrado:
    - EXP-010: v1 no se adopta;
    - **EXP-011: se adopta mclique v2** (D-005);
    - **EXP-012: equivalente**;
    - **EXP-013: calibrable** (D-017);
    - EXP-014: la ruptura cuesta tiempo fijo en la industria;
    - EXP-015: VSA nulo.
  - Investigación de los dos «FALLO» de seguridad de EXP-012: eran del
    verificador (`MemoryError` con ~40 M de cláusulas). Se reescribió
    `verify_model.py` en flujo y los dos modelos resultaron válidos.
  - Simulación de la **ruptura con retraso** con los datos de EXP-007 y
    EXP-014: con X = 2 s mejora a «siempre» y a «nunca» en los dos bancos.
    Pasa a ser la propuesta para EXP-009 (B3).
- **Decisiones**:
  - D-005, D-013 y D-017 cerradas por sus criterios preregistrados;
  - el binario integrado sigue con `CLIQUES=0` hasta que una prueba de
    equivalencia propia valide mclique dentro de él.
- **Salió mal**:
  - **Un heredoc sin comillas** (`<<EOF`) en un comando de shell: las
    palabras entre comillas invertidas del texto de EXP-012 se ejecutaron
    como órdenes. Se ejecutó `solver/labesat` sin argumentos, que solo
    imprimió la ayuda; el resto dio «orden no encontrada». Desaparecieron
    esas palabras del documento commiteado. Se detectó leyendo la salida y se
    corrigió con `--amend` antes de subir. Regla: para texto con comillas
    invertidas, heredoc con comillas (`<<'EOF'`) o la herramienta de edición.
  - Un fallo de un paso de la cola se quedó sin ver hasta la siguiente
    sesión: el diseño lo paró bien, pero nadie miró el estado.
  - Un control mal especificado en EXP-014: «propagaciones idénticas» no
    tiene sentido en corridas que terminan por tiempo. Se investigó y se
    documentó, sin cambiar el criterio a posteriori.
  - Una pareja de EXP-014 murió por la señal 16 en las dos ramas; repetida a
    mano, termina con normalidad. Causa sin identificar.
- **Aprendido**:
  - Un fallo de verificación no es un modelo incorrecto hasta que se
    reproduce. Hay que distinguir el error del verificador del veredicto.
  - Un límite de recursos que frena es peor que uno que mata: el primero
    falsea los tiempos sin dejar rastro.
  - Que «siempre» empate con «nunca» en PAR-2 no cierra la línea: puede
    esconder dos efectos opuestos, coste fijo y ganancia de búsqueda, que una
    política sencilla separa.

## 2026-10-01 — Estrategia de optimización con demostración (research/08, ADR-0009)

- **Se pidió**: los próximos pasos, con la idea de optimizar todo el código de
  LabeSAT para bajar su tiempo. Cada solución, con una demostración rigurosa
  antes de aplicarla, y todo documentado.
- **Se hizo**:
  - **research/08**. Primero, qué se puede ganar:
    - por la teoría de la complejidad de pruebas (Haken; Beame, Kautz y
      Sabharwal; Pipatsrisawat y Darwiche), ninguna estructura de datos
      quita el crecimiento exponencial en conflictos de un CDCL que solo
      deriva por resolución;
    - las ganancias exponenciales vienen de cambiar el sistema de pruebas:
      simetrías (PR), XOR, BVA;
    - lo demás es un factor constante.
  - **Proposición 1**: el valor exacto de un factor constante en PAR-2, con
    datos censurados. Un 10 % de velocidad vale ≈ −1,5 % de PAR-2.
  - **Teorema 5**: cuándo una compilación no cambia ni una decisión de la
    búsqueda. Sin comportamiento indefinido, redondeo IEEE por operación
    (de ahí `-ffp-contract=off` con FMA, por `smooth.c:34-35`), sin
    decisiones por tiempo y sin depender de direcciones absolutas. Cada
    condición se comprobó en el código de Kissat.
  - **ADR-0009**: clases E, P y S de optimización, y qué prueba exige cada
    una.
  - **EXP-016** (perfil de costes) preregistrado y en marcha en la cola.
  - **EXP-017** (PGO, LTO y `-march`) preregistrado con un control
    negativo: el mismo `-march` sin `-ffp-contract=off`, donde el teorema
    predice que la trayectoria cambia. Infraestructura:
    - `build.sh --pgo/--lto/--march`;
    - `--conflicts` en el A/B, para medir velocidad con el mismo trabajo.
- **Decisiones**:
  - No se optimiza nada antes de medir: una parte que pesa < 5 % tiene un
    techo de ≈ 0,8 % de PAR-2 (Amdahl y Proposición 1).
  - La compilación va antes que tocar código: es gratis y su equivalencia
    está demostrada.
  - Ningún cambio de código de búsqueda sin su prueba escrita en research/08.
- **Salió mal**:
  - `configure` de Kissat rechaza `-Wno-missing-profile`; se quitó de
    `build.sh`.
  - La compilación de prueba de la PGO (13 min, 2 núcleos, `nice`) coincidió
    con el perfilado de EXP-016. Se anotó como incidencia en EXP-016 §6.
  - Una función auxiliar de edición en Python falló por un argumento de más
    (`TypeError`) y dejó a medias la edición del CHANGELOG. Se rehízo con la
    herramienta de edición.
  - El A/B habría medido dos veces las instancias presentes en dos bancos.
    Se detectó al montar el banco de EXP-017 y se deduplicó por nombre.
- **Aprendido**: antes de proponer optimizaciones, acotar cuánto pueden
  valer. Cambia el orden de prioridades: la compilación (gratis) y el sistema
  de pruebas (exponencial) van por delante de reescribir estructuras de
  datos que ya son óptimas.

### 2026-10-01 (continuación) — K1: la primera optimización de código, con su prueba

- **Se hizo**:
  - Auditoría del núcleo de Kissat (research/08 §6): ningún componente
    tiene margen asintótico; el factor constante lo domina la latencia de
    memoria.
  - Búsqueda bibliográfica: la precarga de cláusulas ya se midió (+12 %,
    Manthey y Saptawijaya, 2010) en un resolvedor sin literal bloqueante.
  - Implementación de K1 detrás de una macro apagada por defecto, en una
    rama y un *worktree* aparte.
  - Comprobación de equivalencia (81 contadores): idénticos en las 5
    instancias que terminaron; la sexta superó el tope de 15 min.
  - EXP-018 preregistrado.
- **Decisiones**:
  - K1 se desarrolla **fuera del árbol que usa la cola**. El servicio compila
    los binarios de EXP-017 desde ese árbol y el preregistro los ata a su
    commit; un cambio en `proplit.h`, aunque esté desactivado, ensuciaría esa
    trazabilidad. La rama se fusiona cuando la cola haya compilado EXP-017.
  - Distancia de precarga fijada a priori (8), sin ajustarla con datos.
- **Salió mal**: el primer cambio de `proplit.h` se escribió en el árbol de
  la cola; se detectó antes de compilar nada y se movió a su rama.

### 2026-10-01 (tarde) — Técnicas que cambian el sistema de pruebas: X1

- **Se pidió**: mientras terminan los experimentos, diseñar las técnicas que
  cambian el tipo de prueba, demostrarlas y documentarlo todo.
- **Se hizo**:
  - **research/09**:
    - qué familias separan resolución, ER y PR/SR;
    - qué cubre ya LabeSAT (simetrías con SR, BVA con `factor`) y qué no
      (paridad);
    - **Teorema 1**: prueba DRAT de tamaño O(Σ 2^k + N log |S|) para un
      sistema XOR inconsistente, con cadenas ordenadas de variables de
      extensión, lemas por casos y suma en árbol equilibrado;
    - corolario de separación sobre Tseitin.
  - **Prototipo** en Python y **familias sintéticas** (Tseitin, *lights-out*
    y dos órdenes, en versión UNSAT y SAT).
  - **Implementación en Kissat** (`gauss.c`), detrás de `configure --gauss`.
  - `test_gauss.sh`. EXP-019 preregistrado.
  - Refuta en 0,02 s una *lights-out* UNSAT de 2026 que el mejor solver
    tardó 346 s en resolver, con prueba verificada por los dos `dsr-trim`.
- **Decisiones**:
  - Pruebas de X1 **sin borrados** (§4.3 de research/09).
  - X1 **detrás de una macro de compilación** además de la opción, para
    poder fusionarlo sin tocar los binarios de EXP-017 y EXP-018: objetos
    idénticos byte a byte. El gancho va en `internal.c`, porque en
    `search.c` cambiaba una constante `__LINE__`.
  - La descarga de las instancias de paridad de `dev.list.csv` (GBD) queda a
    la espera del visto bueno del director.
- **Salió mal**:
  - **El `dsr-trim` de SC2026 se cuelga** con ciertos borrados. Se tardó
    varias iteraciones en aislarlo: primero una regla de «no borrar lo que
    toque variables fijadas», que no bastó; luego definiciones primero, que
    tampoco; al final, una reducción quitando solo borrados mostró dos
    disparadores de un único borrado cada uno.
  - **Un reinicio de la máquina borró `/tmp`**, y con él el worktree de X1
    con cambios **sin commitear**. `gauss.c` y `gauss.h` se recuperaron; las
    ediciones de `options.h`, `proof.c/h`, `internal.c` y `configure` se
    rehicieron de memoria. Regla desde ahora: commitear el trabajo en curso
    en su rama cada poco, aunque sea provisional.
  - Tres fallos del guion de prueba, no de X1:
    - `grep -q` con `pipefail` (SIGPIPE, ya conocido de `test_symmetry.sh`);
    - el código 10 de Kissat con `set -e`;
    - el retorno de carro con el que `drat-trim` escribe su veredicto.
  - Un error de aritmética en la cota de la malla 30×30 (603 000 en lugar de
    642 602), corregido antes de commitear.

### 2026-10-01 (tarde, tras el reinicio) — Cierre de EXP-016 y EXP-017

- **Se hizo**:
  - **EXP-016** cerrado: propagación ≈ 57 %, análisis 14–19 %, sondeo
    15–19 %.
  - **EXP-017** cerrado: PGO + LTO adoptado (×1,030), `-march` ×1,040.
    El control con FMA no cambió ninguna trayectoria aunque el binario
    llevaba FMA en código que decide.
  - D-019 registrada y agendada (issue #33).
- **Salió mal**:
  - El guion de EXP-016 perdía `propagate` y `decide` en Q4, por
    `join(lsuffix, rsuffix)`.
  - La muestra de EXP-019 marcaba como «unknown» las 450 de `tesis-dev`,
    porque la tesis escribe `SAT`/`UNSAT` en mayúsculas.
  - Los dos se detectaron leyendo la salida antes de usarla, y se
    corrigieron con su incidencia anotada.
- **Aprendido**: un control negativo que no se manifiesta no refuta la
  condición teórica. Sí indica que su efecto práctico es raro, y lo
  correcto es informarlo tal cual, como preveía el preregistro.

### 2026-10-01 (tarde) — Distancia a los ganadores de 2026 (research/10)

- **Se pidió**: mientras corren los experimentos, seguir buscando mejoras y,
  para empezar, analizar lo lejos que está LabeSAT de los ganadores de 2026
  y qué podemos integrar de ellos.
- **Se hizo**:
  - contrafactual por instancia con los tiempos oficiales: hoy, 16.º; con
    B3 + X1 + PGO, 1.º con −75 s;
  - tabla técnica por técnica de los diez primeros;
  - el hueco de 56 instancias, agrupado;
  - comprobación con los rasgos de GBD de que *linear-equations* no son XOR;
  - simulación de la cartera con MAB: no compensa;
  - cuantificación del riesgo del tope de satsuma.
- Se cerró también EXP-018 (K1): un 7 % más lenta; no se adopta.
- **Salió mal**:
  - El preregistro de la ampliación de EXP-019 decía que nadie resolvió
    *ordering-principle-xor* y *xor-shifting* en 2026. La columna
    «no-resuelta» de `dev.list.csv` es de la base Kissat, no del campo. Se
    detectó al cruzar con los datos oficiales y se corrigió antes de
    ejecutar.
  - Una edición por guion se cortó a mitad (no encontró un texto) y el
    commit de research/10 salió sin el índice, el CHANGELOG ni la bitácora.
    Se completó en el commit siguiente.
- **Aprendido**: un contrafactual que pone a LabeSAT 1.º en el banco con el
  que se diseñaron sus técnicas no es una ventaja asegurada. El margen
  (2 %) es menor que la incertidumbre de los topes de satsuma, que se puede
  medir.

### 2026-10-01 (noche) — X1 v2, cierre de EXP-019 y preregistros de EXP-020 y EXP-021

- **Se pidió**: empezar por la mejora 4 (cobertura de X1) y el preregistro
  de la 3 (tope de satsuma).
- **Se hizo**:
  - **X1 v2** (Gauss por componentes conexas, Lema 6 con su demostración),
    con test construido y paso bajo ASan/UBSan;
  - **EXP-019 cerrado**: se adopta X1;
  - **EXP-021** (cobertura de la v2) y **EXP-020** (tope de satsuma)
    preregistrados y en la cola tras EXP-009.
- **Decisiones**:
  - La activación por defecto de X1 espera a EXP-021, porque EXP-019 midió
    la v1.
  - EXP-020 decide por dominancia sobre las 13 candidatas: el efecto fuera
    de ellas es nulo por construcción.
- **Salió mal**: la predicción de la ampliación de EXP-019 para *xor-chain*
  y *tseitin-formulas* (que X1 las refutaría) falló. No contienen XOR:
  codifican la paridad con contadores unarios. Se documenta como límite de
  X1.


### 2026-10-03 — Cierre de EXP-009, EXP-020 y EXP-021; X1 por defecto; D-020

- **Se pidió**: continuar («continua») con la consigna de seguir mejorando
  LabeSAT mientras corren los experimentos. La cola había terminado.
- **Se hizo**:
  - **EXP-009 cerrado**: el retraso de 2 s (B3) se descarta. Empeora frente
    a «nunca» en 153 instancias frescas (fila 4 del criterio). Análisis
    exploratorio: el coste está en las instancias medianas.
  - **EXP-021 cerrado**: X1 v2 procesa 56 de los 103 sistemas saltados y
    pasa a estar **activa por defecto** (`build.sh` con `--gauss`, la
    opción a 1).
  - **EXP-020 cerrado**: se mantiene el tope de 60 s.
  - `build/` recompilado con PGO + LTO, lo adoptado en EXP-017, ahora que
    ninguna tanda lo vigila.
  - research/10 rehecho: «siempre» + X1 + PGO/LTO queda 1.º con −72 s en
    2026, y el selector perfecto entre «siempre» y «nunca» es una cota de
    −395 s.
  - **D-020** registrada (política de simetrías del paquete), con issue.
  - Manual, página `man`, CHANGELOG, ROADMAP y plan al día.
- **Decisiones**:
  - Se aplicó la fila 4 de EXP-009 y no la 2: hay diferencia, y va en
    contra.
  - La política de simetrías del paquete no la decide un experimento sino
    el director (D-020). Mientras tanto no cambia ningún valor por defecto.
  - Los pasos históricos de la cola llevan `--no-gauss`, para que
    reproducirlos dé el mismo binario.
- **Salió mal**:
  - La simulación que eligió X = 2 s predecía −2,4 s, y la medida fresca
    dio +9,9 s. Elegir un parámetro con los mismos datos con los que se
    evalúa infló el efecto, como advertía el propio preregistro (§5).
  - La estimación de EXP-021 (~1 h) se quedó corta: la equivalencia tardó
    ~38 h, porque la muestra eran justo las instancias más grandes.
  - Se tuvieron que corregir dos cifras del borrador de EXP-020 (el rango de
    cambio de cláusulas) y la explicación del respaldo de satsuma, antes de
    commitear.
- **Aprendido**: en 2026, lo que solo resuelve «nunca» es casi todo SAT y lo
  que solo resuelve «siempre», casi todo UNSAT. Un selector entre los dos
  tiene que predecir SAT/UNSAT, que es justo lo difícil.
