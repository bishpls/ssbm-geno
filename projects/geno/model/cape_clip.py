"""cape_clip.py: where the capelet's panels cut into his arms, over every action, frame by frame (ART.md "Cape and scarf":
the arms pass through the front panels when they rise; HANDOFF §7).

    .venv/bin/python projects/geno/model/cape_clip.py FK_DIR OUT.json [ACTION_REGEX]
    .venv/bin/python projects/geno/model/cape_clip.py table BEFORE.json AFTER.json [OUT.md]

FK_DIR is `datkit fkdir PlGeNr.dat PlGe.dat PlGeAJ.dat FK_DIR` of a build: every action's joints, frame by frame, as
the game poses them. The capelet's outer surface (cape_out_L/R, the blue the camera sees) is skinned onto each frame as the
hardware does (linear blend of its vertices' bones; the surface between them interpolated linearly), sampled densely,
and tested against his arms' volume: the elbow and wrist balls, and the upper arm and forearm as the lathes geno_geo
builds (their profiles along each bone, in the posed joint's own frame, so a grown bone counts at its size); the shoulder
ball is left out (arm_parts says why).

The depth of a sample inside an arm is how far it would have to move to leave it (the lathe's radius there, less its
distance from the bone's axis; a ball's radius less its distance from the centre): the panel slicing into the arm. Per
frame: the deepest cut, where (which panel side, which part of which arm), the panel area inside the arms (deeper than
0.1: what shows), the panels' worst edge stretch and each upper arm's elevation. The physics chains (the capelet's joints)
sit where the animation leaves them, their rest pose on the parent; the game's solve moves them a little, so the game
is the judge (director/capelet_lab.py).
"""
import json, math, os, re, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geno_geo as G  # noqa: E402

NAMES = [j[0] for j in G.JOINTS]
IDX = {n: i for i, n in enumerate(NAMES)}
PANELS = ('cape_out_L', 'cape_out_R')
SUB = 5                                   # samples per triangle edge


def rest4(n):
    """A joint's rest transform as a column-vector 4x4 (geno_geo's REST is row-vector)."""
    return G.REST[n].T


def pose4(p):
    """datkit fk's pose entry -> column-vector 4x4 (its r00..r22 columns are the joint's local axes in model space)."""
    M = np.eye(4)
    M[:3, :3] = np.array(p[:9], float).reshape(3, 3)
    M[:3, 3] = p[9:12]
    return M


def panel_samples(meshes=None):
    """The panels' triangles as barycentric samples: for each mesh, its vertices (rest), weights, and a sample matrix
    B (n_samples x n_verts) so samples = B @ skinned vertices; and each sample's area and theta (the angle round the body
    from the front, degrees: the front panels are under ~100)."""
    out = []
    meshes = {m.name: m for m in (meshes or G.build())}
    for name in PANELS:
        m = meshes[name]
        V = np.array(m.V)
        rows, area, theta = [], [], []
        for f in m.F:
            for k in range(1, len(f) - 1):
                tri = (f[0], f[k], f[k + 1])
                P = V[list(tri)]
                a = 0.5 * np.linalg.norm(np.cross(P[1] - P[0], P[2] - P[0]))
                pts = [(i, j) for i in range(SUB + 1) for j in range(SUB + 1 - i)]
                for i, j in pts:
                    w = np.zeros(len(V)); u, v = i / SUB, j / SUB
                    w[tri[0]] += 1 - u - v; w[tri[1]] += u; w[tri[2]] += v
                    rows.append(w); area.append(a / len(pts))
                    c = (1 - u - v) * P[0] + u * P[1] + v * P[2]
                    theta.append(math.degrees(math.atan2(abs(c[0]), c[2])))
        out.append(dict(name=name, mesh=m, B=np.array(rows), area=np.array(area), theta=np.array(theta)))
    return out


def arm_parts():
    """His arms' volume, per side: balls (joint, radius) and lathes (joint, profile [(x, r)]). The shoulder ball is left
    out: it turns in place under the capelet's dome and the collar (the neckline rides the torso over it, 0.1-0.2 into
    it in every pose, the idle's included, hidden by the collar), so it is no part of an arm passing through a panel."""
    parts = []
    for s in 'LR':
        for j, r in ((f'{s}ArmJ', 0.68), (f'{s}HandN', 0.54)):
            parts.append(('ball', f'{s}:{j[1:]}', j, r))
        parts.append(('lathe', f'{s}:upper arm', f'{s}ShoulderJ', G.UPPER_ARM))
        parts.append(('lathe', f'{s}:forearm', f'{s}ArmJ', G.FOREARM))
    return parts


