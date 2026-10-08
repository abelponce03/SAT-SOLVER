#!/usr/bin/env bash
#
# check_authorship.sh — la autoría en git es solo del desarrollador (ADR-0005).
#
# Revisa los commits del rango (por defecto, los que no están en origin/main):
#   - autor y committer no pueden ser una identidad de Claude o de Anthropic;
#   - el mensaje no puede llevar trailers de coautoría, «Generated with|by
#     Claude Code» ni enlaces de sesión de claude.ai.
# Mencionar CLAUDE.md u otras herramientas en el texto de un commit está
# permitido: es contenido, no autoría.
#
# Solo se revisan los commits hechos DESPUÉS de adoptar la norma
# (AUTORIA_DESDE).  Lo anterior es la decisión abierta D-001 del registro, y no
# debe poner CI en rojo mientras el director no la resuelva.
#
# Excepción (D-023, opción b, aprobada por el director el 2026-10-05): el
# mensaje de 4d55340, el squash del PR #49, lleva el pie que el servidor de la
# sesión añade a la descripción de los PR.  Solo se exime la revisión del
# MENSAJE de ese SHA exacto; su autor y su committer se siguen revisando.  No
# se añaden más excepciones sin una decisión nueva en el registro.
#
# Excepción (D-024, aprobada por el director el 2026-10-08): el mismo caso con
# 6450a05, el squash del PR #50.  Mismas condiciones que D-023.
#
# Uso: scripts/check_authorship.sh [RANGO]      (p. ej. origin/main..HEAD)
#      AUTORIA_DESDE="2026-09-23 12:00 +0000" scripts/check_authorship.sh
set -euo pipefail
RANGO="${1:-origin/main..HEAD}"
DESDE="${AUTORIA_DESDE:-2026-09-23 12:00:00 +0000}"
patron_id='(^|[^a-z])claude([^a-z.]|$)|anthropic'
exentos_msg='4d5534072e3b0a5a5033366b0ce4fc4a55336226 6450a050ccacf2b4155947f3ee8370afcbe154fd'   # D-023, D-024
patron_msg='^co-authored-by:.*(claude|anthropic)|generated (with|by) .*claude|claude\.ai/code/session|noreply@anthropic\.com'
fallos=0
while IFS=$'\t' read -r sha autor committer; do
    msg=$(git log -1 --format=%B "$sha")
    if grep -qiE "$patron_id" <<< "$autor $committer"; then
        echo "FALLO ${sha:0:7}: autoría '$autor' / '$committer'"; fallos=1
    fi
    if [[ " $exentos_msg " == *" $sha "* ]]; then
        echo "EXENTO ${sha:0:7}: mensaje no revisado (D-023, D-024)"
    elif grep -qiE "$patron_msg" <<< "$msg"; then
        echo "FALLO ${sha:0:7}: atribución en el mensaje:"
        grep -iE "$patron_msg" <<< "$msg" | sed 's/^/        /'
        fallos=1
    fi
done < <(git log --since="$DESDE" --format=$'%H\t%an <%ae>\t%cn <%ce>' "$RANGO")
n=$(git rev-list --count --since="$DESDE" "$RANGO")
[ $fallos = 0 ] && echo "autoría OK en $n commits ($RANGO)" || echo "autoría: HAY FALLOS (ADR-0005)"
exit $fallos
