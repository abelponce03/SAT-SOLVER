#!/usr/bin/env python3
"""
x1_gauss.py — prototipo de X1 (research/09): refutar una CNF cuyo subsistema
XOR es inconsistente, con una prueba DRAT que usa variables de extensión.

Pasos (las demostraciones están en research/09 §3):

1. Extracción: se agrupan las cláusulas por conjunto de variables. Un grupo de
   k ≤ --max-k variables es una XOR si contiene sus 2^(k-1) cláusulas, todas
   con la misma paridad de negaciones q; entonces x_1 ⊕ … ⊕ x_k = 1 ⊕ q.
   Las unitarias son XOR de una variable.
2. Gauss en GF(2) con historial: si una fila se reduce a 0 = 1, su historial
   es el certificado S (filas originales cuya suma es 0 = 1). Se comprueba
   sumando de nuevo.
3. Prueba (Teorema 1 de research/09):
   - z, variable nueva, con la unitaria ¬z (RAT);
   - cada conjunto se representa con una cadena ordenada de definiciones
     c_j ↔ c_{j-1} ⊕ x_j (c_0 = z), cuatro cláusulas RAT por definición;
   - Lema 2 (hojas): se deriva la unitaria «salida = paridad» de cada fila
     de S con lemas RUP;
   - Lema 3 (barrido): para C = A Δ B se deriva salida_A ⊕ salida_B ⊕
     salida_C = 0 recorriendo las variables de A ∪ B en orden, con 12
     lemas RUP por variable;
   - las filas se suman en un árbol equilibrado (Teorema 1: tamaño
     O(Σ 2^k_i + N log |S|), con N = Σ k_i);
   - al final, el conjunto vacío con paridad 1 da la unitaria z, que choca
     con ¬z: cláusula vacía.

Uso: python3 scripts/x1_gauss.py f.cnf[.xz] --proof f.drat [--max-k 6]
Salida: «s UNSATISFIABLE» si refuta, «c consistente» si no (código 0).
"""
import argparse
import lzma
import sys
import time
from collections import defaultdict


def leer(path):
    abrir = lzma.open if path.endswith(".xz") else open
    n, cls = 0, []
    with abrir(path, "rt") as f:
        for linea in f:
            if not linea.strip() or linea[0] == "c":
                continue
            if linea[0] == "p":
                n = int(linea.split()[2])
                continue
            lits = [int(x) for x in linea.split()]
            assert lits[-1] == 0, "una cláusula por línea"
            cls.append(lits[:-1])
    return n, cls


def propagar(cls):
    """Propagación unitaria en la raíz de F. Devuelve {variable: valor} o None
    si F es inconsistente por propagación (entonces la prueba es la vacía)."""
    val, cambio = {}, True
    while cambio:
        cambio = False
        for c in cls:
            libres, sat = [], False
            for x in c:
                v = val.get(abs(x))
                if v is None:
                    libres.append(x)
                elif v == (x > 0):
                    sat = True
                    break
            if sat:
                continue
            if not libres:
                return None
            if len(libres) == 1:
                val[abs(libres[0])] = libres[0] > 0
                cambio = True
    return val


def extraer_xor(cls, max_k):
    grupos = defaultdict(set)
    for c in cls:
        vs = tuple(sorted({abs(x) for x in c}))
        if len(vs) == len(c) and 1 <= len(vs) <= max_k:   # sin repetidos ni tautologías
            grupos[vs].add(tuple(sorted(c)))
    filas = []
    for vs, g in grupos.items():
        par = {sum(x < 0 for x in c) % 2 for c in g}
        if len(par) == 1 and len(g) == 1 << (len(vs) - 1):
            filas.append((list(vs), 1 ^ par.pop()))
    return filas


def gauss(filas):
    """Devuelve el certificado S (lista de índices) o None si es consistente."""
    col = {}
    for vs, _ in filas:
        for v in vs:
            col.setdefault(v, len(col))
    piv = {}
    for i, (vs, b) in enumerate(filas):
        m, h = sum(1 << col[v] for v in vs), 1 << i
        while m:
            p = m.bit_length() - 1
            if p not in piv:
                piv[p] = (m, b, h)
                break
            pm, pb, ph = piv[p]
            m, b, h = m ^ pm, b ^ pb, h ^ ph
        if not m and b:
            return [j for j in range(len(filas)) if (h >> j) & 1]
    return None


