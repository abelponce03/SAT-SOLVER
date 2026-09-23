#!/usr/bin/env python3
"""
analyze_speedup.py — el análisis PREREGISTRADO de EXP-006, escrito antes de
ver los datos para que no quede margen para elegirlo después.

Contrasta si la rama B resuelve MÁS RÁPIDO que la A las instancias que ambas
resuelven.  Decisiones fijadas de antemano (EXP-006 §3):

  - unidad de análisis: la INSTANCIA, no la corrida.  Con varias semillas por
    instancia, las corridas no son independientes; tratarlas como tales
    inflaría n (pseudo-replicación).  Por instancia se promedia log(t_B/t_A)
    sobre las semillas en que ambas ramas resuelven;
  - se excluyen los pares con algún tiempo < 1 s (domina el ruido de medida);
  - contraste: Wilcoxon de rangos con signo sobre los log-ratios, dos colas;
  - efecto: factor geométrico exp(media), IC95 % por bootstrap de instancias;
  - comprobación contra la deriva de la máquina: el mismo análisis sobre las
    PROPAGACIONES, que son deterministas.  Si el tiempo dice "más rápido" y
    las propagaciones no, el efecto de tiempo no se da por bueno.

Uso:  python3 scripts/analyze_speedup.py A.csv B.csv [--min-time 1.0]
"""
import argparse
import csv
import math
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from par2 import wilcoxon  # noqa: E402  (misma implementación que el resto del harness)

SOLVED = ("SAT", "UNSAT")


def load(path):
    out = {}
    for r in csv.DictReader(open(path, newline="")):
        out[(r["instance"], r["seed"])] = r
    return out


def boot_ci(xs, reps=10000, seed=12345):
    rng = random.Random(seed)
    n = len(xs)
    ms = sorted(sum(xs[rng.randrange(n)] for _ in range(n)) / n for _ in range(reps))
    return ms[int(0.025 * reps)], ms[int(0.975 * reps)]


def analiza(nombre, por_inst):
    xs = [sum(v) / len(v) for v in por_inst.values()]
    if len(xs) < 6:
        print(f"   {nombre}: solo {len(xs)} instancias, insuficiente")
        return None
    m = sum(xs) / len(xs)
    lo, hi = boot_ci(xs)
    w, p, neff = wilcoxon(xs)
    mejor = sum(1 for x in xs if x < 0)
    peor = sum(1 for x in xs if x > 0)
    print(f"   {nombre}:")
    print(f"      instancias           {len(xs)}   (B mejor en {mejor}, peor en {peor})")
    print(f"      factor geométrico    {math.exp(m):.3f}x   "
          f"IC95% [{math.exp(lo):.3f}x, {math.exp(hi):.3f}x]")
    print(f"      Wilcoxon             W={w:.1f}  p={p:.4f}  (n efectivo={neff})")
    return {"n": len(xs), "factor": math.exp(m), "p": p, "hi": math.exp(hi)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--min-time", type=float, default=1.0)
    args = ap.parse_args()

    A, B = load(args.a), load(args.b)
    comunes = sorted(set(A) & set(B))
    t_inst, p_inst = defaultdict(list), defaultdict(list)
    descartes = {"alguna rama no resuelve": 0, f"tiempo < {args.min_time} s": 0}
    for k in comunes:
        a, b = A[k], B[k]
        if a["status"] not in SOLVED or b["status"] not in SOLVED:
            descartes["alguna rama no resuelve"] += 1
            continue
        ta, tb = float(a["cpu_s"]), float(b["cpu_s"])
        if ta < args.min_time or tb < args.min_time:
            descartes[f"tiempo < {args.min_time} s"] += 1
            continue
        t_inst[k[0]].append(math.log(tb / ta))
        pa, pb = int(a["propagations"] or 0), int(b["propagations"] or 0)
        if pa > 0 and pb > 0:
            p_inst[k[0]].append(math.log(pb / pa))

    print(f"{len(comunes)} parejas (instancia × semilla) en común")
    for motivo, n in descartes.items():
        print(f"   descartadas por {motivo}: {n}")
    print(f"   parejas válidas: {sum(len(v) for v in t_inst.values())} "
          f"en {len(t_inst)} instancias\n")

    print("== Métrica primaria: tiempo de CPU")
    rt = analiza("log(t_B / t_A)", t_inst)
    print("\n== Comprobación contra la deriva: propagaciones (deterministas)")
    rp = analiza("log(prop_B / prop_A)", p_inst)

    print("\n== VEREDICTO según el criterio preregistrado (EXP-006 §4)")
    if not rt:
        print("   no evaluable")
        return
    tiempo_ok = rt["p"] < 0.05 and rt["factor"] < 1
    prop_ok = bool(rp) and rp["factor"] < 1
    if tiempo_ok and prop_ok:
        print("   H1 CONFIRMADA: B es más rápido y las propagaciones lo respaldan.")
    elif tiempo_ok:
        print("   NO CONFIRMADA: el tiempo mejora pero las propagaciones no acompañan;")
        print("   la diferencia podría ser de la máquina, no del algoritmo.")
    else:
        print(f"   H1 NO CONFIRMADA (p = {rt['p']:.4f}, factor {rt['factor']:.3f}x).")


if __name__ == "__main__":
    main()
