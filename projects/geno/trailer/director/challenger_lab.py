"""NEW CHALLENGER (trailer shot 1.1): boot straight into the challenger screen (GM_CHALLENGER_APPROACH, 0x14) with a filled
challenger record and film it. CHALLENGER=luigi (default; a vanilla silhouette) or geno (his own silhouette, NtAppro.usd
frame 12, with the decomp's non-matching gmapproach.c and an NtAppro.usd from datkit approach-geno), HUMAN=mario (default;
the shot uses bowser). PRESS_A=F presses A on the human's port at loop frame F (the screen takes A from frame 180), into
the challenger fight (Geno's: the Forest Maze, a level-5 CPU); WALK_OFF=F walks the human off the left edge from loop
frame F (the loss path: the failure counters); LEN seconds (default 10).
    eval "$(sh tools/machinima/melee/sandbox.sh NAME)"
    CHALLENGER=geno HUMAN=bowser .venv/bin/python tools/machinima/melee/build.py projects/geno/trailer challenger_lab
    DOLPHIN_SLOTS=3 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol OUT --until 'DIRECTOR MENU END' --res 3 --quiet
"""
import os, sys
from dsl import Menu

m = Menu(boot='challenger', len_s=float(os.environ.get('LEN', 10.0)),
         challenger=(os.environ.get('HUMAN', 'mario'), os.environ.get('CHALLENGER', 'luigi')))
if os.environ.get('PRESS_A'):
    m.press(int(os.environ['PRESS_A']), 0, 'A')
if os.environ.get('WALK_OFF'):                # the human walks off the stage's left edge from that loop frame: the loss path
    m.hold(int(os.environ['WALK_OFF']), 0, 400, stick=(-80, 0))
m.emit(sys.argv[1])
