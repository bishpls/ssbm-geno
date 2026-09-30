"""Costume match: four Genos in four costumes play a one-stock match that ends as soon as it can (players 2-4 dropped
under the blast zone in turn), so the HUD shows each costume's stock icon and the results screen each panel's (DESIGN.md
§12 "Costumes"; gm_80168B34's frame 180 + costume). The winner's fanfare plays (dir_results_music).
    COSTUME_MATCH=0,1,2,3 .venv/bin/python tools/machinima/melee/build.py projects/geno costume_match_lab
Frames (director): the HUD with four stocks up to 70; drops at 80, 140 and 200; the match ends near 260; the results
screen opens about 200 frames later.
"""
import os, sys
from dsl import Film

cos = [int(c) for c in os.environ.get('COSTUME_MATCH', '0,1,2,3').split(',')]
X = [-45, -15, 15, 45][:len(cos)]
f = Film(len_s=16.0)
f.setup(players=[('geno', dict(x=x, face=1 if x < 0 else -1, color=c)) for x, c in zip(X, cos)], seed=5, stocks=1)
f.cam(0, eye=(0, 30, 260), at=(0, 15, 0), fov=35, ease='cut')
for k, port in enumerate(range(1, len(cos))):
    t = 80 + 60 * k
    f.port(port).hold(t - 8, 3, btn='X')                 # airborne, so the teleport takes
    f.setpos(t, port, 0, -260)
path = f.emit(sys.argv[1])
s = open(path).read()
assert 'const int dir_results_music = 0;' in s
open(path, 'w').write(s.replace('const int dir_results_music = 0;', 'const int dir_results_music = 1;'))
