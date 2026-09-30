"""review.py: render review shots of the built model (geno.blend from build_model.py).

  blender -b OUT/geno.blend --python review.py -- SHOTS.json

SHOTS.json: {"out": DIR, "shots": [{"name": "front", "pose": "rest|design|idle", "yaw": 0, "elev": 0, "ortho": 19,
             "center": [0, 8.6, 0] (glTF coords), "size": [900, 900], "wire": false, "closest": false, "low": false}]}
Lit like render_cast.py (key sun from the front-left above, a fill from behind, grey-white world), so shots compare with
the cast boards. yaw turns the camera around the model (0 = front, 90 = his left side).
"""
import bpy, json, math, os, sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import geno_geo as G  # noqa: E402

job = json.load(open(sys.argv[sys.argv.index('--') + 1]))
OUT = job['out']; os.makedirs(OUT, exist_ok=True)

def fists(side, curl=1.25):
    out = {f'{side}{f}N{k}': (0.0, 0.0, -curl * (0.95 if k == 'a' else 1.1)) for f in ('1st', '2nd', '3rd', '4th') for k in 'ab'}
    out[f'{side}ThumbNa'] = (0.25, 0.0, -0.5 - 0.7); out[f'{side}ThumbNb'] = (0.0, 0.0, -0.8)
    return out


D = 1.0  # radians helper
# the relaxed stance (the cast staggers its feet in Wait by 18-42% of its height): left foot 1.9 forward, right 2.1 back
# (along +Z), 2.6 apart, toes out ~15 deg, soft knees; solved for flat soles on the floor (see make_boards.py)
STANCE = {'TransN': {'t': (0.0, -0.488, 0.0)},
          'LLegJ': (-0.3132, -0.1163, -0.5646), 'LKneeJ': (0.0, 0.0, 0.368), 'LFootJ': (0.0717, 0.0, 0.2047),
          'RLegJ': (0.2995, 0.0931, 0.3243), 'RKneeJ': (0.0, 0.0, 0.2306), 'RFootJ': (0.1792, 0.0, -0.5173)}
POSES = {
    'rest': {},
    'design': dict(G.DESIGN_POSE),
    # relaxed: arms down, elbows a touch forward, loose fists
    'idle': {**G.DESIGN_POSE, 'LArmJ': (0, 0, -0.3), 'RArmJ': (0, 0, -0.3), **fists('L'), **fists('R'), **STANCE},
    # the Samus-style neutral: gun arm (his right) forward, the other hanging
    'gun': {'LShoulderJ': (0, 1.2, 0), 'RShoulderJ': (0, -0.15, -1.35), 'RArmJ': (0, 0, -0.1), 'LArmJ': (0, 0, -0.35),
            'WaistN': (0, 0.35, 0), 'HeadN': (0, -0.3, 0), **fists('L'), **fists('R'),
            'LLegJ': (0, 0, -0.25), 'LKneeJ': (0, 0, 0.45), 'LFootJ': (0, 0, -0.2),
            'RLegJ': (0, 0, 0.15), 'RKneeJ': (0, 0, 0.3), 'RFootJ': (0, 0, -0.45), 'TransN': {'t': (0, -0.25, 0)}},
    'crouch': {**G.DESIGN_POSE, 'TransN': {'t': (0, -1.7, 0)}, 'LLegJ': (0, 0, -1.05), 'RLegJ': (0, 0, -1.05),
               'LKneeJ': (0, 0, 2.0), 'RKneeJ': (0, 0, 2.0), 'LFootJ': (0, 0, -0.95), 'RFootJ': (0, 0, -0.95),
               'WaistN': (0.35, 0, 0), 'HeadN': (-0.25, 0, 0), 'LArmJ': (0, 0, -0.8), 'RArmJ': (0, 0, -0.8), **fists('L'), **fists('R')},
    'arms_up': {'LShoulderJ': (0, -1.45, 0), 'RShoulderJ': (0, 1.45, 0), 'LArmJ': (0, 0, -0.25), 'RArmJ': (0, 0, -0.25),
                'HeadN': (-0.2, 0, 0), **fists('L', 0.6), **fists('R', 0.6)},
    'smash': {'WaistN': (0.15, -0.55, 0), 'HeadN': (0, 0.4, 0), 'RShoulderJ': (0, -0.55, 1.0), 'RArmJ': (0, 0, -1.3),
              'LShoulderJ': (0, 0.35, -1.25), 'LArmJ': (0, 0, -0.3), **fists('L'), **fists('R'), 'TransN': {'t': (0, -0.7, 0)},
              'LLegJ': (0, 0, -0.75), 'LKneeJ': (0, 0, 1.0), 'LFootJ': (0, 0, -0.3), 'RLegJ': (0, 0, 0.35), 'RKneeJ': (0, 0, 0.55),
              'RFootJ': (0, 0, -0.8)},
    'kick': {'RLegJ': (0, 0, -1.45), 'RKneeJ': (0, 0, 0.25), 'RFootJ': (0, 0, 0.3), 'LLegJ': (0, 0, 0.1), 'LKneeJ': (0, 0, 0.35),
             'LFootJ': (0, 0, -0.45), 'WaistN': (-0.25, 0, 0), 'LShoulderJ': (0, 0.2, 0.4), 'RShoulderJ': (0, -0.2, 0.5),
             **fists('L'), **fists('R'), 'TransN': {'t': (0, -0.2, 0)}},
}


