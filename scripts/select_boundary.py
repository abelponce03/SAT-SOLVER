#!/usr/bin/env python3
"""
select_boundary.py — selecciona las instancias "al borde" de un banco a partir
de una tanda de configuraciones, y arma con ellas un banco nuevo (enlaces
simbólicos, sin copiar gigabytes).

Motivación: medir complementariedad entre configuraciones solo tiene resolución
en las instancias donde *unas* resuelven y *otras* no. Las que resuelven todas
(triviales) y las que no resuelve ninguna (fuera de alcance para el presupuesto)
no aportan información y consumen todo el tiempo de cómputo. Concentrar el
presupuesto en la frontera es lo que hace viable el experimento con 4 núcleos.

Uso:
  python3 scripts/select_boundary.py results/exp001/*.csv \\
      --bench bench/downloaded/gbd --out bench/boundary [--include-hard 10]
"""
import argparse
import csv
import os
import random
from collections import defaultdict

SOLVED = ("SAT", "UNSAT")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="+")
    ap.add_argument("--bench", required=True, help="banco original (donde están los ficheros)")
    ap.add_argument("--out", required=True, help="directorio del banco nuevo")
    ap.add_argument("--include-hard", type=int, default=0,
                    help="añadir N instancias que ninguna configuración resolvió "
                         "(para no perder de vista el objetivo real)")
    ap.add_argument("--seed", type=int, default=20260921)
    args = ap.parse_args()

    solved_by = defaultdict(set)
    configs = set()
    for path in args.csv:
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                configs.add(r["label"])
                if r["status"] in SOLVED:
                    solved_by[r["instance"]].add(r["label"])
    todas = {r for p in args.csv for r in _instances(p)}
    n = len(configs)

    frontera = sorted(i for i in todas if 0 < len(solved_by[i]) < n)
    triviales = sorted(i for i in todas if len(solved_by[i]) == n)
    duras = sorted(i for i in todas if not solved_by[i])

    print(f"{len(configs)} configuraciones · {len(todas)} instancias")
    print(f"   triviales (las resuelven todas): {len(triviales)}")
    print(f"   FRONTERA (unas sí, otras no):    {len(frontera)}   <- las informativas")
    print(f"   duras (ninguna):                 {len(duras)}")

    elegidas = list(frontera)
    if args.include_hard and duras:
        rng = random.Random(args.seed)
        elegidas += rng.sample(duras, min(args.include_hard, len(duras)))

    if not elegidas:
        print("\nNo hay instancias de frontera: sube el presupuesto o cambia de banco.")
        return

    os.makedirs(args.out, exist_ok=True)
    index = {}
    for root, _d, files in os.walk(args.bench):
        for name in files:
            index[name] = os.path.join(root, name)

    hechos = 0
    for inst in elegidas:
        src = index.get(inst)
        if not src:
            print(f"   [aviso] no encuentro {inst} en {args.bench}")
            continue
        dst = os.path.join(args.out, inst)
        if not os.path.lexists(dst):
            os.symlink(os.path.abspath(src), dst)
        hechos += 1
    print(f"\n{hechos} enlaces en {args.out}  "
          f"({len(frontera)} de frontera + {hechos - len(frontera)} duras)")


def _instances(path):
    with open(path, newline="") as f:
        return [r["instance"] for r in csv.DictReader(f)]


if __name__ == "__main__":
    main()