class Prueba:
    """Escritor de la prueba. Regla de borrado (research/09 §4.3): nunca se
    borra una cláusula que toque una variable fijada en la raíz (z, las
    salidas ya derivadas y las fijadas por propagación en F). Son las
    «unitarias verdaderas» y sus razones, que el dsr-trim de SC2026 maneja mal
    al comprobar hacia atrás."""

    def __init__(self, f, n, borrar, proteger, fijas):
        self.f, self.sig, self.lineas, self.borradas = f, n + 1, 0, 0
        self.borrar, self.proteger, self.fijas = borrar, proteger, set(fijas)
        self.borrar_defs = True

    def nueva(self):
        self.sig += 1
        return self.sig - 1

    def add(self, c):
        self.f.write(" ".join(map(str, c)) + " 0\n")
        self.lineas += 1

    def borra(self, c):
        if not self.borrar or (self.proteger and any(abs(x) in self.fijas for x in c)):
            return
        self.f.write("d " + " ".join(map(str, c)) + " 0\n")
        self.borradas += 1

    def defin(self, t, p, x):
        """t ↔ p ⊕ x: cuatro cláusulas con el pivote t delante (RAT)."""
        cs = [[-t, p, x], [-t, -p, -x], [t, -p, x], [t, p, -x]]
        for c in cs:
            self.add(c)
        return cs


def xor_cnf(vs, b):
    """CNF de la XOR sobre el multiconjunto vs (las repetidas se cancelan)."""
    cuenta = defaultdict(int)
    for v in vs:
        cuenta[v] ^= 1
    vs = [v for v in cuenta if cuenta[v]]
    k = len(vs)
    if k == 0:
        return [[]] if b else []
    out = []
    for m in range(1 << k):
        if bin(m).count("1") % 2 != b:
            out.append([(-v if (m >> i) & 1 else v) for i, v in enumerate(vs)])
    return out


class Nodo:
    """Un conjunto de variables con su paridad y su cadena ordenada."""

    def __init__(self, P, vs, b, z):
        self.vs, self.b = sorted(vs), b
        self.cadena, self.defs = {}, []
        prev = z
        for v in self.vs:
            t = P.nueva()
            self.defs += P.defin(t, prev, v)
            self.cadena[v] = prev = t
        self.salida = prev  # z si el conjunto es vacío


def derivar_por_casos(P, nuevas, v, unidad_z):
    """Añade cada cláusula E de 'nuevas' vía E ∨ v y E ∨ ¬v (RUP)."""
    for E in nuevas:
        if E == unidad_z:
            continue
        P.add(E + [v])
        P.add(E + [-v])
        P.add(E)
        if len(E) == 1:
            P.fijas.add(abs(E[0]))
        P.borra(E + [v])
        P.borra(E + [-v])


def hoja(P, nodo, z):
    """Lema 2: de las cláusulas originales de la XOR a la unitaria de su salida."""
    b = nodo.b
    previas = None  # L_0 son las propias cláusulas originales (no se borran)
    for j, v in enumerate(nodo.vs):
        L = xor_cnf([nodo.cadena[v]] + nodo.vs[j + 1:], b)
        derivar_por_casos(P, L, v, [-z])
        if previas:
            for E in previas:
                P.borra(E)
        previas = L
    return nodo  # la última L es la unitaria de la salida


