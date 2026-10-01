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


def parse_model(text):
    """Asignación como bytearray indexado por variable: 0 = sin valor,
    1 = verdadera, 2 = falsa. Memoria O(nº de variables), no O(fórmula)."""
    lits = []
    for line in text.splitlines():
        if line.startswith("v "):
            lits.extend(int(t) for t in line[2:].split() if t != "0")
    n = max((abs(l) for l in lits), default=0)
    assign = bytearray(n + 1)
    for lit in lits:
        assign[abs(lit)] = 1 if lit > 0 else 2
    return assign, len(lits)


def check_stream(path, assign):
    """Recorre la CNF en flujo y comprueba cada cláusula al cerrarla.
    Devuelve (nº de cláusulas, None) si todas se satisfacen, o
    (índice, cláusula) de la primera que no. No guarda la fórmula en memoria:
    la versión anterior cargaba todas las cláusulas en listas de Python y, con
    ~40 M de cláusulas, moría por falta de memoria, lo que se registraba como
    un modelo incorrecto (EXP-012, 2026-09-30)."""
    n = len(assign)
    idx, clause, sat = 0, [], False
    with open_cnf(path) as f:
        for line in f:
            if not line or line[0] in "cp%\n":
                continue
            for tok in line.split():
                lit = int(tok)
                if lit == 0:
                    if not sat:
                        return idx, clause
                    idx, clause, sat = idx + 1, [], False
                    continue
                if len(clause) < 16:
                    clause.append(lit)
                v = lit if lit > 0 else -lit
                if not sat and v < n and assign[v] == (1 if lit > 0 else 2):
                    sat = True
    if clause and not sat:
        return idx, clause
    return idx, None


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

    assign, nlits = parse_model(out)
    if not nlits:
        print(f"FALLO  {args.instance}: dijo SAT pero no imprimió modelo")
        return 1
    try:
        idx, cl = check_stream(args.instance, assign)
    except (MemoryError, OSError, EOFError, ValueError) as e:
        # Un fallo DEL VERIFICADOR no es un modelo incorrecto: código propio.
        print(f"ERROR  {args.instance}: no se pudo verificar ({type(e).__name__}: {e})")
        return 2
    if cl is None:
        print(f"OK     {args.instance}: modelo válido ({idx} cláusulas, {nlits} literales)")
        return 0
    print(f"FALLO  {args.instance}: la cláusula #{idx} {cl} no se satisface -> MODELO INCORRECTO")
    return 1


if __name__ == "__main__":
    sys.exit(main())
