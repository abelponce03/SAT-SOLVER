#!/usr/bin/env python3
"""
exp019.py — EXP-019, preregistrado: X1, refutación de sistemas XOR por Gauss
con prueba DRAT (research/09).

  muestra        escribe results/exp019/muestra.csv: las instancias únicas (por
                 nombre) de bench/calib, bench/calib2, bench/symm2026 y
                 bench/tesis-dev con su resultado conocido, más el conjunto
                 sintético (results/exp019/sinteticas/, semillas fijas).
  correr         paso 1, reanudable (results/exp019/x1.csv): en cada instancia,
                 kissat --gauss=1 sin preproceso ni búsqueda, que ejecuta X1 y
                 nada más; en las que refuta, se repite con prueba y la
                 verifican los dos dsr-trim (SC2026 y actual).
  equivalencia   paso 2, reanudable (results/exp019/equivalencia.csv): los
                 contadores de --statistics con --gauss=0 y --gauss=1 (20 000
                 conflictos, semilla 1) en las instancias con alguna fila XOR
                 que X1 no refuta y en las 45 industriales de la muestra de
                 EXP-016.
  analizar       informe de H0 a H3 (docs/experiments/EXP-019 §4).
  muestra-dev    ampliación (EXP-019 §3b): results/exp019/muestra-dev.csv con
                 las instancias de paridad de bench/dev (descargadas de GBD) y
                 su resultado conocido según bench/dev.list.csv.

Uso: python3 scripts/exp019.py {muestra|muestra-dev|correr|equivalencia|analizar}
     [--kissat solver/kissat/build-x1/kissat] [--tools tools]
     [--muestra CSV --out CSV]   (correr: otra muestra y otra salida)
"""
import argparse
import csv
import os
import re
import resource
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from checkpoint import EscritorDuradero, filas_completas  # noqa: E402
from run_experiment import find_instances  # noqa: E402

D = os.path.join(ROOT, "results", "exp019")
MUESTRA = os.path.join(D, "muestra.csv")
X1CSV = os.path.join(D, "x1.csv")
MUESTRA_DEV = os.path.join(D, "muestra-dev.csv")
X1DEV = os.path.join(D, "x1-dev.csv")
EQCSV = os.path.join(D, "equivalencia.csv")
BANCOS = ["calib", "calib2", "symm2026", "tesis-dev"]
SINTETICAS = [  # (familia y parámetros, semilla, ¿satisfacible?)
    ("tseitin-malla 20 20", 7, False), ("tseitin-malla 20 20", 7, True),
    ("tseitin-regular 500 4", 7, False), ("tseitin-regular 500 4", 7, True),
    ("lights-out 14", 7, False), ("lights-out 14", 7, True),
    ("dos-ordenes 300", 7, False), ("dos-ordenes 300", 7, True),
]
MEM = 6 << 30            # tope de memoria por proceso (máquina de 15 GB)
T_X1 = 600               # tope de una corrida de X1 sola
T_CHECK = 3600           # tope de cada verificador

RE_REF = re.compile(r"gauss: refuted (\d+) XOR rows over (\d+) variables \(certificate of (\d+) rows, "
                    r"(\d+) extension variables in the proof, ([\d.]+) seconds\)")
RE_CON = re.compile(r"gauss: (\d+) XOR rows over (\d+) variables are consistent \(rank \d+, ([\d.]+) seconds\)")
RE_NADA = re.compile(r"gauss: no XOR rows to eliminate \(([\d.]+) seconds\)")
RE_SALTA = re.compile(r"gauss: skipping (\d+) rows over (\d+) variables \(.*, ([\d.]+) seconds\)")
RE_TOPE = re.compile(r"gauss: skipping, more than \d+ candidate clauses \(([\d.]+) seconds\)")

CAMPOS = ["instance", "bank", "known", "exit_code", "wall_s", "outcome", "x1_s", "rows", "vars",
          "cert_rows", "ext_vars", "proof_bytes", "dsr_sc2026", "dsr_sc2026_s", "dsr_actual",
          "dsr_actual_s"]
CAMPOS_EQ = ["instance", "status_0", "status_1", "contadores", "identicos", "diferencias"]


def limitar():
    resource.setrlimit(resource.RLIMIT_AS, (MEM, MEM))


