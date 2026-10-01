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
5. **Qué cuenta como «misma búsqueda» al tocar el código** (§6). Los
   *ticks* de Kissat deciden el cambio de modo y los presupuestos de
   inproceso, y el orden de la arena decide qué cláusulas se borran. Una
   optimización que obtiene el mismo resultado visitando menos razones
   **cambia la búsqueda**. El Teorema 6 (refinamiento) dice qué hay que
   demostrar. La auditoría del núcleo concluye que cada componente ya es
   lineal en lo que cualquier algoritmo correcto tiene que leer
   (Proposición 3). El margen está en la latencia de memoria: precarga en la
   propagación (K1-K2), pendiente de lo que mida EXP-016.

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
| O3 | Análisis de los K\* con p_c ≥ 5 %: algoritmo, cota, prueba de corrección o equivalencia, antes de implementar | Demostración escrita en §6 (marco y auditoría del núcleo: hechos; candidatas K1-K3 a la espera de EXP-016 Q4) |
| O4 | Palancas de sistema de pruebas: B3 (EXP-009) y X1 | Criterios de sus preregistros |

Prioridad de cómputo: un paso de la cola a la vez (ADR-0008). C1 necesita
una tanda de tiempo propia.

## 6. Optimizar el código sin cambiar la búsqueda: marco de demostración

El Teorema 5 cubre el compilador. Esta sección cubre los cambios **en el
código fuente** que pretenden ser clase E (ADR-0009): qué hay que demostrar y
qué partes del estado de Kissat no se pueden tocar.

### 6.1 El estado que decide el futuro de una corrida

**Definición (estado observable).** Llamamos σ a la tupla formada por:

- la pila de asignación, con razón y nivel de cada literal, y los valores;
- cada lista de vigilancia **como secuencia** (importa el orden);
- la *arena* de cláusulas **como secuencia** (importa el orden de las
  cláusulas, no su dirección);
- la cola VMTF (enlaces y sellos) y el montículo de puntuaciones;
- las fases guardadas y las medias exponenciales;
- los límites y **todos los contadores estadísticos que se leen para decidir
  algo**, incluidos los *ticks*;
- el estado del generador aleatorio y los valores de las opciones.

No forman parte de σ las direcciones, la capacidad reservada de los vectores,
el estado de las cachés ni el tiempo (Teorema 5, (c) y (d)).

**Lema 1 (los ticks son estado).** El contador `search_ticks` decide:

- el cambio entre modo *focused* y *stable*: en las fases impares se cambia
  cuando `search_ticks ≥ limits.mode.ticks` (`mode.c:336-337`);
- el presupuesto de cada inproceso: `SET_EFFORT_LIMIT` calcula
  `esfuerzo × (search_ticks − último)` (`kimits.h:135-170`), y de él viven
  sondeo, vivificación, barrido, etc.

Y lo incrementan, además de la propagación (`propsearch.c:24`):

- el análisis de conflictos (`analyze.c:158`, una unidad por razón grande
  visitada);
- la minimización (`minimize.c:52`) y el encogimiento (`shrink.c:180`), con
  `minimizeticks=1`, que es el valor por defecto.

*Consecuencia.* Un cambio que produce **la misma cláusula aprendida**
visitando **menos razones** (por ejemplo, otra memoización en la
minimización) **cambia** `search_ticks`, y con ello el instante del cambio de
modo y los presupuestos de inproceso. **No es clase E**: es clase S, aunque
sea «solo» una optimización. Para que sea clase E tiene que conservar la
cuenta de ticks del original. Una forma es un contador fantasma que sume lo
que el original habría sumado, si ese número se puede calcular de forma
barata.

**Lema 2 (el orden de la arena y de las listas es estado).**

- `reduce.c:63-99` recoge las cláusulas candidatas en el orden de la arena y
  las ordena por (glue, tamaño) con una ordenación por base (*radix*), que es
  estable. Los empates son frecuentes y se resuelven por el orden de la
  arena. Por tanto, el orden de la arena decide **qué cláusulas se borran**.
- `proplit.h` recorre la lista de vigilancia en orden y se detiene en el
  **primer** conflicto: el orden de la lista decide qué conflicto se
  analiza.

*Consecuencia.* Cambiar dónde se colocan las cláusulas al compactar
(`collect.c`), al crearlas o al reordenar las listas de vigilancia es clase
S.

**Lema 3 (sustituir una ordenación).** Sea < un orden estricto débil sobre
los elementos que se ordenan. Si dos algoritmos de ordenación correctos A y B
reciben la misma secuencia, sus salidas coinciden en todas las entradas si:

