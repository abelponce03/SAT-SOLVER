#!/usr/bin/env python3
"""
exp013_calibracion.py — selección y análisis PREREGISTRADOS de EXP-013.

EXP-013 mide dos cosas antes de comparar LabeSAT con el Kissat de la tesis:

  1. ¿Es la misma búsqueda? Con la misma semilla, ¿coinciden los conflictos de
     Kissat 4.0.4 (esta máquina) con los de la tesis (otra 4.0.x)?
  2. ¿Cuánto más rápida o lenta es esta máquina? Factor de velocidad por
     conflicto, por grupo de máquinas de la tesis (pc1 / pc2).

Subórdenes:

  seleccionar   escribe bench/tesis-calib/ (enlaces) y results/exp013/instancias.txt
  analizar      lee results/exp013/local.csv y escribe el informe

Selección (fijada antes de correr nada, docs/experiments/EXP-013 §3):
  - solo partición dev de bench/tesis.list.csv;
  - estratos 'facil' y 'media' (las 3 semillas de la tesis resuelven);
  - la corrida de la tesis con semilla 42 resolvió en [10, 400] s;
  - hasta 6 instancias por familia, en orden de md5(hash + SAL).
"""
import argparse
import hashlib
import math
import os
import random
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SAL = "exp013-2026-09-24"
POR_FAMILIA = 6
REF = os.path.join(ROOT, "results", "tesis-kissat.reference.csv")
LISTA = os.path.join(ROOT, "bench", "tesis.list.csv")
OUT_DIR = os.path.join(ROOT, "results", "exp013")


def seleccionar(_):
    t = pd.read_csv(LISTA)
    ref = pd.read_csv(REF)
    r42 = ref[(ref.seed == 42) & ref.result.isin(["SAT", "UNSAT"])].set_index("hash")
    c = t[(t.particion == "dev") & t.dificultad.isin(["facil", "media"])].copy()
    c = c[c.hash.isin(r42.index)]
    c["t42"] = c.hash.map(r42.time)
    c = c[(c.t42 >= 10) & (c.t42 <= 400)]
    c["orden"] = [hashlib.md5((h + SAL).encode()).hexdigest() for h in c.hash]
    sel = c.sort_values("orden").groupby("family").head(POR_FAMILIA).sort_values(["family", "hash"])
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "instancias.txt"), "w") as f:
        f.write("# EXP-013: selección determinista (exp013_calibracion.py seleccionar)\n")
        for h in sel.hash:
            f.write(h + ".cnf.xz\n")
    base = os.path.join(ROOT, "bench", "tesis-calib")
    for _, r in sel.iterrows():
        src = os.path.join(ROOT, "bench", "tesis-dev", r.family, r.hash + ".cnf.xz")
        d = os.path.join(base, r.family)
        os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, r.hash + ".cnf.xz")
        if not os.path.lexists(dst):
            os.symlink(os.path.realpath(src), dst)
    print(sel.groupby("family").size().to_string())
    print(f"total {len(sel)}; suma de t42 de la tesis = {sel.t42.sum():.0f} s")


def gmean_ci(x, n_boot=10000, seed=1):
    x = [v for v in x if v > 0 and math.isfinite(v)]
    if not x:
        return float("nan"), float("nan"), float("nan"), 0
    lg = [math.log(v) for v in x]
    m = sum(lg) / len(lg)
    rnd = random.Random(seed)
    boots = sorted(sum(rnd.choice(lg) for _ in lg) / len(lg) for _ in range(n_boot))
    return math.exp(m), math.exp(boots[int(0.025 * n_boot)]), math.exp(boots[int(0.975 * n_boot)]), len(x)


def analizar(args):
    loc = pd.read_csv(args.local)
    loc["hash"] = loc.instance.str.split(".").str[0]
    ref = pd.read_csv(REF)
    r = ref[ref.seed == 42].set_index("hash")
    loc = loc[loc.seed == 42].copy()
    loc["t_tesis"] = loc.hash.map(r.time)
    loc["c_tesis"] = loc.hash.map(r.conflicts)
    loc["res_tesis"] = loc.hash.map(r.result)
    loc["maquina"] = loc.hash.map(r.maquina).str.split("_").str[0]
    ok = loc[loc.status.isin(["SAT", "UNSAT"])].copy()
    print(f"== EXP-013: {len(loc)} corridas locales, {len(ok)} resueltas")
    mismo = ok[ok.conflicts == ok.c_tesis]
    print(f"H1 (misma trayectoria): conflictos idénticos en {len(mismo)}/{len(ok)} "
          f"({100 * len(mismo) / max(1, len(ok)):.0f} %)")
    print(f"   respuesta distinta de la tesis: {(ok.status != ok.res_tesis).sum()}")
    ok["f_conflicto"] = (ok.wall_s / ok.conflicts) / (ok.t_tesis / ok.c_tesis)
    ok["f_tiempo"] = ok.wall_s / ok.t_tesis
    ok["r_conflictos"] = ok.conflicts / ok.c_tesis
    print("\nH2 (factor de velocidad por conflicto = local/tesis; < 1: esta máquina es más rápida)")
    filas = []
    for grupo, g in [("todas", ok)] + list(ok.groupby("maquina")):
        for col in ("f_conflicto", "f_tiempo", "r_conflictos"):
            m, lo, hi, n = gmean_ci(g[col].tolist())
            filas.append((grupo, col, n, m, lo, hi, (hi - lo) / 2 / m if m == m else float("nan")))
    out = pd.DataFrame(filas, columns=["grupo", "medida", "n", "media_geom", "ic95_inf",
                                       "ic95_sup", "semiancho_rel"])
    print(out.to_string(index=False, float_format="%.3f"))
    print("\nCriterio (§4): se calibra un grupo si el semiancho relativo del IC95 de "
          "f_conflicto es ≤ 0.15.")
    for _, x in out[out.medida == "f_conflicto"].iterrows():
        print(f"   {x.grupo:6} {'CALIBRABLE' if x.semiancho_rel <= 0.15 else 'NO calibrable'}"
              f" (semiancho {100 * x.semiancho_rel:.0f} %)")
    no = loc[~loc.status.isin(["SAT", "UNSAT"])]
    if len(no):
        print(f"\nNo resueltas en local (la tesis sí, con semilla 42): {len(no)}")
        print(no[["instance", "family", "status", "t_tesis"]].to_string(index=False))
    out.to_csv(os.path.join(OUT_DIR, "calibracion.csv"), index=False, float_format="%.4f")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("seleccionar")
    a = sub.add_parser("analizar")
    a.add_argument("--local", default=os.path.join(OUT_DIR, "local.csv"))
    args = ap.parse_args()
    {"seleccionar": seleccionar, "analizar": analizar}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
