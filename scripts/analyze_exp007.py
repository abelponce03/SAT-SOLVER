#!/usr/bin/env python3
"""
analyze_exp007.py — análisis PREREGISTRADO de EXP-007 (docs/experiments/EXP-007 §4).

Se escribió y commiteó antes de que terminara la tanda.  Aplica exactamente lo
fijado en el preregistro:

  - Unidad: la instancia (una semilla).
  - H1 (estrato H):
      contraste principal: Wilcoxon de rangos con signo, dos colas, sobre la
      diferencia de PAR-2 por instancia (cpu_s; 2T si no resuelve);
      además, McNemar sobre las resueltas y ΔPAR-2 medio con IC95 % bootstrap.
  - H2 (estrato N): factor geométrico exp(media log(t_B/t_A)) sobre las
      instancias que ambas ramas resuelven con t >= 1 s, con IC95 % bootstrap.
      Se cumple si el extremo superior del IC <= 1.10.
  - H3 (estrato X, descriptiva): nº de instancias en las que B es >= 3 veces
      más lenta, o en las que A resuelve y B no.
  - Estimación (no es el contraste): ΔPAR-2 post-estratificado,
      Σ_s (pob_s/136) · media_s(ΔPAR-2), con pesos H 54, X 22, N 60, e IC95 %
      bootstrap estratificado.
  - Criterio de decisión: EXP-007 §6.  La seguridad (verify_symm_answers.py) se
      informa aparte y es vinculante.

Uso:  python3 scripts/analyze_exp007.py results/exp007/A.csv results/exp007/B.csv [--timeout 180]
"""
import argparse
import csv
import math
import sys

import numpy as np
from scipy import stats

RESUELTA = {"SAT", "UNSAT"}
POBLACION = {"H": 54, "X": 22, "N": 60}   # estratos de 2026 (EXP-007 §3)
REPS = 10000
SEMILLA = 2027


def carga(path):
    return {r["instance"]: r for r in csv.DictReader(open(path))}


def par2(r, T):
    return float(r["cpu_s"]) if r["status"] in RESUELTA else 2 * T


def boot_media(xs, rng):
    xs = np.asarray(xs, float)
    if len(xs) == 0:
        return (math.nan, math.nan)
    ms = rng.choice(xs, size=(REPS, len(xs)), replace=True).mean(axis=1)
    return tuple(np.percentile(ms, [2.5, 97.5]))


