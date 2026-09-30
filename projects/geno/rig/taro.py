"""Throw-victim animations on the shared 52-node layout ("Taro": PlCo.dat's parts table for kind 0x21, the part order
itself), which any fighter plays while it is thrown.

How the engine plays one (decomp): node n drives the victim's own joint for part n (ftPartsRemap); only rotations reach its
limbs, and translations too reach TopN..HipN (fn_8001E60C drops the translation tracks of every joint but those); the
victim's XRotN is held to the thrower's ThrowN by a position constraint (ftCo_800DB368), so the XRotN rotation keyed here
is the whole body's turn about its hip pivot, in the thrower's facing (the victim takes the thrower's facing when the
throw starts). The values are local rotations in the standard humanoid joint frames the cast shares, so a pose authored on
one skeleton reads on all of them.

Here a pose is authored on Mario's skeleton (the template's; its joint frames are the cast's), per node, by composing the
cast's own victim poses: a donor animation (a cast member's T*Throw*, read from its AJ file on the disc at build time;
nothing of the game's is committed) sampled at chosen times, blended (per-joint quaternion slerp) and turned (the XRotN
yaw, pitch and roll a throw swings the body through). `Clip.tracks()` is what fighter-build writes (anims.json
passthrough, with "tracks").

The reference skeleton and the donors are cached under $MELEE_WORK/rig/taro (datkit rest, skel and fk).
"""
import json, math, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig
from anims import euler_xyz

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
DATKIT = os.path.join(ROOT, 'tools', 'machinima', 'melee', 'datkit.sh')
NODES = 52
B3 = {0, 1, 2, 3, 4}          # the parts whose translations the engine applies (TopN, TransN, XRotN, YRotN, HipN)
CH = {'TRAX': 0, 'TRAY': 1, 'TRAZ': 2, 'ROTX': 3, 'ROTY': 4, 'ROTZ': 5}


def disc():
    return os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc'))


