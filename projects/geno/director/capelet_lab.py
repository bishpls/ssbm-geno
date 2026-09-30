"""Capelet lab (geno-cannon polish): his arms against the capelet's front panels in the moves that raise them. Each segment
is one move from standing, opening with a sync slate, the camera close on his upper body three-quarters from in front
(CAPE_CAM=side: from the side, the game's usual angle; match: at match distance). Fox stands far off (and in reach for
the grab). The plan (segment starts, the input frame) goes next to the script as capelet_lab.plan.json.
    .venv/bin/python tools/machinima/melee/build.py projects/geno capelet_lab
"""
import json, os, sys
from dsl import Film

GENO, FOX = 0, 1
GX = -20
CAM = os.environ.get('CAPE_CAM', 'q34')
# (label, frames, [(offset, frames held, stick, cstick, buttons)])
MOVES = [
    ('wait', 60, []),
    ('usmash', 70, [(0, 2, (0, 0), (0, 80), '')]),
    ('utilt', 50, [(0, 3, (0, 48), (0, 0), 'A')]),
    ('uair', 80, [(0, 2, (0, 0), (0, 0), 'X'), (6, 2, (0, 0), (0, 80), '')]),
    ('fsmash', 70, [(0, 2, (0, 0), (80, 0), '')]),
    ('ftilt', 50, [(0, 3, (48, 0), (0, 0), 'A')]),
    ('jab', 50, [(0, 2, (0, 0), (0, 0), 'A')]),
    ('dsmash', 70, [(0, 2, (0, 0), (0, -80), '')]),
    ('starroad', 110, [(0, 3, (0, 80), (0, 0), 'B'), (3, 40, (0, 80), (0, 0), '')]),
    ('downb', 90, [(0, 60, (0, -80), (0, 0), 'B')]),
    ('beam', 90, [(0, 50, (0, 0), (0, 0), 'B')]),
    ('taunt', 130, [(0, 2, (0, 0), (0, 0), 'DU')]),
    ('grab', 90, [(0, 2, (0, 0), (0, 0), 'Z'), (30, 2, (0, 80), (0, 0), '')]),
    ('run', 70, [(0, 50, (80, 0), (0, 0), '')]),
]
SYNC = 10


def cam_for(x):
    if CAM == 'side':
        return dict(eye=(x + 2, 10, 38), at=(x + 2, 9.5, 0))
    if CAM == 'match':
        return dict(eye=(x + 5, 14, 150), at=(x + 5, 12, 0))
    return dict(eye=(x + 20, 13, 30), at=(x + 1, 9.5, 0))


f = Film(len_s=(60 + sum(m[1] + 30 for m in MOVES) + 30) / 60)
f.setup(players=[('geno', dict(x=GX, face=1)), ('fox', dict(x=GX + 60, face=-1))], seed=5,
        coll=int(os.environ.get('CAPE_COLL', '0')))
geno = f.port(GENO)
t, plan = 60, []
for label, n, steps in MOVES:
    fox_x = GX + 9 if label == 'grab' else GX + 60
    f.reset(t - 20, GENO, GX, 1); f.reset(t - 20, FOX, fox_x, -1)
    f.cam(t - 20, fov=30, ease='cut', **cam_for(GX))
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    for off, dur, st, cs, btn in steps:
        geno.hold(t + off, dur, stick=st, c=cs, btn=btn)
    f.mark(t, len(plan), label)
    plan.append(dict(label=label, start=t, frames=n + 10, sync=t - SYNC))
    t += n + 30
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
