"""Geno's states around the moves, blockout motion only (the template's scripts stay: their sounds, intangibility and
timing are the engine's and the cast's):
  - the ledge: the catch, the hang, the climbs, the ledge rolls and the ledge jumps. Their TransN paths are his own, measured
    from the ledge corner as the engine places them (moves.py, ledge attacks), with the template's timing: the frame he stands
    on the stage and the distance he ends at are Mario's at Geno's scale (anims.root_motion), so the ledge still plays
    the same;
  - the floor: the knockdown bounce, the lying idle's neighbours (the jolt when hit, the stand-up, the rolls), the techs and
    the stamina collapse. The rolls keep the template's root-motion paths (anims.root_motion adds them: these keys never
    move TransN).
Frame counts are the template's (an action's length is its animation's). Registered into moves.MOVES with no script.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig
from anims import base, tuck, down, stride
import moves
from moves import arm, climb, hang_grip, on_stage, HANG_T, MOVES

HY, HZ = HANG_T[1], HANG_T[2]
TAU = 2 * math.pi


def state(name, frames):
    def reg(fn):
        MOVES[name] = (frames, lambda k, fn=fn: (None, fn()))
        return fn
    return reg


# ---------------------------------------------------------------------------------------------------------------- the ledge
@state('CliffCatch', 8)
def cliff_catch():
    """The catch: his hands find the lip and his body swings in under it to the hang. The engine eases him from wherever
    the ledge-grab box caught him onto this path over its first 6 frames (decomp ftcliffcommon.c, Geno's catch), so the
    path starts where a falling catch usually is (the box's floor sits 10 above his feet: the lip ~11 above, a few out)."""
    return [(0, climb(-10.8, -4.0, lean=0.2, legs=0.45)),        # reaching, legs still drawn up from the fall
            (2, climb(-12.2, -2.8, lean=0.1, legs=0.5)),
            (4, climb(-13.2, -1.7, lean=-0.1, legs=0.55)),       # the bottom of the swing: legs forward under the lip
            (6, climb(-12.9, -2.2, lean=0.05, legs=0.15)),       # swinging back
            (8, hang_grip())]


@state('CliffWait', 100)
def cliff_wait():
    """The hang, held (every ledge action starts from it)."""
    return [(0, hang_grip()), (100, hang_grip())]


def step(z, phase, crouch=0.15):
    """A short step onto the stage (a stride frame, side-on), at TransN z."""
    return stride(phase, amp=0.6, crouch=crouch).move('TransN', (0, 0, z))


@state('CliffClimbQuick', 35)
def climb_quick():
    """Under 100%: the ledge attack's snap pull-up, on the corner on frame 20 (the template's), then a step in to 8.2."""
    return [(0, hang_grip()), (3, climb(HY - 0.5, HZ, lean=0.1)), (7, climb(HY - 0.9, HZ, lean=0.15, legs=0.2)),
            (12, climb(HY + 4.5, HZ + 0.1, lean=0.6, legs=0.6)), (16, climb(-3.6, HZ + 0.3, lean=1.1, knee=1.0, legs=0.4)),
            (18, climb(-1.4, -1.0, lean=0.95, knee=1.0, legs=0.2)),
            (20, on_stage(0.0, 0.85, lean=0.55)),
            (24, on_stage(2.4, 0.5, lean=0.25)), (29, step(5.4, 0.25)), (32, step(7.2, 0.5)), (35, on_stage(8.2, 0.0))]


@state('CliffClimbSlow', 60)
def climb_slow():
    """From 100%: the heavy haul, on the corner on frame 34, a step in to 3.5 (template steps sound at 37 and 59)."""
    return [(0, hang_grip()), (4, climb(HY - 0.6, HZ, lean=0.1)), (10, climb(HY + 0.6, HZ, lean=0.2)),
            (18, climb(HY + 4.0, HZ + 0.1, lean=0.5, legs=0.3)), (26, climb(-4.6, HZ + 0.3, lean=1.0, knee=0.8, legs=0.3)),
            (30, climb(-1.8, -1.2, lean=1.0, knee=1.0, legs=0.2)),
            (34, on_stage(0.0, 0.9, lean=0.6)), (40, on_stage(0.4, 0.6, lean=0.3)), (48, on_stage(1.2, 0.35)),
            (54, step(2.4, 0.25)), (58, step(3.3, 0.5)), (60, on_stage(3.5, 0.0))]


CLOTH = ('Cape', 'CapMid', 'CapTip')          # the cape and the cap's point crumple against the floor: not contact


def _verts(p):
    """Every block vertex of a pose but the cloth's, in the world (his position at the origin)."""
    solved = {k: {'t': v[0], 'r': v[1]} for k, v in p.solve().items()}
    W = rig.world_mats(pose=solved)
    for j, shape, c, sz, col, *rot in rig.BLOCKS:
        if j.startswith(CLOTH): continue
        for tri in rig.block_tris(shape, c, sz, *rot):
            for v in tri:
                yield rig.xform(v, W[j])


def _curled(arms):
    """The curled body, not yet turned: knees to the chest, shins tucked, head down, arms round the shins."""
    p = tuck(1.3, arms=arms)
    p.rot('WaistN', (0.9, 0, 0)).rot('HeadN', (0.5, 0, 0))
    for sd, sx in (('L', 1), ('R', -1)):
        p.aim(f'{sd}LegJ', (sx * 0.15, 0.55, 0.8)); p.aim(f'{sd}KneeJ', (0, -0.95, 0.15))
        p.aim(f'{sd}FootJ', (0, -0.2, 1), up=(0, -1, 0))
        p.aim(f'{sd}ShoulderJ', (sx * 0.35, -0.6, 0.8)); p.aim(f'{sd}ArmJ', (sx * 0.1, -0.9, -0.2))
    return p


def _ball(arms):
    """The curled body and the offset that centres it on XRotN, so it turns about its own middle."""
    p = _curled(arms).move('XRotN', (0, 0, 0))
    vs = list(_verts(p))
    cy = (min(v[1] for v in vs) + max(v[1] for v in vs)) / 2
    cz = (min(v[2] for v in vs) + max(v[2] for v in vs)) / 2
    return p, (0, -cy, -cz)


_BALL = {}


def curl(angle, arms=0.2, yaw=0.0):
    """Rolling: curled into a ball turned `angle` about his left-right axis (positive: the top goes forward, a forward
    roll), about the ball's own middle, lifted so its lowest point just touches the floor. yaw turns the ball about his
    vertical inside the roll (YRotN sits inside XRotN: a body direction v goes to v.Ry.Rx), for a roll that turns him
    round."""
    if arms not in _BALL:
        _BALL[arms] = _ball(arms)
    base_pose, centre = _BALL[arms]
    p = _curled(arms)
    y0 = p.trans.get('YRotN', (0, 0, 0))
    c = [a + b for a, b in zip(y0, centre)]
    Ry, Rx = rig.rot_xyz(0, yaw, 0), rig.rot_xyz(angle, 0, 0)
    R = [[sum(Ry[i][k] * Rx[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    turn = lambda v, M: None if v is None else [sum(v[i] * M[i][j] for i in range(3)) for j in range(3)]
    # the limbs are aimed in world directions (anims.Pose), so they turn with the ball too
    p.aims = {j: (turn(x, R), turn(up, R)) for j, (x, up) in p.aims.items()}
    p.move('YRotN', tuple(turn(c, Ry))).rot('YRotN', (0, yaw, 0))      # turning about the ball's middle
    p.move('XRotN', (0, 0, 0)).rot('XRotN', (angle, 0, 0))
    lift = -min(v[1] for v in _verts(p))
    return p.move('XRotN', (0, lift, 0))


def rolled(t0, t1, frames, a0=0.0, turn=TAU, **kw):
    """Keys for one roll: `turn` radians from a0 over [t0, t1], a key on every frame. The curled doll isn't round (the head
    and the cap's crown stand out), so the lift that keeps it on the floor has corners: each frame gets its own."""
    t0, t1 = int(round(t0)), int(round(t1))
    return [(f, curl(a0 + turn * (f - t0) / (t1 - t0), **kw)) for f in range(t0, t1 + 1)]


def ledge_roll(stand, end, frames, dist_keys):
    """The ledge roll: the pull-up onto the corner, a forward roll along dist_keys ((frame, z) of TransN, the template's
    distance: 35 units), and up."""
    k = [(0, hang_grip())]
    if stand == 20:
        k += [(3, climb(HY - 0.5, HZ, lean=0.1)), (7, climb(HY - 0.9, HZ, lean=0.15, legs=0.2)),
              (12, climb(HY + 4.5, HZ + 0.1, lean=0.6, legs=0.6)), (16, climb(-3.6, HZ + 0.3, lean=1.1, knee=1.0, legs=0.4)),
              (18, climb(-1.4, -1.0, lean=0.95, knee=1.0, legs=0.2))]
    else:
        k += [(4, climb(HY - 0.6, HZ, lean=0.1)), (10, climb(HY + 0.6, HZ, lean=0.2)),
              (18, climb(HY + 4.0, HZ + 0.1, lean=0.5, legs=0.3)), (26, climb(-4.6, HZ + 0.3, lean=1.0, knee=0.8, legs=0.3)),
              (30, climb(-1.8, -1.2, lean=1.0, knee=1.0, legs=0.2))]
    k.append((stand, on_stage(0.0, 0.9, lean=0.7)))
    zs = dict(dist_keys)
    f0, f1 = dist_keys[0][0], dist_keys[-3][0]
    for f, p in rolled(f0, f1, frames, a0=0.4):
        z = zs.get(f)
        if z is None:                                  # between the distance keys: interpolate the template's profile
            a = max(x for x in zs if x <= f); b = min(x for x in zs if x >= f)
            z = zs[a] + (zs[b] - zs[a]) * (f - a) / ((b - a) or 1)
        k.append((f, p.move('TransN', (0, 0, z))))
    fu, zu = dist_keys[-2]
    k += [(fu, on_stage(zu, 0.55)), (frames, on_stage(dist_keys[-1][1], 0.0))]
    return k


@state('CliffEscapeQuick', 50)
def escape_quick():
    return ledge_roll(20, 50, 50, [(22, 2.2), (26, 8.4), (30, 16.1), (34, 22.3), (38, 28.0), (42, 32.3), (46, 34.4), (50, 35.2)])


@state('CliffEscapeSlow', 80)
def escape_slow():
    return ledge_roll(34, 80, 80, [(38, 3.0), (44, 10.4), (50, 18.7), (56, 26.0), (62, 32.0), (68, 34.8), (74, 35.3), (80, 35.2)])


def ledge_jump(n):
    """The ledge jump's first part: pushing off the lip up to the corner (TransN rises to (0, 0), the template's straight
    line), ending in the air in the tuck CliffJump2 starts from (anims.keys_for: tuck(0.3))."""
    at = lambda u: (0, HY * (1 - u), HZ * (1 - u))
    push = lambda u, **kw: climb(at(u)[1], at(u)[2], **kw)
    tk = lambda u, a: tuck(a).move('TransN', at(u))
    return [(0, hang_grip()), (round(n * 0.2), push(0.2, lean=0.3, legs=0.5)), (round(n * 0.45), push(0.45, lean=0.5, legs=0.8)),
            (round(n * 0.7), tk(0.7, 0.6)), (n, tk(1.0, 0.3))]


state('CliffJumpQuick1', 16)(lambda: ledge_jump(16))
state('CliffJumpSlow1', 20)(lambda: ledge_jump(20))


# ---------------------------------------------------------------------------------------------------------------- the floor
def lie(face_up, lift=0.0, tip=1.45, limbs=0.0, knees=0.0):
    """Lying (anims.down), lifted off the floor by `lift`, tipped `tip`, the limbs flung up by `limbs` 0..1 (an impact or a
    jolt), the knees drawn up by `knees` 0..1."""
    p = down(face_up, tip=tip, height=(2.2 if face_up else 2.0) + lift)
    along = 1 if face_up else -1
    for sd, sx in (('L', 1), ('R', -1)):
        if limbs:
            p.aim(f'{sd}ShoulderJ', (sx * (0.5 + 0.3 * limbs), 0.9 * limbs - 0.1, along * (1 - limbs)))
            p.aim(f'{sd}ArmJ', (sx * 0.3, 1.0 * limbs - 0.05, along * (1 - 0.6 * limbs)))
            p.aim(f'{sd}LegJ', (sx * 0.2, 0.5 * limbs - 0.12, along))
        if knees:
            p.aim(f'{sd}LegJ', (sx * 0.2, 0.9 * knees - 0.12, along * (1 - 0.3 * knees)))
            p.aim(f'{sd}KneeJ', (0, -0.9 * knees, along * (1 - 0.5 * knees)))
    return p


def bound(face_up):
    """The knockdown: the impact (the limbs whip up), a rebound off the floor, a smaller one, and the lying pose
    DownWait holds."""
    return [(0, lie(face_up, limbs=0.8)), (3, lie(face_up, limbs=0.2)), (7, lie(face_up, lift=1.3, tip=1.3, limbs=0.6, knees=0.3)),
            (11, lie(face_up)), (14, lie(face_up, lift=0.45, tip=1.4, limbs=0.3)), (17, lie(face_up)), (26, lie(face_up))]


state('DownBoundU', 26)(lambda: bound(True))
state('DownBoundD', 26)(lambda: bound(False))


def jolt(face_up):
    """Hit while lying: the body jolts off the floor and drops back."""
    return [(0, lie(face_up, lift=0.8, limbs=0.7)), (4, lie(face_up, lift=0.3, limbs=0.3)), (8, lie(face_up)), (14, lie(face_up))]


state('DownDamageU', 14)(lambda: jolt(True))
state('DownDamageD', 14)(lambda: jolt(False))


def sit(tip, knees=1.0, height=2.1):
    """Sitting up from his back: the torso tipped back by `tip`, knees drawn up, hands planted behind him."""
    p = down(True, tip=tip, height=height)
    for sd, sx in (('L', 1), ('R', -1)):
        p.aim(f'{sd}LegJ', (sx * 0.2, 0.9 * knees - 0.1, 1 - 0.3 * knees)); p.aim(f'{sd}KneeJ', (0, -0.9 * knees, 1 - 0.5 * knees))
        p.aim(f'{sd}FootJ', (0, -0.15, 1), up=(0, -1, 0))
        p.aim(f'{sd}ShoulderJ', (sx * 0.4, -0.8, -0.5)); p.aim(f'{sd}ArmJ', (sx * 0.2, -1, -0.2))
    return p


def press(tip, knees=0.0, height=3.4):
    """Pushing up from his face: arms straight under the shoulders, knees coming under him."""
    p = down(False, tip=tip, height=height)
    for sd, sx in (('L', 1), ('R', -1)):
        p.aim(f'{sd}ShoulderJ', (sx * 0.3, -1, 0.3)); p.aim(f'{sd}ArmJ', (sx * 0.1, -1, 0.1))
        if knees:
            p.aim(f'{sd}LegJ', (sx * 0.15, -1, 0.9 * knees - (1 - knees))); p.aim(f'{sd}KneeJ', (0, -0.3 * knees, -1))
    return p


@state('DownStandU', 30)
def stand_u():
    """Up from his back: sit up, knees in, rock forward onto his feet in a crouch, stand (Wait's first frame)."""
    return [(0, lie(True)), (4, sit(1.1, knees=0.5, height=2.9)), (8, sit(0.6, height=2.4)), (12, sit(0.15, height=2.6)),
            (16, base(crouch=0.9, lean=0.45)), (22, base(crouch=0.45, lean=0.15)), (30, base())]


@state('DownStandD', 30)
def stand_d():
    """Up from his face: a push-up, knees under him, into a crouch, stand."""
    return [(0, lie(False)), (5, press(1.05)), (10, press(0.75, knees=0.8, height=4.4)), (15, base(crouch=0.9, lean=0.6)),
            (22, base(crouch=0.45, lean=0.15)), (30, base())]


def floor_roll(face_up, fwd):
    """A get-up roll (DownForward / DownBack, the template's 41 units over frames 3-24): curl up off the floor, one roll in
    the direction he travels, open into a crouch, stand."""
    a0 = -1.45 if face_up else 1.45
    turn = TAU - a0 if fwd else -TAU - a0            # end upright, a whole number of turns from lying
    return [(0, lie(face_up))] + rolled(3, 24, 36, a0=a0, turn=turn) + [(28, base(crouch=0.6)), (36, base())]


state('DownFowardU', 36)(lambda: floor_roll(True, True))
state('DownBackU', 36)(lambda: floor_roll(True, False))
state('DownFowardD', 36)(lambda: floor_roll(False, True))
state('DownBackD', 36)(lambda: floor_roll(False, False))


@state('DownSpotD', 20)
def stamina_collapse():
    """The stamina KO: he buckles and falls on his face, into DownWaitD."""
    return [(0, base()), (5, base(crouch=0.8, lean=0.6)), (10, press(1.1, height=4.4)), (14, lie(False, lift=0.4, limbs=0.3)),
            (20, lie(False))]


@state('Passive', 26)
def tech_in_place():
    """Teching in place: he lands low, hips back, arms out, then springs up with his arms thrown overhead (the cast's
    tech in place dips to ~0.65 of their height and pops up past it) and settles."""
    land = arm(arm(base(crouch=1.0, lean=0.5), 'R', (-0.7, -0.2, 0.3)), 'L', (0.7, -0.2, 0.3))
    y = land.trans.get('YRotN', (0, 0, 0))
    land.move('YRotN', (y[0], y[1], y[2] - 2.4))
    pop = arm(arm(base(lean=-0.1), 'R', (-0.25, 1, 0.1)), 'L', (0.25, 1, 0.1))
    y = pop.trans.get('YRotN', (0, 0, 0))
    pop.move('YRotN', (y[0], y[1] + 2.2, y[2]))                                     # a hop: the feet leave the floor
    return [(0, land), (5, base(crouch=0.8, lean=0.3)), (11, pop), (17, base(crouch=0.35, arms=0.3)), (26, base())]


def tech_roll(fwd):
    """A tech roll (the template's 47 units over frames 4-32): curled from the landing, one roll, up."""
    pop = arm(arm(base(crouch=0.1), 'R', (-0.3, 1, 0.2)), 'L', (0.3, 1, 0.2))        # up with a flourish, as the cast pop
    y = pop.trans.get('YRotN', (0, 0, 0))
    pop.move('YRotN', (y[0], y[1] + 1.6, y[2]))
    return [(0, curl(0.0))] + rolled(4, 28, 40, a0=0.0, turn=TAU if fwd else -TAU) + [(31, base(crouch=0.6)), (35, pop), (40, base())]


state('PassiveStandF', 40)(lambda: tech_roll(True))
state('PassiveStandB', 40)(lambda: tech_roll(False))
# the wall and ceiling techs are airborne: tucked (their template paths hold him against the wall or ceiling), then the
# fall's tuck(0.3)
state('PassiveWall', 26)(lambda: [(0, tuck(0.9)), (26, tuck(0.4))])
state('PassiveWallJump', 40)(lambda: [(0, tuck(0.9)), (20, tuck(0.6)), (40, tuck(0.3))])
state('PassiveCeil', 26)(lambda: [(0, tuck(0.9)), (26, tuck(0.3))])
