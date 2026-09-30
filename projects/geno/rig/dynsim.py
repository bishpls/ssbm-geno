"""Geno's physics chains off line: Melee's chain solver (decomp lb_8001044C, which runs rig.py DYNAMICS in game) ported to
Python and replayed on a recorded run, so parameters can be tried in seconds and only the winners go to Dolphin.

A recording is a lab run of a decomp built with GENO_DYN_TRACE defined (put `#define GENO_DYN_TRACE` at the top of
src/melee/ft/ftdynamics.c): every frame the log carries each chain's parent frame (GP), its solved joints (GC), the
collision spheres (GS) and, every 60 frames, the chain joints' local transforms (GJ). The body's motion doesn't depend on
the chain parameters, so one recording serves every variant. The port reproduces the game to about 0.002 units at rest
and 0.02 in motion (the engine's quintic sine and cosine included); the floor and wind forces are left out, and so are
the actions that hand a chain to the animation (DYN_ANIMATED: the cap in the guard), where --check differs by design.

    .venv/bin/python projects/geno/rig/dynsim.py RUN                  # the recording's chains, per lab segment
    .venv/bin/python projects/geno/rig/dynsim.py RUN --check          # the port against the game's own solve
    .venv/bin/python projects/geno/rig/dynsim.py RUN '{"capeL": {"chain": {"gravity": 0.1}, "bones": [{"step": 0.6}]}}'
Per segment and chain: the largest swing of any link from its rest direction (degrees, in the chain parent's frame, so
the body's own turns drop out), where it sits at the segment's end, and jitter (frame-to-frame reversals of a turn over
1 degree a frame, the facing flips excepted). Segments are cape_lab's move lab (director/cape_lab.py).
"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig

NAMES = ['back', 'capeL', 'capeR', 'cap']          # rig.DYNAMICS order
SEG = [('idle', 60, 100), ('walk', 150, 245), ('run', 300, 345), ('turn', 345, 395), ('skid', 395, 440),
       ('dashdnc', 470, 600), ('jumps', 630, 790), ('fsmash', 790, 860), ('shield', 860, 960), ('shffl', 1000, 1080),
       ('crouch', 1080, 1190)]


def load(run, port=0):
    fr, cur = [], None
    for line in open(os.path.join(run, 'osreport.log'), errors='replace'):
        t = line.split()
        if not t: continue
        try:
            if t[0] == 'GDYN':
                cur = None
                if int(t[2]) == port:
                    cur = dict(f=int(t[1]), motion=int(t[3]), par=[], chains=[], spheres=[]); fr.append(cur)
            elif cur is None: continue
            elif t[0] == 'GP': cur['par'].append(np.array([float(x) for x in t[2:11]]).reshape(3, 3))
            elif t[0] == 'GC': cur['chains'].append(np.array([float(x) for x in t[2:]]).reshape(-1, 3))
            elif t[0] == 'GS': cur['spheres'].append((np.array([float(x) for x in t[2:5]]), float(t[5])))
            elif t[0] == 'GJ': cur.setdefault('gj', {}).setdefault(int(t[1]), []).append(np.array([float(x) for x in t[2:5]]))
        except ValueError:
            pass
    fr = [r for r in fr if r['chains'] and len(r['par']) == len(r['chains'])]
    t0 = {}                                    # each chain's first joint offset when recorded (the model may move since)
    for r in fr:
        for ci, l in r.get('gj', {}).items(): t0.setdefault(ci, l[0])
    for r in fr: r['t0'] = t0
    return fr


def esin(a):     # lbvector_sin / lbvector_cos: the engine's quintic approximations (its rotation matrices scale ~0.4%)
    if a > math.pi: a -= 2 * math.pi
    elif a < -math.pi: a += 2 * math.pi
    return 0.9878619909286499 * a - 0.15527099370956421 * a ** 3 + 0.0056429998949170113 * a ** 5

def ecos(a): return esin(a + math.pi / 2)

def euler_mtx(e):     # lbVector_CreateEulerMatrix: Rz Ry Rx
    sx, cx, sy, cy, sz, cz = esin(e[0]), ecos(e[0]), esin(e[1]), ecos(e[1]), esin(e[2]), ecos(e[2])
    return np.array([[cy * cz, cz * sx * sy - cx * sz, cz * cx * sy + sx * sz],
                     [cy * sz, sz * sx * sy + cx * cz, sz * cx * sy - sx * cz], [-sy, sx * cy, cx * cy]])

def mtx_euler(m):     # HSD_QuatLib_8037EB28
    ln = math.sqrt(m[0][0] ** 2 + m[1][0] ** 2)
    if ln > 1e-5: return np.array([math.atan2(m[2][1], m[2][2]), math.atan2(-m[2][0], ln), math.atan2(m[1][0], m[0][0])])
    return np.array([math.atan2(-m[1][2], m[1][1]), math.atan2(-m[2][0], ln), 0.0])

def axis_angle(axis, a):
    x, y, z = axis; c, s = math.cos(a), math.sin(a); C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s], [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])

def angle(a, b):     # lbVector_Angle
    la = np.linalg.norm(a) * np.linalg.norm(b)
    return 0.0 if la <= 1e-10 else math.acos(max(-1.0, min(1.0, float(a @ b) / la)))

def unit(v):
    n = np.linalg.norm(v); return v / n if n > 0 else v

def rot(v, axis, a):     # lbVector_RotateAboutUnitAxis
    s, c = esin(a), ecos(a)
    return v * c + np.cross(axis, v) * s + axis * (axis @ v) * (1 - c)

def seg_sphere(p0, p1, c, margin, r):     # lbColl_80005C44
    t = r + margin
    for k in range(3):
        if min(p0[k], p1[k]) - t > c[k] or max(p0[k], p1[k]) + t < c[k]: return False
    d1 = p1 - p0; dd = d1 @ d1
    s = 0.0 if dd < 1e-5 else min(1.0, max(0.0, -(d1 @ (p0 - c)) / dd))
    q = d1 * s + p0
    return (q - c) @ (q - c) <= t * t


def chain_spec(ci, override=None):
    names = [j[0] for j in rig.JOINTS]; J = {j[0]: j for j in rig.JOINTS}
    start, count, cs, bones = rig.DYNAMICS[ci]
    js = names[names.index(start):names.index(start) + count]
    cs = dict(cs); bones = [dict(b) for b in bones]
    if override:
        cs.update(override.get('chain', {}))
        for k, b in enumerate(override.get('bones', [])):
            if b and k < len(bones): bones[k].update(b)
    P = [dict(rig.DYN_BONE, **bones[min(k, count - 2)]) for k in range(count)]
    return js, [np.array(J[j][2], float) for j in js], [np.array(J[j][3], float) for j in js], cs, P


def sim(frames, ci, override=None, colliders=True):
    """World positions of chain ci's joints, frame by frame, as the engine would solve them with these parameters."""
    js, T, R0, cs, P = chain_spec(ci, override)
    n = len(js)
    lens = [np.linalg.norm(T[k + 1]) for k in range(n - 1)]
    grav = [cs['gravity'] / L for L in lens]
    dom = []                                  # the twist the engine bleeds off: the axis of the child's largest offset
    for k in range(n - 1):
        t = np.abs(T[k + 1]); dom.append(-1 if (t[2] > t[1] and t[2] > t[0]) else (1 if t[1] > t[0] else 0))
    rotE = [r.copy() for r in R0]; pos = None; w = [0.0] * n; wax = [np.array([1.0, 0, 0])] * n
    fmul = cs.get('follow_mul', 1.0); out = []
    for r in frames:
        Rp = r['par'][ci]; M = np.eye(4); M[:3, :3] = Rp
        M[:3, 3] = r['chains'][ci][0] - Rp @ r.get('t0', {}).get(ci, T[0])
        if pos is None:                                           # lb_8000FD48: the rest pose's world positions
            pos = []; A = M.copy()
            for k in range(n):
                L = np.eye(4); L[:3, :3] = euler_mtx(rotE[k]); L[:3, 3] = T[k]; A = A @ L; pos.append(A[:3, 3].copy())
        par = M.copy()
        for k in range(n - 1):
            b = P[k]
            bone = par.copy(); bone[:3, 3] = par[:3, :3] @ T[k] + par[:3, 3]
            nat = unit(bone[:3, :3] @ euler_mtx(R0[k]) @ T[k + 1])
            bone[:3, :3] = bone[:3, :3] @ euler_mtx(rotE[k]); pos[k] = bone[:3, 3].copy()
            curd = unit(bone[:3, :3] @ T[k + 1])
            link = unit(pos[k + 1] - pos[k]); saved = link.copy()
            if b['follow'] * fmul < 1.0:
                a = angle(link, curd)
                if a != 0: link = rot(link, unit(np.cross(link, curd)), a * (1.0 - b['follow'] * fmul))
            g = np.array([0.0, -1.0, 0.0]); ga = angle(link, g)
            if ga != 0: link = rot(link, unit(np.cross(link, g)), abs(grav[k] * math.sin(ga)))
            if w[k] != 0.0: link = rot(link, wax[k], w[k])
            if cs['gravity'] > 0 and angle(saved, link) > b['step']: link = rot(saved, unit(np.cross(saved, link)), b['step'])
            if b['converge'] > 0:
                link = nat.copy() if angle(nat, link) < b['converge'] else rot(link, unit(np.cross(link, nat)), b['converge'])
            da = angle(nat, link)
            if da > b['limit']: link = rot(link, unit(np.cross(link, nat)), da - b['limit'])
            if colliders:
                link = unit(link)
                for c, rr in r['spheres']:
                    cd = c - pos[k]; dist = np.linalg.norm(cd)
                    if dist > rr and seg_sphere(pos[k], link * lens[k] + pos[k], c, 0.1, rr):
                        ca = angle(cd, link)
                        if ca != 0:
                            av = abs(math.atan2(0.1 + rr, math.sqrt(max(0.0, dist * dist - (0.1 + rr) ** 2)))) - ca
                            if av > 0: link = rot(link, unit(np.cross(cd, link)), av)
            ad = angle(curd, link); ax = unit(np.cross(curd, link)); link = rot(curd, ax, ad)
            w[k] = angle(saved, link)
            if w[k] > 0: wax[k] = unit(np.cross(saved, link))
            d = b['damp']; w[k] = w[k] - d if w[k] > d else 0.0
            if abs(ad) > 1e-5:
                la = par[:3, :3].T @ ax
                if np.abs(la).max() >= 1e-5: rotE[k] = mtx_euler(axis_angle(unit(la), ad) @ euler_mtx(rotE[k]))
            rotE[k][{-1: 2, 0: 0, 1: 1}[dom[k]]] *= 0.9
            L = np.eye(4); L[:3, :3] = euler_mtx(rotE[k]); L[:3, 3] = T[k]; par = par @ L
        L = np.eye(4); L[:3, :3] = euler_mtx(rotE[n - 1]); L[:3, 3] = T[n - 1]; par = par @ L; pos[n - 1] = par[:3, 3].copy()
        out.append(np.array(pos))
    return np.array(out)


