# 04 — Decisiones pendientes del autor: hechos, opciones y recomendación

- **Fecha**: 2026-09-23
- **Para**: Abel Ponce (las cuatro decisiones son suyas; aquí solo se reúnen los
  hechos)
- **Fuentes primarias**:
  - reglas, pistas y formato de salida de la SAT Competition 2026, y su
    repositorio `satcompetition/2026` (commit `3e2dee7`);
  - el script oficial de selección de benchmarks (`select26.py`);
  - las puntuaciones oficiales de 2026 (`data/competition/scores_2026.csv`);
  - los paquetes de solvers publicados, el código de satsuma y la FAQ de la GPL.
- **Aviso**: nada de esto es asesoramiento jurídico, y **la interpretación
  vinculante de las reglas es de los organizadores**. Donde las reglas no
  concretan, se dice.

---

## Resumen

| # | Decisión | Qué dicen los datos | Recomendación | Urgencia |
|---|---|---|---|---|
| 1 | ¿Subcategoría IA o categoría regular? | Todo el código añadido a LabeSAT lo ha escrito una IA. La regla exige declararlo y no fija ningún umbral | **Preguntar por escrito ya** y planificar como caso base la subcategoría IA | Alta: condiciona la estrategia |
| 2 | ¿Se admite satsuma + kissat? | Hay precedentes directos en 2025 y 2026, en la categoría regular. Las pruebas SR se aceptaron en 2026 con DSRtrim y Trestle | Riesgo bajo: confirmarlo en el mismo correo | Media |
| 3 | Familia de los 20 benchmarks | Entran 12 de 20, por sorteo. El ganador de 2026 envió familias simétricas | **Covering arrays** (primera opción); no existen en GBD | Media: se entregan con el registro (~abril) |
| 4 | ¿MIT o cliques (GPL)? | cliquer se usa en **una sola llamada**. Sin él cambia la salida en 8 de 74 instancias | Esperar a EXP-007. Si hay coste, **reimplementar la clique máxima en MIT** | Baja: depende de EXP-007 |

---

## 1. Subcategoría IA

### Qué dicen las reglas (2026, textual)

- *«There are separate subcategories for AI-generated and AI-tuned solvers in
  each of the Main, Experimental, Parallel, and Cloud tracks. […] However,
  these solvers are not eligible for regular track prizes. An award will be
  given to the best AI-tuned and AI-generated solver in each track.»* (Tracks)
- La descripción del sistema debe incluir: *«State which code base, including
  the version, was used. Quantify how many changes were applied to the code
  base. […] Qualify how many changes are due to AI (also if it is zero). […]
  List all heuristics that have been tuned by AI (also if it is none).»*
  (Rules)
- *«Your system description must report the original solver codebase and
  version, along with the number of lines edited or added by humans and the
  number of lines edited or added by artificial intelligence.»* Además, las
  descripciones se revisan «more strictly» y pueden **rechazarse** (README
  de 2026).

**Lo que las reglas no dicen**:

- no definen qué es «AI-generated» ni «AI-tuned»;
- no fijan ningún umbral: ¿basta una línea escrita por IA?, ¿cuenta el diseño
  asistido por IA si el código lo teclea una persona?

### Cómo se aplicó en 2026

En los datos oficiales, **12 de 33 solvers** llevan la etiqueta
`[main-ai]` o `[exp-ai]`: `gopalan_kissat-evolve` (×4), `ding_kissat-mab-eae`
(×3), `green_lymphosat` (×2), `zheng_kissat-mab-hypre-evolve`,
`zheng_kissat-mab-hypre-satlution` y `zhenwei_mergesat-l`.

- **El mismo equipo** tiene `zheng_kissat-mab-hypre` **[main]** y
  `zheng_kissat-mab-hypre-evolve` **[main-ai]**. La etiqueta depende de *cómo
  se produjo cada variante*, no del equipo. La variante `-evolve` trae
  artefactos de un bucle de evolución con LLM (`.optv-evolve/`, `AGENTS.md`).
  «SATLUTION» es el sistema de arXiv:2509.07367, que evoluciona el
  repositorio completo con agentes LLM.
- **Mejor solver regular**: `anders_satsuma-iter-kissat`, con PAR-2 = 3647 s.
  **Mejor solver IA**: `zheng_kissat-mab-hypre-evolve`, con PAR-2 = 4010 s
  (calculado sobre las 400 instancias). Hay unos 360 s de diferencia.
- La variante IA de zheng **también lleva satsuma** dentro. En la subcategoría
  IA de 2027 es de esperar competencia con ruptura de simetrías.

### La situación de LabeSAT, en números

