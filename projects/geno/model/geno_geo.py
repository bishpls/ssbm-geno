"""geno_geo.py: Geno's production model as data: skeleton (the rig.py contract plus the added cap and cape joints), every
mesh with positions, UVs and skin weights, in glTF space (Y up, facing +Z, feet at y = 0, rest T-pose, model units at
ModelScale 1). Pure Python + numpy, so both Blender (build_model.py) and the painter (paint.py) import it.

    python geno_geo.py            # print the stats table (triangles by region, meshes, bones per mesh)

Conventions: HSD row vectors (v' = v @ M, world = local @ parent), as rig.py. UVs are glTF's (v down, (0,0) = top-left
of the image). Faces wind counter-clockwise seen from outside. A mesh is one material with one texture. Symmetric parts
map both halves onto the same texels (u = |angle|), so a texture paints one half.
"""
import math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'rig'))
import rig  # noqa: E402  (JOINTS: the gameplay contract)

D2R = math.pi / 180


def rot3(rx, ry, rz):
    return np.array(rig.rot_xyz(rx, ry, rz), dtype=float)[:3, :3]


def fk(joints, pose=None):
    """World matrices (4x4, row vectors) for (name, parent, t, r) joints; pose overrides r per joint name."""
    W = {}
    for n, p, t, r in joints:
        if pose and n in pose:
            r = pose[n]
        M = np.eye(4)
        M[:3, :3] = rot3(*r)
        M[3, :3] = t
        W[n] = M @ W[p] if p else M
    return W


# ---- added joints (Gate 1). World positions at rest; local rotation identity, so each new joint's frame is its
# parent's (Marth's cape chains are built the same way). Cap: the point's dynamics chain is CapMidN, CapTipN, CapTip2N,
# CapTip3N (Link's 1 x 4; CapN stays the crown, the ECB top and TopOfHeadBone). Cape: 3 chains of 4 hanging from the back
# of the collar (Marth's 3 x 4): the existing CapeAN-CapeCN extended by CapeDN, and a left and a right chain.
# The positions are refined by the geometry (see cape_chain_positions) and frozen here.
ADDED_WORLD = [
    ('CapTip2N', 'CapTipN', (0.0, 15.44, -3.09)),
    ('CapTip3N', 'CapTip2N', (0.0, 15.33, -3.86)),
    ('CapeDN', 'CapeCN', (0.0, 5.38, -2.52)),
    ('CapeLAN', 'NeckN', (2.63, 10.02, -0.52)),
    ('CapeLBN', 'CapeLAN', (3.26, 8.97, -0.78)),
    ('CapeLCN', 'CapeLBN', (3.69, 7.98, -1.03)),
    ('CapeLDN', 'CapeLCN', (3.87, 7.07, -1.29)),
    ('CapeRAN', 'NeckN', (-2.63, 10.02, -0.52)),
    ('CapeRBN', 'CapeRAN', (-3.26, 8.97, -0.78)),
    ('CapeRCN', 'CapeRBN', (-3.69, 7.98, -1.03)),
    ('CapeRDN', 'CapeRCN', (-3.87, 7.07, -1.29)),
]


CONTRACT = list(getattr(rig, 'GLTF_JNAMES', [j[0] for j in rig.JOINTS]))   # the 60 joints the gameplay hangs off


def joint_table():
    """rig.JOINTS in its order (the rig may already list the added joints at their depth-first places), with the added
    joints' rest positions set from ADDED_WORLD (appended after the table when the rig lacks them); as (name, parent, t, r).
    Only the added joints ever change; every contract joint keeps the rig's transform."""
    out = [(n, p, tuple(float(x) for x in t), tuple(float(x) for x in r)) for n, p, t, r in rig.JOINTS]
    names = [j[0] for j in out]
    for name, parent, wp in ADDED_WORLD:
        W = fk(out)
        Wp = W[parent]
        t = tuple(round(float(x), 6) for x in (np.array(wp, float) - Wp[3, :3]) @ np.linalg.inv(Wp[:3, :3]))
        if name in names:
            k = names.index(name)
            assert out[k][1] == parent, f'{name}: the rig parents it to {out[k][1]}, the model to {parent}'
            out[k] = (name, parent, t, out[k][3])
        else:
            out.append((name, parent, t, (0.0, 0.0, 0.0))); names.append(name)
    return out


def skin_order():
    """glTF skin joint order: the 60 contract joints first (J00-J59 of the exported skeleton), then the added joints, then
    any later rig joints (Geno Flash's cannon: rig.CANNON_JOINTS), so every earlier joint keeps its skin index."""
    first = CONTRACT + [n for n, _, _ in ADDED_WORLD]
    return first + [j[0] for j in rig.JOINTS if j[0] not in first]


def rig_patch():
    """The added joints' rig.py lines (local translations from ADDED_WORLD), to keep the game skeleton matching the model."""
    T = {n: t for n, p, t, r in JOINTS}
    return '\n'.join(f"    ('{n}', '{p}', ({T[n][0]:.3f}, {T[n][1]:.3f}, {T[n][2]:.3f}), (0, 0, 0))," for n, p, _ in ADDED_WORLD)


JOINTS = joint_table()
JNAMES = skin_order()
N_CONTRACT = len(CONTRACT)
REST = fk(JOINTS)
# the design pose: arms hanging (70 degrees down at the shoulder), the pose the cape and collar are modelled in
ARM_DOWN = 70 * D2R
DESIGN_POSE = {'LShoulderJ': (0.0, ARM_DOWN, 0.0), 'RShoulderJ': (0.0, -ARM_DOWN, 0.0)}
DESIGN = fk(JOINTS, DESIGN_POSE)


def jpos(name, W=REST):
    return W[name][3, :3].copy()


def to_world(P, joint, W=REST):
    P = np.asarray(P, float)
    return P @ W[joint][:3, :3] + W[joint][3, :3]


def skin_mats(Wa, Wb):
    """Per-joint 4x4 skinning matrices taking a vertex posed by Wa to pose Wb."""
    return {n: np.linalg.inv(Wa[n]) @ Wb[n] for n in Wa}


def skin_points(P, weights, S):
    P = np.asarray(P, float)
    out = np.zeros_like(P)
    for i, (p, w) in enumerate(zip(P, weights)):
        M = sum(wt * S[b] for b, wt in w.items())
        out[i] = np.append(p, 1.0) @ M[:, :3]
    return out


def unskin_points(P, weights, S):
    """Inverse linear-blend skinning: positions modelled in a pose -> rest positions (S: rest -> pose matrices)."""
    P = np.asarray(P, float)
    out = np.zeros_like(P)
    for i, (p, w) in enumerate(zip(P, weights)):
        M = sum(wt * S[b] for b, wt in w.items())
        out[i] = (np.append(p, 1.0) @ np.linalg.inv(M))[:3]
    return out


# ---------------------------------------------------------------------------------------------------------------------
# mesh container
class Mesh:
    def __init__(self, name, tex, region, spec=True, double=False, spc=(255, 255, 255)):
        self.name, self.tex, self.region = name, tex, region
        self.spec, self.double, self.spc = spec, double, spc
        self.V, self.UV, self.W, self.F = [], [], [], []
        self.sharp = 60.0      # smooth-shading break angle (degrees)
        self.attr = {}         # optional per-vertex attributes for the painter (name -> list)
        self.group, self.option = 0, 0     # the engine's visibility group and option (geno_forms: the weapon forms)

    def add(self, p, uv, w, **attr):
        self.V.append(np.asarray(p, float))
        self.UV.append((float(uv[0]), float(uv[1])))
        self.W.append(dict(w))
        for k, v in attr.items():
            self.attr.setdefault(k, [None] * (len(self.V) - 1)).append(v)
        for k in self.attr:
            if len(self.attr[k]) < len(self.V):
                self.attr[k].append(None)
        return len(self.V) - 1

    def face(self, *idx):
        self.F.append(tuple(idx))

    def grid(self, P, UV, W, wrap=False, flip=False, attr=None):
        """P (R, C, 3), UV (R, C, 2), W: dict or (R, C) nested list of dicts. Quads (i,j)->(i+1,j+1). Rows whose
        points all coincide become a single pole vertex (triangle fans)."""
        P = np.asarray(P, float)
        R, C = P.shape[:2]
        ids = np.zeros((R, C), int)
        for i in range(R):
            pole = np.allclose(P[i], P[i][0], atol=1e-7)
            for j in range(C):
                w = W if isinstance(W, dict) else W[i][j]
                a = {} if attr is None else {k: v[i][j] for k, v in attr.items()}
                if pole and j > 0:
                    ids[i, j] = ids[i, 0]
                    continue
                uv = UV[i][j] if not pole else (float(np.mean([u[0] for u in UV[i]])), UV[i][0][1])
                ids[i, j] = self.add(P[i, j], uv, w, **a)
        cols = C if wrap else C - 1
        for i in range(R - 1):
            for j in range(cols):
                j2 = (j + 1) % C
                q = [ids[i, j], ids[i, j2], ids[i + 1, j2], ids[i + 1, j]]
                if flip:
                    q = q[::-1]
                dq = []
                for v in q:
                    if v not in dq:
                        dq.append(v)
                if len(dq) >= 3:
                    self.face(*dq)
        return ids

    def tris(self):
        return sum(len(f) - 2 for f in self.F)

    def bones(self):
        s = set()
        for w in self.W:
            s |= {b for b, x in w.items() if x > 1e-6}
        return s

    def arrays(self):
        return np.array(self.V), np.array(self.UV)

    def transform(self, fn):
        self.V = [np.asarray(fn(v), float) for v in self.V]

    def orient_outward(self, center=None, sign=1):
        """Flip every face whose normal points toward center (sign=-1: away from it). For convex-ish parts."""
        V = np.array(self.V)
        c = V.mean(0) if center is None else np.asarray(center, float)
        out = []
        for f in self.F:
            p = V[list(f)]
            n = np.cross(p[1] - p[0], p[2] - p[0])
            if len(f) == 4:
                n = n + np.cross(p[2] - p[0], p[3] - p[0])
            d = np.dot(n, p.mean(0) - c) * sign
            out.append(f if d >= 0 else f[::-1])
        self.F = out


# ---------------------------------------------------------------------------------------------------------------------
# primitive surfaces

