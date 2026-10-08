#!/usr/bin/env python3
"""
b4_parche_labesat.py — B4 (research/11) en solver/labesat, detrás de
--symmetry-policy=estructural (LABESAT_SYMM_POLICY; por defecto 'siempre').

PENDIENTE: NO aplicar mientras corre EXP-023, porque su A/B vigila el SHA-1 de
solver/labesat (--guard) y abortaría la tanda.  Al cerrarlo:

    python3 scripts/b4_parche_labesat.py solver/labesat

Probado sobre una copia (2026-10-04): con estructura (php_9_9,
php9x9_rand160u) usa la salida de satsuma y dsr-trim verifica la prueba SR;
sin ella (rand3) resuelve la CNF original con prueba DRAT verificada.
satsuma sin --silent da la misma CNF y la misma prueba que con --silent.
"""
import sys
p = sys.argv[1]
s = open(p).read()
def rep(old, new):
    global s
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)
rep('''#   LABESAT_KISSAT_ARGS       argumentos extra para kissat             ("")''',
'''#   LABESAT_SYMM_POLICY       con --symmetry, qué hacer con la salida de
#                             satsuma: 'siempre' la usa; 'estructural'
#                             (B4, research/11, EXP-023) solo si satsuma
#                             encontró estructura combinatoria (R); si no,
#                             resuelve la CNF original.  También con
#                             --symmetry-policy=P                ('siempre')
#   LABESAT_KISSAT_ARGS       argumentos extra para kissat             ("")''')
rep('''DELAY="${LABESAT_SYMM_DELAY:-0}"''', '''DELAY="${LABESAT_SYMM_DELAY:-0}"
POLICY="${LABESAT_SYMM_POLICY:-siempre}"''')
rep('''        --symmetry-delay=*) DELAY="${1#--symmetry-delay=}" ;;''',
'''        --symmetry-delay=*) DELAY="${1#--symmetry-delay=}" ;;
        --symmetry-policy=*) POLICY="${1#--symmetry-policy=}" ;;''')
rep('''sargs=(fix "$INPUT" --silent --full-skip-limit 100000000 --add-reduced-as-unit
       --bsr --out-file "$SB")''', '''# Con la política estructural (B4) hacen falta las estadísticas de satsuma:
# sin --silent, que no cambia ni la CNF ni la prueba (comprobado).
SILENT=(--silent)
[ "$POLICY" = estructural ] && SILENT=()
sargs=(fix "$INPUT" "${SILENT[@]}" --full-skip-limit 100000000 --add-reduced-as-unit
       --bsr --out-file "$SB")''')
rep(''') </dev/null >/dev/null 2>&1
st=$?''', ''') </dev/null >"$TMP/satsuma.log" 2>&1
st=$?''')
rep('''    KARGS+=("--time=$left")
fi
''', '''    KARGS+=("--time=$left")
    TIME="$left"   # si B4 descarta la salida, run_plain usa lo que queda
fi

# B4 (research/11): R = row_column > 0 o johnson > 0 o orbitopal_units > 0
# o symmetry_units >= 100, con las estadísticas que imprime satsuma.
if [ "$POLICY" = estructural ]; then
    rasgos=$(sed 's/\\x1b\\[[0-9;]*m//g' "$TMP/satsuma.log" | awk '
        /^c[ \\t]+row_column[ \\t]*=/      { rc = $4 }
        /^c[ \\t]+johnson[ \\t]*=/         { jo = $4 }
        /^c[ \\t]+symmetry_units[ \\t]*=/  { su = $4; ou = $7; gsub(/[^0-9]/, "", ou) }
        END { printf "%d %d %d %d", rc, jo, ou, su }')
    read -r rc jo ou su <<< "$rasgos"
    if [ "$rc" -gt 0 ] || [ "$jo" -gt 0 ] || [ "$ou" -gt 0 ] || [ "$su" -ge 100 ]; then
        say "B4: estructura (row_column $rc, johnson $jo, orbitopal $ou, units $su): se usa satsuma"
    else
        run_plain "B4: sin estructura (row_column $rc, johnson $jo, orbitopal $ou, units $su)"
    fi
fi
''')
open(p, 'w').write(s)
print("B4 aplicado a", p)
