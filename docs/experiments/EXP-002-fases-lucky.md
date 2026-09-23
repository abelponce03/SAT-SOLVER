# EXP-002 — Las fases *lucky* de Kissat: coste, beneficio y cuándo aplicarlas

- **Estado**: cerrado (con validación final pendiente sobre `bench/test`)
- **Fecha**: 2026-09-21
- **Origen**: hallazgo lateral de [EXP-001](EXP-001-diversidad-intrinseca-kissat.md)
- **Motiva**: catálogo línea **B3** (condicionar técnicas caras)

---

## 1. De dónde sale

EXP-001 detectó que una instancia ignoraba `--time=180` durante minutos. El
diagnóstico resultó limpio: **`kissat_lucky` no consulta el límite de tiempo ni
el de conflictos**, y en una instancia de 3.56 M variables consume ~175 s en
cada una de sus dos llamadas (`luckyearly` antes del preprocesado y `luckylate`
después).

| ejecución | termina a |
|---|---:|
| `--time=30` | 348.5 s (**11.6×** el límite) |
| `--time=60` | 356.5 s |
| `--time=20 --luckyearly=0 --luckylate=0` | **20.0 s** |

De ahí la pregunta obvia: **¿compensan las fases lucky su coste?**

## 2. Hipótesis (escrita antes de correr)

> Las fases lucky gastan un tiempo desproporcionado en fórmulas grandes sin
> aportar nada, así que desactivarlas debería mejorar el PAR-2, sobre todo en
> las instancias más grandes.

**Esta hipótesis resultó falsa en su parte causal, y del modo más informativo.**

## 3. Diseño

Mismo binario, `--luckyearly=0 --luckylate=0` frente a por defecto, sobre los dos
bancos de EXP-001 (T = 180 s, una seed, `--jobs 4`):

- `bench/calib`: 40 instancias del Main Track 2026 resueltas en ≤120 s en la competición
- `bench/calib2`: 20 instancias de frontera (132–691 s en la competición)

## 4. Resultados

### Los dos bancos se contradicen

**Banda de frontera** (`bench/calib2`, 20 instancias):

| | resueltas | PAR-2 |
|---|---:|---:|
| por defecto (lucky activado) | 4/20 | 311.590 |
| **sin lucky** | **8/20** | **258.651** |

```
ΔPAR-2 = −52.939 s  (−17.0 %)
IC95% bootstrap = [−101.666, −11.681]   EXCLUYE el 0
Wilcoxon p = 0.0587   ·   McNemar: 0 perdidas / 4 ganadas (p = 0.125)
```

**Banco fácil** (`bench/calib`, 40 instancias): **lo contrario, y con más fuerza.**

```
ΔPAR-2 = +33.929 s  (+92.8 % PEOR)
IC95% bootstrap = [+8.234, +65.018]   EXCLUYE el 0
Wilcoxon p = 0.0019   ·   McNemar: 3 perdidas / 0 ganadas
```

Sobre los 60 juntos, desactivarlas sale **+4.97 s peor**: ninguna de las dos
decisiones fijas es buena.

### Por qué: el mecanismo es el opuesto al que suponíamos

Desglosando la diferencia por tamaño de fórmula:

| grupo | n | suma de ΔPAR-2 al desactivar lucky |
|---|---:|---:|
| **> 1 M variables** | 6 | **+683.2 s (mucho PEOR sin lucky)** |
| ≤ 1 M variables | 54 | **−384.8 s (mejor sin lucky)** |

Las mayores pérdidas al desactivarlas son instancias **gigantes que pasan de SAT
a TIMEOUT**:

| variables | con lucky | sin lucky | Δ |
|---:|---|---|---:|
| 32,170,813 | SAT | TIMEOUT | +311.6 |
| 17,518,343 | SAT | TIMEOUT | +332.1 |
| 13,475,543 | SAT (rápida) | SAT (lenta) | +117.8 |

Y las mayores ganancias son instancias **pequeñas o medianas** donde lucky solo
gastaba tiempo:

| variables | con lucky | sin lucky | Δ |
|---:|---|---|---:|
| 361 | TIMEOUT | SAT | −321.2 |
| 3,560,698 | (matada por la guarda) | SAT | −277.2 |
| 16,520 | TIMEOUT | UNSAT | −220.0 |

