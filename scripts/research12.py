#!/usr/bin/env python3
"""
research12.py — muestras y reglas de decisión PREREGISTRADAS de los
experimentos de research/12 (EXP-024 a EXP-034).

  seleccionar        escribe las listas de instancias (deterministas: orden
                     md5(hash + SAL), cuota proporcional por familia); se
                     commitean con los preregistros, antes de ejecutar nada
  seleccionar-2025   la lista de 2025 de EXP-026/027 (etapa 2), cuando exista
                     el escaneo de satsuma de EXP-023; la regla es esta
  cribado A B        etapa 1 de un A/B en dos etapas: ¿pasa a confirmación?
  confirmacion A B   etapa 2: hipótesis H1 (PAR-2) y H2 (velocidad)
  coste-prueba A B   EXP-033: misma trayectoria y coste de escribir la prueba

Reglas (research/12 §10; las mismas para todas las opciones de búsqueda):

  Etapa 1 (cribado, sin contraste): PASA si el ΔPAR-2 medio (B − A) < 0 o el
  factor geométrico de velocidad B/A en las resueltas por las dos ramas (con
  t >= 1 s en alguna) es < 0,97.  Si no, se cierra «sin señal en el cribado».
  Los p de la etapa 1 se informan pero no son evidencia: la etapa 2 usa
  instancias que el cribado no ha visto.

  Etapa 2 (confirmación): H1 = ΔPAR-2 < 0 con Wilcoxon p < 0,05 y el IC95 %
  bootstrap entero por debajo de 0.  H2 = factor geométrico con el IC95 %
  entero por debajo de 1.  Si B empeora con p < 0,05: dañina.
"""
import argparse
import csv
import hashlib
import math
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from par2 import SOLVED, bootstrap_ci, load, mcnemar, per_instance, wilcoxon  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SAL = "research12-2026-10-05"
R = lambda *p: os.path.join(ROOT, *p)  # noqa: E731


def orden(h, sal=SAL):
    return hashlib.md5((h + sal).encode()).hexdigest()


def cuotas(familias, n):
    """Cuota proporcional por familia (al menos 1), que suma n (como EXP-015)."""
    tot = sum(familias.values())
    c = {f: max(1, round(k / tot * n)) for f, k in familias.items()}
    while sum(c.values()) > n:
        f = max(c, key=lambda x: (c[x], x))
        c[f] -= 1
    while sum(c.values()) < n:
        f = min(c, key=lambda x: (c[x], x))
        c[f] += 1
    return c


def estratificada(filas, n, sal, excluir=()):
    """filas: dicts con 'hash' y 'family'.  Devuelve n hashes."""
    filas = [r for r in filas if r["hash"] not in excluir]
    por = defaultdict(list)
    for r in filas:
        por[r["family"]].append(r)
    c = cuotas({f: len(v) for f, v in por.items()}, min(n, len(filas)))
    sel = []
    for f, v in sorted(por.items()):
        sel += [r["hash"] for r in sorted(v, key=lambda r: orden(r["hash"], sal))[:c[f]]]
    return sorted(sel)


def escribir(path, cabecera, nombres):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(f"# {cabecera} (research12.py seleccionar)\n")
        for n in nombres:
            f.write(n + "\n")
    print(f"{len(nombres):4d}  {os.path.relpath(path, ROOT)}")


