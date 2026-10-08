## EXP-019 — X1 (n = 103 instancias)

Resultado de X1: consistente 56, saltada 47

### H0 (seguridad, vinculante)

- Refutadas con resultado conocido SAT: **0**.
- Refutadas cuya prueba no verifica alguno de los dos dsr-trim: **0** de 0.

### H1 (búsqueda idéntica cuando no refuta)

- Parejas con los contadores idénticos: 103 de 103.

### H2 (coste)

- Tiempo de X1 por instancia (n = 103): mediana 0.080 s, p95 0.340 s, máximo 1.47 s, media 0.130 s.
- Corridas sin medida (tiempo agotado o sin mensaje): 0.

### H3 (efecto, descriptivo)

| instancia | banco | conocido | filas | certificado | X1 (s) | prueba (bytes) | dsr SC2026 (s) | dsr actual (s) |
|---|---|---|---|---|---|---|---|---|

**Veredicto (§4)**: ADOPTAR (H0 sí, H1 sí, H2 sí)

### Cobertura: de X1 v1 (EXP-019) a X1 v2

| v1 → v2 | instancias |
|---|---|
| saltada → consistente | 56 |
| saltada → saltada | 47 |
