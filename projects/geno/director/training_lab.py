"""Training mode with Geno: its own character select (the 1P menu model, where he has his own icon joint), Geno for the
player, Fox for the CPU, stage select, then a few seconds of play. Checks he's selectable, loads, and training runs.
    .venv/bin/python tools/machinima/melee/build.py projects/geno training_lab
"""
import sys
from dsl import Menu

m = Menu(boot='training', len_s=30.0)
m.goto(90, 0, 110, 'geno')
m.press(205, 0, 'A')
m.goto(215, 0, 110, 'fox')                            # the CPU's pick
m.press(330, 0, 'A')
m.press(380, 0, 'START')
m.hold(450, 0, 30, stick=(0, 80))
m.press(490, 0, 'A')
for t in range(900, 1600, 40):                        # some play: move, attack, special
    m.hold(t, 0, 8, stick=(80, 0) if t % 80 else (-80, 0))
    m.press(t + 12, 0, 'B' if t % 120 == 0 else 'A')
m.emit(sys.argv[1])
