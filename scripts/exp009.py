#!/usr/bin/env python3
"""
exp009.py — selección y análisis PREREGISTRADOS de EXP-009 (B3: ruptura con retraso).

  seleccionar   escribe results/exp009/principal.txt (instancias frescas de
                tesis-dev) y results/exp009/grupos.csv
  analizar      lee results/exp009/{P_A,P_B,S_A,S_B}.csv y escribe el informe

Selección del contraste PRINCIPAL (fijada antes de medir, EXP-009 §3):
  - S fresco: instancias de tesis-dev en las que satsuma añade ruptura
    (EXP-014 parte 1: status OK y cambia = 1) que NO entraron en el A/B de
    EXP-014 (ni en S ni en los controles): no se ha medido en ellas ninguna
    política;
  - no-S: 40 instancias de tesis-dev donde satsuma no añade ruptura (cualquier
    estado), fuera de los controles de EXP-014, en orden de md5(hash + SAL).
    Sirven para medir el coste del retraso donde la ruptura no aporta nada.

El contraste SECUNDARIO usa las 74 instancias del banco efectivo de EXP-007
(results/exp007/A.csv), que no hay que seleccionar.
"""
import hashlib
import os
import random
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(ROOT, "results", "exp009")
SAL, N_NO_S = "exp009-2026-09-30", 40


def seleccionar():
    s = pd.read_csv(os.path.join(ROOT, "results", "exp014", "satsuma.csv"))
    usadas = set(pd.read_csv(os.path.join(ROOT, "results", "exp014", "grupos.csv")).instance)
    s["orden"] = [hashlib.md5((i + SAL).encode()).hexdigest() for i in s.instance]
    s_fresco = s[(s.status == "OK") & (s.cambia == 1) & ~s.instance.isin(usadas)]
    no_s = s[~((s.status == "OK") & (s.cambia == 1)) & ~s.instance.isin(usadas)]
    no_s = no_s.sort_values("orden").head(N_NO_S)
    os.makedirs(D, exist_ok=True)
    g = pd.concat([s_fresco.assign(grupo="S"), no_s.assign(grupo="noS")])
    g[["instance", "family", "grupo"]].sort_values("instance").to_csv(
        os.path.join(D, "grupos.csv"), index=False)
    with open(os.path.join(D, "principal.txt"), "w") as f:
        f.write("# EXP-009, contraste principal: S fresco + 40 no-S (exp009.py seleccionar)\n")
        for i in sorted(g.instance):
            f.write(i + "\n")
    ef = sorted(set(pd.read_csv(os.path.join(ROOT, "results", "exp007", "A.csv")).instance))
    with open(os.path.join(D, "secundario.txt"), "w") as f:
        f.write("# EXP-009, contraste secundario: las 74 de EXP-007 (banco efectivo)\n")
        f.write("\n".join(ef) + "\n")
    print(f"S fresco: {len(s_fresco)}; no-S: {len(no_s)}; total {len(g)}; secundario: {len(ef)}")
    print(g.groupby(["grupo", "family"]).size().unstack(0).fillna(0).astype(int).to_string())


def par2(df, T):
    ok = df.status.isin(["SAT", "UNSAT"])
    return pd.Series([w if o else 2 * T for w, o in zip(df.wall_s, ok)], index=df.index)


def contraste(a, b, T, nombre):
    from scipy.stats import binomtest, wilcoxon
    m = a.merge(b, on=["instance", "seed"], suffixes=("_a", "_b"))
    pa = par2(m.rename(columns={"status_a": "status", "wall_s_a": "wall_s"}), T)
    pb = par2(m.rename(columns={"status_b": "status", "wall_s_b": "wall_s"}), T)
    m["p_a"], m["p_b"] = pa.values, pb.values
    d = (m.p_b - m.p_a).tolist()
    rnd = random.Random(1)
    bs = sorted(sum(rnd.choice(d) for _ in d) / len(d) for _ in range(10000))
    p = wilcoxon(m.p_b, m.p_a).pvalue if any(x != 0 for x in d) else 1.0
    ok_a, ok_b = m.status_a.isin(["SAT", "UNSAT"]), m.status_b.isin(["SAT", "UNSAT"])
    sb, sa = int((ok_b & ~ok_a).sum()), int((ok_a & ~ok_b).sum())
    mc = binomtest(sb, sa + sb).pvalue if sa + sb else 1.0
    print(f"\n## {nombre} (n = {len(m)}, T = {T:.0f} s)")
    print(f"- resueltas A {int(ok_a.sum())} / B {int(ok_b.sum())}; McNemar solo B {sb}, solo A {sa}, p = {mc:.3g}")
    print(f"- PAR-2 A {m.p_a.mean():.1f} / B {m.p_b.mean():.1f}; ΔPAR-2 = {sum(d) / len(d):+.2f} s, "
          f"IC95 % [{bs[250]:+.2f}, {bs[9750]:+.2f}]; Wilcoxon p = {p:.3g}")
    return m, sum(d) / len(d), bs[250], bs[9750], p


def analizar():
    g = pd.read_csv(os.path.join(D, "grupos.csv"))
    rd = lambda n: pd.read_csv(os.path.join(D, n))
    m, dm, lo, hi, p = contraste(rd("P_A.csv"), rd("P_B.csv"), 300.0,
                                 "Principal: retraso (B) frente a nunca (A), tesis-dev fresco")
    m = m.merge(g, on="instance")
    for grupo, x in m.groupby("grupo"):
        print(f"   {grupo}: n = {len(x)}, ΔPAR-2 = {(x.p_b - x.p_a).mean():+.2f} s")
    h1 = p < 0.05 and dm < 0 and hi < 0
    print(f"**H1** (retraso mejor que nunca): {'SÍ' if h1 else 'no'}")
    _, dm2, lo2, hi2, _ = contraste(rd("S_A.csv"), rd("S_B.csv"), 180.0,
                                    "Secundario: retraso (B) frente a siempre (A), 74 de EXP-007")
    h2 = hi2 <= 5.0
    print(f"**H2** (lo que cuesta la espera frente a siempre: IC superior ≤ +5 s): {'SÍ' if h2 else 'no'}")
    print("\n**Veredicto (§4)**: " + (
        "ACTIVAR la ruptura con retraso de 2 s por defecto (candidata a V1; validación final en H8)"
        if h1 and h2 else
        "no se activa por defecto" + ("" if h1 else " (H1 no)") + ("" if h2 else " (H2 no)")))


if __name__ == "__main__":
    {"seleccionar": seleccionar, "analizar": analizar}[sys.argv[1]]()
