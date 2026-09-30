"""Reference stills of the cast in neutral (Wait) from the game's side camera and orbiting, for art direction: how Melee's
models look and how their neutral stance turns toward the camera.
    CAST_LOOK=mario,marth .venv/bin/python tools/machinima/melee/build.py projects/geno cast_look
CAST_DIST (default 58) moves the camera in; CAST_X (default 9) sets how far apart they stand; CAST_AT (default 8) is the
height the camera looks at (2: the feet); CAST_PITCH (default 5) tilts it.
"""
import os, sys
from dsl import Film

chars = os.environ.get('CAST_LOOK', 'mario,marth').split(',')
f = Film(len_s=5.0)
x = float(os.environ.get('CAST_X', 9))
f.setup(players=[(chars[0], dict(x=-x, face=1)), (chars[1], dict(x=x, face=-1))], seed=5)
for t, yaw in ((0, 0), (80, 35), (140, 90), (200, -35), (260, 180)):
    f.orbit(t, at=(0, float(os.environ.get('CAST_AT', 8)), 0), dist=float(os.environ.get('CAST_DIST', 58)), yaw=yaw,
            pitch=float(os.environ.get('CAST_PITCH', 5)), fov=30, ease='cut')
f.emit(sys.argv[1])
