"""cannon_hurt.py: Geno Flash's hurtboxes against its cannon, and the cast's transformed states against their standing
hurtboxes (DESIGN §12, "What you see against what you hit"; Michael, 2026-09-29: follow the cannon, "but careful not to
make it too small").

    .venv/bin/python projects/geno/director/labs/cannon_hurt.py measure GENO_OUT_DIR OUT.json
        the side view (the stage plane: z ahead, y up), every capsule projected to a stadium and rasterised at 0.05:
        - the cast's comparable states (from the disc, `datkit bodydata --capsules`): Samus's Morph Ball (SpecialLw; the
          game swaps her capsules for one sphere of radius 3 x her scale on joint 2 while the script's flag is up,
          ftSs_SpecialLw_8012AEBC, so that sphere is what's measured, on the flag's frames 10-42), Kirby's Stone
          (SpecialLw2), Jigglypuff's Rest (SpecialLwL,
          the sleep), Yoshi's egg roll (SpecialSLoop), and two more curled forms, Jigglypuff's Rollout (SpecialN) and
          Bowser's Whirling Fortress (SpecialHi, in his shell): each held frame's (TransN, the fighter's movement, taken
          out: the body about its own root)
          union area and top, as shares of the fighter's standing (Wait, frame 0) union area and top
        - Geno standing, and in the Flash (GENO_OUT_DIR's PlGe*.dat), every frame: his area and top, the cannon's
          silhouette (geno_cannon's meshes on poses_air.cannon_pose), the share of the cannon his hurtboxes cover and the
          share of his hurtbox area outside the cannon
    .venv/bin/python projects/geno/director/labs/cannon_hurt.py report GENO_OUT_DIR research/flash_hurtboxes.md
        the same as a research table, with the guardrail (remeasure.sh runs it)
    .venv/bin/python projects/geno/director/labs/cannon_hurt.py fit OUT.json GUARD_AREA GUARD_TOP
        fit poses_air.CURL (the hidden body's curl) to the cannon's silhouette on FIT_FRAMES: cover most of it, spill
        little, keep the guardrail's area and top
    .venv/bin/python projects/geno/director/labs/cannon_hurt.py overlay GENO_OUT_DIR OUTDIR
        overlays per Flash frame: the cannon blue, hurtbox only yellow, both green
"""
import json, math, os, subprocess, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
DISC = os.path.expanduser('~/games/melee/disc/files')
sys.path.insert(0, os.path.join(HERE, '..', '..', 'rig'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'model'))
PX = 0.05                                    # the raster's cell (world units)
Z0, Y0, NZ, NY = -14.0, -2.0, 560, 440       # z -14..14, y -2..20

# (fighter code, internal kind, action, label, frames held or None for all, the code-made sphere: (joint, radius x scale))
CAST = [('Ss', 13, 309, "Samus's Morph Ball (SpecialLw)", range(12, 41), (2, 3.0)),
        ('Kb', 4, 333, "Kirby's Stone (SpecialLw2)", None, None),
        ('Pr', 15, 323, "Jigglypuff's Rest (SpecialLwL, asleep)", None, None),
        ('Ys', 14, 302, "Yoshi's egg roll (SpecialSLoop)", None, None),
        ('Pr', 15, 302, "Jigglypuff's Rollout (SpecialN, rolling)", None, None),
        ('Kp', 5, 311, "Bowser's Whirling Fortress (SpecialHi, ground)", None, None)]
GENO_FLASH, GENO_KIND = 308, 34


def bodydata(files, kind, actions, joint=None):
    cmd = ['sh', f'{ROOT}/tools/machinima/melee/datkit.sh', 'bodydata', *files, f'{DISC}/PlCo.dat', str(kind), '-',
           ','.join(map(str, actions)), '--capsules'] + (['--joint', str(joint)] if joint is not None else [])
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return [json.loads(l) for l in out.splitlines() if l.startswith('{')]


