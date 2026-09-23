# Avisos de terceros

LabeSAT se publica bajo licencia MIT (`LICENSE`). Usa o distribuye los
componentes de terceros de esta tabla. Todos se fijan a un commit concreto,
salvo Kissat, que está vendorizado.

| Componente | Uso en LabeSAT | Versión fijada | Licencia | Titulares | Dónde |
|---|---|---|---|---|---|
| **Kissat** | Base del solver (vendorizado y modificado) | 4.0.4, upstream `8af8e56` | MIT | Armin Biere, Mathias Fleury, Florian Pollitt (U. Freiburg); Armin Biere (JKU Linz) | `solver/kissat/LICENSE` |
| **satsuma** | Ruptura de simetrías, programa externo, **sin modificar** | `c6ad1b5`, compilado con `CLIQUES=OFF` | MIT | Markus Anders | `tools/satsuma-src/LICENSE` |
| **dejavu** | Detección de automorfismos, usado por satsuma | `4c275e9` | MIT | Markus Anders | `tools/satsuma-src/src/dejavu/LICENSE` |
| **dsr-trim** | Verificador de pruebas SR/DSR. Solo pruebas y CI, **no se distribuye** | `c3119d8` y `8f857dd` (SC2026) | Apache 2.0 | Cayden R. Codel | `tools/dsr-trim-src/LICENSE` |
| **drat-trim** | Verificador de pruebas DRAT. Solo pruebas y CI, **no se distribuye** | HEAD en la descarga | MIT | Marijn Heule, Nathan Wetzler (UT Austin) | `tools/drat-trim-src/LICENSE` |

## Lo que **no** se usa

- **cliquer** (GPLv2). satsuma lo enlaza solo con `CLIQUES=ON`.
  `scripts/get_tools.sh` compila con `CLIQUES=OFF` y **aborta** si detecta
  cliquer. Motivos en la ADR-0004; coste medido en `docs/research/03`.
- Código de la entrada ganadora de 2026 (proyecto GPLv3). Solo se ha leído su
  interfaz de invocación. `--append-proof` está escrito desde cero a partir de
  Kissat.

## Datos

- Las instancias de benchmark se descargan de la [Global Benchmark
  Database](https://benchmark-database.de) por hash y no se redistribuyen.
  Excepción: los bancos pequeños `bench/smoke` y `bench/symm`, generados en este
  proyecto.
- Las puntuaciones oficiales de la SAT Competition 2026 (`data/competition/`)
  se descargan con `scripts/fetch_competition_data.sh` y no se versionan.
