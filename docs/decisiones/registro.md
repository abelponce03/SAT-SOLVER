# Registro de decisiones

Proceso en [ADR-0005](../adr/0005-gobernanza-autoria-y-decisiones.md) §3:

1. Toda decisión que el levantamiento de requisitos no cubre se registra aquí
   con un ID `D-NNN`.
2. Se agenda en un issue con la etiqueta `decisión`, enlazado desde el issue de
   la próxima reunión (etiqueta `reunión`).
3. Mientras no se resuelve, se sigue con la opción reversible más conservadora.

Las decisiones de diseño ya tomadas y de largo alcance tienen su ADR en
`docs/adr/`. Este registro es el **índice** y el sitio donde viven las abiertas.

**Estados**: 🟡 abierta · ✅ resuelta · ⏸️ aplazada (con motivo).

| ID | Decisión | Estado | Quién decide | Dónde |
|---|---|---|---|---|
| D-001 | Commits ya publicados con autoría de Claude | ✅ opción b (2026-09-23) | Director | §D-001 · issue #5 · [correspondencia de SHA](D-001-correspondencia-sha.md) |
| D-002 | ¿Subcategoría IA o categoría regular? | ⏸️ correo aplazado hasta definir las mejoras (límite recomendado: 1-feb-2027) | Director (+ organizadores) | [research/04 §1](../research/04-decisiones-pendientes.md) · issue #6 |
| D-003 | ¿Se admite la composición satsuma + kissat? | ⏸️ mismo correo que D-002 (riesgo bajo) | Organizadores | [research/04 §2](../research/04-decisiones-pendientes.md) · issue #7 |
| D-004 | Familia de los 20 benchmarks obligatorios | 🟡 | Director | [research/04 §3](../research/04-decisiones-pendientes.md) · issue #8 |
| D-005 | ¿MIT o cliques (GPL)? | ✅ **opción c** (2026-09-23): reimplementar la clique máxima en MIT | Director | [research/03](../research/03-coste-de-mantener-mit.md) · issue #9 · EXP-010 |
| D-006 | Acceso a un clúster | ✅ no hay (2026-09-23) | Director | ROADMAP §4 |
| D-007 | Nombre del solver | ✅ LabeSAT (2026-09-22) | Director | CHANGELOG |
| D-008 | Ruptura de simetrías como programa externo, en MIT | ✅ (2026-09-23) | Director | [ADR-0004](../adr/0004-ruptura-de-simetrias-con-satsuma-externo.md) |
| D-009 | Autoría: solo el desarrollador en git | ✅ (2026-09-23) | Director | [ADR-0005](../adr/0005-gobernanza-autoria-y-decisiones.md) |
| D-010 | Documentación continua y multiformato, con LaTeX para los PDF | ✅ (2026-09-23) | Director | [ADR-0006](../adr/0006-documentacion-multiformato.md) |
| D-011 | Instalar el plugin «engineering» del catálogo | 🟡 (menor) | Director | §D-011 · issue #10 |
| D-012 | Insignia «via Claude» en las acciones de GitHub hechas desde la sesión | 🟡 | Director | §D-012 · issue #11 |
| D-013 | Base de Kissat: 4.0.4 o sc2026 | 🟡 se decide con EXP-008 | Director (con datos) | [plan](../plan/plan-main-track-2027.md) §3 · issue #18 |
| D-014 | Variantes a presentar (hasta 4 solvers secuenciales) | 🟡 | Director | [plan](../plan/plan-main-track-2027.md) §4 · issue #19 |
| D-015 | Caso de planificación: Main Track con declaración honesta de IA | ✅ (2026-09-23) | Director | [plan](../plan/plan-main-track-2027.md) |

---

## D-001 — Commits ya publicados con autoría de Claude

