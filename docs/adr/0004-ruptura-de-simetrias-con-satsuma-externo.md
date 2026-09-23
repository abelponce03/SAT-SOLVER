# ADR-0004 — Ruptura de simetrías: satsuma como programa externo, todo bajo MIT

- **Estado**: aceptado (integración). **EXP-007 (2026-09-23)**: mejora mucho
  donde hay simetría explotable, pero ralentiza 1.42× las instancias neutras.
  Veredicto: **solo condicional**; en `labesat` es opcional (`--symmetry`) hasta
  que la activación condicional (B3) esté validada.
- **D-005, opción c (2026-09-23)**: la clique máxima que satsuma toma de
  cliquer se reimplementa en MIT (**mclique**, `solver/mclique/`). Se compila
  aparte como `tools/satsuma-mclique`, y pasa a ser el satsuma por defecto solo
  si EXP-010 lo valida.
- **Fecha**: 2026-09-23
- **Decide**: Abel Ponce («usa satsuma como programa externo y mantén MIT»)

## Contexto

- En los datos oficiales de 2026 (`docs/research/01`), la ruptura de simetrías
  como preprocesado es la palanca de PAR-2 más grande que hemos medido: aplicada
  siempre, resuelve 51 instancias que antes no se resolvían y **pierde 13**. El
  oráculo condicional aporta −322 s extra.
- Reproducido en local: `php_12_11` pasa de 68,24 s a 0,02 s, y `php_13_12`
  pasa de timeout a 0,02 s.
- Licencias comprobadas el 2026-09-22:
  - **satsuma** en su repositorio upstream (`markusa4/satsuma`, commit
    `c6ad1b5`): MIT. Su CMake trae `option(CLIQUES … OFF)`.
  - **cliquer**: GPLv2. Solo se enlaza con `CLIQUES=ON`, y además no está en el
    repositorio upstream.
  - **dejavu**: MIT.
  - **dsr-trim**: Apache 2.0.
  - La entrada ganadora de 2026: GPLv3 (proyecto aparte, del que no se copia
    código).
- Pruebas: una respuesta UNSAT con una prueba incorrecta **descalifica**. La
  ruptura de simetrías no es DRAT. satsuma emite el prefijo de la prueba en
  formato **SR** (*substitution redundancy*), que es un superconjunto de DRAT.
  La prueba completa se verifica con **dsr-trim**.

## Decisión

La ruptura de simetrías entra como **programa externo** que se ejecuta **antes**
de kissat. El núcleo del solver no se toca.

1. **`tools/satsuma`**: satsuma upstream fijado en `c6ad1b5`, con dejavu
   `4c275e9`, compilado con `CLIQUES=OFF`. `scripts/get_tools.sh` lo descarga y
   compila, y **aborta** si detecta cliquer. Así todo lo que se distribuye queda
   bajo MIT (más Apache 2.0 en el verificador, que no se entrega).
2. **`--append-proof`** es una opción nueva de la *aplicación* kissat, no del
   solver, así que sobrevive a `--competition`. Abre el fichero de prueba en modo
   añadir (`kissat_open_to_append_file`, en `file.c`) para continuar el prefijo
   de satsuma. Está escrita desde cero a partir del `kissat_open_to_write_file`
   de Kissat (MIT). No se ha copiado el código equivalente de la entrada de 2026.
   - **Formato**: satsuma escribe el prefijo SR **siempre en binario**, y dsr-trim
     detecta el formato una sola vez por fichero. Por eso la continuación también
     va en binario: se respeta el valor por defecto de kissat, y `--no-binary`
     queda para prefijos en texto.
   - Hipótesis inicial equivocada, corregida en el desarrollo: forzar texto
     rompía la verificación con el error `Unexpected binary character`.
   - No se admiten ficheros comprimidos: un flujo comprimido no se puede
     continuar concatenando.
3. **`solver/labesat`** es el guion de entrada:
   `labesat [--symmetry | --no-symmetry] <cnf> [<proof>]` (desde EXP-007, la ruptura va **desactivada por defecto**).
   1. Lanza `satsuma fix … --bsr --add-reduced-as-unit` con un tope de tiempo y
      de tamaño.
   2. Lanza `kissat --append-proof` sobre la CNF simplificada.
   3. Si satsuma falla, se pasa de tiempo o la entrada es demasiado grande,
      **cae a kissat sobre la CNF original** con una prueba DRAT desde cero.
   - Descomprime la entrada, porque satsuma no lee `.xz`.
   - Reenvía SIGTERM a kissat, que imprime sus estadísticas.
   - Limpia los temporales.
   - Los topes (`LABESAT_SYMM_TIMEOUT=60`, `LABESAT_SYMM_MAXBYTES=512 MiB`) son
     **provisionales**: se fijan en EXP-007.
