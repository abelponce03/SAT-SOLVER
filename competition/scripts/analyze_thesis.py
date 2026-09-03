#!/usr/bin/env python3
"""
analyze_thesis.py - análisis Fase 0 sobre el CSV del estudio de tesis
(comparativo de solvers con métricas internas y externas).

Responde tres preguntas para decidir la contribución:
  1. ¿Dónde pierde CaDiCaL contra el mejor solver (gap por familia)?
  2. ¿Cuánta inestabilidad por seed hay (instancias flaky, varianza temporal)?
     -> territorio del reset/restart adaptativo.
  3. ¿Las inestables tienen una firma de restart distinta?

Requiere: pandas, numpy. El CSV debe tener al menos las columnas:
  solver, instance, family, seed, solved, result, time,
  conflicts_per_restart, rephase_per_restart, chronological_ratio.

Uso:
  python3 analyze_thesis.py <results.csv> [--baseline cadical] [--best kissat]
"""
import argparse
import sys

import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--baseline", default="cadical", help="solver a mejorar")
    ap.add_argument("--best", default="kissat", help="solver de referencia (techo)")
    ap.add_argument("--drop-results", default="CORRUPT_XZ",
                    help="valores de 'result' a descartar (coma-separados)")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    drop = [x for x in args.drop_results.split(",") if x]
    df = df[~df.result.isin(drop)].copy()

    print(f"filas válidas: {len(df)}  instancias: {df.instance.nunique()}  "
          f"solvers: {sorted(df.solver.unique())}")

    # 1) tasa de resolución y gap por familia
    print("\n=== solved rate por solver ===")
    print(df.groupby("solver").solved.mean().round(3).sort_values(ascending=False))

    both = df[df.solver.isin([args.baseline, args.best])]
    piv = both.groupby(["family", "solver"]).solved.mean().unstack()
    if args.best in piv and args.baseline in piv:
        piv["gap"] = (piv[args.best] - piv[args.baseline]).round(3)
        print(f"\n=== gap {args.best}-{args.baseline} por familia ===")
        print(piv.round(3).sort_values("gap", ascending=False))

    # 2) inestabilidad por seed en el baseline
    base = df[df.solver == args.baseline]
    per = base.groupby("instance").solved.agg(["sum", "count"])
    per = per[per["count"] >= 2]
    flaky = set(per[(per["sum"] > 0) & (per["sum"] < per["count"])].index)
    always = set(per[per["sum"] == per["count"]].index)
    never = set(per[per["sum"] == 0].index)
    print(f"\n=== estabilidad por seed de '{args.baseline}' (instancias con >=2 seeds: {len(per)}) ===")
    print(f"  siempre resuelve: {len(always)}   nunca: {len(never)}   "
          f"FLAKY: {len(flaky)}  <- territorio del reset")
    fam = df.drop_duplicates("instance").set_index("instance").family
    if flaky:
        print("  familias de las flaky:")
        print(fam.loc[list(flaky)].value_counts().to_string())

    # varianza temporal entre seeds (resueltas no triviales)
    sv = base[base.solved == True].copy()
    sv["time"] = pd.to_numeric(sv.time, errors="coerce")
    sp = sv.groupby("instance").time.agg(["min", "max", "mean"])
    sp = sp[sp["mean"] > 1]
    if len(sp):
        sp["ratio"] = sp["max"] / sp["min"].clip(lower=1e-9)
        print(f"\n  varianza temporal entre seeds (mean>1s, n={len(sp)}): "
              f"ratio mediana={sp.ratio.median():.2f} p90={sp.ratio.quantile(.9):.2f} "
              f"max={sp.ratio.max():.1f}")

    # 3) firma de restart flaky vs always
    sig = ["conflicts_per_restart", "rephase_per_restart", "chronological_ratio",
           "learned_per_conflict"]
    sig = [c for c in sig if c in base.columns]
    if sig and flaky and always:
        b = base[base.solved == True].copy()
        for c in sig:
            b[c] = pd.to_numeric(b[c], errors="coerce")
        b["grp"] = np.where(b.instance.isin(flaky), "flaky",
                            np.where(b.instance.isin(always), "always", "otro"))
        print("\n=== firma de restart: flaky vs always (medianas) ===")
        print(b[b.grp != "otro"].groupby("grp")[sig].median().round(3).T.to_string())


if __name__ == "__main__":
    main()
