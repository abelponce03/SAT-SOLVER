#!/usr/bin/env python3
"""
analyze_exp010.py — análisis preregistrado de EXP-010 (mclique frente a
cliquer y a satsuma sin cliques).  Aplica literalmente los criterios de
docs/experiments/EXP-010-mclique-mit.md §4.

Parte 1 (results/exp010/satsuma.csv, de compare_satsuma_builds.py):
  - coincidencias de SHA-1 de la CNF de salida entre builds, por estrato;
  - refutaciones dentro de satsuma (salida de <= 1 cláusula);
  - fallos y topes; tiempos (descriptivo, H4);
  - escribe la lista de la parte 2: SHA-1(mclique) != SHA-1(mit).

Parte 2 (A.csv, B.csv y seguridad.csv, si existen): H1, H2, H3 y veredicto.

Uso:
  python3 scripts/analyze_exp010.py [--dir results/exp010] [--write-list]
"""
import argparse
import csv
import os
import statistics
from collections import defaultdict

R6 = ["043c9100", "0f1070ba", "1a3bef9e", "65bf849f", "6ddda968", "e5787bb4"]
SOLVED = {"SAT", "UNSAT"}


def parte1(path, write_list, list_path):
    filas = list(csv.DictReader(open(path)))
    por = defaultdict(dict)      # instancia -> build -> fila
    familia = {}
    for f in filas:
        por[f["instance"]][f["build"]] = f
        familia[f["instance"]] = f["family"]
    insts = sorted(por)
    print(f"## Parte 1 — satsuma solo ({len(insts)} instancias)\n")

    def igual(i, a, b):
        return por[i][a]["out_sha1"] == por[i][b]["out_sha1"]

    tabla = defaultdict(lambda: [0, 0, 0, 0])   # estrato -> [n, mcl=cli, mcl=mit, mit=cli]
    for i in insts:
        t = tabla[familia[i]]
        t[0] += 1
        t[1] += igual(i, "mclique", "cliques")
        t[2] += igual(i, "mclique", "mit")
        t[3] += igual(i, "mit", "cliques")
    print("| estrato | n | mclique = cliques | mclique = mit | mit = cliques |")
    print("|---|---:|---:|---:|---:|")
    tot = [0, 0, 0, 0]
    for e in sorted(tabla):
        print(f"| {e} | " + " | ".join(str(x) for x in tabla[e]) + " |")
        tot = [a + b for a, b in zip(tot, tabla[e])]
    print("| **total** | " + " | ".join(f"**{x}**" for x in tot) + " |\n")

    print("Instancias donde algún build difiere:\n")
    print("| instancia | estrato | cláusulas | mit | mclique | cliques |")
    print("|---|---|---:|---:|---:|---:|")
    for i in insts:
        if igual(i, "mclique", "cliques") and igual(i, "mclique", "mit"):
            continue
        c = [por[i][b]["clauses_out"] for b in ("mit", "mclique", "cliques")]
        marca = ["**1** (refutada)" if x in ("0", "1") else x for x in c]
        print(f"| {i[:8]}… | {familia[i]} | {por[i]['mit']['clauses_in']} | "
              + " | ".join(marca) + " |")
    print()

    for b in ("mit", "mclique", "cliques"):
        fallos = [i[:8] for i in insts if por[i][b]["exit"] != "0"]
        secs = [float(por[i][b]["secs"]) for i in insts]
        print(f"- `{b}`: fallos o topes {len(fallos)} {fallos if fallos else ''}; "
              f"tiempo medio {statistics.mean(secs):.2f} s, mediana "
              f"{statistics.median(secs):.2f} s, máximo {max(secs):.1f} s")
    nuevos = [i[:8] for i in insts
              if por[i]["mclique"]["exit"] != "0" and por[i]["mit"]["exit"] == "0"]
    print(f"- topes o fallos **nuevos** de mclique (que mit no tiene): {len(nuevos)} {nuevos}")

    lista = [i for i in insts if not igual(i, "mclique", "mit")]
    print(f"\nParte 2: {len(lista)} instancias con SHA-1(mclique) != SHA-1(mit).")
    if write_list:
        with open(list_path, "w") as f:
            f.write("# EXP-010 parte 2: SHA-1(mclique) != SHA-1(mit) (regla de §3)\n")
            f.write("\n".join(lista) + "\n")
        print(f"Escrita en {list_path}")
    return len(nuevos)


def resueltas(path):
    r = defaultdict(list)
    for f in csv.DictReader(open(path)):
        r[f["instance"]].append(f["status"] in SOLVED)
    return r


def parte2(d, topes_nuevos):
    A, B = resueltas(os.path.join(d, "A.csv")), resueltas(os.path.join(d, "B.csv"))
    print("\n## Parte 2 — kissat sobre las salidas que cambian\n")
    print("| instancia | A sin cliques (resueltas/semillas) | B mclique |")
    print("|---|---|---|")
    for i in sorted(A):
        print(f"| {i[:8]}… | {sum(A[i])}/{len(A[i])} | {sum(B[i])}/{len(B[i])} |")

    r6 = [i for i in B if i[:8] in R6]
    h1 = sum(all(B[i]) for i in r6)
    # Una R6 fuera de la lista de la parte 2 tiene la salida de mit, que no la
    # resuelve (research/03): cuenta como no recuperada.
    print(f"\n- **H1**: R6 recuperadas por mclique (ambas semillas): **{h1} de 6** "
          f"({len(r6)} de R6 están en la parte 2). Criterio: ≥ 5.")
    perdidas = [i[:8] for i in A if any(A[i]) and not any(B[i])]
    print(f"- **H2**: pérdidas (A resuelve alguna semilla, B ninguna): "
          f"**{len(perdidas)}** {perdidas}. Criterio: 0.")
    seg = os.path.join(d, "seguridad.csv")
    fallos = None
    if os.path.exists(seg):
        v = [f["verificacion"] for f in csv.DictReader(open(seg))]
        fallos = v.count("FALLO")
        print(f"- **H3**: {v.count('OK')} OK, {fallos} FALLO, {v.count('TOPE')} TOPE, "
              f"{v.count('SALTADA')} SALTADA. Criterio: 0 FALLO.")
    else:
        print("- **H3**: falta seguridad.csv; no hay veredicto sin él.")

    if fallos is None:
        return
    if fallos:
        veredicto = "NO ADOPTAR: fallo de seguridad; buscar la causa (ADR-0004)"
    elif h1 >= 5 and not perdidas and topes_nuevos == 0:
        veredicto = "ADOPTAR mclique como satsuma por defecto de --symmetry"
    else:
        veredicto = "NO ADOPTAR todavía: H1, H2 o los topes fallan; D-005 a la próxima reunión"
    print(f"\n**Veredicto (§4)**: {veredicto}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default="results/exp010")
    ap.add_argument("--write-list", action="store_true",
                    help="escribe instancias.txt para la parte 2")
    args = ap.parse_args()
    topes = parte1(os.path.join(args.dir, "satsuma.csv"), args.write_list,
                   os.path.join(args.dir, "instancias.txt"))
    if os.path.exists(os.path.join(args.dir, "B.csv")):
        parte2(args.dir, topes)


if __name__ == "__main__":
    main()
