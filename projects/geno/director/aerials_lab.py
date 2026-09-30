"""Aerials and specials lab (animation review): Geno beside a cast member on the same inputs, one move per slot, for
consecutive-frame strips of his aerials, their landings and his specials' body motion against the cast's.
  AERIALS_LAB   aerials (default): each aerial from a full hop (the whole animation, landing without an L-cancel), then from a
            short hop with the director's auto L-cancel (the halved landing), falls into aerials into landings into Wait
            specials: neutral B tapped and charged (ground and air, the timed release, the shield cancel), the Whirl, Star Road (up
            from the ground, diagonal from a jump), the Blast tapped, held to the widen and held into Geno Flash, the air
            Blast, and a charge started on the ground that walks off... not here: see AERIALS_LAB=seams
            seams: the ground/air switches mid-special (a charge carried off a platform edge by momentum is hard to stage,
            so a Beam charged in the air and landing, a Whirl thrown as he lands, a Finger Shot fired rising)
  AERIALS_CAST  the fighter beside him (default marth; none: Geno alone, closer); AERIALS_CAST_FACE -1 turns the cast member
            away (for the specials, so neither's projectiles cross the other); AERIALS_CAM side (default) or orbit (3/4,
            yaw 35); AERIALS_COLL 1 shows hitboxes and hurtboxes; AERIALS_ONLY a comma list of slot labels.
    AERIALS_LAB=aerials AERIALS_CAM=side .venv/bin/python tools/machinima/melee/build.py projects/geno aerials_lab
The plan (slot labels and their first frames) goes beside the script as aerials_lab.plan.json.
"""
import json, os, sys
from dsl import Film

LAB = os.environ.get('AERIALS_LAB', 'aerials')
CAST = os.environ.get('AERIALS_CAST', 'marth')
CAM = os.environ.get('AERIALS_CAM', 'side')
COLL = int(os.environ.get('AERIALS_COLL', '0'))
ONLY = [x for x in os.environ.get('AERIALS_ONLY', '').split(',') if x]

AIR = [('nair', (0, 0), 'A'), ('fair', (80, 0), ''), ('bair', (-80, 0), ''), ('uair', (0, 80), ''), ('dair', (0, -80), '')]
SLOTS = []                   # (label, frames, [(offset, frames, stick, cstick, btn)], auto-lcancel)
if LAB in ('aerials', 'all'):
    for name, c, b in AIR:
        SLOTS.append((f'{name}_fh', 110, [(0, 6, (0, 0), (0, 0), 'X'), (9, 2, (0, 0), c, b)], False))
    for name, c, b in AIR:
        SLOTS.append((f'{name}_sh', 90, [(0, 2, (0, 0), (0, 0), 'X'), (7, 2, (0, 0), c, b)], False))
    for name, c, b in AIR:
        SLOTS.append((f'{name}_sh_lc', 80, [(0, 2, (0, 0), (0, 0), 'X'), (7, 2, (0, 0), c, b)], True))
if LAB in ('specials', 'all'):
    SLOTS += [
        ('finger', 70, [(0, 2, (0, 0), (0, 0), 'B')], False),
        ('beam_full', 170, [(0, 64, (0, 0), (0, 0), 'B')], False),
        ('beam_auto', 170, [(0, 110, (0, 0), (0, 0), 'B')], False),
        ('beam_timed', 170, [(0, 62, (0, 0), (0, 0), 'B')], False),                  # released in star three's window
        ('beam_cancel', 150, [(0, 44, (0, 0), (0, 0), 'B'), (42, 30, (0, 0), (0, 0), 'R')], False),   # into shield (v1.4)
        ('air_finger', 80, [(0, 6, (0, 0), (0, 0), 'X'), (10, 2, (0, 0), (0, 0), 'B')], False),
        ('air_beam', 110, [(0, 6, (0, 0), (0, 0), 'X'), (8, 26, (0, 0), (0, 0), 'B')], False),
        ('whirl', 80, [(0, 3, (60, 0), (0, 0), 'B')], False),
        ('air_whirl', 90, [(0, 6, (0, 0), (0, 0), 'X'), (8, 3, (80, 0), (0, 0), 'B')], False),
        ('starroad_up', 130, [(0, 3, (0, 80), (0, 0), 'B')], False),
        ('starroad_diag', 140, [(0, 6, (0, 0), (0, 0), 'X'), (10, 3, (0, 80), (0, 0), 'B'), (14, 14, (60, 60), (0, 0), '')], False),
        ('blast_tap', 80, [(0, 3, (0, -60), (0, 0), 'B')], False),
        ('blast_widen', 90, [(0, 34, (0, -80), (0, 0), 'B')], False),
        ('flash', 190, [(0, 55, (0, -80), (0, 0), 'B')], False),
        ('air_blast', 90, [(0, 6, (0, 0), (0, 0), 'X'), (10, 3, (0, -80), (0, 0), 'B')], False),
    ]
