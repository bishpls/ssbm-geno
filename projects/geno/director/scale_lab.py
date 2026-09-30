"""Projectile scale lab (geno-fx): how big each big charged projectile is drawn against its hitbox, on one camera at match
distance. Geno fires the Geno Beam at one, two and three stars (untimed, so no rainbow burst), then Samus a full Charge
Shot, Mewtwo a full Shadow Ball and a laser (Falco's, or Fox's with SCALE_LASER=fox), each from the same spot to the
right. Everyone else stands off camera to the left.
    SCALE_COLL=0|2 SCALE_BG=black|stage [SCALE_LASER=falco|fox] [LAB_ONLY=g1,...] \
        .venv/bin/python tools/machinima/melee/build.py projects/geno scale_lab
SCALE_BG=black hides the stage on black (clean masks for fx/scalemeasure.py); SCALE_COLL=2 draws the collision capsules
only (the hitboxes in red), so the same frames of a coll 0 and a coll 2 run give the drawn and the hit sizes. Each segment
opens with a sync slate (fx/fxsync.py).
"""
import json, os, sys
from dsl import Film

LASER = os.environ.get('SCALE_LASER', 'falco')
COLL = int(os.environ.get('SCALE_COLL', '0'))
BLACK = os.environ.get('SCALE_BG', 'black') == 'black'
GENO, SAMUS, MEWTWO, LASERP = 0, 1, 2, 3
SX = -30                     # the shooter's spot
AWAY = -65                   # everyone else, on the stage but left of the frame (it spans x -33.5 to 63.5)
# (label, shooter port, frames, steps (offset, frames, buttons))
SEGS = [
    ('g1', GENO, 110, [(0, 24, 'B')]),                      # released on charge frame 25: one star, untimed
    ('g2', GENO, 130, [(0, 46, 'B')]),                      # 47: two stars, untimed
    ('g3', GENO, 150, [(0, 110, 'B')]),                     # held: the auto-fire on 64, three stars, untimed
    ('samus', SAMUS, 230, [(0, 3, 'B'), (150, 3, 'B')]),     # charge to full (and past it), then fire
    ('mewtwo', MEWTWO, 250, [(0, 3, 'B'), (170, 3, 'B')]),   # Shadow Ball: full at ~120, then fire
    ('laser', LASERP, 90, [(0, 3, 'B')]),
    ('finger', GENO, 70, [(0, 2, 'B')]),                    # a Finger Shot tap: the volley (four hitbox spheres)
]
ONLY = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
if ONLY:
    SEGS = [s for s in SEGS if s[0] in ONLY]
SYNC = 10
f = Film(len_s=(70 + sum(s[2] for s in SEGS) + 40) / 60)
f.setup(players=[('geno', dict(x=SX, face=1)), ('samus', dict(x=AWAY - 5, face=1)), ('mewtwo', dict(x=AWAY - 10, face=1)),
                 (LASER, dict(x=AWAY - 15, face=1))], seed=5, coll=COLL)
# match distance: a fixed camera 150 back (the frame is ~80 units tall at 30 degrees), on the flight
f.cam(0, eye=(15, 12, 150), at=(15, 12, 0), fov=30, ease='cut')
if BLACK:
    f.cue(1, 'stage', a=0); f.cue(1, 'bgcolor', a=0, b=0, c=0)
t, plan = 90, []
for label, shooter, n, steps in SEGS:
    for p in range(4):
        f.reset(t - 24, p, SX if p == shooter else AWAY - 5 * p, 1)
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=0 if BLACK else 1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    for at, k, btn in steps:
        f.port(shooter).hold(t + at, k, btn=btn)
    f.mark(t, len(plan), label)
    plan.append(dict(label=label, start=t, frames=n, sync=t - SYNC, shooter=shooter))
    t += n
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
