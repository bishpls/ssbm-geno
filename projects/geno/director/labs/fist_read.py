"""Fist readability: how big a fist's mesh is on its hit frames against the hitbox it carries, for the cast and for Geno.
The cast grow a limb on its first active frame (research/limb_scale.md); this measures what that buys on screen. For each
move and frame the model (`datkit export`, the rest pose skinned) is posed by the animation (`datkit fkdir`, scale
included) and the hand's vertices (those bound mostly to the hand's model-part joints: the hand, fingers and thumb) are
projected onto the camera's plane (the side view: forward and up). Reported, in world units (times ModelScale):
    s        the hand joint's effective scale (inherited down the arm)
    r        the silhouette's equivalent radius, sqrt(area / pi) (its filled triangles, rasterized at 0.01 units)
    w        its widest extent (Feret diameter)
    hit      the active hitbox nearest the silhouette's centre (movedata's geometry): its radius, and the distance
             between their centres
    cover    r / hit radius: how much of its hitbox the fist fills
    .venv/bin/python projects/geno/director/labs/fist_read.py OUT.json [--geno BUILD_DIR[:LABEL],...] [--md OUT.md] [--png DIR]
--png draws each move's first active frame: the fist's silhouette inside its hitbox, at one scale for every fighter.
BUILD_DIR holds PlGe.dat, PlGeAJ.dat and PlGeNr.dat (a production-model build: the glTF import's hands and forms).
"""
import json, math, os, re, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
DATKIT = os.path.join(ROOT, 'tools/machinima/melee/datkit.sh')
DISC = os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc')) + '/files'
WORK = os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work'))
KIND = dict(Mr=8, Lg=7, Dr=22, Fx=2, Ge=0)
NAME = dict(Mr='Mario', Lg='Luigi', Dr='Doc', Fx='Fox', Ge='Geno')
RES = 0.01

# (fighter, move label (movedata's), action index, frames, part): both sides are measured; the report keeps the one nearer
# a hit. Parts: hand (the hand's model-part joints: the hand, fingers and thumb), rocket (Geno's: the hand as the rocket
# form shows it, with its exhaust ring), leg (the shin and boot: the knee's subtree), arm (the whole arm from the shoulder)
CAST = [('Mr', 'jab1', 46, range(0, 9), 'hand'), ('Mr', 'jab2', 47, range(0, 9), 'hand'),
        ('Mr', 'jab3', 48, range(2, 12), 'leg'), ('Mr', 'fsmash', 62, range(9, 20), 'hand'),
        ('Mr', 'fair', 69, range(14, 30), 'hand'), ('Mr', 'bair', 70, range(4, 20), 'leg'),
        ('Mr', 'uair', 71, range(2, 12), 'leg'), ('Mr', 'utilt', 58, range(2, 16), 'hand'),
        ('Mr', 'grab', 242, range(3, 12), 'hand'), ('Mr', 'pummel', 245, range(10, 20), 'hand'),
        ('Lg', 'jab1', 46, range(0, 9), 'hand'), ('Lg', 'dash_attack', 52, range(2, 40), 'hand'),
        ('Dr', 'jab1', 46, range(0, 9), 'hand'), ('Dr', 'jab3', 48, range(2, 12), 'leg'), ('Dr', 'fsmash', 62, range(9, 20), 'hand'),
        ('Dr', 'bair', 70, range(4, 20), 'leg'), ('Dr', 'utilt', 58, range(2, 16), 'hand'),
        ('Fx', 'dash_attack', 52, range(2, 20), 'leg'), ('Fx', 'nair', 68, range(2, 32), 'leg')]
