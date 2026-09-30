"""Reflect lab (QA, 2026-09-30): Geno's projectiles against reflectors, absorbers and a powershield, on Final Destination.
Geno at x -40 facing right; the reflector at x 0 facing him (for the Blast at the mark, 50 ahead; for the Flash in the sun,
30 ahead). One reflector per build (REFLECTOR):
  fox, falco      the shine (down B, held from before contact)
  mario, doc      the cape (side B, pressed CAPE frames before contact)
  ness            PSI Magnet (down B, held: absorbs energy)
  power           Fox's powershield (shield pressed 1 frame before contact; a second test 2 frames)
  none            standing still: the calibration of each case's contact frame (REFLECT_CAL=1 lists them)
Cases: finger, beam1, beam2, beam3, beam_timed, whirl, whirl_press (the timed press as the disc meets the reflector),
whirl_after (side B pressed while the reflected disc is out, then again later: a crit on Geno? a second Whirl?),
whirl_grind (Fox only: the disc grinds his shield, then he shines out of it), blast, flash, blast_geno (the tap's
column taken over by the reflector at the mark while Geno stands under it: a taken-over column falls in place and can
hit him; Michael, 2026-09-30: the Blast stays reflectable). REFLECT_ITEMS=1 logs the items every frame (ITEMS).
Logged by the sandbox's QA lines (item.c / ftcoll.c: QA REFLECT, QA ABSORB) and the director's IHIT/HIT/MS lines.
    REFLECTOR=fox .venv/bin/python tools/machinima/melee/build.py projects/geno reflect_lab
"""
import json, os, sys
from dsl import Film

GENO, R = 0, 1
FWD, DOWN = (80, 0), (0, -80)
# contact frames with a standing Fox (from REFLECTOR=none; frames after Geno's first input)
C = dict(finger=20, beam1=40, beam2=62, beam3=82, beam_timed=56, whirl=36, whirl_press=36, whirl_after=36,
         whirl_grind=36, blast=86, flash=102, blast_geno=86)
C.update(json.loads(os.environ.get('REFLECT_C', '{}')))
GENO_IN = {                                   # Geno's inputs (offset, frames, stick, button)
    'finger': [(0, 2, (0, 0), 'B')],
    'beam1': [(0, 24, (0, 0), 'B')], 'beam2': [(0, 46, (0, 0), 'B')], 'beam3': [(0, 110, (0, 0), 'B')],
    'beam_timed': [(0, 40, (0, 0), 'B')],     # released on 41: two stars, timed (star 2 lights on 40)
    'whirl': [(0, 3, FWD, 'B')],
    'whirl_press': 'press',                   # side B, then side B again 2 frames before it meets the reflector
    'whirl_after': 'after',                   # side B, then side B again 15 and 40 frames after it's reflected
    'whirl_grind': [(0, 3, FWD, 'B')],
    'blast': [(0, 3, DOWN, 'B')],             # a tap: the mark 50 ahead (x 10)
    'blast_geno': [(0, 3, DOWN, 'B')],        # the same, and Geno set under the column after the release's IASA
    'flash': [(0, 8, DOWN, 'B'), (8, 60, (70, -20), 'B')],
}
SPOT = {'blast': 10, 'flash': -10, 'blast_geno': 14}             # where the reflector stands (else x 0)
REFL = os.environ.get('REFLECTOR', 'none')
CHAR = {'fox': 'fox', 'power': 'fox', 'falco': 'falco', 'mario': 'mario', 'doc': 'doc', 'ness': 'ness',
        'none': 'fox'}[REFL]
CASES = [c for c in os.environ.get('REFLECT_CASES', ','.join(C)).split(',') if c]
if REFL != 'fox':
    CASES = [c for c in CASES if c != 'whirl_grind']
CAPE = int(os.environ.get('CAPE', '7'))
SLOT = 300
tests = [(c, v) for c in CASES for v in ((1, 2) if REFL == 'power' else (0,))]
f = Film(len_s=(len(tests) * SLOT + 110) / 60)
f.setup(players=[('geno', dict(x=-40, face=1)), (CHAR, dict(x=0, face=-1))], seed=5)
geno, ref = f.port(GENO), f.port(R)
f.cam(0, eye=(0, 20, 220), at=(0, 15, 0), fov=30, ease='cut')
plan = []
for i, (case, v) in enumerate(tests):
    t0 = 70 + i * SLOT
    f.reset(t0 - 18, GENO, -40, 1); f.reset(t0 - 18, R, SPOT.get(case, 0), -1)
    f.percent(t0 - 16, GENO, 0); f.percent(t0 - 16, R, 0)
    f.cue(t0 - 10, 'stage', a=0); f.cue(t0 - 10, 'bgcolor', a=255, b=0, c=255)      # the sync slate (fx/fxsync.py)
    f.cue(t0 - 8, 'stage', a=1); f.cue(t0 - 8, 'bgcolor', a=0, b=0, c=0)
    f.mark(t0, i, f'{case}/{REFL}/{v}')
    c = C[case]
    steps = GENO_IN[case]
    if steps == 'press':
        steps = [(0, 3, FWD, 'B'), (c - 2, 3, FWD, 'B')]
    elif steps == 'after':
        steps = [(0, 3, FWD, 'B'), (c + 15, 3, FWD, 'B'), (c + 40, 3, FWD, 'B')]
    for at, n, stick, btn in steps:
        geno.hold(t0 + at, n, stick=stick, btn=btn)
    if case == 'blast_geno':
        f.setpos(t0 + 40, GENO, 8.0)                                    # under the column (x 10), after IASA 38
    if os.environ.get('REFLECT_ITEMS'):
        for k in range(SLOT - 40):
            f.items(t0 + k)
    if REFL in ('fox', 'falco', 'ness') and case != 'whirl_grind':
        ref.hold(t0 + c - 14, 40, stick=DOWN, btn='B')                 # the shine or magnet, held through contact
    elif REFL in ('mario', 'doc'):
        ref.hold(t0 + c - CAPE, 3, stick=(-80, 0), btn='B')            # the cape toward Geno
    elif REFL == 'power':
        ref.hold(t0 + c - v, 12, btn='R')                              # the shield, v frames before contact
    if case == 'whirl_grind' and REFL == 'fox':                        # the disc grinds his shield; he shines out of it
        ref.hold(t0 + c - 6, 14, btn='R')
        ref.hold(t0 + c + 8, 30, stick=DOWN, btn='B')
    plan.append(dict(case=case, reflector=REFL, variant=v, input=t0, contact=c,
                     label=f'{case}' + (f'_{v}' if REFL == 'power' else ''), start=t0, frames=SLOT, sync=t0 - 10))
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