- **Base**: Kissat 4.0.4, con **38 944 líneas** en `src/*.c,h`.
- **Cambios en kissat**: +458 / −13 líneas en 14 ficheros.
  - 277 de esas líneas son A4.1 (`mode.c/h`, `modetrace.c/h`), que va
    **desactivado** por defecto.
  - Lo activo: el terminador de `lucky.c`, `--append-proof`, la identidad del
    banner y los scripts de build.
- **Cambios fuera de kissat**: el guion `solver/labesat` (125 líneas de bash).
  satsuma se usa **sin modificar**.
- **Autoría**: el 100 % de esas líneas las ha escrito un asistente de IA bajo
  dirección humana. También la metodología experimental y los análisis.
- **Heurísticas ajustadas por IA**: ninguna mediante búsqueda automática de
  parámetros. A4.1 está apagado y satsuma usa sus valores por defecto. Pero el
  diseño de B3″ y la elección de umbrales, como `LABESAT_SYMM_TIMEOUT=60`, sí
  salen de un proceso asistido por IA.

### Opciones

| Opción | A favor | En contra |
|---|---|---|
| **A. Declararlo tal cual → subcategoría IA** | Honesto y sin ambigüedad. En 2026, una entrada del nivel de satsuma+kissat habría ganado la subcategoría IA con ~360 s de margen | No opta a los premios regulares. La subcategoría crecerá en 2027 (12 entradas en 2026) |
| **B. Que el autor reescriba a mano el código cambiado y declare 0 líneas de IA** | El código cambiado es pequeño (~200 líneas activas) | La regla cuenta *líneas*, pero ¿cuenta el diseño? Reescribir para evitar la etiqueta puede interpretarse como eludirla. **Solo con permiso explícito de los organizadores** |
| **C. Entrar en las dos** (hasta 4 solvers secuenciales por persona) | Una variante IA declarada y, si los organizadores lo aceptan, una variante escrita por humanos | Duplica el trabajo de descripción. Los premios regulares siguen dependiendo de la respuesta a B |

### Recomendación

1. **Escribir ya a los organizadores** (borrador en §6), preguntando: qué es
   «AI-generated»; si el diseño o los experimentos asistidos por IA, con código
   tecleado por personas, cuentan; y si hay umbral.
2. **Planificar el caso base como la opción A.** Es la única que no depende de
   una interpretación favorable.
3. **No** reescribir para eludir la etiqueta sin permiso escrito.

---

## 2. Composición satsuma + kissat y pruebas SR

### La regla

> *«Pure Portfolios which are a combination of two or more (core) SAT solvers
> developed by different groups of authors are not allowed […]. Otherwise,
> solver compositions must have different solving methodologies, e.g., CDCL,
> SLS, Lookahead, Groebner Basis, etc., not just different solving
> strategies.»*

### Precedentes

| Año | Solver | Composición | Categoría |
|---|---|---|---|
| 2025 | `BreakID-Kissat` | ruptura de simetrías (BreakID) + kissat | Main regular (4.º) |
| 2026 | `anders_satsuma-iter-kissat` | satsuma + kissat; el autor de satsuma, no el de kissat | Main regular (**1.º**) |
| 2026 | `oertel_satsuma-lex-kissat` | satsuma (modo `lex`) + kissat | Main regular |
| 2026 | `zheng_kissat-mab-hypre` | kissat-MAB **con satsuma dentro**; no son autores de ninguno de los dos | Main regular |

**Lectura**:

- Un **preprocesado** seguido de un solver, en tubería, no es una «cartera»:
  no se ejecutan solvers en paralelo ni se elige uno.
- La detección de automorfismos (dejavu) y la ruptura de simetrías son una
  metodología distinta de CDCL.
- Hay **tres equipos en 2026** con esta misma composición, uno de ellos sin ser
  autor de ninguna de las dos partes. El riesgo es **bajo**.

### Pruebas

- Los participantes **eligen** el verificador (*«the proof checker you
  selected»*). La lista oficial de 2026 incluye **DSRtrim `8f857dd`** y
  **Trestle** (*«Verified Substitution Redundancy Checking», Codel, Avigad y
  Heule*): exactamente el formato SR de satsuma + LabeSAT.
- **Riesgo encontrado y mitigado hoy**: nosotros fijábamos dsr-trim `c3119d8`,
  **12 commits de correcciones** después del commit de la competición. Una
  prueba válida para el nuevo y no para el viejo descalificaría. Ahora CI
  verifica **con los dos**, y las pruebas actuales pasan con ambos
  (`c61a184`).
- **Pendiente**: para 2027 hay que volver a comprobar la lista de verificadores
  y su commit. Hay además un plazo propio para *enviar* verificadores (en 2026,
  el 20 de marzo).

### Advertencia estratégica

Una entrada que sea **solo** «satsuma + kissat» es, en esencia, **el ganador de
2026 sin cliques**. Con la revisión estricta de descripciones, tiene que quedar
clara la aportación propia:

