"""The Forest Maze's production art, from code (no image-model output is used): procedural textures and low-poly geometry,
after style target t7 (twilight: umber trunks with pale bark, a purple path, glossy orange-red mushrooms, deep green
bushes; research in DESIGN.md "M2"). stage_spec.py calls build() unless STAGE_ART=greybox.
  - The play plane: the stump is exactly the collision outline extruded (FRONT to BACK): a cut-wood top ringed with moss
    at y = 0, bark sides following the collision below the ledges; the mushroom cap's top is flat at y = 28 and widest at
    x = +-27 on the fighters' plane (z = 0), its rim curling in and down, cream gills under it, a pale stem set back.
  - The background (fogged): trunks (umber, and pale-barked like the SMRPG screens' highlights), a forest floor far below
    the stage (y = -100, behind z = -80) with the purple path winding back, bushes, orange-red mushroom clusters, a dark
    canopy, and a twilight haze card at the back.
Textures are raw BGRA (datkit stage-build encodes them CMPR), with PNG previews, in $MELEE_WORK/stage/art.
"""
import math, os
import numpy as np
from PIL import Image

RNG = np.random.default_rng(7)


# ---------------------------------------------------------------- textures
def _noise(h, w, scale, rng):
    """Smooth value noise in 0..1."""
    gh, gw = max(2, h // scale + 2), max(2, w // scale + 2)
    g = rng.random((gh, gw))
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im).astype(float) / 255


def _tile(a):
    """Blend the image with its half-shifted copy near the seams so it tiles."""
    h, w = a.shape[:2]
    b = np.roll(np.roll(a, h // 2, 0), w // 2, 1)
    wy = np.abs(np.linspace(-1, 1, h))[:, None]; wx = np.abs(np.linspace(-1, 1, w))[None, :]
    m = np.clip(np.maximum(wy, wx) * 1.6 - 0.6, 0, 1)
    if a.ndim == 3: m = m[..., None]
    return a * (1 - m) + b * m


def _col(base, var, n):
    return np.clip(np.array(base, float)[None, None, :] + (n[..., None] - 0.5) * np.array(var, float), 0, 255)


def textures():
    rng = np.random.default_rng(11)
    T = {}
    # bark: vertical grooves, umber
    h, w = 256, 128
    grooves = _noise(h, w, 8, rng) * 0.4 + np.sin(np.linspace(0, 18 * math.pi, w))[None, :] * 0.25 + 0.35
    grooves = np.asarray(Image.fromarray((np.clip(grooves, 0, 1) * 255).astype(np.uint8)).resize((w, h))).astype(float) / 255
    streak = _noise(h, w, 4, rng)
    stretched = np.asarray(Image.fromarray((streak * 255).astype(np.uint8)).resize((w, 16)).resize((w, h), Image.BICUBIC)).astype(float) / 255
    n = np.clip(0.55 * grooves + 0.45 * stretched, 0, 1)
    n = np.clip((n - 0.5) * 1.6 + 0.5, 0, 1)                      # deeper grooves
    T['bark'] = _tile(_col((80, 56, 40), (110, 84, 60), n))
    # pale bark: the SMRPG trunks' pale highlights (birch-like marks)
    n2 = _noise(h, w, 16, rng)
    pale = _col((150, 140, 132), (30, 30, 30), n2)
    marks = _noise(h, w, 6, rng) > 0.72
    pale[marks] = pale[marks] * 0.7
    T['bark_pale'] = _tile(pale)
    # the stump's cut top: tan rings around (0.5, 0.42), moss at the border
    h, w = 128, 256
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w * 0.5) / (w * 0.5), (yy - h * 0.42) / (h * 0.6))
    ring = 0.5 + 0.5 * np.sin(r * 38 + _noise(h, w, 16, rng) * 4)
    top = _col((178, 140, 96), (50, 40, 30), ring * 0.6 + _noise(h, w, 4, rng) * 0.4)
    border = np.clip(np.maximum(np.abs(xx / w - 0.5) * 2, np.abs(yy / h - 0.5) * 2), 0, 1)
    moss = np.clip((border - 0.84) / 0.08 + (_noise(h, w, 6, rng) - 0.5) * 0.9, 0, 1)[..., None]
    T['stump_top'] = top * (1 - moss) + _col((66, 106, 50), (40, 50, 30), _noise(h, w, 3, rng)) * moss
    # moss (the front lip)
    T['moss'] = _tile(_col((62, 102, 48), (46, 60, 34), _noise(64, 64, 4, rng)))
    # the cap: glossy orange-red, pale spots, a highlight toward the back
    h, w = 128, 256
    cap = _col((206, 76, 38), (30, 20, 16), _noise(h, w, 8, rng))
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(26):
        cx, cy, rr = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(6, 15)
        d = np.hypot((xx - cx) / 2.0, yy - cy) / rr
        m = np.clip(1.4 - d * 1.4, 0, 1)[..., None]
        cap = cap * (1 - m) + np.array([236, 214, 178])[None, None, :] * m
    gl = np.clip(1 - np.abs(yy / h - 0.3) * 4, 0, 1)[..., None] * 0.25
    T['cap'] = np.clip(cap + gl * 255, 0, 255)
    # gills: cream with fine stripes
    h, w = 64, 64
    stripes = 0.5 + 0.5 * np.sin(np.linspace(0, 16 * math.pi, w))[None, :].repeat(h, 0)
    T['gills'] = _tile(_col((222, 204, 168), (40, 34, 30), stripes * 0.7 + _noise(h, w, 4, rng) * 0.3))
    T['stem'] = _tile(_col((214, 200, 170), (26, 24, 20), _noise(64, 32, 4, rng)))
    # the forest floor, the path, leaves, canopy
    g = _noise(128, 128, 4, rng)
    litter = _noise(128, 128, 12, rng) > 0.6
    ground = _col((46, 56, 34), (30, 30, 20), g)
    ground[litter] = ground[litter] * 0.6 + np.array([70, 50, 34]) * 0.4
    T['ground'] = _tile(ground)
    p = _col((96, 72, 124), (34, 28, 40), _noise(64, 64, 3, rng))
    T['path'] = _tile(p)
    lv = _noise(64, 64, 3, rng)
    T['leaves'] = _tile(_col((42, 84, 44), (60, 70, 44), lv))
    cn = _noise(128, 128, 6, rng)
    T['canopy'] = _tile(_col((22, 38, 26), (26, 36, 24), cn))
    # the far haze: dark top, a purple-pink twilight glow, dark below
    h, w = 128, 32
    t = np.linspace(0, 1, h)[:, None]
    glow = np.exp(-((t - 0.62) / 0.18) ** 2)
    haze = np.array([22, 18, 30])[None, None, :] + glow[..., None] * np.array([58, 40, 62])[None, None, :]
    T['haze'] = np.repeat(haze, w, 1)
    return {k: np.clip(v, 0, 255).astype(np.uint8) for k, v in T.items()}


