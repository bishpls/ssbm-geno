"""Geno's blocky prototype rig: his own skeleton, parts table and block meshes, at final proportions.

The skeleton follows the engine's contract, not any character's data: the standard Melee humanoid parts (TopN, TransN,
XRotN, YRotN, HipN, legs, arms, fingers, NeckN, HeadN, ThrowN, TransN2; see Fighter_Part in the decomp) with Melee's local
axis conventions (a T-pose facing +Z, limb chains running down each bone's local X), so the engine's IK, throws and
animation retargeting read him correctly. Proportions, extra bones (stocking cap, cape), meshes and every animation are
his own. Units are Melee model units at ModelScale 1 (Mario's cap top is about 13 in game units, Marth's hair about 19).

    .venv/bin/python projects/geno/rig/rig.py OUT.json        # the rig for datkit fighter-build
"""
import json, math, os, sys

# ---- the parts the engine addresses (index = the part number in the per-kind parts table; PlCo.dat's order)
PARTS = ['TopN', 'TransN', 'XRotN', 'YRotN', 'HipN', 'WaistN', 'LLegJA', 'LLegJ', 'LKneeJ', 'LFootJA', 'LFootJ',
         'RLegJA', 'RLegJ', 'RKneeJ', 'RFootJA', 'RFootJ', 'WaistB', 'BustN', 'LShoulderN', 'LShoulderJA', 'LShoulderJ',
         'LArmJ', 'LHandN', 'L1stNa', 'L1stNb', 'L2ndNa', 'L2ndNb', 'L3rdNa', 'L3rdNb', 'L4thNa', 'L4thNb', 'LHandNb',
         'LThumbNa', 'LThumbNb', 'NeckN', 'HeadN', 'RShoulderN', 'RShoulderJA', 'RShoulderJ', 'RArmJ', 'RHandN',
         'R1stNa', 'R1stNb', 'R2ndNa', 'R2ndNb', 'R3rdNa', 'R3rdNb', 'R4thNa', 'R4thNb', 'RHandNb', 'RThumbNa',
         'RThumbNb', 'ThrowN', 'TransN2']
H = math.pi / 2

# ---- proportions (world heights in the T-pose). A head-heavy doll about 3.5 heads tall to the crown of the head, with a
# stocking cap on top whose point droops backward (no hurtbox on it).
HIP_Y = 6.6          # XRotN, the body's pivot
LEG_TOP = 6.0        # hip joints
KNEE_Y = 3.4
ANKLE_Y = 0.95
WAIST_Y = 7.0
SHOULDER_Y = 10.0
NECK_Y = 10.4
HEAD_Y = 10.9        # the head joint (base of the head); the head block reaches ~14.9
HIP_X, SHOULDER_X, CLAV_X = 1.0, 1.9, 0.9
UPPER_ARM, FOREARM, HAND = 1.8, 1.9, 0.75

