"""geno_cannon.py: Geno Flash's full-body cannon (DESIGN §12; ART.md "Geno Flash's cannon"): the blue-and-gold cannon on
its wheeled carriage that he becomes in Super Mario RPG (SPR0030), as the production model's own parts.

It is the body group's option 1 (rig.BODY: group 0 option 0 is Geno, option 1 the cannon, as Samus's group 0 option 2 is
her Morph Ball), so one model-mod command hides every body mesh and shows it. It rides three joints of its own
(rig.CANNON_JOINTS, TopN's last children): nothing on them moves a hurtbox. Built in the joints' rest frames, deployed:
the wheels on the floor, the barrel level along +Z (its pitch is the animation's), in glTF space (Y up, facing +Z).

    CannonN        the carriage: two wooden cheeks cradling the trunnions, the bed between them, a short trail to the
                   floor behind, the iron axle
    CannonWheelN   the two wheels: turned wood with a thick brass tyre and an iron hub in a brass ring (SMRPG's gold
                   half-discs with the dark hole)
    CannonBarrelN  the barrel: SMRPG's blue body (his capelet's blue, lacquered over wooden staves) in two lengths
                   bound by brass hoops, a zig-zag hem where the blue meets the brass breech (the capelet's points), a
                   ribbed brass cascabel with a wooden knob, a studded chase and a flared brass muzzle with a dark bore;
                   the trunnions

Textures: 'fcbarrel' (the barrel, recoloured with the costume's capelet colour: costumes.py) and 'fccarriage' (wood,
brass and iron: never recoloured). Mirrored halves share texels, as the rest of the model's do. The low model's cannon
(build_low) reuses both textures on the same UV conventions.

    python geno_cannon.py        # the stats
"""
import math
import numpy as np
import geno_geo as G
from geno_geo import Mesh

import rig  # noqa: E402  (the joints: rig.CANNON_*)

K = rig.CANNON_K
GROUP, OPTION = rig.BODY_GROUP, rig.BODY['cannon']
TRUNNION = np.array(rig.CANNON_TRUNNION, float)          # the barrel's pivot (world, rest)
AXLE = np.array(rig.CANNON_AXLE, float)                  # the wheels' centre
WR = AXLE[1]                                             # the wheel radius: they stand on the floor
BARREL, WHEEL, CARRIAGE = 'CannonBarrelN', 'CannonWheelN', 'CannonN'

# ---- the barrel: a profile (x along the bore from the trunnions, radius), breech knob to bore floor, in base units
# (x K). One surface of revolution; the texture paints its parts by x (paint.paint_fcbarrel reads BARREL_PARTS).
BARREL_R = 1.12                  # the barrel's girth over the profile's radii: SMRPG's is short and stout
BARREL_PROFILE = [(x, r * BARREL_R) for x, r in [
    (-4.30, 0.00), (-4.18, 0.55), (-3.98, 0.90), (-3.74, 1.10),               # the knob: a wooden dome (SMRPG's brown back)
    (-3.62, 1.30), (-3.30, 1.55), (-2.90, 1.68), (-2.45, 1.72),               # the cascabel (ribbed brass)
    (-2.22, 1.79), (-2.02, 1.64),                                             # the base ring (brass)
    (-0.32, 1.50),                                                            # the first length (blue)
    (-0.28, 1.63), (0.30, 1.63), (0.34, 1.48),                                # the trunnion hoop (brass)
    (2.55, 1.36),                                                             # the second length (blue)
    (2.59, 1.49), (2.92, 1.49), (2.96, 1.33),                                 # the chase hoop (brass)
    (4.25, 1.22),                                                             # the chase (blue, studded)
    (4.32, 1.33), (5.20, 1.54), (5.55, 1.66), (5.66, 1.50), (5.64, 0.98),     # the muzzle (brass): swell, lip, face
    (4.95, 0.90), (4.90, 0.00),                                               # the bore
]]
LOW_BARREL = [0, 3, 7, 10, 14, 18, 21, 23, 25]    # the low model's profile: a subset (the same v, so the same texels)
# the parts along the bore (base units, x from, x to), for the painter
BARREL_PARTS = dict(knob=(-4.4, -3.68), cascabel=(-3.66, -2.40), base_ring=(-2.40, -2.02), blue1=(-2.02, -0.30),
                    hoop1=(-0.30, 0.34), blue2=(0.34, 2.57), hoop2=(2.57, 2.96), chase=(2.96, 4.28),
                    muzzle=(4.28, 5.70))
