#!/usr/bin/env bash
#
# instalar_servicio.sh — servicio de usuario que ejecuta la cola de
# experimentos y la retoma sola tras un apagado o reinicio (ADR-0008).
#
#   ./scripts/instalar_servicio.sh            # instala, habilita y arranca
#   ./scripts/instalar_servicio.sh --quitar   # para, deshabilita y borra la unidad
#
# Qué hace el servicio `labesat-experimentos` (systemd --user):
#   - arranca con la sesión del usuario y lanza `orquestador.py ejecutar`;
#   - mientras corre, BLOQUEA la suspensión, la suspensión por inactividad y la
#     de cerrar la tapa (systemd-inhibit): una tanda no se interrumpe porque el
#     portátil se duerma;
#   - si el orquestador termina con error (p. ej. lo mata el tope de memoria),
#     se relanza a los 2 minutos, como mucho 5 veces por hora;
#   - limita la memoria de TODA la tanda (MemoryHigh 10 GB, MemoryMax 12 GB):
#     si un solver se desboca, el núcleo lo mata a él, no al escritorio.
#
# Para que arranque en cada encendido SIN iniciar sesión hace falta
# «lingering», que es una opción del sistema y la decide el director:
#     loginctl enable-linger "$USER"
#
# Operación:
#   systemctl --user status labesat-experimentos
#   journalctl --user -u labesat-experimentos -f
#   python3 scripts/orquestador.py estado
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UNIDAD="$HOME/.config/systemd/user/labesat-experimentos.service"

if [ "${1:-}" = "--quitar" ]; then
  systemctl --user disable --now labesat-experimentos.service 2>/dev/null || true
  rm -f "$UNIDAD"
  systemctl --user daemon-reload
  echo "servicio quitado"
  exit 0
fi

# El intérprete real (no el shim de pyenv, que fuera de la sesión puede no
# resolver) y su directorio al principio del PATH de los comandos de la cola.
PY="$(python3 -c 'import sys; print(sys.executable)')"
PYDIR="$(dirname "$PY")"
mkdir -p "$(dirname "$UNIDAD")"
cat > "$UNIDAD" <<EOF
[Unit]
Description=LabeSAT: cola de experimentos reanudable (ADR-0008)
Documentation=file://$ROOT/docs/adr/0008-experimentos-reanudables.md
After=default.target
StartLimitIntervalSec=3600
StartLimitBurst=5

[Service]
Type=simple
WorkingDirectory=$ROOT
Environment=PYTHONUNBUFFERED=1
Environment=PATH=$PYDIR:$PATH
ExecStart=/usr/bin/systemd-inhibit --what=sleep:idle:handle-lid-switch --who=LabeSAT --why="experimento en curso" --mode=block $PY $ROOT/scripts/orquestador.py ejecutar
Restart=on-failure
RestartSec=120
KillMode=control-group
KillSignal=SIGTERM
TimeoutStopSec=60
Nice=5
MemoryHigh=10G
MemoryMax=12G

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now labesat-experimentos.service
echo "instalado: $UNIDAD"
systemctl --user --no-pager status labesat-experimentos.service | head -5 || true
