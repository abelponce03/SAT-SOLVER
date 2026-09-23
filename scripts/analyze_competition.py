#!/usr/bin/env python3
"""
analyze_competition.py — explota los resultados oficiales instancia-por-instancia
de la SAT Competition para **estimar el techo de una idea antes de implementarla**.

La competición publica, para cada solver y cada una de las 400 instancias del
Main Track, el tiempo y el estado. Con esa matriz se pueden responder de forma
exacta preguntas que normalmente se responden con fe:

  ranking    ¿cuánto PAR-2 separa a cada entrada del Kissat de referencia?
             (es decir: ¿cuánto vale realmente cada técnica publicada?)
  families   ¿en qué familias gana cada solver? -> dónde vive el margen
  vbs        Virtual Best Solver: el techo de una selección perfecta por
             instancia. Si el VBS de un conjunto de configuraciones es mucho
             mejor que la mejor de ellas, hay complementariedad que explotar.
  portfolio  simula una CARTERA SECUENCIAL con reparto de tiempo (k configs,
             T/k segundos cada una, una tras otra) -- que es lo que **sí** se
             puede hacer dentro de un único binario en la Main Track secuencial,
             sin oráculo. Construcción voraz desde una base.
  headroom   resumen ejecutivo: qué techo tiene cada estrategia.

Uso:
  ./scripts/fetch_competition_data.sh          # una vez
  python3 scripts/analyze_competition.py ranking
  python3 scripts/analyze_competition.py families --solver anders_satsuma-iter-kissat
  python3 scripts/analyze_competition.py vbs --pattern kissat
  python3 scripts/analyze_competition.py portfolio --k 4
  python3 scripts/analyze_competition.py headroom --md
"""
import argparse
import os
import re
import sqlite3
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "competition")
TIMEOUT = 5000.0          # límite oficial de la Main Track, en segundos
SOLVED_STATUS = ("sat-verified", "unsat-verified")
# Kissat "de fábrica" de Armin Biere: la referencia contra la que se mide todo,
# porque es la base de nuestro fork.
BASELINE = "biere_kissat-biere[main]"


def load(year):
    scores = os.path.join(DATA, f"scores_{year}.csv")
    uri = os.path.join(DATA, f"track_main_{year}.uri")
    gbd = os.path.join(DATA, "gbd.db")
    if not os.path.exists(scores):
        sys.exit(f"Faltan datos. Ejecuta primero: ./scripts/fetch_competition_data.sh {year}")
    d = pd.read_csv(scores)
    d["solved"] = d.status.isin(SOLVED_STATUS)
    d["par2"] = np.where(d.solved, d.runtime, 2 * TIMEOUT)

    if os.path.exists(uri) and os.path.exists(gbd):
        hashes = [m.group(1) for m in
                  (re.search(r"/file/([0-9a-f]{32})", l) for l in open(uri)) if m]
        con = sqlite3.connect(gbd)
        q = ("SELECT hash, family, author, result FROM features WHERE hash IN (%s)"
             % ",".join("?" * len(hashes)))
        meta = pd.read_sql(q, con, params=hashes)
        d = d.merge(meta, left_on="instanceid", right_on="hash", how="left")
    else:
        d["family"] = "?"
    return d


def matrices(d):
    """(tiempos, resueltas) como matrices solver × instancia; inf donde no resuelve."""
    t = d.pivot_table(index="solverid", columns="instanceid", values="runtime", aggfunc="first")
    s = d.pivot_table(index="solverid", columns="instanceid", values="solved", aggfunc="first")
    return t.where(s.astype(bool), np.inf)


def par2(times, timeout=TIMEOUT):
    return float(np.where(np.isfinite(times), times, 2 * timeout).mean())


def pick_baseline(tm, name):
    if name in tm.index:
        return name
    cand = [s for s in tm.index if name in s]
    if len(cand) == 1:
        return cand[0]
    sys.exit(f"Baseline ambigua o inexistente: {name}\nDisponibles:\n  " + "\n  ".join(tm.index))