N_BARREL, N_BARREL_LOW = 14, 6

# ---- the wheels: a profile (x out along the axle from the cannon's centre line, radius), hub cap to inner face
WHEEL_OUT = 0.24                 # the wheels stand out past the stout barrel's cheeks
WHEEL_X = 2.40 + WHEEL_OUT       # the wheel's mid-plane (base units)
WHEEL_PROFILE = [(x + WHEEL_OUT, r) for x, r in [
    (3.02, 0.00), (2.92, 0.40), (2.80, 0.62),                                 # the hub (iron) in its brass ring
    (2.73, 0.72), (2.70, 1.80),                                               # the face (wood)
    (2.77, 1.88), (2.77, 2.12), (2.71, 2.30),                                 # the tyre's face (brass)
    (2.09, 2.30),                                                             # the tread
    (2.03, 2.10), (2.03, 0.00),                                               # the inner face
]]
LOW_WHEEL = [0, 7, 8, 10]
N_WHEEL, N_WHEEL_LOW = 14, 6
WHEEL_SPLIT = 8                  # profile points [0, 8) map to the face disc, the rest ring the tread band

# ---- the carriage (base units): the cheeks' outline in the side view (z, y), counter-clockwise seen from +X, with the
# notch the trunnion rests in; their thickness across x; the bed and the trail
CHEEK_X = (1.90, 2.22)
CHEEK = [(-2.70, 0.95), (1.50, 0.95), (1.62, 2.10), (1.35, 3.10), (0.80, 3.72), (0.44, 3.72), (0.30, 3.52),
         (-0.30, 3.52), (-0.44, 3.72), (-0.80, 3.72), (-1.30, 3.00), (-2.70, 1.60)]
CHEEK_FAN = (0.0, 2.30)          # a point every outline vertex sees: the faces are fans from it
BED = dict(x=1.90, z=(-2.60, 1.40), y=(0.95, 1.75))
TRAIL = dict(x0=0.95, x1=0.62, z=(-2.60, -4.55), top=(1.75, 0.62), bot=(0.95, 0.02))
AXLE_R = 0.24

# ---- UV atlas for 'fccarriage' (u0, v0, u1, v1): the painter reads the same rects (paint.paint_fccarriage)
UV_WHEEL = (0.0, 0.0, 0.5, 1.0)          # the wheel's sides: a half-disc (mirrored front and back), hub at the left middle
UV_TREAD = (0.5, 0.0, 1.0, 0.12)         # the tread, round the wheel (u) and across it (v)
UV_CHEEK = (0.5, 0.12, 1.0, 0.56)        # the cheeks' faces: the side view (z -> u, y -> v)
UV_EDGE = (0.5, 0.56, 1.0, 0.62)         # the cheeks' and the trail's edges (brass-bound)
UV_BED_TOP = (0.50, 0.62, 0.70, 0.88)    # the bed's top (z -> u, x -> v)
UV_BED_FRONT = (0.70, 0.62, 0.78, 0.75)  # its front
UV_BED_BOT = (0.70, 0.75, 0.78, 0.88)    # its underside
UV_TRAIL_TOP = (0.78, 0.62, 1.0, 0.75)   # the trail's top (and underside)
UV_TRAIL_SIDE = (0.78, 0.75, 1.0, 0.88)  # the trail's sides
UV_AXLE = (0.5, 0.88, 1.0, 0.94)         # the axle (iron)
# 'fcbarrel': u round the bore (mirrored: |angle| / pi from the top), v along the profile's arc length; the trunnions
# on a strip of their own
UV_BORE = (0.0, 0.0, 1.0, 0.94)
UV_TRUNNIONS = (0.0, 0.95, 1.0, 1.0)


def _k(p):
    return np.asarray(p, float) * K


def _arclen(prof):
    P = np.asarray(prof, float)
    L = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))])
    return L / L[-1]


