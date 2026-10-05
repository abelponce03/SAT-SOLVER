#!/usr/bin/env python3
"""
x1b_potencial.py — EXP-025: ¿cuánto podría aportar X1b (research/09 §5)?

X1b llevaría el sistema XOR de la CNF a forma escalonada REDUCIDA (Gauss-
Jordan) y añadiría, con prueba DRAT, las filas que quedan con una variable
(unidades) o con dos (equivalencias x = y ⊕ b).  Antes de construirlo en
Kissat (registrar variables de extensión, prueba sin borrados), este guion
mide si hay algo que ganar: cuenta, por instancia, las unidades y
equivalencias implicadas por el sistema que NO están ya en la CNF.

- Extracción: la misma de X1 (x1_gauss.extraer_xor, k <= --max-k).
- Componentes conexas (como X1 v2); se salta una componente con más de
  --max-filas filas o --max-cols columnas (se cuenta como saltada).
- Antes de Gauss, propagación unitaria en la raíz: las variables fijadas
  salen de las filas (como en X1), así que una unidad nueva es una que la
  propagación no deduce.
- Unidad nueva: fila reducida con una variable.
- Equivalencia nueva: fila reducida con dos variables {x, y} que no es una
  XOR de dos variables de la CNF (las dos binarias).  No se descuentan las
  equivalencias que ya deduciría el cierre por congruencia de Kissat: el
  recuento es una COTA SUPERIOR de lo que X1b añadiría.
- Determinista: no mide tiempo de búsqueda; el tiempo que informa es el del
  propio diagnóstico, solo para dimensionar.

Uso:
  python3 scripts/x1b_potencial.py --muestra results/exp019/muestra.csv \\
      results/exp019/muestra-dev.csv --out results/exp027/x1b.csv
Reanuda: salta las instancias ya escritas en --out (ADR-0008).
"""
import argparse
import csv
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checkpoint import EscritorDuradero, filas_completas  # noqa: E402
from x1_gauss import extraer_xor, leer  # noqa: E402

CAMPOS = ["instance", "bank", "known", "filas", "variables", "componentes",
          "saltadas", "filas_saltadas", "rango", "inconsistente",
          "unidades_nuevas", "equivalencias_nuevas", "equivalencias_en_cnf",
          "segundos"]


def propagar(cls):
    """Propagación unitaria en la raíz con listas de ocurrencias.  Devuelve
    {variable: bool} o None si la CNF es inconsistente por propagación."""
    occ = defaultdict(list)
    for i, c in enumerate(cls):
        for x in c:
            occ[x].append(i)
    val, cola = {}, []

    def asignar(x):
        v = val.get(abs(x))
        if v is None:
            val[abs(x)] = x > 0
            cola.append(x)
            return True
        return v == (x > 0)

    for c in cls:
        if len(c) == 1 and not asignar(c[0]):
            return None
    while cola:
        x = cola.pop()
        for i in occ[-x]:            # cláusulas donde x se hace falso
            libre, sat, n = None, False, 0
            for y in cls[i]:
                v = val.get(abs(y))
                if v is None:
                    libre, n = y, n + 1
                    if n > 1:
                        break
                elif v == (y > 0):
                    sat = True
                    break
            if sat or n > 1:
                continue
            if n == 0 or not asignar(libre):
                return None
    return val


def componentes(filas):
    padre = {}

    def raiz(x):
        while padre.setdefault(x, x) != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for vs, _ in filas:
        r = raiz(vs[0])
        for v in vs[1:]:
            s = raiz(v)
            if s != r:
                padre[s] = r
    grupos = defaultdict(list)
    for i, (vs, _) in enumerate(filas):
        grupos[raiz(vs[0])].append(i)
    return list(grupos.values())


