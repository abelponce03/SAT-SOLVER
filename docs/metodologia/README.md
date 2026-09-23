# Metodología: desarrollo dirigido por una persona y ejecutado por un asistente de IA

Este documento describe **cómo se construye LabeSAT**. Se escribe mientras se
trabaja, no al final, porque el director considera que el modelo de trabajo
puede ser en sí una aportación: un proyecto de investigación y software
competitivo llevado **de principio a fin** con un asistente de IA agéntico
(Claude Code), bajo la dirección de una persona.

Las entradas de cada sesión están en la [bitácora](bitacora.md).

## 1. Roles

| | Director (Abel Ponce) | Asistente (Claude Code, entorno web) |
|---|---|---|
| Objetivo y requisitos | **Los fija** | Los traduce a un plan y avisa de las contradicciones |
| Decisiones de alcance, licencia, ética y reglas | **Decide** | Investiga, presenta opciones y recomienda (`docs/decisiones/`) |
| Diseño técnico | Aprueba o redirige | Propone y lo escribe en ADR |
| Implementación, experimentos, análisis | Supervisa | **Los ejecuta** |
| Documentación | Revisa | **La escribe de forma continua** (ADR-0006) |
| Autoría en git y GitHub | **Único autor** (ADR-0005) | No figura como autor |
| Fusionar PR | **Fusiona** | Prepara el PR y lleva CI a verde |

## 2. Protocolos que hacen fiable el trabajo del asistente

Un asistente que escribe código y mide resultados puede equivocarse de formas
difíciles de ver. Estos controles existen por errores concretos que ocurrieron
(en la bitácora):

1. **Preregistro de experimentos** (ADR-0003). Hipótesis, métrica, contraste y
   criterio de decisión se commitean **antes** de ejecutar.
   - Motivo: dos veces, un efecto encontrado *a posteriori* desapareció en datos
     frescos: B3′ en EXP-003 y A4.1 en EXP-006.
2. **Procedencia verificable**. Cada tanda registra:
   - el SHA-1 del binario y el `--id` (commit);
   - el host, la carga y las opciones;
   - y aborta si un binario vigilado cambia a mitad (`--guard`).
   - Motivo: en EXP-004 una recompilación a mitad de tanda contaminó los datos,
     que se descartaron.
3. **El diseño intercalado A/B** cancela la deriva de la máquina, que es de ~4 %
   entre sesiones (EXP-004).
4. **Controles negativos en los tests**. Un test que no puede fallar no
   demuestra nada. Ejemplo: sin `--append-proof`, la prueba **debe** rechazarse.
5. **Verificación con la herramienta exacta de la competición**. dsr-trim
   `8f857dd`, además de la versión actual.
6. **Resultados negativos documentados** con el mismo cuidado que los positivos.
7. **Decisiones abiertas registradas y agendadas**, nunca resueltas en silencio
   (ADR-0005).

## 3. Qué hace bien el asistente y dónde necesita control

Observaciones, con evidencia en la bitácora:

- **Bien**:
  - volumen de ejecución: implementar, lanzar tandas y analizar en horas lo que
    llevaría días;
  - disciplina documental sostenida;
  - investigación con fuentes primarias (reglas, datos oficiales, código de
    otros participantes).
- **Necesita control**:
  - tiende a encontrar patrones *a posteriori*. El preregistro lo corrige;
  - errores de integración que ningún test cubría: el directorio tomado por
    binario en EXP-007 y la carrera de `pipefail` en un test. Aparecen como
    fallos visibles gracias a los controles del §2;
  - el entorno impone convenciones propias, como la identidad git y la firma,
    que pueden chocar con las del proyecto. Se resolvió explícitamente
    (ADR-0005).

## 4. Transparencia en los entregables

- La **SAT Competition** exige declarar las líneas escritas por IA y las
  heurísticas ajustadas por IA (`docs/research/04` §1). La cifra sale del
  historial de git y de esta metodología.
- Los **artículos** incluirán una sección de metodología basada en este
  documento y en la bitácora.
- La **autoría en git** es solo del director (ADR-0005). La transparencia va
  aquí, no en los metadatos de git.

## 5. Métricas del proceso (se actualizan en cada hito)

| Métrica | Valor a 2026-09-23 |
|---|---|
| Sesiones de trabajo documentadas | 3 (21, 22 y 23 de septiembre de 2026) |
| Experimentos | 7 (EXP-001 a EXP-007): 2 positivos, 4 negativos o nulos, 1 en curso |
| Efectos *post hoc* que no replicaron en preregistro | 2 (B3′, A4.1) |
| Incidencias que invalidaron datos, detectadas por controles | 2 (EXP-004 contaminado; EXP-007, primer lanzamiento) |
| ADR | 6 |
| Líneas añadidas a Kissat 4.0.4 (38 944) | ~460 (277 de A4.1, desactivado) + guion de 125 |
