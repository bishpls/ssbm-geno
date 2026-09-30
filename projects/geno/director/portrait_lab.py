"""Portrait lab: Geno's menu art rendered in game, on a flat background with the stage hidden, for
projects/geno/menus/portrait.py (the character select portraits, the CSS icon, the stock icons, the VS Records face).
    PORTRAIT_LAB=survey .venv/bin/python tools/machinima/melee/build.py projects/geno portrait_lab
        one Geno running through candidate poses at the portrait's framing, black background, every frame
    PORTRAIT_LAB=0,1,2,3 .venv/bin/python tools/machinima/melee/build.py projects/geno portrait_lab
        up to four Genos in those costumes, frozen in the portrait pose; while frozen the camera visits each
        and every shot is rendered twice, on black then on white, so portrait.py solves each pixel's colour and coverage
        exactly (difference matting): no key colour to fight the costumes, and the antialiased edges come out right.
The pose is the Geno Beam's charge, frozen PORTRAIT_POSE frames (default 26) after B; the osreport's MARK lines name
each shot's black and white renders.
"""
import os, sys
from dsl import Film

mode = os.environ.get('PORTRAIT_LAB', 'survey')
if mode == 'survey':
    f = Film(len_s=9.0)
    f.setup(players=[('geno', dict(x=0, face=1))], seed=5)
    f.cue(0, 'stage', a=0)
    f.cue(0, 'bgcolor', a=0, b=0, c=0)
    f.orbit(0, at=(0.5, 7.5, 0), dist=34, yaw=34, pitch=4, fov=30, ease='cut')
    g = f.port(0)
    g.hold(40, 3, stick=(48, 0), btn='A')            # forward tilt (Hand Gun)   40-
    g.hold(100, 3, stick=(0, 48), btn='A')           # up tilt                   100-
    g.hold(160, 50, btn='B')                         # the Beam's charge         160-
    g.hold(212, 3, trig=140)                         # shield: cancel it
    g.hold(260, 3, btn='DU')                         # the taunt                 260-370
    g.hold(400, 3, c=(80, 0))                        # forward smash             400-
    g.hold(470, 3, c=(0, 80))                        # up smash                  470-
    f.emit(sys.argv[1])
    sys.exit(0)

# ---- the matte run
cos = [int(c) for c in mode.split(',')]
POSE = int(os.environ.get('PORTRAIT_POSE', 26))
X = [-36, -12, 12, 36][:len(cos)]
f = Film(len_s=2.4 + 0.2 * len(cos))
f.setup(players=[('geno', dict(x=x, face=1, color=c)) for x, c in zip(X, cos)], seed=5)
f.cue(0, 'stage', a=0)
f.cue(0, 'bgcolor', a=0, b=0, c=0)
f.orbit(0, at=(0, 8, 0), dist=150, yaw=0, pitch=4, fov=30, ease='cut')

# the framing: (look-at offset from the fighter, distance, yaw, pitch). menus/portrait.py crops every piece of art from it:
# 45 degrees in front, the Beam's charge: his face and both eyes (heavy-lidded and determined, his look in SMRPG's art),
# the barrel still reads
PORTRAIT = ((0.9, 7.6, 0), 34, 45, 4)
T0 = 60                                      # the charge starts (the spawn's dust has gone: a translucent effect spoils the
                                             # matte); while frozen the game stands still and the director counts on
for i in range(len(cos)):
    f.port(i).hold(T0, 60, btn='B')          # the Geno Beam's charge: the arm gives way to the steel barrel
t = T0 + POSE
f.freeze(t)
t += 1
at, dist, yaw, pitch = PORTRAIT
for i, x in enumerate(X):                    # each Geno in turn, on black then on white; MARK 1000 + 100 * geno names the
    f.orbit(t, at=(x + at[0], at[1], at[2]), dist=dist, yaw=yaw, pitch=pitch, fov=30, ease='cut')   # black render
    f.cue(t, 'bgcolor', a=0, b=0, c=0)
    f.cue(t + 3, 'bgcolor', a=255, b=255, c=255)
    f.mark(t + 2, 1000 + 100 * i)
    f.mark(t + 5, 1001 + 100 * i)
    t += 6
f.cue(t, 'bgcolor', a=0, b=0, c=0)
f.emit(sys.argv[1])
