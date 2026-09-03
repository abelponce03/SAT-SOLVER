# Investigación 02 — Fase 0: caracterización de la dinámica de CaDiCaL

> Objetivo: medir **cuánta varianza hay que explotar** en la dinámica de
> búsqueda de CaDiCaL antes de escribir la política de reset/restart adaptativa
> (§5 del doc 01). Método: usar las **estadísticas nativas** del solver
> (`--stats`), sin modificar aún el código.

Herramienta: `scripts/collect_stats.py`. Banco: `benchmarks/dev` (34 instancias,
30 resueltas en 90 s). Entorno: Xeon @ 2.8 GHz, CaDiCaL 3.0.1 vanilla.

---

## 1. Resultado: hay varianza enorme entre instancias

Rango de cada señal sobre las 30 instancias resueltas:

| señal | min | mediana | max |
|---|---:|---:|---:|
| conflicts | 26 | 22 999 | 3 134 556 |
| restarts | **0** | 519 | **103 465** |
| reused% (trail) | **0.0** | 51.8 | **99.7** |
| stabilizing% | 0.0 | 38.9 | 55.3 |
| chronological% | 4.9 | 16.2 | 73.1 |
| rephased | **0** | 6 | **78** |
| improvedglue% | 11.8 | 24.5 | 39.1 |
| reduced% | 0.0 | 52.2 | 65.9 |

Que una señal vaya de su mínimo a su máximo en órdenes de magnitud (restarts,
reused%, rephased) es justamente el margen que una política adaptativa puede
aprovechar: la política fija de CaDiCaL trata igual regímenes muy distintos.

---

## 2. Firmas por familia (lo más informativo)

Medianas por familia:

| familia | n | restarts | reuse% | stab% | chrono% | rephase | confl/restart |
|---|--:|--:|--:|--:|--:|--:|--:|
| aim200 (crafted fácil) | 8 | **0** | 0.0 | 0.0 | 64.2 | 0 | — |
| par16 (parity SAT) | 3 | 173 | 48.0 | 30.7 | 8.0 | 2 | 17.4 |
| uf250 (random SAT) | 8 | 520 | 51.0 | 44.9 | 17.0 | 6 | 44.3 |
| uuf250 (random UNSAT) | 8 | 4 410 | 62.9 | 50.7 | 14.1 | 18 | 41.0 |
| **php (pigeonhole UNSAT)** | 3 | **13 361** | **99.3** | 38.5 | 14.3 | **26** | 27.8 |

Cada familia tiene un régimen propio:
- **aim**: se resuelve casi en la raíz (26–114 conflictos); ninguna política de
  restart importa aquí. (El 64% "chronological" es sobre poquísimos conflictos.)
- **random (uf/uuf250)**: reuse de trail **sano (~50–63%)**, reinicios que sí
  diversifican; CaDiCaL las resuelve holgado. Poco margen de mejora.
- **pigeonhole**: patología clara (ver §3).

---

## 3. Hallazgo central — los reinicios degeneran en pigeonhole

Las instancias donde CaDiCaL **más sufre** (pigeonhole: php_11_10 tarda 62 s,
php_12/13 agotan el tiempo) son precisamente donde su política de reinicio se
degrada:

```
php_9_8    restarts=  1 667   reuse=99.16%   rephase= 9
php_10_9   restarts= 13 361   reuse=99.30%   rephase=26
php_11_10  restarts=103 465   reuse=99.68%   rephase=78
```

**Reuse ~99.7% significa que casi todo reinicio reconstruye el mismo trail**:
CaDiCaL reinicia decenas de miles de veces pero *apenas diversifica* la búsqueda.
Es "restart thrashing" — muchísimos reinicios que no exploran. Y encima reinicia
más seguido que en random (27.8 conflictos/restart vs ~42).

Esto es exactamente el hueco teórico de un **reset**: a diferencia del restart
(que reutiliza el trail), un *reset* **randomiza las activity scores**, forzando
exploración global. La familia donde el restart normal se ha vuelto inútil
(reuse≈100%) es donde inyectar resets bien temporizados tiene más recorrido.

> Hipótesis Fase 1 (afinada por los datos): *un controlador que dispare resets
> cuando el reuse de trail permanece patológicamente alto mientras los conflictos
> no decrecen productivamente puede mejorar el régimen estructurado-difícil
> (pigeonhole-like) sin dañar el régimen random, donde la política actual ya es
> sana.* La señal de disparo candidata: **reuse% alto sostenido + tasa de
> restart alta**. La recompensa candidata: caída de LBD medio / avance en
> profundidad de trail no reutilizada tras el reset.

---

## 4. Implicaciones para el diseño del bandit

- **Dónde actúa**: `restart.cpp` (decisión de reinicio) y `rephase.cpp` (el reset
  ya existe como "rephase" con randomización; el bandit decide *cuándo* forzarlo).
- **Brazos del bandit** (mínimo viable): {no-reset, reset-con-randomización}.
- **Contexto/estado**: reuse% reciente, ratio conflicto/restart, modo
  stable/focused, tendencia de LBD (fast vs slow EMA — que CaDiCaL ya mantiene).
- **Recompensa**: proxy de progreso por ventana de conflictos (ver Fase 0.5).
- **Riesgo controlado**: en random/aim el bandit debe aprender a **no** resetear
  (esas familias ya van bien); el A/B contra el baseline lo verificará.

---

## 5. Limitaciones de esta caracterización (honestas)

- Banco pequeño (34 instancias) y sesgado a crafted/random clásicos; **no**
  incluye instancias industriales/aplicadas de la Main Track, donde los regímenes
  son otros. Ampliar el banco es trabajo pendiente (doc 01, §8, y la opción que
  quedó abierta de añadir instancias Main Track históricas).
- La cola dura (par32×2, php_12/13) **no** se caracterizó: agotan el presupuesto
  y CaDiCaL no imprime stats al ser terminado. Justo esas son las más
  interesantes → en Fase 0.5 conviene correrlas con presupuesto mayor en
  hardware capaz, o instrumentar el solver para volcar stats periódicas.
- `reuse%`, `chronological%` etc. son **agregados finales**, no series
  temporales. Para el bandit necesitamos la señal *durante* la búsqueda → primer
  motivo real para tocar el código (instrumentación ligera por ventana).

---

## 6. Siguiente paso concreto (Fase 0.5)

1. **Instrumentación ligera** en CaDiCaL: volcar, cada N conflictos, una línea
   CSV con (conflicts, restarts, reuse acumulado, LBD medio fast/slow EMA, modo,
   trail medio). Es aditivo (no cambia la lógica) y da la **serie temporal** que
   el bandit observará. Punto de enganche: el mismo sitio donde `report.cpp`
   emite el report periódico.
2. Correr sobre pigeonhole (php_10..php_12) y sobre 2–3 uuf250, y **graficar**
   reuse/LBD vs conflictos: confirmar visualmente el thrashing y localizar el
   momento donde un reset ayudaría.
3. Con eso, diseñar la señal de disparo y recompensa del bandit (Fase 1).

---

## Datos

- CSV completo por instancia: `results/phase0_stats.reference.csv` (versionado).
- Regenerar: `python3 scripts/collect_stats.py -s cadical/build/cadical -b benchmarks/dev -o results/phase0_stats.csv -t 90`
