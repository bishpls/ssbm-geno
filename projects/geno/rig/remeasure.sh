#!/bin/sh
# Rebuild Geno's three fighter files from rig.py + moves.py and re-measure every normal against the cast:
#   projects/geno/rig/remeasure.sh            # -> $MELEE_WORK/rig/out/PlGe*.dat, movedata/Ge.jsonl, research/*.md, board sweeps
set -e
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
PY=${PY:-$ROOT/.venv/bin/python}
MW=${MELEE_WORK:-$HOME/games/melee/work}
W=$MW/rig; F=$W/out; D=${MELEE_DISC:-$HOME/games/melee/disc}/files
LABS=$ROOT/projects/geno/director/labs
$PY "$ROOT/projects/geno/rig/rig.py" "$W/rig.json" >/dev/null
$PY "$ROOT/projects/geno/rig/anims.py" "$W/mr_actions.txt" "$W/anims.json" >/dev/null
"$ROOT/tools/machinima/melee/datkit.sh" fighter-build "$W/rig.json" "$W/anims.json" "$D/PlMr.dat" "$D/PlCo.dat" "$F" Ge Geno 0 | tail -1
"$ROOT/tools/machinima/melee/datkit.sh" movedata "$F/PlGe.dat" "$F/PlGeAJ.dat" "$F/PlGeNr.dat" "$D/PlCo.dat" 0 "$W/rig.json" \
    > "$MW/movedata/Ge.jsonl" 2> "$MW/movedata/Ge.err"
cd "$ROOT/projects/geno"
$PY "$LABS/cast_moves.py" "$MW/movedata" research/cast_moves.md >/dev/null
$PY "$LABS/aerial_profile.py" "$MW/movedata" research/aerial_profile.md >/dev/null
$PY "$LABS/sweeps.py" "$MW/movedata" research/aerial_shape.md nair,fair,bair,uair,dair Ge,Ms,Fx,Fc,Sk,Pe,Ca,Pr,Ss,Mr >/dev/null
$PY "$LABS/sweeps.py" "$MW/movedata" board/sweeps_aerials.png >/dev/null
$PY "$LABS/sweeps.py" "$MW/movedata" board/sweeps_ground.png jab1,ftilt,utilt,dtilt,dash_attack,fsmash,usmash,dsmash >/dev/null
$PY "$LABS/getup_cover.py" "$MW/movedata" research/getup_cover.md >/dev/null
$PY "$LABS/sweeps.py" "$MW/movedata" board/sweeps_getups.png getup_u,getup_d >/dev/null
BODY_FRESH_GE=1 $PY "$LABS/body_cover.py" "$MW/movedata" research/body_moves.md >/dev/null
# Geno Flash's hurtboxes against its cannon and the cast's transformed states, with the guardrail (DESIGN §12)
$PY "$LABS/cannon_hurt.py" report "$F" research/flash_hurtboxes.md >/dev/null
# what the limb growth costs each move: the same build without it (GENO_NO_GROW), and the cast without their scale tracks
mkdir -p "$MW/movedata_nogrow"; GENO_NO_GROW=1 $PY "$ROOT/projects/geno/rig/anims.py" "$W/mr_actions.txt" "$W/anims_nogrow.json" >/dev/null
"$ROOT/tools/machinima/melee/datkit.sh" fighter-build "$W/rig.json" "$W/anims_nogrow.json" "$D/PlMr.dat" "$D/PlCo.dat" "$W/out_nogrow" Ge Geno 0 >/dev/null
"$ROOT/tools/machinima/melee/datkit.sh" movedata "$W/out_nogrow/PlGe.dat" "$W/out_nogrow/PlGeAJ.dat" "$W/out_nogrow/PlGeNr.dat" "$D/PlCo.dat" 0 "$W/rig.json" \
    > "$MW/movedata_nogrow/Ge.jsonl" 2>/dev/null
[ -f "$MW/movedata_noscale/Mr.jsonl" ] || MOVEDATA_NOSCALE=1 OUT="$MW/movedata_noscale" sh "$ROOT/projects/geno/rig/measure_cast.sh" >/dev/null
$PY "$LABS/growth_cost.py" "$MW/movedata" "$MW/movedata_noscale" "$MW/movedata_nogrow/Ge.jsonl" research/growth_cost.md >/dev/null
echo "measured: research/cast_moves.md, aerial_profile.md, aerial_shape.md, getup_cover.md, body_moves.md, flash_hurtboxes.md, growth_cost.md; board/sweeps_*.png"
