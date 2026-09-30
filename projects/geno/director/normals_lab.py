"""Normals lab: Geno throws every normal at a standing Fox, one at a time, with both reset between tries; the director logs
each hit's frame and damage, and labs/report_normals.py turns the log into measured frame data. A Fox jab on Geno first
calibrates input-to-hit timing (Fox's jab is frame 2).
    .venv/bin/python tools/machinima/melee/build.py projects/geno normals_lab
"""
import json, os, sys
from dsl import Film

SLOT = 100               # frames per try
GENO, FOX = 0, 1

# (label, Geno's x, Geno's facing, Fox's x, the attack input's offset, inputs: (frame offset, frames, stick, cstick, buttons))
# Aerials go in on the way down from a short hop, so they meet a standing Fox; uair meets a Fox in a full jump overhead
TESTS = [
    ('calib_fox_jab', -8, 1, 0, 0, None),
    ('jab1', -7, 1, 0, 0, [(0, 2, (0, 0), (0, 0), 'A')]),
    ('jab123', -7, 1, 0, 0, [(0, 2, (0, 0), (0, 0), 'A'), (8, 2, (0, 0), (0, 0), 'A'), (16, 2, (0, 0), (0, 0), 'A')]),
    ('ftilt', -9, 1, 0, 2, [(0, 4, (48, 0), (0, 0), ''), (2, 2, (48, 0), (0, 0), 'A')]),
    ('utilt', -4, 1, 0, 2, [(0, 4, (0, 50), (0, 0), ''), (2, 2, (0, 50), (0, 0), 'A')]),
    ('dtilt', -7, 1, 0, 5, [(0, 8, (0, -60), (0, 0), ''), (5, 2, (0, -60), (0, 0), 'A')]),
    ('dash', -26, 1, 0, 12, [(0, 12, (80, 0), (0, 0), ''), (12, 2, (80, 0), (0, 0), 'A')]),
    ('fsmash', -10, 1, 0, 0, [(0, 3, (0, 0), (80, 0), '')]),
    ('usmash', -3, 1, 0, 0, [(0, 3, (0, 0), (0, 80), '')]),
    ('dsmash', -7, 1, 0, 0, [(0, 3, (0, 0), (0, -80), '')]),
    ('dsmash_back', -7, -1, 0, 0, [(0, 3, (0, 0), (0, -80), '')]),
    ('nair', -5, 1, 0, 18, [(0, 2, (0, 0), (0, 0), 'X'), (18, 2, (0, 0), (0, 0), 'A')]),
    ('fair', -16, 1, 0, 12, [(0, 2, (0, 0), (0, 0), 'X'), (12, 2, (0, 0), (80, 0), '')]),        # at the tip (v1.2)
    ('bair', -16, -1, 0, 12, [(0, 2, (0, 0), (0, 0), 'X'), (12, 2, (0, 0), (-80, 0), '')]),
    ('uair', -1, 1, 0, 8, [(0, 2, (0, 0), (0, 0), 'X'), (8, 2, (0, 0), (0, 80), '')]),
    ('dair', -1, 1, 0, 33, [(0, 6, (0, 0), (0, 0), 'X'), (33, 2, (0, 0), (0, -80), '')]),
    ('grab_close', -7, 1, 0, 0, [(0, 2, (0, 0), (0, 0), 'Z'), (48, 3, (0, -80), (0, 0), '')]),   # grabs end in a throw: a reset
    # mid-grab leaves the engine's grab link stale, and every later grab breaks
    # v1.2 reach at the tip: each should connect from here (measured reach plus Fox's 4.65 of front body, less ~1.5)
    ('jab_tip', -19, 1, 0, 0, [(0, 2, (0, 0), (0, 0), 'A')]),
    ('ftilt_tip', -25, 1, 0, 2, [(0, 4, (48, 0), (0, 0), ''), (2, 2, (48, 0), (0, 0), 'A')]),
    ('dtilt_tip', -22, 1, 0, 5, [(0, 8, (0, -60), (0, 0), ''), (5, 2, (0, -60), (0, 0), 'A')]),
    ('fsmash_tip', -33, 1, 0, 0, [(0, 3, (0, 0), (80, 0), '')]),
    ('dsmash_tip', -20, 1, 0, 0, [(0, 3, (0, 0), (0, -80), '')]),
    ('grab_tip', -15, 1, 0, 0, [(0, 2, (0, 0), (0, 0), 'Z'), (48, 3, (0, -80), (0, 0), '')]),
    # root motion (the flagged actions): Geno's position before and after, from the status cues
    ('roll_f', -30, 1, 25, 0, [(0, 20, (0, 0), (0, 0), 'R'), (4, 3, (80, 0), (0, 0), 'R')]),
    ('roll_b', -10, 1, 25, 0, [(0, 20, (0, 0), (0, 0), 'R'), (4, 3, (-80, 0), (0, 0), 'R')]),
    ('dash_slide', -40, 1, 25, 12, [(0, 12, (80, 0), (0, 0), ''), (12, 2, (80, 0), (0, 0), 'A')]),
    ('fthrow', -7, 1, 0, 0, [(0, 2, (0, 0), (0, 0), 'Z'), (48, 3, (80, 0), (0, 0), '')]),
    ('bthrow', -7, 1, 0, 0, [(0, 2, (0, 0), (0, 0), 'Z'), (48, 3, (-80, 0), (0, 0), '')]),
    ('uthrow', -7, 1, 0, 0, [(0, 2, (0, 0), (0, 0), 'Z'), (48, 3, (0, 80), (0, 0), '')]),
    ('dthrow', -7, 1, 0, 0, [(0, 2, (0, 0), (0, 0), 'Z'), (48, 3, (0, -80), (0, 0), '')]),
]

