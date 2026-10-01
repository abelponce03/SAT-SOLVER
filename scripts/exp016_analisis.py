#!/usr/bin/env python3
"""
exp016_analisis.py — análisis de EXP-016 (perfil de costes), según las
preguntas Q1-Q4 de su preregistro. Es descriptivo: no hay umbral ni veredicto,
solo las fracciones p_c que research/08 §3.2 necesita para la ley de Amdahl.

Jerarquía de fases de Kissat 4.0.4 (profile.h y profile.c):

- total = parse + search + simplify + resto. search y simplify se excluyen
  (STOP_SEARCH_AND_START_SIMPLIFIER: probe, eliminate y walking paran la
  búsqueda).
- Dentro de search: focused/stable, y dentro de ellos analyze (que contiene
  deduce, minimize, shrink y bump), reduce, restart, rephase y reorder.
  Con --profile=4 aparecen además propagate y decide.
- Dentro de simplify: probe (vivify, sweep, substitute, backbone,
  transitive...), eliminate (subsume, definition, extract, congruence...)
  y walking.
- collect y defrag se ejecutan en los dos lados y no se pueden atribuir a
  uno solo; se informan aparte.

«búsqueda sin hijos» = search − analyze − reduce − restart − rephase −
reorder. Con --profile=3 es una cota superior de propagación + decisión +
retroceso (+ la parte de collect y defrag que caiga en la búsqueda).

Uso: python3 scripts/exp016_analisis.py > results/exp016/informe.md
"""
import math
import os
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(ROOT, "results", "exp016")

NIVEL1 = ["parse", "search", "simplify"]
EN_BUSQUEDA = ["analyze", "deduce", "minimize", "shrink", "bump", "reduce", "restart", "rephase", "reorder"]
HIJOS_DIRECTOS_BUSQUEDA = ["analyze", "reduce", "restart", "rephase", "reorder"]
EN_SIMPLIFICACION = ["probe", "vivify", "sweep", "substitute", "backbone", "transitive", "factor",
                     "eliminate", "subsume", "congruence", "walking"]
AMBOS = ["collect", "defrag"]


def tabla_ancha(csv):
    d = pd.read_csv(csv)
    ancha = d.pivot_table(index="instance", columns="fase", values="segundos", aggfunc="first").fillna(0.0)
    meta = d.drop_duplicates("instance").set_index("instance")[
        ["family", "status", "wall_s", "xz_s", "conflicts", "propagations"]]
    ancha = ancha.join(meta)
    if "search" in ancha:
        ancha["busqueda_sin_hijos"] = ancha["search"] - sum(
            ancha[c] for c in HIJOS_DIRECTOS_BUSQUEDA if c in ancha)
    if "total" in ancha:
        ancha["resto"] = ancha["total"] - sum(ancha[c] for c in NIVEL1 if c in ancha)
    return ancha


def grupo(ancha):
    t = pd.read_csv(os.path.join(ROOT, "bench", "tesis.list.csv"))
    industriales = {h + ".cnf.xz" for h in t.hash}
    calib = set()
    for b in ("calib", "calib2"):
        for raiz, _, fs in os.walk(os.path.join(ROOT, "bench", b)):
            calib |= {f for f in fs if f.endswith((".cnf", ".cnf.xz"))}
    return ["2026" if i in calib else ("industria" if i in industriales else "?") for i in ancha.index]


def fracciones(sub, fases):
    """Fracción ponderada por tiempo y mediana / p90 de la fracción por instancia."""
    filas = []
    tot = sub["total"].sum()
    for f in fases:
        if f not in sub:
            continue
        por_inst = sub[f] / sub["total"].where(sub["total"] > 0)
        filas.append((f, 100 * sub[f].sum() / tot, 100 * por_inst.median(), 100 * por_inst.quantile(0.9)))
    return filas


def imprime(filas, titulo):
    print(f"\n| {titulo} | ponderada (%) | mediana (%) | p90 (%) |\n|---|---|---|---|")
    for f, w, m, p in filas:
        print(f"| {f} | {w:.1f} | {m:.1f} | {p:.1f} |")


