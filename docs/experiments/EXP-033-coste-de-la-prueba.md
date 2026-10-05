# EXP-033 — ¿Cuánto cuesta escribir la prueba? (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con:
  - `--proof-dir-a/-b` en `run_ab_interleaved.py`;
  - `research12.py coste-prueba`;
  - la lista `results/exp033/instancias.txt`.

  Ejecución previa: la prueba del arnés en `bench/smoke`, con la misma
  trayectoria en 10 de 10.
- **Fecha**: 2026-10-05
- **Vía**: M11 (research/12 §8; C5 de research/08).
- **Decide**: si optimizar la escritura de la prueba (clase E) merece trabajo.

---

## 1. Qué se quiere saber

- En la competición, todo UNSAT escribe su prueba DRAT, y su tiempo cuenta.
- Ninguno de nuestros A/B la escribe: miden el solver sin prueba.
- research/08 dejó la escritura «por medir» (C5).

## 2. Hipótesis

> **H1 (misma búsqueda, vinculante).** Con presupuesto de conflictos, A (sin
> prueba) y B (con prueba en disco) dan los mismos conflictos, decisiones y
> propagaciones en todas las parejas.
>
> **H2 (coste).** La media geométrica del reloj B/A en las parejas con
> t ≥ 1 s y su IC95 % bootstrap.

**Predicción**: B/A < 1,03. Kissat escribe la prueba binaria con búfer.

## 3. Diseño

```bash
python3 scripts/run_ab_interleaved.py --solver solver/kissat/build-m/kissat \
    --bench bench/tesis-dev --instances results/exp033/instancias.txt \
    --out-a results/exp033/A.csv --out-b results/exp033/B.csv \
    --label-a A-sin-prueba --label-b B-con-prueba \
    --proof-dir-b results/exp033/pruebas-tmp \
    --guard solver/kissat/build-m/kissat --conflicts 300000 --seeds 42 --mem-gb 6
python3 scripts/research12.py coste-prueba results/exp033/A.csv results/exp033/B.csv \
    > results/exp033/informe.txt
```

- **Presupuesto de conflictos** (300 000), no de tiempo. Las dos ramas hacen
  la misma búsqueda (H1), así que la diferencia de reloj es solo la
  escritura.
- **La prueba va a disco**, en el mismo sistema de ficheros del repositorio,
  no a `/dev/null`: la competición la escribe en disco. Se borra tras medir
  su tamaño (`B.pruebas.csv`).
- **Muestra**: 40 de tesis-dev (fácil, media, inestable), por cuota de
  familia (`research12.py seleccionar`).
- **Coste**: ~2 h.

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| H1 falla en alguna pareja | Se investiga: la prueba no debería cambiar la búsqueda (research/08, Teorema 5) |
| B/A < 1,03 (el IC por debajo de 1,05) | Se documenta como despreciable; nada que optimizar |
| B/A ≥ 1,03 | Se abre una candidata de clase E: búfer mayor o escritura asíncrona, con demostración de prueba idéntica byte a byte (research/08 §6) |

## 5. Amenazas a la validez

- **El disco del portátil no es el de la competición.** Lo que se mide es
  un orden de magnitud.
- **Con `labesat --symmetry`, el prefijo SR de satsuma se escribe aparte**
  (satsuma, antes de Kissat). Esto mide solo la parte DRAT de Kissat.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
