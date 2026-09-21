# EXP-004 — Detector estructural barato: ¿cuándo conviene el preprocesado caro?

- **Estado**: estudio previo **hecho** (con datos oficiales) · experimento sobre el solver pendiente
- **Fecha**: 2026-09-21
- **Motiva**: [`docs/research/02-catalogo-de-ideas.md`](../research/02-catalogo-de-ideas.md) línea B3
- **Independiente de**: EXP-001/002/003 (se puede avanzar en paralelo)

---

## 1. Pregunta

Los datos de 2026 muestran que el preprocesado agresivo es **asimétrico**: el
ganador (`satsuma-iter-kissat`) convierte **51 timeouts en resoluciones** pero
**rompe 13 instancias** que la base sí resolvía. Aplicarlo siempre deja dinero
sobre la mesa: el oráculo que decide *cuándo* aplicarlo vale **−322 s** de PAR-2
adicionales sobre aplicarlo incondicionalmente.

> ¿Se puede aproximar ese oráculo con **features estáticos y baratos** de la
> fórmula, sin ejecutar nada?

Si la respuesta es sí, la contribución es pequeña, autocontenida, medible y
**útil para cualquier solver**, no solo para el nuestro.

## 2. Estudio previo con datos oficiales (hecho)

No hace falta escribir una línea de C para tener la primera respuesta: basta
cruzar los resultados por instancia de 2026 con los 59 features estáticos que
la Global Benchmark Database publica (recuentos de cláusulas por tamaño,
fracciones Horn/inv-Horn, grafos variable-cláusula y variable-variable, grados,
entropías, tamaño en bytes, componentes conexas).

**Método**: clasificador (gradient boosting, 200 árboles, profundidad 3) con
**validación cruzada estratificada de 5 pliegues** — el predictor nunca decide
sobre instancias que ha visto. Reproducir con:

```bash
python3 scripts/analyze_conditional.py --treatment anders_satsuma-iter-kissat
python3 scripts/analyze_conditional.py --treatment 'zheng_kissat-mab-hypre[main]'
```

### Resultado 1 — tratamiento = ruptura de simetrías (satsuma)

| estrategia | resueltas | PAR-2 | Δ vs base |
|---|---:|---:|---:|
| base siempre | 114 | 3634.8 | 0.0 |
| tratamiento siempre | 113 | 3614.1 | −20.8 |
| **predictor (CV 5-fold)** | **115** | **3540.2** | **−94.6** |
| oráculo (techo) | 119 | 3269.1 | −365.7 |

Exactitud 66.5 %. **El predictor captura el 26 % del hueco del oráculo y bate a
"aplicarlo siempre" por 73.9 s.**

### Resultado 2 — tratamiento = hiper-resolución binaria (hypre)

| estrategia | resueltas | PAR-2 | Δ vs base |
|---|---:|---:|---:|
| base siempre | 114 | 3634.8 | 0.0 |
| tratamiento siempre | 114 | 3589.2 | −45.6 |
| **predictor (CV 5-fold)** | **116** | **3506.2** | **−128.6** |
| oráculo (techo) | 122 | 3120.6 | −514.2 |

Exactitud 65.9 %, **25 % del hueco capturado**. Dos técnicas distintas, dos
grupos distintos, el mismo comportamiento: **condicionar gana a aplicar
siempre**, con features que se calculan en un barrido de la fórmula.

### Limitaciones de este estudio previo (importantes)

- **Cobertura parcial y sesgada**: solo 167 de las 400 instancias de 2026 tienen
  features calculados en GBD, y no es una muestra aleatoria (GBD tiene
  calculados sobre todo los de ediciones anteriores). En ese subconjunto la
  diferencia entre base y tratamiento es mucho menor que en el banco completo
  (−20.8 s frente a −964.5 s), así que **las cifras absolutas no son
  extrapolables**; lo que sí traslada es el ordenamiento: predictor < siempre.
- **El predictor decide sobre la fórmula original**, no sobre la simplificada
  tras el preprocesado de Kissat, que es donde habría que decidir en la
  práctica.
- **Un solo año**. Hay que repetirlo con 2024 en cuanto se tengan los datos
  instancia-por-instancia de esa edición.
- **66 % de exactitud es poco**: la ganancia sale de que los errores son baratos
  (elegir mal cuesta el margen entre dos tiempos parecidos) mientras que los
  aciertos en los casos extremos son muy valiosos. Conviene reformular el
  problema como **regresión sobre el ΔPAR-2 esperado** en vez de clasificación,
  y ponderar cada instancia por lo que hay en juego.

## 3. Experimento pendiente sobre el solver

1. Implementar en Kissat el cálculo de un subconjunto barato de esos features
   (los que se obtengan en un barrido: recuentos por tamaño de cláusula, Horn,
   grados medios y varianzas). Objetivo de coste: **< 1 % del presupuesto**.
2. Comprobar que reproducen los de GBD (test de regresión contra sus valores).
3. Entrenar el predictor fuera de línea y empotrar el modelo (un árbol pequeño
   o una regresión logística: decenas de coeficientes, no una red).
4. A/B sobre `bench/dev`: `--preprocesado-agresivo=siempre` vs `=condicional`.
5. Validación única sobre `bench/test`.

## 4. Criterio de éxito

El predictor condicional debe batir a "aplicar siempre" en PAR-2 sobre
`bench/test`, con IC95% bootstrap que excluya el 0. Si solo empata, la
contribución se reduce a "el coste de decidir es despreciable", que es un
resultado menor pero publicable como nota.
