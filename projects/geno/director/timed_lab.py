"""Timed-release lab (DESIGN §4, §5): the Geno Beam released within +-3 frames of a star's flash (charge frames 20, 40,
60 from the press) deals +10% (the full Beam 17 -> 18.7), with a chime and a sparkle; a release at 57-59 counts as three
stars, timed; the auto-fire (frame 64) never is. Geno's and Kirby's copy, against a standing Fox.
  geno_early   B held 57 frames: released on charge frame 58, three stars, timed (18.7)
  geno_late    held 62: released on 63, timed (18.7)
  geno_miss    held 53: released on 54, two stars, untimed (11)
  geno_auto    held 110: it fires itself on 64, untimed (17)
  kirby_*      Kirby swallows Geno first (the copy), then the same holds
Logged: GENO/KBGE TIMED (the release), GENO BEAM timed (the boosted hitboxes), IHIT (the damage dealt).
    .venv/bin/python tools/machinima/melee/build.py projects/geno timed_lab
"""
import json, os, sys
from dsl import Film

KIRBY, GENO, FOX = 0, 1, 2
HOLDS = [('early', 57), ('late', 62), ('miss', 53), ('auto', 110)]
SLOT = 170
f = Film(len_s=(70 + 200 + 2 * len(HOLDS) * SLOT + 40) / 60)
f.setup(players=[('kirby', dict(x=-12, face=1)), ('geno', dict(x=6, face=-1)), ('fox', dict(x=40, face=-1))], seed=5)
kb, ge = f.port(KIRBY), f.port(GENO)
f.cam(0, eye=(0, 25, 220), at=(0, 12, 0), fov=30, ease='cut')
t = 70
f.mark(t, 0, 'swallow')                       # Kirby takes Geno's copy
f.reset(t - 18, KIRBY, -12, 1); f.reset(t - 18, GENO, 6, -1)
kb.hold(t, 35, btn='B'); kb.hold(t + 62, 6, stick=(0, -80))
t += 200
SYNC = 10                     # a sync slate per segment (fx/fxsync.py lines strips and reels up on it)
plan = []
for who, port in (('geno', GENO), ('kirby', KIRBY)):
    for label, hold in HOLDS:
        f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
        f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
        plan.append(dict(label=f'{who}_{label}', start=t, frames=SLOT, sync=t - SYNC))
        f.reset(t - 20, KIRBY, -60 if who == 'geno' else -30, 1)
        f.reset(t - 20, GENO, -30 if who == 'geno' else -75, 1)
        f.reset(t - 20, FOX, 40, -1)
        f.percent(t - 18, FOX, 0)
        f.mark(t, len(f.labels), f'{who}_{label}')
        f.port(port).hold(t, hold, btn='B')
        f.status(t + SLOT - 20, FOX)
        t += SLOT
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