# (name, parent, local translation, local rest rotation XYZ radians, part name or None)
JOINTS = [
    ('TopN', None, (0, 0, 0), (0, 0, 0)),
    ('TransN', 'TopN', (0, 0, 0), (0, 0, 0)),
    ('XRotN', 'TransN', (0, HIP_Y, 0), (0, 0, 0)),
    ('YRotN', 'XRotN', (0, 0, 0), (0, 0, 0)),
    ('HipN', 'YRotN', (0, LEG_TOP - HIP_Y, 0), (0, 0, 0)),
    ('WaistN', 'HipN', (0, WAIST_Y - LEG_TOP, 0), (0, 0, 0)),
    # left arm: the clavicle, then a chain along +X
    ('LShoulderN', 'WaistN', (CLAV_X, SHOULDER_Y - WAIST_Y, -0.15), (0, 0, 0)),
    ('LShoulderJA', 'LShoulderN', (SHOULDER_X - CLAV_X, 0, 0), (-H, 0, 0)),
    ('LShoulderJ', 'LShoulderJA', (0, 0, 0), (0, 0, 0)),
    ('LArmJ', 'LShoulderJ', (UPPER_ARM, 0, 0), (0, 0, 0)),
    ('LHandN', 'LArmJ', (FOREARM, 0, 0), (0, 0, 0)),
    ('L1stNa', 'LHandN', (HAND, 0, 0.36), (0, 0, 0)),
    ('L1stNb', 'L1stNa', (0.34, 0, 0), (0, 0, 0)),
    ('L2ndNa', 'LHandN', (HAND + 0.05, 0, 0.12), (0, 0, 0)),
    ('L2ndNb', 'L2ndNa', (0.36, 0, 0), (0, 0, 0)),
    ('L3rdNa', 'LHandN', (HAND + 0.03, 0, -0.12), (0, 0, 0)),
    ('L3rdNb', 'L3rdNa', (0.34, 0, 0), (0, 0, 0)),
    ('L4thNa', 'LHandN', (HAND - 0.03, 0, -0.34), (0, 0, 0)),
    ('L4thNb', 'L4thNa', (0.3, 0, 0), (0, 0, 0)),
    ('LThumbNa', 'LHandN', (0.35, -0.3, 0.45), (0, 0, -0.5)),
    ('LThumbNb', 'LThumbNa', (0.3, 0, 0), (0, 0, 0)),
    ('LHandNb', 'LHandN', (HAND * 0.9, 0, 0.12), (0, -H, 2 * H)),     # item hold: held items sit in this frame
    ('NeckN', 'WaistN', (0, NECK_Y - WAIST_Y, -0.1), (0, 0, 0)),
    ('HeadN', 'NeckN', (0, HEAD_Y - NECK_Y, 0.1), (0, 0, 0)),
    ('CapN', 'HeadN', (0, 3.3, -0.3), (0, 0, 0)),             # the stocking cap: crown, then a floppy point
    ('CapMidN', 'CapN', (0, 1.0, -1.0), (0.6, 0, 0)),
    ('CapTipN', 'CapMidN', (0, 0.3, -1.3), (0.5, 0, 0)),
    # the production model's dynamics chains (projects/geno/model, Gate 1c: the belled capelet's side chains, the grown head): the cap's point is CapMidN-CapTip3N, the cape
    # three chains of four (centre CapeAN-CapeDN, left and right from the neck), like Marth's and Roy's
    ('CapTip2N', 'CapTipN', (0.000, -1.126, 0.259), (0, 0, 0)),
    ('CapTip3N', 'CapTip2N', (0.000, -0.736, -0.251), (0, 0, 0)),
    ('CapeAN', 'NeckN', (0, -0.3, -1.3), (0, 0, 0)),          # the cape, hanging from the back of the collar
    ('CapeBN', 'CapeAN', (0, -1.9, -0.2), (0, 0, 0)),
    ('CapeCN', 'CapeBN', (0, -1.9, -0.1), (0, 0, 0)),
    ('CapeDN', 'CapeCN', (0.000, -0.920, -0.820), (0, 0, 0)),
    ('CapeLAN', 'NeckN', (2.630, -0.380, -0.420), (0, 0, 0)),
    ('CapeLBN', 'CapeLAN', (0.630, -1.050, -0.260), (0, 0, 0)),
    ('CapeLCN', 'CapeLBN', (0.430, -0.990, -0.250), (0, 0, 0)),
    ('CapeLDN', 'CapeLCN', (0.180, -0.910, -0.260), (0, 0, 0)),
    ('CapeRAN', 'NeckN', (-2.630, -0.380, -0.420), (0, 0, 0)),
    ('CapeRBN', 'CapeRAN', (-0.630, -1.050, -0.260), (0, 0, 0)),
    ('CapeRCN', 'CapeRBN', (-0.430, -0.990, -0.250), (0, 0, 0)),
    ('CapeRDN', 'CapeRCN', (-0.180, -0.910, -0.260), (0, 0, 0)),
    # right arm: mirrored (Melee flips the chain with a Z half-turn at the shoulder, so it too runs down local +X)
    ('RShoulderN', 'WaistN', (-CLAV_X, SHOULDER_Y - WAIST_Y, -0.15), (0, 0, 0)),
    ('RShoulderJA', 'RShoulderN', (-(SHOULDER_X - CLAV_X), 0, 0), (-H, 0, -2 * H)),
    ('RShoulderJ', 'RShoulderJA', (0, 0, 0), (0, 0, 0)),
    ('RArmJ', 'RShoulderJ', (UPPER_ARM, 0, 0), (0, 0, 0)),
    ('RHandN', 'RArmJ', (FOREARM, 0, 0), (0, 0, 0)),
    ('R1stNa', 'RHandN', (HAND, 0, -0.36), (0, 0, 0)),
    ('R1stNb', 'R1stNa', (0.34, 0, 0), (0, 0, 0)),
    ('R2ndNa', 'RHandN', (HAND + 0.05, 0, -0.12), (0, 0, 0)),
    ('R2ndNb', 'R2ndNa', (0.36, 0, 0), (0, 0, 0)),
    ('R3rdNa', 'RHandN', (HAND + 0.03, 0, 0.12), (0, 0, 0)),
    ('R3rdNb', 'R3rdNa', (0.34, 0, 0), (0, 0, 0)),
    ('R4thNa', 'RHandN', (HAND - 0.03, 0, 0.34), (0, 0, 0)),
    ('R4thNb', 'R4thNa', (0.3, 0, 0), (0, 0, 0)),
    ('RThumbNa', 'RHandN', (0.35, -0.3, -0.45), (0, 0, -0.5)),
    ('RThumbNb', 'RThumbNa', (0.3, 0, 0), (0, 0, 0)),
    ('RHandNb', 'RHandN', (HAND * 0.9, 0, -0.12), (0, -H, 2 * H)),
    # legs: a chain along local +X pointing down, the foot turned forward
    ('LLegJA', 'HipN', (HIP_X, 0, 0), (-H, 0, -H)),
    ('LLegJ', 'LLegJA', (0, 0, 0), (0, 0, 0)),
    ('LKneeJ', 'LLegJ', (LEG_TOP - KNEE_Y, 0, 0), (0, 0, 0)),
    ('LFootJA', 'LKneeJ', (KNEE_Y - ANKLE_Y, 0, 0), (0, 0, -H)),
    ('LFootJ', 'LFootJA', (0, 0, 0), (0, 0, 0)),
    ('LToeN', 'LFootJ', (1.4, -0.6, 0), (0, 0, 0)),
    ('RLegJA', 'HipN', (-HIP_X, 0, 0), (-H, 0, -H)),
    ('RLegJ', 'RLegJA', (0, 0, 0), (0, 0, 0)),
    ('RKneeJ', 'RLegJ', (LEG_TOP - KNEE_Y, 0, 0), (0, 0, 0)),
    ('RFootJA', 'RKneeJ', (KNEE_Y - ANKLE_Y, 0, 0), (0, 0, -H)),
    ('RFootJ', 'RFootJA', (0, 0, 0), (0, 0, 0)),
    ('RToeN', 'RFootJ', (1.4, -0.6, 0), (0, 0, 0)),
    ('ThrowN', 'YRotN', (0, -HIP_Y, 0), (0, 0, 0)),
    ('TransN2', 'TopN', (0, 0, 0), (0, 0, 0)),
]
# Geno Flash's full-body cannon (projects/geno/model/geno_cannon.py; DESIGN §12, ART.md "Geno Flash's cannon"): three
# joints of its own, TopN's last children, so they come last in depth-first order and no existing joint changes index.
# Why new joints: every existing joint either carries a hurtbox or is an ancestor of one (so animating the cannon on it
# would move his hurtboxes during the Flash), or defines the ECB, the camera target, a physics chain, a part pose, or an
# engine attach point (item hold, throw, shield). The cannon's joints carry nothing the gameplay reads; the body's hidden
# bones keep playing the Flash's own animation, so the hurtboxes are exactly as they were.
#   CannonN        the carriage (the bed, the cheeks, the trail, the axle): placed, rocked and scaled by the animation
#   CannonBarrelN  the barrel, on the trunnions (unrotated at rest, so its pitch is a plain X rotation, clear of the Euler
#                  gimbal a +X bore would sit on): the bore runs along its local +Z, and the fireball's muzzle is
#                  CANNON_MUZZLE along it (ftGe_FlashMuzzle); pitched up to aim, kicked on the shot
#   CannonWheelN   the wheels, on the axle: they turn as the carriage rolls
CANNON_K = 1.25                                        # the cannon's scale (SMRPG's is about his height long)
CANNON_TRUNNION = (0.0, 3.9 * CANNON_K, 0.0)           # the barrel's pivot, over the axle
CANNON_AXLE = (0.0, 2.3 * CANNON_K, 0.0)               # the wheels' centre (the wheel radius: they stand on the floor)
CANNON_MUZZLE = 5.66 * CANNON_K                        # the muzzle's face, along CannonBarrelN's +Z
JOINTS += [
    ('CannonN', 'TopN', (0, 0, 0), (0, 0, 0)),
    ('CannonBarrelN', 'CannonN', CANNON_TRUNNION, (0, 0, 0)),
    ('CannonWheelN', 'CannonN', CANNON_AXLE, (0, 0, 0)),
]
CANNON_JOINTS = ('CannonN', 'CannonBarrelN', 'CannonWheelN')

