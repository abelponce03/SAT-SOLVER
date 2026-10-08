# EXP-020 — ¿Subir el tope de tiempo de satsuma de 60 s a 300 s? (P5, preregistrado)

- **Estado**: **cerrado (2026-10-03): se mantiene el tope de 60 s.** El de
  300 s resuelve las mismas (9 de 13) con más PAR-2 (+24,6 s); resultados en
  §7. Se commiteó antes de ejecutar, junto con `scripts/exp020.py` y
  `results/exp020/candidatas.txt`. No hubo ejecuciones previas.
- **Fecha**: 2026-10-01
- **Decide**: el tope de tiempo de satsuma en `labesat`
  (`LABESAT_SYMM_TIMEOUT`, hoy 60 s) para los experimentos siguientes y el
  paquete de competición (P5 del plan; research/10 §5, acción 4).

---

## 1. Qué se quiere saber

research/10 §2.2 identificó el tope de 60 s como **la incertidumbre más
grande** del análisis frente a los ganadores de 2026.

- El ganador no pone tope.
- De las 51 instancias de 2026 que él resuelve y Kissat solo no, 11 le
  llevan más de 60 s, y no podemos medirlas: 10 no están en disco.
- Si en alguna satsuma necesitara más de 60 s, `labesat` caería a Kissat sin
  simetrías y la perdería. La cota del daño es de hasta +270 s de PAR-2.

Subir el tope tampoco es gratis. Donde satsuma no termina ni con el tope
nuevo, se pierden 240 s más antes de caer a Kissat.

**Por qué basta con las instancias en las que el tope se alcanza.** Si
satsuma termina en menos de 60 s, `labesat` hace exactamente lo mismo con
los dos topes: el tope no se toca y el comando es idéntico. El efecto del
cambio está entero en las instancias en las que satsuma agota los 60 s. Esas
son las candidatas.

## 2. Hipótesis (descriptivas; la decisión es la regla de §4)

> **Q1 (fase 1).** ¿En cuántas candidatas termina satsuma con un tope de
> 300 s, en cuánto tiempo y cambiando cuántas cláusulas?
>
> **Q2 (fase 2).** Con `labesat` (B3, retraso de 2 s) y T = 1200 s,
> ¿cuántas resuelve y qué PAR-2 da cada tope?

**Predicción honesta**:

- En la industria, satsuma rara vez rompe algo útil cuando tarda tanto
  (EXP-014: la ruptura cuesta tiempo fijo).
- En las 3 del banco simétrico, Kissat solo resuelve en 1–4 s
  (research/10 §2.2). Con B3, 2 de ellas ni llegan a satsuma.
- **Se espera que subir el tope no gane nada y cueste algo.** Si es así, el
  riesgo de §1 se queda sin cubrir con los datos locales y se declara como
  tal.

## 3. Diseño

- **Candidatas** (`exp020.py seleccionar`, `results/exp020/candidatas.txt`,
  13 instancias):
  - las 10 de `tesis-dev` en las que satsuma agotó los 60 s en EXP-014
    parte 1;
  - las 3 de `symm2026` en las que satsuma con mclique v2 los agotó en
    EXP-011.

  Se enlazan en `bench/exp020/`, que no se versiona.
- **Fase 1** (paso `exp020-satsuma`):

  ```bash
  python3 scripts/compare_satsuma_builds.py --bench bench/exp020 \
      --build mclique2=tools/satsuma-mclique --timeout 300 \
      --out results/exp020/satsuma300.csv --resume
  ```

- **Fase 2** (paso `exp020-ab`): A/B intercalado sobre las 13. Se incluyen
  también las que no terminan ni con 300 s, porque ahí está el coste.

  ```bash
  python3 scripts/run_ab_interleaved.py --solver solver/labesat \
      --bench bench/exp020 --instances results/exp020/candidatas.txt \
      --out-a results/exp020/A.csv --out-b results/exp020/B.csv \
      --label-a A-tope60 --label-b B-tope300 \
      --opts-a="--symmetry --symmetry-delay=2" --opts-b="--symmetry --symmetry-delay=2" \
      --env-a LABESAT_SYMM_TIMEOUT=60 --env-b LABESAT_SYMM_TIMEOUT=300 \
      --guard solver/kissat/build/kissat --guard tools/satsuma-mclique \
      --timeout 1200 --seeds 42
  python3 scripts/exp020.py analizar
  ```

- **T = 1200 s.** Con T = 300 s, como en EXP-009, el tope de 300 s se
  comería todo el presupuesto. 1200 s deja 900 s a Kissat después de
  satsuma, lo más cerca de los 5000 s de la competición que permite el
  cómputo local.
- **B3 en las dos ramas**: es la configuración candidata (EXP-009). El tope
  es una pregunta ortogonal al retraso.
- **Cuándo**: en la cola, después de EXP-009. Coste ≤ 13 × 300 s (fase 1)
  + 13 × 2 × 1200 s (fase 2) ≈ 9,7 h en el peor caso.

