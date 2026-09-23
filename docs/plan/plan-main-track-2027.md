# Plan: Main Track 2027 con declaración honesta del uso de IA

- **Fecha**: 2026-09-23 · documento vivo, que se revisa en cada hito.
- **Decide**: Abel Ponce («planifica para el caso Main Track con la declaración
  honesta del uso de la IA»).
- **Relación con otros documentos**: concreta y sustituye las fases 3–7 de
  [`ROADMAP.md`](../ROADMAP.md). El estado vivo está en los issues de GitHub
  (§8).

---

## 1. Premisas

1. **Pista**: Main Track secuencial, con pruebas UNSAT obligatorias, T = 5000 s
   y 32 GB (reglas de 2026).
2. **Declaración honesta**:
   - la descripción del solver y la de los benchmarks declaran, con cifras
     exactas, qué escribió la IA y qué heurísticas se ajustaron con procesos
     asistidos por IA;
   - no se reescribe código para esquivar una etiqueta.
3. **Consecuencia esperada**: casi seguro, la etiqueta **AI-generated** dentro
   de la Main Track. En 2026 eso supuso no optar a los premios regulares y
   competir por el premio de la subcategoría IA. **La etiqueta no cambia el
   ranking por PAR-2**, que es común a todos. La clasificación final la deciden
   los organizadores; el correo sale cuando las mejoras estén definidas
   (`docs/decisiones/borrador-correo-organizadores.md`).

## 2. Objetivos medibles

Los umbrales salen del ranking oficial de 2026: PAR-2 medio sobre 400
instancias, con 2 × 5000 s por instancia no resuelta.

| Objetivo | Umbral de 2026 | Qué significa |
|---|---|---|
| **O1 · Mejor solver con etiqueta IA** de la Main Track | superar 4010 s (`zheng_kissat-mab-hypre-evolve`, 5.º general) | Premio de la subcategoría IA |
| **O2 · Top 5 general** | ≤ 4010 s | Competitivo con las mejores entradas regulares |
| **O3 · Nivel del ganador** | ≈ 3647 s (`anders_satsuma-iter-kissat`: satsuma + Kissat 4.0.4, **nuestra misma base**) | Techo realista si la ruptura de simetrías replica y B3 suma |

**Aviso**: con 4 núcleos y sin clúster no se puede medir el PAR-2 a 5000 s del
conjunto de 2027. Los objetivos se siguen con **estimaciones por estratos** a
partir de las instancias de 2026 (EXP-007 §4), y se dice así en cada informe.

## 3. Palancas técnicas, por valor esperado y coste

