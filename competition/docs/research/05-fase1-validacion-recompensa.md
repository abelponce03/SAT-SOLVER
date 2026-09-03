# Investigación 05 — Validación de la señal de recompensa (Fase 1, paso 0)

> Antes de implementar el reset-bandit, validamos su **señal de recompensa** para
> no construirlo sobre una métrica que no refleje progreso. Resultado: la
> recompensa correcta es el **GLR relativo a su propio EMA** (mejora sobre el
> historial reciente), **no** el nivel absoluto de ninguna señal.

## 1. La recompensa candidata (anclada en literatura)

Li et al. 2024 (arXiv:2404.03753, reset-policy por MAB) usan el **Global Learning
Rate por ventana de restart**:

```
rw_glr(ventana) = Δ(cláusulas aprendidas) / Δ(decisiones)
recompensa = ÉXITO si rw_glr(ventana) > EMA_historico(rw_glr)   [decay 0.8]
             FALLO  en caso contrario
```

Es una medida **scale-free e intra-instancia** de productividad de la búsqueda.
Para medirla añadimos a la traza los contadores `learned` y `decisions`
(instrumentación GLR) y la validamos con `scripts/validate_reward.py` sobre 10
trazas reales (6 resueltas, 4 timeout), en ventanas de 10/20/50 restarts.

## 2. Por qué NO usar señales de nivel absoluto (glue ni GLR)

Antes probamos el nivel absoluto de `glue_slow`: su escala varía de **1.7 a 116**
entre instancias y su pendiente global tiene signo mixto en resueltas y en
timeouts → **no discrimina** (doc 04 y exploración previa).

La validación muestra que **el nivel de GLR tampoco sirve, y encima se invierte**:

| prueba (ventana=20) | SOLVED (mediana) | TIMEOUT (mediana) | Δ |
|---|--:|--:|--:|
| **nivel** rw_glr | 0.251 | 0.419 | **−0.168** |
| **pendiente** rw_glr (por 1e6 conflictos) | +0.629 | +0.058 | **+0.571** |
| tasa de éxito EMA-relativa | 48.0% | 46.3% | +1.7% |

Robustez (mismo signo en ventana 10/20/50):

| | Δ nivel | Δ pendiente |
|---|--:|--:|
| ventana 10 | −0.180 | +0.723 |
| ventana 20 | −0.168 | +0.571 |
| ventana 50 | −0.116 | +0.662 |

**Lectura**: instancias estancadas (timeout) pueden tener GLR absoluto *alto*
(aprenden muchísimo por decisión y aun así no cierran) — por eso una recompensa
"más GLR = mejor" sería **errónea**. Lo que sí distingue es la **tendencia**: en
las resueltas el GLR **sube** (productividad creciente → converge), en las
estancadas queda **plano**.

## 3. Veredicto de las tres pruebas

- **V1 no-degeneración** ✅ — rw_glr varía ventana a ventana (CV mediana
  0.46–0.63). El bandit tiene señal real que explotar; no es constante.
- **V2 discriminación** ✅ (por tendencia) / ❌ (por nivel) — la **pendiente**
  de rw_glr separa resueltas (+0.63) de timeout (+0.06) de forma consistente; el
  **nivel** no (se invierte). ⇒ la recompensa debe premiar **mejora**, no nivel.
- **V3 recompensa bien formada** ✅ — la señal de éxito EMA-relativa es no
  trivial (~47%, ni siempre 0 ni 1) y balanceada en ambos regímenes, como
  corresponde a una recompensa **local de control** (no un predictor global).

## 4. Conclusión para el diseño del bandit

1. **Recompensa = GLR relativo al EMA** (éxito si la ventana supera su historial),
   exactamente la formulación de Li et al. — ahora **validada empíricamente en
   nuestras instancias reales**: es la única variante que tiene sentido, porque
   el nivel absoluto no rastrea progreso (y se invierte).
2. La recompensa es un **buen señal local** para el dilema explorar/explotar de
   {no-reset, reset}: informa "¿esta ventana fue más productiva que lo reciente?".
   No pretende predecir el resultado global — eso no es el trabajo de la
   recompensa de un bandit.
3. El **contexto** del bandit puede incluir además la *tendencia* de GLR (que sí
   discrimina) y las señales del doc 04 (reuso, glue ratio, modo), dejando que el
   aprendizaje pese cuáles importan por instancia.

## 5. Limitaciones

- n pequeño (10 trazas, una por familia; 4 timeouts truncados a 100 s en este
  hardware). La discriminación por pendiente es **sugerente, no concluyente**;
  reconfirmar sobre más instancias por familia en el experimento completo.
- Trazas con seed por defecto; la validación final debe repetirse sobre las
  seeds del experimento A/B.

## 6. Siguiente paso (implementación del bandit)

Con la recompensa validada, ya se puede implementar con base sólida:
1. Bandit (UCB o Thompson) en la decisión de `rephasing()` en `rephase.cpp`,
   brazos {no-reset, reset(random+shuffle)}.
2. Recompensa = éxito si rw_glr de la ventana > EMA(0.8) — la instrumentación
   ya calcula learned/decisions; reutilizar esa lógica dentro del solver.
3. A/B con `par2.py` + métricas de robustez (flaky→resuelta, ↓varianza por seed),
   en hardware capaz.

## Datos / reproducción

- Salida de referencia: `results/phase1_reward_validation.txt`
- Regenerar: re-trazar con `CADICAL_TRACE=` (build actual) y
  `python3 scripts/validate_reward.py <trazas> --window 20`
