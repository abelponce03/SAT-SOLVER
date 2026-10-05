# EXP-027 — La configuración `--sat` de Kissat cuando hay ruptura (preregistrado)

- **Estado**: **preregistrado**. Usa las mismas listas que EXP-026
  (`results/exp026/`). Ninguna ejecución previa: no necesita código nuevo.
- **Fecha**: 2026-10-05
- **Vía**: M7 (research/12 §3).
- **Decide**: si `labesat` usa `--sat` cuando satsuma se aplica, como
  candidata para V1 o para una variante (D-014, D-020).

---

## 1. Qué se quiere saber

- El hueco SAT de LabeSAT frente al top-10 de 2026 está en ~20 instancias
  combinatorias simétricas, que resuelven casi solo las variantes MAB
  (research/10 §4).
- Kissat trae la configuración `--sat` (`--target=2 --restartint=50`): fases
  objetivo también en modo enfocado y reinicios más frecuentes.
- Cuando satsuma rompe simetría, las UNSAT combinatorias caen pronto (EXP-007:
  H, de 8 a 37 de 45).

¿Recupera `--sat` las SAT con ruptura sin perder esas UNSAT?

## 2. Hipótesis

Las mismas que EXP-026, con:

- A = `labesat --symmetry`;
- B = `labesat --symmetry --sat`.

> **H1 (primaria, etapa 2a)**: ΔPAR-2 < 0 en 2025 con ruptura (Wilcoxon
> p < 0,05, IC95 % < 0).
>
> **H2 (no daño, etapa 2b)**: extremo superior del IC95 % ≤ +5 s en la
> industria con ruptura.
>
> **H3 (exploratoria)**: «solo B resuelve» > «solo A resuelve» entre las SAT,
> y lo contrario entre las UNSAT.

**Predicción honesta**: gana algunas SAT y pierde algo en UNSAT grandes.
El signo del total depende de la mezcla; en 2025, con más SAT industriales,
puede salir a favor. H2 es la más dudosa: `--sat` no se pensó para la
industria UNSAT.

## 3. Diseño

Igual que EXP-026 §3, con `--opts-b="--symmetry --sat"`, etiqueta
`B-siempre-sat` y salidas en `results/exp027/` (`A1/B1`, `A2a/B2a`,
`A2b/B2b`). Las listas son las de `results/exp026/`.

```bash
python3 scripts/run_ab_interleaved.py --solver solver/labesat --bench bench/symm2026 \
    --instances results/exp026/simetricas.txt \
    --out-a results/exp027/A1.csv --out-b results/exp027/B1.csv \
    --label-a A-siempre --label-b B-siempre-sat \
    --opts-a=--symmetry --opts-b="--symmetry --sat" \
    --env-a "LABESAT_KISSAT=$PWD/solver/kissat/build-m/kissat" \
    --env-b "LABESAT_KISSAT=$PWD/solver/kissat/build-m/kissat" \
    --guard solver/kissat/build-m/kissat --guard tools/satsuma-mclique \
    --timeout 300 --seeds 42 --mem-gb 6
python3 scripts/research12.py cribado results/exp027/A1.csv results/exp027/B1.csv \
    > results/exp027/cribado.txt
```

- **Coste**: como EXP-026.
- **Rama A**: es la misma configuración que la rama A de EXP-026. **No se
  reutiliza**: cada A/B mide su rama A intercalada con su B (ADR-0003 §4b).

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| No pasa el cribado | Se cierra sin señal |
| H1 y H2 | Candidata para V1 (`--sat` cuando satsuma se aplica); se valida en H8 |
| H1 sí, H2 no | Candidata para una **variante** (D-014) o para B4 con la regla R: solo en lo combinatorio |
| H1 no | Se cierra; H3 se informa |

## 5. Amenazas a la validez

- Las de EXP-026 §5.
- Si EXP-026 y EXP-027 pasan las dos, su combinación (`--phase=0 --sat`) no
  está medida. Se preregistraría aparte; no se suma a ojo.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
