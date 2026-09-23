# 06 — ¿Incorporar a LabeSAT el razonamiento XOR (Gauss-Jordan) de CryptoMiniSat?

- **Fecha**: 2026-09-23
- **Pregunta del director**: ¿serviría incorporar a LabeSAT el mecanismo de
  CryptoMiniSat que descubre estructuras algebraicas XOR? ¿Qué beneficios
  tendría? El objetivo es documentar posibles mejoras; si resulta
  contraproducente, se descarta.
- **Estado**: investigación cerrada. Veredicto y recomendaciones en §7. No se
  ha implementado nada.
- **Datos y herramientas nuevas**:
  - `scripts/xor_detect.c`: detector de XOR en una CNF;
  - `scripts/gauss_xor.py`: decide sistemas XOR puros con Gauss en GF(2);
  - `results/research06/estructura_xor.csv`: el escaneo de las instancias.

---

## 1. Qué hace CryptoMiniSat

1. **Recupera las XOR**: busca en la CNF grupos de cláusulas sobre las mismas
   k variables que codifican x₁ ⊕ … ⊕ xₖ = b. Son los 2^(k−1) patrones de signo
   de una misma paridad. También encadena XOR cortas unidas por variables
   auxiliares de Tseitin.
2. **Gauss-Jordan en la búsqueda**: mantiene matrices sobre GF(2) de las XOR
   recuperadas y, en cada nivel de decisión, deduce las propagaciones y los
   conflictos que la propagación unitaria de la CNF no ve (Soos et al., 2009;
   Soos, 2010; Han y Jiang, 2012).
3. **BIRD** (*Blast, Inprocess, Recover, Destroy*): convierte las XOR a CNF
   para el inprocesado y después las vuelve a recuperar (Soos, Gocht y Meel,
   2020).
4. **Autodesactivación**: desde la versión 5.8, Gauss-Jordan viene activado
   por defecto, pero se apaga solo si no rinde.
5. **Pruebas**: para dar pruebas de insatisfacibilidad con Gauss-Jordan, CMS
   integra TBUDDY, una biblioteca de BDD que genera pruebas (Soos y Bryant,
   2023). drat-trim «rinde mal» con esas pruebas, por la gran cantidad de
   variables de extensión, y hubo que usar el formato **FRAT con pistas** y el
   verificador `frat-rs`.

**Licencia**: CryptoMiniSat es MIT en su compilación por defecto. La licencia
no impide usarlo.

## 2. Por qué importa, en teoría

- Las fórmulas de paridad (Tseitin y Urquhart) exigen refutaciones de tamaño
  **exponencial** en resolución, y por tanto en CDCL (Urquhart, 1987;
  Itsykson et al., 2021).
- Incluso dos restricciones de paridad contradictorias con órdenes de
  variables distintos son exponenciales para CDCL (Chew y Heule, 2020;
  Chew et al., 2024).
- La eliminación de Gauss las decide en tiempo **polinómico**. Es una
  separación real de potencia, no un ajuste fino.
- Soos y Bryant (2023): las fórmulas de Urquhart están «fuera del alcance de
  los CDCL actuales» incluso en su tamaño mínimo (m = 3). Con Gauss-Jordan se
  resuelven en milisegundos (m = 15: 14 s incluida la prueba FRAT).

## 3. Lo que ya hace Kissat 4.0.4

| Técnica | Kissat | Alcance |
|---|---|---|
| Extracción de puertas XOR | Sí, en `congruence.c` (`congruencexors`, aridad ≤ 4) | Para el **cierre por congruencia** (Biere et al., 2024): detecta puertas XOR equivalentes y las fusiona, con pruebas DRAT |
| Eliminación de variables con definiciones | Sí (`eliminate.c`, con kitten) | Aprovecha las XOR como definiciones de puerta |
| **Gauss-Jordan sobre sistemas XOR** | **No** | — |

**Antecedente histórico**: Lingeling, el solver anterior de Biere, incluía
eliminación de Gauss en el inprocesado. **No pasó a CaDiCaL ni a Kissat.**

## 4. Cuánta estructura XOR hay de verdad (datos propios)

