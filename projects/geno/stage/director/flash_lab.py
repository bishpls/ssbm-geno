"""Flash lab: a stage's background at real speed on a fixed free camera, framed on the sky and the treeline above the
fighters' heads (the x55 match camera's eye, raised and aimed up: its frame's bottom meets the fighters' plane at y ~ 50),
so the only change frame to frame is the background's own animation. FLASH_STAGE names the stage, FLASH_N the length.
The game isn't frozen (freezing would stop the background too); Fox and Falco stand below the frame.
    FLASH_STAGE=battlefield FLASH_N=600 .venv/bin/python tools/machinima/melee/build.py projects/geno/stage flash_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --frames N --res 1 --quiet
"""
import os, sys
from dsl import Film

N = int(os.environ.get('FLASH_N', 1800))
f = Film(len_s=N / 60.0 + 0.5)
f.setup(players=[('fox', dict(x=-40, face=1)), ('falco', dict(x=40, face=-1))], stage=os.environ.get('FLASH_STAGE', 'forest_maze'), seed=1)
# FLASH_CAM=match: the x55 match framing held still (the shooting star's close-up and its readability check)
# (FLASH_CAM=match25: the x25 framing, fighters at +-25)
if os.environ.get('FLASH_CAM') in ('match', 'match25'):
    x25 = os.environ.get('FLASH_CAM') == 'match25'
    f.setpos(1, 0, -25 if x25 else -55, 0.0); f.setpos(1, 1, 25 if x25 else 55, 0.0)
    f.cam(0, eye=(0, 27.6, 131.3) if x25 else (0, 25.7, 223.2), at=(0, 11.1, 0) if x25 else (0, 7.6, 0), fov=30, ease='cut')
else:
    f.cam(0, eye=(0, 60, 223), at=(0, 110, 0), fov=30, ease='cut')
f.cue(N, 'end')
f.emit(sys.argv[1])