def metrics(frames, ci, P):
    """Per segment: (largest swing from rest in degrees, the swing at its end, jitter count)."""
    names = [j[0] for j in rig.JOINTS]; parent = {n: p for n, p, *_ in rig.JOINTS}; W = rig.world_mats()
    s, c = rig.DYNAMICS[ci][0], rig.DYNAMICS[ci][1]; js = names[names.index(s):names.index(s) + c]
    R = np.array(W[parent[js[0]]])[:3, :3]; R /= np.linalg.norm(R, axis=1, keepdims=True)
    Q = np.array([W[j][3][:3] for j in js]); rest = unit_rows(Q[1:] - Q[:-1]) @ R.T
    M = np.array([r['par'][ci] for r in frames]); M = M / np.linalg.norm(M, axis=1, keepdims=True)
    UL = np.einsum('tij,tki->tkj', M, unit_rows3(P[:, 1:] - P[:, :-1]))
    dev = np.degrees(np.arccos(np.clip((UL * rest).sum(2), -1, 1)))
    V = UL[1:] - UL[:-1]; sp = np.linalg.norm(V, axis=2); vd = (V[1:] * V[:-1]).sum(2)
    rev = (vd < -0.5 * sp[1:] * sp[:-1]) & (sp[1:] > 0.017) & (sp[:-1] > 0.017)
    F = np.array([r['f'] for r in frames]); flips = set()
    for i in range(1, len(frames)):
        if np.sign(frames[i]['par'][ci][0][2]) != np.sign(frames[i - 1]['par'][ci][0][2]): flips |= {F[i] + k for k in range(-1, 3)}
    out = {}
    for name, a, b in SEG:
        idx = np.where((F >= a) & (F < b))[0]
        if len(idx) < 3: continue
        out[name] = (dev[idx].max(), dev[idx[-1]].max(), int(sum(rev[i - 2].any() for i in idx[2:] if F[i] not in flips)))
    return out

def unit_rows(D): return D / np.linalg.norm(D, axis=1, keepdims=True)
def unit_rows3(D): return D / np.linalg.norm(D, axis=2, keepdims=True)


if __name__ == '__main__':
    run = sys.argv[1]; frames = load(run)
    if '--check' in sys.argv:
        for ci in range(len(rig.DYNAMICS)):
            e = np.linalg.norm(sim(frames, ci) - np.array([r['chains'][ci] for r in frames]), axis=2).max(1)
            print(f'{NAMES[ci]:6s} port vs game: median {np.median(e):.4f}, 95% {np.percentile(e, 95):.4f} units')
        sys.exit()
    for v in [json.loads(a) for a in sys.argv[2:]] or [{}]:
        print('---', json.dumps(v) if v else 'rig.py DYNAMICS')
        for ci in range(len(rig.DYNAMICS)):
            if NAMES[ci] == 'capeR': continue                        # the mirror of capeL
            m = metrics(frames, ci, sim(frames, ci, v.get(NAMES[ci])))
            print(f'  {NAMES[ci]:5s} ' + ' '.join(f'{k}:{mx:3.0f}/{end:2.0f}/{rv}' for k, (mx, end, rv) in m.items()))
