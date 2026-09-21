#!/usr/bin/env python3
"""
par2.py — analiza las corridas de `run_experiment.py`: PAR-2, robustez frente a
seeds y comparación A/B con estadística (ADR-0003).

  python3 scripts/par2.py <run.csv>                 # resumen de una corrida
  python3 scripts/par2.py <A.csv> <B.csv>           # comparación A/B emparejada
  python3 scripts/par2.py <run.csv> --by-family     # desglose por familia
  python3 scripts/par2.py <A.csv> <B.csv> --md      # salida en Markdown (para docs/)

PAR-2 (métrica de ranking de la SAT Competition): por instancia, el tiempo si el
solver resuelve; 2×timeout si no. Menor es mejor.

Para el A/B, cada instancia se agrega primero por **mediana entre seeds** (una
observación por instancia, que es la unidad de la que se muestrea), y sobre esas
observaciones emparejadas se corre:
  - Wilcoxon de rangos con signo (no asume normalidad; el PAR-2 está censurado en 2T),
  - bootstrap del IC 95% del ΔPAR-2 (10 000 remuestreos de instancias),
  - McNemar sobre el cambio en el conjunto de resueltas.
También se reporta el detalle por corrida (sin agregar) para no ocultar varianza.
"""
import argparse
import csv
import math
import random
import statistics as st
from collections import defaultdict

SOLVED = ("SAT", "UNSAT")


# --------------------------------------------------------------------------- IO
def load(path):
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            r["cpu_s"] = float(r.get("cpu_s") or 0.0)
            r["wall_s"] = float(r.get("wall_s") or 0.0)
            r["budget_value"] = float(r.get("budget_value") or 0.0)
            r["seed"] = int(r.get("seed") or 0)
            rows.append(r)
    if not rows:
        raise SystemExit(f"{path}: vacío")
    kinds = {r.get("budget_kind") for r in rows}
    if kinds - {"time"}:
        print(f"[aviso] {path} contiene corridas con presupuesto {kinds}; "
              f"el PAR-2 solo tiene sentido con presupuesto de tiempo.")
    return rows


def par2_of(row, time_col="cpu_s"):
    if row["status"] in SOLVED:
        return row[time_col]
    return 2.0 * row["budget_value"]


# ------------------------------------------------------------------- agregación
def per_instance(rows, time_col="cpu_s"):
    """Mediana del PAR-2 entre seeds -> una observación por instancia."""
    by = defaultdict(list)
    for r in rows:
        by[r["instance"]].append(r)
    out = {}
    for inst, rs in by.items():
        vals = [par2_of(r, time_col) for r in rs]
        n_solved = sum(1 for r in rs if r["status"] in SOLVED)
        out[inst] = {
            "par2": st.median(vals),
            "par2_runs": vals,
            "n_runs": len(rs),
            "n_solved": n_solved,
            "flaky": 0 < n_solved < len(rs),
            "always": n_solved == len(rs),
            "family": rs[0].get("family", "-"),
            "solved_times": [r[time_col] for r in rs if r["status"] in SOLVED],
        }
    return out


def summarize(rows, time_col="cpu_s"):
    inst = per_instance(rows, time_col)
    n_inst = len(inst)
    ratios = []
    for v in inst.values():
        ts = [t for t in v["solved_times"] if t > 1.0]
        if len(ts) >= 2 and min(ts) > 0:
            ratios.append(max(ts) / min(ts))
    return {
        "runs": len(rows),
        "instances": n_inst,
        "sat": sum(1 for r in rows if r["status"] == "SAT"),
        "unsat": sum(1 for r in rows if r["status"] == "UNSAT"),
        "timeout": sum(1 for r in rows if r["status"] in ("TIMEOUT", "BUDGET")),
        "error": sum(1 for r in rows if r["status"] in ("ERROR", "HARDKILL")),
        "solved_all_seeds": sum(1 for v in inst.values() if v["always"]),
        "flaky": sum(1 for v in inst.values() if v["flaky"]),
        "never": sum(1 for v in inst.values() if v["n_solved"] == 0),
        "par2": sum(v["par2"] for v in inst.values()) / n_inst,
        "par2_runs": sum(par2_of(r, time_col) for r in rows) / len(rows),
        "seed_ratio_p90": (sorted(ratios)[int(0.9 * (len(ratios) - 1))] if ratios else float("nan")),
        "seed_ratio_max": (max(ratios) if ratios else float("nan")),
        "budget": rows[0]["budget_value"],
    }


