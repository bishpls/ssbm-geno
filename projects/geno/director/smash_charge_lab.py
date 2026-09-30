"""Smash charge lab: each smash (forward, up, down) uncharged, half charged and fully charged, on a standing Fox. A smash
charges while A is held from the script's smash_charge frame: the engine freezes the animation on that frame (the pose
players see for up to 60 frames), shakes the model and flashes, and scales the damage up to 1.367x at full charge. The
director logs Fox's percent after each try, for the damage check; the camera sits close on Geno for the held pose.
    SMASH_CAM=side|34 .venv/bin/python tools/machinima/melee/build.py projects/geno smash_charge_lab
SMASH_OPP picks the target (default fox); SMASH_WHO the fighter (default geno; mario etc. for the cast's held poses).
SMASH_ONLY picks tries (fsmash_half,...); SMASH_COLL=1 shows the hitboxes; SMASH_ANGLES=1 adds the angled forward smash.
"""
import json, os, sys
from dsl import Film

GENO, FOX = 0, 1
cam = os.environ.get('SMASH_CAM', 'side')
who = os.environ.get('SMASH_WHO', 'geno')
opp = os.environ.get('SMASH_OPP', 'fox')
SMASHES = [('fsmash', (80, 0), -10), ('usmash', (0, 80), -3), ('dsmash', (0, -80), -7)]
if os.environ.get('SMASH_ANGLES'):          # the angled Double Punch too (a flick up or down with A: AttackS4Hi / S4Lw)
    SMASHES += [('fsmash_hi', (72, 42), -10), ('fsmash_lw', (72, -42), -10)]
HOLDS = [('none', 2), ('half', 30), ('full', 70)]      # frames A is held (the charge caps at 60)
SLOT = 180

TESTS = [(f'{name}_{h}', stick, gx, n) for name, stick, gx in SMASHES for h, n in HOLDS]
ONLY = [x for x in os.environ.get('SMASH_ONLY', '').split(',') if x]      # e.g. SMASH_ONLY=fsmash_none,fsmash_half
if ONLY:
    TESTS = [t for t in TESTS if t[0] in ONLY]
f = Film(len_s=(len(TESTS) * SLOT + 110) / 60)
f.setup(players=[(who, dict(x=-8, face=1)), (opp, dict(x=0, face=-1))], seed=3, coll=int(os.environ.get('SMASH_COLL', 0)))
g, o = f.port(GENO), f.port(FOX)
if cam == '34':
    f.orbit(0, at=(-6, 8, 0), dist=34, yaw=35, pitch=6, fov=30, ease='cut')
else:
    f.cam(0, eye=(-4, 10, 62), at=(-4, 8, 0), fov=30, ease='cut')
plan = []
for i, (label, stick, gx, hold) in enumerate(TESTS):
    t0 = 70 + i * SLOT
    f.reset(t0 - 18, GENO, gx, 1)
    f.reset(t0 - 18, FOX, 0, -1)
    f.percent(t0 - 16, GENO, 0); f.percent(t0 - 16, FOX, 0)
    f.mark(t0, i, label)
    g.hold(t0, hold, stick=stick, btn='A')            # the stick flicks to the smash direction with A, and A stays held
    f.status(t0 + SLOT - 22, FOX)                     # Fox's percent after the try
    plan.append(dict(label=label, input=t0, hold=hold))
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
