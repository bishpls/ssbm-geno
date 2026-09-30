"""Down air's blast column (DESIGN §6, Michael 2026-09-28): what it does to a Fox at each part of its length, with the
hitbox display on. The meteor sits at the muzzle (airborne targets only), the middle and the weak tail reach ~13 below.
  sh_over    a grounded Fox under a short hop (the column over him): the column's middle or tail, never a spike
  fh_fall    a grounded Fox under a full hop, dair late in the fall: the tail reaches him first
  air_muzzle an airborne Fox placed just under the muzzle (both falling): the meteor
  air_tail   an airborne Fox placed ~10 below him: the column's middle, a pop that doesn't spike
  tail_ground  a grounded Fox with Geno high enough (placed at 37) that only the tail reaches his head: a weak pop
Logged: HIT (frame, attacker, victim, damage), MS, and both fighters' positions (POS) through each try.
    .venv/bin/python tools/machinima/melee/build.py projects/geno dair_lab
"""
import json, os, sys
from dsl import Film

FALL = 29
SLOT = 150
# (label, Geno's x, y (0: grounded), Fox's x, y, Geno's inputs: (offset, frames, stick, cstick, buttons))
TESTS = [
    ('sh_over', -1.8, 0, 0, 0, [(0, 2, (0, 0), (0, 0), 'X'), (7, 2, (0, 0), (0, -80), '')]),
    ('fh_fall', -1.8, 0, 0, 0, [(0, 6, (0, 0), (0, 0), 'X'), (30, 2, (0, 0), (0, -80), '')]),
    ('air_muzzle', -1.8, 46, 0, 40, [(2, 2, (0, 0), (0, -80), '')]),
    ('air_tail', -1.8, 52, 0, 40, [(2, 2, (0, 0), (0, -80), '')]),
    ('tail_ground', -1.8, 37, 0, 0, [(2, 2, (0, 0), (0, -80), '')]),
]
ONLY = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
if ONLY:
    TESTS = [t for t in TESTS if t[0] in ONLY]
f = Film(len_s=(len(TESTS) * SLOT + 110) / 60)
f.setup(players=[('geno', dict(x=-2, face=1)), ('fox', dict(x=0, face=-1))], seed=5, coll=1)
geno, fox = f.port(0), f.port(1)
f.orbit(0, at=(0, 24, 0), dist=96, yaw=0, pitch=0, fov=30, ease='cut')
plan = []
for i, (label, gx, gy, fx, fy, steps) in enumerate(TESTS):
    t0 = 70 + i * SLOT
    f.reset(t0 - 30, 0, gx, 1); f.reset(t0 - 30, 1, fx, -1)
    f.percent(t0 - 28, 0, 0); f.percent(t0 - 28, 1, 60)
    if gy:                                            # placed in the air: jump first (a grounded fighter teleported snaps back)
        geno.hold(t0 - 20, 3, btn='X'); f.setpos(t0, 0, gx, gy); f.cue(t0, 'motion', 0, FALL)
    if fy:
        fox.hold(t0 - 20, 3, btn='X'); f.setpos(t0, 1, fx, fy); f.cue(t0, 'motion', 1, FALL)
    f.mark(t0, i, label)
    for at, n, stick, c, btn in steps:
        geno.hold(t0 + at, n, stick=stick, c=c, btn=btn)
    geno.trace(t0 - 2, t0 + 70); fox.trace(t0 - 2, t0 + 70)
    plan.append(dict(label=label, start=t0, frames=SLOT))
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
