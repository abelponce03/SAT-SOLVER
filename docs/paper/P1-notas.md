# P1 — *Configuration complementarity is an untapped resource in modern CDCL solvers*

> Cuaderno de trabajo del artículo. No es el artículo: es la evidencia que se va
> acumulando y el inventario de lo que falta.

## Argumento en un párrafo

La comunidad de SAT optimiza la media de una configuración: cada año se publican
decenas de variantes de Kissat que ajustan una heurística y se comparan por
instancias resueltas. Los resultados oficiales de la SAT Competition 2026
muestran que ese esfuerzo deja sobre la mesa un recurso mayor que el que
persigue: las 21 variantes de Kissat presentadas tienen un Virtual Best Solver
de 321/400 instancias (PAR-2 = 2354.8 s) frente a las 238 (4611.5 s) del Kissat
de referencia y las 276 (3647.0 s) del ganador. Más revelador todavía: las 12
variantes que quedaron **individualmente peores** que la referencia resuelven
juntas 277 instancias, **más que el campeón del año**. Este trabajo caracteriza
esa complementariedad, muestra que una parte sustancial es reproducible
**dentro de un único solver sin modificar su código** (solo variando su
configuración), y propone un mecanismo de reparto adaptativo de presupuesto que
la convierte en PAR-2 bajo las reglas de la Main Track secuencial.

## Evidencia acumulada

| # | Afirmación | Evidencia | Estado |
|---|---|---|---|
| E1 | El VBS de las variantes de Kissat de 2026 dobla la ganancia del campeón | `scripts/analyze_competition.py vbs`, datos oficiales | ✅ medido |
| E2 | Doce variantes peores que la base superan juntas al campeón | ídem | ✅ medido |
| E3 | Una cartera secuencial k=3 con T/3 da −798 s sin oráculo | `analyze_competition.py portfolio` | ✅ medido (simulación) |
| E4 | El efecto no depende de la ruptura de simetrías | VBS excluyendo satsuma: 311 / 2583.0 s | ✅ medido |
| E4b | El hueco solver-vs-VBS se repite entre ediciones | VBS oficial SC2024: 347 / 1681.3 vs ganador 306 / 2788.1 (+41, −1107 s) | ✅ medido |
| E5 | La complementariedad existe también entre configuraciones del **mismo** binario | EXP-001 | ⏳ en ejecución |
| E6 | La cartera baja además la varianza por seed (robustez) | EXP-002 | ⏳ pendiente |
| E7 | El reparto adaptativo bate al reparto ciego | EXP-003 | ⏳ pendiente |
| E8 | La mejora se sostiene en un banco de validación disjunto | `bench/test` | ⏳ pendiente |
| E9 | **Una regla ajustada en el banco donde se descubre no sobrevive al banco reservado** | EXP-002 (−13.4 s) vs EXP-003 (+2.3 s) sobre la misma regla | ✅ medido |

## Huecos y amenazas a la validez

- **Sobreajuste de la selección**: la cartera voraz de E3 elige miembros mirando
  el mismo banco en que se evalúa. Hay que rehacerlo con validación cruzada por
  familias o con selección sobre 2025 y evaluación sobre 2026.
- **Composición del banco**: 2026 fue rico en combinatoria simétrica.
  **Parcialmente resuelto**: el VBS oficial de SC2024 (347 / 1681.3) también
  queda muy por encima del ganador (306 / 2788.1), así que el fenómeno no es de
  un año. Falta **2025**, cuya tabla instancia-por-instancia los organizadores
  no publicaron; habría que reconstruirla ejecutando las fuentes publicadas, lo
  que es caro pero factible, o pedírsela a los organizadores.
- **Diversidad ≠ configuración**: si EXP-001 dice que las configuraciones del
  Kissat de fábrica apenas se complementan, la tesis del artículo se limita a
  "hacen falta parches distintos", que es una afirmación mucho más débil.
- **Coste del certificado**: una cartera debe producir prueba DRAT válida del
  intento ganador. Hay que medir el sobrecoste y demostrar que las pruebas
  verifican (ya cubierto por `scripts/check_proof.sh` en CI).

## Material para la sección de método

EXP-002 → EXP-003 es un caso de estudio completo y propio del riesgo de ajustar
sobre el banco de descubrimiento: la misma regla da **−13.4 s (−10.5 %)** en las
60 instancias donde se buscó el umbral y **+2.3 s** en las 60 reservadas, con la
explicación mecánica de por qué (una fórmula de 306 variables que solo se
resuelve gracias a las fases lucky, refutando la correlación con el tamaño que
sostenía la regla). Vale como ejemplo concreto en la sección de metodología, y
es del tipo de material que casi nadie publica.

## Segundo caso de estudio metodológico: A4.1 (EXP-005 → EXP-006)

Es el mismo patrón que B3′ y, contado entero, es mejor material que un
resultado positivo.

1. **EXP-005**: la métrica preregistrada (PAR-2) no concluye.
2. Al descomponer, aparece un patrón llamativo: el planificador adaptativo es
   más rápido en 10 de 12 instancias resueltas por ambas ramas (factor 0.648×,
   p = 0.039, Cohen *d* = 0.74).
3. En lugar de publicarlo, se **preregistra** como hipótesis (EXP-006), con datos
   que ningún A/B de A4 había visto y con potencia holgada (n = 40 frente a
   ~14 necesarias).
4. **Resultado**: 0.983×, IC [0.819, 1.151], p = 0.69. Las propagaciones, que
   son deterministas e inmunes a la deriva, tampoco se mueven (0.999×).

Qué muestra:

- **Un p = 0.039 obtenido *a posteriori* con n = 12 no vale nada.** Es el
  jardín que se bifurca, medido: el efecto cae del 35 % a menos del 2 %.
- **El control con el esfuerzo determinista es clave**: distingue «no hay
  efecto» de «el efecto está oculto por la deriva de la máquina».
- **En la literatura de SAT sería un +35 % publicable.** Aquí es un nulo
  documentado.

Para el artículo: la tabla con los dos pasos, uno junto al otro, y el coste en
horas de máquina de hacerlo bien (EXP-006: unas 2,5 h en 4 núcleos).

## Trabajo relacionado que hay que leer y citar

- SATzilla (Xu et al.) y la literatura de *algorithm selection* — el antecedente
  obvio; la diferencia a defender es "dentro del binario, sin modelo entrenado".
- ppfolio / ManySAT — carteras clásicas, en su mayoría paralelas.
- *Restart strategies and their complementarity* (línea Luby/Glucose).
- Kissat_MAB y la familia de bandits 2021–2026 — el contraste: optimizar la
  media frente a explotar la varianza.
- Hyperparameter tuning automático de solvers (SMAC, ParamILS) — producen
  configuraciones; nadie las usa **juntas**.
