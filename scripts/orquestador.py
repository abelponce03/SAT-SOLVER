#!/usr/bin/env python3
"""
orquestador.py — ejecuta la cola de experimentos y sobrevive a apagados (ADR-0008).

    python3 scripts/orquestador.py ejecutar     # recorre scripts/cola.toml
    python3 scripts/orquestador.py estado       # qué está hecho, qué corre, latido
    python3 scripts/orquestador.py marcar ID    # da un paso por hecho a mano (con motivo)

Cómo resiste un apagado, un reinicio o una caída por memoria:

1. **Pasos idempotentes.** Cada paso de `cola.toml` tiene una comprobación
   `hecho` y un `comando` reanudable (los arneses tienen --resume y escriben
   con fsync; ver scripts/checkpoint.py). Volver a lanzar el orquestador salta
   lo hecho y continúa lo empezado. Lo perdido en un corte es, como mucho, la
   corrida (o la pareja A/B) que estaba en marcha.
2. **Arranque automático.** El servicio de usuario `labesat-experimentos`
   (scripts/instalar_servicio.sh) lo lanza al iniciar sesión y lo reinicia si
   termina con error.
3. **Un solo orquestador.** Un `flock` sobre results/.estado/orquestador.lock
   impide dos tandas a la vez, que es lo que tumbó la máquina el 2026-09-24.
4. **Latido.** results/.estado/latido.json se reescribe cada minuto con el paso
   en curso y el PID. `estado` dice si está vivo o si murió sin avisar.
5. **Marcas.** Al terminar un paso se escribe results/.estado/<id>.hecho (JSON)
   con la fecha, el commit y el SHA-1 de los binarios de la tanda.

Nunca compila ni cambia binarios por su cuenta, salvo el `build-symm` que el
propio preregistro de EXP-012 manda compilar si no existe.
"""
import argparse
import fcntl
import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import tomllib
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ESTADO = os.path.join(ROOT, "results", ".estado")
LOGS = os.path.join(ROOT, "results", "logs")
COLA = os.path.join(ROOT, "scripts", "cola.toml")
LIB = os.path.join(ROOT, "scripts", "lib_cola.sh")
BINARIOS = ["solver/kissat/build/kissat", "solver/kissat/build-vsa/kissat",
            "solver/kissat/build-symm/kissat", "tools/satsuma", "tools/satsuma-mclique",
            "tools/satsuma-mclique-v1", "tools/kissat-sc2026"]
REINTENTOS, PAUSA = 3, 300

hijo = None          # proceso del paso en curso
parar = False


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(msg):
    print(f"== {ahora()} {msg}", flush=True)


def escribir_json(path, datos):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(datos, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True).stdout.strip()


def cargar_cola():
    with open(COLA, "rb") as f:
        return tomllib.load(f)["paso"]


def bash(cmd, logf=None):
    """Ejecuta `cmd` con lib_cola.sh cargado, en su propio grupo de procesos."""
    global hijo
    script = f"set -eo pipefail\nsource {LIB}\n{cmd}"
    hijo = subprocess.Popen(["bash", "-c", script], cwd=ROOT, stdout=logf or subprocess.DEVNULL,
                            stderr=subprocess.STDOUT if logf else subprocess.DEVNULL,
                            stdin=subprocess.DEVNULL, start_new_session=True)
    try:
        return hijo.wait()
    finally:
        hijo = None


def esta_hecho(paso):
    return bash(paso["hecho"]) == 0


def latido(estado):
    while not parar:
        estado["latido"] = ahora()
        try:
            escribir_json(os.path.join(ESTADO, "latido.json"), estado)
        except OSError:
            pass
        for _ in range(60):
            if parar:
                return
            time.sleep(1)


