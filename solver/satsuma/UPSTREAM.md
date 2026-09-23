# satsuma y dejavu vendorizados (sin modificar)

- **satsuma** (Markus Anders, MIT): `https://github.com/markusa4/satsuma.git`, commit `c6ad1b59f29fa32dae587ef369135735f40d498a`.
- **dejavu** (Markus Anders, MIT): `https://github.com/markusa4/dejavu.git`, commit `4c275e9ebac4fe51a26aac406682b9bcbfd03a9d`,
  en `src/dejavu/`.
- **tsl robin-map** (Thibaut Goetghebuer-Planchon, MIT): en `src/tsl/`, tal
  como lo trae satsuma.

Copiados por `scripts/vendor_satsuma.sh`. **No se modifica ningún fichero de
este directorio**: CI lo comprueba con `scripts/vendor_satsuma.sh --check`.
Solo se copian las cabeceras, `satsuma.cpp` y las licencias; ni tests, ni
ejemplos, ni ejecutables.

Se compila dentro del binario de Kissat con `configure --symmetry` a través de
`solver/symmetry/satsuma_entry.cpp` (ADR-0007). Sin `--symmetry`, este
directorio no se usa.

cliquer (GPLv2) **no** está aquí: satsuma se compila con `CLIQUES=0`, o con
mclique (`solver/mclique`, MIT) cuando se valide (D-005).