def conocidos():
    """Resultado conocido por hash: listas de 2026 y Kissat de la tesis."""
    res = {}
    for b in ("calib", "calib2", "symm2026"):
        for r in csv.DictReader(open(os.path.join(ROOT, "bench", f"{b}.list.csv"))):
            if r.get("resultado") in ("sat", "unsat"):
                res[r["hash"]] = r["resultado"]
    for r in csv.DictReader(open(os.path.join(ROOT, "bench", "tesis.list.csv"))):
        k = (r.get("k_resultado") or "").lower()  # en la tesis: «SAT» / «UNSAT»
        if k in ("sat", "unsat"):
            res.setdefault(r["hash"], k)
    return res


def sinteticas():
    """Genera (si faltan) las instancias sintéticas; son deterministas por semilla.
    Devuelve sus filas de muestra."""
    os.makedirs(os.path.join(D, "sinteticas"), exist_ok=True)
    filas = []
    for spec, seed, sat in SINTETICAS:
        nombre = spec.replace(" ", "_") + ("_sat" if sat else "_unsat") + f"_s{seed}.cnf"
        path = os.path.join(D, "sinteticas", nombre)
        if not os.path.exists(path):
            with open(path + ".part", "w") as f:
                subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "gen_paridad.py"),
                                *spec.split(), "--seed", str(seed)] + (["--sat"] if sat else []),
                               stdout=f, check=True)
            os.replace(path + ".part", path)
        filas.append({"instance": nombre, "bank": "sintetica", "path": os.path.relpath(path, ROOT),
                      "known": "sat" if sat else "unsat"})
    return filas


def muestra():
    filas, vistas = sinteticas(), set()
    k = conocidos()
    for b in BANCOS:
        for p in find_instances(os.path.join(ROOT, "bench", b)):
            n = os.path.basename(p)
            if n in vistas:
                continue
            vistas.add(n)
            h = n.split(".")[0]
            filas.append({"instance": n, "bank": b, "path": os.path.relpath(p, ROOT),
                          "known": k.get(h, "unknown")})
    with open(MUESTRA, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["instance", "bank", "path", "known"])
        w.writeheader()
        w.writerows(filas)
    print(f"muestra: {len(filas)} instancias ({len(SINTETICAS)} sintéticas)")


def muestra_dev():
    k = {r["hash"]: r["resultado"] for r in csv.DictReader(open(os.path.join(ROOT, "bench", "dev.list.csv")))}
    filas = []
    for p in find_instances(os.path.join(ROOT, "bench", "dev")):
        n = os.path.basename(p)
        h = n.split(".")[0]
        filas.append({"instance": n, "bank": "dev", "path": os.path.relpath(p, ROOT),
                      "known": k.get(h, "unknown") if k.get(h) in ("sat", "unsat") else "unknown"})
    with open(MUESTRA_DEV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["instance", "bank", "path", "known"])
        w.writeheader()
        w.writerows(filas)
    print(f"muestra-dev: {len(filas)} instancias")


def ejecutar(cmd, timeout):
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                           timeout=timeout, preexec_fn=limitar)
        return r.returncode, r.stdout + r.stderr, time.time() - t0
    except subprocess.TimeoutExpired:
        return None, "", time.time() - t0


def verificar(tool, cnf, proof):
    code, out, t = ejecutar([tool, cnf, proof], T_CHECK)
    ok = re.search(r"(^|\r)s VERIFIED", out, re.M) is not None
    return ("VERIFIED" if ok else ("TIMEOUT" if code is None else "FALLA")), f"{t:.2f}"


