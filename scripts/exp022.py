#!/usr/bin/env python3
"""
exp022.py — EXP-022, preregistrado: X1s, la solución de Gauss como asignación
afortunada (research/09 §3.5).

  correr        paso 1, reanudable (results/exp022/x1s.csv): en cada instancia
                de la muestra de EXP-019 (más su ampliación de bench/dev),
                kissat --gausslucky=1 sin preproceso ni búsqueda. Anota si X1s
                actúa, se rechaza o no aplica, con su tiempo; si actúa, el
                modelo lo verifica verify_model.py contra la CNF original.
  equivalencia  paso 2, reanudable (results/exp022/equivalencia.csv): los
                contadores de --statistics con --gausslucky=0 y =1 (2000
                conflictos, semilla 1) donde X1s se calculó y se rechazó.
  analizar      informe de H0 a H3 (docs/experiments/EXP-022 §4).

Uso: python3 scripts/exp022.py {correr|equivalencia|analizar}
     [--kissat solver/kissat/build-x1s/kissat]
"""
import argparse
import csv
import os
import re
import statistics
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import exp019  # noqa: E402
from checkpoint import EscritorDuradero, filas_completas  # noqa: E402

D = os.path.join(ROOT, "results", "exp022")
X1SCSV = os.path.join(D, "x1s.csv")
EQCSV = os.path.join(D, "equivalencia.csv")
MUESTRAS = [os.path.join(ROOT, "results", "exp019", "muestra.csv"),
            os.path.join(ROOT, "results", "exp019", "muestra-dev.csv")]
T_RUN = 600
T_EQ = 3600

RE_ACTUA = re.compile(r"gauss: solution of (\d+) XOR rows over (\d+) variables satisfies all "
                      r"(\d+) clauses \(([\d.]+) seconds\)")
RE_RECHAZA = re.compile(r"gauss: solution of (\d+) XOR rows over (\d+) variables falsifies a clause "
                        r"\(([\d.]+) seconds\)")
RE_LUCKY = re.compile(r"lucky Gauss solution")

CAMPOS = ["instance", "bank", "known", "exit_code", "wall_s", "x1", "x1s", "x1s_s", "rows", "vars",
          "status", "modelo"]
CAMPOS_EQ = exp019.CAMPOS_EQ


def x1_de(out):
    for nombre, rx in (("refutada", exp019.RE_REF), ("consistente", exp019.RE_CON),
                       ("saltada", exp019.RE_SALTA), ("saltada", exp019.RE_TOPE),
                       ("sin_xor", exp019.RE_NADA)):
        if rx.search(out):
            return nombre
    return "sin_mensaje"


def correr(a):
    exp019.sinteticas()  # no se versionan: se regeneran, idénticas, si faltan
    os.makedirs(D, exist_ok=True)
    hechas = filas_completas(X1SCSV, CAMPOS)
    listas = {r["instance"] for r in hechas}
    tmp = os.path.join(D, "tmp")
    os.makedirs(tmp, exist_ok=True)
    with EscritorDuradero(X1SCSV, CAMPOS, hechas) as ed:
        for muestra in MUESTRAS:
            for m in csv.DictReader(open(muestra)):
                if m["instance"] in listas:
                    continue
                path = os.path.join(ROOT, m["path"])
                code, out, wall = exp019.ejecutar(
                    [a.kissat, "--gauss=1", "--gausslucky=1", "--verbose=1", "--conflicts=0",
                     "--preprocess=false", path], T_RUN)
                fila = {k: "" for k in CAMPOS}
                fila.update(instance=m["instance"], bank=m["bank"], known=m["known"],
                            exit_code="" if code is None else code, wall_s=f"{wall:.2f}",
                            x1="timeout" if code is None else x1_de(out))
                st = re.search(r"^s (\S+)", out, re.M)
                fila["status"] = st[1] if st else ""
                if (g := RE_ACTUA.search(out)):
                    fila.update(x1s="actua" if RE_LUCKY.search(out) else "actua_sin_lucky",
                                rows=g[1], vars=g[2], x1s_s=g[4])
                    salida = os.path.join(tmp, "salida.txt")
                    with open(salida, "w") as f:
                        f.write(out)
                    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "verify_model.py"),
                                        "--model", salida, path], capture_output=True, text=True)
                    fila["modelo"] = "VERIFICADO" if r.returncode == 0 else "FALLA"
                    os.remove(salida)
                elif (g := RE_RECHAZA.search(out)):
                    fila.update(x1s="rechazada", rows=g[1], vars=g[2], x1s_s=g[3])
                else:
                    fila["x1s"] = "no_aplica"
                ed.escribir(fila)
                print(f"[{m['instance'][:12]}] X1 {fila['x1']} X1s {fila['x1s']} {fila['x1s_s']} s "
                      f"{fila['status']} {fila['modelo']}", flush=True)


