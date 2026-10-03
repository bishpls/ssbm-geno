"""Icon lab: the Forest Maze with no fighters in frame, for the stage-select icon and the review's close-ups. The fighters
are parked high above the camera and frozen; the free camera holds three shots (frames 20, 60, 100 are logged frames
28, 68, 108 in the dump):
  0-39 the icon's framing (the stage's centre, the cap and the stump's top edge),
  40-79 a close-up of the ledge and the roots,
  80-119 a close-up of the cap.
    .venv/bin/python tools/machinima/melee/build.py projects/geno/stage icon_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --frames 120 --res 2 --quiet
"""
import sys
from dsl import Film

f = Film(len_s=125 / 60.0)
f.setup(players=[('fox', dict(x=-20, face=1)), ('falco', dict(x=20, face=-1))], stage='forest_maze', seed=1)
for port, x in ((0, -20), (1, 20)):
    f.setpos(1, port, x, 900.0)
f.freeze(2)
f.cam(0, eye=(0, 42, 250), at=(0, 12, 0), fov=30, ease='cut')
f.cam(40, eye=(88, 18, 95), at=(62, -8, 0), fov=30, ease='cut')
f.cam(80, eye=(-12, 44, 70), at=(0, 26, 0), fov=30, ease='cut')
f.cue(120, 'end')
f.emit(sys.argv[1])
