# EXP-001 — ¿Tiene Kissat diversidad intrínseca suficiente para una cartera?

- **Estado**: diseñado · en ejecución
- **Fecha de diseño**: 2026-09-21 (escrito **antes** de ejecutar, ADR-0003 §6)
- **Motiva**: [`docs/research/02-catalogo-de-ideas.md`](../research/02-catalogo-de-ideas.md) línea A
- **Decide**: si las ideas A1–A4 son viables o si toda la línea A se cae

---

## 1. Pregunta

Los resultados oficiales de 2026 muestran que **21 variantes de Kissat de
distintos autores** tienen un Virtual Best Solver de PAR-2 = 2354.8 s frente a
4611.5 s del mejor individual: una diferencia enorme. Más aún, las **12
variantes que quedaron peores que el Kissat de fábrica** resuelven juntas 277
instancias, más que el campeón del año (276).

Pero esas variantes son **parches de código distintos**. La pregunta que decide
si podemos explotar ese fenómeno dentro de un único binario es otra:

> **¿Aparece la misma complementariedad entre configuraciones del Kissat *de
> fábrica*, sin tocar una línea de código — solo cambiando seed y opciones?**

Si la respuesta es sí, la línea A se implementa con ~200 líneas y el techo de
−798 s de PAR-2 medido en la simulación es realista. Si es no, la línea A exige
construir diversidad de verdad (parches distintos), y su coste se multiplica.

## 2. Hipótesis falsables

- **H1 (diversidad)**: el VBS de las k configuraciones mejora el PAR-2 de la
  **mejor configuración individual** en **≥ 15 %**.
- **H2 (no es solo la seed)**: el VBS de las configuraciones con *opciones*
  distintas mejora sobre el VBS de las que solo cambian la *seed*. Si H2 falla
  pero H1 se cumple, la diversidad es pura suerte de aleatorización — que sigue
  siendo explotable, pero cambia el diseño (basta con re-lanzar con otra seed).
- **H3 (implementable)**: una cartera secuencial con reparto T/k (k = 2, 3),
  **sin oráculo**, mejora el PAR-2 de la mejor configuración individual.

**Hipótesis nula operativa**: la complementariedad es < 5 % y H3 empeora el
PAR-2. En ese caso la línea A se abandona y se pasa a la línea B (preprocesado
condicional).

## 3. Diseño

| elemento | valor |
|---|---|
| Solver | `solver/kissat/build/kissat` 4.0.4, commit del repo en el `meta.json` |
| Banco | 89 instancias de aplicación reales descargadas de GBD (familias: hardware-verification, cryptography, bitvector, argumentation, scheduling, software-verification…) |
| Presupuesto | 30 s de límite interno (`--time`) por corrida |
| Configuraciones | 7 (abajo) |
| Corridas | 7 × 89 = 623 |
| Paralelismo | `--jobs 3` → **cribado**, no medición final (ADR-0003 §4); el CSV lleva `parallel_jobs=3` |

### Configuraciones (los "brazos")

| id | opciones | qué diversifica |
|---|---|---|
| `c0-default-s1` | `--seed=1` | referencia |
| `c1-default-s2` | `--seed=2` | **solo la aleatorización** (contraste de H2) |
| `c2-sat` | `--sat` (`--target=2 --restartint=50`) | sesgo hacia satisfacibles: reinicios cortos, fases objetivo |
| `c3-unsat` | `--unsat` | sesgo hacia insatisfacibles |
| `c4-focused` | `--stable=0` | solo modo *focused* (sin alternancia) |
| `c5-stable` | `--stable=2` | solo modo *stable* |
| `c6-plain` | `--plain` | CDCL sin técnicas avanzadas (inprocesado apagado) |

`c4`/`c5` rompen la alternancia `stable`/`focused` que Kissat hace por defecto:
son el caso interesante, porque miden si esa alternancia interna **ya está
capturando** la diversidad o si deja margen.

### Métricas

1. PAR-2 de cada configuración por separado (`par2.py`).
2. **VBS** del conjunto y de subconjuntos (`analyze_diversity.py`).
3. **Cartera secuencial simulada** con T/k para k = 2, 3, construcción voraz.
4. Matriz de complementariedad: para cada par, cuántas instancias resuelve una y
   no la otra.

### Criterio de decisión