def lathe(profile, n, frame, joint_w, mesh, u_mirror=True, u_scale=1.0, v_range=(0, 1), squash=(1.0, 1.0),
          phase=0.0, uv_rect=(0, 0, 1, 1)):
    """Surface of revolution in a local frame. profile: [(x_along_axis, radius)] from pole to pole (radius 0 = pole).
    frame: (origin, axis, ref) world vectors: revolves around `axis`, angle 0 at `ref`. squash scales the two
    cross axes (ref, axis x ref). UV: u = angle (mirrored |a|/pi when u_mirror), v = normalised profile arc length,
    mapped into uv_rect (u0, v0, u1, v1)."""
    o, ax, ref = [np.asarray(x, float) for x in frame]
    ax = ax / np.linalg.norm(ax)
    ref = ref - ax * np.dot(ref, ax); ref /= np.linalg.norm(ref)
    side = np.cross(ax, ref)
    prof = np.asarray(profile, float)
    L = np.concatenate([[0], np.cumsum(np.hypot(np.diff(prof[:, 0]), np.diff(prof[:, 1])))])
    vv = v_range[0] + (v_range[1] - v_range[0]) * L / L[-1]
    C = n + (0 if u_mirror else 1)
    P = np.zeros((len(prof), C, 3)); UV = np.zeros((len(prof), C, 2))
    u0, v0, u1, v1 = uv_rect
    for i, (x, r) in enumerate(prof):
        for j in range(C):
            a = 2 * math.pi * j / n + phase
            P[i, j] = o + ax * x + r * (math.cos(a) * ref * squash[0] + math.sin(a) * side * squash[1])
            aa = math.atan2(math.sin(a), math.cos(a))
            u = abs(aa) / math.pi if u_mirror else j / n
            UV[i, j] = (u0 + (u1 - u0) * min(1.0, u * u_scale), v0 + (v1 - v0) * vv[i])
    ids = mesh.grid(P, UV, joint_w, wrap=u_mirror)
    return ids


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def superellipse_ring(n, a, bf, bb, p=2.2, center=(0, 0), phase=0.0):
    """Closed ring of n points around +Z-front: returns (angle, x, z). a = half width, bf/bb = front/back depth."""
    out = []
    for j in range(n):
        th = 2 * math.pi * j / n + phase           # 0 = front (+Z), pi/2 = +X
        s, c = math.sin(th), math.cos(th)
        b = bf if c >= 0 else bb
        # superellipse radius along the direction
        r = 1.0 / ((abs(s) / a) ** p + (abs(c) / b) ** p) ** (1.0 / p)
        out.append((th, center[0] + r * s, center[1] + r * c))
    return out


def mirror_weights(w):
    def m(b):
        if b.startswith('CapeL'): return 'CapeR' + b[5:]
        if b.startswith('CapeR'): return 'CapeL' + b[5:]
        if b[0] == 'L' and b[1:2].isupper() or b[:2] in ('L1', 'L2', 'L3', 'L4'): return 'R' + b[1:]
        if b[0] == 'R' and b[1:2].isupper() or b[:2] in ('R1', 'R2', 'R3', 'R4'): return 'L' + b[1:]
        return b
    return {m(b): x for b, x in w.items()}


def append_mirror(mesh, first_vert=0, first_face=0):
    """Append the x-mirror of the mesh's vertices/faces from the given start indices (UVs shared: same texels)."""
    nv = len(mesh.V)
    base = {}
    for i in range(first_vert, nv):
        p = mesh.V[i].copy(); p[0] = -p[0]
        a = {k: mesh.attr[k][i] for k in mesh.attr}
        base[i] = mesh.add(p, mesh.UV[i], mirror_weights(mesh.W[i]), **a)
    for f in list(mesh.F[first_face:]):
        mesh.face(*[base[i] for i in f[::-1]])


# ---------------------------------------------------------------------------------------------------------------------
# HEAD: a round carved-wood ball on HeadN. The skull is parametrised in a frame tilted back by TILT so its latitude rings
# run parallel to the cap band (the band sits lower at the back).
HC0 = np.array([0.0, 12.8, 0.08])       # Gate 1 head centre (the cap profile below was drawn for it)
HC = np.array([0.0, 12.86, 0.1])
HEAD_K = 1.045                          # Gate 1b: the head grew to fill the 2.4 hurtbox
TILT = 5.5 * D2R
XA = np.array([1.0, 0, 0])
UP = np.array([0, math.cos(TILT), -math.sin(TILT)])
FW = np.array([0, math.sin(TILT), math.cos(TILT)])


def skull_r(d):
    rx = 2.56; ry = 2.4 if d[1] > 0 else 2.46; rz = 2.34 if d[2] > 0 else 2.26; p = 2.3
    return 1.0 / ((abs(d[0]) / rx) ** p + (abs(d[1]) / ry) ** p + (abs(d[2]) / rz) ** p) ** (1.0 / p)


def skull_dir(phi, th):
    return math.cos(phi) * math.sin(th) * XA + math.sin(phi) * UP + math.cos(phi) * math.cos(th) * FW


def skull_pt(phi, th, off=0.0):
    d = skull_dir(phi, th)
    return HC + (skull_r(d) + off) * d


def _solve_phi_for_y(y, th=0.0):
    lo, hi = -80 * D2R, 60 * D2R
    for _ in range(60):
        mid = (lo + hi) / 2
        if skull_pt(mid, th)[1] < y: lo = mid
        else: hi = mid
    return (lo + hi) / 2


BAND_Y = 13.33                       # the band's lower edge at the front (just over the eyes)
PHI_B = _solve_phi_for_y(BAND_Y)     # the band's latitude in the tilted frame
HEAD_LATS = [-90, -71, -56, -44, -34, -25, -17, -10, -4, 2]   # + the band edge and one ring under the band
N_HEAD = 24


def head_meshes():
    lats = [x * D2R for x in HEAD_LATS] + [PHI_B, PHI_B + 11 * D2R]
    top, bot = lats[-1], lats[0]
    face = Mesh('head_face', 'face', 'head')
    back = Mesh('head_back', 'headback', 'head')
    for mesh, t0, t1 in ((face, -90, 90), (back, 90, 270)):
        cols = list(range(t0, t1 + 1, 360 // N_HEAD))
        P = np.zeros((len(lats), len(cols), 3)); UV = np.zeros((len(lats), len(cols), 2))
        for i, ph in enumerate(lats):
            for j, td in enumerate(cols):
                P[i, j] = skull_pt(ph, td * D2R)
                a = abs(((td + 180) % 360) - 180)          # |theta| in degrees, 0 front .. 180 back
                u = a / 90 if mesh is face else (a - 90) / 90
                UV[i, j] = (u, (top - ph) / (top - bot))
        # rows go bottom (pole) -> top; columns left->right seen from outside the front for face (theta -90..90)
        mesh.grid(P, UV, {'HeadN': 1.0})
        mesh.orient_outward(HC)
    return [face, back]


EYE_C = (30.5 * D2R, 2.0 * D2R)     # (theta, phi) of the left eye's centre: its top third tucks under the band
EYE_R = (20.0 * D2R, 14.5 * D2R)    # angular half-sizes


def eye_meshes():
    out = []
    for side in (1, -1):
        m = Mesh('eye_L' if side > 0 else 'eye_R', 'eyeL' if side > 0 else 'eyeR', 'head', spec=False)
        n = 12
        rings = [0.0, 0.62, 1.0]
        P = np.zeros((len(rings), n, 3)); UV = np.zeros((len(rings), n, 2))
        for i, rr in enumerate(rings):
            for j in range(n):
                a = 2 * math.pi * j / n
                th = side * (EYE_C[0] + rr * EYE_R[0] * math.cos(a))
                ph = EYE_C[1] + rr * EYE_R[1] * math.sin(a)
                P[i, j] = skull_pt(ph, th, 0.035)
                # one mirrored texture for both eyes: u runs from the nose (0) outward (1)
                UV[i, j] = (0.5 + 0.48 * rr * math.cos(a), 0.5 - 0.48 * rr * math.sin(a))
        m.grid(P, UV, {'HeadN': 1.0}, wrap=True)
        m.orient_outward(HC)
        m.sharp = 80
        out.append(m)
    return out


def ears_nose_mesh():
    m = Mesh('ears', 'ears', 'head')
    # ears: rounded discs on the skull's sides, a dimple in the middle; tall, tilted back a little
    for side in (1,):
        th = side * 90 * D2R
        c = skull_pt(-5 * D2R, th, -0.08)
        c[2] -= 0.05
        ax = np.array([side * math.cos(12 * D2R), 0.05, -math.sin(12 * D2R)])
        prof = [(0.22, 0.0), (0.27, 0.24), (0.42, 0.46), (0.32, 0.64), (0.05, 0.68), (-0.14, 0.6)]
        lathe(prof, 8, (c, ax, np.array([0, 1.0, 0])), {'HeadN': 1.0}, m, squash=(1.0, 0.7),
              uv_rect=(0, 0, 1, 0.7))
    m.orient_outward(skull_pt(-5 * D2R, 90 * D2R, -0.4))
    append_mirror(m)
    return m


def nose_mesh():
    """The nose: a carved wooden wedge with flat planes (hard edges): a narrow ridge running from between the eyes down
    to a blunt tip, two side planes and an underside. Its own lighter material, so the planes catch the light."""
    m = Mesh('nose', 'nose', 'head')
    k = HEAD_K
    root = [skull_pt(-3.0 * D2R, s * 3.2 * D2R, -0.05) for s in (1, -1)]
    base = [skull_pt(-22.0 * D2R, s * 12.5 * D2R, -0.05) for s in (1, -1)]
    tipc = skull_pt(-19.5 * D2R, 0, 0.0) + np.array([0, -0.05, 0.62 * k])
    tip = [tipc + np.array([s * 0.09 * k, 0.0, 0.0]) for s in (1, -1)]
    faces = [(root[0], root[1], tip[1], tip[0]),   # the ridge (faces up and forward)
             (root[0], tip[0], base[0]),           # his left side plane
             (root[1], base[1], tip[1]),           # his right side plane
             (base[0], tip[0], tip[1], base[1])]   # the underside
    # one UV island per plane (quadrants of the texture: ridge, left, right, under), each a planar front projection
    islands = [(0.0, 0.0), (0.5, 0.0), (0.0, 0.5), (0.5, 0.5)]
    for f, (u0, v0) in zip(faces, islands):
        def uv(p):
            return (u0 + 0.25 + 0.2 * p[0] / 0.6, v0 + 0.25 - 0.2 * (p[1] - tipc[1] - 0.3) / 0.6)
        ids = [m.add(p, uv(p), {'HeadN': 1.0}) for p in f]
        m.face(*ids)
    m.orient_outward(skull_pt(-12 * D2R, 0, -0.6))
    m.sharp = 1.0                                # every edge hard: flat planes
    return m


# ---- CAP: band (rolled felt cuff) on HeadN, crown lofted up to a drooping point on the cap chain.
BAND_PROF = [(-0.03, -0.02), (0.25, 0.05), (0.37, 0.42), (0.33, 0.9), (0.12, 1.16)]
N_CAP = 24


def band_point(k, th):
    base = skull_pt(PHI_B, th)
    rel = base - HC
    h0 = np.dot(rel, UP)
    hdir = rel - UP * h0; rho = np.linalg.norm(hdir); hdir /= rho
    dr, dh = BAND_PROF[k]
    return HC + UP * (h0 + dh) + hdir * (rho + dr)


# crown: rings spanned between a front/top profile line and a back/under profile line of the side view (z, y), each ring
# an ellipse of half-width a in the plane holding the chord and the x axis. Ring 0 is the band's top edge.
CROWN_FRONT = [(2.12, 15.0), (1.6, 15.68), (0.72, 16.22), (-0.38, 16.44), (-1.4, 16.28), (-2.4, 15.92)]
CROWN_BACK = [(-2.56, 14.3), (-2.8, 14.42), (-3.0, 14.5), (-3.18, 14.55), (-3.36, 14.58), (-3.54, 14.62)]
CROWN_A = [2.26, 2.0, 1.6, 1.16, 0.8, 0.54]
CROWN_TIP = (-3.86, 15.14)
CROWN_W = [{'HeadN': 1.0}, {'CapN': 1.0}, {'CapN': 1.0}, {'CapN': 1.0}, {'CapN': 0.5, 'CapMidN': 0.5},
           {'CapMidN': 0.5, 'CapTipN': 0.5}, {'CapTipN': 0.55, 'CapTip2N': 0.45}, {'CapTip3N': 1.0}]


def head_scaled(p):
    """A point drawn for the Gate 1 head, carried onto the grown head (uniform scale about the head centre)."""
    return HC + HEAD_K * (np.asarray(p, float) - HC0)


def crown_ring_point(k, th):
    """Ring k of the crown at angle th (k=0 is the band's top edge; last is the tip)."""
    if k == 0:
        return band_point(len(BAND_PROF) - 1, th)
    if k > len(CROWN_FRONT):
        z, y = CROWN_TIP
        return head_scaled([0.0, y, z])
    fz, fy = CROWN_FRONT[k - 1]; bz, by = CROWN_BACK[k - 1]
    Fp = head_scaled([0.0, fy, fz]); Bp = head_scaled([0.0, by, bz])
    c = (Fp + Bp) / 2; D = Fp - Bp; b = np.linalg.norm(D) / 2; D /= 2 * b
    return c + XA * (HEAD_K * CROWN_A[k - 1] * math.sin(th)) + D * (b * math.cos(th))


def crown_point(s, th):
    """Catmull-Rom through the rings: a continuous crown surface (for the emblem patch)."""
    n = len(CROWN_FRONT) + 2
    k = int(math.floor(s)); t = s - k
    pts = [crown_ring_point(min(max(i, 0), n - 1), th) for i in (k - 1, k, k + 1, k + 2)]
    if k - 1 < 0: pts[0] = 2 * pts[1] - pts[2]
    p0, p1, p2, p3 = pts
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)


def crown_v(s):
    """The crown texture's v at ring parameter s (0 = band top, len(CROWN_FRONT)+1 = the tip)."""
    nR = len(CROWN_FRONT) + 2
    cols = [360 * j / N_CAP for j in range(N_CAP)]
    P = np.array([[crown_ring_point(i, td * D2R) for td in cols] for i in range(nR)])
    seg = np.linalg.norm(np.diff(P, axis=0), axis=2).mean(1)
    Lc = np.concatenate([[0], np.cumsum(seg)]); Lc /= Lc[-1]
    return 1 - float(np.interp(s, np.arange(nR), Lc))


def cap_meshes():
    band = Mesh('cap_band', 'band', 'head', spec=False)
    cols = [360 * j / N_CAP for j in range(N_CAP)]
    R = len(BAND_PROF)
    P = np.zeros((R, N_CAP, 3)); UV = np.zeros((R, N_CAP, 2))
    L = np.concatenate([[0], np.cumsum([math.hypot(BAND_PROF[i + 1][0] - BAND_PROF[i][0], BAND_PROF[i + 1][1] - BAND_PROF[i][1]) for i in range(R - 1)])])
    for i in range(R):
        for j, td in enumerate(cols):
            P[i, j] = band_point(i, td * D2R)
            a = abs(((td + 180) % 360) - 180)
            UV[i, j] = (a / 180, 1 - L[i] / L[-1])
    band.grid(P, UV, {'HeadN': 1.0}, wrap=True)
    band.orient_outward(HC)
    crown = Mesh('cap_crown', 'crown', 'head', spec=False)
    nR = len(CROWN_FRONT) + 2
    P = np.zeros((nR, N_CAP, 3)); UV = np.zeros((nR, N_CAP, 2)); Wg = []
    # v: arc length along the front line (th=0) and back line averaged, normalised
    for i in range(nR):
        for j, td in enumerate(cols):
            P[i, j] = crown_ring_point(i, td * D2R)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=2).mean(1)
    Lc = np.concatenate([[0], np.cumsum(seg)]); Lc /= Lc[-1]
    for i in range(nR):
        Wg.append([CROWN_W[i]] * N_CAP)
        for j, td in enumerate(cols):
            a = abs(((td + 180) % 360) - 180)
            UV[i, j] = (a / 180, 1 - Lc[i])
    crown.grid(P, UV, Wg, wrap=True)
    crown.orient_outward(HC + UP * 1.5 + FW * -0.6)
    return [band, crown]


