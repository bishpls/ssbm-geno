"""Down smash lab: the twin Hand Cannons (both sides at once, frame 7) between two Foxes, one in front and one behind.
  - standing close and at the tip on both sides: both should be hit on the same frame;
  - rolls on both sides: each Fox rolls toward Geno (ending beside or past him) or away, and Geno's down smash is timed
    at several delays after the roll input; the log shows which rolls it covers on which side.
The director logs every hit (HIT frame attacker victim damage) and each fighter's state after a try.
    DS_CAM=side|34 .venv/bin/python tools/machinima/melee/build.py projects/geno dsmash_lab
"""
import json, os, sys
from dsl import Film

GENO, FRONT, BACK = 0, 1, 2
SLOT = 150
# (label, the Foxes' distance, their roll: None / 'toward' / 'away', Geno's input delay after the roll input)
TESTS = [('stand_close', 11, None, 0), ('stand_tip', 19, None, 0)]
TESTS += [(f'roll_toward_d{d}', 24, 'toward', d) for d in (12, 18, 24, 30)]
TESTS += [(f'roll_away_d{d}', 9, 'away', d) for d in (12, 18, 24, 30)]
ONLY = [x for x in os.environ.get('DS_ONLY', '').split(',') if x]
if ONLY:
    TESTS = [t for t in TESTS if t[0] in ONLY]

f = Film(len_s=(len(TESTS) * SLOT + 110) / 60)
f.setup(players=[('geno', dict(x=0, face=1)), ('fox', dict(x=20, face=-1)), ('fox', dict(x=-20, face=1))], seed=3, coll=1)
g, fr, bk = f.port(GENO), f.port(FRONT), f.port(BACK)
if os.environ.get('DS_CAM', 'side') == '34':
    f.orbit(0, at=(0, 8, 0), dist=90, yaw=30, pitch=8, fov=30, ease='cut')
else:
    f.cam(0, eye=(0, 12, 110), at=(0, 8, 0), fov=30, ease='cut')
plan = []
for i, (label, dist, roll, delay) in enumerate(TESTS):
    t0 = 70 + i * SLOT
    f.reset(t0 - 30, GENO, 0, 1)
    f.reset(t0 - 30, FRONT, dist, -1)
    f.reset(t0 - 30, BACK, -dist, 1)
    for p in (GENO, FRONT, BACK):
        f.percent(t0 - 28, p, 0)
    f.mark(t0, i, label)
    if roll:
        # a roll: shield, then the stick toward (forward for each Fox, who faces Geno) or away
        sx = 80 if roll == 'toward' else -80
        for port, face in ((fr, -1), (bk, 1)):
            port.hold(t0, 20, btn='R', dir=face)
            port.hold(t0 + 3, 3, stick=(sx, 0), btn='R', dir=face)
        g.hold(t0 + delay, 3, c=(0, -80))
    else:
        g.hold(t0, 3, c=(0, -80))
    for p in (GENO, FRONT, BACK):
        f.status(t0 + SLOT - 36, p)                   # before the next try's resets (SLOT - 30)
    plan.append(dict(label=label, t0=t0, dist=dist, roll=roll, delay=delay))
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
