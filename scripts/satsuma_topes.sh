#!/usr/bin/env bash
# satsuma_topes.sh — satsuma con los topes internos de kissat-mab-hypre
# (puestos 3.º a 6.º de 2026), para EXP-024 (M2, research/12 §3).
#
# Se usa como LABESAT_SATSUMA de solver/labesat: recibe los argumentos de
# siempre ('fix <cnf> ... --out-file ... [--proof-file ...]') y añade los
# topes.  Así el A/B no cambia solver/labesat, que EXP-023 vigila con --guard.
#   SATSUMA_BASE   binario de satsuma (por defecto tools/satsuma-mclique)
#   SATSUMA_TOPES  los topes (por defecto, los de kissat-mab-hypre)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
read -r -a TOPES <<< "${SATSUMA_TOPES:---component-limit 500000 --order-model-limit 750000 --dense-model-limit 20000000}"
exec "${SATSUMA_BASE:-$ROOT/tools/satsuma-mclique}" "$@" "${TOPES[@]}"