- la activación condicional (B3), dirigida al estrato X donde satsuma daña;
- la verificación reforzada;
- la metodología.

Además, es de esperar que Anders compita en 2027 con una versión mejorada.

**Recomendación**: confirmarlo en el mismo correo del §6; citar a los autores de
satsuma, dejavu y kissat en la descripción; y **priorizar B3** como aportación
diferencial.

---

## 3. Los 20 benchmarks

### Reglas y mecánica

- 20 instancias **nunca vistas** en competiciones anteriores, con una
  descripción del origen y del generador, **que también requiere la
  declaración de IA**.
- Al menos 10 «interesantes»: MiniSat no las resuelve en 1 minuto y el propio
  solver sí en 1 hora.
- En 2026 se entregaron con el registro, el **19 de abril**, un mes antes que
  el solver.
- **Script oficial `select26.py`**:
  - de cada equipo participante se sortean **12 de sus instancias**
    (`budget = 12`), tras deduplicar por `isohash2`; las isomorfas cuentan
    como una;
  - el resto del conjunto (~400) sale del histórico, **excluyendo** las fáciles
    para MiniSat (`minisat1m`), las familias `random` y las `huge`.
- Por tanto, nuestra familia pesaría ~12/400 = **3 %** del PAR-2 de todos.

### Qué hicieron otros en 2026

| Equipo | Familias |
|---|---|
| anders (satsuma) | **clique-coloring, ramsey-numbers**: simétricas, favorables a su técnica |
| biere | multiplier-verification |
| froleyks | hardware-model-checking |
| schreiber | mechanical-master-key |
| zhenwei | equivalence-checking |
| … | argumentation, md5-equivalence, p-center, scheduling, school-timetabling, … |

Elegir una familia de tu dominio es la práctica habitual, y el ganador de 2026
lo hizo con familias simétricas. Es legítimo siempre que las instancias sean
genuinamente interesantes y la descripción sea honesta.

### Candidatas, comprobadas contra GBD (31 809 instancias, 189 familias)

| Familia | ¿Existe en GBD? | Simetría (le va bien a satsuma) | Generador | Dificultad ajustable | Interés aplicado |
|---|---|---|---|---|---|
| **Covering arrays** CA(N; t, k, v) | **No** | **Muy alta**: filas, columnas y símbolos | Sencillo | Sí, alrededor de las cotas conocidas (tablas de Colbourn) | **Alto**: testing combinatorio |
| Reglas de Golomb | No | Baja (reflexión) | Sencillo | Sí (marcas / longitud) | Medio |
| Arrays de Costas | No | Media (diedral) | Sencillo | Sí (orden n) | Medio (radar/sonar) |
| Pares de Langford | No | Baja | Trivial | Limitada (existencia conocida) | Bajo |
| MOLS (cuadrados latinos ortogonales) | No (solo `quasigroup-completion`) | **Muy alta** | Medio | Sí | Medio |
| Números de Schur | **Sí** (56, en `coloring`) | Alta | — | — | Ya usada |

### Recomendación

- **Covering arrays como familia principal**: es nueva, muy simétrica y con
  motivación aplicada real. Se pueden elegir parámetros a ambos lados de las
  cotas conocidas, para tener una mezcla SAT/UNSAT.
- Si se quiere diversificar, **arrays de Costas** como segunda familia.
- Plan de calibración, en local y **antes** de fijar las 20:
  1. escribir el generador (MIT);
  2. barrer parámetros;
  3. medir MiniSat (≥ 60 s) y LabeSAT (≤ 1 h);
  4. comprobar que no son isomorfas entre sí (`isohash2`).
- Coste estimado: ~1 semana de trabajo y del orden de 20–40 h de CPU.
- Con 12 sorteadas, conviene que **las 20** sean interesantes, no solo 10.

---

## 4. MIT frente a cliques (GPL)

### Hechos nuevos

- satsuma usa cliquer en **una sola llamada**:
  `clique_unweighted_find_single(...)` en `src/reorder.h`. Busca **una clique
  máxima** en un grafo de ≤ 10 000 vértices (las variables de una fila de
  simetría que coaparecen en cláusulas) para **reordenar columnas** antes de
  generar los predicados de ruptura.
- Con `CLIQUES=OFF`, `symmetries.h` sustituye `reorder_columns` por una
  función vacía. Se pierde **toda** la reordenación, no solo cliquer.
- Efecto medido (`docs/research/03`), sin kissat:
  - la salida cambia en **8 de 74** instancias;
  - en **5** de ellas, la versión con cliques refuta la fórmula dentro de
    satsuma;
  - con cliques, la salida es idéntica a la del ganador de 2026 en **74 de
    74**.
