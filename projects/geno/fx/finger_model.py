"""The Finger Shot's own projectile model (replaces the donor Falco laser's red bolt in PlGe.dat's Finger article; the
down throw's shots, the article's state 1, are the same model). Built by fighter-build from this spec (datkit
ArticleModel.cs; articles.py hands it over).

SMRPG's Finger Shot (the battle script 0x35F9B4 and SPR0527): the fingers fire small golden-brown pellets that fly to the
target in a quick flurry, with a grey mist at the fingertips that condenses into a small yellow star (the muzzle puff:
efge.py FINGER_PUFF). Michael: "what happened to the finger bullets?": Falco's red laser read as nothing at match
distance. So: a volley of four bright golden slugs with white-hot cores and short orange tracers, staggered along the
flight and across the finger tubes (the design's "four bullets from the right hand"), one projectile as before.

It keeps the laser's own flight code and hitboxes unchanged (it_803F67D0's motion: the laser grows its root along Z to
the article's ext +4, 3, as it leaves the hand, and its four hitbox spheres, radius 1.17, sit on the root at z -0.78,
-3.64, -6.51 and -9.38, so they string out up to 3x along the flight). Each bullet is a child joint of the root placed on
one of those spheres, so it strings out with its hitbox; the item code (itgeno.c itGe_Finger_Anim) undoes the root's
growth on the bullets themselves, so a head keeps its shape instead of being squashed flat for the first frames. The
ribbons lie in the joints' YZ plane, which the root's quarter turn puts in the stage's plane, facing the camera.
    spec(out_dir) -> dict for articles.py (writes the textures into out_dir)
"""
import os

import numpy as np
from PIL import Image

HITBOX_Z = (-0.78125, -3.64453125, -6.5078125, -9.375)   # the donor laser's four spheres (its state 0 script)
# the four bullets: (y across the finger tubes, size), one on each hitbox sphere, the lead first
BULLETS = [(0.3, 1.0), (-0.45, 0.9), (0.5, 0.85), (-0.2, 0.8)]
HEAD_W, HEAD_L = 1.25, 0.7          # a head's half-width and half-length: a round-nosed slug ~2.5 across (the hitbox: 2.3)
TRACER_W, TRACER_L = 0.8, 3.0       # a tracer's half-width and its length behind the head
HALO = 2.1                          # the head's additive halo, times the head (pads the hitbox, reads at match distance)
WHITE, GOLD, AMBER, ORANGE = (1.0, 0.98, 0.9), (1.0, 0.8, 0.25), (0.95, 0.5, 0.08), (1.0, 0.45, 0.1)


def _rgba(rgb, a):
    return Image.fromarray(np.dstack([(np.clip(rgb, 0, 1) * 255).astype(np.uint8),
                                      (np.clip(a, 0, 1) * 255).astype(np.uint8)]), 'RGBA')


def _mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.asarray(a) * (1 - t) + np.asarray(b) * t


def head_texture(n=32):
    """A slug seen side on: a white-hot centre, gold, an amber rim, a soft edge."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot(xx - c, yy - c) / c
    rgb = np.where((r < 0.35)[..., None], _mix(WHITE, GOLD, r / 0.35), _mix(GOLD, AMBER, (r - 0.35) / 0.4))
    a = np.clip((1.0 - r) / 0.25, 0, 1)
    return _rgba(rgb, a)


def halo_texture(n=32):
    """A soft warm glow (additive): the vertex colour tints it gold."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot(xx - c, yy - c) / c
    a = np.clip(1.0 - r, 0, 1) ** 2
    i8 = np.full((n, n), 255, np.uint8)
    return Image.fromarray(np.dstack([i8, (i8 * 0.82).astype(np.uint8), (i8 * 0.45).astype(np.uint8), (a * 255).astype(np.uint8)]), 'RGBA')


def tracer_texture(w=64, h=16):
    """u along the tracer (0 at the head), v across: gold at the head, orange, fading out; thinning to the tail."""
    u = np.linspace(0, 1, w)[None, :].repeat(h, 0)
    v = np.abs(np.linspace(-1, 1, h))[:, None].repeat(w, 1)
    width = 1.0 - 0.6 * u
    across = np.clip((width - v) / (0.35 * width + 1e-3), 0, 1)
    rgb = _mix(_mix(WHITE, GOLD, v * 2)[..., :3], ORANGE, np.clip(u * 1.4, 0, 1))
    a = across * np.clip(1.0 - u, 0, 1) ** 1.3
    return _rgba(rgb, a)


def _quad(z0, z1, y, w, u0=0.0, u1=1.0):
    """A ribbon in the YZ plane from z0 to z1 (u along it), centred at y, half-width w (v across)."""
    p = [(0, y - w, z0, u0, 1), (0, y + w, z0, u0, 0), (0, y + w, z1, u1, 0), (0, y - w, z1, u1, 1)]
    return [[x, yy, z, 1, 1, 1, 1, u, v] for i in (0, 1, 2, 0, 2, 3) for x, yy, z, u, v in [p[i]]]


def spec(out_dir, states=2):
    os.makedirs(out_dir, exist_ok=True)
    head_texture().save(os.path.join(out_dir, 'head.png'))
    tracer_texture().save(os.path.join(out_dir, 'tracer.png'))
    halo_texture().save(os.path.join(out_dir, 'halo.png'))
    joints, meshes = [dict(parent=-1)], []
    for k, ((y, s), z) in enumerate(zip(BULLETS, HITBOX_Z)):
        joints.append(dict(parent=0, t=[0, 0, z]))     # on its hitbox sphere; its geometry is offset across the tubes
        meshes.append(dict(joint=k + 1, blend='xlu', alpha=1.0, texture='tracer.png', tex_fmt='RGBA8',
                           tris=_quad(-HEAD_L * s * 0.5, -(HEAD_L * 0.5 + TRACER_L) * s, y, TRACER_W * s)))
        meshes.append(dict(joint=k + 1, blend='add', alpha=0.55, texture='halo.png', tex_fmt='RGBA8',
                           tris=_quad(HEAD_L * HALO * s, -HEAD_L * HALO * s, y, HEAD_W * HALO * s)))
        meshes.append(dict(joint=k + 1, blend='xlu', alpha=1.0, texture='head.png', tex_fmt='RGBA8',
                           tris=_quad(HEAD_L * s, -HEAD_L * s, y, HEAD_W * s)))
    return dict(dir=out_dir, joints=joints, meshes=meshes)
