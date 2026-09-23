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
from concurrent.futures import ThreadPoolExecutor
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
import tempfile
import sys
import time
from datetime import datetime, timezone

CSV_FIELDS = [
    "label", "instance", "family", "seed", "status", "exit_code",
    "wall_s", "cpu_s", "max_rss_mb",
    "conflicts", "decisions", "propagations", "restarts", "rephased",
    "budget_kind", "budget_value", "opts", "instance_sha1", "started_at",
    "parallel_jobs",
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


def run_one(solver, instance, seed, budget_kind, budget_value, extra_opts, hard_grace,
            env=None):
    """Ejecuta una corrida y devuelve (status, exit_code, wall_s, cpu_s, rss_mb, stats).

    El tiempo de CPU se toma de `wait4` sobre ESTE hijo concreto (no de
    RUSAGE_CHILDREN acumulado), para que la medición siga siendo correcta
    cuando hay varias corridas en vuelo (`--jobs > 1`).

    `env`: variables de entorno que se AÑADEN a las del proceso (p. ej.
    LABESAT_SATSUMA para elegir el binario de satsuma de solver/labesat)."""
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

    t0 = time.monotonic()
    killed = False
    with tempfile.TemporaryFile() as fout:
        # Sesión propia: si hay que matar, se mata el GRUPO.  Con un guion como
        # solver/labesat, matar solo al hijo directo dejaría kissat huérfano.
        proc = subprocess.Popen(cmd, stdout=fout, stderr=subprocess.DEVNULL,
                                start_new_session=True,
                                env={**os.environ, **env} if env else None)
        deadline = (t0 + hard_limit) if hard_limit else None
        delay = 0.002
        while True:
            pid, wstatus, ru = os.wait4(proc.pid, os.WNOHANG)
            if pid:
                break
            if deadline and time.monotonic() > deadline:
                killed = True
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                pid, wstatus, ru = os.wait4(proc.pid, 0)
                break
            time.sleep(delay)
            delay = min(delay * 1.5, 0.05)
        proc.returncode = os.waitstatus_to_exitcode(wstatus)  # el hijo ya está recogido
        wall = time.monotonic() - t0
        fout.seek(0)
        out = fout.read().decode("utf-8", "replace")
    cpu = ru.ru_utime + ru.ru_stime
    rss_mb = ru.ru_maxrss / 1024.0   # en Linux ru_maxrss viene en KiB
    code = -signal.SIGKILL if killed else proc.returncode

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
    ap.add_argument("--jobs", type=int, default=1,
                    help="corridas simultáneas. >1 multiplica el rendimiento del CRIBADO, "
                         "pero contamina la medición de tiempo (contención de memoria y caché): "
                         "los CSV así generados llevan parallel_jobs>1 y NO valen como "
                         "medición final de PAR-2 (ADR-0003 §4)")
    args = ap.parse_args()

    if (args.timeout is None) == (args.conflicts is None):
        ap.error("elige exactamente un presupuesto: --timeout o --conflicts")

    budget_kind = "time" if args.timeout is not None else "conflicts"
    budget_value = args.timeout if args.timeout is not None else args.conflicts
    label = args.label or os.path.basename(args.solver)
    extra_opts = args.opts.split() if args.opts else []
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]

    solver_sha1 = sha1_of(args.solver)

    if args.jobs > 1:
        print(f"[AVISO] --jobs={args.jobs}: los tiempos quedan contaminados por contención.\n"
              f"        Vale para cribar (qué resuelve cada configuración), no para el PAR-2 final.")
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
        "solver_sha1": solver_sha1,
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty": bool(git("status", "--porcelain")),
        "bench": os.path.abspath(args.bench), "n_instances": len(instances),
        "seeds": seeds, "budget_kind": budget_kind, "budget_value": budget_value,
        "opts": args.opts, "parallel_jobs": args.jobs,
        "host": socket.gethostname(), "nproc": os.cpu_count(),
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

        sha_cache = {inst: sha1_of(inst) for inst in instances}
        tasks = [(inst, seed) for inst in instances for seed in seeds]

        def work(task):
            inst, seed = task
            # El binario NO puede cambiar a mitad de una tanda: si alguien
            # recompila mientras esto corre, las instancias medidas antes y
            # después salen de binarios distintos y el CSV mezcla dos
            # experimentos sin que se note. Pasó una vez (EXP-004) y por eso
            # esta comprobación existe.
            if sha1_of(args.solver) != solver_sha1:
                raise SystemExit(
                    f"\nABORTADO: el binario {args.solver} cambió a mitad de la "
                    f"tanda.\n   esperado {solver_sha1[:12]}, ahora "
                    f"{sha1_of(args.solver)[:12]}.\n"
                    "   Los resultados parciales mezclarían dos binarios: se "
                    "descartan.\n   No recompiles mientras haya un experimento "
                    "en curso.")
            started = datetime.now(timezone.utc).isoformat(timespec="seconds")
            status, code, wall, cpu, rss, stats = run_one(
                args.solver, inst, seed, budget_kind, budget_value,
                extra_opts, hard_grace=30.0)
            return {
                "label": label, "instance": os.path.basename(inst),
                "family": family_of(inst, args.bench),
                "seed": seed, "status": status, "exit_code": code,
                "wall_s": f"{wall:.3f}", "cpu_s": f"{cpu:.3f}",
                "max_rss_mb": f"{rss:.1f}",
                "budget_kind": budget_kind, "budget_value": budget_value,
                "opts": args.opts, "instance_sha1": sha_cache[inst],
                "started_at": started, "parallel_jobs": args.jobs, **stats,
            }

        if args.jobs > 1:
            pool = ThreadPoolExecutor(max_workers=args.jobs)
            results = pool.map(work, tasks)       # mantiene el orden de entrada
        else:
            results = map(work, tasks)

        for row in results:
            done += 1
            w.writerow(row)
            f.flush()
            print(f"{row['instance']:<42} {row['seed']:>4} {row['status']:<8} "
                  f"{float(row['cpu_s']):>9.3f} {str(row['conflicts']):>10}"
                  f"   [{done}/{total}]")
        if args.jobs > 1:
            pool.shutdown()

    print(f"\nListo: {args.out}  (metadatos en {os.path.basename(meta_path)})")
    print(f"Analiza con:  python3 scripts/par2.py {args.out}")


if __name__ == "__main__":
    main()