def correr(a):
    sinteticas()  # no se versionan: se regeneran, idénticas, si faltan
    salida, muestra_csv = a.out or X1CSV, a.muestra or MUESTRA
    hechas = filas_completas(salida, CAMPOS)
    listas = {r["instance"] for r in hechas}
    tmp = os.path.join(D, "tmp")
    os.makedirs(tmp, exist_ok=True)
    with EscritorDuradero(salida, CAMPOS, hechas) as ed:
        for m in csv.DictReader(open(muestra_csv)):
            if m["instance"] in listas:
                continue
            path = os.path.join(ROOT, m["path"])
            # X1 y nada más: sin preproceso, sin intentos «lucky», sin conflictos.
            code, out, wall = ejecutar([a.kissat, "--gauss=1", "--verbose=1", "--conflicts=0",
                                        "--preprocess=false", "--lucky=false", "-n", path], T_X1)
            fila = {k: "" for k in CAMPOS}
            fila.update(instance=m["instance"], bank=m["bank"], known=m["known"],
                        exit_code="" if code is None else code, wall_s=f"{wall:.2f}")
            if code is None:
                fila["outcome"] = "timeout"
            elif (g := RE_REF.search(out)):
                fila.update(outcome="refutada", rows=g[1], vars=g[2], cert_rows=g[3], x1_s=g[5])
                # Con prueba: X1 refuta antes de cualquier búsqueda.
                proof = os.path.join(tmp, "x1.proof")
                cnf = path
                if path.endswith(".xz"):
                    cnf = os.path.join(tmp, "x1.cnf")
                    with open(cnf, "w") as f:
                        subprocess.run(["xz", "-dc", path], stdout=f, check=True)
                code2, out2, _ = ejecutar([a.kissat, "--gauss=1", path, proof], T_X1)
                g2 = RE_REF.search(out2)
                fila["ext_vars"] = g2[4] if g2 else ""
                fila["proof_bytes"] = os.path.getsize(proof) if os.path.exists(proof) else ""
                fila["dsr_sc2026"], fila["dsr_sc2026_s"] = verificar(os.path.join(a.tools, "dsr-trim-sc2026"), cnf, proof)
                fila["dsr_actual"], fila["dsr_actual_s"] = verificar(os.path.join(a.tools, "dsr-trim"), cnf, proof)
                for p in (proof, os.path.join(tmp, "x1.cnf")):
                    if os.path.exists(p):
                        os.remove(p)
            elif (g := RE_CON.search(out)):
                fila.update(outcome="consistente", rows=g[1], vars=g[2], x1_s=g[3])
            elif (g := RE_SALTA.search(out)):
                fila.update(outcome="saltada", rows=g[1], vars=g[2], x1_s=g[3])
            elif (g := RE_TOPE.search(out)):
                fila.update(outcome="saltada", x1_s=g[1])
            elif (g := RE_NADA.search(out)):
                fila.update(outcome="sin_xor", rows="0", vars="0", x1_s=g[1])
            else:
                fila["outcome"] = "sin_mensaje"
            ed.escribir(fila)
            print(f"[{m['instance'][:12]}] {fila['outcome']} x1 {fila['x1_s']} s "
                  f"filas {fila['rows']} {fila['dsr_sc2026']} {fila['dsr_actual']}", flush=True)


def contadores(salida):
    out = []
    for linea in salida.splitlines():
        g = re.match(r"^c ([a-z_0-9]+):\s+(\d+)", linea)
        if g and not re.search(r"time|resident|memory|real|process|second", g[1]):
            out.append((g[1], g[2]))
        elif linea.startswith("s "):
            out.append(("s", linea[2:].strip()))
    return out


def equivalencia(a):
    x1 = filas_completas(X1CSV, CAMPOS)
    m16 = {l.strip() for l in open(os.path.join(ROOT, "results", "exp016", "muestra.txt"))
           if l.strip() and not l.startswith("#")}
    rutas = {r["instance"]: r["path"] for r in csv.DictReader(open(MUESTRA))}
    sel = [r["instance"] for r in x1
           if (r["outcome"] in ("consistente", "saltada")) or
           (r["instance"] in m16 and r["bank"] == "tesis-dev" and r["outcome"] != "refutada")]
    hechas = filas_completas(EQCSV, CAMPOS_EQ)
    listas = {r["instance"] for r in hechas}
    with EscritorDuradero(EQCSV, CAMPOS_EQ, hechas) as ed:
        for n in sel:
            if n in listas:
                continue
            path = os.path.join(ROOT, rutas[n])
            base = ["--seed=1", "--conflicts=20000", "--statistics", path]
            _, o0, _ = ejecutar([a.kissat, "--gauss=0"] + base, 3600)
            _, o1, _ = ejecutar([a.kissat, "--gauss=1"] + base, 3600)
            c0, c1 = contadores(o0), contadores(o1)
            dif = [f"{x}≠{y}" for x, y in zip(c0, c1) if x != y]
            st = lambda c: next((v for k, v in c if k == "s"), "?")
            ed.escribir({"instance": n, "status_0": st(c0), "status_1": st(c1), "contadores": len(c0),
                         "identicos": int(c0 == c1 and len(c0) > 0), "diferencias": ";".join(dif[:5])})
            print(f"[{n[:12]}] {'IGUAL' if c0 == c1 else 'DISTINTO'} ({len(c0)})", flush=True)


