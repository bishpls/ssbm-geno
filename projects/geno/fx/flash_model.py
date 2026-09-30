"""Geno Flash's own sun (replaces Ness's PK Flash stand-in on PlGe.dat's Flash article), built by fighter-build from this
spec (datkit ArticleModel.cs; articles.py hands it over).

SMRPG's Geno Flash (the demo battle with spell 16 pointed at it, ~/games/smrpg/work/fx/flash_frames.png): Geno becomes a
cannon and fires a fireball that becomes a sun with a face; the screen flashes red. The SNES draws the sun's corona as
spinning triangles behind it, a 16-bit stylisation (Michael, 2026-09-29). Ours is one sun for the whole move, as the
2023 remake draws it (his reference; studied, nothing taken from it): an orange disc, light yellow at its heart to deep
orange at the rim, a thin bright rim; round it a ragged corona of billowing yellow flame tongues, churning and slowly
turning, fading out through orange into a haze; a small surprised face (two small dark oval eyes, a round "o" mouth).
The fireball in flight (efge.py FLASH_FIREBALL, its textures from sunball_frames here) is the same sun, small.

Sized by the hitbox (the item code, decomp itgeno.c itGe_FlashLook, scales every joint by FIT times the hitbox's
radius each frame): the disc's edge at the hitbox's edge, only the corona past it (fx/sunmeasure.py measures both).
Model units are the disc's radius. Every joint faces the camera (RBILLBOARD keeps the joint's own turn about Z):
  1 haze       a soft orange-brown glow behind everything, out to HAZE_R
  2 corona B   the flame tongues, mirrored and tinted deeper orange, turning one way (the state's animation)
  3 corona A   the flame tongues, yellow, turning the other way; both flicker in scale (the item code)
  4 disc       the sun's disc with its rim, and the face (vertex-coloured geometry, so it stays sharp at any size)
FLASH_PARTS=disc builds the disc and face alone (the measurement's disc-only run).
    spec(out_dir) -> dict for articles.py (writes the textures into out_dir)
"""
import math, os

import numpy as np
from PIL import Image

N = 128
DISC_TEX_R = 0.94          # the disc's edge in its texture (the rest: the bright rim fading out)
CORONA_Q = 1.5             # the corona quad's half-size (disc radii)
HAZE_R = 1.42
B_TINT = (1.0, 0.76, 0.42)
B_SCALE = 1.05
A_TURN, B_TURN = 200, 140  # frames per turn (A clockwise, B the other way)
# the face, in disc radii (y up): the remake's proportions, its features ~1.3x for Melee's distance
EYE_X, EYE_Y, EYE_W, EYE_H = 0.13, 0.05, 0.030, 0.055
MOUTH_Y, MOUTH_W, MOUTH_H = -0.10, 0.024, 0.027
EYE_COL, GLINT_COL, MOUTH_COL = (0.09, 0.07, 0.18), (0.80, 0.84, 1.0), (0.16, 0.07, 0.10)
SEED_A = 7


def _mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.asarray(a, np.float32) * (1 - t) + np.asarray(b, np.float32) * t


def _rgba(rgb, a):
    return Image.fromarray(np.dstack([(np.clip(rgb, 0, 1) * 255).astype(np.uint8),
                                      (np.clip(a, 0, 1) * 255).astype(np.uint8)]), 'RGBA')


