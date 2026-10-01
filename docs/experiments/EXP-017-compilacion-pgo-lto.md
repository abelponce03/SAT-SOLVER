# EXP-017 — C1: compilación guiada por perfil, LTO y `-march` (clase E, preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con
  `scripts/build.sh` (`--pgo`, `--lto`, `--march`, `--control-fma`),
  `scripts/pgo_entrenamiento.txt`, `scripts/exp017.py`,
  `results/exp017/banco.txt` y el soporte de `--conflicts` en
  `run_ab_interleaved.py`.
  - Ejecuciones previas: una compilación PGO+LTO de prueba, para depurar
    `build.sh`, y una comprobación de corrección en 3 instancias de `calib`
    a 20 000 conflictos: contadores idénticos al binario actual en las 3.
  - Ninguna mide tiempo. El binario de prueba se borró y todos se
    recompilan desde el commit del preregistro.
- **Fecha**: 2026-10-01
- **Decide**: si LabeSAT se compila con PGO y LTO (y `-march`) por defecto,
  en los experimentos y en el paquete de competición (research/08, C1;
  ADR-0009).

---

## 1. Qué se quiere saber

Kissat se compila hoy con `-O3` sin más. Dos técnicas estándar pueden
acelerarlo **sin cambiar ni una decisión de la búsqueda**:

- **PGO** (`-fprofile-generate` / `-fprofile-use`): coloca el código según
  las ramas que de verdad se toman (Pettis y Hansen, 1990);
- **LTO**: optimiza entre ficheros.

Además, `-march=x86-64-v3` (AVX2, BMI2, FMA) permite instrucciones más
nuevas. Las máquinas de la competición (Xeon Platinum 8368) y la local
(i5-1135G7) las tienen.

research/08 (Teorema 5 y Corolario 3) demuestra que esas compilaciones
**conservan la trayectoria** si se cumplen cuatro condiciones, entre ellas
**`-ffp-contract=off`** cuando el `-march` incluye FMA. Este experimento:

- comprueba la equivalencia en 85 instancias;
- mide la velocidad;
- y, como **control negativo**, comprueba si la condición de la FMA importa
  en la práctica.

## 2. Hipótesis

> **H0 (equivalencia, vinculante).** Con 100 000 conflictos y la semilla 1,
> `build-pgo` y `build-march` dan, en las 85 instancias, el **mismo estado,
> los mismos conflictos, decisiones y propagaciones** que `build-base`.
>
> **H1 (velocidad de PGO+LTO).** Aceleración geométrica de `build-pgo` frente
> a `build-base` (tiempo de CPU para el mismo trabajo) con el extremo
> inferior del IC95 % **> 1**.
>
> **H2 (velocidad con `-march`).** Lo mismo para `build-march`.
>
> **Control (descriptivo).** `build-fma` (`-march=x86-64-v3` **sin**
> `-ffp-contract=off`, sin PGO ni LTO) frente a `build-base`: número de
> instancias con trayectoria distinta. Predicción: **al menos una**, porque
> `smooth.c:34-35` tiene el patrón `a + b*c`. Si sale 0, se informa: la
> condición sigue siendo necesaria en teoría, pero no se ha manifestado en
> este banco.

**Predicción honesta**: H0 se cumple (lo exige el teorema). Para H1, una
ganancia típica de PGO en código con muchas ramas está en un dígito bajo o
medio de porcentaje; si es < 5 %, su valor en PAR-2 es ≈ −0,8 %
(research/08 §2), y se adopta igualmente si H0 y H1 se cumplen, porque es
gratis.

## 3. Diseño

- **Binarios**, todos desde el commit de este preregistro (paso
  `exp017-construir` de la cola):

  | binario | `build.sh` |
  |---|---|
  | `build-base` | `--dir=build-base` (lo mismo que `build/`: `-O3`) |
  | `build-pgo` | `--dir=build-pgo --pgo --lto` |
  | `build-march` | `--dir=build-march --pgo --lto --march=x86-64-v3` (incluye `-ffp-contract=off`) |
  | `build-fma` | `--dir=build-fma --control-fma=x86-64-v3` |