class Skinner:
    """A mesh's linear-blend skinning, vectorised: its rest vertices and weights as arrays."""
    def __init__(self, m):
        self.bones = sorted(m.bones())
        self.R = np.c_[np.array(m.V), np.ones(len(m.V))]
        self.W = np.array([[w.get(b, 0.0) for b in self.bones] for w in m.W])
        self.inv = {b: np.linalg.inv(rest4(b)) for b in self.bones}

    def __call__(self, W4):
        S = np.stack([W4[b] @ self.inv[b] for b in self.bones])            # bones x 4 x 4
        X = np.einsum('bij,vj->bvi', S, self.R)                            # bones x verts x 4
        return np.einsum('vb,bvi->vi', self.W, X)[:, :3]


def skin(m, W4):
    """Vertices of mesh m skinned by the posed joints W4 (name -> column-vector 4x4)."""
    V = np.c_[np.array(m.V), np.ones(len(m.V))]
    out = np.zeros((len(V), 3))
    S = {b: W4[b] @ np.linalg.inv(rest4(b)) for b in m.bones()}
    for i, (v, w) in enumerate(zip(V, m.W)):
        acc = np.zeros(4)
        for b, x in w.items():
            acc += x * (S[b] @ v)
        out[i] = acc[:3]
    return out


def depth_in(parts, W4, P):
    """For points P (n x 3): the deepest any arm part holds each (0 outside), and which part."""
    best = np.zeros(len(P)); which = np.full(len(P), -1)
    for k, (kind, label, j, spec) in enumerate(parts):
        M = W4[j]
        L = (np.linalg.inv(M) @ np.c_[P, np.ones(len(P))].T).T[:, :3]       # in the joint's own (scaled) frame
        if kind == 'ball':
            d = spec - np.linalg.norm(L, axis=1)
        else:
            xs = np.array([p[0] for p in spec]); rs = np.array([p[1] for p in spec])
            x = L[:, 0]; rad = np.hypot(L[:, 1], L[:, 2])
            r = np.interp(x, xs, rs, left=0.0, right=0.0)
            d = np.where((x > xs[0]) & (x < xs[-1]), r - rad, -1.0)
        upd = d > best
        best = np.where(upd, d, best); which = np.where(upd, k, which)
    return best, which


def stretch(m, Vs):
    """The panel's worst stretch this frame: the most any edge grew over its length in the design pose, in units (the
    tiny edges at the throat make a ratio meaningless)."""
    D = np.array(m.attr['design'])
    worst = 0.0
    for f in m.F:
        for a, b in zip(f, f[1:] + f[:1]):
            worst = max(worst, float(np.linalg.norm(Vs[a] - Vs[b]) - np.linalg.norm(D[a] - D[b])))
    return worst


def measure(fk_dir, out, only=None, meshes=None, quiet=False, step=1):
    panels = panel_samples(meshes)
    parts = arm_parts()
    res = {}
    for pn in panels:
        pn['skin'] = Skinner(pn['mesh'])
    for fn in sorted(os.listdir(fk_dir)):
        if not fn.endswith('.json'): continue
        act = fn[:-5]
        if only and not re.search(only, act): continue
        d = json.load(open(os.path.join(fk_dir, fn)))
        rows = []
        for f, pose in enumerate(d['pose']):
            if step > 1 and f % step: continue
            W4 = {n: pose4(pose[i]) for i, n in enumerate(NAMES) if i < len(pose)}
            deepest, where, area = 0.0, None, 0.0
            side = {}
            for pn in panels:
                Vs = pn['skin'](W4)
                P = pn['B'] @ Vs
                dep, wh = depth_in(parts, W4, P)
                inside = dep > 0.1
                a_side = float(pn['area'][inside].sum())
                area += a_side
                side['area' + pn['name'][-1]] = round(a_side, 3)
                if dep.max() > deepest:
                    k = int(dep.argmax())
                    deepest, where = float(dep[k]), dict(panel=pn['name'], part=parts[wh[k]][1], theta=round(float(pn['theta'][k]), 1))
                side[pn['name'][-1]] = round(float(dep.max()), 3)
                side['stretch' + pn['name'][-1]] = round(stretch(pn['mesh'], Vs), 3)
            # each upper arm's elevation (degrees above horizontal: + raised), the reach the brief is about
            elev = {s_: round(math.degrees(math.asin(max(-1, min(1, W4[f'{s_}ShoulderJ'][1, 0] /
                                                                np.linalg.norm(W4[f'{s_}ShoulderJ'][:3, 0]))))), 1)
                    for s_ in 'LR'}
            rows.append(dict(frame=f, depth=round(deepest, 3), area=round(area, 3), where=where, side=side, elev=elev))
        worst = max(rows, key=lambda r: r['depth'])
        res[act] = dict(frames=len(rows), worst=worst, clipped=sum(1 for r in rows if r['depth'] > 0.1), per=rows)
        if not quiet:
            print(f"{act:24s} worst {worst['depth']:.2f} on {worst['frame']:3d} ({(worst['where'] or {}).get('part')}, "
                  f"{(worst['where'] or {}).get('panel')}), frames over 0.1: {res[act]['clipped']}", flush=True)
    if out: json.dump(res, open(out, 'w'))
    return res


