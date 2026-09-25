#!/usr/bin/env python3
"""
compare_satsuma_builds.py — ¿cambia el resultado de satsuma según cómo se
compile?  Tarea «coste de mantener MIT» (ADR-0004): satsuma sin cliques (el
nuestro, MIT) frente a satsuma con cliques (cliquer, GPLv2).

Solo ejecuta satsuma, sin kissat.  Por cada build e instancia registra el
código de salida, el tiempo, las cláusulas de salida, el tamaño del prefijo de
la prueba y el SHA-1 de la CNF de salida.  Si el SHA-1 coincide, kissat recibe
EXACTAMENTE la misma fórmula y el build no puede cambiar el PAR-2 en esa
instancia; solo hace falta correr kissat donde difiera.

Los binarios con cliquer NO se versionan ni se distribuyen: se pasan por ruta
desde fuera del repositorio.

Uso:
  python3 scripts/compare_satsuma_builds.py --bench bench/symm2026 \\
      --build mit=tools/satsuma --build cliques=/tmp/satsuma-cliques/build/satsuma \\
      --out results/satsuma-builds.csv
"""
import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checkpoint import EscritorDuradero, filas_completas  # noqa: E402
from run_experiment import find_instances  # noqa: E402

ARGS = ["--silent", "--full-skip-limit", "100000000", "--add-reduced-as-unit", "--bsr"]


def header_clauses(path):
    with open(path, errors="replace") as f:
        for line in f:
            if line.startswith("p cnf"):
                return int(line.split()[3])
    return -1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bench", required=True, nargs="+")
    ap.add_argument("--build", required=True, action="append", metavar="NOMBRE=RUTA")
    ap.add_argument("--timeout", type=float, default=60.0,
                    help="el mismo tope que LABESAT_SYMM_TIMEOUT")
    ap.add_argument("--out", required=True)
    ap.add_argument("--resume", action="store_true",
                    help="conservar las instancias ya completas (todas sus builds) y seguir (ADR-0008)")
    args = ap.parse_args()
    builds = [b.split("=", 1) for b in args.build]

    insts = [i for b in args.bench for i in find_instances(b)]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    campos = ["instance", "family", "build", "exit", "secs", "clauses_in",
              "clauses_out", "proof_bytes", "out_sha1"]
    previas = filas_completas(args.out, campos) if args.resume else []
    nombres = {b for b, _ in builds}
    por_inst = {}
    for r in previas:
        por_inst.setdefault(r["instance"], set()).add(r["build"])
    hechas = {i for i, bs in por_inst.items() if nombres <= bs}
    previas = [r for r in previas if r["instance"] in hechas]
    if args.resume:
        print(f"[reanudar] {len(hechas)} instancias completas se conservan", flush=True)
    with EscritorDuradero(args.out, campos, previas) as ed:
        for n, inst in enumerate(insts, 1):
            if os.path.basename(inst) in hechas:
                continue
            filas = []
            with tempfile.TemporaryDirectory() as tmp:
                cnf = inst
                if inst.endswith(".xz"):
                    cnf = os.path.join(tmp, "in.cnf")
                    with open(cnf, "wb") as f:
                        subprocess.run(["xz", "-dc", inst], stdout=f, check=True)
                cin = header_clauses(cnf)
                linea = []
                for nombre, exe in builds:
                    out, proof = os.path.join(tmp, "o.cnf"), os.path.join(tmp, "p")
                    for f in (out, proof):
                        if os.path.exists(f):
                            os.remove(f)
                    t0 = time.monotonic()
                    try:
                        code = subprocess.run([exe, "fix", cnf, *ARGS, "--proof-file", proof,
                                               "--out-file", out],
                                              stdout=subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL,
                                              timeout=args.timeout).returncode
                    except subprocess.TimeoutExpired:
                        code = "TOPE"
                    secs = time.monotonic() - t0
                    ok = code == 0 and os.path.exists(out)
                    sha = hashlib.sha1(open(out, "rb").read()).hexdigest() if ok else ""
                    filas.append({"instance": os.path.basename(inst),
                                "family": os.path.basename(os.path.dirname(inst)),
                                "build": nombre, "exit": code, "secs": f"{secs:.3f}",
                                "clauses_in": cin,
                                "clauses_out": header_clauses(out) if ok else "",
                                "proof_bytes": os.path.getsize(proof) if ok and
                                os.path.exists(proof) else "",
                                "out_sha1": sha})
                    linea.append(f"{nombre}:{code}/{secs:.1f}s/{sha[:8]}")
                for fila in filas:          # la instancia entera, o nada
                    ed.w.writerow(fila)
                ed.persistir()
                print(f"[{n:>3}/{len(insts)}] {os.path.basename(inst)[:34]:<34} "
                      + "  ".join(linea), flush=True)


if __name__ == "__main__":
    main()