def mcnemar(a_si_b_no, a_no_b_si):
    n = a_si_b_no + a_no_b_si
    if n == 0:
        return 1.0
    return stats.binomtest(min(a_si_b_no, a_no_b_si), n, 0.5).pvalue


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--timeout", type=float, default=180.0)
    args = ap.parse_args()
    T = args.timeout
    A, B = carga(args.a), carga(args.b)
    comunes = sorted(set(A) & set(B))
    faltan = sorted(set(A) ^ set(B))
    rng = np.random.default_rng(SEMILLA)

    filas = []
    for i in comunes:
        a, b = A[i], B[i]
        filas.append({
            "inst": i, "estrato": a["family"],
            "a_ok": a["status"] in RESUELTA, "b_ok": b["status"] in RESUELTA,
            "ta": float(a["cpu_s"]), "tb": float(b["cpu_s"]),
            "d": par2(b, T) - par2(a, T),
            "err": a["status"] not in RESUELTA | {"TIMEOUT"} or
                   b["status"] not in RESUELTA | {"TIMEOUT"},
        })
    print(f"EXP-007 — {len(comunes)} instancias en común (faltan {len(faltan)}); "
          f"T = {T:.0f} s; PAR-2 con cpu_s")
    errores = [f["inst"] for f in filas if f["err"]]
    if errores:
        print(f"  [AVISO] estados no esperados (ERROR/HARDKILL) en: {errores}")
    for s in ("H", "N", "X"):
        g = [f for f in filas if f["estrato"] == s]
        print(f"  estrato {s}: n={len(g)}  resueltas A={sum(f['a_ok'] for f in g)}  "
              f"B={sum(f['b_ok'] for f in g)}")

    # ---- H1 ---------------------------------------------------------------
    H = [f for f in filas if f["estrato"] == "H"]
    d = [f["d"] for f in H]
    nz = [x for x in d if x != 0]
    w = stats.wilcoxon(nz, alternative="two-sided") if len(nz) >= 1 else None
    sb = sum(f["a_ok"] and not f["b_ok"] for f in H)
    bs = sum(not f["a_ok"] and f["b_ok"] for f in H)
    lo, hi = boot_media(d, rng)
    print("\n== H1 (estrato H): ¿labesat resuelve más o más rápido que --no-symmetry?")
    print(f"  ΔPAR-2 medio (B−A) = {np.mean(d):+.2f} s   IC95% bootstrap [{lo:+.2f}, {hi:+.2f}]")
    if w is not None:
        print(f"  Wilcoxon (dos colas) sobre ΔPAR-2 por instancia: W={w.statistic:.1f}  "
              f"p={w.pvalue:.3g}  (n efectivo={len(nz)})")
    print(f"  McNemar: solo A={sb}  solo B={bs}  p={mcnemar(sb, bs):.3g}")
    h1 = w is not None and w.pvalue < 0.05 and np.mean(d) < 0

    # ---- H2 ---------------------------------------------------------------
    N = [f for f in filas if f["estrato"] == "N"]
    lr = [math.log(f["tb"] / f["ta"]) for f in N
          if f["a_ok"] and f["b_ok"] and f["ta"] >= 1.0 and f["tb"] >= 1.0]
    print("\n== H2 (estrato N): coste de satsuma cuando no aporta")
    if lr:
        lo2, hi2 = boot_media(lr, rng)
        fac, flo, fhi = math.exp(np.mean(lr)), math.exp(lo2), math.exp(hi2)
        print(f"  factor geométrico t_B/t_A = {fac:.3f}x   IC95% [{flo:.3f}, {fhi:.3f}]  "
              f"(n={len(lr)} con t >= 1 s en ambas)")
        h2 = fhi <= 1.10
    else:
        print("  sin instancias válidas")
        h2 = False
    print(f"  H2 {'SE CUMPLE' if h2 else 'NO se cumple'} (criterio: extremo superior del IC <= 1.10)")

    # ---- H3 ---------------------------------------------------------------
    X = [f for f in filas if f["estrato"] == "X"]
    dano = [f["inst"] for f in X if (f["a_ok"] and not f["b_ok"]) or
            (f["a_ok"] and f["b_ok"] and f["ta"] >= 1.0 and f["tb"] >= 3 * f["ta"])]
    print("\n== H3 (estrato X, descriptiva)")
    print(f"  daño (B >= 3x más lenta, o A resuelve y B no): {len(dano)} de {len(X)}  {dano}")

    # ---- estimación post-estratificada --------------------------------------
    medias, cis = {}, {}
    for s, pob in POBLACION.items():
        ds = [f["d"] for f in filas if f["estrato"] == s]
        medias[s] = np.mean(ds) if ds else 0.0
    tot = sum(POBLACION.values())
    est = sum(POBLACION[s] / tot * medias[s] for s in POBLACION)
    boots = np.zeros(REPS)
    for s, pob in POBLACION.items():
        ds = np.asarray([f["d"] for f in filas if f["estrato"] == s], float)
        if len(ds):
            boots += pob / tot * rng.choice(ds, size=(REPS, len(ds))).mean(axis=1)
    lo3, hi3 = np.percentile(boots, [2.5, 97.5])
    print("\n== Estimación post-estratificada (parte medible de 2026: 136 instancias; NO es el contraste)")
    print(f"  ΔPAR-2 ≈ {est:+.2f} s   IC95% [{lo3:+.2f}, {hi3:+.2f}]   "
          f"(medias por estrato: " + ", ".join(f"{s} {medias[s]:+.1f}" for s in POBLACION) + ")")

    # ---- veredicto ----------------------------------------------------------
    print("\n== Veredicto según EXP-007 §6 (a falta de la seguridad, que es vinculante)")
    if h1 and h2 and not dano:
        v = "H1 confirmada, H2 se cumple y sin daño en X -> ACTIVADA POR DEFECTO (si la seguridad pasa)"
    elif h1:
        v = ("H1 confirmada, pero " + ("H2 no se cumple" if not h2 else "hay daño en X") +
             " -> SOLO CONDICIONAL (B3) hasta tener criterio")
    else:
        v = "H1 NO confirmada -> medir cliques on/off (D-005); decide el director"
    print("  " + v)
    sys.exit(0)


if __name__ == "__main__":
    main()
