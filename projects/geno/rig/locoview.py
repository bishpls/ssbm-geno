"""Look at Geno's animations offline on the production model: the glTF (GENO_MODEL, a snapshot folder) skinned by the
solved poses (linear blend, the game's own inverse binds), flat-shaded with the painter's algorithm. For iterating on
motion without the game; the game is the judge (textures, the cape's physics and the camera are its own).

    GENO_MODEL=~/games/melee/sandbox/geno-walk/model_snap_1c .venv/bin/python projects/geno/rig/locoview.py OUT.png \
        --anim WalkMiddle [--frames 0:45:3] [--view side|34|front] [--world]
--world draws the animation in the world: the body carried forward at the attribute speed per animation frame (as the
game plays it), so planted feet should stand still over a stride; a tick marks each foot's lowest sole point per frame.
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig

COLOURS = {'boot': (122, 52, 30), 'cuff': (226, 196, 150), 'cap': (40, 90, 220), 'cape_out': (40, 90, 220),
           'cape_in': (240, 200, 40), 'collar': (245, 205, 40), 'emblem': (245, 205, 40), 'clasp': (220, 170, 40),
           'curls': (230, 110, 30), 'eye': (20, 12, 10), 'nose': (205, 140, 70)}
WOOD = (222, 160, 96)


def colour(name):
    for k, c in COLOURS.items():
        if name.startswith(k): return c
    return WOOD


class Model:
    def __init__(self, folder):
        folder = os.path.expanduser(folder)
        g = json.load(open(os.path.join(folder, 'geno.gltf')))
        buf = open(os.path.join(folder, g['buffers'][0]['uri']), 'rb').read()
        CT = {5126: np.float32, 5123: np.uint16, 5121: np.uint8, 5125: np.uint32}
        NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

        def acc(i):
            a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]
            off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
            return np.frombuffer(buf, dtype=CT[a['componentType']], count=a['count'] * NC[a['type']],
                                 offset=off).reshape(a['count'], NC[a['type']])
        sk = g['skins'][0]
        self.jnames = [g['nodes'][j].get('name') for j in sk['joints']]
        ibm = acc(sk['inverseBindMatrices']).reshape(-1, 4, 4)        # column-major: as stored, M^T of the math matrix
        self.ibm = ibm.astype(float)                                   # row-vector form: v_row @ ibm_stored
        self.parts = []
        for m in g['meshes']:
            pr = m['primitives'][0]; at = pr['attributes']
            P = acc(at['POSITION']).astype(float); J = acc(at['JOINTS_0']).astype(int); W = acc(at['WEIGHTS_0']).astype(float)
            W = W / np.maximum(W.sum(1, keepdims=True), 1e-9)
            I = acc(pr['indices']).reshape(-1, 3).astype(int)
            self.parts.append((m['name'], P, J, W, I))

    def tris(self, world):
        """world: joint name -> 4x4 row-vector world matrix (rig.world_mats). -> list of (3x3 verts, colour)"""
        M = np.zeros((len(self.jnames), 4, 4))
        for i, n in enumerate(self.jnames):
            M[i] = self.ibm[i] @ np.array(world[n]) if n in world else np.eye(4)
        out = []
        for name, P, J, W, I in self.parts:
            Ph = np.c_[P, np.ones(len(P))]
            V = np.zeros((len(P), 3))
            for k in range(4):
                V += W[:, k:k + 1] * np.einsum('ni,nij->nj', Ph, M[J[:, k]])[:, :3]
            out.append((name, V[I]))
        return out


def pose_world(pose):
    """pose: joint name -> {'t', 'r'} (or (t, r) tuples) -> rig.world_mats"""
    pd = {k: (v if isinstance(v, dict) else {'t': v[0], 'r': v[1]}) for k, v in pose.items()}
    return rig.world_mats(pose=pd)


def view(yaw, pitch):
    """rows: screen x, screen y (up), toward the viewer. yaw pi/2 is the game's side view facing right (+Z to the right,
    his right side toward the camera); 0 looks at his front."""
    cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    return Rx @ Ry


VIEWS = {'side': (math.pi / 2, 0.0), '34': (math.pi / 2 - 0.62, 0.12), 'front': (0.0, 0.05), 'back34': (math.pi / 2 + 0.62, 0.12)}


def draw(img, parts, R, ox, oy, S, light=(0.35, 0.6, 0.72)):
    d = ImageDraw.Draw(img)
    faces = []
    L = np.array(light) / np.linalg.norm(light)
    for name, T in parts:
        V = T @ R.T                                                    # (n, 3, 3) in view space
        n = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        n *= np.sign(n[:, 2:3] + 1e-9)
        k = 0.42 + 0.58 * np.clip(n @ L, 0, 1)
        c = np.array(colour(name))
        z = V[:, :, 2].mean(1)
        for i in range(len(V)):
            faces.append((z[i], [(ox + V[i, j, 0] * S, oy - V[i, j, 1] * S) for j in range(3)], tuple((c * k[i]).astype(int))))
    faces.sort(key=lambda f: f[0])
    for _, pts, col in faces:
        d.polygon(pts, fill=col)


def sole_low(world, side):
    """the lowest point of a boot (sole corners in the foot's frame), world y and z"""
    m = np.array(world[f'{side}FootJ'])
    pts = np.array([[x, y, z, 1] for x in (-0.85, 0.0, 1.3, 1.8, 2.1) for y in (0.95, 0.8) for z in (-0.6, 0.6)])
    w = pts @ m
    i = int(np.argmin(w[:, 1]))
    return w[i, :3]


def strip(out, frames_poses, view_name='side', S=11, cols=12, label='', world_speed=None, notes=None, cell=(260, 300)):
    mdl = MODEL[0]
    R = view(*VIEWS[view_name])
    cw, ch = cell
    rows = (len(frames_poses) + cols - 1) // cols
    img = Image.new('RGB', (cw * min(cols, len(frames_poses)), ch * rows + 26), (46, 48, 60))
    d = ImageDraw.Draw(img)
    d.text((8, 6), label, fill=(230, 230, 240))
    for i, (f, pose) in enumerate(frames_poses):
        W = pose_world(pose)
        parts = mdl.tris(W)
        ox, oy = (i % cols) * cw + cw // 2, 26 + (i // cols) * ch + ch - 40
        shift = -(world_speed or 0.0) * f                              # the floor slides back under a moving body
        d.line([(ox - cw // 2 + 4, oy), (ox + cw // 2 - 4, oy)], fill=(90, 94, 120))
        for gx in range(-60, 61, 1):
            z = gx + (shift % 1.0) if world_speed else gx
            p = np.array([0, 0, z]) @ R.T
            if abs(p[0] * S) > cw // 2 - 4: continue
            big = world_speed and (round(z - shift) % 5 == 0)
            d.line([(ox + p[0] * S, oy + 2), (ox + p[0] * S, oy + (10 if big else 5))], fill=(150, 154, 190) if big else (90, 94, 120))
        draw(img, parts, R, ox, oy, S)
        d = ImageDraw.Draw(img)
        d.text(((i % cols) * cw + 5, 26 + (i // cols) * ch + 4), f'{f:g}' + (f' {notes[f]}' if notes and f in notes else ''),
               fill=(230, 230, 240))
    img.save(out)
    print('wrote', out)
    return out


MODEL = []


def load_model():
    if not MODEL:
        MODEL.append(Model(os.environ.get('GENO_MODEL', '~/games/melee/sandbox/geno-walk/model_snap_1c')))
    return MODEL[0]


def anim_poses(anim, frames):
    import preview
    return [(f, preview.anim_frame(anim, f)) for f in frames]


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--anim', required=True); ap.add_argument('--frames', default='')
    ap.add_argument('--view', default='side'); ap.add_argument('--world', action='store_true'); ap.add_argument('--cols', type=int, default=12)
    ap.add_argument('--json', help='anims.json to read (default: build the animation now)')
    ap.add_argument('--scale', type=float, default=11); ap.add_argument('--cell', default='260x300')
    a = ap.parse_args()
    load_model()
    if a.json:
        anim = json.load(open(a.json))['anims'][a.anim]
    else:
        import anims, locomotion
        got = locomotion.anim(a.anim)
        if got is None:                                   # a state registered in moves.MOVES (states_air, states, moves)
            import moves, states_air
            states_air.register()
            n_, fn = moves.MOVES[a.anim]
            got = (n_, fn(None)[1])
        anim = anims.solve_keys(*got)
    n = anim['frames']
    if a.frames:
        s = [float(x) for x in a.frames.split(':')]
        frames = list(np.arange(s[0], (s[1] if len(s) > 1 else n) + 1e-6, s[2] if len(s) > 2 else 1))
    else:
        frames = list(range(0, n + 1))
    import locomotion
    ws = locomotion.SPEED.get(a.anim) if a.world else None
    cw, chh = map(int, a.cell.split('x'))
    strip(a.out, anim_poses(anim, frames), a.view, S=a.scale, cols=a.cols, label=f'{a.anim} ({n} frames) {a.view}', world_speed=ws, cell=(cw, chh))
