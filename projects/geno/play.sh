#!/bin/sh
# Play Geno by hand: build the hand-play game (VS mode, everything unlocked, no scripted input) and open Dolphin on it with
# its own profile (~/games/dolphin-play), separate from the labs' pinned one. Set your controller once in Dolphin:
# Controllers > Port 1 > Standard Controller > Configure (a USB pad shows up as an SDL device), or "GameCube Adapter
# for Wii U" for Nintendo's adapter.
#   projects/geno/play.sh              # plain
#   GENO_COLL=1 projects/geno/play.sh  # hitboxes and hurtboxes shown (2: the capsules only)
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PY=${PY:-$ROOT/.venv/bin/python}
MW=${MELEE_WORK:-$HOME/games/melee/work}
DISC=${MELEE_DISC:-$HOME/games/melee/disc}
PROFILE=$HOME/games/dolphin-play
# his fighter files (PlGe.dat, PlGeAJ.dat, a PlGe<Cc>.dat per costume) and his results-screen poses; the disc's old
# costume files go first, so a build with fewer costumes (the blocky rig has one) never sits beside stale ones
rm -f "$DISC"/files/PlGe[A-Z][a-z].dat
cp "$MW"/rig/out/PlGe*.dat "$MW"/rig/out/GmRstMGe.dat "$DISC/files/"
# his victory fanfare (our arrangement, built locally: ~/games/melee/work/music/fanfare; the game falls back to Mario's)
[ -f "$MW/music/fanfare/ff_geno.hps" ] && cp "$MW/music/fanfare/ff_geno.hps" "$DISC/files/audio/"
# his effect file (EfGeData.dat, built from projects/geno/fx/efge.py; without it the game plays the borrowed effects)
MELEE_DISC="$DISC" MELEE_WORK="$MW" "$PY" "$ROOT/projects/geno/fx/efge.py" --install >/dev/null
# the Forest Maze stage's files (built locally into $MW/stage; the DOL expects them once the stage is merged)
[ -f "$MW/stage/out/GrFm.dat" ] && MELEE_DISC="$DISC" MELEE_WORK="$MW" sh "$ROOT/projects/geno/stage/install.sh" >/dev/null
"$PY" "$ROOT/tools/machinima/melee/build.py" "$ROOT/projects/geno" play | tail -1
if [ ! -f "$PROFILE/Config/Dolphin.ini" ]; then
    mkdir -p "$PROFILE/Config"
    printf '[Core]\nCPUThread = True\nSlotA = 255\nSlotB = 255\nSIDevice0 = 6\nSIDevice1 = 6\n[Interface]\nConfirmStop = False\n[Movie]\nDumpFrames = False\n' > "$PROFILE/Config/Dolphin.ini"
fi
if [ ! -f "$PROFILE/Config/Logger.ini" ]; then   # the game's reports and panic alerts go to $PROFILE/Logs/dolphin.log
    printf '[Options]\nWriteToFile = True\nWriteToConsole = False\nVerbosity = 3\n[Logs]\nOSREPORT = True\nOSREPORT_HLE = True\nMASTER = True\nVIDEO = True\n' > "$PROFILE/Config/Logger.ini"
fi
exec /Applications/Dolphin.app/Contents/MacOS/Dolphin -u "$PROFILE" -e "$DISC/sys/main.dol"
