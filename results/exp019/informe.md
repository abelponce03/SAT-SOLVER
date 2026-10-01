## EXP-019 — X1 (n = 577 instancias)

Resultado de X1: consistente 199, refutada 5, saltada 103, sin_mensaje 3, sin_xor 267

### H0 (seguridad, vinculante)

- Refutadas con resultado conocido SAT: **0**.
- Refutadas cuya prueba no verifica alguno de los dos dsr-trim: **0** de 5.

### H1 (búsqueda idéntica cuando no refuta)

- Parejas con los contadores idénticos: 321 de 321.

### H2 (coste)

- Tiempo de X1 por instancia (n = 574): mediana 0.020 s, p95 0.370 s, máximo 1.83 s, media 0.085 s.
- Corridas sin medida (tiempo agotado o sin mensaje): 3.

### H3 (efecto, descriptivo)

| instancia | banco | conocido | filas | certificado | X1 (s) | prueba (bytes) | dsr SC2026 (s) | dsr actual (s) |
|---|---|---|---|---|---|---|---|---|
| tseitin-malla_20 | sintetica | unsat | 400 | 400 | 0.00 | 1680576 | VERIFIED 0.98 | VERIFIED 0.92 |
| tseitin-regular_ | sintetica | unsat | 500 | 500 | 0.00 | 2248533 | VERIFIED 1.33 | VERIFIED 1.29 |
| lights-out_14_un | sintetica | unsat | 196 | 72 | 0.00 | 222942 | VERIFIED 0.04 | VERIFIED 0.04 |
| dos-ordenes_300_ | sintetica | unsat | 598 | 598 | 0.00 | 1777548 | VERIFIED 1.11 | VERIFIED 1.04 |
| 667341ee8c1dea3d | calib2 | unsat | 1750 | 596 | 0.00 | 1199153 | VERIFIED 0.79 | VERIFIED 0.81 |

### Ampliación (§3b): instancias de paridad de bench/dev

| instancia | conocido | resultado de X1 | filas | X1 (s) | prueba (bytes) | dsr SC2026 (s) | dsr actual (s) |
|---|---|---|---|---|---|---|---|
| 01d6fa8efd18ebfe | sat | consistente | 625 | 0.00 |  |   |   |
| 22c8d6aa86d51e15 | unsat | sin_xor | 0 | 0.13 |  |   |   |
| 7e21850936d61275 | unknown | sin_xor | 0 | 0.01 |  |   |   |
| 3a8409393cc1ebae | unknown | sin_xor | 0 | 0.01 |  |   |   |
| a60a138325ac9c88 | sat | consistente | 1611 | 0.01 |  |   |   |

- Seguridad en la ampliación (cuenta para H0): 0 fallos.

**Veredicto (§4)**: ADOPTAR (H0 sí, H1 sí, H2 sí)
