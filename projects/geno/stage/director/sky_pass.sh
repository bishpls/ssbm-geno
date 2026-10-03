#!/bin/bash
# One render -> measure pass of the Forest Maze's sky: builds the stage at real speed and with every clock 24x faster
# (SKY_TIME_SCALE=24: 620 frames then cover the longest cloud cycle, 240 s, and several shooting stars), and renders:
#   hero_lab (t7's camera by its horizon, the close-ups, the earlier 23-degree camera), ref_lab x25 and x55 stills,
#   the full cycle at x25 and x55 (the fast build, fighters standing) -> readability for every frame,
#   flash_lab at real speed for 30 s (sky and treeline only) -> the largest per-frame change per region;
# Battlefield's and Final Destination's flash captures (10 s) and art pass 2's "before" stills are made once and kept.
#   projects/geno/stage/director/sky_pass.sh TAG      -> $MELEE_WORK/stage/sky/TAG/{board.jpg,metrics.json,...}
set -e
cd "$(dirname "$0")/../../../.."
eval "$(sh tools/machinima/melee/sandbox.sh geno-stage)"
TAG=$1; W=$MELEE_WORK/stage; R=$W/runs; P=$W/sky/$TAG; B=$W/sky/before; mkdir -p "$P" "$B"
PY=.venv/bin/python
dol() { DOLPHIN_SLOTS=2 $PY tools/machinima/dolphin.py run "$MELEE_DISC/sys/main.dol" "$@" --timeout 1500 --quiet | tail -1 >/dev/null; }
clean() { find "$1" -name 'f[0-9][0-9][0-9][0-9][0-9].png' -delete; }
lab() { $PY tools/machinima/melee/build.py projects/geno/stage "$1" | tail -1 >/dev/null; }
hero() {   # $1 GrFm, $2 out dir
  cp "$1" "$MELEE_DISC/files/GrFm.dat"; lab hero_lab
  rm -rf "$R/hero_sky"; dol "$R/hero_sky" --frames 200 --res 2 --widescreen
  for s in hero:28 base:68 ledge:108 cap:148 hero23:188; do n=${s#*:}; cp "$R/hero_sky/f$(printf %05d $n).png" "$2/${s%:*}.png"; done
  clean "$R/hero_sky"
  for X in 25 55; do REF_STAGE=forest_maze REF_X=$X lab ref_lab; rm -rf "$R/ref_sky"; dol "$R/ref_sky" --frames 110 --res 1
    cp "$R/ref_sky/f00095.png" "$2/match_x$X.png"; clean "$R/ref_sky"; done
}
projects/geno/stage/build_stage.sh "$W/out/GrFm_$TAG.dat" | grep BUDGET | tee "$P/budget.txt"
SKY_TIME_SCALE=24 SPEC_TAG=_fast projects/geno/stage/build_stage.sh "$W/out/GrFm_${TAG}_fast.dat" | grep BUDGET >/dev/null
[ -f "$B/hero.png" ] || hero "$W/out/GrFm_p8.dat" "$B"
hero "$W/out/GrFm_$TAG.dat" "$P"
# the full cycle, fast clocks, at both match framings
cp "$W/out/GrFm_${TAG}_fast.dat" "$MELEE_DISC/files/GrFm.dat"
for X in 25 55; do
  REF_STAGE=forest_maze REF_X=$X REF_N=740 lab ref_lab; rm -rf "$R/cyc_$X"; dol "$R/cyc_$X" --frames 730 --res 1
  $PY projects/geno/stage/sky_measure.py readability "$P/cycle_x$X.json" "$R/cyc_$X" 100 730
  cp "$R/cyc_$X/f00400.png" "$P/cycle_x${X}_f400.png"; clean "$R/cyc_$X"
done
# flash at real speed (the Forest Maze's first shooting star is ~22 s in); Battlefield's and Final Destination's once
cp "$W/out/GrFm_$TAG.dat" "$MELEE_DISC/files/GrFm.dat"
FLASH_STAGE=forest_maze FLASH_N=1800 lab flash_lab; rm -rf "$R/flash_fm"; dol "$R/flash_fm" --frames 1800 --res 1
$PY projects/geno/stage/sky_measure.py flash "$P/flash.json" "$R/flash_fm" 60 1800
cp "$R/flash_fm/f00900.png" "$P/flash_view.png"; clean "$R/flash_fm"
for S in battlefield final_destination; do
  [ -f "$W/sky/flash_$S.json" ] && continue
  FLASH_STAGE=$S FLASH_N=660 lab flash_lab; rm -rf "$R/flash_$S"; dol "$R/flash_$S" --frames 660 --res 1
  $PY projects/geno/stage/sky_measure.py flash "$W/sky/flash_$S.json" "$R/flash_$S" 60 660; cp "$R/flash_$S/f00300.png" "$W/sky/flash_view_$S.png"; clean "$R/flash_$S"
done
$PY projects/geno/stage/sky_board.py "$P"
