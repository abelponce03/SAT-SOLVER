#!/usr/bin/env python3
"""
collect_stats.py - Fase 0: caracteriza la dinámica de búsqueda de CaDiCaL sobre
un directorio de instancias, usando las estadísticas NATIVAS del solver
(`--stats`), sin modificar el código fuente todavía.

Objetivo: cuantificar "cuánta varianza hay que explotar" antes de escribir una
política de restart/reset adaptativa. Para cada instancia resuelta dentro del
presupuesto de tiempo extrae, entre otros:

  - conflicts, decisions, propagations
  - restarts, reused% (reutilización de trail), restartstab (restarts en modo estable)
  - rephased (nº) : cuántos resets de fase hizo la política actual
  - stabilizing%  : fracción de conflictos en modo estable vs focused
  - chronological%: uso de backtracking cronológico
  - reduced%, learned, improvedglue% : dinámica de cláusulas aprendidas / LBD

Escribe un CSV por instancia y un resumen con el rango (min/mediana/max) de cada
señal sobre las instancias resueltas: ahí se ve si una política más lista tiene
margen.

Uso:
  python3 collect_stats.py -s <solver_bin> -b <dir_bench> -o <salida.csv> [-t budget_s]
"""
import argparse
import csv
import os
import re
import statistics
import subprocess
import sys
import time

# campo_csv -> patrón que captura el PRIMER número de la línea `c <clave>: <n> ...`
FIELDS = {
    "conflicts":       r"^c conflicts:\s+(\d+)",
    "decisions":       r"^c decisions:\s+(\d+)",
    "propagations":    r"^c propagations:\s+(\d+)",
    "restarts":        r"^c restarts:\s+(\d+)",
    "learned":         r"^c learned:\s+(\d+)",
    "rephased":        r"^c rephased:\s+(\d+)",
}
# campos que además tienen un PORCENTAJE en la 2ª columna numérica
PCT_FIELDS = {
    "reused_pct":        r"^c\s+reused:\s+\d+\s+([\d.]+)\s*%",
    "stabilizing_pct":   r"^c stabilizing:\s+\d+\s+([\d.]+)\s*%",
    "chronological_pct": r"^c chronological:\s+\d+\s+([\d.]+)\s*%",
    "reduced_pct":       r"^c reduced:\s+\d+\s+([\d.]+)\s*%",
    "improvedglue_pct":  r"^c\s+improvedglue:\s+\d+\s+([\d.]+)\s*%",
    "restartstab_pct":   r"^c\s+restartstab:\s+\d+\s+([\d.]+)\s*%",
}


def parse_stats(text):
    out = {}
    for key, pat in FIELDS.items():
        m = re.search(pat, text, re.MULTILINE)
        out[key] = int(m.group(1)) if m else None
    for key, pat in PCT_FIELDS.items():
        m = re.search(pat, text, re.MULTILINE)
        out[key] = float(m.group(1)) if m else None
    return out


def run_one(solver, cnf, budget):
    start = time.time()
    try:
        p = subprocess.run(
            [solver, "--stats=true", "--report=false", cnf],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=budget, text=True)
        code = p.returncode
        text = p.stdout
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "wall_time_s": float(budget)}, {}
    wall = time.time() - start
    status = {10: "SAT", 20: "UNSAT"}.get(code, "UNKNOWN")
    stats = parse_stats(text) if status in ("SAT", "UNSAT") else {}
    stats.update({"status": status, "wall_time_s": round(wall, 3)})
    return stats, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--solver", required=True)
    ap.add_argument("-b", "--bench", required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("-t", "--budget", type=int, default=90,
                    help="presupuesto de tiempo por instancia (s)")
    args = ap.parse_args()

    files = sorted(
        os.path.join(args.bench, f) for f in os.listdir(args.bench)
        if f.endswith(".cnf"))
    if not files:
        sys.exit(f"no hay .cnf en {args.bench}")

    cols = (["instance", "status", "wall_time_s"]
            + list(FIELDS) + list(PCT_FIELDS))
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    rows = []
    print(f"{'instancia':30s} {'estado':8s} {'t(s)':>7s} {'confl':>9s} "
          f"{'restarts':>9s} {'reused%':>8s} {'stab%':>7s} {'rephase':>7s}")
    print("-" * 92)
    for cnf in files:
        name = os.path.basename(cnf)
        stats, _ = run_one(args.solver, cnf, args.budget)
        row = {"instance": name}
        row.update({c: stats.get(c) for c in cols if c != "instance"})
        rows.append(row)
        fmt = lambda v: "-" if v is None else v
        print(f"{name:30s} {str(row['status']):8s} {row['wall_time_s']:7} "
              f"{str(fmt(row['restarts']) if False else fmt(row['conflicts'])):>9} "
              f"{str(fmt(row['restarts'])):>9} {str(fmt(row['reused_pct'])):>8} "
              f"{str(fmt(row['stabilizing_pct'])):>7} {str(fmt(row['rephased'])):>7}")

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    # --- resumen de varianza sobre instancias resueltas ---
    solved = [r for r in rows if r["status"] in ("SAT", "UNSAT")]
    print("\n" + "=" * 60)
    print(f"RESUMEN sobre {len(solved)}/{len(rows)} instancias resueltas "
          f"(presupuesto {args.budget}s)")
    print("=" * 60)
    print(f"{'señal':22s} {'min':>10s} {'mediana':>10s} {'max':>10s}")
    print("-" * 54)
    for key in list(FIELDS) + list(PCT_FIELDS):
        vals = [r[key] for r in solved if r[key] is not None]
        if not vals:
            continue
        print(f"{key:22s} {min(vals):>10.2f} {statistics.median(vals):>10.2f} "
              f"{max(vals):>10.2f}")
    print("\nLectura: señales con rango amplio (min<<max) entre instancias son")
    print("las que una política adaptativa puede explotar. Restarts, reused%,")
    print("stabilizing% y rephased indican el margen para un controlador de reset.")
    print(f"\nCSV -> {args.out}")


if __name__ == "__main__":
    main()
