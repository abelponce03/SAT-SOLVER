# Investigación 11 — B4: un selector estructural para la ruptura de simetrías

- **Fecha**: 2026-10-04
- **Estado**: **exploratorio**. La regla se eligió mirando los datos de este
  documento. No respalda ninguna afirmación de rendimiento hasta que la
  valide un experimento preregistrado con instancias frescas (§5).
- **Origen**: D-020, opción d; research/10 §0c.
- **Datos y cálculo**: `scripts/b4_exploratorio.py`, con salida en
  `results/estrategia/b4_exploratorio.md`. Los rasgos del banco simétrico
  salen del paso `b4-rasgos` de la cola (`results/b4/`).

---

## 1. Por qué

- **«Siempre» cambia de signo según el año**: 1.º en 2026 y 15.º en 2025
  (research/10 §0c). La entrada de 2025 usaba otra configuración (Kissat
  4.0.2, prueba VeriPB, satsuma sin tope), pero el patrón de familias
  apunta en la misma dirección.
- **«Nunca»** pierde en 2026 las familias combinatorias simétricas
  (+38 resueltas para el ganador).
- **B3**, la ruptura con retraso, se descartó en EXP-009: el tiempo no
  separa bien unas instancias de otras.
- **Un selector por SAT/UNSAT** tendría que predecir el resultado, que es lo
  difícil (research/10 §3.2).

B4 decide por lo que **encuentra satsuma**: la estructura del grupo de
simetrías, que se conoce antes de buscar.

## 2. Los rasgos

`scripts/scan_symmetry.py` registra lo que satsuma informa de sí mismo
(EXP-014 §3). Los que separan los dos bancos:

| Rasgo | Qué es | Banco simétrico (84) | Industria (450) |
|---|---|---|---|
| `row_column` | simetría de filas **y** columnas (matrices) | 26 % | **0 %** |
| `johnson` | esquemas de Johnson (subconjuntos) | 5 % | **0 %** |
| `orbitopal_units` | unidades de la ruptura orbitopal | 37 % | **0 %** |
| `sym_units ≥ 100` | al menos 100 unidades fijadas por simetría | 46 % | 13 % |
| `cambia` | algún predicado de ruptura (lo que hoy decide «siempre») | 63 % | 43 % |

La estructura combinatoria (matrices, subconjuntos, orbitopes) no aparece en
**ninguna** de las 450 instancias industriales. Las simetrías industriales
son pequeñas y locales: rompen algo, pero sobre todo perturban la búsqueda
(EXP-009 §7.1).

## 3. La regla y cómo se evalúa

```
R  =  row_column > 0  o  johnson > 0  o  orbitopal_units > 0  o  sym_units ≥ 100
```

B4 ejecuta satsuma **siempre** y solo usa su salida si se cumple R. Por eso su
tiempo es:

- t(B4) = t(«siempre») si se cumple R;
- t(B4) = t(«nunca») + min(t(satsuma), 60 s) si no, porque satsuma ya se
  ejecutó.

## 4. Resultado exploratorio

| Muestra | n | «siempre» | «nunca» | **B4** |
|---|---|---|---|---|
| Banco simétrico, tiempos oficiales de 2026 (T = 5000 s) | 84 | 103,8 | 3946,7 | **69,4** |
| Industria, EXP-014 parte 2 (T = 300 s) | 90 | 165,0 | 162,4 | **165,7** |
| Industria, EXP-009 principal (T = 300 s) | 153 | 204,6 | 194,6 | **197,7** |

**Lectura**:

- **Banco simétrico**: B4 conserva la ganancia de «siempre» e incluso la
  mejora: se ahorra las instancias en las que la ruptura estorbaba.
- **Industria**: B4 evita la perturbación de la búsqueda. En EXP-009 se
  queda en +3,1 s sobre «nunca», frente a +10 de «siempre». Lo que **no**
  evita es el coste fijo de ejecutar satsuma; en EXP-014, que ya era casi
  todo coste fijo (EXP-014 §8.3), B4 empata con «siempre».
