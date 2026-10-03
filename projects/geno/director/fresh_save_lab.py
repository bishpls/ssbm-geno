"""Fresh-save checks for the release: what a player sees with no unlocks, and what the play build does to a memory card.
FRESH_RUN picks the run (each its own build):
  vs        (default) a fresh save (unlock=False: Melee's own 11 unlockables stay locked): VS mode's character select
            (Geno's icon), Geno and Fox picked, START, the stage select (the Forest Maze's icon at the bottom row's left
            end), the cursor onto it, A: the match loads on it. Dump at res 1.
  classic, adventure, allstar
            the 1P modes' character select, reached through the main menu (1P Mode, Regular Match, then the mode; booted
            into directly, the 1P modes assert in lbarchive.c), on a fresh save (All-Star with everything unlocked: a
            fresh save doesn't offer it). Geno is hidden there: their save records have no row for him. Dump at res 1.
  random    a fresh save, the same picks, then START with nothing hovered on the stage select (Random), a short match,
            pause and quit (L+R+A+START), START through the results to the character select and the stage select, and
            Random again, RANDOM_N times (default 6). Log only: SCENE lines carry each match's StKind (0x15: the Forest
            Maze).
  card      the play build's boot (unlock=True, straight into VS mode), with a memory card in slot A (dolphin.py
            DOLPHIN_SLOTA=8: a GCI folder): Geno and Fox, the Forest Maze, an 8 s match, pause and quit, START through the
            results back to the character select. Hash the card folder before and after: a new or changed .gci is the
            game writing its save (VS mode marks the save dirty after a match: gm_1BFA.c lbCardGame_SetupArchive), and
            this boot never loaded the card (GM_BOOT, where gmboot.c loads it, is skipped).
  cardboot  the positive control for card: the game's own boot (GM_BOOT: the memory-card check, the opening, the
            title) with the card in slot A, A pressed every second through its prompts (create the save data, skip the
            opening, the title, into the menus). A .gci appearing proves the emulated card takes the game's writes.
  back      the play build's boot: hold B on the character select (back to VS mode's menu), then down to Name Entry and
            into its keyboard (the ♡ and ♪ keys), as a player would go. Dump at res 1.
    FRESH_RUN=vs .venv/bin/python tools/machinima/melee/build.py projects/geno fresh_save_lab
    DOLPHIN_SLOTS=3 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --until 'DIRECTOR MENU END' --res 1 --quiet
The stage select's cursor starts at (0, -13) and moves 0.03 x (|stick| - 30) a frame; the Forest Maze's icon is at
(-4.0, -9.1) (stage/director/sss_forest.py).
"""
import os, sys
from dsl import Menu

run = os.environ.get('FRESH_RUN', 'vs')


def goto(m, t, frm, to):
    """Stick holds from frm to to starting at frame t (x first, then y); returns the arrival frame (sss_forest.py)."""
    for axis in (0, 1):
        d = to[axis] - frm[axis]
        sgn = 1 if d > 0 else -1
        n80 = int(abs(d) // 1.5); rem = abs(d) - 1.5 * n80; n40 = int(round(rem / 0.3))
        st = lambda v: (v * sgn, 0) if axis == 0 else (0, v * sgn)
        if n80: m.hold(t, 0, n80, stick=st(80)); t += n80
        if n40: m.hold(t, 0, n40, stick=st(40)); t += n40
    return t


def pick(m):
    """Geno on port 0 and Fox on port 1 (both human, as the labs drive them), then START to the stage select"""
    m.goto(90, 0, 110, 'geno'); m.press(205, 0, 'A')
    m.goto(215, 1, 110, 'fox'); m.press(330, 1, 'A')
    m.press(360, 0, 'START')


def quit_to_css(m, t, presses=8):
    """pause, quit (No Contest), then START on both ports through the results to the character select (it keeps the
    picks) and on to the stage select; returns the frame after the last press"""
    m.press(t, 0, 'START')
    m.hold(t + 30, 0, 40, btn='L+R+A+START', trig=140)
    for k in range(presses):
        m.press(t + 180 + 120 * k, 0, 'START'); m.press(t + 240 + 120 * k, 1, 'START')
    return t + 180 + 120 * presses


if run in ('classic', 'adventure', 'allstar'):
    m = Menu(boot='menu', len_s=10.0, unlock=(run == 'allstar'))
    m.press(120, 0, 'A')                           # the main menu: 1P Mode
    m.press(190, 0, 'A')                           # Regular Match
    t = 280
    for k in range(('classic', 'adventure', 'allstar').index(run)):
        m.press(t, 0, 'DD'); t += 45               # Classic, Adventure, All-Star
    m.press(t, 0, 'A')
elif run == 'vs':
    m = Menu(boot='vs', len_s=22.0, unlock=False)
    pick(m)
    goto(m, 560, (0.0, -13.0), (-4.0, -9.1))
    m.press(700, 0, 'A')                       # held still on the icon a moment first: the name and hologram show
elif run == 'random':
    n = int(os.environ.get('RANDOM_N', '6'))
    m = Menu(boot='vs', len_s=12.0 + n * 26.0, unlock=False)
    pick(m)
    m.press(560, 0, 'START')                   # nothing hovered: Random
    t = 560
    for i in range(n - 1):
        t = quit_to_css(m, t + 600)            # a ~6 s match after the load, then back to the stage select
        m.press(t + 60, 0, 'START')            # Random again
elif run == 'card':
    m = Menu(boot='vs', len_s=50.0, unlock=True)   # the play build's boot (projects/geno/director/play.py)
    pick(m)
    goto(m, 560, (0.0, -13.0), (-4.0, -9.1))
    m.press(620, 0, 'A')
    quit_to_css(m, 620 + 300 + 480, presses=5)    # the load, an 8 s match; back to the character select
elif run == 'cardboot':
    m = Menu(boot='boot', len_s=40.0, unlock=False)
    for t in range(90, 2300, 60):
        m.press(t, 0, 'A')
elif run == 'back':
    m = Menu(boot='vs', len_s=16.0, unlock=True)   # the play build's boot
    m.hold(120, 0, 100, btn='B')                   # held B leaves the character select
    t = 400
    for k in range(4):                             # VS mode's menu: Melee, Tournament, Special, Custom Rules -> Name Entry
        m.press(t, 0, 'DD'); t += 24
    m.press(t, 0, 'A'); t += 110
    m.press(t, 0, 'A')                             # NEW: the keyboard
else:
    sys.exit(f'FRESH_RUN={run}?')
m.emit(sys.argv[1])
