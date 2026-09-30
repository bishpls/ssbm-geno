"""Model review in game: Geno beside another fighter, idle (Wait) and then holding shield, each seen from the side camera and
from 3/4, for judging the production model under Melee's lighting (boots, cuffs, ankles in the shield pose's leg lean).
    MODEL_LOOK=mario MODEL_AT=2.5 MODEL_DIST=24 .venv/bin/python tools/machinima/melee/build.py projects/geno model_look
Frames: idle side 0-69, idle 3/4 70-139; shield side 140-219, shield 3/4 220-299 (Geno shields from frame 140).
MODEL_AT is the look height (2.5 the feet, 11 the face), MODEL_DIST the camera distance, MODEL_X half the spacing.
"""
import os, sys
from dsl import Film

opp = os.environ.get('MODEL_LOOK', 'mario')
at = float(os.environ.get('MODEL_AT', 2.5)); dist = float(os.environ.get('MODEL_DIST', 24))
x = float(os.environ.get('MODEL_X', 4)); pitch = float(os.environ.get('MODEL_PITCH', 5))
f = Film(len_s=5.0)
f.setup(players=[('geno', dict(x=-x, face=1)), (opp, dict(x=x, face=-1))], seed=5)
for t, yaw in ((0, 0), (70, 35), (140, 0), (220, 35)):
    f.orbit(t, at=(-x * 0.6, at, 0), dist=dist, yaw=yaw, pitch=pitch, fov=30, ease='cut')
f.port(0).hold(128, 172, btn='R')
f.emit(sys.argv[1])
