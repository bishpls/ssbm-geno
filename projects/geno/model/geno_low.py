"""geno_low.py: the ~350-triangle low model (the off-screen magnifier bubble and Fountain of Dreams' reflections).

Same skeleton and skinning scheme as the high model; every mesh reuses a high-model texture through the same UV
conventions (mirrored lathes: u = |angle|/pi, v along the part), except the head, which carries its own small face with
the eyes, nose and carved lines painted in ('lowface', as the cast's low models do).
"""
import math
import numpy as np
import geno_geo as G
from geno_geo import Mesh, lathe, D2R


def _orient_axial(m, f0, o, ax):
    V = np.array(m.V)
    for k in range(f0, len(m.F)):
        f = m.F[k]; p = V[list(f)]; c = p.mean(0)
        axial = o + ax * np.dot(c - o, ax)
        n = np.cross(p[1] - p[0], p[2] - p[0])
        if np.dot(n, c - axial) < 0: m.F[k] = f[::-1]


def tube(m, joint, prof, n, ref, low=True):
    W = G.REST[joint]; o, ax = W[3, :3], W[0, :3]
    f0 = len(m.F)
    lathe(prof, n, (o, ax, np.asarray(ref, float)), {joint: 1.0}, m)
    _orient_axial(m, f0, o, ax)


# The low head (geno-cannon polish, 2026-09-29: the magnifier showed a blank wooden ball). It had one 64x64 texture for
# the whole mirrored head, so the face's features got a few texels each: the eye 9 across, faint and CMP-smeared, no nose.
# Now, as the cast's low heads (Mario's and Link's own low faces fill their textures): the front half its own 'lowface'
# texture (LOW_FACE_TOP to the chin, the eye and the carved seams painted large, bold enough for the bubble's size),
# the back half the high model's 'headback' on the high model's own UVs (no new texels), and the high model's nose wedge
# (6 triangles, its own texture), which reads in profile where a painted nose can't.
LOW_FACE_TOP = 30                                    # degrees: the top ring, under the band (the cap covers the rest)
LOW_FACE_BOT = -90
LOW_LATS = [-90, -45, -20, 5, 30]
LOW_FACE_COLS = list(range(-90, 91, 30))             # a column on the centre line: the texture is mirrored there
LOW_BACK_COLS = list(range(90, 271, 60))


def low_face_uv(ph, td):
    """lowface's UVs: u = |theta| / 90 (mirrored), v from LOW_FACE_TOP down to the chin (degrees)."""
    return abs(td) / 90.0, (LOW_FACE_TOP - ph) / (LOW_FACE_TOP - LOW_FACE_BOT)


def low_head():
    out = []
    face = Mesh('low_head', 'lowface', 'head')
    P = np.zeros((len(LOW_LATS), len(LOW_FACE_COLS), 3)); UV = np.zeros(P.shape[:2] + (2,))
    for i, ph in enumerate(LOW_LATS):
        for j, td in enumerate(LOW_FACE_COLS):
            P[i, j] = G.skull_pt(ph * D2R, td * D2R)
            UV[i, j] = low_face_uv(ph, td)
    face.grid(P, UV, {'HeadN': 1.0})
    face.orient_outward(G.HC)
    out.append(face)
    # the back half: the high model's headback texture, on the high head_back's UVs (u = (|theta| - 90) / 90 and v over
    # the high head's own latitude span), so it shows the same grain for nothing
    lats = [x * D2R for x in G.HEAD_LATS] + [G.PHI_B, G.PHI_B + 11 * D2R]
    top, bot = lats[-1], lats[0]
    back = Mesh('low_head_back', 'headback', 'head')
    P = np.zeros((len(LOW_LATS), len(LOW_BACK_COLS), 3)); UV = np.zeros(P.shape[:2] + (2,))
    for i, ph in enumerate(LOW_LATS):
        for j, td in enumerate(LOW_BACK_COLS):
            P[i, j] = G.skull_pt(ph * D2R, td * D2R)
            a = abs(((td + 180) % 360) - 180)
            UV[i, j] = ((a - 90) / 90, (top - ph * D2R) / (top - bot))
    back.grid(P, UV, {'HeadN': 1.0})
    back.orient_outward(G.HC)
    out.append(back)
    nose = G.nose_mesh()
    nose.name = 'low_nose'
    out.append(nose)
    return out