MATS = {  # material: texture, tint (diffuse; ambient half unless given)
    'bark': dict(color=[255, 255, 255]), 'bark_pale': dict(color=[150, 140, 165], ambient=[60, 52, 72]), 'stump_top': dict(color=[255, 250, 240]),
    'moss': dict(color=[255, 255, 255]), 'cap': dict(color=[255, 255, 255]), 'gills': dict(color=[255, 255, 255]),
    'stem': dict(color=[170, 160, 150]), 'ground': dict(color=[200, 190, 210]), 'path': dict(color=[230, 220, 240]),
    'leaves': dict(color=[230, 240, 230]), 'canopy': dict(color=[200, 200, 210]), 'haze': dict(color=[255, 255, 255], ambient=[255, 255, 255]),
}


# ---------------------------------------------------------------- geometry
def _n(a, b, c):
    u = np.subtract(b, a); v = np.subtract(c, a); n = np.cross(u, v); l = np.linalg.norm(n) or 1
    return list(map(float, n / l))


def quad(p, uv, mat, normals=None):
    p = [list(map(float, q)) for q in p]
    f = dict(tris=[[p[0], p[1], p[2]], [p[0], p[2], p[3]]], uv=[[uv[0], uv[1], uv[2]], [uv[0], uv[2], uv[3]]],
             normal=_n(p[0], p[1], p[2]), material=mat)
    if normals: f['normals'] = [[normals[0], normals[1], normals[2]], [normals[0], normals[2], normals[3]]]
    return f


def tri(p, uv, mat):
    p = [list(map(float, q)) for q in p]
    return dict(tris=[p], uv=[uv], normal=_n(*p), material=mat)


def cylinder(cx, cz, r0, r1, y0, y1, sides, mat, utile=1.0, vtile=64.0, twist=0.0):
    out = []
    for k in range(sides):
        a0, a1 = 2 * math.pi * k / sides, 2 * math.pi * (k + 1) / sides
        p = lambda a, r, y: (cx + r * math.cos(a + twist * (y - y0) / 100), y, cz + r * math.sin(a + twist * (y - y0) / 100))
        nn = lambda a: [math.cos(a), 0.0, math.sin(a)]
        u0, u1 = k / sides * utile, (k + 1) / sides * utile
        v0, v1 = y0 / vtile, y1 / vtile
        out.append(quad([p(a0, r0, y0), p(a0, r1, y1), p(a1, r1, y1), p(a1, r0, y0)],
                        [[u0, v0], [u0, v1], [u1, v1], [u1, v0]], mat, [nn(a0), nn(a0), nn(a1), nn(a1)]))
    return out


