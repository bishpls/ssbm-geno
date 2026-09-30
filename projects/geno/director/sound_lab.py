"""Movement sounds: Geno jumps, double-jumps, lands, dashes, turns, rolls, spot-dodges and air-dodges, so the wooden
puppet sounds (bank 55, 550028-550052) play; the audio dump is checked against the synthesized WAVs.
    .venv/bin/python tools/machinima/melee/build.py projects/geno sound_lab
"""
import sys
from dsl import Film

f = Film(len_s=10.0)
f.setup(players=[('geno', dict(x=-20, face=1)), ('fox', dict(x=50, face=-1))], seed=5)
f.cam(0, eye=(0, 25, 220), at=(0, 15, 0), fov=30, ease='cut')
g = f.port(0)
g.hold(60, 3, btn='X'); g.hold(80, 3, btn='X')                  # jump, double jump, landing
g.hold(200, 3, stick=(80, 0))                                    # dash
g.hold(260, 3, stick=(-80, 0))                                   # turn
g.hold(330, 6, stick=(80, 0), btn='R')                           # roll
g.hold(420, 6, stick=(0, -80), btn='R')                          # spot dodge
g.hold(500, 3, btn='X'); g.hold(510, 4, stick=(60, 0), btn='R')  # air dodge
f.emit(sys.argv[1])
