#!/usr/bin/env bash
#
# vendor_satsuma.sh — copia satsuma y dejavu (MIT), SIN MODIFICAR, en
# solver/satsuma/ para compilarlos dentro del binario de Kissat (D-016, fase 1;
# ADR-0007).  La competición compila sin red, así que el código tiene que ir en
# el paquete.
#
# Solo se copian los ficheros que hacen falta para compilar: las cabeceras y
# satsuma.cpp de satsuma, las cabeceras de dejavu y de tsl (robin-map, MIT), y
# las licencias.  Nada de tests, ejemplos ni ejecutables.
#
# Uso:
#   scripts/vendor_satsuma.sh           # (re)copia desde los commits fijados
#   scripts/vendor_satsuma.sh --check   # comprueba que solver/satsuma coincide
#                                       # byte a byte con el upstream (CI)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SATSUMA_URL=https://github.com/markusa4/satsuma.git
SATSUMA_REV=c6ad1b59f29fa32dae587ef369135735f40d498a
DEJAVU_URL=https://github.com/markusa4/dejavu.git
DEJAVU_REV=4c275e9ebac4fe51a26aac406682b9bcbfd03a9d
DEST="$ROOT/solver/satsuma"
MODE="${1:-copy}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fetch_rev() {
    git init --quiet "$1"
    git -C "$1" fetch --quiet --depth 1 "$2" "$3"
    git -C "$1" checkout --quiet FETCH_HEAD
}
fetch_rev "$TMP/satsuma" "$SATSUMA_URL" "$SATSUMA_REV"
fetch_rev "$TMP/dejavu" "$DEJAVU_URL" "$DEJAVU_REV"

# Árbol que se vendoriza, con la misma disposición que espera satsuma
# (src/dejavu/ y src/tsl/ junto a sus cabeceras).
STAGE="$TMP/stage"
mkdir -p "$STAGE/src/dejavu" "$STAGE/src/tsl"
cp "$TMP/satsuma/LICENSE" "$TMP/satsuma/README.md" "$STAGE/"
cp "$TMP/satsuma"/src/*.h "$TMP/satsuma/src/satsuma.cpp" "$STAGE/src/"
cp "$TMP/satsuma"/src/tsl/* "$STAGE/src/tsl/"
cp "$TMP/dejavu"/*.h "$TMP/dejavu/LICENSE" "$TMP/dejavu/README.md" "$STAGE/src/dejavu/"

if [ "$MODE" = "--check" ]; then
    # UPSTREAM.md es nuestro; lo demás tiene que ser idéntico.
    if diff -r -q -x UPSTREAM.md "$STAGE" "$DEST"; then
        echo "solver/satsuma coincide con satsuma ${SATSUMA_REV:0:7} + dejavu ${DEJAVU_REV:0:7}"
    else
        echo "ERROR: solver/satsuma difiere del upstream fijado" >&2; exit 1
    fi
    exit 0
fi

rm -rf "$DEST"
cp -r "$STAGE" "$DEST"
cat > "$DEST/UPSTREAM.md" <<EOT
# satsuma y dejavu vendorizados (sin modificar)

- **satsuma** (Markus Anders, MIT): \`$SATSUMA_URL\`, commit \`$SATSUMA_REV\`.
- **dejavu** (Markus Anders, MIT): \`$DEJAVU_URL\`, commit \`$DEJAVU_REV\`,
  en \`src/dejavu/\`.
- **tsl robin-map** (Thibaut Goetghebuer-Planchon, MIT): en \`src/tsl/\`, tal
  como lo trae satsuma.

Copiados por \`scripts/vendor_satsuma.sh\`. **No se modifica ningún fichero de
este directorio**: CI lo comprueba con \`scripts/vendor_satsuma.sh --check\`.
Solo se copian las cabeceras, \`satsuma.cpp\` y las licencias; ni tests, ni
ejemplos, ni ejecutables.

Se compila dentro del binario de Kissat con \`configure --symmetry\` a través de
\`solver/symmetry/satsuma_entry.cpp\` (ADR-0007). Sin \`--symmetry\`, este
directorio no se usa.

cliquer (GPLv2) **no** está aquí: satsuma se compila con \`CLIQUES=0\`, o con
mclique (\`solver/mclique\`, MIT) cuando se valide (D-005).
EOT
echo "vendorizado en solver/satsuma ($(find "$DEST" -type f | wc -l) ficheros)"
