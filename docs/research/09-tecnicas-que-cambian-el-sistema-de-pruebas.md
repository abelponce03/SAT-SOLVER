# Investigación 09 — Técnicas que cambian el sistema de pruebas: diseño, demostraciones y validación

- **Fecha**: 2026-10-01
- **Pedido del director**: «diseñar las técnicas que cambian el tipo de
  prueba, demostrarlas y documentarlo todo», mientras corren EXP-016 a
  EXP-018.
- **Punto de partida**: research/08 §1 (Corolario 1) demostró que, para un
  CDCL que solo deriva por resolución, ninguna optimización de código evita
  el crecimiento exponencial en ciertas familias. Las únicas palancas que
  cambian el **orden de crecimiento** son las que hacen que el solver
  produzca pruebas de un sistema más fuerte. Este documento las diseña.
- **Estado**:
  - X1 (refutación de sistemas XOR por eliminación de Gauss):
    - diseño y teorema con demostración (§3);
    - prototipo (`scripts/x1_gauss.py`);
    - **implementación en Kissat** (`solver/kissat/src/gauss.c`, detrás de
      `configure --gauss` y de la opción `--gauss`, apagada);
    - validación con los tres verificadores (§4);
    - experimento preregistrado (EXP-019);
  - el resto, analizado y priorizado (§5 y §6).

---

## 0. Resumen

1. **Qué demuestra hoy LabeSAT**:
   - Kissat solo: resolución (más RAT con variables nuevas en `factor`, que
     es BVA);
   - con satsuma: pasos SR para la ruptura de simetrías.

   Las familias que separan sistemas de pruebas (§1) indican qué falta. La
   **paridad** (Tseitin, *lights-out*, XOR-SAT) es exponencial para
   resolución y polinómica con eliminación de Gauss.
2. **X1** extrae el subsistema XOR de la CNF y le aplica Gauss sobre GF(2).
   Si es inconsistente, **emite una refutación DRAT con variables de
   extensión**.
   - **Teorema 1**: la prueba es correcta y tiene tamaño
     O(Σ_{i∈S} 2^{k_i} + N·⌈log₂|S|⌉), con S las filas que suman 0 = 1 y
     N = Σ_{i∈S} k_i.
   - **Corolario 2**: en las fórmulas de Tseitin sobre expansores, X1 da
     pruebas polinómicas donde toda refutación por resolución es
     exponencial.
3. **Validación** (§4.2):
   - El prototipo y la implementación en Kissat generan pruebas que
     verifican `drat-trim` y los dos `dsr-trim` en mallas de Tseitin, grafos
     regulares aleatorios, *lights-out* irresoluble y paridad en dos órdenes.
   - Kissat sin X1 agota 120 s en todas las de Tseitin y paridad en dos
     órdenes; X1 las refuta en 0,1–1,4 s.
   - **Instancia real de 2026**: la *lights-out* `667341ee` (UNSAT;
     CaDiCaL 3 tardó 4717 s y el mejor solver de 2026, 346 s) la refuta X1 en
     **0,02 s**. La prueba verifica en 1,8 s con el `dsr-trim` de SC2026.
4. **Hallazgo crítico (§4.3)**: el `dsr-trim` del commit de SC2026, en su
   modo por defecto (hacia atrás), **se cuelga con violación de segmento**
   si la prueba borra:
   - una cláusula de definición RAT;
   - o ciertos lemas usados para derivar una unitaria.

   La versión actual de `dsr-trim` no falla, y su registro de cambios
   documenta arreglos posteriores en esa zona. Decisión: **las pruebas de X1
   no borran nada**. Además, cualquier técnica nueva que emita RAT se valida
   con el verificador de SC2026.
5. **Prioridad**:
   - X1, implementación en Kissat detrás de `--gauss` (apagada) y
     experimento preregistrado;
   - X1b (unidades y equivalencias implicadas por el sistema XOR);
   - el resto queda analizado y aparcado con su razón (§6).

## 1. Marco: sistemas de pruebas y qué produce LabeSAT

### 1.1 Definiciones

Sea F una CNF.

- **Resolución**: de (C ∨ x) y (D ∨ ¬x) se deriva (C ∨ D). Una refutación
  deriva la cláusula vacía. Los CDCL sin técnicas adicionales generan
  refutaciones de resolución, y viceversa: Beame, Kautz y Sabharwal (2004);
  Pipatsrisawat y Darwiche (2011), research/08 Teorema 2.
- **RUP**: C es RUP respecto de F si la propagación unitaria sobre
  F ∧ ¬C llega a un conflicto. Toda cláusula RUP es implicada por F.
- **RAT** sobre el literal l ∈ C: para toda D ∈ F con ¬l ∈ D, el
  resolvente C ∨ (D \ {¬l}) es RUP. Añadir una cláusula RAT conserva la
  satisfacibilidad, aunque no la equivalencia. Con RAT se pueden
  **introducir variables nuevas**.
