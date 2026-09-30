"""Whirl shield lab: where the Geno Whirl goes after it meets a shield (Michael, 2026-09-29: "the spindown is moving too far
after it hits shield, ending up in a weird position past the character"). Geno throws side B from 40 units at a shielding
opponent; every case logs the disc against the shield every frame from the contact (GENO WHIRLPOS: phase, frame, the
disc's x y, the shielder's motion, shield centre, radius and health, the shielder's and Geno's x) and both fighters' POS.
    WS_CHAR=fox .venv/bin/python tools/machinima/melee/build.py projects/geno whirl_shield_lab
Cases, for the one shielder (WS_CHAR: mario, the small shield; fox; bowser, the big one):
  side    r: Geno on the left throwing right, l: on the right throwing left
  shield  hard: the trigger pressed fully (digital R, analog 1.0); light: the lightest analog shield (43/140, 0.307,
          just past the 0.3 dead zone: lightshield amount 0.01), no digital press
  health  full: 60; low: 40 (hard: ~30 at the contact after ~10 of its hold's decay) or 30 (light: it barely decays)
The shielder holds from 4 frames before the throw to 95 after (past the grind); each case opens with a sync slate.
WS_ONLY picks cases by label (e.g. r_hard_full,l_light_low).
"""
import json, os, sys
from dsl import Film

CHAR = os.environ.get('WS_CHAR', 'fox')
GENO, SH = 0, 1
DIST = 40                      # Geno to the shielder: the follow-in distance (DESIGN §5: "from 40 units he arrives mid-grind")
N = 190                        # frames a case: the disc is gone and side B free again (lock 30) well before the next throw
SYNC = 10
HOLD = 95
LIGHT = 43                     # the lightest analog shield: 43/140 = 0.307 > the 0.3 dead zone
HP = {('hard', 'full'): 60, ('hard', 'low'): 40, ('light', 'full'): 60, ('light', 'low'): 30}
CASES = [(side, sh, hp) for side in ('r', 'l') for sh in ('hard', 'light') for hp in ('full', 'low')]
ONLY = [x for x in os.environ.get('WS_ONLY', '').split(',') if x]
if ONLY:
    CASES = [c for c in CASES if '_'.join(c) in ONLY]

f = Film(len_s=(60 + N * len(CASES) + 30) / 60)
f.setup(players=[('geno', dict(x=-DIST / 2, face=1)), (CHAR, dict(x=DIST / 2, face=-1))], seed=5, coll=1)
geno, sh = f.port(GENO), f.port(SH)
f.orbit(0, at=(0, 22, 0), dist=150, yaw=0, pitch=0, fov=30, ease='cut')
t, plan = 60, []
for i, (side, shield, hp) in enumerate(CASES):
    d = 1 if side == 'r' else -1
    label = f'{side}_{shield}_{hp}'
    f.reset(t - 20, GENO, -d * DIST / 2, d); f.reset(t - 20, SH, d * DIST / 2, -d)
    f.percent(t - 18, GENO, 0); f.percent(t - 18, SH, 0)
    f.cue(t - 16, 'shieldhp', SH, HP[(shield, hp)])
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    if shield == 'hard':
        sh.shield(t - 4, HOLD + 4)
    else:                                   # analog only: no digital R (Port.state adds R whenever trig is set)
        for k in range(t - 4, t + HOLD):
            sh.tl[k] = (0, 0, 0, 0, 0, LIGHT)
    geno.hold(t, 3, stick=(60 * d, 0), btn='B')
    geno.trace(t - 2, t + N - 21); sh.trace(t - 2, t + N - 21)
    f.mark(t, i, label)
    plan.append(dict(label=label, start=t, frames=N - 20, sync=t - SYNC, char=CHAR, side=side, shield=shield, hp=hp))
    t += N
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
