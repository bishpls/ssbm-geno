"""The Forest Maze's production model (t7), built headless in Blender and exported as stage-build faces.
    blender -b --python projects/geno/stage/blender/forest_scene.py -- --out MESH.json [--blend OUT.blend] [--cap float|stem]
                                                                       [--play-only]
Everything is in Melee's units and axes (x right, y up, z toward the camera; the fighters' plane is z = 0), stored as
is in the .blend. Melee's stages draw an unlit baked vertex colour times a texture (VERTEX, TEX0), so this script bakes
the light into vertex colours with Blender's BVH: ambient occlusion (hemisphere rays), a warm key light with shadow
rays, a cool sky fill and a peach rim from the twilight glow behind. forest_tex.py paints the textures.

The rules the play plane keeps (stage_spec.py's collision is unchanged):
  - the stump's top is flat at y = 0 and reaches x = +-70 exactly on z = 0 (the ledge corners); its mossy lip only
    overhangs where it is away from the corners, and never rises above the top;
  - in front of the fighters' plane (z >= 0) the stump stays inside the collision's hull (the ledge wall to y = -6,
    then the taper to the bottom at y = -40), so it never hides a recovering fighter; behind the plane it widens into
    the flared base and roots, drawn behind the fighters;
  - the cap's top is flat at y = 28 along z = 0 from x = -27 to 27 (the collision), domed only front to back, with
    rounded ends past 27;
  - the forest floor lies only behind the stage (its front edge a cliff at z = -24 near the stump), 60 below the top.
"""
import json, math, os, random, sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
OUT = opt('--out', '/tmp/forest_mesh.json')
BLEND = opt('--blend')
CAP = opt('--cap', 'float')
PLAY_ONLY = '--play-only' in argv
STAR_ROAD = os.environ.get('STAR_ROAD', '1') != '0'           # the shooting star (Michael: on)
TIME_SCALE = float(os.environ.get('SKY_TIME_SCALE', '1'))      # > 1 compresses every clock (the full-cycle measure only)
JOINTS = {}                                                     # group -> [{name, t}]
ANIMS = {}                                                      # group -> {"joints": {...}, "materials": [...]}

GROUND = -60.0
HULL = [(70.0, 0.0), (70.0, -6.0), (56.0, -22.0), (40.0, -34.0), (18.0, -40.0)]
BF, BB = 22.0, 34.0            # the stump top's depth in front of and behind the fighters' plane
CAP_Y, CAP_HALF = 28.0, 27.0
R = random.Random(5)


def hull_x(y):
    """The collision's half-width at height y (0 at the top, -40 at the bottom)."""
    if y >= HULL[1][1]:
        return 70.0
    for (x0, y0), (x1, y1) in zip(HULL[1:], HULL[2:]):
        if y1 <= y <= y0:
            return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
    return HULL[-1][0]


def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


class Mesh:
    """Vertices, faces (index lists), per-corner uvs; a material, a model group, a tint and how to light it."""
    def __init__(self, name, mat, group='back', tint=(1, 1, 1), lit=True, occluder=True, orient=None, joint=None):
        self.name, self.mat, self.group, self.tint, self.lit, self.occluder = name, mat, group, tint, lit, occluder
        self.joint = joint              # a child joint of the group's mesh joint (moving parts), or None
        self.orient = orient            # p -> an outward direction (faces are flipped to agree)
        self.V, self.F, self.UV = [], [], []
        self.vtint = {}                 # vertex index -> extra tint (moss, height darkening)

    def v(self, p):
        self.V.append(Vector(p)); return len(self.V) - 1

    def f(self, idx, uv, mat=None):
        self.F.append(list(idx)); self.UV.append([tuple(q) for q in uv])
        self.FM = getattr(self, 'FM', []) + [mat or self.mat]


MESHES = []


def add(m):
    MESHES.append(m); return m


# ---------------------------------------------------------------------------------------------------------- the stump
N = 48                                                        # around; even, so theta = 0 and pi are vertices


def irr(th):
    s2 = math.sin(th) ** 2                                   # zero at the ledges (and flat there)
    return s2 * (0.045 * math.sin(5 * th + 0.7) + 0.03 * math.sin(9 * th + 2.1) + 0.02 * math.sin(13 * th + 0.4))


def outline(th):
    """The stump top's outline. At the ledges it has a small corner (x recedes 8 units per unit of |sin|): a smooth
    rounded end would project past x = +-70 from any camera in front, the part of the rim nearer the camera looking wider."""
    k = 1 + irr(th)
    return 70.0 * math.cos(th) * k - 8.0 * abs(math.sin(th)) * math.cos(th) ** 2 * (1 if math.cos(th) > 0 else -1), \
        (BF if math.sin(th) > 0 else BB) * math.sin(th) * k