_ZZ, _YY = np.meshgrid(Z0 + (np.arange(NZ) + 0.5) * PX, Y0 + (np.arange(NY) + 0.5) * PX)


def raster(caps):
    """Union of capsules [x1 y1 z1 x2 y2 z2 r] seen from the side (z, y)."""
    m = np.zeros((NY, NZ), bool)
    for x1, y1, z1, x2, y2, z2, r in caps:
        dz, dy = z2 - z1, y2 - y1
        L2 = dz * dz + dy * dy or 1e-12
        z0, z1_ = min(z1, z2) - r, max(z1, z2) + r
        y0, y1_ = min(y1, y2) - r, max(y1, y2) + r
        j0, j1 = max(0, int((z0 - Z0) / PX)), min(NZ, int((z1_ - Z0) / PX) + 2)
        i0, i1 = max(0, int((y0 - Y0) / PX)), min(NY, int((y1_ - Y0) / PX) + 2)
        ZZ, YY = _ZZ[i0:i1, j0:j1], _YY[i0:i1, j0:j1]
        t = np.clip(((ZZ - z1) * dz + (YY - y1) * dy) / L2, 0, 1)
        m[i0:i1, j0:j1] |= np.hypot(ZZ - (z1 + t * dz), YY - (y1 + t * dy)) <= r
    return m


def stats(m):
    if not m.any():
        return dict(area=0.0, top=0.0, bottom=0.0, front=0.0, back=0.0)
    ys, zs = np.nonzero(m)
    return dict(area=round(float(m.sum() * PX * PX), 2), top=round(Y0 + (ys.max() + 1) * PX, 2), bottom=round(Y0 + ys.min() * PX, 2),
                front=round(Z0 + (zs.max() + 1) * PX, 2), back=round(Z0 + zs.min() * PX, 2))


def cast():
    out = {}
    for code, kind, act, label, held, sphere in CAST:
        files = [f'{DISC}/Pl{code}.dat', f'{DISC}/Pl{code}AJ.dat', f'{DISC}/Pl{code}Nr.dat']
        o = bodydata(files, kind, [act], joint=sphere[0] if sphere else None)[0]
        stand = stats(raster(o['stand_caps']))
        frames = list(held) if held else list(range(o['frames'] + 1))
        per = []
        for f in frames:
            if sphere:                                  # the game's own hurtbox in this state: one sphere on the joint
                x, y, z = o['joint'][f]; r = sphere[1] * o['scale']
                caps = [[x, y, z, x, y, z, r]]
            else:
                caps = o['caps'][f]
            # TransN is the fighter's movement, not the body's: a root-motion action's (the engine takes it out of the
            # skeleton, ftAnim_8006E054), and the travel some loops carry (Yoshi's egg roll moves 26 units a loop, yet the
            # egg rolls on him): the body is measured about its own root
            ty, tz = o['per'][f][5], o['per'][f][6]
            if not sphere:
                caps = [[x1, y1 - ty, z1 - tz, x2, y2 - ty, z2 - tz, r] for x1, y1, z1, x2, y2, z2, r in caps]
            per.append(stats(raster(caps)))
        area = float(np.median([p['area'] for p in per])); top = float(np.median([p['top'] for p in per]))
        out[f'{code}{act}'] = dict(label=label, action=act, frames=[frames[0], frames[-1]], stand=stand,
                         held=dict(area=round(area, 2), top=round(top, 2)),
                         area_ratio=round(area / stand['area'], 3), top_ratio=round(top / stand['top'], 3),
                         min_area_ratio=round(min(p['area'] for p in per) / stand['area'], 3),
                         min_top_ratio=round(min(p['top'] for p in per) / stand['top'], 3))
        print(f"{label:45s} standing area {stand['area']:6.1f} top {stand['top']:5.2f}   held area {area:6.1f} "
              f"({area / stand['area']:.2f})  top {top:5.2f} ({top / stand['top']:.2f})")
    return out


