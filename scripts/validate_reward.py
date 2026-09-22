#!/usr/bin/env python3
"""
validate_reward.py — EXP-005 paso 0: valida la SEÑAL DE RECOMPENSA del
planificador adaptativo (A4) **antes** de escribirlo.

Lee las trazas de cambio de modo de Kissat (`KISSAT_TRACE`, una fila por fase
`stable`/`focused`) y corre las tres pruebas que la etapa CaDiCaL estableció
(`docs/archive/cadical-era/05-fase1-validacion-recompensa.md`), ahora sobre
Kissat, que es lo que aquel documento dejaba explícitamente pendiente.

  V1 NO-DEGENERACIÓN  el GLR varía de fase a fase.  Si fuera constante, el
                      planificador no tendría nada que aprender.
  V2 DISCRIMINACIÓN   el GLR distingue corridas que acaban resolviendo de las
                      que se estancan -- por nivel, por tendencia, o por
                      ninguna de las dos.  **Es la prueba que puede matar A4.**
  V3 BIEN FORMADA     la señal "esta fase superó a su EMA" no es trivial (ni
                      siempre 0 ni siempre 1).

GLR de una fase = Δconflicts / Δdecisions (cláusulas aprendidas por decisión).
Se usa `conflicts` y no `clauses_learned` porque el primero es un COUNTER de
nivel 0: existe también en el build `--competition`, que es donde el
planificador tendrá que funcionar.

Uso:
  python3 scripts/validate_reward.py results/exp005/traces/*.csv [--decay 0.8]
"""
import argparse
import csv
import os
import statistics as st
from collections import defaultdict


def load(path):
    """Devuelve la lista de fases: (modo, glr, conflictos_acumulados)."""
    out, acc = [], 0
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            try:
                dc, dd = int(r["d_conflicts"]), int(r["d_decisions"])
            except (ValueError, KeyError):
                continue          # fila truncada al matar el proceso
            acc += dc
            if dd > 0:
                out.append((r["mode"], dc / dd, acc))
    return out


def outcome(name):
    up = os.path.basename(name).upper()
    if "TIMEOUT" in up:
        return "TIMEOUT"
    if "SOLVED" in up:
        return "SOLVED"
    return "?"


def ema_success_rate(glrs, decay):
    """Tasa de fases que superan el EMA de su propio historial."""
    ema, succ, n = None, 0, 0
    for g in glrs:
        if ema is None:
            ema = g
            continue
        succ += 1 if g > ema else 0
        n += 1
        ema = decay * ema + (1 - decay) * g
    return succ / n if n else float("nan")


def slope(phases):
    """Pendiente del GLR por millón de conflictos, de la primera a la última fase."""
    if len(phases) < 3:
        return float("nan")
    _, g0, c0 = phases[0]
    _, g1, c1 = phases[-1]
    dc = c1 - c0
    return (g1 - g0) / dc * 1e6 if dc else float("nan")


def cv(xs):
    if len(xs) < 2:
        return float("nan")
    m = st.mean(xs)
    return st.pstdev(xs) / m if m else float("nan")


def median(xs):
    xs = [x for x in xs if x == x]
    return st.median(xs) if xs else float("nan")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("traces", nargs="+")
    ap.add_argument("--decay", type=float, default=0.8)
    ap.add_argument("--min-phases", type=int, default=4,
                    help="trazas con menos fases no informan de nada")
    args = ap.parse_args()

    print(f"{len(args.traces)} trazas · recompensa = éxito si GLR(fase) > EMA({args.decay})\n")
    print(f"{'traza':<34} {'result':<8} {'fases':>6} {'glr_med':>9} "
          f"{'glr_cv':>8} {'pendiente':>11} {'exito':>7}")
    print("-" * 88)

    agg = defaultdict(lambda: defaultdict(list))
    per_mode = defaultdict(list)
    saltadas = 0
    for path in sorted(args.traces):
        ph = load(path)
        res = outcome(path)
        if len(ph) < args.min_phases:
            saltadas += 1
            continue
        glrs = [g for _, g, _ in ph]
        row = {
            "n": len(ph), "med": median(glrs), "cv": cv(glrs),
            "slope": slope(ph), "succ": ema_success_rate(glrs, args.decay),
        }
        for k, v in row.items():
            if k != "n":
                agg[res][k].append(v)
        agg[res]["n"].append(row["n"])
        for m, g, _ in ph:
            per_mode[m].append(g)
        name = os.path.basename(path)[:33]
        print(f"{name:<34} {res:<8} {row['n']:>6} {row['med']:>9.3f} "
              f"{row['cv']:>8.3f} {row['slope']:>11.3f} {row['succ']*100:>6.1f}%")

    if saltadas:
        print(f"\n({saltadas} trazas con menos de {args.min_phases} fases, descartadas)")

    print("\n" + "=" * 88)
    print("AGREGADO POR DESENLACE (medianas)\n")
    print(f"{'':<12} {'n':>4} {'glr_med':>9} {'glr_cv':>8} {'pendiente':>11} {'exito':>8}")
    for res in ("SOLVED", "TIMEOUT"):
        a = agg.get(res)
        if not a:
            continue
        print(f"{res:<12} {len(a['n']):>4} {median(a['med']):>9.3f} "
              f"{median(a['cv']):>8.3f} {median(a['slope']):>11.3f} "
              f"{median(a['succ'])*100:>7.1f}%")

    s, t = agg.get("SOLVED"), agg.get("TIMEOUT")
    print("\n" + "=" * 88)
    print("VEREDICTO\n")

    todos_cv = [c for res in agg.values() for c in res["cv"]]
    v1 = median(todos_cv)
    print(f"V1 no-degeneración : CV mediano del GLR = {v1:.3f}  "
          f"-> {'PASA' if v1 > 0.2 else 'FALLA'} (umbral 0.2)")
    print("     el GLR varía de fase a fase, así que hay señal que explotar."
          if v1 > 0.2 else
          "     el GLR es casi constante: no hay nada que aprender.")

    if s and t:
        d_niv = median(s["med"]) - median(t["med"])
        d_pen = median(s["slope"]) - median(t["slope"])
        print(f"\nV2 discriminación  : Δ nivel (SOLVED−TIMEOUT)     = {d_niv:+.3f}")
        print(f"                     Δ pendiente (SOLVED−TIMEOUT) = {d_pen:+.3f}")
        ok = abs(d_niv) > 0.05 or abs(d_pen) > 0.05
        print(f"                     -> {'PASA' if ok else 'FALLA'}")
        if not ok:
            print("     ni el nivel ni la tendencia separan los dos regímenes:")
            print("     la recompensa no informa y A4 se queda sin señal.")
    else:
        print("\nV2 discriminación  : NO EVALUABLE (falta uno de los dos grupos)")

    todas_succ = [x for res in agg.values() for x in res["succ"]]
    v3 = median(todas_succ)
    ok3 = 0.15 < v3 < 0.85
    print(f"\nV3 bien formada    : tasa de éxito mediana = {v3*100:.1f}%  "
          f"-> {'PASA' if ok3 else 'FALLA'} (debe estar entre 15% y 85%)")

    if per_mode:
        print("\n" + "=" * 88)
        print("GLR POR MODO (¿se diferencian los dos brazos?)\n")
        for m, g in sorted(per_mode.items()):
            print(f"   {m:<10} n={len(g):>5}  mediana={median(g):.3f}  CV={cv(g):.3f}")


if __name__ == "__main__":
    main()
