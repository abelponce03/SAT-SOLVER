# ADR-0001 — Migrar la base del solver de CaDiCaL a Kissat

- **Estado**: aceptado
- **Fecha**: 2026-09-21
- **Decide**: Abel Ponce (autor), con análisis asistido
- **Sustituye a**: la elección implícita de CaDiCaL como base (commits `bef16bf`…`609523c`)

## Contexto

El repositorio nació como *fork de CaDiCaL 3.0.1* con el objetivo de presentar
una entrada a la **Main Track de la SAT Competition 2027**. Tras cinco fases de
caracterización (documentadas en `docs/archive/cadical-era/`), la evidencia
acumulada apunta en contra de esa base:

1. **CaDiCaL pierde sistemáticamente contra Kissat en el régimen de la Main
   Track.** Con el dataset de tesis del autor (4 solvers × 955 instancias de
   aplicación × 3 seeds, timeout 800 s): tasa de resolución `kissat = 0.566` vs
   `cadical = 0.492` (**−7.4 puntos**). Ver
   `docs/archive/cadical-era/03-fase0-datos-tesis.md` §1.
2. **El gap es estructural, no de política de búsqueda.** Se concentra en la
   familia `miter` (+0.285 a favor de Kissat; 37 de las 94 instancias que Kissat
   resuelve y CaDiCaL no). Su causa conocida es *congruence closure* + *SAT
   sweeping*, donde Kissat es la implementación de referencia. Partiendo de
   CaDiCaL, cualquier mejora de búsqueda arrastra ese déficit de base.
   Ver `docs/archive/cadical-era/03-fase0-datos-tesis.md` §2.
3. **La línea ganadora de la competición es Kissat.** Main Sequential 2025:
   1º AE-Kissat-MAB (327), 2º Kissat-public (321), 3º Kissat-VSA (317); el único
   oro de CaDiCaL fue UNSAT. Main Sequential 2026: `satsuma-iter+kissat`. Todas
   las entradas competitivas recientes con mejoras algorítmicas puntuales usan
   **Kissat como host**. Ver `docs/archive/cadical-era/06-estado-del-arte-modificaciones.md` §1.
4. **Comparabilidad científica.** Los competidores directos de las ideas que
   queremos explorar (Kissat_MAB, Kissat-MAB-rephasing, Kissat_MAB_CoRephase,
   AE-Kissat-*) están implementados sobre Kissat. Compartir host hace que un
   A/B contra ellos sea una comparación limpia (misma base, misma ingeniería),
   condición necesaria para publicar.
5. **Ingeniería.** Kissat es C99 puro, monolítico, sin dependencias, con
   `configure && make` y un `src/` de ~50 KLOC muy instrumentable; CaDiCaL es
   C++ con una capa de API externa/incremental que no necesitamos para la Main
   Track.

## Decisión

**Se elimina el fork de CaDiCaL del repositorio y se adopta Kissat `rel-4.0.4`
(commit `8af8e56f174b778aef3aa45af9f739b2a5f492c2`) como única base del
solver.** El código de Kissat se vendoriza bajo `solver/kissat/` mediante
`git subtree`, conservando la capacidad de sincronizar con upstream.

Entra en el alcance: borrar `competition/cadical/`, la instrumentación
`CADICAL_TRACE`, y los scripts atados a la API/salida de CaDiCaL.
No entra: borrar los hallazgos de investigación. Se **archivan** en
`docs/archive/cadical-era/` porque (a) justifican esta decisión y (b) tres de
ellos (inestabilidad por seed, validación de la recompensa GLR, estado del arte)
son independientes del host y siguen siendo la base del plan.

## Alternativas consideradas

| Alternativa | Pros | Contras | Por qué no |
|---|---|---|---|
| **Seguir con CaDiCaL** | 5 fases de trabajo ya hechas sobre esa base; nicho "CaDiCaL como host de bandits" poco explorado | Arranca 7.4 pts por debajo; el gap `miter` es inalcanzable con mejoras de búsqueda; ninguna entrada reciente compite desde ahí | El coste de partir por detrás supera la novedad del host |
| **Portar mejoras de Kissat a CaDiCaL** (ruta CaDiCaL-SC2025) | Mantiene incremental + pruebas | ~3 KLOC de ingeniería pesada dominada por Freiburg; reproduce, no aporta | Fuera de alcance para un autor individual; no es contribución |
| **Escribir un CDCL desde cero** | Control total | Décadas de ingeniería incorporadas en Kissat; PAR-2 no competitivo | Inviable |
| **Kissat como base (elegida)** | Mejor base absoluta; host de los ganadores; C99 instrumentable; comparabilidad con la literatura rival | Pierde incremental/IPASIR maduro y pruebas de CaDiCaL; se descarta la instrumentación ya escrita | — |

## Consecuencias

- **Positivas**: el punto de partida es el estado del arte real; cualquier
  mejora medida se mide *sobre* el mejor solver secuencial disponible, que es
  lo que exige la Main Track. Los A/B contra Kissat_MAB y derivados son
  directos.
- **Coste asumido**: se descartan ~400 líneas de instrumentación
  (`CADICAL_TRACE`) y los baselines medidos sobre CaDiCaL. Hay que reimplementar
  la instrumentación equivalente en Kissat (`kissat/src/`), lo que se estima en
  el mismo orden de esfuerzo (~1 sesión) y se rehará con mejor diseño.
- **Se conserva**: el harness de benchmarking (`scripts/par2.py`,
  `run_baseline.sh`, `fetch_gbd.py`) es agnóstico al solver — solo cambia el
  binario. Los hallazgos de investigación 03/05/06 son agnósticos al host.
- **Riesgos**: (a) el nicho de bandits sobre Kissat está más poblado → la
  contribución debe diferenciarse por **diseño de recompensa** y por **objetivo
  de robustez** (ADR-0003); (b) Kissat es C y su código es más denso que el de
  CaDiCaL → mitigado con instrumentación propia y tests desde el primer día.

## Criterios de reversión

Se revertiría a CaDiCaL solo si (i) la contribución elegida exigiera resolución
incremental o generación de pruebas que Kissat no soporta bien, o (ii) se
midiera que la base Kissat es inestable para nuestro tipo de parche. Ninguna de
las dos condiciones se observa hoy.

## Referencias

- `docs/archive/cadical-era/03-fase0-datos-tesis.md` — datos de tesis, gap por familia, 62 flaky.
- `docs/archive/cadical-era/06-estado-del-arte-modificaciones.md` — resultados SC2025/2026 y taxonomía MAB.
- Kissat: https://github.com/arminbiere/kissat (rel-4.0.4, MIT).
- Biere et al., *CaDiCaL, Gimsatul, IsaSAT and Kissat entering the SAT Competition 2024/2025*.