def cannon_mask(f):
    """The cannon's side silhouette at Flash frame f (its meshes on poses_air.cannon_pose)."""
    import rig, poses_air, geno_cannon as GC
    from PIL import Image, ImageDraw
    rest = {k: np.array(v) for k, v in rig.world_mats().items()}
    cj, sc = poses_air.cannon_pose(f)
    pose = {k: {'t': v[0], 'r': v[1]} for k, v in cj.items()}
    pose['CannonN']['s'] = sc['CannonN']
    W = {k: np.array(v) for k, v in rig.world_mats(pose=pose).items()}
    img = Image.new('L', (NZ, NY), 0); d = ImageDraw.Draw(img)
    for m in GC.build():
        for fc in m.F:
            q = []
            for i in fc:
                w = m.W[i]; j = max(w, key=w.get)
                p = np.append(m.V[i], 1.0) @ (np.linalg.inv(rest[j]) @ W[j])
                q.append(((p[2] - Z0) / PX, (p[1] - Y0) / PX))
            d.polygon(q, fill=255)
    return np.asarray(img) > 0


def geno(out_dir):
    files = [f'{out_dir}/PlGe.dat', f'{out_dir}/PlGeAJ.dat', f'{out_dir}/PlGeNr.dat']
    o = bodydata(files, GENO_KIND, [GENO_FLASH])[0]
    stand = stats(raster(o['stand_caps']))
    per = []
    for f in range(o['frames'] + 1):
        h = raster(o['caps'][f])
        c = cannon_mask(f) if 23 <= f < 76 else None
        s = stats(h)
        if c is not None:
            both = (h & c).sum()
            s.update(cannon=stats(c), covered=round(float(both / c.sum()), 3), outside=round(float((h.sum() - both) / h.sum()), 3))
        per.append(dict(frame=f, **s))
    win = [p for p in per if 'covered' in p]
    full = [p for p in win if 30 <= p['frame'] <= 66]            # the cannon at full size (after the landing, before the fold)
    summ = dict(stand=stand,
                window=dict(area_min=min(p['area'] for p in win), top_min=min(p['top'] for p in win)),
                full=dict(area_median=float(np.median([p['area'] for p in full])), top_median=float(np.median([p['top'] for p in full])),
                          covered_median=float(np.median([p['covered'] for p in full])), covered_min=min(p['covered'] for p in full),
                          outside_median=float(np.median([p['outside'] for p in full])), outside_max=max(p['outside'] for p in full),
                          cannon_area=float(np.median([p['cannon']['area'] for p in full])),
                          cannon_top=float(np.median([p['cannon']['top'] for p in full]))))
    s = summ['full']
    print(f"Geno standing area {stand['area']:.1f} top {stand['top']:.2f}; Flash 30-66: area {s['area_median']:.1f} "
          f"({s['area_median'] / stand['area']:.2f}) top {s['top_median']:.2f} ({s['top_median'] / stand['top']:.2f}); cannon "
          f"area {s['cannon_area']:.1f} top {s['cannon_top']:.2f}; covered {s['covered_median']:.2f} (min {s['covered_min']:.2f}), "
          f"outside {s['outside_median']:.2f} (max {s['outside_max']:.2f})")
    return dict(summary=summ, per=per)


def measure(out_dir, out):
    res = dict(cast=cast(), geno=geno(out_dir))
    json.dump(res, open(out, 'w'), indent=1)
    return res


