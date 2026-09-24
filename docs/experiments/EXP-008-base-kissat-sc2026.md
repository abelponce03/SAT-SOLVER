# EXP-008 — ¿Es mejor base Kissat «sc2026» que Kissat 4.0.4? (preregistrado)

- **Estado**: **preregistrado**. Se escribe **antes** de ejecutar (ADR-0003 §6).
- **Fecha**: 2026-09-23
- **Decide**: D-013 (issue #18). Hito H2 del plan (`docs/plan/plan-main-track-2027.md`).
- **Numeración**: EXP-008 era el número reservado para el seguimiento de A4 con
  presupuesto largo. Ese seguimiento se descartó en EXP-006, así que el número
  queda libre y se usa aquí.

---

## 1. Contexto

- LabeSAT se basa en Kissat 4.0.4 (`8af8e56`), la última versión publicada y la
  misma base que usó el ganador de 2026 (satsuma + 4.0.4).
- Biere presentó a la competición de 2026 **Kissat «sc2026»**: una versión
  posterior, sin release publicada, con licencia MIT, disponible en el paquete
  oficial de solvers. Respecto a 4.0.4 cambia 64 ficheros (~1229 líneas de
  diff). Según su NEWS:
  - elimina `fastel` y los niveles de glue;
  - añade un retraso de BVA en fórmulas grandes;
  - **alterna focused y stable según los conflictos**.
- Sola, sc2026 quedó 16.ª en 2026 (PAR-2 4612). No hay datos de 4.0.4 sin más
  en esa edición, así que **no se sabe si sc2026 es mejor o peor que 4.0.4**.

## 2. Hipótesis

> **H1.** Kissat sc2026 obtiene un PAR-2 distinto (bilateral) que el kissat de
> LabeSAT (4.0.4 con B3″, sin ruptura de simetrías) en el mismo banco.

## 3. Métricas y contraste, fijados ahora

- **Unidad**: la instancia. Por cada instancia se promedia el PAR-2 de las dos
  semillas (T = 180 s; 2T si no resuelve; `cpu_s`).
- **Contraste principal**: Wilcoxon de rangos con signo, dos colas, sobre ΔPAR-2
  por instancia (B − A).
- **Además**:
  - ΔPAR-2 medio con IC95 % bootstrap de instancias;
  - McNemar sobre las instancias resueltas en ambas semillas;
  - factor de velocidad en las resueltas por las dos ramas
    (`analyze_speedup.py`), solo descriptivo.
- **Sin control por propagaciones**: son dos binarios distintos, y el número de
  propagaciones no es comparable entre ellos. La deriva de la máquina se
  controla con el orden intercalado.

## 4. Criterio de decisión (D-013)

| resultado | decisión |
|---|---|
| p < 0.05, ΔPAR-2 < 0 y extremo superior del IC < 0 (sc2026 mejor) | **Cambiar de base a sc2026**. Portar las ~105 líneas activas (`scripts/declaracion_ia.sh`) y repetir `test_symmetry.sh` y la validación de las pruebas |
| p < 0.05 a favor de 4.0.4 | **Mantener 4.0.4**. sc2026 se descarta como base |
| p ≥ 0.05 (sin diferencia detectable) | **Mantener 4.0.4**: es el statu quo, sin coste de migración, y la base del ganador de 2026. sc2026 queda como candidata a variante (D-014) solo si aporta diversidad |

## 5. Diseño

| elemento | valor |
|---|---|
| Rama A | `solver/kissat/build/kissat` (LabeSAT, 4.0.4 + B3″), opciones por defecto |
| Rama B | `tools/kissat-sc2026` (paquete oficial de 2026, sha256 `69fbdae7…`, compilado desde cero con `get_tools.sh`), opciones por defecto |
| Banco | `bench/calib` (40) + `bench/calib2` (20) = 60 instancias reales del Main Track de 2026 |
| Semillas | 1 y 2 |
| Presupuesto | T = 180 s |
| Ejecución | intercalada (`run_ab_interleaved.py --solver-b`), secuencial, orden alternado; SHA-1 de los dos binarios vigilados |

**Por qué estos bancos**:
- `calib` y `calib2` resuelven una buena parte a 180 s, así que son
  informativos.
- `bench/dev` tiene mucha instancia sin resolver a 180 s en ambas ramas.
- `bench/test` sigue reservado.
- Ninguno de estos bancos se ha usado para elegir la base.

## 6. Amenazas a la validez

- **T = 180 s frente a 5000 s**: la ventaja de una base puede depender del
  presupuesto. Esto se declara en el resultado.
- **Diferencias de compilación**: las dos ramas se compilan con la
  configuración por defecto de cada una. La de competición (`--competition`)
  se probará solo si sc2026 gana.
- **Carga concurrente prevista**: mientras corre la tanda se escribe y compila
  el sustituto MIT de la clique máxima (D-005), con compilaciones cortas y
  `nice`. El orden intercalado reparte ese ruido entre las ramas. Se anotará en
  §8.

## 7. Reproducir

```bash
./scripts/get_tools.sh && ./scripts/build.sh
python3 scripts/run_ab_interleaved.py --solver solver/kissat/build/kissat \
    --solver-b tools/kissat-sc2026 --bench bench/calib bench/calib2 \
    --out-a results/exp008/A.csv --out-b results/exp008/B.csv \
    --label-a A-kissat404 --label-b B-kissat-sc2026 --timeout 180 --seeds 1,2
python3 scripts/par2.py results/exp008/A.csv results/exp008/B.csv
python3 scripts/analyze_speedup.py results/exp008/A.csv results/exp008/B.csv
```

## 8. Incidencias de ejecución

- **Lanzamiento** (2026-09-23 16:31 UTC): el binario A se recompiló desde cero
  para que su `--id` coincida con el commit del preregistro (`c5f2e4c`).
  SHA-1: A `bed5fd461957…`, B `80f6fe728488…`.
- **Carga concurrente**, la prevista en §6: la parte 1 de EXP-010 (solo
  satsuma, un núcleo, `nice`) y compilaciones cortas de mclique.
- **Corte por reinicio del contenedor** (hacia las 17:46 UTC): la sesión quedó
  inactiva, el contenedor se suspendió y, al volver, todos los procesos habían
  muerto.
  - Quedaron **60 de 120 parejas completas**. De la pareja 61
    (`ac625665…`, semilla 1) solo existía la fila A; se descarta.
  - **Reanudación** con `run_ab_interleaved.py --resume`: conserva las parejas
    completas, comprueba que los dos binarios tienen el mismo SHA-1 que en el
    `meta.json` original y anota la reanudación en él (`reanudaciones`).
  - **Por qué es válido**: en el diseño intercalado cada pareja A/B se mide con
    segundos de diferencia y comparte las condiciones de la máquina, así que la
    deriva entre sesiones (ADR-0003 §4b) afecta por igual a las dos ramas de
    cada pareja. Las dos semillas de cada instancia pendiente se miden en la
    misma sesión.
  - HEAD ya no es `c5f2e4c` (hay commits de documentación y de mclique
    posteriores), pero **el binario es el mismo**, y la guarda lo vigila.
- **Carga concurrente tras la reanudación** (entre las 18:45 y las 19:20 UTC,
  aproximadamente): compilaciones de Kissat con satsuma integrado (D-016) en
  directorios aparte (`build-symm`, etc.). Tres de ellas usaron `make -j4` con
  `nice`. El binario del experimento no se tocó (la guarda lo vigila). El
  orden intercalado reparte ese ruido entre las dos ramas.
- **HARDKILL en la rama B**: Kissat sc2026 no respetó `--time=180` en al menos
  dos corridas (`b54b26f3…`, las dos semillas), y el arnés lo mató a los
  ~252 s (1,25·T + 30). Cuenta como no resuelta, igual que un TIMEOUT: no
  cambia el PAR-2, que usa 2T para toda no resuelta. Se anota por si sc2026
  llegara a ser la base, porque en competición el tiempo lo impone el entorno.
- **Cambio de máquina (2026-09-23, 21:38 UTC): tanda de la nube descartada sin
  promocionar.** El director indica que, en adelante, todos los experimentos
  se ejecutan en su entorno local, no en el hardware de la sesión de nube.
  - La tanda llevaba **112 de 120 parejas** medidas en la máquina de la nube
    cuando se detuvo.
  - **No se continúa esa tanda en otra máquina.** El diseño A/B intercalado
    (ADR-0003 §4b) existe justamente para anular la deriva *dentro* de una
    sesión y de una máquina; mezclar parejas medidas en dos equipos distintos
    reintroduce exactamente esa deriva como una variable de confusión, sin
    que el orden intercalado pueda repartirla. Siete de las 8 parejas
    HARDKILL/TIMEOUT largas del final tampoco aportan mucha señal para no
    reiniciar.
  - Los CSV parciales (`results/exp008/{A,B}.csv`, 112 filas cada uno) se
    quedan en el disco efímero de la sesión de nube y no se comiten: no
    llegaron a un cierre de experimento (ADR-0003 §6, "solo se promocionan
    los resultados de un experimento cerrado").
  - **Se relanza de cero** en la máquina local del director con el mismo
    comando de §7, ahora a través de `scripts/reanudar_experimentos.sh`
    (idempotente **dentro de una misma máquina**, con guarda de SHA-1).

- **2026-09-24, máquina local (i5-1135G7, 4 núcleos, 15 GB).**
  - Relanzado de cero a las 19:17 UTC con el binario recompilado desde
    `495512f` (SHA-1 `28b587cf…`), satsuma y `kissat-sc2026` bajados con
    `get_tools.sh` y los bancos calib y calib2 bajados de GBD por hash.
  - **Caída por falta de RAM** hacia las 19:25 UTC, con 3 parejas escritas. Se
    solaparon la tanda, la parte 1 de EXP-014 (satsuma), un `make -j8` y una
    prueba de un prototipo de VSA con un fallo que pedía memoria sin control
    (ver commit `237c426`). El sistema mató todos los procesos en segundo
    plano.
  - Se reanuda con `--resume` **en la misma máquina** (lo permite §8 y el
    guion): las 3 parejas completas se conservan, y la cuarta, a medias, no
    llegó a escribirse. La carga concurrente pudo afectar a esas 3 parejas;
    el diseño intercalado reparte ese efecto entre las dos ramas, y se anota
    por transparencia.
  - Desde entonces la tanda corre **sola**: un proceso pesado a la vez y
    satsuma con tope de memoria.

## 9. Resultados

_Pendiente._
