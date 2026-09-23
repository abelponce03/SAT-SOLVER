# D-001 — Tabla de correspondencia de SHA (reescritura de la rama del PR #3)

- **Decisión**: D-001, opción **b**, aprobada por el director el 2026-09-23.
- **Qué se hizo**:
  - Se reescribieron los 25 commits de la rama
    `claude/kissat-migration-sat-solver-ec84qf` que no estaban en `main` (PR #3).
    Los 21 de autor `Claude <noreply@anthropic.com>` pasan a
    `Abel Ponce <abelponce03@gmail.com>`, y se eliminaron los trailers
    `Co-Authored-By: Claude …` y `Claude-Session: …`.
  - Herramienta: `git filter-branch`, con `--env-filter` y `--msg-filter`, solo
    sobre el rango `origin/main..HEAD`. `main` **no se tocó**.
- **Comprobaciones**:
  - el árbol final es idéntico, byte a byte (`git diff` vacío contra la copia de
    seguridad);
  - se conservan las fechas de autor y de committer de todos los commits;
  - los mensajes coinciden con el original salvo las líneas de atribución;
  - `scripts/check_authorship.sh`, sin fecha de corte, pasa en los 25 commits.

## Para qué sirve esta tabla

Algunos registros de procedencia **se capturaron con los SHA antiguos** y no se
modifican, porque son el registro fiel de lo que ocurrió:

- `results/exp006/*.meta.json`: `git_commit` y `solver_id` = `12f871b`;
- `results/exp007/*.meta.json`: `23649fc`;
- el `--id` de los binarios compilados antes de la reescritura.

Para localizar hoy el commit equivalente, se busca el SHA antiguo en esta tabla.
Los dos commits tienen **exactamente el mismo contenido**.

| SHA antiguo | SHA nuevo | Asunto |
|---|---|---|
| `e359229` | `70a4b64` | exp(004): el terminador es neutro — y un "efecto significativo" imposible |
| `0d7e21f` | `02dcc84` | feat: el solver pasa a llamarse LabeSAT |
| `2794bcd` | `4f3af3a` | exp(006): preregistrar la hipótesis de velocidad de A4.1 antes de medirla |
| `12f871b` | `fbc759e` | fix(harness): el A/B intercalado también registra su procedencia |
| `92b7b1c` | `822a389` | docs: hoja de ruta hasta la SAT Competition 2027, y tres reglas que la cambian |
| `03f24f2` | `dc163fa` | feat(solver): --append-proof continúa una prueba ya empezada |
| `36e3b48` | `4a7725e` | build(tools): satsuma, dejavu y dsr-trim fijados a commit en tools/ |
| `21ab11b` | `529cda8` | feat: guion labesat (satsuma → kissat) y su test de punta a punta en CI |
| `a83670d` | `a10e335` | docs(adr-0004): ruptura de simetrías con satsuma externo, todo bajo MIT |
| `16749e9` | `98f7c12` | fix(labesat): truncar el fichero de prueba en vez de borrarlo |
| `0089373` | `ac6ef29` | feat(harness): medir solver/labesat como un solver más |
| `5c5ac02` | `7aab5bf` | exp(007): preregistrar el A/B de ruptura de simetrías antes de medirlo |
| `799957b` | `a428bf1` | feat(exp007): verificación de seguridad de las respuestas con simetrías |
| `12a24ba` | `e319309` | exp(007): banco efectivo tras aplicar el filtro de tamaño preregistrado |
| `1b81d24` | `fd3d72d` | feat(tools): comparar builds de satsuma (MIT sin cliques vs con cliques) |
| `d0c9306` | `ee593cf` | research(03): mantener MIT difiere del ganador de 2026 en 8 de 74 instancias |
| `23649fc` | `7776609` | fix(labesat): no tomar el directorio solver/kissat por el binario |
| `bf9af8f` | `739c5b8` | exp(006): A4.1 no acelera en datos frescos; se cierra sin efecto |
| `caab4ec` | `495fcb2` | docs(paper): A4.1, segundo caso de estudio de un efecto post hoc que no replica |
| `c61a184` | `6f50259` | test(symmetry): verificar también con el dsr-trim exacto de la SAT Competition 2026 |
| `3865c75` | `00ff37b` | research(04): investigación de las decisiones pendientes del autor |
| `4685b1c` | `3fbe7bf` | docs(gobernanza): autoría, decisiones abiertas y documentación continua |
| `9efc63e` | `0d70da9` | docs: manual de usuario, descripción para la competición, página man y CI de documentación |
| `4959355` | `21fc53e` | fix(docs): compilar los LaTeX sin errores ni avisos y enlazar las decisiones con sus issues |
| `77aad69` | `96b8ded` | docs(roadmap): enlazar el plan con las épicas y la agenda de decisiones en GitHub |
