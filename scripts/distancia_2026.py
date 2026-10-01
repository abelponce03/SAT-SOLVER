#!/usr/bin/env python3
"""
distancia_2026.py — ¿A qué distancia está LabeSAT de los ganadores de la Main
Track de 2026? (research/10)

Compone, instancia a instancia y con los tiempos OFICIALES de 2026 (mismas
máquinas, T = 5000 s), las configuraciones de LabeSAT a partir de piezas que
la competición sí midió:

  K    Kissat de Biere (`biere_kissat-biere`): nuestra base. EXP-008 no
       encontró diferencia con Kissat 4.0.4 (p = 0,60).
  S    satsuma + Kissat 4.0.4 (`anders_satsuma-iter-kissat`, el ganador): la
       misma tubería que `labesat --symmetry` (ADR-0004), con dos diferencias
       que se declaran (cliquer frente a mclique v2, EXP-011; sin topes frente
       a 60 s / 512 MiB).
  B3   ruptura con retraso X (EXP-009): t = t_K si t_K <= X; si no, X + t_S.
  X1   refutación por Gauss (research/09): las lights-out UNSAT son sistemas
       lineales inconsistentes por construcción (Ax = t sin solución). Su CNF
       son XOR de hasta 5 variables o cadenas de XOR de 3 con unitarias
       (`667341ee`, que X1 refuta en 0,02 s); las dos caben en la extracción
       (k <= 6). Se cuenta 1 s (lectura + X1).
  PGO  PGO + LTO (EXP-017): ×1,030 de velocidad. Por la Proposición 1 de
       research/08 equivale a dividir los tiempos por 1,030.

Todo es contrafactual: 2026 es el banco con el que se diseñaron B3 y X1, y en
2027 las familias serán otras. Sirve para medir distancias, no para predecir el
puesto.

Uso: python3 scripts/distancia_2026.py [--retraso 2] [--md results/estrategia/distancia_2026.md]
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from analyze_competition import TIMEOUT, load, matrices  # noqa: E402

K = "biere_kissat-biere[main]"
S = "anders_satsuma-iter-kissat[main]"
S_MAB = "anders_satsuma-iter-ae-kissat-mab[main]"
T_X1 = 1.0
PGO = 1.030


def par2(t):
    return float(np.where(t <= TIMEOUT, t, 2 * TIMEOUT).mean())


def resueltas(t):
    return int((t <= TIMEOUT).sum())


def puesto(valor, campo):
    """Puesto que ocuparía un PAR-2 en el campo oficial (1 = mejor)."""
    return int((campo < valor).sum()) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--retraso", type=float, default=2.0)
    ap.add_argument("--md", default=os.path.join(ROOT, "results", "estrategia", "distancia_2026.md"))
    a = ap.parse_args()
    d = load(2026)
    tm = matrices(d)                       # solver × instancia; inf = no resuelta
    fam = d.drop_duplicates("instanceid").set_index("instanceid")["family"].reindex(tm.columns)
    vres = d[d.vresult.isin(["sat", "unsat"])].drop_duplicates("instanceid").set_index("instanceid")["vresult"]
    vres = vres.reindex(tm.columns)
    # Solo la Main Track: fuera las entradas del track experimental ([exp]).
    campo = pd.Series({s: par2(tm.loc[s].values) for s in tm.index if "[exp" not in s}).sort_values()

    tK, tS = tm.loc[K].values, tm.loc[S].values
    X = a.retraso
    tB3 = np.where(tK <= X, tK, X + tS)
    x1 = ((fam == "lights-out") & (vres == "unsat")).values
    tB3X1 = np.where(x1, np.minimum(T_X1, tB3), tB3)
    tFin = tB3X1 / PGO
    tSX1 = np.where(x1, np.minimum(T_X1, tS), tS)

    filas = [
        ("LabeSAT por defecto hoy (Kissat 4.0.4, sin simetrías) ≈ K", tK),
        ("LabeSAT `--symmetry` siempre ≈ S (el ganador)", tS),
        (f"LabeSAT B3 (retraso {X:g} s)", tB3),
        (f"LabeSAT B3 + X1", tB3X1),
        (f"LabeSAT B3 + X1 + PGO/LTO", tFin),
        ("Referencia: S + X1 (si el ganador tuviera X1)", tSX1),
    ]
    out = []
    p = lambda *x: out.append(" ".join(str(y) for y in x))
    p("## Distancia de LabeSAT a la Main Track de 2026 (contrafactual con tiempos oficiales)\n")
    p(f"Ganador: `{S}`, PAR-2 {campo[S]:.1f}, {resueltas(tS)} resueltas.\n")
    p("| Configuración | Resueltas | PAR-2 | Δ frente al ganador | Puesto en 2026 |")
    p("|---|---|---|---|---|")
    for nombre, t in filas:
        v = par2(t)
        p(f"| {nombre} | {resueltas(t)} | {v:.1f} | {v - campo[S]:+.1f} | {puesto(v, campo.drop([S]) if 'ganador' in nombre else campo)} |")
    p(f"\nX1 actúa en {int(x1.sum())} instancias (lights-out UNSAT): "
      + ", ".join(f"{h[:8]} (K {tK[i]:.0f}, S {tS[i]:.0f})" for i, h in enumerate(tm.columns) if x1[i]))

    # ¿Dónde pierde y dónde gana B3 + X1 + PGO frente al ganador?
    gana = (tFin <= TIMEOUT) & ~(tS <= TIMEOUT)
    pierde = ~(tFin <= TIMEOUT) & (tS <= TIMEOUT)
    p(f"\nFrente al ganador: LabeSAT final resuelve {int(gana.sum())} que él no y pierde {int(pierde.sum())} que él sí.")
    for nombre, m in (("Gana", gana), ("Pierde", pierde)):
        if m.any():
            p(f"- {nombre}: " + ", ".join(f"{f} ({c})" for f, c in pd.Series(fam.values[m]).value_counts().items()))

    # Qué resuelven otros solvers del top-10 que LabeSAT final no.
    top = list(campo.index[:10])
    otros = tm.loc[top].values
    alguno = (otros <= TIMEOUT).any(axis=0)
    hueco = alguno & ~(tFin <= TIMEOUT)
    p(f"\nInstancias que resuelve algún solver del top-10 de 2026 y LabeSAT final no: {int(hueco.sum())}.")
    tab = []
    for i in np.where(hueco)[0]:
        quien = [s.split("[")[0] for s in top if tm.loc[s].values[i] <= TIMEOUT]
        tab.append((fam.values[i], vres.values[i], len(quien), ", ".join(q.split("_", 1)[1] for q in quien[:3])))
    if tab:
        h = pd.DataFrame(tab, columns=["familia", "resultado", "n", "quien"])
        g = h.groupby(["familia", "resultado"]).agg(n=("n", "size"), quien=("quien", "first")).sort_values("n", ascending=False)
        p("\n| Familia | Resultado | Instancias | Ejemplo de quién la resuelve |")
        p("|---|---|---|---|")
        for (f, r), row in g.head(20).iterrows():
            p(f"| {f} | {r} | {row.n} | {row.quien} |")

    # Cartera secuencial dentro de un binario: LabeSAT final durante f·T y,
    # si no resuelve, la variante MAB (satsuma + AE-Kissat-MAB) desde cero el
    # resto. Es lo que daría portar el bandido VSIDS/CHB (D-018).
    tSM0 = tm.loc[S_MAB].values
    p("\n**Cartera secuencial** (LabeSAT final durante f·T y, si no resuelve, la variante MAB del 3.º):\n")
    p("| f | Resueltas | PAR-2 | Δ frente al ganador |")
    p("|---|---|---|---|")
    for f in (0.5, 0.6, 0.7, 0.8, 0.9):
        c = f * TIMEOUT
        t = np.where(tFin <= c, tFin, np.where(tSM0 <= TIMEOUT - c, c + tSM0, np.inf))
        p(f"| {f:.1f} | {resueltas(t)} | {par2(t):.1f} | {par2(t) - campo[S]:+.1f} |")

    # Complementariedad con la variante MAB del ganador (lo que daría una V2).
    tSM = tm.loc[S_MAB].values
    vbs = np.minimum(tFin, tSM)
    p(f"\nOráculo (LabeSAT final, {S_MAB.split('[')[0]}): {resueltas(vbs)} resueltas, PAR-2 {par2(vbs):.1f}.")
    p(f"Oráculo de los 33 solvers de 2026: {resueltas(tm.min(axis=0).values)} resueltas, "
      f"PAR-2 {par2(tm.min(axis=0).values):.1f}.")
    texto = "\n".join(out)
    os.makedirs(os.path.dirname(a.md), exist_ok=True)
    open(a.md, "w").write(texto + "\n")
    print(texto)


if __name__ == "__main__":
    main()
