# ADR-0002 — Estructura del repositorio y estrategia de vendorizado del upstream

- **Estado**: aceptado
- **Fecha**: 2026-09-21
- **Decide**: Abel Ponce

## Contexto

Tras ADR-0001 hay que decidir **cómo vive el código de Kissat dentro del
repositorio**. Un solver de competición se entrega como un árbol de fuentes
autocontenido que compila con `./configure && make` (requisito de la SAT
Competition: el organizador construye el binario dentro de un contenedor sin
red). A la vez queremos poder (a) traer correcciones de upstream, (b) ver
nuestro *diff* contra upstream en cualquier momento, y (c) que el repositorio
sea clonable sin pasos extra.

La estructura previa (`competition/cadical/…`) anidaba todo bajo un directorio
`competition/` que no aportaba información: **todo** el repositorio es el
proyecto de competición.

## Decisión

1. **Layout plano y por función** en la raíz del repositorio:

   ```
   solver/kissat/   fork de Kissat (vendorizado vía git subtree)
   scripts/         harness: build, runner, PAR-2, descarga de instancias
   bench/           instancias (muestra versionada + suites descargadas, ignoradas)
   results/         CSV de corridas (solo los de referencia se versionan)
   docs/adr/        registros de decisión (este documento)
   docs/research/   notas de investigación vivas
   docs/experiments/ protocolo y bitácora de cada experimento A/B
   docs/paper/      material destinado a artículos
   docs/archive/    material histórico (etapa CaDiCaL)
   ```

2. **Vendorizado con `git subtree`**, no submódulo ni copia opaca:
   - el árbol completo está en el repositorio → clona y compila, sin `--recursive`;
   - `git subtree pull --prefix=solver/kissat kissat-upstream master` trae
     upstream cuando haga falta;
   - `solver/kissat/UPSTREAM.md` fija commit, versión y fecha del punto base.

3. **Regla de higiene del diff**: todo cambio nuestro sobre el código de Kissat
   va marcado con un comentario `/* [SOLVER] ... */` y, cuando es una feature,
   detrás de una opción de Kissat (`option()`), de modo que el A/B se haga con
   el *mismo binario* activando/desactivando la opción. Esto elimina el sesgo
   de compilación entre las ramas A y B de un experimento.

## Alternativas consideradas

| Alternativa | Pros | Contras | Por qué no |
|---|---|---|---|
| Submódulo git | diff limpio contra upstream | requiere `--recursive`; los parches viven fuera del repo o en una rama aparte; frágil para entrega | La entrega debe ser autocontenida |
| Copia plana sin historial | simple | imposible sincronizar con upstream; no se ve qué es nuestro | Pierde trazabilidad |
| Parches (`*.patch`) aplicados en build | diff explícito | build no reproducible sin red; doloroso al crecer | Escala mal |
| **git subtree (elegida)** | autocontenido + sincronizable + historial de upstream preservado | historial algo más ruidoso | — |

## Consecuencias

- El repositorio se puede empaquetar tal cual para el *starexec*/contenedor de
  la competición.
- `git diff <base-commit> -- solver/kissat` da en todo momento **nuestra
  contribución exacta**, que es el artefacto que pide la descripción de solver
  de la competición.
- Obliga a disciplina: features detrás de opciones, no `#ifdef` dispersos.

## Criterios de reversión

Si upstream se bifurca tanto que los `subtree pull` generen conflictos
sistemáticos, se congela el punto base y se documenta como *hard fork*.
