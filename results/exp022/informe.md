## EXP-022 — X1s (n = 582 instancias)

| X1 | X1s | instancias |
|---|---|---|
| consistente | actua | 7 |
| consistente | rechazada | 250 |
| refutada | no_aplica | 5 |
| saltada | no_aplica | 47 |
| sin_mensaje | no_aplica | 3 |
| sin_xor | no_aplica | 270 |

### H0 (seguridad, vinculante)

- X1s actúa en 7; con modelo no verificado, sin SAT o en una UNSAT conocida: **0**.

### H1 (búsqueda idéntica donde X1s se rechaza)

- Parejas con los contadores idénticos: 250 de 250 (rechazadas: 250).

### H2 (coste de X1s)

- n = 257: mediana 0.000 s, p95 0.010 s, máximo 0.04 s.

### H3 (dónde actúa)

| instancia | banco | conocido | filas | variables | X1s (s) | total (s) |
|---|---|---|---|---|---|---|
| tseitin-malla_20_20_sat_ | sintetica | sat | 400 | 800 | 0.00 | 0.01 |
| tseitin-regular_500_4_sa | sintetica | sat | 500 | 1000 | 0.00 | 0.02 |
| lights-out_14_sat_s7.cnf | sintetica | sat | 196 | 196 | 0.00 | 0.02 |
| dos-ordenes_300_sat_s7.c | sintetica | sat | 598 | 896 | 0.00 | 0.01 |
| 75429ff7acb5acb597abe01a | calib | sat | 250 | 250 | 0.00 | 0.02 |
| 28dcc4119e1bbb5fbd3fdd8f | symm2026 | sat | 2077 | 2077 | 0.00 | 0.03 |
| 01d6fa8efd18ebfecd06af40 | dev | sat | 625 | 625 | 0.00 | 0.02 |

**Veredicto (§4)**: ACTIVAR por defecto (H0 sí, H1 sí, H2 sí)