# The skeleton Geno's glTF models are skinned to (exported from his game file with joints named J00..J59): datkit's glTF
# import resolves a "J%02d" joint name through this list, by name, so joints inserted into JOINTS later (the cape's
# chains, the cap point) don't shift what J27 means. glTF joints may also carry the rig's names directly.
GLTF_JNAMES = [
    'TopN', 'TransN', 'XRotN', 'YRotN', 'HipN', 'WaistN', 'LShoulderN', 'LShoulderJA', 'LShoulderJ', 'LArmJ',
    'LHandN', 'L1stNa', 'L1stNb', 'L2ndNa', 'L2ndNb', 'L3rdNa', 'L3rdNb', 'L4thNa', 'L4thNb', 'LThumbNa', 'LThumbNb',
    'LHandNb', 'NeckN', 'HeadN', 'CapN', 'CapMidN', 'CapTipN', 'CapeAN', 'CapeBN', 'CapeCN', 'RShoulderN',
    'RShoulderJA', 'RShoulderJ', 'RArmJ', 'RHandN', 'R1stNa', 'R1stNb', 'R2ndNa', 'R2ndNb', 'R3rdNa', 'R3rdNb',
    'R4thNa', 'R4thNb', 'RThumbNa', 'RThumbNb', 'RHandNb', 'LLegJA', 'LLegJ', 'LKneeJ', 'LFootJA', 'LFootJ', 'LToeN',
    'RLegJA', 'RLegJ', 'RKneeJ', 'RFootJA', 'RFootJ', 'RToeN', 'ThrowN', 'TransN2',
]
# The costume model. None builds the blocks below; a dict makes fighter-build take the meshes from skinned, textured glTFs
# (tools/machinima/melee/datkit/GltfModel.cs; paths absolute or ~/..., eye frames relative to the high model), e.g.
#   MODEL = dict(high='~/games/melee/work/art/model/geno.gltf', low='~/games/melee/work/art/model/geno_low.gltf',
#                eyes=[dict(material='GenoEyeR', frames=['eyeR_0.png', 'eyeR_1.png', ...]),     # slot 0: Mario's DObj 14 side
#                      dict(material='GenoEyeL', frames=['eyeL_0.png', ...])])
MODEL = None
if os.environ.get('GENO_MODEL'):                   # the production model (projects/geno/model), until it replaces the blocks
    _M = os.path.expanduser(os.environ['GENO_MODEL'])  # GENO_MODEL=1: the modeller's live output; or a folder (a snapshot)
    if not os.path.isdir(_M): _M = os.path.expanduser('~/games/melee/work/art/model')
    MODEL = dict(high=f'{_M}/geno.gltf', low=f'{_M}/geno_low.gltf',
                 # one eye material each (slot 0 = Mario's DObj 14, his right eye at -X; slot 1 = DObj 15, +X), frames in
                 # Mario's order: open, half, closed, squint, look toward -X, look toward +X (the two eyes swap in/out)
                 eyes=[dict(material='Ge_eyeR', slot=0, frames=[f'geno_tex/eye_{f}.png' for f in ('open', 'half', 'closed', 'squint', 'out', 'in')]),
                       dict(material='Ge_eyeL', slot=1, frames=[f'geno_tex/eye_{f}.png' for f in ('open', 'half', 'closed', 'squint', 'in', 'out')])])

# ---- palette (after the 1996 render, see research/geno-source.md)
C = dict(blue=(3, 90, 254), blue_dark=(10, 52, 170), yellow=(255, 209, 0), gold=(255, 212, 0), wood=(255, 186, 80),
         wood_dark=(214, 140, 52), shoe=(58, 20, 6), orange=(225, 52, 0), eye=(40, 10, 10))

# ---- blocks, in each joint's local frame: (joint, shape, centre, size, colour[, rotation XYZ about the centre]). Shapes:
# 'box' (size = full extents), 'ball' (size = radii, a 12-sided ellipsoid), 'cone' (size = base radii x, z and height y,
# point up). Limb blocks run along local +X from the joint.
def limb(j, length, w, colour, start=0.0, shape='box'):
    return (j, shape, (start + length / 2, 0, 0), (length, w, w), colour)

