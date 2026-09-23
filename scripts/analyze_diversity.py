#!/usr/bin/env python3
"""
analyze_diversity.py — mide la COMPLEMENTARIEDAD entre varias configuraciones
del mismo solver, a partir de los CSV de `run_experiment.py` (uno por config).

Responde a las tres preguntas de EXP-001:

  H1  ¿el VBS del conjunto mejora sobre la mejor configuración individual?
      (si no, no hay diversidad que explotar y la línea A se cae)
  H2  ¿la diversidad viene de las OPCIONES o solo de la SEED?
  H3  ¿una cartera secuencial con reparto T/k, sin oráculo, mejora sobre la
      mejor configuración individual? (es lo implementable)

Uso:
  python3 scripts/analyze_diversity.py results/exp001/*.csv [--md]
"""
import argparse
import csv
import itertools
import os
import sys
from collections import defaultdict

SOLVED = ("SAT", "UNSAT")
INF = float("inf")


def load(path):
    """Devuelve (label, {instancia: tiempo|inf}, timeout)."""
    times, label, budget = {}, None, None
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            label = label or r["label"]
            budget = budget or float(r["budget_value"])
            t = float(r["cpu_s"]) if r["status"] in SOLVED else INF
            # si hay varias seeds por instancia nos quedamos con la mediana-ish
            # (la mejor de las disponibles falsearía al alza)
            times.setdefault(r["instance"], []).append(t)
    agg = {}
    for inst, ts in times.items():
        ts.sort()
        agg[inst] = ts[len(ts) // 2]
    return label, agg, budget


def par2(times, T):
    v = [t if t != INF else 2 * T for t in times]
    return sum(v) / len(v) if v else 0.0


def solved(times):
    return sum(1 for t in times if t != INF)


def vbs(configs, insts):
    return [min(c[inst] for c in configs) for inst in insts]


def seq_portfolio(configs, insts, T):
    """k configuraciones, T/k segundos cada una, ejecutadas en orden."""
    k = len(configs)
    slot = T / k
    out = []
    for inst in insts:
        total = INF
        for i, c in enumerate(configs):
            t = c[inst]
            if t <= slot:
                total = i * slot + t
                break
        out.append(total)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="+")
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--seed-pattern", default="default",
                    help="subcadena que identifica a las configuraciones que solo cambian la seed")
    args = ap.parse_args()

    runs = [load(p) for p in args.csv]
    labels = [r[0] for r in runs]
    tables = [r[1] for r in runs]
    T = runs[0][2]
    insts = sorted(set.intersection(*[set(t) for t in tables]))
    if not insts:
        sys.exit("Las configuraciones no comparten instancias")
    print(f"{len(labels)} configuraciones · {len(insts)} instancias comunes · timeout {T:.0f}s\n")

    # --- individuales
    print("== Configuraciones por separado")
    print(f"{'config':<18} {'resueltas':>10} {'PAR-2':>10}")
    print("-" * 42)
    indiv = []
    for lab, tb in zip(labels, tables):
        ts = [tb[i] for i in insts]
        indiv.append((lab, solved(ts), par2(ts, T)))
    for lab, s, p in sorted(indiv, key=lambda x: x[2]):
        print(f"{lab:<18} {s:>10} {p:>10.3f}")
    best_lab, best_s, best_p = min(indiv, key=lambda x: x[2])

    # --- H1: VBS del conjunto
    v = vbs(tables, insts)
    print(f"\n== H1 · VBS del conjunto (oráculo)")
    print(f"   mejor individual ({best_lab}): resueltas={best_s}  PAR-2={best_p:.3f}")
    print(f"   VBS de las {len(tables)}:                resueltas={solved(v)}  PAR-2={par2(v, T):.3f}")
    gain = (best_p - par2(v, T)) / best_p * 100 if best_p else 0
    print(f"   => mejora del VBS sobre la mejor individual: {gain:.1f} %  "
          f"({solved(v) - best_s:+d} instancias)")
    print(f"   H1 (>=15%): {'SE CUMPLE' if gain >= 15 else 'NO SE CUMPLE'}")

    # --- H2: opciones vs seed
    seed_idx = [i for i, l in enumerate(labels) if args.seed_pattern in l]
    opt_idx = [i for i, l in enumerate(labels) if args.seed_pattern not in l]
    if len(seed_idx) >= 2:
        vs = vbs([tables[i] for i in seed_idx], insts)
        print(f"\n== H2 · ¿opciones o solo aleatorización?")
        print(f"   VBS de las {len(seed_idx)} que solo cambian la seed: "
              f"resueltas={solved(vs)}  PAR-2={par2(vs, T):.3f}")
        if opt_idx:
            vo = vbs([tables[i] for i in [seed_idx[0]] + opt_idx], insts)
            print(f"   VBS de una seed + las {len(opt_idx)} con opciones distintas: "
                  f"resueltas={solved(vo)}  PAR-2={par2(vo, T):.3f}")
            print(f"   => la diversidad por OPCIONES aporta "
                  f"{par2(vs, T) - par2(vo, T):+.3f} s sobre la diversidad por seed")

    # --- H3: cartera secuencial sin oráculo, construcción voraz
    print(f"\n== H3 · Cartera secuencial con reparto T/k (sin oráculo)")
    print(f"{'k':>2} {'resueltas':>10} {'PAR-2':>10} {'vs mejor indiv.':>16}  miembros")
    print("-" * 78)
    order = [i for i, _ in sorted(enumerate(indiv), key=lambda x: x[1][2])]
    cur = [order[0]]
    ts = [tables[cur[0]][i] for i in insts]
    print(f"{1:>2} {solved(ts):>10} {par2(ts, T):>10.3f} {0.0:>16.3f}  {labels[cur[0]]}")
    for _ in range(min(3, len(tables) - 1)):
        pick = None
        for c in range(len(tables)):
            if c in cur:
                continue
            res = seq_portfolio([tables[i] for i in cur + [c]], insts, T)
            p = par2(res, T)
            if pick is None or p < pick[1]:
                pick = (c, p, solved(res))
        cur.append(pick[0])
        print(f"{len(cur):>2} {pick[2]:>10} {pick[1]:>10.3f} {pick[1]-best_p:>16.3f}  "
              f"{', '.join(labels[i] for i in cur)}")
    print(f"\n   H3: la cartera {'MEJORA' if pick[1] < best_p else 'NO mejora'} "
          f"a la mejor configuración individual.")

    # --- matriz de complementariedad
    print("\n== Complementariedad por pares (instancias que A resuelve y B no / y viceversa)")
    print(f"{'A':<18} {'B':<18} {'solo A':>8} {'solo B':>8}")
    print("-" * 56)
    for i, j in itertools.combinations(range(len(tables)), 2):
        a = {x for x in insts if tables[i][x] != INF}
        b = {x for x in insts if tables[j][x] != INF}
        if a - b or b - a:
            print(f"{labels[i]:<18} {labels[j]:<18} {len(a-b):>8} {len(b-a):>8}")


if __name__ == "__main__":
    main()