GENO = [('Ge', 'jab1', 46, range(0, 9), 'hand'), ('Ge', 'jab2', 47, range(0, 9), 'hand'), ('Ge', 'jab3', 48, range(2, 12), 'hand'),
        ('Ge', 'utilt', 58, range(3, 14), 'hand'), ('Ge', 'pummel', 245, range(6, 14), 'hand'),
        ('Ge', 'nair', 68, range(2, 22), 'leg'), ('Ge', 'dash_attack', 52, range(4, 18), 'arm'),
        ('Ge', 'fsmash', 62, range(12, 29), 'rocket'), ('Ge', 'fsmash_hi', 60, range(12, 29), 'rocket'),
        ('Ge', 'fsmash_lw', 64, range(12, 29), 'rocket'), ('Ge', 'grab', 242, range(3, 14), 'rocket'),
        ('Ge', 'dash_grab', 243, range(5, 16), 'rocket'), ('Ge', 'ThrowF', 247, range(20, 41), 'rocket')]
# Geno's hands as the fist shows them in the rocket form: the palm, the fingers and the rocket's exhaust ring (the socket
# on the forearm stays behind; its vertices are bound to ArmJ, so the hand's joints leave it out)
GENO_DOBJS = {'L': 'palm_L,fingers_L,rocket_L', 'R': 'palm_R,fingers_R,rocket_R'}
LEG_PART = {'L': 8, 'R': 13}                 # PlCo's part numbers for the knees (LKneeJ, RKneeJ), the same in every table


def dk(*a):
    r = subprocess.run([DATKIT, *a], capture_output=True, text=True)
    if r.returncode: raise SystemExit(f'datkit {a[0]}: {r.stderr or r.stdout}')
    return r.stdout


class Model:
    """A skinned model (datkit export): bind-space positions, joints and weights, inverse binds."""
    def __init__(self, gltf):
        g = json.load(open(gltf))
        buf = open(os.path.join(os.path.dirname(gltf), g['buffers'][0]['uri']), 'rb').read()
        def acc(i):
            a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]
            dt = {5126: np.float32, 5123: np.uint16, 5121: np.uint8, 5125: np.uint32}[a['componentType']]
            n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
            off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
            arr = np.frombuffer(buf, dtype=dt, count=a['count'] * n, offset=off).reshape(a['count'], n)
            return arr.astype(np.float64) if dt == np.float32 else arr.astype(np.int64)
        sk = g['skins'][0]
        self.slot = np.array(sk['joints'])                          # skin slot -> node (= joint index)
        ibm = acc(sk['inverseBindMatrices'])
        self.ibm = np.array([m.reshape(4, 4).T for m in ibm])        # column-vector 4x4
        self.prims = []
        for mesh in g['meshes']:
            for pr in mesh['primitives']:
                at = pr['attributes']
                P, J, Wt = acc(at['POSITION']), acc(at['JOINTS_0']), acc(at['WEIGHTS_0'])
                idx = acc(pr['indices'])[:, 0] if 'indices' in pr else np.arange(len(P))
                self.prims.append((P, J, Wt, idx.reshape(-1, 3)))

    def hand(self, joints, M):
        """the triangles (world, 3 x 3 each) of vertices bound mostly to `joints`, posed by world matrices M[joint]"""
        tris = []
        S = np.array([M[j] @ self.ibm[k] for k, j in enumerate(self.slot)])     # skinning matrix per slot
        for P, J, Wt, T in self.prims:
            dom = self.slot[J[np.arange(len(J)), Wt.argmax(1)]]
            sel = np.isin(dom, list(joints))
            if not sel.any(): continue
            Ph = np.c_[P, np.ones(len(P))]
            V = np.zeros((len(P), 3))
            for c in range(J.shape[1]):
                V += Wt[:, c:c + 1] * np.einsum('nij,nj->ni', S[J[:, c]], Ph)[:, :3]
            keep = sel[T].all(1)
            tris.append(V[T[keep]])
        return np.concatenate(tris) if tris else np.zeros((0, 3, 3))


def fk_mats(fk, frame):
    """joint -> world 4x4 (column vectors) on an animation frame, from `datkit fk`'s pose (columns = local axes)"""
    out = []
    for p in fk['pose'][frame]:
        m = np.eye(4)
        m[:3, :3] = np.array(p[:9]).reshape(3, 3)
        m[:3, 3] = p[9:12]
        out.append(m)
    return out