def gauss_jordan(filas, idx):
    """Forma escalonada reducida de las filas 'idx'.  Devuelve (rango,
    inconsistente, lista de (variables, paridad) de las filas reducidas)."""
    col, var = {}, []
    for i in idx:
        for v in filas[i][0]:
            if v not in col:
                col[v] = len(var)
                var.append(v)
    piv = {}   # bit de pivote -> (máscara, paridad)
    inconsistente = False
    for i in idx:
        vs, b = filas[i]
        m = 0
        for v in vs:
            m ^= 1 << col[v]
        while m:
            p = m.bit_length() - 1
            if p not in piv:
                piv[p] = [m, b]
                break
            m ^= piv[p][0]
            b ^= piv[p][1]
        if not m and b:
            inconsistente = True
    # Hacia atrás: quitar cada pivote de las demás filas (de menor a mayor
    # pivote, cada fila solo tiene bits <= su pivote).
    orden = sorted(piv)
    for k, p in enumerate(orden):
        mp, bp = piv[p]
        bit = 1 << p
        for q in orden[k + 1:]:
            if piv[q][0] & bit:
                piv[q][0] ^= mp
                piv[q][1] ^= bp
    reducidas = []
    for p in orden:
        m, b = piv[p]
        if m.bit_count() <= 2:
            vs = [var[j] for j in range(m.bit_length()) if (m >> j) & 1]
            reducidas.append((vs, b))
    return len(piv), inconsistente, reducidas


def analizar(path, max_k, max_filas, max_cols):
    t0 = time.time()
    _, cls = leer(path)
    fijas = propagar(cls)
    if fijas is None:
        return {**{k: 0 for k in CAMPOS[3:]}, "inconsistente": 1,
                "segundos": round(time.time() - t0, 2)}
    # Las fijadas por propagación salen de la fila y ajustan su paridad (como
    # en X1): lo que X1b aportaría es lo que la propagación no ve.
    filas = []
    for vs, b in extraer_xor(cls, max_k):
        libres = [v for v in vs if v not in fijas]
        for v in vs:
            if v in fijas:
                b ^= fijas[v]
        if libres:
            filas.append((libres, b))
    unidades_cnf = set(fijas)
    pares_cnf = {tuple(vs) for vs, _ in filas if len(vs) == 2}
    fila = {"filas": len(filas), "variables": len({v for vs, _ in filas for v in vs}),
            "componentes": 0, "saltadas": 0, "filas_saltadas": 0, "rango": 0,
            "inconsistente": 0, "unidades_nuevas": 0, "equivalencias_nuevas": 0,
            "equivalencias_en_cnf": len(pares_cnf)}
    if not filas:
        fila["segundos"] = round(time.time() - t0, 2)
        return fila
    for idx in componentes(filas):
        fila["componentes"] += 1
        ncols = len({v for i in idx for v in filas[i][0]})
        if len(idx) > max_filas or ncols > max_cols:
            fila["saltadas"] += 1
            fila["filas_saltadas"] += len(idx)
            continue
        rango, inc, reducidas = gauss_jordan(filas, idx)
        fila["rango"] += rango
        if inc:
            fila["inconsistente"] = 1
            continue
        for vs, _ in reducidas:
            if len(vs) == 1 and vs[0] not in unidades_cnf:
                fila["unidades_nuevas"] += 1
            elif len(vs) == 2 and tuple(vs) not in pares_cnf:
                fila["equivalencias_nuevas"] += 1
    fila["segundos"] = round(time.time() - t0, 2)
    return fila


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--muestra", nargs="+", required=True,
                    help="CSV con columnas instance, bank, path, known (como los de EXP-019)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-k", type=int, default=6, help="como 'gaussmaxsize' de X1")
    ap.add_argument("--max-filas", type=int, default=4000)
    ap.add_argument("--max-cols", type=int, default=8000)
    args = ap.parse_args()
    filas_in = [r for m in args.muestra for r in csv.DictReader(open(m))]
    previas = filas_completas(args.out, CAMPOS)
    hechas = {r["instance"] for r in previas}
    with EscritorDuradero(args.out, CAMPOS, previas) as ed:
        for n, r in enumerate(filas_in, 1):
            if r["instance"] in hechas:
                continue
            if not os.path.exists(r["path"]):
                sys.exit(f"ABORTADO: falta {r['path']} (¿banco sin enlazar?)")
            fila = analizar(r["path"], args.max_k, args.max_filas, args.max_cols)
            fila.update(instance=r["instance"], bank=r.get("bank", ""), known=r.get("known", ""))
            ed.escribir(fila)
            print(f"[{n}/{len(filas_in)}] {r['instance'][:34]:34} filas={fila['filas']} "
                  f"u={fila['unidades_nuevas']} e={fila['equivalencias_nuevas']} "
                  f"saltadas={fila['saltadas']} {fila['segundos']}s", flush=True)


if __name__ == "__main__":
    main()
