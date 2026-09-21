#!/usr/bin/env python3
"""
build_dev_set.py — construye los bancos `bench/dev` y `bench/test` a partir del
conjunto oficial del Main Track, de forma estratificada y **disjunta**.

Por qué no vale coger instancias a ojo (ADR-0003 §2):
  - si dev y test comparten familias con las mismas instancias, cualquier ajuste
    de parámetros sobre dev se contagia a test y el número final miente;
  - si el banco solo tiene instancias que la base ya resuelve, no se puede medir
    la ganancia más valiosa, que es convertir un timeout en una resolución;
  - si no está estratificado por familia, tres familias grandes deciden el PAR-2.

Estrategia:
  1. Parte de los 400 hashes del Main Track y de su familia (metadatos de GBD).
  2. Clasifica cada instancia por dificultad usando el **tiempo del Kissat de
     referencia en la competición** (`scores.csv`): `facil` (<=60 s),
     `media` (<=600 s), `dificil` (resuelta pero lenta), `no-resuelta`.
  3. Reparte cada estrato por familia alternando dev/test, de modo que ninguna
     familia caiga entera en un lado.
  4. Escribe las listas de hashes (versionadas) y, con `--download`, baja las
     instancias (no versionadas: se reconstruyen por hash).

Uso:
  python3 scripts/build_dev_set.py --year 2026 --per-side 60
  python3 scripts/build_dev_set.py --year 2026 --per-side 60 --download
"""
import argparse
import csv
import os
import re
import sqlite3
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "competition")
BASELINE = "biere_kissat-biere[main]"
TIMEOUT = 5000.0


def difficulty(row):
    if not row["solved"]:
        return "no-resuelta"
    if row["runtime"] <= 60:
        return "facil"
    if row["runtime"] <= 600:
        return "media"
    return "dificil"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", default="2026")
    ap.add_argument("--per-side", type=int, default=60, help="instancias por banco")
    ap.add_argument("--baseline", default=BASELINE)
    ap.add_argument("--download", action="store_true", help="descargar las instancias elegidas")
    ap.add_argument("--seed", type=int, default=20260921)
    args = ap.parse_args()

    uri = os.path.join(DATA, f"track_main_{args.year}.uri")
    scores = os.path.join(DATA, f"scores_{args.year}.csv")
    gbd = os.path.join(DATA, "gbd.db")
    for p in (uri, scores, gbd):
        if not os.path.exists(p):
            sys.exit(f"Falta {p}. Ejecuta ./scripts/fetch_competition_data.sh {args.year}")

    hashes = [m.group(1) for m in (re.search(r"/file/([0-9a-f]{32})", l) for l in open(uri)) if m]
    con = sqlite3.connect(gbd)
    meta = pd.read_sql("SELECT hash, family, result FROM features WHERE hash IN (%s)"
                       % ",".join("?" * len(hashes)), con, params=hashes)

    d = pd.read_csv(scores)
    d = d[d.solverid == args.baseline].copy()
    if d.empty:
        sys.exit(f"No hay filas de {args.baseline} en {scores}")
    d["solved"] = d.status.isin(["sat-verified", "unsat-verified"])
    d = d.merge(meta, left_on="instanceid", right_on="hash", how="inner")
    d["dificultad"] = d.apply(difficulty, axis=1)

    print(f"Banco oficial {args.year}: {len(d)} instancias")
    print(d.dificultad.value_counts().to_string(), "\n")

    # Reparto alternado dentro de cada (familia, dificultad): ninguna familia
    # cae entera en un lado y los dos bancos quedan comparables en dificultad.
    rng = np.random.default_rng(args.seed)
    dev, test = [], []
    for (_fam, _dif), grp in d.groupby(["family", "dificultad"]):
        idx = rng.permutation(len(grp))
        for k, i in enumerate(idx):
            (dev if k % 2 == 0 else test).append(grp.iloc[i])

    def take(rows, n):
        """Toma n manteniendo la proporción de dificultades del banco completo."""
        df = pd.DataFrame(rows)
        if len(df) <= n:
            return df
        out = []
        props = d.dificultad.value_counts(normalize=True)
        for dif, p in props.items():
            sub = df[df.dificultad == dif]
            k = min(len(sub), max(1, int(round(p * n))))
            out.append(sub.sample(k, random_state=args.seed))
        return pd.concat(out).head(n)

    dev_df, test_df = take(dev, args.per_side), take(test, args.per_side)
    assert not (set(dev_df.hash) & set(test_df.hash)), "dev y test se solapan"

    for name, df in (("dev", dev_df), ("test", test_df)):
        path = os.path.join(ROOT, "bench", f"{name}.list.csv")
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            # 'group' es el subdirectorio que crea fetch_gbd.py; usamos la familia
            # para que la columna `family` del runner sea directamente útil.
            w.writerow(["hash", "group", "family", "dificultad", "resultado", "t_base_s"])
            for _, r in df.iterrows():
                w.writerow([r["hash"], r["family"], r["family"], r["dificultad"],
                            r["result"], f"{r['runtime']:.1f}"])
        print(f"== bench/{name}.list.csv: {len(df)} instancias")
        print(df.dificultad.value_counts().to_string())
        print(f"   familias distintas: {df.family.nunique()}\n")

    if args.download:
        for name in ("dev", "test"):
            print(f"== descargando bench/{name}")
            subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "fetch_gbd.py"),
                            "--list", os.path.join(ROOT, "bench", f"{name}.list.csv"),
                            "--out", os.path.join(ROOT, "bench", name)], check=False)
    else:
        print("Para bajarlas:  python3 scripts/build_dev_set.py --download")


if __name__ == "__main__":
    main()
