"""Menu test: boot into VS mode, P1 picks Geno and P2 picks Fox on the character select screen, start, pick a stage."""
import sys
from dsl import Menu

m = Menu(boot='vs', len_s=30.0)
m.goto(90, 0, 110, 'geno')
m.press(205, 0, 'A')
m.goto(215, 1, 110, 'fox')
m.press(330, 1, 'A')
m.press(360, 0, 'START')
m.hold(430, 0, 30, stick=(0, 80))        # the stage select: up from the cursor's start onto a stage
m.press(470, 0, 'A')
m.emit(sys.argv[1])
