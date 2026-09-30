"""Down B either-or lab (DESIGN changelog 2026-09-28): the release decides, a Fox standing where the mark lands.
  tap         B tapped: the single-column Blast, marked on frame 10
  rel15       B held to frame 15: one column, marked at the release (frame 16)
  rel30       held past the second star (24): three columns, marked at the release (31)
  rel30_far   the same with the stick forward at the release: the mark 75 ahead (the stick is read at the release)
  flash       held to the third star (48): Geno Flash, and no Blast
  air_tap     a full hop and a tap: the air release
  air_hold    placed high in the air, held: no Flash in the air, the widened Blast releases itself at the third star
              (a full hop lands before it, and grounded the third star is the Flash)
  air_low     a short hop, cast rising; air_high: a full hop and a double jump, cast near its apex
The air casts have a Fox standing on the floor under the mark: every column strikes the floor under its own mark.
  air_land_flash  a short hop, B held from the rise (star 2 in the air or just after), landing, held to 48: the Flash
  air_land_rel    the same released after the landing and the second star: the grounded three-column release
  ledge_walkoff_hold  a dash into a grounded charge that slides off the edge: airborne at 48, the Blast releases itself
                  (over the void: the columns sweep 50 down from his height)
  beam_land, whirl_land  the Beam's air charge and the air Whirl landing mid-move (the same air-to-ground switch)
  hop_land    the reference: plain short hops, Geno's and Fox's, landing together (the engine's own landing)
DOWNB_TRACE=1 logs FEET and HURT every frame (Fox's too in hop_land); each segment opens with a two-frame sync slate.
Every Blast case presses jump every other frame from well before its IASA, so the jump's first frame is the IASA
(release + 28). Logged: GENO BLAST release / star 2, GENO FLASH, GENO SPAWN blast / flash, MS, IHIT (Fox's damage).
    .venv/bin/python tools/machinima/melee/build.py projects/geno downb_lab
"""
import json, os, sys
from dsl import Film

GENO, FOX = 0, 1
GX = -30
DOWN, FWD = (0, -80), (80, -40)
# (label, frames, Geno's steps (offset, frames, stick, buttons), Fox's x or None, IASA probe from (offset) or None)
SEGS = [
    ('tap', 110, [(0, 3, DOWN, 'B')], GX + 50, 30),
    ('rel15', 110, [(0, 15, DOWN, 'B')], GX + 50, 36),
    ('rel30', 130, [(0, 30, DOWN, 'B')], GX + 50, 50),
    ('rel30_far', 130, [(0, 27, DOWN, 'B'), (27, 3, FWD, 'B'), (30, 4, FWD, '')], GX + 75, None),
    ('flash', 190, [(0, 55, DOWN, 'B')], GX + 30, None),
    ('air_tap', 130, [(0, 6, (0, 0), 'X'), (10, 3, DOWN, 'B')], GX + 50, None),
    ('air_hold', 150, [(2, 60, DOWN, 'B')], GX + 50, None),         # placed high (HIGH): airborne at the third star
    ('air_low', 110, [(0, 2, (0, 0), 'X'), (5, 3, DOWN, 'B')], GX + 50, None),          # a short hop, cast rising (~8 up)
    ('air_high', 150, [(0, 6, (0, 0), 'X'), (18, 3, (0, 0), 'X'), (36, 3, DOWN, 'B')], GX + 50, None),   # a double jump's apex
    # landing mid-charge: the charge carries on grounded (no landing lag, the count continues)
    ('air_land_flash', 190, [(0, 2, (0, 0), 'X'), (8, 55, DOWN, 'B')], GX + 30, None),   # short hop, held: the Flash
    ('air_land_rel', 130, [(0, 2, (0, 0), 'X'), (8, 36, DOWN, 'B')], GX + 50, None),     # released after the landing
    # a grounded charge carried off the edge by a run's slide: the air rule (the widened Blast releases itself at 48)
    ('ledge_walkoff_hold', 160, [(0, 24, (80, 0), ''), (24, 60, DOWN, 'B')], 0, None),
    # the other specials that land mid-move through the same switch: the Beam's air charge, the air Whirl
    ('beam_land', 150, [(0, 2, (0, 0), 'X'), (8, 60, (0, 0), 'B')], GX + 60, None),
    ('whirl_land', 110, [(0, 2, (0, 0), 'X'), (14, 3, (80, 0), 'B')], GX + 60, None),
    # the reference: a plain short hop's landing, Geno's and Fox's together (the engine's own landing, no special)
    ('hop_land', 80, [(0, 2, (0, 0), 'X')], GX + 30, None),
]
FOX_STEPS = {'hop_land': [(0, 2, (0, 0), 'X')]}
# a sync slate per segment: the stage hidden on magenta for two frames, SYNC frames before the segment's start (after
# the resets). The dump can lose a frame mid-run (pop_before: 686 images for a 690-frame script, the landing's image
# 3 frames early in the first segment and 5 in the second), so a strip finds each segment's own slate to line its
# images up with the log (labs/aerials_strips.py)
SYNC = 10
TRACE = bool(os.environ.get('DOWNB_TRACE'))                          # every frame: FEET (feet, anim frame), HURT (head)
START_X = {'ledge_walkoff_hold': 44}                                 # Geno's x at the segment's start (else GX)
HIGH = {'air_hold': 150}                                             # Geno's height at the segment's start
ONLY = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
if ONLY:
    SEGS = [s for s in SEGS if s[0] in ONLY]
f = Film(len_s=(70 + sum(s[1] for s in SEGS) + 40) / 60)
f.setup(players=[('geno', dict(x=GX, face=1)), ('fox', dict(x=GX + 50, face=-1))], seed=5, coll=1)
geno, fox = f.port(GENO), f.port(FOX)
f.orbit(0, at=(0, 22, 0), dist=150, yaw=0, pitch=0, fov=30, ease='cut')
t, plan = 70, []
for i, (label, n, steps, fx, probe) in enumerate(SEGS):
    f.reset(t - 20, GENO, START_X.get(label, GX), 1); f.reset(t - 20, FOX, fx, -1)
    f.percent(t - 18, GENO, 0); f.percent(t - 18, FOX, 30)
    if label in HIGH:                                # in the air first (a grounded fighter teleported snaps back)
        geno.hold(t - 16, 3, btn='X'); f.setpos(t, GENO, GX, HIGH[label]); f.cue(t, 'motion', GENO, 29)
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    for at, k, stick, btn in steps:
        geno.hold(t + at, k, stick=stick, btn=btn)
    for at, k, stick, btn in FOX_STEPS.get(label, []):
        fox.hold(t + at, k, stick=stick, btn=btn)
    if probe is not None:
        for k in range(probe, probe + 24, 2):
            geno.hold(t + k, 1, btn='X')
    geno.trace(t - 2, t + n - 1); fox.trace(t - 2, t + n - 1)
    if TRACE:
        for k in range(n):
            f.feet(t + k, GENO); f.shield(t + k, GENO)
            if label in FOX_STEPS:
                f.feet(t + k, FOX); f.shield(t + k, FOX)
    f.mark(t, i, label)
    plan.append(dict(label=label, start=t, frames=n, sync=t - SYNC))
    t += n
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
