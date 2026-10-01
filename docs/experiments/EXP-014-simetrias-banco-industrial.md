# EXP-014 — Ruptura de simetrías en el banco industrial de la tesis (preregistrado)

- **Estado**: **cerrado (2026-09-30)**: `--symmetry` sigue apagado; el daño en
  la industria es sobre todo coste fijo en instancias triviales (§8.3).
  Preregistrado: se commiteó **antes** de ejecutar las dos
  partes, junto con `scripts/scan_symmetry.py` (parte 1) y
  `scripts/exp014_simetrias.py` (selección y análisis de la parte 2).
  Única ejecución previa: satsuma sobre **una** instancia de station-repacking
  para ver qué informa (1039 generadores, 216 unidades, 50,8 s, casi todo en
  la fase de Schreier). Esa instancia no condiciona ningún umbral.
- **Fecha**: 2026-09-24
- **Decide**: qué cuesta y qué aporta `--symmetry` en instancias
  **industriales**, y aporta los datos de entrenamiento que le faltan a B3
  (EXP-009, issue #15).

---

## 1. Qué se quiere saber

EXP-007 midió la ruptura en el banco de 2026: gana mucho donde hay simetría
explotable (H: 8 → 37 de 45) y **ralentiza 1,42×** en las neutras (N, solo 22
instancias). Su veredicto fue «solo condicional», y el criterio de activación
B3 necesita ejemplos de **cuándo daña**. El banco de la tesis tiene 450
instancias industriales en dev: justo el terreno donde se espera el daño y
donde casi no hay datos.

Además, en el sondeo, satsuma encontró estructura en station-repacking y
agotó casi todo el tope de 60 s. Si eso se repite, el tope actual (P5 del
plan) decide mucho en este banco.

## 2. Hipótesis

> **H1 (parte 1, descriptiva).** Fracción de las 450 instancias de tesis-dev
> en las que satsuma, con los topes de `labesat` (60 s, 512 MiB), termina y
> **añade predicados de ruptura** (`cambia` = 1), por familia; y fracción en la
> que agota el tope. Sin umbral: es la medida que dimensiona la parte 2.
>
> **H2 (parte 2, coste).** En las instancias de S resueltas por las dos ramas,
> el factor geométrico de tiempo B/A (B = con ruptura) tiene el extremo
> superior del IC95 % **≤ 1,10**. Predicción a partir de EXP-007 (N: 1,42×):
> **no se cumple**, es decir, la ruptura daña en la industria.
>
> **H3 (parte 2, efecto en resueltas).** McNemar sobre «solo B resuelve» frente
> a «solo A resuelve» en S. Predicción: sin diferencia significativa.
>
> **Control (vinculante para interpretar).** En las 10 instancias de control
> (`cambia` = 0 y el mismo número de cláusulas a la entrada y a la salida), A y
> B hacen **las mismas propagaciones**. Si no, la reescritura de satsuma cambia
> la búsqueda aunque no rompa nada, y la estimación del §5 se revisa.

## 3. Diseño

### 3.1 Parte 1: solo satsuma (determinista salvo el tope de tiempo)

```bash
nice -n 19 python3 scripts/scan_symmetry.py --bench bench/tesis-dev \
    --out results/exp014/satsuma.csv
```

- Mismos argumentos que `solver/labesat`: `fix --full-skip-limit 100000000
  --add-reduced-as-unit --bsr`, tope de 60 s y 512 MiB.
- Se ejecuta **en paralelo** con la cadena de EXP-008, en un solo proceso y
  con `nice -n 19`. Las columnas de estructura no dependen de la carga; lo
  único que puede cambiar es si una instancia cercana a los 60 s agota el
  tope. Se anota como amenaza (§6).

### 3.2 Parte 2: A/B intercalado sobre S

```bash
python3 scripts/exp014_simetrias.py seleccionar
python3 scripts/run_ab_interleaved.py --solver solver/labesat \
    --bench bench/tesis-dev --instances results/exp014/instancias.txt \
    --out-a results/exp014/A.csv --out-b results/exp014/B.csv \
    --label-a A-sin-simetrias --label-b B-simetrias \
    --opts-a=--no-symmetry --opts-b=--symmetry \
    --guard solver/kissat/build/kissat --guard tools/satsuma \
    --timeout 300 --seeds 42
python3 scripts/exp014_simetrias.py analizar
```

- **S**: instancias con `cambia` = 1. Si hay más de 80, se toman 80
  estratificadas por familia en orden de `md5(hash + sal)`.
- **Controles**: 10 instancias con `cambia` = 0 y el mismo número de
  cláusulas a la entrada y a la salida.
- **T = 300 s** y semilla 42: deja la tanda en ≤ 15 h en el peor caso
  (90 parejas × 2 × 300 s), que es lo que admite la máquina entre otras
  tandas. Con una sola semilla, H2 y H3 se
  interpretan por instancia; la varianza entre semillas no se estima aquí.
- **Cuándo**: después de EXP-013, sin otras tandas de tiempo en la máquina.

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| H2 se cumple (sup ≤ 1,10) y el control pasa | La ruptura **no daña en la industria**: el daño de EXP-007 se concentra en otro tipo de instancia. B3 puede ser más permisivo |
| H2 no se cumple y el control pasa | Confirma EXP-007 en otro dominio. `b3-industrial.csv` son ejemplos negativos para entrenar B3, y `--symmetry` sigue apagado por defecto |
| El control falla | La reescritura de satsuma cambia la búsqueda por sí sola: se investiga antes de usar los datos para B3 |
| H1 da una fracción de `TOPE` ≥ 10 % | Los topes de satsuma (P5) se miden aparte antes de fijarlos: el tope decide qué instancias entran en S |

## 5. Estimación para todo tesis-dev (no es un contraste)

- En las instancias **fuera de S**, el efecto de `--symmetry` es el coste de
  satsuma: se toma `wall_s` de la parte 1 (hasta 60 s si agota el tope),
  sumado al tiempo de A. Esto vale si el control pasa.
- En S, lo medido en la parte 2.
- Se informa ΔPAR-2 de todo dev a T = 300 s con esa composición, etiquetado
  como estimación.

## 6. Amenazas a la validez

- **Carga concurrente en la parte 1**: una instancia en el borde de 60 s
  puede pasar de `OK` a `TOPE` según la carga. Se cuenta cuántas quedan entre
  50 y 60 s.
- **T = 300 s**: las instancias de la tesis que Kissat resolvió en más de
  300 s cuentan como no resueltas en las dos ramas.
- **Semilla única**: mitigado porque la comparación es emparejada y la
  instancia es la unidad de análisis (ADR-0003 §3.2 pide ≥ 3 semillas; se
  hace una excepción por coste, y se declara).
- **Sesgo de selección**: S depende del tope de 60 s. Con otro tope, S sería
  otro.

## 7. Incidencias de ejecución

- **2026-09-24, parte 1.** Lanzada a las 19:18 UTC en paralelo con EXP-008,
  como fija §3.1. Hacia las 19:25 UTC la máquina se quedó sin RAM (ver EXP-008
  §8) con 157 instancias escritas.
  - Se reanuda sola, sin EXP-008 en paralelo, porque el guion salta las ya
    registradas y la medida es de satsuma.
  - Se añade `--mem-gb` (6 GB por defecto, `RLIMIT_AS`) para que una
    instancia grande no pueda agotar la máquina. Si satsuma se queda sin
    memoria, la instancia sale como `FALLO`: en `labesat` no hay tope, así
    que cada `FALLO` se revisa a mano.

## 8. Resultados

### 8.1 Parte 1 (cerrada el 2026-09-24): H1

Datos: `results/exp014/satsuma.csv` (450 instancias, satsuma `9881df0f…`).

| Familia | n | OK | Tope de 60 s | CNF > 512 MiB | **Cambia** (añade ruptura) | Tiempo de satsuma (mediana; máximo) |
|---|---:|---:|---:|---:|---:|---|
| argumentation | 48 | 48 | 0 | 0 | 3 | 0,02 s; 2,2 s |
| bitvector | 48 | 48 | 0 | 0 | 3 | 0,42 s; 10,5 s |
| cryptography | 56 | 56 | 0 | 0 | 2 | 0,20 s; 6,5 s |
| hardware-verification | 45 | 44 | 1 | 0 | 29 | 1,54 s; 60 s |
| miter | 60 | 60 | 0 | 0 | 29 | 0,14 s; 28,0 s |
| planning | 47 | 44 | 2 | 1 | 25 | 0,24 s; 60 s |
| scheduling | 58 | 55 | 3 | 0 | 31 | 0,82 s; 60 s |
| software-verification | 33 | 28 | 4 | 1 | 16 | 3,58 s; 60 s |
| station-repacking | 55 | 55 | 0 | 0 | **55** | **39,1 s**; 48,6 s |
| **Total** | **450** | **438** | **10 (2,2 %)** | **2** | **193 (43 %)** | 0,49 s; media 6,8 s |

- **H1**: satsuma añade predicados de ruptura en el **43 %** de las
  instancias industriales de dev, muchas más de las que sugería el estrato N
  de EXP-007. En station-repacking, en **todas**: mediana de 1067
  generadores y 736 unidades, a un coste de ~39 s cada una.
- **Tope**: 10 instancias (2,2 %) lo agotan, por debajo del umbral del 10 %
  de §4. No hace falta medir los topes aparte antes de la parte 2.
- **Amenaza de la carga concurrente (§6)**: ninguna instancia terminó entre
  50 y 60 s, así que la carga no pudo mover ninguna de `OK` a `TOPE`.
- **|S| = 193 > 80**: la parte 2 toma 80, estratificadas por familia (§3.2).
- **Observación no prevista en el preregistro**: en **222** instancias con
  `cambia` = 0, satsuma **reescribe** la fórmula (cambia el número de
  cláusulas; p. ej., duplicados o unidades). Los controles de la parte 2 se
  eligen, como estaba fijado, entre las que no cambian el número de cláusulas.
  Por eso la estimación del §5 («fuera de S, solo el coste de satsuma») **no
  está cubierta** para esas 222. Se informará con esa salvedad, y no se
  cambia el diseño.

### 8.2 Parte 2 (2026-09-28 a 29): A/B intercalado

`python3 scripts/exp014_simetrias.py analizar` (`results/exp014/informe.txt`).
80 instancias de S (estratificadas sobre las 193) y 10 controles, T = 300 s,
semilla 42, `solver/labesat --symmetry` (B) frente a `--no-symmetry` (A),
con satsuma sin cliques (`tools/satsuma`, como fija §3.2).

| estrato S (80) | A: sin ruptura | B: con ruptura |
|---|---:|---:|
| Resueltas | 61 | 62 |
| PAR-2 | 156,5 s | 159,4 s |

- ΔPAR-2 = **+2,9 s**, IC95 % [−9,0; +10,7]. Wilcoxon p = 0,0002: B es peor
  en la mayoría de instancias, pero por poco.
- **H3** (McNemar): solo B resuelve 1, solo A 0, p = 1. Sin diferencia en
  resueltas, como se predijo.
- **H2** (factor de tiempo B/A en las 61 resueltas por ambas): **4,52×**,
  IC95 % [3,02; 6,92]. **No se cumple** (criterio: superior ≤ 1,10), como se
  predijo: la ruptura cuesta tiempo en la industria.

**Control (vinculante).** Tal como estaba fijado, **falla**: propagaciones
idénticas en 6 de 10. Lo que se investigó, como manda §4:

- 3 de los 4 que difieren terminan en **TIMEOUT** en las dos ramas. Con
  presupuesto de tiempo, las propagaciones hasta el corte dependen del reloj,
  así que no son comparables entre dos corridas. El control solo tiene
  sentido en las resueltas, y eso no se previó en el preregistro.
- El cuarto, `f65e6b35`, sí resuelve, pero satsuma escribió 320 bytes de
  prueba: **no fue una reescritura nula**. Pertenece a las 222 instancias que
  satsuma reescribe sin romper simetrías (§8.1).
- En los **6 controles resueltos en los que satsuma no tocó nada**, las
  propagaciones son **idénticas (6 de 6)**.

Conclusión: cuando satsuma no hace nada, la búsqueda no cambia. Cuando
reescribe aunque no rompa simetrías, la búsqueda **sí** puede cambiar. Los
datos de S valen para B3, con esa salvedad para las 222 instancias
reescritas.

**Veredicto según §4**:

- H2 no se cumple: confirma el daño de EXP-007 en otro dominio;
- `results/exp014/b3-industrial.csv` (80 filas) son los ejemplos industriales
  para entrenar B3;
- **`--symmetry` sigue apagado por defecto**.

### 8.3 De dónde sale el 4,5× (exploratorio, no preregistrado)

| instancias resueltas por ambas | n | factor B/A |
|---|---:|---:|
| A tarda < 10 s | 48 | 6,86× |
| **A tarda ≥ 10 s** | **13** | **0,97×** |

- El factor lo dominan instancias **triviales**: el coste fijo de satsuma
  (mediana 1,8 s, hasta 35 s en station-repacking) se suma a corridas de
  menos de un segundo. En las no triviales, la ruptura **no ralentiza** la
  búsqueda de kissat.
- Por familia, el peor caso es station-repacking (28×), donde satsuma
  gasta ~35 s en la fase de Schreier sobre instancias que kissat resuelve
  enseguida.
- **Idea para B3, sin probar**: aplicar la ruptura **con retraso**. Kissat
  corre solo unos segundos y, si no resuelve, se lanza satsuma y se sigue
  sobre la fórmula con predicados. El coste en las instancias de H de EXP-007
  sería esos segundos de espera; el ahorro, todo el coste fijo en las
  triviales. Se propone para el diseño de EXP-009.

### 8.4 Estimación para todo tesis-dev (§5, no es un contraste)

- En S, ponderado por familia a las 193 instancias: +535 s en total.
- Fuera de S, como cota superior, el tiempo de satsuma en las 257: +748 s.
- **ΔPAR-2 medio de tesis-dev a T = 300 s: entre +1,2 y +2,9 s.** Es un daño
  pequeño, casi todo coste fijo.

### Incidencias de la parte 2

- Una pareja (`ed2af4dc`, bitvector) salió **ERROR en las dos ramas**:
  kissat murió por la señal 16 a los 268 s en A y a los 13 s en B. No hubo
  reinicio ni falta de memoria (30 y 78 MB). Repetida a mano el 2026-09-30,
  termina con normalidad por tiempo, igual que en la tesis (TIMEOUT en las 3
  semillas). Causa sin identificar. Las dos ramas cuentan como no resueltas,
  así que no afecta a la comparación.
- Carga ajena durante la tanda: servicios Docker del director, con un
  arranque de contenedor por minuto aproximadamente. El orden intercalado
  reparte ese ruido entre las dos ramas.
