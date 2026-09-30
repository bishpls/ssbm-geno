"""The Geno Blast's own model (replaces Pikachu's thunder stand-in on PlGe.dat's Blast article), built by fighter-build from
this spec (datkit ArticleModel.cs; articles.py hands it over).

SMRPG's Blast (the demo battle with spell 16 pointed at it, ~/games/smrpg/work/fx/blast_frames.png): blue four-point
sparkles rise at his hand, then flat bands of colour (white, purple, teal, yellow-green, yellow, orange, red, blue) drop
from the top of the screen onto the target, each landing in a white cloud. SMRPG has no tell (it's turn-based); ours is
the mark phase: a glowing oval on the floor with a thin beam of light rising from it that widens as the strike nears.

The item (decomp itgeno.c) rides `lift` (40) above the floor: its root is at floor + 40 through the mark, and in the
strike it drops from floor + 90 to floor + 40 in 8 frames, its hitboxes on the lowest 24 of the 40 below it. So:
  joint 1 `mark` (y -40, the floor; turns to face the camera): the oval, and the tell beam rising 55 from it
  joint 2 `strike` (the group; scaled 0 in the mark state, 1 in the strike): the colour columns, one per SNES colour, each
      on its own camera-facing joint (3+k) from 70 above the root down to 40 below it (the floor, at the strike's end);
      the item code shows one and hides the rest (a new colour each Blast, the widened three in a row)
The state animations switch the groups (state 0 the mark, state 1 the strike) and widen the tell beam over the mark.
    spec(out_dir) -> dict for articles.py (writes the textures into out_dir)
"""
import math, os

import numpy as np
from PIL import Image

LIFT = 40.0
MARK_FRAMES = 32
COL_TOP, COL_W = 70.0, 6.0          # a column reaches this far above the root; its half-width (the hitbox radius, 6)
BEAM_H, BEAM_W = 55.0, 1.4          # the tell beam: height above the floor, half-width at full
OVAL_W = 10.0                       # the floor oval's half-width
# SMRPG's column colours, in the order its demo drops them
COLOURS = [(1.0, 1.0, 0.95), (0.62, 0.22, 0.72), (0.2, 0.62, 0.62), (0.62, 0.9, 0.12), (1.0, 0.93, 0.2),
           (1.0, 0.5, 0.1), (0.9, 0.12, 0.12), (0.15, 0.25, 0.95)]


def _ia(i, a):
    i8 = (np.clip(i, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([i8, i8, i8, (np.clip(a, 0, 1) * 255).astype(np.uint8)]), 'RGBA')


def column_texture(w=32, h=128):
    """A flat band of light (u across, v down the column): even colour, a brighter core stripe, soft sides, fading out
    over its top third (it comes out of the sky) and a bright foot."""
    u = np.abs(np.linspace(-1, 1, w))[None, :].repeat(h, 0)
    v = np.linspace(0, 1, h)[:, None].repeat(w, 1)                 # 0 at the top, 1 at the foot
    side = np.clip((1.0 - u) / 0.18, 0, 1)
    core = np.clip(1.0 - u / 0.35, 0, 1)
    top = np.clip(v / 0.35, 0, 1) ** 1.5
    foot = np.clip((v - 0.85) / 0.15, 0, 1)
    inten = np.clip(0.8 + 0.2 * core + 0.3 * foot, 0, 1)
    a = side * top * (0.72 + 0.28 * core)
    return _ia(inten, a)


def oval_texture(n=64, squash=0.32):
    """The floor oval: a bright rim and a soft fill, squashed like a disc on the floor seen from the side."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot((xx - c) / c, (yy - c) / (c * squash))
    rim = np.exp(-((r - 0.8) / 0.12) ** 2)
    fill = np.clip(1.0 - r, 0, 1) * 0.5
    return _ia(np.clip(0.6 + 0.4 * rim, 0, 1), np.clip(rim + fill, 0, 1) * (r < 1.0))


def _quad(x0, x1, y0, y1, col, a=1.0):
    """A quad in the joint's XY plane (a camera-facing joint's), u across x, v from y1 (top, 0) to y0 (1)."""
    p = [(x0, y0, 0, 1), (x1, y0, 1, 1), (x1, y1, 1, 0), (x0, y1, 0, 0)]
    return [[x, y, 0, col[0], col[1], col[2], a, u, v] for i in (0, 1, 2, 0, 2, 3) for x, y, u, v in [p[i]]]


OFF = 0.001     # "hidden" in a state's animation: never 0, since a camera-facing joint divides by its own axes (0 gives
                # NaNs, and the column drew anyway)


def _const(joint, track, value, end):
    return dict(joint=joint, track=track, end=end, keys=[[0, value], [end, value]])


def spec(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    column_texture().save(os.path.join(out_dir, 'column.png'))
    oval_texture().save(os.path.join(out_dir, 'oval.png'))
    vb = ['VBILLBOARD']
    joints = [dict(parent=-1),
              dict(parent=0, t=[0, -LIFT, 0], flags=vb),              # 1 mark: the oval and the tell beam
              dict(parent=0)]                                        # 2 strike: the columns' group
    joints += [dict(parent=2, flags=vb) for _ in COLOURS]            # 3+k: one column per colour
    pale = (0.6, 0.8, 1.0)
    meshes = [dict(joint=1, blend='add', alpha=0.9, texture='oval.png', tex_fmt='IA8',
                   tris=_quad(-OVAL_W, OVAL_W, -OVAL_W * 0.32, OVAL_W * 0.32, pale)),
              dict(joint=1, blend='add', alpha=0.55, texture='column.png', tex_fmt='IA8',
                   tris=_quad(-BEAM_W, BEAM_W, 0.0, BEAM_H, pale))]
    for k, c in enumerate(COLOURS):
        meshes.append(dict(joint=3 + k, blend='xlu', alpha=1.0, texture='column.png', tex_fmt='IA8',
                           tris=_quad(-COL_W, COL_W, -LIFT, COL_TOP, c)))
    mark_state = dict(tracks=[_const(2, 'SCAX', OFF, MARK_FRAMES), _const(2, 'SCAY', OFF, MARK_FRAMES),
                              _const(2, 'SCAZ', OFF, MARK_FRAMES),
                              dict(joint=1, track='SCAX', end=MARK_FRAMES, keys=[[0, 0.4], [MARK_FRAMES, 1.0]])])
    strike_state = dict(tracks=[_const(1, 'SCAX', OFF, 8), _const(1, 'SCAY', OFF, 8), _const(1, 'SCAZ', OFF, 8),
                                _const(2, 'SCAX', 1.0, 8), _const(2, 'SCAY', 1.0, 8), _const(2, 'SCAZ', 1.0, 8)])
    return dict(dir=out_dir, joints=joints, meshes=meshes, states=[mark_state, strike_state])