def _grid(n, half):
    """Pixel centres in model units (disc radii), y up, for a square texture of this half-size."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    return (xx - c) / c * half, (c - yy) / c * half


LIGHT, MID, DEEP, RIM = (1.0, 0.93, 0.55), (1.0, 0.72, 0.25), (0.93, 0.44, 0.08), (1.0, 0.9, 0.5)


def disc_rgba(n=N, half=1.0 / DISC_TEX_R, ss=4):
    """The disc: light yellow at the heart, orange, deep orange at the rim, a thin bright rim just at its edge."""
    x, y = _grid(n * ss, half)
    q = np.hypot(x, y)                                        # disc radii
    rgb = _mix(_mix(LIGHT, MID, q / 0.62), DEEP, (q - 0.55) / 0.42)
    rgb = _mix(rgb, RIM, (q - 0.955) / 0.035)                  # the bright rim
    a = np.clip((1.045 - q) / 0.05, 0, 1)
    img = _rgba(rgb, a)
    return img.resize((n, n), Image.LANCZOS)


CORONA_BASE = 1.13        # the flames' outline, in disc radii: this, plus lobes of up to CORONA_LOBE
CORONA_LOBE = 0.13


def _value_noise(shape, cells, rng):
    """Smooth 2D noise in [0, 1]: a coarse random grid, bicubically enlarged."""
    g = (rng.random((cells, cells)) * 255).astype(np.uint8)
    return np.asarray(Image.fromarray(g).resize(shape[::-1], Image.BICUBIC), np.float32) / 255.0


def corona_rgba(n=N, seed=SEED_A, ss=2):
    """The flames: a continuous band out from under the rim to a billowing, ragged outline (lobes of several sizes round
    it), bright yellow-white at the rim, yellow through the body, orange at the fringe, with soft shading like rolling
    fire; softened at the end."""
    from PIL import ImageFilter
    rng = np.random.default_rng(seed)
    m = n * ss
    x, y = _grid(m, CORONA_Q)
    q = np.hypot(x, y)
    th = np.arctan2(y, x)
    edge = np.full(q.shape, CORONA_BASE, np.float32)
    for k in range(26):                                          # the lobes: big billows and small tongues
        a0 = rng.uniform(0, 2 * math.pi)
        w = rng.uniform(0.05, 0.16)
        amp = CORONA_LOBE * rng.uniform(0.35, 1.0) * (1.0 if w > 0.1 else 0.8)
        d = np.angle(np.exp(1j * (th - a0)))
        edge = np.maximum(edge, CORONA_BASE - 0.03 + amp * np.sqrt(np.clip(1.0 - (d / w) ** 2, 0, 1)))   # a round billow
    edge += 0.018 * np.sin(th * 23 + rng.uniform(0, 6)) + 0.012 * np.sin(th * 37 + rng.uniform(0, 6))
    depth = np.clip((q - 0.98) / np.maximum(edge - 0.98, 1e-3), 0, None)   # 0 at the rim, 1 at the outline
    alpha = np.clip((1.0 - depth) / 0.22, 0, 1) * (q > 0.9)
    billow = _value_noise(q.shape, 18, rng) * 0.6 + _value_noise(q.shape, 40, rng) * 0.4
    rgb = _mix((1.0, 0.97, 0.6), (1.0, 0.88, 0.2), depth / 0.35)
    rgb = _mix(rgb, (0.97, 0.6, 0.1), (depth - 0.72) / 0.28)
    shade = np.clip(0.8 + 0.3 * billow, 0, 1.05)                    # rolling fire: lighter clumps, deeper gaps
    rgb = _mix(rgb * shade[..., None], (0.95, 0.55, 0.08), (0.4 - billow) * depth * 1.2)
    alpha = alpha * np.clip(0.7 + 0.6 * billow + (1 - depth), 0, 1)
    img = _rgba(rgb, alpha).filter(ImageFilter.GaussianBlur(m * 0.006))
    return img.resize((n, n), Image.LANCZOS)


def haze_rgba(n=32):
    x, y = _grid(n, HAZE_R)
    q = np.hypot(x, y)
    a = 0.5 * np.clip((HAZE_R - q) / (HAZE_R - 1.0), 0, 1) ** 1.4
    rgb = _mix((0.95, 0.55, 0.16), (0.62, 0.30, 0.10), (q - 1.0) / 0.4)
    return _rgba(rgb, a)


def _ellipse(cx, cy, w, h, col, a=1.0, seg=20, z=0.0):
    tris = []
    for k in range(seg):
        a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
        for px, py in ((cx, cy), (cx + w * math.cos(a0), cy + h * math.sin(a0)), (cx + w * math.cos(a1), cy + h * math.sin(a1))):
            tris.append([px, py, z, col[0], col[1], col[2], a, 0.5, 0.5])
    return tris


def face_tris():
    """The remake's surprised face: two small dark upright oval eyes with a glint, a small round "o" mouth."""
    t = []
    for sx in (-1, 1):
        t += _ellipse(sx * EYE_X, EYE_Y, EYE_W, EYE_H, EYE_COL)
    for sx in (-1, 1):
        t += _ellipse(sx * EYE_X - 0.008, EYE_Y + 0.024, 0.011, 0.014, GLINT_COL, seg=10)
    t += _ellipse(0.0, MOUTH_Y, MOUTH_W, MOUTH_H, MOUTH_COL)
    return t