def silhouette(tris, scale):
    """equivalent radius, widest extent and centre (forward z, up y) of triangles seen side-on, in world units"""
    if not len(tris): return None
    zy = tris[:, :, [2, 1]] * scale
    lo, hi = zy.reshape(-1, 2).min(0) - RES, zy.reshape(-1, 2).max(0) + RES
    wpx, hpx = [int(math.ceil(x)) for x in (hi - lo) / RES]
    im = Image.new('1', (wpx, hpx), 0)
    d = ImageDraw.Draw(im)
    for t in zy:
        d.polygon([tuple((v - lo) / RES) for v in t], fill=1)
    a = np.array(im, dtype=bool)
    area = a.sum() * RES * RES
    ys, xs = np.nonzero(a)
    cz, cy = lo[0] + (xs.mean() + 0.5) * RES, lo[1] + (ys.mean() + 0.5) * RES
    pts = np.c_[xs, ys] * RES
    # the Feret diameter over the hull's points (a sample of the silhouette's edge is plenty at this resolution)
    from scipy.spatial import ConvexHull
    h = pts[ConvexHull(pts).vertices] if len(pts) > 3 else pts
    w = max(np.linalg.norm(h[i] - h[j]) for i in range(len(h)) for j in range(i + 1, len(h))) if len(h) > 1 else 0.0
    return dict(r=math.sqrt(area / math.pi), w=w, c=(round(float(cy), 2), round(float(cz), 2)))


def hand_parts(pl, nr):
    """the model-part joints of each hand (ftData's model parts: 0 left, 1 right)"""
    t = json.loads(dk('model-tables', pl, nr))
    mp = t['modelParts']
    return {'L': set(mp[0]['entries']), 'R': set(mp[1]['entries'])}


def movedata(code, pl, aj, nr, rig=None):
    path = f'{WORK}/movedata/{code}.jsonl'
    if rig is None and os.path.exists(path):
        lines = open(path).read().splitlines()
    else:
        lines = dk('movedata', pl, aj, nr, f'{DISC}/PlCo.dat', str(KIND[code]), *([rig] if rig else [])).splitlines()
    return {m['move']: m for m in map(json.loads, lines) if 'move' in m}


PNG = None                                               # --png DIR: a drawing of each move's first active frame
DRAW_AT = {'nair': 12, 'bair': 7, 'utilt': 7}           # ... or the frame its part is grown on, where that comes later


def draw(path, tris, scale, hit, title, px=40):
    """the fist's silhouette (filled, side-on) inside its hitbox's circle, px pixels per world unit"""
    from PIL import ImageFont
    y, z, hr = hit
    W = H = int(2 * 5.2 * px)
    im = Image.new('RGB', (W, H + 22), (24, 24, 30))
    d = ImageDraw.Draw(im)
    to = lambda zz, yy: (W / 2 + (zz - z) * px, 22 + H / 2 - (yy - y) * px)
    d.ellipse([to(z - hr, y + hr), to(z + hr, y - hr)], outline=(255, 90, 90), width=2, fill=(70, 30, 34))
    for t in tris[:, :, [2, 1]] * scale:
        d.polygon([to(zz, yy) for zz, yy in t], fill=(236, 190, 120))
    d.text((6, 4), title, fill=(235, 235, 240))
    im.save(path)


def part_roots(code, pl, nr):
    """side -> {part: root joint (or the hand's joint set)}"""
    out = {'L': {}, 'R': {}}
    hands = hand_parts(pl, nr)
    if code == 'Ge':
        sys.path.insert(0, os.path.join(ROOT, 'projects/geno/rig'))
        import rig
        names = [j[0] for j in rig.JOINTS]
        for s in 'LR':
            out[s] = dict(hand=hands[s], rocket=hands[s], leg=names.index(f'{s}KneeJ'), arm=names.index(f'{s}ShoulderJ'))
        return out
    j2p = {}
    for line in dk('skel', f'{DISC}/PlCo.dat', str(KIND[code]), nr).splitlines():
        m = re.match(r'\s*(\d+) p-?\d+\s+part (\d+)', line)
        if m: j2p[int(m.group(1))] = int(m.group(2))
    for s in 'LR':
        out[s] = dict(hand=hands[s], leg=next(j for j, pt in j2p.items() if pt == LEG_PART[s]))
    return out


