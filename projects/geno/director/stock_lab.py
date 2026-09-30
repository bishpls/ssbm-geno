"""Stock match: Geno against Fox, 2 stocks each, so the HUD shows Geno's stock icons; Fox is dropped under the blast zone
twice, the match ends on Geno's win, and the results screen shows his banner, panel icon, name and emblem.
    .venv/bin/python tools/machinima/melee/build.py projects/geno stock_lab
"""
import sys
from dsl import Film

f = Film(len_s=40.0)
f.setup(players=[('geno', dict(x=-30, face=1)), ('fox', dict(x=30, face=-1))], seed=5, stocks=2)
f.cam(0, eye=(0, 30, 260), at=(0, 15, 0), fov=35, ease='cut')
f.port(1).hold(100, 3, btn='X')                       # airborne, so the teleport takes
f.setpos(108, 1, 0, -260)
f.port(1).hold(460, 3, btn='X')
f.setpos(468, 1, 0, -260)
f.emit(sys.argv[1])
