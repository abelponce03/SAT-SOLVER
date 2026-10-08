#!/usr/bin/env python3
"""
x1s_prototipo.py — prototipo de X1s (research/09 §3.5): ¿satisface la
fórmula entera la solución de Gauss del sistema XOR?

Para cada CNF: propaga las unidades de la raíz, extrae las XOR (k <= 6, como
X1), elimina, toma una solución particular por sustitución hacia atrás con
las variables libres a 1 y a 0, y cuenta las cláusulas que deja sin
satisfacer. Con 0, X1s resolvería la instancia sin buscar.

Uso: python3 scripts/x1s_prototipo.py <cnf> [<cnf> ...]
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from x1_gauss import leer, propagar, extraer_xor

def solucion(filas, d):
    col, inv = {}, []
    for vs, _ in filas:
        for v in vs:
            if v not in col:
                col[v] = len(col); inv.append(v)
    piv = {}
    for vs, b in filas:
        m = sum(1 << col[v] for v in vs)
        while m:
            p = m.bit_length() - 1
            if p not in piv:
                piv[p] = (m, b); break
            pm, pb = piv[p]; m, b = m ^ pm, b ^ pb
        if not m and b:
            return None
    x = {}
    for c in range(len(inv)):
        if c not in piv:
            x[c] = d
    for p in sorted(piv):
        m, b = piv[p]; s = b
        mm = m & ~(1 << p)
        while mm:
            q = mm.bit_length() - 1; s ^= x[q]; mm &= ~(1 << q)
        x[p] = s
    return {inv[c]: bool(v) for c, v in x.items()}

for path in sys.argv[1:]:
    t = time.time()
    n, cls = leer(path)
    val = propagar(cls)
    filas = []
    for vs, b in extraer_xor(cls, 6):
        libres = [v for v in vs if v not in val]
        for v in vs:
            if v in val: b ^= val[v]
        if libres: filas.append((libres, b))
    cubre = 0
    xs = {tuple(sorted(vs)) for vs, _ in extraer_xor(cls, 6)}
    for c in cls:
        if tuple(sorted({abs(x) for x in c})) in xs: cubre += 1
    res = []
    for d in (True, False):
        s = solucion(filas, d)
        if s is None: res.append('inconsistente'); break
        sig = lambda v: val[v] if v in val else s.get(v, d)
        malas = sum(1 for c in cls if not any(sig(abs(x)) == (x > 0) for x in c))
        res.append(f"libres={int(d)}: {malas} cláusulas sin satisfacer")
    print(f"{path.split('/')[-1][:10]} n={n} m={len(cls)} filas={len(filas)} cubiertas={cubre/len(cls):.0%} unidades={len(val)} | {'; '.join(res)} ({time.time()-t:.1f} s)", flush=True)
