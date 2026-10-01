#!/usr/bin/env python3
"""
exp016_seleccion.py — muestra PREREGISTRADA de EXP-016 (perfil de costes).

- industria: 5 instancias por familia de tesis-dev (45), fuera del estrato
  'trivial', en orden de md5(hash + SAL);
- 2026: las 60 de bench/calib + bench/calib2 (Main Track 2026), enteras.
- submuestra de sobrecoste: las 20 primeras de 2026 en orden de md5.
Escribe results/exp016/{muestra,submuestra}.txt.
"""
import hashlib
import os
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from run_experiment import find_instances  # noqa: E402

SAL = "exp016-2026-10-01"
md5 = lambda h: hashlib.md5((h + SAL).encode()).hexdigest()  # noqa: E731

t = pd.read_csv(os.path.join(ROOT, "bench", "tesis.list.csv"))
t = t[(t.particion == "dev") & (t.dificultad != "trivial")].copy()
t["orden"] = t.hash.map(md5)
ind = t.sort_values("orden").groupby("family").head(5)
c26 = sorted(os.path.basename(i) for b in ("calib", "calib2")
             for i in find_instances(os.path.join(ROOT, "bench", b)))
muestra = sorted(h + ".cnf.xz" for h in ind.hash) + c26
sub = sorted(c26, key=lambda x: md5(x.split(".")[0]))[:20]
d = os.path.join(ROOT, "results", "exp016")
os.makedirs(d, exist_ok=True)
with open(os.path.join(d, "muestra.txt"), "w") as f:
    f.write("# EXP-016: 45 industriales (5 por familia, no triviales) + 60 de 2026\n")
    f.write("\n".join(muestra) + "\n")
with open(os.path.join(d, "submuestra.txt"), "w") as f:
    f.write("# EXP-016: submuestra de 20 de 2026 para el sobrecoste del nivel 4\n")
    f.write("\n".join(sorted(sub)) + "\n")
print(f"muestra {len(muestra)} ({len(ind)} industriales + {len(c26)} de 2026); submuestra {len(sub)}")
print(ind.groupby(["family", "dificultad"]).size().unstack(fill_value=0).to_string())