def stump():
    ths = [2 * math.pi * i / N for i in range(N)]
    O = [outline(t) for t in ths]
    cx, cz = 0.0, -6.0                                       # the rings' centre (the pith)
    # the top: rings concentric with the outline; the outer 7% is the mossy lip's
    top = add(Mesh('stump_top', 'stump_top', 'stage', tint=(0.86, 0.86, 0.86), orient=lambda p: (0, 1, 0)))
    rhos = [0.0, 0.4, 0.75, 0.93]
    rows = []
    for rho in rhos:
        row = []
        for i, (x, z) in enumerate(O):
            if rho == 0.0 and i > 0:
                row.append(row[0]); continue
            row.append(top.v((cx + (x - cx) * rho, 0.0, cz + (z - cz) * rho)))
        rows.append(row)
    uvp = lambda rho, i: (0.5 + 0.5 * rho * math.cos(ths[i]), 0.5 + 0.5 * rho * math.sin(ths[i]))
    for k in range(len(rhos) - 1):
        for i in range(N):
            j = (i + 1) % N
            if k == 0:
                top.f([rows[0][0], rows[1][i], rows[1][j]], [uvp(0, i), uvp(rhos[1], i), uvp(rhos[1], j)])
            else:
                top.f([rows[k][i], rows[k + 1][i], rows[k + 1][j], rows[k][j]],
                      [uvp(rhos[k], i), uvp(rhos[k + 1], i), uvp(rhos[k + 1], j), uvp(rhos[k], j)])
    # the mossy lip: from 93% on the top, over the rim, rolling out and down; flush at the ledge corners
    lip = add(Mesh('moss_lip', 'moss', 'stage', tint=(0.92, 0.92, 0.92), orient=lambda p: (p.x, 0.4, p.z - cz)))
    prof = [(0.93, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, -1.2, 0.65), (1.0, -3.0, 1.0), (1.0, -4.9, 0.3)]
    drips = {i: R.uniform(1.5, 3.5) for i in range(N) if abs(math.sin(ths[i])) > 0.5 and R.random() < 0.16}
    lrows = []
    for k, (rho, dy, o) in enumerate(prof):
        row = []
        for i, (x, z) in enumerate(O):
            th = ths[i]
            ov = 2.8 * smoothstep(0.12, 0.45, abs(math.sin(th))) * o
            L = math.hypot(x - cx, z - cz) or 1.0
            px, pz = cx + (x - cx) * rho + (x - cx) / L * ov, cz + (z - cz) * rho + (z - cz) / L * ov
            if abs(math.sin(th)) < 0.12:
                px = max(-70.0, min(70.0, px))                # never past the ledge corner
            y = dy - (drips.get(i, 0.0) if k == len(prof) - 1 else 0.0)
            row.append(lip.v((px, y, pz)))
        lrows.append(row)
    for k in range(len(prof) - 1):
        for i in range(N):
            j = (i + 1) % N
            u0, u1 = i / N * 12, (i + 1) / N * 12
            lip.f([lrows[k][i], lrows[k + 1][i], lrows[k + 1][j], lrows[k][j]],
                  [(u0, k * 0.2), (u0, (k + 1) * 0.2), (u1, (k + 1) * 0.2), (u1, k * 0.2)])
    # the bark wall. Under the mossy lip the front undercuts back behind the fighters' plane by y = -18 (in front of the
    # plane it stays inside the hull); below, a round trunk behind the plane: a waist near the hull's width, then the flare
    # into the floor. Below the collision's bottom (y = -40) the flare is visual only, behind any fighter down there.
    wall = add(Mesh('stump_bark', 'bark', 'stage', orient=lambda p: (p.x, 0.0, p.z + 7.0)))
    ys = [-4.4, -8.0, -12.0, -18.0, -25.0, -32.0, -39.0, -46.0, -52.0, -57.0, -61.0, -65.0]
    WP = [(-6.0, 0.97), (-18.0, 0.86), (-30.0, 0.83), (-42.0, 0.88), (-50.0, 0.97), (-56.0, 1.08), (-61.0, 1.2), (-65.0, 1.26)]

    def width(y):
        for (y0, w0), (y1, w1) in zip(WP, WP[1:]):
            if y1 <= y <= y0:
                return 70.0 * (w0 + (w1 - w0) * (y - y0) / (y1 - y0))
        return 70.0 * WP[0][1] if y > WP[0][0] else 70.0 * WP[-1][1]

    wrows = []
    for y in ys:
        row = []
        hs = hull_x(y) / 70.0
        u = smoothstep(-18.0, -6.0, y)                       # 1: the top's outline (the ledge wall), 0: the trunk below
        W = width(y)
        depth = 30.0 * (1.0 + 0.3 * smoothstep(-48.0, -62.0, y))
        for i, (x, z) in enumerate(O):
            th = ths[i]
            s = math.sin(th)
            k = 1 + irr(th)
            xt = W * math.cos(th) * k
            zt = (-3.0 - (1.0 - s) * 4.0) if s > 0 else (-7.0 + depth * s * k)
            if y < -44.0 and s > 0:                           # the base's front leans back toward the cliff's lip
                zt -= 6.0 * smoothstep(-44.0, -65.0, y)
            px, pz = x * hs * u + xt * (1 - u), z * hs * u + zt * (1 - u)
            if pz >= 0.0:
                px = max(-hull_x(y), min(hull_x(y), px))      # in front of the plane: never outside the hull
            if s < -0.1:                                      # grooves in the silhouette, behind the plane
                bump = 1.0 + 0.02 * math.sin(11 * th + y * 0.05)
                px, pz = px * bump, -7.0 + (pz + 7.0) * bump
            row.append(wall.v((px, y, pz)))
        wrows.append(row)
    for k in range(len(ys) - 1):
        for i in range(N):
            j = (i + 1) % N
            u0, u1 = i / N * 6, (i + 1) / N * 6
            v0, v1 = -ys[k] / 44.0, -ys[k + 1] / 44.0
            wall.f([wrows[k][i], wrows[k + 1][i], wrows[k + 1][j], wrows[k][j]], [(u0, v0), (u0, v1), (u1, v1), (u1, v0)])
    for k, y in enumerate(ys):                                # moss creeping up from the base
        g = smoothstep(-50.0, -64.0, y)
        for i in range(N):
            wall.vtint[wrows[k][i]] = (1 - 0.35 * g, 1 - 0.05 * g, 1 - 0.45 * g)
    return O, ths


def tube(m, pts, radii, sides=7, useg=1.0):
    """A tapered tube along pts (a root); faces outward from the centreline."""
    rings = []
    for k, (p, r) in enumerate(zip(pts, radii)):
        p = Vector(p)
        d = (Vector(pts[min(k + 1, len(pts) - 1)]) - Vector(pts[max(k - 1, 0)])).normalized()
        a = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
        u = d.cross(a).normalized(); w = d.cross(u).normalized()
        rings.append([m.v(p + (u * math.cos(2 * math.pi * s / sides) + w * math.sin(2 * math.pi * s / sides)) * r) for s in range(sides)])
    for k in range(len(rings) - 1):
        for s in range(sides):
            t = (s + 1) % sides
            m.f([rings[k][s], rings[k + 1][s], rings[k + 1][t], rings[k][t]],
                [(s / sides * useg, k * 0.25), (s / sides * useg, (k + 1) * 0.25), ((s + 1) / sides * useg, (k + 1) * 0.25),
                 ((s + 1) / sides * useg, k * 0.25)])
    m.orient_c = getattr(m, 'orient_c', []) + list(pts)
    return rings


def bezier(a, b, c, n):
    return [tuple((1 - t) ** 2 * a[i] + 2 * (1 - t) * t * b[i] + t * t * c[i] for i in range(3)) for t in [k / (n - 1) for k in range(n)]]


