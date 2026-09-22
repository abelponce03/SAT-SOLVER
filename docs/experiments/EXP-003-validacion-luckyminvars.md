# EXP-003 — Validación de `luckyminvars` sobre el banco reservado

- **Estado**: diseñado (escrito **antes** de ejecutar, ADR-0003 §6) · en ejecución
- **Fecha de diseño**: 2026-09-22
- **Valida**: la regla B3′ hallada en [EXP-002](EXP-002-fases-lucky.md)
- **Implementación**: opción `luckyminvars` en `solver/kissat/src/options.h` y
  `lucky_worth_trying()` en `src/search.c`

---

## 1. Qué se valida y por qué hace falta

EXP-002 encontró que desactivar las fases *lucky* en fórmulas pequeñas baja el
PAR-2 de 128.248 s a **114.821 s (−10.5 %)** sobre 60 instancias reales.
**Ese número no es publicable**: el umbral (50 000 variables) se eligió
barriendo valores sobre las mismas 60 instancias en las que se midió. Es una
cota optimista, no una estimación.

Este experimento congela la regla y la mide una sola vez sobre un banco que
**nunca se ha tocado**.

## 2. Lo que queda congelado antes de mirar nada

| elemento | valor congelado |
|---|---|
| Regla | saltar las fases lucky si `variables < luckyminvars` |
| Umbral | **`luckyminvars = 50000`** |
| Punto de decisión | recuento de variables del solver en `kissat_search`, antes y después del preprocesado |
| Rama A (control) | binario por defecto (`luckyminvars=0`, idéntico a upstream — verificado: mismos conflictos) |
| Rama B (tratamiento) | mismo binario con `--luckyminvars=50000` |
| Banco | `bench/test`, 60 instancias, **disjunto de `calib` y `calib2`** (assert en `build_dev_set.py`) |
| Presupuesto | T = 180 s (`--time`), una seed |
| Métrica primaria | PAR-2 sobre tiempo de CPU |
| Contraste | Wilcoxon emparejado + IC95 % bootstrap + McNemar (`par2.py`) |

**Un solo binario para las dos ramas**, activando la opción — sin sesgo de
compilación (ADR-0002 §3).

## 3. Criterio de éxito, fijado de antemano

| resultado | decisión |
|---|---|
| ΔPAR-2 < 0 **y** IC95 % excluye el 0 | la regla se valida → se cambia el **valor por defecto** a 50000 y se vuelve a verificar el build de entrega |
| ΔPAR-2 < 0 pero el IC incluye el 0 | sugerente; la opción se queda a 0 por defecto y se anota que hace falta más n |
| ΔPAR-2 ≥ 0 | **la regla no replica**: se documenta el fallo y se retira del catálogo como idea cerrada |

No hay una cuarta salida. Si no replica, se escribe que no replica.

## 4. Composición del banco (mirada antes, es metadato público, no resultado)

60 instancias, 28 familias, 30 SAT / 27 UNSAT / 3 desconocidas, estratificadas
por la dificultad que tuvieron **en la competición**: 11 fáciles (≤60 s),
12 medias (≤600 s), 13 difíciles, **24 que el Kissat de referencia no resolvió
en 5000 s**.

Esas 24 van a agotar el presupuesto en las dos ramas y **diluirán el tamaño del
efecto**: aportan `2T` idéntico a A y a B. Se dejan dentro porque son parte del
banco definido y quitarlas sería elegir la población después de verla. Se
reportará además, **claramente etiquetado como secundario**, el subconjunto que
alguna de las dos ramas resuelve.

## 5. Limitaciones conocidas de antemano

- **n = 60 y una sola seed**: solo se detectan efectos grandes. EXP-002 midió
  −13.4 s sobre 60 instancias; si el efecto real fuese la mitad, este diseño
  probablemente no lo detectaría. Un "no concluyente" aquí **no** será
  evidencia de que la regla no sirve.
- **T = 180 s frente a los 5000 s de la competición.** El peaje de las fases
  lucky es absoluto (segundos), así que pesa relativamente menos con
  presupuesto largo: **se espera que el efecto se reduzca** al escalar. El
  signo debería mantenerse.
- Corridas secuenciales (`--jobs 1`) para que el tiempo sea medición y no
  cribado (ADR-0003 §4).

## 6. Reproducir

```bash
python3 scripts/fetch_gbd.py --list bench/test.list.csv --out bench/test
./scripts/build.sh
python3 scripts/run_experiment.py --solver solver/kissat/build/kissat \
    --bench bench/test --out results/exp003/A_default.csv \
    --timeout 180 --seeds 1 --jobs 1 --label A-default
python3 scripts/run_experiment.py --solver solver/kissat/build/kissat \
    --bench bench/test --out results/exp003/B_luckyminvars.csv \
    --timeout 180 --seeds 1 --jobs 1 --label B-luckyminvars50k \
    --opts="--luckyminvars=50000"
python3 scripts/par2.py results/exp003/A_default.csv results/exp003/B_luckyminvars.csv --md
```

## 7. Resultados

_Pendiente de ejecución._

## 8. Conclusión

_Pendiente._
