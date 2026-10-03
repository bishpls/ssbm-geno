"""The Forest Maze's textures, painted in code (numpy): tileable where they repeat, at sizes fit for Melee's budget.
Melee's stages multiply a texture by a baked vertex colour (VERTEX, TEX0, unlit): these are the albedo at full light, and
forest_scene.py's vertex colours (ambient occlusion, a warm key, a cool sky) darken them. Painterly, not photographic:
value bands, soft noise at two or three scales, a few hard strokes (grooves, rings, spots).
    .venv/bin/python projects/geno/stage/forest_tex.py OUT_DIR        # writes NAME.png and NAME.bgra, prints the table
The noise is FFT-filtered white noise, so every texture tiles by construction.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageFilter

RNG = np.random.default_rng(7)


def noise(h, w, scale, aniso=(1.0, 1.0), seed=None):
    """Tileable noise in [0, 1]: white noise low-passed at `scale` cycles across the texture (aniso stretches it:
    (1, 4) makes features 4x longer in y)."""
    r = np.random.default_rng(seed) if seed is not None else RNG
    f = np.fft.fft2(r.standard_normal((h, w)))
    fy = np.fft.fftfreq(h)[:, None] * h / aniso[1]
    fx = np.fft.fftfreq(w)[None, :] * w / aniso[0]
    k = np.sqrt(fx ** 2 + fy ** 2)
    f *= np.exp(-(k / scale) ** 2)
    n = np.real(np.fft.ifft2(f))
    n -= n.min(); n /= max(n.max(), 1e-9)
    return n


def ramp(v, stops):
    """v in [0, 1] -> RGB through colour stops [(t, (r, g, b)), ...]."""
    v = np.clip(v, 0, 1)
    ts = np.array([s[0] for s in stops]); cs = np.array([s[1] for s in stops], float)
    out = np.empty(v.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(v, ts, cs[:, c])
    return out


def bands(v, n=7, soft=0.35):
    """Painterly value banding: pull v toward n levels (soft=0: hard posterise, 1: none)."""
    q = np.round(v * (n - 1)) / (n - 1)
    return q * (1 - soft) + v * soft


def smooth(a, r=1.0):
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(float)


def bark(w=256, h=256, grooves=5, seed=1, contrast=1.0):
    """Deep vertical grooves between long bark plates, wandering; cross cracks on the plates."""
    y, x = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    warp = noise(h, w, 2, (1, 6), seed) - 0.5                           # slow sideways drift along the trunk
    fine = noise(h, w, 30, (1, 8), seed + 1)                            # long vertical fibres
    spacing = (noise(h, w, 3, (1, 60), seed + 4) - 0.5) * 0.9                # irregular groove spacing across the trunk
    ph = (x * grooves + spacing + warp * 0.3 + (noise(h, w, 5, (1, 6), seed + 2) - 0.5) * 0.08) % 1.0
    plate = np.clip(np.abs(np.sin(np.pi * ph)) ** 0.55 * 1.35 - 0.35, 0, 1)   # 0 in the groove, 1 on the plate
    shade = 0.75 + 0.25 * np.cos(np.pi * (ph - 0.35))                   # each plate lit on one side, as carved
    crack = (noise(h, w, 18, (4, 1), seed + 3) > 0.8) * (plate > 0.7) * 0.3
    v = plate * shade * 0.8 + fine * 0.25 - crack
    v = bands(np.clip(v, 0, 1), 6, 0.45)
    v = 0.6 + (v - 0.6) * contrast * 0.8
    rgb = ramp(v, [(0.0, (40, 24, 20)), (0.25, (76, 44, 32)), (0.55, (122, 72, 46)), (0.8, (152, 96, 62)), (1.0, (176, 120, 80))])
    return smooth(rgb, 0.6 if contrast >= 1 else 1.4)


def bark_far(w=128, h=256):
    """The background trunks' bark: the same grooves, half the contrast and softer, so it reads without busy detail."""
    return bark(w, h, 4, 5, 0.45)