def face_draw(img, n, disc_px, cx=None, cy=None):
    """The face drawn into a texture (the fireball's), disc_px the disc's radius in pixels."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    cx = n / 2 if cx is None else cx
    cy = n / 2 if cy is None else cy
    col = lambda c: tuple(int(v * 255) for v in c) + (255,)
    for sx in (-1, 1):
        ex, ey = cx + sx * EYE_X * disc_px, cy - EYE_Y * disc_px
        d.ellipse((ex - EYE_W * disc_px, ey - EYE_H * disc_px, ex + EYE_W * disc_px, ey + EYE_H * disc_px), fill=col(EYE_COL))
    d.ellipse((cx - MOUTH_W * disc_px, cy - MOUTH_Y * disc_px - MOUTH_H * disc_px,
               cx + MOUTH_W * disc_px, cy - MOUTH_Y * disc_px + MOUTH_H * disc_px), fill=col(MOUTH_COL))


def sunball_frames(n=64, frames=3, ss=4):
    """The fireball: the whole sun small (haze, both coronas, the disc, the face) on one texture of half-size CORONA_Q
    disc radii, one frame per corona turn so the flames churn as it flies (efge.py flips through them)."""
    out = []
    big = n * ss
    for k in range(frames):
        base = Image.new('RGBA', (big, big), (0, 0, 0, 0))
        haze = haze_rgba(64).resize((int(big * HAZE_R / CORONA_Q),) * 2, Image.LANCZOS)
        o = (big - haze.size[0]) // 2
        base.alpha_composite(haze, (o, o))
        cor = corona_rgba(128).resize((big, big), Image.LANCZOS)
        b = cor.transpose(Image.FLIP_LEFT_RIGHT).rotate(-47 * k, resample=Image.BICUBIC)
        b = Image.fromarray((np.asarray(b, np.float32) * np.array(B_TINT + (1.0,), np.float32)).astype(np.uint8), 'RGBA')
        base.alpha_composite(b)
        base.alpha_composite(cor.rotate(31 * k, resample=Image.BICUBIC))
        disc_px = big / 2 / CORONA_Q
        disc = disc_rgba(128).resize((int(2 * disc_px / DISC_TEX_R),) * 2, Image.LANCZOS)
        o = (big - disc.size[0]) // 2
        base.alpha_composite(disc, (o, o))
        face_draw(base, big, disc_px)
        out.append(base.resize((n, n), Image.LANCZOS))
    return out


def _square(s, col=(1, 1, 1), a=1.0, flip=False):
    p = [(-s, -s, 0, 1), (s, -s, 1, 1), (s, s, 1, 0), (-s, s, 0, 0)]
    return [[x, y, 0, col[0], col[1], col[2], a, (1 - u) if flip else u, v] for i in (0, 1, 2, 0, 2, 3)
            for x, y, u, v in [p[i]]]


def spec(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    disc_rgba().save(os.path.join(out_dir, 'disc.png'))
    corona_rgba().save(os.path.join(out_dir, 'corona.png'))
    haze_rgba().save(os.path.join(out_dir, 'haze.png'))
    rb = ['RBILLBOARD']
    disc_only = os.environ.get('FLASH_PARTS', '') == 'disc'
    meshes = [] if disc_only else [
        dict(joint=1, blend='xlu', alpha=1.0, texture='haze.png', tex_fmt='RGBA8', tris=_square(HAZE_R)),
        dict(joint=2, blend='xlu', alpha=0.85, texture='corona.png', tex_fmt='RGBA8',
             tris=_square(CORONA_Q * B_SCALE, col=B_TINT, flip=True)),
        dict(joint=3, blend='xlu', alpha=1.0, texture='corona.png', tex_fmt='RGBA8', tris=_square(CORONA_Q))]
    meshes += [dict(joint=4, blend='xlu', alpha=1.0, texture='disc.png', tex_fmt='RGBA8', tris=_square(1.0 / DISC_TEX_R)),
               dict(joint=4, blend='xlu', alpha=1.0, texture=None, tris=face_tris())]
    return dict(dir=out_dir,
                joints=[dict(parent=-1)] + [dict(parent=0, flags=rb) for _ in range(4)],
                meshes=meshes,
                states=[dict(tracks=[dict(joint=2, track='ROTZ', end=B_TURN, loop=True, keys=[[0, 0.0], [B_TURN, 2 * math.pi]]),
                                     dict(joint=3, track='ROTZ', end=A_TURN, loop=True, keys=[[0, 0.0], [A_TURN, -2 * math.pi]])])])


if __name__ == '__main__':
    import sys
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    disc_rgba(256).save(os.path.join(out, 'disc.png')); corona_rgba(256).save(os.path.join(out, 'corona.png'))
    for k, im in enumerate(sunball_frames(128)):
        im.save(os.path.join(out, f'sunball{k}.png'))
    print('wrote', out)
