#!/usr/bin/env python3
"""
run_experiment.py — ejecuta un solver sobre un banco de instancias y registra
una fila por corrida, con todo lo necesario para que el experimento sea
reproducible y auditable (ADR-0003).

Dos modos de presupuesto:

  * TIEMPO (por defecto): `--timeout T`. Usa el límite interno de Kissat
    (`--time=T`), que termina limpiamente con `s UNKNOWN` y **aun así imprime
    las estadísticas** — a diferencia de un `timeout(1)` externo, que las
    pierde. Se añade igualmente una guarda externa por si el solver se cuelga.

  * CONFLICTOS: `--conflicts N`. Presupuesto determinista: con seed fija, dos
    binarios comparados bajo el mismo presupuesto de conflictos dan resultados
    independientes del ruido de la máquina. Es el cribado barato del ADR-0003 §1.

Uso típico:
    python3 scripts/run_experiment.py \\
        --solver solver/kissat/build/kissat --bench bench/dev \\
        --out results/baseline_dev.csv --timeout 300 --seeds 1,2,3 \\
        --label kissat-4.0.4-vanilla

A/B (mismo binario, la feature detrás de una opción — ADR-0002 §3):
    ... --label mod --opts "--mifeature=1"
"""
import argparse
import csv
import hashlib
import json
import math
import os
import platform
import re
import resource
import shutil
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone

CSV_FIELDS = [
    "label", "instance", "family", "seed", "status", "exit_code",
    "wall_s", "cpu_s", "max_rss_mb",
    "conflicts", "decisions", "propagations", "restarts", "rephased",
    "budget_kind", "budget_value", "opts", "instance_sha1", "started_at",
]

# Extensiones que Kissat descomprime por sí solo (vía xz/gzip/bzip2/7z externos).
BENCH_EXTS = (".cnf", ".cnf.xz", ".cnf.gz", ".cnf.bz2", ".dimacs")

STAT_PATTERNS = {
    "conflicts": re.compile(r"^c conflicts:\s+(\d+)"),
    "decisions": re.compile(r"^c decisions:\s+(\d+)"),
    "propagations": re.compile(r"^c propagations:\s+(\d+)"),
    "restarts": re.compile(r"^c restarts:\s+(\d+)"),
    "rephased": re.compile(r"^c rephased:\s+(\d+)"),
}


def sha1_of(path, limit=None):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            if limit and h.block_size and f.tell() > limit:
                break
    return h.hexdigest()


def find_instances(bench_dir):
    out = []
    for root, _dirs, files in os.walk(bench_dir):
        for name in sorted(files):
            if name.endswith(BENCH_EXTS):
                out.append(os.path.join(root, name))
    return sorted(out)


def family_of(path, bench_dir):
    """La familia es el subdirectorio inmediato bajo el banco ('-' si es plano)."""
    rel = os.path.relpath(path, bench_dir)
    parts = rel.split(os.sep)
    return parts[0] if len(parts) > 1 else "-"


def parse_stats(text):
    stats = {k: "" for k in STAT_PATTERNS}
    for line in text.splitlines():
        for key, pat in STAT_PATTERNS.items():
            if stats[key] == "":
                m = pat.match(line)
                if m:
                    stats[key] = int(m.group(1))
    return stats


