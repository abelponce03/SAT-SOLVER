# EXP-007 — ¿Mejora la ruptura de simetrías (satsuma MIT) el PAR-2 de LabeSAT? (preregistrado)

- **Estado**: **cerrado**. Veredicto: **solo condicional**. H1 se confirma con
  mucha fuerza; H2 no se cumple. Se preregistró antes de ejecutar (ADR-0003 §6).
- **Fecha**: 2026-09-23
- **Origen**: ADR-0004 y `docs/research/01` (el ganador de 2026 arregla 51
  instancias y rompe 13).
- **Numeración**: EXP-006 §4 llamaba «EXP-007» al seguimiento de A4 con un
  presupuesto largo. Ese experimento, si llega a hacerse, será **EXP-008**. Esta
  es la única desviación del texto de EXP-006; no afecta a su diseño.

---

## 1. Qué se quiere saber, y qué no se puede saber con estos datos

Los datos de 2026 comparan dos binarios **distintos**:

- **W** = `anders_satsuma-iter-kissat`, que es satsuma con cliques más una
  versión propia de kissat.
- **K** = el kissat de referencia.

Por eso la diferencia entre W y K mezcla tres cosas: la ruptura de simetrías,
cliques y la versión de kissat. EXP-007 **aísla la primera**: las dos ramas usan
**el mismo binario de kissat**, y solo cambia si satsuma (MIT, sin cliques) se
ejecuta antes o no.

Límite declarado: con T = 180 s en 4 núcleos solo se puede medir la parte de la
competición que se resuelve en ≤ 100 s. En 2026 son los estratos H, X y N:
**136 de las 400 instancias**. Las 264 restantes (estrato R, difíciles o sin
resolver) no se pueden medir aquí, y este experimento **no dice nada** sobre
ellas.

## 2. Hipótesis

> **H1 (replicación).** En el estrato H, `labesat` resuelve **más instancias o
> más rápido** que `labesat --no-symmetry`.
>
> **H2 (coste).** En el estrato N, el coste de ejecutar satsuma sin beneficio es
> pequeño: el factor geométrico `t_B/t_A` es **≤ 1.10**.
>
> **H3 (daño, descriptiva).** En el estrato X, ¿el daño de 2026 se debe a la
> ruptura de simetrías o a la versión de kissat? Se cuenta en cuántas instancias
> de X la rama B es ≥ 3× más lenta o pierde la resolución.

## 3. Banco (fijado con datos de 2026 únicamente)

`scripts/select_symm_bench.py` genera `bench/symm2026.list.csv`, que queda
versionado. Estratos, con L = 100 s:

| estrato | definición en 2026 | población | seleccionadas |
|---|---|---:|---:|
| H «ayuda» | W ≤ L, K ≥ 3·W, K ≥ 10 s | 54 | 45 |
| X «daña» | K ≤ L, W ≥ 3·K, W ≥ 10 s | 22 | 15 (7 tras el filtro de tamaño) |
| N «neutro» | W ≤ L y K ≤ L, fuera de H y X | 60 | 24 (muestra fija, semilla 2027; 22 tras el filtro) |
| R | resto | 264 | — |

- **Exclusiones**, fijadas antes de ver datos propios:
  - las 60 instancias de `bench/test` (reservado);
  - las de tamaño conocido > 5 M cláusulas (14 en la población);
  - tras la descarga, las de > 5 M cláusulas según la cabecera `p cnf`, porque
    la base local de GBD solo tiene el tamaño de 167 de las 400.
- **Solapamiento** con bancos ya usados en A/B de A4: 4 con `dev`, 16 con
  `calib` y 1 con `calib2`. No importa, porque aquí no se evalúa A4.
- Composición: H tiene 39 UNSAT y 6 SAT; X tiene 15 SAT; N tiene 12 UNSAT y 12
  SAT. **Que todo X sea SAT** es coherente con el mecanismo: la ruptura de
  simetrías elimina soluciones, y puede eliminar justo las que kissat
  encontraba rápido.

**Banco efectivo tras la descarga** (anotado antes de ejecutar nada; se aplica
la regla de tamaño de arriba, sin mirar resultados propios):

