"""Look at one of Geno's moves offline, as its script and animation play it: the production model (GENO_MODEL, a snapshot
folder) skinned by the solved poses, with the weapon forms and hand poses its script sets on each frame and its hitboxes
(red; bursts on TopN and spheres riding bones) where the script opens them. For iterating on motion without the game; the
game is the judge (the cape's physics, the lighting and the camera are its own).

    GENO_MODEL=~/games/melee/sandbox/model_snap_2 .venv/bin/python projects/geno/rig/moveview.py OUT.png --move AttackAirF \
        [--frames 0:36:1] [--view side|34|front|back34] [--cols 12] [--scale 9] [--mirror]
Frames are action frames counted from 0 (the pose shown is the animation at that frame, as datkit movedata poses it); a
hitbox from s.at(9) shows from frame 9. --mirror draws the far side (the game facing left: the camera sees his left side).
"""
import argparse, math, os, struct, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig, anims, fcmd
import locoview

ARM_LEVEL = [('forearm', 'palm', 'fingers'), ('forearm_{s}_arm1', 'palm_{s}_arm1'), ('forearm_{s}_arm2',), ()]


def script_timeline(data, n):
    """Interpret a move script (fcmd layouts): per action frame 0..n, the open hitboxes {id: (part, offset, radius)}, the
    visibility groups {group: option}, the part poses {part: pose} and the frames that raise the flag (projectile spawns)."""
    words = lambda o, k: struct.unpack('>' + 'I' * k, data[o:o + 4 * k])
    ev, o, frame = [], 0, 1
    sizes = [5, 5, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 7, 4, 1, 1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1, 1, 3, 3, 2, 1, 4]
    while o < len(data):
        w0 = words(o, 1)[0]; op = w0 >> 26
        if op == 0: break
        nw = (2 if op in (5, 7) else 1) if op < 10 else sizes[op - 10]
        if op == 0x02: frame = w0 & 0x3FFFFFF
        elif op == 0x01: frame += w0 & 0x3FFFFFF
        elif op == 0x0B:
            w = words(o, 5)
            hid, bone = (w[0] >> 23) & 7, (w[0] >> 11) & 0xFF
            s16 = lambda v: (v - 0x10000 if v & 0x8000 else v) / 256
            size, ox = s16(w[1] >> 16), s16(w[1] & 0xFFFF)
            oy, oz = s16(w[2] >> 16), s16(w[2] & 0xFFFF)
            ev.append((frame, 'hit', hid, (fcmd.PARTS[bone], (ox, oy, oz), size)))
        elif op == 0x0F: ev.append((frame, 'remove', w0 & 0x3FFFFFF, None))
        elif op == 0x10: ev.append((frame, 'clear', None, None))
        elif op == 0x1F: ev.append((frame, 'model', (w0 >> 19) & 0x7F, w0 & 0x7FFFF))
        elif op == 0x20: ev.append((frame, 'revert', None, None))
        elif op == 0x29: ev.append((frame, 'pose', (w0 >> 19) & 0x7F, (w0 >> 12) & 0x7F))
        elif op == 0x18: ev.append((frame, 'flag', None, None))
        o += 4 * nw
    out, hits, groups, poses, flags = [], {}, {}, {}, set()
    for f in range(n + 1):
        for fr, kind, a, b in ev:
            if fr != max(f, 1) or (f == 0 and fr != 1): continue
            if kind == 'hit': hits[a] = b
            elif kind == 'remove': hits.pop(a, None)
            elif kind == 'clear': hits.clear()
            elif kind == 'model': groups[a] = b
            elif kind == 'revert': groups.clear()
            elif kind == 'pose': poses[a] = b
            elif kind == 'flag': flags.add(f)
        out.append((dict(hits), dict(groups), dict(poses)))
    return out, flags


def visible(name, groups):
    """Is glTF mesh `name` shown under these visibility groups (rig.FORM_GROUPS; every group defaults to option 0)?"""
    if name.startswith('fc_'):                          # Geno Flash's cannon: group 0's option 1, off in every move
        return False
    for s, (ag, fg) in rig.FORM_GROUPS.items():
        lvl = ARM_LEVEL[groups.get(ag, 0)]
        base = [x.format(s=s) if '{' in x else f'{x}_{s}' for x in lvl]
        if name in (f'forearm_{s}', f'palm_{s}', f'fingers_{s}', f'forearm_{s}_arm1', f'palm_{s}_arm1', f'forearm_{s}_arm2'):
            return name in base
        for k, form in enumerate(rig.FORMS[1:], 1):
            if name == f'{form}_{s}':
                return groups.get(fg, 0) == k
    return True


