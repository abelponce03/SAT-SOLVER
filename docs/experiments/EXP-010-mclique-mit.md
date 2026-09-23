# EXP-010 — ¿Recupera mclique (clique máxima MIT) lo que aportaba cliquer? (preregistrado)

- **Estado**: **preregistrado**. Se escribe **antes** de ejecutar satsuma con
  mclique sobre el banco (ADR-0003 §6). Las únicas ejecuciones previas son las
  pruebas de corrección: `scripts/test_mclique.sh` y `scripts/test_symmetry.sh`
  sobre `bench/symm` (4 instancias de juguete, que no forman parte del banco).
- **Fecha**: 2026-09-23
- **Decide**: la adopción de mclique (D-005, opción c; issue #9).
- **Numeración**: EXP-009 queda reservado para B3, la activación condicional
  (issue #15).

---

## 1. Contexto

- satsuma usa cliquer (GPLv2) en **una sola llamada**: busca una clique máxima
  en el grafo de co-ocurrencia de las variables de una fila de simetría, y la
  usa para reordenar las columnas antes de romperla (`src/reorder.h`).
- Compilar satsuma sin cliquer (`CLIQUES=OFF`, lo que hoy usa LabeSAT) cambia la
  salida en 8 de las 74 instancias de `bench/symm2026` y **cuesta 6 instancias
  del estrato H**, que pasan de resolverse en menos de 2 s a timeout
  (`docs/research/03`, segunda parte).
- D-005, opción c: **mclique** (`solver/mclique/`, MIT) implementa la clique
  máxima desde los algoritmos publicados (Tomita y Seki 2003; San Segundo et al.
  2011), sin leer el código de cliquer, con la interfaz que usa satsuma.
  `get_tools.sh` compila `tools/satsuma-mclique`: el mismo satsuma `c6ad1b5`
  con `CLIQUES=ON` y mclique en el hueco de cliquer.
- **Qué puede cambiar respecto a cliquer**: cuando hay varias cliques de tamaño
  máximo, cada implementación puede devolver una distinta, y el orden de las
  columnas, los predicados de ruptura y la CNF de salida pueden cambiar. Por eso
  no basta con probar que mclique es correcta: hay que medir el efecto.

## 2. Hipótesis

> **H1 (recuperación, principal).** De las 6 instancias que cliquer recupera
> (R6: `043c9100`, `0f1070ba`, `1a3bef9e`, `65bf849f`, `6ddda968`, `e5787bb4`),
> `labesat --symmetry` con mclique resuelve **al menos 5** en las dos semillas.
>
> **H2 (no daño).** En las instancias donde la salida de mclique difiere de la
> de satsuma sin cliques, mclique **no pierde** ninguna instancia que satsuma
> sin cliques resuelva.
>
> **H3 (seguridad, vinculante).** Todas las respuestas de la rama mclique se
> verifican contra la CNF **original**: los modelos con `verify_model.py` y las
> pruebas UNSAT con los dos dsr-trim (el actual y el de SC2026).
>
> **H4 (coste, descriptiva).** Tiempo de satsuma con mclique frente a sin
> cliques y frente a cliquer.

## 3. Diseño

### Parte 1 — solo satsuma (determinista)

```bash
python3 scripts/compare_satsuma_builds.py --bench bench/symm2026 \
    --build mit=tools/satsuma --build mclique=tools/satsuma-mclique \
    --build cliques=/tmp/satsuma-cliques/build/satsuma \
    --out results/exp010/satsuma.csv
```

- Las 74 instancias de EXP-007 y los tres builds, con el tope de 60 s de
  `labesat`.
- Métrica principal: el **SHA-1 de la CNF de salida**. Si coincide, kissat
  recibe la misma fórmula y no hace falta ejecutarlo.
- Se informa:
  - en cuántas de las 74 coincide `mclique` con `cliques`, y en cuántas con
    `mit`;
  - en cuántas de las 5 que cliquer refuta dentro de satsuma también las
    refuta mclique (salida de una cláusula);
  - los tiempos (H4) y cualquier fallo o tope de 60 s.
- El build con cliquer vive **solo en `/tmp`**, como en `research/03`: no se
  versiona ni se distribuye.
- **Carga concurrente**: la parte 1 se ejecuta mientras corre EXP-008 en otro
  núcleo. Su métrica principal (SHA-1) no depende de la carga. Los tiempos
  (H4) sí, y se declaran como orden de magnitud.

### Parte 2 — kissat sobre las salidas que cambian

- **Instancias**: las de la parte 1 con SHA-1(`mclique`) ≠ SHA-1(`mit`). La
  regla se fija ahora; la lista sale de la parte 1, que no mira ningún
  resultado de kissat. Se guarda en `results/exp010/instancias.txt`.
- **Ramas**, las dos con el mismo kissat y `labesat --symmetry`:
  - A = `LABESAT_SATSUMA=tools/satsuma` (sin cliques, lo actual);
  - B = `LABESAT_SATSUMA=tools/satsuma-mclique`.
- Semillas 1 y 2, T = 180 s, orden intercalado. Se ejecuta **después** de
  EXP-008, con la máquina sin otras tandas.

```bash
python3 scripts/run_ab_interleaved.py --solver solver/labesat \
    --bench bench/symm2026 --instances results/exp010/instancias.txt \
    --opts-a=--symmetry --opts-b=--symmetry \
    --env-a LABESAT_SATSUMA=$PWD/tools/satsuma \
    --env-b LABESAT_SATSUMA=$PWD/tools/satsuma-mclique \
    --guard solver/kissat/build/kissat --guard tools/satsuma \
    --guard tools/satsuma-mclique \
    --out-a results/exp010/A.csv --out-b results/exp010/B.csv \
    --label-a A-sin-cliques --label-b B-mclique --timeout 180 --seeds 1,2
LABESAT_SATSUMA=$PWD/tools/satsuma-mclique python3 scripts/verify_symm_answers.py \
    results/exp010/B.csv --bench bench/symm2026 --out results/exp010/seguridad.csv
```

El análisis de las dos partes lo hace `scripts/analyze_exp010.py`, commiteado
antes de que termine la parte 1; `--write-list` escribe la lista de la parte 2.

## 4. Criterio de decisión, fijado ahora

| resultado | decisión |
|---|---|
| H1 (≥ 5 de 6), H2 (0 pérdidas), H3 (0 fallos) y ningún tope de 60 s nuevo en la parte 1 | **Adoptar mclique**: `labesat` usa `tools/satsuma-mclique` como satsuma por defecto de `--symmetry`. Se actualizan ADR-0004, `THIRD_PARTY_NOTICES.md`, la declaración de IA y el manual. D-005 queda cerrada |
| H3 falla en cualquier instancia | **No adoptar**, y buscar la causa antes de nada (ADR-0004, criterios de reversión) |
| H1 o H2 fallan, con H3 correcta | **No adoptar** todavía. Se documenta qué instancias fallan y se analiza el desempate entre cliques máximas; D-005 vuelve a la próxima reunión |

- **Pérdida** (H2): una instancia que A resuelve en al menos una semilla y B no
  resuelve en ninguna.
- Si en la parte 1 `mclique` coincide con `cliques` en las 8 instancias que
  difieren, la parte 2 reproduce las fórmulas de `research/03` (segunda parte)
  y sirve como replicación con dos semillas.

## 5. Amenazas a la validez

- **Banco pequeño**: la parte 2 solo cubre las instancias cuya salida cambia
  (previsiblemente unas 8). Es lo correcto, porque en las demás la fórmula es
  idéntica, pero H1 y H2 son recuentos, no contrastes con potencia estadística.
- **Sesgo de selección**: R6 se eligió porque cliquer las recupera. H1 pregunta
  exactamente eso («¿recupera mclique lo mismo?»), así que no es un sesgo del
  contraste. Lo que no se mide es si mclique recupera otras que cliquer no.
- **T = 180 s**: igual que en EXP-007.
- **Instancias fuera del banco**: con filas de más de 10 000 variables satsuma
  no usa la clique (usa su heurística de pesos), así que ahí mclique no cambia
  nada.

## 6. Incidencias de ejecución

_Ninguna por ahora._

## 7. Resultados

_Pendiente._
