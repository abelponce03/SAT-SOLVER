# EXP-030 — Rampa del decaimiento VSIDS en modo estable (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con
  la opción `--decayramp` (0 por defecto).
- **Ejecuciones previas**: solo de corrección (research/12 §11).
- **Fecha**: 2026-10-05
- **Vía**: M5 (research/12 §5).
- **Decide**: si `--decayramp=200` pasa a candidata.

---

## 1. Qué se quiere saber

- En modo estable, Kissat decide con EVSIDS y un decaimiento fijo de 0,95
  (`decay` = 50 por mil).
- Glucose empieza en 0,80 y sube 0,01 cada 5000 conflictos hasta 0,95: al
  principio, cuando las puntuaciones aún no significan nada, la heurística
  reacciona antes.
- AE-Kissat-MAB, 1.º en 2025, evolucionó un decaimiento dinámico para su
  `bump` (research/07 §1).

`--decayramp=N` empieza en N por mil y baja 10 cada 5000 conflictos hasta
`decay`; con N = 200 es la rampa de Glucose. Solo afecta al modo estable:
el enfocado usa VMTF, sin decaimiento.

## 2. Hipótesis

Las de EXP-028 §2, con:

- A = sin opción;
- B = `--decayramp=200`.

**Predicción honesta**: efecto pequeño. La rampa termina en 75 000
conflictos, y el primer modo estable de Kissat empieza tras el enfocado
inicial (`modeinit` = 1000 conflictos y su réplica en *ticks*). La mayor
parte de la rampa cae en el primer tramo estable y solo afecta a las
instancias que se deciden pronto.

## 3. Diseño

El de EXP-028 §3, cambiando:

- `--opts-b=--decayramp=200`;
- la etiqueta, `B-decayramp`;
- las salidas, a `results/exp030/`.

No se prueba más de un valor de N: probar varios y quedarse con el mejor
sería elegir en la muestra.

## 4. Criterio de decisión

El de EXP-028 §4.

## 5. Amenazas a la validez

- **El conflicto como reloj de la rampa** mezcla los dos modos: en la
  práctica, la rampa avanza también durante el modo enfocado. Se acepta
  así, porque es la regla de Glucose, que no tiene modos.
- **AE-Kissat-MAB usa otro decaimiento**, evolucionado y sin publicar como
  regla cerrada. Esto prueba la idea clásica, no la suya.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
