#!/usr/bin/env python3
"""
exp023.py — EXP-023, preregistrado: B4 (selector estructural, research/11)
fuera de muestra, en las instancias de la Main Track de 2025.

  analizar   lee results/exp023/{satsuma,A,B}.csv y escribe el informe:
             «nunca» (A), «siempre» (B) y B4, compuesto instancia a
             instancia con la regla R FIJADA en research/11 (commit 07d45e6):

               t(B4) = t(B)                                   si R
                     = t(A) + min(t_satsuma, 60)              si no
                       (no resuelta si A no resuelve o se pasa de T)

             H1: IC95 % bootstrap superior de ΔPAR-2(B4 − nunca) <= +5 s.
             H2: ΔPAR-2(B4 − siempre) < 0 y Wilcoxon p < 0,05.
             H3: descriptivo (dónde se cumple R; «siempre» frente a «nunca»).

Uso: python3 scripts/exp023.py analizar
"""
import os
import random
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from b4_exploratorio import regla  # noqa: E402  (R tal como quedó fijada)

D = os.environ.get("EXP023_DIR", os.path.join(ROOT, "results", "exp023"))  # otra ruta: solo pruebas
T = 300.0


def ic_bootstrap(d, semilla=1, n=10000):
    rnd = random.Random(semilla)
    bs = sorted(sum(rnd.choice(d) for _ in d) / len(d) for _ in range(n))
    return bs[int(0.025 * n)], bs[int(0.975 * n) - 1]


def wilcoxon_p(x, y):
    from scipy.stats import wilcoxon
    return wilcoxon(x, y).pvalue if any(a != b for a, b in zip(x, y)) else 1.0


def main():
    from checkpoint import filas_completas
    sat = pd.DataFrame(filas_completas(os.path.join(D, "satsuma.csv")))
    A = pd.DataFrame(filas_completas(os.path.join(D, "A.csv")))
    B = pd.DataFrame(filas_completas(os.path.join(D, "B.csv")))
    lista = pd.read_csv(os.path.join(ROOT, "bench", "sc2025.list.csv"))
    lista["instance"] = lista.hash + ".cnf.xz"
    for c in ("row_column", "johnson", "orbitopal_units", "sym_units", "wall_s"):
        sat[c] = pd.to_numeric(sat[c], errors="coerce")
    for t in (A, B):
        t["wall_s"] = pd.to_numeric(t.wall_s)
    m = (A.merge(B, on=["instance", "seed"], suffixes=("_a", "_b"))
         .merge(sat[["instance", "status", "row_column", "johnson", "orbitopal_units", "sym_units", "wall_s"]]
                .rename(columns={"status": "satsuma", "wall_s": "t_satsuma"}), on="instance", how="left")
         .merge(lista[["instance", "group", "resultado"]], on="instance", how="left"))
    ok = lambda s: s.isin(["SAT", "UNSAT"])
    pa = np.where(ok(m.status_a), m.wall_s_a, 2 * T)
    pb = np.where(ok(m.status_b), m.wall_s_b, 2 * T)
    r = regla(m.fillna({"row_column": 0, "johnson": 0, "orbitopal_units": 0, "sym_units": 0}))
    ta = m.wall_s_a + np.minimum(m.t_satsuma.fillna(60).values, 60.0)
    p4 = np.where(r, pb, np.where(ok(m.status_a) & (ta <= T), ta, 2 * T))
    n = len(m)
    print(f"## EXP-023 — B4 fuera de muestra (2025, n = {n}, T = {T:.0f} s)\n")
    print("| Política | Resueltas | SAT | UNSAT | PAR-2 medio |")
    print("|---|---|---|---|---|")
    for nombre, p, st in (("«nunca» (A)", pa, m.status_a), ("«siempre» (B)", pb, m.status_b),
                          ("**B4**", p4, None)):
        res = p < 2 * T
        if st is None:
            st = np.where(r, m.status_b, m.status_a)
        print(f"| {nombre} | {int(res.sum())} | {int(((st == 'SAT') & res).sum())} | "
              f"{int(((st == 'UNSAT') & res).sum())} | {p.mean():.1f} |")
    print(f"\nR se cumple en {int(r.sum())} de {n} instancias.")

    d1 = list(p4 - pa)
    lo1, hi1 = ic_bootstrap(d1)
    h1 = hi1 <= 5.0
    print(f"\n### H1: B4 frente a «nunca»\n\n- ΔPAR-2 = {np.mean(d1):+.2f} s, IC95 % [{lo1:+.2f}, {hi1:+.2f}]; "
          f"Wilcoxon p = {wilcoxon_p(p4, pa):.3g}. **{'Se cumple' if h1 else 'No se cumple'}** "
          f"(superior <= +5 s).")
    d2 = list(p4 - pb)
    lo2, hi2 = ic_bootstrap(d2)
    p2 = wilcoxon_p(p4, pb)
    h2 = np.mean(d2) < 0 and p2 < 0.05
    print(f"\n### H2: B4 frente a «siempre»\n\n- ΔPAR-2 = {np.mean(d2):+.2f} s, IC95 % [{lo2:+.2f}, {hi2:+.2f}]; "
          f"Wilcoxon p = {p2:.3g}. **{'Se cumple' if h2 else 'No se cumple'}**.")
    d3 = list(pb - pa)
    lo3, hi3 = ic_bootstrap(d3)
    print(f"\n### H3 (descriptivo)\n\n- «siempre» frente a «nunca»: ΔPAR-2 = {np.mean(d3):+.2f} s, "
          f"IC95 % [{lo3:+.2f}, {hi3:+.2f}]; Wilcoxon p = {wilcoxon_p(pb, pa):.3g}.")
    sb, sa = int((ok(m.status_b) & ~ok(m.status_a)).sum()), int((ok(m.status_a) & ~ok(m.status_b)).sum())
    print(f"- Solo «siempre» resuelve {sb}; solo «nunca», {sa}.")
    print(f"- Satsuma: " + ", ".join(f"{k} {v}" for k, v in m.satsuma.value_counts().items()) + ".")
    print("\n| Familia (R se cumple) | Instancias | ΔPAR-2 siempre − nunca (s) |\n|---|---|---|")
    g = pd.DataFrame({"familia": m.group, "r": r, "d": pb - pa})
    for f, x in g[g.r].groupby("familia"):
        print(f"| {f} | {len(x)} | {x.d.sum():+.1f} |")
    if h1 and h2:
        v = "B4 se implementa en labesat y en el binario integrado, y pasa a candidata a V1 (D-020)"
    elif h2:
        v = "B4 mejora a «siempre» pero no protege lo bastante frente a «nunca»: vuelve a D-020"
    else:
        v = "B4 no aporta fuera de muestra: se documenta, y D-020 sigue con V1 y V2"
    print(f"\n**Veredicto (§4)**: {v} (H1 {'sí' if h1 else 'no'}, H2 {'sí' if h2 else 'no'}).")


if __name__ == "__main__":
    if sys.argv[1:] != ["analizar"]:
        sys.exit(__doc__)
    main()
