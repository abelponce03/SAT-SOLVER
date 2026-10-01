#!/usr/bin/env python3
"""
exp018.py — análisis PREREGISTRADO de EXP-018 (K1: precarga de cláusulas en
la propagación; clase E de ADR-0009).

  analizar   lee results/exp018/k1_A.csv y k1_B.csv y escribe el informe con
             el mismo código que EXP-017 (equivalencia vinculante y
             velocidad: media geométrica, IC95 % bootstrap, Wilcoxon).
             Añade, como descriptivo, la aceleración por grupo
             (industria / 2026).
"""
import math
import os
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import exp017  # noqa: E402

D = os.path.join(ROOT, "results", "exp018")


def analizar():
    exp017.D = D
    exp017.analizar("k1")
    a = pd.read_csv(os.path.join(D, "k1_A.csv"))
    b = pd.read_csv(os.path.join(D, "k1_B.csv"))
    m = a.merge(b, on=["instance", "seed"], suffixes=("_a", "_b"))
    m = m[m.cpu_s_a >= 1.0]
    t = pd.read_csv(os.path.join(ROOT, "bench", "tesis.list.csv"))
    industriales = {h + ".cnf.xz" for h in t.hash}
    m["grupo"] = ["industria" if i in industriales else "2026" for i in m.instance]
    print("\n**Descriptivo por grupo** (sin umbral):")
    for g, sub in m.groupby("grupo"):
        lg = [math.log(x) for x in sub.cpu_s_a / sub.cpu_s_b]
        print(f"- {g}: n = {len(sub)}, aceleración geométrica {math.exp(sum(lg) / len(lg)):.3f}")


if __name__ == "__main__":
    analizar()
