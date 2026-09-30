"""Look at Geno's authored moves offline on the production model, as the scripts dress them: the weapon forms and hand
poses each script sets (visibility groups and part poses, replayed frame by frame), the hitboxes it opens (on the bones
they ride, or on TopN), and ThrowN (the held opponent) as a cross. The game is the judge; this is for iterating.

    GENO_MODEL=~/games/melee/sandbox/geno-atk-ground/model_snap_2 .venv/bin/python projects/geno/rig/atkview.py OUT.png \
        --move AttackS3S [--frames 0:30:1] [--view side|34|front|back34] [--cols 16]
Frames follow datkit movedata's convention: action frame n is drawn with animation frame n and the hitboxes active on it.
"""
import argparse, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig, fcmd, anims
import locoview as LV

FORM_MESH = {1: 'fshot', 2: 'gun', 3: 'stargun', 4: 'cannon', 5: 'beam', 6: 'rocket'}
ARM_MESH = {0: ('forearm_{s}', 'palm_{s}', 'fingers_{s}'), 1: ('forearm_{s}_arm1', 'palm_{s}_arm1'), 2: ('forearm_{s}_arm2',),
            3: ()}
GROUP_SIDE = {1: ('R', 'arm'), 2: ('R', 'form'), 3: ('L', 'arm'), 4: ('L', 'form')}
ALL_ARM = {f.format(s=s) for s in 'LR' for v in ARM_MESH.values() for f in v}
ALL_FORM = {f'{m}_{s}' for s in 'LR' for m in FORM_MESH.values()}


# ---- a script's timeline: patch Script to log what each command does, by action frame
def record():
    S = fcmd.Script
    if getattr(S, '_logged', False): return
    init = S.__init__

    def __init__(self):
        init(self); self.log = []
    S.__init__ = __init__
    for name in ('hitbox', 'clear', 'remove', 'model', 'part_pose', 'release', 'smash_charge', 'iasa'):
        orig = getattr(S, name)
        def wrap(self, *a, _o=orig, _n=name, **k):
            self.log.append((max(1, self.frame), _n, a, k))
            return _o(self, *a, **k)
        setattr(S, name, wrap)
    S._logged = True


def timeline(script, n):
    """per action frame 0..n: {'hits': {id: (part, size, off)}, 'groups': {g: opt}, 'poses': {part: pose}, 'marks': [...]}"""
    hits, groups, poses = {}, {}, {}
    out = []
    ev = sorted(getattr(script, 'log', []), key=lambda e: e[0]) if script else []
    i = 0
    for f in range(n + 1):
        marks = []
        while i < len(ev) and ev[i][0] <= f:
            _, name, a, k = ev[i]
            if name == 'hitbox':
                hid, part, dmg, size = a[0], a[1], a[2], a[3]
                off = a[4] if len(a) > 4 else k.get('off', (0, 0, 0))
                hits[hid] = (part if isinstance(part, str) else fcmd.PARTS[part], size, off)
            elif name == 'clear': hits = {}
            elif name == 'remove': hits.pop(a[0], None)
            elif name == 'model': groups[a[0]] = a[1]
            elif name == 'part_pose': poses[a[0]] = a[1]
            else: marks.append(name)
            i += 1
        out.append(dict(hits=dict(hits), groups=dict(groups), poses=dict(poses), marks=marks))
    return out


def visible(groups):
    """mesh names hidden by the visibility groups' options"""
    hide = set(ALL_FORM)
    for s, (ag, fg) in rig.FORM_GROUPS.items():
        ao, fo = groups.get(ag, 0), groups.get(fg, 0)
        hide |= {f.format(s=s) for v in ARM_MESH.values() for f in v} - {f.format(s=s) for f in ARM_MESH[ao]}
        if fo in FORM_MESH: hide.discard(f'{FORM_MESH[fo]}_{s}')
    return hide


def hand_overrides(poses):
    """joint -> local r for the hands' part poses (rig.HAND_POSES, the right mirrored), as rig.part_poses_export"""
    out = {}
    for part, k in poses.items():
        if part == rig.PART['cap']:
            for j, r in rig.CAP_POSES[k].items(): out[j] = r
            continue
        side = 'L' if part == rig.PART['L'] else 'R'
        for j, r in rig.HAND_POSES[k].items():
            if side == 'R': j, r = 'R' + j[1:], (-r[0], -r[1], r[2])
            out[j] = r
    return out


