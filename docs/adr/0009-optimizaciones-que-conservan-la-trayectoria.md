# ADR-0009 — Optimizaciones de rendimiento: clases, pruebas exigidas y validación

- **Estado**: aceptado
- **Fecha**: 2026-10-01
- **Decide**: Abel Ponce («tus soluciones tienen que tener una demostración con
  rigor matemático por detrás antes de aplicarlas y todo debe quedar
  documentado»)
- **Relacionado**:
  - ADR-0003 (protocolo experimental), cuyos A/B de PAR-2 siguen siendo
    obligatorios para todo lo que cambie la búsqueda;
  - research/08 (estrategia, Teorema 5 y Proposiciones 1 y 2).

## Contexto

El director pide optimizar LabeSAT para reducir su tiempo, con una
demostración antes de aplicar cada cambio. ADR-0003 está pensado para ideas
que **cambian la búsqueda**: exigen un A/B de PAR-2 preregistrado, con
muchas instancias y semillas, porque su efecto mezcla suerte y mecanismo.

Una optimización que **no** cambia la búsqueda es otra cosa:

- su efecto en las respuestas es nulo **por construcción**;
- su efecto en el tiempo se mide con mucha menos varianza, porque las dos
  ramas hacen exactamente el mismo trabajo.

Tratarlas igual que una heurística nueva desperdiciaría cómputo. Tratarlas
como «obviamente correctas» sería imprudente: un cambio de compilación puede
alterar la búsqueda sin que nadie lo note (research/08 §3.3, FMA).

## Decisión

### 1. Tres clases

| Clase | Qué cambia | Ejemplos |
|---|---|---|
| **E** (equivalente) | Solo la velocidad: misma trayectoria (definición de research/08 §3.3) | Compilación (PGO, LTO, `-march` con `-ffp-contract=off`), estructuras de datos que dan los mismos resultados en el mismo orden, E/S |
| **P** (tubería) | Lo que pasa antes de Kissat, entregándole **la misma CNF** | Lecturas, temporales, orden de pasos de la tubería |
| **S** (búsqueda) | La trayectoria | Heurísticas, presupuestos de inproceso, contabilidad de *ticks*, B3, VSA |

**Regla de borde**: cambiar cómo se cuentan los *ticks* es **S**, aunque
acelere: los presupuestos de inproceso se miden en *ticks*, así que cambian
las decisiones.

### 2. Qué se exige antes de aplicar

**Clase E**:

1. **Prueba escrita** (en research/08 o en el documento del experimento):
   - por qué el cambio conserva la trayectoria; para cambios de compilación,
     el Teorema 5 y la comprobación de sus condiciones (a)–(d);
   - qué complejidad o constante mejora y por qué.
2. **Comprobación determinista**: con presupuesto de conflictos y las mismas
   semillas, contadores **idénticos** (conflictos, decisiones,
   propagaciones) y la misma respuesta en un banco de equivalencia de al
   menos 40 instancias. Una sola diferencia **refuta** la equivalencia y el
   cambio se reclasifica como S.
3. **Medida de velocidad**: A/B intercalado de tiempo de CPU en la misma
   máquina. Como el trabajo es idéntico, basta el cociente de tiempos por
   instancia: media geométrica con IC95 % bootstrap y Wilcoxon. Se adopta
   si el extremo inferior del IC de la aceleración es > 1.
4. Pruebas UNSAT y modelos SAT verificados en `bench/smoke` y `bench/symm`,
   como en cualquier cambio del binario.

**Clase P**: igual que E, pero la prueba de equivalencia es que la CNF que
recibe Kissat es idéntica byte a byte (SHA-1), como en EXP-012.

**Clase S**: ADR-0003 sin cambios (A/B de PAR-2 preregistrado, opción
apagada por defecto hasta validarse).

### 3. Qué no se optimiza

Por la ley de Amdahl (research/08, Proposición 2), un componente con
fracción p del tiempo acelera el total como mucho 1/(1 − p). Un componente
con p < 5 % en el perfil (EXP-016) **no se optimiza**, salvo que el cambio
sea trivial y su equivalencia sea inmediata: su techo (≈ 0,8 % de PAR-2) está
por debajo de lo que podemos medir.

## Consecuencias

- Una optimización E validada **puede ir por defecto** sin el A/B de PAR-2,
  porque no cambia ninguna respuesta. Su aportación en PAR-2 se calcula
  exactamente con la Proposición 1 a partir de la aceleración medida.
- La comprobación determinista es barata: corridas cortas con presupuesto de
  conflictos.
- La clasificación E/P/S se declara en cada commit y en la declaración de IA
  (las optimizaciones E no son «heurísticas ajustadas por IA»).

## Criterios de reversión

Si una optimización E produce **una sola** trayectoria distinta en cualquier
comprobación posterior (CI, otra máquina, otro banco), se retira de los
valores por defecto hasta explicar la diferencia.
