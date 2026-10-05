#!/usr/bin/env python3
"""
exp024.py — EXP-024 (M2, research/12 §3): topes internos de satsuma.

  analizar     a partir de results/exp024/satsuma.csv (compare_satsuma_builds
               con las configuraciones 'base' y 'topes'): H1 (descriptiva),
               H2 (coste en tesis-dev) y H3 (ruptura intacta en symm2026 H)
  seleccionar  instancias de la parte 2: las dos terminan y la CNF difiere, o
               una pasa de TOPE a terminar; como mucho 60, en orden de
               md5(hash + "exp024")

symm2026 guarda sus instancias por estrato (H, N, X); tesis-dev, por
familia: el estrato distingue los dos bancos.
"""
import argparse
import csv
import hashlib
import os
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV = os.path.join(ROOT, "results", "exp024", "satsuma.csv")
ESTRATOS = {"H", "N", "X"}


def cargar():
    por = defaultdict(dict)
    for r in csv.DictReader(open(CSV)):
        por[r["instance"]][r["build"]] = r
    return {k: v for k, v in por.items() if {"base", "topes"} <= set(v)}


def ok(r):
    return r["exit"] == "0"


def secs(r):
    return float(r["secs"] or 0)


def analizar(_args):
    d = cargar()
    grupos = defaultdict(list)
    for inst, v in d.items():
        fam = v["base"]["family"]
        banco = "symm2026" if fam in ESTRATOS else "tesis-dev"
        grupos[(banco, fam)].append(v)
    print("| banco | familia | n | CNF idéntica | t base (suma; mediana) | t topes (suma; mediana) | TOPE→ok | ok→TOPE |")
    print("|---|---|---:|---:|---|---|---:|---:|")
    tot = defaultdict(float)
    h3_fallos = []
    for (banco, fam), vs in sorted(grupos.items()):
        igual = sum(1 for v in vs if ok(v["base"]) and ok(v["topes"])
                    and v["base"]["out_sha1"] == v["topes"]["out_sha1"])
        tb = sorted(secs(v["base"]) for v in vs)
        tt = sorted(secs(v["topes"]) for v in vs)
        a_ok = sum(1 for v in vs if v["base"]["exit"] == "TOPE" and ok(v["topes"]))
        a_tope = sum(1 for v in vs if ok(v["base"]) and v["topes"]["exit"] == "TOPE")
        tot[banco + "_base"] += sum(tb)
        tot[banco + "_topes"] += sum(tt)
        if banco == "symm2026" and fam == "H":
            h3_fallos = [v["base"]["instance"] for v in vs
                         if v["base"]["out_sha1"] != v["topes"]["out_sha1"]]
        print(f"| {banco} | {fam} | {len(vs)} | {igual} | {sum(tb):.1f}; {tb[len(tb) // 2]:.2f} | "
              f"{sum(tt):.1f}; {tt[len(tt) // 2]:.2f} | {a_ok} | {a_tope} |")
    r = tot["tesis-dev_topes"] / tot["tesis-dev_base"] if tot["tesis-dev_base"] else float("nan")
    print(f"\nH2 (tesis-dev): suma con topes / sin topes = {r:.3f} -> "
          f"{'se cumple' if r <= 0.8 else 'no se cumple'} (umbral 0,8)")
    print(f"H3 (symm2026 H, CNF idéntica en todas): "
          f"{'se cumple' if not h3_fallos else 'no se cumple: ' + ', '.join(h3_fallos[:10])}")


def seleccionar(_args):
    d = cargar()
    sel = []
    for inst, v in d.items():
        b, t = v["base"], v["topes"]
        difiere = ok(b) and ok(t) and b["out_sha1"] != t["out_sha1"]
        if difiere or (b["exit"] == "TOPE" and ok(t)):
            sel.append(inst)
    sel = sorted(sel, key=lambda i: hashlib.md5((i.split(".")[0] + "exp024").encode()).hexdigest())[:60]
    out = os.path.join(ROOT, "results", "exp024", "instancias.txt")
    with open(out, "w") as f:
        f.write("# EXP-024 parte 2: la CNF de satsuma cambia con los topes (exp024.py seleccionar)\n")
        for i in sorted(sel):
            f.write(i + "\n")
    print(f"{len(sel)} instancias -> {os.path.relpath(out, ROOT)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("analizar").set_defaults(f=analizar)
    sub.add_parser("seleccionar").set_defaults(f=seleccionar)
    args = ap.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