def roots(O, ths):
    """Seven buttress roots: broad where they leave the trunk low behind the plane, flattened, running out and down into
    the floor (five) or over the cliff's lip (the two at the sides)."""
    centres = []
    spec = [(-0.1, 44), (-0.55, 32), (-1.15, 26), (-1.6, 28), (-2.05, 26), (-2.6, 32), (math.pi + 0.1, 44)]
    for th, L in spec:
        x, z = outline(th)
        d = Vector((math.cos(th), 0, math.sin(th) * BB / 70.0 - 0.25)).normalized()
        s0 = Vector((math.cos(th) * 70.0 * 1.02, -50.0, -7.0 + 30.0 * 1.2 * math.sin(th) - 2.0))
        e = s0 + d * L + Vector((0, GROUND - 3.0 - s0.y, 0))
        e.z = min(e.z, z_edge(e.x) - 4.0)
        mid = s0 + d * L * 0.4 + Vector((0, -6.0, 0))
        pts = bezier(s0, mid, e, 5)
        m = add(Mesh('root', 'bark', 'stage', orient=None))
        rr = [12.0, 7.6, 4.8, 2.9, 1.4]
        rings = tube(m, pts, rr, 7, 1.0)
        # flatten: squash each ring toward its centre vertically (buttresses are wider than tall... then taller near the trunk)
        for k, ring in enumerate(rings):
            c = Vector(pts[k])
            for vi in ring:
                v = m.V[vi]
                v.y = c.y + (v.y - c.y) * (1.4 if k == 0 else 0.75)
        centres.append(pts)
    return centres


# --------------------------------------------------------------------------------------------------------- the cap
def cap():
    M = 40
    phis = [2 * math.pi * j / M for j in range(M)]
    rx, rz = CAP_HALF, 16.0          # the top's edge: exactly the collision's ends on z = 0

    def ytop(x, z):                  # flat along the fighters' plane, domed front to back
        return CAP_Y - 3.0 * (z / rz) ** 2

    top = add(Mesh('cap_top', 'cap_top', 'stage', orient=lambda p: (0, 1, 0)))
    ts = [0.0, 0.3, 0.6, 0.85, 1.0]
    rows = []
    for t in ts:
        row = []
        for j, ph in enumerate(phis):
            if t == 0.0 and j > 0:
                row.append(row[0]); continue
            x, z = t * rx * math.cos(ph), t * rz * math.sin(ph)
            row.append(top.v((x, ytop(x, z), z)))
        rows.append(row)
    uvt = lambda p: (0.5 + p.x / 60.0, 0.5 + p.z / 60.0)
    for k in range(len(ts) - 1):
        for j in range(M):
            n = (j + 1) % M
            if k == 0:
                q = [rows[0][0], rows[1][j], rows[1][n]]
            else:
                q = [rows[k][j], rows[k + 1][j], rows[k + 1][n], rows[k][n]]
            top.f(q, [uvt(top.V[i]) for i in q])
    # the rim, rolling under, and the gills to the centre
    rim = add(Mesh('cap_rim', 'cap_top', 'stage', orient=lambda p: (p.x, 0.2, p.z)))
    under = add(Mesh('cap_gills', 'gills', 'stage', orient=lambda p: (0, -1, 0)))
    rimrows = [rows[-1]]
    for (sc, dy) in ((1.015, -0.7), (1.03, -1.7), (1.02, -2.6), (0.97, -3.2)):   # out only below the top
        row = []
        for j, ph in enumerate(phis):
            p0 = top.V[rows[-1][j]]
            row.append(rim.v((p0.x * sc, p0.y + dy, p0.z * sc)))
        rimrows.append(row)
    # the rim mesh owns copies of the top's last row
    first = [rim.v(tuple(top.V[i])) for i in rows[-1]]
    rimrows[0] = first
    for k in range(len(rimrows) - 1):
        for j in range(M):
            n = (j + 1) % M
            q = [rimrows[k][j], rimrows[k + 1][j], rimrows[k + 1][n], rimrows[k][n]]
            rim.f(q, [uvt(rim.V[i]) for i in q])
    gts = [1.0, 0.75, 0.45, 0.2, 0.0]
    last = rimrows[-1]
    grows = []
    for t in gts:
        row = []
        for j, ph in enumerate(phis):
            if t == 0.0 and j > 0:
                row.append(row[0]); continue
            p0 = rim.V[last[j]]
            x, z = p0.x * t, p0.z * t
            row.append(under.v((x, p0.y + (1 - t) * 0.3, z)))
        grows.append(row)
    for k in range(len(gts) - 1):
        for j in range(M):
            n = (j + 1) % M
            u0, u1 = j / M * 2, (j + 1) / M * 2
            if k == len(gts) - 2:
                under.f([grows[k][j], grows[k + 1][0], grows[k][n]], [(u0, 1 - gts[k]), (u0, 1.0), (u1, 1 - gts[k])])
            else:
                under.f([grows[k][j], grows[k + 1][j], grows[k + 1][n], grows[k][n]],
                        [(u0, 1 - gts[k]), (u0, 1 - gts[k + 1]), (u1, 1 - gts[k + 1]), (u1, 1 - gts[k])])
    if CAP == 'stem':                                          # a thick tapered stem with a skirt, behind the plane
        st = add(Mesh('cap_stem', 'stem', 'stage', orient=None))
        pts = [(0, 0.0, -9.0), (0, 8.0, -9.0), (0, 16.0, -9.0), (0, 23.5, -9.0)]
        tube(st, pts, [6.0, 4.6, 4.0, 4.4], 10, 2.0)
        sk = add(Mesh('cap_skirt', 'gills', 'stage', orient=None))
        tube(sk, [(0, 17.5, -9.0), (0, 15.0, -9.0), (0, 13.0, -9.0)], [4.4, 6.4, 7.2], 12, 2.0)


# ------------------------------------------------------------------------------------------------------ the background
def z_edge(x):
    return -10.0 - 36.0 * smoothstep(96.0, 300.0, abs(x))


def ground_y(x, z):
    """The forest floor: 60 below the top, rising gently into the distance, with low undulation."""
    return GROUND + 22.0 * smoothstep(-60.0, -640.0, z) + 2.5 * math.sin(x * 0.021 + z * 0.013) + 1.8 * math.sin(x * 0.047 - z * 0.031)