- **DRAT**: sucesión de adiciones RUP o RAT y de borrados.
- **ER** (resolución extendida, Tseitin 1968): resolución más definiciones
  t ↔ φ con t nueva. DRAT y ER se simulan polinómicamente
  (Kiesl, Rebola-Pardo y Heule, 2018).
- **PR y SR**: generalizan RAT con un testigo, que es una asignación (PR) o
  una sustitución (SR). Permiten pruebas cortas **sin variables nuevas**
  para el palomar (Heule, Kiesl y Biere, 2017). LabeSAT ya emite SR para la
  ruptura de simetrías (ADR-0004, ADR-0007).

### 1.2 Familias que separan los sistemas

| Familia | Resolución (≡ CDCL) | ER / DRAT | PR / SR sin variables nuevas | ¿Quién la ataca en LabeSAT? |
|---|---|---|---|---|
| Palomar PHPₙ | 2^Ω(n) (Haken, 1985) | Polinómica (Cook, 1976) | Polinómica (Heule, Kiesl y Biere, 2017) | Simetrías (satsuma, SR) |
| Tseitin en expansores | 2^Ω(n) (Urquhart, 1987; Ben-Sasson y Wigderson, 2001) | **Polinómica (Teorema 1)** | No se usa aquí | **Nadie: X1** |
| Paridad con dos órdenes | Difícil (Chew y Heule, 2020) | O(n log n) (Chew y Heule, 2020; Teorema 1) | — | **Nadie: X1** |
| Tablero mutilado | 2^Ω(n) (Alekhnovich, 2004) | Polinómica | Polinómica (Heule, Kiesl y Biere, 2019) | Simetrías, en parte |

**Lectura**:
- LabeSAT ya cubre la columna de simetrías.
- El hueco que queda, con base teórica y casos reales en la competición
  (research/06 §5: *lights-out* UNSAT, *xor-chain*, *tseitin-formulas* en
  2026), es la **paridad**.

### 1.3 Qué técnicas de Kissat ya salen de la resolución

| Técnica | Sistema | Estado |
|---|---|---|
| `factor` (BVA, Manthey, Heule y Biere, 2012) | ER: variables nuevas con cláusulas RAT | Activa; limitada por esfuerzo |
| Cierre por congruencia (Biere et al., 2024) | Resolución con puertas | Activa; no razona con sistemas lineales |
| Ruptura de simetrías (satsuma) | SR | `--symmetry`; B3 en EXP-009 |
| Gauss sobre sistemas XOR | ER | **No existe** (research/06) |

## 2. Candidatas y valor esperado

| # | Técnica | Familias | Valor esperado (datos) | Coste | Prioridad |
|---|---|---|---|---|---|
| **X1** | Refutación de sistemas XOR inconsistentes con prueba ER | Paridad pura o casi pura | 2026: **+4 resueltas, ≈ −112 s de PAR-2** (research/06 §5), más *xor-chain* y *tseitin-formulas* si son UNSAT | Medio: extracción, Gauss, prueba | **1** |
| X1b | Unidades y equivalencias implicadas por el sistema XOR | Mixtas (criptografía, circuitos con XOR) | Sin estimar; en 2026, ningún solver con Gauss ganó en las mixtas (research/06 §5) | Medio: registrar variables nuevas en Kissat | 2 |
| C1 | Cardinalidad: refutar por conteo (Hall) | Palomar y emparejamientos | Solapa con la ruptura de simetrías, que ya da pruebas SR cortas | Alto (pruebas de conteo con BDD) | Aparcada |
| P1 | Aprendizaje de cláusulas PR en el preproceso (PReLearn) | Combinatoria dura | Ganancias en familias académicas (Reeves, Heule y Bryant, 2022); sin datos de la Main Track | Alto (consultas SAT auxiliares) | Aparcada |
| B1 | BVA más agresivo (`factor` de Kissat) | Industriales con AMO | SBVA ganó en 2023, pero Kissat 4.0 ya incluye `factor` | Bajo (ajuste de opciones) | Clase S: A/B preregistrado si se prueba |

## 3. X1: diseño y demostraciones

### 3.1 Extracción del sistema XOR

Para un conjunto de variables V (|V| = k) y b ∈ {0, 1}, la restricción
⊕V = b se escribe en CNF con las 2^(k−1) cláusulas que prohíben cada
asignación de paridad 1 − b.

**Lema 0 (extracción).** Sea G un conjunto de 2^(k−1) cláusulas distintas
cuyas variables son exactamente V, todas con el mismo número de literales
negativos módulo 2, q. Entonces G ≡ (⊕V = 1 − q).

*Demostración.*

- Cada cláusula de G la falsea exactamente una asignación de V: la que pone
  x = 1 si y solo si ¬x está en la cláusula. Esa asignación tiene paridad q.
