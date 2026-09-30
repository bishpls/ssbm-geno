"""Look at Geno's throws offline on the production model (locoview's skinned glTF): the weapon forms each frame shows
(the script's model commands), the held opponent's pivot (ThrowN) and its path, the release point, and each shot's muzzle
and line. For iterating on the motion; the game is the judge (the victim's own animation, effects, the camera).

    GENO_MODEL=~/games/melee/sandbox/model_snap_2 .venv/bin/python projects/geno/rig/throwview.py OUT.png --throw ThrowF \
        [--frames 0:36:2] [--view side|34|front|back34] [--hold ground]
--hold ground starts the throw on the ground-attacks lane's CatchWait (the left hand gripping, the right cocked, finger
out) instead of whatever moves.py registers here.
"""
import argparse, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig, locoview
import poses_throws as T
import taro

ARM_MESHES = [('forearm_{s}', 'palm_{s}', 'fingers_{s}'), ('forearm_{s}_arm1', 'palm_{s}_arm1'), ('forearm_{s}_arm2',), ()]
FORM_MESH = {'fshot': 'fshot_{s}', 'gun': 'gun_{s}', 'stargun': 'stargun_{s}', 'cannon': 'cannon_{s}', 'beam': 'beam_{s}',
             'rocket': 'rocket_{s}'}
ALL_FORM = {m.format(s=s) for m in FORM_MESH.values() for s in 'LR'} | \
           {m.format(s=s) for lvl in ARM_MESHES for m in lvl for s in 'LR'}


def visible(forms):
    """mesh names shown for {side: form}"""
    show = set()
    for s in 'LR':
        f = forms.get(s, 'hand')
        show |= {m.format(s=s) for m in ARM_MESHES[rig.FORM_ARM[f]]}
        if f in FORM_MESH: show.add(FORM_MESH[f].format(s=s))
    return show


def fist_line(name='ThrowF', start=None, fox=1.45):
    """The forward throw's read, in numbers: the rocket fist's line (the path the fist flies: from the hand on the frame
    before it launches to the hand on the release) and, each frame to the release, how far the held opponent sits off it: their body's centre (the mean of
    their skeleton's joints, their victim animation at Fox's size, XRotN held to ThrowN as the engine holds it) and ThrowN
    itself, perpendicular to the line in the side plane (+ above it), and how far along it. {'origin', 'dir', 'deg',
    'launch', 'rows': [(frame, centre_off, top_off, centre_along, throwN_off, hand_y)]}: top_off
    is their highest joint's (their head's)"""
    th = T.THROWS[name]
    keys = dict(th.keys(start))
    victim = T.victim_poses(name)
    ext = [f for f in range(1, th.n + 1) if abs(T.params_from_pose(keys[f]).get('Rext', 0.0)) > 1e-3]
    f0 = ext[0] - 1                                        # the frame before the launch
    W0 = T.world(keys[f0])
    tr0 = keys[f0].trans.get('TransN', (0.0, 0.0, 0.0))
    o = np.array(T.joint(W0, 'RHandN', tr0))
    W1 = T.world(keys[th.release]); tr1 = keys[th.release].trans.get('TransN', (0.0, 0.0, 0.0))
    u = np.array(T.joint(W1, 'RHandN', tr1)) - o; u /= np.linalg.norm(u)   # the path it flies, launch to release
    up = np.array([0.0, u[2], -u[1]]) if u[2] >= 0 else np.array([0.0, -u[2], u[1]])   # the side plane's normal to it, up
    up /= np.linalg.norm(up)
    rows = []
    for f in range(0, th.release + 1):
        W = T.world(keys[f]); tr = keys[f].trans.get('TransN', (0.0, 0.0, 0.0))
        thn = np.array(T.joint(W, 'ThrowN', tr))
        hand = np.array(T.joint(W, 'RHandN', tr))
        c, ref, pts = thn, None, {}
        if f in victim:
            pts, par, xr = taro.skeleton_world(victim[f], fox)
            ref = np.array(pts[xr])
            c = np.mean([np.array(p) - ref for p in pts.values()], axis=0) + thn
        d = c - o
        top = max(float((np.array(p) - ref + thn - o) @ up) for p in pts.values()) if f in victim else float((thn - o) @ up)
        rows.append((f, round(float(d @ up), 2), round(top, 2), round(float(d @ u), 2), round(float((thn - o) @ up), 2),
                     round(float(hand[1]), 2)))
    return dict(origin=[round(float(x), 2) for x in o], world=[float(x) for x in o + np.array(tr0)], dir=[round(float(x), 3) for x in u], launch=f0 + 1,
                deg=round(math.degrees(math.atan2(u[1], math.hypot(u[0], u[2]))), 1), rows=rows)


