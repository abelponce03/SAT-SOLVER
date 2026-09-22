# EXP-003 — Validación de `luckyminvars` sobre el banco reservado

- **Estado**: **cerrado — la regla NO replica**. Diseño escrito antes de ejecutar (ADR-0003 §6)
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

### Métrica primaria — banco completo (60 instancias, T = 180 s)

| | resueltas | PAR-2 |
|---|---:|---:|
| **A** — por defecto (`luckyminvars=0`) | **16** | **277.772 s** |
| **B** — `--luckyminvars=50000` | 15 | 280.025 s |

```
ΔPAR-2 medio (B−A) = +2.254 s   (+0.8 %, positivo = B PEOR)
IC95 % bootstrap    = [−3.790, +11.165]   INCLUYE el 0
Wilcoxon emparejado = W 68.0, p = 0.9794  (n efectivo = 16)
McNemar (resueltas) = A-sí/B-no 1, A-no/B-sí 0, p = 1.0000
```

**Aplicando el criterio congelado en §3: ΔPAR-2 ≥ 0 ⇒ la regla NO replica.**

### Secundario — solo las 16 instancias que alguna rama resuelve

| | PAR-2 |
|---|---:|
| A | 51.64 s |
| B | 60.09 s |

`Δ = +8.45 s`, IC95 % `[−14.19, +40.33]`. Tampoco aquí hay señal, y el signo
sigue siendo desfavorable.

## 8. Diagnóstico: por qué no replicó

### No fue falta de cobertura de la regla

La regla actuó sobre **45 de las 60** instancias (75 %): `bench/test` tiene
mediana de 5 625 variables y p75 de 72 456, así que la mayoría cae por debajo
del umbral. No es que la regla no se disparara.

| grupo | n | PAR-2 A | PAR-2 B | Δ |
|---|---:|---:|---:|---:|
| tocadas (< 50 000 variables) | 45 | 273.09 | 276.14 | **+3.05** |
| intactas (≥ 50 000) | 15 | 291.83 | 291.68 | −0.15 |

El daño está, en efecto, en las instancias que la regla toca.

### Sí hubo dilución, como se anticipó

De las 45 tocadas, **solo 13 las resuelve alguna de las dos ramas**; las otras
32 agotan el presupuesto en ambas y aportan `2T` idéntico. El diseño ya lo
advirtió en §4; el efecto real se juega en 13 observaciones.

### Lo que pasó en esas 13

| variables | A | B | Δ | |
|---:|---:|---:|---:|---|
| 41 734 | 157.50 | 85.23 | **−72.27** | gana B |
| 1 150 | 152.74 | 128.61 | −24.13 | gana B |
| 440 | 74.04 | 49.92 | −24.12 | gana B |
| 19 484 | 149.62 | 137.89 | −11.74 | gana B |
| 8 400 | 0.81 | 11.28 | +10.48 | gana A |
| 19 384 | 85.96 | 123.88 | +37.92 | gana A |
| **306** | **141.48** | **TIMEOUT** | **+218.52** | **gana A** |

Cuatro ganancias claras frente a tres pérdidas, **pero una de las pérdidas es
catastrófica**: una instancia de **306 variables** que las fases lucky resuelven
en 141.5 s y que, sin ellas, agota el presupuesto.

### La lección mecánica

Esa instancia refuta el modelo que sostenía la regla. EXP-002 concluyó que
*"las fases lucky compensan en fórmulas enormes y son peaje en las pequeñas"*.
Aquí una fórmula de **306 variables** —tres órdenes de magnitud por debajo del
umbral— **solo se resuelve gracias a ellas**. El valor de las fases lucky **no
está correlacionado con el tamaño** del modo simple que suponíamos: dependen de
que la fórmula admita una asignación trivial o casi trivial, y eso es una
propiedad estructural que el recuento de variables no captura.

Visto así, el resultado de EXP-002 (−13.4 s) se explica como lo que era: un
umbral ajustado sobre 60 instancias concretas, que capturó el patrón de esa
muestra y no un mecanismo. **Es el caso de libro de por qué existe el banco
reservado.**

### Una nota sobre lo que NO se va a hacer

Quitando esa única instancia catastrófica, el Δ sería −1.41 s. **No se va a
reportar eso como resultado.** Excluir la observación que estropea la hipótesis
después de verla es precisamente lo que el protocolo prohíbe; se anota aquí solo
para dejar constancia de que la tentación se vio y se descartó, y de que el
efecto —de existir— sería pequeño y de cola muy pesada.

## 9. Conclusión y decisiones tomadas

1. **B3′ se retira del catálogo como idea cerrada**, según el criterio escrito
   antes de ejecutar. No se ajusta el umbral, no se cambia el banco, no se
   reintenta con otra métrica.
2. **La opción `luckyminvars` se elimina del solver.** El diff contra upstream
   es el artefacto que se entrega a la competición (ADR-0002) y no debe
   arrastrar una feature que falló su validación. Todo lo necesario para
   reponerla en 20 líneas queda en este documento y en el historial de git
   (commit `589c853`).
3. **Lo que SÍ sobrevive, y es independiente de esto**: `kissat_lucky` **no
   consulta el límite de tiempo**, y por eso un `--time=30` puede convertirse en
   348 s (EXP-002 §1). Eso es un fallo de upstream con consecuencias reales para
   cualquiera que mida con presupuesto acotado, y **no depende de si conviene
   saltarse las fases lucky**. Se mantiene como línea viva: la corrección
   correcta no es saltarlas, es **hacer que cedan el control**.
4. **Coste de esta línea**: unas 3 horas de cómputo y ~30 líneas de código. El
   catálogo tenía B3′ marcada como "la mejor relación evidencia/esfuerzo"; ahora
   tiene además un dato mucho más valioso: cuánto vale realmente la evidencia
   obtenida en el mismo banco en que se buscó la regla.
