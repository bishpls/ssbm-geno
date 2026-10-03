#!/bin/sh
# Geno's NEW CHALLENGER screen (NtAppro.usd: his silhouette at frame 12) and prize screen (SdPrize.usd: his two messages),
# into $MELEE_WORK/challenger, where play.sh installs them from. Both start from your own disc's vanilla files.
#   projects/geno/trailer/silhouette/build.sh [SIL.bgra]
# The prize messages need nothing else: datkit prize-geno writes them into SdPrize.usd's unused entries 0x47-0x48.
# The silhouette needs one in-game render (Dolphin) of the production model, made once:
#   SIL_LAB=matte .venv/bin/python tools/machinima/melee/build.py projects/geno/trailer silhouette_lab
#   DOLPHIN_SLOTS=1 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --until 'DIRECTOR END' --res 3 --quiet
#   .venv/bin/python projects/geno/trailer/silhouette/silhouette.py solve OUT beam=RUN:INDEX   # the Beam's charge pose
# then pass OUT/beam.bgra here (INDEX: the beam Geno's place, left to right, in SIL_POSES; the release's came from a run
# whose second Geno held the Beam's charge, index 1).
# Built 2026-10-02 from vanilla files, this reproduces the installed SdPrize.usd and, from the release's beam.bgra,
# NtAppro.usd byte for byte.
set -eu
ROOT=$(cd "$(dirname "$0")/../../../.." && pwd)
DK=$ROOT/tools/machinima/melee/datkit.sh
MW=${MELEE_WORK:-$HOME/games/melee/work}
FILES=${MELEE_DISC:-$HOME/games/melee/disc}/files
VAN=${VANILLA_FILES:-$FILES}        # vanilla NtAppro.usd / SdPrize.usd (once Geno's are installed, point this at copies)
OUT=$MW/challenger
mkdir -p "$OUT"
"$DK" prize-geno "$VAN/SdPrize.usd" "$OUT/SdPrize.usd" \
    "You've unlocked the star|spirit in a doll, Geno!" \
    "Geno is a real, fully playable|fighter, built on the Melee|decomp. Link in the comments!" | tail -1
if [ $# -ge 1 ]; then
    "$DK" approach-geno "$VAN/NtAppro.usd" "$1" "$OUT/NtAppro.usd" | tail -1
else
    echo "no silhouette given: NtAppro.usd not built (see the header for the render)" >&2
fi
