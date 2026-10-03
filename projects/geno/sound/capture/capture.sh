#!/bin/sh
# Render Geno's SNES sounds from your own Super Mario RPG (USA) cartridge dump, through the game's own sound driver
# (README.md). Everything written is ROM-derived and stays outside the repo.
#   projects/geno/sound/capture/capture.sh            # state -> SPC image -> every battle sound -> Geno's set
#   KIND=event projects/geno/sound/capture/capture.sh # also the field sounds (event/, for the extras)
# Needs: Mesen2 2.1.1 (MESEN: its binary; default ~/games/smrpg/tools/mesen/Mesen.app/Contents/MacOS/Mesen), the renderer
# (spcrender/build.sh), and the repo's Python (numpy, soundfile). Paths: SMRPG_ROM, SMRPG_WORK, SMRPG_SFX (paths.py).
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../../.." && pwd)
PY=${PY:-$ROOT/.venv/bin/python}
ROM=${SMRPG_ROM:-$HOME/games/smrpg/smrpg_usa.sfc}
WORK=${SMRPG_WORK:-$HOME/games/smrpg/work}
MESEN=${MESEN:-$HOME/games/smrpg/tools/mesen/Mesen.app/Contents/MacOS/Mesen}
export SMRPG_ROM="$ROM" SMRPG_WORK="$WORK"
mkdir -p "$WORK/spc" "$WORK/shots"
# 1. the audio state: with no input the attract demo reaches a battle at about frame 3960; at 4100 the driver, the battle
#    sound set and the fixed samples are all in audio RAM, which drive.lua dumps (with the DSP registers and the SPC700)
sed "s#@SMRPG_WORK@#$WORK#" "$HERE/drive.lua" > "$WORK/drive.lua"
printf 'tag c\nshot 0\nstop 4110\ndumpspc 4100 %s/spc/f4100\n' "$WORK" > "$WORK/sched.txt"
#    The SNES's RAM powers on zeroed: Mesen2's default is random, which leaves the sound CPU at a different point at frame
#    4100 on every run, and some of those states don't render ("SPC emulation error": 3 of 3 fresh runs, 2026-10-02).
#    Zeroed, the dump is the same every run and renders.
"$MESEN" --testrunner "$ROM" "$WORK/drive.lua" --timeout=300 --snes.ramPowerOnState=AllZeros > "$WORK/mesen.log" 2>&1 || true
[ -f "$WORK/spc/f4100.aram" ] || { echo "capture.sh: Mesen wrote no dump (see $WORK/mesen.log)" >&2; exit 1; }
"$PY" -c "import sys; sys.path.insert(0, '$HERE'); import spcharness as S; open('$WORK/spc/f4100.spc', 'wb').write(S.build_spc('$WORK/spc/f4100'))"
# 2. every battle sound alone (the bank's timed-hit sounds read all/), then Geno's set, named like the Melee bank
KIND=battle "$PY" "$HERE/sweep.py" > "$WORK/sweep_battle.log"
[ "${KIND:-battle}" = event ] && KIND=event "$PY" "$HERE/sweep.py" > "$WORK/sweep_event.log"
"$PY" "$HERE/build_geno.py" > "$WORK/build_geno.log"
echo "rendered: ${SMRPG_SFX:-$HOME/games/smrpg/sfx}/all, geno/ (dry, wet, nosat, extra)"