- Cláusulas distintas falsean asignaciones distintas.
- Hay exactamente 2^(k−1) asignaciones de paridad q, así que G prohíbe
  justo esas: G ≡ (⊕V ≠ q). ∎

La extracción agrupa las cláusulas de F de tamaño ≤ K por conjunto de
variables y se queda con los grupos que cumplen el Lema 0. Cada fila
(V_i, b_i) del sistema la implica F. La extracción es **correcta**, pero
**incompleta**: no ve XOR con cláusulas subsumidas o repartidas en cadenas
de Tseitin largas. Las unitarias son filas de una variable.

**Variables fijadas.** Sea ρ la asignación que la propagación unitaria
sobre F fija en la raíz.

- Cada fila se reduce a sus variables libres, con la paridad ajustada:
  b_i ← b_i ⊕ ⊕_{x ∈ V_i ∩ dom ρ} ρ(x).
- Si una fila queda vacía con paridad 1, F ya es inconsistente por
  propagación y la prueba es la cláusula vacía.

### 3.2 Certificado de inconsistencia

**Lema 1 (alternativa de Fredholm en GF(2)).** El sistema Ax = b sobre
GF(2) no tiene solución si y solo si existe y con yA = 0 e y·b = 1.

*Demostración.*

- Si existe tal y y x es solución, entonces 0 = (yA)x = y(Ax) = y·b = 1.
  Contradicción.
- Recíprocamente, si no hay solución, b no está en el espacio de columnas
  de A. Entonces rango [A | b] = rango A + 1, así que la última fila de la
  forma escalonada de [A | b] es (0 … 0 | 1). Esa fila es combinación lineal
  y·[A | b] de las filas originales. ∎

**Construcción.** Gauss con historial: cada fila lleva un vector h, que al
principio es el vector unitario de su índice; al sumar filas, se suman sus
historiales.

- Invariante: fila = h·[A | b].
- Si una fila se reduce a (0 | 1), S = soporte de h cumple
  Δ_{i∈S} V_i = ∅ y ⊕_{i∈S} b_i = 1.
- El prototipo **vuelve a comprobar** esa suma antes de emitir nada.
  Afirmar UNSAT sin esta comprobación no está permitido.

Coste: O(m·r·(n_X + m)/w) operaciones de palabra, con m filas, rango r,
n_X variables en el sistema y palabras de w bits.

### 3.3 La prueba

Se fija un orden total de las variables (el de sus índices).

- **Cadena ordenada** de un conjunto A = {a_1 < … < a_p}:
  - variables nuevas c^A_1, …, c^A_p, con las definiciones
    c^A_j ↔ c^A_{j−1} ⊕ a_j;
  - c^A_0 = z, una variable nueva con la unitaria ¬z;
  - la **salida** de A es out_A = c^A_p (z si A = ∅).
- **Notación**: ⟦⊕W = β⟧ es la CNF de la XOR sobre el multiconjunto W, en
  el que las repeticiones se cancelan. Si W queda vacío, ⟦⊕∅ = 0⟧ no tiene
  cláusulas y ⟦⊕∅ = 1⟧ es la cláusula vacía.

**Lema 2 (las definiciones son RAT).** Sea t una variable que no aparece en
la fórmula acumulada. Las cuatro cláusulas de t ↔ p ⊕ x, añadidas en este
orden y con el pivote delante, son RAT:

(¬t ∨ p ∨ x), (¬t ∨ ¬p ∨ ¬x), (t ∨ ¬p ∨ x), (t ∨ p ∨ ¬x).

*Demostración.*

- Las dos primeras tienen pivote ¬t. Ninguna cláusula contiene t, así que
  la condición RAT se cumple sin resolventes.
- La tercera tiene pivote t. Sus resolventes con las cláusulas que
  contienen ¬t, que son las dos primeras, son tautologías:
  - (¬p ∨ x ∨ p ∨ x) contiene p y ¬p;
  - (¬p ∨ x ∨ ¬p ∨ ¬x) contiene x y ¬x.
- La cuarta, igual:
  - (p ∨ ¬x ∨ p ∨ x) contiene x y ¬x;
  - (p ∨ ¬x ∨ ¬p ∨ ¬x) contiene p y ¬p.
- La unitaria ¬z es RAT por la misma razón que las dos primeras. ∎

**Lema 3 (casos sobre una variable).** Sea Φ la fórmula acumulada y E una
cláusula. Si E ∨ v y E ∨ ¬v son RUP respecto de Φ, añadir E ∨ v, después
E ∨ ¬v y después E es una sucesión de tres pasos RUP.

*Demostración.*

- Los dos primeros, por hipótesis; añadir cláusulas solo ayuda a la
  propagación.
- Al negar E, las dos cláusulas añadidas se vuelven las unitarias v y ¬v.
  Hay conflicto. ∎

