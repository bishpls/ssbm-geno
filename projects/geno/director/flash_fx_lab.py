"""Flash effects lab (geno-fx): Geno Flash's own look (projects/geno/fx/flash_model.py, EfGeData.dat FLASH_*): the
transform's yellow glow, the full-body cannon, the fireball from it (the sun, small), the sun growing with its hitbox (a
disc with a face, a corona of flame tongues), and the red flash as it ends; Fox standing at the sun:
  wide     down B held to the third star (48): the whole Flash on a wide camera (the sun reaches 38 across its radius)
  match    the same at match distance
  close    the same close on Geno: the glow, the cannon, the fireball leaving it
  end      close on the sun (its end and the finishing flash); FX_SEGS=match,end picks segments (default: the first three)
GENO_FLASH_MODEL=0 in the fighter build gives the donor's PK Flash (the "before"). Each segment opens with a sync slate.
FX_COLL=1 draws the collision display over the models (hitboxes red, hurtboxes yellow): the sun's hitbox as it grows.
    .venv/bin/python tools/machinima/melee/build.py projects/geno flash_fx_lab
"""
import json, os, sys
from dsl import Film

GENO, FOX = 0, 1
GX = -30
DOWN = (0, -80)
WIDE = dict(eye=(-5, 16, 210), at=(-5, 16, 0))
MATCH = dict(eye=(5, 14, 150), at=(5, 12, 0))
CLOSE = dict(eye=(-22, 12, 70), at=(-22, 11, 0))
END = dict(eye=(0, 15, 130), at=(0, 15, 0))              # close on the sun's end: the finishing flash
SEGS = [('wide', 215, WIDE), ('match', 215, MATCH), ('close', 130, CLOSE),   # the sun ends ~+172, its flashes to ~+195
        ('end', 215, END)]
ONLY = [x for x in os.environ.get('FX_SEGS', 'wide,match,close').split(',') if x]
SEGS = [s for s in SEGS if s[0] in ONLY]
SYNC = 10
f = Film(len_s=(70 + sum(s[1] for s in SEGS) + 40) / 60)
f.setup(players=[('geno', dict(x=GX, face=1)), ('fox', dict(x=GX + 30, face=-1))], seed=5,
        coll=int(os.environ.get('FX_COLL', '0')))
geno = f.port(GENO)
t, plan = 70, []
for label, n, cam in SEGS:
    f.reset(t - 20, GENO, GX, 1); f.reset(t - 20, FOX, GX + 30, -1); f.percent(t - 18, FOX, 0)
    f.cam(t - 20, fov=30, ease='cut', **cam)
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    geno.hold(t, 55, stick=DOWN, btn='B')
    f.mark(t, len(plan), label)
    plan.append(dict(label=label, start=t, frames=n, sync=t - SYNC))
    t += n
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
