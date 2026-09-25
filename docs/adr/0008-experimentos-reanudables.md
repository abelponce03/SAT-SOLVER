# ADR-0008 — Experimentos reanudables: checkpoints, cola y servicio

- **Estado**: aceptado
- **Fecha**: 2026-09-25
- **Decide**: Abel Ponce («idear algún mecanismo para que existan checkpoint,
  resistencia ante apagado del equipo y demás, porque es tiempo que estamos
  desperdiciando»)

## Contexto

Desde el 2026-09-23 los experimentos corren en la máquina local del director
(portátil i5-1135G7, 15 GB). En dos días se perdió tiempo de cómputo tres veces:

1. **2026-09-23, en la nube**: un reinicio del contenedor cortó EXP-008. Se
   añadió `--resume` al arnés A/B.
2. **2026-09-24**: la máquina se quedó sin RAM al solapar tandas y cayó la
   sesión con todos los procesos.
3. **2026-09-25**: la cadena murió a la 01:13, en EXP-011 parte 1 (80 de 84
   instancias), sin ningún error en los logs. El equipo se apagó o suspendió,
   y se reinició varias veces al día siguiente. La cola de EXP-013, 014 y 015
   nunca arrancó: dependía de un proceso lanzado a mano que ya no existía.

Había tres huecos:

- **Arneses que no reanudaban**: `run_experiment.py`,
  `compare_satsuma_builds.py` y `compare_integrada.py` sobrescribían su CSV.
- **Escrituras no duraderas**: `flush` sin `fsync`. Un apagón podía dejar una
  última línea cortada, que `csv.DictReader` lee como fila con campos `None`,
  y su clave (instancia, semilla) parecería medida.
- **Nada volvía a lanzar la cola** tras un reinicio, y nada impedía que el
  portátil se suspendiera en mitad de una tanda.

## Decisión

Tres capas:

### 1. Checkpoints en los arneses (`scripts/checkpoint.py`)

- `filas_completas()`: solo filas íntegras (línea terminada y con todas las
  columnas).
- `EscritorDuradero`: reescritura atómica de lo conservado y `fsync` por fila.
- `--resume` en todos los arneses, cada uno con su clave natural:
  - pareja (instancia, semilla) en los A/B;
  - (instancia, semilla) en `run_experiment.py`, que además **aborta** si el
    binario, las opciones o el presupuesto no son los de la tanda original;
  - instancia completa (todas sus builds) en `compare_satsuma_builds.py`;
  - instancia en `compare_integrada.py` y `scan_symmetry.py`.
- Un corte pierde, como mucho, la corrida o la pareja en curso.

### 2. Cola declarativa y orquestador

- `scripts/cola.toml`: cada experimento es un paso con un `comando`
  reanudable, que es el de su preregistro, y una comprobación `hecho`.
- `scripts/orquestador.py ejecutar`:
  - recorre la cola en orden y salta lo hecho;
  - un paso a la vez;
  - `flock` para que nunca haya dos orquestadores;
  - latido cada minuto y marcas `results/.estado/<id>.hecho` con el commit y
    el SHA-1 de los binarios;
  - tres fallos seguidos detienen un paso hasta que lo revise una persona.
- `orquestador.py estado` dice qué está hecho, qué corre y si el proceso está
  vivo.

### 3. Servicio de usuario (`scripts/instalar_servicio.sh`)

`labesat-experimentos.service` (systemd `--user`):

- arranca con la sesión y relanza el orquestador si falla (cada 2 min, como
  mucho 5 veces por hora);
- **bloquea la suspensión**, también la de cerrar la tapa (`systemd-inhibit`),
  mientras hay experimentos;
- limita la memoria de toda la tanda (`MemoryHigh` 6 GB, `MemoryMax` 7 GB,
  swap 512 MB) con `OOMPolicy=continue`: si un proceso se desboca, el núcleo
  mata **solo a ese proceso**, su corrida sale como error y la cola sigue.
  El equipo se usa a la vez como escritorio (unos 7 GB), y kissat llegó a
  5,3 GB en EXP-008.

**Primera versión (12 GB, política por defecto), corregida el mismo día**: a
los dos minutos de instalarse, satsuma sobre `bbcfd33f` (una CNF de ~500 MB)
llegó a agotar la memoria **del equipo**, porque la sesión del director
ocupaba otros ~9 GB. Actuó el OOM del sistema, systemd detuvo toda la unidad
(`OOMPolicy=stop`) y la relanzó para repetir lo mismo. Es, muy probablemente,
lo que colgó el portátil a la 01:13. Se corrigió en dos sitios:

- el límite de la unidad, como se describe arriba;
- `compare_satsuma_builds.py`, que ahora aplica el mismo tope de tamaño que
  `labesat` (512 MiB, por encima del cual labesat nunca ejecuta satsuma) y un
  `RLIMIT_AS` de 6 GB por proceso.

Para que arranque en cada encendido sin iniciar sesión hace falta
`loginctl enable-linger`, una opción del sistema que decide el director.

## Validez experimental de reanudar

- **ADR-0003 §4b** exige que las dos ramas de un A/B se midan en la misma
  máquina y con segundos de diferencia. Una pareja completa lo cumple aunque
  la tanda se corte después; la pareja a medias se descarta y se repite
  entera.
- Reanudar tras un reinicio **en la misma máquina** está permitido (CLAUDE.md
  §6). Reanudar en otra máquina, no: la guarda de SHA-1 y el `meta.json` lo
  impiden en los A/B.
- Cada reanudación queda en el `meta.json` (`reanudaciones` en los A/B, `reanudada` en `run_experiment.py`) y en
  la sección de incidencias de su experimento.
- El tope de 7 GB está por debajo de los 32 GB de la competición. Si un
  solver lo alcanza, la corrida sale como error o MEMOUT y se anota; hasta hoy
  ninguna instancia de los bancos lo necesita.

## Verificación

`scripts/test_reanudacion.sh` (también en CI) simula un apagón con `kill -9`
y una última línea cortada, y comprueba que:

- `run_experiment.py --resume` da **exactamente** las mismas corridas que una
  tanda sin cortes;
- el A/B completa todas las parejas sin duplicados;
- el orquestador, matado en pleno paso, lo retoma y lo marca hecho;
- no pueden correr dos orquestadores a la vez.

## Consecuencias

- `scripts/reanudar_experimentos.sh` y `scripts/cola_tesis.sh` quedan
  sustituidos por `cola.toml`. Se conservan como registro de cómo se lanzaron
  EXP-008 y la parte 1 de EXP-014.
- Añadir un experimento = preregistrarlo + añadir su paso a `cola.toml`.

## Criterios de reversión

Si aparece un clúster, la cola se ejecuta allí con el mismo orquestador (sin
el servicio) o se traduce a su gestor de colas.
