# Investigación 08 — Estrategia de optimización de LabeSAT: qué se puede ganar, con qué pruebas y en qué orden

- **Fecha**: 2026-10-01
- **Pedido del director**: optimizar el código de LabeSAT para reducir el
  tiempo de respuesta, con un enfoque de estructuras de datos, algoritmos y
  arquitectura. Cada solución debe tener una **demostración matemática antes
  de aplicarse** y todo debe quedar documentado.
- **Documentos asociados**:
  - ADR-0009 (protocolo de las optimizaciones que conservan la trayectoria);
  - EXP-016 (perfil de costes, en curso);
  - `scripts/valor_aceleracion.py` (§2).

---

## 0. Resumen

1. **Qué significa aquí «reducir la complejidad».** SAT es NP-completo, y
   para cualquier CDCL hay familias con coste **exponencial demostrado**
   (§1). Ninguna estructura de datos cambia eso: el solver produce una
   refutación por resolución, y su tamaño mínimo ya es exponencial. Las
   únicas palancas que cambian el **orden de crecimiento** son las que cambian
   el **sistema de pruebas** efectivo: ruptura de simetrías (ya en LabeSAT),
   razonamiento XOR (X1, research/06) y cardinalidad. Todo lo demás son
   **factores constantes**.
2. **El núcleo de Kissat ya es óptimo donde importa.** La propagación usa la
   búsqueda circular del vigilante de reemplazo, que Gent (2013) demostró
   óptima en coste amortizado (§3.1). Ahí no queda mejora asintótica.
3. **Cuánto vale un factor constante, calculado sin modelos** (Proposición 1,
   §2). Acelerar un 10 % el solver baja el PAR-2 ~1,5 %; duplicar la
   velocidad, un 10–17 %. A T = 5000 s eso son unos 60 s y unos 500 s de PAR-2.
   Por comparar: la ruptura de simetrías valió −964 s en 2026.
4. **Estrategia**, en este orden:
   - **medir** dónde se va el tiempo (EXP-016, ley de Amdahl);
   - aplicar **primero** lo que conserva la trayectoria y se demuestra
     equivalente (clase E, ADR-0009). La primera candidata es la **compilación
     guiada por perfil** (C1), con una condición de coma flotante demostrada
     (§3.3);
   - después, solo los puntos calientes con fracción ≥ 5 % y una mejora
     algorítmica con prueba;
   - en paralelo, las palancas que sí cambian el orden de crecimiento (B3 y
     X1), que son las de más valor esperado.

---

## 1. Límites de lo que una optimización puede ganar

**Teorema 1** (Haken, 1985). Toda refutación por resolución del principio del
palomar PHPⁿ⁺¹ₙ tiene tamaño 2^Ω(n).

**Teorema 2** (Beame, Kautz y Sabharwal, 2004). Toda cláusula aprendida en el
análisis de conflictos de CDCL se deriva de las cláusulas existentes por
resolución trivial, con a lo sumo n pasos (n = número de variables). Por
tanto, una ejecución UNSAT con C conflictos contiene una refutación por
resolución de tamaño O(C·n) más la fórmula de entrada. El recíproco, que CDCL
con reinicios simula polinómicamente la resolución general, lo prueban
Pipatsrisawat y Darwiche (2011): la resolución es **exactamente** el sistema
de pruebas de CDCL.

**Corolario 1.** Considérese CDCL cuyas cláusulas derivadas son consecuencias
por resolución, **sin variables nuevas**: el análisis de conflictos y las
técnicas de inproceso que solo resuelven, subsumen o eliminan. Sobre
PHPⁿ⁺¹ₙ, cualquier implementación, con cualquier estructura de datos,
necesita C = 2^Ω(n) conflictos, y por tanto tiempo exponencial.

*Demostración.* Por el Teorema 2, la ejecución contiene una refutación por
resolución de tamaño O(C·n + |F|), con |F| polinómico en n. Por el
Teorema 1, ese tamaño es 2^Ω(n). Así, C·n ≥ 2^Ω(n) − poly(n), y
C ≥ 2^Ω(n)/n = 2^Ω(n). Cada conflicto cuesta al menos una operación. ∎

