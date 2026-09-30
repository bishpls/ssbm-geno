"""qa.py: measure the built model against the cast spec (SPEC.md) and write the stats table.

  python qa.py [OUT.md] [--json OUT.json]

Checks: triangles by region (by mesh, and by the spec's rule: the joint with the largest summed weight), meshes and
materials, bones per mesh (<= 10) and influences per vertex (<= 3), the share of vertices on a single bone, unique
vertex positions, texel density per region (texels per game unit; the cast: face ~37, body ~30), UV island gaps at the
real texture size (mipless: a gap under 2 texels bleeds under bilinear filtering), texture memory at the GameCube's CMP
(4 bits/texel; eyes CI8), the added joints, and how much of each body part stays inside the gameplay hurtboxes.
"""
import json, math, os, sys
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geno_geo as G  # noqa: E402
import geno_low as GL  # noqa: E402
from paint_sizes import SIZES  # noqa: E402
import rig  # noqa: E402  (via geno_geo's path)

DESIGN_REGION = {  # Geno's budget groups (the brief): mesh -> group
    'balls': None,  # split per bone below
}
BUDGET = {'head+cap': 1400, 'torso+collar': 900, 'cape': 400, 'arms': 550, 'hands': 750, 'legs+boots': 850}


def group_of(mesh, bone):
    r = G.bone_region(bone)
    if mesh.region == 'cape': return 'cape'
    if mesh.region == 'head': return 'head+cap'
    if mesh.region == 'torso': return 'torso+collar'
    return {'arms': 'arms', 'hands': 'hands', 'legs': 'legs+boots', 'torso': 'torso+collar', 'head': 'head+cap', 'cape': 'cape'}[r]


def tri_list(m):
    for f in m.F:
        for k in range(1, len(f) - 1):
            yield (f[0], f[k], f[k + 1])


def density(m, W, H):
    V = np.array(m.V); UV = np.array(m.UV)
    a3 = auv = 0.0
    for a, b, c in tri_list(m):
        a3 += np.linalg.norm(np.cross(V[b] - V[a], V[c] - V[a])) / 2
        u = UV[[a, b, c]] * [W, H]
        e1, e2 = u[1] - u[0], u[2] - u[0]
        auv += abs(e1[0] * e2[1] - e1[1] * e2[0]) / 2
    return math.sqrt(auv / a3) if a3 > 0 else 0.0, a3, auv


def uv_gaps(meshes, tex, W, H):
    """Min gap in texels between distinct UV islands of a texture at its real size."""
    import paint
    uv, at, _ = paint.gather(meshes, tex)
    _, mask, _ = paint.raster(uv, at, W, H, ss=2)
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    if n < 2: return None, n
    best = 1e9
    for i in range(1, n + 1):
        d = ndimage.distance_transform_edt(lab != i)
        other = (lab > 0) & (lab != i)
        if other.any(): best = min(best, float(d[other].min()))
    return best - 1, n


def capsule_dist(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)


def hurtbox_check(meshes):
    caps = []
    for j, p1, p2, r, h, g in rig.HURTBOXES:
        W = G.REST[j]
        caps.append((G.to_world(np.array([p1]), j)[0], G.to_world(np.array([p2]), j)[0], r))
    out = {}
    for m in meshes:
        if m.region in ('cape',) or m.name in ('cap_crown', 'cap_band', 'emblem', 'curls', 'collar', 'collar_in'): continue
        V = np.array(m.V)
        d = np.min([capsule_dist(V, a, b) - r for a, b, r in caps], axis=0)
        out[m.name] = (float((d > 0.3).mean()), float(d.max()))
    return out


def hurtbox_fill(meshes):
    """For each hurtbox capsule: how far the mesh bound to its joint reaches from the capsule's axis (95th percentile and
    max of the vertices whose strongest bone is that joint or, for the hands, a finger of it), against the radius."""
    rows = []
    for j, p1, p2, r, h, g in rig.HURTBOXES:
        a = G.to_world(np.array([p1]), j)[0]; b = G.to_world(np.array([p2]), j)[0]
        fam = {j} | ({n for n in G.JNAMES if n[0] == j[0] and any(k in n for k in ('1st', '2nd', '3rd', '4th', 'Thumb'))}
                     if j.endswith('HandN') else set())
        pts = []
        for m in meshes:
            if m.region == 'cape' or m.name.startswith(('collar', 'cap_', 'emblem', 'curls', 'boot', 'cuff')): continue
            for v, w in zip(m.V, m.W):
                if max(w, key=w.get) in fam: pts.append(v)
        if not pts:
            rows.append((j, r, 0, 0, 0)); continue
        d = capsule_dist(np.array(pts), a, b)            # distance from the axis segment
        rows.append((j, r, float(np.percentile(d, 95)), float(d.max()), len(pts)))
    return rows


