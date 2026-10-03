#!/bin/bash
# A quick sky iteration: build, the x25 and x55 stills with their readability, and (STAR=1) a test build that fires the
# first shooting star at 1.5 s, captured at the x55 framing at res 2 (frames 60-200 kept in $W/sky/TAG/star/).
set -e
cd "$(dirname "$0")/../../../.."
eval "$(sh tools/machinima/melee/sandbox.sh geno-stage)"
TAG=$1; W=$MELEE_WORK/stage; R=$W/runs; P=$W/sky/$TAG; mkdir -p "$P"; PY=.venv/bin/python
dol() { DOLPHIN_SLOTS=2 $PY tools/machinima/dolphin.py run "$MELEE_DISC/sys/main.dol" "$@" --timeout 900 --quiet | tail -1 >/dev/null; }
projects/geno/stage/build_stage.sh "$W/out/GrFm_$TAG.dat" | grep BUDGET
cp "$W/out/GrFm_$TAG.dat" "$MELEE_DISC/files/GrFm.dat"
for X in 25 55; do REF_STAGE=forest_maze REF_X=$X $PY tools/machinima/melee/build.py projects/geno/stage ref_lab | tail -1 >/dev/null
  rm -rf "$R/q_$X"; dol "$R/q_$X" --frames 110 --res 1; cp "$R/q_$X/f00095.png" "$P/match_x$X.png"; rm -rf "$R/q_$X"; done
$PY -c "
import sys; sys.path.insert(0, 'projects/geno/stage'); import lookmetrics as L
for X in (25, 55): m = L.metrics('$P/match_x%d.png' % X); print('x%d' % X, {k: m[k] for k in ('busy', 'contrast_vs_fighter', 'blend_frac', 'readability')})"
if [ "${STAR:-0}" = 1 ]; then
  STAR_T0=1.5 SPEC_TAG=_star projects/geno/stage/build_stage.sh "$W/out/GrFm_${TAG}_star.dat" >/dev/null
  cp "$W/out/GrFm_${TAG}_star.dat" "$MELEE_DISC/files/GrFm.dat"
  REF_STAGE=forest_maze REF_X=55 REF_N=220 $PY tools/machinima/melee/build.py projects/geno/stage ref_lab | tail -1 >/dev/null
  rm -rf "$R/q_star"; dol "$R/q_star" --frames 210 --res 2; mkdir -p "$P/star"; cp "$R/q_star"/f00[0-2][0-9][0-9].png "$P/star/" 2>/dev/null || true; rm -rf "$R/q_star"
  cp "$W/out/GrFm_$TAG.dat" "$MELEE_DISC/files/GrFm.dat"
fi
