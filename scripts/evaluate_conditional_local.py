#!/usr/bin/env python3
"""
evaluate_conditional_local.py — evalúa una regla CONDICIONAL simple ("aplica la
técnica solo si <feature> cruza un umbral") sobre corridas propias, comparándola
con aplicarla siempre, nunca, y con el oráculo.

Nació de EXP-002: desactivar las fases *lucky* de Kissat mejora el PAR-2 un 17 %
en instancias grandes y lo empeora un 93 % en las normales. Ninguna de las dos
decisiones fijas es buena; la pregunta es si un umbral trivial sobre el tamaño
de la fórmula recupera lo mejor de las dos.

Uso:
  python3 scripts/evaluate_conditional_local.py \\
      --on  results/exp001b/c0-default-s1.csv results/exp001c/c0-default-s1.csv \\
      --off results/exp002/nolucky_calib.csv  results/exp002/nolucky_calib2.csv \\
      --sizes /tmp/sizes.csv --feature variables
"""
import argparse
import csv

SOLVED = ("SAT", "UNSAT")


def load(paths):
    out = {}
    budget = None
    for p in paths:
        for r in csv.DictReader(open(p, newline="")):
            budget = budget or float(r["budget_value"])
            out[r["instance"]] = (float(r["cpu_s"]) if r["status"] in SOLVED
                                  else 2 * float(r["budget_value"]))
    return out, budget


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--on", nargs="+", required=True, help="CSV con la técnica ACTIVADA")
    ap.add_argument("--off", nargs="+", required=True, help="CSV con la técnica DESACTIVADA")
    ap.add_argument("--sizes", required=True, help="CSV instance,variables,clauses")
    ap.add_argument("--feature", default="variables", choices=("variables", "clauses"))
    args = ap.parse_args()

    on, T = load(args.on)
    off, _ = load(args.off)
    sizes = {r["instance"]: int(r[args.feature])
             for r in csv.DictReader(open(args.sizes, newline=""))}
    insts = sorted(set(on) & set(off) & set(sizes))
    print(f"{len(insts)} instancias · timeout {T:.0f}s · feature = {args.feature}\n")

    def par2(f):
        return sum(f(i) for i in insts) / len(insts)

    p_on = par2(lambda i: on[i])
    p_off = par2(lambda i: off[i])
    p_orac = par2(lambda i: min(on[i], off[i]))
    print(f"{'estrategia':<46} {'PAR-2':>9} {'Δ vs siempre':>13}")
    print("-" * 72)
    print(f"{'técnica SIEMPRE activada (por defecto)':<46} {p_on:>9.3f} {0.0:>13.3f}")
    print(f"{'técnica NUNCA activada':<46} {p_off:>9.3f} {p_off-p_on:>13.3f}")

    # barrido del umbral: se muestra la curva entera, no solo el mejor punto,
    # para que se vea si hay una meseta (regla robusta) o un pico (sobreajuste).
    cand = sorted({10**k for k in range(2, 9)} | {5 * 10**k for k in range(2, 8)})
    print()
    best = None
    for sense in (">", "<="):
        for thr in cand:
            if sense == ">":
                p = par2(lambda i: off[i] if sizes[i] > thr else on[i])
                n_off = sum(1 for i in insts if sizes[i] > thr)
            else:
                p = par2(lambda i: off[i] if sizes[i] <= thr else on[i])
                n_off = sum(1 for i in insts if sizes[i] <= thr)
            if n_off in (0, len(insts)):
                continue
            tag = ""
            if best is None or p < best[1]:
                best = (f"{args.feature} {sense} {thr:,}", p)
                tag = "  <- mejor hasta aquí"
            print(f"{'desactivar si ' + args.feature + ' ' + sense + ' ' + f'{thr:,}':<46} "
                  f"{p:>9.3f} {p-p_on:>13.3f}   ({n_off} instancias){tag}")
        print()
    print()
    print(f"{'ORÁCULO (techo, elige por instancia)':<46} {p_orac:>9.3f} {p_orac-p_on:>13.3f}")
    print()
    got = p_on - best[1]
    gap = p_on - p_orac
    print(f"Mejor regla: desactivar si {best[0]}  ->  PAR-2 {best[1]:.3f} "
          f"({best[1]-p_on:+.3f} s), captura {got/gap*100:.0f} % del hueco del oráculo.")
    print("\n[AVISO] el umbral se elige mirando LAS MISMAS instancias en que se evalúa:")
    print("        es una cota optimista, no una estimación honesta. Sirve para decidir")
    print("        si merece la pena implementarlo; el número que se publica sale de")
    print("        `bench/test`, con el umbral ya congelado (ADR-0003 §2).")


if __name__ == "__main__":
    main()