def crown_normal(s, t):
    p = crown_point(s, t)
    ds = crown_point(s + 0.02, t) - crown_point(s - 0.02, t)
    dt = crown_point(s, t + 0.02) - crown_point(s, t - 0.02)
    n = np.cross(dt, ds); n /= np.linalg.norm(n)
    return n if np.dot(n, p - (HC + UP * 1.5)) >= 0 else -n


EMB_S0, EMB_SY, EMB_R = 0.98, 1.0 / 0.64, 2.2     # emblem (x, y) in world-ish units -> crown (theta, s)


def emblem_to_crown(x, y, lift=0.03):
    th = x / EMB_R; s = EMB_S0 + y * EMB_SY
    return crown_point(s, th) + crown_normal(s, th) * lift


def emblem_crown_uv(x, y):
    """Where an emblem point falls in the crown's own texture (the bow is painted there too, for the low model)."""
    th = x / EMB_R; s = EMB_S0 + y * EMB_SY
    return (abs(th) / math.pi, crown_v(s))


def emblem_mesh():
    """The yellow ribbon-bow appliqué, cut to its own outline and laid on the crown's front: two almond loops (rings
    whose holes show the cap through), a knot and two short tails."""
    m = Mesh('emblem', 'emblem', 'head', spec=False)
    n = 14
    loops = [(-0.66, 0.06, 0.62, 0.36, 0.3, 0.13, -0.12), (0.66, 0.06, 0.62, 0.36, 0.3, 0.13, 0.12)]
    for li, (cx, cy, ao, bo, ai, bi, rot) in enumerate(loops):
        P = np.zeros((2, n, 3)); UV = np.zeros((2, n, 2)); CUV = [[None] * n for _ in range(2)]
        for j in range(n):
            a = 2 * math.pi * j / n
            cr, sr = math.cos(rot), math.sin(rot)
            for i, (A, B, sh) in enumerate(((ao, bo, 0.0), (ai, bi, 0.03 * (1 if cx > 0 else -1)))):
                # almond: sharpen the inner end (toward the knot) of the outer ellipse
                x0, y0 = A * math.cos(a), B * math.sin(a)
                if i == 0:
                    toward = -math.cos(a) * (1 if cx > 0 else -1)
                    y0 *= 1 - 0.45 * max(toward, 0) ** 2
                x = cx + sh + x0 * cr - y0 * sr; y = cy + x0 * sr + y0 * cr
                P[i, j] = emblem_to_crown(x, y)
                CUV[i][j] = emblem_crown_uv(x, y)
                # uv: loop li occupies half the texture; outer ring on the outside
                rr = 1.0 if i == 0 else 0.45
                UV[i, j] = ((0.25 + 0.5 * li) + 0.24 * rr * math.cos(a), 0.5 - 0.46 * rr * math.sin(a))
        m.grid(P, UV, {'CapN': 1.0}, wrap=True, attr={'crown_uv': CUV})
    # knot
    c = m.add(emblem_to_crown(0.0, 0.03, 0.045), (0.5, 0.5), {'CapN': 1.0}, crown_uv=emblem_crown_uv(0.0, 0.03))
    ring = []
    for j in range(8):
        a = 2 * math.pi * j / 8
        ex, ey = 0.17 * math.cos(a), 0.03 + 0.21 * math.sin(a)
        ring.append(m.add(emblem_to_crown(ex, ey, 0.04), (0.5 + 0.08 * math.cos(a), 0.5 - 0.16 * math.sin(a)), {'CapN': 1.0},
                          crown_uv=emblem_crown_uv(ex, ey)))
    for j in range(8):
        m.face(c, ring[j], ring[(j + 1) % 8])
    # tails
    for sgn in (-1, 1):
        q = [(0.05 * sgn, -0.1), (0.2 * sgn, -0.12), (0.34 * sgn, -0.5), (0.2 * sgn, -0.5)]
        ids = [m.add(emblem_to_crown(x, y, 0.035), (0.5 + 0.1 * sgn * (k in (1, 2)), 0.62 + 0.3 * (k >= 2)), {'CapN': 1.0},
                     crown_uv=emblem_crown_uv(x, y)) for k, (x, y) in enumerate(q)]
        m.face(*ids)
    m.orient_outward(HC + UP * 1.2)
    m.sharp = 80
    # skin each vertex like the felt under it (the crown's first ring blends HeadN into CapN), so the bow stays on the
    # felt when the cap's pose tips the crown (Gate 2)
    nR = len(CROWN_FRONT) + 2
    ss = np.linspace(0, nR - 1, 200)
    vs = np.array([crown_v(x) for x in ss])
    for i, (u, v) in enumerate(m.attr['crown_uv']):
        sv = float(np.interp(-v, -vs, ss))                  # crown_v falls as s rises
        w = CROWN_W[min(int(sv), len(CROWN_W) - 2)]
        w2 = CROWN_W[min(int(sv) + 1, len(CROWN_W) - 1)]
        t = sv - int(sv)
        mix = {}
        for b_, x in w.items(): mix[b_] = mix.get(b_, 0) + x * (1 - t)
        for b_, x in w2.items(): mix[b_] = mix.get(b_, 0) + x * t
        m.W[i] = {b_: x for b_, x in mix.items() if x > 0.02}
        tot = sum(m.W[i].values()); m.W[i] = {b_: x / tot for b_, x in m.W[i].items()}
    return m


def curls_mesh():
    """Two orange paper curls on the band's front (his right): ribbons rolled into spirals. Paper has two faces: each
    curl is two single-sided layers 0.02 apart, since GX lights a double-sided face's back with its front's normal (the
    back rendered dark brown in game through Gate 1c)."""
    m = Mesh('curls', 'curls', 'head', spec=False, double=False)
    specs = [  # (x centre, width, spiral centre y, z, outer radius, turns, axis yaw deg, v0, v1)
        (-1.8, 0.78, 14.08, 3.3, 0.84, 1.4, 30, 0.0, 0.5),
        (-0.56, 0.72, 14.04, 3.22, 0.76, 1.25, 18, 0.5, 1.0),
    ]
    for cx, wd, cy, cz, r0, turns, yaw, v0, v1 in specs:
        n = 16
        # start on the band's lower front, roll forward-down, up the front, back over the top and in
        start = math.atan2(-0.62, -0.5)
        yawr = yaw * D2R
        ax = np.array([math.cos(yawr), 0, math.sin(yawr)])          # spiral axis (tilted so the front shows a spiral)
        e1 = np.array([0, 0, 1.0]); e1 = e1 - ax * np.dot(e1, ax); e1 /= np.linalg.norm(e1)
        e2 = np.cross(ax, e1)
        if e2[1] < 0: e2 = -e2
        ctr = head_scaled([cx, cy, cz]); r0 *= HEAD_K; wd *= HEAD_K
        P = np.zeros((2, n, 3)); UV = np.zeros((2, n, 2))
        for k in range(n):
            t = k / (n - 1)
            ang = start + t * turns * 2 * math.pi
            rr = r0 * (1 - 0.74 * t)
            c = ctr + rr * (math.cos(ang) * e1 + math.sin(ang) * e2)
            for i, sgn in enumerate((-1, 1)):
                P[i, k] = c + ax * (sgn * wd / 2)
                UV[i, k] = (i, v0 + (v1 - v0) * t)
        # the ribbon's normal at each vertex (across the ribbon x along it), then one layer each side
        Nn = np.zeros_like(P)
        for k in range(n):
            along = P[0, min(k + 1, n - 1)] - P[0, max(k - 1, 0)]
            nv = np.cross(ax, along); Nn[:, k] = nv / np.linalg.norm(nv)
        for sgn in (1, -1):
            f0 = len(m.F)
            m.grid(P + Nn * 0.01 * sgn, UV, {'HeadN': 1.0})
            V = np.array(m.V)
            for q in range(f0, len(m.F)):           # each layer faces away from the other
                f = m.F[q]; pp = V[list(f)]
                c = pp.mean(0); nf = np.cross(pp[1] - pp[0], pp[2] - pp[0])
                kk = int(np.argmin(np.linalg.norm(P[0] - c, axis=1)))
                if np.dot(nf, Nn[0, kk]) * sgn < 0: m.F[q] = f[::-1]
    m.sharp = 181
    return m