**Excepción que hay que nombrar.** Kissat también tiene BVA (`factor`), que
**introduce variables nuevas**: es resolución extendida, y la resolución
extendida sí tiene refutaciones polinómicas del palomar (Cook, 1976). El
Corolario 1 no cubre esa parte. En la práctica, BVA no encuentra las
definiciones que necesita el palomar, y Kissat tampoco lo resuelve en las
instancias de 2026 (EXP-007, estrato H: 8 de 45 sin ruptura). Pero la cota
no es un teorema sobre Kissat entero, y no se presenta como tal.

**Teorema 3** (Heule, Kiesl y Biere, 2017). PHPⁿ⁺¹ₙ tiene refutaciones de
tamaño polinómico en el sistema PR, que añade cláusulas redundantes por
propagación. SR, el sistema de satsuma, lo contiene.

**Consecuencia para la estrategia.** La ruptura de simetrías no es una
optimización de constante: separa **exponencialmente** a LabeSAT de Kissat en
las familias simétricas. Así se explica EXP-007: 8 → 37 resueltas en el
estrato H, con casos que pasan de timeout a décimas de segundo.

Lo mismo ocurre con las fórmulas de Tseitin sobre expansores, que exigen
resolución exponencial (Urquhart, 1987) y se resuelven en tiempo polinómico
por eliminación gaussiana (research/06, X1), y con el palomar en planos de
corte (Cook, Coullard y Turán, 1987).

**Las palancas que cambian el orden de crecimiento son las que añaden un
razonamiento más fuerte que la resolución.** Las estructuras de datos solo
cambian constantes y factores polilogarítmicos por operación.

## 2. Cuánto vale un factor constante (resultado exacto)

Sea *A* un solver con tiempo tᵢ en la instancia i (tᵢ = ∞ si no resuelve), y
sea PAR2_T(A) = (1/n) Σᵢ [tᵢ si tᵢ ≤ T; 2T si no]. Sea *A_s* el solver que
hace **la misma búsqueda** *s* veces más deprisa: tᵢ/s.

**Proposición 1.** PAR2_T(A_s) = PAR2_{s·T}(A) / s.

*Demostración.* Para cada i, tᵢ/s ≤ T ⇔ tᵢ ≤ sT. Si se cumple, la
contribución de i es tᵢ/s = (1/s)·tᵢ; si no, es 2T = (1/s)·2sT. Sumando y
dividiendo entre n se obtiene (1/s)·PAR2_{sT}(A). ∎

**Corolario 2.** Si los tiempos de *A* se conocen hasta un límite T₀ (los que
superan T₀ están censurados), PAR2_T(A_s) se calcula **exactamente** para
todo s·T ≤ T₀. No hace falta modelar la cola de la distribución.

Aplicado a datos ya medidos (`scripts/valor_aceleracion.py`,
`results/estrategia/valor_aceleracion.txt`):

| ΔPAR-2 relativo | s = 1,1 | s = 1,25 | s = 1,5 | s = 2 |
|---|---:|---:|---:|---:|
| Kissat, SAT Competition 2026, T = 1000 s | −1,6 % | −3,8 % | −6,6 % | −11,1 % |
| Kissat, 2026, T = 2500 s | −1,3 % | −2,8 % | −7,6 % | −14,3 % |
| satsuma + Kissat (ganador de 2026), T = 2500 s | −1,4 % | −3,6 % | −8,0 % | −17,1 % |
| Kissat en la tesis, T = 400 s | −1,8 % | −3,9 % | −6,7 % | −11,2 % |

- La elasticidad ∂ln PAR-2 / ∂ln s ronda 0,15–0,2 y **apenas cambia con T**
  ni entre bancos. Eso permite extrapolar a T = 5000 s con un margen
  razonable: un 10 % de velocidad ≈ −1,5 % de PAR-2 ≈ −60 s, y el doble de
  velocidad ≈ −12 a −17 % ≈ −500 a −700 s.