- Se apartan 10 instancias con más de 5 M cláusulas: 8 de X y 2 de N.
- Quedan **74**: H 45, X 7 y N 22.
- X queda con solo 7 instancias. Las de 2026 donde la ruptura de simetrías
  «daña» son sobre todo instancias grandes, y aquí casi no caben. **H3 pierde
  casi toda su potencia**: su recuento se informa, pero con 7 instancias no se
  puede generalizar.

## 4. Métricas y contrastes

- **Unidad**: la instancia (una semilla, ver §5).
- **H1**:
  - contraste principal: Wilcoxon de rangos con signo, dos colas, sobre la
    diferencia de PAR-2 por instancia (`cpu_s`, T = 180, 2T si no resuelve) en
    H;
  - además, McNemar sobre las resueltas y ΔPAR-2 medio con IC95 % por bootstrap
    de instancias.
- **H2**:
  - factor geométrico `exp(media log(t_B/t_A))` en N, sobre instancias que
    resuelven ambas ramas con t ≥ 1 s, con IC95 % bootstrap
    (`analyze_speedup.py`);
  - H2 se cumple si el extremo superior del IC ≤ 1.10.
- **H3**: recuento descriptivo en X (≥ 3× más lenta, o A resuelve y B no).
- **Estimación para la parte medible de la competición**:
  - ΔPAR-2 post-estratificado, `Σ_s (pob_s/136) · media_s(ΔPAR-2)` con los pesos
    54/22/60 de la tabla;
  - se informa **con su IC** y **solo como estimación**; no es el contraste.
- **Seguridad (vinculante, ADR-0004)**:
  - **todos** los modelos SAT de la rama B se verifican contra la CNF
    **original**;
  - todas las respuestas UNSAT de la rama B resueltas en ≤ 60 s se reejecutan
    escribiendo la prueba y se verifican con dsr-trim contra la CNF original,
    con un tope de 1800 s por prueba. Se informa cuántas quedan verificadas,
    cuántas agotan el tope y cuántas **fallan**.

## 5. Diseño

| elemento | valor |
|---|---|
| Binario de kissat | el de HEAD tras terminar EXP-006 (incluye `--append-proof`), igual en las dos ramas; SHA-1 vigilado con `--guard` |
| satsuma | `tools/satsuma` (`c6ad1b5`, `CLIQUES=OFF`), SHA-1 vigilado con `--guard` |
| Rama A | `solver/labesat --no-symmetry` (hace `exec` de kissat sobre la CNF original) |
| Rama B | `solver/labesat` con los topes provisionales del ADR-0004 (`LABESAT_SYMM_TIMEOUT=60`, `LABESAT_SYMM_MAXBYTES=512 MiB`), **sin ajustar** |
| Presupuesto | T = 180 s **totales**: en B el tiempo de satsuma (redondeado hacia arriba) se descuenta del `--time` de kissat |
| Semillas | solo 1: satsuma es determinista, y la varianza por semilla de kissat ya se midió en EXP-001 |
| Ejecución | intercalada (`run_ab_interleaved.py`), secuencial, orden alternado |

## 6. Criterio de decisión

