# EXP-009 — B3: ruptura de simetrías con retraso (preregistrado)

- **Estado**: **preregistrado**. Se commitea **antes** de ejecutar, junto con
  la implementación (`solver/labesat --symmetry-delay`), sus pruebas
  (`scripts/test_symmetry.sh`) y la selección y el análisis
  (`scripts/exp009.py`, `results/exp009/*.txt`, `grupos.csv`).
- **Fecha**: 2026-09-30
- **Decide**: si `labesat` activa la ruptura de simetrías **por defecto**,
  con retraso, como candidata a V1 (P2 del plan; issue #15).
- **Número**: EXP-009 estaba reservado para B3 desde el 2026-09-23.

---

## 1. Qué se quiere saber

La ruptura de simetrías tiene dos efectos opuestos:

- **EXP-007** (banco de 2026): gana mucho donde hay simetría explotable,
  con PAR-2 de 209,6 s sin ruptura frente a 69,3 s con ella.
- **EXP-014** (industria): cuesta tiempo. El daño es casi todo **coste fijo**
  de satsuma en instancias que kissat resuelve en segundos (factor 6,9× si A
  tarda < 10 s, 0,97× si tarda ≥ 10 s).

Una política sencilla separa los dos efectos. **Ruptura con retraso**:
kissat corre X segundos sobre la CNF original y, solo si no resuelve, se
aplica satsuma y se sigue sobre la fórmula con predicados (la fase 1 se
descarta, incluida su prueba).

**De dónde sale X = 2 s (análisis exploratorio, EXP-014 §8.3)**: se simuló
la política con los tiempos ya medidos de EXP-007 y EXP-014.

| PAR-2 | nunca | siempre | retraso 1 s | **retraso 2 s** | retraso 5 s | oráculo |
|---|---:|---:|---:|---:|---:|---:|
| EXP-007 (T = 180 s) | 209,6 | 69,3 | 69,5 | **70,4** | 72,8 | 57,2 |
| EXP-014, S (T = 300 s) | 156,5 | 159,4 | 154,4 | **154,1** | 154,3 | 150,4 |

X se eligió **mirando esos datos**, así que la mejora simulada es optimista.
Este experimento la mide en instancias en las que nunca se ha medido ninguna
política.

## 2. Hipótesis

> **H1 (principal).** En las instancias frescas de tesis-dev, la ruptura con
> retraso de 2 s (B) tiene **menor PAR-2** que no romper simetrías (A, el
> defecto actual): ΔPAR-2 < 0, IC95 % bootstrap entero por debajo de 0 y
> Wilcoxon p < 0,05.
>
> **H2 (secundaria, coste de la espera).** En las 74 instancias de EXP-007,
> la ruptura con retraso (B) cuesta poco frente a romper siempre (A): extremo
> superior del IC95 % de ΔPAR-2 **≤ +5 s**.

**Predicción honesta**: H2 se cumple casi seguro (la espera es, como mucho,
2 s más el coste de repetir la lectura). H1 es incierta: en la simulación, la
ventaja frente a «nunca» en la industria es de ~2,4 s sobre 156, una
diferencia del tamaño del ruido de una sola semilla.

## 3. Diseño

### Selección (`python3 scripts/exp009.py seleccionar`, ya ejecutada y commiteada)

- **Principal** (153 instancias de tesis-dev, `results/exp009/principal.txt`):
  - **S fresco**: las 113 en las que satsuma añade ruptura (EXP-014 parte 1)
    que **no** entraron en el A/B de EXP-014;
  - **no-S**: 40 en las que satsuma no añade ruptura, por orden de
    `md5(hash + sal)`, fuera de los controles de EXP-014. Miden el coste del
    retraso donde la ruptura no aporta nada.
- **Secundario** (74, `results/exp009/secundario.txt`): el banco efectivo de
  EXP-007.

### Corridas (pasos `exp009-principal` y `exp009-secundario` de `scripts/cola.toml`)

```bash
# principal: A = nunca, B = retraso 2 s
python3 scripts/run_ab_interleaved.py --solver solver/labesat \
    --bench bench/tesis-dev --instances results/exp009/principal.txt \
    --out-a results/exp009/P_A.csv --out-b results/exp009/P_B.csv \
    --label-a A-nunca --label-b B-retraso2 \
    --opts-a=--no-symmetry --opts-b="--symmetry --symmetry-delay=2" \
    --guard solver/kissat/build/kissat --guard tools/satsuma-mclique \
    --timeout 300 --seeds 42
# secundario: A = siempre, B = retraso 2 s
python3 scripts/run_ab_interleaved.py --solver solver/labesat \
    --bench bench/symm2026 --instances results/exp009/secundario.txt \
    --out-a results/exp009/S_A.csv --out-b results/exp009/S_B.csv \
    --label-a A-siempre --label-b B-retraso2 \
    --opts-a=--symmetry --opts-b="--symmetry --symmetry-delay=2" \
    --guard solver/kissat/build/kissat --guard tools/satsuma-mclique \
    --timeout 180 --seeds 1
python3 scripts/exp009.py analizar
```

- **satsuma**: el de `labesat` por defecto desde EXP-011
  (`tools/satsuma-mclique`), el mismo en las dos ramas.
- **T y semillas**: las de los experimentos que dieron los datos de la
  simulación (300 s y semilla 42 en la industria; 180 s y semilla 1 en
  EXP-007).
- **Coste**: ≤ 153 × 2 × 300 s + 74 × 2 × 180 s ≈ 33 h en el peor caso; se
  esperan ~10 h. Lo ejecuta la cola (ADR-0008), un paso a la vez.

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| H1 y H2 se cumplen | **Activar** `--symmetry` con retraso de 2 s **por defecto** en `labesat` (candidata a V1). Antes de entregarla: validación única en `tesis-test` y `bench/test` (H8) y paso al binario integrado (ADR-0007) |
| H2 sí, H1 no (sin diferencia frente a «nunca») | No se activa por defecto. La ruptura con retraso queda como **variante** (D-014): no daña en la industria y conserva la ganancia en lo simétrico |
| H2 no | La espera cuesta más de lo previsto: se estudia por qué antes de seguir |
| B empeora frente a A con p < 0,05 en el principal | Se descarta el retraso de 2 s y se documenta |

## 5. Amenazas a la validez

- **X elegido con los datos de EXP-007 y EXP-014.** Por eso H1 se contrasta
  solo con instancias frescas. H2 reutiliza el banco de EXP-007: mide el
  coste mecánico de la espera, no la elección de X.
- **Implementación en el guion, no en el binario.** El binario integrado es
  equivalente a la tubería (EXP-012), pero no tiene retraso. Si se adopta, hay
  que portarlo y comprobar la equivalencia.
- **Una semilla** por instancia, por coste (como EXP-007 y EXP-014). Se
  declara.
- **Doble lectura.** Con retraso, la CNF se lee dos veces (fase 1 y satsuma).
  En instancias grandes, ese coste entra en B, como entraría en la competición.
- **Carga ajena**: servicios Docker del director corriendo a la vez. El orden
  intercalado reparte el ruido.

## 6. Incidencias de ejecución

(vacío)

## 7. Resultados

(pendiente)
