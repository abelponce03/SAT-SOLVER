# EXP-018 — K1: precarga de cláusulas en la propagación (clase E, preregistrado)

- **Estado**: **preregistrado**. Se commitea antes de ejecutar, junto con la
  implementación (`proplit.h`, detrás de `LABESAT_PREFETCH`), la opción
  `--prefetch[=d]` del `configure` de Kissat y `scripts/exp018.py`.
  - Única ejecución previa: la comprobación de equivalencia del ADR-0009,
    con la primera instancia de 6 familias de `bench/calib2` y 20 000
    conflictos. En las 5 que terminaron, los 81 contadores de
    `--statistics`, incluidos `search_ticks`, salieron idénticos al binario
    actual. La sexta (`baseball-lineup`) no llegó a compararse: superó el
    tope de 15 min que se puso a toda la comprobación.
  - No se midió tiempo.
- **Fecha**: 2026-10-01
- **Decide**: si LabeSAT se compila con `--prefetch=8` (research/08 §6.2,
  K1).

---

## 1. Qué se quiere saber

- La propagación de Kissat ya es óptima en número de operaciones
  (research/08, Teorema 4).
- Lo que queda es la latencia de memoria. Cada vigilante grande cuyo literal
  bloqueante no es verdadero obliga a leer la cláusula, y en instancias
  grandes esa lectura suele fallar en caché.
- K1 adelanta esas lecturas: un puntero recorre la lista 8 vigilantes por
  delante y precarga (`__builtin_prefetch`) la cabecera de cada cláusula que
  probablemente se va a visitar.
- Por el **Corolario 4** de research/08, K1 no cambia la búsqueda:
  - solo añade lecturas y precargas;
  - no escribe en ningún objeto;
  - no toca los `ticks` ni el orden de las listas.
- Evidencia previa: Manthey y Saptawijaya (2010) midieron +12 % con el
  mismo esquema en un resolvedor **sin** literal bloqueante. Kissat lo tiene,
  así que aquí se espera menos.

## 2. Hipótesis

> **H0 (equivalencia, vinculante).** Con el presupuesto de conflictos de §3
> y la semilla 1, `build-k1` da, en las 85 instancias del banco, el **mismo
> estado y los mismos conflictos, decisiones y propagaciones** que
> `build-base18`.
>
> **H1 (velocidad).** La aceleración geométrica de `build-k1` frente a
> `build-base18` (tiempo de CPU para el mismo trabajo) tiene el extremo
> inferior del IC95 % **> 1**.

**Predicción honesta**:

- H0 se cumple (lo exige el Corolario 4).
- Para H1, entre 0 y +5 %, con más ganancia en las instancias grandes, cuya
  *arena* no cabe en la caché.
- Puede salir < 1 en las pequeñas, en las que la precarga solo cuesta
  instrucciones.

## 3. Diseño

- **Binarios**: los dos se compilan desde el commit de este preregistro, en
  el paso `exp018-construir` de la cola:

  | binario | `build.sh` |
  |---|---|
  | `build-base18` | `--dir=build-base18` (`-O3`) |
  | `build-k1` | `--dir=build-k1 --prefetch=8` |

- **Banco**: el de EXP-017, `results/exp017/banco.txt` (85 instancias, 40
  de 2026 y 47 industriales, 2 en los dos).
- **Presupuesto**: **200 000 conflictos**, semilla 1. Es el doble que en
  EXP-017 a propósito: la ganancia de K1 depende del tamaño de la *arena*, y
  con poco presupuesto se subestimaría. No se sube más porque:
  - en las instancias grandes la *arena* la dominan las cláusulas
    originales, que ya están desde el principio;
  - las instancias más lentas de la muestra de EXP-016 van a ~900
    conflictos/s, y 500 000 conflictos costarían ~10 min por corrida.
- **Corridas**: A/B intercalado (`run_ab_interleaved.py --conflicts 200000
  --seeds 1`), con salida en `results/exp018/k1_{A,B}.csv`.
- **Métrica y análisis**: los de EXP-017, con su mismo código
  (`exp018.py` llama a `exp017.analizar`):
  - s_i = cpu_A / cpu_B;
  - media geométrica, IC95 % por bootstrap y Wilcoxon sobre log s_i;
  - se excluyen las parejas con cpu_A < 1 s, y se informa de cuántas son.
- **Descriptivo, sin umbral**: la aceleración por grupo (industria / 2026).
- **Cuándo**: en la cola, después de EXP-017 y antes de reanudar EXP-009.
  Coste estimado: 170 corridas de 10–220 s, unas 2–3 h.

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| H0 y H1 | `build.sh` compila con `--prefetch=8` por defecto, en los experimentos siguientes y en el paquete de competición. Valor en PAR-2 por la Proposición 1 |
| H0 sí, H1 no | Equivalente, pero sin ganancia medible: no se adopta |
| H0 falla | **No se adopta.** Contradice el Corolario 4, así que hay comportamiento indefinido o un error en la implementación: se investiga antes de nada |

Si EXP-017 adopta PGO/LTO, la combinación final (PGO+LTO+K1) se comprueba
con la igualdad de contadores del ADR-0009 antes de usarla. No hace falta un
A/B de tiempo nuevo si cada parte ya ganó por separado; si se quiere el
valor combinado, se mide aparte.

## 5. Amenazas a la validez

- **Distancia fija (8)**, elegida a priori por la cuenta latencia de DRAM /
  coste por vigilante (~100 ns / ~10 ns), sin ajustar. Otras distancias
  serían exploratorias.
- **Portátil**: frecuencia variable; el intercalado reparte la deriva.
- **La precarga compite por la caché**: en instancias pequeñas puede costar.
  Se informa por grupo.
- **Carga ajena**: servicios Docker del director.

## 6. Incidencias de ejecución

- **2026-10-01, commit posterior al preregistro.** La cola compiló
  `build-base18` y `build-k1` desde `ae7457e`, que ya incluye X1
  (research/09). X1 está detrás de `LABESAT_GAUSS`, que estos binarios no
  definen.
  - Se comprobó, con los 94 objetos de Kissat compilados sin la macro, que
    son idénticos byte a byte (`objdump -s`) a los de antes de X1, salvo
    `build.o`. Ver el commit de X1.
  - Lo único que cambia frente al preregistro son ficheros de documentación
    y guiones que no entran en el binario.

## 7. Resultados

(pendiente)