def rootball(w=128, h=128, seed=141):
    """The stump's underside in front, over the ravine: packed soil and a tangle of root threads (planar mapped)."""
    a = noise(h, w, 6, (1, 1), seed)
    r1 = np.abs(noise(h, w, 10, (1, 4), seed + 1) - 0.5) < 0.05
    r2 = np.abs(noise(h, w, 14, (3, 1), seed + 2) - 0.5) < 0.04
    v = bands(a * 0.55 + 0.1, 5, 0.4) + (r1 | r2) * 0.45
    return smooth(ramp(np.clip(v, 0, 1), [(0.0, (40, 26, 24)), (0.4, (74, 50, 40)), (0.7, (120, 82, 58)), (1.0, (160, 116, 80))]), 0.6)


def mist(w=64, h=64):
    """RGBA: the ravine's haze, the fog's colour, transparent at the top (v = 0) and nearly opaque low down."""
    y = (np.mgrid[0:h, 0:w][0] + 0.5) / h
    a = np.clip((y - 0.05) / 0.9, 0, 1) ** 1.3 * 235
    col = np.zeros((h, w, 3)) + np.array([60, 50, 90])
    return np.concatenate([col, a[..., None]], 2)


def birch(w=128, h=256, seed=11):
    """Pale lilac-cream bark with dark horizontal lenticels and a few dark patches (toned down by vertex colour)."""
    base = noise(h, w, 6, (1, 2), seed)
    dash = noise(h, w, 40, (6, 1), seed + 1) > 0.8
    patch = noise(h, w, 4, (1, 1), seed + 2) > 0.8
    v = 0.78 + base * 0.2 - dash * 0.55 - patch * 0.35
    rgb = ramp(np.clip(v, 0, 1), [(0.0, (46, 36, 44)), (0.45, (120, 104, 116)), (0.8, (206, 194, 198)), (1.0, (232, 222, 220))])
    return smooth(rgb, 0.5)


def stump_top(w=256, h=256, rings=13, seed=21):
    """Growth rings, concentric with the stump's outline (the mesh maps its outline to the unit circle), a darker pith,
    a few radial cracks; the outer rim darkens toward the bark."""
    y, x = (np.mgrid[0:h, 0:w] + 0.5) / np.array([h, w])[:, None, None] * 2 - 1
    r = np.hypot(x, y); th = np.arctan2(y, x)
    wob = (noise(h, w, 5, (1, 1), seed) - 0.5) * 0.09
    rr = np.clip(r + wob, 0, 1.2)
    ring = (rr * rings) % 1.0
    late = np.exp(-((ring - 0.85) / 0.07) ** 2)                        # the thin dark latewood line
    early = 0.5 + 0.5 * np.cos(2 * np.pi * ring)
    grain = noise(h, w, 30, (1, 1), seed + 1)
    v = 0.72 + early * 0.07 + grain * 0.08 - late * 0.18
    cracks = np.zeros_like(r)
    for a in RNG.uniform(-np.pi, np.pi, 5):
        d = np.abs(np.angle(np.exp(1j * (th - a))))
        cracks += (d < 0.012 + 0.02 * (1 - r)) * (r > 0.15) * (r < 0.55 + 0.35 * RNG.random())
    v -= np.clip(cracks, 0, 1) * 0.08
    v -= np.exp(-(r / 0.06) ** 2) * 0.3                                # the pith
    v -= np.clip((r - 0.86) / 0.14, 0, 1) * 0.35                       # darker toward the rim
    v = bands(np.clip(v, 0, 1), 8, 0.5)
    return smooth(ramp(v, [(0.0, (62, 40, 26)), (0.4, (118, 80, 50)), (0.7, (164, 124, 82)), (1.0, (192, 152, 102))]), 0.7)


def moss(w=128, h=128, seed=31):
    a = noise(h, w, 6, (1, 1), seed); b = noise(h, w, 22, (1, 1), seed + 1)
    v = bands(a * 0.6 + b * 0.4, 6, 0.4)
    return smooth(ramp(v, [(0.0, (40, 64, 32)), (0.45, (70, 102, 42)), (0.75, (96, 128, 52)), (1.0, (118, 148, 62))]), 0.8)


