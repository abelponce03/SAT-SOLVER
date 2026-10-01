## Distancia de LabeSAT a la Main Track de 2026 (contrafactual con tiempos oficiales)

Ganador: `anders_satsuma-iter-kissat[main]`, PAR-2 3647.0, 276 resueltas.

| Configuración | Resueltas | PAR-2 | Δ frente al ganador | Puesto en 2026 |
|---|---|---|---|---|
| LabeSAT por defecto hoy (Kissat 4.0.4, sin simetrías) ≈ K | 238 | 4611.5 | +964.5 | 16 |
| LabeSAT `--symmetry` siempre ≈ S (el ganador) | 276 | 3647.0 | +0.0 | 1 |
| LabeSAT B3 (retraso 2 s) | 276 | 3644.5 | -2.5 | 1 |
| LabeSAT B3 + X1 | 278 | 3587.9 | -59.1 | 1 |
| LabeSAT B3 + X1 + PGO/LTO | 278 | 3572.3 | -74.7 | 1 |
| Referencia: S + X1 (si el ganador tuviera X1) | 278 | 3590.5 | -56.5 | 1 |

X1 actúa en 4 instancias (lights-out UNSAT): 0efcbd10 (K 4288, S 2184), 32e344a5 (K inf, S inf), 667341ee (K 388, S 431), 80b163b7 (K inf, S inf)

Frente al ganador: LabeSAT final resuelve 2 que él no y pierde 0 que él sí.
- Gana: lights-out (2)

Instancias que resuelve algún solver del top-10 de 2026 y LabeSAT final no: 56.

| Familia | Resultado | Instancias | Ejemplo de quién la resuelve |
|---|---|---|---|
| linear-equations | sat | 12 | lymphosat |
| ntil | sat | 4 | satsuma-iter-ae-kissat-mab, kissat-mab-hypre-satlution, lymphosat |
| syndrome-decoding | sat | 4 | mergesat-l, satsuma-lex-ae-kissat-mab |
| boxfolding | sat | 3 | kissat-mab-hypre, kissat-mab-hypre-v2, kissat-mab-hypre-satlution |
| allowable-seqence | sat | 3 | satsuma-iter-ae-kissat-mab, kissat-mab-hypre-evolve, satsuma-lex-ae-kissat-mab |
| sorting-networks | sat | 2 | kissat-mab-hypre, kissat-mab-hypre-v2, kissat-mab-hypre-evolve |
| minimal-disagreement-parity | sat | 2 | lymphosat, mergesat-l |
| xor-shifting | sat | 2 | kissat-mab-hypre, kissat-mab-hypre-v2 |
| station-repacking | sat | 2 | satsuma-iter-ae-kissat-mab, kissat-mab-hypre, kissat-mab-hypre-v2 |
| datapath-equivalence-checking | unsat | 2 | mergesat-l |
| cyclic-anti-bandwidth | sat | 2 | satsuma-iter-ae-kissat-mab, kissat-mab-hypre, kissat-mab-hypre-v2 |
| binary-tree-parity | sat | 1 | lymphosat |
| antibandwidth | sat | 1 | satsuma-iter-ae-kissat-mab, kissat-mab-hypre, kissat-mab-hypre-v2 |
| fermat | sat | 1 | lymphosat |
| equivalence-chain-principle | unsat | 1 | mergesat-l |
| cyclic-anti-bandwidth | unsat | 1 | kissat-mab-hypre-evolve, mergesat-l, satsuma-lex-ae-kissat-mab |
| coloring | sat | 1 | satsuma-iter-ae-kissat-mab, mergesat-l |
| circuit-multiplier | sat | 1 | kissat-mab-hypre-evolve, kissat-mab-hypre-satlution, mergesat-l |
| argumentation | sat | 1 | kissat-mab-hypre, kissat-mab-hypre-v2, kissat-mab-hypre-evolve |
| automata-synchronization | sat | 1 | lymphosat |

**Cartera secuencial** (LabeSAT final durante f·T y, si no resuelve, la variante MAB del 3.º):

| f | Resueltas | PAR-2 | Δ frente al ganador |
|---|---|---|---|
| 0.5 | 259 | 3862.2 | +215.2 |
| 0.6 | 259 | 3856.5 | +209.4 |
| 0.7 | 258 | 3863.8 | +216.8 |
| 0.8 | 266 | 3744.3 | +97.2 |
| 0.9 | 277 | 3586.2 | -60.9 |

Oráculo (LabeSAT final, anders_satsuma-iter-ae-kissat-mab): 292 resueltas, PAR-2 3201.0.
Oráculo de los 33 solvers de 2026: 354 resueltas, PAR-2 1495.5.
