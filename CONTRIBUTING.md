# Cómo se trabaja en este repositorio

Proyecto de un solo autor, pero con disciplina de proyecto serio: el objetivo
final es una entrada a la **SAT Competition 2027** y uno o más artículos. Eso
impone que cada número publicado sea reproducible y que cada decisión esté
escrita en el momento en que se toma, no reconstruida después.

## 1. Las tres reglas que no se saltan

1. **Nada que toque el solver se fusiona sin A/B.** `scripts/smoke_test.sh` en
   verde y una tabla de `par2.py` en el PR.
2. **Toda feature de búsqueda vive detrás de una opción de Kissat**, apagada por
   defecto hasta que un experimento la valide (ADR-0002 §3). Así el A/B usa
   **un solo binario** y no hay sesgo de compilación entre A y B.
3. **El diseño del experimento se escribe antes de correrlo** y el resultado se
   documenta aunque sea negativo (ADR-0003 §6). El registro de ideas que no
   funcionaron es la parte más valiosa del historial.

## 2. Flujo de una idea, de principio a fin

```
issue [IDEA]  ->  docs/research/NN-*.md   (¿está hecho ya? ¿qué dice la literatura?)
              ->  docs/experiments/EXP-NNN-*.md  (hipótesis + criterio de éxito, ANTES)
              ->  rama  exp/NNN-nombre-corto
              ->  implementación detrás de una opción
              ->  cribado barato: --conflicts (determinista) sobre bench/dev
              ->  A/B con tiempo sobre bench/dev, >=3 seeds
              ->  si sobrevive: validación única sobre bench/test
              ->  PR con la tabla de par2.py  ->  CHANGELOG  ->  merge
```

Si el cribado barato ya dice que no, se cierra ahí y se escribe el resultado
negativo en el documento del experimento. Coste: media hora. Es la parte que
evita perder semanas.

## 3. Ramas y commits

- Ramas: `exp/NNN-descripcion` (experimentos), `feat/…`, `fix/…`, `docs/…`,
  `chore/…`. La rama de trabajo asistido es `claude/…`.
- Commits: [Conventional Commits](https://www.conventionalcommits.org/).
  Ámbitos habituales: `solver`, `harness`, `bench`, `adr`, `exp`, `docs`, `ci`.
  Ejemplo: `feat(solver): bandit UCB en la decisión de rephase (EXP-004)`.
- El cuerpo del commit explica **por qué**, no qué (el diff ya dice qué). Si el
  commit nace de una medición, el número va en el cuerpo.
- **Autoría** (ADR-0005): los commits llevan solo la identidad del
  desarrollador, `Abel Ponce <abelponce03@gmail.com>`.
  - Sin `Co-Authored-By` de herramientas de IA, sin «Generated with…» y sin
    enlaces de sesión, ni en los commits ni en los PR.
  - `scripts/check_authorship.sh` lo comprueba y CI lo ejecuta.
  - El uso de IA se declara en `docs/metodologia/`, no en git.
- **Decisiones abiertas** (ADR-0005 §2): lo que el levantamiento de requisitos
  no cubre se registra en `docs/decisiones/registro.md` y se agenda en un issue
  con la etiqueta `decisión`. Mientras tanto, se sigue con la opción reversible.
- **Documentación en el mismo PR** (ADR-0006): CHANGELOG, manual o man, ADR y
  bitácora, según lo que toque el cambio.

## 4. Código dentro de `solver/kissat/`

Es código de terceros (MIT, Armin Biere). Reglas:

- Marca cada cambio nuestro: `/* [SOLVER] motivo — ver ADR-000N / EXP-NNN */`.
- Respeta el estilo de Kissat: C99, `snake_case`, `clang-format` del upstream
  (`solver/kissat/.clang-format` si existe), sin dependencias externas.
- Opciones nuevas en `src/options.h`, con rango y valor por defecto explícitos
  y comentario de una línea. El valor por defecto de una feature no validada
  es **0**.
- Contadores nuevos en `src/statistics.h`, entre los `#ifndef KISSAT_QUIET` que
  corresponda, para que `-s` los imprima y el runner los recoja.
- No reformatees ficheros enteros: ensucia el diff contra upstream, que es
  literalmente el artefacto que se entrega a la competición.

## 5. Antes de hacer push

```bash
./scripts/smoke_test.sh          # build + tests + modelos + DRAT + determinismo
python3 -m compileall -q scripts/
```

Si tocaste el solver, además el cribado por conflictos sobre `bench/dev`.

## 6. Datos y resultados

- Los CSV de corridas **no** se versionan salvo en dos casos: los de referencia
  (sufijo `*.reference.csv`) y los de un **experimento documentado**, que viven
  en `results/<exp-id>/` junto a su `.meta.json`. Sin esos ficheros el documento
  del experimento no se puede auditar, y pesan unos pocos KB.
- Los de experimento están **ignorados por defecto** y se promocionan a mano al
  cerrar el experimento: `git add -f results/<exp-id>/`. Es deliberado: mientras
  una tanda corre, su CSV está a medio escribir, y versionar una corrida
  incompleta mete en el histórico un resultado que nunca existió. Antes de
  promocionar, comprueba que el número de filas es el que esperas
  (`wc -l`: instancias × seeds + 1).
- Las instancias descargadas no se versionan (son gigas y son reproducibles por
  hash desde GBD). Lo que sí se versiona es la **lista de hashes** del banco:
  `bench/dev.list.csv` y `bench/test.list.csv`.
- Un resultado sin `meta.json` (commit, versión, host, opciones) no se usa para
  nada. Es ruido, no evidencia.

## 7. Documentación

| Directorio | Qué va ahí | Cuándo se escribe |
|---|---|---|
| `docs/adr/` | decisiones con consecuencias estructurales | al tomarlas |
| `docs/research/` | estudio de literatura y caracterización | al estudiar |
| `docs/experiments/` | un documento por A/B, con hipótesis y resultado | antes y después de correr |
| `docs/paper/` | material redactado para artículos | continuo |
| `docs/archive/` | material de etapas abandonadas | al abandonarlas |

La documentación del artículo se escribe **en paralelo**, no al final: cada
experimento cerrado aporta ya su párrafo de método y su tabla.