def subtree(par, root):
    out = {root}
    for j in range(len(par)):
        k = j
        while par[k] >= 0:
            k = par[k]
            if k == root: out.add(j); break
    return out


def measure(code, label, cases, pl, aj, nr, model_for, md, scale, tmp):
    roots = part_roots(code, pl, nr)
    spec = ','.join(f'{c[2]}={c[1]}' for c in cases)
    dk('fkdir', nr, pl, aj, tmp, spec)
    rows = []
    for _, move, act, frames, part in cases:
        fk = json.load(open(f'{tmp}/{move}.json'))
        par = [j['p'] for j in fk['joints']]
        mv = md.get(move, {})
        geo = {f: sph for f, sph in mv.get('geo', []) if sph}
        first = min(geo) if geo else None
        for f in frames:
            if f >= len(fk['pose']): break
            M = fk_mats(fk, f)
            for side in 'LR':
                r0 = roots[side][part]
                js, hj = (r0, min(r0)) if isinstance(r0, set) else (subtree(par, r0), r0)
                s_eff = float(np.linalg.norm(M[hj][:3, 0]))
                tris = model_for(side, part).hand(js, M)
                sil = silhouette(tris, scale)
                if sil is None: continue
                row = dict(fighter=code, build=label, move=move, part=part, frame=f, hand=side, s=round(s_eff, 3),
                           r=round(sil['r'], 3), w=round(sil['w'], 3), centre=sil['c'])
                hits = geo.get(f, [])
                if hits:
                    y, z, hr = min(hits, key=lambda h: math.hypot(h[0] - sil['c'][0], h[1] - sil['c'][1]))
                    row.update(hit=[y, z, hr], dist=round(math.hypot(y - sil['c'][0], z - sil['c'][1]), 2),
                               cover=round(sil['r'] / hr, 3))
                    if PNG and f == DRAW_AT.get(move, first) and row['dist'] < hr + 2:
                        os.makedirs(PNG, exist_ok=True)
                        draw(os.path.join(PNG, f'{code}_{label}_{move}_{side}.png'), tris, scale, (y, z, hr),
                             f"{NAME[code]} {label} {move} f{f} {side} {part}: s {row['s']}, cover {row['cover']}")
                rows.append(row)
    return rows


def main():
    a = sys.argv[1:]
    out = a[0]
    genos = []
    if '--geno' in a:
        for spec in a[a.index('--geno') + 1].split(','):
            d, _, lab = spec.partition(':')
            genos.append((os.path.expanduser(d), lab or os.path.basename(d.rstrip('/'))))
    out_md = a[a.index('--md') + 1] if '--md' in a else None
    global PNG
    PNG = a[a.index('--png') + 1] if '--png' in a else None
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for code in dict.fromkeys(c for c, *_ in CAST):
            cs = [c for c in CAST if c[0] == code]
            pl, aj, nr = f'{DISC}/Pl{code}.dat', f'{DISC}/Pl{code}AJ.dat', f'{DISC}/Pl{code}Nr.dat'
            dk('export', nr, f'{tmp}/{code}.gltf', '--ft', pl, '--lod', 'high')
            mdl = Model(f'{tmp}/{code}.gltf')
            md = movedata(code, pl, aj, nr)
            sc = next(iter(md.values()))['scale']
            os.makedirs(f'{tmp}/fk_{code}', exist_ok=True)
            rows += measure(code, 'disc', cs, pl, aj, nr, lambda side, part, m=mdl: m, md, sc, f'{tmp}/fk_{code}')
        for d, lab in genos:
            pl, aj, nr = f'{d}/PlGe.dat', f'{d}/PlGeAJ.dat', f'{d}/PlGeNr.dat'
            log = open(f'{d}/PlGeNr.import.txt').read()
            dk('export', nr, f'{tmp}/ge_{lab}.gltf', '--ft', pl, '--lod', 'high')
            mdls = {'all': Model(f'{tmp}/ge_{lab}.gltf')}
            for side, names in GENO_DOBJS.items():
                idx = [re.search(rf'd(\d+)\s+high {n}\s', log).group(1) for n in names.split(',')]
                dk('export', nr, f'{tmp}/ge_{lab}_{side}.gltf', '--dobjs', ','.join(idx))
                mdls[side] = Model(f'{tmp}/ge_{lab}_{side}.gltf')
            rig = f'{WORK}/rig/rig_model.json'
            md = movedata('Ge', pl, aj, nr, rig)
            os.makedirs(f'{tmp}/fk_{lab}', exist_ok=True)
            sc = next(iter(md.values()))['scale']
            rows += measure('Ge', lab, GENO, pl, aj, nr, lambda side, part, m=mdls: m[side] if part == 'rocket' else m['all'],
                             md, sc, f'{tmp}/fk_{lab}')
    json.dump(rows, open(out, 'w'), indent=0)
    print(out, len(rows), 'rows')
    if out_md: write_md(rows, out_md)


