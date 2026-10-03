#!/bin/bash
# after an art change: the hero and close-ups, both match framings and the reel, on the production file
set -e
cd "$(dirname "$0")/../../../.."
eval "$(sh tools/machinima/melee/sandbox.sh geno-stage)"
W=$MELEE_WORK/stage; R=$W/runs; F=$W/final
dol() { DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol "$@" --timeout 900 --quiet | tail -1; }
clean() { find "$1" -name 'f[0-9][0-9][0-9][0-9][0-9].png' -delete; }
cp $W/out/GrFm.dat $MELEE_DISC/files/GrFm.dat
.venv/bin/python tools/machinima/melee/build.py projects/geno/stage icon_lab | tail -1
rm -rf $R/icon_prod; dol $R/icon_prod --frames 125 --res 2
cp $R/icon_prod/f00028.png $F/hero_prod.png; cp $R/icon_prod/f00068.png $F/ledge_prod.png; cp $R/icon_prod/f00108.png $F/cap_prod.png; clean $R/icon_prod
for X in 25 55; do
  REF_STAGE=forest_maze REF_X=$X .venv/bin/python tools/machinima/melee/build.py projects/geno/stage ref_lab | tail -1
  rm -rf $R/ref_prod_$X; dol $R/ref_prod_$X --frames 110 --res 1; cp $R/ref_prod_$X/f00095.png $F/match_prod_x$X.png; clean $R/ref_prod_$X
done
.venv/bin/python tools/machinima/melee/build.py projects/geno/stage reel_lab | tail -1
rm -rf $R/reel; dol $R/reel --frames 1260 --res 2
projects/geno/stage/director/mux_reel.sh $R/reel $F/reel_production.mp4
cp $R/reel/f00600.png $F/reel_f600.png; clean $R/reel
echo BATCH2 DONE
