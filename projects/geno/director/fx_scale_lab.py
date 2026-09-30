"""Effect scale lab: Geno taunts once, with the taunt's script swapped for an effect survey (a scratch patch of anims.json:
each effect spawned in turn 9 in front of him at head height, beside a radius-5 hitbox for scale), filmed close on the
side camera with hitboxes shown. For choosing common effects (EfCoData ids) whose size matches a hitbox.
    FX_FRAMES=N .venv/bin/python tools/machinima/melee/build.py projects/geno fx_scale_lab
"""
import os, sys
from dsl import Film

n = int(os.environ.get('FX_FRAMES', 600))
f = Film(len_s=(70 + n + 20) / 60)
f.setup(players=[('geno', dict(x=-10, face=1)), ('fox', dict(x=60, face=-1))], seed=5, coll=1)
f.cam(0, eye=(-1, 13, 62), at=(-1, 12, 0), fov=30, ease='cut')
f.port(0).hold(70, 2, btn='DU')
f.mark(70, 0, 'fx')
f.emit(sys.argv[1])
