"""geno_forms.py: Geno's weapon forms (Gate 2): the hand and forearm variants the move scripts switch between.

Each form is a small mesh on the arm's own joints, built for the left arm in the rest T-pose (the arm along +X, palm
down, thumb forward) and mirrored for the right. They share one texture atlas ('forms', 128x128; paint.py paint_forms):

    u 0-1,   v 0-0.5    wood (the cannon's staves, the finger-shot tubes)
    u 0-0.5, v 0.5-0.75 steel (the gun and beam barrels)      u 0.5-1, v 0.5-0.75  brass (rings, collars, eyelets)
    u 0-0.5, v 0.75-1   the bore (dark, a few stars)           u 0.5-1, v 0.75-1    gold (the star gun's star)

The forms (ART.md "Weapon forms"; Michael's references: cannon_c.png, ref_beam.png, ref_fingergun.png, weapons_snes.png):
    fshot   Finger Shot: every finger and the thumb a short hollow wooden tube, splayed a little (replaces the fingers)
    gun     Hand Gun: a slim steel barrel from the knuckles, a brass ring at its base (with the fist pose)
    stargun Star Gun: the same barrel with a gold star at the muzzle
    cannon  Hand Cannon: the forearm and hand folded open into a barrel of wooden staves, a brass muzzle ring and a dark
            bore (replaces the forearm, the palm and the fingers; rigid on ArmJ)
    beam    Geno Beam: the hand gives way to a steel barrel with a brass collar and a starry bore (replaces the palm and
            the fingers; on HandN, so the wrist aims it)
    rocket  Rocket fist: a brass exhaust ring behind the fist (on HandN) and a brass socket at the forearm's end (on ArmJ);
            the launch itself is HandN's translation in the animation
"""
import math
import numpy as np
import geno_geo as G
from geno_geo import Mesh, lathe, D2R

WOOD = (0.0, 0.0, 1.0, 0.5)
STEEL = (0.0, 0.5, 0.5, 0.75)
BRASS = (0.5, 0.5, 1.0, 0.75)
BORE = (0.0, 0.75, 0.5, 1.0)
GOLD = (0.5, 0.75, 1.0, 1.0)


def frame_of(joint, ref=(0, 1, 0)):
    W = G.REST[joint]
    return W[3, :3].copy(), W[0, :3].copy(), np.asarray(ref, float)


def ring(m, joint, prof, n, rect, inward=False, axis=None, origin=None, ref=(0, 1, 0), wmap=None):
    """A lathe piece on a joint (profile (x along the axis, radius) in the joint's frame), faces outward from the axis
    (or inward, for a bore's wall)."""
    o, ax, rf = frame_of(joint, ref)
    if axis is not None: ax = np.asarray(axis, float) / np.linalg.norm(axis)
    if origin is not None: o = np.asarray(origin, float)
    f0 = len(m.F); v0 = len(m.V)
    lathe(prof, n, (o, ax, np.asarray(rf, float)), wmap or {joint: 1.0}, m, uv_rect=rect)
    V = np.array(m.V)
    for k in range(f0, len(m.F)):
        f = m.F[k]; p = V[list(f)]; c = p.mean(0)
        axial = o + ax * np.dot(c - o, ax)
        nrm = np.cross(p[1] - p[0], p[2] - p[0])
        if len(f) == 4: nrm = nrm + np.cross(p[2] - p[0], p[3] - p[0])
        radial = c - axial
        if np.linalg.norm(radial) < 1e-6:                   # a disc: face along the axis
            want = -1 if inward else 1
            if np.dot(nrm, ax) * want < 0: m.F[k] = f[::-1]
            continue
        if (np.dot(nrm, radial) < 0) != inward: m.F[k] = f[::-1]
    return v0


