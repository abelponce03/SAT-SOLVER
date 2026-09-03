#!/usr/bin/env python3
"""
Generador de instancias CNF (DIMACS) para el harness de baseline.

Produce dos familias clasicas y controlables:

  * pigeonhole (PHP)  -> UNSAT, dificultad crece rapido con n. Util para medir
                         rendimiento en refutacion (donde las pruebas DRAT importan).
  * random 3-SAT      -> mezcla SAT/UNSAT cerca de la razon critica (~4.26),
                         estandar de la comunidad para comparar solvers.

NO pretende sustituir a los benchmarks oficiales de la SAT Competition (ver
benchmarks/README.md). Sirve para validar el harness y tener una curva de
referencia reproducible sin descargar gigabytes.

Uso:
    python3 gen_benchmarks.py --out ../benchmarks/sample
"""
import argparse
import os
import random


def write_dimacs(path, n_vars, clauses, comment=""):
    with open(path, "w") as f:
        if comment:
            for line in comment.strip().splitlines():
                f.write(f"c {line}\n")
        f.write(f"p cnf {n_vars} {len(clauses)}\n")
        for cl in clauses:
            f.write(" ".join(str(x) for x in cl) + " 0\n")


def pigeonhole(n):
    """PHP(n+1, n): n+1 palomas en n agujeros. UNSAT. Variable x(p,h)=palomar p en agujero h."""
    def var(p, h):
        return p * n + h + 1  # p in [0..n], h in [0..n-1]

    n_vars = (n + 1) * n
    clauses = []
    # Cada paloma en al menos un agujero.
    for p in range(n + 1):
        clauses.append([var(p, h) for h in range(n)])
    # Ningun agujero con dos palomas.
    for h in range(n):
        for p1 in range(n + 1):
            for p2 in range(p1 + 1, n + 1):
                clauses.append([-var(p1, h), -var(p2, h)])
    return n_vars, clauses


def random_3sat(n_vars, ratio, seed):
    """3-SAT aleatorio con n_vars variables y ratio*n_vars clausulas."""
    rng = random.Random(seed)
    n_clauses = int(round(ratio * n_vars))
    clauses = []
    for _ in range(n_clauses):
        cl = set()
        while len(cl) < 3:
            v = rng.randint(1, n_vars)
            lit = v if rng.random() < 0.5 else -v
            if v not in (abs(x) for x in cl):
                cl.add(lit)
        clauses.append(list(cl))
    return n_vars, clauses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../benchmarks/sample",
                    help="directorio de salida")
    ap.add_argument("--php", default="4,5,6,7",
                    help="valores de n para pigeonhole, separados por coma")
    ap.add_argument("--rand-vars", default="80,120,160",
                    help="n_vars para 3-SAT aleatorio, separados por coma")
    ap.add_argument("--ratio", type=float, default=4.26,
                    help="razon clausulas/variables para 3-SAT (defecto ~critica)")
    ap.add_argument("--seeds", default="1,2",
                    help="semillas para 3-SAT, separadas por coma")
    args = ap.parse_args()

    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    for n in [int(x) for x in args.php.split(",") if x]:
        nv, cls = pigeonhole(n)
        path = os.path.join(out, f"php_{n+1}_{n}.cnf")
        write_dimacs(path, nv, cls,
                     comment=f"pigeonhole {n+1} palomas en {n} agujeros (UNSAT)")
        print(f"[php]  {os.path.basename(path):24s} vars={nv:5d} clausulas={len(cls)}")

    for nv in [int(x) for x in args.rand_vars.split(",") if x]:
        for seed in [int(x) for x in args.seeds.split(",") if x]:
            n, cls = random_3sat(nv, args.ratio, seed)
            path = os.path.join(out, f"rand3_{nv}_r{args.ratio}_s{seed}.cnf")
            write_dimacs(path, n, cls,
                         comment=f"random 3-SAT vars={nv} ratio={args.ratio} seed={seed}")
            print(f"[rand] {os.path.basename(path):24s} vars={n:5d} clausulas={len(cls)}")


if __name__ == "__main__":
    main()
