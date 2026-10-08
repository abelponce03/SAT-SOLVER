## EXP-020 — tope de satsuma: 60 s frente a 300 s

**Fase 1** (satsuma solo, tope 300 s): 5 de 13 terminan.

| instancia | salida | segundos | cláusulas de entrada → salida |
|---|---|---|---|
| 34360a677fc85418 | TOPE | 300.218 | 9993021 →  |
| 80bb5209e88def56 | TOPE | 300.517 | 25473117 →  |
| 8db998d5fd64f85a | 0 | 125.103 | 7173053 → 4824073 |
| 008e7716c6900909 | 0 | 66.386 | 207720 → 202873 |
| 3728eb69fc604689 | -6 | 119.846 | 7803199 →  |
| fbe4f6664edfbbfb | -6 | 83.240 | 7803199 →  |
| 8bb5819a23a8f1df | 0 | 164.847 | 214438 → 204259 |
| 8eff8708d366c104 | 0 | 201.329 | 177114 → 166849 |
| bc198d71cb351357 | 0 | 178.732 | 193454 → 193668 |
| 3bbdfd39be8452f7 | -6 | 56.660 | 11784087 →  |
| 613be3fce8fa3e51 | -6 | 45.884 | 12515823 →  |
| b3233e009976748e | -11 | 48.139 | 15032078 →  |
| bbdc1542ad1cd213 | -6 | 43.182 | 18768475 →  |

**Fase 2** (labesat con B3, T = 1200 s, n = 13):
- Resueltas: tope 60 s 9, tope 300 s 9.
- PAR-2 medio: tope 60 s 826.1, tope 300 s 850.6 (Δ = +24.6 s).

| instancia | estado 60 s | t (s) | estado 300 s | t (s) |
|---|---|---|---|---|
| 008e7716c6900909 | UNSAT | 81.474 | UNSAT | 81.371 |
| 34360a677fc85418 | SAT | 1.403 | SAT | 1.353 |
| 3728eb69fc604689 | TIMEOUT | 1204.694 | TIMEOUT | 1206.050 |
| 3bbdfd39be8452f7 | UNSAT | 96.802 | UNSAT | 89.641 |
| 613be3fce8fa3e51 | UNSAT | 596.074 | UNSAT | 657.348 |
| 80bb5209e88def56 | SAT | 68.733 | SAT | 309.069 |
| 8bb5819a23a8f1df | SAT | 91.375 | SAT | 141.809 |
| 8db998d5fd64f85a | SAT | 1.003 | SAT | 1.002 |
| 8eff8708d366c104 | SAT | 1.504 | SAT | 1.554 |
| b3233e009976748e | UNSAT | 200.523 | UNSAT | 175.200 |
| bbdc1542ad1cd213 | TIMEOUT | 1225.051 | TIMEOUT | 1219.873 |
| bc198d71cb351357 | TIMEOUT | 1259.128 | TIMEOUT | 1198.706 |
| fbe4f6664edfbbfb | TIMEOUT | 1202.142 | TIMEOUT | 1199.853 |

**Decisión (§4)**: mantener 60 s (resueltas 9 frente a 9; ΔPAR-2 +24.6 s).
