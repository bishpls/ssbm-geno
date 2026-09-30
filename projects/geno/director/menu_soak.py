"""Menu-path soak: the way a person plays. VS mode through the character select (Geno and Fox) and stage select, default
rules (items on, 2-minute timer), then seeded random play for both. The lab path (a debug VS match, items off, fresh
memory) missed two crashes this path hit (a missing costume table read; a stale fighter-var pointer).
    .venv/bin/python tools/machinima/melee/build.py projects/geno menu_soak
"""
import os, random, sys
from dsl import Menu

MIN = float(os.environ.get('SOAK_MIN', '2.2'))
rng = random.Random(int(os.environ.get('SOAK_SEED', '3')))
m = Menu(boot='vs', len_s=40.0 + MIN * 60)
m.goto(90, 0, 110, 'geno')
m.press(205, 0, 'A')
m.goto(215, 1, 110, 'fox')
m.press(330, 1, 'A')
m.press(360, 0, 'START')
m.hold(430, 0, 30, stick=(0, 80))
m.press(470, 0, 'A')
STICKS = [(0, 0), (80, 0), (-80, 0), (0, 80), (0, -80), (60, 60), (-60, 60), (60, -60), (-60, -60)]
for port, bias in ((0, 0.4), (1, 0.15)):
    t = 700
    while t < 600 + MIN * 3600:
        n = rng.randint(2, 24)
        r = rng.random()
        stick = rng.choice(STICKS)
        if r < bias:
            m.hold(t, port, n if rng.random() < 0.5 else 3, stick=stick, btn='B')
        elif r < bias + 0.25:
            m.hold(t, port, 3, stick=stick, btn=rng.choice(['A', 'A', 'Z']))
        elif r < bias + 0.4:
            m.hold(t, port, 2, stick=stick, btn='X')
        elif r < bias + 0.5:
            m.hold(t, port, n, stick=stick, btn='R')
        else:
            m.hold(t, port, n, stick=stick)
        t += n + rng.randint(0, 10)
end = int(600 + MIN * 3600)                   # the match (2-minute timer) ends around here; then Time!, the results screen
for t in range(end + 400, end + 1600, 120):   # leave the results screen (START) back to the character select
    m.press(t, 0, 'START')
    m.press(t + 60, 1, 'START')
m.emit(sys.argv[1])
