"""Blast cases lab (geno-fx): the Blast cast where Michael saw it draw badly (2026-09-30), on Battlefield (main floor y 0,
edges x +-68.4; side platforms y 27.2, x 18.8 to 57.6; top platform y 54.4, x +-15.6):
  offstage  in the air past the right edge (x 85, y 25), a far mark: over the void (the column sweeps 50 below him)
  edge      on the stage at x 20, held past the second star: three columns at 56, 70, 84, the edge between them
  platform  standing on the top platform, a near mark: the column finds the right platform below
  high      high in the air (x -64, y 110, clear of the platforms: setpos sweeps collision from where he was), a near
            mark: the column falls ~80 to the left platform
Each segment opens with a sync slate. The mark's geometry is the specials' (ftgeno_specials.c ftGe_BlastFloor); this lab
checks the drawing.
    .venv/bin/python tools/machinima/melee/build.py projects/geno blast_cases_lab
"""
import json, os, sys
from dsl import Film

GENO, FOX = 0, 1
FWD, BACK, DOWN = (80, 0), (-80, 0), (0, -80)
# label, frames, camera, Geno's place (x, y or None on the ground), steps (offset, frames, stick, button)
SEGS = [
    ('edge', 140, dict(eye=(55, 20, 170), at=(55, 15, 0)), (20, None), [(0, 30, DOWN, 'B')]),
    ('platform', 120, dict(eye=(15, 40, 170), at=(15, 35, 0)), (0, 54.4), [(0, 3, DOWN, 'B')]),
    ('high', 120, dict(eye=(-45, 60, 230), at=(-45, 55, 0)), (-64, 110), [(0, 3, DOWN, 'B'), (1, 12, BACK, '')]),
    ('offstage', 120, dict(eye=(110, 20, 200), at=(110, 15, 0)), (85, 45), [(0, 3, DOWN, 'B'), (1, 12, FWD, '')]),
]                                                     # offstage last: he falls to his death after it
ONLY = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
if ONLY:
    SEGS = [s for s in SEGS if s[0] in ONLY]
SYNC = 10
f = Film(len_s=(70 + sum(s[1] for s in SEGS) + 40) / 60)
f.setup(players=[('geno', dict(x=0, face=1)), ('fox', dict(x=-60, face=1))], stage='battlefield', seed=5)
geno = f.port(GENO)
t, plan = 70, []
for label, n, cam, (gx, gy), steps in SEGS:
    f.reset(t - 20, GENO, gx, 1); f.reset(t - 20, FOX, -60, 1)
    if gy is not None:                                 # placed (starroad_lab's way): in the air he falls from here
        f.setpos(t - 6, GENO, gx, gy); f.cue(t - 6, 'face', GENO, 1)
        if gy != 54.4:
            f.cue(t - 6, 'motion', GENO, a=29)
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