def analizar(a):
    import statistics as st
    x1 = filas_completas(X1CSV, CAMPOS)
    eq = filas_completas(EQCSV, CAMPOS_EQ)
    print(f"## EXP-019 — X1 (n = {len(x1)} instancias)\n")
    cuenta = {}
    for r in x1:
        cuenta[r["outcome"]] = cuenta.get(r["outcome"], 0) + 1
    print("Resultado de X1: " + ", ".join(f"{k} {v}" for k, v in sorted(cuenta.items())))
    ref = [r for r in x1 if r["outcome"] == "refutada"]
    malas = [r for r in ref if r["known"] == "sat"]
    no_ver = [r for r in ref if r["dsr_sc2026"] != "VERIFIED" or r["dsr_actual"] != "VERIFIED"]
    print("\n### H0 (seguridad, vinculante)\n")
    print(f"- Refutadas con resultado conocido SAT: **{len(malas)}**.")
    print(f"- Refutadas cuya prueba no verifica alguno de los dos dsr-trim: **{len(no_ver)}** de {len(ref)}.")
    h0 = not malas and not no_ver
    print("\n### H1 (búsqueda idéntica cuando no refuta)\n")
    dist = [r for r in eq if r["identicos"] != "1"]
    print(f"- Parejas con los contadores idénticos: {len(eq) - len(dist)} de {len(eq)}.")
    for r in dist:
        print(f"  - DISTINTA: {r['instance']} ({r['diferencias']})")
    h1 = len(eq) > 0 and not dist
    print("\n### H2 (coste)\n")
    t = sorted(float(r["x1_s"]) for r in x1 if r["x1_s"])
    if t:
        p95 = t[min(len(t) - 1, int(0.95 * len(t)))]
        print(f"- Tiempo de X1 por instancia (n = {len(t)}): mediana {st.median(t):.3f} s, "
              f"p95 {p95:.3f} s, máximo {t[-1]:.2f} s, media {st.mean(t):.3f} s.")
        h2 = p95 <= 1.0 and t[-1] <= 10.0
    else:
        h2 = False
    sin = [r for r in x1 if r["outcome"] in ("timeout", "sin_mensaje")]
    print(f"- Corridas sin medida (tiempo agotado o sin mensaje): {len(sin)}.")
    print("\n### H3 (efecto, descriptivo)\n")
    print("| instancia | banco | conocido | filas | certificado | X1 (s) | prueba (bytes) | dsr SC2026 (s) | dsr actual (s) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in ref:
        print(f"| {r['instance'][:16]} | {r['bank']} | {r['known']} | {r['rows']} | {r['cert_rows']} | {r['x1_s']} | "
              f"{r['proof_bytes']} | {r['dsr_sc2026']} {r['dsr_sc2026_s']} | {r['dsr_actual']} {r['dsr_actual_s']} |")
    dev = filas_completas(X1DEV, CAMPOS)
    if dev:
        print("\n### Ampliación (§3b): instancias de paridad de bench/dev\n")
        print("| instancia | conocido | resultado de X1 | filas | X1 (s) | prueba (bytes) | dsr SC2026 (s) | dsr actual (s) |")
        print("|---|---|---|---|---|---|---|---|")
        for r in dev:
            print(f"| {r['instance'][:16]} | {r['known']} | {r['outcome']} | {r['rows']} | {r['x1_s']} | "
                  f"{r['proof_bytes']} | {r['dsr_sc2026']} {r['dsr_sc2026_s']} | {r['dsr_actual']} {r['dsr_actual_s']} |")
        malas_dev = [r for r in dev if r["outcome"] == "refutada" and
                     (r["known"] == "sat" or r["dsr_sc2026"] != "VERIFIED" or r["dsr_actual"] != "VERIFIED")]
        print(f"\n- Seguridad en la ampliación (cuenta para H0): {len(malas_dev)} fallos.")
        h0 = h0 and not malas_dev
    veredicto = "ADOPTAR" if (h0 and h1 and h2) else "no se adopta"
    print(f"\n**Veredicto (§4)**: {veredicto} (H0 {'sí' if h0 else 'NO'}, H1 {'sí' if h1 else 'NO'}, "
          f"H2 {'sí' if h2 else 'NO'})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("paso", choices=["muestra", "muestra-dev", "correr", "equivalencia", "analizar"])
    ap.add_argument("--muestra", help="correr: muestra alternativa (CSV)")
    ap.add_argument("--out", help="correr: salida alternativa (CSV)")
    ap.add_argument("--kissat", default=os.path.join(ROOT, "solver", "kissat", "build-x1", "kissat"))
    ap.add_argument("--tools", default=os.path.join(ROOT, "tools"))
    a = ap.parse_args()
    {"muestra": lambda a: muestra(), "muestra-dev": lambda a: muestra_dev(), "correr": correr,
     "equivalencia": equivalencia,
     "analizar": analizar}[a.paso](a)