def q1_q2_q3(ancha):
    ancha = ancha.copy()
    ancha["grupo"] = grupo(ancha)
    print(f"## EXP-016 — perfil de costes (n = {len(ancha)} instancias)\n")
    print("Estados: " + ", ".join(f"{k} {v}" for k, v in ancha.status.value_counts().items()))
    print("\n### Q1. Fracción del tiempo de Kissat por fase\n")
    print("Ponderada = Σ segundos de la fase / Σ segundos totales. Las fases anidadas "
          "están incluidas en su madre (ver la cabecera del script).")
    for g in ("industria", "2026"):
        sub = ancha[ancha.grupo == g]
        if not len(sub):
            continue
        print(f"\n#### {g} (n = {len(sub)}, {sub.total.sum():.0f} s en total)")
        imprime(fracciones(sub, NIVEL1 + ["resto"]), "nivel 1")
        imprime(fracciones(sub, ["focused", "stable", "busqueda_sin_hijos"] + EN_BUSQUEDA), "dentro de search")
        imprime(fracciones(sub, EN_SIMPLIFICACION), "dentro de simplify")
        imprime(fracciones(sub, AMBOS), "en los dos lados")
    print("\n### Q2. Por duración de la corrida (los dos grupos juntos)\n")
    estratos = [("< 10 s", ancha.total < 10), ("10–100 s", (ancha.total >= 10) & (ancha.total < 100)),
                ("≥ 100 s", ancha.total >= 100)]
    cols = ["parse", "search", "simplify", "busqueda_sin_hijos", "analyze", "probe", "vivify", "eliminate"]
    print("| estrato | n | " + " | ".join(cols) + " |\n|---|---|" + "---|" * len(cols))
    for nombre, m in estratos:
        sub = ancha[m]
        if not len(sub):
            continue
        vals = [100 * sub[c].sum() / sub.total.sum() if c in sub else float("nan") for c in cols]
        print(f"| {nombre} | {len(sub)} | " + " | ".join(f"{v:.1f}" for v in vals) + " |")
    print("\n### Q3. Descompresión xz\n")
    r = ancha.xz_s / ancha.wall_s
    print(f"- Σ xz = {ancha.xz_s.sum():.1f} s frente a Σ kissat = {ancha.wall_s.sum():.0f} s "
          f"({100 * ancha.xz_s.sum() / ancha.wall_s.sum():.2f} %); mediana por instancia "
          f"{100 * r.median():.2f} %, máximo {100 * r.max():.1f} %.")


def q4():
    p3, p4 = os.path.join(D, "nivel3.csv"), os.path.join(D, "nivel4.csv")
    if not (os.path.exists(p3) and os.path.exists(p4)):
        print("\n### Q4\n\n(pendiente: faltan nivel3.csv o nivel4.csv)")
        return
    a, b = tabla_ancha(p3), tabla_ancha(p4)
    # Sufijo explícito en TODAS las columnas: con join(lsuffix, rsuffix) solo
    # se renombran las que existen en los dos niveles, y propagate y decide,
    # que solo aparecen en el nivel 4, se quedaban sin '_4' (y fuera del
    # informe).
    m = a.add_suffix("_3").join(b.add_suffix("_4"), how="inner")
    iguales = (m.conflicts_3 == m.conflicts_4) & (m.propagations_3 == m.propagations_4)
    print(f"\n### Q4. Nivel 4 con 200 000 conflictos (n = {len(m)})\n")
    print(f"- Mismo trabajo en las dos corridas (conflictos y propagaciones): {int(iguales.sum())} de {len(m)}.")
    v = m[iguales & (m.total_3 >= 1.0)]
    lg = [math.log(x) for x in v.total_4 / v.total_3]
    if lg:
        g = math.exp(sum(lg) / len(lg))
        print(f"- Sobrecoste de los temporizadores de nivel 4: media geométrica ×{g:.3f} "
              f"(mín ×{math.exp(min(lg)):.3f}, máx ×{math.exp(max(lg)):.3f}; n = {len(v)}, total_3 ≥ 1 s).")
    for f in ("propagate", "decide", "analyze", "busqueda_sin_hijos"):
        col = f + "_4"
        if col in m:
            fr = m[col] / m.total_4
            print(f"- {f}: ponderada {100 * m[col].sum() / m.total_4.sum():.1f} %, "
                  f"mediana {100 * fr.median():.1f} %, p90 {100 * fr.quantile(0.9):.1f} %.")


if __name__ == "__main__":
    perfil = os.path.join(D, "perfil.csv")
    if not os.path.exists(perfil):
        sys.exit("falta results/exp016/perfil.csv")
    q1_q2_q3(tabla_ancha(perfil))
    q4()