**Las fases lucky hacen exactamente aquello para lo que existen**: resolver de
golpe fórmulas enormes y estructuralmente triviales, probando asignaciones
constantes y hacia delante/atrás. En fórmulas de decenas de millones de
variables son la razón de que se resuelvan. En las demás, son peaje.

Nuestra hipótesis inicial —"gastan de más en las grandes"— confundió un caso
(una instancia de 3.5 M donde el peaje fue de 350 s y no sirvió) con la regla.

### La regla condicional

Barrido de umbrales sobre el número de variables, en los dos sentidos
(`scripts/evaluate_conditional_local.py`):

| estrategia | PAR-2 | Δ vs por defecto |
|---|---:|---:|
| lucky **siempre** (por defecto de Kissat) | 128.248 | 0.000 |
| lucky **nunca** | 133.221 | +4.973 |
| desactivar si `variables > 500 000` | 139.634 | +11.386 |
| **desactivar si `variables ≤ 50 000`** | **114.821** | **−13.427** |
| desactivar si `variables ≤ 5 000 000` | 117.215 | −11.033 |
| oráculo (techo) | 107.160 | −21.088 |

**−13.4 s de PAR-2 (−10.5 %) con un umbral trivial**, que captura el **64 %** del
hueco del oráculo. Y no es un pico aislado: **todo el barrido en el sentido
"desactivar en las pequeñas" es negativo** (entre −6.4 y −13.4 s), lo que sugiere
una regla robusta y no un artefacto de un umbral afortunado.

## 5. Limitaciones (obligatorio citarlas junto a los números)

- **El umbral se eligió mirando las mismas 60 instancias en las que se evalúa.**
  Es una cota optimista. El número publicable sale de `bench/test`, con el
  umbral congelado (ADR-0003 §2). **Pendiente.**
- n = 60, una seed por configuración, T = 180 s frente a los 5000 s de la
  competición. Con presupuesto largo el peaje de lucky pesa relativamente menos
  (350 s de 5000 = 7 %, frente a 350 s de 180 = todo), así que **la magnitud del
  efecto se reducirá**; el signo debería mantenerse.
- `--jobs 4`: los tiempos llevan contención. La cuenta de resueltas no.

## 6. Qué se lleva el proyecto

1. **Un fallo reportable a upstream**: `kissat_lucky` (`src/lucky.c`, llamado
   desde `src/search.c:184` y `:188`) debería consultar el terminador. Hoy un
   límite de tiempo puede excederse 11×, lo que afecta a cualquiera que use
   Kissat con presupuesto acotado — incluidos los organizadores de la
   competición al medir.
2. **Una mejora concreta y barata**: condicionar las fases lucky al tamaño de la
   fórmula. Es la línea B3 del catálogo aterrizada en una decisión mínima, y la
   infraestructura ya existe en Kissat (`src/classify.c` ya clasifica por
   `smallclauses`).
3. **Un refuerzo para A4 frente a A1**: una cartera que reinicia el proceso en
   cada turno vuelve a pagar las fases lucky **en cada turno**.
4. **Una lección de método**: la hipótesis inicial era plausible, tenía un caso
   real detrás, y era causalmente falsa. La salvó el desglose por instancia, no
   el agregado — el PAR-2 global de "nunca lucky" (+4.97 s) habría cerrado el
   asunto como "no funciona" y se habría perdido una mejora de −13.4 s.

## 7. Reproducir

```bash
python3 scripts/run_experiment.py --solver solver/kissat/build/kissat \
    --bench bench/calib2 --out results/exp002/nolucky_calib2.csv \
    --timeout 180 --seeds 1 --jobs 4 --label nolucky \
    --opts="--luckyearly=0 --luckylate=0"
python3 scripts/par2.py results/exp001c/c0-default-s1.csv results/exp002/nolucky_calib2.csv
python3 scripts/evaluate_conditional_local.py \
    --on  results/exp001b/c0-default-s1.csv results/exp001c/c0-default-s1.csv \
    --off results/exp002/nolucky_calib.csv  results/exp002/nolucky_calib2.csv \
    --sizes results/exp002/sizes.reference.csv
```
