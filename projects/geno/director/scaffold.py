"""Scaffold test for the new fighter kind (0x22): Geno's tables currently point at Mario's files, so this proves the plumbing
(spawn, load, animate, get hit, hit back) for a kind past the original roster before any Geno data exists."""
import sys
from dsl import Film

f = Film(len_s=8.0)
f.setup(players=[('geno', dict(x=-20, face=1)), ('fox', dict(x=20, face=-1))], seed=7)
geno, fox = f.port(0), f.port(1)
f.cam(0, eye=(0, 16, 120), at=(0, 10, 0), fov=30, ease='cut', track='mid')
geno.walk(0.5, 1.0, dir=1)
geno.jump(2.0, full=True)
fox.move(3.5, 'jab', dir=-1, mark=24)
geno.move(4.5, 'jab', dir=1, mark=24)
geno.move(5.5, 'fsmash', dir=1, mark=24)
fox.move(6.5, 'usmash', dir=-1, mark=24)
f.emit(sys.argv[1])