if LAB in ('seams', 'all'):
    SLOTS += [
        ('beam_air_to_ground', 150, [(0, 2, (0, 0), (0, 0), 'X'), (7, 90, (0, 0), (0, 0), 'B')], False),
        ('whirl_landing', 90, [(0, 2, (0, 0), (0, 0), 'X'), (12, 3, (80, 0), (0, 0), 'B')], False),
        ('finger_rising', 80, [(0, 6, (0, 0), (0, 0), 'X'), (6, 2, (0, 0), (0, 0), 'B')], False),
        ('blast_landing', 100, [(0, 2, (0, 0), (0, 0), 'X'), (10, 30, (0, -80), (0, 0), 'B')], False),
        ('fall_nair_land', 110, [(0, 6, (0, 0), (0, 0), 'X'), (30, 2, (0, 0), (0, 0), 'A')], False),
    ]
if ONLY:
    SLOTS = [s for s in SLOTS if s[0] in ONLY]

# Geno in front (x +15), the cast member 30 behind him, both facing right: out of each other's reach (at 18 apart Marth's
# back and down airs hit him), each cropped from the frame by labs/aerials_strips.py. AERIALS_CAST=none: Geno alone, centred.
GX, CX = (15, -15) if CAST != 'none' else (0, 0)
total = 80 + sum(s[1] for s in SLOTS)
f = Film(len_s=total / 60 + 1)
CFACE = int(os.environ.get('AERIALS_CAST_FACE', '1'))    # -1: the cast member faces away (the specials: no crossfire)
players = [('geno', dict(x=GX, face=1))] + ([(CAST, dict(x=CX, face=CFACE))] if CAST != 'none' else [])
f.setup(players=players, seed=5, coll=COLL)
yaw = 35 if CAM == 'orbit' else 0
if CAST != 'none':      # a fixed wide shot (labs/aerials_strips.py crops each fighter from it by his logged position)
    f.orbit(0, at=(0, 20, 0), dist=110, yaw=yaw, pitch=0, fov=30, ease='cut')
else:                   # Geno alone, closer: a fixed shot that holds a full hop (cropped the same way)
    f.orbit(0, at=(0, 22, 0), dist=84, yaw=yaw, pitch=0, fov=30, ease='cut')
plan, t = [], 70
for i, (label, n, steps, lc) in enumerate(SLOTS):
    for p in range(len(players)):
        face = 1 if p == 0 else CFACE
        f.reset(t - 20, p, (GX, CX)[p], face)
        f.percent(t - 18, p, 0)
        for at, k, stick, c, btn in steps:
            f.port(p).hold(t + at, k, stick=stick, c=c, btn=btn, dir=face)
        if lc:
            f.port(p).auto(t, fastfall=False, lcancel=True)
            f.port(p).auto(t + n - 22, fastfall=False, lcancel=False)
        f.port(p).trace(t - 2, t + n - 1)
    f.mark(t, i, label)
    f.status(t + n - 25, 0)
    plan.append(dict(label=label, start=t, frames=n))
    t += n
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