**Lema 4 (hoja).** Sea (V, b) una fila de S, ya reducida a variables libres,
con V = {x_1 < … < x_k}, y sea G el grupo de cláusulas de F de su XOR
original. Tras añadir las definiciones de la cadena de V, la sucesión

L_j = ⟦c_j ⊕ x_{j+1} ⊕ … ⊕ x_k = b⟧, para j = 1, …, k,

se deriva por el Lema 3 dividiendo sobre x_j. L_k es la unitaria
«out_V = b». Cuesta a lo sumo 3·2^k líneas.

*Demostración.*

1. Sea E ∈ L_j. Al negar E ∨ x_j (el caso ¬x_j es simétrico) quedan
   asignadas c_j, x_{j+1}, …, x_k (por ¬E) y x_j.
2. La definición c_j ↔ c_{j−1} ⊕ x_j tiene dos de sus tres variables
   asignadas, así que la propagación asigna c_{j−1} = c_j ⊕ x_j.
3. Para j ≥ 2: ya están asignadas todas las variables de L_{j−1}, con
   paridad c_{j−1} ⊕ x_j ⊕ … ⊕ x_k = c_j ⊕ x_{j+1} ⊕ … ⊕ x_k. Esa paridad
   es la errónea, porque ¬E falsea L_j. Entonces la única cláusula de
   L_{j−1} que prohíbe esa asignación está falseada: conflicto.
4. Para j = 1: c_0 = z. Si la propagación asigna z = 1, choca con ¬z. Si
   asigna z = 0, las variables libres de V tienen paridad errónea.
5. Para las variables fijadas por ρ, la propagación de las unitarias de F
   repite ρ en toda comprobación RUP. Con eso la asignación de las
   variables originales viola ⊕V_original = b_original, y falsea una
   cláusula de G: conflicto.
6. Cuenta: L_j tiene 2^(k−j) cláusulas y cada una cuesta 3 líneas. La suma
   es 3·(2^k − 1). ∎

**Lema 5 (barrido).** Sean A y B nodos con sus cadenas y sus unitarias
out_A = b_A, out_B = b_B ya derivadas, y C = A Δ B con su cadena ya
definida. Para cada variable v se definen los punteros

- a(v) = c^A_j, donde a_j es el mayor elemento de A con a_j ≤ v (z si no
  hay ninguno);
- b(v) y c(v), igual con B y con C.

Sea I(v) = ⟦a(v) ⊕ b(v) ⊕ c(v) = 0⟧. Recorriendo v ∈ A ∪ B en orden
creciente, cada I(v) se deriva de I(v⁻) por el Lema 3 dividiendo sobre v,
donde v⁻ es la variable anterior (I antes de la primera es ⟦z = 0⟧, la
unitaria ¬z). Al final, I = ⟦out_A ⊕ out_B ⊕ out_C = 0⟧, y la unitaria
«out_C = b_A ⊕ b_B» es RUP. Cuesta a lo sumo 12·|A ∪ B| + 1 líneas.

*Demostración.*

1. Hay tres casos para v:
   - v ∈ A \ B: avanzan a y c, porque v ∈ C;
   - v ∈ B \ A: avanzan b y c;
   - v ∈ A ∩ B: avanzan a y b, y c no, porque v ∉ C.
2. Sea E ∈ I(v) y niéguese E ∨ v (o E ∨ ¬v). Cada puntero que avanza tiene
   su definición t ↔ t⁻ ⊕ v con t y v asignadas, así que la propagación
   asigna t⁻. Los punteros que no avanzan ya están asignados por ¬E.
3. Quedan asignadas todas las variables de I(v⁻). Su paridad es la de
   (a(v), b(v), c(v)) más v sumado dos veces, porque en los tres casos
   avanzan exactamente dos punteros: es la misma paridad. ¬E la hace
   errónea, así que una cláusula de I(v⁻) está falseada. Las cancelaciones
   del multiconjunto (cuando dos punteros valen z) no cambian el argumento:
   la paridad de un multiconjunto es la de sus elementos de multiplicidad
   impar.
4. Al terminar, cada puntero es la salida de su conjunto. Con out_A y out_B
   fijadas por sus unitarias, negar «out_C = b_A ⊕ b_B» asigna las tres
   variables de I con paridad 1, y una cláusula de I queda falseada. Si
   C = ∅, out_C = z y la unitaria es z (o ¬z).
5. Cuenta: |I(v)| ≤ 4 cláusulas, cada una cuesta 3 líneas, y hay |A ∪ B|
   variables. ∎

**Teorema 1 (X1: corrección y tamaño).** Sea S un certificado del §3.2 y
N = Σ_{i∈S} k_i. La sucesión siguiente es una refutación DRAT de F:

