# EXP-006 — A4.1: ¿acelera el planificador adaptativo? (hipótesis preregistrada)

- **Estado**: **preregistrado** — escrito **antes** de ejecutar (ADR-0003 §6)
- **Fecha**: 2026-09-23
- **Origen**: hallazgo exploratorio de [EXP-005 §7](EXP-005-a4-reparto-adaptativo.md)
- **Por qué existe**: para convertir una observación hecha *después* de ver los
  datos en una prueba hecha *antes*

---

## 1. De dónde viene la hipótesis, y por qué no basta con ella

En EXP-005 la métrica preregistrada (PAR-2) no concluyó: ΔPAR-2 = −2.222 s con
el IC95 % incluyendo el 0. Un análisis de potencia mostró que decidirlo por
PAR-2 exigiría ~155 h de cómputo por rama.

Al descomponer el resultado apareció un patrón nítido: en las 12 instancias que
**ambas** ramas resuelven, el planificador adaptativo fue más rápido en **10**
(test de signo p = 0.039; factor geométrico 0.648×).

**Esa observación no vale como resultado.** Se buscó en una segunda métrica
después de que la primera no diera nada, sobre los mismos datos. Es el camino
del jardín que se bifurca, y el proyecto ya pagó una vez por él: B3′ dio −13.4 %
en su banco de descubrimiento y +2.3 % en el reservado. Este experimento existe
para someter la observación a una prueba honesta: **hipótesis y métrica fijadas
de antemano, sobre datos que no han visto ningún A/B de A4**.

## 2. Hipótesis

> **H1.** En las instancias que resuelven ambas ramas, `--modeadaptive=1`
> las resuelve **más rápido** que el planificador de upstream.

## 3. Métrica primaria y contraste, fijados ahora

- **Unidad de análisis: la instancia**, no la corrida. Con varias semillas por
  instancia, las corridas de una misma instancia no son independientes; tratarlas
  como tales inflaría n artificialmente (pseudo-replicación). Por cada instancia
  se promedia `log(t_B / t_A)` sobre las semillas en que **ambas** ramas
  resuelven.
- **Se excluyen** los pares con algún tiempo < 1 s: a esa escala el ruido de
  medida domina al efecto.
- **Contraste**: Wilcoxon de rangos con signo sobre los log-ratios por instancia,
  dos colas.
- **Tamaño de efecto**: factor geométrico `exp(media de log-ratios)`, con IC95 %
  por bootstrap de instancias.

### Comprobación independiente de la deriva

EXP-004 mostró que el tiempo puede moverse un ~4 % sin que cambie nada del
algoritmo. Por eso se mide también el **esfuerzo determinista**: el número de
**propagaciones** hasta la solución, que no depende del estado de la máquina. Si
el tiempo dice "más rápido" pero las propagaciones no, el efecto de tiempo es
sospechoso y **no se da por bueno**.

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| Wilcoxon p < 0.05, factor < 1, **y** las propagaciones apuntan en el mismo sentido | **H1 confirmada**: A4.1 acelera de verdad. Siguiente paso: EXP-007, comprobar si la aceleración se traduce en PAR-2 con un presupuesto más largo, donde convierte timeouts en resueltas |
| Wilcoxon p < 0.05 pero las propagaciones no acompañan | el efecto es de tiempo sin respaldo algorítmico: **no se confirma**; se investiga el mecanismo |
| p ≥ 0.05 | **H1 no se confirma**: el patrón de EXP-005 era ruido. A4.1 se cierra como «sin efecto detectado» y se documenta |

## 5. Diseño

| elemento | valor |
|---|---|
| Binario | uno solo; SHA-1 registrado, la tanda aborta si cambia |
| Rama A | `modeadaptive=0` (upstream) |
| Rama B | `--modeadaptive=1`, con `modeadaptivedecay=800` y `modeadaptivegain=1000` **tal como estaban en EXP-005**, sin ajustar |
| Bancos | `bench/calib` (40) + `bench/calib2` (20) = 60 instancias reales del Main Track 2026 |
| Semillas | 1 y 2 |
| Presupuesto | T = 180 s |
| Ejecución | **intercalada** (`run_ab_interleaved.py`): A y B de cada instancia seguidas, orden alternado A-B / B-A, secuencial |

### Por qué estos bancos

`bench/dev` ya se usó en EXP-005 y **no puede** volver a usarse para confirmar lo
que en él se descubrió. `bench/test` sigue reservado para una validación final.
`calib` y `calib2` son disjuntos de ambos y **nunca se han usado en un A/B de A4**.

**Salvedad que se declara**: sí se usaron en el paso 0 de EXP-005 para recoger
las trazas con las que se validó la señal de recompensa, y esa validación
informó el diseño (el EMA por brazo). No son datos vírgenes para A4 en sentido
estricto. Lo que no han visto es **ningún resultado de A/B**, que es lo que
importa para no confirmar una hipótesis con los mismos datos que la sugirieron.

### Potencia esperada

Con el tamaño de efecto observado en EXP-005 (Cohen *d* = 0.74 sobre los
log-ratios), bastan ~14 instancias para un 80 % de potencia. `calib` resolvió
39 de 40 con la configuración por defecto en EXP-001, así que se esperan en
torno a 40 instancias informativas: **potencia holgada**. Si aun así sale nulo,
será evidencia real de ausencia de efecto, no falta de datos.

## 6. Amenazas a la validez, anotadas de antemano

- **Regresión a la media.** El efecto de EXP-005 se seleccionó por ser llamativo;
  lo esperable es que en datos nuevos sea **menor**. Un factor más cercano a 1
  que 0.648 no sería una sorpresa sino lo normal.
- **Banco sesgado hacia lo fácil.** `calib` son instancias que Kissat resolvió en
  ≤ 120 s en la competición. Un efecto de velocidad ahí no garantiza nada sobre
  las difíciles. `calib2` compensa en parte.
- **T = 180 s.** Aunque H1 se confirme, **no dice nada todavía sobre PAR-2 de
  competición**: esa pregunta es EXP-007.

## 7. Reproducir

```bash
python3 scripts/run_ab_interleaved.py --solver solver/kissat/build/kissat \
    --bench bench/calib bench/calib2 \
    --out-a results/exp006/A.csv --out-b results/exp006/B.csv \
    --label-a A-upstream --label-b B-adaptive \
    --timeout 180 --seeds 1,2 --opts-b="--modeadaptive=1"
python3 scripts/analyze_speedup.py results/exp006/A.csv results/exp006/B.csv
```

## 8. Resultados

_Pendiente de ejecución._
