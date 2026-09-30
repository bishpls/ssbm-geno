"""Costume select: on the character select screen player 1 picks Geno and steps through every costume with X (the door's
portrait changes each time) until it wraps back to the first, then Y back once to the last; player 2 picks Geno and gets
a costume nobody holds; the match starts. Checks the portraits, the costume cycling past his last costume and the
duplicate search (DESIGN.md §12 "Costumes"). COSTUME_CSS_N is how many costumes the disc has (default 6).
    .venv/bin/python tools/machinima/melee/build.py projects/geno costume_css_lab
Loop frames: P1 has Geno from ~215; X at 240, 280, ... (costumes 1 .. N-1, then 0); Y 40 frames after the last X (N-1);
P2 picks 100 frames later; START 45 after that.
"""
import os, sys
from dsl import Menu

N = int(os.environ.get('COSTUME_CSS_N', 6))
m = Menu(boot='vs', len_s=(560 + 40 * N) / 60)
m.goto(90, 0, 110, 'geno')
m.press(205, 0, 'A')
for k in range(N):
    m.press(240 + 40 * k, 0, 'X')
t = 240 + 40 * N
m.press(t, 0, 'Y')
m.goto(t + 20, 1, 90, 'geno')
m.press(t + 115, 1, 'A')
m.press(t + 160, 0, 'START')
m.hold(t + 240, 0, 30, stick=(0, 80))
m.press(t + 280, 0, 'A')
m.emit(sys.argv[1])
