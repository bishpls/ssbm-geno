"""The prize screen (trailer shot 11.2): boot straight onto the challenger mode's prize screen (if/ifprize.c, IfPrize.usd and
SdPrize.usd's text), as the game's own unlock-only flow does (no human in the challenger record), and film it.
PRIZE=geno (default): Geno as the challenger, so his two messages (the unlock, then the mod's note; the decomp's
non-matching ifprize.c and an SdPrize.usd from datkit prize-geno) under his fanfare. PRIZE=N (a notification id, e.g. 0,
Jigglypuff's) raises that vanilla notification instead, for the before/after check. PRESS=F,F,... presses A at those loop
frames (each press shows the next message; the last one leaves); LEN seconds (default 14).
    eval "$(sh tools/machinima/melee/sandbox.sh NAME)"
    PRIZE=geno PRESS=420 .venv/bin/python tools/machinima/melee/build.py projects/geno/trailer prize_lab
    DOLPHIN_SLOTS=3 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol OUT --until 'DIRECTOR MENU END' --res 3 --quiet
"""
import os, sys
from dsl import Menu

p = os.environ.get('PRIZE', 'geno')
m = Menu(boot='prize', len_s=float(os.environ.get('LEN', 14.0)),
         prize=('geno', []) if p == 'geno' else ('puff', [int(x, 0) for x in p.split(',')]))
for f in [int(x) for x in os.environ.get('PRESS', '').split(',') if x]:
    m.press(f, 0, 'A')
m.emit(sys.argv[1])
