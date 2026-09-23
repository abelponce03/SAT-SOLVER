# EXP-012 — ¿Es `kissat --symmetry` equivalente a la tubería de EXP-007? (preregistrado)

- **Estado**: **preregistrado**. Se escribe **antes** de ejecutar sobre el
  banco (ADR-0003 §6). Las únicas ejecuciones previas son las pruebas de
  corrección en `bench/symm` (4 instancias de juguete, que no están en el
  banco).
- **Fecha**: 2026-09-23
- **Decide**: si el binario integrado (D-016, ADR-0007, fase 1) sustituye a la
  tubería `solver/labesat`, y si las conclusiones de EXP-007 valen para él.

---

## 1. Qué se quiere saber

La fase 1 de ADR-0007 pretende hacer **lo mismo** que la tubería, pero dentro
de un solo binario. Si es así:

- la CNF que recibe Kissat es idéntica;
- con la misma semilla y el mismo presupuesto determinista, la búsqueda sigue
  la **misma trayectoria**.

Entonces los resultados de EXP-007 (H: 8 → 37 de 45; N: 1,42×) valen tal cual
para el binario integrado, sin repetir el A/B de tiempos.

**Posible fuente de diferencias, anotada antes de medir**:
- `tools/satsuma` se compila con `-march=native`, como en el CMake de satsuma;
- el integrado no, por portabilidad.

Si satsuma usa aritmética en coma flotante en alguna decisión, las CNF podrían
diferir en algunas instancias.

## 2. Hipótesis

> **H1 (CNF).** En las 74 instancias de `bench/symm2026`, la CNF intermedia
> del binario integrado es idéntica byte a byte a la de `tools/satsuma` con los
> mismos argumentos. Cuenta como igual que los dos caigan al respaldo.
>
> **H2 (trayectoria).** Con `--conflicts=100000 --seed=1`, el binario integrado
> y el kissat de la tubería dan el mismo estado y el mismo número de
> conflictos, decisiones y propagaciones.
>
> **H3 (seguridad, vinculante).** Todas las respuestas del integrado se
> verifican contra la CNF original: el modelo, o la prueba con los dos
> dsr-trim.

## 3. Diseño

```bash
./scripts/build.sh --dir=build-symm --symmetry --clean   # desde el commit de este preregistro
python3 scripts/compare_integrada.py --bench bench/symm2026 \
    --integrado solver/kissat/build-symm/kissat \
    --kissat solver/kissat/build/kissat --conflicts 100000 \
    --out results/exp012/equivalencia.csv
```

- **Medidas deterministas**: SHA-1 de la CNF y contadores de búsqueda. La carga
  de la máquina no las afecta. Aun así, se ejecuta **después** de la secuencia
  en curso (EXP-008 y partes 2 de EXP-010 y EXP-011), para no añadirle carga.
- **Kissat de la tubería**: `solver/kissat/build/kissat` (SHA-1
  `bed5fd46…`, el de EXP-008). Su núcleo es el mismo código que el del
  integrado: desde `c5f2e4c` solo han cambiado `application.c`, `symmetry.c`
  y el build.
- **Presupuesto**: 100 000 conflictos, lo bastante para cubrir búsqueda real
  en la mayoría de las instancias. El tiempo no importa.
- El guion vigila el SHA-1 de los tres binarios.

## 4. Criterio de decisión

| resultado | decisión |
|---|---|
| H1 74/74, H2 74/74 y H3 sin fallos | **Equivalente.** El binario integrado sustituye a la tubería en los experimentos siguientes (EXP-009/B3) y en la entrega. EXP-007 vale para él. `solver/labesat` queda solo para reproducir experimentos antiguos |
| H3 con algún fallo | **No se usa** el integrado; se busca la causa (ADR-0004, criterios de reversión) |
| H1 o H2 fallan en algunas instancias, con H3 correcta | Se documenta la causa de cada diferencia (se espera `-march=native`). El integrado sigue siendo **válido** (H3), pero EXP-007 **no** se transfiere a esas instancias. Se decide aparte si hace falta un A/B de tiempos sobre ellas |

## 5. Amenazas a la validez

- Un presupuesto de conflictos no cubre la fase final de las búsquedas largas.
  Pero dos trayectorias idénticas durante 100 000 conflictos, con estado
  igual, son una prueba fuerte de que el núcleo se comporta igual.
- Las variables de entorno de los topes se dejan en sus valores por defecto
  (60 s y 512 MiB), igual que en EXP-007.

## 6. Incidencias de ejecución

_Ninguna por ahora._

## 7. Resultados

_Pendiente._
