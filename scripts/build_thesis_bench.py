#!/usr/bin/env python3
"""
build_thesis_bench.py — integra el banco industrial de la tesis del director.

El banco (unas 1900 instancias `.cnf.xz` en 9 familias industriales) vive
FUERA del repositorio: son varios GB y no son nuestras. Este guion:

  1. recorre las instancias locales y comprueba la integridad de cada `.xz`;
  2. cruza cada instancia con los resultados de Kissat de la tesis
     (`results_enriched.csv`: 3 semillas, T = 800 s);
  3. asigna un ESTRATO de dificultad según esos resultados y una PARTICIÓN
     dev/test estratificada, determinista y reproducible (ADR-0003 §2);
  4. escribe dos ficheros versionados, pequeños y suficientes para reproducir
     todo lo demás:
       - bench/tesis.list.csv                 una fila por instancia local
       - results/tesis-kissat.reference.csv   una fila por corrida de Kissat
  5. con --links, crea bench/tesis-dev/ y bench/tesis-test/ (ignorados por
     git) con enlaces simbólicos por familia, para usarlos con los arneses.

Reglas de partición (fijadas ANTES de correr LabeSAT en este banco):
  - solo entran en dev/test las instancias con referencia de Kissat y un `.xz`
    íntegro;
  - dentro de cada (familia, estrato) se ordena por md5(hash + SAL) y se
    alternan dev/test: la mitad a cada lado, sin mirar ningún resultado nuevo;
  - una instancia que ya esté en bench/test.list.csv (banco reservado del
    proyecto) va SIEMPRE a tesis-test;
  - las instancias sin referencia de Kissat forman la 'reserva': no hay
    base con la que compararlas sin correr Kissat de nuevo.

Uso:
  python3 scripts/build_thesis_bench.py                     # listas + referencia
  python3 scripts/build_thesis_bench.py --links             # y los enlaces
  python3 scripts/build_thesis_bench.py --tesis-dir RUTA    # si no está en ../benchmark

Por defecto el directorio de la tesis es $LABESAT_TESIS_DIR o, si no existe,
`benchmark/` junto al checkout principal del repositorio.
"""
import argparse
import concurrent.futures as cf
import csv
import hashlib
import os
import subprocess
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SAL = "labesat-tesis-2026-09-24"
T_TESIS = 800.0
SEMILLAS = (42, 123, 777)


def tesis_dir_por_defecto():
    env = os.environ.get("LABESAT_TESIS_DIR")
    if env:
        return env
    # En un worktree, el checkout principal está donde vive el .git común.
    try:
        comun = subprocess.run(["git", "-C", ROOT, "rev-parse", "--git-common-dir"],
                               capture_output=True, text=True, check=True).stdout.strip()
        principal = os.path.dirname(os.path.abspath(os.path.join(ROOT, comun)))
    except (subprocess.CalledProcessError, FileNotFoundError):
        principal = ROOT
    return os.path.join(principal, "benchmark")


def xz_integro(ruta):
    r = subprocess.run(["nice", "-n", "19", "xz", "-t", ruta], capture_output=True)
    return ruta, r.returncode == 0