`scripts/xor_detect.c` se pasó sobre las **161 instancias únicas** de
nuestros bancos de 2026 (calib, calib2, dev y symm2026; `bench/test` queda
fuera porque está reservado). Se cuentan XOR de 3 a 6 variables.

| Parte de la CNF que son cláusulas XOR | Instancias | Familias |
|---|---:|---|
| **90–100 % (sistema lineal casi puro)** | **4** | lights-out, random-graph-xorsat |
| 50–90 % (XOR mezcladas con otras restricciones) | 9 | xor-shifting, cryptography-ascon y -simon, prime-testing, matrix-multiplication, circuit-minimization, sliding-puzzle… |
| 10–50 % (XOR como **puertas de circuito**) | 14 | multiplicadores, miters, bitvector, cryptography-cbmc… |
| 0–10 % | 5 | planning, software-verification… |
| **Sin ninguna XOR** | **129 (80 %)** | — |

**Lectura**:
- En la mayoría de las instancias industriales con XOR, estas son **puertas
  de circuito** (sumadores, multiplicadores): cada una define una variable a
  partir de otras.
- Ahí la dificultad no es un sistema lineal, y ya las trata el cierre por
  congruencia de Kissat.
- La eliminación de Gauss aporta de verdad en los **sistemas lineales casi
  puros**, que son pocos.

### Gauss sobre los sistemas puros (`scripts/gauss_xor.py`)

| Instancia | Familia | Gauss | Kissat 2026 (5000 s) | Ganador 2026 | LabeSAT (EXP-007, T = 180 s) |
|---|---|---|---|---|---|
| `75429ff7` | random-graph-xorsat | **SAT en 0,01 s** | 113 s | 201 s | 149–172 s (EXP-008, rama A) |
| `01d6fa8e` | lights-out | **SAT en 0,04 s** | 600 s | 714 s | — |
| `28dcc411` | lights-out (+625 unidades) | **SAT en 0,04 s** | 1613 s | 32 s (simetrías) | 150–161 s |

Las tres respuestas coinciden con las conocidas.

## 5. Cuánto se ganaría: SAT Competition 2026 (400 instancias)

Datos oficiales de 2026 (`data/competition/`), familias de sistema lineal:

| Instancia | Resultado | Kissat 2026 | Qué aportaría Gauss |
|---|---|---|---|
| lights-out (3 SAT) | sat | 245, 600 y 1613 s | Instantáneas. Sin prueba: basta el modelo |
| random-graph-xorsat | sat | 113 s | Instantánea. Sin prueba |
| lights-out (4 UNSAT) | unsat | 388 s, 4288 s, **timeout**, **timeout** | Refutación instantánea, **si se genera una prueba válida** |
| xor-chain | desconocido (nadie la resolvió) | timeout | Probablemente refutación instantánea, con prueba |
| tseitin-formulas | desconocido (nadie la resolvió) | timeout | Ídem |

**Estimación sobre 2026**:
- **Lado SAT** (sin prueba): ahorra ~2570 s en total, es decir, **−6 s de
  PAR-2 medio**. No cambia ninguna instancia de resuelta a no resuelta.
- **Lado UNSAT** (con prueba): **+4 instancias resueltas** y unos **−112 s de
  PAR-2 medio**, alrededor del 2,8 % del PAR-2 del mejor solver con etiqueta
  IA de 2026 (4010 s). Es del orden de lo que se recupera con la clique MIT
  (research/03).
- **Familias mixtas** (xor-shifting, *minimum-disagreement-parity*): **no las
  resolvió ningún solver con Gauss.**
  - Las 11 de xor-shifting las resolvió `zhenwei_kissat-sup`, del track
    experimental: una tubería de tres programas (`kmpsym`, `breakid` y
    `sup`) con ruptura de simetrías y decisiones sobre el soporte
    independiente, no Gauss.
  - `green_lymphosat` usa un solver distinto para cada familia de 2026
    (hiperespecialización).
  - Sobre las mixtas, la evidencia de que Gauss ayude viene de benchmarks de
    criptografía y LPN (Soos, 2010; Soos y Bryant, 2023), no de la
    competición.

