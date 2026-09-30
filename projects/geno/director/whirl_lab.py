"""Whirl lab: Geno Whirl's phases in game. The outbound hit, the shield grind (three hits, 13 frames apart), the hover,
the bend, and the follow-in (throw, dash after it, short-hop nair into the grinding shield: DESIGN v1.2 §7).
    .venv/bin/python tools/machinima/melee/build.py projects/geno whirl_lab
"""
import json, os, sys
from dsl import Film

SLOT = int(os.environ.get("LAB_SLOT", "160"))
GENO, FOX = 0, 1
# (label, Geno's x, Fox's x, Geno's inputs, Fox's inputs): inputs are (frame offset, frames, stick, cstick, buttons)
def _mash(start, end, btn, stick=(0, 0), every=2):
    return [(k, 1, stick, (0, 0), btn) for k in range(start, end, every)]


# SH on frame 0 (airborne from 3), the aerial on airborne 11, fast fall at the apex, L-cancel, then mash jump away
# contact ~+17 freezes both for 7 frames of hitlag, so the fast fall and the L-cancel come after it (~+24)
SHFFL_NAIR = [(0, 2, (0, 0), (0, 0), 'X'), (14, 2, (0, 0), (0, 0), 'A'), (25, 3, (0, -80), (0, 0), ''),
              (27, 2, (0, 0), (0, 0), 'L')] + _mash(31, 80, 'X')
# the crossup: drift forward, neutral A for nair (a forward stick makes it fair), then drift on and fast fall past him
SHFFL_NAIR_CROSS = [(0, 2, (0, 0), (0, 0), 'X'), (3, 11, (80, 0), (0, 0), ''), (14, 2, (0, 0), (0, 0), 'A'),
                    (16, 2, (80, 0), (0, 0), ''), (18, 3, (80, -80), (0, 0), ''), (21, 2, (80, 0), (0, 0), 'L')] + _mash(25, 70, 'X')
SHFFL_FAIR = [(0, 2, (0, 0), (0, 0), 'X'), (10, 2, (0, 0), (80, 0), ''), (18, 3, (0, -80), (0, 0), ''),
              (20, 2, (0, 0), (0, 0), 'L')] + _mash(24, 70, 'X')
SHIELD_GRAB = [(0, 30, (0, 0), (0, 0), 'R')] + [(k, 1, (0, 0), (0, 0), 'R+Z' if k % 2 == 0 else 'R') for k in range(30, 80)]  # shieldstun ends ~+31

