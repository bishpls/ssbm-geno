"""Kirby's Geno hat, the geometry: Geno's own cap from the production model, refitted to Kirby's head (Blender, headless).
Run by `kirby_hat.py build`, which then builds the .dat with datkit's kirby-hat:
    blender -b -P projects/geno/rig/kirby_hat_model.py -- OUT_DIR MODEL_DIR TEX_DIR PARAMS_JSON
Writes OUT_DIR/hat_high.gltf, hat_low.gltf (unskinned meshes in Kirby's rest model space: glTF +Y up, +Z his front) and
OUT_DIR/fit.json (the numbers: triangles per mesh, bounds, clearance from Kirby's head sphere).

The fit (every number is PARAMS, kirby_hat.py FIT):
  - the cap's four meshes (crown, band, curls, emblem) are posed on Geno's skeleton, the floppy point bent by `droop`
    degrees per joint of its chain (a static drape: the hat file has no physics, like the vanilla caps);
  - scaled by `scale` about the centre of the band's lower edge, tipped back `tilt` degrees (the vanilla caps sit tipped
    back: Luigi's band is at y 9.43 over the eyes and y 5.65 at the back of the head);
  - seated: that centre moves to where the band's lower edge rests on Kirby's head sphere (centre (0, 5.58, 0), radius
    5.0, fitted to his body mesh) `inset` inside it, found by search;
  - decimated per mesh to the budget (the vanilla caps: 332-360 triangles normal, 78-96 low).
The low model is Geno's own low cap (crown and band in 40 triangles, the emblem painted on) plus the curls decimated.
"""
import bpy, bmesh, sys, json, math, os
import numpy as np
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index('--') + 1:]
OUT, MODEL, TEX, P = argv[0], argv[1], argv[2], json.load(open(argv[3]))
os.makedirs(OUT, exist_ok=True)
KIRBY_C, KIRBY_R = np.array(P['kirby_centre']), P['kirby_radius']
CAP_MESHES = ['cap_crown', 'cap_band', 'curls', 'emblem']
CHAIN = ['CapMidN', 'CapTipN', 'CapTip2N', 'CapTip3N']


def gl(v):      # Blender world -> glTF (Y up, +Z front)
    return np.array([v[0], v[2], -v[1]])


def bl(v):
    return Vector((v[0], -v[2], v[1]))


def load(path, keep, reset=True):
    """the meshes named in `keep`, posed and baked to world space as new objects hat_<name>; everything else removed"""
    if reset:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    # the textures: the downscaled copies in TEX (same names; the importer packs its images, so remap every user)
    for im in list(bpy.data.images):
        stem = os.path.splitext(os.path.basename(im.filepath or im.name))[0]
        path = os.path.join(TEX, stem + '.png')
        if os.path.exists(path) and not bpy.path.abspath(im.filepath).startswith(TEX):
            im.user_remap(bpy.data.images.load(path, check_existing=True))
    arm = next(o for o in new if o.type == 'ARMATURE')
    # the static drape: bend the point's chain down, parent first, each about its own head (world X: Kirby's side axis)
    bpy.context.view_layer.update()
    for name in CHAIN:
        pb = arm.pose.bones.get(name)
        if pb is None:
            continue
        w = arm.matrix_world @ pb.matrix
        head = w.to_translation()
        r = Matrix.Translation(head) @ Matrix.Rotation(math.radians(-P['droop']), 4, 'X') @ Matrix.Translation(-head)
        pb.matrix = arm.matrix_world.inverted() @ r @ w
        bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for o in new:
        if o.type == 'MESH' and o.data.name in keep:
            me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
            me.transform(o.matrix_world)
            n = bpy.data.objects.new('hat_' + o.data.name, me); n['src'] = o.data.name
            bpy.context.scene.collection.objects.link(n)
            out[o.data.name] = n
    for o in new:
        bpy.data.objects.remove(o)
    return out


def verts(o):
    return np.array([gl(v.co) for v in o.data.vertices])