**Salvedad**: las familias de 2027 serán otras. En la competición las
instancias son nuevas cada año, aunque las familias de paridad (Tseitin,
lights-out, XOR-SAT) reaparecen a menudo. El beneficio depende de que las
haya.

## 6. Coste y riesgos de incorporarlo

| Aspecto | Evaluación |
|---|---|
| Integración completa, estilo CMS (Gauss en cada nivel, BIRD) | Miles de líneas, acopladas a la propagación, al análisis de conflictos y al inprocesado. El propio autor lo describe como «ni fácil» ni con «ventajas claras en la mayoría de las situaciones», y lo **desactivó** en su versión para la SAT Race de 2019. Biere no lo trasladó a CaDiCaL ni a Kissat |
| **Pruebas** (lo crítico) | Una respuesta UNSAT basada en Gauss necesita una prueba con variables de extensión (traducción T de Philipp y Rebola-Pardo, 2016; BDD de Soos y Bryant, 2023; o la técnica de Chew y Heule, 2020, O(n log n)). drat-trim no con ellas; nosotros verificamos con **dsr-trim**, y no sabemos cómo rinde con pruebas así. **Una prueba inválida descalifica** |
| Coste en el 80 % sin XOR | La detección es barata (una pasada por las cláusulas cortas; Kissat ya extrae puertas XOR). Con activación condicional, casi nulo |
| Arquitectura (D-016) | Encaja: iría **dentro de Kissat**, en C, como una técnica más. No es un solver aparte |
| Licencia | CMS es MIT. Aun así se recomienda **no copiar** su código: Gauss sobre GF(2) con bits es corto de escribir, y el acoplamiento de CMS no sirve dentro de Kissat |

## 7. Veredicto y recomendaciones

### Descartado por contraproducente: Gauss-Jordan en toda la búsqueda, al estilo de CryptoMiniSat

- Coste de ingeniería y de mantenimiento muy alto, dentro de un núcleo que no
  es el nuestro.
- Pruebas difíciles y con riesgo de descalificación.
- El beneficio se concentra en ~2–3 % de las instancias, la mayoría en
  familias mixtas donde en 2026 no ganó ningún solver con Gauss.
- Los propios autores (Soos en competición, Biere al pasar de Lingeling a
  CaDiCaL y Kissat) lo apartaron del caso general.
- Competiría con B3 (EXP-009), que tiene mucho más margen medido
  (research/05: oráculo −17 %).

### X1 — Refutar sistemas lineales inconsistentes, con prueba (aparcado, prioridad alta en la fase 2 de ADR-0007)

- **Qué**: en el preproceso o en el inprocesado raíz:
  1. extraer el subsistema XOR, reutilizando la extracción de `congruence.c`;
  2. aplicarle Gauss sobre GF(2);
  3. si es **inconsistente**, refutar la fórmula con una prueba (traducción
     T o la técnica de Chew y Heule, 2020);
  4. si es consistente, no hacer nada.
- **Por qué**: es donde está el beneficio de §5 (+4 resueltas, −112 s de
  PAR-2 en 2026), con la separación teórica a favor. Además solo toca la
  raíz: no hay que tocar la propagación ni el análisis de conflictos.
- **Condición previa** (un spike de un día): generar la prueba para una
  lights-out UNSAT de 2026 y comprobar que la aceptan **los dos dsr-trim**
  dentro de un tiempo razonable. Si no, no se sigue.
- **Medible**: sí. Cambia el estado de instancias concretas (de timeout a
  resuelta), igual que la clique MIT.
- **Cuándo**: después de B3 (EXP-009). Encaja en la fase 2 de ADR-0007 como
  una técnica más dentro de Kissat.

### X2 — Fases iniciales desde la solución del sistema lineal (descartado por efecto pequeño)

- **Qué**: si el subsistema XOR es consistente, usar una solución suya como
  fase inicial u objetivo de Kissat.
- No necesita prueba: las fases no afectan a la corrección.
- **Por qué no**: en 2026 ahorra ~6 s de PAR-2 medio y no cambia ninguna
  instancia de estado. Está por debajo de lo que podemos medir en agregado (la
  regla de research/05).
- Solo tendría sentido como subproducto de X1, porque comparte la
  extracción y Gauss, y a coste marginal.

