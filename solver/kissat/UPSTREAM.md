# Punto base del fork (upstream)

Este árbol es un **fork vendorizado de Kissat**, incorporado con `git subtree`
según el [ADR-0002](../../docs/adr/0002-estructura-repo-y-vendorizado.md).
No editar este fichero a mano salvo al sincronizar.

| campo | valor |
|---|---|
| Upstream | https://github.com/arminbiere/kissat |
| Autor upstream | Armin Biere (Universität Freiburg) |
| Licencia | MIT (ver `LICENSE`) |
| Versión base | **4.0.4** |
| Tag | `rel-4.0.4` |
| Commit | `8af8e56f174b778aef3aa45af9f739b2a5f492c2` |
| Fecha del commit | 2025-10-16 |
| Incorporado el | 2026-09-21 |
| Commit de incorporación | `730056d` (subtree add --squash) |

## Por qué 4.0.4 y no el código de competición

`rel-4.0.4` es el último release estable de upstream y desciende directamente
del código de competición `sc2024` (ver `NEWS.md`, "Version 4.0.0 — source code
matches competition version 'sc2024'"), con correcciones posteriores
(congruence/ITE cuadrático, BVA diferido, orden VMTF tras *factoring*). Es la
base más limpia y más reciente disponible públicamente.

## Ver nuestro diff contra upstream

```bash
git diff c56fd44a712ebd597bab6a40097085d0dcaa76b8 -- solver/kissat
```

Ese diff **es** la contribución del proyecto, y es el artefacto que pide la
descripción de solver de la SAT Competition.

## Sincronizar con upstream

```bash
git remote add kissat-upstream https://github.com/arminbiere/kissat.git   # una vez
git fetch kissat-upstream
git subtree pull --prefix=solver/kissat kissat-upstream <tag> --squash
```

Tras cada sincronización: actualizar la tabla de arriba, ejecutar
`scripts/build.sh` y la suite de no-regresión (`scripts/smoke_test.sh`), y
anotar el cambio en `CHANGELOG.md`.

## Convención para nuestros cambios

Todo código nuestro dentro de este árbol va marcado, para que el diff sea
legible y auditable:

```c
/* [SOLVER] <motivo en una línea, con referencia al ADR o experimento> */
```

y, si es una funcionalidad con efecto en la búsqueda, detrás de una opción
declarada en `src/options.h`, apagada por defecto hasta que un experimento la
valide. Así el A/B se hace con **un solo binario**, activando la opción, lo que
elimina el sesgo de compilación (ADR-0002 §3).