- **Robustez**:
  - el umbral da lo mismo entre 50 y 200;
  - R coincide al 100 % entre satsuma sin cliques y mclique v2, el de
    `labesat`.

  La regla no depende de un ajuste fino.

**Por qué esto no es todavía un resultado**:

1. **Sesgo de diseño**: R se eligió mirando estas tres muestras, igual que el
   retraso de 2 s de B3, que luego falló con datos frescos (EXP-009 §7.1).
2. En el banco simétrico, los tiempos de «siempre» son los del ganador de
   2026 (satsuma 1.3 con cliquer), no los nuestros.
3. En EXP-009, la rama B es el retraso de 2 s, no «siempre».
4. El tiempo de satsuma sale de un escaneo aparte, no de la misma corrida.

## 5. Validación: EXP-023 (preregistrado el 2026-10-04, en la cola)

El director autorizó la descarga. El diseño definitivo está en
`docs/experiments/EXP-023-b4-fuera-de-muestra-2025.md`; lo que sigue es la
propuesta que lo originó.

**Muestra fresca**: las instancias de la **Main Track de 2025** con CNF de
como mucho 512 MiB.

- Son **374 de 400**. Las 26 restantes no pasan el tope de tamaño de
  satsuma: ahí las tres políticas son «nunca».
- **Nunca las hemos medido**, y son el año en el que la entrada de satsuma
  quedó 15.ª.
- Pesan 16,7 GB sin comprimir y unos 2-3 GB en `.xz`. Hay 22 GB libres.
- **Hace falta el permiso del director para descargarlas** (GBD,
  `benchmark-database.de`).

**Diseño** (se fija antes de descargar):

- **R queda fijada** como en §3, con U = 100. No se toca después de ver
  2025.
- **Paso 1**: `scan_symmetry.py` con `tools/satsuma-mclique` (el de
  `labesat`), tope de 60 s y 6 GB → rasgos, tiempo de satsuma y R por
  instancia.
- **Paso 2**: A/B intercalado de `labesat` «nunca» frente a «siempre».
  - T = 300 s, semilla 42, tope de 6 GB por proceso.
  - `run_ab_interleaved.py` no pone tope de memoria hoy: se añade la opción
    antes de ejecutar, porque 2025 tiene instancias que agotaron 30 GB en la
    competición.
  - B4 se compone instancia a instancia con la fórmula de §3, sin una
    tercera rama.
- **Coste**: ≤ 374 × 60 s (paso 1) + 374 × 2 × 300 s (paso 2) ≈ 68 h en el
  peor caso; unas 30-40 h esperadas.

**Hipótesis**:

> **H1.** En 2025, B4 no es peor que «nunca» en más de 5 s de PAR-2 (IC95 %
> bootstrap superior ≤ +5 s).
>
> **H2.** En 2025, B4 es mejor que «siempre» (ΔPAR-2 < 0, Wilcoxon p < 0,05).
>
> **H3 (descriptiva).** En cuántas instancias de 2025 se cumple R y en qué
> familias.

**Decisión**:

| Resultado | Decisión |
|---|---|
| H1 y H2 | B4 se implementa en `labesat` y en el binario integrado (leer los rasgos de satsuma), y pasa a candidata a V1 en D-020 |
| H2 sí, H1 no | B4 mejora a «siempre» pero no protege lo bastante: V1 «siempre», o B4 si 2027 se parece a 2026; vuelve a D-020 |
| H2 no | B4 no aporta fuera de muestra; se documenta y D-020 sigue con V1 y V2 |

**Lo que no cubre**:

- Ni 2026 ni 2025 sirven ya para validar la parte simétrica: el banco
  simétrico es de diseño, y 2025 apenas tiene familias simétricas
  (research/10 §0c).
- EXP-023 mide sobre todo que B4 **no cuesta** donde no hay simetría
  explotable. Lo que gana con simetría se apoya en §4, con su sesgo.
