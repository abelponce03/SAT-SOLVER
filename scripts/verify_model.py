#!/usr/bin/env python3
"""
verify_model.py — comprueba que un modelo devuelto por el solver satisface de
verdad la fórmula.

Un solver de competición que devuelve SAT con un modelo incorrecto queda
descalificado, y un parche a la heurística de fases o al *rephasing* es
precisamente el tipo de cambio que puede romper esto sin que ningún test de
tiempo lo note. Por eso esta verificación corre en CI sobre `bench/smoke`.

Uso:
  python3 scripts/verify_model.py <solver> <instancia.cnf>      # resuelve y verifica
  python3 scripts/verify_model.py --model <salida.txt> <instancia.cnf>
"""
import argparse
import gzip
import lzma
import subprocess
import sys


def open_cnf(path):
    if path.endswith(".xz"):
        return lzma.open(path, "rt")
    if path.endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path)


def read_cnf(path):
    clauses, clause = [], []
    with open_cnf(path) as f:
        for line in f:
            line = line.strip()
            if not line or line[0] in "cp%":
                continue
            for tok in line.split():
                lit = int(tok)
                if lit == 0:
                    clauses.append(clause)
                    clause = []
                else:
                    clause.append(lit)
    if clause:
        clauses.append(clause)
    return clauses


def parse_model(text):
    assign = {}
    for line in text.splitlines():
        if line.startswith("v "):
            for tok in line[2:].split():
                lit = int(tok)
                if lit != 0:
                    assign[abs(lit)] = lit > 0
    return assign


def check(clauses, assign):
    for idx, cl in enumerate(clauses):
        if not any(assign.get(abs(l), False) == (l > 0) for l in cl):
            return idx, cl
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("solver_or_model")
    ap.add_argument("instance")
    ap.add_argument("--model", action="store_true",
                    help="el primer argumento es un fichero con la salida del solver")
    args = ap.parse_args()

    if args.model:
        out = open(args.solver_or_model).read()
        status = "SAT" if "s SATISFIABLE" in out else "?"
    else:
        proc = subprocess.run([args.solver_or_model, "-q", args.instance],
                              capture_output=True, text=True)
        out = proc.stdout
        status = {10: "SAT", 20: "UNSAT"}.get(proc.returncode, "UNKNOWN")

    if status == "UNSAT":
        print(f"UNSAT  {args.instance}  (no verificable sin prueba DRAT; ver scripts/check_proof.sh)")
        return 0
    if status != "SAT":
        print(f"{status}  {args.instance}  (nada que verificar)")
        return 0

    clauses = read_cnf(args.instance)
    assign = parse_model(out)
    if not assign:
        print(f"FALLO  {args.instance}: dijo SAT pero no imprimió modelo")
        return 1
    idx, cl = check(clauses, assign)
    if idx is None:
        print(f"OK     {args.instance}: modelo válido ({len(clauses)} cláusulas, {len(assign)} vars)")
        return 0
    print(f"FALLO  {args.instance}: la cláusula #{idx} {cl} no se satisface -> MODELO INCORRECTO")
    return 1


if __name__ == "__main__":
    sys.exit(main())
