#!/bin/sh
# Geno's sound bank (bank 55: geno.ssm, 62 sounds) and both smash2.sem, end to end, from your own Super Mario RPG (USA)
# cartridge dump and your own Melee disc, then installed into the extracted disc (README.md has the chain and its sources).
#   projects/geno/sound/build_bank.sh            # MELEE_DISC, MELEE_WORK, SMRPG_ROM / SMRPG_SFX as elsewhere
# 1. the SNES sounds (capture/capture.sh), unless $SMRPG_SFX/geno/nosat already holds them
# 2. round 3: Geno's 28 SNES sounds cut and timed for Melee (rom_tools/build_sounds_rom.py), encoded into the bank
#    (rom_tools/build_bank.py, which reads the retail smash2.sem from the disc or its backup)
# 3. round 4: the 25 wooden movement sounds synthesized in code (synth.py's committed WAVs) appended
#    (rom_tools/build_bank4.py), installed (its out4/install.sh) so the next step reads it
# 4. SMRPG's timed-hit sounds (timed.py), the gun sounds fitted to their moves (gunfit.py), the crowd's "Ge-no! Ge-no!"
#    spliced from the disc's own chants (cheer/survey.py, cheer/candidates.py: Michael's pick pc_pc_ns_mr), appended by
#    cheer/bank.py and installed
# Everything written is game audio: it stays in $MELEE_WORK (sfxbank/, crowd/) and the disc, never in git.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
PY=${PY:-$ROOT/.venv/bin/python}
MW=${MELEE_WORK:-$HOME/games/melee/work}
export MELEE_WORK="$MW" MELEE_DISC="${MELEE_DISC:-$HOME/games/melee/disc}"
export SFXBANK="${SFXBANK:-$MW/sfxbank}" CROWD_WORK="${CROWD_WORK:-$MW/crowd}"
export SMRPG_SFX="${SMRPG_SFX:-$HOME/games/smrpg/sfx}"
[ -d "$SMRPG_SFX/geno/nosat" ] || sh "$HERE/capture/capture.sh"
"$PY" "$HERE/rom_tools/build_sounds_rom.py" | tail -1
"$PY" "$HERE/rom_tools/build_bank.py" | tail -1
mkdir -p "$SFXBANK/synth/wav"
cp "$HERE"/wav/*.wav "$SFXBANK/synth/wav/"; cp "$HERE/sounds4.json" "$SFXBANK/synth/"
"$PY" "$HERE/rom_tools/build_bank4.py" | tail -1
sh "$SFXBANK/out4/install.sh"
"$PY" "$HERE/timed.py" | tail -1
"$PY" "$HERE/gunfit.py" | tail -1
"$PY" "$HERE/cheer/survey.py" > "$CROWD_WORK.survey.log" 2>&1 || { cat "$CROWD_WORK.survey.log"; exit 1; }
"$PY" "$HERE/cheer/candidates.py" pc_pc_ns_mr | tail -1
"$PY" "$HERE/cheer/bank.py" "$CROWD_WORK/cands/pc_pc_ns_mr.wav" --out "$SFXBANK/final" | tail -1
"$PY" "$HERE/cheer/bank.py" --install "$SFXBANK/final"
shasum "$MELEE_DISC/files/audio/us/geno.ssm"
