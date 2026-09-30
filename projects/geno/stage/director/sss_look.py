"""Stage select look: VS mode, Fox and Falco picked on the character select, START, then the stage select screen held
still (the cursor's start), then the cursor pushed up onto the top rows so a stage's name and preview show.
    .venv/bin/python tools/machinima/melee/build.py projects/geno/stage sss_look
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --frames 760 --res 1 --quiet
"""
import sys
from dsl import Menu

m = Menu(boot='vs', len_s=14.0)
m.goto(90, 0, 110, 'fox')
m.press(205, 0, 'A')
m.goto(215, 1, 110, 'falco')
m.press(330, 1, 'A')
m.press(360, 0, 'START')
m.hold(560, 0, 24, stick=(0, 80))          # up from (0, -13): 1.5 units a frame (0.03 x (80 - 30))
m.emit(sys.argv[1])
