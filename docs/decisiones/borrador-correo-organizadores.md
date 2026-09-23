# Borrador de correo a los organizadores (D-002 y D-003)

- **Estado**: ⏸️ **aplazado por decisión del director** (2026-09-23). Se envía
  cuando esté definido el conjunto final de mejoras de LabeSAT, para que las
  cifras que declara sean las definitivas.
- **Para**: `organizers@satcompetition.org` (contacto de la web de 2026;
  comprobar la de 2027 al enviar).
- **Quién lo envía**: el director, desde su cuenta. Enviarlo es una acción
  externa y no la hace la sesión.
- **Fecha límite recomendada**: **1 de febrero de 2027**. La respuesta decide
  si se apunta a la categoría regular, y eso puede exigir reescribir código a
  mano o cambiar la declaración. Además, los 20 benchmarks se entregan con el
  registro (en 2026, el 19 de abril). Pasada esa fecha, el margen para
  reaccionar a la respuesta se estrecha.

## Qué hay que actualizar antes de enviarlo

Las cifras marcadas con `⟨…⟩` se recalculan desde git en el momento del envío:

```bash
scripts/declaracion_ia.sh      # todas las cifras, calculadas desde git
```

- ⟨líneas añadidas a Kissat⟩, ⟨de ellas, desactivadas⟩, ⟨líneas del guion⟩.
- ⟨lista de mejoras activas⟩: por ejemplo B3 (activación condicional), si se
  valida.
- ⟨satsuma con o sin cliques⟩, según la decisión D-005.
- Comprobar que el commit de DSRtrim sigue siendo el de la convocatoria de 2027.

## Texto (versión del 2026-09-23)

**Asunto**: SAT Competition 2027: AI-subtrack classification and a
preprocessor + CDCL composition

```
Dear organizers,

I am preparing a Main Track entry, LabeSAT, for SAT Competition 2027. I understand the 2027 call has not been published yet, so I am basing these questions on the 2026 rules. I would like to clarify two points early, because they determine how the entry is built and declared.

1. AI classification

LabeSAT is based on Kissat 4.0.4 (about 38,900 lines of C). Our changes add ⟨390⟩ lines of C to Kissat (⟨1.0⟩%). Only ⟨105⟩ of them are active in the submitted configuration; the other ⟨285⟩ implement a feature that is disabled. We also add a ⟨125⟩-line driver script.

These lines were written by an AI coding assistant (Claude Code) under my direction. The experimental methodology was also AI-assisted: every performance claim comes from a pre-registered A/B experiment. No heuristic parameter was tuned by automated (AI) search.

(a) Would this entry be classified as AI-generated, AI-tuned, or regular?
(b) Is there a threshold, for example a fraction of AI-written lines, that decides the classification?
(c) If the same changes were re-implemented by hand following an AI-assisted design, how should this be declared?

2. Composition with a symmetry-breaking preprocessor

LabeSAT first runs the symmetry-breaking preprocessor satsuma (M. Anders; unmodified, MIT license) and then our Kissat derivative. Kissat continues satsuma's SR proof in the same file. We check the combined proof against the original formula with DSRtrim, including commit 8f857dd, the one listed for 2026. As with several 2025 and 2026 entries (for example, BreakID-Kissat and satsuma-iter-kissat), we understand this is a preprocessor + CDCL pipeline and not a portfolio.

(a) Could you confirm that this composition is admissible in the Main Track?
(b) Will the SR/DSR proof-checking pipeline (DSRtrim/Trestle) again be offered in 2027?

Thank you very much for your time and for organizing the competition.

Best regards,
Abel Ponce
```