BLOCKS = [
    ('WaistN', 'ball', (0, 1.2, 0), (1.55, 2.2, 1.35), 'wood'),                   # barrel torso
    ('HipN', 'ball', (0, 0.25, 0), (1.35, 0.8, 1.15), 'wood_dark'),               # hips
    ('HeadN', 'ball', (0, 2.0, 0.15), (1.75, 2.0, 1.6), 'wood'),                   # head
    ('HeadN', 'box', (0, 1.75, 1.75), (0.35, 0.55, 0.5), 'wood_dark'),            # wedge nose
    ('HeadN', 'box', (0.55, 2.35, 1.55), (0.45, 0.28, 0.1), 'eye'),               # eyes
    ('HeadN', 'box', (-0.55, 2.35, 1.55), (0.45, 0.28, 0.1), 'eye'),
    ('HeadN', 'box', (-0.8, 3.0, 1.35), (0.5, 0.5, 0.3), 'orange'),               # curls over his right eye
    ('HeadN', 'ball', (0, 3.25, -0.1), (1.9, 0.85, 1.8), 'blue'),                 # the cap's band around the head
    ('CapN', 'cone', (0, -0.3, -0.2), (1.55, 1.9, 1.45), 'blue'),                 # crown, tapering up
    ('HeadN', 'box', (0, 3.35, 1.7), (1.0, 0.55, 0.15), 'gold'),                  # bow emblem
    ('CapMidN', 'cone', (0, -0.1, 0), (0.85, 1.5, 0.8), 'blue', (-1.2, 0, 0)),    # the floppy point, drooping back
    ('CapTipN', 'ball', (0, 0.0, -0.1), (0.3, 0.3, 0.3), 'blue'),
    ('NeckN', 'box', (1.45, 0.75, 0.15), (2.1, 1.6, 2.0), 'yellow', (0, 0, 0.55)),   # wide pointed collar: two wings
    ('NeckN', 'box', (-1.45, 0.75, 0.15), (2.1, 1.6, 2.0), 'yellow', (0, 0, -0.55)), # flaring up around the jaw
    ('NeckN', 'box', (0, 0.9, -0.85), (2.2, 1.9, 0.3), 'yellow', (-0.35, 0, 0)),     # and the back, standing up
    ('NeckN', 'box', (0, 0.1, 1.2), (0.7, 0.35, 0.15), 'gold'),                   # the cord at the throat
    ('CapeAN', 'box', (0, -0.95, -0.1), (3.6, 1.9, 0.25), 'blue'),                # cape, three panels
    ('CapeBN', 'box', (0, -0.95, -0.1), (3.8, 1.9, 0.25), 'blue'),
    ('CapeCN', 'box', (0, -0.8, -0.1), (4.0, 1.6, 0.25), 'blue_dark'),            # the zig-zag hem, as a darker band
]
for side in 'LR':
    BLOCKS += [
        limb(f'{side}ShoulderJ', UPPER_ARM, 0.75, 'wood'),
        (f'{side}ArmJ', 'ball', (0, 0, 0), (0.45, 0.45, 0.45), 'wood_dark'),        # elbow ring
        limb(f'{side}ArmJ', FOREARM, 0.8, 'wood'),                                 # gun-barrel forearm
        (f'{side}ArmJ', 'box', (FOREARM - 0.12, 0, 0), (0.25, 0.95, 0.95), 'gold'),  # the muzzle ring at the wrist
        (f'{side}HandN', 'box', (HAND / 2 + 0.05, 0, 0), (HAND + 0.1, 0.55, 1.05), 'wood'),   # mitten palm
        limb(f'{side}LegJ', LEG_TOP - KNEE_Y, 0.9, 'wood'),
        (f'{side}KneeJ', 'ball', (0, 0, 0), (0.55, 0.55, 0.55), 'wood_dark'),      # knee ring
        limb(f'{side}KneeJ', KNEE_Y - ANKLE_Y, 0.8, 'wood'),
        (f'{side}FootJ', 'ball', (0.55, -0.3, 0), (0.6, 0.95, 0.75), 'shoe'),       # big round clog
        (f'{side}FootJ', 'box', (0.0, 0.0, 0), (0.5, 0.95, 0.95), 'shoe'),          # ring cuff
    ]
    for fng in ('1st', '2nd', '3rd', '4th', 'Thumb'):
        BLOCKS += [limb(f'{side}{fng}Na', 0.34, 0.28, 'wood'), limb(f'{side}{fng}Nb', 0.3, 0.25, 'wood')]


# ---- fighter data: attributes (design v1.1 §3), hurtboxes (no hurtbox on the cap, cape or collar tips), engine bones
# v1.3 movement (Michael's first hand playtest: "slippery"): a grounded character. HSDRaw's names mislead; the engine's
# (ftCo_DatAttrs) are in brackets. Every dash starts at its initial speed on frame 1 and accelerates to the run speed: v1.2
# started at 1.8 of 1.9 (95%: no felt acceleration); now 1.35 of 1.6 (84%, between Fox's 86% and Marth's 83%), with more
# acceleration and Fox's friction (less slide after a dash). Jumpsquat 5 (Falco, Peach), full hop 34.6 -> 29 units (Fox; Mario
# 27.8), and less air drift (the answer to his zoning is to jump in).
ATTRIBUTES = dict(
    Weight=80, TerminalVelocity=2.3, FastFallTerminalVelocity=3.0, Gravity=0.13,
    MaxAerialHorizontalSpeed=0.85,          # [air_drift_max] was 1.0 (Fox 0.83, Marth 0.9)
    AerialSpeed=0.035,                      # [air_drift_stick_mul] air acceleration, was 0.05 (Fox 0.06, Marth 0.03)
    AirFriction=0.0175, JumpStartupLag=5, MaximumShorthopVerticalVelocity=1.65,
    InitialVerticalJumpVelocity=2.75,       # full hop height v^2 / 2g: 29 units, Fox's (was 3.0: 34.6)
    MaximumShorthopHorizontalVelocity=1.3,  # [jump_h_max] the ground speed a jump keeps, was 1.5
    VerticalAirJumpMultiplier=0.95,
    InitialDashSpeed=1.35,                  # [dash_initial_velocity] was 1.8
    InitialRunSpeed=1.6,                    # [dash_max_velocity] the run speed, was 1.9 (Marth 1.8, Mario 1.5)
    StopTurnInitialSpeedA=0.08,             # [dash_accel_mul] was Mario's 0.06 (Fox 0.1)
    MaxWalkSpeed=1.0, Friction=0.08,        # [ground_friction] was Mario's 0.06 (Fox, Falco, Sheik 0.08)
    NumberOfJumps=2, ModelScale=1.0, NormalLandingLag=4, NairLandingLag=14,
    FairLandingLag=16, BairLandingLag=18, UairLandingLag=16, DairLandingLag=24, CameraZoomTargetBone='WaistN',
    LedgeJumpVerticalVelocity=3.0,
    # the shield's radius scales with ModelScale: Mario 10.75 x 1.1, the cast's mid-heights ~13.5-13.8 world units; Geno
    # (15.2 tall, scale 1.0) needs ~13.75 to cover his body and hat band at full shield (it sat at Mario's 10.75)
    ShieldSize=13.75,
    # DESIGN §6f: every throw plays at its own speed whatever the opponent weighs (the template's mask 0 played them at
    # 100 / weight: 1.33x on Fox), so each beat of a weapon throw and its shots keep their timing (Fox's forward and down
    # throws are weight-independent too)
    WeightIndependentThrows=15,
)
# (joint, p1, p2 in the joint's frame, radius, height class 0 low / 1 mid / 2 high, grabbable)
# v1.3 (Michael, 2026-09-27, with the production model): cast-typical limbs. The limb capsules were half the cast's (arms
# 0.5-0.55, legs 0.6-0.65 against 0.7-1.2; even Sheik's are 0.72 / 0.96), so the model came out spindly and he was
# harder to hit than anyone. The chunkier production body fills these.
HURTBOXES = [
    ('HeadN', (0, 1.8, 0.2), (0, 2.2, 0.2), 2.4, 2, 1),      # the carved head (the model's head is 2.45 across)
    ('WaistN', (0, 0.3, 0.2), (0, 2.2, 0.2), 2.6, 1, 1),
    ('HipN', (0, 0, 0.1), (0, 0.6, 0.1), 2.1, 0, 1),
    ('LShoulderJ', (0, 0, 0), (UPPER_ARM, 0, 0), 0.85, 1, 1), ('LArmJ', (0, 0, 0), (FOREARM + 0.4, 0, 0), 0.85, 1, 1),
    ('RShoulderJ', (0, 0, 0), (UPPER_ARM, 0, 0), 0.85, 1, 1), ('RArmJ', (0, 0, 0), (FOREARM + 0.4, 0, 0), 0.85, 1, 1),
    ('LHandN', (0, 0, 0), (HAND, 0, 0), 1.0, 1, 1), ('RHandN', (0, 0, 0), (HAND, 0, 0), 1.0, 1, 1),
    ('LLegJ', (0, 0, 0), (LEG_TOP - KNEE_Y, 0, 0), 1.05, 0, 1), ('LKneeJ', (0, 0, 0), (KNEE_Y - ANKLE_Y, 0, 0), 1.0, 0, 1),
    ('RLegJ', (0, 0, 0), (LEG_TOP - KNEE_Y, 0, 0), 1.05, 0, 1), ('RKneeJ', (0, 0, 0), (KNEE_Y - ANKLE_Y, 0, 0), 1.0, 0, 1),
]
# The ledge-grab box (ftData+0x44, scaled by ModelScale; the engine searches it for a ledge while he falls): the cast's
# median proportions for his height (Michael: "similar size to his default box, not noticeably larger or smaller"). The cast
# (disc, 25 fighters) against standing height: width 0.78, the box's centre 1.02 up, height 0.74 (Mario's box, which he
# inherited, sat at 0.73 / 0.92 / 0.61 on him).
LEDGE_GRAB = dict(width=12.8, y=16.7, height=12.1)
BONES = dict(
    ItemHoldBone='RHandNb', ShieldBone='ThrowN', TopOfHeadBone='CapN', LeftFootBone='LFootJ', RightFootBone='RFootJ',
    ECB=['CapN', 'RShoulderJ', 'LShoulderJ', 'RKneeJ', 'LKneeJ', 'HipN'], CenterBubble='WaistN',
    HeadBone='HeadN', RightArm='RArmJ', LeftLeg='LKneeJ', RightLeg='RKneeJ', LeftArm='LArmJ',
    RLegJ='RLegJ', LLegJ='LLegJ', RKneeJ='RKneeJ', LKneeJ='LKneeJ', RFootJ='RFootJ', LFootJ='LFootJ',
    RShoulderJ='RShoulderJ', LShoulderJ='LShoulderJ', RArmJ='RArmJ', LArmJ='LArmJ',
    # model parts (hand and cap poses the move scripts switch between): (first joint, joint count, the joints it poses).
    # The cap part owns the crown (CapN) only: its point is a physics chain (DYNAMICS), and a joint a part owns is blended
    # to the part's pose every frame (ftAnim_800707B0), which would fight the solver
    ModelParts=[('LHandN', 12, None), ('RHandN', 12, None), ('HeadN', 2, ['CapN'])],
)


