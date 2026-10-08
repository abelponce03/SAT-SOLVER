#!/usr/bin/env python3
"""
exp021.py — EXP-021, preregistrado: cobertura de X1 v2 (Gauss por componentes
conexas, research/09 §3.4) en las instancias en las que X1 v1 se saltó el
sistema XOR en EXP-019.

Reutiliza el arnés de EXP-019 (`exp019.py`) cambiando solo las rutas, para
que la medida sea la misma:

  muestra       results/exp021/muestra.csv: las instancias con resultado
                «saltada» en results/exp019/x1.csv, con su resultado conocido.
  correr        X1 v2 (solver/kissat/build-x1v2) en cada una; si refuta,
                prueba y los dos dsr-trim  → results/exp021/x1.csv
  equivalencia  contadores con --gauss=0 y --gauss=1 donde no refuta
                → results/exp021/equivalencia.csv
  analizar      H0 a H3 como en EXP-019, más la tabla v1 → v2.

Uso: python3 scripts/exp021.py {muestra|correr|equivalencia|analizar}
"""
import argparse
import csv
import os
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import exp019  # noqa: E402
from checkpoint import filas_completas  # noqa: E402

D = os.path.join(ROOT, "results", "exp021")
exp019.MUESTRA = os.path.join(D, "muestra.csv")
exp019.X1CSV = os.path.join(D, "x1.csv")
exp019.EQCSV = os.path.join(D, "equivalencia.csv")
exp019.X1DEV = os.path.join(D, "no-hay-ampliacion.csv")
V1 = os.path.join(ROOT, "results", "exp019", "x1.csv")


def muestra():
    v1 = {r["instance"]: r for r in filas_completas(V1, exp019.CAMPOS)}
    filas = [m for m in csv.DictReader(open(os.path.join(ROOT, "results", "exp019", "muestra.csv")))
             if v1.get(m["instance"], {}).get("outcome") == "saltada"]
    os.makedirs(D, exist_ok=True)
    with open(exp019.MUESTRA, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["instance", "bank", "path", "known"])
        w.writeheader()
        w.writerows(filas)
    print(f"muestra: {len(filas)} instancias ({dict(Counter(m['known'] for m in filas))})")


def analizar(a):
    exp019.analizar(a)
    v1 = {r["instance"]: r["outcome"] for r in filas_completas(V1, exp019.CAMPOS)}
    v2 = filas_completas(exp019.X1CSV, exp019.CAMPOS)
    print("\n### Cobertura: de X1 v1 (EXP-019) a X1 v2\n")
    print("| v1 → v2 | instancias |\n|---|---|")
    for (x, y), n in sorted(Counter((v1.get(r["instance"], "?"), r["outcome"]) for r in v2).items()):
        print(f"| {x} → {y} | {n} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("paso", choices=["muestra", "correr", "equivalencia", "analizar"])
    ap.add_argument("--kissat", default=os.path.join(ROOT, "solver", "kissat", "build-x1v2", "kissat"))
    ap.add_argument("--tools", default=os.path.join(ROOT, "tools"))
    a = ap.parse_args()
    a.muestra, a.out = exp019.MUESTRA, exp019.X1CSV
    {"muestra": lambda a: muestra(), "correr": exp019.correr, "equivalencia": exp019.equivalencia,
     "analizar": analizar}[a.paso](a)
