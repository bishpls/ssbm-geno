"""Low-model lab (geno-cannon polish): where the game draws the low-detail model, its off-screen magnifier bubble.
    LOWFACE_MODE=bubble (default): Geno, Mario and Link held off the top of the screen (airborne, then set there every
        frame), Fox in the middle holding the game's camera: frames ~60-190 show the three bubbles (the low models). A
        stock match, so the HUD (and the magnifier with it) stays on.
    LOWFACE_MODE=high: the same three standing, a free camera pulled back until they are the bubbles' size on screen
        (7.2 px a unit at res 3, measured from the bubbles): the high models at the same pixels, for the side by side.
    LOWFACE_FACE=-1 turns them to face left.
    .venv/bin/python tools/machinima/melee/build.py projects/geno lowface_lab
"""
import os, sys
from dsl import Film

MODE = os.environ.get('LOWFACE_MODE', 'bubble')
FACE = int(os.environ.get('LOWFACE_FACE', '1'))
Y = float(os.environ.get('LOWFACE_Y', '165'))
XS = [-45.0, 0.0, 45.0]
f = Film(len_s=300 / 60)
players = [('geno', dict(x=XS[0], face=FACE)), ('mario', dict(x=XS[1], face=FACE)), ('link', dict(x=XS[2], face=FACE))]
if MODE == 'bubble':
    f.setup(players=players + [('fox', dict(x=0.0, face=1))], seed=5, stocks=4)   # a stock match keeps the HUD
    f.game_camera()
    for port in range(3):
        f.port(port).hold(30, 3, btn='X')           # airborne first, so the teleport takes (a grounded fighter snaps back)
    for t in range(36, 190):
        for port, x in enumerate(XS):
            f.setpos(t, port, x, Y)
            if t == 36: f.face(t, port, FACE)
else:
    f.setup(players=[(n, dict(o, x=o['x'] * 0.34)) for n, o in players], seed=5)
    # the bubble's scale: 7.2 px a unit at res 3 (1580 px tall), fov 30: the camera 409 units off
    f.cam(0, eye=(0, 8, 409), at=(0, 8, 0), fov=30, ease='cut')
f.emit(sys.argv[1])