# ---- the part poses (projects/geno/model, Gate 2): script command 0x29 (fcmd.part_pose) sets model part P (0 the left
# hand, 1 the right, 2 the cap) to pose K. Local rotations (radians, rig.rot_xyz order) per joint; a pose owns every joint
# it keys until the action changes (the engine resets poses on every action change). Hands, in Mario's order where his
# exist: 0 fist, 1 open (relaxed), then Geno's 2 point (the index finger out) and 3 grip (curled round a handle, for held
# items and grabs). A finger curls toward the palm about its local Y (the left hand +, the right -, as Mario's); the right
# hand is the left mirrored (x and y rotations negated). The cap: 0 rest, 1 back (the crown tipped back: effort, a
# shout), 2 low (pulled down over the eyes: menace, a charge).
def _hand(na, nb, thumb, thumb_b, index=None):
    p = {f'L{f}Na': (0.0, a, s) for f, a, s in zip(('1st', '2nd', '3rd', '4th'), na, (0.06, 0.02, -0.02, -0.06))}
    p.update({f'L{f}Nb': (0.0, b, 0.0) for f, b in zip(('1st', '2nd', '3rd', '4th'), nb)})
    if index is not None: p['L1stNa'], p['L1stNb'] = index
    p['LThumbNa'], p['LThumbNb'] = thumb, thumb_b
    return p


HAND_POSES = [
    _hand((1.35, 1.4, 1.4, 1.35), (1.45, 1.5, 1.5, 1.45), (0.45, 0.6, -0.95), (0.0, 0.7, 0.0)),               # 0 fist
    _hand((0.15, 0.2, 0.28, 0.36), (0.2, 0.25, 0.3, 0.35), (0.1, 0.12, -0.62), (0.0, 0.15, 0.0)),             # 1 open
    _hand((1.35, 1.4, 1.4, 1.35), (1.45, 1.5, 1.5, 1.45), (0.45, 0.6, -0.95), (0.0, 0.7, 0.0),
          index=((0.0, 0.04, 0.03), (0.0, 0.06, 0.0))),                                                       # 2 point
    _hand((0.9, 0.95, 0.95, 0.9), (1.0, 1.05, 1.05, 1.0), (0.35, 0.42, -0.95), (0.0, 0.35, 0.0)),             # 3 grip
]
CAP_POSES = [{'CapN': (0.0, 0.0, 0.0)}, {'CapN': (-0.38, 0.0, 0.0)}, {'CapN': (0.2, 0.0, 0.0)}]
# The hands' default in every animation (anims.base(); Michael, 2026-09-28: straight fingers read as flat mittens): a loose,
# relaxed curl between the open and grip poses, the little finger curled most. Left-hand local rotations; mirror() gives
# the right. A part pose (script command 0x29) or a move that keys the fingers overrides it.
RELAXED_HAND = _hand((0.42, 0.5, 0.58, 0.66), (0.5, 0.56, 0.62, 0.66), (0.22, 0.28, -0.72), (0.0, 0.3, 0.0))


def mirror_hand(pose):
    """A left-hand pose for the right hand: x and y rotations negated (as part_poses_export's side())."""
    return {'R' + n[1:]: (-r[0], -r[1], r[2]) for n, r in pose.items()}


