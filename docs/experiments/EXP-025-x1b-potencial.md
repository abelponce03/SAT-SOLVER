# EXP-025 — X1b: ¿cuántas unidades y equivalencias daría Gauss-Jordan que la propagación no ve? (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con
  `scripts/x1b_potencial.py`. Única ejecución previa: la prueba del guion
  sobre:
  - dos familias sintéticas (`gen_paridad.py`);
  - tres instancias de `calib` con XOR, que dieron 0 unidades y 0
    equivalencias nuevas.

  Esas tres no condicionan el umbral.
- **Fecha**: 2026-10-05
- **Vía**: M4 (research/12 §4; diseño de X1b en research/09 §5).
- **Decide**: si X1b se implementa en Kissat o se descarta.

---

## 1. Qué se quiere saber

- X1b llevaría el sistema XOR a forma escalonada reducida y añadiría, con
  prueba DRAT:
  - las filas con una variable, que son unidades;
  - las filas con dos, que son equivalencias.
- Implementarlo cuesta:
  - registrar variables de extensión en Kissat;
  - una prueba sin borrados, que encarece la verificación (research/09 §5).
- Su valor está **sin estimar**. Antes de construirlo, se mide cuánto hay
  que ganar.

## 2. Hipótesis

> **H1 (descriptiva).** Por banco: instancias con al menos una **unidad
> nueva**, con al menos una **equivalencia nueva**, y su distribución.
> Nueva quiere decir que no la da la propagación en la raíz ni está ya en
> la CNF como XOR de dos variables.
>
> **H2 (decisión).** Al menos **10** instancias de bancos reales (no
> sintéticas) tienen alguna unidad nueva, o al menos **10** tienen 10 o más
> equivalencias nuevas.

**Predicción honesta**: H2 no se cumple. En la industria los sistemas XOR
que encuentra X1 son consistentes y de rango casi completo, y lo que
implican lo ve ya la propagación o el cierre por congruencia de Kissat.
Si es así, X1b se descarta con este dato.

## 3. Diseño

```bash
python3 scripts/x1b_potencial.py --muestra results/exp019/muestra.csv \
    results/exp019/muestra-dev.csv --out results/exp025/x1b.csv
python3 scripts/exp025.py analizar > results/exp025/informe.md
```

- **Muestra**: la de EXP-019 y su ampliación (582 instancias de `calib`,
  `calib2`, `symm2026`, `tesis-dev`, `dev` y sintéticas). Es la muestra con
  la que se cerró X1, y en ella están todos los sistemas XOR conocidos.
- **Qué hace el guion**:
  1. propagación unitaria en la raíz;
  2. extracción de X1 (k ≤ 6);
  3. Gauss-Jordan por componentes conexas.

  Una componente de más de 4000 filas u 8000 columnas se salta y se cuenta
  como saltada. Las 47 que X1 v2 tampoco procesa tienen una componente
  gigante.
- **Determinista**: no mide tiempos de búsqueda. El tiempo que informa es
  el del propio diagnóstico, solo para dimensionar.
- **Coste**: ~1 h (la lectura en Python de las CNF grandes); como mucho,
  3 h.

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| H2 se cumple | Se implementa X1b en `gauss.c` (research/09 §5), detrás de una opción apagada, y se mide con un A/B en las instancias donde actúa |
| H2 no se cumple | **Se descarta X1b**, con este dato en research/09 §5 |
| Más del 30 % de las instancias con XOR tienen componentes saltadas | Se repite con topes mayores antes de decidir, porque el recuento sería una cota inferior |

## 5. Amenazas a la validez

- **Cota superior** de lo que X1b aportaría. No se descuentan las
  equivalencias que encontraría el cierre por congruencia de Kissat
  (`congruencexors`).
- **Cota inferior** en las componentes saltadas.
- **La extracción es la de X1**. Las paridades codificadas con contadores
  (*xor-chain*, *tseitin-formulas* de 2026; EXP-019 §3b) no las ve ni X1 ni
  X1b.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
