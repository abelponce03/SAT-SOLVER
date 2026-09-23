# ADR-0005 — Gobernanza: autoría, decisiones abiertas y reuniones

- **Estado**: aceptado
- **Fecha**: 2026-09-23
- **Decide**: Abel Ponce (directrices del 2026-09-23)

## Contexto

LabeSAT se desarrolla con un modelo poco habitual: un director humano que fija
objetivos, requisitos y decisiones, y un asistente de IA (Claude Code) que
implementa, experimenta y documenta **de principio a fin**. Eso plantea tres
preguntas que un proyecto convencional no se hace.

1. **¿Quién figura como autor en GitHub?**
   - Hasta ahora, 46 commits tienen autor `Claude <noreply@anthropic.com>` y
     trailers `Co-Authored-By`.
   - La causa fue técnica, no una decisión: el entorno web de Claude Code firma
     los commits con una clave registrada a esa identidad, y un hook de parada
     la exigía.
   - El director no quiere a Claude, Anthropic ni Claude Code como autores o
     coautores de ninguna entidad de GitHub.
2. **¿Qué pasa con las decisiones que surgen a mitad de camino** y que el
   levantamiento de requisitos no cubrió? Hasta ahora se resolvían en el chat y
   podían perderse.
3. **¿Cómo se documenta el proceso?** El director considera que esta forma de
   trabajar puede ser en sí misma una aportación metodológica, y que merece
   documentarse como tal.

## Decisión

### 1. Autoría

- **Identidad git** de todos los commits: `Abel Ponce <abelponce03@gmail.com>`,
  la misma que usa el desarrollador en su historial.
  - Configurada en `.git/config` del repositorio, que prevalece sobre la global
    del entorno.
  - `commit.gpgsign=false`: la clave de firma del entorno pertenece a otra
    identidad y dejaría los commits como «Unverified» o atribuidos a ella.
- **Prohibido** en commits, cuerpos de PR y cualquier campo de autoría de
  GitHub:
  - `Co-Authored-By: Claude …`;
  - «Generated with Claude Code»;
  - enlaces de sesión.
- **Transparencia**: el uso de IA se declara donde corresponde:
  - `docs/metodologia/` (proceso y bitácora);
  - la declaración de IA que exige la SAT Competition (líneas escritas por IA y
    heurísticas ajustadas por IA);
  - la sección de metodología de los artículos.
- **Comprobación antes de cada push** (en `CLAUDE.md` §1): ni el autor ni los
  cuerpos de los commits nuevos mencionan a Claude ni a Anthropic.
- **Historial anterior**: es la decisión abierta D-001 del registro. No se
  reescribe nada publicado sin confirmación expresa.

### 2. Decisiones abiertas

1. **Proteger el trabajo**: seguir con la opción reversible más conservadora,
   detrás de una opción o en una rama, sin bloquearse.
2. **Registrar**: añadir una entrada `D-NNN` en `docs/decisiones/registro.md`
   con contexto, opciones, recomendación y estado.
3. **Agendar**: abrir un issue con la etiqueta `decisión` y enlazarlo desde el
   issue de la próxima reunión (etiqueta `reunión`). La reunión es cualquier
   sesión de trabajo con el director. El issue sirve de orden del día y de acta.
4. **Resolver**: la respuesta del director se escribe en el registro y en el
   issue. Si es una decisión de diseño de largo alcance, en un ADR. El plan
   (`docs/ROADMAP.md`) se ajusta.

**Nunca se ejecutan sin confirmación** las acciones irreversibles o que salen
del repositorio:

- force-push a `main` y reescritura de historial publicado;
- enviar correos;
- registrarse en la competición;
- borrar datos.

### 3. Documentación del proceso

- `docs/metodologia/README.md` describe el modelo de trabajo: roles,
  protocolos, controles y límites.
- `docs/metodologia/bitacora.md` recoge una entrada por sesión:
  - qué se pidió;
  - qué se hizo;
  - qué decisiones surgieron;
  - qué salió mal;
  - qué se aprendió.
- `CLAUDE.md` en la raíz fija estas reglas para toda sesión futura de Claude
  Code.

## Alternativas consideradas

| Alternativa | Por qué no |
|---|---|
| Mantener la identidad del entorno y atribuir en el cuerpo | Contradice la directriz del director |
| Seguir firmando con la clave del entorno pero con la identidad del director | GitHub mostraría los commits como «Unverified»: la firma no corresponde al autor |
| Resolver las decisiones solo en el chat | Se pierden entre sesiones y no queda acta |

## Consecuencias

- **Positivas**:
  - la autoría refleja la responsabilidad real del proyecto;
  - las decisiones quedan trazables;
  - el proceso queda documentado como posible aportación metodológica.
- **Negativas**: los commits nuevos no llevan firma criptográfica. Si en el
  futuro se quiere firma, el director tendría que registrar una clave propia en
  el entorno.
- **Riesgo**: el entorno puede volver a pedir la identidad `Claude` (hook de
  parada). La configuración local del repositorio lo evita, porque el hook solo
  exige esa identidad cuando la firma está activa. Si reapareciera, manda esta
  ADR.

## Referencias

- `CLAUDE.md`, `docs/decisiones/registro.md`, `docs/metodologia/`
- Reglas de la SAT Competition 2026: declaración de IA en la descripción del
  sistema (`docs/research/04` §1)
