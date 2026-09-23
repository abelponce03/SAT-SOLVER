#!/usr/bin/env python3
"""
analyze_exp011.py — análisis preregistrado de EXP-011 (mclique v2, con
presupuesto de trabajo).  Aplica docs/experiments/EXP-011-mclique-presupuesto.md
§4, combinando sus datos con los de EXP-010.

Parte 1 (results/exp011/satsuma.csv): topes y fallos por build (H1),
coincidencias v2 = v1 (H2) y lista de la parte 2:
SHA-1(mclique2) != SHA-1(mclique1) y != SHA-1(mit).

Parte 2 y veredicto: para cada instancia de EXP-010 parte 2, el resultado de v2
es el de EXP-011 parte 2 si está en su lista, o el de v1 (EXP-010) si
SHA-1(v2) = SHA-1(v1).

Uso:
  python3 scripts/analyze_exp011.py [--write-list]
"""
import argparse
import csv
import os
from collections import defaultdict

R6 = ["043c9100", "0f1070ba", "1a3bef9e", "65bf849f", "6ddda968", "e5787bb4"]
SOLVED = {"SAT", "UNSAT"}
D10, D11 = "results/exp010", "results/exp011"


def resueltas(path):
    r = defaultdict(list)
    if os.path.exists(path):
        for f in csv.DictReader(open(path)):
            r[f["instance"]].append(f["status"] in SOLVED)
    return r


def verificaciones(path):
    if not os.path.exists(path):
        return None
    return {f["instance"]: f["verificacion"] for f in csv.DictReader(open(path))}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write-list", action="store_true")
    args = ap.parse_args()

    por = defaultdict(dict)
    for f in csv.DictReader(open(os.path.join(D11, "satsuma.csv"))):
        por[f["instance"]][f["build"]] = f
    insts = sorted(por)
    print(f"## Parte 1 — satsuma solo ({len(insts)} instancias)\n")
    for b in ("mit", "mclique1", "mclique2", "cliques"):
        malos = [i[:8] for i in insts if por[i][b]["exit"] != "0"]
        print(f"- `{b}`: topes o fallos {len(malos)} {malos if malos else ''}")
    h1 = all(por[i]["mclique2"]["exit"] == "0" for i in insts)
    print(f"- **H1** (v2 sin topes ni fallos en las {len(insts)}): {'sí' if h1 else 'NO'}")

    def sha(i, b):
        return por[i][b]["out_sha1"]

    iguales = [i for i in insts if sha(i, "mclique2") == sha(i, "mclique1")]
    print(f"- **H2**: v2 = v1 en {len(iguales)} de {len(insts)}; distintas: "
          f"{[i[:8] for i in insts if i not in iguales]}")
    print(f"- v2 = cliques en {sum(sha(i, 'mclique2') == sha(i, 'cliques') for i in insts)}"
          f" de {len(insts)}")

    lista = [i for i in insts
             if sha(i, "mclique2") != sha(i, "mclique1") and sha(i, "mclique2") != sha(i, "mit")]
    print(f"\nParte 2: {len(lista)} instancias {[i[:8] for i in lista]}")
    if args.write_list:
        os.makedirs(D11, exist_ok=True)
        with open(os.path.join(D11, "instancias.txt"), "w") as f:
            f.write("# EXP-011 parte 2: SHA-1(v2) != SHA-1(v1) y != SHA-1(mit) (regla de §3)\n")
            f.write("\n".join(lista) + ("\n" if lista else ""))

    A10, B10 = resueltas(os.path.join(D10, "A.csv")), resueltas(os.path.join(D10, "B.csv"))
    A11, B11 = resueltas(os.path.join(D11, "A.csv")), resueltas(os.path.join(D11, "B.csv"))
    if not A10:
        print("\nFalta EXP-010 parte 2: no hay veredicto todavía.")
        return
    if lista and not B11:
        print("\nFalta EXP-011 parte 2: no hay veredicto todavía.")
        return
    v10 = verificaciones(os.path.join(D10, "seguridad.csv")) or {}
    v11 = verificaciones(os.path.join(D11, "seguridad.csv")) or {}

    print("\n## Resultado combinado para v2\n")
    print("| instancia | A sin cliques | v2 | fuente |")
    print("|---|---|---|---|")
    B, A, V, sin_dato = {}, {}, {}, []
    for i in sorted(A10):
        if i in lista:
            A[i], B[i], V[i], fuente = A11[i], B11[i], v11.get(i), "EXP-011"
        elif sha(i, "mclique2") == sha(i, "mclique1"):
            A[i], B[i], V[i], fuente = A10[i], B10[i], v10.get(i), "EXP-010 (v2 = v1)"
        else:   # v2 = mit: la fórmula de B es la de A
            A[i], B[i], V[i], fuente = A10[i], A10[i], "igual a mit", "v2 = mit"
        print(f"| {i[:8]}… | {sum(A[i])}/{len(A[i])} | {sum(B[i])}/{len(B[i])} | {fuente} |")
        if V[i] is None:
            sin_dato.append(i[:8])

    rec = sum(all(B[i]) for i in B if i[:8] in R6)
    perdidas = [i[:8] for i in A if any(A[i]) and not any(B[i])]
    fallos = [i[:8] for i in V if V[i] == "FALLO"]
    print(f"\n- R6 recuperadas por v2 (ambas semillas): **{rec} de 6** (criterio ≥ 5)")
    print(f"- pérdidas: **{len(perdidas)}** {perdidas} (criterio 0)")
    print(f"- fallos de seguridad: **{len(fallos)}** {fallos}; sin verificación: {sin_dato}")
    if fallos:
        v = "NO ADOPTAR: fallo de seguridad"
    elif h1 and rec >= 5 and not perdidas:
        v = "ADOPTAR mclique v2 como satsuma por defecto de --symmetry"
    else:
        v = "NO ADOPTAR todavía: D-005 a la próxima reunión"
    print(f"\n**Veredicto (§4)**: {v}")


if __name__ == "__main__":
    main()