# ---- the weapon forms (projects/geno/model/geno_forms.py builds the meshes; ART.md "Weapon forms: the interface"). The
# engine shows one option per visibility group (script command 0x1F, fcmd model / form): group 0 is the body; each hand
# has an arm group (its base meshes: forearm, palm, fingers, at four levels) and a form group (the form's own mesh).
# A form needs both commands (form_commands). Every group defaults to option 0 (ftGe_Init_OnDeath), and an action change
# reverts them all unless the new action keeps its model (Ft_MF_SkipModel), as part poses reset too: set a form, and a
# pose, in every action that shows one.
FORMS = ['hand', 'fshot', 'gun', 'stargun', 'cannon', 'beam', 'rocket']    # the form group's option = position
FORM_GROUPS = {'R': (1, 2), 'L': (3, 4)}      # (arm group, form group); the gun arm (his right) first
FORM_ARM = {'hand': 0, 'fshot': 1, 'gun': 0, 'stargun': 0, 'cannon': 3, 'beam': 2, 'rocket': 0}   # the arm group's option:
# 0 forearm + palm + fingers, 1 forearm + palm (the Finger Shot's tubes replace the fingers), 2 forearm (the beam replaces
# the hand), 3 none (the cannon replaces the forearm and the hand)
PART = {'L': 0, 'R': 1, 'cap': 2}             # model parts (BONES ModelParts order): script command 0x29's part
HAND_POSE = {'fist': 0, 'open': 1, 'point': 2, 'grip': 3}
CAP_POSE = {'rest': 0, 'back': 1, 'low': 2}


# Group 0 is the body. Its option 1 is Geno Flash's cannon (geno_cannon.py), the way Samus's group 0 option 2 is her
# Morph Ball: showing it hides every body mesh in one command. The hands' arm groups are separate, so the cannon's
# command set also takes both arms to option 3 (none): cannon_commands. An action change reverts all of it.
BODY_GROUP = 0
BODY = {'geno': 0, 'cannon': 1}


def cannon_commands(on):
    """The (group, option) model-mod pairs that show Geno Flash's cannon in place of his whole body (on), or Geno again."""
    arm = 3 if on else 0
    return [(BODY_GROUP, BODY['cannon' if on else 'geno']), (FORM_GROUPS['R'][0], arm), (FORM_GROUPS['L'][0], arm),
            (FORM_GROUPS['R'][1], 0), (FORM_GROUPS['L'][1], 0)]


def form_commands(side, form):
    """The (group, option) model-mod pairs that show `form` on hand `side` ('L' or 'R')."""
    arm, frm = FORM_GROUPS[side]
    return [(arm, FORM_ARM[form]), (frm, FORMS.index(form))]


def part_poses_export():
    """anims.json "part_poses" (FighterBuild reads it): per model part, per pose, {joint index: {"r": [x, y, z]}}."""
    idx = {j[0]: i for i, j in enumerate(JOINTS)}
    def side(pose, s):
        out = {}
        for n, r in pose.items():
            if s == 'R': n, r = 'R' + n[1:], (-r[0], -r[1], r[2])
            out[str(idx[n])] = {'r': [round(float(v), 5) for v in r]}
        return out
    parts = []
    for st, cnt, ents in BONES['ModelParts']:
        if st in ('LHandN', 'RHandN'):
            parts.append([side(p, st[0]) for p in HAND_POSES])
        else:
            parts.append([{str(idx[n]): {'r': list(r)} for n, r in p.items()} for p in CAP_POSES])
    return parts
IK = dict(LegParam=LEG_TOP - KNEE_Y, KneeParam=KNEE_Y - ANKLE_Y, FootParam1=1.4, FootParam2=0.25,
          ShoulderParam=UPPER_ARM, ArmParam=FOREARM)