# ---------------------------------------------------------------------------------------------------------------------
# TORSO (WaistN / NeckN), waist ball, pelvis (HipN)
TORSO_Z = -0.12
CHEST_RINGS = [  # y, half width, front depth, back depth, exponent: a smooth wooden barrel (Gate 2: no pectoral bulge,
    # the front depth rising and falling in one curve; the chest plate is only a carved line in the texture)
    (7.02, 1.22, 1.04, 0.98, 2.3),
    (7.55, 1.34, 1.17, 1.06, 2.3),
    (8.15, 1.58, 1.29, 1.18, 2.4),
    (8.72, 1.74, 1.37, 1.28, 2.5),
    (9.22, 1.82, 1.41, 1.26, 2.6),
    (9.72, 1.8, 1.38, 1.24, 2.6),
    (10.12, 1.58, 1.14, 1.1, 2.5),
    (10.42, 1.12, 0.84, 0.9, 2.3),
    (10.58, 0.60, 0.54, 0.58, 2.1),
    (10.98, 0.52, 0.48, 0.50, 2.0),
]
N_TORSO = 20


def chest_radius(y, th):
    """Chest surface distance from the torso axis at height y, angle th (for the collar/cape fits)."""
    ys = [r[0] for r in CHEST_RINGS]
    y = min(max(y, ys[0]), ys[-1])
    k = max(i for i in range(len(ys)) if ys[i] <= y) if y < ys[-1] else len(ys) - 2
    t = (y - ys[k]) / (ys[k + 1] - ys[k])
    def rr(r):
        _, a, bf, bb, p = r
        s, c = math.sin(th), math.cos(th)
        b = bf if c >= 0 else bb
        return 1.0 / ((abs(s) / a) ** p + (abs(c) / b) ** p) ** (1.0 / p)
    return rr(CHEST_RINGS[k]) * (1 - t) + rr(CHEST_RINGS[k + 1]) * t


def torso_meshes():
    chest = Mesh('chest', 'chest', 'torso')
    R = len(CHEST_RINGS)
    P = np.zeros((R, N_TORSO, 3)); UV = np.zeros((R, N_TORSO, 2)); Wg = []
    y0, y1 = CHEST_RINGS[0][0], CHEST_RINGS[-3][0]
    for i, (y, a, bf, bb, p) in enumerate(CHEST_RINGS):
        ring = superellipse_ring(N_TORSO, a, bf, bb, p, (0, TORSO_Z))
        wrow = []
        for j, (th, x, z) in enumerate(ring):
            # pectoral plates: a bulge either side of the sternum on the upper chest
            if math.cos(th) > 0:
                pec = math.exp(-((abs(x) - 0.66) / 0.45) ** 2) * math.cos(th) ** 0.5
                pass                          # (Gate 2: no pectoral bulge)
            P[i, j] = (x, y, z)
            a_ = abs(math.atan2(math.sin(th), math.cos(th)))
            UV[i, j] = (a_ / math.pi, min(1.0, max(0.0, (y1 + 0.35 - y) / (y1 + 0.35 - y0))))
            wrow.append({'WaistN': 1.0} if y < 10.5 else {'NeckN': 1.0})
        Wg.append(wrow)
    chest.grid(P, UV, Wg, wrap=True)
    chest.orient_outward((0, 8.8, TORSO_Z))
    waist = Mesh('waist', 'joint', 'torso')
    lathe([(-0.26, 1.02), (0.0, 1.25), (0.24, 1.06)], 12, ((0, 6.98, TORSO_Z), (0, 1, 0), (0, 0, 1)), {"WaistN": 1.0},
          waist, squash=(0.86, 1.0), uv_rect=(0, 0, 1, 0.5))
    waist.orient_outward((0, 6.98, TORSO_Z))
    pelvis = Mesh('pelvis', 'pelvis', 'torso')
    PR = [(7.0, 1.28, 1.02, 1.04), (6.6, 1.44, 1.1, 1.14), (6.1, 1.5, 1.1, 1.18), (5.62, 1.36, 1.02, 1.1),
          (5.3, 0.82, 0.82, 0.92), (5.14, 0.4, 0.48, 0.54)]
    n = 16
    P = np.zeros((len(PR) + 1, n, 3)); UV = np.zeros((len(PR) + 1, n, 2))
    for i, (y, a, bf, bb) in enumerate(PR):
        for j, (th, x, z) in enumerate(superellipse_ring(n, a, bf, bb, 2.4, (0, TORSO_Z))):
            # leg openings: the rim rides up over each hip at the sides
            side = abs(math.sin(th)) ** 3
            yy = y + (0.34 * side if i >= 3 else 0.0)
            P[i, j] = (x, yy, z)
            UV[i, j] = (abs(math.atan2(math.sin(th), math.cos(th))) / math.pi, i / len(PR))
    for j in range(n):
        P[-1, j] = (0, 5.06, TORSO_Z + 0.02); UV[-1, j] = (UV[-2, j][0], 1.0)
    pelvis.grid(P, UV, {'HipN': 1.0}, wrap=True)
    pelvis.orient_outward((0, 6.2, TORSO_Z))
    return [chest, waist, pelvis]


# ---------------------------------------------------------------------------------------------------------------------
# LIMBS: rigid doll segments, ball joints between them
def limb_frame(joint, ref_world):
    W = REST[joint]
    return (W[3, :3], W[0, :3], np.asarray(ref_world, float))


def joints_meshes():
    """The ball joints (darker turned wood, closed balls with their poles along the limb): one mesh for the arms'
    (shoulder, elbow, wrist; 6 bones) and one for the legs' (hip, knee; 4 bones)."""
    out = []
    for name, region, specs in (
            ('balls_arms', 'arms', [('LShoulderJ', 0.62, (0, 1, 0), 8), ('LArmJ', 0.68, (0, 1, 0), 8), ('LHandN', 0.54, (0, 1, 0), 6)]),
            ('balls_legs', 'legs', [('LLegJ', 0.84, (0, 0, 1), 6), ('LKneeJ', 0.74, (0, 0, 1), 8)])):
        m = Mesh(name, 'joint', region)
        for j, r, ref, n in specs:
            o, ax, rf = limb_frame(j, ref)
            prof = [(-r, 0.0), (-r * 0.707, r * 0.707), (0.0, r), (r * 0.707, r * 0.707), (r, 0.0)]
            lathe(prof, n, (o, ax, rf), {j: 1.0}, m, uv_rect=(0, 0.5, 1, 1))
        V = np.array(m.V); F = []
        for f in m.F:
            p = V[list(f)]; c = p.mean(0)
            b = max(m.W[f[0]], key=m.W[f[0]].get)
            nrm = np.cross(p[1] - p[0], p[2] - p[0])
            F.append(f if np.dot(nrm, c - REST[b][3, :3]) >= 0 else f[::-1])
        m.F = F
        append_mirror(m)
        out.append(m)
    return out


def limb_mesh(name, tex, region, joint, prof, n, ref, mirror=True, uv_rect=(0, 0, 1, 1)):
    m = Mesh(name, tex, region)
    o, ax, rf = limb_frame(joint, ref)
    lathe(prof, n, (o, ax, rf), {joint: 1.0}, m, uv_rect=uv_rect)
    V = np.array(m.V)
    F = []
    for f in m.F:
        p = V[list(f)]; c = p.mean(0)
        axial = o + ax * np.dot(c - o, ax)
        nrm = np.cross(p[1] - p[0], p[2] - p[0])
        if len(f) == 4: nrm += np.cross(p[2] - p[0], p[3] - p[0])
        F.append(f if np.dot(nrm, c - axial) >= -1e-9 else f[::-1])
    m.F = F
    return m


UPPER_ARM = [(0.34, 0.0), (0.42, 0.56), (0.64, 0.7), (1.36, 0.68), (1.58, 0.53), (1.64, 0.0)]
FOREARM = [(0.2, 0.0), (0.28, 0.56), (0.5, 0.72), (1.24, 0.77), (1.52, 0.72), (1.62, 0.5), (1.66, 0.0)]
THIGH = [(0.3, 0.0), (0.38, 0.7), (0.6, 0.9), (2.02, 0.84), (2.3, 0.64), (2.38, 0.0)]
SHIN = [(0.16, 0.0), (0.25, 0.66), (0.46, 0.8), (1.52, 0.74), (1.58, 0.0)]


def limb_meshes():
    out = []
    for side, s in (('L', 1), ('R', -1)):
        out.append(limb_mesh(f'upperarm_{side}', 'upperarm', 'arms', f'{side}ShoulderJ', UPPER_ARM, 8, (0, 1, 0)))
        out.append(limb_mesh(f'forearm_{side}', 'forearm', 'arms', f'{side}ArmJ', FOREARM, 10, (0, 1, 0)))
        out.append(limb_mesh(f'thigh_{side}', 'thigh', 'legs', f'{side}LegJ', THIGH, 10, (0, 0, 1)))
        out.append(limb_mesh(f'shin_{side}', 'shin', 'legs', f'{side}KneeJ', SHIN, 8, (0, 0, 1)))
    return out


# ---- HANDS: a rounded palm block on HandN, two-segment fingers on the finger joints (the model-part poses curl them)
def rounded_rect(hy, hz, rad, n_corner=3):
    pts = []
    for cy, cz, a0 in ((hy - rad, hz - rad, 0), (-(hy - rad), hz - rad, 90), (-(hy - rad), -(hz - rad), 180), (hy - rad, -(hz - rad), 270)):
        for k in range(n_corner):
            a = (a0 + 90 * k / (n_corner - 1)) * D2R
            pts.append((cy + rad * math.cos(a), cz + rad * math.sin(a)))
    return pts


