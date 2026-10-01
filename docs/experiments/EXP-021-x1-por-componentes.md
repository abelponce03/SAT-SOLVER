# EXP-021 — X1 v2: Gauss por componentes conexas (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con
  `scripts/exp021.py` y `results/exp021/muestra.csv`. La implementación
  (research/09 §3.4, commit `14f2a2e`) solo se ha ejecutado en
  `test_gauss.sh`, con familias sintéticas.
- **Fecha**: 2026-10-01
- **Decide**: si la versión de X1 que se activa por defecto es la v2 (por
  componentes) o la v1 que validó EXP-019.

---

## 1. Qué se quiere saber

- EXP-019 adoptó X1 (v1). En 103 de 577 instancias, la v1 **se saltó el
  sistema XOR**: la matriz entera, con el historial, superaba los topes.
- La v2 parte el sistema en componentes conexas (Lema 6) y elimina cada una
  por separado, con el tope de memoria por componente y un presupuesto de
  trabajo común.
- Por el Lema 6 es igual de correcta. Queda medir lo mismo que en EXP-019
  justo donde la v2 actúa distinto:
  - que no se equivoca;
  - que no cambia la búsqueda cuando no refuta;
  - que no cuesta más de lo admitido;
  - y cuántos de esos sistemas pasa a procesar y a refutar.

## 2. Hipótesis

Son las de EXP-019, con los mismos umbrales, sobre las 103 instancias:

> **H0 (seguridad, vinculante).** Ninguna refutación de instancias SAT
> conocidas (35 en la muestra). Toda refutación con prueba verificada por
> los dos `dsr-trim`.
>
> **H1 (equivalencia, vinculante).** Contadores idénticos con `--gauss=1` y
> `--gauss=0` (20 000 conflictos, semilla 1) donde no refuta.
>
> **H2 (coste).** Tiempo de X1 por instancia con p95 ≤ 1 s y máximo ≤ 10 s.
>
> **H3 (cobertura, descriptiva).** Cuántas instancias pasan de «saltada» a
> «consistente» o a «refutada».

**Predicción honesta**:

- H0 y H1 se cumplen (Lema 6 y `test_gauss.sh`).
- H2 es la incertidumbre: la v2 hace más trabajo en estas instancias, y el
  presupuesto común (`gaussops` = 4·10⁹ operaciones de palabra) puede
  llevar a algunas cerca de 2–4 s.
- H3: la mayoría pasa a «consistente», porque en la industria las XOR son
  puertas que se definen unas a otras. Pocas o ninguna refutación, aunque
  hay 41 UNSAT en la muestra.

## 3. Diseño

- **Binario**: `solver/kissat/build-x1v2/kissat`, con
  `./scripts/build.sh --dir=build-x1v2 --gauss`, compilado por la cola desde
  el commit de este preregistro (paso `exp021-construir`).
- **Muestra** (`exp021.py muestra`): las 103 instancias con resultado
  «saltada» en `results/exp019/x1.csv`.
- **Corridas**: `exp021.py correr` y `exp021.py equivalencia`. Son el
  arnés de EXP-019 (`exp019.py`) con otras rutas, la misma medida.
- **Análisis**: `exp021.py analizar`, que es el de EXP-019 más la tabla
  v1 → v2.
- **Cuándo**: en la cola, después de EXP-009 y antes de EXP-020. Coste
  estimado: ~1 h (X1 solo y ~100 parejas de equivalencia).

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| H0, H1 y H2 | Se activa por defecto **X1 v2**: `build.sh` compila con `--gauss` y la opción vale 1 |
| H0 y H1, pero no H2 | Se activa la v2 con el presupuesto de trabajo reducido hasta cumplir H2 en estas instancias, o la v1 si no se puede |
| H0 o H1 fallan | Se activa la **v1** (EXP-019) y se busca el fallo de la v2 |

## 5. Amenazas a la validez

- La muestra la eligió el resultado de la v1: es justo donde la v2 actúa
  distinto.
- En el resto de instancias, el sistema cabía entero. Ahí v1 y v2 dan el
  **mismo resultado** (refutada o consistente) por el Lema 6. Solo pueden
  diferir:
  - el certificado elegido, con su prueba, igual de válida;
  - el tiempo.
- En ninguna de las dos versiones toca X1 el estado del solver cuando no
  refuta. Aun así, H1 se vuelve a comprobar aquí: no se hereda de EXP-019.
- Mismo arnés y misma máquina que EXP-019, con un tope de 6 GB por proceso.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