# ------------------------------------------------------------------- comandos
def cmd_ranking(d, args):
    tm = matrices(d)
    base = pick_baseline(tm, args.baseline)
    bp = par2(tm.loc[base].values)
    rows = []
    for s in tm.index:
        t = tm.loc[s]
        vbs = np.minimum(t.values, tm.loc[base].values)
        rows.append({
            "solver": s,
            "resueltas": int(np.isfinite(t).sum()),
            "PAR-2": par2(t.values),
            "vs_base": par2(t.values) - bp,
            "VBS_con_base": par2(vbs) - bp,
        })
    r = pd.DataFrame(rows).sort_values("PAR-2")
    print(f"Referencia: {base}  (PAR-2 = {bp:.1f}, resueltas = {int(np.isfinite(tm.loc[base]).sum())})")
    print("'vs_base' negativo = mejor que la referencia.")
    print("'VBS_con_base' = cuánto bajaría el PAR-2 si se pudiera elegir por instancia "
          "entre la referencia y ese solver (techo de complementariedad).\n")
    if args.md:
        print(r.to_markdown(index=False, floatfmt=".1f"))
    else:
        print(r.to_string(index=False, float_format=lambda x: f"{x:9.1f}"))


def cmd_families(d, args):
    tm = matrices(d)
    base = pick_baseline(tm, args.baseline)
    target = pick_baseline(tm, args.solver) if args.solver else None
    fam = d.drop_duplicates("instanceid").set_index("instanceid")["family"]
    out = []
    for f, insts in fam.groupby(fam):
        cols = [i for i in insts.index if i in tm.columns]
        b = tm.loc[base, cols].values
        row = {"familia": f, "n": len(cols),
               "base_resueltas": int(np.isfinite(b).sum()), "base_PAR2": par2(b)}
        if target is not None:
            t = tm.loc[target, cols].values
            row["otro_resueltas"] = int(np.isfinite(t).sum())
            row["otro_PAR2"] = par2(t)
            row["dPAR2"] = par2(t) - par2(b)
        out.append(row)
    r = pd.DataFrame(out).sort_values("dPAR2" if target is not None else "base_PAR2")
    print(f"Referencia: {base}" + (f"   vs   {target}" if target else "") + "\n")
    if args.md:
        print(r.to_markdown(index=False, floatfmt=".1f"))
    else:
        print(r.to_string(index=False, float_format=lambda x: f"{x:9.1f}"))


def cmd_vbs(d, args):
    tm = matrices(d)
    base = pick_baseline(tm, args.baseline)
    members = [s for s in tm.index if re.search(args.pattern, s)] if args.pattern else list(tm.index)
    if args.exclude:
        members = [s for s in members if not re.search(args.exclude, s)]
    sub = tm.loc[members]
    v = sub.min(axis=0).values
    best = min(members, key=lambda s: par2(tm.loc[s].values))
    print(f"Conjunto: {len(members)} solvers" + (f" que casan con /{args.pattern}/" if args.pattern else ""))
    for s in members:
        print(f"   {s}")
    print()
    print(f"  mejor individual ({best}): resueltas={int(np.isfinite(tm.loc[best]).sum())}  PAR-2={par2(tm.loc[best].values):.1f}")
    print(f"  referencia ({base}):       resueltas={int(np.isfinite(tm.loc[base]).sum())}  PAR-2={par2(tm.loc[base].values):.1f}")
    print(f"  VBS del conjunto:          resueltas={int(np.isfinite(v).sum())}  PAR-2={par2(v):.1f}")
    print()
    print(f"  => techo de una selección perfecta por instancia: "
          f"{par2(v) - par2(tm.loc[base].values):+.1f} s de PAR-2 sobre la referencia")
    print(f"     ({int(np.isfinite(v).sum()) - int(np.isfinite(tm.loc[base]).sum()):+d} instancias)")
    print("\n  Aviso: el VBS es un ORÁCULO (necesita saber de antemano qué configuración")
    print("  usar). No es alcanzable; acota lo que como mucho podría dar una selección")
    print("  por instancia. Para lo alcanzable sin oráculo, ver el comando 'portfolio'.")


def seq_portfolio(tm, members, timeout=TIMEOUT):
    """Cartera SECUENCIAL: k configuraciones, T/k segundos cada una, en orden.
    Es lo implementable dentro de un binario secuencial, sin oráculo ni paralelismo."""
    k = len(members)
    slot = timeout / k
    sub = tm.loc[members]
    res = []
    for inst in tm.columns:
        total = np.inf
        for i, m in enumerate(members):
            ti = sub.loc[m, inst]
            if np.isfinite(ti) and ti <= slot:
                total = i * slot + ti
                break
        res.append(total)
    res = np.array(res)
    return int(np.isfinite(res).sum()), par2(res, timeout)


