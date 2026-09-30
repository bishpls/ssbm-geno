"""CPU soak: a level-9 CPU Geno against a level-9 CPU Kirby on Battlefield (SOAK_MIN minutes). The CPU plays from its
per-kind attack tables (Geno reads Mario's rows) and a CPU Kirby inhales and copies Geno.
    .venv/bin/python tools/machinima/melee/build.py projects/geno cpu_soak
SOAK_COLOR picks Geno's costume (default 0).
"""
import os, sys
from dsl import Film

MIN = float(os.environ.get('SOAK_MIN', '3'))
OPP = os.environ.get('SOAK_OPP', 'kirby')
f = Film(len_s=MIN * 60)
f.setup(players=[('geno', dict(x=-30, face=1, cpu=9, color=int(os.environ.get('SOAK_COLOR', 0)))), (OPP, dict(x=30, face=-1, cpu=9))], stage='battlefield', seed=11)
f.cam(0, eye=(0, 40, 260), at=(0, 25, 0), fov=30, ease='cut', track='mid')
for k in range(1, int(MIN * 6)):                      # a status line for each fighter every 10 s
    f.status(k * 600, 0); f.status(k * 600 + 1, 1)
f.emit(sys.argv[1])
