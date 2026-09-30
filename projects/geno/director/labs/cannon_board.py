"""cannon_board.py: the numbers and the boards for Geno Flash's cannon (flash_cannon_lab.py runs; DESIGN §12).

    .venv/bin/python projects/geno/director/labs/cannon_board.py check BEFORE_RUN AFTER_RUN [OUT.json]
        what must not move, before (the Hand Cannon stub) against after (the cannon), segment by segment on the lab's own
        frames: Geno's hurtboxes on every logged frame of the Flash (HURT lines), every hit (HIT, IHIT) and every action
        Fox and Geno go through (MS); plus the cannon's visibility (VIS: on at Flash frame 26, off at 76 or at the first
        action change, a hit or a KO) and the muzzle's logged position on the shot
    .venv/bin/python projects/geno/director/labs/cannon_board.py wysiwyg OUTDIR
        what you see against what you hit, offline: the cannon's side silhouette against his hurtboxes' union per frame
    .venv/bin/python projects/geno/director/labs/cannon_board.py muzzle AFTER_RUN OUTDIR [SEGMENT]
        the fireball against the barrel: the logged muzzle (the barrel joint's tip, ftGe_FlashMuzzle) projected into the
        segment's keyed camera, and the fireball's centre found in each dumped image from the shot on (its warm core),
        back-projected onto the stage plane: the first image's distance from the muzzle, and each later image's from
        the path the C sets (muzzle + k x velocity to the sun's centre). Writes overlays and muzzle.json.
Runs are Dolphin dump folders with RUN.plan.json beside them (the lab's plan). Game renders: keep the output out of the repo.
"""
import json, math, os, re, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'fx'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'rig'))

FLASH_MS = None          # the Flash's motion state id, read from the log (the state the charge turns into)
GX = -30.0               # flash_cannon_lab.py's Geno
SUN = (30.0, 14.0)       # ftGe_SpawnFlash: ahead, up
FIREBALL_T = 5           # efge.py: frames from the muzzle to the sun's centre
CAMS = dict(side=dict(eye=(GX + 4, 7, 46), at=(GX + 4, 6, 0)), front=dict(eye=(GX + 30, 11, 34), at=(GX + 2, 5, 0)),
            back=dict(eye=(GX - 30, 12, 34), at=(GX + 1, 5, 0)), match=dict(eye=(5, 14, 150), at=(5, 12, 0)),
            hit_in=dict(eye=(GX + 4, 7, 46), at=(GX + 4, 6, 0)), hit_out=dict(eye=(GX + 4, 7, 46), at=(GX + 4, 6, 0)),
            metal=dict(eye=(GX + 4, 7, 46), at=(GX + 4, 6, 0)))
FOV, ASPECT = 30.0, 1.2173


def parse(run):
    out = dict(HURT=[], HIT=[], IHIT=[], MS=[], VIS=[], MUZZLE=[], FIREBALL=[])
    mark = -1                                   # the segment a line belongs to (the director's MARK lines)
    for line in open(os.path.join(run, 'osreport.log'), errors='replace'):
        w = line.split()
        if not w: continue
        if w[0] == 'MARK':
            mark = int(w[2])
        elif w[0] == 'HURT':
            out['HURT'].append((int(w[1]), int(w[2]), int(w[3]), tuple(float(x) for x in w[4:11])))
        elif w[0] == 'HIT':
            out['HIT'].append((int(w[1]), int(w[2]), int(w[3]), float(w[4]), int(w[5])))
        elif w[0] == 'IHIT':
            out['IHIT'].append((int(w[1]), int(w[2]), float(w[3])))
        elif w[0] == 'MS':
            out['MS'].append((int(w[1]), int(w[2]), int(w[3]), float(w[4]), float(w[5])))
        elif w[0] == 'VIS':
            out['VIS'].append((int(w[1]), int(w[2]), int(w[4]), float(w[6]), [int(x) for x in w[8:]]))
        elif line.startswith('GENO MUZZLE flash cannon'):
            m = re.search(r'fwd (-?\d+) up (-?\d+)(?: depth (-?\d+))?', line)
            a = re.search(r'anim (\d+)', line)
            out['MUZZLE'].append((mark, int(m.group(1)) / 100, int(m.group(2)) / 100, int(m.group(3) or 0) / 100,
                                  int(a.group(1)) if a else None))
        elif line.startswith('GENO FLASH fireball frame'):
            out['FIREBALL'].append(int(line.split()[-1]))
    return out


def segments(run):
    return json.load(open(run.rstrip('/') + '.plan.json'))


def in_seg(seg, s):
    return seg['start'] - 20 <= s < seg['start'] + seg['frames'] - 20