- **Umbral de interés.** Con lo que podemos medir (A/B intercalados de
  60–150 instancias), un efecto de PAR-2 por debajo del ~1 % no se distingue.
  Una optimización de constante tiene que dar **≥ 7–10 % de velocidad** para
  que su valor sea medible.

## 3. Qué puede acelerar una optimización: Amdahl y equivalencia

### 3.1 La propagación ya es óptima

**Teorema 4** (Gent, 2013). Con vigilantes y una búsqueda **circular** del
literal de reemplazo (empezando donde terminó la búsqueda anterior), el coste
de la propagación es óptimo en notación O, amortizado sobre el árbol de
búsqueda.

Kissat 4.0.4 implementa justo eso (`src/proplit.h`):

- el campo `c->searched` guarda la posición de la búsqueda anterior y el
  recorrido continúa desde ahí, dando la vuelta hasta `lits + 2`;
- tiene además literal bloqueante en cada vigilante;
- las cláusulas binarias van dentro de la lista de vigilancia;
- el otro vigilante se obtiene con `lits[0] ^ lits[1] ^ not_lit`, sin
  comparar.

**Conclusión: no hay mejora asintótica en la propagación.** Solo caben
factores de microarquitectura: disposición en memoria, saltos y prefetch.

### 3.2 Ley de Amdahl con trayectoria conservada

Sean p_c las fracciones del tiempo de una corrida en cada componente c
(Σ p_c = 1).

**Proposición 2.** Si una optimización conserva la trayectoria (definición en
§3.3) y acelera el componente c por un factor k_c ≥ 1, el tiempo total se
multiplica por Σ_c p_c / k_c. La aceleración máxima alcanzable optimizando
solo c es 1 / (1 − p_c).

*Demostración.* Con la trayectoria conservada, cada componente hace
exactamente el mismo trabajo, y su tiempo pasa de p_c·t a p_c·t / k_c.
Sumando: t' = t·Σ p_c / k_c. Si k_c → ∞, t' → t·(1 − p_c). ∎

Combinada con la Proposición 1, el valor máximo en PAR-2 de optimizar c es el
de la aceleración 1 / (1 − p_c). **Por eso se mide antes de optimizar
(EXP-016)**:

- un componente con p_c = 5 % puede dar, como mucho, un 5,3 % de velocidad,
  es decir, ≈ −0,8 % de PAR-2: por debajo de lo medible;
- solo los componentes con p_c grande (búsqueda, eliminación, sondeo) tienen
  margen.

### 3.3 Cuándo dos binarios hacen la misma búsqueda

**Definición.** Dos binarios B₁ y B₂ de LabeSAT **conservan la trayectoria**
si, para toda entrada y semilla, recorren la misma sucesión de estados del
solver: misma pila de asignación tras cada propagación, mismas cláusulas
aprendidas y mismas decisiones de inproceso. En particular, dan los mismos
contadores (conflictos, decisiones y propagaciones) y la misma respuesta, el
mismo modelo y la misma prueba hasta el instante de terminación.

**Teorema 5.** Sean B₁ y B₂ dos compilaciones del mismo código fuente C de
LabeSAT con compiladores conformes a C11. Si se cumplen las condiciones
siguientes, B₁ y B₂ conservan la trayectoria:

- **(a)** las ejecuciones no tienen comportamiento indefinido (UB);
- **(b)** cada operación en coma flotante se redondea por separado según IEEE
  754 binary64: sin contracción en FMA (`-ffp-contract=off`), sin
  reasociación (sin `-ffast-math`) y sin precisión extendida x87 (en x86-64
  se usa SSE2);
- **(c)** el programa es secuencial y ninguna decisión depende del reloj;
- **(d)** ninguna decisión depende del valor absoluto de una dirección de
  memoria.

*Demostración.*

1. Por la regla del «como si» (C11 §5.1.2.3), un compilador conforme solo
   puede transformar el programa conservando su semántica en la máquina
   abstracta. Con (a), esa semántica está definida.
2. Con (b), cada valor de coma flotante es la operación IEEE correctamente
   redondeada, idéntica en B₁ y en B₂ (IEEE 754-2008 §4 y §5.4).