def ground(w=256, h=256, seed=41):
    """Mossy forest floor: greens with darker leaf litter and a few light specks."""
    a = noise(h, w, 5, (1, 1), seed); b = noise(h, w, 20, (1, 1), seed + 1); c = noise(h, w, 60, (1, 1), seed + 2)
    v = 0.35 + (a * 0.55 + b * 0.35 + (c > 0.82) * 0.25 - 0.35) * 0.6      # low contrast: it lies behind the fighters
    v = bands(np.clip(v, 0, 1), 6, 0.45)
    return smooth(ramp(v, [(0.0, (24, 34, 28)), (0.35, (40, 64, 40)), (0.7, (66, 98, 52)), (1.0, (110, 138, 70))]), 0.7)


def path(w=128, h=128, seed=51):
    """The purple path across u (grassy edges at u = 0 and 1, so it lies on the ground seamlessly), tiling in v."""
    y, x = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    a = noise(h, w, 6, (1, 1), seed); peb = noise(h, w, 36, (1, 1), seed + 1) > 0.8
    v = bands(a * 0.8 + peb * 0.25, 6, 0.4)
    dirt = ramp(v, [(0.0, (58, 40, 74)), (0.5, (92, 66, 116)), (1.0, (136, 104, 156))])
    edge = np.clip((np.abs(x - 0.5) - 0.32 + (noise(h, w, 8, (1, 1), seed + 2) - 0.5) * 0.12) / 0.1, 0, 1)
    return smooth(dirt * (1 - edge[..., None]) + ground(w, h, seed + 3) * edge[..., None], 0.6)


def cap_top(w=256, h=256, seed=61):
    """SMRPG's orange-red cap with cream spots, seen from above (the mesh projects top-down: x and z over 62 units)."""
    y, x = (np.mgrid[0:h, 0:w] + 0.5) / np.array([h, w])[:, None, None] * 2 - 1
    ex = np.hypot(x / 1.0, y / 0.56)                                   # the cap's outline is 31 x 17: an ellipse here
    v = 0.8 - np.clip(ex - 0.55, 0, 1) * 0.5 + (noise(h, w, 6, (1, 1), seed) - 0.5) * 0.12
    rgb = ramp(np.clip(v, 0, 1), [(0.0, (116, 30, 22)), (0.5, (172, 56, 32)), (0.8, (210, 90, 42)), (1.0, (228, 118, 56))])
    spots = np.zeros((h, w))
    for (cx, cy, rad) in [(0, 0, 0.17), (-0.46, 0.1, 0.13), (0.46, -0.08, 0.13), (-0.2, -0.3, 0.1), (0.24, 0.3, 0.1),
                          (-0.62, 0.34, 0.07), (0.63, -0.34, 0.07), (0.02, 0.43, 0.07), (-0.02, -0.46, 0.07)]:
        # none near the ends: seen edge-on at match distance they flash as bright streaks behind the fighters
        d = np.hypot(x - cx, (y - cy) / 0.56 * 0.8) / rad
        spots = np.maximum(spots, np.clip((1.0 - d) / 0.12, 0, 1))
    cream = ramp(noise(h, w, 10, (1, 1), seed + 1), [(0, (172, 104, 72)), (1, (188, 120, 84))])   # peach, not cream: off the blend band
    return smooth(rgb * (1 - spots[..., None]) + cream * spots[..., None], 0.8)


def gills(w=256, h=32, n=48, seed=71):
    """The cap's underside: radial gills across u (repeating around), v from the rim (0) to the centre (1)."""
    y, x = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    g = np.abs(np.sin(np.pi * (x * n + (noise(h, w, 4, (1, 1), seed) - 0.5) * 0.3))) ** 0.6
    v = 0.55 + g * 0.4 - y * 0.35
    return smooth(ramp(np.clip(v, 0, 1), [(0.0, (104, 76, 60)), (0.5, (190, 160, 124)), (1.0, (240, 222, 186))]), 0.5)


