"""The Geno Blast's own model (replaces Pikachu's thunder stand-in on PlGe.dat's Blast article), built by fighter-build from
this spec (datkit ArticleModel.cs; articles.py hands it over).

SMRPG's Blast (the demo battle with spell 16 pointed at it, ~/games/smrpg/work/fx/blast_frames.png): blue four-point
sparkles rise at his hand, then flat bands of colour (white, purple, teal, yellow-green, yellow, orange, red, blue) drop
from the top of the screen onto the target, each landing in a white cloud. SMRPG has no tell (it's turn-based); ours is
the mark phase: a glowing oval on the floor with a thin beam of light rising from it that widens as the strike nears.

Richer since 2026-09-30 (Michael: "lower-quality than the rest of Geno's kit ... spruce them up a little bit in terms of
detail and sprite richness"): each column is three layers (a wide soft glow, the band with SMRPG's faint horizontal
banding, streaks and bright edges, a hot core), shimmering in width, with a flare at its falling foot; the tell is a
double-rimmed oval and a beam with a glow; and the column comes from far up (it used to appear mid-screen under a high
cast). Over the void the item code hides the floor parts (the oval, the foot's flare) and shows a tail that fades the
column into the depths instead of ending it on nothing.

The item (decomp itgeno.c) rides `lift` (40) above the floor: its root is at floor + 40 through the mark, and in the
strike it drops from floor + 90 to floor + 40, its hitboxes on the lowest 24 of the 40 below it. Joints:
  1 `mark` (y -40, the floor; turns to face the camera): the tell beam; its child 11 the floor oval
  2 `strike` (the group; scaled 0 in the mark state, 1 in the strike): one column per SNES colour, each on its own
      camera-facing joint (3+k), from COL_TOP above the root down to 40 below it (the floor, at the strike's end); the
      item code shows one and hides the rest (a new colour each Blast, the widened three in a row). Each column's first
      child (12+k) is its foot's flare, its second (20+k) the void tail
The state animations switch the groups (state 0 the mark, state 1 the strike), breathe the tell (a slow loop, since
the marks stand through the whole charge from 2026-09-30) and shimmer the columns.
    spec(out_dir) -> dict for articles.py (writes the textures into out_dir)
"""
import math, os

import numpy as np
from PIL import Image

LIFT = 40.0
MARK_FRAMES = 32
PULSE = 36                          # the tell's breath: one slow pulse of its width, looping while the mark stands
COL_TOP, COL_W = 150.0, 6.0         # a column reaches this far above the root; its half-width (the hitbox radius, 6)
TAIL = 70.0                         # over the void, the tail runs this far below the column's foot, fading
BEAM_H, BEAM_W = 55.0, 1.4          # the tell beam: height above the floor, half-width at full
OVAL_W = 10.0                       # the floor oval's half-width
# SMRPG's column colours, in the order its demo drops them
COLOURS = [(1.0, 1.0, 0.95), (0.62, 0.22, 0.72), (0.2, 0.62, 0.62), (0.62, 0.9, 0.12), (1.0, 0.93, 0.2),
           (1.0, 0.5, 0.1), (0.9, 0.12, 0.12), (0.15, 0.25, 0.95)]


