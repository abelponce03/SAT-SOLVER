#!/usr/bin/env python3
"""
exp015_seleccion.py — selección PREREGISTRADA de EXP-015 (VSA).

Instancias de tesis-dev donde el orden de la vivificación puede notarse en
T = 300 s: estratos 'facil', 'media' e 'inestable' según Kissat en la tesis.
60 instancias, cuota proporcional por familia (al menos 1), en orden de
md5(hash + SAL). Escribe results/exp015/instancias.txt.
"""
import hashlib
import os

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SAL, N = "exp015-2026-09-24", 60

t = pd.read_csv(os.path.join(ROOT, "bench", "tesis.list.csv"))
c = t[(t.particion == "dev") & t.dificultad.isin(["facil", "media", "inestable"])].copy()
c["orden"] = [hashlib.md5((h + SAL).encode()).hexdigest() for h in c.hash]
cuota = (c.family.value_counts() / len(c) * N).round().clip(lower=1).astype(int)
while cuota.sum() > N:
    cuota[cuota.idxmax()] -= 1
while cuota.sum() < N:
    cuota[cuota.idxmin()] += 1
sel = pd.concat(g.sort_values("orden").head(cuota[f]) for f, g in c.groupby("family"))
os.makedirs(os.path.join(ROOT, "results", "exp015"), exist_ok=True)
with open(os.path.join(ROOT, "results", "exp015", "instancias.txt"), "w") as f:
    f.write("# EXP-015: selección determinista (exp015_seleccion.py)\n")
    for h in sorted(sel.hash):
        f.write(h + ".cnf.xz\n")
print(pd.crosstab(sel.family, sel.dificultad, margins=True).to_string())
