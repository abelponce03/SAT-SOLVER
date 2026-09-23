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
| D-001 | Commits ya publicados con autoría de Claude | 🟡 | Director | §D-001 |
| D-002 | ¿Subcategoría IA o categoría regular? | 🟡 | Director (+ organizadores) | [research/04 §1](../research/04-decisiones-pendientes.md) |
| D-003 | ¿Se admite la composición satsuma + kissat? | 🟡 (riesgo bajo) | Organizadores | [research/04 §2](../research/04-decisiones-pendientes.md) |
| D-004 | Familia de los 20 benchmarks obligatorios | 🟡 | Director | [research/04 §3](../research/04-decisiones-pendientes.md) |
| D-005 | ¿MIT o cliques (GPL)? | ⏸️ esperando a EXP-007 | Director | [research/04 §4](../research/04-decisiones-pendientes.md), [research/03](../research/03-coste-de-mantener-mit.md) |
| D-006 | Acceso a un clúster | ✅ no hay (2026-09-23) | Director | ROADMAP §4 |
| D-007 | Nombre del solver | ✅ LabeSAT (2026-09-22) | Director | CHANGELOG |
| D-008 | Ruptura de simetrías como programa externo, en MIT | ✅ (2026-09-23) | Director | [ADR-0004](../adr/0004-ruptura-de-simetrias-con-satsuma-externo.md) |
| D-009 | Autoría: solo el desarrollador en git | ✅ (2026-09-23) | Director | [ADR-0005](../adr/0005-gobernanza-autoria-y-decisiones.md) |
| D-010 | Documentación continua y multiformato, con LaTeX para los PDF | ✅ (2026-09-23) | Director | [ADR-0006](../adr/0006-documentacion-multiformato.md) |
| D-011 | Instalar el plugin «engineering» del catálogo | 🟡 (menor) | Director | §D-011 |

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
- **Mientras tanto**: no se reescribe nada. Es una operación destructiva y
  necesita confirmación (CLAUDE.md §3).

## D-011 — Plugin «engineering» del catálogo de claude.ai

- **Contexto**: el catálogo ofrece el plugin `engineering` de Anthropic, con
  skills de arquitectura (ADR), documentación, estrategia de tests, deuda
  técnica y revisión de código. Hoy no está activado.
- **Recomendación**: activarlo es opcional. Las skills que ya vienen con Claude
  Code (`code-review`, `security-review`, `simplify`, `session-start-hook`)
  cubren lo esencial. Aportaría plantillas para ADR y documentación.
- **Coste**: ninguno. Es una decisión de configuración de la cuenta del
  director.
