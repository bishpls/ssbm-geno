"""Finisher lab: the cast's comparable finishers on Fox, the kill lab's way (kill_lab.py: centre stage on Final
Destination, a sweep of percents at no DI and full perpendicular DI either side of the launch, a kill only if Fox dies
before he can act), to anchor Geno Flash's numbers (DESIGN §5). One finisher per build, its fighter on port 0:
  falcon   Falcon Punch (grounded)
  ganon    Warlock Punch (grounded)
  samus    a full Charge Shot (charged well past full, then fired)
  ness     a full PK Flash (held; the ball charges to 100 while B is held and bursts ~18 frames after the release)
    FINISHER=falcon [KILL_PCTS=30,40,...] [FIN_CAL=1] .venv/bin/python tools/machinima/melee/build.py projects/geno finisher_lab
    .venv/bin/python projects/geno/director/kill_lab.py --report RUN_DIR PLAN.json
FIN_CAL=1: one percent (50), no DI, and for PK Flash a spread of release frames, to find each finisher's contact frame
(the HIT/IHIT log) before a sweep. The DI inputs start 4 frames after contact, inside hitlag, as kill_lab's do.
"""
import json, math, os, sys
from dsl import Film

SLOT = int(os.environ.get('KILL_SLOT', '520'))    # longer for a late contact (the Charge Shot's +244): KILL_SLOT=800
FOX = 1
# name: (character, x, facing, inputs (offset, frames, stick, buttons), contact frame from the input, launch angle).
# Contact frames measured with FIN_CAL=1 (2026-09-29): Falcon Punch +52 (25%), Warlock Punch +70 (30%)
FINISHERS = {
    'falcon': ('falcon', -13, 1, [(0, 3, (0, 0), 'B')], 52, 44),
    'ganon': ('ganon', -14, 1, [(0, 3, (0, 0), 'B')], 70, 44),
    'samus': ('samus', -40, 1, [(0, 3, (0, 0), 'B'), (220, 3, (0, 0), 'B')], 244, 44),   # full (25%) at +244
    # (measured 2026-09-29: released on 124 the ball bursts on Fox at +144 with its full 36%; on 112, 35% at +132)
    'ness': ('ness', -8, 1, [(0, 124, (0, 0), 'B')], 144, 70),
}
name = os.environ.get('FINISHER', 'falcon')
char, fx, face, steps, hit, ang = FINISHERS[name]
PERCENTS = [int(q) for q in os.environ.get('KILL_PCTS', '40,60,80,100').split(',')]
DI = [('none', None), ('ccw', 90), ('cw', -90)]
CAL = os.environ.get('FIN_CAL') == '1'
tests = []
if CAL:
    variants = [steps]
    if name == 'ness':                                   # the release frame: when the ball bursts, and where
        variants = [[(0, r, (0, 0), 'B')] for r in (100, 106, 112, 118, 124, 130)]
    tests = [(f'{name}#{k}', v, 50, 'none', None) for k, v in enumerate(variants)]
else:
    tests = [(name, steps, q, di, rot) for q in PERCENTS for di, rot in DI]
f = Film(len_s=(len(tests) * SLOT + 110) / 60)
f.setup(players=[(char, dict(x=fx, face=face)), ('fox', dict(x=0, face=-1))], seed=11, coll=0)
shooter, fox = f.port(0), f.port(FOX)
f.cam(0, eye=(0, 40, 320), at=(0, 30, 0), fov=40, ease='cut', track='mid')
plan = []
for i, (m, st, q, di, rot) in enumerate(tests):
    t0 = 70 + i * SLOT
    f.reset(t0 - 18, 0, fx, face)
    f.reset(t0 - 18, FOX, 0, -1)
    f.percent(t0 - 16, 0, 0); f.percent(t0 - 16, FOX, q)
    f.mark(t0, i, f'{m}@{q}/{di}')
    for at, n, stick, btn in st:
        shooter.hold(t0 + at, n, stick=stick, btn=btn, dir=face)
    di_stick = (0, 0) if rot is None else (round(80 * math.cos(math.radians(ang + rot))), round(80 * math.sin(math.radians(ang + rot))))
    for k in range(hit + 4, hit + 190):
        stick = di_stick if k <= hit + 30 else (0, 0)
        btn = 'X' if k >= hit + 12 and (k - hit) % 3 == 0 else ''
        fox.hold(t0 + k, 1, stick=stick, btn=btn)
    for k in range(210 + max(0, hit - 100), SLOT - 70, 20):
        fox.hold(t0 + k, 4, stick=(0, -80))
    plan.append(dict(move=m, percent=q, di=di, input=t0))
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