def run_one(solver, instance, seed, budget_kind, budget_value, extra_opts, hard_grace):
    """Ejecuta una corrida y devuelve (status, exit_code, wall_s, cpu_s, rss_mb, stats)."""
    cmd = [solver, "-n", "-s", f"--seed={seed}"]
    if budget_kind == "time":
        # Kissat solo acepta segundos enteros en --time.
        cmd.append(f"--time={int(math.ceil(budget_value))}")
        hard_limit = budget_value * 1.25 + hard_grace
    else:
        cmd.append(f"--conflicts={budget_value}")
        hard_limit = None
    cmd.extend(extra_opts)
    cmd.append(instance)

    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    t0 = time.monotonic()
    killed = False
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=hard_limit)
        out, code = proc.stdout, proc.returncode
    except subprocess.TimeoutExpired as e:
        killed = True
        out, code = (e.stdout or ""), -signal.SIGKILL
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
    wall = time.monotonic() - t0
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (after.ru_utime + after.ru_stime) - (before.ru_utime + before.ru_stime)
    rss_mb = after.ru_maxrss / 1024.0  # Linux: ru_maxrss viene en KiB

    if code == 10:
        status = "SAT"
    elif code == 20:
        status = "UNSAT"
    elif killed:
        status = "HARDKILL"      # el límite interno no respondió: hay que mirarlo
    elif code == 0:
        status = "TIMEOUT" if budget_kind == "time" else "BUDGET"
    else:
        status = "ERROR"

    return status, code, wall, cpu, rss_mb, parse_stats(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solver", required=True, help="ruta del binario")
    ap.add_argument("--bench", required=True, help="directorio de instancias (se recorre recursivamente)")
    ap.add_argument("--out", required=True, help="CSV de salida")
    ap.add_argument("--label", default=None, help="etiqueta de la configuración (columna 'label')")
    ap.add_argument("--timeout", type=float, default=None, help="presupuesto de tiempo por corrida, en segundos")
    ap.add_argument("--conflicts", type=int, default=None, help="presupuesto determinista de conflictos")
    ap.add_argument("--seeds", default="1", help="lista separada por comas, p.ej. 1,2,3")
    ap.add_argument("--opts", default="", help="opciones extra para el solver, entre comillas")
    ap.add_argument("--limit", type=int, default=None, help="usar solo las primeras N instancias (pruebas rápidas)")
    ap.add_argument("--append", action="store_true", help="añadir al CSV en vez de sobrescribir")
    args = ap.parse_args()

    if (args.timeout is None) == (args.conflicts is None):
        ap.error("elige exactamente un presupuesto: --timeout o --conflicts")

    budget_kind = "time" if args.timeout is not None else "conflicts"
    budget_value = args.timeout if args.timeout is not None else args.conflicts
    label = args.label or os.path.basename(args.solver)
    extra_opts = args.opts.split() if args.opts else []
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]

    if not os.access(args.solver, os.X_OK):
        sys.exit(f"ERROR: solver no ejecutable: {args.solver}")
    instances = find_instances(args.bench)
    if args.limit:
        instances = instances[: args.limit]
    if not instances:
        sys.exit(f"ERROR: no hay instancias en {args.bench}")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)

    # --- Metadatos del experimento: sin esto una corrida no es reproducible ---
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    def git(*a):
        try:
            return subprocess.run(["git", "-C", repo, *a], capture_output=True,
                                  text=True, check=True).stdout.strip()
        except Exception:
            return "?"
    meta = {
        "label": label, "solver": os.path.abspath(args.solver),
        "solver_version": subprocess.run([args.solver, "--version"], capture_output=True,
                                         text=True).stdout.strip(),
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty": bool(git("status", "--porcelain")),
        "bench": os.path.abspath(args.bench), "n_instances": len(instances),
        "seeds": seeds, "budget_kind": budget_kind, "budget_value": budget_value,
        "opts": args.opts, "host": socket.gethostname(), "nproc": os.cpu_count(),
        "platform": platform.platform(), "loadavg": os.getloadavg(),
        "cc": (shutil.which("gcc") or "?"),
        "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    meta_path = os.path.splitext(args.out)[0] + ".meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    mode = "a" if args.append and os.path.exists(args.out) else "w"
    with open(args.out, mode, newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if mode == "w":
            w.writeheader()

        total = len(instances) * len(seeds)
        done = 0
        print(f"== {label}: {len(instances)} instancias × {len(seeds)} seeds "
              f"= {total} corridas · presupuesto {budget_kind}={budget_value}")
        print(f"{'instancia':<42} {'seed':>4} {'estado':<8} {'cpu(s)':>9} {'confl':>10}")
        print("-" * 78)

        for inst in instances:
            sha = sha1_of(inst)
            fam = family_of(inst, args.bench)
            for seed in seeds:
                started = datetime.now(timezone.utc).isoformat(timespec="seconds")
                status, code, wall, cpu, rss, stats = run_one(
                    args.solver, inst, seed, budget_kind, budget_value,
                    extra_opts, hard_grace=30.0)
                done += 1
                row = {
                    "label": label, "instance": os.path.basename(inst), "family": fam,
                    "seed": seed, "status": status, "exit_code": code,
                    "wall_s": f"{wall:.3f}", "cpu_s": f"{cpu:.3f}",
                    "max_rss_mb": f"{rss:.1f}",
                    "budget_kind": budget_kind, "budget_value": budget_value,
                    "opts": args.opts, "instance_sha1": sha, "started_at": started,
                    **stats,
                }
                w.writerow(row)
                f.flush()
                print(f"{os.path.basename(inst):<42} {seed:>4} {status:<8} "
                      f"{cpu:>9.3f} {str(stats['conflicts']):>10}")

    print(f"\nListo: {args.out}  (metadatos en {os.path.basename(meta_path)})")
    print(f"Analiza con:  python3 scripts/par2.py {args.out}")


if __name__ == "__main__":
    main()
