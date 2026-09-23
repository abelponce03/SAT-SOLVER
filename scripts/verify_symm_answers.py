#!/usr/bin/env python3
"""
verify_symm_answers.py — comprobación de seguridad de EXP-007 (vinculante,
ADR-0004): reejecuta las respuestas de la rama con ruptura de simetrías y las
verifica contra la CNF ORIGINAL.

  - SAT:   se reejecuta `labesat` y el modelo se comprueba con verify_model.py.
  - UNSAT: si la rama la resolvió en <= --max-solve s, se reejecuta escribiendo
           la prueba y dsr-trim la verifica (tope --check-timeout por prueba).

Salida: CSV con instance,status,verificacion (OK / FALLO / TOPE / SALTADA) y un
resumen.  Código de salida 1 si hay algún FALLO.

Uso:
  python3 scripts/verify_symm_answers.py results/exp007/B.csv \\
      --bench bench/symm2026 --out results/exp007/seguridad.csv
"""
import argparse
import csv
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_experiment import find_instances  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABESAT = os.path.join(ROOT, "solver", "labesat")
DSR = os.path.join(ROOT, "tools", "dsr-trim")
VERIFY = os.path.join(ROOT, "scripts", "verify_model.py")


def plain_cnf(path, tmp):
    """dsr-trim y verify_model necesitan la CNF sin comprimir."""
    if not path.endswith(".xz"):
        return path
    out = os.path.join(tmp, "orig.cnf")
    with open(out, "wb") as f:
        subprocess.run(["xz", "-dc", path], stdout=f, check=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_b")
    ap.add_argument("--bench", required=True, nargs="+",
                    help="bancos donde buscar las instancias (el CSV guarda el nombre)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=180, help="--time al reejecutar")
    ap.add_argument("--max-solve", type=float, default=60.0)
    ap.add_argument("--check-timeout", type=int, default=1800)
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.csv_b)))
    rutas = {os.path.basename(i): i for b in args.bench for i in find_instances(b)}
    res, cuenta = [], {}
    for n, r in enumerate(rows, 1):
        inst, st, t = rutas[r["instance"]], r["status"], float(r["cpu_s"])
        seed = r.get("seed") or "1"
        ver = "SALTADA"
        with tempfile.TemporaryDirectory() as tmp:
            if st == "SAT":
                out = os.path.join(tmp, "out")
                with open(out, "w") as f:
                    code = subprocess.run([LABESAT, f"--seed={seed}", f"--time={args.timeout}",
                                           inst], stdout=f).returncode
                if code != 10:
                    ver = f"NO-REPRODUCE({code})"
                else:
                    cnf = plain_cnf(inst, tmp)
                    ok = subprocess.run([sys.executable, VERIFY, "--model", out, cnf],
                                        capture_output=True).returncode == 0
                    ver = "OK" if ok else "FALLO"
            elif st == "UNSAT" and t <= args.max_solve:
                proof = os.path.join(tmp, "proof")
                code = subprocess.run([LABESAT, f"--seed={seed}", f"--time={args.timeout}",
                                       "-q", inst, proof],
                                      stdout=subprocess.DEVNULL).returncode
                if code != 20:
                    ver = f"NO-REPRODUCE({code})"
                else:
                    cnf = plain_cnf(inst, tmp)
                    try:
                        p = subprocess.run([DSR, cnf, proof], capture_output=True, text=True,
                                           timeout=args.check_timeout)
                        ok = any(l.startswith("s VERIFIED") for l in p.stdout.splitlines())
                        ver = "OK" if ok else "FALLO"
                    except subprocess.TimeoutExpired:
                        ver = "TOPE"
        cuenta[(st, ver)] = cuenta.get((st, ver), 0) + 1
        res.append({"instance": inst, "status": st, "cpu_s": t, "verificacion": ver})
        print(f"[{n:>3}/{len(rows)}] {os.path.basename(inst)[:40]:<40} {st:<8} {ver}",
              flush=True)

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["instance", "status", "cpu_s", "verificacion"])
        w.writeheader()
        w.writerows(res)
    print("\nresumen:", {f"{a}/{b}": c for (a, b), c in sorted(cuenta.items())})
    fallos = sum(c for (a, b), c in cuenta.items() if b == "FALLO")
    noreps = sum(c for (a, b), c in cuenta.items() if b.startswith("NO-REPRODUCE"))
    print("SEGURIDAD:", "sin fallos" if not fallos else f"{fallos} FALLOS -> desactivar (ADR-0004)")
    if noreps:
        print(f"   {noreps} respuestas no se reprodujeron al reejecutar: NO cuentan como"
              " verificadas; hay que mirarlas una a una")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