def revolve(m, prof, vs, n, origin, axis, ref, weights, uv, polar=None, rect=None, inside=None):
    """A surface of revolution: profile [(x along axis, r)] (already scaled), v per profile point, n segments round
    (u = |angle| / pi from ref, mirrored). polar: (r_max) maps the profile's points into rect as a disc (u, v = centre +
    r / r_max x (cos a, sin a)) instead. Faces wind consistently along the profile (outward on the outside, inward in a
    bore); returns the grid of vertex ids."""
    o, ax, rf = (np.asarray(x, float) for x in (origin, axis, ref))
    ax = ax / np.linalg.norm(ax)
    rf = rf - ax * np.dot(rf, ax); rf /= np.linalg.norm(rf)
    sd = np.cross(ax, rf)
    R, C = len(prof), n
    ids = np.zeros((R, C), int)
    for i, (x, r) in enumerate(prof):
        pole = r < 1e-9
        for j in range(C):
            a = 2 * math.pi * j / n
            if pole and j > 0:
                ids[i, j] = ids[i, 0]; continue
            p = o + ax * x + r * (math.cos(a) * rf + math.sin(a) * sd)
            if polar is not None:           # a half-disc: its diameter down the rect's left edge, the rim to the right
                u0, v0, u1, v1 = rect
                rr = 0.0 if pole else min(1.0, r / polar)
                aa = abs(math.atan2(math.sin(a), math.cos(a)))
                uvp = (u0 + (u1 - u0) * (0.02 + 0.96 * rr * math.sin(aa)),
                       (v0 + v1) / 2 - (v1 - v0) / 2 * 0.96 * rr * math.cos(aa))
            else:
                u0, v0, u1, v1 = uv
                aa = abs(math.atan2(math.sin(a), math.cos(a)))
                uvp = (u0 + (u1 - u0) * aa / math.pi, v0 + (v1 - v0) * vs[i])
            ids[i, j] = m.add(p, uvp, weights)
    f0 = len(m.F)
    for i in range(R - 1):
        for j in range(C):
            q = [ids[i, j], ids[i, (j + 1) % C], ids[i + 1, (j + 1) % C], ids[i + 1, j]]
            dq = []
            for v in q:
                if v not in dq: dq.append(v)
            if len(dq) >= 3: m.face(*dq)
    # wind: faces point away from `inside` (a point: a wheel's centre) or, by default, from the axis (a barrel), by an
    # area-weighted vote over the call's faces (flat rings have no say); a bore's walls then face in, as they should
    V = np.array(m.V)
    vote = 0.0
    for k in range(f0, len(m.F)):
        f = m.F[k]; p = V[list(f)]
        c = p.mean(0)
        nrm = np.cross(p[1] - p[0], p[2] - p[0])
        if len(f) == 4: nrm = nrm + np.cross(p[2] - p[0], p[3] - p[0])
        away = c - np.asarray(inside, float) if inside is not None else c - (o + ax * np.dot(c - o, ax))
        vote += np.dot(nrm, away / (np.linalg.norm(away) + 1e-12))
    if vote < 0:
        m.F[f0:] = [ff[::-1] for ff in m.F[f0:]]
    return ids


# ---------------------------------------------------------------------------------------------------------------------
def barrel_mesh(low=False):
    """The barrel and its trunnions, rigid on CannonBarrelN (which pitches about the trunnions' axis, world X)."""
    m = Mesh('low_fc_barrel' if low else 'fc_barrel', 'fcbarrel', 'cannon')
    idx = LOW_BARREL if low else range(len(BARREL_PROFILE))
    vs_all = _arclen(BARREL_PROFILE)
    prof = [tuple(_k(BARREL_PROFILE[i])) for i in idx]
    vs = [vs_all[i] for i in idx]
    revolve(m, prof, vs, N_BARREL_LOW if low else N_BARREL, TRUNNION, (0, 0, 1), (0, 1, 0), {BARREL: 1.0}, UV_BORE)
    if not low:                   # the trunnions: short brass pins out to the cheeks, on their own strip of the texture
        for sx in (1, -1):
            prof_t = [(1.38 * K, 0.36 * K), (CHEEK_X[1] * K + 0.08 * K, 0.36 * K), (CHEEK_X[1] * K + 0.12 * K, 0.0)]
            revolve(m, [(x * sx, r) for x, r in prof_t], [0.0, 0.7, 1.0], 8, TRUNNION, (1, 0, 0), (0, 1, 0),
                    {BARREL: 1.0}, UV_TRUNNIONS)
    m.sharp = 40
    m.group, m.option = GROUP, OPTION
    return m


