"""Look at the rig: flat-shaded orthographic views of Geno's block model in any pose, beside the rest skeletons of Mario and
Marth at game scale (from `datkit rest`, if present in the work folder).
    .venv/bin/python projects/geno/rig/preview.py OUT.png [--pose NAME] [--anim NAME --frames a,b,c]
"""
import argparse, json, math, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig

WORK = os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work'))
LIGHT = (0.35, 0.6, 0.72)


def tris_world(pose=None):
    W = rig.world_mats(pose=pose)
    out = []
    for j, shape, c, s, col, *rot in rig.BLOCKS:
        for tri in rig.block_tris(shape, c, s, *rot):
            out.append(([rig.xform(p, W[j]) for p in tri], rig.C[col]))
    return out, W


def view_rot(yaw, pitch):
    cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    def f(p):
        x, y, z = p[0] * cy + p[2] * sy, p[1], -p[0] * sy + p[2] * cy
        return (x, y * cp - z * sp, y * sp + z * cp)      # +z toward the viewer
    return f


def draw(img, tris, yaw, pitch, ox, oy, scale):
    d = ImageDraw.Draw(img)
    f = view_rot(yaw, pitch)
    faces = []
    for tri, col in tris:
        v = [f(p) for p in tri]
        e1 = [v[1][i] - v[0][i] for i in range(3)]; e2 = [v[2][i] - v[0][i] for i in range(3)]
        n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
        ln = math.sqrt(sum(x * x for x in n)) or 1
        n = [x / ln for x in n]
        if n[2] < 0: n = [-x for x in n]                       # two-sided shading for the preview
        k = 0.45 + 0.55 * max(0, sum(n[i] * LIGHT[i] for i in range(3)))
        faces.append((sum(p[2] for p in v) / 3, [(ox + p[0] * scale, oy - p[1] * scale) for p in v],
                      tuple(int(c * k) for c in col)))
    for _, pts, col in sorted(faces, key=lambda t: t[0]):
        d.polygon(pts, fill=col)


def draw_ref(img, path, sc, ox, oy, scale, colour):
    if not os.path.exists(path): return
    J = [json.loads(l) for l in open(path)]
    d = ImageDraw.Draw(img)
    for j in J:
        if j['p'] >= 0:
            p = J[j['p']]
            d.line([(ox + p['x'] * sc * scale, oy - p['y'] * sc * scale), (ox + j['x'] * sc * scale, oy - j['y'] * sc * scale)], fill=colour, width=2)


