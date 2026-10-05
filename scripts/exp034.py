#!/usr/bin/env python3
"""
exp034.py — EXP-034 (M12, research/12 §8): ¿verifican las pruebas de
LabeSAT a escala, y cuánto tardan frente a la resolución?

  correr      por instancia de las listas: `labesat --symmetry` con prueba
              (T = --timeout); si sale UNSAT, verifican la prueba los DOS
              dsr-trim (el actual y el de SC2026), con tope --check-timeout
              cada uno, midiendo el reloj; se borra la prueba
  analizar    resumen: fallos (vinculante), razón verificación/resolución,
              tamaños, y la extrapolación al límite de la competición

Reanuda (ADR-0008): salta las instancias ya escritas en --out.

Uso:
  python3 scripts/exp034.py correr --listas results/exp034/simetricas.txt \\
      results/exp034/industria.txt --bench bench/symm2026 bench/tesis-dev \\
      --out results/exp034/verificacion.csv
  python3 scripts/exp034.py analizar results/exp034/verificacion.csv
"""
import argparse
import csv
import math
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checkpoint import EscritorDuradero, filas_completas  # noqa: E402
from run_experiment import find_instances, sha1_of  # noqa: E402
from verify_symm_answers import DSRS, plain_cnf  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABESAT = os.path.join(ROOT, "solver", "labesat")
CAMPOS = ["instance", "lista", "status", "solve_wall_s", "proof_bytes",
          "dsr_trim", "dsr_trim_s", "dsr_trim_sc2026", "dsr_trim_sc2026_s",
          "kissat_sha1", "started_at"]


def verificar(dsr, cnf, prueba, tope):
    t0 = time.monotonic()
    try:
        p = subprocess.run([dsr, cnf, prueba], capture_output=True, text=True,
                           errors="replace", timeout=tope)
        ok = any("s VERIFIED" in ln for ln in p.stdout.splitlines())
        return ("OK" if ok else "FALLO"), round(time.monotonic() - t0, 2)
    except subprocess.TimeoutExpired:
        return "TOPE", round(time.monotonic() - t0, 2)


def correr(args):
    faltan = [d for d in DSRS if not os.access(d, os.X_OK)]
    if faltan:
        sys.exit(f"ABORTADO: falta el verificador {faltan} (scripts/get_tools.sh)")
    rutas = {os.path.basename(i): i for b in args.bench for i in find_instances(b)}
    tareas = []
    for lista in args.listas:
        for ln in open(lista):
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                if ln not in rutas:
                    sys.exit(f"ABORTADO: {ln} no está en {args.bench}")
                tareas.append((ln, os.path.basename(lista)))
    kissat = os.environ.get("LABESAT_KISSAT", os.path.join(ROOT, "solver", "kissat", "build", "kissat"))
    sha = sha1_of(kissat)
    previas = filas_completas(args.out, CAMPOS)
    hechas = {r["instance"] for r in previas}
    with EscritorDuradero(args.out, CAMPOS, previas) as ed:
        for n, (nombre, lista) in enumerate(tareas, 1):
            if nombre in hechas:
                continue
            if sha1_of(kissat) != sha:
                sys.exit("ABORTADO: el binario de kissat cambió durante la tanda")
            fila = {"instance": nombre, "lista": lista, "kissat_sha1": sha[:12],
                    "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
            with tempfile.TemporaryDirectory(dir=args.tmp) as tmp:
                prueba = os.path.join(tmp, "p.proof")
                t0 = time.monotonic()
                with open(os.devnull, "w") as nul:
                    code = subprocess.run([LABESAT, "--symmetry", "-n", "--seed=42",
                                           f"--time={args.timeout}", rutas[nombre], prueba],
                                          stdout=nul, stderr=subprocess.DEVNULL).returncode
                fila["solve_wall_s"] = round(time.monotonic() - t0, 2)
                fila["status"] = {10: "SAT", 20: "UNSAT"}.get(code, "UNKNOWN" if code == 0 else f"ERROR({code})")
                fila["proof_bytes"] = os.path.getsize(prueba) if os.path.exists(prueba) else 0
                if code == 20:
                    cnf = plain_cnf(rutas[nombre], tmp)
                    for dsr in DSRS:
                        k = os.path.basename(dsr).replace("-", "_")
                        fila[k], fila[k + "_s"] = verificar(dsr, cnf, prueba, args.check_timeout)
            ed.escribir(fila)
            print(f"[{n}/{len(tareas)}] {nombre[:34]:34} {fila['status']:8} {fila['solve_wall_s']}s "
                  f"{fila['proof_bytes'] / 2**20:.1f} MiB  dsr {fila.get('dsr_trim', '-')} "
                  f"{fila.get('dsr_trim_s', '')}  sc2026 {fila.get('dsr_trim_sc2026', '-')} "
                  f"{fila.get('dsr_trim_sc2026_s', '')}", flush=True)


def analizar(args):
    filas = [r for r in csv.DictReader(open(args.csv)) if r["status"] == "UNSAT"]
    print(f"UNSAT: {len(filas)}")
    for k in ("dsr_trim", "dsr_trim_sc2026"):
        c = {}
        for r in filas:
            c[r[k]] = c.get(r[k], 0) + 1
        print(f"  {k}: {c}")
    fallos = [r["instance"] for r in filas if "FALLO" in (r["dsr_trim"], r["dsr_trim_sc2026"])]
    print(f"FALLOS (vinculante): {len(fallos)} {fallos[:10]}")
    razones = []
    for r in filas:
        if r["dsr_trim_sc2026"] == "OK" and float(r["solve_wall_s"]) >= 1.0:
            razones.append(float(r["dsr_trim_sc2026_s"]) / float(r["solve_wall_s"]))
    if razones:
        razones.sort()
        p = lambda q: razones[min(len(razones) - 1, int(q * len(razones)))]  # noqa: E731
        print(f"verificación SC2026 / resolución (n = {len(razones)}): mediana {p(0.5):.2f}, "
              f"p90 {p(0.9):.2f}, p95 {p(0.95):.2f}, máx {razones[-1]:.2f}")
        print(f"  a T = 5000 s, una razón de {40000 / 5000:.0f} agota 40 000 s de verificación; "
              f"instancias por encima: {sum(x > 8 for x in razones)}")
    tam = sorted(int(r["proof_bytes"]) for r in filas)
    if tam:
        print(f"tamaño de la prueba: mediana {tam[len(tam) // 2] / 2**20:.1f} MiB, "
              f"máx {tam[-1] / 2**20:.1f} MiB; media geométrica "
              f"{math.exp(sum(math.log(max(t, 1)) for t in tam) / len(tam)) / 2**20:.2f} MiB")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("correr")
    c.add_argument("--listas", nargs="+", required=True)
    c.add_argument("--bench", nargs="+", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--timeout", type=int, default=300)
    c.add_argument("--check-timeout", type=int, default=3600)
    c.add_argument("--tmp", default=None, help="directorio de las pruebas temporales (disco local)")
    c.set_defaults(f=correr)
    a = sub.add_parser("analizar")
    a.add_argument("csv")
    a.set_defaults(f=analizar)
    args = ap.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
