# EXP-015 — VSA: vivificación programada por actividad (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con la
  selección (`scripts/exp015_seleccion.py`, `results/exp015/instancias.txt`).
  Ejecuciones previas: solo pruebas de corrección (12 instancias de calib a
  50 000 conflictos, 7 pruebas DRAT y 4 modelos). Ninguna mide tiempo en el
  banco del experimento.
- **Fecha**: 2026-09-24
- **Decide**: si `vivifyactivity=1` entra en la lista de candidatas para V1
  (plan §3), y se valida después en `tesis-test`.

---

## 1. Qué se quiere saber

Kissat-VSA (Li y Zhang) quedó **2.º en UNSAT** en la SAT Competition 2025,
con un único cambio sobre Kissat sc2024: en modo estable, las cláusulas cuya
variable menos activa tiene la mayor puntuación VSIDS se vivifican antes.
Kissat vivifica con un presupuesto de *ticks*, así que el orden decide qué
cláusulas llegan a vivificarse. LabeSAT lo implementa detrás de la opción
`vivifyactivity` (commit `237c426`; research/07 §3).

¿Mejora el PAR-2 en el banco industrial de la tesis, que es donde nuestra
base es Kissat 4.0.4 y no sc2024?

## 2. Hipótesis

> **H1 (primaria).** ΔPAR-2 (B − A) < 0 con Wilcoxon emparejado p < 0,05 y
> el IC95 % bootstrap entero por debajo de 0.
>
> **H2 (velocidad).** En las resueltas por las dos ramas, factor geométrico
> B/A < 1 con el IC95 % por debajo de 1.
>
> **H3 (UNSAT, exploratoria pero fijada ahora).** El efecto se concentra en
> las UNSAT, como en 2025: ΔPAR-2 en UNSAT < ΔPAR-2 en SAT.

**Predicción honesta**: efecto pequeño. VSA ganó en UNSAT sobre sc2024, pero
en la clasificación global de 2025 quedó por detrás de AE-Kissat-MAB y de
Kissat-public. Un resultado nulo es plausible y se documenta igual.

## 3. Diseño

- **Banco**: 60 instancias de **tesis-dev**, estratos `facil`, `media` e
  `inestable`, cuota proporcional por familia, orden de `md5(hash + sal)`.
  23 fáciles, 29 medias y 8 inestables.
- **Binario**: `solver/kissat/build-vsa/kissat` (`--id` `237c4262…`, SHA-1
  `6cd7466b…`), el mismo en las dos ramas; B añade `--vivifyactivity=1`
  (ADR-0002 §3).
- **Corrida**:

  ```bash
  python3 scripts/run_ab_interleaved.py --solver solver/kissat/build-vsa/kissat \
      --bench bench/tesis-dev --instances results/exp015/instancias.txt \
      --out-a results/exp015/A.csv --out-b results/exp015/B.csv \
      --label-a A-base --label-b B-vsa --opts-b=--vivifyactivity=1 \
      --guard solver/kissat/build-vsa/kissat --timeout 300 --seeds 42,123
  python3 scripts/par2.py results/exp015/A.csv results/exp015/B.csv --md
  python3 scripts/analyze_speedup.py results/exp015/A.csv results/exp015/B.csv
  ```

- **Dos semillas** (42 y 123, dos de las de la tesis): la variación entre
  semillas en este banco es grande (razón máx/mín p90 = 4,3 en la tesis).
  Tres semillas costarían ≥ 15 h; se declara la desviación de ADR-0003 §3.2.
- **Coste**: ≤ 60 × 2 × 2 × 300 s = 20 h en el peor caso; se esperan ~6 h.
- **Cuándo**: después de EXP-013 y de la parte 2 de EXP-014, **sola** en la
  máquina (la máquina local tiene 15 GB y se cayó el 2026-09-24 por lanzar
  varias tandas a la vez).

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| H1 se cumple | VSA pasa a **candidata** para V1; validación preregistrada en `tesis-test` (y en `bench/test` en H8) antes de activarla por defecto |
| H1 no, pero H2 sí | Candidata débil: se repite con más instancias `media` antes de decidir |
| Ni H1 ni H2 | Se cierra sin efecto detectado; la opción se queda apagada, como A4.1 (EXP-006) |
| B empeora con p < 0,05 | Se cierra como **dañina** en este banco y se documenta |

## 5. Amenazas a la validez

- **Base distinta**: el VSA original va sobre sc2024, no sobre 4.0.4. Si
  EXP-008 cambia la base (D-013), habría que repetirlo sobre sc2026.
- **Implementación propia**: se hizo a partir de la descripción de dos
  párrafos de las actas de 2025, sin ver su código. Puede diferir en
  detalles, por ejemplo si también se aplica a las irredundantes (aquí sí,
  en modo estable).
- **Una sola familia de 2025**: el efecto publicado es de un único envío a la
  competición, sin artículo con ablación.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