# arm extremes for the capelet's front panels (forward tilt: the arm straight out in front; up: overhead; back: a
# smash wind-up with the arm drawn back and up)
POSES['arm_fwd'] = {'RShoulderJ': (0, -0.1, -1.55), 'LShoulderJ': (0, 0.1, -1.55), **fists('L'), **fists('R')}
POSES['arm_up'] = {'RShoulderJ': (0, 0.2, -2.6), 'LShoulderJ': (0, -0.2, -2.6), **fists('L'), **fists('R')}
POSES['arm_back'] = {'RShoulderJ': (0, -0.9, 1.2), 'LShoulderJ': (0, 0.9, 1.2), 'RArmJ': (0, 0, -1.2), 'LArmJ': (0, 0, -1.2),
                     **fists('L'), **fists('R')}
POSES['arm_side_up'] = {'RShoulderJ': (0, 0.6, -0.3), 'LShoulderJ': (0, -0.6, -0.3), **fists('L'), **fists('R')}
# the part poses (rig.py HAND_POSES, CAP_POSES), both hands, the arms out front
import rig as _rig


def _part(k):
    out = {}
    for n, r in _rig.HAND_POSES[k].items():
        out[n] = r
        out['R' + n[1:]] = (-r[0], -r[1], r[2])
    return out


for _k, _nm in enumerate(('fist', 'open', 'point', 'grip')):
    POSES[f'hp_{_nm}'] = {'RShoulderJ': (0, -0.2, -1.2), 'LShoulderJ': (0, 0.2, -1.2), **_part(_k)}
    POSES[f'ht_{_nm}'] = _part(_k)            # in the T-pose
    POSES[f'aim_{_nm}'] = {'RShoulderJ': (0, 0.0, -1.5), 'LShoulderJ': (0, 0.0, -1.5), **_part(_k)}   # both arms aimed forward
for _k, _nm in enumerate(('rest', 'back', 'low')):
    POSES[f'cap_{_nm}'] = dict(POSES['idle'], CapN=_rig.CAP_POSES[_k]['CapN'])
for _deg in (-57, -40, -35, -20, 20, 35, 40, 57):   # ankle range of motion: + lifts the heel (toe down), - brings the shin over the foot
    POSES[f'ankle{_deg:+d}'] = {'LFootJ': (0.0, 0.0, _deg * math.pi / 180), 'RFootJ': (0.0, 0.0, _deg * math.pi / 180)}


def pose(arm, name):
    P = POSES.get(name, {})
    rest_r = {j[0]: j[3] for j in G.JOINTS}
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    for n, r in P.items():
        pb = arm.pose.bones[n]
        if isinstance(r, dict):
            if 't' in r: pb.location = r['t']
            if 'r' not in r: continue
            r = r['r']
        Rrel = np.linalg.inv(G.rot3(*rest_r[n])) @ G.rot3(*r)
        # row-vector: new local rotation = Rrel @ R0; in the bone's own frame the pose basis is Rrel (transposed)
        pb.rotation_quaternion = Matrix(Rrel.T.tolist()).to_quaternion()
    bpy.context.view_layer.update()