def leaves(w=128, h=128, seed=81):
    """Bush foliage: clumps of leaves, dark in the gaps."""
    a = noise(h, w, 10, (1, 1), seed); b = noise(h, w, 28, (1, 1), seed + 1)
    v = bands(np.clip(a * 0.5 + b * 0.6 - 0.05, 0, 1), 6, 0.35)
    return smooth(ramp(v, [(0.0, (16, 34, 22)), (0.4, (34, 70, 38)), (0.75, (64, 110, 52)), (1.0, (108, 150, 70))]), 0.6)


def mush(w=64, h=64, seed=91):
    """A small SMRPG mushroom's cap from above: orange-red, three cream spots."""
    y, x = (np.mgrid[0:h, 0:w] + 0.5) / np.array([h, w])[:, None, None] * 2 - 1
    r = np.hypot(x, y)
    rgb = ramp(np.clip(1 - r * 0.7, 0, 1), [(0.0, (150, 40, 26)), (0.6, (214, 84, 40)), (1.0, (246, 132, 62))])
    spots = np.zeros((h, w))
    for cx, cy, rad in [(0, 0.05, 0.2), (-0.5, -0.3, 0.16), (0.48, -0.36, 0.15), (0.4, 0.45, 0.13), (-0.42, 0.45, 0.12)]:
        spots = np.maximum(spots, np.clip((1 - np.hypot(x - cx, y - cy) / rad) / 0.2, 0, 1))
    return smooth(rgb * (1 - spots[..., None]) + np.array([240, 226, 190]) * spots[..., None], 0.5)


def stem(w=32, h=32, seed=95):
    v = 0.85 + noise(h, w, 6, (1, 3), seed) * 0.15
    return ramp(v, [(0.0, (170, 150, 122)), (1.0, (236, 222, 192))])


def earth(w=128, h=128, seed=101):
    """The cliff under the forest floor: dark soil with root threads."""
    a = noise(h, w, 6, (1, 1), seed); rt = noise(h, w, 30, (6, 1), seed + 1) > 0.8
    v = bands(a * 0.7 + rt * 0.3, 5, 0.4)
    return smooth(ramp(v, [(0.0, (40, 28, 32)), (0.5, (74, 52, 50)), (1.0, (118, 84, 66))]), 0.6)


def sky(w=256, h=256, seed=111):
    """The twilight backdrop behind everything (unfogged): purple above, a peach glow low through the gaps, far trunk
    silhouettes painted soft into the haze. v = 0 is the top."""
    y, x = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    # the glow sits where the match camera shows it: the top of the frame, above the fighters' band. The camera is about
    # 150 in front at y 45, so at the backdrop (z = -700) the frame's top is y ~ 155-220 and the band starts at y ~ 90.
    # v = (760 - y) / 1080: the glow's centre at y ~ 205 (v 0.51), dark by y ~ 90 (v 0.62)
    grad = ramp(y, [(0.0, (34, 28, 58)), (0.25, (70, 54, 100)), (0.4, (132, 96, 130)), (0.51, (212, 148, 138)),
                    (0.58, (130, 92, 124)), (0.64, (64, 50, 90)), (0.8, (50, 42, 78)), (1.0, (40, 34, 62))])
    glow = np.exp(-((y - 0.51) / 0.05) ** 2) * (0.6 + 0.4 * noise(h, w, 3, (1, 1), seed))
    grad = grad + glow[..., None] * np.array([18, 10, 0])
    trunks = np.zeros((h, w))
    r = np.random.default_rng(seed)
    for cx in r.uniform(0, 1, 9):                                       # a few far trunks, soft, fading up into the dark
        wd = r.uniform(0.01, 0.03)
        d = np.abs(((x - cx + 0.5) % 1.0) - 0.5) / wd
        trunks = np.maximum(trunks, np.clip(1.2 - d, 0, 1) * r.uniform(0.25, 0.55))
    trunks *= np.clip((y - 0.1) / 0.2, 0, 1)
    sil = np.array([70, 50, 84])
    return smooth(grad * (1 - trunks[..., None]) + sil * trunks[..., None], 1.2)