def _ia(i, a):
    i8 = (np.clip(i, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([i8, i8, i8, (np.clip(a, 0, 1) * 255).astype(np.uint8)]), 'RGBA')


def _smooth(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def column_texture(w=64, h=256, tail=False):
    """The band (u across, v down the column, 0 at its top): even colour for the vertex colour to carry, SMRPG's faint
    horizontal banding, a few soft vertical streaks, a bright line inside each edge, a hotter middle, soft sides; it
    fades in over its top 40% (out of the sky). tail=True: no fade-in, fading out to the bottom instead (the void tail)."""
    rng = np.random.default_rng(3)
    u = np.linspace(-1, 1, w)[None, :].repeat(h, 0)
    v = np.linspace(0, 1, h)[:, None].repeat(w, 1)
    au = np.abs(u)
    streak = np.interp(u[0], np.linspace(-1, 1, 9), rng.uniform(-1, 1, 9))[None, :]
    bands = np.sin(v * (COL_TOP + LIFT) / 5.0 * 2 * np.pi)
    inten = 0.74 + 0.16 * (1 - au / 0.6).clip(0, 1) + 0.05 * streak + 0.02 * bands
    inten += 0.3 * np.exp(-((au - 0.84) / 0.05) ** 2)                 # the bright edge lines
    side = 1 - _smooth(au, 0.9, 1.0)
    fade = (1 - v) ** 1.2 if tail else _smooth(v, 0.0, 0.4) ** 1.3
    a = side * fade * (0.8 + 0.2 * (1 - au))
    return _ia(inten, a)


def glow_texture(w=32, h=128, tail=False):
    """The soft glow round a band (and the tell beam's): a Gaussian across, the band's fade along it."""
    u = np.linspace(-1, 1, w)[None, :].repeat(h, 0)
    v = np.linspace(0, 1, h)[:, None].repeat(w, 1)
    fade = (1 - v) ** 1.2 if tail else _smooth(v, 0.0, 0.4) ** 1.3
    return _ia(np.ones_like(u), np.exp(-(u / 0.5) ** 2) * fade)


def flare_texture(n=64):
    """The foot's flare: a round glow with a brighter horizontal streak through it."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    x, y = (xx - c) / c, (yy - c) / c
    glow = np.exp(-(x * x + y * y) / 0.18)
    streak = np.exp(-(y / 0.08) ** 2) * np.clip(1 - np.abs(x), 0, 1) ** 1.5
    return _ia(np.clip(0.7 + 0.3 * glow, 0, 1), np.clip(glow + 0.8 * streak, 0, 1))


def oval_texture(n=64, squash=0.32):
    """The floor oval: a bright outer rim, a fainter inner ring and a soft fill, squashed like a disc on the floor."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot((xx - c) / c, (yy - c) / (c * squash))
    rim = np.exp(-((r - 0.82) / 0.09) ** 2)
    inner = 0.55 * np.exp(-((r - 0.5) / 0.07) ** 2)
    fill = np.clip(1.0 - r, 0, 1) * 0.35
    return _ia(np.clip(0.6 + 0.4 * rim, 0, 1), np.clip(rim + inner + fill, 0, 1) * (r < 1.0))


def _quad(x0, x1, y0, y1, col, a=1.0):
    """A quad in the joint's XY plane (a camera-facing joint's), u across x, v from y1 (top, 0) to y0 (1)."""
    p = [(x0, y0, 0, 1), (x1, y0, 1, 1), (x1, y1, 1, 0), (x0, y1, 0, 0)]
    return [[x, y, 0, col[0], col[1], col[2], a, u, v] for i in (0, 1, 2, 0, 2, 3) for x, y, u, v in [p[i]]]


OFF = 0.001     # "hidden" in a state's animation: never 0, since a camera-facing joint divides by its own axes (0 gives
                # NaNs, and the column drew anyway)


def _const(joint, track, value, end):
    return dict(joint=joint, track=track, end=end, keys=[[0, value], [end, value]])


def _mix(c, t):
    return tuple(ci + (1 - ci) * t for ci in c)


def spec(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    column_texture().save(os.path.join(out_dir, 'column.png'))
    column_texture(tail=True).save(os.path.join(out_dir, 'column_tail.png'))
    glow_texture().save(os.path.join(out_dir, 'glow.png'))
    glow_texture(tail=True).save(os.path.join(out_dir, 'glow_tail.png'))
    flare_texture().save(os.path.join(out_dir, 'flare.png'))
    oval_texture().save(os.path.join(out_dir, 'oval.png'))
    vb = ['VBILLBOARD']
    n = len(COLOURS)
    joints = [dict(parent=-1),
              dict(parent=0, t=[0, -LIFT, 0], flags=vb),              # 1 mark: the tell beam
              dict(parent=0)]                                        # 2 strike: the columns' group
    joints += [dict(parent=2, flags=vb) for _ in COLOURS]            # 3+k: one column per colour
    joints += [dict(parent=1)]                                       # 11: the floor oval (hidden over the void)
    joints += [dict(parent=3 + k) for k in range(n)]                 # 12+k: the foot's flare (hidden over the void)
    joints += [dict(parent=3 + k) for k in range(n)]                 # 20+k: the void tail (hidden over a floor)
    pale = (0.6, 0.8, 1.0)
    oval_j, foot_j, tail_j = 3 + n, 4 + n, 4 + 2 * n
    meshes = [dict(joint=1, blend='add', alpha=0.45, texture='glow.png', tex_fmt='IA8',
                   tris=_quad(-BEAM_W * 3.5, BEAM_W * 3.5, 0.0, BEAM_H, pale)),
              dict(joint=1, blend='add', alpha=0.7, texture='column.png', tex_fmt='IA8',
                   tris=_quad(-BEAM_W, BEAM_W, 0.0, BEAM_H, _mix(pale, 0.5))),
              dict(joint=oval_j, blend='add', alpha=0.9, texture='oval.png', tex_fmt='IA8',
                   tris=_quad(-OVAL_W, OVAL_W, -OVAL_W * 0.32, OVAL_W * 0.32, pale))]
    for k, c in enumerate(COLOURS):
        j = 3 + k
        meshes += [dict(joint=j, blend='add', alpha=0.5, texture='glow.png', tex_fmt='IA8',
                        tris=_quad(-COL_W * 2.1, COL_W * 2.1, -LIFT, COL_TOP, c)),
                   dict(joint=j, blend='xlu', alpha=1.0, texture='column.png', tex_fmt='IA8',
                        tris=_quad(-COL_W, COL_W, -LIFT, COL_TOP, c)),
                   dict(joint=j, blend='add', alpha=0.55, texture='glow.png', tex_fmt='IA8',
                        tris=_quad(-COL_W * 0.45, COL_W * 0.45, -LIFT, COL_TOP, _mix(c, 0.65))),
                   dict(joint=foot_j + k, blend='add', alpha=0.95, texture='flare.png', tex_fmt='IA8',
                        tris=_quad(-COL_W * 2.2, COL_W * 2.2, -LIFT - COL_W * 1.1, -LIFT + COL_W * 1.1, _mix(c, 0.7))),
                   dict(joint=tail_j + k, blend='add', alpha=0.5, texture='glow_tail.png', tex_fmt='IA8',
                        tris=_quad(-COL_W * 2.1, COL_W * 2.1, -LIFT - TAIL, -LIFT, c)),
                   dict(joint=tail_j + k, blend='xlu', alpha=1.0, texture='column_tail.png', tex_fmt='IA8',
                        tris=_quad(-COL_W, COL_W, -LIFT - TAIL, -LIFT, c))]
    mark_state = dict(tracks=[_const(2, 'SCAX', OFF, MARK_FRAMES), _const(2, 'SCAY', OFF, MARK_FRAMES),
                              _const(2, 'SCAZ', OFF, MARK_FRAMES),
                              # the tell breathes, calm over a long hold (the marks show through the whole charge)
                              dict(joint=1, track='SCAX', end=PULSE, loop=True,
                                   keys=[[0, 0.8], [PULSE / 2, 1.0], [PULSE, 0.8]])])
    shimmer = [dict(joint=3 + k, track='SCAX', end=6, loop=True,
                    keys=[[0, 1.0], [2, 1.07 - 0.01 * (k % 3)], [4, 0.96], [6, 1.0]]) for k in range(n)]
    strike_state = dict(tracks=[_const(1, 'SCAX', OFF, 8), _const(1, 'SCAY', OFF, 8), _const(1, 'SCAZ', OFF, 8),
                                _const(2, 'SCAX', 1.0, 8), _const(2, 'SCAY', 1.0, 8), _const(2, 'SCAZ', 1.0, 8)] + shimmer)
    return dict(dir=out_dir, joints=joints, meshes=meshes, states=[mark_state, strike_state])
