"""Effects lab (projects/geno/fx): Geno's own effects in game, for before/after strips. Geno charges the Geno Beam at
Fox and releases it, filmed close on the barrel and then wide on the flight:
  timed3    B held 57: released on charge frame 58, three stars, timed: the rainbow stars at the barrel (EfGeData.dat
            generator 22000), and the full Beam
  timed1    held 17: released on 18, one star, timed
  untimed2  held 47: released on 48, two stars, untimed (no stars: the plain release)
  wide3     the timed full Beam again, on a wide camera (match distance), for its flight
  air3      a full hop, the charge held from the rise, timed: the charge's draw-in stars riding the barrel as he falls
The charge's draw-in stars (EfGeData.dat 22011+) show in every hold: a wave lands as each star lights.
A disc without EfGeData.dat plays the old placeholder (Samus's full-charge flash) in the same frames: the "before".
    [FX_COLL=1] .venv/bin/python tools/machinima/melee/build.py projects/geno fx_lab      (FX_COLL=1: hitboxes drawn)
"""
import json, os, sys
from dsl import Film

GENO, FOX = 0, 1
SHOTS = [('timed3', 57, 'close'), ('timed1', 17, 'close'), ('untimed2', 47, 'close'), ('wide3', 57, 'wide'),
         ('air3', 57, 'close')]     # air3: a full hop, then the charge held from its rise (the draw-in rides the barrel down)
SLOT = 150
f = Film(len_s=(70 + len(SHOTS) * SLOT + 30) / 60)
f.setup(players=[('geno', dict(x=-30, face=1)), ('fox', dict(x=40, face=-1))], seed=5, coll=int(os.environ.get('FX_COLL', 0)))
ge = f.port(GENO)
t = 70
# a sync slate per segment (downb_lab's): the stage hidden on magenta for two frames, SYNC frames before the segment's
# start. The dump drops images on heavy frames, so the strips and reels (fx/fxstrips.py, fx/fxreel.py) line each
# segment up on its own slate, not one constant offset
SYNC = 10
plan = []
for label, hold, cam in SHOTS:
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    plan.append(dict(label=label, start=t, frames=SLOT, sync=t - SYNC))
    f.reset(t - 20, GENO, -30, 1)
    f.reset(t - 20, FOX, 40, -1)
    f.percent(t - 18, FOX, 0)
    if cam == 'close':
        f.cam(t - 20, eye=(-16, 13, 58), at=(-16, 11, 0), fov=30, ease='cut')
    else:
        f.cam(t - 20, eye=(4, 16, 150), at=(4, 12, 0), fov=30, ease='cut')
    f.mark(t, len(f.labels), label)
    if label.startswith('air'):
        ge.hold(t - 8, 4, btn='X')
    ge.hold(t, hold, btn='B')
    f.status(t + SLOT - 20, FOX)
    t += SLOT
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
