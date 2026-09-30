"""Star Road on Battlefield: recoveries from exact spots off the right ledge (~68, 0), placed in the air (setpos + Fall).
v1.3 rules: 20 travel frames, the ledge catches from travel frame 4 (facing it, and as for everyone only while descending: a
rising star pops over and catches it falling), a rising star slides up a wall, a level or falling one (or the stage's
underside) stops dead. Logged: GENO STARROAD angle / slide / bonk, Geno's path (POS) and state
(STATUS: 252 CliffCatch, 253 CliffWait; 35-ish FallSpecial).
    .venv/bin/python tools/machinima/melee/build.py projects/geno starroad_lab
"""
import json, os, sys
from dsl import Film

SLOT = 220
FALL = 29                                             # ftCo_MS_Fall
# (label, x, y, facing, aim during the fold)
TESTS = [
    ('sr_level_bonk', 82, -14, -1, (-80, 0)),         # under the ledge, straight at the stage: stops dead
    ('sr_rise_slide', 76, -30, -1, (-40, 70)),        # low and close, steeply up-left into the wall: slides up to the ledge
    ('sr_early_snap', 80, -8, -1, (-60, 60)),         # just under and out: catches the ledge a few frames into the travel
    ('sr_far_diag', 110, -20, -1, (-60, 60)),         # far out, 45 degrees back
    ('sr_far_level', 115, 2, -1, (-80, 0)),           # far out at ledge height, straight back
    ('sr_low_up', 90, -45, -1, (-20, 80)),            # low, nearly straight up
    ('sr_down_snap', 100, 22, -1, (-70, -35)),         # above and out, down-left into the ledge: catches mid-travel
    ('sr_steep_down', 82, 38, -1, (-35, -75)),         # high over the ledge, steeply down: catches mid-travel
]
ONLY = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
if ONLY:
    TESTS = [t for t in TESTS if t[0] in ONLY]
f = Film(len_s=(len(TESTS) * SLOT + 110) / 60)
f.setup(players=[('geno', dict(x=55, face=1)), ('fox', dict(x=-40, face=1))], stage='battlefield', seed=5, coll=1)
geno = f.port(0)
f.cam(0, eye=(75, -10, 240), at=(75, -12, 0), fov=35, ease='cut')
plan = []
for i, (label, x, y, face, aim) in enumerate(TESTS):
    t0 = 70 + i * SLOT
    f.reset(t0 - 40, 0, 55, 1)
    f.reset(t0 - 40, 1, -40, 1)
    geno.hold(t0 - 30, 3, btn='X')                    # airborne first: a grounded fighter teleported offstage snaps back
    f.mark(t0, i, label)
    f.setpos(t0, 0, x, y); f.cue(t0, 'face', 0, face); f.cue(t0, 'motion', 0, FALL)
    geno.hold(t0 + 2, 3, stick=(0, 80), btn='B')
    geno.hold(t0 + 6, 14, stick=aim)
    geno.trace(t0, t0 + 70)
    for k in (40, 70, 110):
        f.status(t0 + k, 0)
    plan.append(dict(label=label, input=t0))
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