def check(before, after, out=None):
    B, A = parse(before), parse(after)
    plan = segments(after)
    assert [s['label'] for s in segments(before)] == [s['label'] for s in plan], 'the two runs are different labs'
    res = dict(segments={})
    for seg in plan:
        lab = seg['label']
        r = {}
        # hurtboxes: every logged capsule, frame by frame (the Flash's own frames: `flash` is its first)
        hb = {(s, k): v for s, p, k, v in B['HURT'] if p == 0 and in_seg(seg, s)}
        ha = {(s, k): v for s, p, k, v in A['HURT'] if p == 0 and in_seg(seg, s)}
        if hb or ha:
            keys = sorted(set(hb) | set(ha))
            miss = [k for k in keys if k not in hb or k not in ha]
            d = max((max(abs(x - y) for x, y in zip(hb[k], ha[k])) for k in keys if k in hb and k in ha), default=0.0)
            r['hurtboxes'] = dict(capsules=len(keys), frames=len({k[0] for k in keys}), max_diff=round(d, 4),
                                  unmatched=len(miss))
        # hits and actions
        for kind in ('HIT', 'IHIT'):
            b = [x for x in B[kind] if in_seg(seg, x[0])]
            a = [x for x in A[kind] if in_seg(seg, x[0])]
            r[kind] = dict(before=b, after=a, same=b == a)
        for port, who in ((0, 'geno'), (1, 'fox')):
            b = [(s, ms, x, y) for s, p, ms, x, y in B['MS'] if p == port and in_seg(seg, s)]
            a = [(s, ms, x, y) for s, p, ms, x, y in A['MS'] if p == port and in_seg(seg, s)]
            r[f'actions_{who}'] = dict(same=b == a, n=len(a), **({} if b == a else dict(before=b, after=a)))
        # the cannon: on and off (the body group, group 0), against the Flash's frames
        v = [(s, ms, anim, g) for s, p, ms, anim, g in A['VIS'] if p == 0 and in_seg(seg, s)]
        r['vis'] = [dict(frame=s, flash_frame=s - seg['flash'] + 1, state=ms, anim=anim, groups=g[:5]) for s, ms, anim, g in v]
        res['segments'][lab] = r
    res['muzzle'] = dict(before=B['MUZZLE'], after=A['MUZZLE'], fireball_frames=sorted(set(A['FIREBALL'])))
    ok = all(r.get('hurtboxes', {}).get('max_diff', 0) < 1e-3 and r['HIT']['same'] and r['IHIT']['same']
             and r['actions_fox']['same'] and r['actions_geno']['same'] for r in res['segments'].values())
    res['unchanged'] = ok
    for lab, r in res['segments'].items():
        h = r.get('hurtboxes')
        print(f"{lab:8s} hurtboxes {h['capsules'] if h else '-':>4} capsules {h['frames'] if h else '-':>3} frames max diff "
              f"{h['max_diff'] if h else '-'}  hits same {r['HIT']['same']} item hits same {r['IHIT']['same']}  "
              f"Fox's actions same {r['actions_fox']['same']}  Geno's same {r['actions_geno']['same']}")
        for x in r['vis']:
            print(f"          VIS frame {x['frame']} (Flash frame {x['flash_frame']}) state {x['state']} anim {x['anim']} groups {x['groups']}")
    print('muzzle', res['muzzle'])
    print('UNCHANGED' if ok else 'CHANGED')
    if out:
        json.dump(res, open(out, 'w'), indent=1)
    return res


# ---- the camera: Melee's perspective (vertical fov, the projection's aspect), looking from eye to at, +Y up
def cam_basis(eye, at):
    e, a = np.array(eye, float), np.array(at, float)
    f = a - e; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return e, r, u, f


def project(p, cam, W, H):
    e, r, u, f = cam_basis(cam['eye'], cam['at'])
    d = np.array(p, float) - e
    z = d @ f
    t = math.tan(math.radians(FOV) / 2)
    x, y = (d @ r) / (z * t * ASPECT), (d @ u) / (z * t)
    return ((x + 1) / 2 * W, (1 - y) / 2 * H)


def unproject(px, cam, W, H, plane_z=0.0):
    """A pixel back onto the stage plane z = plane_z."""
    e, r, u, f = cam_basis(cam['eye'], cam['at'])
    t = math.tan(math.radians(FOV) / 2)
    x, y = px[0] / W * 2 - 1, 1 - px[1] / H * 2
    d = f + r * x * t * ASPECT + u * y * t
    k = (plane_z - e[2]) / d[2]
    return e + d * k