def floor_and_cliff():
    g = add(Mesh('ground', 'ground', 'back', orient=lambda p: (0, 1, 0)))
    xs = [-1320, -1040, -780, -560, -400, -290, -210, -150, -105, -70, -35, 0, 35, 70, 105, 150, 210, 290, 400, 560, 780,
          1040, 1320]                                        # out to the sky's walls (the trailer's orbits look sideways)
    zf = [0.0, 0.08, 0.18, 0.3, 0.45, 0.62, 0.8, 1.0]          # fraction from the edge to the back
    idx = {}
    for a, x in enumerate(xs):
        for b, f in enumerate(zf):
            z = z_edge(x) + (-660.0 - z_edge(x)) * (f ** 1.4)
            idx[a, b] = g.v((x, ground_y(x, z), z))
    for a in range(len(xs) - 1):
        for b in range(len(zf) - 1):
            q = [idx[a, b], idx[a + 1, b], idx[a + 1, b + 1], idx[a, b + 1]]
            g.f(q, [(g.V[i].x / 60.0, g.V[i].z / 60.0) for i in q])
    c = add(Mesh('cliff', 'earth', 'back', orient=lambda p: (0, 0, 1)))
    cy = [0.0, -18.0, -60.0, -190.0]
    crow = []
    for a, x in enumerate(xs):
        z0 = z_edge(x)
        crow.append([c.v((x, ground_y(x, z0) + dy, z0 - 3.0 * math.sin(x * 0.05 + k) * (k > 0))) for k, dy in enumerate(cy)])
    for a in range(len(xs) - 1):
        for k in range(len(cy) - 1):
            q = [crow[a][k], crow[a + 1][k], crow[a + 1][k + 1], crow[a][k + 1]]
            c.f(q, [(c.V[i].x / 50.0, c.V[i].y / 50.0) for i in q])
    for a in range(len(xs)):
        for k in range(len(cy)):
            c.vtint[crow[a][k]] = (1 - 0.12 * k,) * 3
    lip = add(Mesh('cliff_lip', 'moss', 'back', orient=lambda p: (0, 0.5, 1)))
    lrow = [(lip.v((x, ground_y(x, z_edge(x)) + 0.6, z_edge(x) - 6.0)), lip.v((x, ground_y(x, z_edge(x)) - 3.5, z_edge(x) + 1.2 + 1.2 * math.sin(x * 0.07))))
            for x in xs]
    for a in range(len(xs) - 1):
        q = [lrow[a][0], lrow[a + 1][0], lrow[a + 1][1], lrow[a][1]]
        lip.f(q, [(xs[a] / 30.0, 0), (xs[a + 1] / 30.0, 0), (xs[a + 1] / 30.0, 0.4), (xs[a] / 30.0, 0.4)])
    mist = add(Mesh('mist', 'mist', 'back', tint=(1, 1, 1), lit=False, occluder=False))
    for z, y0 in ((-6.0, -70.0), (-14.0, -60.0)):
        mist.f([mist.v((-1320, y0 - 170, z)), mist.v((1320, y0 - 170, z)), mist.v((1320, y0, z)), mist.v((-1320, y0, z))],
               [(0, 1), (1, 1), (1, 0), (0, 0)])
    # the ravine's floor, far below the stage and fogged: the front of the world, closed (no void past the mist)
    rv = add(Mesh('ravine', 'earth', 'back', tint=(0.5, 0.45, 0.55), lit=False, occluder=False))
    rv.f([rv.v((-1320, -252, 720)), rv.v((1320, -252, 720)), rv.v((1320, -252, -60)), rv.v((-1320, -252, -60))],
         [(0, 0), (40, 0), (40, 12), (0, 12)])


def path():
    P = [(-300, -30), (-215, -44), (-150, -80), (-70, -118), (20, -150), (85, -200), (95, -265), (40, -330), (-40, -400),
         (-70, -480), (-30, -570), (20, -640)]
    m = add(Mesh('path', 'path', 'back', orient=lambda p: (0, 1, 0)))
    dense = []
    for k in range(len(P) - 1):
        for t in (0.0, 0.5):
            a, b = Vector((*P[k], 0)), Vector((*P[k + 1], 0))
            dense.append(a.lerp(b, t))
    dense.append(Vector((*P[-1], 0)))
    L, prev = 0.0, None
    rows = []
    for k, p in enumerate(dense):
        if prev is not None:
            L += (p - prev).length
        prev = p
        q = dense[min(k + 1, len(dense) - 1)] - dense[max(k - 1, 0)]
        nrm = Vector((-q.y, q.x, 0)).normalized()
        w = 27.0 - 10.0 * k / len(dense)
        row = []
        for s in (-1, 1):
            x, z = p.x + nrm.x * w * s, p.y + nrm.y * w * s
            row.append((m.v((x, ground_y(x, z) + 0.35, z)), L))
        rows.append(row)
    for k in range(len(rows) - 1):
        (a0, l0), (b0, _) = rows[k]; (a1, l1), (b1, _) = rows[k + 1]
        m.f([a0, b0, b1, a1], [(0, l0 / 60.0), (1, l0 / 60.0), (1, l1 / 60.0), (0, l1 / 60.0)])