def hand_meshes():
    out = []
    palm = Mesh('palm_L', 'palm', 'hands')
    W = REST['LHandN']; o = W[3, :3]
    along, up, fw = np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])
    secs = [(0.08, 0.42, 0.33, 0.22, 0.0), (0.2, 0.66, 0.42, 0.26, 0.0), (0.6, 0.74, 0.45, 0.27, 0.02),
            (0.82, 0.69, 0.4, 0.25, 0.02)]
    rr = rounded_rect(1, 1, 0.5)
    n = len(rr)
    P = np.zeros((len(secs) + 2, n, 3)); UV = np.zeros((len(secs) + 2, n, 2))
    for i, (x, hy, hz, rad, dy) in enumerate(secs):
        pts = rounded_rect(hy, hz, rad)
        for j, (py, pz) in enumerate(pts):
            P[i + 1, j] = o + along * x + up * (py + dy) + fw * pz
            a = math.atan2(pz, py)
            UV[i + 1, j] = (0.02 + 0.96 * ((a / (2 * math.pi)) % 1.0), 0.1 + 0.8 * i / (len(secs) - 1))
    P[0, :] = o + along * 0.03; P[-1, :] = o + along * 0.85 + up * 0.02
    for j in range(n):
        UV[0, j] = (UV[1, j][0], 0.0); UV[-1, j] = (UV[-2, j][0], 1.0)
    palm.grid(P, UV, {'LHandN': 1.0}, wrap=True)
    palm.orient_outward(o + along * 0.45)
    out.append(palm)
    fingers = Mesh('fingers_L', 'finger', 'hands')
    specs = [('L1stNa', 0.36, 0.34), ('L2ndNa', 0.38, 0.36), ('L3rdNa', 0.36, 0.34), ('L4thNa', 0.32, 0.3),
             ('LThumbNa', 0.32, 0.32)]
    for ja, la, lb in specs:
        jb = ja[:-1] + 'b'
        thick = (0.21, 0.23) if 'Thumb' in ja else (0.172, 0.215)
        for jn, x0, x1, tip, v in ((ja, -0.05, la, False, (0, 0, 1, 0.5)), (jb, -0.03, lb, True, (0, 0.5, 1, 1))):
            Wj = REST[jn]
            prof = [(x0, 0.0), (x0 + 0.045, 1.0), (x1 - 0.045, 1.0), (x1, 0.0)]
            if tip:
                prof = [(x0, 0.0), (x0 + 0.05, 1.0), (x1 - 0.07, 0.96), (x1 - 0.005, 0.0)]
            prof = [(x, r) for x, r in prof]
            # ref = world up (the finger's thickness is vertical), the cross axis the depth
            ref = np.array([0, 1.0, 0]); ax = Wj[0, :3]
            m0 = len(fingers.V); f0 = len(fingers.F)
            lathe([(x, r) for x, r in prof], 6, (Wj[3, :3], ax, ref), {jn: 1.0}, fingers,
                  squash=(thick[0], thick[1]), uv_rect=v, phase=math.pi / 6)
            # orient this segment
            V = np.array(fingers.V)
            for fi in range(f0, len(fingers.F)):
                f = fingers.F[fi]; p = V[list(f)]; c = p.mean(0)
                axial = Wj[3, :3] + ax * np.dot(c - Wj[3, :3], ax)
                nrm = np.cross(p[1] - p[0], p[2] - p[0])
                if np.dot(nrm, c - axial) < 0: fingers.F[fi] = f[::-1]
    fingers.sharp = 89
    palm.sharp = 80
    out.append(fingers)
    for m in list(out):
        r = Mesh(m.name.replace('_L', '_R'), m.tex, m.region)
        r.V, r.UV, r.W, r.F = [], [], [], []
        for p, uv, w in zip(m.V, m.UV, m.W):
            q = p.copy(); q[0] = -q[0]
            r.add(q, uv, mirror_weights(w))
        r.F = [f[::-1] for f in m.F]
        r.sharp = m.sharp
        out.append(r)
    return out


# ---- BOOTS: heavy rounded Mario-like loaves: a thick sole band all round, a tall blunt toe dome, a short round heel,
# the leg entering the back third, and a wide rolled leather cuff flaring round the ankle (all on LFootJ)
def boot_ring(h, n=16):
    """Footprint ring of the boot at height h above the floor (left boot, x centred on 1.0)."""
    # (height, heel back, toe front, half width front, half width back)
    keys = [(0.0, 0.74, 2.04, 0.86, 0.72), (0.3, 0.8, 2.12, 0.91, 0.77), (0.36, 0.74, 2.06, 0.86, 0.72),
            (0.72, 0.77, 2.1, 0.9, 0.75), (1.0, 0.74, 1.98, 0.87, 0.72), (1.18, 0.68, 1.72, 0.8, 0.66),
            (1.34, 0.6, 1.08, 0.66, 0.6)]
    hs = [k[0] for k in keys]
    h = min(max(h, hs[0]), hs[-1])                 # no extrapolation past the top ring
    i = max(j for j in range(len(hs)) if hs[j] <= h + 1e-9)
    i = min(i, len(keys) - 2)
    t = (h - hs[i]) / (hs[i + 1] - hs[i])
    k = [a * (1 - t) + b * t for a, b in zip(keys[i], keys[i + 1])]
    _, back, front, wf, wb = k
    cz = 0.5 * (1 - smoothstep(1.0, 1.4, h)) + (-0.04) * smoothstep(1.0, 1.4, h)
    pts = []
    for j in range(n):
        th = 2 * math.pi * j / n
        s, c = math.sin(th), math.cos(th)
        L = (front - cz) if c >= 0 else (back + cz)
        w = wf if c >= 0 else wb
        p = 2.6
        r = 1.0 / ((abs(s) / w) ** p + (abs(c) / L) ** p) ** (1 / p)
        pts.append((th, 1.0 + r * s, cz + r * c))
    return pts


def toe_spring(z, h):
    """The sole rockers up a little at the front (Mario's shoes) and rounds off at the heel; the toe dome stays blunt."""
    t = smoothstep(1.2, 2.2, z)
    heel = smoothstep(-0.45, -0.85, z)
    lower = 1.0 - smoothstep(0.36, 1.0, h)
    return float((0.2 * t * t + 0.06 * heel) * lower)


BOOT_H = [0.0, 0.3, 0.36, 0.72, 1.0, 1.18, 1.34]


def boot_meshes():
    out = []
    boot = Mesh('boot_L', 'boot', 'legs', spc=(255, 255, 255))
    n = 16
    P = np.zeros((len(BOOT_H) + 1, n, 3)); UV = np.zeros((len(BOOT_H) + 1, n, 2))
    for i, h in enumerate(BOOT_H):
        for j, (th, x, z) in enumerate(boot_ring(h, n)):
            P[i + 1, j] = (x, h + toe_spring(z, h), z)
            UV[i + 1, j] = (abs(math.atan2(math.sin(th), math.cos(th))) / math.pi, 0.12 + 0.88 * i / (len(BOOT_H) - 1))
    for j in range(n):
        P[0, j] = (1.0, 0.0, 0.6); UV[0, j] = (UV[1, j][0], 0.0)
    Wb = []
    for i in range(P.shape[0]):
        h = BOOT_H[i - 1] if i > 0 else 0.0
        wk = {1.18: 0.2, 1.34: 0.45}.get(round(h, 2), 0.0)        # the shaft's top rings, hidden inside the cuff
        Wb.append([{'LFootJ': 1 - wk, 'LKneeJ': wk} if wk else {'LFootJ': 1.0}] * n)
    boot.grid(P, UV, Wb, wrap=True)
    boot.orient_outward((1.0, 0.8, 0.3))
    boot.sharp = 50
    out.append(boot)
    cuff = Mesh('cuff_L', 'cuff', 'legs', spc=(255, 255, 255))
    # the rolled cuff rides the shin (KneeJ) so the leg never passes through its wall when the ankle bends; its lower edge
    # blends into the boot on FootJ so the two stay joined (Gate 1d: dorsiflexion to 35, heel-up to 40, walk roll +-35)
    # a soft leather roll splits the ankle's bend: its weights run from 30% shin at the bottom to 70% at the lip
    # ... and its lip folds in toward the shin (an inner wall), so looking down into the cuff shows leather, not a hole
    # (Gate 2: the lip and its inner fold ride the shin fully, so no gap opens behind a leaning shin; the roll's lower
    # half carries the blend into the boot)
    prof = [(1.22, 0.76), (1.3, 1.0), (1.56, 1.14), (1.82, 1.12), (1.95, 1.03), (1.96, 0.93), (1.56, 0.79)]
    wts = [{'LFootJ': 0.8, 'LKneeJ': 0.2}, {'LFootJ': 0.45, 'LKneeJ': 0.55}, {'LFootJ': 0.15, 'LKneeJ': 0.85}] + \
          [{'LKneeJ': 1.0}] * 4
    f0 = len(cuff.V)
    lathe([(y, r) for y, r in prof], 10, ((1.0, 0, -0.04), (0, 1, 0), (0, 0, 1)), {'LFootJ': 1.0}, cuff)
    for i in range(f0, len(cuff.V)):          # weights by the ring each vertex sits on
        k = int(np.argmin([abs(cuff.V[i][1] - y) for y, _ in prof]))
        cuff.W[i] = dict(wts[k])
    # the lathe winds consistently: orient the whole surface by its outer wall (the inner fold then faces the shin)
    V = np.array(cuff.V); score = 0.0
    for f in cuff.F:
        p = V[list(f)]; c = p.mean(0)
        if not (1.35 < c[1] < 1.85): continue
        score += np.dot(np.cross(p[1] - p[0], p[2] - p[0]), c - np.array([1.0, c[1], -0.04]))
    if score < 0:
        cuff.F = [f[::-1] for f in cuff.F]
    out.append(cuff)
    # the whole boot a size up (a heavy loaf), about the middle of the sole
    c0, S = np.array([1.0, 0.0, 0.55]), np.array([1.1, 1.12, 1.1])
    for m in out:
        m.V = [c0 + S * (np.asarray(v) - c0) for v in m.V]
    for m in list(out):
        r = Mesh(m.name.replace('_L', '_R'), m.tex, m.region, spc=m.spc)
        r.sharp = m.sharp
        for p, uv, w in zip(m.V, m.UV, m.W):
            q = p.copy(); q[0] = -q[0]
            r.add(q, uv, mirror_weights(w))
        r.F = [f[::-1] for f in m.F]
        out.append(r)
    return out


# ---------------------------------------------------------------------------------------------------------------------
# COLLAR and CAPE. The collar stands up around the neck from the cape's neckline (outside blue, lining yellow) and flares
# into two points beside the jaw; the cape falls from the same neckline over the shoulders. Both are modelled in the
# design pose (arms hanging) and taken back to the rest T-pose by inverse skinning, so they drape correctly when posed.
GROMMET_TH = 28 * D2R          # the cape's inner edges start at the throat: grommets about a jaw-width apart


def neckline(th):
    a, bf, bb, p = 1.48, 1.16, 1.3, 2.3
    s, c = math.sin(th), math.cos(th)
    b = bf if c >= 0 else bb
    r = 1.0 / ((abs(s) / a) ** p + (abs(c) / b) ** p) ** (1.0 / p)
    y = 10.26 + 0.14 * (1 - c) / 2
    return np.array([r * s, y, TORSO_Z + r * c])


def polar(p):
    return math.atan2(p[0], p[2] - TORSO_Z), math.hypot(p[0], p[2] - TORSO_Z)


def from_polar(th, rho, y):
    return np.array([rho * math.sin(th), y, TORSO_Z + rho * math.cos(th)])


COLLAR_TOP = [  # m (0 back centre .. 1 front end), top-edge height, radius, theta of the top (deg), forward push
    # a modest standing back; two rounded petals beside the jaw, pointed at mouth height and swept back, so their yellow
    # lining shows from the front past the narrow lower jaw; the front edge runs down to the grommets at the throat
    (0.0, 11.55, 2.3, 180, 0.0), (0.333, 11.5, 2.5, 142, 0.0), (0.556, 11.62, 3.02, 118, 0.0), (0.667, 11.9, 3.38, 104, 0.0),
    (0.778, 11.38, 3.08, 90, 0.0), (0.889, 10.95, 2.42, 68, 0.0), (1.0, 10.62, 1.7, 40, 0.0)]