1. ¬z;
2. las definiciones de las cadenas de todos los nodos de un árbol binario
   equilibrado cuyas hojas son las filas de S y cuyos nodos internos son la
   diferencia simétrica de sus hijos;
3. los Lemas 4 para las hojas;
4. los Lemas 5 de abajo arriba;
5. la cláusula vacía.

Su longitud es a lo sumo

  2 + Σ_{i∈S} (4k_i + 3·2^{k_i}) + ⌈log₂|S|⌉·(16N + |S|),

con cláusulas de ancho ≤ max(K + 1, 4) y a lo sumo
1 + N·(1 + ⌈log₂|S|⌉) variables nuevas.

*Demostración.*

1. **Corrección**:
   - toda adición es RAT (Lema 2) o RUP (Lemas 3 a 5);
   - en la raíz, C = Δ_{i∈S} V_i = ∅ y su paridad es 1, así que el Lema 5
     deriva la unitaria z, y la cláusula vacía es RUP con ¬z;
   - las definiciones se emiten todas antes que los lemas, y sus variables
     son nuevas en ese momento, así que el Lema 2 vale.
2. **Tamaño**:
   - En cada nivel del árbol, la suma de |conjunto| de los nodos es a lo
     sumo N, porque |A Δ B| ≤ |A| + |B|.
   - Un nodo interno cuesta 4|C| (definiciones) más 12|A ∪ B| + 1 (Lema 5).
     Además, |A ∪ B| ≤ |A| + |B|. Por nivel: ≤ 4N + 12N + (nodos del
     nivel).
   - Hay ⌈log₂|S|⌉ niveles.
   - Las hojas cuestan 4k_i (definiciones) más 3·2^{k_i} (Lema 4).
   - Las variables nuevas son z más una por elemento de cada nodo. ∎

**Corolario 2 (separación).** Sea T(G, χ) la fórmula de Tseitin de un grafo
conexo G de n vértices y grado d con cargas de suma impar.

- X1 la refuta con una prueba DRAT de tamaño O(2^d·n + d·n·log n).
- Si G es un expansor, toda refutación por resolución tiene tamaño
  2^Ω(n) (Urquhart, 1987; Ben-Sasson y Wigderson, 2001). Por research/08
  Teorema 2, eso vale también para el tiempo de un CDCL sin X1.

*Demostración.*

1. Cada vértice da una fila (sus d aristas, con su carga): el Lema 0 la
   extrae si d ≤ K.
2. La suma de todas las filas cancela cada arista, que aparece en dos
   vértices, y tiene paridad Σχ = 1. Por el Lema 1, Gauss encuentra un
   certificado S con |S| ≤ n y N ≤ d·n.
3. El Teorema 1 da la cota. ∎

**Observaciones de diseño.**

- **El árbol equilibrado es esencial.** Sumar las filas en orden lineal
  cuesta Σ_t |A_t|, que en un expansor es Θ(n²): el conjunto acumulado es
  un corte grande. El árbol lo baja a O(N log |S|) sin depender del grafo.
  Es la misma cota O(n log n) que Chew y Heule (2020) obtienen para
  reordenar paridades.
- **Sin variables nuevas en el solver.** X1 refuta y termina. Las
  variables de extensión existen solo en la prueba, con índices mayores que
  cualquier variable que haya usado Kissat (incluidas las de `factor` y las
  de satsuma). Así no hay que registrar variables en el solver; X1b sí
  tendrá que hacerlo (§5).
- **Fuera del caso inconsistente, X1 no toca nada.** Si el sistema es
  consistente, no se emite ni una línea ni cambia ningún estado del solver.
  La trayectoria es la misma más un coste fijo (research/08 §6, clase E más
  una salida temprana).

## 4. Validación del diseño (prototipo)

### 4.1 Herramientas

- `scripts/gen_paridad.py`: familias sintéticas insatisfacibles por
  construcción, con semilla:
  - Tseitin en malla toroidal y en grafo regular aleatorio conexo;
  - *lights-out* N×N con un objetivo fuera de la imagen (N singular);
  - paridad en dos órdenes (Chew y Heule, 2020).

  Son sintéticas a propósito: las instancias de paridad UNSAT de 2026 están
  en `bench/test`, reservado para la validación final.
- `scripts/x1_gauss.py`: extracción, Gauss con certificado comprobado y la
  prueba del Teorema 1. Sin borrados por defecto (§4.3).

### 4.2 Resultados

**Prototipo** (`x1_gauss.py`, prueba sin borrados con las definiciones
primero). Kissat 4.0.4 de LabeSAT sin X1, con 120 s; un núcleo a prioridad
mínima mientras corría la cola:

