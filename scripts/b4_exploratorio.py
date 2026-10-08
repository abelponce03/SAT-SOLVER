#!/usr/bin/env python3
"""
b4_exploratorio.py — B4, selector estructural de la ruptura de simetrías
(research/11).  EXPLORATORIO: la regla se eligió mirando estos datos.

Política B4: satsuma se ejecuta siempre (como con --symmetry), pero su salida
solo se usa si lo que encontró tiene estructura de simetría «de verdad»:

    R  =  row_column > 0  o  johnson > 0  o  orbitopal_units > 0
          o  sym_units >= U          (U = 100; plano entre 50 y 200)

Si R no se cumple, se resuelve la CNF original, pero el tiempo de satsuma ya
se ha pagado.  El tiempo de B4 en una instancia se compone así:

    t_B4 = t_siempre                      si R
         = t_nunca + min(t_satsuma, 60)   si no

Datos:
  - banco simétrico (bench/symm2026, 84 instancias de 2026): rasgos de
    results/b4/satsuma-{,mclique-}symm2026.csv; tiempos OFICIALES de 2026 de
    «siempre» (anders_satsuma-iter-kissat) y «nunca» (biere_kissat-biere);
  - industria (tesis-dev): rasgos de results/exp014/satsuma.csv; A/B de
    EXP-014 parte 2 (nunca frente a siempre) y de EXP-009 principal (nunca
    frente a retraso de 2 s, que pasado ese umbral es «siempre» más 2 s).

Uso: python3 scripts/b4_exploratorio.py [--md results/estrategia/b4_exploratorio.md]
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from analyze_competition import TIMEOUT, load, matrices  # noqa: E402

K26 = "biere_kissat-biere[main]"
S26 = "anders_satsuma-iter-kissat[main]"
U = 100


def regla(x, u=U):
    return ((x.row_column > 0) | (x.johnson > 0) | (x.orbitopal_units > 0) | (x.sym_units >= u)).values


def coste_satsuma(x):
    return np.minimum(x.wall_s.fillna(60).values, 60.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=os.path.join(ROOT, "results", "estrategia", "b4_exploratorio.md"))
    a = ap.parse_args()
    out = []
    p = out.append
    R = lambda *x: os.path.join(ROOT, "results", *x)

    # Rasgos: ¿se distinguen el banco simétrico y la industria?
    sy = pd.read_csv(R("b4", "satsuma-symm2026.csv"))
    ind = pd.read_csv(R("exp014", "satsuma.csv"))
    p("## Rasgos de satsuma (sin cliques): fracción de instancias en las que aparecen\n")
    p("| Rasgo | Banco simétrico (84) | Industria, tesis-dev (450) |")
    p("|---|---|---|")
    for f, txt in (("row_column", "row_column > 0"), ("johnson", "johnson > 0"),
                   ("orbitopal_units", "orbitopal_units > 0"), ("sym_units", f"sym_units ≥ {U}"),
                   ("cambia", "cambia (algún predicado)")):
        c = (lambda x: x[f] >= U) if f == "sym_units" else (lambda x: x[f] > 0)
        p(f"| {txt} | {c(sy).mean():.2f} | {c(ind).mean():.2f} |")
    p(f"| **R** | {regla(sy).mean():.2f} | {regla(ind).mean():.2f} |")

    # Banco simétrico con los tiempos oficiales de 2026.
    d = load(2026)
    tm = matrices(d)
    par = lambda t: np.where(t <= TIMEOUT, t, 2 * TIMEOUT)
    sy["hash"] = sy.instance.str.split(".").str[0]
    sy = sy[sy.hash.isin(tm.columns)].copy()
    pK, pS = par(tm.loc[K26, sy.hash].values), par(tm.loc[S26, sy.hash].values)
    filas = [("Banco simétrico, tiempos oficiales de 2026 (T = 5000 s)", len(sy), pS.mean(), pK.mean(),
              np.where(regla(sy), pS, np.minimum(pK + coste_satsuma(sy), 2 * TIMEOUT)).mean(), int(regla(sy).sum()))]

    def industria(nombre, A, B, T):
        m = A.merge(B, on="instance", suffixes=("_a", "_b")).merge(ind, on="instance", how="left")
        ok = lambda st: st.isin(["SAT", "UNSAT"])
        pn = np.where(ok(m.status_a), m.wall_s_a, 2 * T)
        ps = np.where(ok(m.status_b), m.wall_s_b, 2 * T)
        ta = m.wall_s_a + coste_satsuma(m)
        pr = np.where(regla(m.fillna(0)), ps, np.where(ok(m.status_a) & (ta <= T), ta, 2 * T))
        filas.append((nombre, len(m), ps.mean(), pn.mean(), pr.mean(), int(regla(m.fillna(0)).sum())))

    industria("Industria, EXP-014 parte 2 (T = 300 s)", pd.read_csv(R("exp014", "A.csv")),
              pd.read_csv(R("exp014", "B.csv")), 300.0)
    industria("Industria, EXP-009 principal (T = 300 s; «siempre» = retraso de 2 s)",
              pd.read_csv(R("exp009", "P_A.csv")), pd.read_csv(R("exp009", "P_B.csv")), 300.0)
    p("\n## PAR-2 medio de cada política (con el tiempo de satsuma cargado a B4 cuando no aplica)\n")
    p("| Muestra | n | «siempre» | «nunca» | **B4** | R aplica en |")
    p("|---|---|---|---|---|---|")
    for nombre, n, s, k, b, ap_ in filas:
        p(f"| {nombre} | {n} | {s:.1f} | {k:.1f} | **{b:.1f}** | {ap_} |")

    # Robustez: umbral y build de satsuma.
    mc = pd.read_csv(R("b4", "satsuma-mclique-symm2026.csv"))
    mc["hash"] = mc.instance.str.split(".").str[0]
    mc = mc.set_index("hash").reindex(sy.hash)
    acuerdo = (regla(sy) == regla(mc.reset_index())).mean()
    p(f"\nAcuerdo de R entre satsuma sin cliques y mclique v2 (el de `labesat`): {acuerdo:.0%}.")
    p("\nUmbral U en el banco simétrico (PAR-2 de B4): " + ", ".join(
        f"U = {u}: {np.where(regla(sy, u), pS, np.minimum(pK + coste_satsuma(sy), 2 * TIMEOUT)).mean():.1f}"
        for u in (50, 100, 200, 400)))
    texto = "\n".join(out)
    os.makedirs(os.path.dirname(a.md), exist_ok=True)
    open(a.md, "w").write(texto + "\n")
    print(texto)


if __name__ == "__main__":
    main()
