"""Team colours: on the character select screen player 1 picks Geno and turns team battle on (the MELEE/TEAM toggle at
the top left, which takes a free hand), and his Geno changes to the red team's costume (Mario's colours); player 2 then
picks Geno and joins the red team too, in the same costume. The game's per-character team row is ftgeno_costumes.h's
FTGE_COSTUME_RED/BLUE/GREEN (blue is his own costume 0). A one-team match can't start, so the lab ends on the screen.
    .venv/bin/python tools/machinima/melee/build.py projects/geno costume_team_lab
Loop frames: P1 picks at ~205 (blue), the toggle at ~290 (red), P2 picks at ~415 (red).
"""
import sys
from dsl import Menu

m = Menu(boot='vs', len_s=8.0)
m.goto(90, 0, 110, 'geno')
m.press(205, 0, 'A')                         # P1 places the token on Geno: the hand is free
m.goto(215, 0, 70, (-28.0, 23.2))           # the token stays put, so the steering drives the hand up-left into the corner
m.press(290, 0, 'A')                         # the toggle (the hand past x -25.5 and above y 22, mncharsel.c): TEAM
m.goto(300, 1, 110, 'geno')
m.press(415, 1, 'A')
m.emit(sys.argv[1])