def trunk(x, z, r, mat, tint, sides=10, top=380.0, lean=0.0, flare=True):
    m = add(Mesh('trunk', mat, 'back', tint=tint, orient=None))
    y0 = ground_y(x, z)
    ys = [y0 - 3.0, y0 + 5.0, y0 + 16.0, y0 + 40.0, y0 + 110.0, y0 + 220.0, top] if flare else [y0 - 3.0, y0 + 90.0, top]
    fl = [1.75, 1.4, 1.1, 1.0, 0.97, 0.93, 0.88] if flare else [1.0, 0.95, 0.88]
    ph = R.uniform(0, 6.28)
    reps = max(1, round(2 * math.pi * r / 70.0))
    rings = []
    for k, (y, f) in enumerate(zip(ys, fl)):
        row = []
        for s in range(sides):
            a = 2 * math.pi * s / sides
            b = 1.0 + (0.35 * max(0.0, math.cos(5 * a + ph)) ** 2 if k < 2 and flare else 0.0)
            row.append(m.v((x + lean * (y - y0) + math.cos(a) * r * f * b, y, z + math.sin(a) * r * f * b)))
        rings.append(row)
    for k in range(len(rings) - 1):
        for s in range(sides):
            t = (s + 1) % sides
            u0, u1 = s / sides * reps, (s + 1) / sides * reps
            v0, v1 = ys[k] / 70.0, ys[k + 1] / 70.0
            m.f([rings[k][s], rings[k][t], rings[k + 1][t], rings[k + 1][s]], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    m.axis = (x, z)
    return m


def blob(m, c, r, lon=7, lat=4, squash=0.8, seed=0):
    rr = random.Random(seed)
    bumps = [(rr.uniform(0, 6.28), rr.uniform(-1, 1), rr.uniform(0.08, 0.16)) for _ in range(5)]
    rows = []
    for i in range(lat + 1):
        th = math.pi * i / lat                                  # 0 top, pi bottom
        row = []
        for j in range(lon):
            ph = 2 * math.pi * j / lon
            d = Vector((math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph)))
            k = 1.0 + sum(a * max(0.0, d.dot(Vector((math.cos(p), h, math.sin(p))).normalized())) ** 3 for p, h, a in bumps)
            if i in (0, lat):
                if j > 0:
                    row.append(row[0]); continue
            row.append(m.v(Vector(c) + Vector((d.x * r * k, d.y * r * k * squash, d.z * r * k))))
        rows.append(row)
    for i in range(lat):
        for j in range(lon):
            n = (j + 1) % lon
            uv = [(j / lon * 2, i / lat * 1.5), (j / lon * 2, (i + 1) / lat * 1.5), ((j + 1) / lon * 2, (i + 1) / lat * 1.5),
                  ((j + 1) / lon * 2, i / lat * 1.5)]
            q = [rows[i][j], rows[i + 1][j], rows[i + 1][n], rows[i][n]]
            if i == 0:
                m.f([q[0], q[1], q[2]], uv[:3])
            elif i == lat - 1:
                m.f([q[0], q[1], q[3]], [uv[0], uv[1], uv[3]])
            else:
                m.f(q, uv)


def bushes():
    spots = [(-100, -46, 1.0), (104, -50, 1.05), (-40, -64, 0.75), (-215, -66, 1.25), (-128, -118, 1.0), (24, -168, 1.1),
             (150, -212, 1.0), (-160, -268, 1.3), (118, -312, 1.2), (-64, -372, 1.1), (270, -258, 1.25), (-305, -226, 1.3),
             (330, -128, 1.1), (-250, -150, 1.0), (-190, -104, 1.1), (-30, -130, 0.9), (60, -236, 1.0), (-110, -206, 1.0),
             (200, -150, 1.0), (-24, -300, 1.2)]
    for n, (x, z, s) in enumerate(spots):
        m = add(Mesh('bush', 'leaves', 'back', orient=None))
        cents = []
        for k in range(3 if s > 0.9 else 2):
            cx, cz = x + R.uniform(-14, 14) * s, z + R.uniform(-8, 8) * s
            r = R.uniform(9, 15) * s
            c = (cx, ground_y(cx, cz) + r * 0.35, cz)
            blob(m, c, r, 6, 4 if z > -200 else 3, 0.8, n * 10 + k)
            cents.append(c)
        m.blobs = cents


def mushrooms():
    clusters = [(-104, -22, 3, 1.7), (112, -20, 3, 1.5), (-208, -84, 3, 1.1), (232, -100, 2, 1.0), (-140, -176, 3, 0.85),
                (166, -170, 2, 0.85), (-98, -292, 2, 0.9), (62, -322, 2, 0.9)]
    for n, (x, z, cnt, s) in enumerate(clusters):
        stem_m = add(Mesh('mush_stem', 'stem', 'back', orient=None))
        cap_m = add(Mesh('mush_cap', 'mush', 'back', orient=None))
        for k in range(cnt):
            px, pz = x + R.uniform(-9, 9) * s, z + R.uniform(-6, 6) * s
            h = R.uniform(6, 12) * s * (1.2 if k == 0 else 0.85)
            rc = R.uniform(5, 8) * s * (1.15 if k == 0 else 0.8)
            y0 = ground_y(px, pz)
            tube(stem_m, [(px, y0 - 1, pz), (px, y0 + h, pz)], [rc * 0.3, rc * 0.24], 5, 1.0)
            sides = 8 if z > -120 else 5
            ring = [cap_m.v((px + math.cos(2 * math.pi * s_ / sides) * rc, y0 + h, pz + math.sin(2 * math.pi * s_ / sides) * rc)) for s_ in range(sides)]
            mid = [cap_m.v((px + math.cos(2 * math.pi * s_ / sides) * rc * 0.7, y0 + h + rc * 0.55, pz + math.sin(2 * math.pi * s_ / sides) * rc * 0.7)) for s_ in range(sides)]
            apex = cap_m.v((px, y0 + h + rc * 0.75, pz))
            uvm = lambda i: (0.5 + (cap_m.V[i].x - px) / (2.2 * rc), 0.5 + (cap_m.V[i].z - pz) / (2.2 * rc))
            for s_ in range(sides):
                t = (s_ + 1) % sides
                q = [ring[s_], mid[s_], mid[t], ring[t]]
                cap_m.f(q, [uvm(i) for i in q])
                q = [mid[s_], apex, mid[t]]
                cap_m.f(q, [uvm(i) for i in q])
            cap_m.blobs = getattr(cap_m, 'blobs', []) + [(px, y0 + h, pz)]
            under = cap_m.v((px, y0 + h - rc * 0.1, pz))
            for s_ in range(sides):
                t = (s_ + 1) % sides
                q = [ring[t], under, ring[s_]]
                cap_m.f(q, [(0.5, 0.5)] * 3)


def cards():
    """Branches framing the top, the canopy's underside, and the twilight backdrop (unfogged, in the stage group)."""
    def quad(m, a, b, c, d, uv=((0, 1), (1, 1), (1, 0), (0, 0))):
        m.f([m.v(a), m.v(b), m.v(c), m.v(d)], uv)
    br = add(Mesh('branches', 'branch', 'back', tint=(0.85, 0.8, 0.9), lit=False, occluder=False))
    quad(br, (-520, 92, -95), (-110, 92, -95), (-110, 302, -95), (-520, 302, -95))
    quad(br, (520, 100, -110), (110, 100, -110), (110, 310, -110), (520, 310, -110))
    quad(br, (-300, 190, -230), (40, 190, -230), (40, 380, -230), (-300, 380, -230))



def frames(t):
    return round(t * 60.0 / TIME_SCALE, 2)