def print_summary(label, s):
    print(f"== {label}")
    print(f"   instancias / corridas: {s['instances']} / {s['runs']}   (timeout = {s['budget']:.0f}s)")
    print(f"   resueltas en TODAS las seeds: {s['solved_all_seeds']}"
          f"   flaky: {s['flaky']}   nunca: {s['never']}")
    print(f"   corridas: SAT={s['sat']} UNSAT={s['unsat']} TIMEOUT={s['timeout']} ERROR={s['error']}")
    print(f"   PAR-2 (mediana de seeds por instancia): {s['par2']:.3f} s   <-- métrica primaria")
    print(f"   PAR-2 (todas las corridas):             {s['par2_runs']:.3f} s")
    if not math.isnan(s["seed_ratio_p90"]):
        print(f"   varianza por seed (>1s): p90 del ratio max/min = {s['seed_ratio_p90']:.2f}x"
              f"   máx = {s['seed_ratio_max']:.2f}x")


def print_by_family(rows, time_col="cpu_s"):
    inst = per_instance(rows, time_col)
    fam = defaultdict(list)
    for v in inst.values():
        fam[v["family"]].append(v)
    print(f"\n{'familia':<28} {'n':>4} {'resueltas':>10} {'flaky':>6} {'PAR-2':>10}")
    print("-" * 62)
    for name in sorted(fam):
        vs = fam[name]
        print(f"{name:<28} {len(vs):>4} {sum(1 for v in vs if v['always']):>10} "
              f"{sum(1 for v in vs if v['flaky']):>6} "
              f"{sum(v['par2'] for v in vs)/len(vs):>10.3f}")


