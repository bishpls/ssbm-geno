"""pose_look.py: render the model posed on an action's frames, from datkit fk's joints (Blender, headless).

  blender -b MODEL/geno.blend --python pose_look.py -- FK_DIR OUTDIR ACTION:FRAME[,FRAME...] ... [--views front,q34,side]
                                                       [--low] [--size 700] [--ortho 11] [--center Y]

Each frame's joints are set from FK_DIR/ACTION.json (the game's own pose, `datkit fkdir`): the capelet's chains sit
where the animation leaves them (their rest on the parent), as cape_clip.py measures them. The default model is shown
(every group's option 0); --low shows the low model. Close on the upper body by default (--center, --ortho). For
looking at a clip offline; the game is the judge (flash_cannon_lab / capelet checks).
"""
import bpy, json, math, os, sys
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index('--') + 1:]
FK, OUT = argv[0], argv[1]
opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
VIEWS = opt('--views', 'front,q34,side').split(',')
LOW = '--low' in argv
SIZE = int(opt('--size', '700'))
ORTHO = float(opt('--ortho', '11'))
CY = float(opt('--center', '9.5'))
specs = [a for a in argv[2:] if ':' in a and not a.startswith('--')]
os.makedirs(OUT, exist_ok=True)
C4 = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))      # glTF (Y up) -> Blender (Z up)

sc = bpy.context.scene
arm = bpy.data.objects['GenoLow' if LOW else 'Geno']
for o in sc.objects:
    if o.type == 'MESH':
        mo = o.get('melee')
        o.hide_render = not (o.parent == arm and (not mo or mo['option'] == 0))
arm.hide_render = False
bones = [b.name for b in arm.data.bones]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geno_geo as G  # noqa: E402
JI = {j[0]: k for k, j in enumerate(G.JOINTS)}        # the fk joints are in the rig's order
order = sorted(bones, key=lambda n: len(arm.pose.bones[n].parent_recursive))

sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = SIZE
sc.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 0.55
for name, e, rx, rz in (('key', 2.2, 50, -30), ('fill', 0.6, 70, 150)):
    L = bpy.data.lights.new(name, 'SUN'); L.energy = e
    lo = bpy.data.objects.new(name, L); sc.collection.objects.link(lo); lo.rotation_euler = (math.radians(rx), 0, math.radians(rz))
cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = ORTHO
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
YAW = {'front': 0, 'q34': 35, 'side': 90, 'back': 180, 'q34b': 145, 'qr34': -35}

for spec in specs:
    act, frames = spec.split(':', 1)
    d = json.load(open(os.path.join(FK, act + '.json')))
    names = None
    for f in [int(x) for x in frames.split(',')]:
        pose = d['pose'][f]
        for n in order:                       # parents first: a bone's armature-space matrix, from the game's joint
            if n not in JI: continue
            p = pose[JI[n]]
            M = Matrix(((p[0], p[1], p[2], p[9]), (p[3], p[4], p[5], p[10]), (p[6], p[7], p[8], p[11]), (0, 0, 0, 1)))
            arm.pose.bones[n].matrix = C4 @ M
            bpy.context.view_layer.update()
        for v in VIEWS:
            a = math.radians(YAW[v])
            dvec = Vector((math.sin(a), -math.cos(a), 0.12))
            co.location = Vector((0, 0, CY)) + dvec * 60
            co.rotation_euler = (math.radians(90) - math.atan2(0.12, 1), 0, a)
            cam.clip_start, cam.clip_end = 1, 200
            sc.render.filepath = os.path.join(OUT, f'{act}_{f:03d}_{v}{"_low" if LOW else ""}.png')
            bpy.ops.render.render(write_still=True)
print('pose_look ->', OUT)