def equivalencia(a):
    filas = [r for r in filas_completas(X1SCSV, CAMPOS) if r["x1s"] == "rechazada"]
    rutas = {}
    for muestra in MUESTRAS:
        for m in csv.DictReader(open(muestra)):
            rutas[m["instance"]] = m["path"]
    hechas = filas_completas(EQCSV, CAMPOS_EQ)
    listas = {r["instance"] for r in hechas}
    with EscritorDuradero(EQCSV, CAMPOS_EQ, hechas) as ed:
        for r in filas:
            n = r["instance"]
            if n in listas:
                continue
            base = ["--seed=1", "--conflicts=2000", "--statistics", os.path.join(ROOT, rutas[n])]
            _, o0, _ = exp019.ejecutar([a.kissat, "--gausslucky=0"] + base, T_EQ)
            _, o1, _ = exp019.ejecutar([a.kissat, "--gausslucky=1"] + base, T_EQ)
            c0, c1 = exp019.contadores(o0), exp019.contadores(o1)
            dif = [f"{x}≠{y}" for x, y in zip(c0, c1) if x != y]
            st = lambda c: next((v for k, v in c if k == "s"), "?")
            ed.escribir({"instance": n, "status_0": st(c0), "status_1": st(c1), "contadores": len(c0),
                         "identicos": int(c0 == c1 and len(c0) > 0), "diferencias": ";".join(dif[:5])})
            print(f"[{n[:12]}] {'IGUAL' if c0 == c1 else 'DISTINTO'} ({len(c0)})", flush=True)


def analizar(a):
    x = filas_completas(X1SCSV, CAMPOS)
    eq = filas_completas(EQCSV, CAMPOS_EQ)
    print(f"## EXP-022 — X1s (n = {len(x)} instancias)\n")
    cuenta = {}
    for r in x:
        cuenta[(r["x1"], r["x1s"])] = cuenta.get((r["x1"], r["x1s"]), 0) + 1
    print("| X1 | X1s | instancias |\n|---|---|---|")
    for (p, q), n in sorted(cuenta.items()):
        print(f"| {p} | {q} | {n} |")
    actua = [r for r in x if r["x1s"].startswith("actua")]
    malas = [r for r in actua if r["known"] == "unsat" or r["modelo"] != "VERIFICADO" or r["status"] != "SATISFIABLE"]
    print("\n### H0 (seguridad, vinculante)\n")
    print(f"- X1s actúa en {len(actua)}; con modelo no verificado, sin SAT o en una UNSAT conocida: "
          f"**{len(malas)}**.")
    sin_lucky = [r for r in actua if r["x1s"] != "actua"]
    if sin_lucky:
        print(f"- Actúa sin que `lucky` use la solución: {len(sin_lucky)} (revisar).")
    print("\n### H1 (búsqueda idéntica donde X1s se rechaza)\n")
    rech = [r for r in x if r["x1s"] == "rechazada"]
    print(f"- Parejas con los contadores idénticos: {sum(int(r['identicos']) for r in eq)} de {len(eq)} "
          f"(rechazadas: {len(rech)}).")
    print("\n### H2 (coste de X1s)\n")
    ts = sorted(float(r["x1s_s"]) for r in x if r["x1s_s"])
    if ts:
        p95 = ts[min(len(ts) - 1, int(0.95 * len(ts)))]
        print(f"- n = {len(ts)}: mediana {statistics.median(ts):.3f} s, p95 {p95:.3f} s, máximo {ts[-1]:.2f} s.")
    else:
        p95 = 0.0
    print("\n### H3 (dónde actúa)\n")
    print("| instancia | banco | conocido | filas | variables | X1s (s) | total (s) |\n|---|---|---|---|---|---|---|")
    for r in actua:
        print(f"| {r['instance'][:24]} | {r['bank']} | {r['known']} | {r['rows']} | {r['vars']} | "
              f"{r['x1s_s']} | {r['wall_s']} |")
    h0 = not malas
    h1 = len(eq) == len(rech) and all(int(r["identicos"]) for r in eq)
    h2 = bool(ts) and p95 <= 0.1 and ts[-1] <= 2.0
    veredicto = ("ACTIVAR por defecto" if h0 and h1 and h2 else
                 "acotar la comprobación y repetir H2" if h0 and h1 else "NO activar")
    print(f"\n**Veredicto (§4)**: {veredicto} (H0 {'sí' if h0 else 'no'}, H1 {'sí' if h1 else 'no'}, "
          f"H2 {'sí' if h2 else 'no'})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("paso", choices=["correr", "equivalencia", "analizar"])
    ap.add_argument("--kissat", default=os.path.join(ROOT, "solver", "kissat", "build-x1s", "kissat"))
    a = ap.parse_args()
    {"correr": correr, "equivalencia": equivalencia, "analizar": analizar}[a.paso](a)
