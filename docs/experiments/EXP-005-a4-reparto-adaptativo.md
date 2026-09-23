# EXP-005 — A4: reparto adaptativo del presupuesto entre modos de búsqueda

- **Estado**: paso 0 cerrado (V1/V2/V3 pasan) · implementado · **A/B en `bench/dev`: dirección favorable, sin significación** — NO pasa a `bench/test`. Diseño escrito antes de implementar (ADR-0003 §6)
- **Fecha de diseño**: 2026-09-22
- **Motiva**: [`catálogo`](../research/02-catalogo-de-ideas.md) línea A4 — la contribución candidata
- **Depende de**: [EXP-004](EXP-004-lucky-terminator.md) (el solver ya cede el control), [EXP-001](EXP-001-diversidad-intrinseca-kissat.md) (la diversidad existe)

---

## 1. La idea, y por qué es una generalización y no un injerto

Kissat **ya reparte su presupuesto entre dos políticas de búsqueda**:
alterna modo `stable` y modo `focused`. Lo hace en `src/mode.c`, con un
planificador **ciego**:

```c
bool kissat_switching_search_mode (kissat *solver) {
  if (limits->mode.count & 1)
    return statistics->search_ticks >= limits->mode.ticks;   /* stable */
  else
    return statistics->conflicts >= limits->mode.conflicts;  /* focused */
}
```

y los límites se fijan sin mirar nunca qué está pasando dentro:

- al entrar en `stable`: se le dan **tantos ticks como consumió el `focused`
  anterior** (`limits->mode.ticks = search_ticks + delta_ticks`);
- al entrar en `focused`: `modeint · nlogpown(count, 4)` conflictos, una
  progresión creciente fijada de antemano.

**Ningún término de esas fórmulas depende de si el modo actual está
progresando.** Si `stable` está resultando estéril en esta instancia, se le da
exactamente el mismo turno que si fuera brillante.

A4 sustituye ese planificador ciego por uno guiado por el progreso observado.
**No añade un mecanismo nuevo al solver: cambia la política de uno que upstream
ya considera correcto.** Eso importa para la aceptabilidad de la contribución
tanto como para el riesgo técnico.

## 2. Por qué esta forma de bandit y no la que fracasó en 2026

Los datos oficiales de 2026 son demoledores con los bandits: siete variantes de
cuatro grupos independientes, **todas peor** que el Kissat de fábrica
(`docs/research/01`, §1). Aquello no invalida esta idea, y conviene tener claro
por qué:

| | bandits de 2026 | A4 |
|---|---|---|
| Qué elige el brazo | una heurística **dentro** de la búsqueda (rephase, restart, rama VSIDS/CHB) | **cuánto presupuesto** recibe una trayectoria completa |
| Horizonte de la decisión | un reinicio (miles de conflictos) | una fase de modo (millones de ticks, decenas de segundos) |
| Dilución de la señal | alta: el efecto de un brazo se mezcla con millones de conflictos | baja: cada fase tiene su propia trayectoria medible |
| Qué se juega en cada decisión | marginal | un turno entero |

La apuesta explícita: **el bandit falla cuando su decisión es demasiado pequeña
para tener consecuencias medibles**, y aquí la decisión es grande. Si A4 también
fracasa, ese será el resultado interesante y se documentará como tal.

## 3. Alcance: qué entra y qué NO

**A4.1 (este experimento)**: dos brazos —los que ya existen, `stable` y
`focused`— y reparto adaptativo entre ellos.

**No entra**: añadir brazos nuevos (más configuraciones), que es A4.2 y depende
de que A4.1 demuestre que la señal sirve. Empezar por k>2 mezclaría dos
preguntas y haría imposible atribuir el resultado.

## 4. Paso 0 — validar la señal ANTES de construir nada

La etapa CaDiCaL ya estableció que la recompensa útil es el **GLR relativo a su
propio EMA**, y **no** el nivel absoluto, que incluso se invierte
(`docs/archive/cadical-era/05-fase1-validacion-recompensa.md`). Ese resultado se
midió sobre trazas de **CaDiCaL** y el archivo lo marca explícitamente como
«hay que reproducirlo sobre Kissat». Construir A4 sin reproducirlo sería
repetir el error de B3′: fiarse de una regla medida en otro sitio.

### Señal candidata, en términos de Kissat

```
GLR(fase) = Δconflicts / Δdecisions
```