def sheet(out, pose=None, label=''):
    tris, _ = tris_world(pose)
    S, W, Hh = 22, 1600, 560
    img = Image.new('RGB', (W, Hh), (46, 48, 60))
    d = ImageDraw.Draw(img)
    ground = Hh - 60
    for gx in range(0, W, 40):
        d.line([(gx, ground), (gx + 20, ground)], fill=(90, 92, 110))
    for y in range(0, 21, 5):
        d.text((6, ground - y * S - 6), str(y), fill=(120, 124, 150))
        d.line([(24, ground - y * S), (W, ground - y * S)], fill=(56, 58, 72))
    draw_ref(img, os.path.join(WORK, 'rig', 'rest_Mr.jsonl'), 1.1, 150, ground, S, (220, 70, 60))
    d.text((120, ground + 12), 'Mario (rest, x1.1)', fill=(220, 70, 60))
    for i, (yaw, pitch, name) in enumerate([(0, 0, 'front'), (math.pi / 2, 0, 'side'), (math.pi, 0, 'back'), (-0.7, 0.25, '3/4')]):
        draw(img, tris, yaw, pitch, 420 + i * 270, ground, S)
        d.text((380 + i * 270, ground + 12), name, fill=(200, 200, 220))
    draw_ref(img, os.path.join(WORK, 'rig', 'rest_Ms.jsonl'), 1.15, 1480, ground, S, (90, 140, 230))
    d.text((1440, ground + 12), 'Marth (rest, x1.15)', fill=(90, 140, 230))
    if label: d.text((W // 2 - 60, 10), label, fill=(230, 230, 240))
    img.save(out)
    print('wrote', out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    a = ap.parse_args()
    sheet(a.out, label='GENO block rig: rest (T-pose)')


def pose_strip(out, poses):
    """A strip of named poses (Pose.solve() dicts), front and side views."""
    S, cell = 18, 250
    img = Image.new('RGB', (cell * len(poses), 700), (46, 48, 60))
    d = ImageDraw.Draw(img)
    for i, (label, pose) in enumerate(poses):
        solved = {k: {'t': v[0], 'r': v[1]} for k, v in pose.items()}
        tris, _ = tris_world(solved)
        draw(img, tris, 0, 0, i * cell + cell // 2, 330, S)
        draw(img, tris, math.pi / 2, 0, i * cell + cell // 2, 660, S)
        d.text((i * cell + 10, 8), label, fill=(230, 230, 240))
    img.save(out)
    print('wrote', out)


def anim_frame(anim, f):
    """A solved animation (anims.solve_keys) at frame f, keys interpolated linearly as the game plays them: joint name ->
    {'t', 'r'} (and 's' where a joint is grown, which rig.world_mats inherits)."""
    names, out = [j[0] for j in rig.JOINTS], {}
    for ji, tr in anim['tracks'].items():
        d = {}
        for k in ('t', 'r', 's'):
            if k not in tr: continue
            ks = tr[k]
            v = ks[0][1:] if f <= ks[0][0] else ks[-1][1:]
            for a, b in zip(ks, ks[1:]):
                if a[0] <= f <= b[0]:
                    u = (f - a[0]) / ((b[0] - a[0]) or 1)
                    v = [x + (y - x) * u for x, y in zip(a[1:], b[1:])]
                    break
            d[k] = v
        out[names[int(ji)]] = d
    return out


def anim_strip(out, anim, frames, geo=None, ledge=False, label='', notes=None, cols=8, S=8, yaw=math.pi / 2):
    """Side views (facing right) of an animation at chosen frames, with the measured hitboxes (datkit movedata `geo`:
    per active frame, (y, z, r) spheres in the fighter's space) in red and the floor; ledge=True draws the stage's corner
    at the origin (ledge actions move by TransN from it). notes: frame -> a short tag (e.g. 'INT' while intangible)."""
    cw, ch = 34 * S, 36 * S
    rows = (len(frames) + cols - 1) // cols
    img = Image.new('RGB', (cw * min(cols, len(frames)), ch * rows + 24), (46, 48, 60))
    d = ImageDraw.Draw(img)
    d.text((8, 6), label, fill=(230, 230, 240))
    hits = {f: sph for f, sph in (geo or [])}
    for i, f in enumerate(frames):
        ox, oy = (i % cols) * cw + (14 if ledge else 17) * S, 24 + (i // cols) * ch + (22 if ledge else 28) * S
        stage = (60, 64, 84)
        if ledge:
            d.rectangle([ox, oy, ox + 20 * S, oy + 14 * S], fill=stage)
        else:
            d.rectangle([ox - 17 * S, oy, ox + 17 * S, oy + 6 * S], fill=stage)
        tris, _ = tris_world(anim_frame(anim, f))
        draw(img, tris, yaw, 0, ox, oy, S)
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for y, z, r in hits.get(f, []):
            od.ellipse([ox + (z - r) * S, oy - (y + r) * S, ox + (z + r) * S, oy - (y - r) * S], fill=(255, 40, 40, 90),
                       outline=(255, 90, 90, 255))
        img.paste(Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB'))
        d = ImageDraw.Draw(img)
        d.text(((i % cols) * cw + 6, 24 + (i // cols) * ch + 4), f'{f}' + (f' {notes[f]}' if notes and f in notes else ''),
               fill=(255, 220, 120) if f in hits else (200, 200, 220))
    img.save(out)
    print('wrote', out)
