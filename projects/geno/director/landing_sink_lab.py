"""Landing sink lab: how far a fighter's body and feet go below the floor on the last air frame before landing, for a plain
short hop and for a short hop with B held through the landing (Link's bow, Mewtwo's Shadow Ball and Geno's Beam charge
carry on as the ground charge; Fox's laser ends in the ordinary landing). Four fighters side by side on Final Destination
do the same inputs at once; every frame logs POS and FEET (the ankle joints' world matrices). labs/landing_sink.py reads
the log.
    .venv/bin/python tools/machinima/melee/build.py projects/geno landing_sink_lab
SINK_WHO: the fighters (default link,mewtwo,geno,fox).
"""
import json, os, sys
from dsl import Film

WHO = os.environ.get('SINK_WHO', 'link,mewtwo,geno,fox').split(',')
XS = [-60, -20, 20, 60][:len(WHO)]
SEGS = [('hop', 70, []), ('hop_b', 110, [(6, 70, 'B')])]    # (name, frames, extra holds after the hop: offset, frames, buttons)
T0 = 70
f = Film(len_s=(T0 + sum(s[1] + 20 for s in SEGS) + 30) / 60)
f.setup(players=[(w, dict(x=x, face=1)) for w, x in zip(WHO, XS)], seed=5)
f.cam(0, eye=(0, 12, 190), at=(0, 10, 0), fov=30, ease='cut')
t, plan = T0, []
for name, dur, extra in SEGS:
    for i, x in enumerate(XS):
        f.reset(t - 14, i, x, 1)
        p = f.port(i)
        p.hold(t, 2, btn='X')                                  # a short hop (X let go inside jumpsquat)
        for off, k, btn in extra:
            p.hold(t + off, k, btn=btn)
    f.mark(t, len(plan), name)
    plan.append(dict(name=name, start=t, frames=dur))
    t += dur + 20
for s in range(T0 - 4, t):
    for i in range(len(XS)):
        f.feet(s, i)
for i in range(len(XS)):
    f.port(i).trace(T0 - 4, t)
f.emit(sys.argv[1])
json.dump(dict(who=WHO, segments=plan), open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
