"""Charge-cancel lab: the Geno Beam's shield cancel beside Samus's charge shot and Mewtwo's Shadow Ball (Michael: shield-
cancellable as theirs, never stored), with Kirby's copy of Geno, all four on the same inputs, frame by frame.
  shield       charging 40 frames, then shield held: the cancel (8 frames), then the shield
  shield_tap   the same with a 2-frame tap: the cancel plays out into Wait
  roll         charging, then a sideways smash of the stick: the roll out of the charge
  air          a full hop, charging in the air, then shield: the air cancel into the fall (Samus can't charge in the air:
               her air B fires)
Geno and Kirby hold B to charge (Geno's fires on release); Samus and Mewtwo press it once. Logged: MS (every port's
states, for the cancel's length and hand-off), POS (the crops), GENO/KBGE CANCEL.
    .venv/bin/python tools/machinima/melee/build.py projects/geno cancel_lab
The plan (segments' first frames) goes beside the script as cancel_lab.plan.json. labs/aerials_strips.py and
labs/aerials_reel.py take --ports 0,1,2,3 --dist 140 --at 18 for it.
"""
import json, os, sys
from dsl import Film

GENO, SAMUS, MEWTWO, KIRBY = 0, 1, 2, 3
XS = {GENO: -33, SAMUS: -11, MEWTWO: 11, KIRBY: 33}
HOLDERS = (GENO, KIRBY)                       # hold B to charge
# (label, frames, [(offset, frames, stick, buttons, trigger)] for everyone, B's press or hold (offset, frames for holders))
SEGS = [
    ('shield', 130, [(40, 30, (0, 0), '', 140)], (0, 44)),
    ('shield_tap', 110, [(40, 2, (0, 0), '', 140)], (0, 44)),
    ('roll', 120, [(40, 3, (80, 0), '', 0)], (0, 44)),
    ('air', 150, [(0, 6, (0, 0), 'X', 0), (32, 3, (0, 0), '', 140)], (8, 30)),
]
ONLY = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
if ONLY:
    SEGS = [s for s in SEGS if s[0] in ONLY]
T_SWALLOW = 200
f = Film(len_s=(70 + T_SWALLOW + sum(s[1] for s in SEGS) + 40) / 60)
f.setup(players=[('geno', dict(x=6, face=-1)), ('samus', dict(x=-11, face=1)), ('mewtwo', dict(x=11, face=1)),
                 ('kirby', dict(x=-12, face=1))], seed=5)
f.orbit(0, at=(0, 18, 0), dist=140, yaw=0, pitch=0, fov=30, ease='cut')
t = 70                                        # Kirby takes Geno's copy first (the others well clear of the inhale)
f.reset(t - 18, KIRBY, -12, 1); f.reset(t - 18, GENO, 6, -1)
f.reset(t - 18, SAMUS, -60, 1); f.reset(t - 18, MEWTWO, 60, -1)
f.mark(t, 0, 'swallow')
f.port(KIRBY).hold(t, 35, btn='B'); f.port(KIRBY).hold(t + 62, 6, stick=(0, -80))
t += T_SWALLOW
plan = []
for i, (label, n, steps, (b_at, b_hold)) in enumerate(SEGS):
    for p in XS:
        f.reset(t - 20, p, XS[p], 1)
        f.percent(t - 18, p, 0)
        # B first: a later hold overrides an earlier one over its span, so the steps go on top, keeping B held where a
        # holder's charge overlaps them (a step written first would be erased by the B hold)
        f.port(p).hold(t + b_at, b_hold if p in HOLDERS else 2, btn='B')
        for at, k, stick, btn, trig in steps:
            held = p in HOLDERS and b_at <= at < b_at + b_hold
            f.port(p).hold(t + at, k, stick=stick, btn='+'.join(x for x in (btn, 'B' if held else '') if x), trig=trig)
            if held and at + k < b_at + b_hold:          # the rest of the charge after the step
                f.port(p).hold(t + at + k, b_at + b_hold - at - k, btn='B')
        f.port(p).trace(t - 2, t + n - 1)
    f.mark(t, i + 1, label)
    plan.append(dict(label=label, start=t, frames=n))
    t += n
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
