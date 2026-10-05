# EXP-026 — Fase inicial falsa cuando hay ruptura: ¿recupera las SAT que pierde «siempre»? (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con las
  listas de `scripts/research12.py seleccionar`:
  - `results/exp026/simetricas.txt`;
  - `results/exp026/industria.txt`.

  La lista de 2025 tiene su regla fijada aquí y en `research12.py
  seleccionar-2025`, y se escribe cuando exista el escaneo de EXP-023.
  Ninguna ejecución previa: no necesita código nuevo.
- **Fecha**: 2026-10-05
- **Vía**: M1 (research/12 §3).
- **Decide**: si `labesat` añade `--phase=0` cuando satsuma se aplica,
  como candidata para V1 (D-020).

---

## 1. Qué se quiere saber

- El predicado lex-leader de satsuma deja, de cada clase de asignaciones
  simétricas, la que tiene **falsos al principio** del orden.
- Kissat decide con fase inicial **verdadera** hasta que guarda otra.
- En 2026, de las 13 instancias que solo resuelve «nunca», 10 son SAT
  (research/10 §0b).

¿Empezar con fase falsa cuando hay ruptura alinea la búsqueda con los
predicados y recupera esas SAT, sin coste en el resto?

## 2. Hipótesis

> **H1 (primaria, etapa 2a).** En las instancias de 2025 con ruptura,
> ΔPAR-2 (B − A) < 0, con Wilcoxon p < 0,05 y el IC95 % bootstrap entero
> por debajo de 0.
>
> **H2 (no daño, etapa 2b).** En las industriales con ruptura, el extremo
> superior del IC95 % de ΔPAR-2 (B − A) es ≤ +5 s.
>
> **H3 (exploratoria, fijada ahora).** El efecto se concentra en las SAT:
> en las de resultado conocido, «solo B resuelve» > «solo A resuelve»
> entre las SAT.

- A = `labesat --symmetry`;
- B = `labesat --symmetry --phase=0`.

**Predicción honesta**: efecto pequeño en el total. Kissat cambia de fase
muy pronto (*warmup*, objetivo, refaseo), así que la fase inicial solo
decide el principio. Un nulo es plausible.

## 3. Diseño

En dos etapas (research/12 §10).

### Etapa 1 (cribado): symm2026 con ruptura

- 54 instancias con `cambia` = 1 en el escaneo de B4 con mclique v2: 13 SAT
  y 41 UNSAT.

```bash
python3 scripts/run_ab_interleaved.py --solver solver/labesat --bench bench/symm2026 \
    --instances results/exp026/simetricas.txt \
    --out-a results/exp026/A1.csv --out-b results/exp026/B1.csv \
    --label-a A-siempre --label-b B-siempre-fase0 \
    --opts-a=--symmetry --opts-b="--symmetry --phase=0" \
    --env-a "LABESAT_KISSAT=$PWD/solver/kissat/build-m/kissat" \
    --env-b "LABESAT_KISSAT=$PWD/solver/kissat/build-m/kissat" \
    --guard solver/kissat/build-m/kissat --guard tools/satsuma-mclique \
    --timeout 300 --seeds 42 --mem-gb 6
python3 scripts/research12.py cribado results/exp026/A1.csv results/exp026/B1.csv \
    > results/exp026/cribado.txt
```

- **Regla**: la de research/12 §10. PASA si ΔPAR-2 < 0 o si el factor de
  velocidad es < 0,97.

### Etapa 2 (solo si pasa)

- **2a. Instancias frescas de 2025 con ruptura.** Hasta 60, de
  `research12.py seleccionar-2025`: `cambia` = 1 en
  `results/exp023/satsuma.csv`, cuota por familia y orden de
  `md5(hash + sal)`. Son instancias que nada de LabeSAT se diseñó mirando.
- **2b. Industria con ruptura.** 40 de tesis-dev, estratos fácil, media e
  inestable, con `cambia` = 1 (`results/exp026/industria.txt`).
- **Comando**: el mismo con `--bench bench/sc2025` y la lista
  `results/exp026/sc2025.txt` (salidas `A2a/B2a`), y con `--bench
  bench/tesis-dev` y `results/exp026/industria.txt` (salidas `A2b/B2b`).
  Después, `research12.py confirmacion` sobre cada pareja.
- **Una semilla** (42) en las dos etapas, como EXP-014: la desviación de
  ADR-0003 §3.2 se declara. La instancia es la unidad de análisis.
- **Binario**: `build-m` en las dos ramas (con las opciones de research/12
  apagadas, hace la misma búsqueda que el adoptado; research/12 §11). Así
  no se toca `build/`, que vigila EXP-023.
- **Coste**:
  - etapa 1: ≤ 54 × 2 × 300 s = 9 h; se esperan ~3 h, porque las H con
    ruptura caen en segundos;
  - etapa 2: ≤ 100 × 2 × 300 s = 17 h; se esperan ~6 h.

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| No pasa el cribado | Se cierra sin señal; la fase inicial no estorba a la ruptura en este banco |
| H1 y H2 se cumplen | `labesat` y el binario integrado añaden `--phase=0` cuando satsuma se aplica; candidata para V1, que se valida en H8 |
| H1 sí, H2 no | Solo con un selector de lo combinatorio (B4, regla R): se anota para cuando EXP-023 decida B4 |
| H1 no | Se cierra; H3 se informa como descriptiva |

## 5. Amenazas a la validez

- **La etapa 1 usa symm2026**, que también se usó para diseñar B3 y B4. Por
  eso la confirmación es en 2025, con instancias frescas.
- **`--phase=0` también cambia el refaseo «original» e «invertido»**, no
  solo las primeras decisiones. Es lo que se desplegaría, así que se mide
  tal cual.
- **El orden de satsuma no es el de las variables**: la alineación es
  aproximada (research/12 §3). Un nulo no descarta un alineamiento más fino
  (fase falsa solo en las variables de los predicados), que exigiría
  modificar satsuma.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