def track(typ, keys, end, interp='lin'):
    return dict(type=typ, keys=[[frames(f / 60.0), v] if not isinstance(f, str) else None for f, v in keys], end=frames(end / 60.0), interp=interp)


def sky():
    """The twilight sky, behind everything and unfogged (the stage group): a painted backdrop, four star fields that
    twinkle on staggered periods (material alpha, as Final Destination's fades), three cloud banks drifting at different
    speeds (texture scroll, as Battlefield's sky), the treeline's ragged silhouette, the shooting star (a joint, two
    events in a 62 s loop) and six fireflies low in the forest (joints drifting and pulsing, as Fountain's sparkles)."""
    A = ANIMS.setdefault('stage', dict(joints={}, materials=[]))
    J = JOINTS.setdefault('stage', [])

    # The sky wraps the stage (the trailer's orbits and diagonal cameras look past the old flat cards): each layer is an
    # elliptical wall around the origin, as deep behind the stage as the old card was (b) and 1300 to each side (a), so
    # the match framings, which see only the back, are unchanged. Textures tile a whole number of times around.
    SEG0 = 32                                                  # (the star fields: 16, points need no finer curve)

    def ellwall(m, b, y0, y1, tile, v=(0, 1), col_lo=None, stretch=None, seg=None):
        SEG = seg or SEG0
        a = 1300.0 * b / 700.0 if stretch is None else stretch
        ang = [2 * math.pi * k / SEG for k in range(SEG + 1)]
        pts = [(a * math.sin(t), -b * math.cos(t)) for t in ang]           # t = 0: straight behind the stage
        L = [0.0]
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            L.append(L[-1] + math.hypot(x1 - x0, z1 - z0))
        reps = max(1, round(L[-1] / tile)) if tile else None
        for k in range(SEG):
            (xa, za), (xb, zb) = pts[k], pts[k + 1]
            if reps:
                ua, ub = L[k] / L[-1] * reps, L[k + 1] / L[-1] * reps
            else:                                             # the clamped backdrop: as the old card's u behind the
                sa = L[k] if L[k] <= L[-1] / 2 else L[k] - L[-1]          # stage (u = 0.5 + arc / 2600), clamped round
                sb = L[k + 1] if L[k + 1] <= L[-1] / 2 else L[k + 1] - L[-1]
                if k == SEG // 2 - 1:
                    sb = L[-1] / 2
                ua, ub = 0.5 + sa / 2600.0, 0.5 + sb / 2600.0
            q = [m.v((xa, y0, za)), m.v((xb, y0, zb)), m.v((xb, y1, zb)), m.v((xa, y1, za))]
            m.f(q, [(ua, v[1]), (ub, v[1]), (ub, v[0]), (ua, v[0])])
            if col_lo is not None:
                m.vtint[q[0]] = m.vtint[q[1]] = col_lo
        return reps
    bd = add(Mesh('sky_backdrop', 'sky2', 'stage', lit=False, occluder=False))
    ellwall(bd, 700.0, -420, 760, None, (0, (760 + 420) / 1080.0 * 1.0))
    # the stars: fading in above the glow (vertex colour: additive, so darker is fainter); three fields, staggered
    for k, (name, tile, per) in enumerate((('stars_a', 173.0, 180), ('stars_b', 153.0, 234), ('stars_c', 137.0, 287))):
        st = add(Mesh(name, name, 'stage', lit=False, occluder=False))
        b = 696.0 - k
        ellwall(st, b, 130, 230, tile, (0, 100 / tile), col_lo=(0.0, 0.0, 0.0), seg=16)
        ellwall(st, b, 230, 760, tile, (100 / tile, 630 / tile), seg=16)
        ph = [0.0, 0.3, 0.55, 0.8, 1.0]; val = [1.0, 0.3, 0.9, 0.55, 1.0]
        off = k * 0.33
        keys = sorted(((((p + off) % 1.0) * per, v) for p, v in zip(ph, val)))
        keys = [(0, keys[-1][1] if keys[0][0] > 0 else keys[0][1])] + [kv for kv in keys if kv[0] > 0] + [(per, keys[-1][1] if keys[0][0] > 0 else keys[0][1])]
        A['materials'].append(dict(material=name, tracks=[track('ALPHA', keys, per)]))
    # the clouds: three banks, far (high, slow) to near (low, faster); seamless loops (one texture width a cycle)
    for name, b, y0, y1, cyc, tint in (('cloud_far', 690.0, 176, 280, 240, (0.86, 0.86, 0.9)),
                                       ('cloud_mid', 672.0, 132, 232, 180, (0.95, 0.95, 0.97)),
                                       ('cloud_near', 655.0, 96, 200, 150, (1.0, 1.0, 1.0))):   # above x25's band (78)
        cl = add(Mesh(name, name, 'stage', tint=tint, lit=False, occluder=False))
        ellwall(cl, b, y0, y1, 650.0, (0, 1))
        A['materials'].append(dict(material=name, tracks=[track('TRAU', [(0, 0.0), (cyc * 60, 1.0)], cyc * 60)]))
    # the canopy: two ridges; each runs on down past the floor (v past 1 clamps to the texture's solid bottom row)
    tf = add(Mesh('treeline_far', 'treeline_far', 'stage', lit=False, occluder=False))     # a farther, lighter ridge
    ellwall(tf, 665.0, -420, 142, 520.0, (0, (142 + 420) / 172.0))
    tl = add(Mesh('treeline', 'treeline', 'stage', lit=False, occluder=False))
    ellwall(tl, 640.0, -420, 130, 520.0, (0, (130 + 420) / 160.0))   # crowns ~ y 30-100: across x25's band top (78)
    if STAR_ROAD:                                            # a small Star Road nod: rare, high, under a second
        # its paths run through the open sky between the near trunks, above the treeline (y 150 to 116 on the backdrop:
        # under x25's frame top, y 142, and mostly above x55's band top, y 123)
        d = Vector((0.84, -0.54, 0)).normalized(); n = Vector((-d.y, d.x, 0))
        ss = add(Mesh('shooting_star', 'streak', 'stage', lit=False, occluder=False, joint='star'))
        o = Vector((0, 0, -680.0)); tail = o - d * 46.0
        q = [ss.v(tuple(tail - n * 1.0)), ss.v(tuple(o - n * 1.0)), ss.v(tuple(o + n * 1.0)), ss.v(tuple(tail + n * 1.0))]
        ss.f(q, [(0, 1), (1, 1), (1, 0), (0, 0)])
        J.append(dict(name='star', t=[0.0, 0.0, -680.0]))
        loop, dur, travel = 62 * 60, 40, 58.0
        t0 = float(os.environ.get('STAR_T0', 22))            # the first event (s); a test build fires it early
        ev = [(int(t0 * 60), Vector((-45.0, 150.0, 0))), (int((t0 + 29) * 60), Vector((58.0, 147.0, 0)))]
        tx, ty, sc = [(0, ev[-1][1].x + d.x * travel)], [(0, ev[-1][1].y + d.y * travel)], [(0, 0.0)]
        for t0, p0 in ev:
            p1 = p0 + d * travel
            tx += [(t0, p0.x), (t0 + dur, p1.x)]; ty += [(t0, p0.y), (t0 + dur, p1.y)]
            sc += [(t0, 0.0), (t0 + 5, 1.0), (t0 + dur - 12, 1.0), (t0 + dur, 0.0)]
        tx.append((loop, tx[-1][1])); ty.append((loop, ty[-1][1])); sc.append((loop, 0.0))
        def mixed(tr, keys):                                 # hold (con) between events, move (lin) during them
            out = track(tr, keys, loop)
            out['interp'] = 'lin'
            return out
        A['joints']['star'] = [mixed('TRAX', tx), mixed('TRAY', ty)] + [track(a, sc, loop) for a in ('SCAX', 'SCAY', 'SCAZ')]
    # fireflies: six glows drifting low in the forest, each on its own slow loop, pulsing
    homes = [(-128, -46, -70), (140, -42, -92), (-214, -38, -160), (226, -36, -142), (-66, -44, -205), (86, -40, -244)]
    for k, h in enumerate(homes):
        nm = f'fly{k}'
        fl = add(Mesh('firefly', 'glowdot', 'stage', tint=(0.85, 0.9, 0.7), lit=False, occluder=False, joint=nm))
        c = Vector(h); r = 1.3
        q = [fl.v(tuple(c + Vector((-r, -r, 0)))), fl.v(tuple(c + Vector((r, -r, 0)))), fl.v(tuple(c + Vector((r, r, 0)))), fl.v(tuple(c + Vector((-r, r, 0))))]
        fl.f(q, [(0, 1), (1, 1), (1, 0), (0, 0)])
        J.append(dict(name=nm, t=list(h)))
        per = 420 + 70 * k
        rr = random.Random(100 + k)
        pts = [(rr.uniform(-12, 12), rr.uniform(-5, 6), rr.uniform(-8, 8)) for _ in range(4)]
        pts.append(pts[0])
        ts = [i * per / 4 for i in range(5)]
        A['joints'][nm] = [track(ax, [(t, h[i] + p[i]) for t, p in zip(ts, pts)], per, 'spl') for i, ax in enumerate(('TRAX', 'TRAY', 'TRAZ'))]
        blink = [(0, 1.0), (per * 0.2, 0.25), (per * 0.35, 1.0), (per * 0.7, 0.6), (per, 1.0)]
        A['joints'][nm] += [track(a, blink, per) for a in ('SCAX', 'SCAY', 'SCAZ')]