def disc(m, joint, x, r, n, rect, face=1, axis=None, origin=None, ref=(0, 1, 0)):
    """A flat disc across the axis at x, facing +axis (face=1) or -axis."""
    o, ax, rf = frame_of(joint, ref)
    if axis is not None: ax = np.asarray(axis, float) / np.linalg.norm(axis)
    if origin is not None: o = np.asarray(origin, float)
    rf = rf - ax * np.dot(rf, ax); rf /= np.linalg.norm(rf); sd = np.cross(ax, rf)
    c = m.add(o + ax * x, ((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2), {joint: 1.0})
    ids = []
    for j in range(n):
        a = 2 * math.pi * j / n
        p = o + ax * x + r * (math.cos(a) * rf + math.sin(a) * sd)
        ids.append(m.add(p, ((rect[0] + rect[2]) / 2 + (rect[2] - rect[0]) / 2 * 0.9 * math.cos(a),
                             (rect[1] + rect[3]) / 2 + (rect[3] - rect[1]) / 2 * 0.9 * math.sin(a)), {joint: 1.0}))
    for j in range(n):
        f = (c, ids[j], ids[(j + 1) % n])
        p = np.array([m.V[i] for i in f])
        nrm = np.cross(p[1] - p[0], p[2] - p[0])
        m.face(*(f if np.dot(nrm, ax) * face >= 0 else f[::-1]))


# ---------------------------------------------------------------------------------------------------------------------
def fshot(side='L'):
    """Finger Shot: the fingers and the thumb become short hollow wooden tubes, straight out and fanned a little, rigid on
    the hand (so any hand pose shows them the same way; the fingers themselves are hidden)."""
    m = Mesh(f'fshot_{side}', 'forms', 'hands')
    W = G.REST['LHandN']; o0, X = W[3, :3], W[0, :3]
    fw = np.array([0, 0, 1.0]); up = np.array([0, 1.0, 0])
    specs = [(0.34, 0.02, 12, 0.92), (0.12, 0.05, 4, 1.0), (-0.12, 0.05, -4, 0.96), (-0.34, 0.02, -12, 0.84)]
    for z, y, fan, L in specs:                           # the four fingers from the knuckles
        o = o0 + X * 0.7 + fw * z + up * y
        ax = X * math.cos(fan * D2R) + fw * math.sin(fan * D2R)
        tube(m, o, ax, L, 0.19, 0.12)
    o = o0 + X * 0.36 + fw * 0.5 - up * 0.02            # the thumb, out to the side and forward
    ax = X * math.cos(40 * D2R) + fw * math.sin(40 * D2R)
    tube(m, o, ax, 0.62, 0.2, 0.13)
    return m


def tube(m, o, ax, L, ro, ri, joint='LHandN'):
    ax = ax / np.linalg.norm(ax)
    ring(m, joint, [(0.0, ro * 0.92), (L, ro)], 6, (0.0, 0.0, 1.0, 0.45), axis=ax, origin=o)          # the wood
    ring(m, joint, [(L, ro), (L + 0.005, ri)], 6, (0.0, 0.45, 1.0, 0.5), axis=ax, origin=o)          # the rim
    ring(m, joint, [(L + 0.005, ri), (L - 0.3, ri * 0.95)], 6, BORE, inward=True, axis=ax, origin=o)  # the bore


def barrel(m, joint, x0, L, r, rim_brass=True, n=8):
    """A slim steel barrel along the joint's X from x0: a brass base ring, the barrel, a rim and a dark bore."""
    o, ax, rf = frame_of(joint)
    up = G.REST[joint][1, :3]
    ring(m, joint, [(x0 - 0.06, r * 1.75), (x0 + 0.1, r * 1.75), (x0 + 0.16, r * 1.2)], n, BRASS)
    ring(m, joint, [(x0 + 0.1, r), (x0 + L, r)], n, STEEL)
    ring(m, joint, [(x0 + L, r * 1.18), (x0 + L + 0.1, r * 1.18), (x0 + L + 0.12, r * 0.7)], n,
         BRASS if rim_brass else STEEL)
    ring(m, joint, [(x0 + L + 0.12, r * 0.7), (x0 + L - 0.15, r * 0.66), (x0 + L - 0.16, 0.0)], n, BORE, inward=True)


def gun(side='L'):
    m = Mesh(f'gun_{side}', 'forms', 'hands')
    barrel(m, 'LHandN', 0.72, 1.9, 0.19)
    return m


def star_points(R, r, k=5):
    return [((R if i % 2 == 0 else r) * math.cos(math.pi / 2 + i * math.pi / k), (R if i % 2 == 0 else r) * math.sin(math.pi / 2 + i * math.pi / k))
            for i in range(2 * k)]


def stargun(side='L'):
    """The Star Gun: the slim barrel, crowned with a flat five-pointed gold star facing forward."""
    m = Mesh(f'stargun_{side}', 'forms', 'hands')
    barrel(m, 'LHandN', 0.72, 1.6, 0.19)
    o, ax, _ = frame_of('LHandN')
    up, fw = np.array([0, 1.0, 0]), np.array([0, 0, 1.0])
    x = 0.72 + 1.6 + 0.14
    pts = star_points(0.6, 0.26)
    for depth, face in ((0.0, 1), (-0.1, -1)):
        c = m.add(o + ax * (x + depth + 0.02 * face), (0.75, 0.875), {'LHandN': 1.0})
        ids = [m.add(o + ax * (x + depth) + up * py + fw * px, (0.75 + 0.2 * px / 0.6, 0.875 - 0.1 * py / 0.6), {'LHandN': 1.0})
               for px, py in pts]
        for j in range(len(ids)):
            f = (c, ids[j], ids[(j + 1) % len(ids)])
            p = np.array([m.V[i] for i in f]); nrm = np.cross(p[1] - p[0], p[2] - p[0])
            m.face(*(f if np.dot(nrm, ax) * face >= 0 else f[::-1]))
    # the star's edge
    n = len(pts)
    for j in range(n):
        a, b = pts[j], pts[(j + 1) % n]
        q = [o + ax * x + up * a[1] + fw * a[0], o + ax * x + up * b[1] + fw * b[0],
             o + ax * (x - 0.1) + up * b[1] + fw * b[0], o + ax * (x - 0.1) + up * a[1] + fw * a[0]]
        ids = [m.add(p, (0.62 + 0.05 * (k % 2), 0.8 + 0.05 * (k // 2)), {'LHandN': 1.0}) for k, p in enumerate(q)]
        p = np.array(q); nrm = np.cross(p[1] - p[0], p[2] - p[0])
        mid = (np.array(a) + np.array(b)) / 2
        out = up * mid[1] + fw * mid[0]
        m.face(*(ids if np.dot(nrm, out) >= 0 else ids[::-1]))
    return m


def cannon(side='L'):
    """The Hand Cannon: eight wooden staves round the forearm, flaring open at the elbow like the petals of a bud,
    widening to a brass muzzle ring past the hand, a dark bore inside. Rigid on ArmJ."""
    m = Mesh(f'cannon_{side}', 'forms', 'arms')
    j = 'LArmJ'
    n = 8
    ring(m, j, [(0.32, 0.72), (0.5, 0.84), (1.6, 0.9), (2.62, 0.95)], n, (0.0, 0.0, 1.0, 0.42))    # the staves
    ring(m, j, [(2.55, 0.97), (2.6, 1.08), (2.95, 1.1), (3.02, 1.02), (3.04, 0.8)], n, BRASS)      # the muzzle ring
    ring(m, j, [(3.04, 0.8), (2.5, 0.76), (2.48, 0.0)], n, BORE, inward=True)                       # the bore
    # four petals folded open over the elbow (the staves' back ends, curling out)
    o, ax, _ = frame_of(j)
    up, fw = np.array([0, 1.0, 0]), np.array([0, 0, 1.0])
    for k in range(4):
        a = (45 + 90 * k) * D2R
        rd = math.cos(a) * up + math.sin(a) * fw
        tg = np.cross(ax, rd)
        q = [o + ax * 0.62 + rd * 0.86 + tg * 0.36, o + ax * 0.62 + rd * 0.86 - tg * 0.36,
             o + ax * 0.12 + rd * 1.08 - tg * 0.26, o + ax * 0.12 + rd * 1.08 + tg * 0.26]
        for layer in (1, -1):
            ids = [m.add(p + rd * 0.02 * layer, (0.1 + 0.2 * (i in (1, 2)), 0.42 + 0.06 * (i >= 2)), {j: 1.0})
                   for i, p in enumerate(q)]
            p = np.array(q); nrm = np.cross(p[1] - p[0], p[2] - p[0])
            m.face(*(ids if np.dot(nrm, rd) * layer >= 0 else ids[::-1]))
    return m


def beam(side='L'):
    """The Geno Beam: a brass collar at the wrist, a steel barrel and a starry bore, on HandN."""
    m = Mesh(f'beam_{side}', 'forms', 'hands')
    j = 'LHandN'
    n = 10
    ring(m, j, [(-0.28, 0.5), (-0.18, 0.62), (0.26, 0.62), (0.34, 0.5)], n, BRASS)           # the collar over the wrist
    ring(m, j, [(0.3, 0.4), (1.55, 0.4)], n, STEEL)                                          # the barrel
    ring(m, j, [(1.55, 0.4), (1.6, 0.47), (1.74, 0.47), (1.78, 0.33)], n, STEEL)             # the muzzle
    ring(m, j, [(1.78, 0.33), (1.5, 0.32)], n, BORE, inward=True)                           # the bore's wall
    disc(m, j, 1.5, 0.32, n, BORE, face=1)                                                   # its starry floor
    return m


def rocket(side='L'):
    """The Rocket fist: a brass exhaust ring behind the fist (HandN) and a brass socket at the forearm's end (ArmJ)."""
    m = Mesh(f'rocket_{side}', 'forms', 'hands')
    ring(m, 'LHandN', [(-0.3, 0.3), (-0.26, 0.46), (0.02, 0.5), (0.1, 0.44)], 8, BRASS)
    disc(m, 'LHandN', -0.3, 0.3, 8, BORE, face=-1)
    ring(m, 'LArmJ', [(1.5, 0.74), (1.56, 0.8), (1.86, 0.8), (1.9, 0.56)], 8, BRASS)
    disc(m, 'LArmJ', 1.88, 0.56, 8, BORE, face=1)
    return m


# ---- the swap interface (ART.md "Weapon forms: the interface"). The engine shows one option per visibility group, and
# an option's meshes must not appear in another option of the group (ftParts_80074B6C hides every other option's DObjs
# after showing the chosen one). So each hand has two groups: its base meshes at four levels (spare copies of the forearm
# and palm where a level keeps them), and the form's own mesh.
import rig  # noqa: E402  (the interface: rig.FORMS, FORM_GROUPS, FORM_ARM, PART, HAND_POSE, CAP_POSE)
FORMS = rig.FORMS
BUILD = {'fshot': fshot, 'gun': gun, 'stargun': stargun, 'cannon': cannon, 'beam': beam, 'rocket': rocket}
ARM_LEVELS = [('forearm', 'palm', 'fingers'), ('forearm', 'palm'), ('forearm',), ()]    # the arm group's options
GROUPS = rig.FORM_GROUPS
form_commands = rig.form_commands


def mirror(m):
    r = Mesh(m.name[:-2] + '_R', m.tex, m.region, spec=m.spec, spc=m.spc)
    r.sharp = m.sharp
    for p, uv, w in zip(m.V, m.UV, m.W):
        q = np.array(p, float).copy(); q[0] = -q[0]
        r.add(q, uv, G.mirror_weights(w))
    r.F = [f[::-1] for f in m.F]
    return r


def copy_mesh(m, name):
    c = Mesh(name, m.tex, m.region, spec=m.spec, double=m.double, spc=m.spc)
    c.V, c.UV, c.W, c.F = [np.array(v, float) for v in m.V], list(m.UV), [dict(w) for w in m.W], list(m.F)
    c.sharp = m.sharp
    return c


def build(base=None):
    """The form meshes, plus the spare copies of the base meshes the arm group's levels need. base: the default model's
    meshes (geno_geo.build()), whose arm meshes are put in the arm groups here."""
    out = []
    for name in FORMS[1:]:
        m = BUILD[name]('L')
        m.sharp = 50
        for mm in (m, mirror(m)):
            mm.group, mm.option = GROUPS[mm.name[-1]][1], FORMS.index(name)
            out.append(mm)
    if base is not None:
        byname = {m.name: m for m in base}
        for side in 'LR':
            arm = GROUPS[side][0]
            for part in ARM_LEVELS[0]:
                byname[f'{part}_{side}'].group, byname[f'{part}_{side}'].option = arm, 0
            for lvl in (1, 2):
                for part in ARM_LEVELS[lvl]:
                    c = copy_mesh(byname[f'{part}_{side}'], f'{part}_{side}_arm{lvl}')
                    c.group, c.option = arm, lvl
                    out.append(c)
    for m in out:
        assert np.isfinite(np.array(m.V)).all(), m.name
    return out


if __name__ == '__main__':
    for m in build(G.build()):
        print(f'{m.name:16s} group {m.group} option {m.option}  tris {m.tris():4d}  bones {sorted(m.bones())}')
    for side in 'RL':
        print(side, {f: form_commands(side, f) for f in FORMS})