def _cheek(m, sx, low=False):
    """One cheek: the outline extruded across CHEEK_X, faces as fans from CHEEK_FAN, the edge brass-bound."""
    xi, xo = (x * K for x in CHEEK_X)
    zs = [p[0] for p in CHEEK]; ys = [p[1] for p in CHEEK]
    z0, z1, y0, y1 = min(zs), max(zs), min(ys), max(ys)
    u0, v0, u1, v1 = UV_CHEEK

    def uv(z, y):
        return (u0 + (u1 - u0) * (z - z0) / (z1 - z0), v1 - (v1 - v0) * (y - y0) / (y1 - y0))
    W = {CARRIAGE: 1.0}
    for x, out in ((xo, 1),) + (() if low else ((xi, -1),)):   # the outer face looks away from the barrel, the inner toward it
        c = m.add((sx * x, CHEEK_FAN[1] * K, CHEEK_FAN[0] * K), uv(*CHEEK_FAN), W)
        ids = [m.add((sx * x, y * K, z * K), uv(z, y), W) for z, y in CHEEK]
        for j in range(len(ids)):
            f = (c, ids[j], ids[(j + 1) % len(ids)])
            p = np.array([m.V[i] for i in f]); nrm = np.cross(p[1] - p[0], p[2] - p[0])
            m.face(*(f if nrm[0] * sx * out > 0 else f[::-1]))
    if low:                                     # the low model: the outer face only
        return
    # the edge: a strip round the outline, facing out of the outline (counter-clockwise in (z, y) seen from +X)
    eu0, ev0, eu1, ev1 = UV_EDGE
    L = np.concatenate([[0], np.cumsum([math.hypot(CHEEK[(j + 1) % len(CHEEK)][0] - CHEEK[j][0],
                                                   CHEEK[(j + 1) % len(CHEEK)][1] - CHEEK[j][1]) for j in range(len(CHEEK))])])
    for j in range(len(CHEEK)):
        (za, ya), (zb, yb) = CHEEK[j], CHEEK[(j + 1) % len(CHEEK)]
        if ya < 1.0 and yb < 1.0: continue           # the bottom edge sits on the bed
        a0, a1 = L[j] / L[-1], L[j + 1] / L[-1]
        q = [m.add((sx * xo, ya * K, za * K), (eu0 + (eu1 - eu0) * a0, ev0), W),
             m.add((sx * xo, yb * K, zb * K), (eu0 + (eu1 - eu0) * a1, ev0), W),
             m.add((sx * xi, yb * K, zb * K), (eu0 + (eu1 - eu0) * a1, ev1), W),
             m.add((sx * xi, ya * K, za * K), (eu0 + (eu1 - eu0) * a0, ev1), W)]
        p = np.array([m.V[i] for i in q]); nrm = np.cross(p[1] - p[0], p[2] - p[0])
        # counter-clockwise (z right, y up, seen from +X): outward is the edge direction turned clockwise
        e = np.array([zb - za, yb - ya]); o2 = np.array([e[1], -e[0]])       # (z, y)
        o3 = np.array([0.0, o2[1], o2[0]])
        m.face(*(q if np.dot(nrm, o3) > 0 else q[::-1]))


