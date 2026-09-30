"""Form lab (Gate 2): Geno taunts with the lab taunt (GENO_FORM_LAB=1 in the anims build: rig/moves.py form_lab), which
cycles every weapon form on both hands, then the hand poses and the cap poses, 30 frames each, arms held out.
    GENO_FORM_LAB=1 .venv/bin/python projects/geno/rig/anims.py ... ; fighter-build ...
    FORM_LAB_AT=9 FORM_LAB_DIST=22 .venv/bin/python tools/machinima/melee/build.py projects/geno form_lab
Frames: the taunt starts at 20; forms at 21 + 30k (hand, fshot, gun, stargun, cannon, beam, rocket), hand poses from 231
(fist, open, point, grip), cap poses from 351 (rest, back, low). The camera sits 3/4 in front so both hands show.
"""
import os, sys
from dsl import Film

at = float(os.environ.get('FORM_LAB_AT', 9)); dist = float(os.environ.get('FORM_LAB_DIST', 22))
yaw = float(os.environ.get('FORM_LAB_YAW', 50))
f = Film(len_s=7.9)
f.setup(players=[('geno', dict(x=-6, face=1)), ('mario', dict(x=20, face=-1))], seed=5)
f.orbit(0, at=(-5, at, 0), dist=dist, yaw=yaw, pitch=6, fov=30, ease='cut')
f.port(0).hold(18, 3, btn='DU')
f.emit(sys.argv[1])
