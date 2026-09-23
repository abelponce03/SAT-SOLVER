#!/bin/sh
script=`basename $0`
die () {
  echo "$script: error: $*" 1>&2
  exit 1
}
[ -f makefile ] || die "no 'makefile' (run './configure' first)"
CC="`sed -e '/^CC/!d' -e 's,^CC=,,' makefile`"
[ "$CC" = "" ] && die "could not get 'CC' from makefile"
case "$CC" in
  gcc*|clang*)
    CFLAGS="`echo $CC|sed -e 's,^[^ ]* ,,'`"
    CC="`echo $CC|awk '{print \$1}'`"
    CC="`$CC --version 2>/dev/null|head -1`"
    ;;
esac
COMPILER="$CC $CFLAGS"
VERSION="`cat ../VERSION 2>/dev/null`"
[ "$VERSION" = "" ] && die "could not get 'VERSION'"
cat <<EOF
#define VERSION "$VERSION"
#define COMPILER "$COMPILER"
EOF
#START-CUT-OUT-ID
# [SOLVER] Kissat solo buscaba '.git' en el directorio actual y en el padre.
# Vendorizado con 'git subtree' dentro de LabeSAT, el '.git' está tres niveles
# más arriba y el binario salía como 'unknown'.  'git rev-parse' encuentra el
# repositorio desde cualquier punto del árbol, de modo que cada binario lleva
# el commit exacto del que sale -- imprescindible para reproducir una medición.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1
then
  ID="`git rev-parse HEAD 2>/dev/null`"
  [ "$ID" = "" ] && die "could not get git id with 'git rev-parse'"
else
  ID=unknown
fi
#END-CUT-OUT-ID
cat <<EOF
#define ID "$ID"
EOF
LC_TIME="en_US"
export LC_TIME
DATE="`date 2>/dev/null|sed -e 's,  *, ,g'`"
OS="`uname -srmn 2>/dev/null`"
BUILD="`echo $DATE $OS|sed -e 's,^ *,,' -e 's, *$,,'`"
cat << EOF
#define BUILD "$BUILD"
EOF
DIR="`pwd`"
cat <<EOF
#define DIR "$DIR"
EOF