3. Con (c) y (d), el estado de la máquina abstracta en cada paso es una
   función determinista de la entrada y la semilla; no interviene nada que
   cambie entre compilaciones (direcciones de carga, tiempo, orden entre
   hilos).
4. Por inducción sobre los pasos, B₁ y B₂ pasan por los mismos estados. ∎

**Comprobación de las condiciones en LabeSAT** (2026-10-01):

- **(a)** CI compila y prueba con ASan/UBSan en cada PR (trabajo «Build con
  sanitizers»). No es una demostración para todas las entradas, pero sí la
  práctica estándar; la comprobación empírica del ADR-0009 añade una red.
- **(b)** Kissat usa `double` en las puntuaciones VSIDS (`heap.h`) y en las
  medias exponenciales (`smooth.c`). En `smooth.c:34-35`,
  `new_biased = old_biased + alpha * delta` es exactamente el patrón que GCC
  fusiona en una FMA si `-march` la incluye, porque `-ffp-contract=fast` es
  el valor por defecto en modo GNU C. Una FMA redondea una vez donde había
  dos, así que el resultado puede diferir en el último bit y cambiar una
  decisión de reinicio. Por tanto, **cualquier `-march` con FMA exige
  `-ffp-contract=off`**. Sin `-march` (x86-64 base, sin FMA) no hay
  contracción posible.
- **(c)** El reloj solo se lee para informar (`mode.c:186`, `mode.c:262`,
  con verbosidad ≥ 2), para el perfilado y para `--time`. Ninguna decisión
  de búsqueda lo usa.
- **(d)** Se revisaron los 24 puntos de ordenación de `src/`. Todos comparan
  literales, referencias (desplazamientos en la *arena*), identificadores o
  puntuaciones. El único que usa direcciones (`vector.c:148-183`) ordena
  vectores **dentro de un único bloque contiguo**: el orden relativo de dos
  direcciones de un mismo array es el de sus desplazamientos (C11
  §6.5.8 ¶5), independiente de dónde se cargue.

**Corolario 3.** Una compilación con PGO (`-fprofile-use`), LTO (`-flto`) o
con `-march=…` **más** `-ffp-contract=off` conserva la trayectoria. Su efecto
es solo de velocidad, y se valida con la igualdad de contadores más un A/B de
tiempos (ADR-0009).

## 4. Catálogo de candidatas, por valor esperado y coste

Clases (ADR-0009):

- **E**: conserva la trayectoria; se prueba la equivalencia y se mide la
  velocidad.
- **P**: cambia solo la tubería y entrega a Kissat la misma CNF; se prueba
  la igualdad de la CNF.
- **S**: cambia la búsqueda; necesita un A/B de PAR-2 preregistrado.

| # | Candidata | Clase | Valor esperado | Coste | Prueba que exige | Estado |
|---|---|---|---|---|---|---|
| **B3** | Ruptura con retraso (`--symmetry-delay`) | S | Alto en lo simétrico (cambio de sistema de pruebas, §1) sin pagar el coste fijo | Hecho | A/B preregistrado | **EXP-009, en curso** |
| **C1** | Compilación guiada por perfil + LTO (+ `-march` con `-ffp-contract=off`) | E | Si da 5–15 % de velocidad, ≈ −0,8 a −2,5 % de PAR-2 (§2) | Bajo | Teorema 5 + contadores idénticos + A/B de tiempo | **Siguiente: EXP-017** |
| **X1** | Refutación en la raíz de sistemas XOR inconsistentes | S | Exponencial en familias de paridad: +4 resueltas y ~−112 s en 2026 (research/06) | Medio | Pruebas aceptadas por dsr-trim, A/B | Aparcada (ADR-0007, fase 2) |
| **K\*** | Puntos calientes de Kissat con p_c ≥ 5 % | E o S | ≤ el techo de Amdahl de cada componente | Por ver | Complejidad + equivalencia | **Pendiente de EXP-016** |
| C4 | Coste de la fase de Schreier de satsuma (35–50 s en station-repacking) | P/S | Acotado: con B3, solo lo pagan las instancias que no caen en 2 s | Alto (código de terceros) | Igualdad de CNF, o A/B si cambia la salida | Tras EXP-009 |
| C5 | Escritura de la prueba (cuenta en el tiempo de la competición) | E | Por medir | Bajo | Prueba idéntica byte a byte | Medir en EXP-016bis |
| ~~C6~~ | Descomprimir una sola vez | P | **Nulo en competición**: las CNF llegan sin comprimir (los guiones de los dos primeros de 2026 las leen tal cual) | — | — | Solo abarata la máquina local |

