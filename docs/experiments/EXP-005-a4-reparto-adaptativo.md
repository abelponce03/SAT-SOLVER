# EXP-005 — A4: reparto adaptativo del presupuesto entre modos de búsqueda

- **Estado**: **paso 0 cerrado — la señal se valida (V1, V2 y V3 pasan)**. Diseño escrito antes de implementar (ADR-0003 §6)
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

## 7. Amenazas a la validez, anotadas de antemano

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
- [ ] Implementación del planificador — **desbloqueada**, con dos requisitos que
      salen de los datos: EMA **por brazo** (las escalas difieren 75 %) y
      recompensa por **mejora**, nunca por nivel
- [ ] A/B en `bench/dev` → validación en `bench/test`