`conflicts` es el número de cláusulas aprendidas (una por conflicto) y ambos son
`COUNTER` en `src/statistics.h`, así que **existen incluso en el build
`--competition`**, donde `METRIC` y `STATISTIC` se compilan fuera. Eso es
condición necesaria: una señal que solo exista en builds de depuración no puede
gobernar el solver que se entrega.

### Qué hay que comprobar (las tres pruebas del doc archivado 05)

| | prueba | criterio |
|---|---|---|
| **V1** | no-degeneración: el GLR varía de fase a fase | CV mediano > 0.2; si fuera constante, no hay nada que aprender |
| **V2** | discriminación: distingue corridas que acaban resolviendo de las que se estancan | la **pendiente** del GLR separa resueltas de timeout, de forma consistente al variar la ventana |
| **V3** | recompensa bien formada: la señal «esta fase superó a su EMA» no es trivial | tasa de éxito lejos de 0 % y de 100 % |

**V2 es la que puede matar la idea.** En CaDiCaL el *nivel* de GLR no
discriminaba e incluso se invertía; solo la tendencia servía. Si en Kissat no
discrimina ni por nivel ni por tendencia, A4 se queda sin recompensa y hay que
buscar otra señal antes de escribir el planificador.

### Instrumentación

Una traza CSV por corrida, una fila por cambio de modo, activada por variable de
entorno (`KISSAT_TRACE=<fichero>`) para que no toque el camino de competición:

```
phase,mode,d_conflicts,d_decisions,d_ticks,d_learned,glr,time
```

Coste: una escritura cada decenas de segundos. Irrelevante.

### Resultados del paso 0

**Datos**: 60 instancias reales del Main Track 2026 (`bench/calib` + `bench/calib2`),
T = 180 s, seed 1. 48 produjeron traza utilizable (12 se resolvieron sin llegar a
cambiar de modo; 1 con menos de 4 fases, descartada). **31 SOLVED / 16 TIMEOUT**,
con **1 660 fases** de modo en total.

```
                n   glr_med   glr_cv   pendiente    exito
SOLVED         31     0.503    0.421       0.645    58.9%
TIMEOUT        16     0.712    0.413       0.077    59.0%
```

| prueba | resultado | veredicto |
|---|---|---|
| **V1** no-degeneración | CV mediano del GLR = **0.421** (umbral 0.2) | ✅ **PASA** |
| **V2** discriminación | Δ nivel = **−0.209** (p = 0.062) · Δ pendiente = **+0.568** (p = **0.022**) | ✅ **PASA por pendiente** |
| **V3** bien formada | tasa de éxito EMA-relativa = **59.0 %** | ✅ **PASA** |

#### Lo importante: la inversión del nivel se replica

El documento archivado midió sobre **CaDiCaL** que el *nivel* absoluto de GLR no
solo no discrimina, sino que **se invierte**: las corridas estancadas tienen GLR
*más alto*. Aquí, sobre **Kissat**, sale lo mismo y con magnitudes casi
idénticas:

| | CaDiCaL (doc archivado 05, ventana 20) | **Kissat (este experimento)** |
|---|---:|---:|
| Δ nivel (SOLVED − TIMEOUT) | −0.168 | **−0.209** |
| Δ pendiente (SOLVED − TIMEOUT) | +0.571 | **+0.568** |

Dos solvers distintos, dos bancos distintos, dos instrumentaciones escritas por
separado, y el mismo resultado hasta la segunda cifra. Eso deja de ser una
peculiaridad de CaDiCaL y pasa a ser una propiedad de la búsqueda CDCL: **una
instancia estancada puede estar aprendiendo muchísimo por decisión y aun así no
cerrar**. Una recompensa del tipo «más GLR = mejor» sería **activamente
errónea**.

Queda confirmada, ahora sobre el host correcto, la decisión de diseño: la
recompensa premia **mejora sobre el propio historial**, no nivel.

#### Hallazgo nuevo: los dos brazos tienen escalas distintas

```
   focused    n= 866   mediana GLR = 0.462   CV = 0.640
   stable     n= 794   mediana GLR = 0.810   CV = 0.326
```

El modo `stable` aprende **un 75 % más por decisión** que el `focused`, de forma
sistemática. Eso no es una diferencia de calidad sino de régimen: `stable` usa
reinicios largos y fases objetivo, así que cada decisión cunde más.

