#!/usr/bin/env python3
"""
compare_integrada.py — EXP-012: ¿es `kissat --symmetry` (satsuma dentro del
binario, ADR-0007) equivalente a la tubería `solver/labesat --symmetry`
(satsuma externo + kissat, EXP-007)?

Por cada instancia, todo con medidas DETERMINISTAS (no dependen de la carga):
  1. CNF intermedia: SHA-1 de la salida de `tools/satsuma` (tubería) frente a
     la del binario integrado (LABESAT_SYMM_KEEP=1).  Si satsuma no se aplica
     en alguna de las dos, se anota.
  2. Trayectoria: el kissat de la tubería sobre la CNF de satsuma frente al
     binario integrado sobre la instancia, los dos con --conflicts=N y
     --seed=1: estado, conflictos, decisiones y propagaciones.
  3. Seguridad del integrado: modelo contra la CNF original (SAT) o prueba
     con los dos dsr-trim (UNSAT).

Uso:
  python3 scripts/compare_integrada.py --bench bench/symm2026 \\
      --integrado solver/kissat/build-symm/kissat \\
      --kissat solver/kissat/build/kissat --conflicts 100000 \\
      --out results/exp012/equivalencia.csv
"""
import argparse
import csv
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_experiment import find_instances, sha1_of  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SATSUMA_ARGS = ["--silent", "--full-skip-limit", "100000000", "--add-reduced-as-unit", "--bsr"]
DSRS = [os.path.join(ROOT, "tools", d) for d in ("dsr-trim", "dsr-trim-sc2026")]
VERIFY = os.path.join(ROOT, "scripts", "verify_model.py")
STAT = re.compile(r"^c (conflicts|decisions|propagations):\s+(\d+)", re.M)


def sha(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest() if os.path.exists(path) else ""


def estado(code):
    return {10: "SAT", 20: "UNSAT"}.get(code, "UNKNOWN" if code == 0 else f"ERROR({code})")


def stats(text):
    return {k: int(v) for k, v in STAT.findall(text)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bench", required=True, nargs="+")
    ap.add_argument("--integrado", required=True)
    ap.add_argument("--kissat", required=True, help="kissat de la tubería")
    ap.add_argument("--satsuma", default=os.path.join(ROOT, "tools", "satsuma"))
    ap.add_argument("--conflicts", type=int, default=100000)
    ap.add_argument("--satsuma-timeout", type=float, default=60.0)
    ap.add_argument("--check-timeout", type=float, default=600.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    shas = {p: sha1_of(p) for p in (args.integrado, args.kissat, args.satsuma)}
    insts = [i for b in args.bench for i in find_instances(b)]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    campos = ["instance", "family", "sb_sha_tuberia", "sb_sha_integrado", "cnf_igual",
              "estado_tuberia", "estado_integrado", "conflicts_t", "conflicts_i",
              "decisions_t", "decisions_i", "propagations_t", "propagations_i",
              "trayectoria_igual", "seguridad"]
    with open(args.out, "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=campos)
        w.writeheader()
        for n, inst in enumerate(insts, 1):
            for p, h in shas.items():
                if sha1_of(p) != h:
                    sys.exit(f"ABORTADO: {p} cambió a mitad de la tanda")
            with tempfile.TemporaryDirectory() as tmp:
                env = {**os.environ, "TMPDIR": tmp}
                plain = inst
                if inst.endswith(".xz"):
                    plain = os.path.join(tmp, "orig.cnf")
                    with open(plain, "wb") as f:
                        subprocess.run(["xz", "-dc", inst], stdout=f, check=True)
                # 1a. tubería: satsuma externo
                sb = os.path.join(tmp, "sb_ref.cnf")
                try:
                    rc = subprocess.run([args.satsuma, "fix", plain, *SATSUMA_ARGS,
                                         "--out-file", sb], stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL,
                                        timeout=args.satsuma_timeout).returncode
                except subprocess.TimeoutExpired:
                    rc = "TOPE"
                aplica_t = rc == 0 and os.path.getsize(sb) > 0 if os.path.exists(sb) else False
                sha_t = sha(sb) if aplica_t else ""
                # 2a. tubería: kissat sobre la CNF de satsuma (o la original, respaldo)
                entrada_t = sb if aplica_t else plain
                pt = subprocess.run([args.kissat, "-n", f"--conflicts={args.conflicts}",
                                     "--seed=1", entrada_t], capture_output=True, text=True, errors="replace")
                st_t = stats(pt.stdout)
                # 1b + 2b. integrado, conservando la CNF intermedia y con prueba
                proof = os.path.join(tmp, "int.proof")
                pi = subprocess.run([args.integrado, "--symmetry", f"--conflicts={args.conflicts}",
                                     "--seed=1", inst, proof], capture_output=True, text=True, errors="replace",
                                    env={**env, "LABESAT_SYMM_KEEP": "1"})
                m = re.search(r"conservados en (\S+)", pi.stderr)
                sha_i = sha(os.path.join(m.group(1), "sb.cnf")) if m else ""
                st_i = stats(pi.stdout)
                # 3. seguridad del integrado
                seg = "SALTADA"
                if pi.returncode == 10:
                    mod = os.path.join(tmp, "model")
                    open(mod, "w").write(pi.stdout)
                    ok = subprocess.run([sys.executable, VERIFY, "--model", mod, plain],
                                        capture_output=True).returncode == 0
                    seg = "OK" if ok else "FALLO"
                elif pi.returncode == 20:
                    try:
                        ok = all(any(l.startswith("s VERIFIED") for l in subprocess.run(
                            [d, plain, proof], capture_output=True, text=True, errors="replace",
                            timeout=args.check_timeout).stdout.splitlines()) for d in DSRS)
                        seg = "OK" if ok else "FALLO"
                    except subprocess.TimeoutExpired:
                        seg = "TOPE"
                if m:
                    shutil.rmtree(m.group(1), ignore_errors=True)
            igual_t = (estado(pt.returncode) == estado(pi.returncode) and
                       all(st_t.get(k) == st_i.get(k) for k in ("conflicts", "decisions", "propagations")))
            fila = {"instance": os.path.basename(inst),
                    "family": os.path.basename(os.path.dirname(inst)),
                    "sb_sha_tuberia": sha_t, "sb_sha_integrado": sha_i,
                    "cnf_igual": sha_t == sha_i,
                    "estado_tuberia": estado(pt.returncode), "estado_integrado": estado(pi.returncode),
                    "conflicts_t": st_t.get("conflicts", ""), "conflicts_i": st_i.get("conflicts", ""),
                    "decisions_t": st_t.get("decisions", ""), "decisions_i": st_i.get("decisions", ""),
                    "propagations_t": st_t.get("propagations", ""),
                    "propagations_i": st_i.get("propagations", ""),
                    "trayectoria_igual": igual_t, "seguridad": seg}
            w.writerow(fila)
            fo.flush()
            print(f"[{n:>3}/{len(insts)}] {fila['instance'][:34]:<34} cnf={'=' if fila['cnf_igual'] else '≠'} "
                  f"tray={'=' if igual_t else '≠'} {fila['estado_integrado']:<7} seg={seg}", flush=True)
    filas = list(csv.DictReader(open(args.out)))
    cnf = sum(r["cnf_igual"] == "True" for r in filas)
    tray = sum(r["trayectoria_igual"] == "True" for r in filas)
    fallos = sum(r["seguridad"] == "FALLO" for r in filas)
    print(f"\nCNF intermedia igual: {cnf}/{len(filas)}; trayectoria igual: {tray}/{len(filas)}; "
          f"fallos de seguridad: {fallos}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
