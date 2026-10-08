#!/usr/bin/env python3
"""
exp025.py — EXP-025 (M4, research/12 §4): análisis de x1b_potencial.py.

  analizar    H1 por banco y H2 (decisión preregistrada)
"""
import argparse
import csv
import os
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV = os.path.join(ROOT, "results", "exp025", "x1b.csv")


def analizar(_args):
    filas = list(csv.DictReader(open(CSV)))
    por = defaultdict(list)
    for r in filas:
        por[r["bank"]].append(r)
    print("| banco | n | con XOR | con saltadas | con unidad nueva | con equivalencia nueva | con ≥ 10 equivalencias nuevas |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for b, rs in sorted(por.items()):
        xor = [r for r in rs if int(r["filas"] or 0) > 0]
        print(f"| {b} | {len(rs)} | {len(xor)} | {sum(int(r['saltadas'] or 0) > 0 for r in xor)} | "
              f"{sum(int(r['unidades_nuevas'] or 0) > 0 for r in xor)} | "
              f"{sum(int(r['equivalencias_nuevas'] or 0) > 0 for r in xor)} | "
              f"{sum(int(r['equivalencias_nuevas'] or 0) >= 10 for r in xor)} |")
    reales = [r for r in filas if r["bank"] != "sintetica"]
    u = sum(int(r["unidades_nuevas"] or 0) > 0 for r in reales)
    e = sum(int(r["equivalencias_nuevas"] or 0) >= 10 for r in reales)
    xor = [r for r in reales if int(r["filas"] or 0) > 0]
    salt = sum(int(r["saltadas"] or 0) > 0 for r in xor)
    print(f"\nH2: {u} instancias reales con alguna unidad nueva, {e} con >= 10 equivalencias "
          f"nuevas -> {'se cumple' if u >= 10 or e >= 10 else 'no se cumple'} (umbral 10)")
    if xor and salt / len(xor) > 0.3:
        print(f"AVISO: {salt} de {len(xor)} instancias con XOR tienen componentes saltadas "
              "(> 30 %): repetir con topes mayores antes de decidir (§4)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("analizar").set_defaults(f=analizar)
    args = ap.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