- (i) no hay dos elementos distintos equivalentes (< es total sobre esa
  entrada), **o**
- (ii) A y B son estables.

Si hay elementos equivalentes y alguno de los dos no es estable, la
coincidencia no está garantizada.

*Demostración.* Una salida ordenada está determinada salvo permutaciones
dentro de cada clase de equivalencia de <.

- Con (i), las clases tienen un solo elemento y la salida es única.
- Con (ii), las dos conservan el orden de entrada dentro de cada clase, así
  que coinciden.
- Si A no es estable, existe una entrada con dos equivalentes x ≠ y que A
  invierte. Si B es estable, en esa entrada B no los invierte y las salidas
  difieren. Si B tampoco es estable, la igualdad depende de los detalles de
  cada uno. ∎

*Aplicación a Kissat.* `QUICK_SORT` (`sort.h:41`) no es estable.

- Es seguro sustituirlo donde la clave no tiene empates:
  - en `bump.c:17-24` (sellos VMTF, únicos por variable);
  - en `analyze.c:219-225` (niveles de decisión, distintos por
    construcción).
- Donde hay empates, solo con una ordenación estable que replique el orden de
  entrada. Es el caso de `reduce.c`, que ya usa *radix*.

**Teorema 6 (refinamiento).** Sea K el programa original, con estados Σ y un
paso F: Σ → Σ, y K' el optimizado, con estados Σ' y paso F'. Supongamos que
existe una función de abstracción α: Σ' → Σ tal que:

