"""paint.py: paint Geno's textures (original procedural art) for the UVs geno_geo.py lays out.

  python paint.py OUTDIR [--ao AODIR]        # (the repo's .venv python: numpy, scipy, PIL)

Every texture is painted in 3D: its triangles are rasterised into UV space as position and normal maps, and the colour
is a function of the surface point (turned wood with rings and streaks along each part's own log axis, felt, leather,
brass, paper), so the grain runs continuously across UV seams and a decal (the emblem, the eye patches) carries exactly
the wood or felt beneath it. Carved seams, folds and the painted details are signed-distance shapes on top; distance-
limited ambient occlusion baked in Blender (build_model.py --bake) is multiplied in lightly, as Melee's textures carry
their shading. Gutters are filled outward so bilinear filtering never picks up the background.
Writes OUTDIR/<tex>.png for every texture, the six eye frames eye_0..eye_5.png, and sizes.json.
"""
import json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geno_geo as G  # noqa: E402
import geno_low as GL  # noqa: E402

from paint_sizes import SIZES  # noqa: E402
SS = 3   # supersampling of the rasteriser


def C(*rgb):
    return np.array(rgb, float) / 255.0


# ---------------------------------------------------------------------------------------------------------------------
# noise (deterministic value noise)
def _hash(ix, iy, iz, seed):
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761 & 0xffffffff)
    h = h & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    h = h ^ (h >> 16)
    return (h & 0xffffff).astype(np.float64) / float(0x1000000)


def vnoise(P, seed=0):
    P = np.asarray(P, float)
    i = np.floor(P).astype(np.int64); f = P - i
    f = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[..., 0] if dx else 1 - f[..., 0]) * (f[..., 1] if dy else 1 - f[..., 1]) * (f[..., 2] if dz else 1 - f[..., 2])
                out = out + w * _hash(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz, seed)
    return out


def fbm(P, freq=1.0, octaves=3, seed=0, gain=0.5):
    tot, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        tot = tot + amp * (vnoise(np.asarray(P) * freq * (2 ** o), seed + 17 * o) - 0.5)
        norm += amp; amp *= gain
    return tot / norm      # about [-0.5, 0.5]


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    t = np.asarray(t)[..., None] if np.ndim(t) else t
    return a * (1 - t) + b * t


# ---------------------------------------------------------------------------------------------------------------------
# rasteriser: triangles in UV space -> per-texel attributes
def vertex_normals(V, F):
    N = np.zeros_like(V)
    for f in F:
        p = V[list(f)]
        for k in range(1, len(f) - 1):
            n = np.cross(p[k] - p[0], p[k + 1] - p[0])
            for idx in (f[0], f[k], f[k + 1]): N[idx] += n
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)


def gather(meshes, tex):
    """Triangles of every mesh using tex: uv (T,3,2), attributes (T,3,K) = position(3) normal(3) mesh id(1) + vertex
    params. Positions use the design pose where the mesh has one (the cape), and |x| (mirrored halves share texels)."""
    uv, at = [], []
    names = []
    for mi, m in enumerate(meshes):
        if m.tex != tex: continue
        names.append(m.name)
        V = np.array(m.attr['design'], float) if 'design' in m.attr else np.array(m.V)
        N = vertex_normals(V, m.F)
        UV = np.array(m.UV)
        for f in m.F:
            for k in range(1, len(f) - 1):
                idx = [f[0], f[k], f[k + 1]]
                p = V[idx].copy(); n = N[idx].copy()
                neg = p[:, 0].mean() < 0
                if neg: p[:, 0] *= -1; n[:, 0] *= -1
                uv.append(UV[idx])
                at.append(np.concatenate([p, n, np.full((3, 1), len(names) - 1)], axis=1))
    return np.array(uv), np.array(at), names


def raster(uv, at, W, H, ss=SS):
    Wp, Hp = W * ss, H * ss
    K = at.shape[2]
    acc = np.zeros((Hp, Wp, K)); cov = np.zeros((Hp, Wp), bool)
    for t in range(len(uv)):
        p = uv[t] * [Wp, Hp]
        x0 = max(int(np.floor(p[:, 0].min())), 0); x1 = min(int(np.ceil(p[:, 0].max())), Wp - 1)
        y0 = max(int(np.floor(p[:, 1].min())), 0); y1 = min(int(np.ceil(p[:, 1].max())), Hp - 1)
        if x1 < x0 or y1 < y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        (ax, ay), (bx, by), (cx, cy) = p
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12: continue
        l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
        l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
        l3 = 1 - l1 - l2
        ins = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        if not ins.any(): continue
        vals = l1[..., None] * at[t, 0] + l2[..., None] * at[t, 1] + l3[..., None] * at[t, 2]
        sub = acc[y0:y1 + 1, x0:x1 + 1]; c = cov[y0:y1 + 1, x0:x1 + 1]
        sub[ins] = vals[ins]; c[ins] = True
    # downsample: average the covered subsamples
    a = acc.reshape(H, ss, W, ss, K); c = cov.reshape(H, ss, W, ss).astype(float)
    n = c.sum((1, 3))
    out = (a * c[..., None]).sum((1, 3)) / np.maximum(n, 1)[..., None]
    mask = n > 0
    return out, mask, cov


def fill_gutters(img, mask):
    if mask.all(): return img
    _, (iy, ix) = ndimage.distance_transform_edt(~mask, return_indices=True)
    return img[iy, ix]


UP = 2   # every texture is painted at UP x its size and box-filtered down: anti-aliased seams, calmer grain


def downsample(img, W, H):
    """Box-filter a painted (UP x) image to the texture's size."""
    k = img.shape[0] // H
    return img.reshape(H, k, W, k, -1).mean((1, 3))