def _box(m, lo, hi, W, rects, skip=()):
    """An axis-aligned box (lo, hi: (x, y, z)), each face ('+y', '-z', ...) mapped to rects[face] by its own two axes;
    faces in skip left out."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    faces = {'+y': [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
             '-y': [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)],
             '+x': [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)],
             '-x': [(x0, y0, z1), (x0, y0, z0), (x0, y1, z0), (x0, y1, z1)],
             '+z': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
             '-z': [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)]}
    c = np.array([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    for key, q in faces.items():
        if key in skip: continue
        u0, v0, u1, v1 = rects[key]
        P = np.array(q, float)
        ids = []
        for p in P:
            a, b = {'x': (2, 1), 'y': (2, 0), 'z': (0, 1)}[key[1]]
            lo_a, hi_a = min(P[:, a]), max(P[:, a]); lo_b, hi_b = min(P[:, b]), max(P[:, b])
            ids.append(m.add(p, (u0 + (u1 - u0) * (p[a] - lo_a) / (hi_a - lo_a + 1e-9),
                                 v0 + (v1 - v0) * (p[b] - lo_b) / (hi_b - lo_b + 1e-9)), W))
        nrm = np.cross(P[1] - P[0], P[2] - P[0])
        m.face(*(ids if np.dot(nrm, P.mean(0) - c) > 0 else ids[::-1]))


def _trail(m, W, low=False):
    """The trail: a tapering beam from the bed down to the floor behind, its end shod in brass (painted)."""
    t = TRAIL
    za, zb = (z * K for z in t['z'])
    xa, xb = t['x0'] * K, t['x1'] * K
    ta, tb = (y * K for y in t['top']); ba, bb = (y * K for y in t['bot'])
    P = np.array([(-xa, ba, za), (xa, ba, za), (xa, ta, za), (-xa, ta, za),
                  (-xb, bb, zb), (xb, bb, zb), (xb, tb, zb), (-xb, tb, zb)], float)
    quads = {'top': (3, 2, 6, 7), 'L': (1, 5, 6, 2), 'R': (0, 3, 7, 4), 'bot': (0, 4, 5, 1), 'end': (4, 7, 6, 5)}
    rects = {'top': UV_TRAIL_TOP, 'bot': UV_TRAIL_TOP, 'L': UV_TRAIL_SIDE, 'R': UV_TRAIL_SIDE, 'end': UV_EDGE}
    c = P.mean(0)
    for key, q in quads.items():
        if low and key == 'bot': continue
        u0, v0, u1, v1 = rects[key]
        pts = P[list(q)]
        ids = []
        for p in pts:
            along = (p[2] - za) / (zb - za)                                   # 0 at the bed, 1 at the floor
            if key in ('top', 'bot'): across = (p[0] + xa) / (2 * xa)
            elif key == 'end': along, across = (p[0] + xb) / (2 * xb), (p[1] - bb) / (tb - bb)
            else: across = (p[1] - bb) / (ta - bb)
            ids.append(m.add(p, (u0 + (u1 - u0) * along, v0 + (v1 - v0) * across), W))
        nrm = np.cross(pts[1] - pts[0], pts[2] - pts[0])
        m.face(*(ids if np.dot(nrm, pts.mean(0) - c) > 0 else ids[::-1]))


def carriage_mesh(low=False):
    """The carriage (CannonN) and the wheels (CannonWheelN) in one mesh: one material, two bones, every vertex rigid."""
    m = Mesh('low_fc_carriage' if low else 'fc_carriage', 'fccarriage', 'cannon')
    Wc, Ww = {CARRIAGE: 1.0}, {WHEEL: 1.0}
    # the wheels
    idx = LOW_WHEEL if low else range(len(WHEEL_PROFILE))
    for sx in (1, -1):
        prof = [(sx * WHEEL_PROFILE[i][0] * K, WHEEL_PROFILE[i][1] * K) for i in idx]
        face = [i < WHEEL_SPLIT for i in idx]
        n = N_WHEEL_LOW if low else N_WHEEL
        # the face disc and the tyre's face (polar), the tread (a band), the inner face (the face's texels again)
        k = max(j for j, f in enumerate(face) if f)
        hub = AXLE + np.array([sx * WHEEL_X * K, 0.0, 0.0])                   # the wheel's centre: faces point away
        revolve(m, prof[:k + 1], None, n, AXLE, (1, 0, 0), (0, 1, 0), Ww, None, polar=WR, rect=UV_WHEEL, inside=hub)
        revolve(m, prof[k:k + 2], [0.0, 1.0], n, AXLE, (1, 0, 0), (0, 1, 0), Ww, UV_TREAD, inside=hub)
        if k + 2 < len(prof):
            revolve(m, prof[k + 1:], None, n, AXLE, (1, 0, 0), (0, 1, 0), Ww, None, polar=WR, rect=UV_WHEEL, inside=hub)
    # the axle: iron, between the wheels' inner faces (hidden ends)
    ax0 = WHEEL_PROFILE[-1][0] * K
    if not low:
        revolve(m, [(-ax0 - 0.02, AXLE_R * K), (ax0 + 0.02, AXLE_R * K)], [0.0, 1.0], 6, AXLE, (1, 0, 0), (0, 1, 0), Wc,
                UV_AXLE)
    # the cheeks, the bed, the trail
    for sx in (1, -1):
        _cheek(m, sx, low)
    b = BED
    _box(m, (-b['x'] * K, b['y'][0] * K, b['z'][0] * K), (b['x'] * K, b['y'][1] * K, b['z'][1] * K), Wc,
         {'+y': UV_BED_TOP, '+z': UV_BED_FRONT, '-y': UV_BED_BOT}, skip=('+x', '-x', '-z') + (('-y',) if low else ()))
    _trail(m, Wc, low)
    m.sharp = 40
    m.group, m.option = GROUP, OPTION
    return m


def build():
    """The high model's cannon meshes (body group, option 1)."""
    return [barrel_mesh(), carriage_mesh()]


def build_low():
    return [barrel_mesh(low=True), carriage_mesh(low=True)]


if __name__ == '__main__':
    for m in build() + build_low():
        print(f'{m.name:16s} {m.tex:10s} group {m.group} option {m.option}  tris {m.tris():4d}  verts {len(m.V):4d}  '
              f'bones {sorted(m.bones())}')
    print('high', sum(m.tris() for m in build()), 'low', sum(m.tris() for m in build_low()))