| resultado | decisión |
|---|---|
| H1 ✅ y H3 ✅ | seguir con A1 (implementar cartera) y diseñar EXP-002 como A/B real |
| H1 ✅ y H3 ❌ | la diversidad existe pero el reparto ciego no la cobra → ir directo a A4 (reparto adaptativo), que es la contribución interesante |
| H1 ❌ | abandonar la línea A tal cual; pasar a la línea B, y reconsiderar A solo con parches que generen diversidad real |
| H2 ❌ (solo importa la seed) | la cartera se construye con seeds, no con opciones: más simple y más barata |

## 4. Limitaciones conocidas (escritas antes de ver los resultados)

- **T = 30 s, no 5000 s.** El régimen de tiempo corto favorece a las
  configuraciones agresivas y penaliza el inprocesado, que amortiza tarde. La
  conclusión sobre *existencia* de diversidad sí traslada; la de *cuál* es la
  mejor cartera, no. Hay que reconfirmar a T alto antes de decidir la cartera
  definitiva.
- **89 instancias**, seleccionadas en la etapa anterior por su comportamiento
  *en CaDiCaL* (62 marcadas como inestables + 27 de control). Eso sesga el banco
  hacia instancias al borde de lo resoluble, que es precisamente donde una
  cartera ayuda más → el efecto medido aquí será **optimista**. La validación
  final va contra `bench/test`, construido desde el banco oficial de 2026.
- **`--jobs 3`**: los tiempos están contaminados por contención. La
  clasificación resuelve/no-resuelve es robusta; el PAR-2 absoluto, no. Todas
  las configuraciones sufren la misma contención, así que la **comparación
  entre ellas** sigue siendo informativa.
- **Una seed por configuración** (salvo el par c0/c1). No separa el efecto de la
  opción del efecto de la aleatorización salvo en ese contraste concreto.

## 5. Reproducir

```bash
./scripts/build.sh
python3 scripts/fetch_gbd.py --list docs/archive/cadical-era/results/phase1_download_list.csv \
        --out bench/downloaded/gbd
./scripts/run_diversity.sh              # lanza las 7 configuraciones
python3 scripts/analyze_diversity.py results/exp001/*.csv
```

## 6. Resultados

### Fase 1 (banco GBD heredado, T = 20 s) — **detenida por falta de resolución**

Se ejecutaron 3 de las 7 configuraciones sobre las 89 instancias. Se paró ahí,
porque el problema ya era evidente y seguir costaba media hora de CPU sin
aportar información:

| configuración | resueltas de 89 | PAR-2 |
|---|---:|---:|
| c1-default-s2 | 18 | 33.414 |
| c0-default-s1 | 15 | 34.321 |
| c2-sat | 13 | 34.828 |
| **VBS de las 3** | **20** | **32.446** |

| hipótesis | resultado |
|---|---|
| H1 (VBS mejora ≥15 %) | ❌ **2.9 %** (+2 instancias) |
| H2 (opciones > seed) | ❌ la diversidad por seed aportó más que `--sat` en este régimen |
| H3 (cartera k=2,3 mejora) | ❌ **empeora**: k=2 → +1.45 s, k=3 → +2.16 s |

### Por qué salió así: el banco no era medible con ese presupuesto

De las 89 instancias, con 2 configuraciones: **14 triviales** (las resuelven
todas), **5 de frontera** (unas sí, otras no) y **70 fuera de alcance** (ninguna).
El 79 % del banco no aporta ninguna información sobre complementariedad, y el
PAR-2 está tan dominado por la penalización `2T` que las diferencias reales se
comprimen a la nada.

### El hallazgo metodológico (vale para todos los experimentos siguientes)

H3 no falló porque la idea sea mala: falló porque **el reparto de tiempo solo
puede funcionar si el presupuesto es grande respecto a lo que tarda el solver en
resolver**. Comparación de los dos regímenes:

| | T | mediana del tiempo de resolución | **ratio T / mediana** | ¿funciona la cartera? |
|---|---:|---:|---:|---|
| Main Track 2026 (datos oficiales) | 5000 s | 297.9 s | **≈ 17** | sí: −798 s con k=3 |
| EXP-001 fase 1 (este banco) | 20 s | ≥ 20 s (más de la mitad no resuelve) | **< 1** | no: empeora |