4. **Verificación continua**: `scripts/test_symmetry.sh` se ejecuta en CI, tanto
   con el build normal como con el de competición. Usa `bench/symm` y comprueba:
   - **UNSAT**: dsr-trim verifica la prueba combinada contra la CNF **original**.
   - **SAT**: el modelo satisface la CNF **original**.
   - **Control negativo**: sin `--append-proof`, dsr-trim **rechaza** la prueba.
     Si la aceptara, el test no demostraría nada.
   - **Ruta de respaldo**: la prueba es DRAT pura y la verifica drat-trim.

## Alternativas consideradas

| Alternativa | Pros | Contras | Por qué no |
|---|---|---|---|
| Copiar la entrada ganadora de 2026 | Ya está probada en competición | GPLv3: contagiaría todo LabeSAT | Incompatible con mantener MIT |
| satsuma con `CLIQUES=ON` | Quizá rompe más simetrías | cliquer es GPLv2; no está en el upstream | Mismo motivo. Su coste se midió (`research/03`: 6 instancias de H) y se ataca con mclique, en MIT (D-005, EXP-010) |
| Ruptura de simetrías *dentro* de kissat | Una sola pasada; podría usar `classify.c` | Meses de trabajo; la prueba SR habría que generarla nosotros | Coste desproporcionado antes de saber si compensa (EXP-007) |
| BreakID | Referencia clásica | Predicados de ruptura sin prueba SR integrada | Sin prueba no se puede entregar |
| Prefijo en texto (`--no-binary`) | Legible | satsuma solo emite SR binario | No es posible con satsuma |

## Consecuencias

- **Positivas**:
  - Acceso a la mayor palanca medida, con pruebas verificables y licencia MIT.
  - El núcleo de kissat no cambia: los experimentos A4 siguen siendo
    comparables.
- **Negativas / coste asumido**:
  - Hay un proceso extra, más E/S de la CNF (se escribe dos veces) y el tiempo
    de satsuma, incluso cuando no encuentra simetrías.
  - En `php9x9_rand160u` la prueba de kissat **no necesita** el prefijo, porque
    la contradicción está en la parte aleatoria. El control negativo usa
    `php_12_11`, cuya refutación corta sí lo necesita.
- **Riesgos y cómo se vigilan**:
  - **Reglas (§1.2 del ROADMAP)**: kissat y satsuma son de grupos distintos. No
    es una cartera (se ejecutan en secuencia, y la ruptura de simetrías es otra
    metodología: preprocesado, no CDCL), pero **conviene confirmarlo por escrito
    con los organizadores**. Es una decisión pendiente del autor.
  - **Formato de prueba**: hay que confirmar que en 2027 se siga aceptando SR
    verificado con dsr-trim.
  - **Modelos**: `fix` simplifica la CNF: en `php9x9_rand160s` pasa de 1015 a 763
    cláusulas. En `bench/symm` los modelos satisfacen la CNF original, pero
    EXP-007 comprobará **todos** los modelos SAT con `verify_model.py` contra la
    CNF original.

## Criterios de reversión

- Si EXP-007 no mejora el PAR-2 respecto a LabeSAT sin simetrías (protocolo del
  ADR-0003), `labesat` se entrega con `--no-symmetry` o sin satsuma.
- Si **un solo** modelo o prueba sale inválido en cualquier experimento, se
  desactiva hasta encontrar la causa.
- Si los organizadores consideran la combinación una cartera prohibida, se
  retira.

## Referencias

- satsuma: <https://github.com/markusa4/satsuma> (MIT)
- dejavu: <https://github.com/markusa4/dejavu> (MIT)
- dsr-trim: <https://github.com/ccodel/dsr-trim> (Apache 2.0)
- `docs/research/01-analisis-empirico-sc2026.md`: 51 instancias ganadas, 13
  perdidas y el oráculo condicional.