def overlay(out_dir, outdir, frames=(22, 23, 26, 32, 40, 49, 52, 60, 70, 75, 76)):
    from PIL import Image, ImageDraw
    os.makedirs(outdir, exist_ok=True)
    files = [f'{out_dir}/PlGe.dat', f'{out_dir}/PlGeAJ.dat', f'{out_dir}/PlGeNr.dat']
    o = bodydata(files, GENO_KIND, [GENO_FLASH])[0]
    tiles = []
    for f in frames:
        h = raster(o['caps'][f]); c = cannon_mask(f) if 23 <= f < 76 else np.zeros_like(h)
        rgb = np.zeros(h.shape + (3,), np.uint8) + 24
        rgb[c] = (60, 110, 230); rgb[h & ~c] = (240, 200, 40); rgb[h & c] = (80, 200, 120)
        rgb[int(-Y0 / PX), :] = (120, 120, 120)                                # the floor
        im = Image.fromarray(rgb[::-1][:, 100:460]); d = ImageDraw.Draw(im)
        d.text((6, 4), f'Flash frame {f}', fill=(255, 255, 255))
        im.save(os.path.join(outdir, f'hurt_{f}.png')); tiles.append(im)
    W, H = tiles[0].size
    sheet = Image.new('RGB', (W * len(tiles) + 4 * (len(tiles) - 1), H), (10, 10, 12))
    for i, t in enumerate(tiles): sheet.paste(t, (i * (W + 4), 0))
    sheet.save(os.path.join(outdir, 'hurt_sheet.png'))
    return os.path.join(outdir, 'hurt_sheet.png')


# ---- the fit: the curl's parameters (poses_air.CURL) against the cannon's silhouette, offline
FIT_FRAMES = (32, 40, 49, 52, 60)


def pose_caps(pose):
    """rig.HURTBOXES on a pose (anims.Pose or poses_air.Solved), in world (x y z pairs and the radius)."""
    import rig
    sol = pose.solve()
    sc = getattr(pose, 'scale', {})
    W = rig.world_mats(pose={k: {'t': v[0], 'r': v[1], **({'s': sc[k]} if k in sc else {})} for k, v in sol.items()})
    out = []
    for j, a, b, r, h, g in rig.HURTBOXES:
        A, B = rig.xform(a, W[j]), rig.xform(b, W[j])
        k = math.sqrt(sum(v * v for v in W[j][0][:3]))           # the bone's scale grows the radius (lbColl_80006E58)
        out.append([*A, *B, r * k])
    return out


def score(P, masks, guard, verbose=False):
    import poses_air
    tot, rows = 0.0, []
    for f, c in masks.items():
        h = raster(pose_caps(poses_air.curl_pose(f, P)))
        both = (h & c).sum(); hs = h.sum()
        cov, outside = both / c.sum(), (hs - both) / max(hs, 1)
        st = stats(h)
        # cover most of it, spill little, and keep the guardrail's area and height
        j = cov - 2.0 * max(0.0, outside - 0.06) - 0.5 * outside
        j -= 0.05 * max(0.0, guard['area'] - st['area']) + 0.5 * max(0.0, guard['top'] - st['top'])
        tot += j
        rows.append(dict(frame=f, covered=round(float(cov), 3), outside=round(float(outside), 3), **st))
    if verbose:
        for r in rows: print(r)
    return tot / len(masks), rows


def fit(out, guard_area, guard_top, iters=3000):
    import poses_air
    from scipy.optimize import minimize
    masks = {f: cannon_mask(f) for f in FIT_FRAMES}
    keys = list(poses_air.CURL)
    x0 = np.array([poses_air.CURL[k] for k in keys], float)
    guard = dict(area=guard_area, top=guard_top)
    best = [None, -1e9]

    def f(x):
        j, _ = score(dict(zip(keys, x)), masks, guard)
        if j > best[1]: best[:] = [x.copy(), j]
        return -j
    for rnd in range(3):
        start = best[0] if best[0] is not None else x0
        minimize(f, start, method='Powell', options=dict(maxfev=iters, xtol=1e-3, ftol=1e-5))
        print('round', rnd, 'score', round(best[1], 4))
    P = {k: round(float(v), 4) for k, v in zip(keys, best[0])}
    j, rows = score(P, masks, guard, verbose=True)
    json.dump(dict(params=P, score=j, rows=rows, guard=guard), open(out, 'w'), indent=1)
    print(json.dumps(P))
    return P


