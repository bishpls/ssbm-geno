"""Angled attacks lab: forward tilt and forward smash angled up, straight and down (the control stick's angle picks
AttackS3Hi/S/Lw and AttackS4Hi/S/Lw when the fighter has animations for them), each on a standing Fox. The director logs each
hit and Geno's motion state (STATUS), so the report shows which variant played.
    ANGLE_CAM=side|34 .venv/bin/python tools/machinima/melee/build.py projects/geno angles_lab
"""
import json, os, sys
from dsl import Film

GENO, FOX = 0, 1
cam = os.environ.get('ANGLE_CAM', 'side')
SLOT = 110
# (label, Geno's x, the stick: tilts ease to ~48, smashes flick to 80; up and down at about 30 degrees)
TESTS = [('ftilt_hi', -9, (44, 26), 'tilt'), ('ftilt_s', -9, (48, 0), 'tilt'), ('ftilt_lw', -9, (44, -26), 'tilt'),
         ('fsmash_hi', -10, (72, 42), 'smash'), ('fsmash_s', -10, (80, 0), 'smash'), ('fsmash_lw', -10, (72, -42), 'smash')]
f = Film(len_s=(len(TESTS) * SLOT + 110) / 60)
f.setup(players=[('geno', dict(x=-8, face=1)), ('fox', dict(x=0, face=-1))], seed=3, coll=1)
g = f.port(GENO)
if cam == '34':
    f.orbit(0, at=(-5, 8, 0), dist=40, yaw=35, pitch=6, fov=30, ease='cut')
else:
    f.cam(0, eye=(-4, 10, 70), at=(-4, 8, 0), fov=30, ease='cut')
plan = []
for i, (label, gx, stick, kind) in enumerate(TESTS):
    t0 = 70 + i * SLOT
    f.reset(t0 - 18, GENO, gx, 1); f.reset(t0 - 18, FOX, 0, -1)
    f.percent(t0 - 16, GENO, 0); f.percent(t0 - 16, FOX, 0)
    f.mark(t0, i, label)
    if kind == 'tilt':
        g.hold(t0, 4, stick=stick); g.hold(t0 + 2, 2, stick=stick, btn='A')   # the stick eases in, then A: a tilt
    else:
        g.hold(t0, 2, stick=stick, btn='A')                                   # a flick with A: a smash (uncharged)
    f.status(t0 + 6, GENO)                                                    # the motion state that played
    f.status(t0 + SLOT - 22, FOX)
    plan.append(dict(label=label, input=t0))
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
