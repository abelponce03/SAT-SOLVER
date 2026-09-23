#!/usr/bin/env python3
"""
gauss_xor.py — decide con eliminación de Gauss en GF(2) una CNF que sea un
sistema de restricciones XOR más cláusulas unitarias (research/06).

Cada XOR de k variables tiene que aparecer como sus 2^(k-1) cláusulas; si la
CNF contiene cualquier otra cosa, el guion lo dice y termina con código 2.
Sirve para comprobar qué instancias son sistemas lineales puros y lo que
tardaría la eliminación de Gauss en decidirlas.

Uso: python3 scripts/gauss_xor.py instancia.cnf[.xz]
"""
import lzma
import sys
import time
from collections import defaultdict


def main():
    t0 = time.time()
    grupos, unidades = defaultdict(set), []
    abrir = lzma.open if sys.argv[1].endswith(".xz") else open
    for linea in abrir(sys.argv[1], "rt"):
        if linea[0] in "cp":
            continue
        lits = [int(x) for x in linea.split()[:-1]]
        if len(lits) == 1:
            unidades.append(lits[0])
        elif lits:
            grupos[tuple(sorted(abs(x) for x in lits))].add(tuple(sorted(lits)))
    filas = []
    for vs, cls in grupos.items():
        paridades = {sum(x < 0 for x in c) % 2 for c in cls}
        if len(cls) != 2 ** (len(vs) - 1) or len(paridades) != 1:
            print(f"no es un sistema XOR puro (variables {vs[:6]}…)")
            sys.exit(2)
        # La asignación que falsea una cláusula pone a 1 sus literales negativos:
        # su paridad es q, y el XOR exige la contraria.
        q = paridades.pop()
        mascara = 0
        for v in vs:
            mascara |= 1 << v
        filas.append((mascara, 1 - q))
    filas += [(1 << abs(u), 1 if u > 0 else 0) for u in unidades]
    pivotes = {}
    for m, b in filas:
        while m:
            h = m.bit_length() - 1
            if h not in pivotes:
                pivotes[h] = (m, b)
                break
            pm, pb = pivotes[h]
            m, b = m ^ pm, b ^ pb
        else:
            if b:
                print(f"UNSAT (0 = 1) en {time.time() - t0:.2f} s; rango {len(pivotes)}")
                return
    print(f"SAT (sistema consistente) en {time.time() - t0:.2f} s; rango {len(pivotes)}, "
          f"{len(filas)} ecuaciones")


if __name__ == "__main__":
    main()