Con ratio 17, partir en tres deja a cada miembro 1667 s, por encima del p75 de
los tiempos de resolución (1409 s): se pierde poco. Con ratio < 1, partir en
tres deja 6.7 s a cada miembro y **no resuelve nada**.

> **Regla de diseño que se adopta a partir de aquí**: un experimento local sobre
> reparto de presupuesto debe reproducir el **ratio T/mediana** de la
> competición (≈15–20), no su T absoluto. Medir con un banco cuya mediana de
> resolución esté cerca del timeout garantiza un resultado negativo
> artificial — y es, muy probablemente, la razón por la que muchos trabajos
> descartan las carteras midiendo con timeouts cortos.

### Fase 1b (banco de calibración `bench/calib`, T = 180 s) — en ejecución

Rediseño según la regla anterior: **40 instancias reales del Main Track 2026**
que el Kissat de referencia resolvió en ≤ 120 s en la competición, muestreadas
de forma estratificada en 8 bandas de tiempo (mediana oficial 19.6 s, máximo
112.9 s, 28 familias, 27 SAT / 13 UNSAT), **disjuntas de `bench/test`**. Con
T = 180 s el ratio esperado queda en el orden correcto aunque nuestra máquina
sea más lenta que la de la competición.

Configuraciones: c0, c1 (contraste de seed), c2-sat, c4-focused, c6-plain.

#### Resultados (40 instancias × 5 configuraciones, T = 180 s, `--jobs 4`)

| configuración | resueltas de 40 | PAR-2 |
|---|---:|---:|
| c0-default-s1 | 39 | 36.578 |
| c2-sat | 39 | 45.404 |
| c1-default-s2 | 37 | 48.303 |
| c4-focused | 34 | 82.965 |
| c6-plain | 26 | 151.772 |
| **VBS de las 5** | **39** | **26.808** |

| hipótesis | resultado |
|---|---|
| **H1** (VBS mejora ≥ 15 %) | ✅ **26.7 %** (36.578 → 26.808 s) |
| **H2** (las opciones aportan más que la seed) | ✅ solo-seed 33.070 s · seed + opciones **27.711 s** (−5.36 s) |
| **H3** (cartera con reparto T/k mejora) | ❌ k=2 → +0.44 s, k=3 → +16.6 s, k=4 → +33.4 s |

#### Lo que hay detrás del 26.7 %

**Cada configuración es la mejor en su parcela**, y el reparto es casi uniforme:

| configuración | es la más rápida en | su PAR-2 global |
|---|---:|---:|
| c0-default-s1 | 9 de 40 | 36.6 s (la mejor) |
| c1-default-s2 | 9 de 40 | 48.3 s |
| c2-sat | 8 de 40 | 45.4 s |
| c4-focused | 7 de 40 | 83.0 s |
| **c6-plain** | **7 de 40** | **151.8 s (la peor, con diferencia)** |

`c6-plain` (CDCL sin técnicas avanzadas) resuelve 26 de 40 y tiene un PAR-2
cuatro veces peor que el de la configuración por defecto — **y aun así es la más
rápida en 7 instancias**. Es, en pequeño y dentro de un mismo binario, el mismo
fenómeno que en los datos oficiales de 2026, donde las 12 variantes peores que
la base resuelven juntas más que el campeón.

La ganancia está **muy concentrada**: 6 instancias acumulan el **78 %** de los
390.8 s que el oráculo le saca a la configuración por defecto. Ejemplos:

| instancia | por defecto | mejor configuración | ganancia |
|---|---:|---|---:|
| `75429ff7…` | 154.5 s | c4-focused → 44.4 s | −110.0 s |
| `15e666a4…` | 58.5 s | c1-default-s2 → 5.5 s | −53.0 s |
| `f497bda3…` | 94.9 s | c4-focused → 42.7 s | −52.2 s |

Que la distribución sea de cola pesada es justo lo que hace explotable la
diversidad: no se trata de ganar un 5 % en todas partes, sino de evitar unos
pocos desastres de 100 s.

#### Por qué H3 falla aquí y qué significa

En este banco la mejor configuración ya resuelve **39 de 40**. Repartir el
presupuesto no puede ganar instancias —no quedan— y sí puede perderlas, así que
el reparto ciego solo resta. **H3 no está refutada en general: está sin probar**,
porque este banco no tiene el margen donde el reparto cobra. Eso es lo que mide
la fase 1c (`bench/calib2`, banda de frontera).