def al_terminar(signum, _frame):
    """SIGTERM/SIGINT (apagado ordenado, `systemctl stop`): corta el paso en
    curso. Su corrida a medias se descarta al reanudar."""
    global parar
    parar = True
    if hijo is not None:
        try:
            os.killpg(hijo.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    log(f"señal {signum}: se detiene; al volver a lanzarlo, reanuda")


def ejecutar(args):
    os.makedirs(ESTADO, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)
    cerrojo = open(os.path.join(ESTADO, "orquestador.lock"), "w")
    try:
        fcntl.flock(cerrojo, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit("ya hay un orquestador en marcha (results/.estado/orquestador.lock)")
    signal.signal(signal.SIGTERM, al_terminar)
    signal.signal(signal.SIGINT, al_terminar)
    estado = {"pid": os.getpid(), "host": socket.gethostname(), "inicio": ahora(),
              "commit": git("rev-parse", "HEAD"), "paso": None}
    threading.Thread(target=latido, args=(estado,), daemon=True).start()
    log(f"orquestador en marcha (pid {os.getpid()}, commit {estado['commit'][:7]})")

    pendientes = True
    while pendientes and not parar:
        pendientes = False
        for paso in cargar_cola():                     # se relee en cada vuelta
            if parar:
                break
            pid_ = paso["id"]
            marca = os.path.join(ESTADO, f"{pid_}.hecho")
            if os.path.exists(marca):
                continue
            if esta_hecho(paso):
                escribir_marca(paso, marca, "ya estaba hecho")
                continue
            faltan = [r for r in paso.get("requiere", []) if not os.path.exists(os.path.join(ROOT, r))]
            if faltan:
                log(f"{pid_}: faltan {faltan}; se salta de momento")
                continue
            fallos_path = os.path.join(ESTADO, f"{pid_}.fallos")
            fallos = int(open(fallos_path).read()) if os.path.exists(fallos_path) else 0
            if fallos >= REINTENTOS:
                log(f"{pid_}: {fallos} fallos seguidos; necesita revisión humana "
                    f"(borrar {os.path.relpath(fallos_path, ROOT)} para reintentar)")
                continue
            estado["paso"] = pid_
            log(f"{pid_}: {paso.get('descripcion', '')}")
            with open(os.path.join(LOGS, f"{pid_}.log"), "a") as lf:
                lf.write(f"\n== {ahora()} inicio (orquestador pid {os.getpid()})\n")
                lf.flush()
                rc = bash(paso["comando"], lf)
            estado["paso"] = None
            if parar:
                break
            if rc == 0 and esta_hecho(paso):
                escribir_marca(paso, marca, "completado")
                if os.path.exists(fallos_path):
                    os.remove(fallos_path)
                log(f"{pid_}: hecho")
                pendientes = True          # otra vuelta: un paso puede habilitar otro
                break
            fallos += 1
            with open(fallos_path, "w") as f:
                f.write(str(fallos))
            log(f"{pid_}: terminó con código {rc} sin completar (fallo {fallos}/{REINTENTOS}); "
                f"ver results/logs/{pid_}.log")
            for _ in range(PAUSA):
                if parar:
                    break
                time.sleep(1)
            pendientes = True
            break
    log("cola terminada" if not parar else "detenido")
    if parar:
        sys.exit(143)
    incompletos = [p["id"] for p in cargar_cola()
                   if not os.path.exists(os.path.join(ESTADO, f"{p['id']}.hecho"))]
    if incompletos:
        log(f"quedan sin completar: {incompletos}")
        sys.exit(1)


def escribir_marca(paso, marca, como):
    shas = {b: sha1(os.path.join(ROOT, b))[:12] for b in BINARIOS
            if os.path.isfile(os.path.join(ROOT, b))}
    escribir_json(marca, {"id": paso["id"], "fecha": ahora(), "como": como,
                          "commit": git("rev-parse", "HEAD"), "host": socket.gethostname(),
                          "binarios_sha1": shas})


def estado(_):
    lat = os.path.join(ESTADO, "latido.json")
    if os.path.exists(lat):
        d = json.load(open(lat))
        edad = time.time() - datetime.fromisoformat(d["latido"]).timestamp()
        vivo = edad < 180
        try:
            os.kill(d["pid"], 0)
        except (ProcessLookupError, PermissionError):
            vivo = False
        print(f"orquestador: {'VIVO' if vivo else 'parado'} (pid {d['pid']}, latido hace "
              f"{edad:.0f} s, paso en curso: {d.get('paso') or '-'})")
    else:
        print("orquestador: nunca lanzado")
    for paso in cargar_cola():
        marca = os.path.join(ESTADO, f"{paso['id']}.hecho")
        fallos = os.path.join(ESTADO, f"{paso['id']}.fallos")
        if os.path.exists(marca):
            e = "hecho " + json.load(open(marca))["fecha"][:16]
        elif os.path.exists(fallos):
            e = f"FALLOS {open(fallos).read().strip()}"
        else:
            e = "pendiente"
        print(f"  {paso['id']:<16} {e:<24} {paso.get('descripcion', '')}")


def marcar(args):
    paso = next((p for p in cargar_cola() if p["id"] == args.id), None)
    if paso is None:
        sys.exit(f"no hay paso {args.id}")
    os.makedirs(ESTADO, exist_ok=True)
    escribir_marca(paso, os.path.join(ESTADO, f"{args.id}.hecho"), f"a mano: {args.motivo}")
    print(f"{args.id} marcado como hecho")


def main():
    global ESTADO, COLA, LOGS
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--cola", default=COLA, help="cola TOML (por defecto scripts/cola.toml)")
    ap.add_argument("--estado-dir", default=ESTADO,
                    help="directorio de marcas, latido y cerrojo (por defecto results/.estado)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ejecutar")
    sub.add_parser("estado")
    m = sub.add_parser("marcar")
    m.add_argument("id")
    m.add_argument("--motivo", required=True)
    args = ap.parse_args()
    if os.path.abspath(args.estado_dir) != ESTADO:      # pruebas: todo fuera de results/
        LOGS = os.path.join(os.path.abspath(args.estado_dir), "logs")
    COLA, ESTADO = os.path.abspath(args.cola), os.path.abspath(args.estado_dir)
    {"ejecutar": ejecutar, "estado": estado, "marcar": marcar}[args.cmd](args)


if __name__ == "__main__":
    main()