| Familia (semilla 1) | Kissat 120 s | X1 (s) | \|S\| | N | Líneas | Variables nuevas | `dsr-trim` SC2026 / actual (s) |
|---|---|---|---|---|---|---|---|
| Tseitin malla 10×10 | sin resolver | 0,19 | 100 | 400 | 39 961 | 2 361 | 0,14 / 0,12 |
| Tseitin malla 30×30 | sin resolver | 1,16 | 900 | 3 600 | 534 169 | 32 149 | 25,0 / 24,4 |
| Tseitin 4-regular, 200 vértices | sin resolver | 0,26 | 200 | 800 | 91 377 | 5 437 | 0,41 / 0,40 |
| Tseitin 4-regular, 1000 vértices | sin resolver | 1,40 | 1 000 | 4 000 | 598 929 | 36 059 | 11,9 / 11,2 |
| *Lights-out* 9×9 | UNSAT, 0,03 s | 0,13 | 42 | 190 | 14 361 | 780 | 0,04 / 0,03 |
| *Lights-out* 19×19 | UNSAT, 95,5 s | 0,22 | 112 | 544 | 54 849 | 3 023 | 0,22 / 0,19 |
| Dos órdenes, n = 100 | sin resolver | 0,25 | 198 | 592 | 66 285 | 4 095 | 0,31 / 0,28 |

El tiempo de X1 incluye arrancar Python y leer la CNF. Todas las pruebas
verifican. El tamaño crece como predice el Teorema 1: la malla 30×30 tiene
N·⌈log₂|S|⌉ = 36 000 y 534 169 líneas, por debajo de la cota
2 + Σ(4k_i + 3·2^{k_i}) + ⌈log₂|S|⌉(16N + |S|) = 2 + 900·64 + 10·58 500 =
642 602.

**Implementación en Kissat** (`configure --gauss`, opción `--gauss=1`):

- **Familias sintéticas** (`scripts/test_gauss.sh`):
  - refuta las cuatro familias UNSAT y sus pruebas las verifican
    `drat-trim` y los dos `dsr-trim`;
  - en las cuatro variantes **satisfacibles** no refuta, y los 81
    contadores de `--statistics` son idénticos con `--gauss=1` y
    `--gauss=0`.
- **Instancia real de 2026, `667341ee`** (*lights-out*, `bench/calib2`,
  UNSAT verificada en 2026):

  | | Tiempo |
  |---|---|
  | CaDiCaL 3 en 2026 | 4717 s |
  | Mejor solver de 2026 (`satsuma-iter-ae-kissat-mab`) | 346 s |
  | **LabeSAT con X1** (lectura incluida) | **0,02 s** |
  | Verificación con `dsr-trim` de SC2026 | 1,77 s |
  | Verificación con `dsr-trim` actual | 1,20 s |
  | Verificación con `drat-trim` | 9,33 s |

  Datos de X1: 1750 filas sobre 1750 variables, certificado de 596 filas,
  7864 variables de extensión y una prueba de 1,2 MB.
- **Sin refutación, la búsqueda no cambia**. Con 20 000 conflictos, los 81
  contadores son idénticos con y sin X1 en cuatro instancias reales con y
  sin XOR:
  - `0be1e12a` (*or_randxor*, sistema consistente);
  - `75429ff7` (*random-graph-xorsat*, sistema consistente de rango 250);
  - `3e912cd2` (`calib2`);
  - `php_6_5`.
- **Sin `configure --gauss` el binario no cambia**:
  - los 94 ficheros objeto de Kissat son idénticos byte a byte (`objdump -s`)
    a los de antes de X1, salvo `build.o`, que guarda commit y fecha;
  - el gancho está en `internal.c`, después de la última macro que usa
    `__LINE__`. En `search.c` cambiaba la constante de línea que `TERMINATED`
    pasa a sus mensajes.

### 4.3 El `dsr-trim` de SC2026 falla con ciertos borrados

**Qué se observó.**

- La primera versión del prototipo borraba los lemas auxiliares.
- `drat-trim` y el `dsr-trim` actual verificaban las cuatro familias
  pequeñas.
- El `dsr-trim` del commit de SC2026 (`8f857dd`), que es el de la
  competición, **terminaba con violación de segmento** en modo hacia atrás
  (el modo por defecto).
  - En modo hacia delante (`-f`) verificaba.
  - Sin borrados, verificaba.

**Reducción.** Quitando líneas de borrado mientras el fallo persistía (la
prueba sigue siendo válida), se llegó a dos disparadores de **un solo
borrado** cada uno:

1. borrar una **cláusula de definición RAT** (`d 99 98 -8`, cuarta cláusula
   de la definición de 99);
2. con las definiciones conservadas, borrar un **lema RUP binario justo
   después de usarlo para derivar una unitaria** (`d 24 -13` tras `-25`).

**Contexto.** El registro de cambios del `dsr-trim` actual
(`bug_log.txt`) documenta, después del commit de SC2026, dos arreglos del
modo hacia atrás en esa zona:

- (29/4/26) el borrado de unitarias verdaderas se ignoraba mal;
- (11/9/26) no se borraban bien las unitarias verdaderas.

