"""Finger Shot lab (geno-fx): the Finger Shot's own model (a volley of golden slugs, projects/geno/fx/finger_model.py) and
its muzzle puff (EfGeData.dat FINGER_PUFF), against Fox:
  tap        a grounded tap, close on the hand
  air        a short hop and a tap: the aerial shot dips ~10 degrees
  two        two taps in a row: two on screen, the cap (a third tap fires nothing)
  match      a grounded tap at match distance into Fox 30 ahead (it hits: 3%)
  dthrow     the down throw's three point-blank shots (the Finger article's state 1), close
GENO_FINGER_MODEL=0 in the fighter build gives the donor's red laser (the "before"). Each segment opens with a sync slate.
    .venv/bin/python tools/machinima/melee/build.py projects/geno finger_lab
"""
import json, os, sys
from dsl import Film

GENO, FOX = 0, 1
CLOSE = dict(eye=(-14, 10, 55), at=(-14, 9, 0))
MATCH = dict(eye=(5, 14, 150), at=(5, 12, 0))
# (label, frames, camera, Geno's steps (offset, frames, stick, buttons), Fox's x)
SEGS = [
    ('tap', 60, CLOSE, [(0, 2, (0, 0), 'B')], 60),
    ('air', 70, CLOSE, [(0, 2, (0, 0), 'X'), (7, 2, (0, 0), 'B')], 60),
    ('two', 80, CLOSE, [(0, 2, (0, 0), 'B'), (36, 2, (0, 0), 'B'), (72, 2, (0, 0), 'B')], 60),
    ('match', 70, MATCH, [(0, 2, (0, 0), 'B')], 0),
    ('dthrow', 110, CLOSE, [(0, 2, (0, 0), 'Z'), (40, 3, (0, -80), '')], -21),
]
SYNC = 10
f = Film(len_s=(70 + sum(s[1] for s in SEGS) + 40) / 60)
f.setup(players=[('geno', dict(x=-30, face=1)), ('fox', dict(x=60, face=-1))], seed=5)
geno = f.port(GENO)
t, plan = 70, []
for label, n, cam, steps, fx in SEGS:
    f.reset(t - 20, GENO, -30, 1); f.reset(t - 20, FOX, fx, -1); f.percent(t - 18, FOX, 0)
    f.cam(t - 20, fov=30, ease='cut', **cam)
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    for at, k, stick, btn in steps:
        geno.hold(t + at, k, stick=stick, btn=btn)
    f.mark(t, len(plan), label)
    plan.append(dict(label=label, start=t, frames=n, sync=t - SYNC))
    t += n
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
