#!/usr/bin/env bash
#
# reanudar_experimentos.sh — lanza en secuencia los experimentos pendientes
# del 2026-09-23 (EXP-008, partes 1 y 2 de EXP-010 y EXP-011, y EXP-012).
#
# Pensado para correr ENTERO en una sola máquina, de un tirón. El diseño A/B
# intercalado (ADR-0003 §4b) asume que las dos ramas de una misma tanda se
# miden en la MISMA máquina: mezclar parejas medidas en equipos distintos
# reintroduce justo la deriva que el diseño intercalado existe para anular.
# Por eso, si una tanda se cortó en otra máquina (por ejemplo, en la sesión de
# nube anterior), este guion la EMPIEZA DE CERO en la máquina donde se lanza,
# no continúa parejas ajenas.
#
# Es idempotente DENTRO de una misma máquina: si se corta a mitad (Ctrl-C,
# apagón, lo que sea), se puede volver a lanzar tal cual y retoma con
# --resume donde se quedó, siempre que sea la misma máquina y los mismos
# binarios (la guarda de SHA-1 de run_ab_interleaved.py lo comprueba).
#
# Requisitos previos (una vez):
#   ./scripts/get_tools.sh && ./scripts/build.sh --clean
#   (comprobar que 'solver/kissat/build/kissat --id' == 'git rev-parse HEAD')
#
# Uso:
#   ./scripts/reanudar_experimentos.sh              # todo, en orden
#   ./scripts/reanudar_experimentos.sh --solo-exp008 # solo ese paso
#
# Pasos y qué preregistro sigue cada uno:
#   1. EXP-008 (docs/experiments/EXP-008-base-kissat-sc2026.md §7)
#   2. EXP-011 parte 1 (docs/experiments/EXP-011-mclique-presupuesto.md §3)
#   3. EXP-010 parte 2 (docs/experiments/EXP-010-mclique-mit.md §3)
#   4. EXP-011 parte 2 (docs/experiments/EXP-011-mclique-presupuesto.md §3)
#   5. EXP-012 (docs/experiments/EXP-012-equivalencia-integrada.md §3), con
#      el binario integrado recompilado en build-symm/
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

filas() { [ -f "$1" ] && echo $(( $(wc -l < "$1") - 1 )) || echo 0; }
log() { echo "== $(date -u +%FT%TZ) $*"; }

# ab <esperadas> <out-a> <out-b> <args de run_ab_interleaved.py...>
# Añade --resume solo si ya hay un meta.json (tanda empezada en ESTA máquina).
ab() {
  local n=$1 a=$2 b=$3; shift 3
  if [ "$(filas "$a")" -ge "$n" ] && [ "$(filas "$b")" -ge "$n" ]; then
    echo "   ya hecho: $a ($n parejas)"; return 0
  fi
  local extra=(); [ -f "${a%.csv}.meta.json" ] && extra=(--resume)
  python3 scripts/run_ab_interleaved.py "$@" --out-a "$a" --out-b "$b" "${extra[@]}"
}

paso_exp008() {
  log "EXP-008: Kissat 4.0.4 frente a sc2026 (D-013)"
  [ -x tools/kissat-sc2026 ] || { echo "falta tools/kissat-sc2026: ./scripts/get_tools.sh"; return 1; }
  ab 120 results/exp008/A.csv results/exp008/B.csv \
    --solver solver/kissat/build/kissat --solver-b tools/kissat-sc2026 \
    --bench bench/calib bench/calib2 \
    --label-a A-kissat404 --label-b B-kissat-sc2026 --timeout 180 --seeds 1,2
}

paso_exp011_parte1() {
  log "EXP-011 parte 1: satsuma solo, mclique v1 frente a v2"
  [ -x tools/satsuma-mclique-v1 ] || { echo "falta tools/satsuma-mclique-v1 (D-005/EXP-010)"; return 1; }
  mkdir -p results/exp011
  if [ "$(filas results/exp011/satsuma.csv)" -lt 296 ]; then
    local args=(--bench bench/symm2026 --build mit=tools/satsuma \
      --build mclique1=tools/satsuma-mclique-v1 --build mclique2=tools/satsuma-mclique \
      --out results/exp011/satsuma.csv)
    if [ -x /tmp/satsuma-cliques/build/satsuma ]; then
      args+=(--build cliques=/tmp/satsuma-cliques/build/satsuma)
      echo "   (con el build de referencia con cliquer, research/03)"
    else
      echo "   AVISO: sin el build de referencia con cliquer en /tmp; se compara solo mit/mclique1/mclique2"
    fi
    nice -n 5 python3 scripts/compare_satsuma_builds.py "${args[@]}"
  else
    echo "   ya hecho: results/exp011/satsuma.csv"
  fi
}