def cache():
    d = os.path.join(os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work')), 'rig', 'taro')
    os.makedirs(d, exist_ok=True)
    return d


def _run(args):
    return subprocess.run([DATKIT] + args, check=True, capture_output=True, text=True).stdout


# ---------------------------------------------------------------------------------------------------------------- reference
_REF = {}


def reference():
    """Mario's skeleton (rest t, r and parents per joint) and his part -> joint map: the frames the poses are authored in."""
    if _REF: return _REF
    path = os.path.join(cache(), 'mario_ref.json')
    if not os.path.exists(path):
        nr, co = os.path.join(disc(), 'files', 'PlMrNr.dat'), os.path.join(disc(), 'files', 'PlCo.dat')
        joints = [json.loads(l) for l in _run(['rest', nr]).splitlines() if l.startswith('{')]
        skel = _run(['skel', co, '0', nr])
        line = next(l for l in skel.splitlines() if l.startswith('part_to_joint:'))
        p2j = {int(a): int(b) for a, b in (kv.split(':') for kv in line.split()[1:])}
        json.dump(dict(joints=joints, p2j=p2j), open(path, 'w'))
    d = json.load(open(path))
    _REF.update(joints=d['joints'], p2j={int(k): v for k, v in d['p2j'].items()})
    return _REF


def rest(node):
    """a node's rest (t, r): its joint's in Mario's skeleton"""
    ref = reference()
    j = ref['p2j'].get(node, 255)
    if j == 255 or j >= len(ref['joints']): return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    jj = ref['joints'][j]
    return tuple(jj['t']), tuple(jj['r'])


# ---------------------------------------------------------------------------------------------------------------- donors
def donor(sym, file, off, size):
    """A cast member's victim animation, sampled every frame: [frame] -> {node: (t or None, r)}, keyed channels only
    (unkeyed ones take the rest's). Cached by symbol."""
    path = os.path.join(cache(), sym + '.json')
    if not os.path.exists(path):
        with open(file, 'rb') as fh:
            fh.seek(off); chunk = fh.read(size)
        assert sym.encode() in chunk, f'{file}: no {sym} at {off}'
        tmp = os.path.join(cache(), sym + '.dat')
        open(tmp, 'wb').write(chunk)
        _run(['fk', os.path.join(disc(), 'files', 'PlMrNr.dat'), tmp, path])
    d = json.load(open(path))
    keyed = {}
    for t in d['tracks']:
        if t['node'] < NODES and t['type'] in CH: keyed.setdefault(t['node'], set()).add(CH[t['type']])
    frames = []
    for loc in d['local']:
        pose = {}
        for n, chans in keyed.items():
            rt, rr = rest(n)
            v = loc[n]
            r = tuple(v[3 + c] if 3 + c in chans else rr[c] for c in range(3))
            t = tuple(v[c] if c in chans else rt[c] for c in range(3)) if (n in B3 and chans & {0, 1, 2}) else None
            pose[n] = (t, r)
        frames.append(pose)
    return frames


def at(frames, u):
    """a donor pose at fractional frame u (clamped), slerped between its frames"""
    u = max(0.0, min(len(frames) - 1.0, u))
    i = int(math.floor(u)); k = u - i
    if k < 1e-6 or i + 1 >= len(frames): return dict(frames[i])
    return blend(frames[i], frames[i + 1], k)


# ---------------------------------------------------------------------------------------------------------------- rotations
def mat(r):
    m = rig.rot_xyz(*r)
    return [row[:3] for row in m[:3]]


def quat(m):
    """row-vector rotation matrix -> quaternion (w, x, y, z)"""
    t = m[0][0] + m[1][1] + m[2][2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        return (0.25 * s, (m[1][2] - m[2][1]) / s, (m[2][0] - m[0][2]) / s, (m[0][1] - m[1][0]) / s)
    if m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2
        return ((m[1][2] - m[2][1]) / s, 0.25 * s, (m[1][0] + m[0][1]) / s, (m[2][0] + m[0][2]) / s)
    if m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2
        return ((m[2][0] - m[0][2]) / s, (m[1][0] + m[0][1]) / s, 0.25 * s, (m[2][1] + m[1][2]) / s)
    s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2
    return ((m[0][1] - m[1][0]) / s, (m[2][0] + m[0][2]) / s, (m[2][1] + m[1][2]) / s, 0.25 * s)


def unquat(q):
    w, x, y, z = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y)],
            [2 * (x * y - w * z), 1 - 2 * (x * x + z * z), 2 * (y * z + w * x)],
            [2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)]]


def slerp(a, b, k):
    d = sum(x * y for x, y in zip(a, b))
    if d < 0: b, d = tuple(-x for x in b), -d
    if d > 0.9995:
        q = tuple(x + (y - x) * k for x, y in zip(a, b))
    else:
        th = math.acos(d); s = math.sin(th)
        q = tuple((math.sin((1 - k) * th) * x + math.sin(k * th) * y) / s for x, y in zip(a, b))
    l = math.sqrt(sum(x * x for x in q))
    return tuple(x / l for x in q)


def lerp_r(ra, rb, k):
    return euler_xyz(unquat(slerp(quat(mat(ra)), quat(mat(rb)), k)))


def blend(pa, pb, k):
    """two poses mixed k of the way to pb (nodes either lacks keep the other's)"""
    out = {}
    for n in set(pa) | set(pb):
        if n not in pa: out[n] = pb[n]; continue
        if n not in pb: out[n] = pa[n]; continue
        (ta, ra), (tb, rb) = pa[n], pb[n]
        t = None if ta is None and tb is None else \
            tuple(x + (y - x) * k for x, y in zip(ta or rest(n)[0], tb or rest(n)[0]))
        out[n] = (t, lerp_r(ra, rb, k))
    return out