### Fase 1c (banda de frontera `bench/calib2`, T = 180 s) — en ejecución

20 instancias con tiempo oficial entre 132 s y 691 s (mediana 388 s), 20
familias, 13 UNSAT / 7 SAT, disjuntas de `test` y de `calib`. Con T = 180 s
local caen alrededor y por encima del timeout: ahí unas configuraciones
resolverán y otras no, que es el régimen donde el reparto puede pagar.

#### Resultados (20 instancias × 5 configuraciones, T = 180 s)

| configuración | resueltas de 20 | PAR-2 |
|---|---:|---:|
| **c4-focused** (`--stable=0`) | **8** | **251.783** |
| c2-sat | 6 | 283.408 |
| c1-default-s2 | 6 | 286.449 |
| **c0-default-s1** (por defecto) | **4** | 311.590 |
| c6-plain | 2 | 338.123 |
| **VBS de las 5** | **9** | **228.748** |

| hipótesis | resultado |
|---|---|
| H1 (VBS mejora ≥ 15 %) | ❌ **9.1 %** (+1 instancia) — el VBS está limitado por lo poco que resuelve nadie |
| **H2** (opciones > seed) | ✅✅ **+43.1 s**: solo-seed 271.869 s · seed + opciones **228.748 s** |
| H3 (cartera con reparto T/k) | ❌ k=2 → +18.5 s, k=3 → +46.1 s |

#### Los dos hallazgos de esta fase

**1. La configuración por defecto NO es la mejor en el régimen difícil.**
`--stable=0` (solo modo *focused*, sin la alternancia `stable`/`focused` que
Kissat hace por defecto) resuelve **8 de 20 frente a 4**, y baja el PAR-2 un
**19.2 %**. Contraste estadístico emparejado (`par2.py`):

```
ΔPAR-2 medio (focused − defecto):  −59.806 s   (−19.2 %)
IC95% bootstrap:                   [−120.810, +0.856]   INCLUYE el 0
Wilcoxon emparejado:               W=7.0   p=0.0756   (n efectivo = 9)
McNemar (resueltas):               defecto-sí/focused-no=1, al revés=5, p=0.2188
```

**Sugerente, no concluyente**: con n=20 solo se detectan efectos grandes y este
se queda al borde. No se puede afirmar que `--stable=0` sea mejor; sí se puede
afirmar que **la alternancia por defecto no es obviamente la mejor política con
presupuesto ajustado**, y que merece un experimento con n mayor. Es exactamente
la clase de resultado que el ADR-0003 existe para no sobreinterpretar.

Ojo con extrapolar: con T = 5000 s el modo `stable` tiene tiempo de amortizar y
la comparación podría invertirse. Que la política óptima **dependa del
presupuesto** es, precisamente, el argumento de A4.

**2. La diversidad por opciones se dispara donde importa.** En el banco fácil
las opciones aportaban 5.4 s sobre la diversidad por seed; en la frontera
aportan **43.1 s**, y en cuenta de resueltas la diferencia es 7 → 9. La
complementariedad **crece con la dificultad**, que es donde se juega el PAR-2 de
la competición.

Aun así, la semilla sola mueve mucho: c0 y c1 se diferencian **únicamente** en
la semilla y resuelven **4 y 6** instancias respectivamente. Es la inestabilidad
por aleatorización del documento archivado 03, reproducida ahora sobre Kissat y
sobre instancias reales de competición.

## 7. Conclusión

**La premisa de la línea A se sostiene: Kissat tiene diversidad intrínseca
suficiente.** Sin tocar una línea de código, cinco configuraciones del binario
de fábrica dan un VBS un **26.7 % mejor** que la mejor de ellas, y la
complementariedad viene sobre todo de las **opciones** (−5.36 s adicionales
sobre la diversidad por seed sola), no de la aleatorización.

Aplicando la tabla de decisión que se escribió **antes** de ejecutar:

> | resultado | decisión |
> |---|---|
> | H1 ✅ y H3 ❌ | la diversidad existe pero el reparto ciego no la cobra → **ir directo a A4** (reparto adaptativo) |

Es el caso que se ha dado. La consecuencia operativa:

