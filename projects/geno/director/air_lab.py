"""States lab: one fighter alone on Battlefield turning, jumping (full hop, short hop, drifting forward and back, double
jumps forward and back, a fast fall), crouching, going helpless after the up special, dropping through a platform and
teetering at the edge, with a close camera that follows it. Logged every frame: POS, the motion states and the foot bones
(FEET), for the planted-foot checks (labs/footslide.py) and strips (labs/walk_board.py).
    AIR_LAB=geno AIR_CAM=side .venv/bin/python tools/machinima/melee/build.py projects/geno air_lab
AIR_LAB: the fighter. AIR_CAM: side or 34. AIR_STAGE: fd (default: turn, hop, drift, djump, jumpb, crouch, helpless) or bf
(Battlefield: pass, teeter, fall). AIR_ONLY: a comma list of segments.
"""
import json, os, sys
from dsl import Film

who = os.environ.get('AIR_LAB', 'geno')
cam = os.environ.get('AIR_CAM', 'side')
only = [s for s in os.environ.get('AIR_ONLY', '').split(',') if s]
stage = os.environ.get('AIR_STAGE', 'fd')

# (name, frames, x, y, facing, [(frame offset, frames, stick, buttons)])
SEGS = [
    ('turn', 100, -20, 0, 1, [(10, 2, (-40, 0), ''), (40, 2, (40, 0), ''), (70, 2, (-40, 0), '')]),
    ('hop', 130, -30, 0, 1, [(5, 8, (0, 0), 'X'), (80, 1, (0, 0), 'X')]),                     # a full hop, a short hop
    ('drift', 150, -40, 0, 1, [(5, 8, (0, 0), 'X'), (14, 50, (80, 0), ''), (80, 8, (0, 0), 'X'), (89, 50, (-80, 0), '')]),
    ('djump', 170, -20, 0, 1, [(5, 8, (0, 0), 'X'), (28, 2, (80, 0), 'X'), (29, 30, (40, 0), ''),
                               (90, 8, (0, 0), 'X'), (113, 2, (-80, 0), 'X'), (114, 30, (-40, 0), ''),
                               (150, 6, (0, -80), '')]),                                     # a fast fall at the end
    ('jumpb', 90, -10, 0, 1, [(5, 3, (-50, 0), 'X'), (8, 60, (-50, 0), '')]),                  # a jump backward
    ('fall', 110, 8, 54.6, 1, [(5, 22, (60, 0), ''), (30, 40, (-70, 0), '')]),               # off the top platform: the falls
    ('crouch', 100, 0, 0, 1, [(10, 60, (0, -80), '')]),
    ('helpless', 170, 0, 0, 1, [(5, 8, (0, 0), 'X'), (22, 3, (0, 80), 'B'), (26, 60, (10, 0), '')]),
    ('pass', 90, -28.8, 27.4, 1, [(12, 3, (0, -80), '')]),                                   # the left platform
    ('teeter', 200, 50, 0, 1, [(5, 190, (26, 0), '')]),                                     # a slow walk to the edge
]
BF = ('pass', 'teeter', 'fall')
SEGS = [s for s in SEGS if (s[0] in BF) == (stage == 'bf') and (not only or s[0] in only)]

T0 = 70
n = T0 + sum(s[1] + 20 for s in SEGS) + 30
f = Film(len_s=n / 60)
f.setup(players=[(who, dict(x=-20, face=1))], stage='battlefield' if stage == 'bf' else 'final_destination', seed=5)
p = f.port(0)
t, plan = T0, []
for name, dur, x0, y0, face, inputs in SEGS:
    f.reset(t - 12, 0, x0, face)
    if y0: f.setpos(t - 11, 0, x0, y0)
    for off, k, stick, btn in inputs:
        p.hold(t + off, k, stick=stick, btn=btn)
    f.mark(t, len(plan), name)
    plan.append((name, t, dur))
    t += dur + 20
for s in range(T0 - 12, t):
    f.feet(s, 0)
p.trace(T0 - 12, t)
if cam == 'side':
    f.cam(0, eye=(0, 10, 74), at=(0, 9, 0), fov=32, ease='cut', track='p0')
else:
    f.orbit(0, at=(0, 9, 0), dist=74, yaw=35, pitch=8, fov=32, ease='cut', track='p0')
f.emit(sys.argv[1])
json.dump({'segments': plan, 'who': who, 'cam': cam}, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'))
