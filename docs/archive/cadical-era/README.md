# Archivo — etapa CaDiCaL (jul–sep 2026)

Este directorio conserva el trabajo realizado mientras la base del proyecto fue
un fork de **CaDiCaL 3.0.1**. Esa base se abandonó el 2026-09-21 por las razones
del [ADR-0001](../../adr/0001-migracion-cadical-a-kissat.md).

**No es código vivo.** Se conserva por tres motivos: (1) justifica la decisión
de migrar, (2) parte de los hallazgos son independientes del solver y siguen
dirigiendo el plan, y (3) es material de la sección de metodología de futuros
artículos.

## Qué sigue siendo válido tras la migración

| Documento | Hallazgo | ¿Vale para Kissat? |
|---|---|---|
| `03-fase0-datos-tesis.md` | 62 instancias *flaky* por seed; varianza temporal hasta 102×; el gap CaDiCaL–Kissat se concentra en `miter` | **Sí (parcial)**: la inestabilidad por seed se midió sobre CaDiCaL; hay que **re-medirla sobre Kissat** antes de usarla como objetivo. El análisis de familias y el ranking de solvers sí trasladan. |
| `05-fase1-validacion-recompensa.md` | La recompensa útil para un bandit es el **GLR relativo a su EMA**, no el nivel absoluto (que incluso se invierte) | **Sí**: la conclusión es sobre la señal, no sobre el host. Hay que reproducir la validación con trazas de Kissat. |
| `06-estado-del-arte-modificaciones.md` | Estado del arte SC2025/2026, taxonomía de bandits, matriz de decisión | **Sí, íntegro**: es literatura. Es además la principal fuente del ADR-0001. |
| `01-panorama-modificaciones-cadical.md` | Panorama de modificaciones sobre CaDiCaL | **Parcialmente**: la parte de técnicas (congruence, sweeping, gestión de cláusulas) traslada; la de puntos de enganche en el código, no. |
| `02-fase0-caracterizacion.md`, `04-fase05-instrumentacion-trazas.md`, `00-baseline-cadical.md` | Caracterización y baselines medidos **sobre CaDiCaL** | **No**: hay que rehacerlos sobre Kissat. Se conservan como referencia metodológica. |

## `scripts/`

`analyze_trace.py` y `validate_reward.py` leen el formato de traza de la
instrumentación `CADICAL_TRACE`, que ya no existe. Se conservan como
**implementación de referencia** para reescribir el equivalente en Kissat: la
lógica estadística (ventanas, EMA, pendiente del GLR, pruebas V1/V2/V3) es
reutilizable tal cual; solo cambia el parser de entrada.
