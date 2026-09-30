"""Specials lab: every special and its variants, one at a time, logged by the specials' own OSReport lines (GENO SPAWN,
STAR, CANCEL, STARROAD) plus motion states, with the hitbox display on.
    .venv/bin/python tools/machinima/melee/build.py projects/geno specials_lab
"""
import json, os, sys
from dsl import Film

SLOT = 150
GENO, FOX = 0, 1
# (label, Geno's x, inputs: (frame offset, frames held, stick, cstick, buttons))
TESTS = [
    ('finger_tap', -30, [(0, 2, (0, 0), (0, 0), 'B')]),
    ('finger_hit', -30, [(0, 2, (0, 0), (0, 0), 'B')], 20),        # Fox 50 away: the shot connects
    ('finger_far', -30, [(0, 2, (0, 0), (0, 0), 'B')], 44),        # 74 away: near the end of its ~75 units
    ('finger_air_hit', -30, [(0, 2, (0, 0), (0, 0), 'X'), (10, 2, (0, 0), (0, 0), 'B')], 10),
    ('finger_air_late', -30, [(0, 2, (0, 0), (0, 0), 'X'), (15, 2, (0, 0), (0, 0), 'B')], 10),
    ('beam_1star', -30, [(0, 25, (0, 0), (0, 0), 'B')], 60),
    ('beam_2star', -30, [(0, 45, (0, 0), (0, 0), 'B')], 60),
    ('beam_3star', -30, [(0, 62, (0, 0), (0, 0), 'B')], 60),     # released inside star three's +-3 window: the timed bonus
    ('beam_auto', -30, [(0, 110, (0, 0), (0, 0), 'B')]),          # held past it: fires by itself on frame 64 (v1.4)
    # v1.4 has no store: the shield cancels the charge and its stars are lost, so the next tap is a plain Finger Shot
    ('beam_cancel', -30, [(0, 44, (0, 0), (0, 0), 'B'), (42, 3, (0, 0), (0, 0), 'R'), (70, 2, (0, 0), (0, 0), 'B')]),
    ('air_finger', -30, [(0, 2, (0, 0), (0, 0), 'X'), (10, 2, (0, 0), (0, 0), 'B')]),
    ('whirl', -30, [(0, 3, (60, 0), (0, 0), 'B')]),
    ('air_whirl', -30, [(0, 2, (0, 0), (0, 0), 'X'), (8, 3, (80, 0), (0, 0), 'B')]),
    ('starroad_up', -10, [(0, 3, (0, 80), (0, 0), 'B')]),
    ('starroad_fwd', -40, [(0, 3, (0, 80), (0, 0), 'B'), (10, 12, (80, 0), (0, 0), '')]),
    ('blast_tap', -30, [(0, 3, (0, -60), (0, 0), 'B')]),
    ('blast_widen', -30, [(0, 30, (0, -80), (0, 0), 'B')]),
    ('flash', -30, [(0, 55, (0, -80), (0, 0), 'B')]),
    ('starroad_air_diag', -30, [(0, 6, (0, 0), (0, 0), 'X'), (14, 3, (0, 80), (0, 0), 'B'), (20, 14, (60, 60), (0, 0), '')]),
]

ONLY = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
if ONLY:
    TESTS = [t for t in TESTS if t[0] in ONLY]
f = Film(len_s=(len(TESTS) * SLOT + 110) / 60)
f.setup(players=[('geno', dict(x=-30, face=1)), ('fox', dict(x=40, face=-1))], seed=5, coll=1)
geno, fox = f.port(GENO), f.port(FOX)
f.cam(0, eye=(0, 30, 200), at=(0, 25, 0), fov=30, ease='cut', track='p0')
plan = []
for i, (label, gx, steps, *fox_x) in enumerate(TESTS):
    t0 = 70 + i * SLOT
    f.reset(t0 - 18, GENO, gx, 1)
    f.reset(t0 - 18, FOX, fox_x[0] if fox_x else 60, -1)
    f.percent(t0 - 16, FOX, 0)
    f.mark(t0, i, label)
    for at, n, stick, c, btn in steps:
        geno.hold(t0 + at, n, stick=stick, c=c, btn=btn)
    f.status(t0 + SLOT - 22, GENO); f.status(t0 + SLOT - 21, FOX)
    plan.append(dict(label=label, input=t0))
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
