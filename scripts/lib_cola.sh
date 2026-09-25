# lib_cola.sh — funciones para los comandos de scripts/cola.toml (ADR-0008).
# El orquestador hace `source` de este fichero antes de cada comando y de cada
# comprobación de «hecho». No se ejecuta solo.

# filas FICHERO -> nº de filas ÍNTEGRAS de un CSV (0 si no existe). Una última
# línea cortada por un apagón no cuenta (scripts/checkpoint.py).
filas() {
  [ -f "$1" ] || { echo 0; return; }
  python3 -c 'import sys; sys.path.insert(0, "scripts")
from checkpoint import filas_completas; print(len(filas_completas(sys.argv[1])))' "$1"
}

# lineas_lista FICHERO -> nº de líneas que no son comentario
# (grep -c escribe 0 y además sale con 1 si no hay líneas: de ahí el || true)
lineas_lista() { [ -f "$1" ] || { echo 0; return; }; grep -cv '^#' "$1" || true; }

# ab ARGS... -> run_ab_interleaved.py con --resume si la tanda ya empezó
# en esta máquina (existe el meta.json de la rama A).
ab() {
  local out_a="" prev=""
  for a in "$@"; do [ "$prev" = "--out-a" ] && out_a="$a"; prev="$a"; done
  local extra=()
  [ -n "$out_a" ] && [ -f "${out_a%.csv}.meta.json" ] && extra=(--resume)
  python3 scripts/run_ab_interleaved.py "$@" "${extra[@]}"
}
