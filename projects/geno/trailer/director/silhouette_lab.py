"""Silhouette lab: Geno's NEW CHALLENGER silhouette (NtAppro.usd frame 12) rendered in game from the production model, for
projects/geno/trailer/silhouette/silhouette.py. Geno faces left, as most of the eleven vanilla silhouettes do (toward the
screen's "A new foe has appeared!"), on a long lens (fov 12 from ~110 units: near-orthographic, as the vanilla ones read).
    SIL_LAB=survey .venv/bin/python tools/machinima/melee/build.py projects/geno/trailer silhouette_lab
        one Geno running through the candidate poses on black, every frame (pick the frames: the POSES table below)
    SIL_LAB=matte .venv/bin/python tools/machinima/melee/build.py projects/geno/trailer silhouette_lab
        up to four Genos, each timed into its own candidate pose on one frozen frame; while frozen the camera visits each,
        rendered on black then on white (portrait_lab's difference matte: coverage a = 1 - (W - B), exact at the edges).
        SIL_POSES=idle,finger,beam,taunt picks the Genos (POSES names; NAME@YAW[@PITCH[@FACE]] sets that Geno's camera
        and facing, 1 right, default -1 left), SIL_YAW
        the camera's swing (default -30: his front three-quarters, facing left), SIL_PITCH (default 3).
    DOLPHIN_SLOTS=3 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol OUT --until 'DIRECTOR END' --res 3 --quiet
"""
import os, sys
from dsl import Film

mode = os.environ.get('SIL_LAB', 'survey')
YAW = float(os.environ.get('SIL_YAW', -30))
PITCH = float(os.environ.get('SIL_PITCH', 3))
FOV, DIST, AT_Y = 12.0, 112.0, 8.0          # 2 x 112 x tan 6 deg = 23.5 units of frame height: the whole figure with room

# Each candidate: the inputs that bring him into the pose, as (offset from the press, frames held, stick, cstick, buttons,
# trigger), and the frame (from the press) the pose is held on. Sticks are for facing left (-x is forward).
# Survey frames (runs/survey, every frame dumped at res 2) put each pose's frame from the press, by the muzzle blast's
# first frame (the Hand Gun's active frame 7): the Hand Gun's arm and barrel are out and clean of the blast at +4; the
# Beam's barrel is formed at +10 and its draw-in stars start at +22, so +16; the curtain call bows at +52..+64.
POSES = {
    'idle':    ([], 0),                                                  # Wait1 (the breath and sway)
    'handgun': ([(0, 3, (-48, 0), (0, 0), 'A', 0)], 4),                  # forward tilt: the arm and the wrist barrel out
    'finger':  ([(0, 4, (0, 0), (0, 0), 'B', 0)], 22),                   # the Finger Shot's arm, between the bullets
    'beam':    ([(0, 60, (0, 0), (0, 0), 'B', 0)], 16),                  # the Beam's charge: the arm given way to the barrel
    'taunt':   ([(0, 3, (0, 0), (0, 0), 'DU', 0)], 58),                  # the curtain call's bow, the brim tipped
    'dsmash':  ([(0, 50, (0, -80), (0, 0), 'A', 0)], 20),                # twin Hand Cannons, cocked in the charge (A held)
    'fsmash':  ([(0, 3, (0, 0), (-80, 0), '', 0)], 16),                  # Double Punch
    'usmash':  ([(0, 3, (0, 0), (0, 80), '', 0)], 9),                    # Star Gun: both wrists up
    'utilt':   ([(0, 3, (0, 48), (0, 0), 'A', 0)], 7),                   # the cape spun upward
    'jab':     ([(0, 3, (0, 0), (0, 0), 'A', 0)], 4),
    'run':     ([(0, 40, (-80, 0), (0, 0), '', 0)], 30),
    'jump':    ([(0, 3, (0, 0), (0, 0), 'X', 0)], 14),
    'fair':    ([(0, 3, (0, 0), (0, 0), 'X', 0), (6, 3, (-60, 0), (0, 0), 'A', 0)], 16),   # Hand Gun burst, airborne
    'bair':    ([(0, 3, (0, 0), (0, 0), 'X', 0), (6, 3, (60, 0), (0, 0), 'A', 0)], 16),    # Hand Cannon backward
    'nair':    ([(0, 3, (0, 0), (0, 0), 'X', 0), (6, 3, (0, 0), (0, 0), 'A', 0)], 12),
    'uair':    ([(0, 3, (0, 0), (0, 0), 'X', 0), (6, 3, (0, 60), (0, 0), 'A', 0)], 12),
    'dashatk': ([(0, 20, (-80, 0), (0, 0), '', 0), (12, 3, (-80, 0), (0, 0), 'A', 0)], 22),
    'upb':     ([(0, 3, (0, 80), (0, 0), 'B', 0)], 14),                  # Star Road
    'sideb':   ([(0, 3, (-80, 0), (0, 0), 'B', 0)], 14),                 # the Whirl
    'downb':   ([(0, 3, (0, -80), (0, 0), 'B', 0)], 6),                  # the Blast's call: both hands up to the sky
    'grab':    ([(0, 3, (0, 0), (0, 0), 'Z', 0)], 8),
}