def estrato(filas):
    """Estrato de dificultad a partir de las 3 corridas de Kissat de la tesis."""
    resueltas = filas[filas.result.isin(["SAT", "UNSAT"])]
    n = len(resueltas)
    if n == 0:
        return "dura"
    if n < len(filas):
        return "inestable"
    tmax = resueltas.time.max()
    if tmax < 10:
        return "trivial"
    if tmax < 100:
        return "facil"
    return "media"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--tesis-dir", default=tesis_dir_por_defecto())
    ap.add_argument("--links", action="store_true",
                    help="crear bench/tesis-dev y bench/tesis-test con enlaces simbólicos")
    ap.add_argument("--jobs", type=int, default=4, help="procesos para `xz -t`")
    args = ap.parse_args()

    ind = os.path.join(args.tesis_dir, "industrial")
    raw = os.path.join(args.tesis_dir, "results", "raw", "results_enriched.csv")
    feats = os.path.join(args.tesis_dir, "results", "stats", "instance_features.csv")
    meta = os.path.join(ind, "metadata.csv")
    for p in (ind, raw):
        if not os.path.exists(p):
            sys.exit(f"no encuentro {p}; usa --tesis-dir o LABESAT_TESIS_DIR")

    # 1. instancias locales e integridad
    locales = {}
    for fam in sorted(os.listdir(ind)):
        d = os.path.join(ind, fam)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".cnf.xz"):
                locales[f.split(".")[0]] = (fam, os.path.join(d, f))
    print(f"== {len(locales)} instancias locales en {ind}")
    print(f"== comprobando integridad de los .xz con {args.jobs} procesos (nice)")
    integro = {}
    with cf.ThreadPoolExecutor(args.jobs) as ex:
        for ruta, ok in ex.map(xz_integro, [p for _, p in locales.values()]):
            integro[os.path.basename(ruta).split(".")[0]] = ok
    print(f"   dañadas: {sum(not v for v in integro.values())}")

    # 2. referencia de Kissat
    df = pd.read_csv(raw, low_memory=False)
    k = df[df.solver == "kissat"].copy()
    k["hash"] = k.instance.str.split(".").str[0]
    ref = k[["hash", "family", "seed", "result", "time", "conflicts", "decisions",
             "propagations", "returncode", "__source__"]].rename(columns={"__source__": "maquina"})
    ref = ref.sort_values(["family", "hash", "seed"])
    out_ref = os.path.join(ROOT, "results", "tesis-kissat.reference.csv")
    ref.to_csv(out_ref, index=False, float_format="%.3f")
    print(f"== {out_ref}: {len(ref)} corridas de {ref.hash.nunique()} instancias")

    md = pd.read_csv(meta).set_index("hash") if os.path.exists(meta) else pd.DataFrame()
    ft = pd.read_csv(feats) if os.path.exists(feats) else pd.DataFrame()
    if len(ft):
        ft["hash"] = ft.instance.str.split(".").str[0]
        ft = ft.set_index("hash")
    reservado = set(pd.read_csv(os.path.join(ROOT, "bench", "test.list.csv")).hash)

    # 3. estrato y partición
    filas = []
    kv = {h: g for h, g in k.groupby("hash")}
    for h, (fam, _) in locales.items():
        g = kv.get(h)
        valida = g is not None and not (g.result == "CORRUPT_XZ").any()
        r = {"hash": h, "group": fam, "family": fam, "xz_ok": int(integro[h]),
             "kissat_ref": int(valida)}
        if valida:
            res = g[g.result.isin(["SAT", "UNSAT"])]
            r.update(k_resueltas=len(res),
                     k_resultado=res.result.iloc[0] if len(res) else "",
                     k_t_min=g.time.min(), k_t_med=g.time.median(), k_t_max=g.time.max(),
                     dificultad=estrato(g))
        else:
            r.update(k_resueltas="", k_resultado="", k_t_min="", k_t_med="", k_t_max="",
                     dificultad="sin-ref" if g is None else "danada")
        if h in md.index:
            r.update(gbd_family=md.at[h, "gbd_family"], track_main=md.at[h, "track_main"],
                     original_filename=md.at[h, "original_filename"])
        if len(ft) and h in ft.index:
            r.update(n_vars=int(ft.at[h, "n_vars"]), n_clauses=int(ft.at[h, "n_clauses"]))
        filas.append(r)
    t = pd.DataFrame(filas)
    t["particion"] = "reserva"
    t.loc[(t.kissat_ref == 0) & (t.dificultad == "danada"), "particion"] = "excluida"
    t.loc[t.xz_ok == 0, "particion"] = "excluida"
    elegibles = t[(t.kissat_ref == 1) & (t.xz_ok == 1)].copy()
    elegibles["orden"] = [hashlib.md5((h + SAL).encode()).hexdigest() for h in elegibles.hash]
    for _, g in elegibles.groupby(["family", "dificultad"]):
        g = g.sort_values("orden")
        for i, idx in enumerate(g.index):
            t.at[idx, "particion"] = "dev" if i % 2 == 0 else "test"
    t.loc[t.hash.isin(reservado) & t.particion.isin(["dev"]), "particion"] = "test"

    cols = ["hash", "group", "family", "particion", "dificultad", "xz_ok", "kissat_ref",
            "k_resueltas", "k_resultado", "k_t_min", "k_t_med", "k_t_max",
            "n_vars", "n_clauses", "gbd_family", "track_main", "original_filename"]
    t = t.reindex(columns=cols).sort_values(["family", "hash"])
    out = os.path.join(ROOT, "bench", "tesis.list.csv")
    t.to_csv(out, index=False, float_format="%.3f", quoting=csv.QUOTE_MINIMAL)
    print(f"== {out}")
    print(pd.crosstab(t.family, t.particion, margins=True).to_string())
    print(pd.crosstab(t.dificultad, t.particion, margins=True).to_string())

    # 5. enlaces
    if args.links:
        for part in ("dev", "test"):
            base = os.path.join(ROOT, "bench", f"tesis-{part}")
            for _, r in t[t.particion == part].iterrows():
                d = os.path.join(base, r.family)
                os.makedirs(d, exist_ok=True)
                dst = os.path.join(d, f"{r.hash}.cnf.xz")
                if not os.path.lexists(dst):
                    os.symlink(locales[r.hash][1], dst)
            print(f"== {base}: {(t.particion == part).sum()} enlaces")


if __name__ == "__main__":
    main()
