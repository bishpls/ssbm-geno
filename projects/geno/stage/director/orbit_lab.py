"""Orbit lab: the Forest Maze from off the match axis, as the trailer's cameras see it (orbits around a trophy on the
stump, a diagonal battle view). The free camera holds each shot 3 frames: yaw -60 to +60 degrees every 10 around the
stump top (0, 12, -6), at 160 units, pitched 20 and then 30 degrees above it; fighters parked out of frame, the game
frozen (a still per shot). Shot k's settled image is dump frame 3k + 10.
    .venv/bin/python tools/machinima/melee/build.py projects/geno/stage orbit_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --frames 90 --res 1 --widescreen --quiet
"""
import math, sys
from dsl import Film

AT = (0.0, 12.0, -6.0); D = 160.0
SHOTS = [(p, y) for p in (20, 30) for y in range(-60, 61, 10)]
f = Film(len_s=(len(SHOTS) * 3 + 12) / 60.0)
f.setup(players=[('fox', dict(x=-20, face=1)), ('falco', dict(x=20, face=-1))], stage='forest_maze', seed=1)
for port, x in ((0, -20), (1, 20)):
    f.setpos(1, port, x, 900.0)
f.freeze(2)
for k, (p, y) in enumerate(SHOTS):
    pr, yr = math.radians(p), math.radians(y)
    eye = (AT[0] + D * math.sin(yr) * math.cos(pr), AT[1] + D * math.sin(pr), AT[2] + D * math.cos(yr) * math.cos(pr))
    f.cam(k * 3, eye=eye, at=AT, fov=30, ease='cut')
f.cue(len(SHOTS) * 3 + 6, 'end')
f.emit(sys.argv[1])