def peaks(rows):
    """per (fighter, build, move): the striking hand on the move's first active frame (the hand nearer its hitbox), its
    largest growth over the active frames, and the mean cover over them"""
    by = {}
    for r in rows:
        if 'hit' in r: by.setdefault((r['fighter'], r['build'], r['move']), []).append(r)
    out = []
    for (c, b, m), rs in by.items():
        f0 = min(r['frame'] for r in rs)
        h = min((r for r in rs if r['frame'] == f0), key=lambda r: r['dist'])
        same = [r for r in rs if r['hand'] == h['hand']]
        pk = max(same, key=lambda r: r['s'])
        out.append(dict(fighter=c, build=b, move=m, part=h.get('part', 'hand'), frame=f0, hand=h['hand'], s=h['s'], r=h['r'], w=h['w'], hit=h['hit'][2],
                        cover=h['cover'], peak_frame=pk['frame'], peak_s=pk['s'], peak_cover=pk['cover'],
                        mean_cover=round(sum(r['cover'] for r in same) / len(same), 3), rest_r=round(h['r'] / h['s'], 3)))
    return out


def write_md(rows, path):
    L = ['# Fist readability: the fist against its hitbox', '',
         'Measured by `director/labs/fist_read.py`: the hand\'s mesh posed by the move\'s animation (scale included) and seen '
         'side-on, in world units (ModelScale applied). s: the hand\'s effective scale; r: the silhouette\'s equivalent radius '
         '(sqrt(area / pi)); w: its widest extent; hit: the nearest active hitbox; cover: r / hitbox radius; r/s: the '
         'silhouette at scale 1.', '', '## On the first active frame', '',
         '| Fighter | Build | Move | Part | Frame | Side | s | r | w | Hit r | Cover | Largest s (frame) | Mean cover (active) | r/s |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for p in peaks(rows):
        L.append(f"| {NAME[p['fighter']]} | {p['build']} | {p['move']} | {p['part']} | {p['frame']} | {p['hand']} | {p['s']} | {p['r']} | {p['w']} "
                 f"| {p['hit']} | **{p['cover']}** | {p['peak_s']} ({p['peak_frame']}) | {p['mean_cover']} | {p['rest_r']} |")
    L += ['', '## Every active frame', '',
          '| Fighter | Build | Move | Part | Frame | Side | s | r | w | Hit r | Dist | Cover |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        if 'hit' not in r: continue
        L.append(f"| {NAME[r['fighter']]} | {r['build']} | {r['move']} | {r.get('part', 'hand')} | {r['frame']} | {r['hand']} | {r['s']} | {r['r']} | {r['w']} "
                 f"| {r['hit'][2]} | {r['dist']} | {r['cover']} |")
    open(path, 'w').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
