"""Down air as a rocket fist (Michael, 2026-09-29): does the flying fist hold up? Every case logs GENO FIST every frame of
AttackAirLw and LandingAirLw (decomp ftgeno.c: his position, the right hand's world position and scale, the hitboxes),
both fighters' POS and MS, and HIT/IHIT. The camera is fixed at match distance (150) with the hitbox display on; each
case opens with a two-frame sync slate.
  DF_GROUP=follow    the fist riding his fall: a short hop (down air rising), a full hop at the apex, late in the fall,
                     fast-falling before the move, fast-falling during it, rising after a double jump
  DF_GROUP=land      a landing on every frame of the move: placed high, fast-falling (3 units a frame), down air on the
                     next frame; drop j lands about j frames into it (j = 1..45)
  DF_GROUP=ground    a grounded Fox under him: short hops at three timings, a full hop late in the fall, a fast-falling
                     short hop, and drops placed low over him (fast-falling) that land on move frames 8-15, cutting the
                     fist's flight short
  DF_GROUP=platform  (Battlefield) fast-falling down airs onto the left platform, landing at six move frames
  DF_CHAR=ganon (or another of the cast) with DF_GROUP=land: that fighter's own down air through drops 8-30, to compare
                     how far the cast's limbs go into the floor on a landing mid-move
    DF_GROUP=land .venv/bin/python tools/machinima/melee/build.py projects/geno dair_fist_lab
"""
import json, os, sys
from dsl import Film

GROUP = os.environ.get('DF_GROUP', 'follow')
CHAR = os.environ.get('DF_CHAR', 'geno')        # the cast's down airs for comparison (DF_GROUP=land): ganon, falcon, ...
GENO, FOX = 0, 1
FALL = 29
DAIR = ((0, 0), (0, -80))                 # stick, cstick: the C-stick down in the air
FF = ((0, -80), (0, 0))
SYNC = 10
GX = -10
# (label, frames, Geno's steps (offset, frames, (stick, cstick), buttons), placed (x, y) or None, Fox's x, Fox's steps)
if GROUP == 'follow':
    CASES = [
        ('sh_rising', 110, [(0, 2, None, 'X'), (8, 2, DAIR, '')], None, 70, []),
        ('fh_apex', 130, [(0, 6, None, 'X'), (24, 2, DAIR, '')], None, 70, []),
        ('fh_late', 130, [(0, 6, None, 'X'), (36, 2, DAIR, '')], None, 70, []),
        ('ff_before', 130, [(0, 6, None, 'X'), (28, 1, FF, ''), (30, 2, DAIR, '')], None, 70, []),
        ('ff_during', 130, [(0, 6, None, 'X'), (24, 2, DAIR, ''), (31, 1, FF, '')], None, 70, []),
        ('dj_rising', 140, [(0, 6, None, 'X'), (16, 2, None, 'X'), (19, 2, DAIR, '')], None, 70, []),
    ]
elif GROUP == 'land':
    CASES = [(f'land_{j:02d}', 80, [(1, 1, FF, ''), (2, 2, DAIR, '')], (GX, 3.0 * j + 1.5), 70, []) for j in range(1, 46)
             if CHAR == 'geno' or 8 <= j <= 30]
elif GROUP == 'ground':
    CASES = [
        ('sh_1', 110, [(0, 2, None, 'X'), (6, 2, DAIR, '')], None, GX, []),     # down air on the short hop's first frames
        ('sh_4', 110, [(0, 2, None, 'X'), (9, 2, DAIR, '')], None, GX, []),
        ('sh_8', 110, [(0, 2, None, 'X'), (13, 2, DAIR, '')], None, GX, []),
        ('fh_late', 130, [(0, 6, None, 'X'), (44, 2, DAIR, '')], None, GX, []),
        ('sh_ff', 110, [(0, 2, None, 'X'), (9, 2, DAIR, ''), (14, 1, FF, '')], None, GX, []),
    ] + [(f'low_{j:02d}', 90, [(1, 1, FF, ''), (2, 2, DAIR, '')], (GX, 3.0 * j + 1.5), GX, []) for j in (8, 9, 10, 11, 12, 13, 15)]
    # placed low over him, fast-falling: the landing cuts the fist's flight short (8-15), the fist near the floor
else:                                      # Battlefield's left platform (x -57.6..-20, top 27.2)
    CASES = [(f'plat_{j:02d}', 80, [(1, 1, FF, ''), (2, 2, DAIR, '')], (-38, 27.2 + 3.0 * j + 1.5), 50, [])
             for j in (3, 6, 9, 12, 15, 20)]
ONLY = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
if ONLY:
    CASES = [c for c in CASES if c[0] in ONLY]

f = Film(len_s=(60 + sum(c[1] for c in CASES) + 30) / 60)
f.setup(players=[(CHAR, dict(x=GX, face=1)), ('fox', dict(x=70, face=-1))], seed=5, coll=1,
        stage='battlefield' if GROUP == 'platform' else 'final_destination')
geno, fox = f.port(GENO), f.port(FOX)
f.orbit(0, at=(0, 22, 0), dist=150, yaw=0, pitch=0, fov=30, ease='cut')
t, plan = 60, []
for i, (label, n, steps, placed, fx, fsteps) in enumerate(CASES):
    x0 = placed[0] if placed else GX
    f.reset(t - 20, GENO, x0, 1); f.reset(t - 20, FOX, fx, -1)
    f.percent(t - 18, GENO, 0); f.percent(t - 18, FOX, 60)
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    if placed:                             # in the air first (a grounded fighter teleported snaps back)
        geno.hold(t - 16, 3, btn='X'); f.setpos(t, GENO, placed[0], placed[1]); f.cue(t, 'motion', GENO, FALL)
    for at, k, sc, btn in steps:
        stick, c = sc if sc else ((0, 0), (0, 0))
        geno.hold(t + at, k, stick=stick, c=c, btn=btn)
    for at, k, sc, btn in fsteps:
        stick, c = sc if sc else ((0, 0), (0, 0))
        fox.hold(t + at, k, stick=stick, c=c, btn=btn)
    geno.trace(t - 2, t + n - 21); fox.trace(t - 2, t + n - 21)
    f.mark(t, i, label)
    plan.append(dict(label=label, start=t, frames=n - 20, sync=t - SYNC, group=GROUP, placed=placed))
    t += n
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