# ---- dynamics: the cape and the cap's point as Melee's physics chains (ftData+0x2C; datkit writes them into Pl{CODE}.dat).
# How the engine runs them (decomp: ftCo_8009CF84 loads them at spawn, Fighter_procDynamics -> ftCo_8009DD94 -> lb_8001044C
# solves each chain once a frame, after the animation; the animation skips a physics joint): a chain is a run of joints
# through first children, consecutive in depth-first order; every joint but the last (the tail, only placed) is rotated.
# Per joint, per frame, starting from where the chain's next joint was last frame (so the chain trails its parent):
#   follow    (x the chain's follow_mul) 1 keeps that trailing world direction; below 1 turns it that fraction of the way
#             back toward riding the parent rigidly (every vanilla chain: 1)
#   gravity   the chain's pull toward straight down: gravity / the bone's length x sin(its angle from down), radians a frame
#   momentum  last frame's turn is applied again, less damp (radians a frame, subtracted)
#   step      the most the joint turns from the trailing direction in one frame: the drag (moving faster than step x the
#             bone's length a frame, the chain falls behind toward its limit; slower, momentum carries it along)
#   converge  turns it back toward its rest direction by this much a frame (snapping inside it): shape memory, which
#             no vanilla chain uses (0); the capelet's felt needs it, or gravity undoes the bell's flare
#   limit     the hard cone around the rest direction
# then away from the collision spheres (SPHERES: every chain avoids every sphere; a joint already inside one is let be)
# and, on the ground, the floor. The rest direction is the joint's rest rotation in JOINTS (so the modeller's rest pose is
# the shape the chain returns to: a moved joint moves its chain with it). Twist about the bone is bled off (x0.9 a frame).
# Vanilla (datkit dynamics PlMs.dat): Marth's, Roy's and Ganondorf's capes are three chains of 4 at gravity 0.1745, follow 1,
# limit 60 deg (Ganondorf's tighten to 30 down the chain), damp 0.0087 (Ganondorf 0.014), step 0.06-0.16, no spheres;
# Link's cap one chain of 4 at gravity 0.0436, limit 40-45 deg, step 0.052. Fox's tail and DK's tie avoid one sphere each.
# Geno's, tuned in game beside Marth (director/cape_lab.py) and off line on recorded runs (dynsim.py), are a felt capelet,
# not a cloak: converge beats gravity at rest (gravity / length x sin(the rest angle from down) is ~0.035 on the panels' first
# links and 0.044 on the back's hem), so it holds the modelled bell and hem; step 0.5 lets it ride steady motion (it trails
# ~20 degrees in a run and ~5 in a walk rather than sitting at its limit, as Marth's does); limits grow down the chain, the
# shoulder dome stiffest and the hem freest (the panels' hem at most 45 degrees off the body, the back's 52); damp 0.02
# settles a swing in 10-15 frames with one rebound. The cap's point is the floppy one (step 0.3, 14/26/34 degrees).
DYN_BONE = dict(follow=1.0, converge=0.0, limit=1.0472, damp=0.0087, step=0.0873)
DYNAMICS = [
    # (first joint, joint count, per-chain settings, per-joint settings for the rotated joints down the chain)
    ('CapeAN', 4, dict(gravity=0.08), [dict(converge=0.05, limit=0.2, damp=0.02, step=0.5),       # the back
                                        dict(converge=0.04, limit=0.3, damp=0.02, step=0.5),
                                        dict(converge=0.07, limit=0.4, damp=0.02, step=0.5)]),
    ('CapeLAN', 4, dict(gravity=0.08), [dict(converge=0.06, limit=0.15, damp=0.02, step=0.5),       # the side and front
                                        dict(converge=0.05, limit=0.28, damp=0.02, step=0.5),       # panels, over the arms
                                        dict(converge=0.05, limit=0.35, damp=0.02, step=0.5)]),
    ('CapeRAN', 4, dict(gravity=0.08), [dict(converge=0.06, limit=0.15, damp=0.02, step=0.5),
                                        dict(converge=0.05, limit=0.28, damp=0.02, step=0.5),
                                        dict(converge=0.05, limit=0.35, damp=0.02, step=0.5)]),
    ('CapMidN', 4, dict(gravity=0.035), [dict(converge=0.05, limit=0.25, damp=0.015, step=0.3),   # the cap's point
                                          dict(converge=0.045, limit=0.45, damp=0.015, step=0.3),
                                          dict(converge=0.06, limit=0.6, damp=0.015, step=0.3)]),
]
# actions whose animation drives some chains (Marth's cape wraps him in his Guard this way): per chain (by first joint),
# how many of its leading joints the animation keeps; 256 = the whole chain, unsolved. The guard animations fold the cap's
# point down inside the shield (anims.py guard_pose; the engine poses a physics joint's position only, not its rotation)
DYN_ANIMATED = {a: {'CapMidN': 256} for a in ('GuardOn', 'Guard', 'GuardOff', 'GuardDamage')}
# collision spheres the chains stay out of: (joint, centre in the joint's frame, radius); at most 11
SPHERES = [   # the body under the back of the cape, from the model's surface (chest back at z -1.4, pelvis -1.3), 0.3 or more
              # clear of the cape's joints at rest so they only act when it swings in (the solver adds 0.1)
    ('WaistN', (0, 1.8, 0), 1.4), ('WaistN', (0, 0.3, -0.05), 1.15),      # chest, waist
    ('HipN', (0, 0, -0.15), 1.2),                                          # pelvis
]


def dynamics_export():
    """DYNAMICS and SPHERES as rig.json's "dynamics": chains by joint index with their 15-float parameter blocks (the
    engine's order: follow, converge, rest rotation x y z w, limit, 6 unused range floats, damp, step)."""
    names = [j[0] for j in JOINTS]
    parent = {n: p for n, p, t, r in JOINTS}
    rest = {n: r for n, p, t, r in JOINTS}
    chains, used = [], set()
    for start, count, cs, bones in DYNAMICS:
        i0 = names.index(start)
        js = names[i0:i0 + count]
        for k in range(1, count):      # each joint the first child of the one before (lb_8000FD48 walks jobj->child)
            if parent[js[k]] != js[k - 1] or next(n for n, p, *_ in JOINTS if p == js[k - 1]) != js[k]:
                raise SystemExit(f'dynamics: {js[k]} is not the first child of {js[k - 1]}')
        if used & set(js): raise SystemExit(f'dynamics: chain {start} overlaps another')
        used |= set(js)
        params = []
        for k, j in enumerate(js):
            b = dict(DYN_BONE, **bones[min(k, count - 2)])      # the tail repeats the joint before it (as vanilla's do)
            params.append([b['follow'], b['converge'], *rest[j], 0.0, b['limit'],
                           2 * math.pi, 2 * math.pi, 2 * math.pi, -2 * math.pi, -2 * math.pi, -2 * math.pi, b['damp'], b['step']])
        chains.append(dict(bone=i0, count=count, follow_mul=cs.get('follow_mul', 1.0), mul_y=cs.get('mul_y', 1.0),
                           gravity=cs['gravity'], params=params, names=js))
    if len(chains) >= 10: raise SystemExit('dynamics: at most 9 chains (Ft_Dynamics_NumMax)')
    if len(SPHERES) > 11: raise SystemExit('dynamics: at most 11 spheres')
    starts = [c[0] for c in DYNAMICS]
    for a, row in DYN_ANIMATED.items():
        if set(row) - set(starts): raise SystemExit(f'dynamics: {a} names a chain that is not in DYNAMICS')
    return dict(chains=chains, spheres=[dict(bone=names.index(j), offset=list(c), r=r) for j, c, r in SPHERES],
                animated={a: [row.get(st, 0) for st in starts] for a, row in DYN_ANIMATED.items()})


# ---- matrices (row vectors, v * M, as in HSD: scale, then rotate X, Y, Z, then translate)
def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

