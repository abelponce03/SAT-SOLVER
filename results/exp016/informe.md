## EXP-016 — perfil de costes (n = 105 instancias)

Estados: UNKNOWN 45, SAT 36, UNSAT 23, ERROR 1

### Q1. Fracción del tiempo de Kissat por fase

Ponderada = Σ segundos de la fase / Σ segundos totales. Las fases anidadas están incluidas en su madre (ver la cabecera del script).

#### industria (n = 45, 6866 s en total)

| nivel 1 | ponderada (%) | mediana (%) | p90 (%) |
|---|---|---|---|
| parse | 0.2 | 0.1 | 0.9 |
| search | 77.1 | 74.3 | 92.0 |
| simplify | 21.7 | 23.9 | 42.1 |
| resto | 1.0 | 0.4 | 3.7 |

| dentro de search | ponderada (%) | mediana (%) | p90 (%) |
|---|---|---|---|
| focused | 39.3 | 38.4 | 48.2 |
| stable | 37.7 | 37.4 | 44.9 |
| busqueda_sin_hijos | 56.7 | 54.0 | 69.8 |
| analyze | 18.6 | 19.3 | 27.2 |
| deduce | 3.4 | 3.9 | 5.2 |
| minimize | 0.5 | 0.5 | 1.0 |
| shrink | 5.7 | 5.2 | 8.5 |
| bump | 2.7 | 2.7 | 4.5 |
| reduce | 1.3 | 1.2 | 2.4 |
| restart | 0.3 | 0.3 | 0.8 |
| rephase | 0.0 | 0.0 | 0.0 |
| reorder | 0.1 | 0.1 | 0.3 |

| dentro de simplify | ponderada (%) | mediana (%) | p90 (%) |
|---|---|---|---|
| probe | 18.5 | 20.0 | 34.7 |
| vivify | 8.6 | 9.2 | 11.5 |
| sweep | 3.9 | 2.7 | 11.7 |
| substitute | 1.6 | 1.7 | 4.3 |
| backbone | 0.7 | 0.4 | 2.4 |
| transitive | 0.4 | 0.4 | 0.9 |
| factor | 1.9 | 1.7 | 4.4 |
| eliminate | 3.6 | 2.3 | 9.7 |
| subsume | 0.7 | 0.4 | 1.8 |
| congruence | 1.4 | 0.4 | 3.6 |
| walking | 0.4 | 0.3 | 1.0 |

| en los dos lados | ponderada (%) | mediana (%) | p90 (%) |
|---|---|---|---|
| collect | 1.2 | 1.1 | 2.2 |
| defrag | 0.1 | 0.1 | 0.2 |

#### 2026 (n = 60, 4764 s en total)

| nivel 1 | ponderada (%) | mediana (%) | p90 (%) |
|---|---|---|---|
| parse | 1.0 | 0.0 | 92.3 |
| search | 76.2 | 76.5 | 92.0 |
| simplify | 17.9 | 12.6 | 38.7 |
| resto | 4.9 | 0.6 | 10.9 |

| dentro de search | ponderada (%) | mediana (%) | p90 (%) |
|---|---|---|---|
| focused | 39.9 | 37.8 | 49.1 |
| stable | 36.3 | 35.3 | 44.7 |
| busqueda_sin_hijos | 58.7 | 55.4 | 71.4 |
| analyze | 16.0 | 15.1 | 28.6 |
| deduce | 3.5 | 2.7 | 6.4 |
| minimize | 0.5 | 0.4 | 1.2 |
| shrink | 4.1 | 4.1 | 7.8 |
| bump | 2.5 | 2.4 | 5.1 |
| reduce | 1.2 | 0.9 | 2.3 |
| restart | 0.2 | 0.0 | 0.4 |
| rephase | 0.0 | 0.0 | 0.0 |
| reorder | 0.1 | 0.0 | 0.3 |

| dentro de simplify | ponderada (%) | mediana (%) | p90 (%) |
|---|---|---|---|
| probe | 15.0 | 11.2 | 31.1 |
| vivify | 7.9 | 7.5 | 12.0 |
| sweep | 2.9 | 2.0 | 9.9 |
| substitute | 1.2 | 0.5 | 4.0 |
| backbone | 0.4 | 0.0 | 1.1 |
| transitive | 0.3 | 0.1 | 0.8 |
| factor | 1.9 | 0.4 | 6.3 |
| eliminate | 3.0 | 0.6 | 9.2 |
| subsume | 1.1 | 0.1 | 2.9 |
| congruence | 0.5 | 0.1 | 1.4 |
| walking | 0.5 | 0.2 | 1.2 |

| en los dos lados | ponderada (%) | mediana (%) | p90 (%) |
|---|---|---|---|
| collect | 1.1 | 0.9 | 2.1 |
| defrag | 0.3 | 0.1 | 1.9 |

### Q2. Por duración de la corrida (los dos grupos juntos)

| estrato | n | parse | search | simplify | busqueda_sin_hijos | analyze | probe | vivify | eliminate |
|---|---|---|---|---|---|---|---|---|---|
| < 10 s | 20 | 36.4 | 37.4 | 20.5 | 24.8 | 11.4 | 19.5 | 5.6 | 3.9 |
| 10–100 s | 32 | 1.1 | 73.8 | 24.0 | 51.9 | 19.9 | 20.1 | 8.9 | 4.3 |
| ≥ 100 s | 53 | 0.1 | 77.4 | 19.6 | 58.6 | 17.3 | 16.6 | 8.2 | 3.2 |

### Q3. Descompresión xz

- Σ xz = 61.3 s frente a Σ kissat = 11746 s (0.52 %); mediana por instancia 0.08 %, máximo 56.2 %.

### Q4. Nivel 4 con 200 000 conflictos (n = 20)

- Mismo trabajo en las dos corridas (conflictos y propagaciones): 20 de 20.
- Sobrecoste de los temporizadores de nivel 4: media geométrica ×1.145 (mín ×1.034, máx ×1.440; n = 16, total_3 ≥ 1 s).
- propagate: ponderada 56.6 %, mediana 51.1 %, p90 65.7 %.
- decide: ponderada 1.0 %, mediana 1.1 %, p90 2.3 %.
- analyze: ponderada 13.6 %, mediana 17.1 %, p90 31.6 %.
- busqueda_sin_hijos: ponderada 52.8 %, mediana 49.4 %, p90 63.1 %.