| resultado | decisión |
|---|---|
| H1 confirmada (p < 0.05 a favor de B), H2 se cumple y **cero** fallos de seguridad | La ruptura de simetrías pasa a estar **activada por defecto** en `labesat`. Siguiente paso: activación condicional (B3), dirigida a X |
| H1 confirmada, pero H2 no se cumple o X muestra daño claro | **Solo condicional**: no se activa por defecto hasta que exista un criterio B3 que evite el coste o el daño |
| H1 no se confirma | La versión MIT no reproduce el efecto de 2026. Se mide cliques on/off (tarea #5) para saber si la causa es cliquer, y la decisión (licencia frente a rendimiento) es **del autor** |
| Cualquier modelo o prueba inválidos | Se **desactiva** la ruptura de simetrías hasta encontrar la causa (ADR-0004), sea cual sea el PAR-2 |

## 7. Amenazas a la validez, anotadas de antemano

- **Selección por los extremos.** H y X se eligieron por su comportamiento
  extremo en 2026. Es de esperar regresión a la media: efectos locales más
  pequeños que los de 2026.
- **Máquina y timeout distintos.** Un factor 3× a 5000 s no tiene por qué
  mantenerse a 180 s en otra CPU.
- **Sesgos conservadores contra B**, que se aceptan:
  - B descomprime `.xz` para satsuma, mientras que A lee directamente;
  - B pierde hasta 1 s de presupuesto por el redondeo de `--time`.
- **Una semilla.** En el estrato N, un factor cercano a 1 puede esconder ruido
  por semilla; para eso está el IC bootstrap. Las propagaciones no sirven de
  control de deriva, porque la CNF que ve kissat **es distinta** en cada rama.

## 8. Reproducir

```bash
python3 scripts/select_symm_bench.py --download
./scripts/get_tools.sh && ./scripts/build.sh
python3 scripts/run_ab_interleaved.py --solver solver/labesat \
    --guard solver/kissat/build/kissat --guard tools/satsuma \
    --bench bench/symm2026 \
    --out-a results/exp007/A.csv --out-b results/exp007/B.csv \
    --label-a A-sin-simetrias --label-b B-labesat \
    --opts-a="--no-symmetry" --timeout 180 --seeds 1
# Desde el cierre de EXP-007 la ruptura está DESACTIVADA por defecto en
# solver/labesat: para reproducir la rama B hay que añadir --opts-b="--symmetry".
```

**Análisis** (script fijado antes de que terminara la tanda):

```bash
python3 scripts/analyze_exp007.py results/exp007/A.csv results/exp007/B.csv
python3 scripts/verify_symm_answers.py results/exp007/B.csv \
    --bench bench/symm2026 --out results/exp007/seguridad.csv
```

## 9. Incidencias de ejecución

- **2026-09-23, primer lanzamiento, abortado.**
  - Las 11 primeras parejas salieron `ERROR` en **las dos ramas**, en 0,0–0,4 s.
    Sin `LABESAT_KISSAT`, `solver/labesat` tomaba el **directorio**
    `solver/kissat` por el binario, porque `-x` es cierto para directorios.
  - No llegó a resolverse nada, así que no hay datos que puedan sesgar el
    relanzamiento; los parciales se descartan.
  - Correcciones:
    - `first_exe` exige un fichero regular;
    - `test_symmetry.sh` comprueba también la búsqueda por defecto (el test
      fijaba siempre `LABESAT_KISSAT`, y por eso el fallo no se vio);
    - `run_ab_interleaved.py` aborta si el solver no contesta `--id`.
  - El diseño no cambia.
- **2026-09-23, durante el relanzamiento (parejas ~27–35).**
  - Se ejecutaron en paralelo tests cortos (`test_symmetry.sh`, 8 veces) y dos
    compilaciones de dsr-trim, con `nice` y usando como mucho 2 de los 4
    núcleos, mientras la tanda ocupaba 1.
  - El diseño intercalado reparte ese ruido entre las dos ramas. Se anota por
    transparencia; no es motivo para descartar datos.
  - Un reinicio del contenedor no afectó a la tanda: el proceso siguió vivo.
- **2026-09-23, parejas ~40–45.**
  - Se instalaron TeX Live y poppler con `apt`, a prioridad mínima de CPU y de
    E/S (`nice -n 19`, `ionice -c3`), y se compilaron dos documentos LaTeX.
  - Se anota por transparencia, igual que la carga anterior.

## 10. Resultados

Ejecutado el 2026-09-23.

- **Procedencia**:
  - `--id` = HEAD `23649fc`, que tras la reescritura D-001 es `7776609` (ver
    `docs/decisiones/D-001-correspondencia-sha.md`);
  - SHA-1 de kissat y satsuma vigilados con `--guard`;
  - 74 parejas intercaladas, todas completas y sin estados ERROR;
  - datos en `results/exp007/`.
- **Análisis**: el preregistrado, `scripts/analyze_exp007.py`, que se commiteó
  antes de que terminara la tanda.

### Visión global (T = 180 s)

| | A: sin simetrías | B: labesat con satsuma |
|---|---:|---:|
| Resueltas (de 74) | 35 (20 SAT, 15 UNSAT) | **64** (19 SAT, 45 UNSAT) |
| PAR-2 | 209.3 s | **69.0 s** |

- ΔPAR-2 = −140.3 s, IC95 % [−183.4, −97.2]; Wilcoxon p ≈ 0.
- McNemar: 31 instancias solo las resuelve B y 2 solo A.

### Hipótesis preregistradas

| | Resultado | Criterio | Veredicto |
|---|---|---|---|
| **H1** (estrato H, 45) | B resuelve **37**, A **8**. ΔPAR-2 = **−233.8 s**, IC95 % [−283.6, −179.0]. Wilcoxon **p = 8·10⁻¹⁰** (n = 38); McNemar 30 frente a 1, p = 3·10⁻⁸ | p < 0.05 a favor de B | ✅ **confirmada** |
| **H2** (estrato N, 22) | Factor geométrico **1.416×**, IC95 % [1.158, 1.753], n = 20 | IC superior ≤ 1.10 | ❌ **no se cumple** |
| **H3** (estrato X, 7) | Daño en **1 de 7**: `fca71c20`, SAT en 86 s con A y timeout con B | Descriptiva | Daño puntual |
| Estimación post-estratificada (136 instancias de 2026 medibles) | ΔPAR-2 ≈ **−90.2 s**, IC95 % [−118.9, −61.0] | No es el contraste | — |

### Seguridad (vinculante)

`scripts/verify_symm_answers.py` (`results/exp007/seguridad.csv`):

- **19 de 19** modelos SAT satisfacen la CNF **original**;
- **42 de 42** pruebas UNSAT reejecutadas se verifican con dsr-trim contra la
  CNF original;
- 3 UNSAT de más de 60 s quedan sin verificar, como fijaba el preregistro;
- **0 fallos** y **0 respuestas que no se reproduzcan**.

### Veredicto según §6

**H1 se confirma, pero H2 no se cumple: solo condicional.**

- La ruptura de simetrías **no se activa por defecto** hasta que exista un
  criterio B3 que evite el coste en las instancias neutras.
- Desde este cierre, `solver/labesat` la aplica solo con `--symmetry` (o
  `LABESAT_SYMMETRY=1`).
- La estimación global (−90 s) indica que activarla siempre ya compensaría
  en la parte medible, pero el criterio preregistrado exige no pagar un 42 %
  en las instancias neutras. B3 (EXP-009) pasa a ser la prioridad técnica.

### Análisis exploratorio, NO preregistrado: de dónde sale el 1.42× en N

Se contrasta con el tiempo de satsuma en solitario
(`results/satsuma-builds/builds.csv`):

- **Tiempo de satsuma**: mediana de 0.44 s y media de 3.84 s (máximo 36.7 s en
  `91860f79`). Explica solo una parte.
- **Sin el tiempo de satsuma, el factor sigue en ~1.27×.** Kissat **trabaja más
  sobre la fórmula modificada**: por ejemplo, `91860f79` pasa de 107 M a 313 M
  propagaciones y `c557ad9c` de 28 M a 95 M.
- **En las 5 instancias de N en las que satsuma no cambia la fórmula**, las
  propagaciones son **idénticas**. El coste ahí es solo el de satsuma y la
  descompresión.
- **Implicación para B3**: no basta con detectar si hay simetrías. El criterio
  tiene que predecir si romperlas **ayuda** a la búsqueda. Candidatos: el tipo
  y tamaño de los grupos, la fracción de variables afectadas, o SAT/UNSAT
  esperado (el daño se concentra en SAT).

### Cliques (research/03, segunda parte)

Sobre las 8 instancias cuya salida difiere, satsuma con cliques resuelve **6
de H en menos de 2 s** que la versión MIT deja en timeout. Mantener MIT cuesta
~−29 s de PAR-2 medio en este banco. Queda en manos de D-005.
