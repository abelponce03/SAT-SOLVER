#!/usr/bin/env bash
#
# fetch_competition_data.sh — descarga los datos oficiales de la SAT Competition
# y los metadatos de la Global Benchmark Database.
#
# Esto es lo que convierte el proyecto en empírico desde el minuto cero: con los
# resultados instancia-por-instancia de la edición pasada se puede **estimar el
# techo de una idea antes de implementarla** (¿cuánto PAR-2 habría ganado?), en
# vez de discutirla en abstracto.
#
# Descarga (a data/competition/, ignorado por git — son ~30 MB regenerables):
#   scores_<año>.csv      resultado de cada solver en cada instancia (2026)
#   track_main_<año>.uri  los 400 hashes del Main Track
#   2025/main-*.tex       2025: curvas de cactus (no hay datos por instancia)
#   gbd.db                base de metadatos de GBD (familia, autor, resultado)
#
# Uso: ./scripts/fetch_competition_data.sh [año]
set -euo pipefail
YEAR="${1:-2026}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/data/competition"
mkdir -p "$OUT"

get() {  # get <url> <destino>
    if [ -s "$2" ]; then echo "   ya está: $(basename "$2")"; return; fi
    echo "   bajando $(basename "$2") ..."
    curl -sS --fail --max-time 300 -o "$2.part" "$1" && mv "$2.part" "$2"
}

echo "== Resultados oficiales SAT Competition $YEAR"
if [ "$YEAR" = 2025 ]; then
    # 2025 no publica resultados por instancia (ni scores.csv ni
    # detailed_results): solo las curvas de cactus de las diapositivas, que dan
    # resueltas y PAR-2 por solver, pero no qué instancia resolvió cada uno.
    # Se analizan con scripts/fuera_de_muestra_2025.py.
    RAW="https://raw.githubusercontent.com/satcompetition/2025/HEAD"
    mkdir -p "$OUT/2025"
    for k in ALL SAT UNSAT; do
        get "$RAW/slides/plots/main-$k.tex" "$OUT/2025/main-$k.tex"
    done
    get "$RAW/downloads/SC2025.uri" "$OUT/track_main_2025.uri"
else
    get "https://satcompetition.github.io/$YEAR/downloads/scores.csv"             "$OUT/scores_$YEAR.csv"
    get "https://satcompetition.github.io/$YEAR/downloads/track_main_$YEAR.uri"   "$OUT/track_main_$YEAR.uri"
fi

echo "== Metadatos de GBD (familia de cada instancia)"
get "https://benchmark-database.de/getdatabase" "$OUT/gbd.db"
get "https://benchmark-database.de/getdatabase/base" "$OUT/gbd_base.db"

echo ""
echo "Listo en $OUT. Analiza con:"
echo "   python3 scripts/analyze_competition.py ranking --year $YEAR"
