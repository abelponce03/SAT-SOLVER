#!/usr/bin/env python3
"""
select_symm_bench.py — banco de EXP-007: instancias del Main Track 2026
estratificadas SOLO con los datos oficiales de 2026.  No se mira ningún
resultado nuestro.

Se comparan dos soluciones de 2026:
  - W = anders_satsuma-iter-kissat[main]  (satsuma + kissat, el ganador)
  - K = biere_kissat-biere[main]          (kissat de referencia)

Estratos (L = 100 s, para que quepan en el timeout local de 180 s):
  H  «ayuda»:  W <= L,  K >= 3·W  y  K >= 10 s  (incluye timeouts de K)
  X  «daña»:   K <= L,  W >= 3·K  y  W >= 10 s
  N  «neutro»: W <= L y K <= L, fuera de H y X   -> muestra aleatoria fija

Exclusiones, decididas antes de ver ningún dato nuestro:
  - bench/test.list.csv: el banco de test está reservado (ADR-0003).
  - más de MAX_CLAUSES cláusulas: no caben en la máquina local (15 GB).
    La base local de GBD solo tiene el tamaño de 167 de las 400; si falta, la
    instancia se admite aquí y el mismo límite se aplica tras descargarla,
    leyendo la cabecera 'p cnf' (--download).

W y K no usan el mismo kissat.  Por eso los estratos solo sirven para ELEGIR
instancias; el efecto de la ruptura de simetrías, aislado, lo mide EXP-007
con el MISMO binario de kissat en las dos ramas.

Uso:  python3 scripts/select_symm_bench.py [--download]
"""
import argparse
import csv
import os
import sqlite3
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "competition")
W = "anders_satsuma-iter-kissat[main]"
K = "biere_kissat-biere[main]"
L = 100.0
RATIO = 3.0
MIN_SLOW = 10.0
N_NEUTRAL = 24
SEED = 2027
MAX_CLAUSES = 5_000_000
OUT = os.path.join(ROOT, "bench", "symm2026.list.csv")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--download", action="store_true")
    args = ap.parse_args()

    s = pd.read_csv(os.path.join(DATA, "scores_2026.csv"))
    p = s.pivot_table(index="instanceid", columns="solverid", values="score",
                      aggfunc="first")[[W, K]].dropna()
    p.columns = ["w", "k"]
    n_total = len(p)

    test = set(pd.read_csv(os.path.join(ROOT, "bench", "test.list.csv"))["hash"])
    con = sqlite3.connect(os.path.join(DATA, "gbd.db"))
    meta = pd.read_sql("SELECT hash, family, result FROM features", con).set_index("hash")
    base = sqlite3.connect(os.path.join(DATA, "gbd_base.db"))
    size = pd.read_sql("SELECT hash, clauses FROM features", base).set_index("hash")
    size["clauses"] = pd.to_numeric(size["clauses"], errors="coerce")
    p = p.join(meta, how="left").join(size, how="left")

    w, k = p["w"], p["k"]
    H = (w <= L) & (k >= RATIO * w) & (k >= MIN_SLOW)
    X = (k <= L) & (w >= RATIO * k) & (w >= MIN_SLOW)
    Nall = (w <= L) & (k <= L) & ~H & ~X
    p["estrato"] = np.select([H, X, Nall], ["H", "X", "N"], default="R")
    poblacion = p["estrato"].value_counts().to_dict()

    ok = ~p.index.isin(test) & ~(p["clauses"] > MAX_CLAUSES)
    sel = p[ok & p["estrato"].isin(["H", "X"])]
    neutros = p[ok & (p["estrato"] == "N")].sort_index()
    rng = np.random.default_rng(SEED)
    idx = rng.choice(len(neutros), size=min(N_NEUTRAL, len(neutros)), replace=False)
    sel = pd.concat([sel, neutros.iloc[sorted(idx)]]).sort_values(["estrato", "family"])

    with open(OUT, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["hash", "group", "family", "estrato", "resultado",
                     "t_satsuma_kissat_2026", "t_kissat_2026", "clauses"])
        for h, r in sel.iterrows():
            wr.writerow([h, r["estrato"], r["family"], r["estrato"], r["result"],
                         f"{r['w']:.2f}", f"{r['k']:.2f}",
                         "" if pd.isna(r["clauses"]) else int(r["clauses"])])

    print(f"población 2026 ({n_total} instancias) por estrato: {poblacion}")
    print(f"excluidas por test: {int((~ok & p.index.isin(test)).sum())}, "
          f"por tamaño conocido: {int((p['clauses'] > MAX_CLAUSES).sum())}")
    print(f"seleccionadas: {sel['estrato'].value_counts().to_dict()}  -> {OUT}")
    print(f"familias distintas: {sel['family'].nunique()}")
    if args.download:
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "fetch_gbd.py"),
                        "--list", OUT, "--out", os.path.join(ROOT, "bench", "symm2026")],
                       check=True)
        demasiado_grandes(os.path.join(ROOT, "bench", "symm2026"))


def demasiado_grandes(d):
    """Aparta (a <d>-grandes/) las descargadas con más de MAX_CLAUSES cláusulas."""
    import lzma
    import shutil
    fuera = d + "-grandes"
    for raiz, _, fs in os.walk(d):
        for f in fs:
            path = os.path.join(raiz, f)
            opener = lzma.open if f.endswith(".xz") else open
            with opener(path, "rt", errors="replace") as fh:
                for line in fh:
                    if line.startswith("p cnf"):
                        ncl = int(line.split()[3])
                        break
                else:
                    ncl = 0
            if ncl > MAX_CLAUSES:
                os.makedirs(fuera, exist_ok=True)
                shutil.move(path, os.path.join(fuera, f))
                print(f"   apartada por tamaño ({ncl} cláusulas): {f}")


if __name__ == "__main__":
    main()
