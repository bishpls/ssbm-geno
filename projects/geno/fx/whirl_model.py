"""The Geno Whirl's own disc (replaces Samus's charge-shot ball stand-in on PlGe.dat's Whirl article), built by
fighter-build from this spec (datkit ArticleModel.cs; articles.py hands it over).

SMRPG's Whirl (the demo battle with spell 16 pointed at it, ~/games/smrpg/work/fx/whirl_frames.png; EF0032): a white-yellow
disc of light streaking out, seen at an angle (an oval), trailing fading yellow ovals (the ring trail: efge.py WHIRL_RING,
dropped by the item code). Ours: a flat disc with a white-hot centre, a pale-yellow body and four swept blades (so its
spin reads), tilted about the flight axis into a SNES-like oval and spun in its own plane by every state's joint
animation (fast out, slower in the hover), with a soft round aura (additive) padding its 3.6 hitbox.

Joints: 0 root (the item's: +Z is its facing); 1 tilt (a fixed turn about Z, the flight axis); 2 spin (the disc, spun
about its local X, the disc's normal); 3 aura (on the root, camera-facing: the quad lies in the root's YZ plane).
    spec(out_dir) -> dict for articles.py (writes the textures into out_dir)
"""
import math, os

import numpy as np
from PIL import Image

R = 4.4                 # the disc's radius (the hitbox's is 3.6)
TILT = math.radians(48) # about the flight axis: the disc shows as an oval ~1.5:1, the SNES's angle
AURA = 5.2              # the round aura's radius (additive, faint)
SPIN = {'travel': 6, 'grind': 5, 'hover': 11, 'recall': 6}   # frames a turn in each state (the article's states 0-3)
STATES = ['travel', 'grind', 'hover', 'recall']


def _rgba(rgb, a):
    return Image.fromarray(np.dstack([(np.clip(rgb, 0, 1) * 255).astype(np.uint8),
                                      (np.clip(a, 0, 1) * 255).astype(np.uint8)]), 'RGBA')


def disc_texture(n=64):
    """A disc of light: white-hot centre, pale yellow, four swept blades of brighter yellow, a bright rim, soft edge."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    dx, dy = (xx - c) / c, (yy - c) / c
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    blades = 0.5 + 0.5 * np.cos(4 * (th + 2.2 * r))                  # four arms swept back with the radius
    blades = np.clip((blades - 0.45) / 0.55, 0, 1) * np.clip((r - 0.25) / 0.2, 0, 1)
    core = np.clip(1.0 - r / 0.33, 0, 1)
    rim = np.exp(-((r - 0.86) / 0.07) ** 2)
    white = np.array([1.0, 1.0, 0.97]); pale = np.array([1.0, 0.96, 0.62]); gold = np.array([1.0, 0.84, 0.25])
    rgb = pale[None, None] * np.ones((n, n, 1))
    rgb = rgb * (1 - blades[..., None] * 0.6) + gold[None, None] * (blades[..., None] * 0.6)
    rgb = rgb * (1 - core[..., None]) + white[None, None] * core[..., None]
    rgb = rgb * (1 - rim[..., None] * 0.5) + white[None, None] * (rim[..., None] * 0.5)
    a = np.clip((1.0 - r) / 0.1, 0, 1) * (0.72 + 0.28 * np.maximum(np.maximum(blades, core), rim))
    return _rgba(rgb, a)


def aura_texture(n=32):
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot(xx - c, yy - c) / c
    a = np.clip(1.0 - r, 0, 1) ** 1.8
    rgb = np.dstack([np.ones_like(r), np.full_like(r, 0.9), np.full_like(r, 0.55)])
    return _rgba(rgb, a)


def _square(s):
    """A square of half-width s in the joint's YZ plane, UVs 0..1."""
    p = [(-s, -s, 0, 1), (s, -s, 1, 1), (s, s, 1, 0), (-s, s, 0, 0)]
    return [[0, y, z, 1, 1, 1, 1, u, v] for i in (0, 1, 2, 0, 2, 3) for y, z, u, v in [p[i]]]


def spec(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    disc_texture().save(os.path.join(out_dir, 'disc.png'))
    aura_texture().save(os.path.join(out_dir, 'aura.png'))
    states = []
    for st in STATES:
        n = SPIN[st]
        states.append(dict(tracks=[dict(joint=2, track='ROTX', end=n, loop=True, keys=[[0, 0.0], [n, 2 * math.pi]])]))
    return dict(dir=out_dir,
                joints=[dict(parent=-1), dict(parent=0, r=[0, 0, TILT]), dict(parent=1), dict(parent=0)],
                meshes=[dict(joint=3, blend='add', alpha=0.45, texture='aura.png', tex_fmt='RGBA8', tris=_square(AURA)),
                        dict(joint=2, blend='xlu', alpha=1.0, texture='disc.png', tex_fmt='RGBA8', tris=_square(R))],
                states=states)
