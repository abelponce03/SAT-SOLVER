# Investigación 01 — Qué dicen los resultados oficiales de la SAT Competition 2026

> **Propósito**: antes de proponer ninguna mejora, medir *dónde está el margen*
> usando la única evidencia no opinable que existe: la matriz de resultados
> instancia-por-instancia de la edición 2026, publicada por los organizadores.
>
> **Reproducir**:
> ```bash
> ./scripts/fetch_competition_data.sh 2026
> python3 scripts/analyze_competition.py headroom --md
> python3 scripts/analyze_competition.py ranking --md
> python3 scripts/analyze_competition.py families --solver anders_satsuma-iter-kissat
> python3 scripts/analyze_competition.py vbs --pattern kissat --exclude 'satsuma|sup|isasat'
> python3 scripts/analyze_competition.py portfolio --k 4
> ```
> Datos: `scores.csv` de satcompetition.github.io (33 solvers × 400 instancias)
> + metadatos de familia de la Global Benchmark Database. Timeout oficial
> T = 5000 s; PAR-2 = tiempo si resuelve, 10 000 s si no.

---

## 0. Resumen en cinco líneas

1. Nuestra base (Kissat de fábrica) resolvió **238/400** con **PAR-2 = 4611.5 s**.
2. El ganador de 2026 (`satsuma-iter-kissat`) es **Kissat + ruptura de simetrías**
   y saca **−964.5 s** de PAR-2 (+38 instancias). Todo su margen viene de
   familias simétricas.
3. **Casi todas las variantes con bandit (MAB) de 2026 quedaron igual o PEOR que
   el Kissat de fábrica.** La línea "poner un MAB en Kissat" está saturada.
4. El **VBS de 21 variantes de Kissat es PAR-2 = 2354.8 s (321 resueltas)**:
   elegir bien *qué Kissat* usar en cada instancia valdría **−2256.7 s**, más del
   doble de lo que ganó el campeón. La complementariedad entre configuraciones
   es el recurso peor explotado de todo el campo.
5. Y no hace falta oráculo: una **cartera secuencial con reparto de tiempo**
   (3 configuraciones, T/3 cada una, dentro de un único binario) ya da
   **−798.4 s (+36 instancias)** sobre la base con la regla real de la Main Track.

---

## 1. La foto: PAR-2 de cada entrada frente a nuestra base

Referencia `biere_kissat-biere[main]` — el Kissat de Armin Biere, que es
esencialmente nuestro punto de partida. `vs_base` negativo = mejor que la base.

| solver | resueltas | PAR-2 | vs_base | VBS con la base |
|---|---:|---:|---:|---:|
| anders_satsuma-iter-kissat | 276 | 3647.0 | **−964.5** | −1286.9 |
| anders_satsuma-iter-ae-kissat-mab | 269 | 3696.8 | −914.7 | **−1495.0** |
| zheng_kissat-mab-hypre | 255 | 3996.3 | −615.3 | −1230.0 |
| zheng_kissat-mab-hypre-v2 | 255 | 3997.3 | −614.3 | −1217.1 |
| green_lymphosat | 251 | 4176.9 | −434.6 | −854.4 |
| oertel_satsuma-lex-kissat | 249 | 4279.6 | −332.0 | −730.5 |
| zhenwei_mergesat-l | 245 | 4385.8 | −225.7 | −559.5 |
| yalun_kissat-eda-{1..4} | 236–242 | 4469–4570 | −142 … −41 | −520 … −391 |
| **biere_kissat-biere (base)** | **238** | **4611.5** | **0.0** | 0.0 |
| guo_kissat-ae-eg | 235 | 4636.5 | +25.0 | −418.5 |
| liang_kissat-mab-da | 236 | 4640.4 | +28.8 | −472.8 |
| ding_kissat-mab-eae1 | 228 | 4709.9 | +98.4 | −429.3 |
| gopalan_kissat-evolve* | 222–228 | 4726–4848 | +114 … +237 | −454 … −403 |
| guo_kissat-ae-hucb | 227 | 4744.3 | +132.7 | −363.7 |
| liang_kissat-lr-ds | 221 | 4868.9 | +257.3 | −280.0 |
| reeves_cadical-xlc-freeze | 221 | 4980.5 | +369.0 | −431.1 |
| biere_cadical3 | 205 | 5260.2 | +648.7 | −228.4 |

*(tabla completa: `python3 scripts/analyze_competition.py ranking --md`)*

### Lectura 1 — la migración a Kissat queda confirmada por los números de 2026

CaDiCaL 3 resolvió **205** frente a los **238** de Kissat: **+648.7 s de PAR-2 de
desventaja**, un 14 % peor. Partir de CaDiCaL habría significado empezar 33
instancias por detrás (ADR-0001, ahora con evidencia de la edición más reciente
y no solo del dataset de tesis).

