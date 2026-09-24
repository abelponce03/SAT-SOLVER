#!/usr/bin/env python3
"""
exp014_simetrias.py — selección y análisis PREREGISTRADOS de EXP-014 (parte 2).

Parte 1 (scan_symmetry.py) dice en qué instancias de tesis-dev añade satsuma
predicados de ruptura (`cambia` = 1). La parte 2 es un A/B intercalado sobre
esas instancias: `solver/labesat --symmetry` (B) frente a `--no-symmetry` (A).

Subórdenes:
  seleccionar  lee results/exp014/satsuma.csv y escribe results/exp014/instancias.txt
  analizar     lee results/exp014/A.csv y B.csv; escribe el informe y el
               conjunto de datos para B3 (results/exp014/b3-industrial.csv)

Selección (EXP-014 §3.2, fijada antes de ver ningún tiempo de kissat):
  - S = instancias con status OK y cambia = 1;
  - si |S| > 80, se toman 80 estratificadas por familia (proporcional, al
    menos 1 por familia presente) en orden de md5(hash + SAL);
  - más 10 CONTROLES con status OK, cambia = 0 y la misma cantidad de
    cláusulas a la entrada y a la salida, para comprobar que ahí la búsqueda
    de kissat no cambia.
"""
import argparse
import hashlib
import math
import os
import random

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(ROOT, "results", "exp014")
SAL = "exp014-2026-09-24"
MAX_S, N_CONTROL = 80, 10
T = 300.0


def md5(h):
    return hashlib.md5((h + SAL).encode()).hexdigest()


def seleccionar(_):
    s = pd.read_csv(os.path.join(D, "satsuma.csv"))
    s["orden"] = s.instance.map(md5)
    S = s[(s.status == "OK") & (s.cambia == 1)]
    if len(S) > MAX_S:
        cuota = (S.family.value_counts() / len(S) * MAX_S).round().clip(lower=1).astype(int)
        while cuota.sum() > MAX_S:
            cuota[cuota.idxmax()] -= 1
        S = pd.concat(g.sort_values("orden").head(cuota[f]) for f, g in S.groupby("family"))
    C = s[(s.status == "OK") & (s.cambia == 0) & (s.in_clauses == s.out_clauses)]
    C = C.sort_values("orden").head(N_CONTROL)
    with open(os.path.join(D, "instancias.txt"), "w") as f:
        f.write("# EXP-014 parte 2: S (cambia=1) y controles (cambia=0)\n")
        for x in sorted(S.instance) + sorted(C.instance):
            f.write(x + "\n")
    pd.concat([S.assign(grupo="S"), C.assign(grupo="control")])[
        ["instance", "family", "grupo"]].to_csv(os.path.join(D, "grupos.csv"), index=False)
    print(f"S: {len(S)} (de {int(((s.status == 'OK') & (s.cambia == 1)).sum())}); controles: {len(C)}")
    print(S.family.value_counts().to_string())


def par2(row):
    return float(row.wall_s) if row.status in ("SAT", "UNSAT") else 2 * T


def gmean_ci(x, n_boot=10000, seed=1):
    lg = [math.log(v) for v in x if v > 0]
    if not lg:
        return float("nan"), float("nan"), float("nan")
    rnd = random.Random(seed)
    b = sorted(sum(rnd.choice(lg) for _ in lg) / len(lg) for _ in range(n_boot))
    return math.exp(sum(lg) / len(lg)), math.exp(b[250]), math.exp(b[9750])


def analizar(_):
    from scipy.stats import binomtest, wilcoxon
    a = pd.read_csv(os.path.join(D, "A.csv"))
    b = pd.read_csv(os.path.join(D, "B.csv"))
    g = pd.read_csv(os.path.join(D, "grupos.csv"))
    m = a.merge(b, on=["instance", "seed"], suffixes=("_a", "_b")).merge(g, on="instance")
    for k in "ab":
        m[f"ok_{k}"] = m[f"status_{k}"].isin(["SAT", "UNSAT"])
        m[f"par2_{k}"] = [float(w) if o else 2 * T for w, o in zip(m[f"wall_s_{k}"], m[f"ok_{k}"])]
    print(f"== EXP-014 parte 2: {len(m)} parejas (T = {T:.0f} s)")

    ctl = m[m.grupo == "control"]
    iguales = (ctl.propagations_a == ctl.propagations_b).sum()
    print(f"\nControles (cambia = 0): propagaciones idénticas en {iguales}/{len(ctl)}")

    S = m[m.grupo == "S"]
    print(f"\nEstrato S ({len(S)}): resueltas A {S.ok_a.sum()} / B {S.ok_b.sum()}; "
          f"PAR-2 A {S.par2_a.mean():.1f} / B {S.par2_b.mean():.1f}")
    d = S.par2_b - S.par2_a
    if (d != 0).any():
        print(f"   ΔPAR-2 = {d.mean():+.1f} s; Wilcoxon p = {wilcoxon(S.par2_b, S.par2_a).pvalue:.3g}")
    rnd = random.Random(1)
    bs = sorted(sum(rnd.choice(list(d)) for _ in d) / len(d) for _ in range(10000))
    print(f"   IC95 % del ΔPAR-2 [{bs[250]:+.1f}, {bs[9750]:+.1f}]")
    solo_b, solo_a = int((S.ok_b & ~S.ok_a).sum()), int((S.ok_a & ~S.ok_b).sum())
    p = binomtest(solo_b, solo_b + solo_a).pvalue if solo_a + solo_b else float("nan")
    print(f"H3 McNemar: solo B {solo_b}, solo A {solo_a}, p = {p:.3g}")
    amb = S[S.ok_a & S.ok_b]
    f, lo, hi = gmean_ci((amb.wall_s_b / amb.wall_s_a).tolist())
    print(f"H2 factor B/A en las {len(amb)} resueltas por ambas: {f:.3f} [IC95 {lo:.3f}, {hi:.3f}] "
          f"-> {'NO daña' if hi <= 1.10 else 'daña o no concluyente'} (criterio: sup ≤ 1.10)")
    print("\nPor familia:")
    print(S.groupby("family").agg(n=("instance", "count"), A=("ok_a", "sum"), B=("ok_b", "sum"),
                                  par2_A=("par2_a", "mean"), par2_B=("par2_b", "mean"))
          .round(1).to_string())

    sat = pd.read_csv(os.path.join(D, "satsuma.csv"))
    ds = S.merge(sat, on="instance", suffixes=("", "_scan"))
    ds["ayuda"] = (ds.par2_b < ds.par2_a * 0.9).astype(int)
    ds["dana"] = (ds.par2_b > ds.par2_a * 1.1).astype(int)
    cols = ["instance", "family", "status_a", "status_b", "par2_a", "par2_b", "ayuda", "dana",
            "in_vars", "in_clauses", "wall_s", "dejavu_gens", "avg_support", "row", "row_column",
            "johnson", "sym_units", "sym_binary", "sym_lex", "schreier_ms", "total_ms"]
    ds[[c for c in cols if c in ds]].to_csv(os.path.join(D, "b3-industrial.csv"), index=False)
    print(f"\nConjunto de datos para B3: {os.path.join(D, 'b3-industrial.csv')} ({len(ds)} filas)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("seleccionar")
    sub.add_parser("analizar")
    args = ap.parse_args()
    {"seleccionar": seleccionar, "analizar": analizar}[args.cmd](args)


if __name__ == "__main__":
    main()