No se ha aislado la línea exacta del verificador, y no hace falta: lo que
importa es qué pruebas acepta.

**Decisión de diseño:**

- Las pruebas de X1 **no borran nada**.
- Coste: la comprobación es más lenta, porque los lemas antiguos siguen
  participando en la propagación. En la malla 30×30 (534 169 líneas):
  - el `dsr-trim` de SC2026 verifica en **97 s** y el actual en 66 s, con
    unos 65 MB;
  - `drat-trim` no termina en 600 s; no es el verificador de la
    competición.

**Consecuencia general**:

- Cualquier técnica nueva de LabeSAT que emita cláusulas RAT, o que borre
  cláusulas usadas como razones de unitarias, se valida con el verificador
  de SC2026 en modo hacia atrás antes de darla por buena.
- Es un riesgo que no se veía con las pruebas de Kissat solo: estas apenas
  contienen RAT y sí se verificaron en 2026.

## 5. X1b: unidades y equivalencias implicadas por el sistema XOR (diseño)

**Qué.** Llevar el sistema a forma escalonada reducida (Gauss-Jordan):

- toda fila con una sola variable libre es una **unidad** implicada;
- toda fila con dos es una **equivalencia** x ↔ y ⊕ b.

Ni la propagación unitaria ni el cierre por congruencia las ven cuando
salen de combinar muchas filas.

**Prueba.** Es la misma maquinaria:

- el historial de la fila da S_r;
- el árbol del Teorema 1 deriva la unitaria de la salida del conjunto
  {x} o {x, y};
- la cláusula final es RUP:
  - para {x}: la definición c_1 ↔ z ⊕ x, con z falsa y c_1 fijada, propaga
    x;
  - para {x, y}: las dos cláusulas de x ⊕ y = b se comprueban igual con
    c_2 ↔ c_1 ⊕ y.

**Proposición 3.** Las unidades y equivalencias que produce X1b las implica
F, y la prueba que las acompaña es DRAT válida. Su tamaño está acotado por
el del Teorema 1 aplicado a S_r.

*Demostración.* Es el Teorema 1 sin el último paso: la raíz del árbol es
{x} o {x, y} en vez de ∅. La cláusula final es RUP por el argumento de
arriba. ∎

**Lo que falta para implementarlo, y por eso va después de X1:**

1. **Registrar las variables nuevas en Kissat.** Aquí el solver sigue
   buscando después. Si `factor` reutilizara un índice de variable de la
   prueba, una de sus cláusulas RAT dejaría de ser válida. Kissat tiene
   `kissat_reserve` para fijar el máximo de variables externas.
2. **No borrar** (§4.3). Las cadenas quedan en la prueba durante el resto
   de la búsqueda y encarecen su comprobación.
3. **Valor sin estimar.** En 2026 ningún solver con Gauss ganó en las
   familias mixtas (research/06 §5). Se mediría con un A/B de clase S.

## 6. Otras técnicas: análisis y decisión

**C1, cardinalidad (refutar por conteo).**

- *Idea*: detectar restricciones «al menos uno» y «como mucho uno» que
  formen un palomar o un emparejamiento imposible, y refutarlo por conteo
  (teorema de Hall).
- *Pruebas*: el conteo necesita codificaciones con variables de extensión
  (BDD o sumadores). Bryant, Biere y Heule (2022) generan pruebas clausales
  para razonamiento pseudo-booleano con BDD.
- *Decisión*: **aparcada**. Las familias de palomar con filas
  intercambiables ya las rompe satsuma con pruebas SR cortas. El caso no
  cubierto (conteo sin simetría) no tiene, en nuestros datos de 2026,
  instancias identificadas que lo justifiquen.

**P1, aprendizaje de cláusulas PR en el preproceso.**

- *Idea*: Reeves, Heule y Bryant (2022, 2023) buscan cláusulas PR mediante
  consultas SAT sobre el «reducto positivo». Aceleran familias combinatorias
  académicas, y sus pruebas se comprueban con `dpr-trim`/`dsr-trim`.
- *Decisión*: **aparcada**. Necesita un solver auxiliar dentro del
  preproceso y no hay datos de la Main Track. Además emite líneas PR, el
  tipo de línea donde §4.3 encontró fallos del verificador de SC2026.

**B1, BVA más agresivo.**

- *Idea*: SBVA (Haberlandt, Green y Heule, 2023) ganó la Main Track de 2023
  como preproceso de CaDiCaL. Kissat 4.0.4 ya trae su propia BVA
  (`factor`), activa y limitada por esfuerzo.
- *Decisión*: subir sus límites es un ajuste de parámetros de clase S. Solo
  con un A/B preregistrado, y detrás de las líneas con más valor medido.

## 7. Plan

