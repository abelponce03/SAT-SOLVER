# EXP-011 — mclique v2: presupuesto de trabajo determinista (preregistrado)

- **Estado**: **preregistrado**. Se escribe **antes** de mirar ningún
  resultado de mclique v2 sobre el banco (ADR-0003 §6); ver §5 sobre la traza
  de diagnóstico.
- **Fecha**: 2026-09-23
- **Origen**: EXP-010, parte 1 (§6 de EXP-010).
- **Decide**: la adopción de mclique (D-005, opción c; issue #9), junto con los
  datos de EXP-010.

---

## 1. Contexto

- EXP-010, parte 1: mclique v1 da **la misma CNF que cliquer en 72 de 74**
  instancias, y refuta dentro de satsuma las 5 que refuta cliquer y una más
  (`65bf849f`).
- Pero en `9ba8145e` (4,6 M cláusulas) satsuma llega al tope de 60 s con
  mclique v1, y el criterio preregistrado de EXP-010 no admite topes nuevos.
  **mclique v1 no se puede adoptar.**
- **Diagnóstico** (exploratorio, con una build de traza que no es la del
  experimento):
  - la llamada que no termina recibe un grafo de 896 vértices y 304 624 aristas
    (densidad 0,76, casi regular: grado 679–683);
  - la clique voraz inicial ya tiene 90 vértices, y ninguna búsqueda aleatoria
    encontró más;
  - lo caro es **demostrar** que no hay una de 91: la cota por coloreado voraz
    da 163 colores, y DSATUR, 129. Una implementación de prueba del algoritmo de
    Östergård (2002) tampoco termina en 60 s con ningún orden de vértices;
  - el build con cliquer pasa ese paso en menos de 3 s. No se ha investigado
    por qué, porque exigiría leer cliquer.
- **Cambio (mclique v2)**: la búsqueda exacta tiene un **presupuesto de trabajo
  determinista** de 5·10⁸ unidades (|P| · palabras por nodo). Si se agota,
  devuelve la mayor clique encontrada hasta entonces, ampliada hasta ser
  maximal. En el grafo de arriba se corta a los ~0,7 s con la clique de 90.
- **Por qué es seguro**: satsuma usa la clique solo para ordenar las columnas
  antes de romper la simetría. Cualquier orden da predicados y pruebas
  correctos; sin cliques, satsuma ni siquiera reordena. Aun así, las pruebas y
  los modelos se verifican (H3).

## 2. Hipótesis

> **H1 (sin topes).** satsuma con mclique v2 termina con código 0 en las 74
> instancias de `bench/symm2026`, sin topes de 60 s.
>
> **H2 (lo demás no cambia).** Donde el presupuesto no se agota, v2 da la misma
> CNF que v1. Se informa en cuántas de las 74 coincide.
>
> **H3 (seguridad, vinculante).** Todas las respuestas de v2 en la parte 2 se
> verifican contra la CNF original.

## 3. Diseño

### Parte 1 — solo satsuma

```bash
python3 scripts/compare_satsuma_builds.py --bench bench/symm2026 \
    --build mit=tools/satsuma --build mclique1=tools/satsuma-mclique-v1 \
    --build mclique2=tools/satsuma-mclique \
    --build cliques=/tmp/satsuma-cliques/build/satsuma \
    --out results/exp011/satsuma.csv
```

- Binarios: `tools/satsuma-mclique-v1` es el de EXP-010 (SHA-1 `e13f27f7…`);
  `tools/satsuma-mclique` es v2 (SHA-1 `1325c402…`), compilado con
  `get_tools.sh` desde este commit.

### Parte 2 — kissat donde v2 cambia la fórmula

- **Instancias**: las de la parte 1 con SHA-1(`mclique2`) ≠ SHA-1(`mclique1`) y
  SHA-1(`mclique2`) ≠ SHA-1(`mit`). En las demás, kissat recibe una fórmula ya
  medida en EXP-010 (parte 2) o idéntica a la de `mit`. Lista en
  `results/exp011/instancias.txt`.
- Ramas, semillas, T y verificación: **las mismas que EXP-010 parte 2**, con
  B = `LABESAT_SATSUMA=tools/satsuma-mclique` (v2) y resultados en
  `results/exp011/`. Se ejecuta después de EXP-010 parte 2.

El análisis lo hace `scripts/analyze_exp011.py` (`--write-list` escribe la
lista de la parte 2), commiteado junto con este preregistro.

## 4. Criterio de decisión (adopción de mclique v2), fijado ahora

Para cada instancia de EXP-010 parte 2, el resultado de v2 es:

- el de EXP-011 parte 2, si la instancia está en su lista;
- el de v1 en EXP-010, si SHA-1(v2) = SHA-1(v1).

Con eso se aplican **los mismos criterios de EXP-010 §4** a v2:

| resultado | decisión |
|---|---|
| H1 de este experimento, y H1 (≥ 5 de R6), H2 (0 pérdidas) y H3 (0 fallos) de EXP-010 evaluados para v2 | **Adoptar mclique v2**, con las actualizaciones de EXP-010 §4 |
| Fallo de seguridad | No adoptar; buscar la causa |
| Cualquier otro fallo | No adoptar todavía; D-005 a la próxima reunión |

## 5. Amenazas a la validez

- **El presupuesto se fijó mirando este banco**: se eligió por **tiempo**
  (~0,7 s en el grafo difícil), sin mirar ninguna CNF de salida ni ningún
  resultado de kissat. Mientras se escribía este documento corría una traza de
  diagnóstico (build aparte) que registra el trabajo de cada búsqueda en las 74
  instancias; el valor 5·10⁸ quedó fijado **antes** de leerla. Si la traza
  muestra que el presupuesto se agota en otras instancias, se informa aquí,
  pero no se reajusta el valor.
- **Generalización**: un grafo difícil en 74 instancias no dice cuántos habrá
  en la competición. El presupuesto acota el coste por búsqueda, pero no el
  número de búsquedas.
- Las de EXP-010 §5.

## 6. Incidencias de ejecución

_Ninguna por ahora._

## 7. Resultados

_Pendiente._
