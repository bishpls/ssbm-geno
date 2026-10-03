#!/bin/bash
# ref_lab on each named stage: $MELEE_WORK/stage/refs/<stage>.png (frame 95 at res 1) and its no-HUD frame
set -e
cd "$(dirname "$0")/../../../.."
eval "$(sh tools/machinima/melee/sandbox.sh geno-stage)"
mkdir -p "$MELEE_WORK/stage/refs"
for S in "$@"; do
  REF_STAGE=$S .venv/bin/python tools/machinima/melee/build.py projects/geno/stage ref_lab | tail -1
  R="$MELEE_WORK/stage/runs/ref_$S"; rm -rf "$R"
  DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run "$MELEE_DISC/sys/main.dol" "$R" --frames 110 --res 1 --timeout 300 --quiet | tail -1
  cp "$R/f00095.png" "$MELEE_WORK/stage/refs/$S${REF_TAG:-}.png"
  find "$R" -name 'f[0-9][0-9][0-9][0-9][0-9].png' -delete
  echo "== $S done"
done
echo REFS DONE