def posed(solved, poses):
    """Apply the script's part poses (hands, cap) to a solved frame (joint -> {'t','r'})."""
    out = {k: dict(v) for k, v in solved.items()}
    idx = {j[0]: j for j in rig.JOINTS}
    for part, k in poses.items():
        if part in (0, 1):
            side = 'L' if part == 0 else 'R'
            for n, r in rig.HAND_POSES[k].items():
                if side == 'R': n, r = 'R' + n[1:], (-r[0], -r[1], r[2])
                out.setdefault(n, {'t': idx[n][2], 'r': idx[n][3]})['r'] = r
        elif part == 2:
            for n, r in rig.CAP_POSES[k].items():
                out.setdefault(n, {'t': idx[n][2], 'r': idx[n][3]})['r'] = r
    return out


def render(out, anim, timeline, frames, view='side', cols=12, S=9.0, cell=(230, 270), label='', flags=(), mirror=False,
           oy_frac=0.8):
    mdl = locoview.load_model()
    yaw, pitch = locoview.VIEWS[view]
    if mirror: yaw = -yaw
    R = locoview.view(yaw, pitch)
    cw, ch = cell
    rows = (len(frames) + cols - 1) // cols
    img = Image.new('RGB', (cw * min(cols, len(frames)), ch * rows + 26), (46, 48, 60))
    d = ImageDraw.Draw(img)
    d.text((8, 6), label, fill=(230, 230, 240))
    import preview
    for i, f in enumerate(frames):
        hits, groups, poses = timeline[min(int(f), len(timeline) - 1)]
        sol = posed(preview.anim_frame(anim, f), poses)
        W = rig.world_mats(pose=sol)
        parts = [(nm, T) for nm, T in mdl.tris(W) if visible(nm, groups)]
        ox, oy = (i % cols) * cw + cw // 2, 26 + (i // cols) * ch + int(ch * oy_frac)
        g0 = np.array([0, 0, -40]) @ R.T; g1 = np.array([0, 0, 40]) @ R.T
        d.line([(ox + g0[0] * S, oy - g0[1] * S), (ox + g1[0] * S, oy - g1[1] * S)], fill=(90, 94, 120))
        locoview.draw(img, parts, R, ox, oy, S)
        if hits:
            ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            for hid, (part, off, r) in sorted(hits.items()):
                c = np.array(rig.xform(off, W[part])) @ R.T
                od.ellipse([ox + (c[0] - r) * S, oy - (c[1] + r) * S, ox + (c[0] + r) * S, oy - (c[1] - r) * S],
                           fill=(255, 40, 40, 70), outline=(255, 90, 90, 255))
            img.paste(Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB'))
        d = ImageDraw.Draw(img)
        tag = f'{f:g}' + (' HIT' if hits else '') + (' FLAG' if int(f) in flags else '')
        d.text(((i % cols) * cw + 5, 26 + (i // cols) * ch + 4), tag, fill=(255, 220, 120) if hits or int(f) in flags else (230, 230, 240))
    img.save(out)
    print('wrote', out)
    return out


def load_move(name):
    import moves
    frames, fn = moves.MOVES[name]
    s, keys = fn(None)
    anim = anims.solve_keys(frames, keys)
    data = s.bytes() if s is not None else b'\0\0\0\0'
    tl, flags = script_timeline(data, frames)
    return frames, anim, tl, flags


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--move', required=True); ap.add_argument('--frames', default='')
    ap.add_argument('--view', default='side'); ap.add_argument('--cols', type=int, default=12)
    ap.add_argument('--scale', type=float, default=9); ap.add_argument('--cell', default='230x270')
    ap.add_argument('--mirror', action='store_true'); ap.add_argument('--oy', type=float, default=0.8)
    a = ap.parse_args()
    n, anim, tl, flags = load_move(a.move)
    if a.frames:
        s = [float(x) for x in a.frames.split(':')]
        frames = [int(x) for x in np.arange(s[0], (s[1] if len(s) > 1 else n) + 1e-6, s[2] if len(s) > 2 else 1)]
    else:
        frames = list(range(0, n + 1))
    cw, chh = map(int, a.cell.split('x'))
    render(a.out, anim, tl, frames, a.view, a.cols, a.scale, (cw, chh), f'{a.move} ({n} frames) {a.view}', flags, a.mirror,
           a.oy)
