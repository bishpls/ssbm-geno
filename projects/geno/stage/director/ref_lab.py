"""Reference lab: a stage at match distance, for the look boards and the readability measure. Fox and Falco stand at
their spawns with the game's own camera (the match framing); frames 80-100 are the settled view. REF_STAGE names the stage
(dsl.STAGE).
    REF_STAGE=kongo_jungle .venv/bin/python tools/machinima/melee/build.py projects/geno/stage ref_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --frames 110 --res 1 --quiet
"""
import os, sys
from dsl import Film

N = int(os.environ.get('REF_N', 110))                 # longer for a motion capture (the sky's cycle)
f = Film(len_s=N / 60.0)
X = float(os.environ.get('REF_X', 25))
f.setup(players=[('fox', dict(x=-X, face=1)), ('falco', dict(x=X, face=-1))], stage=os.environ.get('REF_STAGE', 'battlefield'), seed=1)
f.game_camera()
f.cue(N - 5, 'end')
f.emit(sys.argv[1])
