# ADR-0006 — Documentación continua y multiformato, con fuentes editables

- **Estado**: aceptado
- **Fecha**: 2026-09-23
- **Decide**: Abel Ponce (directrices del 2026-09-23)

## Contexto

- El proyecto tiene que terminar con entregables impecables:
  - el solver;
  - la descripción del sistema para la competición;
  - la descripción de los benchmarks;
  - el manual de usuario;
  - uno o más artículos;
  - material de apoyo (presentaciones, figuras).
- Si la documentación se deja para el final, se reconstruye de memoria y sale
  peor.
- El director pide:
  - documentar **desde el principio**;
  - gestionar la documentación para el usuario (manuales, material
    multiformato);
  - usar formatos **fáciles de editar**, con **LaTeX para los PDF**.

## Decisión

### 1. Formato según el tipo de documento

| Tipo | Formato fuente | Salida | Por qué |
|---|---|---|---|
| Documentación del repositorio (ADR, experimentos, investigación, registro de decisiones, metodología) | **Markdown** | Se lee en GitHub | Se ve en el navegador, se revisa en los diff y cualquiera la edita |
| Manual de usuario | **LaTeX** (`docs/manual/`) | PDF | Documento largo, con índice, referencias cruzadas y buena tipografía |
| Descripción del solver para la competición | **LaTeX, IEEEtran** (`docs/competicion/`) | PDF de 1–2 páginas | Formato exigido: «IEEE Proceedings style, PDF» |
| Descripción de los benchmarks | **LaTeX, IEEEtran** (`docs/competicion/`) | PDF | Mismo formato que las descripciones de los proceedings |
| Artículos | **LaTeX** (`docs/paper/`), con la plantilla de cada revista o congreso | PDF | Estándar del área |
| Presentaciones | **LaTeX Beamer** (`docs/presentaciones/`) | PDF | Editable, versionable y comparte macros y figuras con los artículos |
| Referencia de la herramienta | **Página man** (`docs/man/labesat.1`, roff) | `man labesat` | Formato estándar de la línea de órdenes Unix |
| Figuras | Script Python que genera PDF/SVG a partir de `results/` | PDF (LaTeX) y SVG (Markdown) | Reproducibles: una figura se regenera, no se retoca a mano |
| Datos tabulares | CSV | — | Se versiona y cualquier herramienta lo abre |

- `.docx` y `.pptx` **solo** si alguien los pide expresamente, y siempre
  generados desde la fuente LaTeX o Markdown, nunca editados como fuente.
- Los PDF **no se versionan**: los compila CI (trabajo `documentacion`) y quedan
  como artefactos descargables del workflow. En cada entrega (registro, envío)
  se adjuntan a la release correspondiente.

### 2. Documentación continua

- **Regla del mismo PR**: cada PR actualiza lo que su cambio afecta:
  - `CHANGELOG.md`, siempre;
  - el manual o la página man, si el usuario ve el cambio;
  - un ADR, si hay decisión;
  - `EXP-NNN`, si hay medición.

  La plantilla de PR lo pregunta.
- `docs/README.md` es el **índice** de toda la documentación y dice en qué
  estado está cada entregable.
- `CITATION.cff` para que el software sea citable.
- `THIRD_PARTY_NOTICES.md` con las licencias de todo lo que se usa o se
  distribuye.

### 3. Estado inicial (2026-09-23)

- Esqueletos con contenido real:
  - manual de usuario (LaTeX);
  - descripción del solver para la competición (IEEEtran);
  - página man.
- CI los compila.
- El resto (artículo, Beamer, descripción de benchmarks) se abre como issues en
  el hito correspondiente del ROADMAP.

## Alternativas consideradas

| Alternativa | Por qué no |
|---|---|
| Todo en Markdown y PDF con pandoc | Da menos control tipográfico. La competición exige IEEE, y los artículos, plantillas LaTeX |
| Word/Google Docs para el manual | Difícil de versionar y de revisar en los diff; contradice la directriz |
| Versionar los PDF | Engordan el repositorio y se desincronizan de la fuente |
| Sphinx/MkDocs como web de documentación | Útil más adelante si hay usuarios externos; hoy añade infraestructura sin beneficio |

## Consecuencias

- **Positivas**:
  - los entregables crecen con el proyecto;
  - al final solo se revisan, no se escriben;
  - todo es editable con herramientas estándar.
- **Coste**: CI necesita TeX Live, lo que añade unos minutos al workflow. Se
  resuelve en un trabajo aparte que solo corre si cambia `docs/`.
- **Riesgo**: que la regla del mismo PR se relaje. Para evitarlo, la plantilla
  de PR lleva la casilla y la revisión la comprueba.
