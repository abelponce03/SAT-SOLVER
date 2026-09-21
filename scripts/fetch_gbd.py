#!/usr/bin/env python3
"""
fetch_gbd.py - descarga instancias de la Global Benchmark Database (GBD) por
hash, usando el endpoint público https://benchmark-database.de/file/<hash>.

Los nombres de instancia del estudio de tesis SON hashes GBD, así que se pueden
recuperar directamente sin la máquina local del autor. CaDiCaL lee .cnf.xz de
forma nativa, así que se guardan comprimidas.

Entrada: un CSV con al menos la columna `hash` (opcionalmente `group` para
organizar en subcarpetas). Salida: <outdir>/<group>/<hash>.cnf.xz

Uso:
  python3 fetch_gbd.py --list results/phase1_download_list.csv --out benchmarks/downloaded/gbd
  python3 fetch_gbd.py --hash <hash> --out /tmp/x        # una sola
"""
import argparse
import csv
import os
import subprocess
import sys
import time
import urllib.request

BASE = "https://benchmark-database.de/file/"


def fetch(h, dest, timeout=120):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return "skip"
    tmp = dest + ".part"
    try:
        with urllib.request.urlopen(BASE + h, timeout=timeout) as r:
            data = r.read()
        if not data:
            return "empty"
        with open(tmp, "wb") as f:
            f.write(data)
        # verificar integridad xz
        if subprocess.run(["xz", "-t", tmp], capture_output=True).returncode != 0:
            os.remove(tmp)
            return "bad-xz"
        os.rename(tmp, dest)
        return "ok"
    except Exception as e:
        if os.path.exists(tmp):
            os.remove(tmp)
        return f"error:{type(e).__name__}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", help="CSV con columna 'hash' (y opcional 'group')")
    ap.add_argument("--hash", help="descargar un único hash")
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    jobs = []
    if args.hash:
        jobs.append((args.hash, ""))
    elif args.list:
        with open(args.list) as f:
            for row in csv.DictReader(f):
                jobs.append((row["hash"].strip(), row.get("group", "").strip()))
    else:
        sys.exit("pasa --list o --hash")

    tally = {}
    total_bytes = 0
    t0 = time.time()
    for i, (h, grp) in enumerate(jobs, 1):
        d = os.path.join(args.out, grp) if grp else args.out
        os.makedirs(d, exist_ok=True)
        dest = os.path.join(d, h + ".cnf.xz")
        res = fetch(h, dest, args.timeout)
        tally[res] = tally.get(res, 0) + 1
        if res in ("ok", "skip") and os.path.exists(dest):
            total_bytes += os.path.getsize(dest)
        print(f"[{i:3d}/{len(jobs)}] {grp:8s} {h}  -> {res}")

    print(f"\nresumen: {tally}")
    print(f"tamaño total: {total_bytes/1e6:.1f} MB   tiempo: {time.time()-t0:.0f}s")
    fails = sum(v for k, v in tally.items() if k not in ("ok", "skip"))
    if fails:
        print(f"ADVERTENCIA: {fails} descargas fallaron")
        sys.exit(1)


if __name__ == "__main__":
    main()
