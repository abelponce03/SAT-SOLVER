#!/usr/bin/env python3
"""
perfil_costes.py — ¿en qué gasta el tiempo LabeSAT? (EXP-016, descriptivo)

Por instancia, mide:

  1. `xz_s`: tiempo de descomprimir la CNF (`xz -dc > /dev/null`), el coste
     que la tubería de simetrías paga una vez más que kissat solo;
  2. el perfil por fases de kissat (`--profile=N`, temporizadores internos de
     Kissat, tiempo de proceso): una columna por fase, en segundos.

Escribe una fila por (instancia, fase) en `--out` (formato largo), con
escritura duradera y reanudación por instancia (ADR-0008).

Uso:
  python3 scripts/perfil_costes.py --lista results/exp016/muestra.txt \\
      --bench bench/tesis-dev bench/calib bench/calib2 \\
      --out results/exp016/perfil.csv --timeout 200 --profile 3 --seed 42
"""
import argparse
import os
import re
import resource
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checkpoint import EscritorDuradero, filas_completas  # noqa: E402
from run_experiment import find_instances, sha1_of  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CAMPOS = ["instance", "family", "status", "exit_code", "xz_s", "wall_s", "fase",
          "segundos", "porcentaje", "conflicts", "propagations", "kissat_sha1",
          "profile", "timeout", "conflicts_budget"]
FASE = re.compile(r"^c\s+([\d.]+)\s+([\d.]+)\s*%\s+(\w+)\s*$")
STAT = re.compile(r"^c (conflicts|propagations):\s+(\d+)")


def tope_memoria(gb):
    def f():
        b = int(gb * (1 << 30))
        resource.setrlimit(resource.RLIMIT_AS, (b, b))
    return f


def medir_xz(path):
    if not path.endswith(".xz"):
        return 0.0
    t0 = time.monotonic()
    subprocess.run(["xz", "-dc", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return time.monotonic() - t0


def perfilar(kissat, inst, args):
    presupuesto = f"--conflicts={args.conflicts}" if args.conflicts else f"--time={args.timeout}"
    cmd = [kissat, f"--seed={args.seed}", presupuesto, f"--profile={args.profile}", "-n", inst]
    t0 = time.monotonic()
    p = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                       preexec_fn=tope_memoria(args.mem_gb),
                       timeout=(args.timeout if not args.conflicts else 3600) + 120)
    wall = time.monotonic() - t0
    fases, stats, dentro = [], {}, False
    for line in p.stdout.splitlines():
        if "[ profiling ]" in line:
            dentro = True
            continue
        if dentro and line.startswith("c ----"):
            dentro = False
        if dentro:
            m = FASE.match(line)
            if m:
                fases.append((m.group(3), float(m.group(1)), float(m.group(2))))
        m = STAT.match(line)
        if m:
            stats[m.group(1)] = int(m.group(2))
    estado = {10: "SAT", 20: "UNSAT", 0: "UNKNOWN"}.get(p.returncode, "ERROR")
    return estado, p.returncode, wall, fases, stats


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--lista", required=True)
    ap.add_argument("--bench", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--kissat", default=os.path.join(ROOT, "solver", "kissat", "build", "kissat"))
    ap.add_argument("--timeout", type=int, default=200)
    ap.add_argument("--profile", type=int, default=3)
    ap.add_argument("--conflicts", type=int, default=0,
                    help="presupuesto determinista de conflictos en vez de --timeout (mismo trabajo "
                         "en dos corridas: sirve para medir el sobrecoste de los temporizadores)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--mem-gb", type=float, default=6)
    args = ap.parse_args()

    quiero = [l.strip() for l in open(args.lista) if l.strip() and not l.startswith("#")]
    rutas = {os.path.basename(i): i for b in args.bench for i in find_instances(b)}
    faltan = [q for q in quiero if q not in rutas]
    if faltan:
        sys.exit(f"faltan en los bancos: {faltan[:5]}…")
    previas = filas_completas(args.out, CAMPOS)
    hechas = {r["instance"] for r in previas}
    sha = sha1_of(args.kissat)
    with EscritorDuradero(args.out, CAMPOS, previas) as ed:
        for n, q in enumerate(quiero, 1):
            if q in hechas:
                continue
            if sha1_of(args.kissat) != sha:
                sys.exit("ABORTADO: el binario cambió a mitad de la tanda")
            inst = rutas[q]
            xz = medir_xz(inst)
            estado, rc, wall, fases, stats = perfilar(args.kissat, inst, args)
            fam = os.path.basename(os.path.dirname(inst))
            comunes = dict(instance=q, family=fam, status=estado, exit_code=rc,
                           xz_s=f"{xz:.3f}", wall_s=f"{wall:.3f}",
                           conflicts=stats.get("conflicts", ""),
                           propagations=stats.get("propagations", ""),
                           kissat_sha1=sha[:12], profile=args.profile, timeout=args.timeout,
                           conflicts_budget=args.conflicts or "")
            filas = [dict(comunes, fase=f, segundos=s, porcentaje=pc) for f, s, pc in fases]
            if not filas:
                filas = [dict(comunes, fase="(sin perfil)", segundos="", porcentaje="")]
            for f in filas:        # la instancia entera, o nada
                ed.w.writerow(f)
            ed.persistir()
            print(f"[{n}/{len(quiero)}] {estado:7} {wall:7.1f}s xz {xz:5.1f}s {q[:12]} ({fam})",
                  flush=True)


if __name__ == "__main__":
    main()
