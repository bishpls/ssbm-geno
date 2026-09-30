#!/bin/bash
# showcase_capture.sh TAG RES SPEC...: build and capture showcase runs, one after another (each build rewrites main.dol, and the
# sandbox has one Dolphin user folder, so its captures never overlap). SPEC: part:a|b|c, entry, costumes:0,1,2,3, win:B|Y|X, lose, kirby
set -e
TAG=$1; RES=$2; shift 2
eval "$(sh ~/animation-pipeline-geno-atk-air/tools/machinima/melee/sandbox.sh geno-atk-air)"
R=~/animation-pipeline-geno-atk-air; S=~/games/melee/sandbox/geno-atk-air/runs; PY=$R/.venv/bin/python
cd $R
for spec in "$@"; do
    kind=${spec%%:*}; arg=${spec#*:}; name=${TAG}_${kind}${arg:+_${arg//,/}}
    [ "$kind" = "$spec" ] && arg='' && name=${TAG}_${kind}
    case $kind in
        part) env SHOW=main SHOW_PART=$arg $PY tools/machinima/melee/build.py projects/geno showcase_lab | tail -1; lab=showcase_lab;;
        entry) env SHOW=entry $PY tools/machinima/melee/build.py projects/geno showcase_lab | tail -1; lab=showcase_lab;;
        costumes) env SHOW=costumes SHOW_COLORS=$arg $PY tools/machinima/melee/build.py projects/geno showcase_lab | tail -1; lab=showcase_lab;;
        win) env WIN_BTN=$arg WIN_AT=440 $PY tools/machinima/melee/build.py projects/geno victory_lab | tail -1; lab=victory_lab;;
        lose) env WIN_LOSER=geno $PY tools/machinima/melee/build.py projects/geno victory_lab | tail -1; lab=victory_lab;;
        kirby) env KBHAT=costumes KBHAT_COLORS=0 $PY tools/machinima/melee/build.py projects/geno kirby_hat_lab | tail -1; lab=kirby_hat_lab;;
    esac
    [ -f projects/geno/director/build/$lab.plan.json ] && cp projects/geno/director/build/$lab.plan.json $S/$name.plan.json || echo '[]' > $S/$name.plan.json
    case $kind in
        part) n=$($PY -c "import json;p=json.load(open('$S/$name.plan.json'));print(p[-1]['start']+p[-1]['frames']+80)");;
        entry) n=420;; costumes) n=330;; win|lose) n=1100;; kirby) n=$($PY -c "import json;p=json.load(open('$S/$name.plan.json'));p=p['segs'] if isinstance(p,dict) else p;print(max(x['start']+x['frames'] for x in p)+80)");;
    esac
    rm -rf $S/$name
    DOLPHIN_SLOTS=2 $PY tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol $S/$name --frames $n --res $RES --timeout 2400 --quiet > $S/$name.out 2>&1
done
ls $S | grep "^${TAG}_" | grep -v "\." | while read r; do echo "$r $(tail -c 200 $S/$r.out | tr -d '\n' | grep -o '"frames": [0-9]*')"; done
