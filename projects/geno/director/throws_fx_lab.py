"""Throws effects lab (geno-fx): the throws' own visuals, against Fox grabbed at 0%:
  uthrow       the up throw's Star Gun salvo: three spinning gold stars with sparkle trails (the Beam article's state
               3), the Star Gun's muzzle flash (N_STAR_FLASH), close
  uthrow_match the same at match distance
  fthrow       the forward throw's Rocket Fist: the launch's white four-point star at the wrist and the exhaust, close
  fthrow_match the same at match distance
Each segment opens with a sync slate. Grab on the segment's first frame, the throw 40 frames later.
    .venv/bin/python tools/machinima/melee/build.py projects/geno throws_fx_lab
"""
import json, os, sys
from dsl import Film

GENO, FOX = 0, 1
GX, FX = -30, -21
CLOSE = dict(eye=(-20, 22, 90), at=(-20, 20, 0))
MATCH = dict(eye=(5, 20, 150), at=(5, 18, 0))
THROW = dict(uthrow=(0, 80), fthrow=(80, 0))
SEGS = [('uthrow', 150, CLOSE), ('uthrow_match', 150, MATCH), ('fthrow', 130, CLOSE), ('fthrow_match', 130, MATCH)]
ONLY = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
if ONLY:
    SEGS = [s for s in SEGS if s[0] in ONLY]
SYNC = 10
f = Film(len_s=(70 + sum(s[1] for s in SEGS) + 40) / 60)
f.setup(players=[('geno', dict(x=GX, face=1)), ('fox', dict(x=FX, face=-1))], seed=5)
geno = f.port(GENO)
t, plan = 70, []
for label, n, cam in SEGS:
    f.reset(t - 20, GENO, GX, 1); f.reset(t - 20, FOX, FX, -1); f.percent(t - 18, FOX, 0)
    f.cam(t - 20, fov=30, ease='cut', **cam)
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    geno.hold(t, 2, btn='Z')
    geno.hold(t + 40, 3, stick=THROW[label.split('_')[0]])
    f.mark(t, len(plan), label)
    plan.append(dict(label=label, start=t, frames=n, sync=t - SYNC))
    t += n
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