def branch(w=256, h=128, seed=121):
    """RGBA: dark branches from the left edge, thinning, with leaf clumps; alpha cut out (RGB5A3)."""
    rgba = np.zeros((h, w, 4))
    y, x = np.mgrid[0:h, 0:w].astype(float)
    r = np.random.default_rng(seed)
    a = np.zeros((h, w))
    def limb(x0, y0, ang, length, th, depth):
        nonlocal a
        pts = []
        for i in range(24):
            t = i / 23
            pts.append((x0 + math.cos(ang) * length * t, y0 + math.sin(ang) * length * t + math.sin(t * 3 + depth) * 6))
        for i, (px, py) in enumerate(pts):
            rad = th * (1 - i / 30)
            a = np.maximum(a, np.clip(rad + 0.8 - np.hypot(x - px, y - py), 0, 1))
        if depth < 3:
            for k in range(2):
                j = r.integers(8, 20)
                limb(pts[j][0], pts[j][1], ang + r.uniform(-0.9, 0.9), length * 0.55, th * 0.55, depth + 1)
        else:
            px, py = pts[-1]
            leaf = noise(h, w, 30, (1, 1), int(px * 7 + py)) > 0.45
            a = np.maximum(a, leaf * (np.hypot(x - px, y - py) < 14))
    limb(-4, 70, -0.25, 250, 9, 0)
    limb(-4, 30, 0.12, 190, 6, 1)
    col = ramp(noise(h, w, 12, (1, 1), seed), [(0, (22, 16, 22)), (1, (60, 46, 50))])
    rgba[..., :3] = col; rgba[..., 3] = (a > 0.5) * 255
    return rgba


def canopy(w=256, h=128, seed=131):
    """RGBA: leaf clusters hanging from the top edge (the canopy's underside), alpha cut out."""
    y, x = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    n = noise(h, w, 9, (1, 1), seed); d = noise(h, w, 30, (1, 1), seed + 1)
    edge = 0.25 + 0.55 * noise(1, w, 6, (1, 1), seed + 2)[0]
    a = ((y < edge[None, :] + (n - 0.5) * 0.3) & (d > 0.25)) * 255
    col = ramp(n * 0.7 + d * 0.3, [(0, (14, 24, 20)), (0.6, (34, 56, 38)), (1, (70, 96, 58))])
    return np.concatenate([col, a[..., None]], 2)


# ------------------------------------------------------------------------------------------------ the twilight sky
# The backdrop card spans world y 760 (v = 0) to -320 (v = 1) at z = -700; the match framings see y ~ 40-195 of it
# (x25's frame top meets it at y 142, x55's at 195; the fighters' band reaches up to y 78 and 123), so the colours are
# placed by world height: the glow just above the treeline (y ~ 45), a narrow rose band, violet, indigo from y ~ 150 up.
def _yv(y):
    return (760.0 - y) / 1080.0


def sky2(w=128, h=256, seed=151):
    """The painted backdrop: indigo, violet, a rose band, a peach-gold glow low over the trees (held off the readability
    metric's blend luminance), dim mauve below the treeline; the glow warmer and brighter left of centre."""
    y, x = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    stops = [(0.0, (14, 12, 40)), (_yv(420), (22, 20, 58)), (_yv(260), (36, 30, 80)), (_yv(215), (70, 50, 108)),
             (_yv(180), (134, 84, 122)), (_yv(155), (200, 128, 118)), (_yv(136), (160, 98, 114)), (_yv(118), (112, 70, 102)),
             (_yv(100), (122, 72, 86)), (_yv(80), (124, 72, 76)), (_yv(56), (98, 60, 72)), (_yv(20), (66, 44, 70)),
             (1.0, (44, 34, 60))]
    rgb = ramp(y, stops)
    lift = 1.0 + 0.1 * np.exp(-((x - 0.38) / 0.22) ** 2) * np.exp(-((y - _yv(82)) / 0.04) ** 2)
    return smooth(rgb * lift[..., None] + (noise(h, w, 4, (1, 1), seed) - 0.5)[..., None] * 4, 1.0)