def cmd_portfolio(d, args):
    tm = matrices(d)
    base = pick_baseline(tm, args.baseline)
    pool = [s for s in tm.index if s != base]
    if args.pattern:
        pool = [s for s in pool if re.search(args.pattern, s)]
    cur = [base]
    n, p = seq_portfolio(tm, cur)
    p0 = p
    print("Cartera secuencial con reparto de tiempo (k configs × T/k s, una tras otra).")
    print("Construcción voraz: en cada paso se añade la configuración que más baja el PAR-2.\n")
    print(f"{'k':>2} {'resueltas':>10} {'PAR-2':>10} {'Δ vs k=1':>10}  configuración añadida")
    print("-" * 78)
    print(f"{1:>2} {n:>10} {p:>10.1f} {0.0:>10.1f}  {base}")
    for _ in range(args.k - 1):
        best = None
        for c in pool:
            if c in cur:
                continue
            nn, pp = seq_portfolio(tm, cur + [c])
            if best is None or pp < best[2]:
                best = (c, nn, pp)
        if best is None:
            break
        cur.append(best[0])
        print(f"{len(cur):>2} {best[1]:>10} {best[2]:>10.1f} {best[2]-p0:>10.1f}  +{best[0]}")
    print("\n  Aviso: cada miembro es un solver completo de la competición, no una")
    print("  configuración nuestra. El resultado acota lo que da la DIVERSIDAD entre")
    print("  motores; para saber si basta con diversificar Kissat consigo mismo hay que")
    print("  medirlo en local (ver docs/experiments/).")


def cmd_headroom(d, args):
    tm = matrices(d)
    base = pick_baseline(tm, args.baseline)
    b = tm.loc[base].values
    bp, bs = par2(b), int(np.isfinite(b).sum())
    kiss = [s for s in tm.index if "kissat" in s and "satsuma" not in s]
    vbs_k = tm.loc[kiss].min(axis=0).values
    vbs_all = tm.min(axis=0).values
    best = min(tm.index, key=lambda s: par2(tm.loc[s].values))
    # cartera voraz de 3 miembros a partir de la base (misma construcción que
    # el comando 'portfolio', para que los dos informes no se contradigan)
    cur = [base]
    for _ in range(2):
        pick = None
        for c in tm.index:
            if c in cur:
                continue
            nn, pp = seq_portfolio(tm, cur + [c])
            if pick is None or pp < pick[2]:
                pick = (c, nn, pp)
        cur.append(pick[0])
    n3, p3 = seq_portfolio(tm, cur)
    rows = [
        ("Kissat de referencia (nuestra base)", bs, bp, 0.0),
        (f"Mejor entrada de la edición ({best})", int(np.isfinite(tm.loc[best]).sum()),
         par2(tm.loc[best].values), par2(tm.loc[best].values) - bp),
        (f"VBS de las {len(kiss)} variantes de Kissat (oráculo)",
         int(np.isfinite(vbs_k).sum()), par2(vbs_k), par2(vbs_k) - bp),
        (f"VBS de los {len(tm.index)} solvers (oráculo, techo absoluto)",
         int(np.isfinite(vbs_all).sum()), par2(vbs_all), par2(vbs_all) - bp),
        ("Cartera secuencial voraz k=3 (sin oráculo, implementable)", n3, p3, p3 - bp),
    ]
    r = pd.DataFrame(rows, columns=["estrategia", "resueltas", "PAR-2", "Δ PAR-2 vs base"])
    if args.md:
        print(r.to_markdown(index=False, floatfmt=".1f"))
    else:
        print(r.to_string(index=False, float_format=lambda x: f"{x:9.1f}"))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comando", choices=["ranking", "families", "vbs", "portfolio", "headroom"])
    ap.add_argument("--year", default="2026")
    ap.add_argument("--baseline", default=BASELINE)
    ap.add_argument("--solver", default=None, help="para 'families': con quién comparar")
    ap.add_argument("--pattern", default=None, help="regex para filtrar solvers")
    ap.add_argument("--exclude", default=None, help="regex de solvers a excluir")
    ap.add_argument("--k", type=int, default=4, help="tamaño máximo de la cartera")
    ap.add_argument("--md", action="store_true", help="salida en Markdown")
    args = ap.parse_args()
    d = load(args.year)
    {"ranking": cmd_ranking, "families": cmd_families, "vbs": cmd_vbs,
     "portfolio": cmd_portfolio, "headroom": cmd_headroom}[args.comando](d, args)


if __name__ == "__main__":
    main()
