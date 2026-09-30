"""Dash feel: Geno and Fox each tap a dash and let go (the released dash plays out, then the skid), then a dash held
into a run and reversed (the run turnaround). Logged: POS every frame and the motion states.
    .venv/bin/python tools/machinima/melee/build.py projects/geno dash_lab
"""
import sys
from dsl import Film

f = Film(len_s=6.0)
f.setup(players=[('geno', dict(x=-60, face=1)), ('fox', dict(x=-60, face=1))], seed=5)
f.cam(0, eye=(0, 20, 260), at=(0, 10, 0), fov=35, ease='cut')
for port in (0, 1):
    p = f.port(port)
    p.hold(60, 2, stick=(80, 0))                   # a tapped dash, released
    p.trace(60, 110)
    f.reset(150, port, -60, 1)
    p.hold(170, 40, stick=(80, 0))                 # dash into a run, then reverse
    p.hold(210, 30, stick=(-80, 0))
    p.trace(170, 250)
f.emit(sys.argv[1])
