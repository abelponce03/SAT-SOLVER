#!/usr/bin/env python3
"""
fuera_de_muestra_2025.py — ¿Se sostiene fuera de 2026 la conclusión de
research/10 («siempre» con simetrías queda 1.º)?

2025 no publica resultados por instancia: solo las curvas de cactus de las
diapositivas (data/competition/2025/main-{ALL,SAT,UNSAT}.tex, bajadas con
scripts/fetch_competition_data.sh 2025). De ellas salen, para cada solver,
las resueltas y el PAR-2 (N = 400, T = 5000 s). La cuenta coincide con las
cifras oficiales de las diapositivas (AE-Kissat2025-MAB: 2264,73 y 327).

Compara:
  1. el ranking de 2025, con la entrada «siempre» (Satsuma-Kissat-sc) frente
     a las Kissat sin simetrías;
  2. las familias en las que «siempre» ganó a «nunca» en 2026 (tiempos
     oficiales por instancia) con las familias del banco de 2025 (GBD).

Uso: python3 scripts/fuera_de_muestra_2025.py [--md results/estrategia/fuera_de_muestra_2025.md]
"""
import argparse
import os
import re
import sqlite3
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from analyze_competition import TIMEOUT, load, matrices  # noqa: E402

DATA = os.path.join(ROOT, "data", "competition")
N, T = 400, 5000.0
K26 = "biere_kissat-biere[main]"
S26 = "anders_satsuma-iter-kissat[main]"


def cactus(path):
    """{solver: [tiempos de las resueltas]} de un fichero de pgfplots."""
    t = open(path).read()
    nombres = dict(re.findall(r"\\newcommand\{\\solver(\w)\}\{([^}]*)\}", t))
    res = {}
    for col, coords in re.findall(r"\\addplot\[color=col(\w)[^\]]*\] coordinates \{([^}]*)\}", t):
        ts = [float(a) for a, _ in re.findall(r"\(([\d.]+), (\d+)\)", coords)]
        res[nombres.get(col, col)] = [x for x in ts if x <= T]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=os.path.join(ROOT, "results", "estrategia", "fuera_de_muestra_2025.md"))
    a = ap.parse_args()
    out = []
    p = out.append
    todos = cactus(os.path.join(DATA, "2025", "main-ALL.tex"))
    sat = cactus(os.path.join(DATA, "2025", "main-SAT.tex"))
    unsat = cactus(os.path.join(DATA, "2025", "main-UNSAT.tex"))
    filas = sorted(((sum(v) + 2 * T * (N - len(v))) / N, k, len(v)) for k, v in todos.items())
    p("## 2025 (Main Track, N = 400, T = 5000 s), desde las curvas de cactus oficiales\n")
    p("| Puesto | Solver | PAR-2 | Resueltas | SAT | UNSAT |")
    p("|---|---|---|---|---|---|")
    for i, (par2, k, n) in enumerate(filas, 1):
        marca = (" **(«siempre»: satsuma + Kissat)**" if "atsuma" in k else
                 " (Kissat de Biere, sin simetrías)" if k in ("Kissat-public", "Kissat-sc2025") else "")
        p(f"| {i} | {k}{marca} | {par2:.1f} | {n} | {len(sat.get(k, []))} | {len(unsat.get(k, []))} |")

    # Familias: 2026 (por instancia) frente al banco de 2025.
    d = load(2026)
    tm = matrices(d)
    fam = d.drop_duplicates("instanceid").set_index("instanceid")["family"].reindex(tm.columns)
    tK, tS = tm.loc[K26].values, tm.loc[S26].values
    solo_s = (tS <= TIMEOUT) & ~(tK <= TIMEOUT)
    solo_k = (tK <= TIMEOUT) & ~(tS <= TIMEOUT)
    g = pd.DataFrame({"familia": fam.values, "solo_siempre": solo_s, "solo_nunca": solo_k}).groupby("familia").sum()
    g["neto"] = g.solo_siempre - g.solo_nunca
    hashes = [m.group(1) for m in (re.search(r"/file/([0-9a-f]{32})", l)
                                   for l in open(os.path.join(DATA, "track_main_2025.uri"))) if m]
    con = sqlite3.connect(os.path.join(DATA, "gbd.db"))
    f25 = pd.read_sql("SELECT hash, family FROM features WHERE hash IN (%s)" % ",".join("?" * len(hashes)),
                      con, params=hashes).drop_duplicates("hash")
    c25 = f25.family.value_counts()
    g["en_2025"] = [int(c25.get(f, 0)) for f in g.index]
    g = g[g.neto != 0].sort_values("neto", ascending=False)
    p(f"\n## Familias en las que «siempre» y «nunca» se separan en 2026, y su presencia en 2025\n")
    p("| Familia | Solo «siempre» (2026) | Solo «nunca» (2026) | Neto | Instancias en 2025 |")
    p("|---|---|---|---|---|")
    for f, r in g.iterrows():
        p(f"| {f} | {r.solo_siempre} | {r.solo_nunca} | {r.neto:+d} | {r.en_2025} |")
    ganan = g[g.neto > 0]
    p(f"\nDe las {int(ganan.neto.sum())} instancias netas que «siempre» gana en 2026, "
      f"{int(ganan[ganan.en_2025 == 0].neto.sum())} son de familias que no estaban en 2025.")
    texto = "\n".join(out)
    os.makedirs(os.path.dirname(a.md), exist_ok=True)
    open(a.md, "w").write(texto + "\n")
    print(texto)


if __name__ == "__main__":
    main()
