#!/usr/bin/env bash
#
# cola_tesis.sh — experimentos sobre el banco de la tesis, en secuencia y de
# uno en uno (la máquina local tiene 15 GB; ver EXP-008 §8, 2026-09-24).
#
#   ./scripts/cola_tesis.sh [--esperar PID]
#
# 1. EXP-013  calibración frente a la tesis        (docs/experiments/EXP-013 §3)
# 2. EXP-014  parte 2, A/B de --symmetry sobre S     (docs/experiments/EXP-014 §3.2)
# 3. EXP-015  A/B de vivifyactivity (VSA)            (docs/experiments/EXP-015 §3)
#
# Cada paso usa exactamente el comando de su preregistro y es idempotente
# dentro de esta máquina: los A/B se reanudan con --resume; EXP-013 se omite
# si local.csv ya está completo (si se cortó a medias, se repite entero).
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
log() { echo "== $(date -u +%FT%TZ) $*"; }
filas() { [ -f "$1" ] && echo $(( $(wc -l < "$1") - 1 )) || echo 0; }

if [ "${1:-}" = "--esperar" ]; then
  log "esperando a que termine el PID $2"
  while kill -0 "$2" 2>/dev/null; do sleep 60; done
fi

log "EXP-013: calibración"
if [ "$(filas results/exp013/local.csv)" -lt 54 ]; then
  python3 scripts/run_experiment.py --solver solver/kissat/build/kissat \
      --bench bench/tesis-calib --out results/exp013/local.csv \
      --timeout 800 --seeds 42 --label labesat-defecto --jobs 1
fi
python3 scripts/exp013_calibracion.py analizar > results/exp013/informe.txt 2>&1

log "EXP-014 parte 2"
[ -f results/exp014/instancias.txt ] || python3 scripts/exp014_simetrias.py seleccionar
extra=(); [ -f results/exp014/A.meta.json ] && extra=(--resume)
python3 scripts/run_ab_interleaved.py --solver solver/labesat \
    --bench bench/tesis-dev --instances results/exp014/instancias.txt \
    --out-a results/exp014/A.csv --out-b results/exp014/B.csv \
    --label-a A-sin-simetrias --label-b B-simetrias \
    --opts-a=--no-symmetry --opts-b=--symmetry \
    --guard solver/kissat/build/kissat --guard tools/satsuma \
    --timeout 300 --seeds 42 "${extra[@]}"
python3 scripts/exp014_simetrias.py analizar > results/exp014/informe.txt 2>&1

log "EXP-015: VSA"
extra=(); [ -f results/exp015/A.meta.json ] && extra=(--resume)
python3 scripts/run_ab_interleaved.py --solver solver/kissat/build-vsa/kissat \
    --bench bench/tesis-dev --instances results/exp015/instancias.txt \
    --out-a results/exp015/A.csv --out-b results/exp015/B.csv \
    --label-a A-base --label-b B-vsa --opts-b=--vivifyactivity=1 \
    --guard solver/kissat/build-vsa/kissat --timeout 300 --seeds 42,123 "${extra[@]}"
python3 scripts/par2.py results/exp015/A.csv results/exp015/B.csv --md > results/exp015/informe.md 2>&1
python3 scripts/analyze_speedup.py results/exp015/A.csv results/exp015/B.csv >> results/exp015/informe.md 2>&1
log "fin de la cola"
