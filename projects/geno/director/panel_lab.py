"""Panel lab (Gate 2): Geno's forward tilt, up tilt, forward smash and up smash, 70 frames each, from 3/4 in front, to check
that the capelet's front panels ride the raised arm (the arm showed through them in Gate 1d).
    .venv/bin/python tools/machinima/melee/build.py projects/geno panel_lab
Frames: ftilt from 20, utilt from 90, fsmash from 160, usmash from 230.
"""
import os, sys
from dsl import Film

f = Film(len_s=5.2)
f.setup(players=[('geno', dict(x=-6, face=1)), ('mario', dict(x=30, face=-1))], seed=5)
f.orbit(0, at=(-5.5, 8.5, 0), dist=float(os.environ.get('PANEL_DIST', 30)), yaw=float(os.environ.get('PANEL_YAW', 40)),
        pitch=6, fov=30, ease='cut')
g = f.port(0)
g.hold(18, 4, stick=(48, 0)); g.hold(20, 2, stick=(48, 0), btn='A')       # forward tilt
g.hold(88, 4, stick=(0, 50)); g.hold(90, 2, stick=(0, 50), btn='A')       # up tilt
g.hold(160, 3, c=(80, 0))                                                 # forward smash
g.hold(230, 3, c=(0, 80))                                                 # up smash
f.emit(sys.argv[1])
