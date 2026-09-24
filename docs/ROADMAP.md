# LabeSAT — hoja de ruta hasta la SAT Competition 2027

- **Fecha**: 2026-09-23 · se revisa al cerrar cada fase
- **Objetivo**: una entrada competitiva en la **Main Track** de la SAT Competition
  2027 y, en paralelo, al menos un artículo con una contribución defendible.

> **Supuesto de calendario.** Las fechas de 2027 no están publicadas. Se toman las
> de 2026 como referencia: registro del solver **con benchmarks** el 19 de abril,
> envío del solver secuencial el 10 de mayo, descripción del sistema el 17 de
> mayo. Hay que confirmarlas en cuanto salga la convocatoria.

> **Seguimiento en GitHub.** Este plan es el mapa. El estado vivo está en los
> issues:
>
> - épica de la fase 2: #12;
> - épica de documentación: #16;
> - infraestructura: #17;
> - las **decisiones abiertas**, en la Reunión 1 (#4), con un sub-issue por
>   decisión (etiqueta `decisión`).
>
> El plan se mueve cuando se resuelve una decisión (ADR-0005 §2), y aquí se
> apunta el cambio.

---

## 1. Tres reglas que cambian el plan

Leídas en `satcompetition.github.io/2026/rules.html` y `tracks.html`:

### 1.1 Hay que aportar 20 benchmarks nuevos (obligatorio)

> «Each team participating in the Main Track is required to submit **20 benchmark
> instances that have not been seen in previous competitions**. At least 10 of
> those benchmarks should be *interesting*: not too easy (solvable by MiniSat in a
> minute) or too hard (unsolvable by the participants own solver within one hour).»

No estaba en ningún plan. Es trabajo real —encontrar o generar una familia de
problemas nueva, calibrar su dificultad contra MiniSat y contra LabeSAT— y se
entrega **con el registro**, un mes antes que el solver. Fase 4.

### 1.2 Las carteras de solvers tienen restricciones

> «Pure Portfolios which are a combination of two or more (core) SAT solvers
> developed by different groups of authors are **not allowed**. Otherwise, solver
> compositions must have **different solving methodologies**, e.g., CDCL, SLS,
> Lookahead, Groebner Basis, etc., **not just different solving strategies**.»

Consecuencias para el catálogo:

- **La cifra de −798 s de la cartera A1** (`docs/research/01`) se simuló con
  solvers **de otros grupos** (satsuma, lymphosat, mergesat). Esa combinación
  concreta **está prohibida**. Sigue valiendo como medida de cuánta
  complementariedad hay, no como entrada posible.
- **Una cartera de configuraciones de Kissat** queda en zona gris: son
  «estrategias distintas» de una misma metodología (CDCL). No se apuesta por ella
  sin confirmación escrita de los organizadores.
- **A4 no tiene este problema**: reparte presupuesto *dentro* de una única
  búsqueda, igual que la alternancia `stable`/`focused` que Kissat ya hace. Es un
  argumento más a su favor, además de los técnicos.

### 1.3 Existen subcategorías «AI-generated» y «AI-tuned»

> «these solvers are **not eligible for regular track prizes**»

Las modificaciones de LabeSAT se están escribiendo con asistencia de IA. Si eso
lo encuadra o no en «AI-generated» depende de una definición que la página de
2026 **no da**. Es una decisión de los organizadores, no nuestra, y afecta a la
elegibilidad para premio, así que **hay que preguntarlo por escrito antes del
registro** y declarar la asistencia de IA de forma proactiva. Ocultarlo no es
una opción: el historial de git lo documenta commit a commit.

---

## 2. Dos objetivos distintos que no hay que confundir

| | **Entrada competitiva** | **Contribución publicable** |
|---|---|---|
| Qué la mide | PAR-2 a T = 5000 s sobre el banco de 2027 | Novedad + evidencia |
| Mayor palanca medida | **Ruptura de simetrías**: −964 s en los datos de 2026 (ganó la edición) | **A4**: reparto adaptativo, nuestro y defendible |
| Problema | No es nuevo (satsuma existe) | Su efecto medido es pequeño |

Una entrada que solo lleve A4 probablemente no será competitiva; una que solo
lleve simetrías no tendrá nada propio que contar. **El plan persigue las dos
cosas**, y el límite de **cuatro variantes secuenciales por participante**
permite presentarlas por separado y juntas.

---

## 3. Fases

### Fase 1 — Cerrar A4.1 · octubre 2026

- [x] **EXP-006**: ¿acelera A4.1 las instancias que resuelve? **No**: 0.983×,
      p = 0.69, con las propagaciones sin cambio (0.999×).
- [x] A4.1 cerrado como «sin efecto detectado». El seguimiento con presupuesto
      largo (renumerado EXP-008) no se hace.
- [ ] **Resolver el acceso a cómputo** (ver §4). Sigue siendo el mayor riesgo.

### Fase 2 — Preprocesado estructural condicional · noviembre–diciembre 2026

La mayor palanca de PAR-2 medida en todo el proyecto.

- [x] Licencia y viabilidad (ADR-0004): **satsuma upstream es MIT** si se
      compila con `CLIQUES=OFF` (cliquer, GPLv2, queda fuera). Se usa como
      programa externo fijado a un commit; nada de la entrada GPLv3 de 2026.
- [x] Pruebas: formato **SR** (prefijo de satsuma) + DRAT de kissat en el mismo
      fichero (`--append-proof`, propio), verificado con **dsr-trim** contra la
      CNF original. En CI con el build normal y el de competición, con control
      negativo (`scripts/test_symmetry.sh`).
- [x] Guion de entrada `solver/labesat` con respaldo a kissat puro si satsuma
      falla o tarda.
- [ ] **EXP-007**: A/B `labesat` vs `labesat --no-symmetry` (preregistrado),
      contando también dónde **empeora** (en 2026: 51 arregladas, 13 rotas).
- [ ] Coste de mantener MIT: satsuma sin cliques vs con cliques (medido fuera
      del repositorio).
- [ ] Integrarlo **condicionado** (B3): el oráculo condicional vale −322 s
      extra. Criterio de activación, preferiblemente con features baratos
      (tamaño, tiempo de satsuma, nº de generadores) o los de `classify.c`.

### Fases 3–7 — Plan Main Track con declaración honesta (desde 2026-09-23)

El director fijó el caso: **Main Track con declaración honesta del uso de IA**.
El plan detallado está en
[`plan/plan-main-track-2027.md`](plan/plan-main-track-2027.md): objetivos,
palancas, variantes, hitos H1–H11, presupuesto de cómputo y riesgos. Resumen:

- ~~A4.2 (más brazos)~~ **descartada**: A4.1 no tuvo efecto (EXP-006).
- Palancas por orden:
  1. ruptura de simetrías (EXP-007);
  2. activación condicional B3 (EXP-009);
  3. cliques en MIT (D-005);
  4. base Kissat sc2026 frente a 4.0.4 (EXP-008, D-013);
  5. topes de satsuma (se declaran).
- Variantes: hasta 4 (D-014). Propuesta: V1 LabeSAT y V2 sin simetrías como
  cobertura.
- **H5: mejoras definidas ≤ 25 de enero de 2027. H6: correo a los
  organizadores ≤ 1 de febrero de 2027.**
- Declaración de IA con cifras calculadas desde git
  (`scripts/declaracion_ia.sh`, en CI).

Las secciones de fase de abajo se conservan como referencia; el calendario
vigente es el del plan.

### Fase 3b — Banco industrial de la tesis y líneas de los ganadores · desde 2026-09-24

Épica: #30 (EXP-013 #25, EXP-014 #26, EXP-015 #27, D-017 #28, D-018 #29).

- [x] Banco de la tesis integrado: 450 dev / 427 test / 871 reserva / 169
      excluidas (`bench/tesis.list.csv`), con la referencia de Kissat.
- [x] research/07: ganadores 2021–2026. **B2 retirada** (era satsuma + MAB);
      reinicios fríos a ciegas descartados por simulación.
- [x] VSA (P6) implementada detrás de `vivifyactivity`.
- [ ] EXP-013 (calibración con la tesis) → D-017.
- [ ] EXP-014 (simetrías en la industria) → datos para B3 y P5.
- [ ] EXP-015 (VSA).
- [ ] D-018: línea VSIDS/CHB, tras EXP-008.

### Fase 4 — Los 20 benchmarks obligatorios · febrero–marzo 2027

- [ ] Elegir una familia de problemas nueva. Candidata natural: los dominios del
      estudio de tesis del autor.
- [ ] Generar instancias y calibrar: ≥10 que MiniSat **no** resuelva en 1 min y
      LabeSAT **sí** en 1 h.
- [ ] Documentarlas (la competición publica una descripción por familia).

### Fase 5 — Congelar y validar · marzo 2027

- [ ] Fijar los **valores por defecto** de cada variante. Recordatorio del
      ADR-0002: el build `--competition` compila las opciones fuera, así que una
      feature validada debe ser el defecto, no una opción.
- [ ] Validación única en `bench/test` al presupuesto más largo disponible.
- [ ] Elegir el **verificador de pruebas** y comprobarlo a escala sobre todo el
      banco, no solo sobre `bench/smoke`.

### Fase 6 — Registro · abril 2027

- [ ] Hasta **4 variantes**: p. ej. base (Kissat + B3″), + A4, + simetrías, + ambas.
- [ ] Los 20 benchmarks.
- [ ] Resuelta la cuestión de la subcategoría de IA.

### Fase 7 — Envío · mayo 2027

- [ ] Empaquetado: adaptar `solver/kissat/scripts/prepare-competition.sh`, que ya
      genera la estructura de build + ejecución.
- [ ] **Descripción del sistema**: 1–2 páginas, formato IEEE, PDF. Se genera desde
      el diff contra upstream y los documentos de experimentos.

### En paralelo — artículos

- **P1** — *Configuration complementarity is an untapped resource*: la evidencia
  de `docs/research/01` + EXP-001 ya es sólida por sí sola.
- **P2** — preprocesado condicional (Fase 2).
- **Nota metodológica**: lo que el proyecto ha aprendido midiendo —la deriva del
  4 % entre sesiones que da p ≈ 0 con trayectorias idénticas (EXP-004), y la regla
  B3′ que dio −13.4 % en su banco y +2.3 % en el reservado (EXP-003)—. Es
  material que casi nadie publica.

---

## 4. El riesgo principal: el cómputo

Todo lo medido hasta ahora es a **T = 180 s en 4 núcleos**. La competición es a
**T = 5000 s**. El análisis de potencia de EXP-005 lo deja claro: decidir un
efecto de PAR-2 del tamaño que produce A4.1 costaría **~155 h de cómputo por
rama**, y eso a 180 s.

**Acceso a un clúster (p. ej. el de la universidad, vía la tesis) es la acción
individual que más cambiaría el proyecto.** Sin él, las decisiones de la Fase 5
se tomarán con presupuestos cortos y habrá que declararlo así.

## 5. Decisiones pendientes del autor

Investigadas a fondo, con hechos, opciones, recomendación y un borrador de correo
a los organizadores, en [`docs/research/04`](research/04-decisiones-pendientes.md).

1. ¿Hay acceso a un clúster? → **no** (2026-09-23): todo se mide en local.
2. Subcategoría de IA → **preguntar por escrito ya**. Caso base: subcategoría IA.
3. Composición satsuma + kissat → riesgo bajo (hay precedentes en 2025 y 2026);
   confirmarlo en el mismo correo.
4. Familia de los 20 benchmarks → recomendación: **covering arrays**.
6. **Base de Kissat (D-013)**: 4.0.4 (la del ganador de 2026) o sc2026 (sin
   publicar, MIT). Se decide con EXP-008.
7. **Variantes a presentar (D-014)**: propuesta V1 + V2, ampliable.
5. MIT frente a cliques → esperar a EXP-007. Si hay coste, reimplementar la
   clique máxima en MIT.
