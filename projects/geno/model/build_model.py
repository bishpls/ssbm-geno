"""build_model.py: build Geno's production model in Blender from geno_geo.py and export it.

  blender -b --python build_model.py -- [--out DIR] [--tex DIR] [--preview] [--bake DIR] [--render DIR [--pose design]]

  --out DIR      where geno.blend, geno.gltf (+ .bin, textures), geno_low.gltf and geno.melee.json go
                 (default ~/games/melee/work/art/model)
  --tex DIR      the painted textures (paint.py); without it (or with --preview) materials are flat colours
  --bake DIR     bake distance-limited ambient occlusion for every texture into DIR/ao_<tex>.png and stop
  --render DIR   also render quick look views (front / 3/4 / side / back) into DIR; --pose design poses the arms down

The armature is the rig.py contract (joint order, names, rest transforms untouched) plus the added joints; every glTF
node keeps its HSD local transform exactly (checked against geno_blocks.gltf when it is present).
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Matrix, Vector, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import geno_geo as G  # noqa: E402
import geno_low as GL  # noqa: E402
import paint_sizes  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def arg(k, d=None):
    return argv[argv.index(k) + 1] if k in argv else d


OUT = os.path.expanduser(arg('--out', '~/games/melee/work/art/model'))
TEX = arg('--tex')
PREVIEW = '--preview' in argv or not TEX
BAKE = arg('--bake')
RENDER = arg('--render')
POSE = arg('--pose', 'rest')
os.makedirs(OUT, exist_ok=True)

C3 = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))      # glTF (Y up) -> Blender (Z up)
C4 = C3.to_4x4()


def gl2bl(p):
    return (p[0], -p[2], p[1])


FLAT = {  # preview colours (linear)
    'face': (0.62, 0.36, 0.15), 'headback': (0.62, 0.36, 0.15), 'ears': (0.62, 0.36, 0.15), 'eyeR': (0.95, 0.95, 0.95), 'eyeL': (0.95, 0.95, 0.95),
    'band': (0.03, 0.14, 0.62), 'crown': (0.04, 0.16, 0.7), 'emblem': (0.95, 0.7, 0.02), 'curls': (0.9, 0.25, 0.02),
    'chest': (0.62, 0.36, 0.15), 'pelvis': (0.55, 0.3, 0.12), 'joint': (0.3, 0.14, 0.05), 'upperarm': (0.62, 0.36, 0.15),
    'forearm': (0.62, 0.36, 0.15), 'thigh': (0.62, 0.36, 0.15), 'shin': (0.62, 0.36, 0.15), 'palm': (0.62, 0.36, 0.15),
    'finger': (0.62, 0.36, 0.15), 'collar': (0.04, 0.16, 0.7), 'clasp': (0.8, 0.55, 0.1), 'cape': (0.04, 0.16, 0.7),
    'lining': (0.95, 0.65, 0.03), 'forms': (0.5, 0.4, 0.2), 'fcbarrel': (0.05, 0.2, 0.75), 'fccarriage': (0.6, 0.4, 0.15), 'boot': (0.2, 0.05, 0.02), 'cuff': (0.16, 0.04, 0.015), 'lowface': (0.62, 0.36, 0.15),
}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


def build_armature(name='Geno'):
    arm = bpy.data.armatures.new(name + '_rig')
    ob = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = {}
    kids = {}
    for n, p, t, r in G.JOINTS:
        kids.setdefault(p, []).append(n)
    for n, p, t, r in G.JOINTS:
        eb = arm.edit_bones.new(n)
        eb.head = (0, 0, 0); eb.tail = (0, 1, 0)       # a bone needs length before its matrix can be set
        M = Matrix(G.REST[n].T.tolist())               # column-vector world matrix (glTF space)
        # bone length: to the first child if it lies along +Y, else a small fixed length (display only)
        L = 0.3
        eb.matrix = C4 @ M
        eb.length = L
        ebs[n] = eb
    for n, p, t, r in G.JOINTS:
        if p:
            ebs[n].parent = ebs[p]
            ebs[n].use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


EYE_SLOT = {'eyeR': 0, 'eyeL': 1}      # Mario's slot 0 is DObj 14 (his right eye, -X); slot 1 DObj 15 (+X)
EYE_ORDER = {'eyeR': ['open', 'half', 'closed', 'squint', 'out', 'in'], 'eyeL': ['open', 'half', 'closed', 'squint', 'in', 'out']}
WOOD = {'face', 'headback', 'ears', 'chest', 'pelvis', 'joint', 'upperarm', 'forearm', 'thigh', 'shin', 'palm', 'finger', 'lowface'}


# CI8 (256 exact colours, paint.py quantises them) where CMP's 4x4 blocks can't hold the detail: the eyes, and the low
# model's face (geno-cannon polish: its eye's white, black and wood in one block smeared under CMP; 4.5 KiB against 2)
CI8_TEX = set(EYE_SLOT) | {'lowface'}


def tex_png(tex):
    return 'eye_open.png' if tex in EYE_SLOT else f'{tex}.png'


def make_material(tex, spec, double):
    name = f'Ge_{tex}'
    mat = bpy.data.materials.get(name)
    if mat: return mat
    mat = bpy.data.materials.new(name)
    # what datkit's glTF importer reads (GltfModel.cs): the SPECULAR flag and, for an eye, its slot and frames. Specular
    # only where paint.py wrote a map (TEX1 modulating the importer's white highlight); everything else is matte
    pass
    spec = tex in paint_sizes.SPEC
    mx = {'specular': bool(spec)}
    if spec: mx['specular_color'] = list(paint_sizes.SPEC[tex])
    if tex in EYE_SLOT:
        mx.update(eye=EYE_SLOT[tex], frames=[f'geno_tex/eye_{f}.png' for f in EYE_ORDER[tex]])
    elif tex in CI8_TEX:
        mx['format'] = 'CI8'                         # datkit's importer: the texture's format (GltfModel ChooseFormat)
    mat['melee'] = mx
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.55 if spec else 0.9
    bsdf.inputs['Metallic'].default_value = 0.0
    try: bsdf.inputs['Specular IOR Level'].default_value = 0.35 if spec else 0.1
    except Exception: pass
    png = os.path.join(TEX, tex_png(tex)) if TEX else None
    if not PREVIEW and png and os.path.exists(png):
        ti = nt.nodes.new('ShaderNodeTexImage')
        ti.image = bpy.data.images.load(png, check_existing=True)
        ti.image.name = tex_png(tex)
        ti.extension = 'EXTEND'
        ti.interpolation = 'Linear'
        nt.links.new(ti.outputs['Color'], bsdf.inputs['Base Color'])
    else:
        c = FLAT.get(tex, (0.5, 0.5, 0.5))
        bsdf.inputs['Base Color'].default_value = (*c, 1)
    mat.use_backface_culling = not double
    return mat


def build_mesh(m, arm_ob, collection=None):
    V = np.array(m.V)
    me = bpy.data.meshes.new(m.name)
    me.from_pydata([gl2bl(p) for p in V], [], [list(f) for f in m.F])
    me.validate(clean_customdata=False)
    uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            u, v = m.UV[vi]
            uvl.data[li].uv = (u, 1.0 - v)
    ob = bpy.data.objects.new(m.name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    if m.group or m.option:        # datkit's importer: the engine's visibility group and option (node extras)
        ob['melee'] = {'group': int(m.group), 'option': int(m.option)}
    # smooth shading with hard edges past the part's angle
    for poly in me.polygons:
        poly.use_smooth = True
    bm = bmesh.new(); bm.from_mesh(me)
    lim = math.radians(m.sharp)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > lim:
            e.smooth = False
    bm.to_mesh(me); bm.free()
    # skin
    for b in sorted(m.bones()):
        ob.vertex_groups.new(name=b)
    for i, w in enumerate(m.W):
        for b, x in w.items():
            if x > 1e-6:
                ob.vertex_groups[b].add([i], float(x), 'REPLACE')
    md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = arm_ob
    ob.parent = arm_ob
    me.materials.append(make_material(m.tex, m.spec, m.double))
    return ob


def pose_armature(arm_ob, pose):
    for pb in arm_ob.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = (1, 0, 0, 0)
    for n, r in pose.items():
        Rrow = G.rot3(*r)
        # rest local rotation for these joints is identity; the pose rotation in the bone's own (= node's) frame
        rest_r = dict((j[0], j[3]) for j in G.JOINTS)[n]
        R0 = G.rot3(*rest_r)
        Rrel = np.linalg.inv(R0) @ Rrow                  # row-vector: local = Rrel @ R0 ... relative to the rest
        q = Matrix(Rrel.T.tolist()).to_quaternion()
        pb = arm_ob.pose.bones[n]
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = q
    bpy.context.view_layer.update()


def export_gltf(path, objs, arm_ob):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs + [arm_ob]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm_ob
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', use_selection=True, export_yup=True,
                              export_skins=True, export_animations=False, export_morph=False, export_apply=False,
                              export_texcoords=True, export_normals=True, export_materials='EXPORT',
                              export_image_format='NONE' if PREVIEW else 'AUTO', export_texture_dir='geno_tex',
                              export_rest_position_armature=True, export_def_bones=False, export_extras=True,
                              export_all_influences=False, export_vertex_color='NONE', export_armature_object_remove=False)


def hsd_order():
    """Depth-first order of the joint tree, children in table order: the JObj indices the game will see."""
    kids = {}
    for n, p, t, r in G.JOINTS:
        kids.setdefault(p, []).append(n)
    out = []
    def walk(n):
        out.append(n)
        for c in kids.get(n, []): walk(c)
    for root in kids[None]: walk(root)
    return out


def fix_joint_order(path):
    """Blender writes skin joints and node children in its own (alphabetical) order. Rewrite them in the joint table's
    order (the 60 contract joints keep indices 0-59, the added joints follow), remapping JOINTS_0 and the inverse bind
    matrices, and tag each joint node with its contract and HSD (depth-first) index."""
    g = json.load(open(path))
    binp = os.path.join(os.path.dirname(path), g['buffers'][0]['uri'])
    buf = bytearray(open(binp, 'rb').read())
    name2node = {n.get('name'): i for i, n in enumerate(g['nodes'])}
    if 'skins' not in g: return
    sk = g['skins'][0]
    old = [g['nodes'][j]['name'] for j in sk['joints']]
    new = list(G.JNAMES)
    remap = np.array([new.index(n) for n in old])
    def acc_view(ai):
        a = g['accessors'][ai]; bv = g['bufferViews'][a['bufferView']]
        off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        return a, bv, off
    done = set()
    if 'skins' not in g: return
    for me in g.get('meshes', []):
        for pr in me['primitives']:
            ai = pr['attributes'].get('JOINTS_0')
            if ai is None or ai in done: continue
            done.add(ai)
            a, bv, off = acc_view(ai)
            dt = {5121: np.uint8, 5123: np.uint16}[a['componentType']]
            stride = bv.get('byteStride', 0)
            n = a['count']
            if stride and stride != 4 * np.dtype(dt).itemsize:
                raise RuntimeError('interleaved joints not handled')
            arr = np.frombuffer(bytes(buf[off:off + n * 4 * np.dtype(dt).itemsize]), dt).reshape(n, 4).copy()
            arr = remap[arr].astype(dt)
            buf[off:off + arr.nbytes] = arr.tobytes()
    a, bv, off = acc_view(sk['inverseBindMatrices'])
    ibm = np.frombuffer(bytes(buf[off:off + a['count'] * 64]), np.float32).reshape(-1, 16).copy()
    ibm2 = np.zeros_like(ibm)
    for i, j in enumerate(remap): ibm2[j] = ibm[i]
    buf[off:off + ibm2.nbytes] = ibm2.tobytes()
    sk['joints'] = [name2node[n] for n in new]
    order = {n: i for i, n in enumerate(new)}
    hsd = {n: i for i, n in enumerate(hsd_order())}
    for n in g['nodes']:
        if n.get('name') in order:
            n['extras'] = {'contract_index': order[n['name']], 'hsd_index': hsd[n['name']],
                           'added': order[n['name']] >= G.N_CONTRACT}
            if 'children' in n:
                n['children'] = sorted(n['children'], key=lambda c: order.get(g['nodes'][c].get('name'), 999))
    open(binp, 'wb').write(bytes(buf))
    json.dump(g, open(path, 'w'), indent=1)


def check_skeleton(path):
    ref = os.path.expanduser('~/games/melee/work/art/model/geno_blocks.gltf')
    if not os.path.exists(ref):
        print('skeleton check: no reference'); return
    a = json.load(open(ref)); b = json.load(open(path))
    bn = {n.get('name'): n for n in b['nodes']}
    worst = 0.0
    for i, n in enumerate(a['nodes']):
        if not n['name'].startswith('J'): continue
        k = int(n['name'][1:])
        m = bn.get(G.JNAMES[k])
        if m is None:
            print('MISSING', G.JNAMES[k]); worst = 9; continue
        for key, d in (('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])):
            x = n.get(key, d); y = m.get(key, d)
            e = max(abs(p - q) for p, q in zip(x, y))
            if key == 'rotation': e = min(e, max(abs(p + q) for p, q in zip(x, y)))
            worst = max(worst, e)
    # parents
    par_b = {}
    for i, n in enumerate(b['nodes']):
        for c in n.get('children', []): par_b[b['nodes'][c]['name']] = n['name']
    bad = [n for n, p, t, r in G.JOINTS if p and par_b.get(n) != p]
    skin_j = [b['nodes'][j]['name'] for j in b['skins'][0]['joints']]
    order_ok = skin_j[:G.N_CONTRACT] == G.JNAMES[:G.N_CONTRACT]
    print(f'skeleton check vs geno_blocks.gltf: max TRS error {worst:.2e}, parent mismatches {bad}, contract order kept {order_ok}')


def sidecar(path, meshes, tex_sizes):
    mats = []
    seen = {}
    for m in meshes:
        name = f'Ge_{m.tex}'
        if name in seen: continue
        w, h = tex_sizes.get(m.tex, (64, 64))
        # lacquered wood gets a soft sheen (a dimmed, warm specular colour); leather and brass keep white highlights
        spc = list(paint_sizes.SPEC.get(m.tex, (255, 255, 255))) + [255]
        layers = [{'info': {'alphamap': 'none', 'blend': 1, 'colormap': 'replace', 'coord': 'uv', 'fmt': 'CI8' if m.tex in CI8_TEX else 'CMP',
                            'w': w, 'h': h, 'lightmaps': ['diffuse'], 'uv': 0, 'wrap': ['CLAMP', 'CLAMP'], 'repeat': [1, 1],
                            'mag': 'GX_LINEAR', 'mip': 0},
                   'png': f'geno_tex/{tex_png(m.tex)}', 'xf': {'off': [0, 0], 'sc': [1, 1]}}]
        pass
        has_spec = m.tex in paint_sizes.SPEC
        flags = ['DIFFUSE', 'TEX0'] + (['SPECULAR'] if has_spec else [])
        seen[name] = 1
        mats.append({'name': name, 'flags': flags, 'dif': [179, 179, 179, 255], 'amb': [179, 179, 179, 255],
                     'spc': spc, 'shininess': 50, 'alpha': 1.0, 'render': '0000001C' if has_spec else '00000014',
                     'cull': 'none' if m.double else 'back', 'layers': layers})
    texanims = [{'material': f'Ge_{t}', 'mesh': 'eye_R' if t == 'eyeR' else 'eye_L', 'slot': EYE_SLOT[t],
                 'frames': [f'geno_tex/eye_{f}.png' for f in EYE_ORDER[t]], 'order': EYE_ORDER[t]} for t in ('eyeR', 'eyeL')]
    json.dump({'flipped': False, 'materials': mats, 'texanims': texanims,
               'eye_frames': "Mario's order: 0 open, 1 half-lidded, 2 closed, 3 squint, 4 look toward -X, 5 look toward +X "
                             "(one shared image set; u runs outward from the nose on both eyes, so the two eyes swap 'in'/'out')"},
              open(path, 'w'), indent=1)


# ---------------------------------------------------------------------------------------------------------------------
def setup_render(w=900, h=900):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'
    try: sc.eevee.taa_render_samples = 32
    except Exception: pass
    world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
    bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 0.55
    sun = bpy.data.lights.new('key', 'SUN'); sun.energy = 2.2; sun.angle = 0.2
    so = bpy.data.objects.new('key', sun); sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), 0, math.radians(-30))
    fill = bpy.data.lights.new('fill', 'SUN'); fill.energy = 0.6
    fo = bpy.data.objects.new('fill', fill); sc.collection.objects.link(fo); fo.rotation_euler = (math.radians(70), 0, math.radians(150))
    cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'
    co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
    return sc, co


def render_views(outdir, arm_ob, tag, views=(('front', 0), ('q34', 35), ('side', 90), ('back', 180)), ortho=19.0,
                 center=(0, 0, 8.6), size=(900, 900), elev=0.0):
    os.makedirs(outdir, exist_ok=True)
    sc, cam = setup_render(*size)
    cam.data.ortho_scale = ortho
    for name, yaw in views:
        a = math.radians(yaw); e = math.radians(elev)
        # camera orbits around the model (model faces -Y in Blender: glTF +Z -> Blender -Y)
        d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = Vector(center) + d * 60
        cam.rotation_euler = (math.radians(90) - e, 0, a)
        cam.data.clip_start = 1; cam.data.clip_end = 200
        sc.render.filepath = os.path.join(outdir, f'{tag}_{name}.png')
        bpy.ops.render.render(write_still=True)


def main():
    reset()
    arm_ob = build_armature()
    meshes = G.build_all()
    if BAKE:          # the spare copies of the forearm and palm (geno_forms) share the originals' texels: bake these once
        meshes = [mm for mm in meshes if '_arm' not in mm.name]
    objs = [build_mesh(m, arm_ob) for m in meshes]
    if BAKE:
        import bake_ao, paint_sizes
        bake_ao.bake(objs, meshes, BAKE, arm_ob, paint_sizes.SIZES, lambda: pose_armature(arm_ob, G.DESIGN_POSE))
        return
    gl = os.path.join(OUT, 'geno.gltf')
    export_gltf(gl, objs, arm_ob)
    fix_joint_order(gl)
    check_skeleton(gl)
    sizes = {}
    if TEX and os.path.exists(os.path.join(TEX, 'sizes.json')):
        sizes = json.load(open(os.path.join(TEX, 'sizes.json')))
    sidecar(os.path.join(OUT, 'geno.melee.json'), meshes, sizes)
    # low model: its own armature copy in the same scene, exported alone
    low_coll = bpy.data.collections.new('low'); bpy.context.scene.collection.children.link(low_coll)
    arm_low = build_armature('GenoLow')
    lows = GL.build()
    lobjs = [build_mesh(m, arm_low, low_coll) for m in lows]
    export_gltf(os.path.join(OUT, 'geno_low.gltf'), lobjs, arm_low)
    fix_joint_order(os.path.join(OUT, 'geno_low.gltf'))
    sidecar(os.path.join(OUT, 'geno_low.melee.json'), lows, sizes)
    for o in lobjs + [arm_low]:
        o.hide_render = True; o.hide_viewport = True
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'geno.blend'))
    if RENDER:
        if POSE == 'design':
            pose_armature(arm_ob, G.DESIGN_POSE)
        render_views(RENDER, arm_ob, POSE)


main()