TESTS = [
    ('whirl_hit', -30, 15, [(0, 3, (60, 0), (0, 0), 'B')], []),
    ('whirl_shield', -30, 5, [(0, 3, (60, 0), (0, 0), 'B')], [(0, 110, (0, 0), (0, 0), 'R')]),
    ('whirl_up', -30, 70, [(0, 3, (60, 70), (0, 0), 'B')], []),
    ('follow_in', -40, 5, [(0, 3, (60, 0), (0, 0), 'B'), (26, 20, (80, 0), (0, 0), ''), (46, 2, (0, 0), (0, 0), 'X'),
                           (49, 2, (0, 0), (0, 0), 'A')], [(0, 120, (0, 0), (0, 0), 'R')]),
    # the timed hit: side B again in flight arms a 4-frame window (contact ~37 frames in at this spacing); early voids it
    ('whirl_crit', -30, 15, [(0, 3, (60, 0), (0, 0), 'B'), (34, 2, (60, 0), (0, 0), 'B')], [], 60),
    ('whirl_crit_early', -30, 15, [(0, 3, (60, 0), (0, 0), 'B'), (26, 2, (60, 0), (0, 0), 'B')], [], 60),
    ('whirl_plain_60', -30, 15, [(0, 3, (60, 0), (0, 0), 'B')], [], 60),
    # the ground lane: bent down, it meets the floor and rolls into a grounded Fox 45 away
    ('whirl_roll', -30, 15, [(0, 3, (60, -70), (0, 0), 'B')], []),
    # Star Road v1.2: off the right edge, below the ledge, then straight back into the stage's side wall: a dead stop
    ('starroad_bonk', 60, -60, [(0, 12, (80, 0), (0, 0), ''), (12, 2, (80, 0), (0, 0), 'X'), (14, 8, (80, 0), (0, 0), ''),
                                 (44, 3, (0, 80), (0, 0), 'B'), (48, 16, (-80, 0), (0, 0), '')], []),
    ('starroad_ledge', 60, -60, [(0, 12, (80, 0), (0, 0), ''), (12, 2, (80, 0), (0, 0), 'X'), (14, 8, (80, 0), (0, 0), ''),
                                 (44, 3, (0, 80), (0, 0), 'B'), (48, 16, (-60, 60), (0, 0), '')], []),
    # shield safety in game: SH, nair, fast fall, L-cancel onto a shielding Fox who mashes shield grab; Geno mashes jump
    # away after landing (grabbed = Geno in a capture state; escaped = his jump comes first)
    ('shield_nair_front', -11, 0, SHFFL_NAIR, SHIELD_GRAB),
    ('shield_nair_cross', -10, 0, SHFFL_NAIR_CROSS, SHIELD_GRAB),
    ('shield_fair_tip', -24, 0, SHFFL_FAIR, SHIELD_GRAB),
    # the break rule: Fox meets the incoming Whirl with a jab (4%: it survives) or a forward smash (15%: it breaks)
    ('whirl_vs_jab', -30, 20, [(0, 3, (60, 0), (0, 0), 'B')], [(33, 2, (0, 0), (0, 0), 'A')]),
    ('whirl_vs_fsmash', -30, 22, [(0, 3, (60, 0), (0, 0), 'B')], [(18, 3, (0, 0), (-80, 0), '')]),
    # stored stars fade: two stars stored (shield), 170 frames later B fires the one that's left
    ('store_decay', -30, 70, [(0, 34, (0, 0), (0, 0), 'B'), (33, 3, (0, 0), (0, 0), 'R'), (210, 2, (0, 0), (0, 0), 'B')], []),
    # side B locked (30 frames after every Whirl ends): one ends ~97 frames in; side B just after is refused, 40 frames later it works
    ('whirl_lock', -30, 70, [(0, 3, (60, 0), (0, 0), 'B'), (104, 3, (60, 0), (0, 0), 'B'), (140, 3, (60, 0), (0, 0), 'B')], []),
    # no Blast below ledge height: off the right edge, falling, down B is refused
    ('blast_ledge', 60, -60, [(0, 12, (80, 0), (0, 0), ''), (12, 2, (80, 0), (0, 0), 'X'), (14, 8, (80, 0), (0, 0), ''),
                              (40, 3, (0, -80), (0, 0), 'B')], []),
    # helpless despawns the Whirl: throw it, then Star Road from the ground; helpless at the end of the travel
    ('whirl_helpless', -30, 70, [(12, 3, (60, 0), (0, 0), 'B'), (38, 3, (0, 80), (0, 0), 'B')], []),   # (after a lockout)
    # Geno Blast (down B): the mark lands ~50 ahead (stick neutral), 25 (back) or 75 (forward); the strike ~42 frames in
    ('blast_ground', -30, 20, [(0, 3, (0, -80), (0, 0), 'B')], []),
    ('blast_air', -30, 20, [(0, 3, (0, -80), (0, 0), 'B')], [(34, 6, (0, 0), (0, 0), 'X')]),
    ('blast_far', -30, 45, [(0, 3, (0, -80), (0, 0), 'B'), (6, 8, (80, -20), (0, 0), '')], []),
    ('blast_widen', -30, 34, [(0, 26, (0, -80), (0, 0), 'B')], []),
    # Geno Flash: down B held through the third star (~90 frames); the sun sits ~30 ahead. Fox at 0% and at 75%
    ('flash_hit', -30, 0, [(0, 100, (0, -80), (0, 0), 'B')], []),
    ('flash_75', -30, 0, [(0, 100, (0, -80), (0, 0), 'B')], [], 75),
]
ONLY = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
if ONLY:
    TESTS = [t for t in TESTS if t[0] in ONLY]

f = Film(len_s=(len(TESTS) * SLOT + 110) / 60)
f.setup(players=[('geno', dict(x=-30, face=1)), ('fox', dict(x=40, face=-1))], seed=7, coll=1)
geno, fox = f.port(GENO), f.port(FOX)
f.cam(0, eye=(0, 20, 170), at=(0, 15, 0), fov=30, ease='cut', track='mid')
plan = []
for i, (label, gx, fx, gsteps, fsteps, *pct) in enumerate(TESTS):
    t0 = 70 + i * SLOT
    f.reset(t0 - 18, GENO, gx, 1)
    f.reset(t0 - 18, FOX, fx, -1)
    f.percent(t0 - 16, FOX, pct[0] if pct else 0)
    f.mark(t0, i, label)
    for at, n, stick, c, btn in gsteps:
        geno.hold(t0 + at, n, stick=stick, c=c, btn=btn)
    for at, n, stick, c, btn in fsteps:
        fox.hold(t0 + at, n, stick=stick, c=c, btn=btn)
    for k in (20, 40, 60, 80, 100, 120):
        f.status(t0 + k, FOX)
    plan.append(dict(label=label, input=t0))
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
