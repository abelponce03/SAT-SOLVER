# Índice de la documentación

Qué documento hay, en qué formato está y en qué estado se encuentra. Política de
formatos: [ADR-0006](adr/0006-documentacion-multiformato.md). Los PDF los
compila CI (trabajo `documentacion`) y se descargan como artefactos del
workflow.

## Para usuarios

| Documento | Fuente | Formato final | Estado |
|---|---|---|---|
| Manual de usuario | [`manual/manual-usuario.tex`](manual/manual-usuario.tex) | PDF | 🟢 v0: instalación, uso, verificación, reproducción |
| Página de manual `labesat(1)` | [`man/labesat.1`](man/labesat.1) | `man` | 🟢 v0 |
| README | [`../README.md`](../README.md) | Markdown | 🟢 |
| Licencias de terceros | [`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) | Markdown | 🟢 |
| Cómo citar | [`../CITATION.cff`](../CITATION.cff) | CFF | 🟢 |

## Entregables de la SAT Competition

| Documento | Fuente | Formato final | Estado |
|---|---|---|---|
| Descripción del solver (1–2 págs., IEEE) | [`competicion/descripcion-solver.tex`](competicion/descripcion-solver.tex) | PDF | 🟡 borrador; las marcas `PENDING` salen de EXP-007 y D-002 |
| Descripción de los 20 benchmarks | `competicion/descripcion-benchmarks.tex` | PDF | ⚪ pendiente de D-004 |

## Proyecto y decisiones

| Documento | Qué contiene |
|---|---|
| [`ROADMAP.md`](ROADMAP.md) | Fases hasta la SAT Competition 2027 |
| [`plan/plan-main-track-2027.md`](plan/plan-main-track-2027.md) | **Plan vigente**: Main Track con declaración honesta; hitos H1–H11 |
| [`competicion/declaracion-ia.md`](competicion/declaracion-ia.md) | Registro vivo de la declaración de IA (cifras con `scripts/declaracion_ia.sh`) |
| [`adr/`](adr/) | Decisiones de diseño (ADR-0001 a ADR-0008; la 0007 integra la ruptura de simetrías en Kissat; la 0008 hace los experimentos reanudables) |
| [`decisiones/registro.md`](decisiones/registro.md) | Decisiones abiertas y resueltas (D-NNN) |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Cómo se trabaja: flujo, ramas, commits, autoría |
| [`../CHANGELOG.md`](../CHANGELOG.md) | Cambios por hito |
| [`../CLAUDE.md`](../CLAUDE.md) | Reglas para las sesiones de Claude Code |

## Investigación y experimentos

| Documento | Qué contiene |
|---|---|
| [`research/01`](research/01-analisis-empirico-sc2026.md) | Análisis de los resultados oficiales de 2026 |
| [`research/02`](research/02-catalogo-de-ideas.md) | Catálogo de ideas y su estado |
| [`research/03`](research/03-coste-de-mantener-mit.md) | Coste de mantener MIT (satsuma sin cliques) |
| [`research/06`](research/06-razonamiento-xor.md) | Razonamiento XOR / Gauss-Jordan (CryptoMiniSat): estructura XOR medida en 161 instancias, estimación sobre 2026 y veredicto |
| [`research/05`](research/05-enfoques-probabilisticos.md) | Enfoques probabilísticos para SAT: revisión de ~75 trabajos, recomendaciones R1–R3 y descartes por ruido |
| [`research/04`](research/04-decisiones-pendientes.md) | Investigación de las decisiones pendientes del autor |
| [`research/07`](research/07-ganadores-y-banco-tesis.md) | Ganadores 2021–2026 (fuentes primarias), corrección de B2, lo que dice el banco de la tesis y líneas nuevas (VSA, VSIDS/CHB) |
| [`../bench/README.md`](../bench/README.md) | Bancos de instancias, incluido el banco industrial de la tesis y sus particiones |
| [`experiments/`](experiments/) | EXP-001 a EXP-008 y EXP-010 a EXP-015 (EXP-013 a 015, sobre el banco de la tesis): hipótesis antes de medir, resultados después |

## Metodología (desarrollo asistido por IA)

| Documento | Qué contiene |
|---|---|
| [`metodologia/README.md`](metodologia/README.md) | Modelo de trabajo director + asistente de IA, controles y métricas |
| [`metodologia/bitacora.md`](metodologia/bitacora.md) | Una entrada por sesión |

## Artículos y presentaciones

| Documento | Fuente | Estado |
|---|---|---|
| Notas del artículo P1 | [`paper/P1-notas.md`](paper/P1-notas.md) | 🟡 notas; pasa a LaTeX al fijar la revista o el congreso |
| Presentaciones | `presentaciones/` (Beamer) | ⚪ pendiente; la primera, para la reunión de cierre de fase 2 |
