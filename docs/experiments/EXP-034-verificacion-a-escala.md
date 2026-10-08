# EXP-034 — Verificación de las pruebas a escala: ¿contarán nuestros UNSAT? (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con
  `scripts/exp034.py` y las listas `results/exp034/simetricas.txt` y
  `industria.txt`. Ejecución previa: la prueba del guion en dos palomares
  de `bench/smoke` (verificados por los dos `dsr-trim`).
- **Fecha**: 2026-10-05
- **Vía**: M12 (research/12 §8).
- **Decide**:
  - si las pruebas de V1 (`labesat --symmetry`, con X1) verifican a escala;
  - si el tiempo de verificación es un riesgo para la competición;
  - aporta el dato para elegir verificador (fase 5, H8).

---

## 1. Qué se quiere saber

- En 2026, 12 respuestas de entradas de cabeza se perdieron por
  *checker-timeout*:
  - las cuatro variantes de `zheng`, dos cada una;
  - tres de `oertel`;
  - una de `reeves`.
- Un UNSAT sin prueba verificada no cuenta.
- Nuestras pruebas mezclan el prefijo SR de satsuma, el DRAT de Kissat y las
  variables de extensión de X1. Se ha comprobado que **verifican** en
  EXP-007, 010, 011, 012, 019 y 022, pero no **cuánto tardan** ni **cuánto
  ocupan** a escala.

## 2. Hipótesis

> **H1 (vinculante).** Todas las pruebas de los UNSAT las aceptan los dos
> `dsr-trim`, el actual y el de SC2026, o como mucho agotan su tope.
> Ninguna es rechazada.
>
> **H2 (descriptiva).** Distribución de la razón
> t(verificación SC2026) / t(resolución) y del tamaño de la prueba.
>
> **H3 (riesgo).** Ninguna instancia tiene una razón > 8. Con T = 5000 s de
> resolución, una razón de 8 agota 40 000 s de verificación.

El límite de verificación de 2027 está por confirmar. Se toma 40 000 s como
referencia y se recalcula cuando salgan las reglas.

## 3. Diseño

```bash
LABESAT_KISSAT=$PWD/solver/kissat/build-m/kissat python3 scripts/exp034.py correr \
    --listas results/exp034/simetricas.txt results/exp034/industria.txt \
    --bench bench/symm2026 bench/tesis-dev --out results/exp034/verificacion.csv \
    --timeout 300 --check-timeout 3600 --tmp results/exp034
python3 scripts/exp034.py analizar results/exp034/verificacion.csv > results/exp034/informe.txt
```

- **Muestra**:
  - las 41 UNSAT de symm2026 donde satsuma añade ruptura;
  - 30 UNSAT de tesis-dev (fácil, media, inestable), por cuota de familia.
- **Configuración**: la V1 de D-020, `labesat --symmetry` con el Kissat
  adoptado (`build-m` con las opciones de research/12 apagadas, que hace la
  misma búsqueda), semilla 42 y T = 300 s.
- **Verificación**: los dos `dsr-trim` sobre la CNF **original**, con un
  tope de 3600 s cada uno, midiendo el reloj. La prueba se borra después.
- **Una corrida por instancia, no un A/B**: se mide la verificación, no se
  compara el solver.
- **Coste**: ≤ 71 × (300 s + 2 × 3600 s) en el peor caso; se esperan ~10 h.

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| H1 falla (alguna prueba rechazada) | **Bloqueante**: se busca la causa antes de cualquier variante con esa configuración (ADR-0004, criterios de reversión) |
| H1 y H3 se cumplen | Se documenta. El verificador de H8 es el `dsr-trim` del commit de la competición |
| H3 falla | Riesgo de *checker-timeout*. Se miran las instancias: ¿prefijo de satsuma grande, cadenas de X1 o DRAT largo? Se abre una candidata para recortar la prueba (borrar lemas, o el tope de modelos de satsuma, EXP-024) |

## 5. Amenazas a la validez

- **T = 300 s, no 5000 s.** La razón verificación/resolución puede crecer
  con pruebas más largas. Se informa por tramos de tiempo de resolución para
  ver la tendencia.
- **Máquina local frente a la de verificación de la competición.** La razón
  es más estable que los tiempos absolutos.
- **Tope de 3600 s.** Una verificación que lo agota cuenta como `TOPE`, no
  como rechazo, y se informa aparte.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
