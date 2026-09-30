#!/bin/sh
# Re-measure every cast member's moves and bodies with datkit movedata (after a change to MoveData.cs):
#   projects/geno/rig/measure_cast.sh          # -> $MELEE_WORK/movedata/XX.jsonl (derived numbers only; the disc stays local)
#   MOVEDATA_NOSCALE=1 OUT=DIR projects/geno/rig/measure_cast.sh   # the same with every limb at rest scale, into DIR (what
#                                              # the cast's own limb growth costs them: diff the two with labs/growth_cost.py)
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
MW=${MELEE_WORK:-$HOME/games/melee/work}; D=$HOME/games/melee/disc/files; O=${OUT:-$MW/movedata}; mkdir -p "$O"
"$ROOT/tools/machinima/melee/datkit.sh" roots "$D/PlCo.dat" >/dev/null     # build once, before the parallel runs
k=0
for c in Mr Fx Ca Dk Kb Kp Lk Sk Ns Pe Pp Nn Pk Ss Ys Pr Mt Lg Ms Zd Cl Dr Fc Pc Gw Gn Fe; do     # Ft_Kind order
    "$ROOT/tools/machinima/melee/datkit.sh" movedata "$D/Pl$c.dat" "$D/Pl${c}AJ.dat" "$D/Pl${c}Nr.dat" "$D/PlCo.dat" $k \
        > "$O/$c.jsonl" 2> "$O/$c.err" &
    k=$((k + 1))
    [ $((k % 6)) = 0 ] && wait
done
wait
echo "measured $k fighters -> $O"
