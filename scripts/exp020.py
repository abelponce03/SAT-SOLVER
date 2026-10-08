#!/usr/bin/env python3
"""
exp020.py — EXP-020, preregistrado: ¿subir el tope de tiempo de satsuma de
60 s a 300 s? (P5; research/10 §2.2 y §5, acción 4)

El tope solo cambia algo en las instancias en las que satsuma lo alcanza. En
las demás, satsuma termina antes y `labesat` hace exactamente lo mismo con
los dos topes. Por eso las candidatas son las instancias en las que satsuma
(mclique v2, el de `labesat`) agotó los 60 s en experimentos anteriores:

  - EXP-014 parte 1 (banco industrial, results/exp014/satsuma.csv,
    estado TOPE);
  - EXP-011 (banco simétrico de 2026, results/exp011/satsuma.csv, build
    mclique2, salida TOPE).

  seleccionar  escribe results/exp020/candidatas.txt y enlaces simbólicos en
               bench/exp020/<familia>/ (no versionados) para usar --bench.
  analizar     informe de la fase 1 (satsuma solo, tope 300 s) y de la fase 2
               (A/B de labesat con B3: tope 60 s frente a 300 s, T = 1200 s).

Uso: python3 scripts/exp020.py {seleccionar|analizar}
"""
import csv
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from checkpoint import filas_completas  # noqa: E402
from run_experiment import find_instances  # noqa: E402

D = os.path.join(ROOT, "results", "exp020")
BENCH = os.path.join(ROOT, "bench", "exp020")
T = 1200.0


def seleccionar():
    cand = {}
    for r in csv.DictReader(open(os.path.join(ROOT, "results", "exp014", "satsuma.csv"))):
        if r["status"] == "TOPE":
            cand[r["instance"]] = ("tesis-dev", r["family"])
    for r in csv.DictReader(open(os.path.join(ROOT, "results", "exp011", "satsuma.csv"))):
        if r["build"] == "mclique2" and r["exit"] == "TOPE":
            cand.setdefault(r["instance"], ("symm2026", r["family"]))
    rutas = {}
    for banco in ("tesis-dev", "symm2026"):
        for p in find_instances(os.path.join(ROOT, "bench", banco)):
            rutas.setdefault(os.path.basename(p), p)
    os.makedirs(D, exist_ok=True)
    with open(os.path.join(D, "candidatas.txt"), "w") as f:
        f.write("# EXP-020: satsuma (mclique v2) agotó los 60 s en EXP-014 o EXP-011\n")
        for n in sorted(cand):
            banco, fam = cand[n]
            if n not in rutas:
                sys.exit(f"falta en disco: {n}")
            dest = os.path.join(BENCH, fam, n)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if not os.path.lexists(dest):
                os.symlink(os.path.realpath(rutas[n]), dest)
            f.write(n + "\n")
            print(f"{n}  {banco}  {fam}")
    print(f"{len(cand)} candidatas")


def par2(t, ok):
    return t if ok else 2 * T


def analizar():
    print("## EXP-020 — tope de satsuma: 60 s frente a 300 s\n")
    s300 = filas_completas(os.path.join(D, "satsuma300.csv"))
    if s300:
        termina = [r for r in s300 if str(r.get("exit")) == "0"]
        print(f"**Fase 1** (satsuma solo, tope 300 s): {len(termina)} de {len(s300)} terminan.")
        print("\n| instancia | salida | segundos | cláusulas de entrada → salida |\n|---|---|---|---|")
        for r in s300:
            print(f"| {r['instance'][:16]} | {r['exit']} | {r['secs']} | {r['clauses_in']} → {r['clauses_out']} |")
    a = {r["instance"]: r for r in filas_completas(os.path.join(D, "A.csv"))}
    b = {r["instance"]: r for r in filas_completas(os.path.join(D, "B.csv"))}
    comunes = sorted(set(a) & set(b))
    if not comunes:
        print("\n**Fase 2**: pendiente.")
        return
    ok = lambda r: r["status"] in ("SAT", "UNSAT")
    pa = [par2(float(a[i]["wall_s"]), ok(a[i])) for i in comunes]
    pb = [par2(float(b[i]["wall_s"]), ok(b[i])) for i in comunes]
    ra, rb = sum(ok(a[i]) for i in comunes), sum(ok(b[i]) for i in comunes)
    print(f"\n**Fase 2** (labesat con B3, T = {T:.0f} s, n = {len(comunes)}):")
    print(f"- Resueltas: tope 60 s {ra}, tope 300 s {rb}.")
    print(f"- PAR-2 medio: tope 60 s {sum(pa) / len(pa):.1f}, tope 300 s {sum(pb) / len(pb):.1f} "
          f"(Δ = {(sum(pb) - sum(pa)) / len(pa):+.1f} s).")
    print("\n| instancia | estado 60 s | t (s) | estado 300 s | t (s) |\n|---|---|---|---|---|")
    for i in comunes:
        print(f"| {i[:16]} | {a[i]['status']} | {a[i]['wall_s']} | {b[i]['status']} | {b[i]['wall_s']} |")
    subir = rb >= ra and sum(pb) <= sum(pa)
    print(f"\n**Decisión (§4)**: {'subir el tope a 300 s' if subir else 'mantener 60 s'} "
          f"(resueltas {rb} frente a {ra}; ΔPAR-2 {(sum(pb) - sum(pa)) / len(pa):+.1f} s).")


if __name__ == "__main__":
    {"seleccionar": seleccionar, "analizar": analizar}[sys.argv[1]]()