def fit_matrix(band):
    """scale about the band's centre, tip it back so the band's axis leans `tilt` degrees, then seat it: the underside of
    the band's roll on Kirby's head sphere, `inset` inside it (least squares over a grid of heights and depths). A band
    hugs a ball best at its equator, which is how Geno wears it; on Kirby that would cover his eyes, so the band sits
    higher, on its lower edge, as the vanilla caps do."""
    v = verts(band)
    c = v.mean(0)
    ax = np.linalg.svd(v - c)[2][2]; ax = ax if ax[1] > 0 else -ax
    own = math.degrees(math.atan2(-ax[2], ax[1]))                   # Geno's band already leans back this much
    h = (v - c) @ ax; rad = np.linalg.norm((v - c) - np.outer(h, ax), axis=1)
    lower = v[h < np.percentile(h, 15)]         # the roll's underside: it rests on his head (the rest flares off it)
    t = math.radians(P['tilt'] - own)
    rot = np.array([[1, 0, 0], [0, math.cos(t), math.sin(t)], [0, -math.sin(t), math.cos(t)]])   # front edge up
    rel = (lower - c) * P['scale'] @ rot.T
    best = None
    for py in np.arange(KIRBY_C[1], KIRBY_C[1] + KIRBY_R, 0.01):
        for pz in np.arange(-3.0, 3.0, 0.01):
            d = np.linalg.norm(rel + [0, py, pz] - KIRBY_C, axis=1) - (KIRBY_R - P['inset'])
            e = float((d ** 2).mean())
            if best is None or e < best[0]:
                best = (e, py, pz)
    target = np.array([0, best[1], best[2]])
    Mg = np.eye(4); Mg[:3, :3] = rot * P['scale']; Mg[:3, 3] = target - rot @ c * P['scale']
    C = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], float)     # Blender -> glTF
    Mb = np.linalg.inv(C) @ Mg @ C
    # the band's lower edge after the fit, front and back (Luigi's: y 9.43 over the eyes, 5.65 behind)
    w = (v - c) * P['scale'] @ rot.T + target
    front = w[w[:, 2] > np.percentile(w[:, 2], 90)]; back = w[w[:, 2] < np.percentile(w[:, 2], 10)]
    return Matrix(Mb.tolist()), dict(band_centre=target.tolist(), band_own_lean=round(own, 2), seat_rms=round(math.sqrt(best[0]), 3),
                                     band_front_bottom_y=round(float(front[:, 1].min()), 2), band_back_bottom_y=round(float(back[:, 1].min()), 2))


def decimate(o, target):
    n0 = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if target and target < n0:
        m = o.modifiers.new('dec', 'DECIMATE')
        m.decimate_type = 'COLLAPSE'; m.ratio = target / n0; m.use_collapse_triangulate = True
        if o.get('src') in P.get('symmetric', []):
            m.use_symmetry = True; m.symmetry_axis = 'X'
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=m.name)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(o.data); bm.free()
    return n0, len(o.data.polygons)


def clearance(o):
    v = verts(o)
    d = np.linalg.norm(v - KIRBY_C, axis=1) - KIRBY_R
    return dict(min=round(float(d.min()), 3), inside=int((d < 0).sum()), verts=len(v),
                lo=np.round(v.min(0), 2).tolist(), hi=np.round(v.max(0), 2).tolist())


def export(objs, path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', use_selection=True, export_apply=True,
                              export_yup=True, export_skins=False, export_animations=False, export_extras=True,
                              export_image_format='AUTO')


fit = {'params': P}
# ---- normal detail
objs = load(os.path.join(MODEL, 'geno.gltf'), CAP_MESHES)
M, fit['seat'] = fit_matrix(objs['cap_band'])
fit['high'] = {}
for name in CAP_MESHES:
    o = objs[name]
    o.data.transform(M)
    n0, n1 = decimate(o, P['high'][name])
    fit['high'][name] = dict(tris_source=n0, tris=n1, **clearance(o))
export([objs[n] for n in CAP_MESHES], os.path.join(OUT, 'hat_high.gltf'))
# ---- low detail: Geno's low cap, plus the curls (the same fit: the normal band decides it)
lo = load(os.path.join(MODEL, 'geno_low.gltf'), ['low_cap'])
lo.update(load(os.path.join(MODEL, 'geno.gltf'), ['curls'], reset=False))
fit['low'] = {}
# the curls are two single-sided layers each (ART.md: double-sided backs light wrong); the low model keeps one layer of
# each curl, double-sided, since collapsing both layers together shreds them (and the magnifier won't show the lighting)
c = lo['curls']
bm = bmesh.new(); bm.from_mesh(c.data); bm.faces.ensure_lookup_table()
parts, seen = [], set()
for f in bm.faces:
    if f.index in seen:
        continue
    stack, part = [f], []
    while stack:
        g = stack.pop()
        if g.index in seen:
            continue
        seen.add(g.index); part.append(g)
        stack.extend(h for e in g.edges for h in e.link_faces if h.index not in seen)
    parts.append(part)
cent = [sum((f.calc_center_median() for f in p), Vector()) / len(p) for p in parts]
keep = []
for i, p in enumerate(parts):
    if not any((cent[i] - cent[j]).length < 0.3 for j in keep):
        keep.append(i)
bmesh.ops.delete(bm, geom=[f for i, p in enumerate(parts) if i not in keep for f in p], context='FACES')
bm.to_mesh(c.data); bm.free()
for m in c.data.materials:
    m.use_backface_culling = False
fit['low_curls_layers'] = f'{len(keep)} of {len(parts)} kept'
for key in ('low_cap', 'curls'):
    o = lo[key]
    o.name = 'hat_low_' + key.replace('low_', '')
    o.data.transform(M)
    n0, n1 = decimate(o, P['low'][key])
    fit['low'][key] = dict(tris_source=n0, tris=n1, **clearance(o))
export(list(lo.values()), os.path.join(OUT, 'hat_low.gltf'))
json.dump(fit, open(os.path.join(OUT, 'fit.json'), 'w'), indent=1)
print('FIT', json.dumps(fit))