ONLY = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]          # e.g. LAB_ONLY=grab_close,fthrow
if ONLY:
    TESTS = [t for t in TESTS if t[0] in ONLY or t[0] == 'calib_fox_jab']
f = Film(len_s=(len(TESTS) * SLOT + 110) / 60)
f.setup(players=[('geno', dict(x=-8, face=1)), ('fox', dict(x=0, face=-1))], seed=3, coll=1)
geno, fox = f.port(GENO), f.port(FOX)
f.cam(0, eye=(0, 14, 110), at=(0, 8, 0), fov=30, ease='cut', track='mid')
plan = []
for i, (label, gx, face_g, fx, a_at, steps) in enumerate(TESTS):
    t0 = 70 + i * SLOT                                # after the entry: resets need ground under the fighter
    f.reset(t0 - 18, GENO, gx, face_g)
    f.reset(t0 - 18, FOX, fx, -1 if gx < fx else 1)
    f.percent(t0 - 16, GENO, 0); f.percent(t0 - 16, FOX, 0)
    f.mark(t0, i, label)
    if steps is None:                                 # the calibration: Fox jabs Geno
        fox.hold(t0, 2, btn='A')
    else:
        for at, n, stick, c, btn in steps:
            geno.hold(t0 + at, n, stick=stick, c=c, btn=btn, dir=face_g)
    if label == 'uair':
        fox.hold(t0 - 6, 6, btn='X')                  # Fox full-jumps so Geno's up air meets him overhead
    if os.environ.get('LAB_TRACE'):                   # Fox's position every frame of the try (grab holds, throw paths)
        fox.trace(t0, t0 + 60)
    f.status(t0 + SLOT - 22, FOX)                     # Fox's percent and state after the try (throws log no hits)
    f.status(t0 - 2, GENO); f.status(t0 + SLOT - 24, GENO)   # Geno's position before and after (root motion)
    plan.append(dict(label=label, input=t0, attack=t0 + a_at, gx=gx, fx=fx))
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