if mode == 'survey':
    f = Film(len_s=float(os.environ.get('SIL_LEN', 11.0)))
    f.setup(players=[('geno', dict(x=0, face=-1))], seed=5)
    f.cue(0, 'stage', a=0)
    f.cue(0, 'bgcolor', a=0, b=0, c=0)
    f.hud(0, 0)
    f.orbit(0, at=(0, AT_Y, 0), dist=DIST, yaw=YAW, pitch=PITCH, fov=FOV, ease='cut')
    g = f.port(0)
    t = 40
    for name in os.environ.get('SIL_SURVEY', 'handgun,finger,beam,taunt,dsmash,fsmash').split(','):
        steps, _ = POSES[name]
        f.mark(t, len(f.labels), name)
        for off, n, st, c, btn, trig in steps:
            g.hold(t + off, n, stick=st, c=c, btn=btn, trig=trig)
        if name == 'beam':
            g.hold(t + 62, 3, trig=140)      # shield: cancel the charge
        t += {'taunt': 140, 'beam': 110, 'dsmash': 110}.get(name, 70)
        f.reset(t, 0, 0, -1)                 # back to the middle, facing left, in Wait
        t += 10
    f.emit(sys.argv[1])
    sys.exit(0)

# ---- the matte run
# NAME or NAME@YAW (a camera swing per Geno; default SIL_YAW) or NAME@YAW@PITCH
specs = [p.split('@') for p in os.environ.get('SIL_POSES', 'idle,finger,beam,taunt').split(',')]
names = [sp[0] for sp in specs]
yaws = [float(sp[1]) if len(sp) > 1 else YAW for sp in specs]
pitches = [float(sp[2]) if len(sp) > 2 else PITCH for sp in specs]
faces = [int(sp[3]) if len(sp) > 3 else -1 for sp in specs]       # NAME@YAW@PITCH@FACE: 1 faces right (sticks mirrored)
X = [-54, -18, 18, 54][:len(names)]   # 36 apart: a neighbour projects 31+ units off, outside the 31-unit frame
f = Film(len_s=4.0 + 0.2 * len(names))
f.setup(players=[('geno', dict(x=x, face=fc)) for x, fc in zip(X, faces)], seed=5)
f.cue(0, 'stage', a=0)
f.cue(0, 'bgcolor', a=0, b=0, c=0)
f.hud(0, 0)
f.orbit(0, at=(0, 8, 0), dist=220, yaw=0, pitch=PITCH, fov=30, ease='cut')
T = 150                                      # the freeze: every Geno is on his pose's frame here (the spawn's dust long gone)
for i, name in enumerate(names):
    steps, hold = POSES[name]
    t0 = T - hold
    for off, n, st, c, btn, trig in steps:
        f.port(i).hold(t0 + off, n, stick=st, c=c, btn=btn, trig=trig, dir=-faces[i])
f.freeze(T)
t = T + 1
for i, x in enumerate(X):                    # each Geno in turn, on black then on white; MARK 1000 + 100 * i names them
    f.orbit(t, at=(x, AT_Y, 0), dist=DIST, yaw=yaws[i], pitch=pitches[i], fov=FOV, ease='cut')
    f.cue(t, 'bgcolor', a=0, b=0, c=0)
    f.cue(t + 3, 'bgcolor', a=255, b=255, c=255)
    f.mark(t + 2, 1000 + 100 * i)
    f.mark(t + 5, 1001 + 100 * i)
    t += 6
f.cue(t, 'bgcolor', a=0, b=0, c=0)
f.emit(sys.argv[1])