def collar_rows(m):
    """Collar column at mirrored position m (0 = back centre, 1 = the front edge/tip), left side: base, mid, top.
    Two wide flaps stand up beside the jaw to about mouth height, fold outward and end in points; the back stands up."""
    ks = np.array([k[0] for k in COLLAR_TOP])
    yt, rt, tht_d, fwd = [float(np.interp(m, ks, [k[i] for k in COLLAR_TOP])) for i in (1, 2, 3, 4)]
    thb = math.pi - m * (math.pi - GROMMET_TH)
    base = neckline(thb)
    top = from_polar(tht_d * D2R, rt, yt) + np.array([0.0, 0.0, fwd])
    mid = (base + top) / 2
    th_m, r_m = polar(mid)
    mid = from_polar(th_m, r_m + 0.1, mid[1] - 0.08)          # the collar bows out a little (felt, stiffened)
    return [base, mid, top]


def collar_meshes():
    """The collar as two single-sided layers: the blue outside and the yellow lining 0.045 inside it (meeting at the
    top edge), each its own mesh and texture, like the cape."""
    N = 19
    P0 = np.zeros((3, N, 3))
    for j in range(N):
        t = j / (N - 1)
        mm = abs(t - 0.5) * 2
        rows = collar_rows(mm)
        if t < 0.5:
            rows = [np.array([-p[0], p[1], p[2]]) for p in rows]
        for i, p in enumerate(rows):
            P0[i, j] = p
    Nn = grid_normals(P0)
    out = []
    for layer, name, tex in ((0, 'collar', 'collar'), (1, 'collar_in', 'collarin')):
        m = Mesh(name, tex, 'torso', spec=False)
        P = P0.copy(); UV = np.zeros((3, N, 2))
        for j in range(N):
            mm = abs(j / (N - 1) - 0.5) * 2
            for i in range(3):
                if layer == 1 and i < 2:
                    P[i, j] = P0[i, j] - Nn[i, j] * 0.045
                UV[i, j] = (mm, 1 - i / 2)
        m.grid(P, UV, {'WaistN': 1.0})
        V = np.array(m.V); score = 0.0
        for f in m.F:
            p = V[list(f)]; c = p.mean(0)
            score += np.dot(np.cross(p[1] - p[0], p[2] - p[0]), c - np.array([0, c[1], TORSO_Z]))
        if score * (1 if layer == 0 else -1) < 0:
            m.F = [f[::-1] for f in m.F]
        m.sharp = 70
        out.append(m)
    return out


# cape (a capelet): columns from the left grommet at the throat round to the back centre, dense over the front panel;
# the right half mirrors it. Each column's hem: a base height and a point (-) or notch (+), irregular, the longest point
# at the front panel's outer corner (Gate 1b: Michael's review against the remake art).
CAPE_TH_DEG = [28, 38, 50, 63, 77, 92, 108, 125, 143, 162, 180]
CAPE_COLS = len(CAPE_TH_DEG)
CAPE_TH = [d * D2R for d in CAPE_TH_DEG]
CAPE_HEM_FRONT = 50                # the front edge's angle at the hem (28 at the throat): the chest opening widens
# hem heights per column (points low, notches high): the centre front ends at mid-belly, the front panel's points
# lengthen to the outer corner (hip / fist level), the back is a capelet's (upper thigh)
HEM_Y = [7.75, 8.5, 7.2, 8.1, 6.15, 7.4, 5.75, 6.85, 5.5, 6.35, 5.1]    # points low, notches high; longest at the front panel's outer corner
HEM = [(0.5 * (HEM_Y[max(j - 1, 0)] + HEM_Y[min(j + 1, len(HEM_Y) - 1)]) * 0.5 + 0.5 * HEM_Y[j], 0.0) for j in range(len(HEM_Y))]
HEM = [(b, y - b) for (b, _), y in zip(HEM, HEM_Y)]     # (smooth envelope, the point/notch offset): the low model uses the envelope
CHAIN_Y = (8.2, 6.3, 5.4)           # the centre chain's B, C, D (A at the collar)
SIDE_CHAIN_TH = 95 * D2R            # the left and right chains ride the sides and drive the front and side panels
SIDE_CHAIN_Y = (10.06, 9.0, 8.0, 7.0)  # the side chain spans the side panel down to its hem (~7.07 at 95 deg)


def hem_base(th):
    d = th / D2R
    return float(np.interp(d, CAPE_TH_DEG, [h for h, _ in HEM]))


def hull_drape(th, body, clearance=0.26, flare=0.1, y_end=3.0):
    """The cloth's section at angle th: from the neckline over the body's convex hull (a string over pegs), then hanging
    down with a slight flare. body: (N, 3) design-pose points. Returns a polyline [(rho, y)]."""
    N = neckline(th)
    _, rn = polar(N)
    ang = np.arctan2(body[:, 0], body[:, 2] - TORSO_Z)
    d = np.abs((ang - th + math.pi) % (2 * math.pi) - math.pi)
    sel = body[d < 9 * D2R]
    rho = np.hypot(sel[:, 0], sel[:, 2] - TORSO_Z) + clearance
    pts = [(r, y) for r, y in zip(rho, sel[:, 1]) if y < N[1] + 0.6]
    cur = (rn, N[1]); line = [cur]
    for _ in range(200):
        cand = [(math.atan2(y - cur[1], r - cur[0]), r, y) for r, y in pts if r > cur[0] + 1e-3 and y > y_end]
        if not cand: break
        a, r, y = max(cand)
        cur = (r, y); line.append(cur)
    r0, y0 = line[-1]
    line.append((r0 + flare * (y0 - y_end), y_end))
    return line


def poly_at(line, s):
    L = np.concatenate([[0], np.cumsum([math.hypot(line[i + 1][0] - line[i][0], line[i + 1][1] - line[i][1]) for i in range(len(line) - 1)])])
    s = min(max(s, 0), L[-1])
    k = min(np.searchsorted(L, s, side='right') - 1, len(line) - 2)
    t = (s - L[k]) / max(L[k + 1] - L[k], 1e-9)
    return (line[k][0] * (1 - t) + line[k + 1][0] * t, line[k][1] * (1 - t) + line[k + 1][1] * t), L


def poly_s_at_y(line, y):
    L = np.concatenate([[0], np.cumsum([math.hypot(line[i + 1][0] - line[i][0], line[i + 1][1] - line[i][1]) for i in range(len(line) - 1)])])
    for k in range(len(line) - 1):
        (r0, y0), (r1, y1) = line[k], line[k + 1]
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            return L[k] + (L[k + 1] - L[k]) * (y0 - y) / (y0 - y1)
    return L[-1]


def grid_normals(P):
    """Per-vertex normals of a grid surface from its consistent winding, one sign for the whole grid: pointing away
    from the torso axis on balance (a per-vertex sign test is ambiguous where the cloth lies flat)."""
    R, Cn = P.shape[:2]
    Nn = np.zeros_like(P)
    for i in range(R):
        for j in range(Cn):
            du = P[i, min(j + 1, Cn - 1)] - P[i, max(j - 1, 0)]
            dv = P[min(i + 1, R - 1), j] - P[max(i - 1, 0), j]
            n = np.cross(dv, du)
            Nn[i, j] = n / max(np.linalg.norm(n), 1e-12)
    score = sum(np.dot(Nn[i, j], P[i, j] - np.array([0, P[i, j][1], TORSO_Z])) for i in range(R) for j in range(Cn))
    return Nn if score >= 0 else -Nn


CHAIN_JOINTS = {'L': ('CapeLAN', 'CapeLBN', 'CapeLCN', 'CapeLDN'), 'C': ('CapeAN', 'CapeBN', 'CapeCN', 'CapeDN')}


def chain_weights(chain, y):
    """Linear-blend weights along a hanging chain by height: a vertex between joints k and k+1 is shared by them."""
    names = CHAIN_JOINTS[chain]
    ys = [jpos(n)[1] for n in names]
    if y >= ys[0]: return {names[0]: 1.0}
    if y <= ys[-1]: return {names[-1]: 1.0}
    for k in range(3):
        if ys[k + 1] <= y <= ys[k]:
            t = (ys[k] - y) / (ys[k] - ys[k + 1])
            return {names[k]: 1 - t, names[k + 1]: t}


# The capelet's arm-riding (geno-cannon polish, 2026-09-29: the arms passed through the front panels whenever they rose;
# cape_clip.py measures it over every action). None keeps Gate 2's rule below; a dict rides the panel on the arm by
# distance from the arm in the design pose: the upper arm's share A[row] x (1 - smoothstep(d0, d1, distance from the
# upper arm's axis)), the forearm's F[row] x (1 - smoothstep(f0, f1, distance from the forearm's)), the rest the chains'
# and the torso's as before. Row 0 (the neckline) stays on the torso. Fitted by cape_fit.py against cape_clip.py, over
# every action every third frame (DESIGN changelog 2026-09-29, the polish round): the mid-dome and the dome's end ride the
# upper arm most (rows 1-2), the skirt rows a little of the forearm. Measured on every frame: the panel area the arms
# cut, with an arm raised, fell from 1.27 to 0.36 square units a frame (0.85 from 1.10 over all), with less stretch and
# the idle, walk and run hanging within 0.14 of before (mean vertex move). Static weights also follow an arm that swings
# down and forward, so some arms-down poses cut more (the shield, item swings, the walk; DESIGN has the table).
# GENO_CAPE_GATE2=1 builds Gate 2's rule (an A/B).
CAPE_ARM = None if os.environ.get('GENO_CAPE_GATE2') else dict(
    A=[0, 0.4, 0.8, 0.05, 0.05, 0.05], F=[0, 0.0, 0.0, 0.2, 0.2, 0.0], d0=1.233, d1=2.267, f0=0.6, f1=2.0)


def _seg_dist(p, a, b):
    t = float(np.clip(np.dot(p - a, b - a) / np.dot(b - a, b - a), 0, 1))
    return float(np.linalg.norm(p - (a + t * (b - a)))), t


def _cape_torso_chains(p, row, th):
    """The chains' and the torso's shares of a capelet vertex (cape_weights without the arm)."""
    d = th / D2R
    depth = [0.12, 0.35, 0.72, 0.9, 1.0][row - 1]
    side = float(smoothstep(30, 62, d) * (1 - smoothstep(128, 165, d))) * depth
    centre = float(smoothstep(120, 165, d)) * depth
    tot = side + centre
    if tot > depth: side, centre = side * depth / tot, centre * depth / tot
    w = {}
    for chain, share in (('L', side), ('C', centre)):
        if share <= 1e-4: continue
        for b, x in chain_weights(chain, p[1]).items():
            w[b] = w.get(b, 0) + share * x
    if 1 - side - centre > 1e-6: w['WaistN'] = w.get('WaistN', 0) + 1 - side - centre
    return w


