#!/bin/sh
# Install the Forest Maze's game files into a disc (MELEE_DISC; default the main disc, so point it at a sandbox to test):
# the stage (GrFm.dat), the stage select (MnSlMap.usd), the menu text (SdMenu.usd) and the music (audio/gr_forestmaze.hps).
# They're built locally (never in git): stage_spec.py + datkit stage-build, menu_art.py + datkit menus-stage, music.py build.
# The decomp side (the stage code and the menus) comes with the geno-stage branch; a disc without these files would show
# a broken slot, so install them together with that DOL.
set -e
W=${MELEE_WORK:-$HOME/games/melee/work}/stage
DISC=${MELEE_DISC:-$HOME/games/melee/disc}
cp "$W/out/GrFm.dat" "$W/out/MnSlMap.usd" "$W/out/SdMenu.usd" "$DISC/files/"
cp "$W/music/gr_forestmaze.hps" "$DISC/files/audio/"
echo "installed the Forest Maze into $DISC"