| Paso | Qué | Puerta |
|---|---|---|
| 1 | Prototipo X1 validado con los tres verificadores (este documento) | **Hecho** |
| 2 | X1 dentro de Kissat, en C, detrás de `configure --gauss` y `--gauss` (apagada): extracción en la raíz antes de la búsqueda, Gauss con bits, prueba sin borrados con índices de variable por encima del máximo externo | **Hecho**: `test_gauss.sh` en verde con los tres verificadores; contadores idénticos donde no refuta; objetos idénticos sin la macro |
| 3 | **EXP-019**, preregistrado: X1 sobre `calib`, `calib2`, `symm2026`, `tesis-dev` y sintéticas (no `bench/test`) | Seguridad (H0), equivalencia (H1), coste (H2) |
| 4 | X1b, si el paso 3 sale bien | Clase S: A/B de PAR-2 |

## Referencias

- Alekhnovich, M. (2004). Mutilated chessboard problem is exponentially hard
  for resolution. *Theoretical Computer Science* 310, 513–525.
  https://doi.org/10.1016/S0304-3975(03)00395-5
- Beame, P., Kautz, H., y Sabharwal, A. (2004). Towards understanding and
  harnessing the potential of clause learning. *JAIR* 22, 319–351.
- Ben-Sasson, E., y Wigderson, A. (2001). Short proofs are narrow —
  resolution made simple. *Journal of the ACM* 48(2), 149–169.
  https://doi.org/10.1145/375827.375835
- Biere, A., Fazekas, K., Fleury, M., y Froleyks, N. (2024). Clausal
  congruence closure. *SAT 2024*, LIPIcs 305, 6:1–6:25.
- Bryant, R. E., Biere, A., y Heule, M. J. H. (2022). Clausal proofs for
  pseudo-Boolean reasoning. *TACAS 2022*, LNCS 13243, 443–461.
  https://doi.org/10.1007/978-3-030-99524-9_25
- Chew, L., y Heule, M. J. H. (2020). Sorting parity encodings by reusing
  variables. *SAT 2020*, LNCS 12178, 1–10.
  https://doi.org/10.1007/978-3-030-51825-7_1
- Codel, C., Avigad, J., y Heule, M. J. H. (2024). Verified substitution
  redundancy checking. *FMCAD 2024* (`dsr-trim`).
- Cook, S. A. (1976). A short proof of the pigeon hole principle using
  extended resolution. *SIGACT News* 8(4), 28–32.
- Haberlandt, A., Green, H., y Heule, M. J. H. (2023). Effective auxiliary
  variables via structured reencoding. *SAT 2023*, LIPIcs 271, 11:1–11:19.
  https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SAT.2023.11
- Haken, A. (1985). The intractability of resolution. *Theoretical Computer
  Science* 39, 297–308.
- Heule, M. J. H., Kiesl, B., y Biere, A. (2017). Short proofs without new
  variables. *CADE-26*, LNCS 10395, 130–147.
  https://doi.org/10.1007/978-3-319-63046-5_9
- Heule, M. J. H., Kiesl, B., y Biere, A. (2019). Clausal proofs of
  mutilated chessboards. *NFM 2019*, LNCS 11460, 204–210.
  https://doi.org/10.1007/978-3-030-20652-9_13
- Kiesl, B., Rebola-Pardo, A., y Heule, M. J. H. (2018). Extended resolution
  simulates DRAT. *IJCAR 2018*, LNCS 10900, 516–531.
  https://doi.org/10.1007/978-3-319-94205-6_34
- Manthey, N., Heule, M. J. H., y Biere, A. (2013). Automated reencoding of
  Boolean formulas. *HVC 2012*, LNCS 7857, 102–117.
  https://doi.org/10.1007/978-3-642-39611-3_14
- Philipp, T., y Rebola-Pardo, A. (2016). DRAT proofs for XOR reasoning.
  *JELIA 2016*.
- Pipatsrisawat, K., y Darwiche, A. (2011). On the power of clause-learning
  SAT solvers as resolution engines. *Artificial Intelligence* 175(2),
  512–525.
- Reeves, J. E., Heule, M. J. H., y Bryant, R. E. (2022). Preprocessing of
  propagation redundant clauses. *IJCAR 2022*, LNCS 13385, 106–124.
  https://doi.org/10.1007/978-3-031-10769-6_8 (versión de revista: *JAR*
  67, 2023, https://doi.org/10.1007/s10817-023-09681-3).
- Soos, M., y Bryant, R. E. (2023). Proof generation for CDCL solvers using
  Gauss-Jordan elimination. *arXiv* 2304.04292.
- Tseitin, G. S. (1983). On the complexity of derivation in propositional
  calculus. En *Automation of Reasoning*, 466–483 (original de 1968).
  https://doi.org/10.1007/978-3-642-81955-1_28
- Urquhart, A. (1987). Hard examples for resolution. *Journal of the ACM*
  34(1), 209–219.
