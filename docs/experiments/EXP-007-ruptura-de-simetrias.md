# EXP-007 — ¿Mejora la ruptura de simetrías (satsuma MIT) el PAR-2 de LabeSAT? (preregistrado)

- **Estado**: **preregistrado**. Escrito **antes** de ejecutar ninguna corrida
  del A/B (ADR-0003 §6).
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
| X «daña» | K ≤ L, W ≥ 3·K, W ≥ 10 s | 22 | 15 |
| N «neutro» | W ≤ L y K ≤ L, fuera de H y X | 60 | 24 (muestra fija, semilla 2027) |
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
```

## 9. Resultados

_Pendiente de ejecución (después de EXP-006)._