### Lectura 2 — la línea de los bandits está saturada

De las entradas con MAB explícito en el nombre (`*-mab-*`, `*-ae-*`, `*-eae*`,
`*-hucb`, `*-evolve`), **solo las que además llevan otra cosa** (hypre, satsuma)
superan al Kissat de fábrica. Las que aportan *solo* el bandit quedan entre
**+25 y +280 s peor**. Cuatro grupos independientes (Ding, Gopalan, Guo, Liang)
presentaron variantes de bandit y ninguna batió a la base por sí sola.

> Esto **cambia la recomendación del documento archivado 06**, que en su momento
> (con datos de 2025) proponía B+D: bandit con recompensa mejor. Con los datos de
> 2026, el bandit por sí solo no es un vehículo de mejora de PAR-2: es un
> multiplicador pequeño y ruidoso sobre una base que ya está muy afinada.
> Se mantiene como componente posible **dentro** de una idea mayor, no como idea.

### Lectura 3 — el margen está en el preprocesado estructural… y en la diversidad

Lo que sí ganó fue **transformar la fórmula antes de buscar**: ruptura de
simetrías (satsuma, −964 s) e hiper-resolución binaria (hypre, −615 s).

---

## 2. Dónde gana el campeón: desglose por familia

`satsuma-iter-kissat` vs la base, familias con mayor diferencia (ΔPAR-2 < 0 = gana el campeón):

| familia | n | base resueltas | base PAR-2 | satsuma resueltas | satsuma PAR-2 | ΔPAR-2 |
|---|---:|---:|---:|---:|---:|---:|
| relativized-pigeon-hole | 1 | 0 | 10000.0 | 1 | 0.1 | −9999.9 |
| clique-coloring | 2 | 0 | 10000.0 | 2 | 0.1 | −9999.9 |
| chnl | 6 | 0 | 10000.0 | 6 | 0.1 | −9999.9 |
| count | 6 | 0 | 10000.0 | 6 | 0.8 | −9999.2 |
| ordering-principle-xor | 1 | 0 | 10000.0 | 1 | 141.2 | −9858.9 |
| exam-scheduling | 12 | 1 | 9271.1 | 12 | 1.6 | −9269.6 |
| sudoku-php | 2 | 1 | 7171.0 | 2 | 0.0 | −7171.0 |
| graph-coloring | 25 | 10 | 6113.2 | 22 | 1325.4 | −4787.7 |
| boxfolding | 16 | 9 | 5530.8 | 13 | 3956.5 | −1574.3 |
| lights-out | 7 | 5 | 3876.0 | 5 | 3360.2 | −515.9 |

Y donde **pierde** (la ruptura de simetrías también hace daño):

| familia | n | ΔPAR-2 |
|---|---:|---:|
| oddball-weighing | 1 | +9585.1 |
| st-connectivity-principle | 1 | +7761.7 |
| fermat | 1 | +7749.4 |
| sorting-networks | 4 | +1958.8 |
| argumentation | 15 | +660.1 |

**Tres conclusiones operativas:**

1. El margen del campeón es **binario y concentrado**: familias que la base no
   resuelve *en absoluto* (0/6 en `chnl`, 0/2 en `clique-coloring`, 0/6 en
   `count`) y que con simetrías se resuelven en **décimas de segundo**. No es
   una mejora de velocidad: es un cambio de complejidad efectiva.
2. `kissat-mab-hypre` gana en **las mismas familias** (chnl, clique-coloring,
   exam-scheduling, count, sudoku-php) con una técnica distinta
   (hiper-resolución binaria). Es decir: esas familias están **infra-atacadas
   por el preprocesado por defecto de Kissat**, y hay más de un camino para
   entrarles.
3. El preprocesado agresivo tiene **coste asimétrico**: convierte 0→1 en unas
   familias y 1→0 en otras (fermat, st-connectivity, oddball-weighing). Eso
   sugiere de inmediato una idea: **aplicarlo condicionalmente**, no siempre.

> Salvedad de generalización: el banco de 2026 es inusualmente rico en
> combinatoria simétrica (graph-coloring 25, boxfolding 16,
> cyclic-anti-bandwidth 16, van-der-waerden 12, exam-scheduling 12…). El banco
> de 2027 se compondrá con el mismo script público, pero de otras sumisiones.
> Cualquier apuesta 100 % a simetrías es una apuesta a la composición del banco.

---

## 3. El hallazgo principal: la complementariedad entre configuraciones