### Por qué C1 va primero

- Es la única candidata **clase E** que no depende del perfil.
- Su equivalencia se demuestra (Corolario 3) y se comprueba de forma barata
  y determinista con contadores idénticos.
- No toca una sola línea de la búsqueda, así que no introduce riesgo en las
  pruebas UNSAT.
- La PGO reordena el código según las ramas que se toman de verdad y acierta
  más en los saltos y en la caché de instrucciones (Pettis y Hansen, 1990).
  En código con muchas ramas, como un CDCL, la ganancia típica es de un
  dígito o dos en porcentaje; aquí se mide, no se supone.
- **Cautela de diseño**: los perfiles de entrenamiento salen de instancias
  **disjuntas** de las de evaluación (bench/smoke, bench/symm y calib2), para
  no ajustar el binario al banco con el que se mide.

## 5. Plan y puertas de decisión

| Fase | Qué | Puerta para pasar |
|---|---|---|
| O1 | EXP-016 (perfil) y research/08 | Fracciones p_c por fase, con sobrecoste medido |
| O2 | C1: `build.sh --pgo --lto` (+ `--march` con `-ffp-contract=off`); EXP-017 | Contadores idénticos en el banco de equivalencia **y** velocidad con IC95 % > 1 en el A/B |
| O3 | Análisis de los K\* con p_c ≥ 5 %: algoritmo, cota, prueba de corrección o equivalencia, antes de implementar | Demostración escrita en research/08 §6 (se añadirá) |
| O4 | Palancas de sistema de pruebas: B3 (EXP-009) y X1 | Criterios de sus preregistros |

Prioridad de cómputo: un paso de la cola a la vez (ADR-0008). C1 necesita
una tanda de tiempo propia.

## Referencias

- Amdahl, G. M. (1967). Validity of the single processor approach to
  achieving large scale computing capabilities. *AFIPS Spring Joint Computer
  Conference*, 483–485.
- Beame, P., Kautz, H., y Sabharwal, A. (2004). Towards understanding and
  harnessing the potential of clause learning. *JAIR* 22, 319–351.
- Cook, S. A. (1976). A short proof of the pigeon hole principle using
  extended resolution. *SIGACT News* 8(4), 28–32.
- Cook, W., Coullard, C. R., y Turán, G. (1987). On the complexity of
  cutting-plane proofs. *Discrete Applied Mathematics* 18(1), 25–38.
- Gent, I. P. (2013). Optimal implementation of watched literals and more
  general techniques. *JAIR* 48, 231–252. https://doi.org/10.1613/jair.4016
- Haken, A. (1985). The intractability of resolution. *Theoretical Computer
  Science* 39, 297–308.
- Heule, M. J. H., Kiesl, B., y Biere, A. (2017). Short proofs without new
  variables. *CADE-26*, LNCS 10395, 130–147.
  https://link.springer.com/chapter/10.1007/978-3-319-63046-5_9
- IEEE (2008). *IEEE Standard for Floating-Point Arithmetic*, IEEE 754-2008.
- ISO/IEC 9899:2011 (C11), §5.1.2.3 (ejecución del programa) y §6.5.8
  (operadores relacionales sobre punteros).
- GCC Manual, opción `-ffp-contract` (valor por defecto `fast` en los modos
  GNU).
- Pettis, K., y Hansen, R. C. (1990). Profile guided code positioning.
  *PLDI '90*, 16–27.
- Pipatsrisawat, K., y Darwiche, A. (2011). On the power of clause-learning
  SAT solvers as resolution engines. *Artificial Intelligence* 175(2),
  512–525.
- Urquhart, A. (1987). Hard examples for resolution. *JACM* 34(1), 209–219.