## 4. Criterio de decisión

Fuera de las candidatas, los dos topes se comportan igual (§1), así que el
efecto total es exactamente el de las candidatas. Con n = 13 no se busca
significación estadística: la regla es de dominancia.

| resultado | decisión |
|---|---|
| El tope de 300 s resuelve **al menos tantas** y su PAR-2 total sobre las candidatas es **≤** | Subir el tope a 300 s |
| Resuelve menos, o su PAR-2 es mayor | Mantener 60 s |

**En los dos casos** se informa:

- cuántas candidatas terminan entre 60 y 300 s (fase 1);
- que el riesgo de las 11 instancias de 2026 no medibles sigue abierto. Se
  declara en la descripción para la competición.

## 5. Amenazas a la validez

- **n = 13** y una semilla: la decisión es de dominancia, no estadística.
- **T = 1200 s frente a 5000 s**: el coste relativo de esperar a satsuma es
  mayor aquí que en la competición, lo que favorece mantener 60 s. Si la
  fase 1 muestra que satsuma termina entre 60 y 300 s y la ruptura ayuda, se
  reconsidera con esa salvedad.
- **Las candidatas salen de los bancos locales**; las 11 de 2026 que
  motivaron la pregunta no están. Por eso el experimento acota el riesgo,
  pero no lo cierra.
- **El tope de memoria** (512 MiB, 2 instancias «GRANDE» en EXP-014) queda
  fuera.

## 6. Incidencias de ejecución

- **Apagado de la máquina a mitad de la fase 2** (2026-10-03, de 14:02 a
  14:50 hora local). El servicio retomó la tanda en la misma máquina con
  `--resume` (ADR-0008): conservó las 4 parejas completas y descartó la fila
  A a medias de `3728eb69`, que se repitió entera. Las ramas siguen
  intercaladas, así que no hay sesgo entre A y B.
- **satsuma muere en 6 de las 13 de la fase 1**, todas de más de 7,8
  millones de cláusulas, con el tope de 6 GB de `compare_satsuma_builds.py`:
  - 5 abortan (`std::bad_alloc`, salida −6);
  - 1 se cae con SIGSEGV (`b3233e00`, 15 millones de cláusulas, salida −11).

  En `labesat` no hay respuesta errónea: si satsuma sale con cualquier
  código distinto de 0 (tiempo, memoria o señal), se cae a Kissat solo
  (`run_plain`). Solo se pierde el tiempo hasta la caída. El SIGSEGV queda
  anotado como fallo de robustez de satsuma cuando se queda sin memoria.

## 7. Resultados

Informe: `results/exp020/informe.md` (`exp020.py analizar`).

**Fase 1 (Q1)**: satsuma solo, con tope de 300 s:

| Resultado | Instancias | Detalle |
|---|---|---|
| Termina entre 60 y 300 s | **5** | 66, 125, 165, 179 y 201 s |
| Agota los 300 s | 2 | 10 y 25 millones de cláusulas |
| Muere por memoria (6 GB) | 6 | §6 |

En las 5 que terminan, la ruptura apenas cambia la fórmula:

- de −2 % a −6 % de cláusulas en tres de ellas;
- +0,1 % en `bc198d71`;
- −33 % en `8db998d5`, que Kissat resuelve igual en 1 s.

**Fase 2 (Q2)**: `labesat` con B3, T = 1200 s, n = 13:

| | Tope 60 s | Tope 300 s |
|---|---|---|
| Resueltas | 9 | 9 |
| PAR-2 medio | 826,1 | 850,6 |

- Las dos resuelven las mismas 9.
- El coste del tope alto se ve en `80bb5209`: con 60 s, satsuma se corta y
  Kissat resuelve en 69 s; con 300 s, se esperan los 300 s y tarda 309 s.
  En `8bb5819a`, satsuma termina a los 165 s, y aun así B tarda más que A
  (142 frente a 91 s).
- En ninguna candidata la ruptura que llega tarde resuelve algo que el tope
  de 60 s no resolviera.

**Decisión (§4)**: **se mantiene el tope de 60 s**. El de 300 s resuelve
las mismas y su PAR-2 es mayor (+24,6 s de media).

Lo que §4 manda informar:

- **5 de las 13 candidatas terminan entre 60 y 300 s**, y en ninguna eso da
  una instancia más.
- **El riesgo de research/10 §2.2 sigue abierto.** Son las 11 instancias de
  2026 en las que el ganador tarda más de 60 s y que no tenemos en disco.
  Los datos locales apuntan a que el tope no las perdería (aquí, la ruptura
  tardía no aporta), pero no lo prueban. Se declara en la descripción para
  la competición.
- **Nota de diseño**: la fase 2 usó B3, que EXP-009 descartó después. La
  pregunta del tope es ortogonal al retraso (§3), y con «siempre» el coste
  de esperar a satsuma sería el mismo.
