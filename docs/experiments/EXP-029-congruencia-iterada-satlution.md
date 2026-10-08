# EXP-029 — Réplica fuera de muestra de SATLUTION: congruencia y reducción transitiva iteradas (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con
  la opción `--probeiterate` (apagada).
- **Ejecuciones previas**: solo de corrección (research/12 §11).
- **Fecha**: 2026-10-05
- **Vía**: M8 (research/12 §6).
- **Decide**: si `--probeiterate` pasa a candidata. Es además el primer caso
  medido de una mejora «evolucionada con LLM» replicada con preregistro
  (material para el artículo metodológico; research/07, N7).

---

## 1. Qué se quiere saber

- **El cambio.** SATLUTION (Kissat_MAB 4.0.2 evolucionado con LLM; paquete
  oficial de 2026, MIT) cambió `probe()` así: si la reducción transitiva
  quitó binarias, se ejecuta otra vez la congruencia (ciclo 42) y después
  una segunda reducción transitiva (ciclo 51).
- **La evidencia a favor.** Su `RESULTS.md` dice −61 s de PAR-2 y +4 SAT
  resueltas sobre su banco, con un ruido de σ ≈ 22. El cambio se aceptó con
  α = 0, es decir, se quedaba si bajaba el PAR-2 **en la misma muestra**.
- **La evidencia en contra.** En la SAT Competition 2026,
  `zheng_kissat-mab-hypre-satlution` quedó por detrás de su base,
  `zheng_kissat-mab-hypre`: 253 frente a 255 resueltas y PAR-2 4066,8
  frente a 3996,3. Esa diferencia incluye otros dos cambios de SATLUTION,
  el arreglo de `eliminate.c` (EXP-028) y la guarda de CHB.

¿Hay algún efecto fuera de su muestra?

## 2. Hipótesis

Las de EXP-028 §2, con:

- A = sin opción;
- B = `--probeiterate=1`.

**Predicción honesta**: **nula**. Es la de mayor riesgo de ser ruido de
selección. Se declara antes para que un nulo no se lea como fallo del
diseño.

## 3. Diseño

El de EXP-028 §3, cambiando:

- `--opts-b=--probeiterate=1`;
- la etiqueta, `B-probeiterate`;
- las salidas, a `results/exp029/` (`A1/B1`, `A2/B2`, `cribado.txt`,
  `confirmacion.txt`).

Mismas listas y mismo binario (`build-m`).

## 4. Criterio de decisión

El de EXP-028 §4. Además, cualquier resultado se documenta junto a la cifra
de SATLUTION (−61 s dentro de la muestra) como comparación metodológica.

## 5. Amenazas a la validez

- **Base distinta**: SATLUTION partía de Kissat_MAB 4.0.2; nosotros, de
  Kissat 4.0.4 sin MAB. El cambio es local a `probe()` y no depende del
  MAB, pero el efecto puede depender de la base.
- **Coste**: si `kissat_congruence` es cara en una instancia, la segunda
  llamada lo duplica. Se ve en H2.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