def combinar(P, A, B, C, z):
    """Lema 3: C = A Δ B y la unitaria de su salida."""
    assert set(C.vs) == set(A.vs) ^ set(B.vs) and C.b == A.b ^ B.b
    a = b = c = z
    previas = [[-z]]
    for v in sorted(set(A.vs) | set(B.vs)):
        enA, enB = v in A.cadena, v in B.cadena
        a2 = A.cadena[v] if enA else a
        b2 = B.cadena[v] if enB else b
        c2 = C.cadena[v] if enA != enB else c
        nuevas = xor_cnf([a2, b2, c2], 0)
        derivar_por_casos(P, nuevas, v, [-z])
        for E in previas:
            if E != [-z]:
                P.borra(E)
        previas, a, b, c = nuevas, a2, b2, c2
    # unitaria de la salida de C, por RUP desde las de A y B y el invariante final
    u = [C.salida] if C.b else [-C.salida]
    if u != [-z]:
        P.add(u)
        P.fijas.add(abs(u[0]))
    for E in previas:
        if E != [-z]:
            P.borra(E)
    if P.borrar_defs:
        for d in A.defs + B.defs:
            P.borra(d)
    return C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cnf")
    ap.add_argument("--proof", required=True)
    ap.add_argument("--max-k", type=int, default=6)
    ap.add_argument("--sin-borrados", action="store_true",
                    help="no borrar nada (la prueba es más lenta de comprobar)")
    ap.add_argument("--conservar-defs", action="store_true",
                    help="no borrar las definiciones al terminar con ellas")
    ap.add_argument("--borrar-todo", action="store_true",
                    help="borrar también lo que toca variables fijadas: el dsr-trim de "
                         "SC2026 falla con esto (research/09 §4.3); solo para reproducirlo")
    a = ap.parse_args()
    t0 = time.time()
    n, cls = leer(a.cnf)
    val = propagar(cls)
    if val is None:
        open(a.proof, "w").write("0\n")
        print("c F es inconsistente por propagación unitaria\ns UNSATISFIABLE")
        return
    # Las variables fijadas salen de las filas y ajustan su paridad: las
    # cadenas solo usan variables libres (research/09 §4.3).
    filas = []
    for vs, b in extraer_xor(cls, a.max_k):
        libres = [v for v in vs if v not in val]
        b ^= sum(val[v] for v in vs if v in val) % 2
        if libres:
            filas.append((libres, b))
        elif b:   # todas fijadas y paridad violada: conflicto por propagación
            open(a.proof, "w").write("0\n")
            print("c una XOR queda violada por propagación\ns UNSATISFIABLE")
            return
    t1 = time.time()
    S = gauss(filas)
    t2 = time.time()
    nx = len({v for vs, _ in filas for v in vs})
    print(f"c {len(cls)} cláusulas, {len(filas)} XOR sobre {nx} variables "
          f"(extracción {t1 - t0:.2f} s, Gauss {t2 - t1:.2f} s)")
    if S is None:
        print("c consistente: X1 no hace nada")
        return
    # Comprobación independiente del certificado: la suma es 0 = 1.
    suma, par = set(), 0
    for i in S:
        suma ^= set(filas[i][0])
        par ^= filas[i][1]
    assert not suma and par == 1, "certificado incorrecto"
    N = sum(len(filas[i][0]) for i in S)
    with open(a.proof, "w") as f:
        P = Prueba(f, n, not a.sin_borrados, not a.borrar_todo, list(val))
        z = P.nueva()
        P.add([-z])
        P.fijas.add(z)
        P.borrar_defs = not a.conservar_defs
        # Fase 1: todas las definiciones (RAT) antes que ningún lema ni borrado.
        # El árbol de sumas se conoce de antemano (research/09 §4.3).
        hojas = [Nodo(P, filas[i][0], filas[i][1], z) for i in S]
        niveles, nodos = [], hojas
        while len(nodos) > 1:
            pares = [(nodos[i], nodos[i + 1]) for i in range(0, len(nodos) - 1, 2)]
            sig = [Nodo(P, set(x.vs) ^ set(y.vs), x.b ^ y.b, z) for x, y in pares]
            niveles.append(list(zip(pares, sig)))
            if len(nodos) % 2:
                sig.append(nodos[-1])
            nodos = sig
        assert not nodos[0].vs and nodos[0].b == 1
        # Fase 2: lemas RUP (y borrados), de las hojas a la raíz.
        for h in hojas:
            hoja(P, h, z)
        for nivel in niveles:
            for (x, y), c in nivel:
                combinar(P, x, y, c, z)
        P.add([])  # z (derivada en la última combinación) choca con ¬z
    print(f"c certificado: |S| = {len(S)} filas, N = Σk = {N}; prueba: {P.lineas} líneas añadidas, "
          f"{P.borradas} borradas, {P.sig - n - 1} variables nuevas ({time.time() - t2:.2f} s)")
    print("s UNSATISFIABLE")


if __name__ == "__main__":
    main()