- **Entrenamiento de la PGO**: `scripts/pgo_entrenamiento.txt` (bench/smoke,
  bench/symm y bench/calib2, 50 000 conflictos cada una). Es **disjunto** del
  banco de evaluación, y `exp017.py` lo comprueba con un `assert`.
- **Banco** (`results/exp017/banco.txt`, 85 instancias):
  - las 40 de `bench/calib` (2026);
  - las industriales de la muestra de EXP-016;
  - 2 están en los dos conjuntos.
- **Corridas** (pasos `exp017-pgo`, `exp017-march` y `exp017-control`):
  A/B intercalado con **presupuesto de conflictos**:

  ```bash
  python3 scripts/run_ab_interleaved.py --solver solver/kissat/build-base/kissat \
      --solver-b solver/kissat/build-pgo/kissat --bench bench/calib bench/tesis-dev \
      --instances results/exp017/banco.txt --out-a results/exp017/pgo_A.csv \
      --out-b results/exp017/pgo_B.csv --conflicts 100000 --seeds 1
  # ídem con build-march (march_*) y con build-fma (control_*)
  python3 scripts/exp017.py analizar pgo     # y march, control
  ```

  Con el mismo trabajo en las dos ramas, el cociente de tiempos de CPU por
  instancia mide la velocidad sin censura por límite de tiempo.
- **Métrica**: s_i = cpu_A / cpu_B. Media geométrica, IC95 % por bootstrap y
  Wilcoxon sobre log s_i. Se excluyen las parejas con cpu_A < 1 s, y se
  informa de cuántas son.
- **Cuándo**: en la cola, después de EXP-016 y antes de reanudar EXP-009,
  sin otras tandas a la vez.

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| H0 y H1 | `build.sh` compila con `--pgo --lto` en los experimentos siguientes y en el paquete de competición. Valor en PAR-2 calculado con la Proposición 1 |
| H0 y H2, con s(march) > s(pgo) | Se añade `--march=x86-64-v3`, condicionado a confirmar que el entorno de compilación de la competición lo admite (Ice Lake sí); si no se confirma, solo PGO+LTO |
| H0 falla en cualquier pareja | **No se adopta** esa compilación. Se busca la causa: alguna condición del Teorema 5 no se cumple, y eso es un hallazgo en sí |
| H0 sí, H1 no | Equivalente pero sin ganancia medible: no se adopta (no compensa la complejidad del build) |

## 5. Amenazas a la validez

- **El perfil depende del entrenamiento**: se usan instancias disjuntas del
  banco de evaluación, pero de las mismas fuentes (2026 y sintéticas). La
  ganancia en la competición puede ser algo menor.
- **Portátil**: frecuencia variable y temperatura; el intercalado reparte la
  deriva.
- **100 000 conflictos** cubren el inicio de la búsqueda y el preproceso. En
  corridas largas, el reparto entre fases cambia (EXP-016, Q2). La ganancia
  por fase se puede cruzar con el perfil de EXP-016.
- **Carga ajena**: servicios Docker del director.

## 6. Incidencias de ejecución

- **2026-10-01, commit posterior al preregistro.** Antes de que la cola
  compilara los binarios de este experimento se fusionó K1 (EXP-018):
  `proplit.h` y `configure`, con el código nuevo detrás de
  `LABESAT_PREFETCH`, que estos binarios no definen. Se comprobó que no cambia
  nada: se compiló Kissat con `-O3` desde el commit anterior y desde el de K1
  sin `--prefetch`, y se compararon los 95 objetos sección a sección
  (`objdump -s`). Son idénticos byte a byte salvo `build.o`, que solo guarda
  el commit y la fecha de compilación. `results/exp017/commit.txt` registra
  el commit real con el que se compiló.

## 7. Resultados

(pendiente)