**Consecuencia directa para el planificador**: la recompensa debe compararse
contra el **EMA del propio brazo**, nunca contra un EMA global. Con un EMA común,
`stable` ganaría casi siempre por construcción y el bandit dejaría morir de
hambre al `focused` — no porque sea peor, sino porque su señal vive en otra
escala. El diseño de §5 ya lo preveía («estado por brazo»); ahora hay evidencia
de por qué es imprescindible y no un detalle.

Nótese también que `focused` es mucho más variable (CV 0.640 frente a 0.326):
es el brazo donde un reparto adaptativo tiene más que ganar y más que perder.

## 5. Diseño del planificador (A4.1), para implementar tras el paso 0

Manteniendo la estructura de `mode.c`:

- **Estado por brazo**: EMA del GLR y presupuesto concedido acumulado.
- **Recompensa de una fase**: éxito si `GLR(fase) > EMA(GLR del brazo)`.
- **Asignación**: el tamaño del siguiente turno de un brazo escala con su tasa
  de éxito reciente, dentro de un rango acotado respecto del reparto actual
  (p. ej. entre ×0.5 y ×2 del que le tocaría hoy), para que la política nunca se
  aleje mucho de la de upstream. **La cota es deliberada**: convierte el cambio
  en una perturbación acotada de una política que ya funciona, en vez de una
  política nueva sin garantías.
- **Exploración**: nunca se reduce un brazo por debajo de un mínimo, para no
  quedarse atrapado descartando el modo que haría falta más tarde.
- Todo detrás de la opción `modeadaptive` (0 = comportamiento de upstream,
  valor por defecto hasta que un A/B lo valide, ADR-0002 §3).

## 5b. Implementación (hecha)

Diff contra upstream: **~190 líneas** en `src/mode.{c,h}` y `src/options.h`.

| pieza | dónde |
|---|---|
| Estado por brazo (`ema_glr`, `ema_success`, `seeded`) | `src/mode.h`, `struct adaptive_arm` dentro de `struct mode` |
| Recompensa de la fase que termina | `kissat_adaptive_finish_phase()`, llamada desde `kissat_switch_search_mode` **antes** de voltear `solver->stable` |
| Factor de presupuesto | `adaptive_factor()` / `adaptive_budget()`, aplicado a los **dos** presupuestos de `update_mode_limit` |
| Opciones | `modeadaptive` (0), `modeadaptivedecay` (800), `modeadaptivegain` (1000) |

Tres decisiones de implementación que conviene justificar:

1. **Aritmética entera por milésimas, sin coma flotante.** El planificador está
   en el camino caliente y debe ser determinista y reproducible bit a bit entre
   compiladores; con dobles, el redondeo puede diferir y dos corridas con la
   misma semilla dejarían de coincidir — lo que rompería todo el protocolo de
   medición del ADR-0003.
2. **Los campos van fuera de los `#ifndef QUIET`** de `struct mode`. El binario
   de entrega se compila con `--competition` (= `--no-options --quiet`), así
   que un planificador que solo existiera en builds con mensajes no llegaría a
   la competición — es la misma trampa que documentó el ADR-0002 tras EXP-004.
3. **El factor está acotado en `[×0.5, ×2]`** del presupuesto que upstream
   daría, y el suelo del 0.5 **es la exploración**: un brazo con mala racha
   conserva turno suficiente para demostrar lo contrario más tarde. Sin ese
   suelo, una racha inicial mala podría matar a un brazo que hacía falta luego.

### Verificación

| comprobación | resultado |
|---|---|
| `modeadaptive=0` (defecto) es un **no-op** | conflictos idénticos a antes del parche: 2592 / 12203 / 1457 |
| la opción actúa | factores observados 0.900 y 1.200; recompensas por brazo en el log |
| determinismo con el planificador activo | misma semilla → mismos conflictos (11050, dos veces); semilla distinta → 12562 |
| estados correctos sobre `bench/smoke` | 10/10 con `--modeadaptive=1` |
| modelos SAT | válidos con `--modeadaptive=1` (3 instancias verificadas) |
| **pruebas DRAT** | verificadas con drat-trim con `--modeadaptive=1` (3 instancias) |
| build `--debug` (asertos) | sin abortos |
| build `--sanitize` (ASan+UBSan) | 0 errores, códigos de salida correctos (20/20/10) |
| suite completa `smoke_test.sh` | en verde |

## 6. Criterios de éxito, fijados de antemano

**Paso 0 (señal)**:

| resultado | decisión |
|---|---|
| V1, V2 y V3 se cumplen | se implementa A4.1 con esta recompensa |
| V2 falla | **no se implementa**: se busca otra señal o se cierra A4. Escribir un planificador sobre una señal que no discrimina es construir sobre arena |