def _canopy(w, h, seed, n, r_units, top_v, col_top, col_low, aspect=3.25, tile_units=520.0, tall=0.08):
    """RGBA: a forest canopy's silhouette for a strip card (v = 0 its top), SMRPG-round: each crown a disc with 5-9
    lobes bumping its upper rim, round on the card (a tile is `aspect` times as wide as tall, `tile_units` wide), the
    mass below each crown widening down (no vertical sides), a few taller ones with a slightly pointed top, noise on the
    rim; drawn at 4x and reduced (a soft edge for blending). Tiles in u."""
    S = 4
    W, H = w * S, h * S
    r = np.random.default_rng(seed)
    F = np.full((H, W), -1.0)                                   # > 0 inside: max over shapes of (1 - distance)
    yy, xx = np.mgrid[0:H, 0:W]
    v = (yy + 0.5) / H; u = (xx + 0.5) / W

    def blob(cx, cy, ru, rv, pointed=1.0, down=True):
        nonlocal F
        x0, x1 = int((cx - ru * 2.5) * W), int((cx + ru * 2.5) * W) + 1
        cols = np.arange(x0, x1) % W
        dx = (((u[:, cols] - cx + 0.5) % 1.0) - 0.5) / ru
        dy = (v[:, cols] - cy) / rv
        d = (np.abs(dx) ** 2 + np.abs(np.minimum(dy, 0)) ** (2 / pointed) * np.sign(1) + np.maximum(dy, 0) ** 2) ** 0.5
        f = 1 - d
        if down:                                                # below the centre: widen toward the base (no walls)
            spread = 1 + np.maximum(dy, 0) * 0.9
            f = np.maximum(f, np.where(dy > 0, 1 - np.abs(dx) / spread, -1.0))
        F[:, cols] = np.maximum(F[:, cols], f)

    for _ in range(n):
        cx = r.uniform(0, 1)
        R = r.uniform(*r_units)
        ru, rv = R / tile_units, R / tile_units * aspect
        cy = r.uniform(*top_v) + rv
        pointed = r.uniform(1.4, 1.8) if r.random() < tall else 1.0
        if pointed > 1:
            rv *= 1.5
        blob(cx, cy, ru, rv, pointed)
        for _k in range(r.integers(5, 10)):                     # lobes bumping the upper rim
            a = r.uniform(0.15, 0.85) * np.pi
            lr = r.uniform(0.3, 0.55)
            blob(cx + np.cos(a) * ru * 0.8, cy - np.sin(a) * rv * 0.8, ru * lr, rv * lr, 1.0, False)
    F = np.where(v > max(top_v) + 0.35, 1.0, F)                 # the mass below
    F += (noise(H, W, 60, (1, 1), seed + 5) - 0.5) * 0.18       # a leafy rim
    a = ((F > 0).astype(float).reshape(h, S, w, S).mean((1, 3)) * 255)
    col = ramp(noise(h, w, 10, (1, 1), seed + 2) * 0.35 + (np.mgrid[0:h, 0:w][0] / h) * 0.65, [(0, col_top), (1, col_low)])
    return np.concatenate([col, a[..., None]], 2)


def treeline(w=512, h=128, seed=161):
    """The near canopy (dark)."""
    return _canopy(w, h, seed, 48, (8, 22), (0.16, 0.42), (42, 34, 64), (24, 20, 40))


def treeline_far(w=512, h=128, seed=171):
    """A farther canopy ridge behind it, lighter and cooler (atmospheric falloff), peeking above in places."""
    return _canopy(w, h, seed, 44, (6, 15), (0.1, 0.34), (74, 64, 108), (56, 48, 86))


