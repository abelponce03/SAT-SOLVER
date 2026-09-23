#!/usr/bin/env python3
"""
analyze_trace.py - analiza la traza de eventos (restart/rephase) que produce
CaDiCaL instrumentado (CADICAL_TRACE=<fichero>), para caracterizar la dinámica
de la búsqueda y confirmar la señal que explotará el reset-bandit.

Cuantifica:
  - reuso de trail por restart (fracción del nivel reutilizada) y su evolución,
  - razón glue_fast/glue_slow en cada restart (el disparador de restart Glucose),
  - tasa de restart (conflictos entre restarts) por tramos,
  - histograma de tipos de rephase (O/I/F/#/B/W) y su cadencia.

Uso:
  python3 analyze_trace.py <trace.csv> [--label nombre]
"""
import argparse
import csv
import statistics as st


def load(path):
    R, P = [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            if row["event"] == "R":
                R.append(row)
            elif row["event"] == "P":
                P.append(row)
    return R, P


def num(x, cast=float):
    try:
        return cast(x)
    except (ValueError, TypeError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace")
    ap.add_argument("--label", default=None)
    args = ap.parse_args()
    label = args.label or args.trace

    R, P = load(args.trace)
    print(f"=== {label} ===")
    print(f"restarts: {len(R)}   rephases: {len(P)}")
    if not R:
        return

    # reuso por restart: delta(cum_reusedlevels) / level (nivel pre-backtrack)
    reuse_frac = []
    prev = 0
    for r in R:
        cum = num(r["cum_reusedlevels"], int) or 0
        lvl = num(r["level"], int) or 0
        # cum_reusedlevels es acumulativo y monótono salvo por reinicios internos
        # del contador (compact/restore): tratamos el salto negativo como 0.
        d = max(0, cum - prev)
        prev = cum
        if lvl > 0:
            reuse_frac.append(min(d / lvl, 1.0))

    # razón glue fast/slow
    ratios = []
    for r in R:
        f, s = num(r["glue_fast"]), num(r["glue_slow"])
        if f is not None and s and s > 0:
            ratios.append(f / s)

    # conflictos entre restarts (tasa)
    confl = [num(r["conflicts"], int) for r in R if num(r["conflicts"], int) is not None]
    gaps = [b - a for a, b in zip(confl, confl[1:]) if b >= a]

    def line(name, xs):
        if not xs:
            print(f"  {name:26s} (sin datos)")
            return
        print(f"  {name:26s} min={min(xs):.3f}  mediana={st.median(xs):.3f}  "
              f"max={max(xs):.3f}  media={sum(xs)/len(xs):.3f}")

    line("reuso trail / restart", reuse_frac)
    line("glue_fast/glue_slow", ratios)
    line("conflictos entre restarts", [float(g) for g in gaps])

    # fracción de restarts en modo estable
    stab = [1 for r in R if r["stable"] == "1"]
    print(f"  restarts en modo estable:  {len(stab)}/{len(R)} "
          f"({100*len(stab)/len(R):.1f}%)")

    # rephase: histograma de tipos
    if P:
        from collections import Counter
        types = Counter(p["rephase_type"] for p in P)
        names = {"O": "original", "I": "invertido", "F": "flip",
                 "#": "random", "B": "best", "W": "walk"}
        print("  rephase por tipo:")
        for t, n in types.most_common():
            print(f"     {names.get(t, t):10s} {n}")

    # lectura del thrashing: reuso alto sostenido = restarts que no diversifican
    if reuse_frac:
        hi = sum(1 for x in reuse_frac if x > 0.9) / len(reuse_frac)
        print(f"\n  >> {100*hi:.1f}% de los restarts reutilizan >90% del trail")
        if hi > 0.5:
            print("     -> THRASHING: la mayoría de restarts casi no diversifican;")
            print("        territorio donde un reset (randomización) tiene recorrido.")


if __name__ == "__main__":
    main()