| estrategia | resueltas | PAR-2 | Δ vs base |
|---|---:|---:|---:|
| Kissat de referencia (nuestra base) | 238 | 4611.5 | 0.0 |
| Mejor entrada de 2026 (`satsuma-iter-kissat`) | 276 | 3647.0 | −964.5 |
| **VBS de 21 variantes de Kissat (oráculo)** | **321** | **2354.8** | **−2256.7** |
| VBS de los 33 solvers (oráculo, techo absoluto) | 354 | 1495.5 | −3116.0 |
| Cartera secuencial voraz k=3 (**sin oráculo**) | 274 | 3813.1 | −798.4 |

Léase con cuidado, porque es el número que orienta todo el proyecto:

- **321 de 400**: si en cada instancia se pudiera elegir *cuál* de las 21
  variantes de Kissat ejecutar, se resolverían 83 instancias más que con la
  mejor de ellas en solitario. El campeón, con su técnica nueva, llegó a 276.
- Dicho de otro modo: **la varianza entre configuraciones de un mismo motor es
  un recurso mayor que la mejor técnica nueva publicada ese año**, y nadie la
  está cobrando.
- Restringiendo el conjunto a las variantes de Kissat **sin** satsuma y sin las
  entradas del track experimental (`--pattern kissat --exclude 'satsuma|sup|isasat'`),
  el VBS sigue en **311 resueltas / PAR-2 2583.0** (−2028.6 s): el efecto **no**
  depende de la ruptura de simetrías.
- Solvers **peores que la base en solitario** aportan muchísimo al VBS: por
  ejemplo `ding_kissat-mab-eae1` es +98 s peor, y sin embargo VBS(base, eae1) =
  −429 s. Son *diferentes*, no mejores. Para una cartera, diferente vale más que
  mejor.

### Lo alcanzable sin oráculo

La Main Track secuencial da un núcleo y T = 5000 s. Dentro de un único binario
se puede repartir ese presupuesto entre k configuraciones ejecutadas una tras
otra. Construyendo la cartera de forma voraz:

| k | resueltas | PAR-2 | Δ vs k=1 | añadido |
|---:|---:|---:|---:|---|
| 1 | 238 | 4611.5 | 0.0 | `kissat-biere` (base) |
| 2 | 264 | 4074.0 | −537.5 | `satsuma-iter-ae-kissat-mab` |
| 3 | 274 | 3813.1 | −798.4 | `lymphosat` |
| 4 | 273 | 3811.5 | −800.0 | `mergesat` (ya no compensa) |

Con **k = 3** se llega a 274 resueltas, a dos del campeón de 2026, **sin ninguna
técnica nueva**: solo repartiendo el tiempo entre tres motores distintos. Y k=4
ya no aporta: el reparto empieza a castigar más de lo que la diversidad añade.

**Esta simulación es una cota, no un resultado nuestro**, por dos motivos que
hay que repetir cada vez que se cite: (a) los miembros son solvers ajenos, no
configuraciones de nuestro binario; (b) la construcción voraz elige los miembros
mirando el mismo banco en el que se evalúa (sobreajuste de selección). La
pregunta que abre —*¿basta con diversificar Kissat consigo mismo?*— es
directamente medible en local y es el experimento EXP-001.

---

## 4. Qué se lleva el proyecto de aquí

| Hallazgo | Consecuencia para el plan |
|---|---|
| CaDiCaL 205 vs Kissat 238 en 2026 | ADR-0001 confirmado con datos de la última edición |
| Los bandits solos no baten a la base (4 grupos, 2026) | El "reset-bandit" deja de ser la idea principal; baja a componente |
| El campeón gana por preprocesado estructural en familias que la base no toca | Línea A del catálogo: preprocesado condicional (simetrías/hypre) |
| El preprocesado agresivo rompe otras familias | Cualquier preprocesado nuevo debe ir **condicionado**, no incondicional |
| VBS de configuraciones de Kissat = −2256.7 s | Línea B del catálogo: explotar la diversidad (cartera/selección), la de mayor techo medido |
| Cartera secuencial k=3 sin oráculo = −798.4 s | Hay versión implementable y barata de la línea B; medir en local primero (EXP-001) |

El catálogo completo de ideas, con techo estimado y diseño experimental para
cada una, está en [`02-catalogo-de-ideas.md`](02-catalogo-de-ideas.md).

## Fuentes

- Resultados oficiales SAT Competition 2026: https://satcompetition.github.io/2026/
  (`downloads/scores.csv`, `downloads/track_main_2026.uri`, `downloads/satcomp26slides.pdf`)
- Global Benchmark Database (familias, metadatos): https://benchmark-database.de/
- Análisis reproducible: `scripts/analyze_competition.py` en este repositorio.