**A4.1 (A/B)**:

| resultado | decisión |
|---|---|
| ΔPAR-2 < 0 con IC95 % que excluye el 0 en `bench/test` | se valida; pasa a ser el valor por defecto |
| ΔPAR-2 < 0 sin significación | se documenta; se decide si escalar el banco compensa |
| ΔPAR-2 ≥ 0 | A4.1 se cierra como B3′: se documenta y se retira |

## 7. Resultado del A/B en `bench/dev`

60 instancias, T = 180 s, una semilla, **ejecución secuencial** (`--jobs 1`),
**un único binario** congelado en `6380e4d5` para las dos ramas.

| | resueltas | PAR-2 |
|---|---:|---:|
| **A** — planificador ciego (upstream) | 15 | 282.670 s |
| **B** — `--modeadaptive=1` | 15 | **280.448 s** |

```
ΔPAR-2 medio (B−A) = −2.222 s   (−0.8 %, negativo = B mejor)
IC95 % bootstrap    = [−14.099, +11.043]   INCLUYE el 0
Wilcoxon emparejado = W 30.0, p = 0.0938  (n efectivo = 15)
McNemar (resueltas) = 1 a favor de cada lado, p = 1.0000
```

**Veredicto según el criterio congelado en §6**: «ΔPAR-2 < 0 pero el IC incluye
el 0 → se documenta; se decide si escalar el banco compensa». Es el caso
intermedio. **No se pasa a `bench/test`**: el banco reservado se gasta una sola
vez por idea, y quemarlo con una hipótesis que su propio banco de desarrollo no
confirma sería tirarlo.

### El planificador sí está haciendo algo

No es un no-op disfrazado: **cambia la trayectoria en 55 de las 60 instancias**
(recuentos de conflictos distintos). El problema no es que no actúe.

### Dónde se pierde el efecto: la dilución, otra vez

**44 de las 60 instancias agotan el presupuesto en las dos ramas.** Aportan `2T`
idéntico a A y a B, así que el ΔPAR-2 real se juega en **16 observaciones**. Era
previsible —está escrito en §4 y volvió a pasar en EXP-003— y es el motivo de
que un efecto de este tamaño no pueda alcanzar significación con este banco.

Restringiendo a las 16 que alguna rama resuelve:

| | PAR-2 |
|---|---:|
| A | 70.01 s |
| B | **61.68 s** |

`Δ = −8.33 s (−11.9 %)`, IC95 % `[−51.04, +40.18]`. **La dirección se mantiene y
el tamaño crece**, pero el intervalo es enorme con n=16: sugerente, no
concluyente. No se va a reportar el −11.9 % como si fuera un resultado.

### Qué hizo instancia a instancia

| familia | A | B | Δ |
|---|---:|---:|---:|
| graph-coloring | 162.3 s | **23.5 s** | −138.8 |
| graph-coloring | TIMEOUT | **UNSAT** | gana una |
| sorting-networks | 150.2 s | 106.4 s | −43.8 |
| graph-coloring | 95.2 s | 64.6 s | −30.6 |
| syndrome-decoding | 60.1 s | 65.4 s | +5.3 |
| school-timetabling | 63.8 s | 69.0 s | +5.3 |
| school-timetabling | UNSAT | **TIMEOUT** | pierde una |

El perfil es el mismo que vimos en EXP-001: **cola pesada**. Las ganancias son
grandes y concentradas (una instancia de 162 s a 23 s), las pérdidas pequeñas y
repartidas (dos de +5.3 s), y hay un intercambio de una instancia en cada
sentido. Eso es coherente con un mecanismo que a veces acierta mucho y rara vez
estropea, que es exactamente lo que la cota `[×0.5, ×2]` pretendía garantizar.

### Qué haría falta para decidirlo

No más ajuste de hiperparámetros sobre estos datos —eso es el error de B3′—
sino **más observaciones informativas**: un banco con más instancias en la
frontera (ni triviales ni imposibles) y varias semillas. Con 16 observaciones
útiles y un efecto del orden del 10 %, este diseño no tenía potencia para
detectarlo; decirlo ahora es más honesto que haberlo descubierto después.

### Análisis de potencia: ¿compensa escalar el banco?

Es la decisión que el criterio de §6 dejaba pendiente. Se toma con números:

```
diferencias B−A ordenadas (s): -196.3 -138.8 -43.8 -30.6 -6.3 -5.7 -2.4 -1.7
                               -0.9 -0.7 -0.6 -0.0 0.0 5.3 5.3 283.9
tamaño de efecto (Cohen d)   = |-8.33| / 93.6 = 0.089
n informativas para 80 % de potencia: ~990
  -> ~3 700 corridas por rama (tasa informativa del banco: 27 %)
  -> ~155 h de cómputo SECUENCIAL por rama
```

**Escalar el banco para decidir A4.1 por PAR-2 no compensa**: es inviable en esta
máquina. El PAR-2 está dominado por tres valores extremos, dos de ellos
instancias que cambian de estado en sentidos opuestos y casi se cancelan
(−196.3 y +283.9). Con presupuesto corto, el PAR-2 mide sobre todo *qué*
instancias se resuelven, y ahí A4.1 empata 1–1.

### Un hallazgo exploratorio — que NO es un resultado

Restringiendo a las 12 instancias que **ambas** ramas resuelven, el patrón es
nítido:

| familia | A | B | factor |
|---|---:|---:|---:|
| graph-coloring | 162.3 s | 23.5 s | **0.14×** |
| multiplier-circuits | 8.5 s | 2.7 s | 0.32× |
| stable-semantics | 4.2 s | 1.8 s | 0.42× |
| clique-formulas | 14.7 s | 8.4 s | 0.57× |
| graph-coloring | 95.2 s | 64.6 s | 0.68× |
| sorting-networks | 150.2 s | 106.4 s | 0.71× |
| *(cuatro más entre 0.94× y 0.98×)* | | | |
| school-timetabling | 63.8 s | 69.0 s | 1.08× |
| syndrome-decoding | 60.1 s | 65.4 s | 1.09× |

B más rápido en **10 de 12** (test de signo p = 0.039); log-ratio medio −0.433
(factor geométrico **0.648×**), Cohen *d* = 0.742, y con eso bastarían ~14
observaciones para 80 % de potencia.

**Esto no se reporta como resultado, y conviene dejar escrito por qué.** Se
encontró *después* de que la métrica preregistrada (PAR-2) no concluyera.
Mirar los datos, no encontrar el efecto en la métrica fijada, y buscarlo en otra
hasta que aparece es exactamente el camino que llevó a B3′ a un −13.4 % que
luego no replicó. La diferencia aquí es que se sabe, y se actúa en
consecuencia: la observación se convierte en **hipótesis preregistrada de
EXP-006**, que se prueba con **datos que no han visto este A/B**.

## 8. Amenazas a la validez, anotadas de antemano

- **El banco local no reproduce el régimen de competición** (EXP-001: ratio
  T/mediana). Un reparto adaptativo tiene más margen cuanto más largo es el
  presupuesto, así que **un resultado nulo a T = 180 s no cerraría la cuestión a
  T = 5000 s**. Se dirá así.
- **Riesgo de sobreajuste en los hiperparámetros** (decay del EMA, cotas del
  reparto). Se fijan **antes** del A/B final y no se tocan después de ver
  `bench/test`. Cualquier ajuste se hace sobre `bench/dev`.
- **La instancia patológica de EXP-003** enseñó que una sola observación puede
  dar la vuelta al agregado. Se reportará siempre el desglose por instancia,
  no solo la media.

## 8. Estado

- [x] `mode.c` leído y el planificador ciego documentado
- [x] Señales disponibles verificadas (`conflicts`, `decisions`, `search_ticks`,
      `clauses_learned` son `COUNTER` → existen en el build de competición)
- [x] Instrumentación de trazas (`src/modetrace.{c,h}`, no-op sin `KISSAT_TRACE`)
- [x] Recogida de trazas sobre `bench/calib` y `bench/calib2` (48 trazas, 1 660 fases)
- [x] **Validación V1/V2/V3: las tres pasan**; la inversión del nivel de GLR se
      replica desde CaDiCaL con magnitudes casi idénticas
- [x] **Implementación del planificador** (ver §5b), con los dos requisitos que
      salen de los datos: EMA **por brazo** y recompensa por **mejora**
- [x] **A/B en `bench/dev`** (ver §7): ΔPAR-2 = −2.222 s, IC95 % incluye el 0
- [ ] ~~Validación en `bench/test`~~ — **no se ejecuta**: el criterio escrito de
      antemano no se cumple, y gastar el banco reservado en una hipótesis no
      confirmada lo quemaría para siempre
- [ ] A/B en `bench/dev` → validación en `bench/test`
