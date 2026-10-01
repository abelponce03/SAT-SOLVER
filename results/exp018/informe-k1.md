## EXP-017 — k1 (n = 85 parejas, presupuesto conflicts = 200000)

**Equivalencia**: 85 de 85 parejas idénticas (estado, conflictos, decisiones, propagaciones).

**Velocidad** (n = 80; 5 parejas con cpu_A < 1 s excluidas):
- aceleración geométrica s = 0.931, IC95 % [0.906, 0.953], Wilcoxon p = 4.34e-09
- tiempo total de CPU: A 2238 s, B 2389 s (cociente 0.937)

**Veredicto (ADR-0009 §2)**: no se adopta (equivalente; IC inferior 0.906 ≤ 1)

**Descriptivo por grupo** (sin umbral):
- 2026: n = 34, aceleración geométrica 0.931
- industria: n = 46, aceleración geométrica 0.930