def setup(w, h):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'
    try: sc.eevee.taa_render_samples = 32
    except Exception: pass
    if not sc.world:
        world = bpy.data.worlds.new('w'); sc.world = world
    world = sc.world; world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 0.55
    if 'key' not in bpy.data.objects:
        sun = bpy.data.lights.new('key', 'SUN'); sun.energy = 2.2; sun.angle = 0.2
        so = bpy.data.objects.new('key', sun); sc.collection.objects.link(so)
        so.rotation_euler = (math.radians(50), 0, math.radians(-30))
        fill = bpy.data.lights.new('fill', 'SUN'); fill.energy = 0.6
        fo = bpy.data.objects.new('fill', fill); sc.collection.objects.link(fo); fo.rotation_euler = (math.radians(70), 0, math.radians(150))
    if 'cam' not in bpy.data.objects:
        cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'
        co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co)
    sc.camera = bpy.data.objects['cam']
    return sc, bpy.data.objects['cam']


def wire_on(objs, thick):
    wm = bpy.data.materials.get('wire') or bpy.data.materials.new('wire')
    wm.use_nodes = True; nt = wm.node_tree; nt.nodes.clear()
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (0.02, 0.02, 0.05, 1)
    o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0], o.inputs[0])
    out = []
    for m in objs:
        w = m.copy(); w.data = m.data.copy(); bpy.context.scene.collection.objects.link(w)
        w.data.materials.clear(); w.data.materials.append(wm)
        md = w.modifiers.new('wf', 'WIREFRAME'); md.thickness = thick; md.use_replace = True; md.use_even_offset = True
        md.offset = 0.6
        # the wireframe must come after the armature deform
        out.append(w)
    return out


def main():
    arm_hi = bpy.data.objects['Geno']; arm_lo = bpy.data.objects.get('GenoLow')
    hi = [o for o in bpy.data.objects if o.type == 'MESH' and o.parent == arm_hi]
    lo = [o for o in bpy.data.objects if o.type == 'MESH' and arm_lo and o.parent == arm_lo]
    for s in job['shots']:
        low = s.get('low', False)
        show, hide = (lo, hi) if low else (hi, lo)
        for o in show: o.hide_render = False
        for o in hide: o.hide_render = True
        # the engine's visibility: one option per group (defaults 0), as the move scripts set them (shot "forms":
        # {"R": "cannon", "L": "hand"}; geno_forms.form_commands)
        import geno_forms
        sel = {}
        for side, form in s.get('forms', {}).items():
            for g, o in geno_forms.form_commands(side, form): sel[g] = o
        for o in show:
            if 'melee' in o.keys():
                mg = o['melee']
                if int(mg.get('option', 0)) != sel.get(int(mg.get('group', 0)), 0): o.hide_render = True
        for o in show:
            if any(o.name.startswith(h) for h in s.get('hide', [])): o.hide_render = True
            if s.get('only') and not any(o.name.startswith(h) for h in s['only']): o.hide_render = True
        arm = arm_lo if low else arm_hi
        pose(arm, s.get('pose', 'rest'))
        for img in bpy.data.images:
            pass
        for m in bpy.data.materials:
            if not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE': n.interpolation = 'Closest' if s.get('closest') else 'Linear'
        w, h = s.get('size', [900, 900])
        sc, cam = setup(w, h)
        wires = wire_on(show, s.get('thick', 0.012)) if s.get('wire') else []
        cam.data.ortho_scale = s.get('ortho', 19)
        c = s.get('center', [0, 8.6, 0]); ctr = Vector((c[0], -c[2], c[1]))
        a = math.radians(s.get('yaw', 0)); e = math.radians(s.get('elev', 0))
        d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = ctr + d * 80
        cam.rotation_euler = (math.radians(90) - e, 0, a)
        cam.data.clip_start = 1; cam.data.clip_end = 300
        sc.render.filepath = os.path.join(OUT, s['name'] + '.png')
        bpy.ops.render.render(write_still=True)
        for wo in wires:
            bpy.data.objects.remove(wo, do_unlink=True)


main()
