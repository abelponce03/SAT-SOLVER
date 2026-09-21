#!/usr/bin/env python3
"""
validate_reward.py - Fase 1 (paso 0): valida la SEÑAL DE RECOMPENSA candidata
para el reset-bandit antes de implementarlo.

Recompensa candidata (anclada en Li et al. 2024, arXiv:2404.03753):
  rw_glr = Global Learning Rate por ventana = Δ(cláusulas aprendidas) / Δ(decisiones)
  entre eventos de restart. Mide cuán productiva es la búsqueda (cláusulas
  aprendidas por decisión). La recompensa del bandit: éxito si rw_glr de la
  ventana supera el EMA histórico de rw_glr (decay 0.8), fallo si no.

Requiere trazas con columnas learned,decisions (instrumentación GLR).

Valida tres cosas:
  V1 NO-DEGENERACIÓN : rw_glr varía ventana a ventana (si fuera constante, el
                       bandit no tendría nada que aprender).
  V2 DISCRIMINACIÓN  : rw_glr distingue instancias resueltas de estancadas
                       (timeout) — nivel y/o tendencia.
  V3 RECOMPENSA BIEN FORMADA : la señal de éxito EMA-relativa no es trivial
                       (ni siempre 0 ni siempre 1) y su tasa difiere por régimen.

Uso:
  python3 validate_reward.py <traza.csv> [<traza.csv> ...] [--window 20]
  # etiqueta el resultado por nombre de fichero (…SOLVED / …TIMEOUT si lo incluye)
"""
import argparse
import csv
import os
import statistics as st


def load_restarts(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            if r["event"] != "R":
                continue
            try:
                rows.append((int(r["conflicts"]), int(r["learned"]),
                             int(r["decisions"])))
            except (ValueError, TypeError, KeyError):
                continue  # fila truncada por timeout
    return rows


def windows_glr(rows, k):
    """rw_glr por ventana de k restarts: Δlearned/Δdecisions."""
    out = []
    for i in range(0, len(rows) - k, k):
        c0, l0, d0 = rows[i]
        c1, l1, d1 = rows[i + k]
        dd = d1 - d0
        if dd > 0:
            out.append((c1, (l1 - l0) / dd))
    return out


def ema_reward(glr, decay=0.8):
    """Recompensa EMA-relativa del paper: éxito si glr_ventana > EMA histórico."""
    ema = None
    succ = 0
    seq = []
    for _, g in glr:
        if ema is None:
            ema = g
            seq.append(None)
        else:
            s = 1 if g > ema else 0
            succ += s
            seq.append(s)
            ema = decay * ema + (1 - decay) * g
    valid = [s for s in seq if s is not None]
    return (succ / len(valid) if valid else float("nan")), seq


def slope(glr):
    """pendiente de rw_glr por millón de conflictos (inicio->fin)."""
    if len(glr) < 3:
        return float("nan")
    c0, g0 = glr[0]
    c1, g1 = glr[-1]
    dc = c1 - c0
    return (g1 - g0) / dc * 1e6 if dc else float("nan")


def outcome(name):
    up = name.upper()
    if "TIMEOUT" in up:
        return "TIMEOUT"
    if "SAT" in up or "SOLVED" in up:
        return "SOLVED"
    return "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("traces", nargs="+")
    ap.add_argument("--window", type=int, default=20,
                    help="restarts por ventana rw_glr (suavizado)")
    args = ap.parse_args()

    print(f"ventana = {args.window} restarts   recompensa = éxito si rw_glr > EMA(0.8)\n")
    print(f"{'traza':26s} {'result':8s} {'n_win':>6s} {'glr_med':>8s} "
          f"{'glr_cv':>7s} {'glr_slope':>10s} {'succ_rate':>9s}")
    print("-" * 82)
    agg = {"SOLVED": [], "TIMEOUT": []}
    for path in args.traces:
        name = os.path.basename(path).replace(".csv", "")
        rows = load_restarts(path)
        glr = windows_glr(rows, args.window)
        if len(glr) < 5:
            print(f"{name:26s} (traza corta: {len(glr)} ventanas)")
            continue
        vals = [g for _, g in glr]
        med = st.median(vals)
        cv = st.pstdev(vals) / (st.mean(vals) or 1e-9)
        sl = slope(glr)
        sr, _ = ema_reward(glr)
        oc = outcome(name)
        print(f"{name:26s} {oc:8s} {len(glr):>6d} {med:>8.3f} {cv:>7.2f} "
              f"{sl:>10.3f} {sr:>8.1%}")
        if oc in agg:
            agg[oc].append({"med": med, "cv": cv, "slope": sl, "succ": sr})

    # --- resumen de validación ---
    print("\n" + "=" * 60)
    print("VALIDACIÓN")
    print("=" * 60)

    def group(key):
        s = [d[key] for d in agg["SOLVED"] if d[key] == d[key]]
        t = [d[key] for d in agg["TIMEOUT"] if d[key] == d[key]]
        return s, t

    # V1 no-degeneración
    allcv = [d["cv"] for g in agg.values() for d in g]
    if allcv:
        print(f"V1 no-degeneración: rw_glr CV mediana = {st.median(allcv):.2f} "
              f"({'OK, varía' if st.median(allcv) > 0.05 else 'CASI CONSTANTE'})")

    # V2 discriminación (nivel y pendiente)
    for key, lab in [("med", "nivel rw_glr"), ("slope", "pendiente rw_glr")]:
        s, t = group(key)
        if s and t:
            print(f"V2 {lab:18s}: SOLVED med={st.median(s):+.3f}  "
                  f"TIMEOUT med={st.median(t):+.3f}  "
                  f"Δ={st.median(s)-st.median(t):+.3f}")

    # V3 recompensa bien formada
    s, t = group("succ")
    if s and t:
        print(f"V3 tasa de éxito EMA : SOLVED={st.median(s):.1%}  "
              f"TIMEOUT={st.median(t):.1%}  "
              f"(no trivial si ~30-70%)")


if __name__ == "__main__":
    main()
