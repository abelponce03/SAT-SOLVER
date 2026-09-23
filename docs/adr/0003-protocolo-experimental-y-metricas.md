# ADR-0003 — Protocolo experimental: métricas, validez estadística y anti-overfitting

- **Estado**: aceptado
- **Fecha**: 2026-09-21
- **Decide**: Abel Ponce

## Contexto

El objetivo del proyecto es una mejora **demostrable** en PAR-2 sobre la Main
Track. Sin un protocolo fijado de antemano, cualquier idea "mejora" si se mide
en el banco correcto con la seed correcta: la literatura de SAT está llena de
mejoras que no replican. Además el hardware disponible (4 núcleos, 15 GB) es
~3 órdenes de magnitud menor que el de la competición (~5000 s × 400 instancias
× muchos nodos), así que el protocolo debe estar *escalado* y ser honesto sobre
lo que puede y no puede concluir.

## Decisión

### 1. Métricas

- **Primaria — PAR-2** (la de ranking oficial): por instancia, `t` si resuelve
  dentro del timeout `T`, `2T` si no. Se reporta la media sobre el banco.
- **Secundaria — nº resueltas** (y desglose SAT/UNSAT, que se ranquean aparte
  en la competición).
- **Terciaria — robustez** (aportación propia, ver ADR-0001 §Riesgos):
  - `flaky → resuelta`: instancias que con la base se resuelven en unas seeds y
    no en otras, y que pasan a resolverse en todas;
  - `p90 del ratio max/min de tiempo entre seeds` (medida de varianza de búsqueda).
- **Diagnóstica — esfuerzo determinista**: conflictos y propagaciones hasta la
  solución. Con `--conflicts=<n>` y una seed fija, Kissat es determinista; esta
  métrica **no depende del ruido de la máquina** y permite detectar mejoras
  reales con presupuesto de cómputo pequeño.

### 2. Bancos de prueba y disciplina dev/test

Tres bancos **disjuntos**, fijados antes de cualquier experimento:

| banco | origen | uso | ¿se puede mirar? |
|---|---|---|---|
| `bench/smoke` | muestra sintética versionada | CI, no-regresión funcional | siempre |
| `bench/dev` | muestra estratificada de instancias reales (GBD / SAT Comp) | desarrollo, tuning, exploración | sí |
| `bench/test` | muestra disjunta de las mismas familias + años de competición distintos | **solo** validación final de una idea ya congelada | una vez por idea |

Ningún hiperparámetro se ajusta mirando `bench/test`. Cada idea que llegue a
validación final reporta sus números en `bench/test` y ese número es el que
entra en la documentación del artículo.

### 3. Validez estadística

Una comparación A/B se considera concluyente solo si:

1. **Emparejada por instancia y por seed**: A y B corren la misma instancia con
   la misma seed, en la misma máquina, secuencialmente (nunca en paralelo, para
   no contaminar por contención de memoria/caché).
2. **≥ 3 seeds por instancia** (la varianza por seed llega a 102× en nuestros
   datos, `docs/archive/cadical-era/03-fase0-datos-tesis.md` §3). El estadístico
   se calcula sobre el agregado por instancia (mediana de seeds) y, por
   separado, sobre todas las corridas.
3. **Test de Wilcoxon de rangos con signo** sobre el PAR-2 emparejado
   (no normal, con censura en `2T`), más **bootstrap** (10 000 remuestreos) del
   intervalo de confianza del ΔPAR-2. Se reporta el IC, no solo el p-valor.
4. **McNemar** sobre el cambio en el conjunto de instancias resueltas
   (resuelve→no resuelve vs no resuelve→resuelve).
5. **Tamaño de efecto** siempre: ΔPAR-2 absoluto y relativo, y Δresueltas.
6. **Se reporta la potencia**: con `n` instancias y el timeout usado, qué
   tamaño de efecto era detectable. Un "no significativo" con n=30 no es
   evidencia de ausencia de efecto y se dirá así.

### 4. Control del ruido de medición

- Tiempo de **CPU** del proceso (no wall) como medida primaria de coste;
  wall-clock se registra en paralelo para detectar interferencias.
- Una corrida a la vez; `taskset` a un núcleo fijo cuando se mida tiempo.
- Cada experimento registra: commit del solver, opciones exactas, versión del
  compilador, `nproc`, carga de la máquina, y hash de cada instancia.
- Toda corrida escribe CSV en `results/` con esas columnas; los CSV de
  referencia se versionan.

### 4b. Comparaciones entre sesiones (añadido tras EXP-004)

Comparar una tanda nueva contra corridas **de otra sesión** mide también la
deriva de la máquina. Medida en EXP-004: **~4 %** entre dos sesiones separadas
31 horas, con trayectorias de búsqueda **idénticas** (39/39 instancias con el
mismo recuento de conflictos) y aun así Wilcoxon p ≈ 0.

Reglas:

1. **Preferir siempre** las dos ramas en la misma sesión y con el mismo binario
   (feature detrás de una opción, ADR-0002 §3). Es lo que hacen EXP-003 y EXP-005.
2. Si la comparación entre sesiones es inevitable (p. ej. un parche que no se
   puede poner detrás de una opción), **comprobar primero si las trayectorias
   coinciden** (recuento de conflictos con la misma semilla). Si coinciden, la
   diferencia de tiempo es de la máquina y no se interpreta.
3. Ninguna diferencia de tiempo **por debajo del 4 %** entre sesiones distintas
   se reporta como efecto.

### 5. Escalado del timeout

La competición usa `T = 5000 s`. Localmente se usa `T ∈ {60, 300, 900} s` según
la fase. **Consecuencia explícita**: un PAR-2 medido a `T = 300 s` no es
comparable con el oficial y se etiqueta siempre con su `T`. Las ideas se criban
a `T` bajo y solo las supervivientes se validan a `T` alto.

### 6. Registro (bitácora)

Cada experimento tiene un documento en `docs/experiments/EXP-NNN-*.md` escrito
**antes** de correrlo, con: hipótesis falsable, banco, métrica, criterio de
éxito y de fracaso. Se rellenan resultados después. Un experimento cuyo
resultado contradice la hipótesis **se documenta igual** — es el registro
antiselección que hace creíble el artículo.

## Consecuencias

- Ralentiza la exploración: cada idea cuesta un documento y un A/B serio.
- A cambio, cualquier número que publiquemos es defendible y reproducible, y el
  histórico de experimentos negativos es material directo para la sección de
  "lecciones" del artículo.
- Con 4 núcleos no podremos cerrar una validación al nivel de la competición;
  el protocolo lo reconoce y usa la métrica determinista (conflictos) como
  cribado barato antes de gastar horas de wall-clock.

## Criterios de reversión

Si se consigue acceso a hardware mayor (clúster), se suben los timeouts y el
tamaño de banco; el resto del protocolo no cambia.

## Referencias

- SAT Competition rules (PAR-2, timeout 5000 s): https://satcompetition.github.io/
- Kissat soporta `--time`, `--conflicts`, `--decisions` y `--seed` → base del cribado determinista.
