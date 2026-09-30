"""Star Road effects lab (geno-fx): the launch's burst and the flight's trail of stars (EfGeData.dat SR_*), on Final
Destination:
  close    grounded, aimed up and forward, close on the launch
  match    the same at match distance
  recover  placed off the right ledge (100, -12), aimed back up at the stage, at match distance
Each segment opens with a sync slate. The fold is frames 1-18 (aimed through it), the launch the travel's frame 1.
    .venv/bin/python tools/machinima/melee/build.py projects/geno starroad_fx_lab
"""
import json, os, sys
from dsl import Film

GENO, FOX = 0, 1
UPFWD, UPBACK = (45, 70), (-55, 60)
SEGS = [
    ('close', 90, dict(eye=(-5, 30, 110), at=(-5, 28, 0)), (-30, None), UPFWD),
    ('match', 90, dict(eye=(5, 30, 170), at=(5, 26, 0)), (-30, None), UPFWD),
    ('recover', 100, dict(eye=(80, 5, 170), at=(80, 5, 0)), (100, -12), UPBACK),
]
SYNC = 10
f = Film(len_s=(70 + sum(s[1] for s in SEGS) + 40) / 60)
f.setup(players=[('geno', dict(x=-30, face=1)), ('fox', dict(x=-70, face=1))], seed=5)
geno = f.port(GENO)
t, plan = 70, []
for label, n, cam, (gx, gy), aim in SEGS:
    f.reset(t - 20, GENO, gx, 1 if gy is None else -1); f.reset(t - 20, FOX, -70, 1)
    if gy is not None:                                 # placed in the air (starroad_lab's way), falling
        f.setpos(t - 4, GENO, gx, gy); f.cue(t - 4, 'face', GENO, -1); f.cue(t - 4, 'motion', GENO, a=29)
    f.cam(t - 20, fov=30, ease='cut', **cam)
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    geno.hold(t, 2, stick=(0, 80), btn='B')
    geno.hold(t + 2, 16, stick=aim)
    f.mark(t, len(plan), label)
    plan.append(dict(label=label, start=t, frames=n, sync=t - SYNC))
    t += n
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
