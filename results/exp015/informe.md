### A/B — A = `A-base` vs B = `B-vsa`

Banco: 60 instancias comunes · timeout 300s · 2 seeds/instancia · tiempo de CPU

| métrica | A | B | Δ (B−A) |
|---|---:|---:|---:|
| PAR-2 (s) | 101.800 | 115.048 | **+13.248** (+13.0%) |
| resueltas en todas las seeds | 53 | 53 | +0 |
| flaky | 6 | 3 | -3 |
| p90 ratio entre seeds | 2.39x | 2.40x | — |

- ΔPAR-2 medio = **+13.248 s**, IC95% bootstrap = [-4.972, +33.641] (incluye 0 → no concluyente)
- Wilcoxon emparejado: W=824.0, p=0.6479 (n efectivo=59)
- McNemar sobre resueltas: A-sí/B-no=2, A-no/B-sí=2, p=1.0000
- Robustez: flaky→estable = 2, estable→flaky = 2
120 parejas (instancia × semilla) en común
   descartadas por alguna rama no resuelve: 14
   descartadas por tiempo < 1.0 s: 0
   parejas válidas: 106 en 55 instancias

== Métrica primaria: tiempo de CPU
   log(t_B / t_A):
      instancias           55   (B mejor en 29, peor en 26)
      factor geométrico    1.008x   IC95% [0.878x, 1.172x]
      Wilcoxon             W=707.0  p=0.6005  (n efectivo=55)

== Comprobación contra la deriva: propagaciones (deterministas)
   log(prop_B / prop_A):
      instancias           55   (B mejor en 25, peor en 28)
      factor geométrico    1.001x   IC95% [0.881x, 1.148x]
      Wilcoxon             W=676.0  p=0.7299  (n efectivo=53)

== VEREDICTO según el criterio preregistrado (EXP-006 §4)
   H1 NO CONFIRMADA (p = 0.6005, factor 1.008x).
