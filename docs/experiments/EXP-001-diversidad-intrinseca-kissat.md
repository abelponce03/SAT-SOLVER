# EXP-001 — ¿Tiene Kissat diversidad intrínseca suficiente para una cartera?

- **Estado**: diseñado · en ejecución
- **Fecha de diseño**: 2026-09-21 (escrito **antes** de ejecutar, ADR-0003 §6)
- **Motiva**: [`docs/research/02-catalogo-de-ideas.md`](../research/02-catalogo-de-ideas.md) línea A
- **Decide**: si las ideas A1–A4 son viables o si toda la línea A se cae

---

## 1. Pregunta

Los resultados oficiales de 2026 muestran que **21 variantes de Kissat de
distintos autores** tienen un Virtual Best Solver de PAR-2 = 2354.8 s frente a
4611.5 s del mejor individual: una diferencia enorme. Más aún, las **12
variantes que quedaron peores que el Kissat de fábrica** resuelven juntas 277
instancias, más que el campeón del año (276).

Pero esas variantes son **parches de código distintos**. La pregunta que decide
si podemos explotar ese fenómeno dentro de un único binario es otra:

> **¿Aparece la misma complementariedad entre configuraciones del Kissat *de
> fábrica*, sin tocar una línea de código — solo cambiando seed y opciones?**

Si la respuesta es sí, la línea A se implementa con ~200 líneas y el techo de
−798 s de PAR-2 medido en la simulación es realista. Si es no, la línea A exige
construir diversidad de verdad (parches distintos), y su coste se multiplica.

## 2. Hipótesis falsables

- **H1 (diversidad)**: el VBS de las k configuraciones mejora el PAR-2 de la
  **mejor configuración individual** en **≥ 15 %**.
- **H2 (no es solo la seed)**: el VBS de las configuraciones con *opciones*
  distintas mejora sobre el VBS de las que solo cambian la *seed*. Si H2 falla
  pero H1 se cumple, la diversidad es pura suerte de aleatorización — que sigue
  siendo explotable, pero cambia el diseño (basta con re-lanzar con otra seed).
- **H3 (implementable)**: una cartera secuencial con reparto T/k (k = 2, 3),
  **sin oráculo**, mejora el PAR-2 de la mejor configuración individual.

**Hipótesis nula operativa**: la complementariedad es < 5 % y H3 empeora el
PAR-2. En ese caso la línea A se abandona y se pasa a la línea B (preprocesado
condicional).

## 3. Diseño

| elemento | valor |
|---|---|
| Solver | `solver/kissat/build/kissat` 4.0.4, commit del repo en el `meta.json` |
| Banco | 89 instancias de aplicación reales descargadas de GBD (familias: hardware-verification, cryptography, bitvector, argumentation, scheduling, software-verification…) |
| Presupuesto | 30 s de límite interno (`--time`) por corrida |
| Configuraciones | 7 (abajo) |
| Corridas | 7 × 89 = 623 |
| Paralelismo | `--jobs 3` → **cribado**, no medición final (ADR-0003 §4); el CSV lleva `parallel_jobs=3` |

### Configuraciones (los "brazos")

| id | opciones | qué diversifica |
|---|---|---|
| `c0-default-s1` | `--seed=1` | referencia |
| `c1-default-s2` | `--seed=2` | **solo la aleatorización** (contraste de H2) |
| `c2-sat` | `--sat` (`--target=2 --restartint=50`) | sesgo hacia satisfacibles: reinicios cortos, fases objetivo |
| `c3-unsat` | `--unsat` | sesgo hacia insatisfacibles |
| `c4-focused` | `--stable=0` | solo modo *focused* (sin alternancia) |
| `c5-stable` | `--stable=2` | solo modo *stable* |
| `c6-plain` | `--plain` | CDCL sin técnicas avanzadas (inprocesado apagado) |

`c4`/`c5` rompen la alternancia `stable`/`focused` que Kissat hace por defecto:
son el caso interesante, porque miden si esa alternancia interna **ya está
capturando** la diversidad o si deja margen.

### Métricas

1. PAR-2 de cada configuración por separado (`par2.py`).
2. **VBS** del conjunto y de subconjuntos (`analyze_diversity.py`).
3. **Cartera secuencial simulada** con T/k para k = 2, 3, construcción voraz.
4. Matriz de complementariedad: para cada par, cuántas instancias resuelve una y
   no la otra.

### Criterio de decisión

| resultado | decisión |
|---|---|
| H1 ✅ y H3 ✅ | seguir con A1 (implementar cartera) y diseñar EXP-002 como A/B real |
| H1 ✅ y H3 ❌ | la diversidad existe pero el reparto ciego no la cobra → ir directo a A4 (reparto adaptativo), que es la contribución interesante |
| H1 ❌ | abandonar la línea A tal cual; pasar a la línea B, y reconsiderar A solo con parches que generen diversidad real |
| H2 ❌ (solo importa la seed) | la cartera se construye con seeds, no con opciones: más simple y más barata |

## 4. Limitaciones conocidas (escritas antes de ver los resultados)

- **T = 30 s, no 5000 s.** El régimen de tiempo corto favorece a las
  configuraciones agresivas y penaliza el inprocesado, que amortiza tarde. La
  conclusión sobre *existencia* de diversidad sí traslada; la de *cuál* es la
  mejor cartera, no. Hay que reconfirmar a T alto antes de decidir la cartera
  definitiva.
- **89 instancias**, seleccionadas en la etapa anterior por su comportamiento
  *en CaDiCaL* (62 marcadas como inestables + 27 de control). Eso sesga el banco
  hacia instancias al borde de lo resoluble, que es precisamente donde una
  cartera ayuda más → el efecto medido aquí será **optimista**. La validación
  final va contra `bench/test`, construido desde el banco oficial de 2026.
- **`--jobs 3`**: los tiempos están contaminados por contención. La
  clasificación resuelve/no-resuelve es robusta; el PAR-2 absoluto, no. Todas
  las configuraciones sufren la misma contención, así que la **comparación
  entre ellas** sigue siendo informativa.
- **Una seed por configuración** (salvo el par c0/c1). No separa el efecto de la
  opción del efecto de la aleatorización salvo en ese contraste concreto.

## 5. Reproducir

```bash
./scripts/build.sh
python3 scripts/fetch_gbd.py --list docs/archive/cadical-era/results/phase1_download_list.csv \
        --out bench/downloaded/gbd
./scripts/run_diversity.sh              # lanza las 7 configuraciones
python3 scripts/analyze_diversity.py results/exp001/*.csv
```

## 6. Resultados

<!-- se rellena al terminar; si contradice la hipótesis, se escribe igual -->

_Pendiente de ejecución._

## 7. Conclusión

_Pendiente._
