# EXP-024 — Topes internos de satsuma: ¿abaratan «siempre» en la industria sin quitar ruptura en lo simétrico? (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con:
  - `scripts/satsuma_topes.sh`, que añade los topes y se pasa a `labesat`
    como `LABESAT_SATSUMA`. No toca `solver/labesat`, que EXP-023 vigila;
  - `--build-args` en `scripts/compare_satsuma_builds.py`.

  Única ejecución previa: la prueba de que los argumentos llegan a satsuma,
  sobre las 4 instancias de juguete de `bench/symm`. Allí la CNF de salida
  es idéntica con y sin topes, y la prueba la acepta `dsr-trim`.
- **Fecha**: 2026-10-05
- **Vía**: M2 (research/12 §3).
- **Decide**: si `labesat` y el binario integrado pasan los topes de
  `zheng` a satsuma por defecto. Afecta a la V1 de D-020.

---

## 1. Qué se quiere saber

- `zheng_kissat-mab-hypre` (puestos 3.º a 6.º de 2026) llama a satsuma con
  tres topes internos:
  - `--component-limit 500000`;
  - `--order-model-limit 750000`;
  - `--dense-model-limit 20000000`.
- Nosotros, como el ganador, no ponemos ninguno; solo 60 s y 512 MiB.
- En la industria, «siempre» cuesta casi solo el tiempo fijo de satsuma
  (EXP-014 §8.3). En station-repacking son 39 s de mediana, casi todo en la
  fase de Schreier.

¿Recortan esos topes el tiempo de satsuma en la industria, y a cambio de
qué ruptura en las instancias combinatorias?

## 2. Hipótesis

> **H1 (descriptiva, parte 1).** Por banco y familia:
> - fracción de instancias con la CNF de salida idéntica (mismo SHA-1) con
>   y sin topes;
> - suma y mediana del tiempo de satsuma de cada configuración;
> - instancias que pasan de `TOPE` a terminar, o al revés.
>
> **H2 (coste, parte 1).** En tesis-dev, la suma del tiempo de satsuma con
> topes es ≤ 0,8 × la suma sin ellos.
>
> **H3 (ruptura intacta, parte 1).** En symm2026, estrato H, la CNF de
> salida es idéntica en todas las instancias.
>
> **H4 (efecto, parte 2, solo si se ejecuta).** En las instancias donde la
> CNF cambia, ΔPAR-2 (con topes − sin topes) tiene el extremo superior del
> IC95 % ≤ +5 s.

**Predicción honesta**:

- H3 se cumple: los topes son grandes para las combinatorias, que tienen
  pocas variables.
- H2 depende de si station-repacking gasta su tiempo en los modelos de
  orden. research/12 §3 no lo sabe. Si es la fase de Schreier, que no
  depende de esos topes, H2 no se cumple.

## 3. Diseño

### Parte 1: satsuma solo, intercalado por instancia

```bash
python3 scripts/compare_satsuma_builds.py --bench bench/tesis-dev bench/symm2026 \
    --build base=tools/satsuma-mclique --build topes=tools/satsuma-mclique \
    --build-args "topes=--component-limit 500000 --order-model-limit 750000 --dense-model-limit 20000000" \
    --timeout 60 --mem-gb 6 --out results/exp024/satsuma.csv --resume
python3 scripts/exp024.py analizar > results/exp024/informe.md
```

- Mismo binario (`tools/satsuma-mclique`, el de `labesat`). Las dos
  configuraciones se miden seguidas en cada instancia, para que la deriva
  de la máquina no las separe.
- `out_sha1` es determinista: si coincide, Kissat recibe exactamente la
  misma fórmula y el PAR-2 no puede cambiar en esa instancia.
- **Coste**: unos 534 × 2 × 7 s de media ≈ 2 h; como mucho, 4 h.

### Parte 2: A/B, solo si H2 se cumple

- **Muestra**: las instancias de la parte 1 en las que las dos
  configuraciones terminan y `out_sha1` difiere, más las que cambian de
  `TOPE` a terminar. Si son más de 60, se toman 60 en orden de
  `md5(hash + "exp024")`.

```bash
python3 scripts/exp024.py seleccionar
python3 scripts/run_ab_interleaved.py --solver solver/labesat \
    --bench bench/tesis-dev bench/symm2026 --instances results/exp024/instancias.txt \
    --out-a results/exp024/A.csv --out-b results/exp024/B.csv \
    --label-a A-sin-topes --label-b B-topes \
    --opts-a=--symmetry --opts-b=--symmetry \
    --env-a "LABESAT_KISSAT=$PWD/solver/kissat/build-m/kissat" \
    --env-a "LABESAT_SATSUMA=$PWD/tools/satsuma-mclique" \
    --env-b "LABESAT_KISSAT=$PWD/solver/kissat/build-m/kissat" \
    --env-b "LABESAT_SATSUMA=$PWD/scripts/satsuma_topes.sh" \
    --guard solver/kissat/build-m/kissat --guard tools/satsuma-mclique \
    --guard scripts/satsuma_topes.sh \
    --timeout 300 --seeds 42 --mem-gb 6
python3 scripts/research12.py confirmacion results/exp024/A.csv results/exp024/B.csv
```

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| H2 y H3 se cumplen y H4 también | Los topes pasan a ser el defecto en `labesat` (cuando no corra ninguna tanda que lo vigile) y en el binario integrado (`LABESAT_SYMM_ARGS`); se declaran como heurística (plan §5, P5) |
| H2 no se cumple | Se cierra. Los topes no abaratan lo que cuesta; queda anotado que el coste está en otra fase de satsuma (C4 de research/08) |
| H3 no se cumple | Se mira caso a caso qué ruptura se pierde en H. Si alguna de esas instancias cae de resuelta a no resuelta en la parte 2, se cierra |
| H4 no se cumple | Se cierra: lo que se ahorra en satsuma se pierde en Kissat |

## 5. Amenazas a la validez

- **El reloj de satsuma depende de la carga**; `out_sha1` no. Se ejecuta
  sola en la máquina (cola).
- **Selección de la parte 2 por diferencia de CNF**: es una selección por un
  rasgo previo a la búsqueda, no por el resultado.
- **Los topes de `zheng` se eligieron para su máquina y su banco**. Aquí se
  prueban tal cual, sin ajustarlos: ajustarlos con este banco lo
  sobreajustaría.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
