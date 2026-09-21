#!/usr/bin/env python3
"""
par2.py - calcula el PAR-2 (Penalized Average Runtime, factor 2) a partir de
los CSV que produce run_baseline.sh, y compara dos corridas A/B.

PAR-2 es la metrica oficial de ranking de la SAT Competition:
  - si el solver resuelve la instancia: se cuenta su tiempo real.
  - si NO la resuelve (timeout/unknown): se cuenta 2 * timeout como penalizacion.
El PAR-2 de un solver es el promedio de esos valores sobre todas las instancias.
Menor es mejor.

Uso:
  python3 par2.py <run.csv>                 # resumen de una corrida
  python3 par2.py <baseline.csv> <mod.csv>  # comparacion A/B por instancia
"""
import csv
import sys


def load(path):
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            r["wall_time_s"] = float(r["wall_time_s"])
            r["timeout_s"] = float(r["timeout_s"])
            rows.append(r)
    return rows


def par2_value(row):
    if row["status"] in ("SAT", "UNSAT"):
        return row["wall_time_s"]
    return 2.0 * row["timeout_s"]


def summarize(rows):
    solved = [r for r in rows if r["status"] in ("SAT", "UNSAT")]
    par2_total = sum(par2_value(r) for r in rows)
    n = len(rows)
    return {
        "n": n,
        "solved": len(solved),
        "sat": sum(1 for r in rows if r["status"] == "SAT"),
        "unsat": sum(1 for r in rows if r["status"] == "UNSAT"),
        "timeout": sum(1 for r in rows if r["status"] == "TIMEOUT"),
        "unknown": sum(1 for r in rows if r["status"] == "UNKNOWN"),
        "par2_avg": par2_total / n if n else 0.0,
        "solved_time": sum(r["wall_time_s"] for r in solved),
    }


def print_summary(label, s):
    print(f"== {label}")
    print(f"   instancias:      {s['n']}")
    print(f"   resueltas:       {s['solved']}  (SAT={s['sat']}, UNSAT={s['unsat']})")
    print(f"   no resueltas:    {s['timeout']} timeout, {s['unknown']} unknown")
    print(f"   PAR-2 (prom):    {s['par2_avg']:.3f} s   <-- menor es mejor")
    print(f"   tiempo resueltas:{s['solved_time']:.3f} s")


def compare(base_path, mod_path):
    base = {r["instance"]: r for r in load(base_path)}
    mod = {r["instance"]: r for r in load(mod_path)}
    common = sorted(set(base) & set(mod))

    b_label = next(iter(base.values()))["solver"] if base else "A"
    m_label = next(iter(mod.values()))["solver"] if mod else "B"

    print(f"Comparacion A/B  (A={b_label}  vs  B={m_label})")
    print(f"{'instancia':30s} {'A_estado':9s} {'A_t(s)':>9s} {'B_estado':9s} {'B_t(s)':>9s} {'delta':>9s}")
    print("-" * 82)
    for inst in common:
        a, b = base[inst], mod[inst]
        pa, pb = par2_value(a), par2_value(b)
        delta = pb - pa  # negativo => B (modificado) es mas rapido
        mark = "  <=B mejor" if delta < -1e-6 else ("  <=A mejor" if delta > 1e-6 else "")
        print(f"{inst:30s} {a['status']:9s} {pa:9.3f} {b['status']:9s} {pb:9.3f} {delta:9.3f}{mark}")

    print()
    sb, sm = summarize(list(base.values())), summarize(list(mod.values()))
    print_summary(f"A = {b_label}", sb)
    print()
    print_summary(f"B = {m_label}", sm)
    print()
    improvement = sb["par2_avg"] - sm["par2_avg"]
    pct = (improvement / sb["par2_avg"] * 100) if sb["par2_avg"] else 0.0
    verdict = "MEJORA" if improvement > 0 else ("EMPEORA" if improvement < 0 else "SIN CAMBIO")
    print(f">> PAR-2: B respecto a A = {improvement:+.3f} s ({pct:+.1f}%)  [{verdict}]")
    print(f">> Instancias resueltas: A={sb['solved']}  B={sm['solved']}  (delta={sm['solved']-sb['solved']:+d})")


def main():
    if len(sys.argv) == 2:
        print_summary(sys.argv[1], summarize(load(sys.argv[1])))
    elif len(sys.argv) == 3:
        compare(sys.argv[1], sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
