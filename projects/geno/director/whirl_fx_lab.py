"""Whirl effects lab (geno-fx): the Whirl's own disc (projects/geno/fx/whirl_model.py) and its trail rings, hit bursts
and crit flash (EfGeData.dat WHIRL_*), against Fox:
  hit        the outbound hit on Fox 15 ahead (the burst), then the spin-down (the disc shrinks away)
  crit       side B again 39 frames in (contact +42): the timed crit (the blue flash), Fox at 60%
  shield     Fox shields 5 ahead: the grind (three spark bursts), then the hover and its fade
  recall     Fox 70 ahead: the hover, then side B at 60 recalls it through him (the trail on the way back)
  match      the outbound hit at match distance
GENO_WHIRL_MODEL=0 in the fighter build gives the donor's ball (the "before"). Each segment opens with a sync slate.
    .venv/bin/python tools/machinima/melee/build.py projects/geno whirl_fx_lab
"""
import json, os, sys
from dsl import Film

GENO, FOX = 0, 1
MID = dict(eye=(-8, 11, 90), at=(-8, 10, 0))
MATCH = dict(eye=(5, 14, 150), at=(5, 12, 0))
SB = (60, 0)
# (label, frames, camera, Geno's steps (offset, frames, stick, buttons), Fox's x, Fox's steps, Fox's percent)
SEGS = [
    ('hit', 110, MID, [(0, 3, SB, 'B')], 15, [], 0),
    ('crit', 110, MID, [(0, 3, SB, 'B'), (39, 2, SB, 'B')], 15, [], 60),
    ('shield', 150, MID, [(0, 3, SB, 'B')], 5, [(0, 110, (0, 0), 'R')], 0),
    ('recall', 130, MID, [(0, 3, SB, 'B'), (60, 3, SB, 'B')], 70, [], 0),
    ('match', 110, MATCH, [(0, 3, SB, 'B')], 15, [], 0),
]
SYNC = 10
f = Film(len_s=(70 + sum(s[1] for s in SEGS) + 40) / 60)
f.setup(players=[('geno', dict(x=-30, face=1)), ('fox', dict(x=15, face=-1))], seed=5)
geno, fox = f.port(GENO), f.port(FOX)
t, plan = 70, []
for label, n, cam, steps, fx, fsteps, pct in SEGS:
    f.reset(t - 20, GENO, -30, 1); f.reset(t - 20, FOX, fx, -1); f.percent(t - 18, FOX, pct)
    f.cam(t - 20, fov=30, ease='cut', **cam)
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    for at, k, stick, btn in steps:
        geno.hold(t + at, k, stick=stick, btn=btn)
    for at, k, stick, btn in fsteps:
        fox.hold(t + at, k, stick=stick, btn=btn)
    f.mark(t, len(plan), label)
    plan.append(dict(label=label, start=t, frames=n, sync=t - SYNC))
    t += n
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
