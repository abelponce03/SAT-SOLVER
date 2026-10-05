# EXP-032 — X2: la solución de Gauss como fase inicial (preregistrado, prioridad baja)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con:
  - la opción `--gaussphase` (apagada);
  - las listas `results/exp032/cribado.txt` y `confirmacion.txt`.
- **Ejecuciones previas**: solo de corrección (research/12 §11). En
  `test_opciones_m.sh`, X2 pone 288 fases en una paridad sintética con una
  cláusula ajena.
- **Fecha**: 2026-10-05
- **Vía**: X2 (research/06 §X2; research/12 §4).
- **Decide**: si `--gaussphase` pasa a candidata.

---

## 1. Qué se quiere saber

- research/06 descartó X2 por efecto pequeño: ~6 s de PAR-2 estimados en
  2026, sin cambiar ninguna instancia de estado. La veía razonable solo
  «como subproducto de X1, a coste marginal».
- Con X1s ya lo es. Cuando el sistema XOR es consistente pero σ no satisface
  todas las cláusulas, X1s la descarta; X2 la copia como **fase guardada
  inicial** de las variables del sistema.
- **Dónde actúa**: en las 250 instancias de EXP-022 con X1 consistente y X1s
  rechazada. Casi todas son de tesis-dev (226) y de resultado desconocido o
  industrial.

## 2. Hipótesis

Las de EXP-028 §2, con:

- A = sin opción;
- B = `--gaussphase=1`;
- las listas propias (`results/exp032/`).

**Predicción honesta**: nula. La fase inicial dura poco en Kissat, y en las
industriales el sistema XOR suele ser una parte pequeña de la fórmula. Va al
final de la cola por eso.

## 3. Diseño

El de EXP-028 §3, cambiando:

- las listas: `results/exp032/cribado.txt` (40) y `confirmacion.txt` (60),
  disjuntas, del conjunto «X1 consistente, X1s rechazada» de EXP-022;
- los bancos: `--bench bench/tesis-dev bench/calib bench/calib2
  bench/symm2026 bench/dev`, donde están;
- `--opts-b=--gaussphase=1`, la etiqueta `B-gaussphase` y las salidas en
  `results/exp032/`.

## 4. Criterio de decisión

El de EXP-028 §4. Si no pasa el cribado, X2 queda cerrada definitivamente
(research/06 ya la había descartado sobre el papel).

## 5. Amenazas a la validez

- **Muestra condicionada a X1s** (σ rechazada), que es exactamente donde se
  desplegaría X2: no es un sesgo, es su ámbito.
- **Las variables libres del sistema** reciben la fase inicial por defecto
  (verdadero), así que X2 solo cambia las variables pivote.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
