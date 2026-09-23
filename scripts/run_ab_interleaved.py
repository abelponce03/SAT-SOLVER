#!/usr/bin/env python3
"""
run_ab_interleaved.py — A/B con las dos ramas INTERCALADAS instancia a instancia.

Por qué existe (ADR-0003 §4b): EXP-004 midió una deriva de ~4 % entre dos
sesiones con trayectorias de búsqueda IDÉNTICAS, y un Wilcoxon la declaró
"significativa" con p ~ 0.  Correr las dos ramas en la misma sesión no basta:
si A ocupa la primera hora y B la segunda, cualquier deriva DENTRO de la sesión
(carga, temperatura, estado de la caché) se confunde con el efecto.

Aquí cada instancia se resuelve con A y con B una detrás de otra, y el ORDEN se
alterna (A-B, B-A, A-B...) para que un sesgo de "el primero de la pareja va
más rápido" también se cancele.  Las dos corridas de una pareja se miden con
segundos de diferencia, así que comparten las condiciones de la máquina.

Además de tiempo, cada fila registra las PROPAGACIONES hasta la solución: es una
medida de esfuerzo DETERMINISTA, inmune a la deriva, que sirve para confirmar
que una diferencia de tiempo es del algoritmo y no de la máquina.

Escribe dos CSV con el mismo esquema que `run_experiment.py`, de modo que
`par2.py A.csv B.csv` funciona sin cambios.

Uso:
  python3 scripts/run_ab_interleaved.py --solver solver/kissat/build/kissat \\
      --bench bench/calib --out-a results/X/A.csv --out-b results/X/B.csv \\
      --timeout 180 --seeds 1,2 --opts-b="--modeadaptive=1"

Ojo: las opciones del solver empiezan por "--", así que van con "=" pegado
(--opts-b="--x=1"); con espacio, argparse las toma por opciones propias.
"""
import argparse
import csv
import json
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_experiment import (CSV_FIELDS, family_of, find_instances,  # noqa: E402
                            run_one, sha1_of)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solver", required=True)
    ap.add_argument("--bench", required=True, nargs="+", help="uno o varios bancos")
    ap.add_argument("--out-a", required=True)
    ap.add_argument("--out-b", required=True)
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    ap.add_argument("--opts-a", default="")
    ap.add_argument("--opts-b", default="")
    ap.add_argument("--timeout", type=float, required=True)
    ap.add_argument("--seeds", default="1")
    args = ap.parse_args()

    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    tareas = []
    for bench in args.bench:
        for inst in find_instances(bench):
            for seed in seeds:
                tareas.append((bench, inst, seed))

    sha = sha1_of(args.solver)
    ramas = {
        "A": (args.label_a, args.opts_a.split() if args.opts_a else [], args.out_a),
        "B": (args.label_b, args.opts_b.split() if args.opts_b else [], args.out_b),
    }
    ficheros, escritores = {}, {}
    for k, (_, _, out) in ramas.items():
        os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
        ficheros[k] = open(out, "w", newline="")
        escritores[k] = csv.DictWriter(ficheros[k], fieldnames=CSV_FIELDS)
        escritores[k].writeheader()

    # Metadatos de procedencia, como run_experiment.py: el ADR-0003 dice que un
    # resultado sin ellos "no se usa para nada".
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def git(*a):
        try:
            return subprocess.run(["git", "-C", repo, *a], capture_output=True,
                                  text=True, check=True).stdout.strip()
        except Exception:
            return "?"

    solver_id = subprocess.run([args.solver, "--id"], capture_output=True,
                               text=True).stdout.strip()
    head = git("rev-parse", "HEAD")
    meta = {
        "diseno": "A/B intercalado (run_ab_interleaved.py)",
        "solver": os.path.abspath(args.solver), "solver_sha1": sha,
        "solver_id": solver_id, "git_commit": head,
        "solver_id_coincide_con_head": solver_id == head,
        "git_dirty": bool(git("status", "--porcelain")),
        "solver_version": subprocess.run([args.solver, "--version"],
                                         capture_output=True, text=True).stdout.strip(),
        "benches": [os.path.abspath(b) for b in args.bench], "n_parejas": len(tareas),
        "seeds": seeds, "timeout": args.timeout,
        "rama_a": {"label": args.label_a, "opts": args.opts_a},
        "rama_b": {"label": args.label_b, "opts": args.opts_b},
        "host": socket.gethostname(), "nproc": os.cpu_count(),
        "platform": platform.platform(), "loadavg": os.getloadavg(),
        "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if solver_id != head:
        print(f"[AVISO] el binario dice --id {solver_id[:12]} y HEAD es "
              f"{head[:12]}: se compiló desde otro commit.")
    for out in (args.out_a, args.out_b):
        with open(os.path.splitext(out)[0] + ".meta.json", "w") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"== A/B intercalado: {len(tareas)} parejas (instancia × seed), "
          f"binario {sha[:12]}")
    print(f"   A = {args.label_a} [{args.opts_a or 'por defecto'}]")
    print(f"   B = {args.label_b} [{args.opts_b or 'por defecto'}]\n")

    for n, (bench, inst, seed) in enumerate(tareas, 1):
        if sha1_of(args.solver) != sha:
            sys.exit(f"\nABORTADO: el binario cambió a mitad de la tanda "
                     f"({sha[:12]} -> {sha1_of(args.solver)[:12]}). "
                     "Los parciales mezclarían dos binarios: se descartan.")
        # alternar el orden dentro de la pareja cancela el sesgo de posición
        orden = ("A", "B") if n % 2 else ("B", "A")
        resumen = {}
        for k in orden:
            label, opts, _ = ramas[k]
            started = datetime.now(timezone.utc).isoformat(timespec="seconds")
            status, code, wall, cpu, rss, stats = run_one(
                args.solver, inst, seed, "time", args.timeout, opts, hard_grace=30.0)
            escritores[k].writerow({
                "label": label, "instance": os.path.basename(inst),
                "family": family_of(inst, bench), "seed": seed,
                "status": status, "exit_code": code,
                "wall_s": f"{wall:.3f}", "cpu_s": f"{cpu:.3f}",
                "max_rss_mb": f"{rss:.1f}", "budget_kind": "time",
                "budget_value": args.timeout, "opts": " ".join(opts),
                "instance_sha1": "", "started_at": started,
                "parallel_jobs": 1, **stats,
            })
            ficheros[k].flush()
            resumen[k] = (status, cpu)
        print(f"[{n:>4}/{len(tareas)}] {os.path.basename(inst)[:34]:<34} s{seed} "
              f"A {resumen['A'][0]:<7} {resumen['A'][1]:7.1f}s | "
              f"B {resumen['B'][0]:<7} {resumen['B'][1]:7.1f}s  ({'-'.join(orden)})")

    for f in ficheros.values():
        f.close()
    print(f"\nListo. Analiza con:  python3 scripts/par2.py {args.out_a} {args.out_b}")


if __name__ == "__main__":
    main()
