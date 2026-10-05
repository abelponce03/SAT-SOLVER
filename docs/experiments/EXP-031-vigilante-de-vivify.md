# EXP-031 — El vigilante de `vivify`: diagnóstico y, si procede, A/B (preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con:
  - la opción `--vivifywatchfix` (apagada);
  - la estadística `vivify_watch_mismatch` (solo con `--stats`);
  - `scripts/exp031.py`.
- **Ejecuciones previas**:
  - de corrección (research/12 §11);
  - el diagnóstico en **3 instancias de calib** con XOR (`ae48df65`,
    `4f09ef86`, `8d0d8518`), a 20 000 conflictos y semilla 1, al verificar
    que la estadística funciona. Dieron 328 de 2901, 347 de 3308 y 356 de
    3144 cláusulas vivificadas con un par vigilado peor: ≈ 11 %.
    Después, en las 29 de calib y calib2 de research/12 §12: 9,5 % (4114 de
    43 514), en 19 instancias.

  No son de la muestra del preregistro (tesis-dev) y no condicionan el
  umbral, que se fijó antes de verlas.
- **Fecha**: 2026-10-05
- **Vía**: M10 (research/12 §7).
- **Decide**: si el arreglo merece un A/B y, si lo merece, si pasa a
  candidata.

---

## 1. Qué se quiere saber

- En `swap_first_literal_with_best_watch` (`vivify.c`), una sombra de
  `value` hace que la guarda del bucle no cambie. Tras un literal no falso,
  uno falso de nivel mayor puede quedarse como vigilante.
- El arreglo para en el primer literal no falso, como sugiere la guarda.
- **Antes de medir el PAR-2**, ¿con qué frecuencia la elección difiere?

## 2. Hipótesis

> **Etapa 0 (diagnóstico, determinista).** Tasa = desajustes / cláusulas
> vivificadas, sumadas sobre la lista de cribado, a 100 000 conflictos.
> Un desajuste es una vivificación tras la que el par vigilado tiene
> **menos literales no falsos** de los que tendría con el arreglo (se
> simulan las dos elecciones, la búsqueda no cambia). PASA al A/B si la
> tasa es ≥ 0,1 % **y** hay desajustes en al menos 4 instancias.
>
> **Etapas 1 y 2 (si pasa)**: las de EXP-028 §2, con A = sin opción y
> B = `--vivifywatchfix=1`.

**Predicción honesta**: la etapa 0 **pasa**. Era lo contrario antes de las
ejecuciones previas: se esperaba un caso raro, y en 3 instancias de calib
sale en ≈ 10 % de las vivificaciones.

Lo que no se sabe es si importa. El vigilante falso solo estorba mientras la
vivificación siga en niveles por encima del suyo; al terminar la ronda se
vuelve al nivel 0 y el invariante se recupera. Para el A/B, la predicción
es un efecto pequeño.

## 3. Diseño

```bash
# Etapa 0: binario con --stats del mismo commit (la búsqueda es la misma)
python3 scripts/exp031.py diagnostico --kissat solver/kissat/build-m-stats/kissat \
    --lista results/research12/cribado.txt --bench bench/tesis-dev \
    --out results/exp031/diagnostico.csv --conflicts 100000
python3 scripts/exp031.py analizar results/exp031/diagnostico.csv > results/exp031/diagnostico.txt
```

- Si pasa, las etapas 1 y 2 son las de EXP-028 §3, cambiando
  `--opts-b=--vivifywatchfix=1`, la etiqueta (`B-vivifywatchfix`) y las
  salidas (`results/exp031/`).
- **Coste**: etapa 0, ~1 h (40 instancias a 100 000 conflictos).

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| La etapa 0 no pasa | Se cierra: el desajuste es demasiado raro para moverse en PAR-2. Se documenta como fallo menor de Kissat y entra en D-021 junto con el de `eliminate.c` |
| La etapa 0 pasa (lo esperado) | Etapas 1 y 2, con los criterios de EXP-028 §4. El fallo entra en D-021 con su frecuencia medida, sea cual sea el A/B |

## 5. Amenazas a la validez

- **El diagnóstico usa la búsqueda sin el arreglo**: cuenta las veces en
  que el arreglo **mejoraría** el par vigilado, no el efecto en cadena de
  cambiarlo. Es lo que se necesita para decidir si vale la pena medir.
- **Cuenta solo los pares peores**: elegir otro literal no falso, que
  también cambia la trayectoria, no cuenta como desajuste.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
