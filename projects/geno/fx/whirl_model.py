"""The Geno Whirl's own disc (replaces Samus's charge-shot ball stand-in on PlGe.dat's Whirl article), built by
fighter-build from this spec (datkit ArticleModel.cs; articles.py hands it over).

SMRPG's Whirl (the demo battle with spell 16 pointed at it, ~/games/smrpg/work/fx/whirl_frames.png; EF0032): a white-yellow
disc of light streaking out, seen at an angle (an oval), trailing fading yellow ovals (the ring trail: efge.py WHIRL_RING,
dropped by the item code). Ours (2026-09-30, after the remake's spiky rings, Michael's reference): a stylized sun, a
white-gold core and a rim of small straight spikes, facing the camera and spun in the screen's plane by every state's
joint animation (fast out, slower in the hover), with a soft round aura (additive) padding its 3.6 hitbox; its trail's
rings are spiked the same way.

Joints: 0 root (the item's: +Z is its facing); 1 tilt (a fixed turn about Z, the flight axis); 2 spin (the disc, spun
about its local X, the disc's normal); 3 aura (on the root, camera-facing: the quad lies in the root's YZ plane).
    spec(out_dir) -> dict for articles.py (writes the textures into out_dir)
"""
import math, os

import numpy as np
from PIL import Image

R = 4.4                 # the disc's radius (the hitbox's is 3.6)
# Michael, 2026-09-30: a stylized sun, small straight spikes round its rim, rotating (the remake's spiky rings; not
# sawtooth). How it faces Melee's side-on camera is WHIRL_LOOK: 'face' (built) turned to face the camera and spun in the
# screen's plane, the clearest sun at match distance; 'tilt' the SNES's oval (48 degrees about the flight axis), its
# spikes squeezed at the sides and its spin a shimmer. (A 70-degree tilt went more edge-on, a sliver: not an option.)
LOOK = os.environ.get('WHIRL_LOOK', 'face')
TILT = math.radians({'tilt': 48, 'face': 0}[LOOK])
SPIKES = 22             # the rim's spikes: straight, clean triangles pointing outward
AURA = 5.2              # the round aura's radius (additive, faint)
SPIN = {'travel': 6, 'grind': 5, 'hover': 11}   # frames a turn in each state (the article's states 0-2; no recall since v1.5)
STATES = ['travel', 'grind', 'hover']


def _rgba(rgb, a):
    return Image.fromarray(np.dstack([(np.clip(rgb, 0, 1) * 255).astype(np.uint8),
                                      (np.clip(a, 0, 1) * 255).astype(np.uint8)]), 'RGBA')


def disc_texture(n=128, ss=4):
    """A stylized sun: a white-gold core, a bright ring, and a rim of SPIKES small straight triangles pointing outward
    (their sides radial-symmetric, not sawtooth), gold darkening to orange at their tips."""
    from PIL import ImageDraw
    m = n * ss
    c = m / 2
    mask = Image.new('L', (m, m), 0)
    d = ImageDraw.Draw(mask)
    r0, r1, half = 0.64 * c, 0.98 * c, math.pi / SPIKES * 0.55
    for k in range(SPIKES):
        a = 2 * math.pi * k / SPIKES
        d.polygon([(c + r0 * math.cos(a - half), c + r0 * math.sin(a - half)), (c + r1 * math.cos(a), c + r1 * math.sin(a)),
                   (c + r0 * math.cos(a + half), c + r0 * math.sin(a + half))], fill=255)
    d.ellipse((c - 0.7 * c, c - 0.7 * c, c + 0.7 * c, c + 0.7 * c), fill=255)
    cover = np.asarray(mask.resize((n, n), Image.LANCZOS), np.float32) / 255.0
    cc = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot(xx - cc, yy - cc) / cc
    white = np.array([1.0, 1.0, 0.95]); gold = np.array([1.0, 0.86, 0.3]); orange = np.array([1.0, 0.55, 0.12])
    t = np.clip(r / 0.62, 0, 1)[..., None]
    rgb = white * (1 - t ** 2) + gold * t ** 2
    tip = np.clip((r - 0.7) / 0.28, 0, 1)[..., None]
    rgb = rgb * (1 - tip) + orange * tip
    ring = np.exp(-((r - 0.66) / 0.04) ** 2)[..., None]
    rgb = rgb * (1 - ring * 0.6) + white * (ring * 0.6)
    return _rgba(rgb, cover * (0.85 + 0.15 * (1 - tip[..., 0])))


def aura_texture(n=32):
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot(xx - c, yy - c) / c
    a = np.clip(1.0 - r, 0, 1) ** 1.8
    rgb = np.dstack([np.ones_like(r), np.full_like(r, 0.9), np.full_like(r, 0.55)])
    return _rgba(rgb, a)


def _xy_square(s):
    """A square of half-width s in the joint's XY plane (a camera-facing joint's), UVs 0..1."""
    p = [(-s, -s, 0, 1), (s, -s, 1, 1), (s, s, 1, 0), (-s, s, 0, 0)]
    return [[x, y, 0, 1, 1, 1, 1, u, v] for i in (0, 1, 2, 0, 2, 3) for x, y, u, v in [p[i]]]


def _square(s):
    """A square of half-width s in the joint's YZ plane, UVs 0..1."""
    p = [(-s, -s, 0, 1), (s, -s, 1, 1), (s, s, 1, 0), (-s, s, 0, 0)]
    return [[0, y, z, 1, 1, 1, 1, u, v] for i in (0, 1, 2, 0, 2, 3) for y, z, u, v in [p[i]]]


def spec(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    disc_texture().save(os.path.join(out_dir, 'disc.png'))
    aura_texture().save(os.path.join(out_dir, 'aura.png'))
    face = LOOK == 'face'
    track = 'ROTZ' if face else 'ROTX'            # the disc's own axis: the screen's normal, or the tilted disc's
    states = []
    for st in STATES:
        n = SPIN[st]
        states.append(dict(tracks=[dict(joint=2, track=track, end=n, loop=True, keys=[[0, 0.0], [n, -2 * math.pi]])]))
    spin = dict(parent=1, flags=['RBILLBOARD']) if face else dict(parent=1)
    return dict(dir=out_dir,
                joints=[dict(parent=-1), dict(parent=0, r=[0, 0, TILT]), spin, dict(parent=0)],
                meshes=[dict(joint=3, blend='add', alpha=0.45, texture='aura.png', tex_fmt='RGBA8', tris=_square(AURA)),
                        dict(joint=2, blend='xlu', alpha=1.0, texture='disc.png', tex_fmt='RGBA8',
                             tris=_xy_square(R) if face else _square(R))],
                states=states)
