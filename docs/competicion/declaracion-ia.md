# Declaración de uso de IA (registro vivo)

Base de la sección *Mandatory statement* de la descripción del solver
(`descripcion-solver.tex`) y de la descripción de los benchmarks.
Plan Main Track §5.

## 1. Código

- **Cifras**: siempre desde `scripts/declaracion_ia.sh`. No se copian a mano.
- **Autoría**: el 100 % de las líneas añadidas o cambiadas en LabeSAT (Kissat y
  guion) las escribe un asistente de IA (Claude Code) bajo la dirección del
  autor. El proceso está en `docs/metodologia/`.
- **Código de terceros sin modificar**: satsuma, dejavu y, en verificación,
  dsr-trim y drat-trim. Cuentan como 0 líneas de IA.

## 2. Heurísticas y parámetros ajustados con procesos asistidos por IA

«Ajustado por IA» se interpreta de forma amplia: todo valor elegido a partir de
experimentos que el asistente diseñó, ejecutó o analizó. Ningún valor sale de
una búsqueda automática de parámetros.

| Parámetro / heurística | Valor | Cómo se fijó | Activo en competición |
|---|---|---|---|
| `LABESAT_SYMM_TIMEOUT` (tope de satsuma) | 60 s (provisional) | Elección inicial; se revisa con EXP-007 y EXP-009 | Sí |
| `LABESAT_SYMM_MAXBYTES` (tope de tamaño) | 512 MiB (provisional) | Ídem | Sí |
| B3″: las fases *lucky* ceden al terminador | — | Corrección de comportamiento, no ajuste. Neutral en EXP-004 | Sí |
| A4.1: `modeadaptive`, `modeadaptivedecay`, `modeadaptivegain` | 0 (apagado), 800, 1000 | Diseño asistido; sin efecto en EXP-006 | **No** |
| B3 (activación condicional de simetrías) | — | Pendiente (EXP-009) | — |

## 3. Benchmarks

Se completa en la fase de benchmarks (D-004). Hay que declarar si el
generador de instancias lo escribe el asistente.
