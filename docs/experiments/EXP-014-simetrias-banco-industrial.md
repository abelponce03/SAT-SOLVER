# EXP-014 — Ruptura de simetrías en el banco industrial de la tesis (preregistrado)

- **Estado**: **preregistrado**. Se commitea **antes** de ejecutar las dos
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
