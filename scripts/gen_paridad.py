#!/usr/bin/env python3
"""
gen_paridad.py — familias sintéticas de paridad INSATISFACIBLES, para probar
la refutación por eliminación de Gauss con prueba (research/09, X1).

Son las familias clásicas que separan resolución de sistemas más fuertes:

  tseitin-malla W H      Tseitin en una malla toroidal W×H (grado 4) con
                         cargas aleatorias de suma impar (Tseitin, 1968).
  tseitin-regular N D    Tseitin en un grafo D-regular aleatorio de N
                         vértices (expansor con alta probabilidad: exige
                         refutaciones de resolución exponenciales,
                         Urquhart, 1987).
  lights-out N           Lights-out N×N con un objetivo sin solución (solo
                         existe si la matriz de pulsaciones es singular:
                         N = 4, 5, 9, 11, 14, 16, 17, 19, 23, 24…).
  dos-ordenes N          x1 ⊕ … ⊕ xN = 0 y = 1, cada una codificada como
                         cadena de Tseitin con variables auxiliares, en dos
                         órdenes aleatorios distintos (Chew y Heule, 2020).

Cada XOR de k variables se escribe con sus 2^(k-1) cláusulas. La semilla fija
la instancia. Con --sat se genera la variante SATISFACIBLE de la misma familia
(carga par, objetivo alcanzable, misma paridad en los dos órdenes): sirve para
comprobar que X1 no refuta lo que tiene solución. Uso:
  python3 scripts/gen_paridad.py FAMILIA PARÁMETROS... --seed S [--sat] > f.cnf
"""
import argparse
import random
import sys


def clausulas_xor(vs, b):
    """Las 2^(k-1) cláusulas de x_1 ⊕ … ⊕ x_k = b."""
    k = len(vs)
    out = []
    for m in range(1 << k):
        # m pone a 1 las variables de la asignación que se prohíbe
        if bin(m).count("1") % 2 != b:
            out.append([(-v if (m >> i) & 1 else v) for i, v in enumerate(vs)])
    return out


def tseitin(aristas, nv, rnd, sat=False):
    """Una variable por arista; en cada vértice, XOR de sus aristas = carga.
    Cargas aleatorias con suma impar: insatisfacible en un grafo conexo.
    Con suma par es satisfacible."""
    inc = [[] for _ in range(nv)]
    for e, (u, v) in enumerate(aristas, 1):
        inc[u].append(e)
        inc[v].append(e)
    carga = [rnd.randint(0, 1) for _ in range(nv)]
    if sum(carga) % 2 != (0 if sat else 1):
        carga[0] ^= 1
    cls = []
    for u in range(nv):
        cls += clausulas_xor(inc[u], carga[u])
    return len(aristas), cls


def malla(w, h):
    a = []
    for y in range(h):
        for x in range(w):
            u = y * w + x
            a.append((u, y * w + (x + 1) % w))
            a.append((u, ((y + 1) % h) * w + x))
    return a, w * h


def conexo(aristas, n):
    """Tseitin con carga impar solo es insatisfacible si el grafo es conexo."""
    ady = [[] for _ in range(n)]
    for u, v in aristas:
        ady[u].append(v)
        ady[v].append(u)
    vistos, pila = {0}, [0]
    while pila:
        for v in ady[pila.pop()]:
            if v not in vistos:
                vistos.add(v)
                pila.append(v)
    return len(vistos) == n


def regular(n, d, rnd):
    """Grafo d-regular simple por el modelo de configuración con reintentos."""
    assert n * d % 2 == 0
    for _ in range(1000):
        puntos = [u for u in range(n) for _ in range(d)]
        rnd.shuffle(puntos)
        a = [(puntos[i], puntos[i + 1]) for i in range(0, len(puntos), 2)]
        if all(u != v for u, v in a) and len({(min(u, v), max(u, v)) for u, v in a}) == len(a) \
                and conexo(a, n):
            return a, n
    sys.exit("no se encontró un grafo regular simple")


