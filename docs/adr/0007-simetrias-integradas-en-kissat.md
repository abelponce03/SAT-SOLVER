# ADR-0007 — Ruptura de simetrías integrada en Kissat, por fases

- **Estado**: aceptado. La fase 1 está implementada detrás de una opción,
  **apagada por defecto**; su equivalencia se valida en EXP-012.
- **Fecha**: 2026-09-23
- **Decide**: Abel Ponce (D-016, opción c: «tomar los algoritmos y montarlos
  sobre Kissat, no tener un selector de solucionadores»).
- **Sustituye en parte a**: ADR-0004, en lo que se refiere a satsuma como
  **programa externo**. Las licencias, el formato de prueba y la verificación
  de ADR-0004 siguen vigentes.

## Contexto

- ADR-0004 dejó la ruptura de simetrías como un programa aparte: el guion
  `solver/labesat` ejecuta satsuma y después kissat. Así lo pidió el director
  (D-008).
- El 2026-09-23 el director aclara el objetivo: **un único solver**, Kissat con
  los algoritmos montados encima. Ni una tubería de dos programas ni un
  selector.
- Opciones estudiadas (registro, D-016):
  - **a.** Dejarlo externo.
  - **b.** Reimplementar en C, dentro de Kissat, la detección de simetrías, la
    ruptura y la prueba SR. Son meses de trabajo, con riesgo alto antes del
    congelado de mejoras (H5, 25 de enero de 2027).
  - **c.** Por fases: primero satsuma **compilado dentro del binario**; después,
    reimplementación pieza a pieza donde aporte.
- Restricciones:
  - la competición compila sin red, así que el código tiene que ir en el
    paquete;
  - todo en MIT (ADR-0004);
  - una prueba inválida descalifica.

## Decisión: opción c

### Fase 1 (esta ADR): un solo binario

1. **Vendorizado**: satsuma `c6ad1b5`, dejavu `4c275e9` y tsl robin-map van en
   `solver/satsuma/`, **sin modificar**. Todos son MIT.
   - Solo se copian las cabeceras, `satsuma.cpp` y las licencias.
   - `scripts/vendor_satsuma.sh --check` comprueba en CI que coinciden byte a
     byte con el upstream.
2. **Unión**: `solver/symmetry/satsuma_entry.cpp` (20 líneas) incluye
   `satsuma.cpp` renombrando su `main`, y expone `labesat_satsuma_main` a C.
3. **Kissat** (`src/symmetry.c`, `src/application.c`, marcados `[SOLVER]`):
   - nueva opción de la aplicación `--symmetry`, **apagada por defecto**. Es
     una opción de la aplicación, no del solver, así que sobrevive a
     `--competition`;
   - antes de abrir la prueba y leer la CNF, Kissat ejecuta satsuma en un
     **proceso hijo** con los mismos argumentos que usaba el guion;
   - si funciona, lee la CNF simplificada y continúa la prueba SR (modo
     añadir);
   - si falla, se pasa del tope (`LABESAT_SYMM_TIMEOUT`, 60 s) o la entrada
     supera `LABESAT_SYMM_MAXBYTES`, lee la CNF original con prueba DRAT desde
     cero;
   - el tiempo de satsuma cuenta dentro de `--time`, porque la alarma ya corre.
4. **Compilación**: `configure --symmetry` (o `scripts/build.sh --symmetry`)
   compila satsuma con el C++ que corresponde al compilador de C y enlaza con
   él. Sin `--symmetry`, el build es el de siempre: C puro, sin satsuma, y la
   opción da un error.
   - Sin `-march=native`: el binario de competición tiene que funcionar en
     otra máquina.
   - `CLIQUES=0` hasta que D-005 (mclique) se valide.

**Por qué un proceso hijo y no una llamada directa**:
- el resultado es **idéntico** al del programa externo (EXP-012 lo comprueba),
  así que EXP-007 sigue valiendo;
- un `exit()`, un fallo o un tope dentro de satsuma no tumban al solver;
- se puede matar a satsuma al llegar al tope sin dejar memoria ni estado a
  medias.

Sigue siendo **un binario**, y el `fork` es un detalle de implementación. En la
fase 2, la parte que se reimplemente en Kissat podrá correr en el mismo
proceso.

### Fase 2 (después de H5, o antes si da tiempo)

- **B3 dentro de Kissat** (EXP-009): decidir si se aplica la ruptura con
  información del propio Kissat, sin pagar satsuma cuando no ayuda.
- Reimplementar en C, por orden de valor:
  1. la escritura de la CNF y la lectura sin ficheros intermedios;
  2. la ruptura de filas y órbitas sobre las estructuras de Kissat;
  3. la detección de simetrías.

  Cada pieza lleva su experimento de equivalencia o de rendimiento.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| a. Programa externo | No cumple el objetivo del director (un solo solver) y mantiene la duda de la composición (D-003) |
| b. Reimplementación completa ya | Riesgo de no llegar a 2027 con nada validado |
| Llamada directa en el mismo proceso | Un `exit()` de satsuma (`terminate_with_error`) mataría al solver; no hay forma limpia de aplicar el tope de tiempo |
| Enlazar satsuma como biblioteca externa | La competición compila sin red: el código tiene que ir en el paquete |

## Consecuencias

- **Positivas**:
  - un único binario, `kissat --symmetry`, sin guion de por medio;
  - B3 puede hacerse dentro de Kissat;
  - el camino queda abierto para sustituir satsuma por código propio;
  - desaparece la pregunta de la composición de dos programas (D-003), aunque
    satsuma sigue siendo código de terceros, declarado.
- **Negativas**:
  - hace falta un compilador de C++20 cuando se compila con `--symmetry`;
  - se añaden unas 29 700 líneas de terceros al paquete (satsuma, dejavu y
    tsl, sin modificar, declaradas en `THIRD_PARTY_NOTICES.md`);
  - el binario crece de 0,57 a 1,3 MB.
- **`solver/labesat`** se mantiene mientras sirva para reproducir EXP-007 y
  EXP-010/011. La entrega usa el binario integrado.
- **Declaración de IA**:
  - `symmetry.c/h` cuentan como líneas inactivas hasta que `--symmetry` vaya
    activado en la entrega;
  - la unión C++ se cuenta aparte;
  - satsuma y dejavu, 0 líneas nuestras.

## Validación

- `scripts/test_symmetry_integrada.sh` (en CI), sobre `bench/symm`:
  - CNF intermedia idéntica a la de satsuma externo;
  - pruebas aceptadas por los dos dsr-trim;
  - modelos correctos contra la CNF original;
  - entrada `.xz`;
  - respaldo con prueba DRAT pura;
  - apagado por defecto.
- CI compila también la configuración de competición con `--symmetry` y
  verifica una prueba.
- **EXP-012** (preregistrado): equivalencia en las 74 instancias de
  `bench/symm2026` frente a la tubería de EXP-007.

## Referencias

- ADR-0004 (satsuma externo, licencias y pruebas).
- D-016 en `docs/decisiones/registro.md`.
- `solver/satsuma/UPSTREAM.md`.