def rot_xyz(rx, ry, rz):
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    X = [[1, 0, 0, 0], [0, cx, sx, 0], [0, -sx, cx, 0], [0, 0, 0, 1]]
    Y = [[cy, 0, -sy, 0], [0, 1, 0, 0], [sy, 0, cy, 0], [0, 0, 0, 1]]
    Z = [[cz, sz, 0, 0], [-sz, cz, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    return mat_mul(mat_mul(X, Y), Z)

def local_mat(t, r, s=None):
    m = rot_xyz(*r)
    if s is not None:                              # scale first (row vectors: S R T), as HSD's SRT
        m = [[v * s[i] for v in m[i]] if i < 3 else m[i] for i in range(4)]
    m[3] = [t[0], t[1], t[2], 1]
    return m

def world_mats(joints=JOINTS, pose=None):
    """World matrices for every joint, with pose overriding (t, r) and optionally a scale (s) per joint name; scale is
    inherited down the chain (classical scale, as the engine's figatrees set it)."""
    out, idx = {}, {}
    for name, parent, t, r in joints:
        s = None
        if pose and name in pose:
            t, r, s = pose[name].get('t', t), pose[name].get('r', r), pose[name].get('s')
        m = local_mat(t, r, s)
        out[name] = mat_mul(m, out[parent]) if parent else m
    return out

def xform(p, m):
    return tuple(p[0] * m[0][i] + p[1] * m[1][i] + p[2] * m[2][i] + m[3][i] for i in range(3))


# ---- block geometry (triangles in the joint's frame)
def block_tris(shape, c, s, rot=(0, 0, 0)):
    tris = block_tris_axis(shape, (0, 0, 0), s)
    m = rot_xyz(*rot)
    return [[tuple(xform(p, m)[i] + c[i] for i in range(3)) for p in tri] for tri in tris]


def block_tris_axis(shape, c, s):
    tris = []
    if shape == 'cone':
        n = 12
        base = [(s[0] * math.cos(2 * math.pi * i / n), 0, s[2] * math.sin(2 * math.pi * i / n)) for i in range(n)]
        tip, ctr = (0, s[1], 0), (0, 0, 0)
        for i in range(n):
            a, b = base[i], base[(i + 1) % n]
            tris += [(a, tip, b), (a, b, ctr)]
        return tris
    if shape == 'box':
        hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
        v = [(c[0] + x * hx, c[1] + y * hy, c[2] + z * hz) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        for a, b, cc, d in quads:
            tris += [(v[a], v[b], v[cc]), (v[a], v[cc], v[d])]
    else:
        n_lon, n_lat = 12, 8
        def pt(i, k):
            th, ph = 2 * math.pi * i / n_lon, math.pi * k / n_lat - math.pi / 2
            return (c[0] + s[0] * math.cos(ph) * math.cos(th), c[1] + s[1] * math.sin(ph), c[2] + s[2] * math.cos(ph) * math.sin(th))
        for k in range(n_lat):
            for i in range(n_lon):
                a, b, cc, d = pt(i, k), pt(i + 1, k), pt(i + 1, k + 1), pt(i, k + 1)
                if k > 0: tris.append((a, cc, b))
                if k < n_lat - 1: tris.append((a, d, cc))
    return tris


def export(path):
    names = [j[0] for j in JOINTS]
    parts = {p: i for i, p in enumerate(PARTS)}
    part_to_joint = [names.index(p) if p in names else 255 for p in PARTS] + [0, 0]   # 56 entries, as PlCo's tables
    joint_to_part = [parts.get(n, 255) for n in names]
    W = world_mats()
    blocks = []
    for j, shape, c, s, col, *rot in BLOCKS:
        tris = [[xform(p, W[j]) for p in tri] for tri in block_tris(shape, c, s, *rot)]
        blocks.append(dict(joint=names.index(j), colour=C[col], tris=tris))
    J = names.index
    bones = {k: (J(v) if isinstance(v, str) else v) for k, v in BONES.items() if k not in ('ECB', 'ModelParts')}
    bones['ECB'] = [J(n) for n in BONES['ECB']]
    bones['ModelParts'] = [dict(start=J(st), count=c, entries=[J(e) for e in ents] if ents else list(range(J(st), J(st) + c)))
                           for st, c, ents in BONES['ModelParts']]
    attrs = {k: (J(v) if isinstance(v, str) else v) for k, v in ATTRIBUTES.items()}
    hurt = [dict(bone=J(j), p1=list(a), p2=list(b), size=r, type=h, grab=g) for j, a, b, r, h, g in HURTBOXES]
    rig = dict(joints=[dict(name=n, parent=names.index(p) if p else -1, t=list(t), r=list(r)) for n, p, t, r in JOINTS],
               part_to_joint=part_to_joint, joint_to_part=joint_to_part, blocks=blocks, attributes=attrs, hurtboxes=hurt,
               bones=bones, ik=IK, jnames=GLTF_JNAMES, dynamics=dynamics_export(), ledge=LEDGE_GRAB)
    if MODEL:
        # the costumes (model/costumes.py): a recoloured copy of the model folder each, next to the rig json; fighter-build
        # writes one PlGe<Cc>.dat per entry. GENO_COSTUMES=Nr,Re,... picks another set (the review's candidates).
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model'))
        import costumes
        codes = os.environ['GENO_COSTUMES'].split(',') if os.environ.get('GENO_COSTUMES') else None
        cos = costumes.write(os.path.dirname(MODEL['high']), os.path.join(os.path.dirname(os.path.abspath(path)), 'costumes'), codes)
        rig['model'] = dict(MODEL, costumes=cos)
    json.dump(rig, open(path, 'w'))
    print(f'{len(JOINTS)} joints, {len(blocks)} blocks, {sum(len(b["tris"]) for b in blocks)} triangles -> {path}')


def export_c(path):
    """The parts table as C, for the decomp's ftGeno module (joint -> part, part -> joint, joint count)."""
    names = [j[0] for j in JOINTS]
    parts = {p: i for i, p in enumerate(PARTS)}
    j2p = [parts.get(n, 255) for n in names]
    p2j = [names.index(p) if p in names else 255 for p in PARTS] + [0, 0]
    row = lambda xs: ',\n'.join('    ' + ', '.join(f'{x:3d}' for x in xs[i:i + 12]) for i in range(0, len(xs), 12))
    open(path, 'w').write(
        '/* generated by animation-pipeline projects/geno/rig/rig.py: Geno\'s skeleton, as the engine addresses it */\n'
        f'#define FTGE_JOINT_COUNT {len(names)}\n'
        '/* Geno Flash\'s cannon (no parts: addressed by joint index) and its muzzle, along CannonBarrelN\'s +Z */\n'
        + ''.join(f'#define FTGE_JOINT_{n[:-1].upper()} {names.index(n)}\n' for n in CANNON_JOINTS)
        + f'#define FTGE_CANNON_MUZZLE {CANNON_MUZZLE:.4f}f\n'
        '#ifndef FTGE_RIG_DEFINES_ONLY /* the tables once, in ftgeno.c; other files take the defines */\n'
        f'static u8 ftGe_JointToPart[{len(j2p)}] = {{\n{row(j2p)}\n}};\n'
        f'static u8 ftGe_PartToJoint[{len(p2j)}] = {{\n{row(p2j)}\n}};\n'
        '#endif\n'
        '/* joints: ' + ' '.join(f'{i}:{n}' for i, n in enumerate(names)) + ' */\n')
    print('wrote', path)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--c':
        export_c(sys.argv[2])
    else:
        export(sys.argv[1] if len(sys.argv) > 1 else 'rig.json')