- **Surge**: el 2026-09-23, con la directriz de autoría.
- **Contexto**:
  - Hay commits con autor y committer `Claude <noreply@anthropic.com>` y
    trailers `Co-Authored-By: Claude …`: **25 en `main`** (de las épocas de los
    PR #1 y #2) y **21 en la rama del PR #3**.
  - El origen: el entorno de Claude Code on the web firma los commits con una
    clave registrada a esa identidad, y un hook de parada **exigía** esa
    identidad mientras la firma estaba activa.
  - Desde el 2026-09-23 el repositorio usa la identidad del desarrollador con la
    firma desactivada (ADR-0005). Los commits **nuevos** ya cumplen.
- **Opciones**:

| Opción | Qué implica | Coste / riesgo |
|---|---|---|
| a. Dejar el historial como está y documentarlo | Cumplir desde ahora; ADR-0005 explica el porqué del historial antiguo | Nulo. Quedan 46 commits con autor Claude |
| b. Reescribir solo la rama del PR #3 (21 commits) | `rebase` cambiando autor y quitando trailers; force-push **a la rama** (no a `main`) | Bajo. Cambian los SHA: hay que actualizar las referencias de procedencia (el `--id` de binarios y los `meta.json` de EXP-006 y EXP-007) con una tabla de correspondencia |
| c. Reescribir también `main` (46 commits) | `filter-repo` sobre todo el historial y **force-push a `main`** | **Alto e irreversible**: cambian todos los SHA de `main`; se rompen las referencias de los PR #1 y #2, de los ADR y de los `meta.json` de EXP-001–005. Cualquier clon existente queda desfasado |

- **Recomendación**: **b ahora y a para `main`**.
  - La rama del PR #3 todavía no está fusionada y reescribirla es barato. La
    procedencia se conserva con una tabla SHA antiguo → nuevo en
    `docs/decisiones/D-001-correspondencia-sha.md`.
  - Para `main`, reescribir rompe la trazabilidad de cinco experimentos. Es mejor
    dejarlo documentado.
  - La opción c solo si el director la pide expresamente, sabiendo lo que
    implica.
- **Resolución (2026-09-23, director): opción b.**
  - Se reescribieron los 25 commits de la rama del PR #3 (21 con autoría de
    Claude). Autor y committer pasan a ser el desarrollador y se quitaron los
    trailers de atribución.
  - Árbol, fechas y mensajes se conservan; los detalles están en
    [`D-001-correspondencia-sha.md`](D-001-correspondencia-sha.md).
  - Force-push **solo** a la rama del PR, no a `main`.
  - Los 25 commits antiguos de `main` (épocas de los PR #1 y #2) quedan como
    están, documentados en la ADR-0005.

## D-011 — Plugin «engineering» del catálogo de claude.ai

- **Contexto**: el catálogo ofrece el plugin `engineering` de Anthropic, con
  skills de arquitectura (ADR), documentación, estrategia de tests, deuda
  técnica y revisión de código. Hoy no está activado.
- **Recomendación**: activarlo es opcional. Las skills que ya vienen con Claude
  Code (`code-review`, `security-review`, `simplify`, `session-start-hook`)
  cubren lo esencial. Aportaría plantillas para ADR y documentación.
- **Coste**: ninguno. Es una decisión de configuración de la cuenta del
  director.

## D-012 — Insignia «via Claude» en las acciones de GitHub

- **Surge**: el 2026-09-23, al crear los primeros issues.
- **Contexto**:
  - Los issues y PR creados desde la sesión figuran con autor `abelponce03`.
  - GitHub añade la insignia «via Claude»: la integración usa la GitHub App
    oficial de Claude (`performed_via_github_app`). No se puede quitar desde la
    sesión.
  - Los commits sí cumplen del todo la ADR-0005.
- **Opciones**:
  - **a.** Aceptarla como metadato técnico. No es coautoría y es coherente con
    la transparencia de `docs/metodologia/`.
  - **b.** Que el director haga todas las acciones de autoría en GitHub.
  - **c.** Mixto: la sesión gestiona issues y CI, y el director abre y fusiona
    los PR.
- **Recomendación**: a o c.
- **Agenda**: Reunión 1 (issue #4).

## D-002 y D-003 — Aplazamiento del correo a los organizadores

- **Decisión del director (2026-09-23)**: el correo se envía **cuando esté
  definido el conjunto final de mejoras de LabeSAT**, porque las cifras que
  declara (líneas cambiadas, qué va activado, cliques sí o no) todavía van a
  cambiar.
- **Texto y cifras a recalcular**: [`borrador-correo-organizadores.md`](borrador-correo-organizadores.md).
- **Riesgo anotado y fecha límite recomendada, el 1 de febrero de 2027**:
  - La respuesta decide si se apunta a la categoría regular, lo que puede
    exigir reescribir código a mano o cambiar la declaración.
  - Los 20 benchmarks se entregan con el registro (en 2026, el 19 de abril).
- **Mientras tanto**: se sigue planificando con el caso base de
  `research/04` §1, es decir, la subcategoría IA con declaración honesta.
  D-003 tiene riesgo bajo por los precedentes, y la tubería no cambia.
- **Nota técnica**: el conector de Gmail de la sesión no tenía permiso de
  redacción, así que el borrador no pudo dejarse en Gmail. Si se quiere, se
  reconecta con ese permiso en https://claude.ai/customize/connectors.

## D-013 — Base de Kissat: 4.0.4 o sc2026

- **Hechos**:
  - Kissat 4.0.4 es la última versión publicada y el master de GitHub
    (`8af8e56`), y también la base del ganador de 2026 (satsuma + 4.0.4).
  - Biere compitió en 2026 con **«sc2026»**, una versión posterior sin publicar,
    con licencia MIT, disponible en los paquetes de la competición. Cambia 64
    ficheros (~1229 líneas de diff). Entre otras cosas: elimina `fastel` y los
    niveles de glue, y cambia de modo focused/stable **guiado por conflictos**.
  - Sola, quedó 16.ª (PAR-2 4612).
  - Hoy no se sabe si sc2026 es mejor que 4.0.4.
- **Cómo se decide**: con EXP-008, un A/B preregistrado de las dos bases,
  intercalado, en calib y calib2.
- **Coste de cambiar**: portar ~105 líneas activas (más el resto si procede) y
  repetir la validación de las pruebas.

## D-014 — Variantes a presentar

- **Regla**: hasta 4 solvers secuenciales por participante.
- **Propuesta**:
  - **V1** = la mejor combinación validada;
  - **V2** = sin ruptura de simetrías, como cobertura frente a un conjunto de
    2027 con menos simetría o más SAT grandes;
  - V3 y V4 solo si algún experimento las respalda.
- **Coste**: cada variante lleva su propia declaración de IA y consume cómputo
  en la validación final (H8).

## D-005 — Resolución

- **Decisión del director (2026-09-23): opción c**. La búsqueda de clique
  máxima que satsuma toma de cliquer (GPLv2) se reimplementa en MIT.
- **Motivo**: sin cliques, 6 instancias del estrato H pasan de resolverse en
  menos de 2 s a timeout (research/03, segunda parte). La opción c es la única
  que recupera ese efecto sin salir de la directriz «mantén MIT».
- **Reglas de la reimplementación**:
  - **sala limpia**: se implementa a partir de los algoritmos publicados
    (Östergård 2002; Tomita y Seki 2003) y **sin leer el código de cliquer**;
  - de satsuma (MIT) solo se usa su interfaz: la única llamada y los tipos que
    consume `reorder.h`.
- **Validación**: EXP-010, preregistrado, compara la versión MIT frente a la
  versión con cliquer.