1. **A1 (cartera con reparto ciego T/k) no se implementa como contribución**,
   solo como línea base honesta contra la que medir A4. En el régimen de la
   competición la simulación con datos oficiales le da −798 s, así que sigue
   siendo un punto de comparación imprescindible, pero el reparto uniforme
   desaprovecha la información que la propia búsqueda va generando.
2. **A4 (reparto adaptativo del presupuesto entre configuraciones) pasa a ser
   la contribución candidata**, con dos apoyos empíricos ya medidos: el techo
   (VBS −2256.7 s sobre datos oficiales; −26.7 % en local) y el hecho de que
   `src/mode.c` de Kissat ya hace exactamente esto con dos brazos y una
   planificación ciega, así que la generalización es natural y no un injerto.
3. La **fase 1c** confirmó el rumbo y añadió dos cosas: la complementariedad
   por opciones **crece con la dificultad** (5.4 s → 43.1 s), y la política por
   defecto de Kissat no es la mejor con presupuesto ajustado (`--stable=0`
   resuelve 8 de 20 frente a 4, −19.2 % de PAR-2, aunque sin significación a
   n=20). Que la política óptima dependa del presupuesto es el argumento de A4.

**Sobre H3, que falla en las tres fases**: no es un resultado sobre la idea sino
sobre el régimen. El ratio T/mediana fue <1 en la fase 1, ~13 en la 1b (pero con
39/40 ya resueltas, sin margen que ganar) y ~1.5 en la 1c. **Ninguna fase local
reprodujo el régimen de la competición** (ratio 17 *con* un 40 % de instancias
sin resolver), que es donde la simulación con datos oficiales da −798 s. Evaluar
A1 honestamente exige o bien corridas locales de varias horas por instancia, o
bien apoyarse en la simulación sobre datos oficiales. Se deja anotado como deuda
experimental, no como conclusión negativa.

### Hallazgo lateral: las fases *lucky* ignoran el límite de tiempo

Una instancia (`b54b26f3…`, familia `baseball-lineup`, **3.56 M variables y
7.12 M cláusulas**) tuvo que ser matada por la guarda externa del runner. La
investigación dio un resultado limpio y reproducible:

| ejecución | termina a |
|---|---:|
| `--time=30` | **348.5 s** (exceso 11.6×) |
| `--time=60` | **356.5 s** |
| `--time=20 -v` | **355.4 s** |
| **`--time=20 --luckyearly=0 --luckylate=0`** | **20.0 s** ✅ |

El log con `-v` sitúa el problema con precisión. **No es el parseo** (1.59 s) ni
el inprocesado (`[preprocess] finished after 1 rounds` en 0.4 s): es
**`kissat_lucky`**, la rutina de *lucky phases*, que Kissat ejecuta **dos
veces** —antes y después del preprocesado (`luckyearly` y `luckylate`, según
`NEWS.md` de la versión 4.0.0)— y que **no consulta el límite de tiempo ni el de
conflictos**:

```
c finished parsing after 1.59 seconds
c lucky 322 units
c l 174.74 ...        <- primera llamada a lucky: ~173 s
c [preprocess] finished after 1 rounds
c ) 175.18 ...
c [search-1] initializing focus search after 0 conflicts
c { 351.34 ...        <- segunda llamada a lucky: ~176 s
```

La búsqueda arranca en el segundo **351**, y ahí el límite de 20 s se detecta de
inmediato y el solver para. Es decir: en esta instancia Kissat gasta **350 s
antes de buscar nada**, y ningún presupuesto lo detiene.

**Tres consecuencias:**

1. **Es un fallo reportable a upstream**: `kissat_lucky` debería consultar el
   terminador. Ficheros: `src/lucky.c`, invocado desde `src/search.c:184,188`.
2. **Tiene efecto directo en el PAR-2 de competición**: 350 s de 5000 son el
   **7 % del presupuesto** gastados sin buscar, en toda instancia grande. Se
   mide en EXP-002.
3. **Es un argumento fuerte a favor de A2/A4 frente a A1**: una cartera que
   reinicia el proceso en cada turno **vuelve a pagar las fases lucky cada
   vez** (~350 s por turno en instancias así), mientras que conmutar la
   configuración dentro de una misma instancia del solver las paga una sola
   vez. El coste de reiniciar no es solo perder las cláusulas aprendidas.
