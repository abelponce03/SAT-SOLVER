# Investigación 04 — Fase 0.5: instrumentación y trazas sobre instancias reales

> Objetivo: obtener la **serie temporal** de la dinámica de restart/rephase
> (no solo agregados) y comprobar, sobre instancias **reales** flaky, si la
> patología de "restart thrashing" (reuso de trail ~99%) que vimos en el
> pigeonhole sintético (doc 02) generaliza. La respuesta cambia el diseño del
> bandit.

## 1. Qué se construyó

Instrumentación mínima y aditiva en CaDiCaL (`src/bandit_trace.hpp` + un
`fprintf` en `restart()` y en `rephase()`), activada por `CADICAL_TRACE=<fichero>`.
Vuelca una fila CSV por evento con: `conflicts, restarts, level,
cum_reusedlevels, glue_fast, glue_slow, stable, rephase_total, rephase_type`.

- **Determinismo verificado**: con y sin traza, el nº de conflictos es idéntico
  (279402 = 279402). No altera la búsqueda; coste = un `getenv` por corrida.
- Análisis con `scripts/analyze_trace.py` (reuso por restart, razón glue
  fast/slow, cadencia de restart, histograma de tipos de rephase).
- 61 líneas añadidas por IA — anotado para el disclosure de la Main Track.

## 2. Resultado sobre 8 familias reales (una flaky por familia)

`% reuso>90%` = fracción de restarts que reutilizan >90% del trail (proxy de
thrashing: reinicios que casi no diversifican). `glue_max` = pico de la razón
glue_fast/glue_slow (volatilidad del disparador de restart).

| familia | resultado | restarts | reuso>90% | glue_max |
|---|---|--:|--:|--:|
| station-repacking | TIMEOUT | 59 156 | **54.9%** | 3.77 |
| cryptography | SAT (58s) | 24 652 | **24.5%** | 2.72 |
| argumentation | TIMEOUT | 55 934 | **21.3%** | 4.28 |
| hardware-verification | UNSAT (23s) | 23 796 | 5.1% | 4.31 |
| planning | UNSAT (11s) | 14 421 | 4.3% | 2.60 |
| software-verification | UNSAT (22s) | 4 655 | 3.6% | 7.44 |
| bitvector | TIMEOUT | 29 558 | 1.9% | 3.11 |
| scheduling | TIMEOUT | 63 173 | 0.8% | 2.27 |

Referencias del doc 02 (sintéticas): pigeonhole 43.8% (thrashing), random uuf250
5.1% (sano).

## 3. Hallazgo central — el thrashing NO es universal (y NO predice el fallo)

1. **La patología del pigeonhole aparece en algunas familias reales**
   (station-repacking 54.9%, crypto 24.5%, argumentation 21.3%) **pero no en
   otras** (bitvector 1.9%, scheduling 0.8%, hw-verification 5.1%).
2. **Y no correlaciona con la dificultad/fallo**: hay TIMEOUTs con reuso
   altísimo (station-repacking) y TIMEOUTs con reuso casi nulo (scheduling 0.8%,
   bitvector 1.9%); hay instancias resueltas con reuso alto (crypto 24.5%). Es
   decir: **un disparador de reset basado solo en "reuso alto" ayudaría a unas
   familias y sería inútil o dañino en otras.**
3. **Lo que sí es transversal es la volatilidad del glue**: `glue_fast/glue_slow`
   pica alto en todas las familias (2.3–7.4), con el máximo en
   software-verification (7.4) — que tiene reuso bajísimo. El disparador de
   restart de CaDiCaL (Glucose EMA) vive en régimen volátil en todas.

## 4. Consecuencia para el diseño del bandit (recalibración)

Esto **refuerza** la elección de un *bandit* sobre una heurística fija, pero
**cambia la señal**:

- ❌ Un trigger de reset hand-tuned sobre "reuso alto" **no** es la respuesta:
  solo cubre 3 de 8 familias y puede dañar el resto.
- ✅ Un **bandit adaptativo** es exactamente lo adecuado porque **aprende por
  instancia** si el reset ayuda — sin comprometer a una señal que no generaliza.
- ✅ La **recompensa** debe ser **genérica de progreso** (p.ej. caída sostenida
  del glow/LBD medio, avance en profundidad de trail "nueva" tras el reset,
  tasa de aprendizaje de glues), **no** el reuso.
- ✅ El **contexto/estado** del bandit puede incluir varias señales (reuso
  reciente, razón glue fast/slow, modo estable/focused, cadencia de restart)
  y dejar que el aprendizaje pese cuál importa en cada instancia.

En una frase: *el valor del bandit no es "detectar thrashing", es aprender, por
instancia y sin supervisión, cuándo un reset paga* — y los datos muestran que
"cuándo paga" depende de la familia, que es justo lo que una heurística fija no
captura y un bandit sí.

## 5. Limitaciones y notas de realidad

- **Hardware/tiempo**: 4 de 8 flaky agotaron 100 s en este entorno (4 núcleos).
  Las trazas de los TIMEOUT quedan con la última línea truncada (buffer de
  `fprintf` cortado por SIGTERM) — no afecta las medianas/%; para Fase 1 con
  timeouts largos conviene un `fflush` periódico en la instrumentación.
- **n pequeño**: una instancia por familia. Antes de fijar el diseño del bandit,
  ampliar a varias por familia (las 62 flaky) en hardware capaz.
- Estos números son de CaDiCaL con **seed por defecto**; la naturaleza "flaky"
  se manifiesta variando seed (doc 03). Para Fase 1, cada configuración
  (baseline vs bandit) debe medirse **sobre varias seeds**.

## 6. Siguiente paso (Fase 1, ya con base empírica)

1. Añadir `fflush` periódico a la traza (para capturar corridas que agotan
   tiempo) — cambio mínimo.
2. Definir la **recompensa de progreso** y validarla: correlacionar, sobre las
   trazas, señales de progreso con el resultado (resuelve pronto vs tarde).
3. Implementar el bandit (UCB/Thompson) en la decisión de `rephasing()`:
   brazos {no-reset, reset}, contexto multi-señal, recompensa de progreso.
4. A/B con `par2.py` + métricas de robustez (flaky→resuelta, ↓varianza por seed)
   sobre un subconjunto de las 62 flaky, en hardware capaz.

## Datos / reproducción

- Instrumentación: `CADICAL_TRACE=<f> cadical/build/cadical <instancia>`
- Análisis: `python3 scripts/analyze_trace.py <traza.csv>`
- Instancias: `scripts/fetch_gbd.py` + `results/phase1_download_list.csv`