def render(out, name, frames, view_name='side', start=None, S=12, cols=9, cell=(330, 340)):
    mdl = locoview.load_model()
    th = T.THROWS[name]
    keys = dict(th.keys(start))
    ev = th.events
    victim = T.victim_poses(name)
    R = locoview.view(*locoview.VIEWS[view_name])
    rows = (len(frames) + cols - 1) // cols
    img = Image.new('RGB', (cell[0] * min(cols, len(frames)), cell[1] * rows + 26), (46, 48, 60))
    d = ImageDraw.Draw(img)
    d.text((8, 6), f'{name} ({th.n} frames) {view_name}: release {th.release}, shots {th.shots}', fill=(230, 230, 240))
    line = fist_line(name, start) if name == 'ThrowF' else None      # the rocket fist's flight line, drawn to the release
    path = []
    for f in range(th.n + 1):
        W = locoview.pose_world({k: v for k, v in keys[f].solve().items()})
        path.append(np.array(W['ThrowN'][3][:3]))
    for i, f in enumerate(frames):
        pose = keys[f]
        W = locoview.pose_world(pose.solve())
        show = visible(th.forms_at(f))
        parts = [(n, t) for n, t in mdl.tris(W) if (n not in ALL_FORM or n in show) and not n.startswith('fc_')]   # (fc_: Geno Flash's cannon)
        ox, oy = (i % cols) * cell[0] + cell[0] // 2, 26 + (i // cols) * cell[1] + cell[1] - 50
        d.line([(ox - cell[0] // 2 + 4, oy), (ox + cell[0] // 2 - 4, oy)], fill=(90, 94, 120))
        locoview.draw(img, parts, R, ox, oy, S)
        P = lambda p: (ox + (R @ p)[0] * S, oy - (R @ p)[1] * S)
        for k in range(1, len(path)):                    # the held opponent's pivot, over the whole throw
            if k <= th.release:
                d.line([P(path[k - 1]), P(path[k])], fill=(90, 200, 255) if k <= f else (70, 90, 120), width=1)
        if f <= th.release and f in victim:             # the opponent: its victim animation on Mario's skeleton, at Fox's size
            pts, par, xr = taro.skeleton_world(victim[f], 1.45)
            o = np.array(pts[xr])
            for j, q in par.items():
                a, b = np.array(pts[q]) - o + path[f], np.array(pts[j]) - o + path[f]
                d.line([P(a), P(b)], fill=(255, 150, 90) if (a[0] + b[0]) / 2 > path[f][0] + 0.5 else (90, 200, 255), width=2)
        if line and f <= th.release:
            o, u = np.array(line['world']), np.array(line['dir'])
            d.line([P(o - u * 2), P(o + u * 14)], fill=(255, 230, 90), width=1)
            row = line['rows'][f]
            d.text(((i % cols) * cell[0] + 5, 26 + (i // cols) * cell[1] + 18), f'centre {row[1]:+.1f} head {row[2]:+.1f}',
                   fill=(255, 230, 90))
        if f == th.release:
            x, y = P(path[f]); d.text((x + 5, y - 12), 'release', fill=(90, 200, 255))
        if f in th.shots:                                 # the shot's muzzle and its line
            h = np.array(W['RHandN'])
            m0 = np.array([th.muzzle, 0, 0, 1.0]) @ h
            d0 = (np.array([1.0, 0, 0, 0]) @ h)[:3]
            a, b = P(m0[:3]), P(m0[:3] + d0 * 14)
            d.line([a, b], fill=(255, 230, 90), width=2); d.ellipse([a[0] - 3, a[1] - 3, a[0] + 3, a[1] + 3], fill=(255, 230, 90))
        forms = th.forms_at(f)
        tag = ' '.join(f'{s}:{v}' for s, v in sorted(forms.items()) if v != 'hand')
        d.text(((i % cols) * cell[0] + 5, 26 + (i // cols) * cell[1] + 4), f'{f} {tag} {ev.get(f, "")}', fill=(230, 230, 240))
    img.save(out)
    print('wrote', out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--throw', required=True); ap.add_argument('--frames', default='')
    ap.add_argument('--view', default='side'); ap.add_argument('--hold', default=''); ap.add_argument('--cols', type=int, default=10)
    ap.add_argument('--scale', type=float, default=12)
    ap.add_argument('--line', action='store_true', help='print the forward throw\'s victim-to-fist-line numbers')
    a = ap.parse_args()
    if a.line:
        r = fist_line(a.throw, start=T.GROUND_HOLD if a.hold == 'ground' else None)
        print(f"{a.throw}: the fist launches on {r['launch']} from {r['origin']} along {r['dir']} ({r['deg']} deg up)")
        print('frame  centre_off  top_off  along  ThrowN_off  hand_y')
        for row in r['rows']: print('%5d %10.2f %8.2f %6.2f %10.2f %7.2f' % row)
        sys.exit(0)
    th = T.THROWS[a.throw]
    if a.frames:
        s = [int(x) for x in a.frames.split(':')]
        frames = list(range(s[0], (s[1] if len(s) > 1 else th.n) + 1, s[2] if len(s) > 2 else 1))
    else:
        frames = list(range(0, th.n + 1))
    render(a.out, a.throw, frames, a.view, start=T.GROUND_HOLD if a.hold == 'ground' else None, S=a.scale, cols=a.cols)