def _cloud(w, h, seed, n, warm, aspect=6.0):
    """RGBA: soft cloud banks, tiling in u, lit from below by the set sun: warm undersides, cool tops, soft alpha.
    Shapes are made in the card's proportions (a tile is `aspect` times as wide as tall on the card): long flat bases
    with rounded puffs on top."""
    y, x = (np.mgrid[0:h, 0:w] + 0.5) / np.array([h, w])[:, None, None]
    r = np.random.default_rng(seed)
    dens = np.zeros((h, w))
    for _ in range(n):
        cx, base = r.uniform(0, 1), r.uniform(0.62, 0.78)          # the bank's flat underside (v; 1 is the card's bottom)
        half = r.uniform(0.07, 0.14)                                # half its length, in tile widths
        dx = (((x - cx + 0.5) % 1.0) - 0.5) * aspect                 # card-isotropic units (tile height = 1)
        L = half * aspect
        body = np.clip(1 - np.hypot(dx / L, (y - base + 0.12) / 0.16), 0, 1)
        for _k in range(6):                                          # puffs on top
            px, rr = r.uniform(-0.8, 0.8) * L, r.uniform(0.12, 0.24)
            py = base - 0.14 - r.uniform(0.0, 0.12)
            body = np.maximum(body, np.clip(1 - np.hypot(dx - px, y - py) / rr, 0, 1))
        body *= y < base + 0.02                                      # flat underside
        dens = np.maximum(dens, body)
    dens = np.clip(dens * 2.2 + (noise(h, w, 12, (1, 1), seed + 1) - 0.5) * 0.4 * (dens > 0.05), 0, 1)   # texture inside only
    lit = np.clip((y - 0.35) / 0.4, 0, 1)                        # 0 at the tops, 1 underneath
    col = ramp(lit, [(0, (84, 72, 128)), (0.55, (136, 96, 136)), (1, warm)])
    a = smooth((dens ** 1.1 * 225)[..., None].repeat(3, 2), 1.4)[..., :1]
    a[a < 10] = 0; a[:2] = 0; a[-2:] = 0                         # no haze floor, clean edges (the card's edge showed)
    return np.concatenate([smooth(col, 1.0), a], 2)


def cloud_far(w=256, h=64):
    return _cloud(w, h, 171, 4, (190, 122, 128))


def cloud_mid(w=256, h=64):
    return _cloud(w, h, 181, 3, (212, 136, 118))


def cloud_near(w=256, h=64):
    return _cloud(w, h, 191, 3, (204, 130, 112))


def _stars(seed, n, w=64, h=64):
    """RGBA: n stars, a bright texel and a soft cross, a few larger; transparent elsewhere (tiles)."""
    img = np.zeros((h, w, 4))
    r = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w]
    for _ in range(n):
        cx, cy = r.uniform(0, w), r.uniform(0, h)
        big = r.random() < 0.2
        dx = ((x - cx + w / 2) % w) - w / 2; dy = ((y - cy + h / 2) % h) - h / 2
        core = np.exp(-(dx ** 2 + dy ** 2) / (0.35 if not big else 0.8))
        cross = (np.exp(-dx ** 2 / 0.25) * np.exp(-dy ** 2 / 3.0) + np.exp(-dy ** 2 / 0.25) * np.exp(-dx ** 2 / 3.0)) * (0.35 if big else 0.15)
        v = np.clip(core + cross, 0, 1)
        tint = np.array([236, 232, 255]) if r.random() < 0.7 else np.array([255, 230, 190])
        img[..., :3] = np.maximum(img[..., :3], v[..., None] * tint)
        img[..., 3] = np.maximum(img[..., 3], v * 255)
    return img


def stars_a(): return _stars(201, 4)
def stars_b(): return _stars(211, 3)
def stars_c(): return _stars(221, 3)
def stars_d(): return _stars(231, 3)


