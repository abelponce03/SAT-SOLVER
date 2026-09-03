#!/usr/bin/env python3
"""
normalize_cnf.py - normaliza ficheros DIMACS CNF a un formato limpio que
cualquier solver estricto (CaDiCaL incluido) parsea sin errores.

Corrige los defectos tipicos de colecciones antiguas (SATLIB, DIMACS):
  - basura final tipo `%` y `0` centinela despues de las clausulas,
  - lineas de comentario mezcladas,
  - cabecera `p cnf V C` con conteos incorrectos (se recalcula),
  - clausulas repartidas en varias lineas fisicas (se reagrupan por el 0).

Lee TODOS los tokens tras la cabecera, ignora comentarios (`c ...`), se detiene
en `%`, agrupa literales en clausulas por el delimitador 0, y reescribe con una
cabecera correcta.

Uso:
  python3 normalize_cnf.py entrada.cnf salida.cnf
  python3 normalize_cnf.py --dir <dir_entrada> --out <dir_salida> [--flatten]
"""
import argparse
import os
import sys


def normalize_text(text):
    """Devuelve (n_vars, clausulas) a partir del texto DIMACS crudo."""
    tokens = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s[0] == "c":          # comentario
            continue
        if s[0] == "p":          # cabecera declarada (la ignoramos y recalculamos)
            continue
        if s[0] == "%":          # centinela de fin -> basura, paramos
            break
        tokens.extend(s.split())

    clauses = []
    cur = []
    for tok in tokens:
        try:
            v = int(tok)
        except ValueError:
            continue  # token no numerico -> lo saltamos
        if v == 0:
            if cur:
                clauses.append(cur)
                cur = []
        else:
            cur.append(v)
    if cur:                      # ultima clausula sin 0 explicito
        clauses.append(cur)

    n_vars = 0
    for cl in clauses:
        for lit in cl:
            n_vars = max(n_vars, abs(lit))
    return n_vars, clauses


def write_clean(path, n_vars, clauses):
    with open(path, "w") as f:
        f.write(f"p cnf {n_vars} {len(clauses)}\n")
        for cl in clauses:
            f.write(" ".join(str(x) for x in cl) + " 0\n")


def normalize_file(src, dst):
    with open(src, "r", errors="ignore") as f:
        nv, cls = normalize_text(f.read())
    if not cls:
        return None
    write_clean(dst, nv, cls)
    return nv, len(cls)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?", help="fichero de entrada")
    ap.add_argument("dst", nargs="?", help="fichero de salida")
    ap.add_argument("--dir", help="normalizar todos los .cnf de un directorio (recursivo)")
    ap.add_argument("--out", help="directorio de salida (con --dir)")
    ap.add_argument("--flatten", action="store_true",
                    help="aplanar: nombre = <subdir>_<fichero> para evitar colisiones")
    args = ap.parse_args()

    if args.dir:
        if not args.out:
            sys.exit("ERROR: --dir requiere --out")
        os.makedirs(args.out, exist_ok=True)
        count = 0
        for root, _, files in os.walk(args.dir):
            for name in sorted(files):
                if not name.endswith(".cnf"):
                    continue
                src = os.path.join(root, name)
                if args.flatten:
                    rel = os.path.relpath(root, args.dir).replace(os.sep, "_")
                    prefix = "" if rel == "." else rel + "_"
                    dst = os.path.join(args.out, prefix + name)
                else:
                    dst = os.path.join(args.out, name)
                res = normalize_file(src, dst)
                if res:
                    count += 1
        print(f"normalizados {count} ficheros -> {args.out}")
    elif args.src and args.dst:
        res = normalize_file(args.src, args.dst)
        if res:
            print(f"{args.dst}: vars={res[0]} clausulas={res[1]}")
        else:
            sys.exit(f"ERROR: sin clausulas en {args.src}")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