def dome(cx, cy, cz, rx, ry, rz, mat, sides=10, rings=3):
    """A half-ellipsoid (a small mushroom cap or a bush), smooth normals."""
    out = []
    for i in range(rings):
        t0, t1 = (math.pi / 2) * i / rings, (math.pi / 2) * (i + 1) / rings
        for k in range(sides):
            a0, a1 = 2 * math.pi * k / sides, 2 * math.pi * (k + 1) / sides
            P = lambda t, a: (cx + rx * math.cos(t) * math.cos(a), cy + ry * math.sin(t), cz + rz * math.cos(t) * math.sin(a))
            N = lambda t, a: list(np.array([math.cos(t) * math.cos(a) / rx, math.sin(t) / ry, math.cos(t) * math.sin(a) / rz]) /
                                  np.linalg.norm([math.cos(t) * math.cos(a) / rx, math.sin(t) / ry, math.cos(t) * math.sin(a) / rz]))
            uv = [[k / sides, i / rings], [k / sides, (i + 1) / rings], [(k + 1) / sides, (i + 1) / rings], [(k + 1) / sides, i / rings]]
            out.append(quad([P(t0, a0), P(t1, a0), P(t1, a1), P(t0, a1)], uv, mat, [N(t0, a0), N(t1, a0), N(t1, a1), N(t0, a1)]))
    return out


def mushroom(x, y, z, s, rng):
    return cylinder(x, z, 0.25 * s, 0.2 * s, y, y + 0.9 * s, 4, 'stem') + dome(x, y + 0.85 * s, z, 0.65 * s, 0.5 * s, 0.65 * s, 'cap', 6, 2)