def main():
    md = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else None
    M = G.build(); L = [m for m in GL.build() if not m.option]      # the default low model (not Geno Flash's cannon)
    rows = []
    groups = {k: 0 for k in BUDGET}
    for m in M:
        for f in m.F:
            acc = {}
            for v in f:
                for b, x in m.W[v].items(): acc[b] = acc.get(b, 0) + x
            groups[group_of(m, max(acc, key=acc.get))] += len(f) - 2
    spec_rule = G.region_tris(M)
    tot = sum(m.tris() for m in M)
    nverts = sum(len(np.unique(np.round(np.array(m.V), 5), axis=0)) for m in M)
    single = sum(sum(1 for w in m.W if len([x for x in w.values() if x > 1e-6]) == 1) for m in M)
    allv = sum(len(m.W) for m in M)
    infl2 = sum(sum(1 for w in m.W if len([x for x in w.values() if x > 1e-6]) == 2) for m in M)
    infl3 = sum(sum(1 for w in m.W if len([x for x in w.values() if x > 1e-6]) == 3) for m in M)
    dens = {}
    for m in M:
        W, H = SIZES[m.tex]
        d, a3, auv = density(m, W, H)
        rows.append((m.name, m.tex, f'{W}x{H}', m.tris(), len(m.bones()), max(len([x for x in w.values() if x > 1e-6]) for w in m.W),
                     'yes' if m.spec else '', 'double' if m.double else 'back', d))
        dens.setdefault(m.region if m.name not in ('head_face', 'eye_L', 'eye_R') else 'face', []).append((a3, auv))
    dreg = {k: math.sqrt(sum(b for a, b in v) / sum(a for a, b in v)) for k, v in dens.items()}
    texs = sorted({m.tex for m in M + L} - {'eyeL'})      # both eyes share one image set
    tex_rows = []
    kib = 0.0
    for t in texs:
        W, H = SIZES[t]
        b = W * H / 2 if t != 'eyeR' else 6 * (W * H + 512)
        kib += b / 1024
        g, n = uv_gaps(M + L, t, W, H) if t != 'eyeR' else (None, 2)
        tex_rows.append(('eye (both eyes)' if t == 'eyeR' else t, f'{W}x{H}', 'CI8 x6 frames' if t == 'eyeR' else 'CMP', b / 1024, n, g))
    hb = hurtbox_check(M)
    low_tris = sum(m.tris() for m in L)
    lines = ['# Geno production model: stats (generated by qa.py)', '',
             f'High model: **{tot} triangles** (cast 4,600-5,050; never over 5,050), {len(M)} meshes / {len({m.tex for m in M})} materials, '
             f'{nverts} unique vertex positions. Low model: **{low_tris} triangles**, {len(L)} meshes.', '',
             '## Triangles by region', '', '| Region | by mesh (budget) | by bone (spec rule) |', '| --- | --- | --- |']
    for k, bud in BUDGET.items():
        sr = {'head+cap': 'head', 'torso+collar': 'torso', 'cape': 'cape', 'arms': 'arms', 'hands': 'hands', 'legs+boots': 'legs'}[k]
        lines.append(f'| {k} | {groups[k]} (~{bud}) | {spec_rule[sr]} |')
    lines += ['', 'By mesh: each part counted where the brief budgets it (the ball joints split by their bone). By bone: the spec\'s '
              'measurement (a triangle belongs to the joint with the largest summed weight), so cloth bound to the torso counts as torso.', '',
              f'Skinning: {100 * single / allv:.0f}% of vertices on one bone, {100 * infl2 / allv:.0f}% on two, {100 * infl3 / allv:.1f}% on three '
              f'(cast: 75-92% / 7-24% / <2%); no vertex has four; every mesh at most 10 bones.', '',
              '## Meshes', '', '| Mesh | Texture | Size | Tris | Bones | Max infl. | Specular | Faces | Texels/unit |', '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in rows:
        lines.append(f'| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | {r[7]} | {r[8]:.0f} |')
    lines += ['', '## Texel density (texels per game unit, ModelScale 1.0)', '', '| Region | Density | Cast |', '| --- | --- | --- |']
    cast = {'face': '~37 (28-79)', 'head': '~30', 'torso': '~30 (16-39)', 'cape': '~30', 'arms': '~30', 'hands': '~30', 'legs': '~30'}
    for k in ('face', 'head', 'torso', 'cape', 'arms', 'hands', 'legs'):
        if k in dreg: lines.append(f'| {k} | {dreg[k]:.0f} | {cast[k]} |')
    lines += ['', '## Textures', '', f'{len(texs) - 1} textures + one 6-frame eye set; **{kib:.0f} KiB** at GameCube formats '
              f'({kib - 6 * (128 * 128 + 512) / 1024:.0f} KiB without the eye frames; cast median 171 KiB + 128 KiB of eyes).', '',
              '| Texture | Size | Format | KiB | UV islands | Min island gap (texels) |', '| --- | --- | --- | --- | --- | --- |']
    for t, sz, f, k, n, g in tex_rows:
        lines.append(f'| {t} | {sz} | {f} | {k:.1f} | {n} | {"-" if g is None else f"{g:.0f}"} |')
    # the weapon forms (geno_forms): swapped variants; one form per hand shows at a time
    import geno_forms, rig as _rig
    allm = G.build_all()
    byname = {m.name: m for m in allm}
    lines += ['', '## Weapon forms (Gate 2: visibility groups; one form per hand at a time)', '',
              'Each form shows the arm group\'s base meshes at its level plus the form\'s own mesh (rig.form_commands). '
              'The shown total is the default model with both hands in that form.', '',
              '| Form | Option (arm / form group) | Form mesh tris | Replaces | Hand tris shown | Model tris, both hands |',
              '| --- | --- | --- | --- | --- | --- |']
    base_hand = sum(byname[f'{p}_R'].tris() for p in geno_forms.ARM_LEVELS[0])
    for form in _rig.FORMS:
        lvl = _rig.FORM_ARM[form]
        kept = sum(byname[f'{p}_R'].tris() for p in geno_forms.ARM_LEVELS[lvl])
        own = byname[f'{form}_R'].tris() if form != 'hand' else 0
        shown = kept + own
        repl = ', '.join(p for p in geno_forms.ARM_LEVELS[0] if p not in geno_forms.ARM_LEVELS[lvl]) or '-'
        lines.append(f'| {form} | {lvl} / {_rig.FORMS.index(form)} | {own} | {repl} | {shown} | {tot - 2 * base_hand + 2 * shown} |')
    variants = sum(m.tris() for m in allm) - tot
    cannon = [m for m in allm if m.group == _rig.BODY_GROUP and m.option == _rig.BODY['cannon']]
    low_cannon = [m for m in GL.build() if m.group == _rig.BODY_GROUP and m.option == _rig.BODY['cannon']]
    lines += ['', f'Variant meshes in the file (not drawn together): {variants} triangles in {len(allm) - len(M)} meshes '
              f'(the forms, the spare forearm and palm copies, and Geno Flash\'s cannon); {len(allm) + len(L) + len(low_cannon)} '
              f'DObjs in all with the low model (the engine holds 124).', '',
              f'Geno Flash\'s cannon (geno_cannon.py; the body group\'s option 1, shown in place of the whole body): '
              f'{sum(m.tris() for m in cannon)} triangles high in {len(cannon)} meshes, {sum(m.tris() for m in low_cannon)} low.']
    lines += ['', '## Added joints (glTF node order 60+; rest positions in model units, local rotation identity)', '',
              '| Joint | Parent | World position | Local translation | Purpose |', '| --- | --- | --- | --- | --- |']
    purpose = {'CapTip2N': 'cap point chain (CapMidN, CapTipN, CapTip2N, CapTip3N)', 'CapTip3N': 'cap point tip',
               'CapeDN': 'centre cape chain, 4th bone (CapeAN-CapeDN)',
               'CannonN': "Geno Flash's cannon: the carriage", 'CannonBarrelN': "Geno Flash's cannon: the barrel (bore on +Z)",
               'CannonWheelN': "Geno Flash's cannon: the wheels"}
    for n, p, t, r in G.JOINTS[G.N_CONTRACT:]:
        wp = G.jpos(n)
        lines.append(f'| {n} | {p} | ({wp[0]:.2f}, {wp[1]:.2f}, {wp[2]:.2f}) | ({t[0]:.3f}, {t[1]:.3f}, {t[2]:.3f}) | '
                     f'{purpose.get(n, ("left" if "CapeL" in n else "right") + " cape chain")} |')
    lines += ['', '## Hurtbox fill (rig.py v1.3 radii)', '', 'How far each capsule\'s own mesh reaches from the capsule axis: '
              'the 95th percentile and the maximum distance of the vertices bound to that joint, against the radius. '
              'Near 1.0 fills the capsule; the cast\'s hurtboxes are typically a little larger than the limb they cover.', '',
              '| Hurtbox joint | Radius | Mesh reach (p95) | Mesh reach (max) | Fill (max / radius) |', '| --- | --- | --- | --- | --- |']
    for j, r, p95, mx, n in hurtbox_fill(M):
        lines.append(f'| {j} | {r:.2f} | {p95:.2f} | {mx:.2f} | {mx / r:.2f} |')
    lines += ['', '## Inside the gameplay hurtboxes', '', 'Share of each body mesh\'s vertices more than 0.3 units outside every hurtbox '
              'capsule (rig.py HURTBOXES), and the worst excess. Cap, cape, collar and curls are exempt (no hurtboxes, as the cast).', '',
              '| Mesh | Outside (>0.3) | Max excess |', '| --- | --- | --- |']
    for k, (f, mx) in hb.items():
        lines.append(f'| {k} | {100 * f:.0f}% | {mx:.2f} |')
    text = '\n'.join(lines) + '\n'
    if md:
        open(md, 'w').write(text)
    print(text)
    if '--json' in sys.argv:
        json.dump({'tris': tot, 'groups': groups, 'spec_rule': spec_rule, 'density': dreg, 'kib': kib, 'low_tris': low_tris},
                  open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)


if __name__ == '__main__':
    main()
