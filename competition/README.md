# Workspace de competición — SAT Competition 2027 (Main Track)

Base de trabajo para preparar una entrada a la **Main Track** de la
[SAT Competition](https://satcompetition.github.io/) (edición objetivo: **2027**).
La estrategia acordada: **partir de un fork de CaDiCaL** (solver CDCL de
referencia, MIT) y aportar **una** mejora medible, en lugar de escribir un solver
desde cero o construir un portfolio tipo SATzilla (ver justificación abajo).

## Estructura

```
competition/
├── cadical/        Fork vendorizado de CaDiCaL v3.0.1 (MIT). Aquí van tus cambios.
├── benchmarks/
│   ├── sample/     Instancias pequeñas para validar el harness (versionadas).
│   └── downloaded/ Suites oficiales de la SAT Competition (NO versionadas).
├── scripts/
│   ├── build.sh          Compila el fork.
│   ├── gen_benchmarks.py  Genera instancias de muestra (pigeonhole, 3-SAT).
│   ├── run_baseline.sh    Corre el solver sobre un dir de CNF con timeout -> CSV.
│   └── par2.py            Calcula PAR-2 y compara dos corridas (A/B).
└── results/        CSV de las corridas (NO versionados; regenerables).
```

## Arranque rápido

```bash
cd competition

# 1. Compilar el fork
./scripts/build.sh

# 2. Generar instancias de muestra (ya vienen algunas en benchmarks/sample)
python3 scripts/gen_benchmarks.py --out benchmarks/sample

# 3. Medir el baseline (CaDiCaL sin modificar)
./scripts/run_baseline.sh -s cadical/build/cadical -b benchmarks/sample \
    -o results/baseline.csv -t 60 -n cadical-3.0.1-vanilla

# 4. Ver el PAR-2
python3 scripts/par2.py results/baseline.csv
```

## Metodología A/B (así se mide una mejora)

La métrica oficial de ranking es **PAR-2** (Penalized Average Runtime, factor 2):
tiempo real si el solver resuelve la instancia; `2 × timeout` de penalización si
no. **Menor es mejor.** Flujo para validar cualquier cambio que hagas:

```bash
# baseline: CaDiCaL sin tocar
./scripts/run_baseline.sh -s cadical/build/cadical -b <bench> \
    -o results/A_baseline.csv -t 60 -n vanilla

# ... editas cadical/src/... , recompilas con ./scripts/build.sh ...

# modificado
./scripts/run_baseline.sh -s cadical/build/cadical -b <bench> \
    -o results/B_mod.csv -t 60 -n mi-mejora

# comparación instancia por instancia + veredicto de PAR-2
python3 scripts/par2.py results/A_baseline.csv results/B_mod.csv
```

Regla de oro: **cambia una sola cosa a la vez** y mídela contra el mismo conjunto
de instancias y el mismo timeout. Guarda copia del binario baseline antes de
empezar a editar, para poder comparar siempre contra la misma referencia.

## Por qué fork de CaDiCaL y no SATzilla / portfolio

- Las reglas prohíben portfolios puros que combinen solvers de **distintos
  autores** salvo que usen **metodologías distintas** (CDCL, SLS, lookahead…);
  un SATzilla clásico de selección entre solvers CDCL de terceros no encaja.
- Entrenar un portfolio exige correr todos los solvers candidatos sobre un banco
  grande de instancias (cientos de horas de cómputo) y arriesga sobreajuste a
  instancias conocidas: los benchmarks nuevos de cada año lo penalizan.
- La familia CaDiCaL/Kissat es de donde derivan casi todos los top solvers
  recientes. Forkear + aportar una técnica es el flujo **que la competencia
  espera** (la descripción del sistema pide declarar código base, versión y
  líneas modificadas).
- CaDiCaL ya trae resuelto lo caro: certificados DRAT, parsing, preprocesado,
  gestión de cláusulas. Te concentras en la contribución novedosa.

> La intuición de SATzilla sigue siendo válida como **autoconfiguración interna
> por features dentro de tu propio fork** (un único solver, un único autor): no
> cae bajo la restricción de portfolios y es una contribución publicable.

## Requisitos de la Main Track a no olvidar

- **Certificados UNSAT en DRAT** — CaDiCaL ya los produce (`--no-binary` /
  opción de traza); valida con `drat-trim`.
- **Modelo** impreso en instancias SAT (CaDiCaL ya lo hace).
- **Código fuente** licenciado para investigación (MIT de CaDiCaL cumple; añade
  tu propia atribución sin quitar la de los autores originales — ver `cadical/LICENSE`).
- **Descripción del sistema** (1–2 pág., IEEE): base = CaDiCaL v3.0.1, % líneas
  modificadas, técnica añadida, y **disclosure de uso de IA** (obligatorio 2026).
- **20 benchmarks nuevos** propios (ver `benchmarks/README.md`).
- Calendario objetivo **2027** (aún sin publicar). Referencia 2026: registro
  ~**abr**, solver secuencial ~**may**, documentación ~**may**. Con vista a 2027
  tenemos margen amplio: el año extra es para la contribución de investigación.

## Atribución

CaDiCaL es MIT © sus autores (Biere, Fleury, Fazekas, Pollitt, Faller, y otros;
ver `cadical/LICENSE`). Este fork conserva esa licencia y su aviso de copyright.
Tus modificaciones deben quedar claramente identificadas en la descripción del
sistema y, si publicas el fork, en un aviso añadido — sin eliminar el original.