def build(c, BODY, FRONT, BACK, CAP_T, ring):
    """-> (stage faces, background faces, materials, textures)."""
    rng = np.random.default_rng(5)
    L = BODY['ledge_x']
    stage = []
    # the stump: the collision outline extruded, bark on the sides and the front, the cut top at y = 0
    n = len(ring)
    per = 0.0
    for k in range(n):
        (ax, ay), (bx, by) = ring[k], ring[(k + 1) % n]
        ln = math.hypot(bx - ax, by - ay)
        if abs(ay) < 1e-6 and abs(by) < 1e-6:                    # the top: one cut-wood face across the whole top
            per += ln; continue
        u0, u1 = per / 40, (per + ln) / 40; per += ln
        stage.append(quad([(ax, ay, FRONT), (bx, by, FRONT), (bx, by, BACK), (ax, ay, BACK)],
                          [[u0, FRONT / 40], [u1, FRONT / 40], [u1, BACK / 40], [u0, BACK / 40]], 'bark'))
    stage.append(quad([(-L, 0, BACK), (-L, 0, FRONT), (L, 0, FRONT), (L, 0, BACK)], [[0, 0], [0, 1], [1, 1], [1, 0]], 'stump_top'))
    cx, cy = sum(p[0] for p in ring) / n, sum(p[1] for p in ring) / n
    for k in range(n):                                            # the front face: bark, planar
        a, b = ring[k], ring[(k + 1) % n]
        pts = [(cx, cy, FRONT), (b[0], b[1], FRONT), (a[0], a[1], FRONT)]
        stage.append(tri(pts, [[p[0] / 44, p[1] / 44] for p in pts], 'bark'))
    # the moss lip under the front edge (on the front face, just in front of it)
    stage.append(quad([(-L, 0, FRONT + 0.05), (L, 0, FRONT + 0.05), (L, -2.6, FRONT + 0.05), (-L, -2.6, FRONT + 0.05)],
                      [[0, 0], [8, 0], [8, 0.4], [0, 0.4]], 'moss'))
    # the cap: flat top at y (an ellipse widest at x = +-x1 on z = 0), the rim curling in, gills, the stem set back
    for p in c['platforms']:
        rx, rz, y = (p['x1'] - p['x0']) / 2, 13.0, p['y']
        mx = (p['x0'] + p['x1']) / 2
        seg = 20
        E = lambda s, t, yy: (mx + s * math.cos(t), yy, t_z(t, s))
        def t_z(t, s): return (s / rx) * rz * math.sin(t)
        top_uv = lambda X, Z: [(X - mx + rx) / (2 * rx), (Z + rz) / (2 * rz)]
        rings = [(rx, y), (rx - 0.9, y - 1.3), (rx - 2.4, y - 2.6), (rx - 4.5, y - CAP_T)]
        for k in range(seg):
            t0, t1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
            a0, a1 = E(rx, t0, y), E(rx, t1, y)
            stage.append(tri([(mx, y, 0.0), a1, a0], [top_uv(mx, 0), top_uv(a1[0], a1[2]), top_uv(a0[0], a0[2])], 'cap'))
            for (r0, y0), (r1, y1) in zip(rings, rings[1:]):      # the rim, curling in and down
                q = [E(r0, t0, y0), E(r0, t1, y0), E(r1, t1, y1), E(r1, t0, y1)]
                nrm = [[math.cos(t), 0.5, math.sin(t)] for t in (t0, t1, t1, t0)]
                stage.append(quad(q, [top_uv(v[0], v[2]) for v in q], 'cap', nrm))
            # the gills: from the rim's underside to the stem
            rl, yl = rings[-1]
            g0, g1 = E(rl, t0, yl), E(rl, t1, yl)
            stage.append(tri([g0, g1, (mx, y - CAP_T - 1.5, -9.0)], [[k / seg * 4, 0], [(k + 1) / seg * 4, 0], [k / seg * 4 + 0.1, 1]], 'gills'))
        stage += cylinder(mx, -9.0, 1.9, 1.5, 0.0, y - CAP_T - 1.0, 10, 'stem', 1.0, 24.0)
    # ---------------------------------------------------------------- background
    back = []
    if os.environ.get('FOREST_BACK', '1') == '0':                # the play plane alone (edge_lab's clean silhouette)
        return stage, back
    floor_y = -100.0
    back.append(quad([(-700, floor_y, -80), (700, floor_y, -80), (700, floor_y, -520), (-700, floor_y, -520)],
                     [[0, 0], [14, 0], [14, 9], [0, 9]], 'ground'))
    # the purple path, winding back
    pts = [(-30 + 55 * math.sin(i * 0.55), floor_y + 0.4, -90 - i * 34) for i in range(13)]
    for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:]):
        w0, w1 = 16, 16
        back.append(quad([(x0 - w0, y0, z0), (x0 + w0, y0, z0), (x1 + w1, y1, z1), (x1 - w1, y1, z1)],
                         [[0, z0 / 32], [1, z0 / 32], [1, z1 / 32], [0, z1 / 32]], 'path'))
    # trunks: a near rank flanking the stage, then deeper ones; every third pale-barked
    trunks = [(-185, -110, 22), (190, -120, 24), (-120, -190, 16), (130, -200, 17), (-260, -210, 26), (270, -230, 28),
              (-40, -300, 20), (165, -340, 18), (-190, -350, 22), (200, -380, 24), (-330, -300, 30), (350, -320, 30)]
    for i, (x, z, r) in enumerate(trunks):
        back += cylinder(x, z, r * 1.25, r, floor_y, 360, 10, 'bark_pale' if i % 3 == 1 else 'bark', 2.0, 96.0, 0.25)
        back += cylinder(x, z, r * 1.9, r * 1.25, floor_y - 1, floor_y + 14, 10, 'bark', 2.0, 30.0)   # root flare
    # bushes and mushroom clusters on the floor (FOREST_DECOR=0 leaves them out: the performance A/B)
    decor = os.environ.get('FOREST_DECOR', '1') != '0'
    for i in range(9 if decor else 0):
        x, z = rng.uniform(-420, 420), rng.uniform(-420, -110)
        r = rng.uniform(14, 24)
        back += dome(x, floor_y, z, r * 1.3, r, r, 'leaves', 6, 2)
    for i in range(7 if decor else 0):
        x, z = rng.uniform(-320, 320), rng.uniform(-330, -100)
        for j in range(2):
            back += mushroom(x + rng.uniform(-8, 8), floor_y, z + rng.uniform(-6, 6), rng.uniform(6, 11), rng)
    # the canopy and the haze
    for i in range(3 if decor else 0):
        x0 = -360 + i * 240
        back.append(quad([(x0, 250, -120), (x0 + 260, 250, -120), (x0 + 260, 300, -480), (x0, 300, -480)],
                         [[0, 0], [3, 0], [3, 4], [0, 4]], 'canopy'))
    back.append(quad([(-900, -240, -540), (900, -240, -540), (900, 420, -540), (-900, 420, -540)],
                     [[0, 1], [1, 1], [1, 0], [0, 0]], 'haze'))
    return stage, back


def write_textures(out):
    os.makedirs(out, exist_ok=True)
    mats = {}
    for name, a in textures().items():
        h, w = a.shape[:2]
        rgba = np.concatenate([a, np.full((h, w, 1), 255, np.uint8)], 2)
        open(os.path.join(out, name + '.bgra'), 'wb').write(rgba[..., [2, 1, 0, 3]].tobytes())
        Image.fromarray(a).save(os.path.join(out, name + '.png'))
        mats[name] = dict(MATS[name], texture=f'art/{name}.bgra', size=[w, h], format='CMP',
                          **({'wrap': 'clamp'} if name == 'haze' else {}))
    return mats
