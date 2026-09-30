"""The Forest Maze in the stage select, in VS mode's own menus. Two runs (SSS_RUN):
  look  (default): Fox and Falco picked, START; the stage select still, then the cursor onto the Forest Maze's icon (its
        name and hologram show), A: the match loads on it; a few seconds of it. Dump frames at res 1.
  flow: the same pick, then a 105 s match (past the music's loop at 91.2 s). Dump audio only (--audioonly).
  back: the same pick, an 8 s match, pause and quit (L+R+A+START), START through the results and the character select
        to the stage select, and START there with nothing hovered: a random stage. Log only.
The director logs SSS (the hovered entry and cursor), SCENE (with the selected StKind) and the stage's GRFOREST INIT.
    SSS_RUN=flow .venv/bin/python tools/machinima/melee/build.py projects/geno/stage sss_forest
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --audioonly --until 'DIRECTOR MENU END' --quiet
The cursor starts at (0, -13) and moves 0.03 x (|stick| - 30) a frame; the Forest Maze's icon is at (-11.2, -1.9) (under
Random) and Random's at (-14.1, 3.6) (MnSlMap.usd PositionModel).
"""
import os, sys
from dsl import Menu

run = os.environ.get('SSS_RUN', 'look')
# names: hover each target for 80 frames (res 1 frames) to measure where its name plate falls against the Forest Maze's
# icon; targets are icon centres (the hit test's), reached open loop at 1.5 (stick 80) and 0.3 (stick 40) units a frame
NAMES = [('forest_maze', -4.0, -9.1), ('battlefield', 1.3, -9.1), ('final_destination', 6.6, -9.1),
         ('dream_land', 12.3, -9.1), ('kongo_jungle_64', 22.9, -9.1), ('peach_castle', -16.5, 15.7),
         ('fountain', 3.3, 15.7)]
HOLD = 80


def goto(m, t, frm, to):
    """Stick holds from frm to to starting at frame t (x first, then y); returns the arrival frame."""
    for axis in (0, 1):
        d = to[axis] - frm[axis]
        sgn = 1 if d > 0 else -1
        n80 = int(abs(d) // 1.5); rem = abs(d) - 1.5 * n80; n40 = int(round(rem / 0.3))
        st = lambda v: (v * sgn, 0) if axis == 0 else (0, v * sgn)
        if n80: m.hold(t, 0, n80, stick=st(80)); t += n80
        if n40: m.hold(t, 0, n40, stick=st(40)); t += n40
    return t
MATCH_S = {'flow': 105.0, 'back': 8.0}.get(run, 5.0)
if run == 'names':
    m = Menu(boot='vs', len_s=10.0 + (560 + len(NAMES) * (HOLD + 30)) / 60.0)
    m.goto(90, 0, 110, 'fox'); m.press(205, 0, 'A'); m.goto(215, 1, 110, 'falco'); m.press(330, 1, 'A')
    m.press(360, 0, 'START')
    t, cur, plan = 560, (0.0, -13.0), []
    for name, x, y in NAMES:
        t = goto(m, t, cur, (x, y)); cur = (x, y)
        plan.append(dict(name=name, x=x, y=y, arrive=t, shot=t + HOLD - 5)); t += HOLD
    import json
    json.dump(dict(baseline=540, targets=plan), open(os.path.splitext(sys.argv[1])[0] + '.names.json', 'w'), indent=1)
    m.emit(sys.argv[1]); sys.exit(0)
m = Menu(boot='vs', len_s=40.0 + MATCH_S + (25.0 if run == 'back' else 0.0))
m.goto(90, 0, 110, 'fox')
m.press(205, 0, 'A')
m.goto(215, 1, 110, 'falco')
m.press(330, 1, 'A')
m.press(360, 0, 'START')
if run == 'look':                              # Battlefield first (a vanilla hologram at the same scale)
    m.hold(560, 0, 4, stick=(40, 40))          # -> (1.2, -11.8)
    m.hold(564, 0, 9, stick=(0, 40))           # -> (1.2, -9.1): Battlefield
    m.hold(700, 0, 8, stick=(-80, 0))          # -> x -10.8
    m.hold(708, 0, 1, stick=(-40, 0))          # -> x -11.1
    m.hold(709, 0, 4, stick=(0, 80))           # -> y -3.1
    m.hold(713, 0, 4, stick=(0, 40))           # -> y -1.9: the Forest Maze, under RANDOM
    a_at = 860
else:
    m.hold(560, 0, 8, stick=(-80, 0))          # -> x -12.0
    m.hold(568, 0, 3, stick=(40, 0))           # -> x -11.1
    m.hold(571, 0, 6, stick=(0, 80))           # -> y -4.0
    m.hold(577, 0, 7, stick=(0, 40))           # -> y -1.9: the Forest Maze
    a_at = 620
m.press(a_at, 0, 'A')
t = a_at + int(MATCH_S * 60) + 300              # the load, then the match
if run == 'back':
    m.press(t, 0, 'START')                     # pause
    m.hold(t + 30, 0, 40, btn='L+R+A+START', trig=140)   # quit: No Contest, then the results
    for k in range(8):                         # START (both players: the results wait for each) through the results to the
        m.press(t + 180 + 120 * k, 0, 'START') # character select (it keeps the picks), on to the stage select, and there
        m.press(t + 240 + 120 * k, 1, 'START') # START with nothing hovered: Random
m.emit(sys.argv[1])