def background():
    floor_and_cliff()
    path()
    near = [(-238, -104, 30, 'bark'), (252, -118, 28, 'bark'), (-172, -178, 15, 'birch'), (182, -190, 16, 'birch'),
            (-340, -165, 34, 'bark'), (352, -180, 32, 'bark')]
    mid = [(-112, -300, 17, 'bark'), (72, -345, 15, 'bark'), (148, -282, 12, 'birch'), (-42, -410, 14, 'bark'),
           (-270, -338, 20, 'bark'), (312, -362, 19, 'bark'), (-196, -252, 11, 'birch'), (232, -430, 15, 'bark')]
    for x, z, r, m in near:
        trunk(x, z, r, m, (0.5, 0.47, 0.56) if m == 'birch' else (0.78, 0.76, 0.82), 9, lean=R.uniform(-0.03, 0.03))
    for x, z, r, m in mid:
        trunk(x, z, r, 'birch' if m == 'birch' else 'bark_far', (0.5, 0.47, 0.56) if m == 'birch' else (0.8, 0.78, 0.84), 7,
              lean=R.uniform(-0.03, 0.03))
    for k in range(6):
        x = -560 + k * 224 + R.uniform(-40, 40)
        trunk(x, R.uniform(-560, -500), R.uniform(10, 18), 'bark_far', (0.7, 0.68, 0.76), 6, flare=False)
    bushes()
    mushrooms()
    cards()
    sky()


# ----------------------------------------------------------------------------------------------------------- light
KEY = Vector((-0.45, 0.78, 0.44)).normalized(); KEY_C = Vector((1.0, 0.84, 0.68))
RIM = Vector((0.1, 0.25, -1.0)).normalized(); RIM_C = Vector((0.95, 0.62, 0.52))
SKY_UP, SKY_DN = Vector((0.52, 0.5, 0.66)), Vector((0.2, 0.16, 0.2))


def hemi(n, k=24):
    """k cosine-weighted directions around n (a fixed Fibonacci set, rotated)."""
    a = Vector((0, 1, 0)) if abs(n.y) < 0.9 else Vector((1, 0, 0))
    u = n.cross(a).normalized(); w = n.cross(u)
    out = []
    for i in range(k):
        t = (i + 0.5) / k
        r = math.sqrt(t); ph = i * 2.39996
        out.append((u * (r * math.cos(ph)) + w * (r * math.sin(ph)) + n * math.sqrt(1 - t)).normalized())
    return out