def build():
    out = []
    out += low_head()
    # cap: band and crown in one cone on the crown's texture
    cap = Mesh('low_cap', 'crown', 'head', spec=False)
    n = 8
    rings = [G.band_point(0, 0)]
    P = np.zeros((4, n, 3)); UV = np.zeros((4, n, 2))
    for j in range(n):
        th = 2 * math.pi * j / n
        P[0, j] = G.band_point(1, th)
        P[1, j] = G.crown_ring_point(1, th)
        P[2, j] = G.crown_ring_point(4, th)
        P[3, j] = G.crown_ring_point(len(G.CROWN_FRONT) + 1, th)
        a = abs(math.atan2(math.sin(th), math.cos(th)))
        for i, v in enumerate((1.0, G.crown_v(1), G.crown_v(4), 0.0)):
            UV[i, j] = (a / math.pi, v)
    Wg = [[{'HeadN': 1.0}] * n, [{'CapN': 1.0}] * n, [{'CapN': 0.5, 'CapMidN': 0.5}] * n, [{'CapTip3N': 1.0}] * n]
    cap.grid(P, UV, Wg, wrap=True)
    cap.orient_outward(G.HC + G.UP * 1.4 + G.FW * -0.8)
    out.append(cap)
    # collar: one layer, both sides drawn (the blue half of its texture)
    col = Mesh('low_collar', 'collar', 'torso', spec=False, double=True)
    N = 7
    P = np.zeros((2, N, 3)); UV = np.zeros((2, N, 2))
    for j in range(N):
        t = j / (N - 1); mm = abs(t - 0.5) * 2
        rows = G.collar_rows(mm)
        if t < 0.5: rows = [np.array([-p[0], p[1], p[2]]) for p in rows]
        P[0, j], P[1, j] = rows[0], rows[2]
        UV[0, j] = (mm, 0.98); UV[1, j] = (mm, 0.02)
    col.grid(P, UV, {'WaistN': 1.0})
    out.append(col)
    # cape: a single double-sided sheet over the shoulders and down the back, on the centre chain and the arms
    cape = Mesh('low_cape', 'cape', 'cape', spec=False, double=True)
    body = G.torso_meshes() + G.joints_meshes() + G.limb_meshes() + G.hand_meshes()
    bd = G.design_body_points(body)
    cols = [G.GROMMET_TH + (2 * math.pi - 2 * G.GROMMET_TH) * j / 8 for j in range(9)]
    R = 4
    Pd = np.zeros((R, len(cols), 3)); UV = np.zeros((R, len(cols), 2)); Wt = [[None] * len(cols) for _ in range(R)]
    for j, th in enumerate(cols):
        tl = th if th <= math.pi else 2 * math.pi - th
        line = G.hull_drape(tl, bd, flare=0.2)
        hem = G.hem_base(tl) - 0.1
        s_hem = G.poly_s_at_y(line, hem)
        for i, f in enumerate((0.0, 0.25, 0.6, 1.0)):
            (rho, y), _ = G.poly_at(line, f * s_hem)
            p = G.from_polar(tl, rho, y)
            if th > math.pi: p[0] = -p[0]
            Pd[i, j] = p
            side = 'L' if th <= math.pi else 'R'
            u = abs(math.pi - th) / (math.pi - G.GROMMET_TH)
            UV[i, j] = (1 - u, f * s_hem / 7.5)
            d = tl / D2R
            if i == 0:
                w = {'WaistN': 1.0}
            elif d > 125:
                w = {('CapeBN', 'CapeCN', 'CapeDN')[i - 1]: 1.0}
            elif 60 < d < 125 and i >= 1:
                w = {f'{side}ShoulderJ': 0.6, 'WaistN': 0.4}
            else:
                w = {'WaistN': 1.0}
            Wt[i][j] = w
    S = G.skin_mats(G.REST, G.DESIGN)
    Pr = G.unskin_points(Pd.reshape(-1, 3), [w for row in Wt for w in row], S).reshape(Pd.shape)
    cape.grid(Pr, UV, Wt)
    out.append(cape)
    # torso
    chest = Mesh('low_chest', 'chest', 'torso')
    n = 8
    P = np.zeros((3, n, 3)); UV = np.zeros((3, n, 2)); Wg = []
    for i, k in enumerate((0, 4, 7)):
        y, a, bf, bb, p = G.CHEST_RINGS[k]
        for j, (th, x, z) in enumerate(G.superellipse_ring(n, a, bf, bb, p, (0, G.TORSO_Z))):
            P[i, j] = (x, y, z); UV[i, j] = (abs(math.atan2(math.sin(th), math.cos(th))) / math.pi, 1 - i / 2)
        Wg.append([{'WaistN': 1.0}] * n)
    chest.grid(P, UV, Wg, wrap=True)
    chest.orient_outward((0, 8.8, G.TORSO_Z))
    out.append(chest)
    pel = Mesh('low_pelvis', 'pelvis', 'torso')
    P = np.zeros((3, n, 3)); UV = np.zeros((3, n, 2))
    for i, (y, a, bf, bb) in enumerate(((7.0, 1.16, 0.98, 1.0), (6.1, 1.34, 1.06, 1.14))):
        for j, (th, x, z) in enumerate(G.superellipse_ring(n, a, bf, bb, 2.4, (0, G.TORSO_Z))):
            P[i, j] = (x, y, z); UV[i, j] = (abs(math.atan2(math.sin(th), math.cos(th))) / math.pi, i * 0.5)
    for j in range(n):
        P[2, j] = (0, 5.2, G.TORSO_Z); UV[2, j] = (UV[1, j][0], 1.0)
    pel.grid(P, UV, {'HipN': 1.0}, wrap=True)
    pel.orient_outward((0, 6.2, G.TORSO_Z))
    out.append(pel)
    # limbs: six-sided tubes; hands: blocks with the fingers' length; boots: round clogs
    for side in 'LR':
        for name, tex, reg, j0, j1, r0, r1, r2, ref, n_ in (
                ('arm', 'forearm', 'arms', 'ShoulderJ', 'ArmJ', 0.48, 0.44, 0.46, (0, 1, 0), 5),
                ('leg', 'thigh', 'legs', 'LegJ', 'KneeJ', 0.56, 0.5, 0.48, (0, 0, 1), 5)):
            m = Mesh(f'low_{name}_{side}', tex, reg)
            A, B = G.REST[side + j0], G.REST[side + j1]
            o, ax = A[3, :3], A[0, :3]
            L1 = np.linalg.norm(B[3, :3] - o)
            L2 = 1.75 if name == 'arm' else 1.6
            refv = np.asarray(ref, float); refv = refv - ax * np.dot(refv, ax); refv /= np.linalg.norm(refv)
            sd = np.cross(ax, refv)
            P = np.zeros((3, n_ + 1, 3)); UV = np.zeros((3, n_ + 1, 2))
            for i, (x, r) in enumerate(((0.0, r0), (L1, r1), (L1 + L2, r2))):
                for k in range(n_ + 1):
                    a = 2 * math.pi * k / n_
                    P[i, k] = o + ax * x + r * (math.cos(a) * refv + math.sin(a) * sd)
                    UV[i, k] = (k / n_, i / 2)
            Wg = [[{side + j0: 1.0}] * (n_ + 1), [{side + j0: 0.5, side + j1: 0.5}] * (n_ + 1), [{side + j1: 1.0}] * (n_ + 1)]
            m.grid(P, UV, Wg)
            _orient_axial(m, 0, o, ax)
            out.append(m)
        h = Mesh(f'low_hand_{side}', 'palm', 'hands')
        tube(h, f'{side}HandN', [(0.0, 0.0), (0.12, 0.5), (1.3, 0.45), (1.45, 0.0)], 4, (0, 1, 0))
        out.append(h)
        b = Mesh(f'low_boot_{side}', 'boot', 'legs')
        n = 6
        hs = [0.0, 0.9, 1.9]
        P = np.zeros((len(hs) + 1, n, 3)); UV = np.zeros((len(hs) + 1, n, 2)); Wg = []
        sx = 1 if side == 'L' else -1
        for i, hh in enumerate(hs):
            ring = G.boot_ring(min(hh, 1.34), n)
            for j, (th, x, z) in enumerate(ring):
                if hh > 1.34:
                    x = 1.0 + 1.05 * math.sin(th); z = -0.04 + 1.05 * math.cos(th)
                P[i + 1, j] = (sx * x, hh, z)
                UV[i + 1, j] = (abs(math.atan2(math.sin(th), math.cos(th))) / math.pi, 0.12 + 0.88 * min(hh, 1.34) / 1.34)
            wk = 0.0
            Wg.append([{f'{side}KneeJ': 1.0} if wk else {f'{side}FootJ': 1.0}] * n)
        for j in range(n):
            P[0, j] = (sx * 1.0, 0.0, 0.5); UV[0, j] = (UV[1, j][0], 0.0)
        b.grid(P, UV, [Wg[0]] + Wg, wrap=True)
        b.orient_outward((sx * 1.0, 0.9, 0.3))
        out.append(b)
    import geno_cannon                  # Geno Flash's cannon: the body group's option 1, as in the high model
    out += geno_cannon.build_low()
    for m in out:
        assert np.isfinite(np.array(m.V)).all(), f'{m.name}: non-finite vertices'
    return out
