"""Costume lab: four Genos, each in a costume, on Final Destination under the game's lighting, for judging the costumes
in game (DESIGN.md §12 "Costumes"; the recolours are projects/geno/model/costumes.py).
    COSTUME_LAB=0,1,2,3 .venv/bin/python tools/machinima/melee/build.py projects/geno costume_lab
COSTUME_LAB lists the four costume ids (the game's order), left to right.
Frames (director frames; the dump's f is about frame + 12):
    0-59     the line-up from the front, idle             60-119   from 3/4 in front
    120-179  from behind (the capes)                      180-239  at the game camera's distance (how they read in play)
    240-479  a close-up of each, 60 frames apiece (head and shoulders, 3/4)
    480-569  each in turn: a forward tilt (Hand Gun), a full hop, a forward smash, 3/4 wide
"""
import os, sys
from dsl import Film

cos = [int(c) for c in os.environ.get('COSTUME_LAB', '0,1,2,3').split(',')]
X = [-24, -8, 8, 24][:len(cos)]
f = Film(len_s=9.6)
f.setup(players=[('geno', dict(x=x, face=1, color=c)) for x, c in zip(X, cos)], seed=5)
f.orbit(0, at=(0, 9, 0), dist=112, yaw=0, pitch=4, fov=30, ease='cut')
f.orbit(60, at=(0, 9, 0), dist=112, yaw=32, pitch=6, fov=30, ease='cut')
f.orbit(120, at=(0, 9, 0), dist=112, yaw=160, pitch=6, fov=30, ease='cut')
f.cam(180, eye=(0, 30, 260), at=(0, 15, 0), fov=35, ease='cut')
for i, x in enumerate(X):
    f.orbit(240 + 60 * i, at=(x + 0.6, 11.5, 0), dist=26, yaw=28, pitch=6, fov=30, ease='cut')
f.orbit(480, at=(0, 10, 0), dist=120, yaw=20, pitch=5, fov=30, ease='cut')
for i in range(len(cos)):
    p = f.port(i)
    p.hold(482 + 4 * i, 3, stick=(48, 0), btn='A')          # forward tilt
    p.hold(512 + 4 * i, 2, btn='X')                          # full hop
    p.hold(542 + 4 * i, 2, c=(80, 0))                        # forward smash
f.emit(sys.argv[1])
