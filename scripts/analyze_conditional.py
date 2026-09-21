#!/usr/bin/env python3
"""
analyze_conditional.py — ¿se puede predecir, con features baratos de la CNF,
cuándo conviene aplicar una técnica cara (ruptura de simetrías, hiper-resolución,
una configuración agresiva) y cuándo no?

La pregunta importa porque los datos oficiales muestran que el preprocesado
agresivo es **asimétrico**: el ganador de 2026 convierte 51 timeouts en
resoluciones pero rompe 13 instancias que la base sí resolvía. Un oráculo que
supiera cuándo aplicarlo valdría −322 s de PAR-2 adicionales. Este script mide
cuánto de ese oráculo alcanza un predictor real, entrenado solo con features
estáticos de la fórmula (los 59 de la base `base` de GBD: recuentos de cláusulas
por tamaño, fracción de Horn, grafos variable-cláusula, entropías…).

Metodología: validación cruzada estratificada de 5 pliegues. El predictor nunca
decide sobre instancias que ha visto, que es la única forma de que el número
signifique algo.

Uso:
  ./scripts/fetch_competition_data.sh 2026
  python3 scripts/analyze_conditional.py --treatment anders_satsuma-iter-kissat
  python3 scripts/analyze_conditional.py --treatment zheng_kissat-mab-hypre --folds 10
"""
import argparse
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "competition")
TIMEOUT = 5000.0
BASELINE = "biere_kissat-biere[main]"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", default="2026")
    ap.add_argument("--baseline", default=BASELINE)
    ap.add_argument("--treatment", required=True, help="solver que aplica la técnica cara")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--md", action="store_true")
    args = ap.parse_args()

    try:
        from sklearn.ensemble import GradientBoostingClassifier
        from sklearn.model_selection import StratifiedKFold
    except ImportError:
        sys.exit("Falta scikit-learn: pip install -r requirements.txt")

    scores = os.path.join(DATA, f"scores_{args.year}.csv")
    basedb = os.path.join(DATA, "gbd_base.db")
    if not os.path.exists(scores):
        sys.exit(f"Falta {scores}. Ejecuta ./scripts/fetch_competition_data.sh {args.year}")
    if not os.path.exists(basedb):
        sys.exit("Falta data/competition/gbd_base.db (lo baja fetch_competition_data.sh)")

    d = pd.read_csv(scores)
    d["par2"] = np.where(d.status.isin(["sat-verified", "unsat-verified"]),
                         d.runtime, 2 * TIMEOUT)

    def pick(name):
        if name in set(d.solverid):
            return name
        c = [s for s in d.solverid.unique() if name in s]
        if len(c) == 1:
            return c[0]
        sys.exit(f"'{name}' no identifica un solver único: {c}")

    base, treat = pick(args.baseline), pick(args.treatment)
    df = pd.DataFrame({
        "base": d[d.solverid == base].set_index("instanceid")["par2"],
        "treat": d[d.solverid == treat].set_index("instanceid")["par2"],
    }).dropna()

    con = sqlite3.connect(basedb)
    hs = list(df.index)
    f = pd.read_sql("SELECT * FROM features WHERE hash IN (%s)" % ",".join("?" * len(hs)),
                    con, params=hs).set_index("hash")
    f = f.drop(columns=[c for c in ("status",) if c in f.columns])
    f = f.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
    df = df.join(f, how="inner")

    cov = len(df) / len(hs) * 100
    print(f"Base: {base}\nTratamiento: {treat}")
    print(f"Instancias con features en GBD: {len(df)} de {len(hs)} ({cov:.0f}% de cobertura)")
    if cov < 95:
        print("  [AVISO] la cobertura es parcial y NO es aleatoria: GBD tiene features")
        print("  calculados sobre todo para instancias de ediciones anteriores, así que el")
        print("  subconjunto está sesgado hacia instancias 'conocidas'. Los PAR-2 de abajo")
        print("  se refieren a ese subconjunto, no al banco completo.")

    X = df[[c for c in df.columns if c not in ("base", "treat")]].fillna(-1).values
    y = (df.treat < df.base).astype(int).values
    print(f"\nEl tratamiento conviene en {y.sum()}/{len(y)} instancias ({y.mean()*100:.0f}%)")

    pred = np.zeros(len(y))
    skf = StratifiedKFold(args.folds, shuffle=True, random_state=args.seed)
    for tr, te in skf.split(X, y):
        m = GradientBoostingClassifier(random_state=args.seed, n_estimators=200, max_depth=3)
        m.fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    sel = np.where(pred == 1, df.treat.values, df.base.values)
    orac = np.minimum(df.base.values, df.treat.values)

    rows = [
        ("base siempre", (df.base.values < 2 * TIMEOUT).sum(), df.base.mean(), 0.0),
        ("tratamiento siempre", (df.treat.values < 2 * TIMEOUT).sum(), df.treat.mean(),
         df.treat.mean() - df.base.mean()),
        (f"predictor ({args.folds}-fold CV)", (sel < 2 * TIMEOUT).sum(), sel.mean(),
         sel.mean() - df.base.mean()),
        ("oráculo (techo)", (orac < 2 * TIMEOUT).sum(), orac.mean(),
         orac.mean() - df.base.mean()),
    ]
    r = pd.DataFrame(rows, columns=["estrategia", "resueltas", "PAR-2", "Δ vs base"])
    print()
    print(r.to_markdown(index=False, floatfmt=".1f") if args.md
          else r.to_string(index=False, float_format=lambda x: f"{x:9.1f}"))

    gap = df.base.mean() - orac.mean()
    got = df.base.mean() - sel.mean()
    print(f"\nExactitud del predictor: {(pred == y).mean()*100:.1f} %")
    print(f"El predictor captura {got/gap*100:.0f} % del hueco del oráculo "
          f"({got:.1f} s de los {gap:.1f} s disponibles).")
    print("\nLectura: si el predictor bate a 'tratamiento siempre', condicionar la técnica")
    print("es mejor que aplicarla incondicionalmente, que es justo lo que hacen hoy las")
    print("entradas de la competición.")


if __name__ == "__main__":
    main()
