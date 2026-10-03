"""Reel lab: four level-9 CPUs (Geno, Fox, Pikachu, Ness) on the Forest Maze with the game's own camera and the stage's
music, for a review reel with game audio (frames + dsp.wav through ffmpeg).
    .venv/bin/python tools/machinima/melee/build.py projects/geno/stage reel_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --frames 1260 --res 2 --quiet
"""
import os, sys
from dsl import Film

N = int(os.environ.get('REEL_N', 1250))
f = Film(len_s=N / 60.0)
cast = [('geno', -45), ('fox', -15), ('pikachu', 15), ('ness', 45)]
f.setup(players=[(c, dict(x=x, face=1 if x < 0 else -1, cpu=9)) for c, x in cast], stage='forest_maze', seed=5, stocks=4,
        music=True)
f.game_camera()
f.cue(N - 5, 'end')
f.emit(sys.argv[1])
