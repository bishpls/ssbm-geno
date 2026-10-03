#!/bin/bash
# One render -> measure pass of the Forest Maze's art (pass 2): build the stage file and the play-plane-only edge build,
# render hero_lab (t7's camera and three close-ups, widescreen), ref_lab at x 25 and 55 (the match framings, with
# fighters) and edge_lab, then art_board.py measures and boards it against t7 and M3. Frame dumps are deleted.
#   projects/geno/stage/director/art_pass.sh TAG        -> $MELEE_WORK/stage/passes/TAG/{board.jpg,metrics.json,...}
set -e
cd "$(dirname "$0")/../../../.."
eval "$(sh tools/machinima/melee/sandbox.sh geno-stage)"
TAG=$1; W=$MELEE_WORK/stage; R=$W/runs; P=$W/passes/$TAG; mkdir -p "$P"
dol() { DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run "$MELEE_DISC/sys/main.dol" "$@" --timeout 900 --quiet | tail -1 >/dev/null; }
clean() { find "$1" -name 'f[0-9][0-9][0-9][0-9][0-9].png' -delete; }
projects/geno/stage/build_stage.sh "$W/out/GrFm_$TAG.dat" | grep BUDGET | tee "$P/budget.txt"
cp "$W/forest_mesh.json" "$P/forest_mesh_stats.json" 2>/dev/null || true
FOREST_BACK=0 SPEC_TAG=_edge projects/geno/stage/build_stage.sh "$W/out/GrFm_${TAG}_edge.dat" >/dev/null
cp "$W/out/GrFm_$TAG.dat" "$MELEE_DISC/files/GrFm.dat"
.venv/bin/python tools/machinima/melee/build.py projects/geno/stage hero_lab | tail -1 >/dev/null
rm -rf "$R/hero_$TAG"; dol "$R/hero_$TAG" --frames 160 --res 2 --widescreen
for s in hero:28 base:68 ledge:108 cap:148; do cp "$R/hero_$TAG/f00${s#*:}.png" "$P/${s%:*}.png" 2>/dev/null || cp "$R/hero_$TAG/f000${s#*:}.png" "$P/${s%:*}.png"; done
clean "$R/hero_$TAG"
for X in 25 55; do
  REF_STAGE=forest_maze REF_X=$X .venv/bin/python tools/machinima/melee/build.py projects/geno/stage ref_lab | tail -1 >/dev/null
  rm -rf "$R/ref_${TAG}_$X"; dol "$R/ref_${TAG}_$X" --frames 110 --res 1
  cp "$R/ref_${TAG}_$X/f00095.png" "$P/match_x$X.png"; clean "$R/ref_${TAG}_$X"
done
cp "$W/out/GrFm_${TAG}_edge.dat" "$MELEE_DISC/files/GrFm.dat"
STAGE_ART=forest2 .venv/bin/python tools/machinima/melee/build.py projects/geno/stage edge_lab | tail -1 >/dev/null
rm -rf "$R/edge_$TAG"; dol "$R/edge_$TAG" --frames 135 --res 2
STAGE_ART=forest2 .venv/bin/python projects/geno/stage/director/edge_lab.py --report "$R/edge_$TAG" "$P/edge.json" >/dev/null
cp "$R/edge_$TAG/f00058.png" "$P/edge_floor.png"; cp "$R/edge_$TAG/f00118.png" "$P/edge_cap.png"; clean "$R/edge_$TAG"
cp "$W/out/GrFm_$TAG.dat" "$MELEE_DISC/files/GrFm.dat"
.venv/bin/python projects/geno/stage/art_board.py "$P"
