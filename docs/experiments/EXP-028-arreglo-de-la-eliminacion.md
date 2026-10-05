# EXP-028 — El fallo de `eliminate.c` arreglado: ¿mejora o empeora? (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con la
  opción `--eliminatefix` (apagada) y las listas compartidas de
  `results/research12/` (`research12.py seleccionar`).
- **Ejecuciones previas**: solo pruebas de corrección (research/12 §11):
  - contadores idénticos a la base con la opción a 0 (50 de 50);
  - con 1, modelos y pruebas verificados en `test_opciones_m.sh`.
- **Fecha**: 2026-10-05
- **Vía**: M9 (research/12 §7).
- **Decide**: si `--eliminatefix` pasa a candidata, y aporta el dato para
  D-021 (avisar o no a upstream).

---

## 1. Qué se quiere saber

- **El fallo.** Desde Kissat 3.1.0, `eliminate_variables` declara otra vez
  `last_round_eliminated` dentro del bucle de rondas. La variable exterior
  se queda en 0, y como `remain` también es 0 en ese punto, Kissat da la
  eliminación por **completa** siempre.
- **Qué hace Kissat entonces.**
  - Sube la cota de cláusulas añadidas (0, 1, 2, 4, 8, 16) y reprograma
    todas las variables.
  - No descarta nunca las candidatas.
- **Con `--eliminatefix`**, si la última ronda eliminó algo (por ejemplo, al
  agotar `eliminaterounds` = 2), la eliminación queda incompleta. La cota no
  sube y las candidatas pendientes se descartan.

La conducta con el fallo es la que ganó las competiciones de 2023 a 2026.
¿Es la arreglada mejor, peor o igual?

## 2. Hipótesis

> **Etapa 1 (cribado, sin contraste)**: regla de research/12 §10.
>
> **H1 (etapa 2)**: ΔPAR-2 (B − A) < 0, con Wilcoxon p < 0,05 y el IC95 %
> bootstrap entero por debajo de 0.
>
> **H2 (etapa 2)**: el factor geométrico de velocidad B/A tiene el IC95 %
> entero por debajo de 1.
>
> **H0′ (dañina)**: ΔPAR-2 > 0 con p < 0,05.

- A = sin opción;
- B = `--eliminatefix=1`.

**Predicción honesta**: sin dirección clara. Arreglado, Kissat elimina
menos agresivamente en las rondas largas. Eso puede ahorrar tiempo de
preproceso o dejar fórmulas más grandes. Lo más probable es un efecto
pequeño en cualquiera de los dos sentidos.

## 3. Diseño

```bash
# Etapa 1: 40 de tesis-dev, T = 300 s, semilla 42
python3 scripts/run_ab_interleaved.py --solver solver/kissat/build-m/kissat \
    --bench bench/tesis-dev --instances results/research12/cribado.txt \
    --out-a results/exp028/A1.csv --out-b results/exp028/B1.csv \
    --label-a A-base --label-b B-eliminatefix --opts-b=--eliminatefix=1 \
    --guard solver/kissat/build-m/kissat --timeout 300 --seeds 42 --mem-gb 6
python3 scripts/research12.py cribado results/exp028/A1.csv results/exp028/B1.csv \
    > results/exp028/cribado.txt
# Etapa 2, solo si el cribado dice PASA: 60 instancias DISTINTAS, semillas 42 y 123
python3 scripts/run_ab_interleaved.py --solver solver/kissat/build-m/kissat \
    --bench bench/tesis-dev --instances results/research12/confirmacion.txt \
    --out-a results/exp028/A2.csv --out-b results/exp028/B2.csv \
    --label-a A-base --label-b B-eliminatefix --opts-b=--eliminatefix=1 \
    --guard solver/kissat/build-m/kissat --timeout 300 --seeds 42,123 --mem-gb 6
python3 scripts/research12.py confirmacion results/exp028/A2.csv results/exp028/B2.csv \
    > results/exp028/confirmacion.txt
```

- **Muestras**: `results/research12/cribado.txt` (40) y `confirmacion.txt`
  (60), disjuntas. Son de tesis-dev, estratos fácil, media e inestable,
  con cuota por familia y orden de `md5(hash + sal)`.
  - Las comparten EXP-028 a EXP-031: cada experimento es una hipótesis
    distinta sobre las mismas instancias.
  - Ninguna opción se diseñó mirándolas.
- **Binario**: `solver/kissat/build-m/kissat`, compilado desde el commit de
  este preregistro con `--pgo --lto`, la configuración adoptada (EXP-017).
- **Coste**:
  - etapa 1: ≤ 6,7 h; se esperan ~2,5 h;
  - etapa 2: ≤ 20 h; se esperan ~6 h.

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| No pasa el cribado | Se cierra sin señal; la opción queda apagada. D-021 se resuelve igual, porque el fallo existe aunque no importe en PAR-2 |
| H1 | Candidata para V1; se valida en H8 y se avisa a upstream con el dato, si D-021 lo aprueba |
| Solo H2 | Candidata débil; se repite con más instancias de estrato media antes de decidir |
| H0′ | **El fallo ayuda**: se documenta (material para el artículo) y la opción queda apagada |
| Ni H1 ni H2 ni H0′ | Sin efecto detectado; apagada |

## 5. Amenazas a la validez

- **Solo tesis-dev.** El efecto podría ser distinto en el banco de 2026.
  Si pasa, H8 lo valida en `bench/test`.
- **T = 300 s.** La eliminación pesa más al principio. Las rondas largas en
  las que actúa el arreglo son de las primeras eliminaciones, así que se
  ven en este presupuesto.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