def bake(meshes):
    V, P = [], []
    for m in meshes:
        if not m.occluder:
            continue
        o = len(V); V += [tuple(v) for v in m.V]; P += [[o + i for i in f] for f in m.F]
    bvh = BVHTree.FromPolygons(V, P, all_triangles=False)
    V2, P2 = [], []
    for m in meshes:
        if not m.occluder or m.name.startswith('cap_'):
            continue
        o = len(V2); V2 += [tuple(v) for v in m.V]; P2 += [[o + i for i in f] for f in m.F]
    shadow = BVHTree.FromPolygons(V2, P2, all_triangles=False)
    for m in meshes:
        # face normals, flipped to the mesh's outward sense; smooth vertex normals from them
        vn = [Vector((0, 0, 0)) for _ in m.V]
        for fi, f in enumerate(m.F):
            p = [m.V[i] for i in f]
            n = (p[1] - p[0]).cross(p[2] - p[0])
            if len(p) == 4:
                n += (p[2] - p[0]).cross(p[3] - p[0])
            c = sum(p, Vector()) / len(p)
            if m.orient is not None:
                out = Vector(m.orient(c))
            elif hasattr(m, 'axis'):
                out = Vector((c.x - m.axis[0], 0, c.z - m.axis[1]))
            elif hasattr(m, 'blobs'):
                out = c - Vector(min(m.blobs, key=lambda b: (Vector(b) - c).length))
            elif hasattr(m, 'orient_c'):
                cc = min(m.orient_c, key=lambda q: (Vector(q) - c).length)
                out = c - Vector(cc)
            else:
                out = n
            if n.dot(out) < 0:
                m.F[fi] = f[::-1]; m.UV[fi] = m.UV[fi][::-1]; n = -n
            for i in f:
                vn[i] += n
        m.N = [n.normalized() if n.length > 1e-9 else Vector((0, 1, 0)) for n in vn]
        cols = []
        for i, (p, n) in enumerate(zip(m.V, m.N)):
            t = Vector(m.tint)
            if i in m.vtint:
                t = Vector((t.x * m.vtint[i][0], t.y * m.vtint[i][1], t.z * m.vtint[i][2]))
            if not m.lit:
                cols.append(t); continue
            o = p + n * 0.15
            hits = 0.0
            for d in hemi(n):
                h = bvh.ray_cast(o, d, 45.0)
                if h[0] is not None:
                    hits += 1.0 - h[3] / 45.0
            ao = 1.0 - 0.85 * hits / 24.0
            sky = SKY_DN.lerp(SKY_UP, n.y * 0.5 + 0.5)
            kd = max(0.0, n.dot(KEY))
            if kd > 0 and shadow.ray_cast(o, KEY, 1500.0)[0] is not None:
                kd *= 0.3
            rd = max(0.0, n.dot(RIM)) ** 2
            c = sky * ao + KEY_C * (kd * 0.72 * (0.55 + 0.45 * ao)) + RIM_C * rd * 0.35 * ao
            cols.append(Vector((min(1.0, c.x * t.x), min(1.0, c.y * t.y), min(1.0, c.z * t.z))))
        m.C = cols


def export(meshes, out):
    groups = {}
    for m in meshes:
        g = groups.setdefault(m.group, {})
        for f, uv, fm in zip(m.F, m.UV, getattr(m, 'FM', [m.mat] * len(m.F))):
            e = g.setdefault((fm, m.joint), dict(material=fm, tris=[], uv=[], colors=[], **({'joint': m.joint} if m.joint else {})))
            for tri in ([0, 1, 2], [0, 2, 3])[:len(f) - 2]:
                e['tris'].append([[round(c, 3) for c in m.V[f[k]]] for k in tri])
                e['uv'].append([[round(uv[k][0], 4), round(uv[k][1], 4)] for k in tri])
                e['colors'].append([[round(c * 255) for c in m.C[f[k]]] for k in tri])
    stats = {g: {}for g in groups}
    for g, d in groups.items():
        for (mat, j), v in d.items():
            stats[g][mat] = stats[g].get(mat, 0) + len(v['tris'])
    json.dump(dict(groups={g: list(d.values()) for g, d in groups.items()}, stats=stats, joints=JOINTS, anims=ANIMS), open(out, 'w'))
    return stats


def to_blend(meshes, path):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for m in meshes:
        me = bpy.data.meshes.new(m.name)
        me.from_pydata([tuple(v) for v in m.V], [], m.F)
        ca = me.color_attributes.new('light', 'FLOAT_COLOR', 'POINT')
        for i, c in enumerate(m.C):
            ca.data[i].color = (c.x, c.y, c.z, 1.0)
        ob = bpy.data.objects.new(f'{m.group}_{m.name}', me)
        bpy.context.scene.collection.objects.link(ob)
    bpy.ops.wm.save_as_mainfile(filepath=path)


def holo():
    """The stage-select hologram: the stump and the cap, low poly (24 around), no textures; not in the stage file."""
    n = 24
    th = [2 * math.pi * i / n for i in range(n)]
    m = add(Mesh('holo_stump', 'holo', 'holo', lit=False, occluder=False))
    ys = [0.0, -6.0, -18.0, -32.0, -46.0, -60.0]
    ws = [1.0, 0.97, 0.86, 0.83, 0.93, 1.2]
    rows = []
    for y, w in zip(ys, ws):
        rows.append([m.v((outline(t)[0] * (1 if y == 0 else w), y, outline(t)[1] if y == 0 else -7.0 + 30.0 * math.sin(t) * (0.3 if math.sin(t) > 0 else 1.0))) for t in th])
    for k in range(len(rows) - 1):
        for i in range(n):
            j = (i + 1) % n
            m.f([rows[k][i], rows[k + 1][i], rows[k + 1][j], rows[k][j]], [(0, 0)] * 4)
    c = add(Mesh('holo_cap', 'holo', 'holo', lit=False, occluder=False))
    ring = [c.v((CAP_HALF * math.cos(t), CAP_Y - 3.0 * math.sin(t) ** 2, 16.0 * math.sin(t))) for t in th]
    under = [c.v((CAP_HALF * 1.03 * math.cos(t), CAP_Y - 2.6 - 3.0 * math.sin(t) ** 2, 16.5 * math.sin(t))) for t in th]
    top, bot = c.v((0, CAP_Y, 0)), c.v((0, CAP_Y - 3.4, 0))
    for i in range(n):
        j = (i + 1) % n
        c.f([top, ring[i], ring[j]], [(0, 0)] * 3)
        c.f([ring[i], under[i], under[j], ring[j]], [(0, 0)] * 4)
        c.f([bot, under[j], under[i]], [(0, 0)] * 3)


if __name__ == '__main__':
    O, ths = stump()
    holo()
    cap()
    if not PLAY_ONLY:
        roots(O, ths)
        background()
    bake(MESHES)
    stats = export(MESHES, OUT)
    if BLEND:
        to_blend(MESHES, BLEND)
    tot = sum(sum(d.values()) for d in stats.values())
    print('FOREST_SCENE', json.dumps(stats), 'triangles', tot)