paso_exp010_parte2() {
  log "EXP-010 parte 2: kissat con mclique v1 en las instancias que cambian"
  [ -f results/exp010/instancias.txt ] || { echo "falta results/exp010/instancias.txt (parte 1 de EXP-010)"; return 1; }
  local n10=$(( $(grep -cv '^#' results/exp010/instancias.txt) * 2 ))
  ab "$n10" results/exp010/A.csv results/exp010/B.csv \
    --solver solver/labesat --bench bench/symm2026 --instances results/exp010/instancias.txt \
    --opts-a=--symmetry --opts-b=--symmetry \
    --env-a "LABESAT_SATSUMA=$ROOT/tools/satsuma" \
    --env-b "LABESAT_SATSUMA=$ROOT/tools/satsuma-mclique-v1" \
    --guard solver/kissat/build/kissat --guard tools/satsuma --guard tools/satsuma-mclique-v1 \
    --label-a A-sin-cliques --label-b B-mclique --timeout 180 --seeds 1,2
  [ -f results/exp010/seguridad.csv ] || LABESAT_SATSUMA="$ROOT/tools/satsuma-mclique-v1" \
    python3 scripts/verify_symm_answers.py results/exp010/B.csv --bench bench/symm2026 \
    --out results/exp010/seguridad.csv
}

paso_exp011_parte2() {
  log "EXP-011 parte 2: kissat con mclique v2 en las instancias que cambian"
  python3 scripts/analyze_exp011.py --write-list >/dev/null
  local n11=$(( $(grep -cv '^#' results/exp011/instancias.txt) * 2 ))
  if [ "$n11" -eq 0 ]; then echo "   sin instancias que cambien: nada que correr"; return 0; fi
  ab "$n11" results/exp011/A.csv results/exp011/B.csv \
    --solver solver/labesat --bench bench/symm2026 --instances results/exp011/instancias.txt \
    --opts-a=--symmetry --opts-b=--symmetry \
    --env-a "LABESAT_SATSUMA=$ROOT/tools/satsuma" \
    --env-b "LABESAT_SATSUMA=$ROOT/tools/satsuma-mclique" \
    --guard solver/kissat/build/kissat --guard tools/satsuma --guard tools/satsuma-mclique \
    --label-a A-sin-cliques --label-b B-mclique2 --timeout 180 --seeds 1,2
  [ -f results/exp011/seguridad.csv ] || LABESAT_SATSUMA="$ROOT/tools/satsuma-mclique" \
    python3 scripts/verify_symm_answers.py results/exp011/B.csv --bench bench/symm2026 \
    --out results/exp011/seguridad.csv
}

paso_exp012() {
  log "EXP-012: equivalencia de kissat --symmetry con la tubería"
  if [ ! -x solver/kissat/build-symm/kissat ]; then
    ./scripts/build.sh --dir=build-symm --symmetry --clean || return 1
  fi
  local esperadas=$(( $(find bench/symm2026 -name '*.cnf*' | wc -l) ))
  if [ "$(filas results/exp012/equivalencia.csv)" -ge "$esperadas" ]; then
    echo "   ya hecho: results/exp012/equivalencia.csv"; return 0
  fi
  mkdir -p results/exp012
  python3 scripts/compare_integrada.py --bench bench/symm2026 \
    --integrado solver/kissat/build-symm/kissat --kissat solver/kissat/build/kissat \
    --conflicts 100000 --out results/exp012/equivalencia.csv
}

case "${1:-}" in
  --solo-exp008)        paso_exp008 ;;
  --solo-exp011-parte1) paso_exp011_parte1 ;;
  --solo-exp010-parte2) paso_exp010_parte2 ;;
  --solo-exp011-parte2) paso_exp011_parte2 ;;
  --solo-exp012)        paso_exp012 ;;
  "")
    paso_exp008        || exit 1
    paso_exp011_parte1 || exit 1
    paso_exp010_parte2 || exit 1
    paso_exp011_parte2 || exit 1
    paso_exp012        || exit 1
    log "fin: todos los pasos completados"
    echo ""
    echo "Analiza con:"
    echo "  python3 scripts/par2.py results/exp008/A.csv results/exp008/B.csv"
    echo "  python3 scripts/analyze_speedup.py results/exp008/A.csv results/exp008/B.csv"
    echo "  python3 scripts/analyze_exp010.py --write-list"
    echo "  python3 scripts/analyze_exp011.py --write-list"
    echo "  (EXP-012 ya analizado arriba: results/exp012/equivalencia.csv)"
    ;;
  *) echo "uso: $0 [--solo-exp008|--solo-exp011-parte1|--solo-exp010-parte2|--solo-exp011-parte2|--solo-exp012]" >&2; exit 1 ;;
esac