class Ctx:
    def __init__(self, tex, meshes, ao_dir=None):
        self.tex = tex
        W, H = SIZES[tex]
        self.W0, self.H0 = W, H
        W, H = W * UP, H * UP
        self.W, self.H = W, H
        uv, at, self.names = gather(meshes, tex)
        out, self.mask, _ = raster(uv, at, W, H, ss=2)
        self.P = out[..., 0:3]; self.N = out[..., 3:6]
        self.N = self.N / np.maximum(np.linalg.norm(self.N, axis=2, keepdims=True), 1e-9)
        self.mid = np.round(out[..., 6]).astype(int)
        u, v = np.meshgrid((np.arange(W) + 0.5) / W, (np.arange(H) + 0.5) / H)
        self.u, self.v = u, v
        self.ao = np.ones((H, W))
        if ao_dir:
            p = os.path.join(ao_dir, f'ao_{tex}.png')
            if os.path.exists(p):
                a = np.array(Image.open(p).convert('L'), float) / 255
                a = ndimage.gaussian_filter(a, 1.6)
                a = np.array(Image.fromarray((a * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS), float) / 255
                self.ao = np.clip(0.35 + 0.65 * a / 0.85, 0.45, 1.0)


# ---------------------------------------------------------------------------------------------------------------------
# materials
# calibrated in game (Gate 1d): Melee's lights lift a REPLACE texture ~1.2x on the lit side, so the wood is painted darker
# and richer than it should look in Blender
WOOD_L, WOOD_M, WOOD_D, WOOD_G = C(212, 142, 74), C(190, 118, 56), C(158, 90, 40), C(108, 56, 24)
DARKWOOD_L, DARKWOOD_M, DARKWOOD_G = C(176, 110, 58), C(150, 90, 44), C(104, 60, 26)
BLUE_L, BLUE_M, BLUE_D, BLUE_P = C(92, 150, 238), C(52, 108, 218), C(26, 62, 158), C(70, 70, 190)
YEL_L, YEL_M, YEL_D = C(255, 222, 88), C(250, 190, 36), C(206, 132, 18)


def wood(P, axis_o, axis_d, freq=2.0, seed=0, dark=False, streak=1.0, warp=0.22, lines=1.0, warp_along=1.0, contrast=1.0):
    """Turned, lacquered wood: the growth rings of a (warped) log whose axis runs along the part. Soft early/late-wood
    bands, thin darker ring lines (continuous, ~1.5 texels), a slow colour drift along the grain. Surfaces cut along
    the axis get long streaks; oblique cuts get cathedral arches; end grain gets concentric rings."""
    axis_d = np.asarray(axis_d, float); axis_d /= np.linalg.norm(axis_d)
    d = P - np.asarray(axis_o, float)
    along = d @ axis_d
    radial = d - along[..., None] * axis_d
    Ps = radial + along[..., None] * axis_d * 0.15          # coordinates stretched along the grain
    r = np.linalg.norm(radial, axis=-1)
    Pw = radial + along[..., None] * axis_d * warp_along      # warp_along < 1: the waviness runs along the grain
    r = r + warp * fbm(Pw, 0.45, 3, seed) + 0.035 * fbm(Ps, 2.6, 2, seed + 5)
    t1 = r * freq
    bands = 0.5 + 0.5 * np.cos(2 * math.pi * t1)             # 1 = early wood (light), 0 = late wood
    f2 = freq * 3.0
    t2 = r * f2 + 0.25 * fbm(Ps, 1.4, 2, seed + 7)
    fr = t2 % 1.0
    dist = np.minimum(fr, 1 - fr) / f2                        # world distance to the nearest ring line
    line = 1 - sstep(0.006, 0.02, dist)
    strength = np.clip(0.55 + 1.6 * fbm(Ps, 1.1, 2, seed + 9), 0.15, 1.0)
    drift = fbm(Ps, 0.5, 2, seed + 31)
    if dark:
        c = mix(DARKWOOD_L, DARKWOOD_M, np.clip(0.55 - 0.35 * bands + 1.2 * drift, 0, 1))
        c = mix(c, DARKWOOD_G, np.clip(0.35 * line * strength * lines, 0, 1))
    else:
        c = mix(WOOD_L, WOOD_M, np.clip(0.62 - 0.42 * bands + 1.3 * drift, 0, 1))
        c = mix(c, WOOD_D, np.clip(0.28 * (1 - bands) * streak, 0, 1))
        c = mix(c, WOOD_G, np.clip(0.5 * line * strength * lines, 0, 0.7))
    if contrast != 1.0:            # pull the grain toward the local average (the slow colour drift stays)
        base = mix(DARKWOOD_L, DARKWOOD_M, np.clip(0.4 + 1.2 * drift, 0, 1)) if dark else \
            mix(WOOD_L, WOOD_M, np.clip(0.55 + 1.3 * drift, 0, 1)) * 0.96
        c = base + contrast * (c - base)
    return c


def felt(P, base_l, base_m, base_d, seed=0, mottle=1.0):
    n1 = fbm(P, 0.9, 3, seed); n2 = fbm(P, 4.0, 2, seed + 3); n3 = fbm(P, 16.0, 1, seed + 7)
    t = np.clip(0.5 + 1.1 * n1 * mottle + 0.35 * n2, 0, 1)
    c = mix(base_l, base_m, 0.55 + 0.45 * (t - 0.5) * 2 * 0.6)
    c = mix(c, base_d, np.clip(-n1 * 0.8 * mottle, 0, 0.35))
    c = c * (1 + 0.07 * n3[..., None] + 0.04 * n2[..., None])
    return c


def carve(c, dist, width=0.035, depth=0.55, light_side=None, dist_lit=None):
    """A carved channel at distance dist from its centre line: a dark floor, a lit wall on the side facing the light
    (dist_lit: the distance sampled a little toward the light; smaller there = this side faces the light)."""
    core = 1 - sstep(width * 0.3, width, np.abs(dist))
    c = c * (1 - depth * core[..., None])
    if dist_lit is not None:
        near = (1 - sstep(width * 0.8, width * 2.0, dist)) * sstep(width * 0.4, width * 0.9, dist)
        lit = np.where(dist_lit < dist, 1.0, -0.6)
        c = c * (1 + 0.22 * near * lit)[..., None]
    return c


def seg_dist(px, py, pts):
    """Distance from (px, py) arrays to a 2D polyline."""
    best = np.full(px.shape, 1e9)
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        dx, dy = bx - ax, by - ay
        t = np.clip(((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy + 1e-12), 0, 1)
        best = np.minimum(best, np.hypot(px - ax - t * dx, py - ay - t * dy))
    return best


def shade(ctx, c, ao_amt=0.55, top=0.08):
    """Light painted shading: baked AO, a hint of top light."""
    a = 1 - ao_amt * (1 - ctx.ao)
    t = 1 + top * np.clip(ctx.N[..., 1], -1, 1)
    return c * a[..., None] * t[..., None]


# ---------------------------------------------------------------------------------------------------------------------
# per-texture painters. P is the surface point (x mirrored to >= 0), N its normal.
HEAD_AXIS = ((0.0, 12.6, -5.5), (0.08, 1.0, 0.12))     # back of the head: rings round a log behind it
FACE_AXIS = ((-9.0, 12.6, -1.2), (0.03, 1.0, 0.0))     # the face: vertical grain (a log far to the side)


def _hs(pts):
    """Face features drawn for the Gate 1 head, carried onto the grown head (front projection x, y)."""
    return [(x * G.HEAD_K, G.HC[1] + G.HEAD_K * (y - G.HC0[1])) for x, y in pts]


# cheek seams from under the eyes down off the jaw; the marionette mouth: a line whose corners turn down and run off the
# bottom of the chin (the jaw is a hinged block, open at the bottom)
FACE_SEAM = _hs([(0.8, 12.3), (0.81, 11.7), (0.86, 11.15), (0.95, 10.72), (1.02, 10.3), (1.05, 10.0)])
FACE_JAW = _hs([(0.0, 11.44), (0.44, 11.44), (0.47, 11.38), (0.5, 10.95), (0.56, 10.5), (0.64, 10.05)])
LIGHT2 = np.array([-0.55, 0.83])


def face_dist(x, y):
    return np.minimum(seg_dist(x, y, FACE_SEAM), seg_dist(x, y, FACE_JAW))


def face_details(P):
    """Carved lines of the face: cheek seams and the mouth board, in the front projection (x, y)."""
    x, y = P[..., 0], P[..., 1]
    front = P[..., 2] > 0.6
    d = np.where(front, face_dist(x, y), 1e9)
    dl = np.where(front, face_dist(x + LIGHT2[0] * 0.03 * np.sign(x + 1e-9), y + LIGHT2[1] * 0.03), 1e9)
    return d, dl


def face_wood(P):
    return wood(P, *FACE_AXIS, freq=2.6, seed=1, warp=0.16, warp_along=0.25, contrast=0.75)


def paint_face(ctx):
    P = ctx.P
    c = face_wood(P)
    d, dl = face_details(P)
    c = carve(c, d, width=0.075, depth=0.5, dist_lit=dl)
    x, y = P[..., 0], P[..., 1]
    # the mouth is a step: the jaw sits back under the upper face, so a soft shadow falls just under the groove
    my = FACE_JAW[0][1]; jx = FACE_JAW[1][0]
    under = (np.abs(x) < jx) & (y < my) & (P[..., 2] > 0.6)
    c = np.where(under[..., None], c * (1 - 0.22 * (1 - sstep(0.0, 0.2, my - y)))[..., None], c)
    # eye sockets: a soft darkening round each eye patch
    ec = G.skull_pt(G.EYE_C[1], G.EYE_C[0])
    de = np.linalg.norm((P - ec) / np.array([0.8, 0.66, 0.9]), axis=-1)
    c = c * (1 - 0.1 * (1 - sstep(1.0, 1.25, de)))[..., None]
    # a soft occlusion shadow on the face just under the nose (the nose itself is a separate carved wedge)
    ny = G.HC[1] + G.HEAD_K * (11.88 - G.HC0[1])
    nz = np.hypot(x / 0.34, (y - ny) / 0.16)
    c = c * (1 - 0.28 * (1 - sstep(0.4, 1.15, nz)) * (P[..., 2] > 1.5))[..., None]
    return shade(ctx, c, 0.65)


def paint_nose(ctx):
    """The same wood as the face; each plane painted by how it would be lit (Melee's lights are soft): the ridge a
    little darker than the face, the side planes darker, the underside darkest, so the wedge reads as a carved, slightly
    darker triangle against the face with depth."""
    c = face_wood(ctx.P)
    ridge = (ctx.u < 0.5) & (ctx.v < 0.5); under = (ctx.u >= 0.5) & (ctx.v >= 0.5)
    k = np.where(ridge, 0.9, np.where(under, 0.55, 0.72))
    return shade(ctx, c * k[..., None], 0.0, top=0.0)


def paint_headback(ctx):
    c = wood(ctx.P, *HEAD_AXIS, freq=2.2, seed=1, contrast=0.75)
    return shade(ctx, c, 0.65)


def paint_ears(ctx):
    P = ctx.P
    ear = ctx.v < 0.72
    ec = G.skull_pt(-5 * G.D2R, 90 * G.D2R, 0.1)
    c_ear = wood(P, ec, (1.0, 0.0, -0.2), freq=4.2, seed=3, warp=0.08)
    # the hollow of the ear: darker in the middle
    r = np.hypot(P[..., 1] - ec[1], (P[..., 2] - ec[2]) * 1.4)
    c_ear = c_ear * (1 - 0.28 * (1 - sstep(0.12, 0.34, r)))[..., None]
    c_nose = face_wood(P)
    c = np.where(ear[..., None], shade(ctx, c_ear, 0.55), shade(ctx, c_nose * 1.06, 0.1))
    return c


FELT_HI, FELT_MID, FELT_LO, FELT_DEEP = C(118, 178, 246), C(56, 112, 222), C(36, 70, 176), C(44, 40, 132)


def painted_felt(P, seed, mottle=1.0):
    """Felt as a painter would lay it in: a soft two-tone mottle (cool light, purple-blue dark), a faint nap."""
    n1 = fbm(P, 0.7, 3, seed); n2 = fbm(P, 2.6, 2, seed + 3)
    c = mix(FELT_MID, FELT_HI, np.clip(0.12 + 0.7 * n1 * mottle, 0, 0.32))
    c = mix(c, FELT_LO, np.clip(-0.8 * n1 * mottle + 0.08 * n2, 0, 0.25))
    nap = fbm(P * np.array([1, 3.5, 1]), 9.0, 2, seed + 7)    # short fibres, a hint of direction
    c = c * (1 + 0.05 * nap[..., None] + 0.03 * n2[..., None])
    return c


def painted_ridges(u, v, ridges, light=(0.45, -0.9)):
    """Soft painted folds in UV space: each ridge (u0, u1 at v=0 and v=1, width, height) raises a smooth crease; the
    height field is shaded by a fixed painted light, giving a lit side and a shadowed side like brushed-in folds."""
    h = np.zeros_like(u)
    for (a, b, w, amp, v0, v1) in ridges:
        uc = a + (b - a) * v
        fade = sstep(v0, v0 + 0.15, v) * (1 - sstep(v1 - 0.15, v1, v))
        h += amp * np.exp(-((u - uc) / w) ** 2) * fade
    gy, gx = np.gradient(h)
    shade_ = -(gx * light[0] + gy * light[1]) * 40
    return np.clip(shade_, -1, 1), h


def paint_band(ctx):
    P = ctx.P
    c = painted_felt(P, 41)
    v, u = ctx.v, ctx.u
    # the rolled cuff: a highlight along the roll's crown, a soft shadow tucked under it and at the top seam
    roll = np.exp(-((v - 0.36) / 0.2) ** 2)
    under = sstep(0.62, 1.0, v)
    top = 1 - sstep(0.0, 0.12, v)
    c = mix(c, FELT_HI, 0.35 * roll)
    c = mix(c, FELT_DEEP, 0.45 * under + 0.35 * top)
    # bunching: a few soft vertical folds round the cuff
    rid = [(0.2, 0.22, 0.05, 0.6, 0.1, 0.9), (0.52, 0.5, 0.06, 0.5, 0.1, 0.9), (0.83, 0.85, 0.05, 0.6, 0.1, 0.9)]
    s, _ = painted_ridges(u, v, rid, light=(1.0, 0.0))
    c = mix(c, FELT_HI, np.clip(s, 0, 1) * 0.14)
    c = mix(c, FELT_DEEP, np.clip(-s, 0, 1) * 0.14)
    return shade(ctx, c, 0.5, top=0.0)


def crown_folds(P):
    """(kept for the emblem's background) soft folds running from the band up to the point."""
    th = np.arctan2(P[..., 0], P[..., 2] + 1.2)
    return np.sin(th * 7 + 2.0 * fbm(P, 0.7, 2, 55) * 6)


CROWN_RIDGES = [  # u at the tip (v=0) and at the band (v=1), width, height, v range: a few broad folds from the point
    (0.7, 0.28, 0.07, 1.0, 0.05, 0.9), (0.86, 0.6, 0.08, 0.8, 0.0, 0.85), (0.97, 0.9, 0.06, 0.7, 0.05, 0.9)]


def paint_crown(ctx):
    P = ctx.P
    c = painted_felt(P, 51)
    s, h = painted_ridges(ctx.u, ctx.v, CROWN_RIDGES)
    c = mix(c, FELT_HI, np.clip(s, 0, 1) * 0.22)
    c = mix(c, FELT_DEEP, np.clip(-s, 0, 1) * 0.22)
    # a broad painted gradient: light on the crown's top and front, darker under the drooping point and to the back
    up = np.clip(ctx.N[..., 1], -1, 1)
    c = mix(c, FELT_HI, np.clip(up, 0, 1) * 0.18)
    c = mix(c, FELT_DEEP, np.clip(-up, 0, 1) * 0.4 + 0.2 * sstep(0.55, 1.0, ctx.u))
    c = shade(ctx, c, 0.55, top=0.0)
    # the bow painted under the emblem mesh: hidden on the high model, the emblem itself on the low model's cap
    mk = ndimage.binary_erosion(emblem_mask_on_crown(ctx.W, ctx.H), iterations=1).astype(float)
    y = felt(P, YEL_L, YEL_M, YEL_D, seed=61, mottle=0.5)
    return mix(c, y, np.clip(mk, 0, 1))


def emblem_mask_on_crown(W, H):
    """The bow's footprint in the crown texture (rasterised from the emblem mesh through the crown's UV mapping)."""
    em = [m for m in G.build() if m.name == 'emblem'][0]
    uv, at = [], []
    for f in em.F:
        for k in range(1, len(f) - 1):
            idx = [f[0], f[k], f[k + 1]]
            q = []
            for i in idx:
                p = em.V[i]
                # recover the emblem-plane (x, y) from the vertex: theta from x/z about the head axis, s by nearest v
                q.append(em.attr['crown_uv'][i])
            uv.append(q); at.append(np.ones((3, 1)))
    _, mask, _ = raster(np.array(uv), np.array(at), W, H)
    return mask


def emblem_shape(u, v):
    """The ribbon-bow emblem in its patch (u 0..1 across, v 0..1 top to bottom): (inside, outline distance)."""
    x = (u - 0.5) * 2.0       # -1..1 across
    y = (0.52 - v) * 1.0      # up
    def ell(cx, cy, a, b, rot=0.0):
        cr, sr = math.cos(rot), math.sin(rot)
        xx = (x - cx) * cr + (y - cy) * sr; yy = -(x - cx) * sr + (y - cy) * cr
        return np.hypot(xx / a, yy / b)
    L_out = ell(-0.42, 0.06, 0.4, 0.27, -0.15); L_in = ell(-0.44, 0.07, 0.22, 0.12, -0.15)
    R_out = ell(0.42, 0.06, 0.4, 0.27, 0.15); R_in = ell(0.44, 0.07, 0.22, 0.12, 0.15)
    knot = ell(0.0, 0.0, 0.13, 0.16)
    tailL = np.maximum(np.abs(x + 0.1 + (y + 0.2) * 0.3) / 0.07, np.abs(y + 0.18) / 0.2)
    tailR = np.maximum(np.abs(x - 0.1 - (y + 0.2) * 0.3) / 0.07, np.abs(y + 0.18) / 0.2)
    loops = np.minimum(L_out, R_out)
    holes = np.minimum(L_in, R_in)
    solid = np.minimum(np.minimum(np.maximum(loops, 2 - holes), knot), np.minimum(tailL, tailR))
    return solid


def paint_emblem(ctx):
    P = ctx.P
    y = felt(P, YEL_L, YEL_M, YEL_D, seed=61, mottle=0.5)
    # the sewn edge: darker toward each ring's rims (uv: ring li centred at u=0.25/0.75)
    cu = np.where(ctx.u < 0.5, 0.25, 0.75)
    r = np.hypot((ctx.u - cu) / 0.24, (ctx.v - 0.5) / 0.46)
    rim = np.where((np.abs(ctx.u - 0.5) < 0.1), 0.0, 0.8 * sstep(0.9, 0.99, r) + 0.6 * (1 - sstep(0.45, 0.51, r)))
    y = y * (1 - 0.22 * np.clip(rim, 0, 1))[..., None]
    return shade(ctx, y, 0.3)


def paint_curls(ctx):
    u, v = ctx.u, ctx.v
    t = (v % 0.5) / 0.5                      # 0 at the band, 1 at the spiral's heart
    OR_L, OR_M, OR_D = C(255, 168, 70), C(240, 118, 28), C(186, 70, 14)
    base = mix(OR_L, OR_M, 0.45 + 0.4 * t)
    base = mix(base, OR_D, 0.55 * sstep(0.55, 1.0, t))
    edge = np.minimum(u, 1 - u)
    base = base * (1 - 0.3 * (1 - sstep(0.0, 0.12, edge)))[..., None]
    base = base * (1 + 0.1 * np.exp(-((u - 0.3) / 0.12) ** 2))[..., None]
    fib = fbm(np.stack([u * 3, v * 40, u * 0], -1), 1.0, 2, 71)
    base = base * (1 + 0.06 * fib[..., None])
    return shade(ctx, base, 0.5, top=0.0)


def paint_collar(ctx):
    P = ctx.P
    vv = ctx.v                                                  # 0 = top edge, 1 = base
    c = felt(P, BLUE_L, BLUE_M, BLUE_D, seed=81)
    c = c * (1 - 0.18 * (1 - sstep(0.03, 0.12, vv)))[..., None]
    return shade(ctx, c, 0.3, top=0.05)


def paint_collarin(ctx):
    P = ctx.P
    vv = ctx.v
    c = felt(P, YEL_L, YEL_M, YEL_D, seed=83, mottle=0.7)
    c = mix(c, YEL_D, 0.45 * sstep(0.45, 1.0, vv))           # the lining darkens down into the neck
    c = mix(c, painted_felt(P, 81) * 0.95, 1 - sstep(0.035, 0.06, vv))   # thin blue piping along the top edge
    return shade(ctx, c, 0.3, top=0.05)


def cape_folds(P):
    th = np.arctan2(P[..., 0], P[..., 2] - G.TORSO_Z)
    ph = 1.6 * fbm(P * np.array([1, 0.2, 1]), 0.8, 2, 91) * 6
    return np.sin(th * 9 + ph)


def paint_cape(ctx):
    P = ctx.P
    c = felt(P, BLUE_L, BLUE_M, BLUE_D, seed=101)
    f = cape_folds(P)
    hang = sstep(9.8, 6.5, P[..., 1])
    c = c * (1 + 0.1 * f * hang)[..., None]
    st = fbm(P, 0.7, 2, 105)
    c = mix(c, BLUE_P * 0.9, np.clip((st - 0.14) * 1.4, 0, 0.3))
    return shade(ctx, c, 0.35)


def paint_lining(ctx):
    P = ctx.P
    c = felt(P, YEL_L, YEL_M, YEL_D, seed=111, mottle=0.7)
    f = cape_folds(P)
    c = c * (1 + 0.08 * f * sstep(9.8, 6.5, P[..., 1]))[..., None]
    return shade(ctx, c, 0.35)


def paint_clasp(ctx):
    u, v = ctx.u, ctx.v
    rope = v < 0.49
    # the rope: two twisted strands, gold
    # two twisted strands: diagonal bands, each rounded (light in the middle, a dark groove between strands)
    t = (u * 2 + (v / 0.44) * 5) % 1.0
    strand = np.sin(t * math.pi) ** 0.7
    GOLD_L, GOLD_M, GOLD_D = C(255, 214, 96), C(232, 172, 52), C(150, 96, 22)
    cr = mix(GOLD_D, GOLD_M, sstep(0.05, 0.6, strand))
    cr = mix(cr, GOLD_L, sstep(0.75, 1.0, strand) * 0.7)
    # the grommet: polished brass ring (u around, v across the lip)
    BR_L, BR_M, BR_D = C(255, 236, 160), C(206, 160, 66), C(110, 74, 24)
    vv = (v - 0.54) / 0.46
    lip = np.sin(np.clip(vv, 0, 1) * math.pi)
    cb = mix(BR_D, BR_M, sstep(0.0, 0.6, lip))
    cb = mix(cb, BR_L, sstep(0.75, 1.0, lip) * (0.6 + 0.4 * np.cos(u * 2 * math.pi * 1)))
    c = np.where(rope[..., None], cr, cb)
    return shade(ctx, c, 0.4, top=0.0)


def chest_details(P):
    """Carved plates of the chest: the pectoral line, the sternum, the rib line, the back's shoulder blades and spine."""
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    front = z > G.TORSO_Z
    # a smooth barrel: only the chest plate's lower edge and a faint sternum
    df = seg_dist(x, y, [(0.0, 8.85), (0.4, 8.7), (0.9, 8.68), (1.3, 8.85), (1.6, 9.25)])
    db = seg_dist(x, y, [(0.0, 10.2), (0.0, 7.3)])              # the back: just the spine groove
    return np.where(front, df, db)


def paint_chest(ctx):
    P = ctx.P
    c = wood(P, (-9.0, 8.0, -1.0), (0.04, 1.0, 0.0), freq=2.2, seed=121, warp=0.16, warp_along=0.3, contrast=0.5)   # vertical grain
    d = chest_details(P)
    dl = chest_details(P + np.array([LIGHT2[0] * 0.03, LIGHT2[1] * 0.03, 0.0]))
    c = carve(c, d, width=0.055, depth=0.22, dist_lit=dl)
    sternum = np.where(ctx.P[..., 2] > G.TORSO_Z, np.abs(ctx.P[..., 0]) + 1e9 * (ctx.P[..., 1] < 8.9) + 1e9 * (ctx.P[..., 1] > 10.0), 1e9)
    c = carve(c, sternum, width=0.04, depth=0.18)
    # the neck: a darker turned ring where it meets the head
    c = np.where((P[..., 1] > 10.5)[..., None], c * 0.86, c)
    return shade(ctx, c, 0.6)


def paint_pelvis(ctx):
    P = ctx.P
    c = wood(P, (-9.0, 6.2, -1.0), (0.05, 1.0, 0.0), freq=2.2, seed=131, warp=0.16, warp_along=0.3, contrast=0.5)
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    # a waistband groove and the rims of the leg openings
    band = np.abs(y - 6.8)
    c = carve(c, band, width=0.05, depth=0.35)
    return shade(ctx, c, 0.65)


def paint_joint(ctx):
    P = ctx.P
    # each ball is turned on its own axis; the waist ball on the vertical
    c = np.zeros(P.shape)
    for i, name in enumerate(ctx.names):
        sel = ctx.mid == i
        if not sel.any(): continue
        if name == 'waist':
            cc = wood(P, (0.0, 6.98, G.TORSO_Z), (0, 1, 0), freq=4.0, seed=141, dark=True, contrast=0.6)
        else:
            cc = wood(P, (0.0, 0.0, 0.0), (0, 0, 1), freq=3.0, seed=143, dark=True, contrast=0.6)
        c[sel] = cc[sel]
    return shade(ctx, c, 0.5)


def limb_painter(joint, seed, freq=3.2):
    def f(ctx):
        W = G.REST[joint]
        c = wood(ctx.P, W[3, :3] + np.array([0.0, 1.9, 2.2]), W[0, :3], freq=freq * 0.8, seed=seed, contrast=0.5)
        # turned ends: a darker band at each end of the segment
        along = (ctx.P - W[3, :3]) @ W[0, :3]
        return shade(ctx, c, 0.6)
    return f


def paint_palm(ctx):
    W = G.REST['LHandN']
    c = wood(ctx.P, W[3, :3] + np.array([0, 1.9, -2.2]), W[0, :3], freq=2.6, seed=151, contrast=0.55)
    # soft creases where the fingers leave the palm, on the palm side only
    x, y, z = ctx.P[..., 0], ctx.P[..., 1], ctx.P[..., 2]
    lx = x - W[3, 0]
    palm_side = z > W[3, 2] + 0.05
    for yy in (10.24, 10.0, 9.77):
        c = carve(c, np.where(palm_side & (lx > 0.55), np.abs(y - yy), 1e9), width=0.03, depth=0.25)
    return shade(ctx, c, 0.6)


def paint_finger(ctx):
    W = G.REST['LHandN']
    c = wood(ctx.P, W[3, :3] + np.array([0, 1.9, -2.2]), W[0, :3], freq=2.6, seed=151, contrast=0.55)
    # darker joint rings at the segment ends
    vv = np.where(ctx.v < 0.5, ctx.v * 2, (ctx.v - 0.5) * 2)
    ends = 1 - sstep(0.06, 0.16, np.minimum(vv, 1 - vv))
    c = c * (1 - 0.22 * ends)[..., None]
    return shade(ctx, c, 0.6)


LEATHER_L, LEATHER_M, LEATHER_D = C(118, 80, 52), C(88, 56, 34), C(52, 32, 20)    # toward Mario's matte brown


def paint_boot(ctx):
    P = ctx.P
    n1 = fbm(P, 1.1, 3, 161); n2 = fbm(P, 6.0, 2, 163)
    c = mix(LEATHER_M, LEATHER_L, np.clip(0.25 + 0.9 * n1, 0, 1))
    c = mix(c, LEATHER_D, np.clip(-0.9 * n1, 0, 0.5))
    c = c * (1 + 0.08 * n2[..., None])
    y = P[..., 1] / 1.12 - 0.2 * sstep(1.3, 2.4, P[..., 2]) ** 2   # height above the (rockered) sole line (boots scaled 1.12 up)
    SOLE_L, SOLE_D = C(176, 138, 92), C(136, 102, 64)
    sole_c = mix(SOLE_L, SOLE_D, np.clip(0.5 + n1, 0, 1)) * (1 + 0.06 * n2[..., None])
    sole_c = mix(sole_c, SOLE_D * 0.85, sstep(0.08, 0.0, y))        # the tread edge underneath
    band = 1 - sstep(0.31, 0.35, y)
    c = mix(c, sole_c, band)
    c = c * (1 - 0.3 * (1 - sstep(0.0, 0.05, np.abs(y - 0.345))) * (y > 0.3))[..., None]   # the seam where the upper meets the sole
    # polish on the toe cap
    toe = np.exp(-(((P[..., 2] - 1.3) / 0.6) ** 2 + ((y - 0.85) / 0.35) ** 2))
    c = c * (1 + 0.08 * toe)[..., None]
    return shade(ctx, c, 0.6)


def paint_cuff(ctx):
    P = ctx.P
    n1 = fbm(P, 1.4, 3, 171)
    c = mix(C(80, 52, 32), C(108, 72, 46), np.clip(0.4 + n1, 0, 1))
    v = ctx.v
    roll = np.sin(np.clip(1 - v, 0, 1) * math.pi)
    c = c * (0.72 + 0.34 * roll)[..., None]
    cre = fbm(P * np.array([4, 1, 4]), 1.0, 2, 173)
    c = c * (1 + 0.1 * cre[..., None])
    return shade(ctx, c, 0.5)


OUT_DIR = None          # where main() writes: paint_lowface starts from the finished high face texture there


def sample(img, u, v):
    """Bilinear sample of an (H, W, 3) image at UVs (texel centres at (i + 0.5) / size), clamped."""
    H, W = img.shape[:2]
    x = np.clip(u * W - 0.5, 0, W - 1); y = np.clip(v * H - 0.5, 0, H - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, W - 1), np.minimum(y0 + 1, H - 1)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    return (img[y0, x0] * (1 - fx) + img[y0, x1] * fx) * (1 - fy) + (img[y1, x0] * (1 - fx) + img[y1, x1] * fx) * fy


def paint_lowface(ctx):
    """The low model's face (the front half of its head; geno_low.low_head): the high face texture itself (its wood,
    carving and baked shading: so the low head meets the high model's headback, which its back half wears, without a
    seam), resampled onto the low face's layout; its seams and the jaw's step a little bolder for the magnifier's size;
    and the high model's open eye (white, the big black pupil with its glint, the dark rim) painted where the eye patch
    sits (EYE_C, EYE_R), a touch larger so it reads; the cast's low faces carry their features painted the same way."""
    P = ctx.P
    dv = (P - G.HC) / np.linalg.norm(P - G.HC, axis=-1, keepdims=True)
    th = np.arctan2(dv @ G.XA, dv @ G.FW); ph = np.arcsin(np.clip(dv @ G.UP, -1, 1))
    lats = [x * G.D2R for x in G.HEAD_LATS] + [G.PHI_B, G.PHI_B + 11 * G.D2R]
    top, bot = lats[-1], lats[0]
    hf = os.path.join(OUT_DIR, 'face.png') if OUT_DIR else None
    if hf and os.path.exists(hf):                                  # the high face's own texel at this point
        c = sample(np.asarray(Image.open(hf).convert('RGB'), float) / 255, np.abs(th) / (math.pi / 2), (top - ph) / (top - bot))
    else:
        c = shade(ctx, face_wood(P), 0.65)
    d, dl = face_details(P)
    c = carve(c, d, width=0.11, depth=0.35, dist_lit=dl)            # the seams bolder than the high face's (0.075)
    x, y = P[..., 0], P[..., 1]
    my = FACE_JAW[0][1]; jx = FACE_JAW[1][0]
    under = (np.abs(x) < jx) & (y < my) & (P[..., 2] > 0.6)
    c = np.where(under[..., None], c * (1 - 0.15 * (1 - sstep(0.0, 0.25, my - y)))[..., None], c)
    # the eye: where the texel sits on the skull (theta out from the nose, phi up), against the eye patch's ellipse
    k = 1.12                                                          # a touch larger than the high patch
    ex = (th - G.EYE_C[0]) / (G.EYE_R[0] * k); ey = (ph - G.EYE_C[1]) / (G.EYE_R[1] * k)
    r = np.hypot(ex, ey)
    WHITE, SH, LINE, PUP = C(250, 250, 246), C(206, 206, 214), C(58, 32, 18), C(14, 10, 10)
    eye = WHITE + 0 * c
    eye = mix(eye, SH, np.clip(sstep(0.0, 0.3, ey) * 0.5 + sstep(0.7, 0.95, r) * 0.3, 0, 1))
    px, py, pr = 0.04, 0.06, 0.42                                     # the pupil a little inward of the high one's
    dp = np.hypot(ex + px, (ey - py) * 0.92)
    eye = mix(eye, PUP, 1 - sstep(pr - 0.04, pr + 0.02, dp))
    hl = np.hypot(ex + px + pr * 0.35, ey - py - pr * 0.42)
    eye = mix(eye, C(235, 235, 240), (1 - sstep(0.06, 0.1, hl)) * 0.85)
    eye = mix(eye, LINE, sstep(0.86, 0.92, r))
    inside = (r < 1.0) & (P[..., 2] > 0.5)
    c = np.where(inside[..., None], eye, c)
    c = c * (1 - 0.18 * (1 - sstep(1.0, 1.3, r)) * (r >= 1.0))[..., None]     # the socket's soft shadow round it
    # the nose's shadow on the face under the wedge (the wedge itself is the high model's nose mesh)
    ny = G.HC[1] + G.HEAD_K * (11.88 - G.HC0[1])
    nz = np.hypot(x / 0.34, (y - ny) / 0.16)
    c = c * (1 - 0.12 * (1 - sstep(0.4, 1.15, nz)) * (P[..., 2] > 1.5))[..., None]
    return c

def paint_forms(ctx):
    """The weapon forms' atlas (geno_forms.py): wood staves and tubes, steel, brass, the starry bore, the gold star."""
    u, v, P = ctx.u, ctx.v, ctx.P
    out = np.zeros(P.shape)
    # wood: grain along each part's own axis (the forearm's X), stave seams on the cannon
    wd = wood(P, (-9.0, 9.0, -2.0), (1.0, 0.0, 0.0), freq=2.4, seed=191, warp=0.16, warp_along=0.3, contrast=0.55)
    is_cannon = np.isin(ctx.mid, [i for i, n in enumerate(ctx.names) if n.startswith('cannon')])
    seam = np.abs(((u * 4) + 0.5) % 1.0 - 0.5) / 4                      # 8 staves (u mirrored over half a turn)
    wd = np.where(is_cannon[..., None], wd * (1 - 0.45 * (1 - sstep(0.004, 0.012, seam)))[..., None], wd)
    rim = sstep(0.41, 0.45, v) * (v < 0.5)                                # the tubes' end-grain rim, lighter
    wd = mix(wd, wd * 1.12, rim)
    out = np.where((v < 0.5)[..., None], wd, out)
    # steel: a cool grey tube with a long highlight and a darker underside
    STEEL_L, STEEL_M, STEEL_D = C(196, 204, 214), C(132, 140, 152), C(70, 74, 84)
    hl = np.exp(-((u - 0.3) / 0.12) ** 2)
    st = mix(STEEL_M, STEEL_D, sstep(0.55, 1.0, u)); st = mix(st, STEEL_L, 0.8 * hl)
    st = st * (1 + 0.04 * fbm(P * np.array([0.3, 3, 3]), 6.0, 2, 193)[..., None])
    reg = (v >= 0.5) & (v < 0.75)
    out = np.where((reg & (u < 0.5))[..., None], st, out)
    # brass: warm bands
    BR_L, BR_M, BR_D = C(250, 222, 140), C(204, 156, 62), C(120, 82, 28)
    uu = (u - 0.5) * 2
    br = mix(BR_M, BR_D, sstep(0.5, 1.0, uu)); br = mix(br, BR_L, 0.75 * np.exp(-((uu - 0.25) / 0.14) ** 2))
    out = np.where((reg & (u >= 0.5))[..., None], br, out)
    # the bore: near black, a few stars
    bore = np.zeros(P.shape) + C(18, 16, 26)
    rng = np.random.default_rng(7)
    for _ in range(9):
        cx, cy, r = rng.uniform(0.05, 0.45), rng.uniform(0.78, 0.97), rng.uniform(0.006, 0.014)
        d = np.hypot(u - cx, v - cy)
        bore = mix(bore, C(250, 246, 220), 1 - sstep(r * 0.4, r, d))
    out = np.where(((v >= 0.75) & (u < 0.5))[..., None], bore, out)
    # gold: the star, a bright rim to a warm core
    GD_L, GD_M = C(255, 232, 110), C(236, 176, 32)
    gd = mix(GD_L, GD_M, sstep(0.0, 0.1, np.hypot(u - 0.75, v - 0.875)))
    out = np.where(((v >= 0.75) & (u >= 0.5))[..., None], gd, out)
    return shade(ctx, out, 0.3, top=0.0)


# ---- Geno Flash's cannon (geno_cannon.py): SMRPG's blue-and-gold cannon on its carriage, in his materials: the barrel's
# blue is his capelet's (lacquered over wooden staves; costumes.py recolours it with the capelet), the brass is the weapon
# forms', the carriage his wood with brass and iron fittings
BRASS_L, BRASS_M, BRASS_D = C(252, 226, 140), C(214, 162, 58), C(122, 80, 24)
IRON_L, IRON_M, IRON_D = C(120, 118, 124), C(66, 64, 72), C(30, 28, 34)


def brass(ctx, t, shine=0.0):
    """Polished brass: t in 0..1 across a band (a rounded hoop: light in the middle, dark at the edges); shine adds a
    warm highlight."""
    c = mix(BRASS_D, BRASS_M, sstep(0.0, 0.45, np.sin(np.clip(t, 0, 1) * math.pi)))
    c = mix(c, BRASS_L, np.clip(shine, 0, 1) * 0.8)
    n = fbm(ctx.P, 3.0, 2, 401)
    return c * (1 + 0.06 * n[..., None])


def stud(c, d, r, metal_l, metal_d):
    """A round stud of radius r at distance d: a dark ring, a lit dome, a highlight up and to the left."""
    rim = (1 - sstep(r * 0.85, r * 1.05, d)) * sstep(r * 0.6, r * 0.85, d)
    dome = 1 - sstep(r * 0.55, r * 0.85, d)
    c = mix(c, metal_d, rim * 0.9)
    c = mix(c, mix(metal_d, metal_l, 0.75), dome)
    return c


def paint_fcbarrel(ctx):
    import geno_cannon as GC
    K = GC.K
    P = ctx.P
    x = P[..., 2] / K                                         # along the bore (base units), from the trunnions
    dy, dx = P[..., 1] - GC.TRUNNION[1], np.abs(P[..., 0])
    r = np.hypot(dx, dy) / K / GC.BARREL_R                    # the profile's own radius
    th = np.arctan2(dx, dy)                                   # 0 on top, pi underneath (mirrored)
    B = GC.BARREL_PARTS
    inb = lambda k: (x >= B[k][0]) & (x < B[k][1])
    # the blue lengths: his capelet's blue, lacquered over eight staves, a soft light along the top
    grain = fbm(P * np.array([4.0, 4.0, 0.5]), 1.0, 3, 411)
    blue = mix(BLUE_M, BLUE_L, np.clip(0.25 + 0.5 * np.cos(th) + 0.8 * grain, 0, 1) * 0.55)
    blue = mix(blue, BLUE_D, np.clip(-0.3 * np.cos(th) + 0.1, 0, 0.5))
    seam = np.abs(((th / (math.pi / 4)) + 0.5) % 1.0 - 0.5)           # 8 staves round the bore
    blue = blue * (1 - 0.3 * (1 - sstep(0.02, 0.06, seam)))[..., None]
    out = blue.copy()
    # the brass: the hoops, the base ring, the cascabel (ribbed), the muzzle
    def band(k):
        a, b = B[k]
        return (x - a) / (b - a)
    for k in ('hoop1', 'hoop2', 'base_ring'):
        t = band(k)
        out = np.where(inb(k)[..., None], brass(ctx, t, 0.6 * np.exp(-((t - 0.45) / 0.18) ** 2) * (np.cos(th) > 0.2)), out)
    # the hem: the first length's blue ends in the capelet's points over the base ring
    hem = B['blue1'][0] - 0.28 * (1 - np.abs(((th / (math.pi / 4)) % 1.0) * 2 - 1))
    blue_pts = (x >= hem) & (x < B['blue1'][0] + 0.02) & (r > 1.5)
    out = np.where(blue_pts[..., None], blue * 0.92, out)
    edge = np.abs(x - hem) < 0.035
    out = np.where((edge & (x < B['blue1'][0] + 0.02) & (r > 1.5))[..., None], out * 0.55, out)
    # the cascabel: a brass dome ribbed with four grooves, and the wooden knob
    t = band('cascabel')
    casc = brass(ctx, 0.5 + 0.5 * np.cos(th) * 0.6, 0.5 * sstep(0.3, 1.0, np.cos(th)))
    for g in (-3.28, -3.02, -2.76):
        casc = casc * (1 - 0.45 * (1 - sstep(0.02, 0.06, np.abs(x - g))))[..., None]
    out = np.where(inb('cascabel')[..., None], casc, out)
    knob = wood(P, (0.0, GC.TRUNNION[1], -4.4 * K), (0.0, 0.0, 1.0), freq=2.2, seed=421, dark=True, contrast=0.6)
    knob = mix(knob, C(96, 40, 26), 0.45)                    # SMRPG's red-brown back: lacquered dark wood, end grain
    out = np.where(inb('knob')[..., None], knob, out)
    # the chase: blue with a ring of ten steel studs (SMRPG's grey studs by the muzzle)
    tc = band('chase')
    studs_at = 0.55
    ang = (th / (math.pi / 5)) % 1.0 - 0.5                     # 10 round the bore
    d = np.hypot((x - (B['chase'][0] + studs_at * (B['chase'][1] - B['chase'][0]))) / 1.0, ang * (math.pi / 5) * 1.25)
    chase = stud(blue, d, 0.16, C(226, 228, 236), C(70, 72, 84))
    out = np.where(inb('chase')[..., None], chase, out)
    # the muzzle: a flared brass bell, its lip bright; the face; the bore dark
    tm = band('muzzle')
    mz = brass(ctx, 0.5 + 0.45 * np.cos(th), 0.7 * sstep(0.55, 0.9, tm) * sstep(-0.2, 0.6, np.cos(th)))
    out = np.where(inb('muzzle')[..., None], mz, out)
    bore = (x > 4.85) & (r < 1.0)
    depth = np.clip((5.64 - x) / 0.75, 0, 1)
    out = np.where(bore[..., None], mix(C(58, 40, 30), C(14, 12, 18), depth), out)
    # the trunnions (their own strip): brass pins, a bright end
    tv = ctx.v >= GC.UV_TRUNNIONS[1] - 0.005
    tt = (ctx.v - GC.UV_TRUNNIONS[1]) / (GC.UV_TRUNNIONS[3] - GC.UV_TRUNNIONS[1])
    out = np.where(tv[..., None], brass(ctx, 0.3 + 0.5 * tt, 0.5 * sstep(0.6, 1.0, tt)), out)
    return shade(ctx, out, 0.45, top=0.0)


def paint_fccarriage(ctx):
    import geno_cannon as GC
    K = GC.K
    u, v, P = ctx.u, ctx.v, ctx.P
    out = np.zeros(P.shape)
    inr = lambda R: (u >= R[0]) & (u < R[2]) & (v >= R[1]) & (v < R[3])
    # the wheels' sides: iron hub, brass ring with six bolts, turned wood in six planks, a brass tyre face with rivets
    u0, v0, u1, v1 = GC.UV_WHEEL
    su = ((u - u0) / (u1 - u0) - 0.02) / 0.96
    sv = ((v0 + v1) / 2 - v) / ((v1 - v0) / 2) / 0.96
    rr = np.hypot(su, sv) * GC.WHEEL_PROFILE[7][1]            # radius in base units (the tyre's edge is the rim)
    ang = np.arctan2(su, sv)                                  # 0 up, pi down (mirrored)
    wd = wood(np.stack([np.cos(ang) * rr, np.sin(ang) * rr, np.zeros_like(rr)], -1) * K, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0),
              freq=2.2, seed=431, contrast=0.7)
    plank = np.abs(((ang / (math.pi / 3)) + 0.5) % 1.0 - 0.5) * rr
    wd = wd * (1 - 0.35 * (1 - sstep(0.03, 0.07, plank)) * (rr > 0.7))[..., None]
    wh = wd
    ring = (rr > 0.40) & (rr < 0.70)
    wh = np.where(ring[..., None], brass(ctx, (rr - 0.40) / 0.30, 0.4 * (np.cos(ang) > 0.3)), wh)
    bang = (ang / (math.pi / 3)) % 1.0 - 0.5
    wh = np.where(ring[..., None], stud(wh, np.hypot(rr - 0.55, bang * (math.pi / 3) * 0.55), 0.07, BRASS_L, BRASS_D), wh)
    hub = rr <= 0.40
    wh = np.where(hub[..., None], mix(IRON_M, IRON_L, sstep(0.3, 0.0, rr) * 0.6 * (np.cos(ang) > 0)), wh)
    tyre = rr >= 1.84
    ttyre = (rr - 1.84) / (2.30 - 1.84)
    tb = brass(ctx, ttyre, 0.6 * np.exp(-((ttyre - 0.35) / 0.2) ** 2) * sstep(-0.3, 0.7, np.cos(ang)))
    rang = (ang / (math.pi / 8)) % 1.0 - 0.5
    tb = stud(tb, np.hypot(rr - 2.07, rang * (math.pi / 8) * 2.07), 0.07, BRASS_L, BRASS_D)
    wh = np.where(tyre[..., None], tb, wh)
    wh = wh * (1 - 0.4 * (1 - sstep(0.015, 0.05, np.abs(rr - 1.84))))[..., None]      # the tyre's seam
    out = np.where((u < u1)[..., None], wh, out)
    # the tread: a brass band, darker at its edges, a row of rivets
    R = GC.UV_TREAD
    tt = (v - R[1]) / (R[3] - R[1])
    tr = brass(ctx, tt, 0.25)
    rv = (((u - R[0]) / (R[2] - R[0])) * 8) % 1.0 - 0.5
    tr = stud(tr, np.hypot(rv * 0.9, (tt - 0.5) * 0.4), 0.06, BRASS_L, BRASS_D)
    out = np.where(inr(R)[..., None], tr, out)
    # the cheeks: dark wood along their length, iron bolts
    R = GC.UV_CHEEK
    zs = [p[0] for p in GC.CHEEK]; ys = [p[1] for p in GC.CHEEK]
    cz = min(zs) + (u - R[0]) / (R[2] - R[0]) * (max(zs) - min(zs))
    cy = max(ys) - (v - R[1]) / (R[3] - R[1]) * (max(ys) - min(ys))
    ck = wood(np.stack([np.zeros_like(cz), cy, cz], -1) * K, (0.0, -3.0, 0.0), (0.0, 0.0, 1.0), freq=2.6, seed=441,
              dark=True, contrast=0.8)
    for bz, by in ((1.05, 1.35), (-2.05, 1.35), (0.95, 2.95), (-0.9, 2.95), (-0.35, 1.9), (0.35, 1.9)):
        ck = stud(ck, np.hypot(cz - bz, cy - by), 0.11, IRON_L, IRON_D)
    out = np.where(inr(R)[..., None], ck, out)
    # the brass-bound edges (and the trail's shod end)
    R = GC.UV_EDGE
    out = np.where(inr(R)[..., None], brass(ctx, (v - R[1]) / (R[3] - R[1]), 0.3), out)
    # the bed and the trail: dark planks along the length, brass bands across them, rivets on the bands
    for R, along, n_b in ((GC.UV_BED_TOP, 'u', 3), (GC.UV_BED_FRONT, 'v', 0), (GC.UV_BED_BOT, 'u', 0),
                          (GC.UV_TRAIL_TOP, 'u', 1), (GC.UV_TRAIL_SIDE, 'u', 1)):
        a = (u - R[0]) / (R[2] - R[0]); b = (v - R[1]) / (R[3] - R[1])
        L, W = (a, b) if along == 'u' else (b, a)
        pl = wood(np.stack([W * 3.0, np.zeros_like(W), L * 6.0], -1) * K, (0.0, -4.0, 0.0), (0.0, 0.0, 1.0), freq=2.4,
                  seed=451, dark=True, contrast=0.8)
        seamw = np.abs(((W * 3.0) % 1.0) - 0.5)
        pl = pl * (1 - 0.3 * sstep(0.44, 0.5, seamw))[..., None]
        for k in range(n_b):
            c0 = (k + 0.5) / n_b
            bt = (L - (c0 - 0.06)) / 0.12
            on = (bt >= 0) & (bt <= 1)
            bb = brass(ctx, bt, 0.3)
            bb = stud(bb, np.hypot((L - c0) * 4.0, ((W * 3.0) % 1.0 - 0.5) * 0.7), 0.1, BRASS_L, BRASS_D)
            pl = np.where(on[..., None], bb, pl)
        out = np.where(inr(R)[..., None], pl, out)
    # the axle: iron
    R = GC.UV_AXLE
    ta = (u - R[0]) / (R[2] - R[0])
    out = np.where(inr(R)[..., None], mix(IRON_D, IRON_L, 0.3 + 0.4 * np.sin(ta * math.pi)), out)
    return shade(ctx, out, 0.5, top=0.0)


PAINTERS = {
    'face': paint_face, 'nose': paint_nose, 'headback': paint_headback, 'ears': paint_ears, 'band': paint_band, 'crown': paint_crown,
    'emblem': paint_emblem, 'curls': paint_curls, 'collar': paint_collar, 'collarin': paint_collarin, 'cape': paint_cape, 'lining': paint_lining,
    'clasp': paint_clasp, 'chest': paint_chest, 'pelvis': paint_pelvis, 'joint': paint_joint,
    'upperarm': limb_painter('LShoulderJ', 181), 'forearm': limb_painter('LArmJ', 183),
    'thigh': limb_painter('LLegJ', 185, 2.8), 'shin': limb_painter('LKneeJ', 187, 2.8),
    'palm': paint_palm, 'finger': paint_finger, 'forms': paint_forms, 'boot': paint_boot, 'cuff': paint_cuff, 'lowface': paint_lowface,
    'fcbarrel': paint_fcbarrel, 'fccarriage': paint_fccarriage,
}
CI8 = {'lowface'}                            # written CI8 (build_model.CI8_TEX): quantised to a palette here
HIGH_ONLY = {'fcbarrel', 'fccarriage',      # painted from the high model's surfaces only (the low cannon maps onto them,
             'headback', 'nose'}              # and the low head's back and nose, since the polish round, onto these)


# ---------------------------------------------------------------------------------------------------------------------
# eyes: one mirrored set of six 128x128 frames. u runs from the nose (0) outward (1); the patch is an ellipse filling
# the texture's inscribed circle (radius 0.48 about the centre).
# Mario's order (his move scripts address frames by number): 0 open, 1 half-lidded, 2 closed, 3 squint (pained), 4 and 5
# looking aside. Mario's two eyes swap 4 and 5 so both pupils turn the same way: frame 4 looks toward -X, 5 toward +X.
# The texture's u runs outward from the nose on both eyes (as Mario's), so -X is 'out' for the right eye (slot 0) and
# 'in' for the left (slot 1).
EYE_FRAMES = ['open', 'half', 'closed', 'squint', 'out', 'in']
EYE_ORDER = {'eyeR': ['open', 'half', 'closed', 'squint', 'out', 'in'], 'eyeL': ['open', 'half', 'closed', 'squint', 'in', 'out']}


def paint_eyes(ctx, out_dir):
    W, H = ctx.W, ctx.H                           # painted at UP x, box-filtered to the texture size per frame
    u, v = ctx.u, ctx.v
    x = (u - 0.5) / 0.48; y = (0.5 - v) / 0.48            # -1..1 across the patch, y up
    r = np.hypot(x, y)
    lid_wood = face_wood(ctx.P) * 0.97
    WHITE, SH, LINE, PUP = C(250, 250, 246), C(206, 206, 214), C(58, 32, 18), C(14, 10, 10)
    frames = []
    specs = {
        'open': dict(px=-0.04, py=0.06, pr=0.36, lid=None),
        'half': dict(px=-0.04, py=-0.06, pr=0.36, lid=-0.12),
        'closed': dict(px=0, py=0, pr=0, lid=-2.0),
        'squint': dict(px=0, py=0, pr=0, lid=-3.0),
        'in': dict(px=-0.4, py=0.04, pr=0.35, lid=None),
        'out': dict(px=0.4, py=0.04, pr=0.35, lid=None),
    }
    for k, name in enumerate(EYE_FRAMES):
        sp = specs[name]
        c = np.zeros((H, W, 3)) + WHITE
        c = mix(c, SH, np.clip(sstep(0.0, 0.3, y) * 0.5 + sstep(0.7, 0.95, r) * 0.3, 0, 1))  # shadow from the band above
        if sp['pr'] > 0:
            dp = np.hypot(x - sp['px'], (y - sp['py']) * 0.92)
            c = mix(c, PUP, 1 - sstep(sp['pr'] - 0.03, sp['pr'] + 0.02, dp))
            hl = np.hypot(x - sp['px'] + sp['pr'] * 0.35, y - sp['py'] - sp['pr'] * 0.42)
            c = mix(c, C(235, 235, 240), (1 - sstep(0.05, 0.08, hl)) * 0.85)
        if sp['lid'] is not None:
            if name == 'closed':
                lid = np.ones_like(r)
                lash = np.abs(y - (-0.3 - 0.16 * x * x))
                c = mix(c, lid_wood, 1.0)
                c = c * (1 - 0.75 * (1 - sstep(0.03, 0.08, lash)))[..., None]
            elif name == 'squint':
                # screwed shut: a tight crease bowed upward with little wrinkles fanning from the outer corner
                c = mix(c, lid_wood * 0.95, 1.0)
                crease = np.abs(y - (-0.2 + 0.22 * (1 - x * x)))
                c = c * (1 - 0.8 * (1 - sstep(0.035, 0.09, crease)))[..., None]
                for k, (ax, ay) in enumerate(((0.62, 0.18), (0.68, -0.05), (0.6, -0.28))):
                    wr = seg_dist(x, y, [(0.42, ay * 0.5), (ax + 0.25, ay)])
                    c = c * (1 - 0.45 * (1 - sstep(0.02, 0.05, wr)))[..., None]
            else:
                edge = sp['lid'] - 0.12 * x * x
                lid = sstep(edge - 0.02, edge + 0.02, y)
                c = mix(c, lid_wood, lid)
                lash = np.abs(y - edge)
                c = c * (1 - 0.7 * (1 - sstep(0.03, 0.08, lash)))[..., None]
        # the carved outline round the eye
        c = mix(c, LINE, sstep(0.89, 0.935, r))
        img = np.clip(c, 0, 1)
        img = downsample(fill_gutters(img, ctx.mask), ctx.W0, ctx.H0)
        # CI8: at most 256 colours per frame, chosen here (median cut, no dither) so the game's palette is exact
        q = Image.fromarray((img * 255 + 0.5).astype(np.uint8)).quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        img = np.asarray(q.convert('RGB'), float) / 255
        frames.append(img)
        Image.fromarray((img * 255 + 0.5).astype(np.uint8)).save(os.path.join(out_dir, f'eye_{name}.png'))
    return frames[0]


def main():
    global OUT_DIR
    out_dir = OUT_DIR = sys.argv[1]
    ao_dir = sys.argv[sys.argv.index('--ao') + 1] if '--ao' in sys.argv else None
    os.makedirs(out_dir, exist_ok=True)
    meshes = G.build_all() + GL.build()
    sizes = {}
    for tex, (W, H) in SIZES.items():
        if not any(m.tex == tex for m in meshes): continue
        ctx = Ctx(tex, [m for m in meshes if not (tex in HIGH_ONLY and m.name.startswith('low_'))], ao_dir)
        if tex in ('eyeR', 'eyeL'):
            if tex == 'eyeL': continue                  # both eyes share one image set (painted with eyeR)
            ctx = Ctx(tex, [m for m in meshes if m.tex in ('eyeR', 'eyeL')], ao_dir)
            img = paint_eyes(ctx, out_dir)
            sizes['eyeR'] = sizes['eyeL'] = (W, H)
            continue
        else:
            img = np.clip(PAINTERS[tex](ctx), 0, 1)
            img = downsample(fill_gutters(img, ctx.mask), W, H)
            if tex in CI8:          # at most 256 colours, chosen here (median cut, no dither), so the game's palette is exact
                q = Image.fromarray((img * 255 + 0.5).astype(np.uint8)).quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
                img = np.asarray(q.convert('RGB'), float) / 255
        Image.fromarray((img * 255 + 0.5).astype(np.uint8)).save(os.path.join(out_dir, f'{tex}.png'))
        sizes[tex] = (W, H)
        print(f'{tex:9s} {W}x{H}  coverage {ctx.mask.mean() * 100:4.0f}%')
    json.dump(sizes, open(os.path.join(out_dir, 'sizes.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