def summary(res):
    """The whole table in a few numbers, per arm-frame (each side of each frame): how many cut deeper than 0.3; the
    panel area inside the arm (deeper than 0.1: what shows) as its mean, 90th percentile and the frames with more than
    0.25 square units; the same over the frames with that arm raised above horizontal; and the worst stretch."""
    d, a, dr, ar, st = [], [], [], [], []
    for r in res.values():
        for p in r['per']:
            for s_ in 'LR':
                x, y = p['side'].get(s_, 0.0), p['side'].get('area' + s_, 0.0)
                d.append(x); a.append(y)
                if p['elev'][s_] > 0: dr.append(x); ar.append(y)
                st.append(p['side'].get('stretch' + s_, 0.0))
    d, a, dr, ar, st = map(np.array, (d, a, dr, ar, st))
    return dict(arm_frames=len(d), deeper_0_3=int((d > 0.3).sum()), area_mean=round(float(a.mean()), 3),
                area_p90=round(float(np.percentile(a, 90)), 3), area_over_0_25=int((a > 0.25).sum()),
                raised=len(dr), raised_deeper_0_3=int((dr > 0.3).sum()), raised_area_mean=round(float(ar.mean()), 3),
                raised_area_p90=round(float(np.percentile(ar, 90)), 3), raised_area_over_0_25=int((ar > 0.25).sum()),
                stretch_p99=round(float(np.percentile(st, 99)), 3), stretch_max=round(float(st.max()), 3))


OVERHEAD = ['AttackHi4', 'AttackAirHi', 'AttackHi3', 'SpecialHiStart', 'SpecialAirHiStart', 'SpecialLw', 'SpecialAirLw',
            'SpecialLwFlash', 'Appeal', 'ThrowHi', 'CliffClimbSlow', 'SpecialNLoop', 'AttackS4Hi', 'AttackS3Hi']


def per_action(r):
    """An action's numbers: its deepest cut (units), the frames any arm cuts more than 0.25 square units of panel, the
    frames it does with that arm raised, and the mean cut area."""
    per = r['per']
    a = [max(p['side'].get('areaL', 0), p['side'].get('areaR', 0)) for p in per]
    raised = [max((p['side'].get('area' + s_, 0) for s_ in 'LR' if p['elev'][s_] > 0), default=0) for p in per]
    return dict(frames=len(per), deepest=max(p['depth'] for p in per), cut=sum(x > 0.25 for x in a),
                cut_raised=sum(x > 0.25 for x in raised), area=float(np.mean([p['area'] for p in per])))


def table(before, after, md=None, n=30):
    """The before/after penetration table (markdown): the overhead moves first, then the worst of the rest."""
    B, A = json.load(open(before)), json.load(open(after))
    rows = []
    rest = sorted((a for a in B if a not in OVERHEAD), key=lambda a: -per_action(B[a])['area'])[:n - len(OVERHEAD)]
    L = ['| Action | Frames | Deepest cut (units) | Frames cut > 0.25 sq u | ... with the arm raised | Mean cut area (sq u) |',
         '| --- | --- | --- | --- | --- | --- |']
    for act in [a for a in OVERHEAD if a in B] + rest:
        b, a = per_action(B[act]), per_action(A[act])
        L.append(f"| {act} | {b['frames']} | {b['deepest']:.2f} -> {a['deepest']:.2f} | {b['cut']} -> {a['cut']} | "
                 f"{b['cut_raised']} -> {a['cut_raised']} | {b['area']:.2f} -> {a['area']:.2f} |")
    sb, sa = summary(B), summary(A)
    L += ['', f"Every action, every frame, each arm ({sb['arm_frames']} arm-frames): cut deeper than 0.3 {sb['deeper_0_3']} -> "
          f"{sa['deeper_0_3']}; more than 0.25 sq u cut {sb['area_over_0_25']} -> {sa['area_over_0_25']}; mean cut area "
          f"{sb['area_mean']} -> {sa['area_mean']}. With that arm raised ({sb['raised']}): more than 0.25 sq u "
          f"{sb['raised_area_over_0_25']} -> {sa['raised_area_over_0_25']}, mean {sb['raised_area_mean']} -> "
          f"{sa['raised_area_mean']}, 90th percentile {sb['raised_area_p90']} -> {sa['raised_area_p90']}. The panels' worst "
          f"stretch (99th percentile, units) {sb['stretch_p99']} -> {sa['stretch_p99']}."]
    out = '\n'.join(L)
    if md: open(md, 'w').write(out + '\n')
    print(out)


if __name__ == '__main__':
    if sys.argv[1] == 'table':
        table(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    else:
        measure(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