def cape_weights_arm(p, row, th, P):
    if row == 0:
        return {'WaistN': 1.0}
    p = np.asarray(p, float)
    sh, el, ha = DESIGN['LShoulderJ'][3, :3], DESIGN['LArmJ'][3, :3], DESIGN['LHandN'][3, :3]
    du, _ = _seg_dist(p, sh, el)
    df, tf = _seg_dist(p, el, ha)
    wa = P['A'][row] * (1 - float(smoothstep(P['d0'], P['d1'], du)))
    wf = P['F'][row] * (1 - float(smoothstep(P['f0'], P['f1'], df))) * (tf > 0.02)
    wf = min(wf, 1 - wa)
    w = {b: x * (1 - wa - wf) for b, x in _cape_torso_chains(p, row, th).items()}
    if wa > 1e-4: w['LShoulderJ'] = w.get('LShoulderJ', 0) + wa
    if wf > 1e-4: w['LArmJ'] = w.get('LArmJ', 0) + wf
    items = sorted(w.items(), key=lambda kv: -kv[1])[:3]
    items = [(b, x) for k, (b, x) in enumerate(items) if x > (0.02 if k < 2 else 0.1)]
    tot = sum(x for _, x in items)
    return {b: x / tot for b, x in items}


def cape_weights(p, row, th):
    if CAPE_ARM is not None:
        return cape_weights_arm(p, row, th, CAPE_ARM)
    return cape_weights_gate2(p, row, th)


def cape_weights_gate2(p, row, th):
    """Skin weights for a capelet vertex (design pose, left half). The neckline rides the torso; the side chain drives
    the front and side panels, the centre chain the back; the dome over the shoulder shares the arm so a raised arm
    lifts it. At most 3 influences."""
    if row == 0:
        return {'WaistN': 1.0}
    d = th / D2R
    _, rho = polar(p)
    # the panel over the upper arm rides the arm (Gate 2: a raised arm showed through the front panels in the forward
    # tilt, up tilt and smash wind-ups): the arm and one other bone, the nearest chain joint (or the torso on the dome)
    # (the front panel's inner edge, the part in front of the upper arm; the side panels stay on the chains)
    arm = float(1 - smoothstep(58, 86, d)) * [0.45, 0.62, 0.6, 0.5, 0.38][row - 1]
    if arm > 0.05:
        if row <= 1:
            other = 'WaistN'
        else:
            cw = chain_weights('L', p[1])
            other = max(cw, key=cw.get)
        return {'LShoulderJ': arm, other: 1 - arm}
    depth = [0.12, 0.35, 0.72, 0.9, 1.0][row - 1]      # the chains take over below the shoulder dome
    side = float(smoothstep(30, 62, d) * (1 - smoothstep(128, 165, d))) * depth
    centre = float(smoothstep(120, 165, d)) * depth
    tot = side + centre
    if tot > depth: side, centre = side * depth / tot, centre * depth / tot
    w = {}
    for chain, share in (('L', side), ('C', centre)):
        if share <= 1e-4: continue
        for b, x in chain_weights(chain, p[1]).items():
            w[b] = w.get(b, 0) + share * x
    rest = 1 - side - centre
    if rest > 1e-6:
        bump = float(smoothstep(48, 70, d) * (1 - smoothstep(112, 132, d)))
        wa = bump * float(smoothstep(1.6, 2.4, rho)) * 0.9
        if wa > 1e-6: w['LShoulderJ'] = rest * wa
        if rest * (1 - wa) > 1e-6: w['WaistN'] = w.get('WaistN', 0) + rest * (1 - wa)
    items = sorted(w.items(), key=lambda kv: -kv[1])[:3]
    items = [(b, x) for k, (b, x) in enumerate(items) if x > (0.02 if k < 2 else 0.15)]
    tot = sum(x for _, x in items)
    return {b: x / tot for b, x in items}


def design_body_points(meshes):
    """Every body-mesh vertex (single-bone parts) in the design pose."""
    S = skin_mats(REST, DESIGN)
    pts = []
    for m in meshes:
        if m.name.startswith(('chest', 'pelvis', 'balls_arms', 'upperarm_L', 'forearm_L', 'palm_L', 'upperarm_R', 'forearm_R', 'palm_R')):
            q = skin_points(np.array(m.V), m.W, S)
            if m.name.startswith(('forearm', 'palm')):
                # room for a bent elbow: inflate the forearm and hand away from their bone axis
                j = next(iter(m.W[0]))
                o = jpos(j, DESIGN); ax = DESIGN[j][0, :3]
                rad = q - o - np.outer((q - o) @ ax, ax)
                q = q + 0.22 * rad / np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), 1e-9)
            pts.append(q)
    # the cloth rides over the shoulders: an inflated ball at each shoulder joint keeps it clear of the arm's pivot
    sph = []
    for i in range(10):
        for k in range(20):
            ph = math.pi * (i + 0.5) / 10 - math.pi / 2; th = 2 * math.pi * k / 20
            sph.append((math.cos(ph) * math.cos(th), math.sin(ph), math.cos(ph) * math.sin(th)))
    sph = np.array(sph)
    for side in ('L', 'R'):
        pts.append(jpos(f'{side}ShoulderJ', DESIGN) + 0.78 * sph)
    return np.concatenate(pts)


def hull2d(P):
    """Convex hull of 2D points (Andrew's monotone chain), counter-clockwise."""
    P = sorted(set(map(tuple, np.round(P, 5))))
    if len(P) < 3: return np.array(P)
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0: hi.pop()
        hi.append(p)
    return np.array(lo[:-1] + hi[:-1])


def hull_radius(H, th):
    """Distance from the torso axis to the boundary of hull H (x, z-TORSO_Z) along angle th (0 = +Z, 90 = +X)."""
    d = np.array([math.sin(th), math.cos(th)])
    best = 0.0
    for a, b in zip(H, np.roll(H, -1, axis=0)):
        e = b - a
        den = d[0] * (-e[1]) - d[1] * (-e[0])
        if abs(den) < 1e-12: continue
        t = (a[0] * (-e[1]) - a[1] * (-e[0])) / den          # ray parameter
        u = (d[0] * a[1] - d[1] * a[0]) / den                # edge parameter
        if t > 0 and -1e-6 <= u <= 1 + 1e-6: best = max(best, t)
    return best


def bell_out(Pd, body, clearance=0.32, rows=None):
    """Make each cloth row wrap the body like a bell: a point is pushed out to the convex hull of the body's
    cross-section around its height (arms included), so the front panels pass in front of the hanging arms."""
    rel = np.stack([body[:, 0], body[:, 2] - TORSO_Z], 1)
    out = Pd.copy()
    for i in (rows or range(1, Pd.shape[0])):
        for j in range(Pd.shape[1]):
            p = Pd[i, j]
            sl = rel[np.abs(body[:, 1] - p[1]) < 0.55]
            sl = np.concatenate([sl, sl * np.array([-1, 1])])     # both arms: the hull of the whole slice
            if len(sl) < 3: continue
            H = hull2d(sl)
            th, rho = polar(p)
            need = hull_radius(H, th) + clearance
            if rho < need: out[i, j] = from_polar(th, need, p[1])
    return out


