#!/usr/bin/env python3
"""
scan_symmetry.py — ¿qué hace satsuma con cada instancia de un banco?

Parte 1 de EXP-014. Ejecuta SOLO satsuma, con los mismos argumentos y topes que
`solver/labesat --symmetry` (60 s, 512 MiB de CNF sin comprimir), y registra
por instancia lo que satsuma informa de sí mismo:

  - si terminó, se pasó del tope o falló (en esos casos labesat cae al
    respaldo y resuelve la CNF original);
  - generadores encontrados (dejavu_gens) y estructuras reconocidas
    (row, row_column, johnson);
  - predicados de ruptura añadidos: unidades, binarias y lexicográficos;
  - cláusulas de entrada y de salida, bytes del prefijo de la prueba;
  - tiempo total y fracción en la fase de Schreier.

`cambia` = 1 si satsuma añadió algún predicado de ruptura. Solo en esas
instancias puede la ruptura cambiar la búsqueda de kissat más allá de la
reescritura trivial (la parte 2 de EXP-014 lo comprueba con controles).

Estas columnas son también los features candidatos de B3 (EXP-009): se
calculan antes de buscar y no miran el resultado.

Uso:
  nice -n 19 python3 scripts/scan_symmetry.py --bench bench/tesis-dev \\
      --out results/exp014/satsuma.csv [--satsuma tools/satsuma] [--timeout 60]

Reanuda: si --out ya existe, salta las instancias ya registradas.
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
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CAMPOS = ["instance", "family", "status", "exit_code", "wall_s", "in_vars", "in_clauses",
          "out_vars", "out_clauses", "proof_bytes", "dejavu_gens", "avg_support",
          "row", "row_column", "johnson", "sym_units", "orbitopal_units", "sym_binary",
          "amo_binary", "sym_lex", "schreier_ms", "total_ms", "cambia",
          "satsuma_sha1", "started_at"]
STAT = re.compile(r"^c\s+(\w+)\s*=\s*([\d.]+)(?:\s+\((\w+)\s*=\s*([\d.]+)\))?")
FASE = re.compile(r"^c\s+([\d.]+)ms\s+[\d.]+%\s+(\w+)")


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cabecera(path):
    with open(path, errors="replace") as f:
        for line in f:
            if line.startswith("p"):
                p = line.split()
                return int(p[2]), int(p[3])
    return "", ""


def descomprimir(src, dst):
    if src.endswith(".xz"):
        cmd = ["xz", "-dc", src]
    elif src.endswith(".gz"):
        cmd = ["gzip", "-dc", src]
    else:
        shutil.copyfile(src, dst)
        return True
    with open(dst, "wb") as out:
        return subprocess.run(cmd, stdout=out, stderr=subprocess.DEVNULL).returncode == 0


def escanear(satsuma, cnf, tmp, timeout, maxbytes):
    fila = {}
    inp = os.path.join(tmp, "in.cnf")
    if not descomprimir(cnf, inp):
        return {"status": "ERROR-descompresion"}
    fila["in_vars"], fila["in_clauses"] = cabecera(inp)
    if os.path.getsize(inp) > maxbytes:
        return {**fila, "status": "GRANDE"}
    out, prf = os.path.join(tmp, "sb.cnf"), os.path.join(tmp, "p.sr")
    cmd = [satsuma, "fix", inp, "--full-skip-limit", "100000000", "--add-reduced-as-unit",
           "--bsr", "--out-file", out, "--proof-file", prf]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                           timeout=timeout, stdin=subprocess.DEVNULL)
        fila["wall_s"] = round(time.time() - t0, 3)
        fila["exit_code"] = r.returncode
        texto = r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return {**fila, "status": "TOPE", "wall_s": round(time.time() - t0, 3)}
    if r.returncode != 0 or not os.path.exists(out) or not os.path.getsize(out):
        return {**fila, "status": "FALLO"}
    fila["status"] = "OK"
    fila["out_vars"], fila["out_clauses"] = cabecera(out)
    fila["proof_bytes"] = os.path.getsize(prf) if os.path.exists(prf) else 0
    limpio = re.sub(r"\x1b\[[0-9;]*m", "", texto)
    mapa = {"dejavu_gens": "dejavu_gens", "row": "row", "row_column": "row_column",
            "johnson": "johnson", "symmetry_units": "sym_units",
            "symmetry_binary": "sym_binary", "symmetry_lex": "sym_lex"}
    extra = {"average_support": "avg_support", "orbitopal_units": "orbitopal_units",
             "amo_binary": "amo_binary"}
    total = 0.0
    for line in limpio.splitlines():
        m = STAT.match(line)
        if m and m.group(1) in mapa:
            fila[mapa[m.group(1)]] = m.group(2)
            if m.group(3) in extra:
                fila[extra[m.group(3)]] = m.group(4)
        m = FASE.match(line)
        if m:
            if m.group(2) == "schreier":
                fila["schreier_ms"] = m.group(1)
            if m.group(2) == "total":
                total = float(m.group(1))
    fila["total_ms"] = total or ""
    añadidos = sum(float(fila.get(k) or 0) for k in ("sym_units", "sym_binary", "sym_lex"))
    fila["cambia"] = int(añadidos > 0)
    return fila


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--bench", required=True, nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--satsuma", default=os.path.join(ROOT, "tools", "satsuma"))
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--maxbytes", type=int, default=536870912)
    args = ap.parse_args()

    insts = []
    for b in args.bench:
        for d, _, fs in os.walk(b, followlinks=True):
            for f in sorted(fs):
                if re.search(r"\.cnf(\.(xz|gz))?$", f):
                    insts.append(os.path.join(d, f))
    insts.sort()
    hechas = set()
    if os.path.exists(args.out):
        hechas = {r["instance"] for r in csv.DictReader(open(args.out))}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    nuevo = not os.path.exists(args.out)
    s1 = sha1(args.satsuma)
    with open(args.out, "a", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=CAMPOS)
        if nuevo:
            w.writeheader()
        for i, cnf in enumerate(insts, 1):
            nombre = os.path.basename(cnf)
            if nombre in hechas:
                continue
            if sha1(args.satsuma) != s1:
                sys.exit("ABORTO: el binario de satsuma cambió durante la tanda")
            tmp = tempfile.mkdtemp(prefix="scan-symm.")
            try:
                fila = escanear(args.satsuma, cnf, tmp, args.timeout, args.maxbytes)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            fila.update(instance=nombre, family=os.path.basename(os.path.dirname(cnf)),
                        satsuma_sha1=s1[:12],
                        started_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
            w.writerow(fila)
            fo.flush()
            print(f"[{i}/{len(insts)}] {fila['status']:6} cambia={fila.get('cambia', '')} "
                  f"gens={fila.get('dejavu_gens', '')} {fila.get('wall_s', '')}s {nombre}",
                  flush=True)


if __name__ == "__main__":
    main()