def seleccionar(_args):
    tesis = list(csv.DictReader(open(R("bench", "tesis.list.csv"))))
    dev = [r for r in tesis if r["particion"] == "dev" and r["xz_ok"] == "1"
           and r["dificultad"] in ("facil", "media", "inestable")]
    # Listas compartidas de las opciones de búsqueda (EXP-028 a EXP-031: M9, M8, M5 y M10):
    # cribado (40) y confirmación (60), disjuntas.
    l1 = estratificada(dev, 40, SAL + "-cribado")
    l2 = estratificada(dev, 60, SAL + "-confirmacion", excluir=set(l1))
    escribir(R("results", "research12", "cribado.txt"),
             "Etapa 1 de las opciones de búsqueda: 40 de tesis-dev (facil, media, inestable)",
             [h + ".cnf.xz" for h in l1])
    escribir(R("results", "research12", "confirmacion.txt"),
             "Etapa 2 de las opciones de búsqueda: 60 de tesis-dev, disjuntas del cribado",
             [h + ".cnf.xz" for h in l2])

    # EXP-026 (M1) y EXP-027 (M7): donde satsuma añade ruptura.
    sym = [r for r in csv.DictReader(open(R("results", "b4", "satsuma-mclique-symm2026.csv")))
           if r["status"] == "OK" and r["cambia"] == "1"]
    escribir(R("results", "exp026", "simetricas.txt"),
             "EXP-026/EXP-027 etapa 1: symm2026 con ruptura (cambia = 1, mclique v2)",
             sorted(r["instance"] for r in sym))
    esc = {r["instance"].split(".")[0]: r for r in csv.DictReader(open(R("results", "exp014", "satsuma.csv")))}
    ind = [r for r in dev if esc.get(r["hash"], {}).get("cambia") == "1"]
    escribir(R("results", "exp026", "industria.txt"),
             "EXP-026/EXP-027 etapa 2: tesis-dev con ruptura (cambia = 1), facil/media/inestable",
             [h + ".cnf.xz" for h in estratificada(ind, 40, SAL + "-industria-simetrica")])

    # EXP-032 (X2): instancias con sistema XOR consistente donde X1s se rechaza.
    x1s = [r for r in csv.DictReader(open(R("results", "exp022", "x1s.csv")))
           if r["x1s"] == "rechazada" and r["bank"] != "sintetica"]
    for r in x1s:
        r["hash"], r["family"] = r["instance"], r["bank"]
    e1 = estratificada(x1s, 40, SAL + "-x2-cribado")
    e2 = estratificada(x1s, 60, SAL + "-x2-confirmacion", excluir=set(e1))
    escribir(R("results", "exp032", "cribado.txt"),
             "EXP-032 etapa 1: X1 consistente y X1s rechazada (EXP-022)", e1)
    escribir(R("results", "exp032", "confirmacion.txt"),
             "EXP-032 etapa 2: ídem, disjuntas del cribado", e2)

    # EXP-033 (M11): coste de escribir la prueba, 40 de tesis-dev no triviales.
    escribir(R("results", "exp033", "instancias.txt"),
             "EXP-033: 40 de tesis-dev (facil, media, inestable)",
             [h + ".cnf.xz" for h in estratificada(dev, 40, SAL + "-prueba")])

    # EXP-034 (M12): UNSAT con ruptura de symm2026 y UNSAT de tesis-dev.
    lista = {r["hash"]: r for r in csv.DictReader(open(R("bench", "symm2026.list.csv")))}
    s_unsat = sorted(r["instance"] for r in sym
                     if lista.get(r["instance"].split(".")[0], {}).get("resultado") == "unsat")
    t_unsat = [r for r in dev if r["k_resultado"] == "UNSAT"]
    escribir(R("results", "exp034", "simetricas.txt"),
             "EXP-034: symm2026 UNSAT con ruptura", s_unsat)
    escribir(R("results", "exp034", "industria.txt"),
             "EXP-034: 30 UNSAT de tesis-dev (facil, media, inestable)",
             [h + ".cnf.xz" for h in estratificada(t_unsat, 30, SAL + "-verificacion")])


def seleccionar_2025(_args):
    """Etapa 2 de EXP-026 y EXP-027 en instancias que el cribado no vio: las
    de 2025 donde satsuma añade ruptura (cambia = 1 en el escaneo de
    EXP-023, paso 1).  Se ejecuta en la cola DESPUÉS de ese escaneo; la regla
    queda fijada aquí, antes de verlo."""
    esc = R("results", "exp023", "satsuma.csv")
    if not os.path.exists(esc):
        sys.exit(f"falta {os.path.relpath(esc, ROOT)} (EXP-023, paso 1)")
    cambia = {r["instance"].split(".")[0] for r in csv.DictReader(open(esc))
              if r["status"] == "OK" and r["cambia"] == "1"}
    filas = [{"hash": r["hash"], "family": r["group"]}
             for r in csv.DictReader(open(R("bench", "sc2025.list.csv"))) if r["hash"] in cambia]
    escribir(R("results", "exp026", "sc2025.txt"),
             "EXP-026/EXP-027 etapa 2: 2025 con ruptura (cambia = 1 en EXP-023), hasta 60",
             [h + ".cnf.xz" for h in estratificada(filas, 60, SAL + "-sc2025")])


# ------------------------------------------------------------------ análisis
def pares(path_a, path_b):
    ia, ib = per_instance(load(path_a)), per_instance(load(path_b))
    comunes = sorted(set(ia) & set(ib))
    if len(comunes) < max(len(ia), len(ib)):
        print(f"[aviso] {max(len(ia), len(ib)) - len(comunes)} instancias sin pareja")
    return ia, ib, comunes


