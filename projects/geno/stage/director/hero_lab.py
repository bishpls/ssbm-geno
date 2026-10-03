"""Hero lab: the Forest Maze's art on the free camera, fighters parked out of frame (as icon_lab). Run widescreen (16:9,
t7's aspect) at res 2; each shot holds 40 frames (logged frame = t + 8 in the dump):
  0-39    t7's camera by its horizon: 10 degrees down (t7's horizon sits ~18% from the top), the stump half the width
          (the stump top's ellipse in t7 suggests 23 degrees, but the image model draws tops too open; at 23 degrees no
          sky can be in frame)
  40-79   the stump's base and roots, from the front left and below the top
  80-119  the ledge, close
  120-159 the cap from the front, a little below its rim (the gills)
  160-199 the earlier t7 camera (23 degrees down), for before/after with art pass 2's boards
    .venv/bin/python tools/machinima/melee/build.py projects/geno/stage hero_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --frames 200 --res 2 --widescreen --quiet
"""
import math, sys
from dsl import Film

SHOTS = [dict(eye=(0, 46.6, 286), at=(0, -5, -6), fov=30),
         dict(eye=(-150, -20, 190), at=(-10, -38, -20), fov=34),
         dict(eye=(110, 22, 105), at=(66, -6, 0), fov=32),
         dict(eye=(-18, 22, 78), at=(0, 25, 0), fov=34),
         dict(eye=(0, 111, 267), at=(0, -5, -6), fov=30)]
f = Film(len_s=205 / 60.0)
f.setup(players=[('fox', dict(x=-20, face=1)), ('falco', dict(x=20, face=-1))], stage='forest_maze', seed=1)
for port, x in ((0, -20), (1, 20)):
    f.setpos(1, port, x, 900.0)
f.freeze(2)
for i, s in enumerate(SHOTS):
    f.cam(i * 40, eye=s['eye'], at=s['at'], fov=s['fov'], ease='cut')
f.cue(200, 'end')
f.emit(sys.argv[1])