def smooth_drape(line, body, th, d_min=0.16, iters=10):
    """Round the string-over-pegs drape into a smooth cloth curve: resample, then alternate Laplacian smoothing (which
    rounds the corner over the shoulder into a dome) with pushing any point closer than d_min to a body point back out
    along the curve's normal. The neckline end and the hanging end stay put."""
    ang = np.arctan2(body[:, 0], body[:, 2] - TORSO_Z)
    dd = np.abs((ang - th + math.pi) % (2 * math.pi) - math.pi)
    sl = body[dd < 10 * D2R]
    B = np.stack([np.hypot(sl[:, 0], sl[:, 2] - TORSO_Z), sl[:, 1]], 1)
    L = np.array(line, float)
    seg = np.hypot(*np.diff(L, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(24, int(s[-1] / 0.15))
    ss = np.linspace(0, s[-1], n)
    P = np.stack([np.interp(ss, s, L[:, 0]), np.interp(ss, s, L[:, 1])], 1)
    for _ in range(iters):
        for _ in range(8):
            P[1:-1] = 0.25 * P[:-2] + 0.5 * P[1:-1] + 0.25 * P[2:]
        if len(B):
            for k in range(1, len(P)):
                d = np.hypot(*(B - P[k]).T)
                i = int(np.argmin(d))
                if d[i] < d_min:
                    t = P[min(k + 1, len(P) - 1)] - P[k - 1]
                    nrm = np.array([t[1], -t[0]]); nrm /= max(np.linalg.norm(nrm), 1e-9)
                    if np.dot(nrm, P[k] - B[i]) < 0: nrm = -nrm
                    P[k] = P[k] + nrm * (d_min - d[i])
    return [tuple(p) for p in P]


_DRAPE = {}


def drape_line(th, body):
    key = (round(th, 5), id(body))
    if key not in _DRAPE:
        _DRAPE[key] = smooth_drape(hull_drape(th, body, clearance=0.18, flare=cape_flare(th)), body, th)
    return _DRAPE[key]


def dome_end(line):
    """Arc length where the drape turns steeper than 55 degrees downward (the end of the shoulder dome)."""
    L = np.array(line); seg = np.diff(L, axis=0); s = np.concatenate([[0], np.cumsum(np.hypot(*seg.T))])
    for k, (dr, dy) in enumerate(seg):
        if dy < 0 and math.atan2(-dy, max(dr, 1e-9)) > 55 * D2R and L[k][1] < L[0][1] + 0.4:
            return s[k]
    return s[-1] * 0.3


def cape_flare(th):
    d = th / D2R
    return 0.24 + 0.2 * float(smoothstep(50, 78, d) * (1 - smoothstep(118, 145, d))) + 0.06 * float(smoothstep(120, 170, d))


def cape_meshes(body_design):
    """Returns (outer_L, outer_R, inner_L, inner_R) meshes, the design-pose outer grid and its normals."""
    R = 6                                   # neckline, mid-dome, dome end, two skirt rows, hem
    Pd = np.zeros((R, CAPE_COLS, 3)); Wt = [[None] * CAPE_COLS for _ in range(R)]; S_arc = np.zeros((R, CAPE_COLS))
    TH = np.zeros((R, CAPE_COLS))
    for j, th0 in enumerate(CAPE_TH):
        base, zig = HEM[j]
        hem_y = base + zig
        line0 = drape_line(th0, body_design)
        s_hem0 = poly_s_at_y(line0, hem_y)
        sd = min(max(dome_end(line0), 0.2 * s_hem0), 0.5 * s_hem0)
        fr = [0.0, 0.5 * sd / s_hem0, sd / s_hem0, (sd + 0.36 * (s_hem0 - sd)) / s_hem0, (sd + 0.7 * (s_hem0 - sd)) / s_hem0, 1.0]
        th_hem = (CAPE_HEM_FRONT + (CAPE_TH_DEG[j] - CAPE_TH_DEG[0]) * (180 - CAPE_HEM_FRONT) / (180 - CAPE_TH_DEG[0])) * D2R
        for i in range(R):
            th = th0 + (th_hem - th0) * (i / (R - 1)) ** 1.5
            TH[i, j] = th
            line = drape_line(th, body_design) if abs(th - th0) > 1e-4 else line0
            s_hem = poly_s_at_y(line, hem_y)
            (rho, y), _ = poly_at(line, fr[i] * s_hem)
            Pd[i, j] = from_polar(th, rho, y)
            S_arc[i, j] = fr[i] * s_hem
    # round every row in plan view: push out to the body's cross-section hull (the arms included), then smooth the
    # radius across the columns and push out again, so the bell is convex with no corner where the panels meet the sides
    for _ in range(3):
        Pd = bell_out(Pd, body_design, rows=range(3, R))       # the skirt rows wrap the arms; the dome keeps its drape
        for i in range(2, R):
            rho = np.array([polar(Pd[i, j])[1] for j in range(CAPE_COLS)])
            ext = np.concatenate([[rho[1]], rho, [rho[-2]]])            # mirror at the back centre and the front edge
            sm = 0.25 * ext[:-2] + 0.5 * ext[1:-1] + 0.25 * ext[2:]
            for j in range(1, CAPE_COLS):
                th, r0 = polar(Pd[i, j])
                Pd[i, j] = from_polar(th, max(r0, sm[j]), Pd[i, j][1])
    # the hem flares a little further out than the row above it (a bell, not a tube)
    for j in range(CAPE_COLS):
        for i in (R - 2, R - 1):
            th, rho = polar(Pd[i, j]); _, rho_up = polar(Pd[i - 1, j])
            drop = Pd[i - 1, j][1] - Pd[i, j][1]
            Pd[i, j] = from_polar(th, max(rho, rho_up + (0.18 if i == R - 2 else 0.26) * drop), Pd[i, j][1])
    for i in range(R):
        for j in range(CAPE_COLS):
            Wt[i][j] = cape_weights(Pd[i, j], i, TH[i, j])
    Smax = S_arc.max()
    Nd = grid_normals(Pd)
    S = skin_mats(REST, DESIGN)
    out = []
    for layer in (0, 1):
        P = Pd.copy()
        if layer == 1:
            for i in range(R):
                for j in range(CAPE_COLS):
                    if i == R - 1 or j == 0: continue
                    P[i, j] = P[i, j] - Nd[i, j] * 0.035
        flat = P.reshape(-1, 3); wflat = [Wt[i][j] for i in range(R) for j in range(CAPE_COLS)]
        Pr = unskin_points(flat, wflat, S).reshape(P.shape)
        UV = np.zeros((R, CAPE_COLS, 2))
        for i in range(R):
            for j in range(CAPE_COLS):
                UV[i, j] = (j / (CAPE_COLS - 1), S_arc[i, j] / Smax)
        m = Mesh('cape_out_L' if layer == 0 else 'cape_in_L', 'cape' if layer == 0 else 'lining', 'cape', spec=False)
        m.grid(Pr, UV, Wt, attr={'design': [[tuple(P[i, j]) for j in range(CAPE_COLS)] for i in range(R)]})
        Dv = np.array(m.attr['design'])
        score = 0.0
        for f in m.F:
            p = Dv[list(f)]; c = p.mean(0)
            nrm = np.cross(p[1] - p[0], p[2] - p[0])
            th, _ = polar(c)
            score += np.dot(nrm, np.array([math.sin(th), 0.3, math.cos(th)]))
        if score * (1 if layer == 0 else -1) < 0:
            m.F = [f[::-1] for f in m.F]
        m.sharp = 75
        r = Mesh(m.name.replace('_L', '_R'), m.tex, 'cape', spec=False)
        for p, uv, w, dp in zip(m.V, m.UV, m.W, m.attr['design']):
            q = p.copy(); q[0] = -q[0]
            r.add(q, uv, mirror_weights(w), design=(-dp[0], dp[1], dp[2]))
        r.F = [f[::-1] for f in m.F]
        r.sharp = m.sharp
        out += [m, r]
    return out, Pd, Nd


def cape_joint_targets(Pd, Nd):
    """Where the added cape joints should sit: on the cape's centre and side-chain lines, just inside the outer layer,
    at the chain heights (10.1 for the first joint, then CHAIN_Y)."""
    def col_at(th):
        d = th / D2R
        j0 = max(k for k in range(CAPE_COLS - 1) if CAPE_TH_DEG[k] <= d); t = (d - CAPE_TH_DEG[j0]) / (CAPE_TH_DEG[j0 + 1] - CAPE_TH_DEG[j0])
        return Pd[:, j0] * (1 - t) + Pd[:, j0 + 1] * t, Nd[:, j0] * (1 - t) + Nd[:, j0 + 1] * t
    def at_y(col, ncol, y):
        for k in range(len(col) - 1):
            if (col[k][1] - y) * (col[k + 1][1] - y) <= 0:
                t = (col[k][1] - y) / (col[k][1] - col[k + 1][1])
                return col[k] + (col[k + 1] - col[k]) * t, ncol[k] + (ncol[k + 1] - ncol[k]) * t
        return col[-1], ncol[-1]
    out = {}
    col, ncol = col_at(SIDE_CHAIN_TH)
    for name, y in zip(('CapeLAN', 'CapeLBN', 'CapeLCN', 'CapeLDN'), SIDE_CHAIN_Y):
        p, n = at_y(col, ncol, y); out[name] = p - n * 0.06
    col, ncol = Pd[:, -1], Nd[:, -1]
    p, n = at_y(col, ncol, CHAIN_Y[2]); out['CapeDN'] = p - n * 0.06
    return {k: tuple(round(float(x), 3) for x in v) for k, v in out.items()}


def clasp_mesh(Pd=None, Nd=None):
    """Two brass eyelets set flat in the cape's front panels just under the collar, and the short twisted gold rope
    threaded through them, sagging in a small U."""
    m = Mesh('clasp', 'clasp', 'torso', spc=(255, 240, 200))
    g = []
    for side in (1, -1):
        # on the outer panel near its inner edge, just under the collar (the grid's first two rows and columns)
        t = 0.45
        p = (1 - t) * Pd[0, 0] + t * Pd[1, 0]; q = (1 - t) * Pd[0, 1] + t * Pd[1, 1]
        c = 0.72 * p + 0.28 * q
        nrm = 0.72 * ((1 - t) * Nd[0, 0] + t * Nd[1, 0]) + 0.28 * ((1 - t) * Nd[0, 1] + t * Nd[1, 1])
        nrm /= np.linalg.norm(nrm)
        if side < 0:
            c = c * np.array([-1, 1, 1]); nrm = nrm * np.array([-1, 1, 1])
        c = c + nrm * 0.03
        ref = np.cross(nrm, [0, 1, 0]); ref /= np.linalg.norm(ref)
        prof = [(0.0, 0.08), (0.045, 0.155), (0.0, 0.225)]          # a low rolled ring, flat in the cloth
        f0 = len(m.F)
        lathe([(x, r) for x, r in prof], 8, (c, nrm, ref), {"WaistN": 1.0}, m, uv_rect=(0, 0.54, 1, 1))
        V = np.array(m.V)
        for k in range(f0, len(m.F)):
            f = m.F[k]; pp = V[list(f)]
            if np.dot(np.cross(pp[1] - pp[0], pp[2] - pp[0]), nrm) < 0: m.F[k] = f[::-1]
        g.append((c, nrm))
    (a, na), (b, nb) = g
    nseg, nsides, rr = 8, 5, 0.14
    pts = []
    for k in range(nseg + 1):
        t = k / nseg
        p = a * (1 - t) + b * t
        sag = 4 * t * (1 - t)
        p = p + np.array([0, -0.3 * sag, 0.1 * sag])
        pts.append(p)
    pts[0] = pts[0] - na * 0.1; pts[-1] = pts[-1] - nb * 0.1            # threaded through the eyelets
    P = np.zeros((nseg + 1, nsides + 1, 3)); UV = np.zeros((nseg + 1, nsides + 1, 2))
    for k, p in enumerate(pts):
        tng = pts[min(k + 1, nseg)] - pts[max(k - 1, 0)]; tng /= np.linalg.norm(tng)
        e1 = np.cross(tng, [0, 0, 1.0]); e1 /= np.linalg.norm(e1); e2 = np.cross(tng, e1)
        for s_ in range(nsides + 1):
            a_ = 2 * math.pi * s_ / nsides
            P[k, s_] = p + rr * (math.cos(a_) * e1 + math.sin(a_) * e2)
            UV[k, s_] = (s_ / nsides, 0.44 * k / nseg)
    f0 = len(m.F)
    m.grid(P, UV, {'WaistN': 1.0})
    V = np.array(m.V)
    for k in range(f0, len(m.F)):
        f = m.F[k]; p = V[list(f)]; c = p.mean(0)
        kk = int(np.argmin([np.linalg.norm(c - q) for q in pts]))
        if np.dot(np.cross(p[1] - p[0], p[2] - p[0]), c - pts[kk]) < 0: m.F[k] = f[::-1]
    return m


# ---------------------------------------------------------------------------------------------------------------------
def build():
    """All high-model meshes in the rest pose."""
    body = torso_meshes() + joints_meshes() + limb_meshes() + hand_meshes()
    bd = design_body_points(body)
    capes, Pd, Nd = cape_meshes(bd)
    meshes = head_meshes() + eye_meshes() + [ears_nose_mesh(), nose_mesh()] + cap_meshes() + [emblem_mesh(), curls_mesh()] \
        + body + collar_meshes() + [clasp_mesh(Pd, Nd)] + capes + boot_meshes()
    for m in meshes:
        assert np.isfinite(np.array(m.V)).all(), f'{m.name}: non-finite vertices'
    return meshes


def build_all():
    """The default visible model, the weapon-form variants (geno_forms), which the move scripts show in place of
    the hands (only one form per hand at a time), and Geno Flash's cannon (geno_cannon), shown in place of the whole
    body (the body group's option 1)."""
    import geno_forms, geno_cannon
    base = build()
    return base + geno_forms.build(base) + geno_cannon.build()


REGIONS = ['head', 'torso', 'cape', 'arms', 'hands', 'legs']
BUDGET = {'head': 1400, 'torso': 900, 'cape': 400, 'arms': 550, 'hands': 750, 'legs': 850}


def bone_region(b):
    if b in ('HeadN',) or b.startswith('Cap') and not b.startswith('Cape'): return 'head'
    if b.startswith('Cape'): return 'cape'
    if b in ('WaistN', 'NeckN', 'HipN', 'TopN', 'TransN', 'XRotN', 'YRotN'): return 'torso'
    if any(k in b for k in ('1st', '2nd', '3rd', '4th', 'Thumb', 'HandN')): return 'hands'
    if any(k in b for k in ('Shoulder', 'ArmJ')): return 'arms'
    return 'legs'


def region_tris(meshes):
    tot = {r: 0 for r in REGIONS}
    for m in meshes:
        for f in m.F:
            acc = {}
            for v in f:
                for b, x in m.W[v].items(): acc[b] = acc.get(b, 0) + x
            n = len(f) - 2
            tot[bone_region(max(acc, key=acc.get))] += n
    return tot


def stats(meshes):
    lines = []
    tot = region_tris(meshes)
    for r in REGIONS:
        lines.append(f'{r:6s} {tot[r]:5d}  (budget ~{BUDGET[r]})')
    lines.append(f'TOTAL  {sum(tot.values()):5d}  meshes {len(meshes)}  verts {sum(len(np.unique(np.round(np.array(m.V), 5), axis=0)) for m in meshes)}')
    for m in meshes:
        b = m.bones()
        infl = [len([x for x in w.values() if x > 1e-6]) for w in m.W]
        lines.append(f'  {m.name:14s} {m.tex:10s} {m.region:6s} tris {m.tris():4d}  bones {len(b):2d}  max infl {max(infl)}')
    return '\n'.join(lines)


if __name__ == '__main__':
    M = build()
    print(stats(M))
