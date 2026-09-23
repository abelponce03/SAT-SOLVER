# 03 — El coste de mantener MIT: satsuma sin cliques frente a satsuma con cliques

- **Fecha**: 2026-09-23
- **Pregunta** (tarea #5 del ADR-0004): compilar satsuma con `CLIQUES=OFF`
  deja fuera cliquer (GPLv2) y mantiene LabeSAT bajo MIT. ¿Cuánto se pierde?
- **Datos**: `results/satsuma-builds/builds.csv`; script
  `scripts/compare_satsuma_builds.py`. Se usan las 74 instancias de EXP-007.

## Método

Solo se ejecuta satsuma (`fix`, con los mismos argumentos que `solver/labesat`
y un tope de 60 s), sin kissat. Se comparan tres builds:

| build | qué es | licencia |
|---|---|---|
| `mit` | upstream `c6ad1b5`, `CLIQUES=OFF` (`tools/satsuma`) | MIT |
| `cliques` | el mismo commit con `CLIQUES=ON` (cliquer copiado **solo en /tmp**) | GPLv2 por cliquer |
| `ganador2026` | el binario de la entrada ganadora de 2026 | GPLv3 (proyecto) |

La comparación principal es el **SHA-1 de la CNF de salida**. Es determinista:
si dos builds producen la misma CNF, kissat recibe la misma fórmula y el build
no puede cambiar nada en esa instancia.

## Resultados

- Los tres builds terminan con código 0 en las 74 instancias.
- **`cliques` = `ganador2026` en 74/74.** El preprocesado de la entrada ganadora
  es exactamente satsuma upstream con cliques; no tiene nada adicional.
- **`mit` ≠ `cliques` en 8/74**: 7 del estrato H y 1 del estrato N. Ninguna del
  estrato X.

| instancia | estrato | cláusulas originales | salida con cliques | salida MIT |
|---|---|---:|---:|---:|
| 043c9100… | H | 748 640 | **1** (refutada) | 410 537 |
| 0f1070ba… | H | 116 738 | **1** (refutada) | 93 893 |
| 1a3bef9e… | H | 198 762 | **1** (refutada) | 303 996 |
| 6ddda968… | H | 562 074 | **1** (refutada) | 392 022 |
| e5787bb4… | H | 252 490 | **1** (refutada) | 264 756 |
| 65bf849f… | H | 208 955 | 38 808 | 191 315 |
| 9ba8145e… | H | 4 611 150 | 3 489 290 | 3 489 290 (mismo tamaño, contenido distinto) |
| f52a3496… | N | 1 432 755 | 1 833 214 | 1 833 214 (ídem) |

- En **5 de las 45 instancias de H**, cliquer **refuta la fórmula dentro de
  satsuma**: la salida es la cláusula vacía. La versión MIT le pasa a kissat una
  fórmula de 94 000 a 410 000 cláusulas.
- Tiempo de satsuma: media de 3,39 s (MIT) frente a 2,96 s (cliques); mediana de
  0,39 s frente a 0,36 s. **Aviso**: medido con EXP-006 ejecutándose en otro
  núcleo. Sirve como orden de magnitud, no como medida fina.

## Lectura

- El coste de mantener MIT está **acotado y localizado**. En 66 de 74
  instancias, el 89 %, el resultado es idéntico al del ganador. La diferencia
  se concentra en 5 a 7 instancias del estrato H.
- En esas 5 no se sabe todavía si kissat las resuelve igual de rápido sobre la
  salida MIT. Eso lo mide EXP-007: las 8 instancias están en su banco, y ahí la
  rama B usa la salida MIT. Después de EXP-007, y **solo en estas 8**, se
  medirá kissat sobre la salida con cliques para cuantificar la diferencia en
  PAR-2. Si se hiciera antes, se mirarían datos que el A/B todavía no ha
  producido.
- **Consecuencia para la decisión de licencia** (del autor): si EXP-007 muestra
  que kissat recupera esas instancias, mantener MIT sale casi gratis. Si no, el
  coste se puede expresar en instancias concretas, y una reimplementación MIT de
  la búsqueda de cliques que usa satsuma (máxima clique acotada) pasaría a ser
  una tarea candidata.

## Segunda parte: kissat sobre la salida con cliques (2026-09-23, tras EXP-007)

**Diseño**:
- solo las 8 instancias cuya salida difiere;
- `solver/labesat` con satsuma MIT frente a satsuma con cliques;
- el mismo kissat, T = 180 s, orden intercalado.
- Datos: `results/satsuma-builds/cliques_ab.csv`. El binario con cliquer vive
  solo en `/tmp`.

| instancia | estrato | MIT (sin cliques) | con cliques |
|---|---|---|---|
| 043c9100… | H | TIMEOUT | **UNSAT 0,8 s** |
| 0f1070ba… | H | TIMEOUT | **UNSAT 0,2 s** |
| 1a3bef9e… | H | TIMEOUT | **UNSAT 0,4 s** |
| 65bf849f… | H | TIMEOUT | **UNSAT 1,6 s** |
| 6ddda968… | H | TIMEOUT | **UNSAT 0,9 s** |
| e5787bb4… | H | TIMEOUT | **UNSAT 0,5 s** |
| 9ba8145e… | H | UNSAT 18,0 s | UNSAT 19,3 s |
| f52a3496… | N | SAT 37,5 s | SAT 32,5 s |

**Lectura**:

- **Mantener MIT sin cliques cuesta 6 instancias de las 45 del estrato H**, que
  pasan de timeout a resolverse en menos de 2 s. A T = 180 s son unos 358 s
  de PAR-2 por instancia, es decir, unos **−29 s** de PAR-2 medio sobre las 74
  de EXP-007.
- Las 5 que cliquer refutaba dentro de satsuma (§ anterior) están entre ellas.
  Las otras dos instancias que difieren quedan casi iguales.
- **Consecuencia para D-005**: el coste es real. De las opciones de
  `research/04` §4, la **c** (reimplementar la clique máxima en MIT) mantiene
  la directriz del director («mantén MIT») y recupera este efecto. La **b**
  (ejecutable GPL aparte) la recupera sin trabajo, pero introduce GPL en lo que
  se distribuye.
