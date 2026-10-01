#!/usr/bin/env python3
"""
exp017.py — selección y análisis PREREGISTRADOS de EXP-017 (C1: compilación
guiada por perfil, LTO y -march; clase E de ADR-0009).

  seleccionar   escribe results/exp017/banco.txt: las 40 de bench/calib y las
                47 de la muestra de EXP-016 que están en el banco de la tesis
                (2 en los dos conjuntos: 85). Es disjunto del entrenamiento de
                la PGO (bench/smoke, bench/symm y bench/calib2).
  analizar CMP  CMP = pgo | march | control. Lee results/exp017/{CMP}_A.csv y
                {CMP}_B.csv y escribe el informe.

Equivalencia (vinculante): en cada pareja, mismo estado y mismos conflictos,
decisiones y propagaciones. Una sola diferencia refuta la clase E.
Velocidad: s_i = cpu_A / cpu_B por instancia (> 1: B más rápido); media
geométrica, IC95 % bootstrap (10 000) y Wilcoxon sobre log s_i. Se excluyen
de la velocidad las parejas con cpu_A < 1 s (ruido de arranque), y se informa
cuántas son.
"""
import math
import os
import random
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(ROOT, "results", "exp017")


def seleccionar():
    m16 = [l.strip() for l in open(os.path.join(ROOT, "results", "exp016", "muestra.txt"))
           if l.strip() and not l.startswith("#")]
    t = pd.read_csv(os.path.join(ROOT, "bench", "tesis.list.csv"))
    industriales = {h + ".cnf.xz" for h in t.hash}
    ind = [x for x in m16 if x in industriales]
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from run_experiment import find_instances
    calib = sorted(os.path.basename(i) for i in find_instances(os.path.join(ROOT, "bench", "calib")))
    entreno = {os.path.basename(l.split()[0]) for l in open(os.path.join(ROOT, "scripts", "pgo_entrenamiento.txt"))
               if l.strip() and not l.startswith("#")}
    banco = sorted(set(ind) | set(calib))
    assert not (set(banco) & entreno), "el banco de evaluación se solapa con el entrenamiento"
    os.makedirs(D, exist_ok=True)
    with open(os.path.join(D, "banco.txt"), "w") as f:
        f.write("# EXP-017: 40 de bench/calib + las de la muestra de EXP-016 que están en el banco de la tesis (disjunto del entrenamiento PGO)\n")
        f.write("\n".join(banco) + "\n")
    comunes = len(set(ind) & set(calib))
    print(f"banco {len(banco)}: {len(calib)} de calib + {len(ind)} de la muestra de EXP-016 "
          f"que están en el banco de la tesis ({comunes} en los dos)")


def analizar(cmp):
    from scipy.stats import wilcoxon
    a = pd.read_csv(os.path.join(D, f"{cmp}_A.csv"))
    b = pd.read_csv(os.path.join(D, f"{cmp}_B.csv"))
    m = a.merge(b, on=["instance", "seed"], suffixes=("_a", "_b"))
    claves = ["status", "conflicts", "decisions", "propagations"]
    distintas = m[[any(str(r[k + "_a"]) != str(r[k + "_b"]) for k in claves) for _, r in m.iterrows()]]
    print(f"## EXP-017 — {cmp} (n = {len(m)} parejas, presupuesto {m.budget_kind_a.iloc[0]} = "
          f"{m.budget_value_a.iloc[0]})\n")
    print(f"**Equivalencia**: {len(m) - len(distintas)} de {len(m)} parejas idénticas "
          f"(estado, conflictos, decisiones, propagaciones).")
    if len(distintas):
        print("**REFUTADA**: la compilación cambia la trayectoria en:")
        print(distintas[["instance", "status_a", "status_b", "conflicts_a", "conflicts_b"]].to_string(index=False))
    v = m[m.cpu_s_a >= 1.0].copy()
    v["s"] = v.cpu_s_a / v.cpu_s_b
    lg = [math.log(x) for x in v.s]
    rnd = random.Random(1)
    bs = sorted(sum(rnd.choice(lg) for _ in lg) / len(lg) for _ in range(10000))
    g = math.exp(sum(lg) / len(lg))
    p = wilcoxon(lg).pvalue
    print(f"\n**Velocidad** (n = {len(v)}; {len(m) - len(v)} parejas con cpu_A < 1 s excluidas):")
    print(f"- aceleración geométrica s = {g:.3f}, IC95 % [{math.exp(bs[250]):.3f}, {math.exp(bs[9750]):.3f}],"
          f" Wilcoxon p = {p:.3g}")
    print(f"- tiempo total de CPU: A {v.cpu_s_a.sum():.0f} s, B {v.cpu_s_b.sum():.0f} s "
          f"(cociente {v.cpu_s_a.sum() / v.cpu_s_b.sum():.3f})")
    ok = len(distintas) == 0 and math.exp(bs[250]) > 1.0
    print(f"\n**Veredicto (ADR-0009 §2)**: {'ADOPTAR' if ok else 'no se adopta'} "
          f"({'equivalente' if not len(distintas) else 'NO equivalente'}; "
          f"IC inferior {math.exp(bs[250]):.3f} {'>' if math.exp(bs[250]) > 1 else '≤'} 1)")
    return g


if __name__ == "__main__":
    if sys.argv[1] == "seleccionar":
        seleccionar()
    else:
        analizar(sys.argv[2])