def posed(pose, poses):
    """a Pose -> {'t', 'r'} per joint, the part poses applied"""
    sol = {k: {'t': v[0], 'r': v[1]} for k, v in pose.solve().items()}
    for j, r in hand_overrides(poses).items():
        sol[j] = dict(sol[j], r=r)
    return sol


def draw_frame(img, W, hide, st, R, ox, oy, S):
    mdl = LV.MODEL[0]
    parts = [(n, T) for n, T in mdl.tris(W) if n not in hide]
    LV.draw(img, parts, R, ox, oy, S)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for hid, (part, size, off) in st['hits'].items():
        m = np.array(W[part])
        p = np.array([*off, 1.0]) @ m
        v = p[:3] @ R.T
        od.ellipse([ox + (v[0] - size) * S, oy - (v[1] + size) * S, ox + (v[0] + size) * S, oy - (v[1] - size) * S],
                   fill=(255, 40, 40, 70), outline=(255, 90, 90, 255))
    img.paste(Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB'))


def strip(out, name, frames=None, view='side', cols=16, S=9, cell=(190, 250), label=None):
    import moves
    record()
    total, fn = moves.MOVES[name]
    script, keys = fn(None)
    anim = anims.solve_keys(total, keys)
    tl = timeline(script, total)
    import preview
    frames = frames if frames is not None else list(range(total + 1))
    R = LV.view(*LV.VIEWS[view])
    cw, ch = cell
    rows = (len(frames) + cols - 1) // cols
    img = Image.new('RGB', (cw * min(cols, len(frames)), ch * rows + 26), (46, 48, 60))
    d = ImageDraw.Draw(img)
    d.text((8, 6), label or f'{name} ({total} frames) {view}', fill=(230, 230, 240))
    names = [j[0] for j in rig.JOINTS]
    for i, f in enumerate(frames):
        st = tl[min(int(f), total)]
        sol = preview.anim_frame(anim, f)
        full = {j[0]: {'t': j[2], 'r': j[3]} for j in rig.JOINTS}
        full.update(sol)
        for j, r in hand_overrides(st['poses']).items(): full[j] = dict(full[j], r=r)
        W = rig.world_mats(pose=full)
        ox, oy = (i % cols) * cw + cw // 2 - 10, 26 + (i // cols) * ch + ch - 34
        tz = W['TransN'][3][2]
        ox -= int(tz * S) if abs(tz) > 1e-6 else 0                # root motion: keep him in the cell
        d = ImageDraw.Draw(img)
        d.line([(i % cols) * cw + 2, oy, (i % cols) * cw + cw - 2, oy], fill=(90, 94, 120))
        draw_frame(img, W, visible(st['groups']), st, R, ox, oy, S)
        d = ImageDraw.Draw(img)
        if 'ThrowN' in sol:
            v = np.array(W['ThrowN'][3][:3]) @ R.T
            px, py = ox + v[0] * S, oy - v[1] * S
            d.line([px - 5, py - 5, px + 5, py + 5], fill=(80, 255, 120), width=2)
            d.line([px - 5, py + 5, px + 5, py - 5], fill=(80, 255, 120), width=2)
        tag = f'{f:g}' + (' HIT' if st['hits'] else '') + ''.join(f' {m}' for m in st['marks'])
        d.text(((i % cols) * cw + 4, 26 + (i // cols) * ch + 3), tag, fill=(255, 220, 120) if st['hits'] else (220, 220, 235))
    img.save(out)
    print('wrote', out)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--move', required=True); ap.add_argument('--frames', default='')
    ap.add_argument('--view', default='side'); ap.add_argument('--cols', type=int, default=16)
    ap.add_argument('--scale', type=float, default=9); ap.add_argument('--cell', default='190x250')
    a = ap.parse_args()
    LV.MODEL.append(LV.Model(os.environ.get('GENO_MODEL', '~/games/melee/sandbox/geno-atk-ground/model_snap_2')))
    fr = None
    if a.frames:
        s = [float(x) for x in a.frames.split(':')]
        fr = [int(x) for x in np.arange(s[0], s[1] + 1e-6, s[2] if len(s) > 2 else 1)]
    cw, chh = map(int, a.cell.split('x'))
    strip(a.out, a.move, fr, a.view, a.cols, a.scale, (cw, chh))