- **(i)** α(σ'₀) = σ₀ para los estados iniciales de la misma entrada y
  semilla;
- **(ii)** para todo σ' alcanzable, α(F'(σ')) = F(α(σ'));
- **(iii)** las salidas (respuesta, modelo, bytes de la prueba y contadores)
  se calculan solo a partir de la abstracción: out'(σ') = out(α(σ'));
- **(iv)** la comprobación de terminación (`TERMINATED`) se hace en los
  mismos puntos del paso abstracto.

Entonces K y K' conservan la trayectoria (§3.3).

*Demostración.* Por inducción sobre n, α(F'ⁿ(σ'₀)) = Fⁿ(σ₀).

- El caso base es (i).
- Paso inductivo: α(F'ⁿ⁺¹(σ'₀)) = α(F'(F'ⁿ(σ'₀))) = F(α(F'ⁿ(σ'₀)))
  = F(Fⁿ(σ₀)), por (ii) y la hipótesis de inducción.
- Las salidas coinciden por (iii).
- Por (iv), una terminación por tiempo corta las dos corridas en estados
  abstractos del mismo tipo. ∎

Es el método de Hoare (1972) para probar representaciones de datos, en la
forma de simulación hacia delante de de Roever y Engelhardt (1998). En la
práctica, F es un **macropaso**:

- la propagación de un literal;
- un análisis de conflicto;
- un `reduce`;
- una ronda de un inproceso.

Basta con que el diagrama conmute en sus fronteras, porque nada fuera del
macropaso lee su estado interno.

**Corolario 4 (pistas sin semántica).** Estos cambios son clase E con
α = identidad:

- `__builtin_prefetch` sobre una dirección cuyo cálculo es válido;
- `__builtin_expect`;
- atributos de alineación, `inline` y `noinline`;
- reordenar lecturas independientes.

*Demostración.* Ninguno cambia el valor de ningún objeto de la máquina
abstracta de C11, así que F' = F. Para el *prefetch*, el manual de GCC
garantiza que no provoca fallos aunque la dirección no sea válida, siempre
que la **expresión** que la calcula sí lo sea. Por eso solo se precarga
`arena + ref` cuando `ref` es una referencia leída de un vigilante grande,
que el invariante de Kissat sitúa dentro de la arena
(`assert (ref < SIZE_STACK (solver->arena))`). ∎

### 6.2 Auditoría del núcleo de búsqueda (Kissat 4.0.4, lectura del código)

Notación:

- k: variables analizadas en un conflicto;
- R: suma de los tamaños de las razones visitadas;
- g: glue de la cláusula aprendida;
- n: número de variables;
- w: tamaño de la lista de vigilancia.

| Componente | Código | Algoritmo | Coste | ¿Mejorable en O? |
|---|---|---|---|---|
| Propagación | `proplit.h` | Vigilantes con búsqueda circular, literal bloqueante y binarias en línea | O(w + reemplazos) por literal; óptimo amortizado (Teorema 4) | No |
| Análisis 1UIP | `analyze.c` | Recorrido hacia atrás del grafo de implicación | O(R) | No (Proposición 3) |
| Minimización | `minimize.c` | Recursiva con memo (*removable*/*poisoned*), profundidad ≤ `minimizedepth` | Lineal en las razones alcanzadas: cada variable se resuelve una vez (Sörensson y Biere, 2009) | No |
| Encogimiento | `shrink.c` | *All-UIP* por bloques de nivel | Lineal en el grafo de implicación (Fleury y Biere, 2021) | No |
| Orden por niveles | `analyze.c:219` | Inserción/*quick* si g < 32; *radix* si no | O(g log g) u O(g) | Despreciable |
| Puntuación (*bump*) | `bump.c` | *Focused*: *radix* por sello y al frente de la cola VMTF. *Stable*: montículo binario | O(k) en *focused*; O(k log n) en *stable* | No en *focused*; en *stable*, el log n es el del montículo |
| Decisión | `decide.c` | VMTF con puntero de búsqueda (Biere y Fröhlich, 2015) o montículo | O(1) amortizado; O(log n) por extracción | No |
| Retroceso | `backtrack.c` | Desasigna y reinserta | O(literales desasignados), × log n en *stable* | No |
| `reduce` | `reduce.c` | Recorrido de la parte redundante de la arena + *radix* | O(\|arena redundante\|) por llamada | No (hay que leer cada candidata) |
| Recolección | `collect.c` | Compactación de la arena y vaciado de vigilantes | O(\|arena\| + Σ w) | No |

**Proposición 3 (cota inferior del análisis).** Todo algoritmo que calcule
exactamente la cláusula 1UIP a partir del grafo de implicación tiene que leer
Ω(R) literales en el peor caso.

*Demostración (adversario).* Supongamos que un algoritmo no lee el literal ℓ
de una razón visitada en el recorrido del original. El adversario cambia ℓ
por un literal falso de un nivel inferior que no esté en la cláusula
aprendida. La 1UIP correcta de la nueva instancia contiene ese literal. El
algoritmo, que no ha leído ℓ, devuelve la misma salida que antes, sin él:
error. Por tanto debe leer los R literales. ∎

**Conclusión de la auditoría.** En el núcleo de búsqueda **no queda mejora
asintótica**: cada componente es lineal, o casi, en la información que
cualquier algoritmo correcto tiene que leer. Lo que queda es el factor
constante, y en un CDCL ese factor lo domina la **latencia de memoria**:

- cada vigilante grande cuya cláusula no está en caché cuesta un fallo de
  caché (`arena + ref` en `proplit.h`);
- Chu, Harwood y Stuckey (2009) midieron que los fallos de caché dominan el
  tiempo de los resolvedores CDCL y propusieron, entre otras cosas, guardar
  un literal en el propio vigilante, que es el literal bloqueante que Kissat
  ya usa.

Candidatas de clase E que se derivan de esto (para después de EXP-016 Q4 y
solo si `propagate` pesa lo suficiente):

| # | Candidata | Clase | Prueba | Riesgo |
|---|---|---|---|---|
| K1 | Precarga (*prefetch*) de la cabecera de las cláusulas de los vigilantes grandes que vienen a continuación en la lista, con una anticipación fija | E (Corolario 4) | α = identidad; ticks intactos, porque no se toca ningún `ticks++` | Puede **ralentizar** si la cláusula ya estaba en caché o si un conflicto corta la lista: se mide |
| K2 | Precarga de `values[blocking]` del siguiente vigilante | E (Corolario 4) | Ídem | Ídem; `values` cabe en caché en instancias pequeñas |
| K4 | Precarga del inicio de la lista de vigilancia de ¬ℓ al asignar ℓ, antes de que le toque propagarse | E (Corolario 4) | Ídem | Si la cola de propagación es larga, la línea puede salir de la caché antes de usarse |
| K3 | Inserción de vigilantes diferida (`delayed`) sin la pila intermedia | E solo si el orden final de cada lista es el mismo (Lema 2) | Teorema 6 con α = identidad sobre las listas | Si cambia el orden de una sola lista, es S |

**Evidencia previa para K1 y K4.** Manthey y Saptawijaya (2010) midieron,
en un CDCL propio que pasaba ~90 % del tiempo en la propagación:

- **+12 %** de velocidad precargando las cláusulas de la lista que se está
  recorriendo (su «primer esquema», que es K1);
- **+4 %** precargando las de las listas de los 10 literales siguientes de la
  cola de propagación (su «segundo esquema», pariente de K4);
- sin cambiar la búsqueda y sin ningún caso de pérdida en su banco.

Su resolvedor no tenía literal bloqueante, que evita muchas visitas a la
cláusula. En Kissat cabe esperar **menos**. Hölldobler, Manthey y
Saptawijaya (2010) recogen el conjunto: hasta un 83 % y un 60 % de media
combinando técnicas de memoria, sin cambiar la búsqueda. Como `proplit.h`
lo incluyen tanto la propagación de búsqueda como la de sondeo
(`propsearch.c`, `proprobe.c`), K1 acelera las dos.

Lo que **no** se hará como «optimización» (sería clase S por los Lemas 1-3):

- otra memoización en la minimización (cambia ticks);
- otro orden de compactación de la arena (cambia qué se borra);
- sustituir la ordenación de `reduce` por una inestable.

Cualquiera de estas, si se quisiera, necesitaría un A/B de PAR-2.

## Referencias

- Amdahl, G. M. (1967). Validity of the single processor approach to
  achieving large scale computing capabilities. *AFIPS Spring Joint Computer
  Conference*, 483–485.
- Beame, P., Kautz, H., y Sabharwal, A. (2004). Towards understanding and
  harnessing the potential of clause learning. *JAIR* 22, 319–351.
- Biere, A., y Fröhlich, A. (2015). Evaluating CDCL variable scoring
  schemes. *SAT 2015*, LNCS 9340, 405–422.
  https://doi.org/10.1007/978-3-319-24318-4_29
- Chu, G., Harwood, A., y Stuckey, P. J. (2009). Cache conscious data
  structures for Boolean satisfiability solvers. *JSAT* 6(1-3), 99–120.
- Cook, S. A. (1976). A short proof of the pigeon hole principle using
  extended resolution. *SIGACT News* 8(4), 28–32.
- Cook, W., Coullard, C. R., y Turán, G. (1987). On the complexity of
  cutting-plane proofs. *Discrete Applied Mathematics* 18(1), 25–38.
- de Roever, W.-P., y Engelhardt, K. (1998). *Data Refinement:
  Model-Oriented Proof Methods and their Comparison*. Cambridge University
  Press.
- Fleury, M., y Biere, A. (2021). Efficient all-UIP learned clause
  minimization. *SAT 2021*, LNCS 12831.
  https://doi.org/10.1007/978-3-030-80223-3_12
- Gent, I. P. (2013). Optimal implementation of watched literals and more
  general techniques. *JAIR* 48, 231–252. https://doi.org/10.1613/jair.4016
- Haken, A. (1985). The intractability of resolution. *Theoretical Computer
  Science* 39, 297–308.
- Heule, M. J. H., Kiesl, B., y Biere, A. (2017). Short proofs without new
  variables. *CADE-26*, LNCS 10395, 130–147.
  https://link.springer.com/chapter/10.1007/978-3-319-63046-5_9
- Hoare, C. A. R. (1972). Proof of correctness of data representations.
  *Acta Informatica* 1(4), 271–281.
- Hölldobler, S., Manthey, N., y Saptawijaya, A. (2010). Improving
  resource-unaware SAT solvers. *LPAR-17*, LNCS 6397, 519–534.
  https://doi.org/10.1007/978-3-642-16242-8_37
- IEEE (2008). *IEEE Standard for Floating-Point Arithmetic*, IEEE 754-2008.
- ISO/IEC 9899:2011 (C11), §5.1.2.3 (ejecución del programa) y §6.5.8
  (operadores relacionales sobre punteros).
- GCC Manual, opción `-ffp-contract` (valor por defecto `fast` en los modos
  GNU) y `__builtin_prefetch` (no provoca fallos aunque la dirección no sea
  válida, si la expresión que la calcula lo es).
- Manthey, N., y Saptawijaya, A. (2010). Towards improving the resource
  usage of SAT solvers. *Pragmatics of SAT (POS-10)*.
  https://easychair.org/publications/paper/9W
- Pettis, K., y Hansen, R. C. (1990). Profile guided code positioning.
  *PLDI '90*, 16–27.
- Pipatsrisawat, K., y Darwiche, A. (2011). On the power of clause-learning
  SAT solvers as resolution engines. *Artificial Intelligence* 175(2),
  512–525.
- Sörensson, N., y Biere, A. (2009). Minimizing learned clauses. *SAT
  2009*, LNCS 5584, 237–243. https://doi.org/10.1007/978-3-642-02777-2_23
- Urquhart, A. (1987). Hard examples for resolution. *JACM* 34(1), 209–219.