def report(out_dir, md):
    """research/flash_hurtboxes.md: the cast's comparable states, the guardrail, and where Geno's Flash lands."""
    import poses_air
    c = cast()
    g = geno(out_dir)
    # the Flash's own body without the curl (the cannon's first version), offline on the same clip, for the comparison
    orig = poses_air.flash_cannon_keys
    try:
        poses_air.flash_cannon_keys = lambda frames, curl=True: orig(frames, curl=False)
        plain = dict(poses_air.flash())
    finally:
        poses_air.flash_cannon_keys = orig
    stand = g['summary']['stand']
    ar = sorted(v['area_ratio'] for v in c.values()); tr = sorted(v['top_ratio'] for v in c.values())
    med = lambda xs: (xs[len(xs) // 2] + xs[(len(xs) - 1) // 2]) / 2
    guard = dict(area_ratio=round(med(ar), 3), top_ratio=min(tr))
    L = ['# Geno Flash: his hurtboxes against the cannon, and the cast\'s transformed states (measured)', '',
         'Generated by `director/labs/cannon_hurt.py report` (remeasure.sh). The side view (the stage plane), each capsule '
         'projected and rasterised at 0.05 units: union areas in square units, tops in units above his position. '
         'Ratios are against the fighter\'s own standing hurtboxes (Wait, frame 0).', '',
         '## The cast\'s comparable states', '',
         '| State | Frames | Standing area | Standing top | Held area (median) | Area ratio | Held top | Top ratio |',
         '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for v in c.values():
        L.append(f"| {v['label']} | {v['frames'][0]}-{v['frames'][1]} | {v['stand']['area']} | {v['stand']['top']} | "
                 f"{v['held']['area']} | {v['area_ratio']:.2f} | {v['held']['top']} | {v['top_ratio']:.2f} |")
    L += ['', 'Samus\'s Morph Ball is the game\'s own code, not her bones: while its flag is up (frames 10-42) '
          '`ftSs_SpecialLw_8012AEBC` makes her capsules intangible and puts one sphere of radius 3 x her scale (2.64) on '
          'joint 2, about her ball\'s own radius (2.78). Every other state is measured about the body\'s own root: '
          'TransN, the fighter\'s movement, is taken out (Kirby\'s Stone hops it 8 units, a root-motion action the game '
          'strips; Yoshi\'s egg roll carries it 26 units a loop while the egg rolls on him).', '',
          '## The guardrail', '',
          f"- **Area:** at least the cast's median ratio, {guard['area_ratio']:.2f} of standing "
          f"({guard['area_ratio'] * stand['area']:.1f} for Geno).",
          f"- **Top:** at least the cast's lowest ratio, {guard['top_ratio']:.2f} of standing "
          f"({guard['top_ratio'] * stand['top']:.1f}; the Morph Ball's). The median ({med(tr):.2f}) would put capsules "
          f"{med(tr) * stand['top'] - g['summary']['full']['cannon_top']:.1f} units over the cannon: every state in the "
          'table keeps its hurtboxes at its own visible top, so the cannon\'s top (approved at its size) sets his.', '',
          '## Geno', '',
          f"Standing: area {stand['area']}, top {stand['top']}. The cannon at full size (Flash frames 30-66): silhouette "
          f"area {g['summary']['full']['cannon_area']:.1f}, top {g['summary']['full']['cannon_top']:.2f}.", '',
          '| Flash frame | Area | Area ratio | Top | Top ratio | Cannon covered | Hurtbox area outside the cannon | '
          'Without the curl: covered | outside |', '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for p in g['per']:
        f = p['frame']
        if f not in (0, 10, 22, 23, 24, 26, 28, 32, 40, 49, 50, 52, 57, 60, 66, 68, 70, 72, 73, 76, 94): continue
        q = ''
        if 'covered' in p:
            h = raster(pose_caps(plain[f])); cm = cannon_mask(f)
            both = (h & cm).sum()
            q = f"{both / cm.sum():.2f} | {(h.sum() - both) / h.sum():.2f}"
        L.append(f"| {f} | {p['area']} | {p['area'] / stand['area']:.2f} | {p['top']} | {p['top'] / stand['top']:.2f} | "
                 f"{p.get('covered', '')} | {p.get('outside', '')} | {q or ' | '} |")
    s_ = g['summary']
    L += ['', f"Frames 30-66 (the cannon at full size): area {s_['full']['area_median']:.1f} "
          f"({s_['full']['area_median'] / stand['area']:.2f}), top {s_['full']['top_median']:.2f} "
          f"({s_['full']['top_median'] / stand['top']:.2f}); covered {s_['full']['covered_median']:.2f} (min "
          f"{s_['full']['covered_min']:.2f}), outside {s_['full']['outside_median']:.2f} (max {s_['full']['outside_max']:.2f}). "
          f"The whole swap (23-75): area at least {s_['window']['area_min']:.1f}, top at least {s_['window']['top_min']:.2f}.",
          '', f"Guardrail: area {'met' if s_['full']['area_median'] >= guard['area_ratio'] * stand['area'] else 'NOT met'}, top "
          f"{'met' if s_['full']['top_median'] >= guard['top_ratio'] * stand['top'] else 'NOT met'}."]
    open(md, 'w').write('\n'.join(L) + '\n')
    print('wrote', md)


def cast_board(out):
    """Each cast state's held hurtboxes (green) over its standing ones (grey), side view, at one scale, and the numbers."""
    from PIL import Image, ImageDraw
    tiles = []
    for code, kind, act, label, held, sphere in CAST:
        files = [f'{DISC}/Pl{code}.dat', f'{DISC}/Pl{code}AJ.dat', f'{DISC}/Pl{code}Nr.dat']
        o = bodydata(files, kind, [act], joint=sphere[0] if sphere else None)[0]
        st = raster(o['stand_caps'])
        frames = list(held) if held else list(range(o['frames'] + 1))
        f = frames[len(frames) // 2]
        if sphere:
            x, y, z = o['joint'][f]; caps = [[x, y, z, x, y, z, sphere[1] * o['scale']]]
        else:
            caps = o['caps'][f]
        if not sphere:
            ty, tz = o['per'][f][5], o['per'][f][6]
            caps = [[a, b - ty, c - tz, d, e - ty, g - tz, r] for a, b, c, d, e, g, r in caps]
        h = raster(caps)
        a, b = stats(st), stats(h)
        rgb = np.zeros(h.shape + (3,), np.uint8) + 24
        rgb[st] = (90, 90, 100); rgb[h] = (80, 200, 120); rgb[h & ~st] = (240, 200, 40)
        rgb[int(-Y0 / PX), :] = (150, 150, 150)
        im = Image.fromarray(rgb[::-1][:, 60:500]); d = ImageDraw.Draw(im)
        d.text((6, 4), label, fill=(255, 255, 255))
        d.text((6, 18), f"area {b['area'] / a['area']:.2f}, top {b['top'] / a['top']:.2f} of standing (frame {f})", fill=(255, 230, 90))
        tiles.append(im)
    W, H = tiles[0].size
    sheet = Image.new('RGB', (3 * W + 8, 2 * H + 4), (10, 10, 12))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % 3) * (W + 4), (i // 3) * (H + 4)))
    sheet.save(out)
    return out


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'measure':
        measure(sys.argv[2], sys.argv[3])
    elif cmd == 'cast':
        print(json.dumps(cast(), indent=1))
    elif cmd == 'report':
        report(sys.argv[2], sys.argv[3])
    elif cmd == 'fit':
        fit(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]))
    elif cmd == 'castboard':
        print(cast_board(sys.argv[2]))
    elif cmd == 'overlay':
        print(overlay(sys.argv[2], sys.argv[3]))