def factor_velocidad(ra, rb):
    """Media geométrica de B/A por instancia (mediana entre semillas), solo
    con las dos ramas resueltas y t >= 1 s en alguna.  IC95 % bootstrap."""
    def tiempos(rows):
        d = defaultdict(list)
        for r in rows:
            if r["status"] in SOLVED:
                d[r["instance"]].append(r["cpu_s"])
        return {k: sorted(v)[len(v) // 2] for k, v in d.items()}
    ta, tb = tiempos(ra), tiempos(rb)
    logs = [math.log(tb[k] / ta[k]) for k in sorted(set(ta) & set(tb))
            if max(ta[k], tb[k]) >= 1.0 and ta[k] > 0 and tb[k] > 0]
    if not logs:
        return float("nan"), (float("nan"), float("nan")), 0
    rng = random.Random(12345)
    medias = sorted(sum(logs[rng.randrange(len(logs))] for _ in logs) / len(logs)
                    for _ in range(10000))
    g = math.exp(sum(logs) / len(logs))
    return g, (math.exp(medias[250]), math.exp(medias[9749])), len(logs)


def informe(path_a, path_b):
    ra, rb = load(path_a), load(path_b)
    ia, ib, comunes = pares(path_a, path_b)
    diffs = [ib[k]["par2"] - ia[k]["par2"] for k in comunes]
    media = sum(diffs) / len(diffs)
    lo, hi = bootstrap_ci(diffs)
    _, p, n = wilcoxon(diffs)
    solo_a = sum(1 for k in comunes if ia[k]["n_solved"] and not ib[k]["n_solved"])
    solo_b = sum(1 for k in comunes if ib[k]["n_solved"] and not ia[k]["n_solved"])
    g, (glo, ghi), ng = factor_velocidad(ra, rb)
    print(f"instancias: {len(comunes)}  PAR-2 A {sum(ia[k]['par2'] for k in comunes) / len(comunes):.1f}"
          f"  B {sum(ib[k]['par2'] for k in comunes) / len(comunes):.1f}")
    print(f"ΔPAR-2 (B − A): {media:+.2f} s  IC95 % [{lo:+.2f}, {hi:+.2f}]  Wilcoxon p = {p:.3g} (n = {n})")
    print(f"solo A: {solo_a}  solo B: {solo_b}  McNemar p = {mcnemar(solo_a, solo_b):.3g}")
    print(f"factor de velocidad B/A: {g:.3f}  IC95 % [{glo:.3f}, {ghi:.3f}]  (n = {ng})")
    return media, (lo, hi), p, g, (glo, ghi)


def cribado(args):
    media, _, _, g, _ = informe(args.a, args.b)
    pasa = media < 0 or (g == g and g < 0.97)
    print("DECISIÓN (etapa 1):", "PASA a confirmación" if pasa else "se cierra sin señal en el cribado")


def confirmacion(args):
    media, (lo, hi), p, g, (glo, ghi) = informe(args.a, args.b)
    h1 = media < 0 and p < 0.05 and hi < 0
    h2 = ghi < 1
    print(f"H1 (PAR-2): {'se cumple' if h1 else 'no se cumple'}")
    print(f"H2 (velocidad): {'se cumple' if h2 else 'no se cumple'}")
    if media > 0 and p < 0.05:
        print("B EMPEORA con p < 0,05: se cierra como dañina")


def coste_prueba(args):
    """EXP-033: con presupuesto de conflictos, A sin prueba y B con prueba
    deben hacer la MISMA búsqueda; la razón de tiempos es el coste de
    escribirla."""
    ra, rb = load(args.a), load(args.b)
    ka = {(r["instance"], r["seed"]): r for r in ra}
    kb = {(r["instance"], r["seed"]): r for r in rb}
    distintas, logs = 0, []
    for k in sorted(set(ka) & set(kb)):
        a, b = ka[k], kb[k]
        if any(a.get(c) != b.get(c) for c in ("conflicts", "decisions", "propagations")):
            distintas += 1
            continue
        if a["status"] in ("ERROR", "HARDKILL") or b["status"] in ("ERROR", "HARDKILL"):
            continue
        if max(a["cpu_s"], b["cpu_s"]) >= 1.0:
            logs.append(math.log(b["wall_s"] / a["wall_s"]))
    print(f"parejas con trayectoria distinta: {distintas} (debe ser 0)")
    if logs:
        rng = random.Random(12345)
        m = sorted(sum(logs[rng.randrange(len(logs))] for _ in logs) / len(logs) for _ in range(10000))
        print(f"coste de la prueba (reloj B/A): {math.exp(sum(logs) / len(logs)):.3f}  "
              f"IC95 % [{math.exp(m[250]):.3f}, {math.exp(m[9749]):.3f}]  (n = {len(logs)})")
    ruta = os.path.splitext(args.b)[0] + ".pruebas.csv"
    if os.path.exists(ruta):
        tam = sorted(int(r["proof_bytes"]) for r in csv.DictReader(open(ruta)))
        if tam:
            print(f"tamaño de la prueba: mediana {tam[len(tam) // 2] / 2**20:.1f} MiB, "
                  f"máximo {tam[-1] / 2**20:.1f} MiB")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("seleccionar").set_defaults(f=seleccionar)
    sub.add_parser("seleccionar-2025").set_defaults(f=seleccionar_2025)
    for nombre, f in (("cribado", cribado), ("confirmacion", confirmacion),
                      ("coste-prueba", coste_prueba)):
        p = sub.add_parser(nombre)
        p.add_argument("a")
        p.add_argument("b")
        p.set_defaults(f=f)
    args = ap.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