def fireball_centre(im, near, rad):
    """The fireball's warm core in an image (H, W, 3 floats 0..1): the centroid of the bright orange-to-yellow pixels
    within rad pixels of near, weighted by their brightness; None when there are too few."""
    H, W, _ = im.shape
    x0, x1 = int(max(0, near[0] - rad)), int(min(W, near[0] + rad))
    y0, y1 = int(max(0, near[1] - rad)), int(min(H, near[1] + rad))
    c = im[y0:y1, x0:x1]
    R, G, B = c[..., 0], c[..., 1], c[..., 2]
    m = (R > 0.8) & (G > 0.45) & (R >= B)             # its white-yellow core and orange rim (the additive puff)
    if m.sum() < 12:
        return None, int(m.sum())
    ys, xs = np.nonzero(m)
    w = (R + G)[m]
    return (x0 + float((xs * w).sum() / w.sum()), y0 + float((ys * w).sum() / w.sum())), int(m.sum())


def muzzle(run, outdir, label='side'):
    """The fireball against the muzzle (see the module doc). The effect system moves a particle before it first draws it,
    so the fireball's k-th image (k = 0 on the shot's frame) shows it k + 1 velocity steps out along its path: fitting
    its centres gives the path's line, and the muzzle's distance from that line is how straight it leaves the barrel."""
    from PIL import Image, ImageDraw
    import fxsync
    os.makedirs(outdir, exist_ok=True)
    A = parse(run)
    R = fxsync.load(run)
    seg, _ = R.segment(label)
    cam = CAMS[label]
    idx = [s['label'] for s in R.plan].index(label)
    _, fwd, up, depth, anim = next(m for m in A['MUZZLE'] if m[0] == idx)
    mz = np.array([GX + fwd, up, 0.0])
    sun = np.array([GX + SUN[0], SUN[1], 0.0])
    vel = (sun - mz) / FIREBALL_T
    shot = seg['flash'] - 1 + 49          # the director frame of Flash frame 49 (Flash frame k shows on flash - 1 + k)
    load = lambda s: np.asarray(Image.open(R.path(label, s - seg['start'])).convert('RGB'), float) / 255
    rows, found = [], []
    prev = load(shot - 1)
    for k in range(0, 4):
        s = shot + k
        im = load(s)
        H, W, _ = im.shape
        head = mz + vel * (k + 1)
        hp = project(head, cam, W, H)
        new = np.clip(im - prev, 0, None).sum(-1) > 0.25                      # what lit up this frame
        c, n = fireball_centre(np.where(new[..., None], im, 0.0), hp, 70)
        world = unproject(c, cam, W, H) if c else None
        if world is not None:
            t = float(np.dot(world[:2] - mz[:2], vel[:2]) / np.dot(vel[:2], vel[:2]))
            e = vel[:2] / np.linalg.norm(vel[:2]); dd = world[:2] - mz[:2]; perp = float(e[0] * dd[1] - e[1] * dd[0])
            found.append((k, world[:2]))
        rows.append(dict(k=k, frame=s, flash_frame=49 + k, expected=[round(float(v), 3) for v in head[:2]],
                         found=[round(float(v), 3) for v in world[:2]] if world is not None else None, pixels=n,
                         steps_out=round(t, 3) if world is not None else None,
                         off_path=round(perp, 3) if world is not None else None))
        pil = Image.fromarray((im * 255).astype(np.uint8)); d = ImageDraw.Draw(pil)
        mp = project(mz, cam, W, H)
        d.line([mp[0] - 14, mp[1], mp[0] + 14, mp[1]], fill=(0, 255, 255), width=2)
        d.line([mp[0], mp[1] - 14, mp[0], mp[1] + 14], fill=(0, 255, 255), width=2)
        sp = project(sun, cam, W, H)
        d.line([mp, sp], fill=(255, 0, 255), width=1)
        if c: d.ellipse([c[0] - 7, c[1] - 7, c[0] + 7, c[1] + 7], outline=(0, 255, 0), width=2)
        d.text((10, 10), f'Flash frame {49 + k}: cyan = the barrel\'s muzzle (logged), magenta = the path the C sets, '
                         f'green = the fireball found', fill=(255, 255, 255))
        pil.save(os.path.join(outdir, f'muzzle_{label}_{49 + k}.png'))
        prev = im
    fit = None
    # the fireball's own line, back to the muzzle: from its images after the shot's (on the shot's frame the muzzle flash
    # shares its pixels at match distance), or all of them when that leaves fewer than two
    pts = [p for k, p in found if k >= 1]
    pts = pts if len(pts) >= 2 else [p for k, p in found]
    if len(pts) >= 2:
        P = np.array(pts); c0 = P.mean(0); u = np.linalg.svd(P - c0)[2][0]
        fit = dict(points=len(pts), angle_deg=round(math.degrees(math.atan2(abs(u[1]), abs(u[0]))), 3),
                   muzzle_off_line=round(float(abs(u[0] * (mz[1] - c0[1]) - u[1] * (mz[0] - c0[0]))), 3))
    import poses_air
    pitch = poses_air.cannon_channel('pitch', 49)
    res = dict(segment=label, muzzle_logged=dict(fwd=fwd, up=up, depth=depth, anim=anim),
               muzzle_model=[round(v, 3) for v in poses_air.cannon_aim(49)[2][1:]], barrel_pitch_deg=pitch,
               path_deg=round(math.degrees(math.atan2(vel[1], vel[0])), 3), fireball_line=fit, frames=rows, camera=cam)
    json.dump(res, open(os.path.join(outdir, f'muzzle_{label}.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ('frames', 'camera')}))
    for r in rows:
        print(r)
    return res


def wysiwyg(outdir, frames=(23, 32, 40, 49, 52, 60, 70, 76)):
    """What you see against what you hit, offline from the build's own data: the cannon's side silhouette (geno_cannon's
    meshes on poses_air.cannon_pose) against the union of his hurtboxes (rig.HURTBOXES on the Flash's body pose), per
    Flash frame, in the side view (+Z ahead, +Y up; the stage plane). Writes wysiwyg.json and an overlay per frame."""
    from PIL import Image, ImageDraw
    sys.path.insert(0, os.path.join(HERE, '..', '..', 'model'))
    import rig, poses_air, geno_cannon as GC
    os.makedirs(outdir, exist_ok=True)
    body = dict(poses_air.flash())
    meshes = GC.build()
    rest = {k: np.array(v) for k, v in rig.world_mats().items()}
    px, z0, y0, Wg, Hg = 0.05, -9.0, -1.0, 400, 360           # the grid: 0.05 units a cell, z -9..11, y -1..17
    zz, yy = np.meshgrid(z0 + (np.arange(Wg) + 0.5) * px, y0 + (np.arange(Hg) + 0.5) * px)
    res = []
    for f in frames:
        sol = body[f]
        pose = {k: {'t': v[0], 'r': v[1], **({'s': sol.scale[k]} if k in sol.scale else {})} for k, v in sol.solve().items()}
        W = {k: np.array(v) for k, v in rig.world_mats(pose=pose).items()}
        hurt = np.zeros((Hg, Wg), bool)
        for j, a, b, r, h, g in rig.HURTBOXES:
            A = np.array(rig.xform(a, W[j].tolist())); B = np.array(rig.xform(b, W[j].tolist()))
            d = B[[2, 1]] - A[[2, 1]]; L2 = float(d @ d) or 1e-9
            t = np.clip(((zz - A[2]) * d[0] + (yy - A[1]) * d[1]) / L2, 0, 1)
            hurt |= np.hypot(zz - (A[2] + t * d[0]), yy - (A[1] + t * d[1])) <= r
        can = np.zeros((Hg, Wg), bool)
        img = Image.new('L', (Wg, Hg), 0); dr = ImageDraw.Draw(img)
        for m in meshes:
            V = np.array(m.V)
            P = np.zeros_like(V)
            for i, (v, w) in enumerate(zip(V, m.W)):
                j = max(w, key=w.get)
                M = np.linalg.inv(rest[j]) @ W[j]
                P[i] = (np.append(v, 1.0) @ M)[:3]
            for fc in m.F:
                q = [((P[i][2] - z0) / px, (P[i][1] - y0) / px) for i in fc]
                dr.polygon(q, fill=255)
        can = np.asarray(img)[::1] > 0
        a_c, a_h, a_i = can.sum() * px * px, hurt.sum() * px * px, (can & hurt).sum() * px * px
        res.append(dict(flash_frame=f, cannon_area=round(float(a_c), 2), hurt_area=round(float(a_h), 2),
                        cannon_covered=round(float(a_i / a_c), 3) if a_c else None,
                        hurt_outside_cannon=round(float((a_h - a_i) / a_h), 3) if a_h else None))
        rgb = np.zeros((Hg, Wg, 3), np.uint8) + 24
        rgb[can] = (60, 110, 230); rgb[hurt & ~can] = (240, 200, 40); rgb[hurt & can] = (80, 200, 120)
        Image.fromarray(rgb[::-1]).resize((Wg * 2, Hg * 2), Image.NEAREST).save(os.path.join(outdir, f'wysiwyg_{f}.png'))
        print(res[-1])
    json.dump(res, open(os.path.join(outdir, 'wysiwyg.json'), 'w'), indent=1)
    return res


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'check':
        check(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    elif cmd == 'wysiwyg':
        wysiwyg(sys.argv[2])
    elif cmd == 'muzzle':
        muzzle(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else 'side')
