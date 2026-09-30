"""bake_ao.py: distance-limited ambient occlusion for every texture of the model, baked by Cycles into UV space.

Called by build_model.py --bake DIR. The model is posed with the arms hanging (the design pose) so the cape, collar and
hands shadow each other as they will in play. Writes DIR/ao_<tex>.png at twice the texture size (paint.py resamples).
"""
import bpy, json, math, os


def bake(objs, meshes, out_dir, arm_ob, sizes, pose_fn, distance=0.55, samples=64):
    os.makedirs(out_dir, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.cycles.seed = 0
    if not sc.world:
        sc.world = bpy.data.worlds.new('w')
    sc.world.light_settings.distance = distance
    pose_fn()
    by_tex = {}
    for o, m in zip(objs, meshes):
        by_tex.setdefault(m.tex, []).append(o)
    # occluders left out of a texture's bake: the bow lies on the crown; a cloth layer never shadows its own twin
    # and the cloth never shadows the torso (its hard-edged shadow through the capelet's opening reads as carving)
    CLOTH = ('cape_out_L', 'cape_out_R', 'cape_in_L', 'cape_in_R', 'collar', 'collar_in', 'clasp')
    IGNORE = {'crown': ('emblem',), 'face': CLOTH + ('nose',), 'nose': CLOTH + ('head_face',), 'collar': ('collar_in',), 'collarin': ('collar',),
              'cape': ('cape_in_L', 'cape_in_R'), 'lining': ('cape_out_L', 'cape_out_R'),
              **{t: CLOTH for t in ('chest', 'pelvis', 'joint', 'headback', 'ears', 'upperarm', 'forearm', 'palm',
                                    'finger', 'thigh', 'shin', 'eyeR', 'eyeL')}}    # cloth moves: never bake it onto the body
    FORM = ('fshot_', 'gun_', 'stargun_', 'cannon_', 'beam_', 'rocket_')      # the weapon forms (swapped variants)
    BASE_ARM = ('forearm_', 'palm_', 'fingers_')
    CANNON = 'fc_'
    for tex, obs in by_tex.items():
        w, h = sizes.get(tex, (64, 64))
        hidden = [o for o in objs if o.name in IGNORE.get(tex, ())]
        # a form and the hand it replaces are never seen together: neither shadows the other
        hidden += [o for o in objs if (tex == 'forms' and o.name.startswith(BASE_ARM)) or
                   (tex != 'forms' and o.name.startswith(FORM))]
        # Geno Flash's cannon replaces the whole body (geno_cannon.py): it and the body never shadow each other
        hidden += [o for o in objs if o.name.startswith(CANNON) != tex.startswith('fc') and o not in hidden]
        for o in hidden: o.hide_render = True
        img = bpy.data.images.new(f'ao_{tex}', width=w * 2, height=h * 2, alpha=False, float_buffer=False)
        img.generated_color = (1, 1, 1, 1)
        mats = {s.material for o in obs for s in o.material_slots if s.material}
        nodes = []
        for mat in mats:
            nt = mat.node_tree
            n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; n.name = 'ao_target'
            nt.nodes.active = n
            nodes.append((nt, n))
        bpy.ops.object.select_all(action='DESELECT')
        for o in obs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        bpy.ops.object.bake(type='AO', margin=6, use_clear=True, use_selected_to_active=False)
        img.filepath_raw = os.path.join(out_dir, f'ao_{tex}.png'); img.file_format = 'PNG'
        img.save()
        for nt, n in nodes:
            nt.nodes.remove(n)
        for o in hidden: o.hide_render = False
        print('baked', tex)
