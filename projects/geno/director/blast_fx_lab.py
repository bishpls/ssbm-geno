"""Blast effects lab (geno-fx): the Geno Blast's own look (projects/geno/fx/blast_model.py, EfGeData.dat BLAST_*): the
cast's sparkles, the mark's tell (the floor oval and its beam), SMRPG's coloured columns and their landing clouds, with a
Fox standing where the mark lands:
  tap      down B tapped: one column, marked on frame 10, struck 32 frames later
  three    held past the second star (24), released on 31: three columns in SMRPG's colours in turn
  tell     a tap, close on the mark: the tell over its 32 frames
  match    a tap at match distance
GENO_BLAST_MODEL=0 in the fighter build gives the donor's bolt (the "before"). Each segment opens with a sync slate.
    .venv/bin/python tools/machinima/melee/build.py projects/geno blast_fx_lab
"""
import json, os, sys
from dsl import Film

GENO, FOX = 0, 1
GX = -30
DOWN = (0, -80)
TALL = dict(eye=(0, 34, 165), at=(0, 32, 0))          # the whole column, from the floor to ~70 up
CLOSE = dict(eye=(20, 12, 70), at=(20, 11, 0))         # the mark
MATCH = dict(eye=(5, 14, 150), at=(5, 12, 0))
SEGS = [
    ('tap', 110, TALL, [(0, 3, DOWN, 'B')], GX + 50),
    ('three', 130, TALL, [(0, 30, DOWN, 'B')], GX + 50),
    ('tell', 110, CLOSE, [(0, 3, DOWN, 'B')], GX + 80),
    ('match', 110, MATCH, [(0, 3, DOWN, 'B')], GX + 50),
]
SYNC = 10
f = Film(len_s=(70 + sum(s[1] for s in SEGS) + 40) / 60)
f.setup(players=[('geno', dict(x=GX, face=1)), ('fox', dict(x=GX + 50, face=-1))], seed=5)
geno = f.port(GENO)
t, plan = 70, []
for label, n, cam, steps, fx in SEGS:
    f.reset(t - 20, GENO, GX, 1); f.reset(t - 20, FOX, fx, -1); f.percent(t - 18, FOX, 30)
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