def turned(pose, yaw=0.0, pitch=0.0, roll=0.0):
    """the whole body turned about its hip pivot (XRotN, node 2) in the thrower's frame: yaw about +Y, then pitch (its
    front down) about the thrower's +X, roll about +Z; the body's own rotation first"""
    pose = dict(pose)
    t, r = pose.get(2, (None, rest(2)[1]))
    m = mat(r)
    for axis, a in (('z', roll), ('x', pitch), ('y', yaw)):
        if abs(a) < 1e-9: continue
        rr = (a, 0, 0) if axis == 'x' else (0, a, 0) if axis == 'y' else (0, 0, a)
        m = [[sum(m[i][k] * mat(rr)[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    pose[2] = (t, euler_xyz(m))
    return pose


# ---------------------------------------------------------------------------------------------------------------- clips
class Clip:
    """A victim animation: a pose on every frame 0..n (built by the throw), written as linear keys on every frame."""

    def __init__(self, n, sym):
        self.n, self.sym, self.poses = n, sym, {}

    def set(self, f, pose):
        self.poses[f] = pose
        return self

    def tracks(self):
        out = {}
        nodes = sorted(set(n for p in self.poses.values() for n in p))
        prev = {}
        for n in nodes:
            rk, tk = [], []
            for f in range(self.n + 1):
                t, r = self.poses[f].get(n, (None, rest(n)[1]))
                if n in prev:                                     # unwrap each angle to the nearest turn of the last
                    r = tuple(c + 2 * math.pi * round((p - c) / (2 * math.pi)) for p, c in zip(prev[n], r))
                prev[n] = r
                rk.append([f, *[round(x, 5) for x in r]])
                if t is not None: tk.append([f, *[round(x, 5) for x in t]])
            e = {'r': rk}
            if tk and n in B3: e['t'] = tk
            out[str(n)] = e
        return out

    def entry(self):
        return dict(sym=self.sym, frames=self.n, nodes=NODES, tracks=self.tracks())


# ---------------------------------------------------------------------------------------------------------------- preview
def skeleton_world(pose, scale=1.45):
    """world points (the victim's own frame: TopN at the origin, facing +Z) of Mario's body joints (XRotN and below) under a
    Taro pose, and each one's parent, for a stick figure; and XRotN's joint index"""
    ref = reference()
    j2n = {j: n for n, j in ref['p2j'].items() if j != 255 and n < NODES}
    joints = []
    for jj in ref['joints']:
        t, r = tuple(jj['t']), tuple(jj['r'])
        n = j2n.get(jj['i'])
        if n is not None and n in pose:
            pt, pr = pose[n]
            r = pr
            if pt is not None and n in B3 and n != 2: t = pt
        joints.append((f"J{jj['i']}", f"J{jj['p']}" if jj['p'] >= 0 else None, tuple(x * scale for x in t), r))
    W = rig.world_mats(joints=joints)
    xr = ref['p2j'][2]
    body, par = set([xr]), {}
    for jj in ref['joints']:                                   # XRotN and its descendants (parents come first)
        if jj['p'] in body: body.add(jj['i']); par[jj['i']] = jj['p']
    pts = {j: tuple(W[f"J{j}"][3][:3]) for j in body}
    return pts, par, xr


CAST = ['Mr', 'Fx', 'Fc', 'Ss', 'Ca', 'Ns', 'Lk', 'Pe', 'Kp', 'Dk', 'Mt', 'Sk', 'Fe', 'Pr', 'Kb', 'Ys', 'Gn', 'Zd', 'Lg',
        'Cl', 'Pk', 'Gw', 'Dr', 'Pp', 'Fc']


def find(name):
    """(file, off, size, sym) of a cast victim animation by its short name (e.g. TFoxThrowLw), from each fighter's action
    table (datkit actions, cached)"""
    path = os.path.join(cache(), 'victims.json')
    table = json.load(open(path)) if os.path.exists(path) else {}
    if not table:
        import re
        rx = re.compile(r'^\s*\d+ 0x\w+ off\s+(\d+) size\s+(\d+) .* (PlyTaro_Share_ACTION_(\w+?)_figatree)')
        for code in dict.fromkeys(CAST):
            pl = os.path.join(disc(), 'files', f'Pl{code}.dat')
            for line in _run(['actions', pl]).splitlines():
                m = rx.match(line)
                if m: table.setdefault(m.group(4), [os.path.join(disc(), 'files', f'Pl{code}AJ.dat'), int(m.group(1)), int(m.group(2)), m.group(3)])
        json.dump(table, open(path, 'w'))
    return table[name]


def load(name):
    file, off, size, sym = find(name)
    return donor(sym, file, off, size)