- Cuánto cuesta eso en PAR-2 lo dirá **EXP-007** (en curso). Después se medirá
  kissat sobre la salida con cliques en esas 8 instancias.

### Opciones

| Opción | Licencia resultante | Coste | Notas |
|---|---|---|---|
| **a. Seguir sin cliques** | Todo MIT | El que mida EXP-007 (quizá 0) | Lo actual |
| **b. satsuma + cliquer como ejecutable GPL aparte** | El kissat de LabeSAT sigue **MIT**; solo el binario de satsuma es GPLv2 | Nulo en rendimiento | Según la FAQ de la GPL, programas separados que se comunican por ficheros o línea de órdenes son una «mere aggregation» y la GPL de uno no afecta al otro. Aquí se comunican con CNF y prueba en DIMACS estándar. La competición exige el código «licensed for research purposes», y la GPL lo cumple. cliquer se **descargaría** en el build, sin entrar en el repositorio |
| **c. Reimplementar la clique máxima en MIT** | Todo MIT | ~1–2 días más su validación | Es un algoritmo publicado (Östergård 2002; Tomita y Seki 2003). Hay que implementarlo desde el artículo, **sin leer el código de cliquer**. Recupera la reordenación. Validación: la misma salida que cliques, salvo empates, en las 74 de EXP-007. Además, es aportación propia que contar |

### Recomendación

- **Esperar al resultado de EXP-007.** Si no hay coste medible, la opción a.
- Si lo hay:
  - **la opción c** respeta tu «mantén MIT» y suma contribución;
  - **la opción b** es el respaldo inmediato, ya que no toca la licencia del
    código de LabeSAT.

---

## 5. Calendario orientativo (patrón de 2026; las fechas de 2027 aún no están publicadas)

| Hito | 2026 | Qué hay que tener |
|---|---|---|
| Envío de verificadores | 20-mar | — (no enviamos ninguno) |
| **Registro + 20 benchmarks** | **19-abr** | Familia elegida, generador, 20 instancias calibradas y su descripción (con declaración de IA) |
| Envío del solver secuencial | 10-may | Build de competición congelado; pruebas verificadas con el commit exacto del verificador |
| Descripción del solver (1–2 págs. IEEE) | 17-may | Declaración de IA con líneas humanas/IA y heurísticas ajustadas |

---

## 6. Borrador de correo a los organizadores (en inglés)

> **Subject:** SAT Competition 2027 — questions on AI-subtrack classification
> and a preprocessor + CDCL composition
>
> Dear organizers,
>
> I am preparing a Main Track entry, **LabeSAT**, for SAT Competition 2027 and
> would like to clarify two points in advance.
>
> **1. AI classification.** LabeSAT is based on Kissat 4.0.4 (38,944 lines).
> Our changes add about 460 lines to Kissat and a 125-line driver script.
> These lines were written by an AI coding assistant under my direction; the
> experimental methodology was also AI-assisted. No heuristic parameters were
> tuned by automated (AI) search. (a) Would this entry be classified as
> AI-generated, AI-tuned, or regular? (b) Is there a threshold (fraction of
> AI-written lines)? (c) If the same changes were re-implemented by hand from
> an AI-assisted design, how should this be declared?
>
> **2. Composition.** LabeSAT runs the symmetry-breaking preprocessor satsuma
> (M. Anders, unmodified, MIT) before our Kissat derivative, and continues
> satsuma's SR proof (checked with DSRtrim/Trestle). As with several 2025–2026
> entries (e.g., BreakID-Kissat, satsuma-iter-kissat), we understand this is a
> preprocessor + CDCL pipeline and not a portfolio. Could you confirm that
> this composition is admissible in the Main Track, and that the SR checking
> pipeline will again be offered in 2027?
>
> Thank you very much,
> Abel Ponce

---

## Fuentes

- Reglas SC2026: <https://satcompetition.github.io/2026/rules.html>
- Pistas y subcategorías IA: <https://satcompetition.github.io/2026/tracks.html>
- Formato de salida y verificadores: <https://satcompetition.github.io/2026/output.html>
- Repositorio de la web, con el README, `checker.commits.txt` y el script de
  selección: <https://github.com/satcompetition/2026>
- Paquetes de solvers de 2026: <https://satcompetition.github.io/2026/downloads.html>
- SATLUTION: <https://arxiv.org/abs/2509.07367>
- FAQ de la GPL v2 (mere aggregation; comunicación por pipes y línea de
  órdenes): <https://www.gnu.org/licenses/old-licenses/gpl-2.0-faq.en.html>
- dsr-trim: <https://github.com/ccodel/dsr-trim>
- Datos propios: `data/competition/scores_2026.csv`,
  `results/satsuma-builds/builds.csv`, `docs/research/03`.
