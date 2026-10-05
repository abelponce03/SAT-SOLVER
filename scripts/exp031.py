#!/usr/bin/env python3
"""
exp031.py — EXP-031 (M10, research/12 §7): ¿cuántas veces elige
`vivify` un vigilante distinto del que daría el arreglo?

  diagnostico   corre el binario compilado con --stats sobre la lista, con
                presupuesto de conflictos fijo y --vivifywatchfix=0 (la
                búsqueda de siempre), y recoge las estadísticas
                vivify_watch_mismatch (desajustes) y vivified (cláusulas
                vivificadas).  Determinista: no depende de la carga.
  analizar      tasa de desajuste y la decisión preregistrada

Uso:
  python3 scripts/exp031.py diagnostico --kissat solver/kissat/build-m-stats/kissat \\
      --lista results/research12/cribado.txt --bench bench/tesis-dev \\
      --out results/exp031/diagnostico.csv
  python3 scripts/exp031.py analizar results/exp031/diagnostico.csv
"""
import argparse
import csv
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checkpoint import EscritorDuradero, filas_completas  # noqa: E402
from run_experiment import find_instances, sha1_of  # noqa: E402

CAMPOS = ["instance", "exit_code", "conflicts", "vivified", "vivify_watch_mismatch",
          "kissat_sha1"]
STAT = re.compile(r"^c (conflicts|vivified|vivify_watch_mismatch):\s+(\d+)", re.M)


def diagnostico(args):
    rutas = {os.path.basename(i): i for b in args.bench for i in find_instances(b)}
    nombres = [ln.strip() for ln in open(args.lista) if ln.strip() and not ln.startswith("#")]
    sha = sha1_of(args.kissat)
    previas = filas_completas(args.out, CAMPOS)
    hechas = {r["instance"] for r in previas}
    with EscritorDuradero(args.out, CAMPOS, previas) as ed:
        for n, nombre in enumerate(nombres, 1):
            if nombre in hechas:
                continue
            p = subprocess.run([args.kissat, "-n", "--statistics", "--seed=42",
                                f"--conflicts={args.conflicts}", "--vivifywatchfix=0",
                                rutas[nombre]], capture_output=True, text=True, errors="replace")
            st = dict(STAT.findall(p.stdout))
            if "vivify_watch_mismatch" not in st and "vivified" in st:
                st["vivify_watch_mismatch"] = "0"   # Kissat no imprime contadores a 0
            fila = {"instance": nombre, "exit_code": p.returncode, "kissat_sha1": sha[:12],
                    **{k: st.get(k, "") for k in ("conflicts", "vivified", "vivify_watch_mismatch")}}
            ed.escribir(fila)
            print(f"[{n}/{len(nombres)}] {nombre[:34]:34} vivified={fila['vivified']} "
                  f"desajustes={fila['vivify_watch_mismatch']}", flush=True)


def analizar(args):
    filas = [r for r in csv.DictReader(open(args.csv)) if r["vivified"]]
    viv = sum(int(r["vivified"]) for r in filas)
    mis = sum(int(r["vivify_watch_mismatch"] or 0) for r in filas)
    con = sum(1 for r in filas if int(r["vivify_watch_mismatch"] or 0) > 0)
    tasa = mis / viv if viv else 0.0
    print(f"instancias con estadísticas: {len(filas)}; con algún desajuste: {con}")
    print(f"desajustes / cláusulas vivificadas: {mis} / {viv} = {100 * tasa:.3f} %")
    pasa = tasa >= 0.001 and con >= 4
    print("DECISIÓN (etapa 0):", "PASA al A/B en dos etapas" if pasa else
          "se cierra: el desajuste es demasiado raro para medirse en PAR-2")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("diagnostico")
    d.add_argument("--kissat", required=True)
    d.add_argument("--lista", required=True)
    d.add_argument("--bench", nargs="+", required=True)
    d.add_argument("--out", required=True)
    d.add_argument("--conflicts", type=int, default=100000)
    d.set_defaults(f=diagnostico)
    a = sub.add_parser("analizar")
    a.add_argument("csv")
    a.set_defaults(f=analizar)
    args = ap.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
