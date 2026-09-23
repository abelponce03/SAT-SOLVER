#!/usr/bin/env bash
#
# declaracion_ia.sh — cifras de la declaración obligatoria de la SAT Competition
# («Mandatory statement»), calculadas desde git y nunca escritas a mano.
# Plan Main Track, §5 (docs/plan/plan-main-track-2027.md).
#
# Informa de:
#   - la base: Kissat 4.0.4, commit upstream y líneas de C de la base;
#   - las líneas añadidas y eliminadas en Kissat, fichero a fichero, clasificadas
#     como ACTIVA (entra en la configuración de competición), INACTIVA
#     (detrás de una opción apagada por defecto) o DOC/BUILD;
#   - las líneas del guion solver/labesat;
#   - las líneas de mclique (solver/mclique), la clique máxima MIT de satsuma.
# Todo el código de LabeSAT lo escribe un asistente de IA bajo la dirección del
# autor (docs/metodologia/), así que «líneas de IA» = líneas cambiadas.
#
# Uso: scripts/declaracion_ia.sh [--markdown]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
BASE=730056d      # merge del subtree: Kissat 4.0.4 sin modificar (ADR-0002)
UPSTREAM=8af8e56  # commit upstream de rel-4.0.4

# Clasificación por fichero.  Si se añade un fichero nuevo, clasifícalo aquí:
# el script falla con los ficheros sin clasificar para que no se cuelen en la
# cifra equivocada.
clase() {
    case "$1" in
        solver/kissat/src/mode.c|solver/kissat/src/mode.h|\
        solver/kissat/src/modetrace.c|solver/kissat/src/modetrace.h|\
        solver/kissat/src/search.c|solver/kissat/src/options.h)
            echo INACTIVA ;;   # A4.1 (modeadaptive=0) y trazas (KISSAT_TRACE)
        solver/kissat/src/lucky.c|solver/kissat/src/terminate.h|\
        solver/kissat/src/application.c|solver/kissat/src/file.c|\
        solver/kissat/src/file.h|solver/kissat/src/build.c)
            echo ACTIVA ;;     # B3'' terminador, --append-proof, identidad del banner
        solver/kissat/UPSTREAM.md|solver/kissat/scripts/*)
            echo DOC/BUILD ;;
        *) echo SIN-CLASIFICAR ;;
    esac
}

base_lines=$(git ls-tree -r --name-only "$BASE" solver/kissat/src |
    grep -E '\.(c|h)$' | while read -r f; do git show "$BASE:$f"; done | wc -l)

declare -A add del
tot_add=0; tot_del=0; sin=0
while read -r a d f; do
    c=$(clase "$f")
    [ "$c" = SIN-CLASIFICAR ] && { echo "ERROR: fichero sin clasificar: $f" >&2; sin=1; }
    add[$c]=$(( ${add[$c]:-0} + a )); del[$c]=$(( ${del[$c]:-0} + d ))
    tot_add=$((tot_add + a)); tot_del=$((tot_del + d))
    filas+="| \`${f#solver/kissat/}\` | $c | +$a | −$d |"$'\n'
done < <(git diff --numstat "$BASE" HEAD -- solver/kissat)
[ $sin = 0 ] || exit 1

guion=$(wc -l < solver/labesat)
# mclique: clique máxima MIT para satsuma (D-005).  Se cuenta aparte porque no
# es código de Kissat; las pruebas no entran en la cifra del solver.
mclique=$(cat solver/mclique/mclique.[ch] solver/mclique/satsuma/* | wc -l)
mclique_test=$(wc -l < solver/mclique/test_mclique.c)
c_add=$(( ${add[ACTIVA]:-0} + ${add[INACTIVA]:-0} ))
pct=$(awk -v a="$c_add" -v b="$base_lines" 'BEGIN{printf "%.1f", 100*a/b}')

cat <<EOF
## Cifras de la declaración (generado por scripts/declaracion_ia.sh, commit $(git rev-parse --short HEAD))

- **Base**: Kissat 4.0.4, upstream \`$UPSTREAM\`: **$base_lines** líneas de C (\`src/*.c,h\`).
- **Cambios en el código C de Kissat**: **+$c_add** líneas (${pct} % de la base):
  - activas en la configuración de competición: +${add[ACTIVA]:-0} / −${del[ACTIVA]:-0};
  - inactivas (opción apagada o trazas): +${add[INACTIVA]:-0} / −${del[INACTIVA]:-0}.
- **Documentación y build dentro de Kissat**: +${add[DOC/BUILD]:-0} / −${del[DOC/BUILD]:-0}.
- **Guion de la tubería** (\`solver/labesat\`): **$guion** líneas.
- **mclique** (\`solver/mclique\`, clique máxima para satsuma, D-005): **$mclique**
  líneas de C, más $mclique_test de pruebas. Solo entra en la entrega si EXP-010
  la valida.
- **Escritas por IA**: todas las anteriores (asistente de IA bajo la dirección del autor).
- **satsuma y dejavu**: se usan sin modificar (0 líneas). mclique ocupa el
  hueco de cliquer sin tocar satsuma.

| Fichero | Clase | Añadidas | Eliminadas |
|---|---|---:|---:|
$filas
EOF