| # | Palanca | Evidencia hasta hoy | Coste | Decisión o experimento |
|---|---|---|---|---|
| **P1** | Ruptura de simetrías (satsuma MIT) | **EXP-007 (cerrado)**: H 37/45 frente a 8/45 (p = 8·10⁻¹⁰); **en N ralentiza 1.42×**; estimación de −90 s. Veredicto: **solo condicional** | Hecho. **Integrada en el binario de Kissat** (D-016, ADR-0007, fase 1) | Opcional (`--symmetry`) hasta P2; equivalencia en EXP-012 |
| **P2** | **Activación condicional** (B3). **Prioridad n.º 1 tras EXP-007**. Diseño: decisión probabilística calibrada con regla de coste esperado (research/05, R1) | El oráculo valdría −322 s extra (research/01). EXP-007: el coste en N viene de la búsqueda de kissat sobre la fórmula modificada, no del tiempo de satsuma. El criterio debe predecir si la ruptura **ayuda** | Medio | EXP-009, preregistrado |
| **P3** | Cliques en MIT (reimplementar la clique máxima) | **Medido**: sin cliques quedan sin resolver 6 instancias de H que con cliques caen en < 2 s (≈ −29 s de PAR-2 en el banco de EXP-007) | 1–2 días | D-005 (#9) |
| **P4** | **Base Kissat sc2026** en lugar de 4.0.4 | sc2026 (sin publicar, MIT) quedó 16.º en solitario. No se sabe si mejora a 4.0.4 | Portar ~105 líneas activas (`scripts/declaracion_ia.sh`) | **EXP-008** → D-013 |
| **P5** | Topes de satsuma (tiempo y tamaño) | Provisionales, 60 s y 512 MiB | Bajo | Se fijan con los datos de EXP-007 y EXP-009. Se **declaran** como heurística ajustada con asistencia de IA |
| — | ~~A4.2 (más brazos)~~ | A4.1 no tuvo efecto (EXP-006) | — | **Descartada**: la fase 3 original desaparece |

## 4. Variantes a presentar (hasta 4 solvers secuenciales por participante)

Propuesta, pendiente de la decisión **D-014**. Cada variante lleva su propia
declaración de IA.

| Variante | Contenido | Para qué |
|---|---|---|
| **V1 · LabeSAT** | La mejor combinación validada: P1 + P2 (+ P3 y P4 si pasan) | Entrada principal: O1–O3 |
| **V2 · LabeSAT-nosym** | Mismo kissat, sin ruptura de simetrías | Cobertura por si la ruptura daña en 2027 (más SAT o más instancias grandes); mide la contribución de P1 en datos oficiales |
| **V3 · LabeSAT-base alternativa** | V1 sobre la otra base (4.0.4 o sc2026, la que no gane EXP-008) | Solo si EXP-008 no es concluyente |
| V4 | Sin asignar | Se reserva para lo que salga de la fase de validación |

Condición para presentar una variante: un experimento preregistrado que la
respalde. **No se presenta nada sin medir.**

## 5. Declaración honesta: trabajo continuo

1. **Cifras reproducibles**: `scripts/declaracion_ia.sh` calcula desde git:
   - la base y su commit;
   - las líneas añadidas y eliminadas en Kissat;
   - las líneas del guion;
   - cuáles de esas líneas están activas en la configuración de competición.

   Se ejecuta en CI y su salida alimenta la sección *Mandatory statement* de
   `docs/competicion/descripcion-solver.tex`.
2. **Líneas escritas por IA**: el 100 % del código de LabeSAT lo escribe el
   asistente bajo la dirección del autor (`docs/metodologia/`).
3. **Heurísticas ajustadas por IA**: una lista explícita, que se mantiene al día
   en `docs/competicion/declaracion-ia.md`. Incluye todo parámetro fijado con
   experimentos diseñados con IA: topes de satsuma, umbrales de B3, etc.
4. **Benchmarks**: su descripción también lleva la declaración de IA, si el
   generador lo escribe el asistente.
5. **Artículos**: la sección de metodología cuenta el proceso sin rebajarlo.

## 6. Calendario e hitos

| Hito | Fecha objetivo | Criterio de salida | Depende de |
|---|---|---|---|
| **H1 · Cierre de EXP-007** | ✅ **2026-09-23** | Solo condicional; seguridad 61/61 sin fallos | — |
| **H2 · Base decidida** (EXP-008) | nov 2026 | A/B de Kissat 4.0.4 frente a sc2026, preregistrado, en calib + calib2 | H1 (máquina libre) |
| **H3 · Cliques decididos** (D-005) | nov 2026 | Coste de mantener MIT medido en PAR-2; si hay coste, reimplementación MIT validada | H1 |
| **H3b · Un solo binario** (D-016) | oct 2026 | `kissat --symmetry` equivalente a la tubería (EXP-012), en CI y en la configuración de competición; la entrega deja de depender de `solver/labesat` | — |
| **H4 · B3 validado** (EXP-009) | dic 2026 – ene 2027 | Criterio de activación entrenado sin `bench/test` y validado preregistrado | H1, H2 |
| **H5 · Mejoras definidas** | **≤ 25 ene 2027** | Contenido de V1–V4 congelado | H2–H4 |
| **H6 · Correo a los organizadores** | **≤ 1 feb 2027** | Enviado con las cifras de H5 | H5 |
| **H7 · 20 benchmarks** | feb – mar 2027 | 20 instancias nuevas, ≥ 10 «interesantes» (idealmente 20), descripción con declaración de IA | D-004 |
| **H8 · Validación final** | mar 2027 | `bench/test`, una sola vez, al presupuesto más largo posible; pruebas verificadas con el commit exacto del verificador de 2027 | H5 |
| **H9 · Registro** | ~abr 2027 (en 2026, 19 abr) | Variantes y 20 benchmarks registrados | H7, H8, respuesta de H6 |
| **H10 · Envío del solver** | ~may 2027 (en 2026, 10 may) | Paquete de competición probado en un contenedor limpio | H9 |
| **H11 · Descripción del sistema** | ~may 2027 (en 2026, 17 may) | PDF IEEE sin marcas `PENDING` | H10 |

## 7. Presupuesto de cómputo (4 núcleos, sin clúster)

| Experimento | Diseño | Coste estimado |
|---|---|---|
| EXP-007 (en curso) | 74 parejas, T = 180 s | ~5 h |
| EXP-008 (base) | 60 instancias × 2 semillas, T = 180 s, intercalado | ~5 h |
| EXP-009 (B3) | Entrenamiento con los datos de EXP-007 y de 2026, más validación en ~80 instancias | ~6–8 h |
| H8 (validación final) | 60 instancias de test, T = 1000 s, 2 variantes | ~35 h en secuencial. Por eso se decide antes de H8 cuántas variantes se validan |
| H7 (benchmarks) | Calibrar ~60 candidatas con MiniSat (60 s) y LabeSAT (≤ 1 h) | ~20–40 h |

**Riesgo principal**: sin clúster, H8 no puede reproducir T = 5000 s. Se
declara en la descripción y en los artículos. Si aparece acceso a cómputo,
H8 se amplía.

## 8. Seguimiento en GitHub

- **Épica del plan: #20**, con EXP-008 (#21), benchmarks (#22) y entrega (#23).
- Épicas por fase, cada una con sub-issues:
  - fase 2 (#12);
  - base y variantes;
  - benchmarks;
  - entrega;
  - declaración de IA;
  - documentación (#16).
- Decisiones de este plan en la agenda (#4):
  - **D-013**: base de Kissat;
  - **D-014**: variantes a presentar.
- Revisión del plan: en cada hito se actualizan esta tabla, el ROADMAP y el
  acta.

## 9. Riesgos

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| La ruptura de simetrías no replica con satsuma MIT | Media | Alto | EXP-007; si falla, P3 (cliques MIT) y D-005 |
| El conjunto de 2027 trae menos simetría o más SAT grandes | Media | Medio | P2 (B3) y la variante V2 como cobertura |
| Anders compite en 2027 con una versión mejorada | Alta | Medio | Aportación propia: B3 y quizá la base sc2026; O1 no depende de ganarle |
| Otros participantes con IA también usan satsuma (en 2026, zheng) | Alta | Medio | Ídem |
| Una prueba falla con el verificador de 2027 | Baja | **Descalificación** | CI con el commit exacto del verificador; H8 verifica a escala |
| Sin clúster: decisiones a T = 180 s | Cierta | Medio | Estratos, preregistro y declararlo |
| Cambian las reglas de 2027 (IA, pruebas, plazos) | Media | Medio–alto | Revisar la convocatoria en cuanto salga; H6 con margen |
