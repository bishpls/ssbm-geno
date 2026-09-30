"""cannon_look.py: look renders of Geno Flash's cannon (geno_cannon.py) from a built model folder, in Blender (headless).

  blender -b MODEL/geno.blend --python cannon_look.py -- OUTDIR [--pitch DEG] [--scale] [--low]

Renders the cannon alone, aimed (the barrel pitched --pitch degrees, default the Flash's aim), from the side, three-quarter
front, three-quarter back, above and SPR0030's angle (the SNES sprite's isometric view); --scale adds Geno standing beside it (his rest model, arms down) for size; --low
renders the low model's cannon. For iterating on the model; the judgement is in game (flash_cannon_lab.py).
"""
import bpy, math, os, sys
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0]
PITCH = float(argv[argv.index('--pitch') + 1]) if '--pitch' in argv else 16.9
SCALE = '--scale' in argv
LOW = '--low' in argv
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rig'))
import rig  # noqa: E402

sc = bpy.context.scene
arm = bpy.data.objects['GenoLow' if LOW else 'Geno']
for o in sc.objects:
    if o.type == 'MESH':
        mine = o.parent == arm
        cannon = o.name.startswith(('fc_', 'low_fc_'))
        mo = o.get('melee')
        body = mine and not cannon and (not mo or mo['option'] == 0)   # the default model: every group's option 0
        o.hide_render = not (mine and (cannon or (SCALE and body)))
        o.hide_viewport = o.hide_render
arm.hide_render = arm.hide_viewport = False

# pose: the barrel pitched up about the trunnions (world X), and with --scale the cannon moved beside him
for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
pb = arm.pose.bones['CannonBarrelN']
# the bone's rest axes in Blender (Z up): pitch the muzzle (glTF +Z = Blender -Y) upward about the world X axis
rest = arm.data.bones['CannonBarrelN'].matrix_local.to_3x3()
rot_w = Matrix.Rotation(-math.radians(PITCH), 3, 'X')          # the muzzle (Blender -Y) turns up toward +Z
pb.rotation_quaternion = (rest.inverted() @ rot_w @ rest).to_quaternion()
if SCALE:
    cb = arm.pose.bones['CannonN']
    rest_c = arm.data.bones['CannonN'].matrix_local.to_3x3()
    cb.location = rest_c.inverted() @ Vector((0.0, 13.0, 0.0))  # behind him (Blender +Y is glTF -Z), side by side in the side view
bpy.context.view_layer.update()

# light and camera, as build_model.py's look renders
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = (1400, 900) if SCALE else (900, 700)
sc.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 0.55
for name, e, rx, rz in (('key', 2.2, 50, -30), ('fill', 0.6, 70, 150)):
    L = bpy.data.lights.new(name, 'SUN'); L.energy = e
    lo = bpy.data.objects.new(name, L); sc.collection.objects.link(lo); lo.rotation_euler = (math.radians(rx), 0, math.radians(rz))
cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
K = rig.CANNON_K
center = Vector((0.0, 6.5, 8.0)) if SCALE else Vector((0.0, 0.0, 3.6 * K))
cam.ortho_scale = 31.0 if SCALE else 13.5 * K
views = [('side', 90, 0), ('front34', 35, 12), ('back34', 215, 14), ('top', 60, 55), ('snes', 45, 30)] \
    if not SCALE else [('scale', 90, 0), ('scale34', 30, 8)]            # snes: SPR0030's angle (the muzzle down-left)
for name, yaw, elev in views:
    a, e = math.radians(yaw), math.radians(elev)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    co.location = center + d * 60
    co.rotation_euler = (math.radians(90) - e, 0, a)
    cam.clip_start, cam.clip_end = 1, 200
    sc.render.filepath = os.path.join(OUT, f'{"low_" if LOW else ""}{name}.png')
    bpy.ops.render.render(write_still=True)
print('cannon_look ->', OUT)
