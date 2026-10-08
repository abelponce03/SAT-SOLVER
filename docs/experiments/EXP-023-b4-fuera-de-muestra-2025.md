# EXP-023 — B4 fuera de muestra: «nunca», «siempre» y el selector estructural en 2025 (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con:
  - `scripts/exp023.py`;
  - la lista `bench/sc2025.list.csv`;
  - la opción `--mem-gb` de `run_ab_interleaved.py`.

  La regla R se fijó antes en research/11 (commit `07d45e6`), sin haber
  visto ningún dato de 2025.
- **Ejecuciones previas**: ninguna sobre estas instancias.
  `scripts/exp023.py` solo se ha probado con datos sintéticos.
- **Fecha**: 2026-10-04
- **Decide**: si B4 pasa a candidata a V1 (D-020) y se implementa en
  `labesat` y en el binario integrado.

---

## 1. Qué se quiere saber

1. **B4** (research/11) ejecuta satsuma siempre, pero solo usa su salida si
   encuentra estructura combinatoria (R). En los datos de diseño conserva la
   ganancia en lo simétrico y evita casi todo el coste en la industria.
   Como R se eligió mirando esos datos, hay que medirlo en instancias
   **frescas**.
2. **Cuánto pierde nuestra «siempre» en un año como 2025.** El 15.º de la
   entrada de satsuma en 2025 era de otra configuración (Kissat 4.0.2,
   prueba VeriPB, satsuma sin tope; research/10 §0c).

## 2. Hipótesis

> **H1 (B4 no cuesta).** En 2025, ΔPAR-2(B4 − «nunca») tiene el extremo
> superior del IC95 % bootstrap ≤ +5 s.
>
> **H2 (B4 mejora a «siempre»).** ΔPAR-2(B4 − «siempre») < 0 y Wilcoxon
> p < 0,05.
>
> **H3 (descriptiva).**
> - En cuántas instancias y familias de 2025 se cumple R.
> - «Siempre» frente a «nunca», con resueltas SAT y UNSAT.

**Predicción honesta**:

- 2025 tiene pocas familias simétricas, así que R se cumplirá en pocas
  instancias.
- H1 dependerá del tiempo de satsuma: es lo que B4 paga cuando no aplica.
  En la industria eran +3 s (research/11).
- H2 es probable si «siempre» cuesta en 2025 lo que en EXP-009.
- «Siempre» frente a «nunca»: se espera que «siempre» pierda, pero menos
  de lo que sugiere el 15.º de 2025.

## 3. Diseño

- **Muestra**: las instancias de la Main Track de 2025 (GBD) cuya CNF sin
  comprimir mide **≤ 512 MiB**: 374 de 400 (`bench/sc2025.list.csv`; 170
  UNSAT, 153 SAT y 51 de resultado desconocido).
  - Las 26 restantes no pasan el tope de tamaño de satsuma, así que en ellas
    las tres políticas son la misma.
  - Se descargan en `bench/sc2025/`, que no se versiona.
- **Binarios**:
  - `solver/kissat/build/kissat`, la configuración adoptada: PGO + LTO, X1 y
    X1s;
  - `tools/satsuma-mclique`.

  Los dos los vigila `--guard`, igual que `solver/labesat`.
- **Paso 1** (`exp023-satsuma`):

  ```bash
  python3 scripts/scan_symmetry.py --bench bench/sc2025 --out results/exp023/satsuma.csv \
      --satsuma tools/satsuma-mclique --timeout 60 --mem-gb 6
  ```

  Da los rasgos, R y el tiempo de satsuma de cada instancia.
- **Paso 2** (`exp023-ab`): A/B intercalado.

  ```bash
  python3 scripts/run_ab_interleaved.py --solver solver/labesat --bench bench/sc2025 \
      --out-a results/exp023/A.csv --out-b results/exp023/B.csv \
      --label-a A-nunca --label-b B-siempre \
      --opts-a=--no-symmetry --opts-b=--symmetry \
      --guard solver/kissat/build/kissat --guard tools/satsuma-mclique --guard solver/labesat \
      --timeout 300 --seeds 42 --mem-gb 6
  ```

- **B4 no es una tercera rama**: se compone instancia a instancia
  (`exp023.py analizar`).
  - Si se cumple R, t(B4) = t(B).
  - Si no, t(B4) = t(A) + min(t_satsuma, 60), donde t_satsuma sale del
    paso 1. La instancia cuenta como no resuelta si A no la resuelve o si se
    pasa de T.
- **Tope de memoria de 6 GB por proceso**, nuevo en el arnés. 2025 tiene
  instancias que en la competición agotaron 30 GB, y la máquina tiene 15.
  Se aplica igual a las dos ramas.
- **Coste**: ≤ 374 × 60 s + 374 × 2 × 300 s ≈ 68 h en el peor caso; unas
  30–40 h esperadas.

## 4. Criterio de decisión

| Resultado | Decisión |
|---|---|
| H1 y H2 | B4 se implementa en `labesat` y en el binario integrado (leyendo los rasgos de satsuma), y pasa a candidata a V1 en D-020 |
| H2 sí, H1 no | B4 mejora a «siempre» pero no protege lo bastante frente a «nunca»: vuelve a D-020 con el dato |
| H2 no | B4 no aporta fuera de muestra: se documenta, y D-020 sigue con V1 «siempre» y V2 «nunca» |

En los tres casos, H3 se lleva a D-020 y a research/10: es lo que valía
nuestra «siempre» en 2025.

## 5. Amenazas a la validez

- **T = 300 s frente a 5000 s** y una sola semilla, como EXP-009.
- **2025 apenas tiene familias simétricas** (research/10 §0c). EXP-023 mide
  sobre todo que B4 **no cuesta**. Lo que gana con simetría solo lo
  respaldan los datos de diseño (research/11 §4).
- **El tiempo de satsuma de B4 sale del paso 1**, no de la misma corrida.
- **El tope de 6 GB**: las instancias que lo agoten fallan en las dos
  ramas. Se informa de cuántas son.
- **Carga ajena** en la máquina del director: el orden intercalado la
  reparte entre las ramas.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