def rango_y_nucleo(filas, n):
    """Gauss en GF(2) sobre filas (enteros como vectores de bits): devuelve un
    vector y ≠ 0 con y·A = 0 (combinación de filas nula), o None."""
    piv, hist = {}, []
    for i, f in enumerate(filas):
        h = 1 << i
        while f:
            p = f.bit_length() - 1
            if p not in piv:
                piv[p] = (f, h)
                break
            f ^= piv[p][0]
            h ^= piv[p][1]
        if not f:
            return h
    return None


def lights_out(n, rnd, sat=False):
    """Pulsar la casilla c cambia c y sus vecinas. Objetivo t sin solución:
    si y·A = 0 con y ≠ 0 (A simétrica), basta y·t = 1."""
    idx = lambda x, y: y * n + x
    vec = []
    for y in range(n):
        for x in range(n):
            vs = [idx(x, y)] + [idx(a, b) for a, b in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
                                if 0 <= a < n and 0 <= b < n]
            vec.append(sorted(vs))
    filas = [sum(1 << v for v in vs) for vs in vec]
    y_ = rango_y_nucleo(filas, n * n)
    if y_ is None:
        sys.exit(f"lights-out {n}×{n} es invertible: todo objetivo tiene solución")
    if sat:  # objetivo en la imagen: t = A·x con x aleatorio
        x = [rnd.randint(0, 1) for _ in range(n * n)]
        t = [sum(x[v] for v in vs) % 2 for vs in vec]
    else:
        t = [rnd.randint(0, 1) for _ in range(n * n)]
        if sum(t[i] for i in range(n * n) if (y_ >> i) & 1) % 2 == 0:
            i = (y_ & -y_).bit_length() - 1
            t[i] ^= 1
    cls = []
    for c, vs in enumerate(vec):
        cls += clausulas_xor([v + 1 for v in vs], t[c])
    return n * n, cls


def cadena(orden, b, sig):
    """x_{o1} ⊕ … ⊕ x_{oN} = b como cadena de XOR de 3 variables con auxiliares."""
    cls, prev = [], orden[0]
    for x in orden[1:-1]:
        t = sig[0]
        sig[0] += 1
        cls += clausulas_xor([prev, x, t], 0)  # t = prev ⊕ x
        prev = t
    cls += clausulas_xor([prev, orden[-1]], b)
    return cls


def dos_ordenes(n, rnd, sat=False):
    sig = [n + 1]
    o1, o2 = list(range(1, n + 1)), list(range(1, n + 1))
    rnd.shuffle(o1)
    rnd.shuffle(o2)
    cls = cadena(o1, 0, sig) + cadena(o2, 0 if sat else 1, sig)
    return sig[0] - 1, cls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("familia", choices=["tseitin-malla", "tseitin-regular", "lights-out", "dos-ordenes"])
    ap.add_argument("params", nargs="+", type=int)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--sat", action="store_true", help="variante satisfacible")
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    if a.familia == "tseitin-malla":
        nv, cls = tseitin(*malla(*a.params), rnd, a.sat)
    elif a.familia == "tseitin-regular":
        ar, n = regular(a.params[0], a.params[1], rnd)
        nv, cls = tseitin(ar, n, rnd, a.sat)
    elif a.familia == "lights-out":
        nv, cls = lights_out(a.params[0], rnd, a.sat)
    else:
        nv, cls = dos_ordenes(a.params[0], rnd, a.sat)
    rnd.shuffle(cls)  # sin pistas de orden para el solver
    out = sys.stdout
    estado = "SAT" if a.sat else "UNSAT"
    out.write(f"c {a.familia} {' '.join(map(str, a.params))} seed {a.seed} ({estado} por construcción)\n")
    out.write(f"p cnf {nv} {len(cls)}\n")
    for c in cls:
        out.write(" ".join(map(str, c)) + " 0\n")


if __name__ == "__main__":
    main()
