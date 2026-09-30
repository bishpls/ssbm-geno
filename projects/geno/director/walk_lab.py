"""Locomotion lab: one fighter alone on Final Destination walks at each speed, dashes into a run and skids, dash-dances,
turns a run around and walks to a stop, with a close camera that follows it. Logged every frame: POS, the motion states,
and each foot bone's world position and axes (FEET lines), for the foot-slide check (labs/footslide.py).
    WALK_LAB=geno WALK_CAM=side .venv/bin/python tools/machinima/melee/build.py projects/geno walk_lab
WALK_LAB: the fighter (geno, mario, samus, fox...). WALK_CAM: side (the game's own view, close) or 34 (a 3/4 view from in
front of him). WALK_ONLY: a comma list of segments to keep (slow, middle, fast, run, dance, turn, stop, tap, tap6).
"""
import os, sys
from dsl import Film

who = os.environ.get('WALK_LAB', 'geno')
cam = os.environ.get('WALK_CAM', 'side')
only = [s for s in os.environ.get('WALK_ONLY', '').split(',') if s]

# (name, frames, x start, stick timeline: [(frame offset, frames, stick x)]); ramps avoid the smash (0.8 within 2 frames)
ramp = lambda x: [(0, 3, 24), (3, 3, (24 + x) // 2)]
# (name, frames, x start, stick timeline [(frame offset, frames, stick x)], camera lead [(frame offset, x)]). The tracking
# camera trails a moving fighter by speed x 7.3 (the director's 12% a frame), so the lead puts him back in frame
SEGS = [
    ('slow', 100, -70, [(0, 100, 26)], [(0, 2.4)]),                          # 0.33: WalkSlow at rate ~1.8
    ('middle', 90, -70, ramp(48) + [(6, 84, 48)], [(0, 4.4)]),               # 0.6: WalkMiddle at rate ~1.36
    ('fast', 90, -70, ramp(80) + [(6, 84, 80)], [(0, 7.3)]),                 # 1.0: WalkFast at rate ~1.43
    ('run', 110, -75, [(0, 70, 80)], [(0, 11.7), (70, 11.7), (95, 0)]),      # dash into a run, release: the skid
    ('dance', 110, -10, [(0, 9, 80), (9, 9, -80), (18, 9, 80), (27, 9, -80), (36, 9, 80), (45, 9, -80), (54, 9, 80),
                         (63, 9, -80)], [(0, 0)]),
    ('turn', 110, -60, [(0, 45, 80), (45, 50, -80)], [(0, 11.7), (45, 11.7), (75, -11.7), (95, -11.7), (110, 0)]),
    ('stop', 100, -60, ramp(80) + [(6, 30, 80), (60, 30, 44)], [(0, 7.3), (36, 7.3), (50, 0), (60, 4.4), (90, 4.4), (100, 0)]),
    ('tap', 60, -40, [(0, 2, 80)], [(0, 3)]),                                # a tapped dash, released: it plays out
    ('tap6', 60, -40, [(0, 6, 80)], [(0, 5)]),                               # held a little longer
]
if only:
    SEGS = [s for s in SEGS if s[0] in only]

T0 = 70
n = T0 + sum(s[1] + 20 for s in SEGS) + 30
f = Film(len_s=n / 60)
f.setup(players=[(who, dict(x=-70, face=1))], seed=5)
p = f.port(0)
t = T0
plan = []
cams = []
for name, dur, x0, sticks, lead in SEGS:
    f.reset(t - 12, 0, x0, 1)
    for off, k, sx in sticks:
        p.hold(t + off, k, stick=(sx, 0))
    f.mark(t, len(plan), name)
    plan.append((name, t, dur))
    cams += [(t + off if off else t - 12, x, off == 0) for off, x in lead]
    t += dur + 20
for s in range(T0 - 12, t):
    f.feet(s, 0)                                     # FEET lines every frame: each foot bone's world position and axes
p.trace(T0 - 12, t)
for k, (s, lead, cut) in enumerate(cams):
    ease = 'cut' if cut or k + 1 == len(cams) or cams[k + 1][2] else 'inout'     # cut at each shot, ease between leads
    if cam == 'side':
        f.cam(s, eye=(lead, 9, 62), at=(lead, 8, 0), fov=30, ease=ease, track='p0')
    else:                                            # 3/4 from in front of him (his face and right side as he walks right)
        f.orbit(s, at=(lead, 8, 0), dist=62, yaw=35, pitch=8, fov=30, ease=ease, track='p0')
f.emit(sys.argv[1])
import json
json.dump({'segments': plan, 'who': who, 'cam': cam}, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'))
