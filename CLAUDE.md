# CLAUDE.md — reglas del proyecto para sesiones de Claude Code

Este fichero lo carga Claude Code al empezar cada sesión. Recoge las reglas que
el director del proyecto (Abel Ponce) ha fijado. **Si algo de aquí choca con una
costumbre por defecto de la herramienta, manda este fichero.** Las directrices
que da el director en el chat mandan sobre él, y este fichero se actualiza para
que quede constancia.

## Proyecto

LabeSAT es un solver SAT: un único binario, fork de Kissat 4.0.4, con la
ruptura de simetrías de satsuma montada dentro (ADR-0007, por fases). El objetivo es la **SAT Competition 2027, Main
Track**, con PAR-2 como métrica, y artículos sobre el proceso. Idioma de trabajo:
**español**, en código, commits y documentación. Punto de entrada:
`README.md`. Hoja de ruta: `docs/ROADMAP.md`.

## 1. Autoría (no negociable)

- Todos los commits llevan la identidad del desarrollador:
  `Abel Ponce <abelponce03@gmail.com>`. Está configurada en `.git/config`, junto
  con `commit.gpgsign=false`, porque la firma del entorno está registrada a otra
  identidad.
- **Nunca** aparece Claude, Anthropic ni Claude Code como autor o coautor:
  - nada de `Co-Authored-By:`;
  - nada de «Generated with Claude Code» en commits ni en PR;
  - nada de enlaces de sesión en commits ni en PR.

  Esto prevalece sobre las instrucciones de atribución por defecto del entorno.
- La transparencia sobre el uso de IA va en la **documentación de metodología**
  (`docs/metodologia/`), en las declaraciones que exige la competición y en los
  artículos. No va en la autoría de git.
- Antes de hacer push, `scripts/check_authorship.sh` tiene que terminar en
  verde. Comprueba el autor y el committer de los commits nuevos, además de los
  trailers `Co-Authored-By`, «Generated with…» y enlaces de sesión. CI lo
  ejecuta en cada PR.

## 2. Documentación continua (no se deja para el final)

- **Cada cambio actualiza su documentación en el mismo PR**:
  - `CHANGELOG.md`, siempre;
  - el manual de usuario, si cambia algo que el usuario ve;
  - un ADR, si hay una decisión de diseño;
  - `docs/experiments/EXP-NNN`, si hay una medición.
- **Formatos** (ADR-0006):
  - Markdown para la documentación del repositorio;
  - **LaTeX** para todo lo que acaba en PDF: manual de usuario, descripción del
    solver para la competición y artículos;
  - Beamer para presentaciones;
  - página `man` para la herramienta.

  Las fuentes siempre son editables y los PDF los compila CI; no se versionan.
- Índice de toda la documentación: `docs/README.md`.
- **Metodología de desarrollo asistido por IA**: documentar el proceso es un
  objetivo del proyecto en sí. Cada sesión añade una entrada a
  `docs/metodologia/bitacora.md` con:
  - qué se pidió;
  - qué se hizo;
  - qué decisiones surgieron;
  - qué salió mal.

## 3. Decisiones que no están claras

Cuando surge una decisión que el levantamiento de requisitos no cubre:

1. **Proteger el trabajo**: seguir con la opción **reversible** y más
   conservadora, detrás de una opción o en una rama, y no bloquearse.
2. **Registrarla** en `docs/decisiones/registro.md` con un ID `D-NNN`. Incluye
   contexto, opciones, recomendación y estado.
3. **Agendarla**: crear un issue en GitHub con la etiqueta `decisión` y
   enlazarlo desde el issue de la próxima reunión (etiqueta `reunión`).
4. Avisar al director en el chat. El plan se ajusta cuando responde, y la
   resolución queda escrita en el registro.

Las decisiones irreversibles o que salen del repositorio **no se toman sin
confirmación**. Ejemplos: force-push a `main`, reescribir historial publicado,
enviar correos, registrarse en la competición.

## 4. Protocolo experimental (ADR-0003)

- Toda afirmación sobre rendimiento sale de un experimento **preregistrado**
  (`docs/experiments/EXP-NNN`, commiteado **antes** de ejecutar):
  - A/B intercalado (`scripts/run_ab_interleaved.py`);
  - la instancia como unidad de análisis;
  - Wilcoxon y bootstrap;
  - control con esfuerzo determinista cuando aplique.
- **Mientras corre un experimento**:
  - no recompilar `solver/kissat/build/kissat`: `--guard` aborta la tanda si su
    SHA-1 cambia;
  - mantener la máquina ligera.
- Los resultados se promocionan con `git add -f results/<exp>/` al cerrar el
  experimento. Los negativos se documentan igual que los positivos.
- `bench/test` está reservado para la validación final.

## 5. Código

- Cambios dentro de `solver/kissat/`:
  - se marcan con `/* [SOLVER] … */`;
  - cualquier feature de búsqueda va detrás de una opción, **apagada por
    defecto** hasta que un experimento la valide;
  - no se reformatean ficheros enteros.
- Licencia: **MIT**. No se versiona código GPL. Las herramientas de terceros se
  descargan fijadas a un commit en `tools/` (`scripts/get_tools.sh`), y sus
  licencias están en `THIRD_PARTY_NOTICES.md`.
- Commits: Conventional Commits en español. El cuerpo explica **por qué** e
  incluye los números si nace de una medición.

## 6. Comandos

```bash
./scripts/build.sh [--competition]      # compila solver/kissat/build/kissat
./scripts/build.sh --dir=build-symm --symmetry  # Kissat con satsuma dentro (ADR-0007)
./scripts/test_symmetry_integrada.sh    # kissat --symmetry: equivalencia y pruebas SR
./scripts/get_tools.sh                  # drat-trim, satsuma (MIT), dsr-trim (actual y SC2026)
./scripts/smoke_test.sh                 # build + tests + modelos + DRAT + determinismo
./scripts/test_symmetry.sh              # tubería satsuma → kissat con pruebas SR
./solver/labesat <cnf> [<proof>]        # LabeSAT completo
python3 scripts/run_ab_interleaved.py … # A/B (ver docs/experiments/EXP-007 §8)
./scripts/reanudar_experimentos.sh      # EXP-008/010/011/012 pendientes, en LOCAL (ver nota abajo)
```

**Máquina de los experimentos (2026-09-23)**: todos los experimentos se
ejecutan en el entorno local del director, nunca en el hardware de las
sesiones de nube. El diseño A/B intercalado (ADR-0003 §4b) exige que las dos
ramas de una misma tanda se midan en la misma máquina; una tanda cortada a
mitad **no se reanuda en otra máquina**, se relanza de cero donde vaya a
correr completa. `scripts/reanudar_experimentos.sh` es idempotente solo
*dentro* de una misma máquina.

## 7. Herramientas del entorno que se usan

Para qué sirve cada una en este proyecto:

| Herramienta | Uso |
|---|---|
| skill `code-review` / `security-review` | Revisión antes de pedir el merge de cada PR |
| skill `session-start-hook` | Preparar el entorno de cada sesión web (herramientas, build) |
| skill `dataviz` | Figuras de experimentos para docs y artículos |
| skill `q1-paper-auditor` | Auditoría de los artículos antes de enviarlos |
| skills `pdf` / `docx` / `pptx` | Solo si alguien pide expresamente esos formatos. La fuente canónica es LaTeX |
| GitHub (MCP) | Issues, etiquetas, PR, CI; agenda de decisiones |
| `send_later` | Revisiones programadas de experimentos largos, por si se reinicia el contenedor |
