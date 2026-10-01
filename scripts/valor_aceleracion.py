#!/usr/bin/env python3
"""
valor_aceleracion.py — ¿cuánto PAR-2 compra hacer el solver s veces más rápido?

Identidad exacta (research/08 §2, Proposición 1): acelerar un solver por un
factor s con límite T da, instancia a instancia, el resultado de ejecutar el
solver original con límite s·T y dividir el tiempo entre s:

    t'_i = t_i / s,  resuelta  <=>  t_i <= s·T.

Por eso, con datos censurados en T0 (tiempos conocidos solo hasta T0), el PAR-2
acelerado es EXACTO para todo par (s, T) con s·T <= T0. No hace falta modelar la
cola de la distribución.

Fuentes:
  - SAT Competition 2026 (400 instancias, T0 = 5000 s): Kissat de fábrica y el
    ganador (satsuma + Kissat 4.0.4, la referencia más cercana a LabeSAT);
  - tesis (Kissat, 883 instancias industriales, T0 = 800 s, media de 3 semillas).

Uso: python3 scripts/valor_aceleracion.py > results/estrategia/valor_aceleracion.txt
"""
import os

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
S = [1.0, 1.05, 1.10, 1.25, 1.5, 2.0, 3.0, 5.0]


def par2_acelerado(t, s, T):
    """t: tiempos (np.inf si no resolvió en T0). Exacto si s*T <= T0."""
    tp = t / s
    return np.where(tp <= T, tp, 2 * T).mean(), int((tp <= T).sum())


def tabla(nombre, t, T0, Ts):
    print(f"\n## {nombre} (n = {len(t)}, censura T0 = {T0:.0f} s)\n")
    print("| T | " + " | ".join(f"s = {s:g}" for s in S) + " |")
    print("|---:|" + "---:|" * len(S))
    for T in Ts:
        base, nb = par2_acelerado(t, 1.0, T)
        celdas = []
        for s in S:
            if s * T > T0 + 1e-9:
                celdas.append("—")
                continue
            p, n = par2_acelerado(t, s, T)
            celdas.append(f"{100 * (p - base) / base:+.1f} % ({n - nb:+d})")
        print(f"| {T:.0f} | " + " | ".join(celdas) + " |")
    print("\nCelda: ΔPAR-2 relativo frente a s = 1 (y Δ resueltas). «—»: s·T > T0, no exacto.")


def main():
    sc = pd.read_csv(os.path.join(ROOT, "data", "competition", "scores_2026.csv"))
    ok = sc.vresult.isin(["sat", "unsat"]) & sc.status.str.contains("verified|sat|unsat", regex=True)
    sc["t"] = np.where(ok & (sc.runtime <= 5000), sc.runtime, np.inf)
    for solver in ("biere_kissat-biere[main]", "anders_satsuma-iter-kissat[main]"):
        t = sc[sc.solverid == solver].t.to_numpy()
        tabla(f"SAT Competition 2026 — {solver}", t, 5000.0, [100, 250, 500, 1000, 2500])
    ref = pd.read_csv(os.path.join(ROOT, "results", "tesis-kissat.reference.csv"))
    ref = ref[ref.result != "CORRUPT_XZ"]
    ref["t"] = np.where(ref.result.isin(["SAT", "UNSAT"]), ref.time, np.inf)
    t = ref.t.to_numpy()   # cada corrida (instancia × semilla) cuenta como una observación
    tabla("Tesis — Kissat, 883 instancias × 3 semillas", t, 800.0, [50, 100, 160, 400])


if __name__ == "__main__":
    main()