### Hallazgo lateral (para B3 y la línea de simetrías)

- En 2026, las 11 xor-shifting (SAT) las resolvió `kissat-sup` con ruptura de
  simetrías (BreakID + `kmpsym`) y decisiones sobre el soporte independiente.
- satsuma + Kissat no resolvió ninguna.
- No es XOR, pero indica que **otra ruptura de simetrías** captura familias
  que satsuma no ve. Se anota para la línea de simetrías (research/03, D-005,
  B3); no es una recomendación.
- `kissat-sup` corrió en el track experimental, con tres programas y
  probablemente sin pruebas.

## 8. Referencias

- Biere, A., Fazekas, K., Fleury, M., y Froleyks, N. (2024). Clausal congruence closure. *SAT 2024*, LIPIcs 305, 6:1–6:25. https://doi.org/10.4230/LIPIcs.SAT.2024.6
- Chew, L., y Heule, M. (2020). Sorting parity encodings by reusing variables. *SAT 2020*. https://consensus.app/papers/details/7bb827e1439f5d89a61071d6274398df/
- Chew, L., et al. (2024). Hardness of random reordered encodings of parity for resolution and CDCL. https://consensus.app/papers/details/015d652b37d25bbb8b789db0ea0cac19/
- Gocht, S., y Nordström, J. (2021). Certifying parity reasoning efficiently using pseudo-Boolean proofs. *AAAI 2021*. https://consensus.app/papers/details/8cd77e9018f95a58a7809c1357178d90/
- Han, C.-S., y Jiang, J.-H. R. (2012). When Boolean satisfiability meets Gaussian elimination in a simplex way. *CAV 2012*. https://consensus.app/papers/details/9b915e462c19550292b69cd65d1fa8ab/
- Itsykson, D., et al. (2021). Near-optimal lower bounds on regular resolution refutations of Tseitin formulas for all constant-degree graphs. *Computational Complexity*. https://consensus.app/papers/details/1838efbba923563abc2f0c9d79dad36e/
- Laitinen, T., Junttila, T., y Niemelä, I. (2012). Extending clause learning SAT solvers with complete parity reasoning. *ICTAI 2012*. https://consensus.app/papers/details/a407d10d40495de0b9b20f37646abbdd/
- Philipp, T., y Rebola-Pardo, A. (2016). DRAT proofs for XOR reasoning. *JELIA 2016*. https://consensus.app/papers/details/233bc9e791235a66bc98df6c1ea45828/
- Soos, M. (2010). Enhanced Gaussian elimination in DPLL-based SAT solvers. *POS 2010*. https://www.msoos.org/wordpress/wp-content/uploads/2010/08/PoS10-Soos.pdf
- Soos, M. (2019). CryptoMiniSat 5.6 with YalSAT at the SAT Race (Gauss desactivado en competición). https://consensus.app/papers/details/6bdf11e1916f56789d88620d0d97e192/
- Soos, M., y Bryant, R. E. (2023). Proof generation for CDCL solvers using Gauss-Jordan elimination. *arXiv* 2304.04292. https://arxiv.org/abs/2304.04292
- Soos, M., Gocht, S., y Meel, K. S. (2020). Tinted, detached, and lazy CNF-XOR solving and its applications to counting and sampling. *CAV 2020*, 463–484. https://doi.org/10.1007/978-3-030-53288-8_22
- Soos, M., Nohl, K., y Castelluccia, C. (2009). Extending SAT solvers to cryptographic problems. *SAT 2009*. https://consensus.app/papers/details/bfe9d61d31595b18b2e59c14baf6b244/
- Soos, M. Blog *Wonderings of a SAT geek*, etiqueta «Gaussian elimination». https://www.msoos.org/tag/gaussian-elimination/
- Urquhart, A. (1987). Hard examples for resolution. *Journal of the ACM*. https://consensus.app/papers/details/2554d32011e6568aa1d63ad669a56702/
- Datos: SAT Competition 2026, resultados oficiales del Main Track (`data/competition/scores_2026.csv`) y paquetes de solvers públicos (`zhenwei`, `green`), consultados solo para identificar técnicas, sin copiar código.