def streak(w=64, h=8):
    """RGBA: the shooting star, head at u = 1, a tapering tail to u = 0 (additive)."""
    y, x = (np.mgrid[0:h, 0:w] + 0.5) / np.array([h, w])[:, None, None]
    tail = x ** 1.4 * np.exp(-((y - 0.5) / (0.14 + 0.2 * x)) ** 2)
    head = np.exp(-(((x - 0.95) / 0.05) ** 2 + ((y - 0.5) / 0.3) ** 2))
    a = np.clip(tail * 0.9 + head, 0, 1)
    col = ramp(x, [(0, (180, 160, 255)), (0.7, (255, 236, 200)), (1, (255, 255, 240))])
    return np.concatenate([col, (a * 255)[..., None]], 2)


def glowdot(w=16, h=16):
    """RGBA: a firefly's soft glow (additive)."""
    y, x = (np.mgrid[0:h, 0:w] + 0.5) / np.array([h, w])[:, None, None] * 2 - 1
    a = np.exp(-(x ** 2 + y ** 2) / 0.18)
    col = np.zeros((h, w, 3)) + np.array([214, 236, 140])
    return np.concatenate([col, (a * 255)[..., None]], 2)


# name -> (painter, format, wrap); CMP for opaque (4 bits a texel), RGB5A3 for the cut-out cards
TEXTURES = {
    'bark': (bark, 'CMP', 'repeat'), 'birch': (birch, 'CMP', 'repeat'), 'stump_top': (stump_top, 'CMP', 'clamp'),
    'moss': (moss, 'CMP', 'repeat'), 'ground': (ground, 'CMP', 'repeat'), 'path': (path, 'CMP', 'repeat'),
    'cap_top': (cap_top, 'CMP', 'clamp'), 'gills': (gills, 'CMP', 'repeat'), 'leaves': (leaves, 'CMP', 'repeat'),
    'mush': (mush, 'CMP', 'clamp'), 'stem': (stem, 'CMP', 'repeat'), 'earth': (earth, 'CMP', 'repeat'),
    'branch': (branch, 'RGB5A3', 'clamp'),
    'bark_far': (bark_far, 'CMP', 'repeat'), 'mist': (mist, 'RGB5A3', 'clamp'),
    'sky2': (sky2, 'CMP', 'clamp'), 'treeline': (treeline, 'RGB5A3', 'u'), 'treeline_far': (treeline_far, 'RGB5A3', 'u'),
    'cloud_far': (cloud_far, 'RGB5A3', 'u'), 'cloud_mid': (cloud_mid, 'RGB5A3', 'u'),
    'cloud_near': (cloud_near, 'RGB5A3', 'u'),
    'stars_a': (stars_a, 'RGB5A3', 'repeat'), 'stars_b': (stars_b, 'RGB5A3', 'repeat'),
    'stars_c': (stars_c, 'RGB5A3', 'repeat'), 'stars_d': (stars_d, 'RGB5A3', 'repeat'),
    'streak': (streak, 'RGB5A3', 'clamp'), 'glowdot': (glowdot, 'RGB5A3', 'clamp'),
}
BYTES = {'CMP': 0.5, 'RGB5A3': 2, 'RGB565': 2}


def write(out):
    """Paint every texture into out/ (PNG to look at, raw BGRA for stage-build); -> {name: material fields}."""
    os.makedirs(out, exist_ok=True)
    mats, total = {}, 0
    for name, (fn, fmt, wrap) in TEXTURES.items():
        a = fn()
        if a.shape[2] == 3:
            a = np.concatenate([a, np.full(a.shape[:2] + (1,), 255.0)], 2)
        a = np.clip(a, 0, 255).astype(np.uint8)
        h, w = a.shape[:2]
        Image.fromarray(a).save(os.path.join(out, name + '.png'))
        open(os.path.join(out, name + '.bgra'), 'wb').write(a[..., [2, 1, 0, 3]].tobytes())
        mats[name] = dict(texture=f'art2/{name}.bgra', size=[w, h], format=fmt, wrap=wrap)
        total += int(w * h * BYTES[fmt])
    return mats, total


if __name__ == '__main__':
    out = sys.argv[1]
    mats, total = write(out)
    for k, m in mats.items():
        print(f"{k:10s} {m['size'][0]}x{m['size'][1]} {m['format']}")
    print(f'texture bytes {total}')
