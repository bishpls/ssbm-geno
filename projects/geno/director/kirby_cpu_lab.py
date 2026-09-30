"""Kirby CPU lab: a level-9 CPU Kirby against a level-9 CPU Geno, one stock each (KB_STOCKS), until the match ends or
KB_MIN minutes: the CPU inhales and copies Geno, fires Kirby's Geno Beam, loses the copy to hits, copies again. The log
counts the copies (KBCOPY/KBLOSE), the copy's states (544-551) and shots (KBGE SPAWN), and the hits.
    KB_MIN=4 .venv/bin/python tools/machinima/melee/build.py projects/geno kirby_cpu_lab
"""
import os, sys
from dsl import Film

MIN = float(os.environ.get('KB_MIN', '4'))
STOCKS = int(os.environ.get('KB_STOCKS', '1'))
STAGE = os.environ.get('KB_STAGE', 'final_destination')
f = Film(len_s=MIN * 60)
f.setup(players=[('kirby', dict(x=-20, face=1, cpu=9)), ('geno', dict(x=20, face=-1, cpu=9))], stage=STAGE, seed=13,
        stocks=STOCKS)
f.cam(0, eye=(0, 40, 260), at=(0, 20, 0), fov=30, ease='cut', track='mid')
for k in range(1, int(MIN * 6)):                      # a status line for each fighter every 10 s
    f.status(k * 600, 0); f.status(k * 600 + 1, 1)
f.emit(sys.argv[1])
