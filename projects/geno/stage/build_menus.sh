#!/bin/sh
# The Forest Maze in the stage select: its icon, its name and its hologram, in MnSlMap.usd and SdMenu.usd (SCOPE.md,
# "Stage select"), into $MELEE_WORK/stage/out, where install.sh copies them from. Run after build_stage.sh (it reads the
# stage's spec for the hologram).
#   projects/geno/stage/build_menus.sh [ICON_RENDER.png]
# ICON_RENDER is an in-game render of the finished stage (director/icon_lab.py, its hero frame 28 at --res 2); without it
# the icon is drawn from the spec in the greybox colours (a placeholder). The name's small line is copied from a vanilla
# name, so it matches the others.
set -eu
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
PY=${PY:-$ROOT/.venv/bin/python}
DK=$ROOT/tools/machinima/melee/datkit.sh
W=${MELEE_WORK:-$HOME/games/melee/work}/stage
VAN=${VANILLA_FILES:-${MELEE_DISC:-$HOME/games/melee/disc}/files}   # vanilla MnSlMap.usd / SdMenu.usd (copies, once installed)
mkdir -p "$W/out" "$W/sss"
"$DK" mdump "$VAN/MnSlMap.usd" MnSelectStageDataTable:StageNameModel "$W/sss/name" 2 > /dev/null
"$PY" "$ROOT/projects/geno/stage/menu_art.py" "$W/menuart" "$W/sss/name/j2_m0_ta0_000.png" ${1:+"$1"}
"$DK" menus-stage "$W/menuart" "$W/forest_maze.spec.json" "$VAN/MnSlMap.usd" "$W/out/MnSlMap.usd" "$VAN/SdMenu.usd" "$W/out/SdMenu.usd" | tail -1
