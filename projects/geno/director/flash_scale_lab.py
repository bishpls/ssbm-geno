"""Flash scale lab (geno-fx): how big Geno Flash's sun is drawn against its hitbox, frame by frame, on one far camera that
holds the whole sun (hitbox radius 8 -> 38, 14 above his feet). Ness's PK Flash, the cast's own big growing blast, from
the same spot for the margin the cast draws past such a hitbox. Nobody else is in frame.
  flash    Geno: down B held to the third star (the fireball, the sun's 40-frame growth, its 30-frame linger, the red flash)
  pkflash  Ness: PK Flash held to full (it bursts by itself)
    SCALE_COLL=0|2 SCALE_BG=black|stage [LAB_ONLY=flash,...] .venv/bin/python tools/machinima/melee/build.py projects/geno flash_scale_lab
SCALE_BG=black hides the stage (clean masks for fx/sunmeasure.py); SCALE_COLL=2 draws the collision capsules only, so a
coll 0 and a coll 2 run of the same build give the drawn and the hit sizes on the same frames. Each segment opens with a
sync slate (fx/fxsync.py).
"""
import json, os, sys
from dsl import Film

COLL = int(os.environ.get('SCALE_COLL', '0'))
BLACK = os.environ.get('SCALE_BG', 'black') == 'black'
GENO, NESS = 0, 1
SX = -30                     # the caster's spot; the sun's centre is 30 ahead, 14 up: (0, 14)
AWAY = -75                   # the other, left of the frame
CAM = dict(eye=(0, 14, 260), at=(0, 14, 0))      # 30 degrees: ~139 units tall, the sun's 38 plus its corona in view
DOWN = (0, -80)
SEGS = [('flash', GENO, 215, [(0, 55, DOWN, 'B')]),
        ('pkflash', NESS, 250, [(0, 150, (0, 0), 'B')])]
ONLY = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
if ONLY:
    SEGS = [s for s in SEGS if s[0] in ONLY]
SYNC = 10
f = Film(len_s=(90 + sum(s[2] for s in SEGS) + 40) / 60)
f.setup(players=[('geno', dict(x=SX, face=1)), ('ness', dict(x=AWAY, face=1))], seed=5, coll=COLL)
f.cam(0, fov=30, ease='cut', **CAM)
if BLACK:
    f.cue(1, 'stage', a=0); f.cue(1, 'bgcolor', a=0, b=0, c=0)
t, plan = 90, []
for label, caster, n, steps in SEGS:
    for p in range(2):
        f.reset(t - 24, p, SX if p == caster else AWAY, 1)
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=0 if BLACK else 1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    for at, k, stick, btn in steps:
        f.port(caster).hold(t + at, k, stick=stick, btn=btn)
    f.mark(t, len(plan), label)
    plan.append(dict(label=label, start=t, frames=n, sync=t - SYNC, caster=caster))
    t += n
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
