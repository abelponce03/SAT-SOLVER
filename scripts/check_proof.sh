#!/usr/bin/env bash
#
# check_proof.sh — verifica una respuesta UNSAT comprobando la prueba DRAT.
#
# Un UNSAT no se puede verificar mirando la salida: hay que comprobar la prueba.
# La SAT Competition exige prueba DRAT para las UNSAT de la Main Track, así que
# cualquier parche nuestro que toque aprendizaje, vivification, eliminación de
# variables o inprocesado debe seguir produciendo pruebas válidas. Esto lo
# comprueba.
#
# Uso:
#   ./scripts/check_proof.sh <instancia.cnf> [solver]
#
# Requiere drat-trim: ./scripts/get_tools.sh lo descarga y compila en tools/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INSTANCE="${1:?falta la instancia}"
SOLVER="${2:-$ROOT/solver/kissat/build/kissat}"
DRAT="$ROOT/tools/drat-trim"

[ -x "$DRAT" ] || { echo "SALTADO: no está $DRAT (ejecuta ./scripts/get_tools.sh)"; exit 0; }

PROOF="$(mktemp -t proof.XXXXXX.drat)"
CNF="$INSTANCE"
# drat-trim necesita el CNF sin comprimir.
case "$INSTANCE" in
    *.xz) CNF="$(mktemp -t inst.XXXXXX.cnf)"; xz -dc "$INSTANCE" > "$CNF" ;;
    *.gz) CNF="$(mktemp -t inst.XXXXXX.cnf)"; gzip -dc "$INSTANCE" > "$CNF" ;;
esac
trap 'rm -f "$PROOF"; [ "$CNF" != "$INSTANCE" ] && rm -f "$CNF"' EXIT

set +e
"$SOLVER" -q -n "$CNF" "$PROOF" >/dev/null 2>&1
CODE=$?
set -e

case "$CODE" in
    20) ;;  # UNSAT: seguimos
    10) echo "SAT $INSTANCE (no aplica verificación de prueba)"; exit 0 ;;
    *)  echo "SIN RESOLVER $INSTANCE (código $CODE)"; exit 0 ;;
esac

if "$DRAT" "$CNF" "$PROOF" 2>/dev/null | grep -q "s VERIFIED"; then
    echo "OK    $INSTANCE: prueba DRAT verificada"
else
    echo "FALLO $INSTANCE: drat-trim NO verificó la prueba"
    exit 1
fi
