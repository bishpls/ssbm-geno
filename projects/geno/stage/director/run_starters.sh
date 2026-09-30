#!/bin/bash
# Build, run and report starter_lab for each starter (or the ones named): $MELEE_WORK/stage/lab/<stage>.json
#   bash projects/geno/stage/director/run_starters.sh [stage ...]
set -e
cd "$(dirname "$0")/../../../.."
eval "$(sh tools/machinima/melee/sandbox.sh geno-stage)"
mkdir -p "$MELEE_WORK/stage/lab" "$MELEE_WORK/stage/runs"
for S in ${@:-battlefield final_destination yoshis_story dream_land fountain stadium}; do
  echo "== $S"
  STAGE_LAB=$S .venv/bin/python tools/machinima/melee/build.py projects/geno/stage starter_lab | tail -1
  R="$MELEE_WORK/stage/runs/$S"; rm -rf "$R"
  DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run "$MELEE_DISC/sys/main.dol" "$R" --logonly --until 'DIRECTOR END' --frames 20000 --timeout 400 --quiet | tail -1
  cp projects/geno/stage/director/build/starter_lab.plan.json "$R/plan.json"
  .venv/bin/python projects/geno/stage/director/starter_lab.py --report "$R" "$MELEE_WORK/stage/lab/$S.json"
done
