#!/bin/sh
# Build the announcer's "Geno!" from your own disc: cut from his real recorded name calls, never synthesized (NOTES.md).
#   projects/geno/sound/announcer/build.sh            # -> $MELEE_WORK/announcer/out/nr_name.ssm, then install.sh
# 1. sources.py: decode the clips the splice uses from audio/us/nr_name.ssm and nr_vs.ssm into $MELEE_WORK/announcer/src
# 2. final.py: round 1's candidates (C, the head the call keeps: Jigglypuff's J, Pichu's ee, "Green team"'s n)
# 3. hybrid.py deliver: round 2, Michael's pick geno_CD_full (C's head with Mario's long O)
# 4. patch_bank.py: DSP-ADPCM encode (dspenc.py, a port of the reference encoder) and the US bank with the call appended
#    and entry 17 (sound 510017, the decomp's name call for kind 0x22) pointed at it
# Built 2026-10-02 from a retail disc this reproduces the installed bank bit for bit (SHA-1 ba2e1d69...).
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../../.." && pwd)
PY=${PY:-$ROOT/.venv/bin/python}
MW=${MELEE_WORK:-$HOME/games/melee/work}
DISC=${MELEE_DISC:-$HOME/games/melee/disc}
# the retail bank: install.sh's backup once Geno's call is installed, else the disc's own
BAK=$MW/orig/audio/us/nr_name.ssm
[ -f "$BAK" ] && export ANNOUNCER_SRC_BANK="$BAK"
"$PY" "$HERE/tools/sources.py" "$DISC"
"$PY" "$HERE/tools/final.py" > /dev/null
"$PY" "$HERE/tools/hybrid.py" deliver | grep geno_CD_full
"$PY" "$HERE/tools/patch_bank.py" | tail -1
shasum "${ANNOUNCER_WORK:-$MW/announcer}/out/nr_name.ssm"