# ----------------------------------------------------------------- estadística
def wilcoxon(diffs):
    """Wilcoxon de rangos con signo, aproximación normal con corrección de empates.
    Devuelve (estadístico W, p bilateral, n efectivo). Sin dependencias externas."""
    nz = [d for d in diffs if d != 0.0]
    n = len(nz)
    if n < 6:
        return float("nan"), float("nan"), n
    order = sorted(range(n), key=lambda i: abs(nz[i]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(nz[order[j + 1]]) == abs(nz[order[i]]):
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    w_pos = sum(r for r, d in zip(ranks, nz) if d > 0)
    w_neg = sum(r for r, d in zip(ranks, nz) if d < 0)
    w = min(w_pos, w_neg)
    mu = n * (n + 1) / 4.0
    tie_groups = defaultdict(int)
    for d in nz:
        tie_groups[abs(d)] += 1
    tie_corr = sum(t ** 3 - t for t in tie_groups.values()) / 48.0
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0 - tie_corr)
    if sigma == 0:
        return w, float("nan"), n
    z = (w - mu + 0.5) / sigma
    p = 2.0 * 0.5 * math.erfc(abs(z) / math.sqrt(2))
    return w, min(1.0, p), n


def bootstrap_ci(diffs, reps=10000, alpha=0.05, seed=12345):
    """IC del ΔPAR-2 medio por remuestreo de instancias."""
    if not diffs:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    n = len(diffs)
    means = []
    for _ in range(reps):
        means.append(sum(diffs[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return means[int(alpha / 2 * reps)], means[int((1 - alpha / 2) * reps)]


def mcnemar(b, c):
    """Prueba exacta binomial de McNemar sobre los discordantes (b, c)."""
    n = b + c
    if n == 0:
        return float("nan")
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n) * 2
    return min(1.0, p)


# -------------------------------------------------------------------------- A/B
def compare(path_a, path_b, as_md=False, time_col="cpu_s"):
    ra, rb = load(path_a), load(path_b)
    la = ra[0]["label"] or "A"
    lb = rb[0]["label"] or "B"
    ia, ib = per_instance(ra, time_col), per_instance(rb, time_col)
    common = sorted(set(ia) & set(ib))
    if not common:
        raise SystemExit("A y B no comparten instancias")
    if len(common) < max(len(ia), len(ib)):
        print(f"[aviso] solo {len(common)} instancias en común de {len(ia)}/{len(ib)}")

    diffs = [ib[i]["par2"] - ia[i]["par2"] for i in common]   # negativo => B mejor
    mean_d = sum(diffs) / len(diffs)
    lo, hi = bootstrap_ci(diffs)
    w, p_w, n_eff = wilcoxon(diffs)
    b = sum(1 for i in common if ia[i]["always"] and not ib[i]["always"])   # A sí, B no
    c = sum(1 for i in common if not ia[i]["always"] and ib[i]["always"])   # B sí, A no
    p_mc = mcnemar(b, c)
    sa, sb = summarize(ra, time_col), summarize(rb, time_col)
    flaky_fixed = sum(1 for i in common if ia[i]["flaky"] and ib[i]["always"])
    flaky_broken = sum(1 for i in common if ia[i]["always"] and ib[i]["flaky"])

    rel = (-mean_d / sa["par2"] * 100) if sa["par2"] else 0.0
    if as_md:
        print(f"### A/B — A = `{la}` vs B = `{lb}`\n")
        print(f"Banco: {len(common)} instancias comunes · timeout {sa['budget']:.0f}s · "
              f"{sa['runs'] // max(1, sa['instances'])} seeds/instancia · tiempo de CPU\n")
        print("| métrica | A | B | Δ (B−A) |")
        print("|---|---:|---:|---:|")
        print(f"| PAR-2 (s) | {sa['par2']:.3f} | {sb['par2']:.3f} | **{mean_d:+.3f}** ({-rel:+.1f}%) |")
        print(f"| resueltas en todas las seeds | {sa['solved_all_seeds']} | {sb['solved_all_seeds']} | {sb['solved_all_seeds']-sa['solved_all_seeds']:+d} |")
        print(f"| flaky | {sa['flaky']} | {sb['flaky']} | {sb['flaky']-sa['flaky']:+d} |")
        print(f"| p90 ratio entre seeds | {sa['seed_ratio_p90']:.2f}x | {sb['seed_ratio_p90']:.2f}x | — |")
        print()
        print(f"- ΔPAR-2 medio = **{mean_d:+.3f} s**, IC95% bootstrap = [{lo:+.3f}, {hi:+.3f}] "
              f"({'excluye 0 → efecto detectable' if lo*hi > 0 else 'incluye 0 → no concluyente'})")
        print(f"- Wilcoxon emparejado: W={w:.1f}, p={p_w:.4f} (n efectivo={n_eff})")
        print(f"- McNemar sobre resueltas: A-sí/B-no={b}, A-no/B-sí={c}, p={p_mc:.4f}")
        print(f"- Robustez: flaky→estable = {flaky_fixed}, estable→flaky = {flaky_broken}")
        return

    print(f"Comparación A/B   A = {la}   vs   B = {lb}")
    print(f"{'instancia':<42} {'A PAR-2':>9} {'B PAR-2':>9} {'Δ':>9}")
    print("-" * 74)
    for i in common:
        d = ib[i]["par2"] - ia[i]["par2"]
        mark = "  B mejor" if d < -1e-6 else ("  A mejor" if d > 1e-6 else "")
        print(f"{i:<42} {ia[i]['par2']:>9.3f} {ib[i]['par2']:>9.3f} {d:>9.3f}{mark}")
    print()
    print_summary(f"A = {la}", sa)
    print()
    print_summary(f"B = {lb}", sb)
    print("\n== Contraste estadístico (ADR-0003 §3)")
    print(f"   ΔPAR-2 medio (B−A):  {mean_d:+.3f} s   ({-rel:+.1f}% respecto de A; negativo = B mejor)")
    print(f"   IC95% bootstrap:     [{lo:+.3f}, {hi:+.3f}]  -> "
          f"{'EXCLUYE el 0: efecto detectable' if lo*hi > 0 else 'INCLUYE el 0: no concluyente'}")
    print(f"   Wilcoxon emparejado: W={w:.1f}  p={p_w:.4f}  (n efectivo={n_eff})")
    print(f"   McNemar (resueltas): A-sí/B-no={b}  A-no/B-sí={c}  p={p_mc:.4f}")
    print(f"   Robustez:            flaky→estable={flaky_fixed}   estable→flaky={flaky_broken}")
    if len(common) < 30:
        print(f"   [aviso] n={len(common)}: con este tamaño solo se detectan efectos grandes.")
        print("           Un resultado no significativo aquí NO es evidencia de ausencia de efecto.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="+", help="uno (resumen) o dos (A/B) CSV de run_experiment.py")
    ap.add_argument("--by-family", action="store_true")
    ap.add_argument("--md", action="store_true", help="salida Markdown para pegar en docs/")
    ap.add_argument("--wall", action="store_true", help="usar wall-clock en vez de tiempo de CPU")
    args = ap.parse_args()
    col = "wall_s" if args.wall else "cpu_s"

    if len(args.csv) == 1:
        rows = load(args.csv[0])
        print_summary(args.csv[0], summarize(rows, col))
        if args.by_family:
            print_by_family(rows, col)
    elif len(args.csv) == 2:
        compare(args.csv[0], args.csv[1], as_md=args.md, time_col=col)
    else:
        ap.error("máximo dos CSV")


if __name__ == "__main__":
    main()
