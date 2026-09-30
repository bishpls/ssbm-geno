"""Two Genos on the character select: both pick him, player 2 presses X and Y (costume change; with one costume this spun
forever), then the match starts. Checks the costume searches settle on his single costume.
    .venv/bin/python tools/machinima/melee/build.py projects/geno css_dupe
"""
import sys
from dsl import Menu

m = Menu(boot='vs', len_s=22.0)
m.goto(90, 0, 110, 'geno')
m.press(205, 0, 'A')
m.goto(215, 1, 110, 'geno')
m.press(330, 1, 'A')
for k in range(4):
    m.press(360 + 30 * k, 1, 'X')
    m.press(375 + 30 * k, 1, 'Y')
m.press(520, 0, 'START')
m.hold(590, 0, 30, stick=(0, 80))
m.press(630, 0, 'A')
m.emit(sys.argv[1])
