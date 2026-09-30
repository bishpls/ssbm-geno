"""Cape lab: Geno's cape and cap point (the dynamics chains, rig.py DYNAMICS) beside Marth's cape, both fighters on the same
inputs, so the two sets of chains can be judged side by side through the same motions. CAPE_LAB picks the part:
  move  (default) idle, walk, dash into a run, run turnaround, skid, dash-dance, full hop and double jump, a smash attack,
        shield, short hop fast fall, crouch
  attacks  every ground attack and aerial (the arms against the capelet's front panels)
  menu  VS mode through the menus, Geno drifting off screen (the game's camera and its magnifier bubble, about game
        frames 980-1020); a menu run prints no DIRECTOR END, so stop it with dolphin.py --frames 1100
  hit   Geno and Marth take turns launching each other hard at high percent (tumble, a KO, the respawn), then a shield poke
CAPE_CAM: side (default; the game's side view) or orbit (3/4, yaw 35 degrees). CAPE_TRACK: mid (default; the pair) or p0 / p1
(a close-up on Geno / on Marth, for strips that pair the two frame by frame).
    CAPE_LAB=move CAPE_CAM=side CAPE_TRACK=p0 .venv/bin/python tools/machinima/melee/build.py projects/geno cape_lab
With the decomp built with GENO_DYN_TRACE defined, the log carries Geno's solved chain positions every frame (GDYN/GC/GS).
"""
import os, sys
from dsl import Film, Menu

LAB = os.environ.get('CAPE_LAB', 'move')
CAM = os.environ.get('CAPE_CAM', 'side')
TRACK = os.environ.get('CAPE_TRACK', 'mid')        # mid: the pair; p0: a close-up on Geno; p1: on Marth


def camera(f, n, dist=88):
    if TRACK != 'mid': dist = 60                   # one fighter, tracked (the game's tracking lags a run and a jump)
    yaw = 35 if CAM == 'orbit' else 0
    f.orbit(0, at=(0, 8.5 if TRACK != 'mid' else 7, 0), dist=dist, yaw=yaw, pitch=6 if CAM == 'orbit' else 4, fov=30,
            ease='cut', track=TRACK)


if LAB == 'menu':
    # the game's own camera (a director match flies a free camera, which never shows the off-screen magnifier): VS mode
    # through the character select (Geno and Fox), then Geno runs off the stage's left edge, double jumps away and drifts
    # off screen, so the magnifier bubble draws his low model (its cape on the back chain, its cap on the cap's point)
    m = Menu(boot='vs', len_s=26.0)
    m.goto(90, 0, 110, 'geno')
    m.press(205, 0, 'A')
    m.goto(215, 1, 110, 'fox')
    m.press(330, 1, 'A')
    m.press(360, 0, 'START')
    m.hold(430, 0, 30, stick=(0, 80))
    m.press(470, 0, 'A')
    m.hold(760, 0, 150, stick=(-80, 0))                # run left, off the edge
    m.press(830, 0, 'X')                               # jump and double jump away from the stage
    m.press(860, 0, 'X')
    m.hold(862, 0, 300, stick=(-80, 0))
    m.emit(sys.argv[1]); sys.exit()
elif LAB == 'move':
    # every segment starts from a reset (a teleport: the chains swing from it, so each gets a quiet second first), so the
    # runs stay on Final Destination (its ledges at +-85.6); Geno on the left, Marth 18 units to his right
    f = Film(len_s=20.0)
    f.setup(players=[('geno', dict(x=-9, face=1)), ('marth', dict(x=9, face=1))], seed=5)
    camera(f, f.n)
    for i in (0, 1):
        p = f.port(i)
        f.reset(100, i, -50 + 18 * i, 1)
        p.hold(150, 90, stick=(44, 0))                     # 150 walk right
        f.reset(260, i, -72 + 18 * i, 1)
        p.hold(300, 45, stick=(80, 0))                     # 300 dash into a run
        p.hold(345, 50, stick=(-80, 0))                    # 345 run turnaround, run left; 395 let go: the skid
        f.reset(440, i, -9 + 18 * i, 1)
        for k in range(12):                                # 470 dash-dance
            p.hold(470 + 10 * k, 10, stick=(80 if k % 2 == 0 else -80, 0))
        f.reset(600, i, -9 + 18 * i, 1)
        p.hold(630, 6, btn='X')                            # 630 full hop, 670 double jump
        p.hold(670, 3, btn='X')
        p.hold(790, 3, c=(80, 0))                          # 790 forward smash
        p.hold(860, 90, trig=140)                          # 860 shield
        p.hold(1000, 2, btn='X')                           # 1000 short hop, fast fall at the apex
        p.hold(1016, 20, stick=(0, -80))
        p.hold(1080, 60, stick=(0, -80))                   # 1080 crouch
elif LAB == 'attacks':
    # the arms against the capelet's front panels: every ground attack, then the aerials from short hops
    f = Film(len_s=21.0)
    f.setup(players=[('geno', dict(x=-9, face=1)), ('marth', dict(x=9, face=1))], seed=5)
    camera(f, f.n)
    GROUND = [('jab', (0, 0), (0, 0), 'A'), ('ftilt', (48, 0), (0, 0), 'A'), ('utilt', (0, 48), (0, 0), 'A'),
              ('dtilt', (0, -48), (0, 0), 'A'), ('fsmash', (0, 0), (80, 0), ''), ('usmash', (0, 0), (0, 80), ''),
              ('dsmash', (0, 0), (0, -80), ''), ('grab', (0, 0), (0, 0), 'Z')]
    AIR = [('nair', (0, 0)), ('fair', (80, 0)), ('bair', (-80, 0)), ('uair', (0, 80)), ('dair', (0, -80))]
    for i in (0, 1):
        p = f.port(i); t = 90
        for name, st, c, b in GROUND:
            f.reset(t - 20, i, -9 + 18 * i, 1)
            p.hold(t, 3, stick=st, c=c, btn=b); t += 75
        for name, c in AIR:
            f.reset(t - 20, i, -9 + 18 * i, 1)
            p.hold(t, 2, btn='X'); p.hold(t + 7, 3, c=c); t += 75
elif LAB == 'hit':
    f = Film(len_s=17.0)
    f.setup(players=[('geno', dict(x=-12, face=1)), ('marth', dict(x=12, face=-1))], seed=5)
    camera(f, f.n, dist=120)
    g, m = f.port(0), f.port(1)
    f.percent(60, 0, 150)
    m.hold(100, 3, c=(-80, 0))                             # Marth's forward smash launches Geno (KO at 150%)
    f.percent(400, 1, 150)
    f.reset(400, 0, -12, 1)
    f.reset(400, 1, 12, -1)
    g.hold(430, 3, c=(80, 0))                              # Geno's forward smash on Marth
    f.percent(700, 0, 60)
    f.reset(700, 0, -12, 1)
    f.reset(700, 1, 12, -1)
    m.hold(730, 3, stick=(-48, 0), btn='A')                # a forward tilt on Geno at 60%: hitstun, no KO
    g.hold(820, 80, trig=140)                              # Geno shields Marth's jab
    m.hold(840, 2, btn='A')
f.emit(sys.argv[1])
