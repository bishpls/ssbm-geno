#!/bin/bash
# M3's in-game renders and checks, in one pass (the decomp and disc are the sandbox's): greybox and production at two
# framings, the close-ups, the edge lab, the starter lab and the reel. Outputs in $MELEE_WORK/stage/final and lab/.
set -e
cd "$(dirname "$0")/../../../.."
eval "$(sh tools/machinima/melee/sandbox.sh geno-stage)"
W=$MELEE_WORK/stage; R=$W/runs; F=$W/final; mkdir -p $F
PROD=$W/out/GrFm.dat; GREY=$W/out/GrFm_greybox.dat
dol() { DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol "$@" --timeout 900 --quiet | tail -1; }
clean() { find "$1" -name 'f[0-9][0-9][0-9][0-9][0-9].png' -delete; }
for X in 25 55; do
  REF_STAGE=forest_maze REF_X=$X .venv/bin/python tools/machinima/melee/build.py projects/geno/stage ref_lab | tail -1
  for art in prod grey; do
    [ $art = prod ] && cp $PROD $MELEE_DISC/files/GrFm.dat || cp $GREY $MELEE_DISC/files/GrFm.dat
    rm -rf $R/ref_${art}_$X; dol $R/ref_${art}_$X --frames 110 --res 1
    cp $R/ref_${art}_$X/f00095.png $F/match_${art}_x$X.png; clean $R/ref_${art}_$X
  done
done
.venv/bin/python tools/machinima/melee/build.py projects/geno/stage icon_lab | tail -1
for art in prod grey; do
  [ $art = prod ] && cp $PROD $MELEE_DISC/files/GrFm.dat || cp $GREY $MELEE_DISC/files/GrFm.dat
  rm -rf $R/icon_$art; dol $R/icon_$art --frames 125 --res 2
  cp $R/icon_$art/f00028.png $F/hero_$art.png; cp $R/icon_$art/f00068.png $F/ledge_$art.png; cp $R/icon_$art/f00108.png $F/cap_$art.png
  clean $R/icon_$art
done
cp $PROD $MELEE_DISC/files/GrFm.dat
.venv/bin/python tools/machinima/melee/build.py projects/geno/stage edge_lab | tail -1
rm -rf $R/edge; dol $R/edge --frames 135 --res 2
.venv/bin/python projects/geno/stage/director/edge_lab.py --report $R/edge $W/lab/edge.json | grep '"ok"'
cp $R/edge/f00058.png $F/edge_floor.png; cp $R/edge/f00118.png $F/edge_cap.png; clean $R/edge
STAGE_LAB_SERIES=600 bash projects/geno/stage/director/run_starters.sh forest_maze | grep -v '^{'
.venv/bin/python tools/machinima/melee/build.py projects/geno/stage reel_lab | tail -1
rm -rf $R/reel; dol $R/reel --frames 1260 --res 2
projects/geno/stage/director/mux_reel.sh $R/reel $F/reel_production.mp4
cp $R/reel/f00600.png $F/reel_f600.png; clean $R/reel
echo BATCH DONE
