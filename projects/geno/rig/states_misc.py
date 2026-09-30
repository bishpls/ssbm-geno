"""Geno's character moments (the idles, the taunt, the entrance) and the motion toolkit his item actions share.

Every action here is a function of time sampled on every frame (the figatrees interpolate their keys linearly, so a key
per frame keeps the arcs and the easing): each body part's parameters are splines over the action's frames, and a pose
is built from them by `body()`, which starts from the idle stance (anims.base) and adds to it:
  - the pelvis moves (`root`, `crouch`, `bob`) and turns (`turn`, `tilt`) over feet that stay where they're put: the legs
    are solved by two-bone IK to each foot's target, with the heel lift base() uses, so a planted foot never slides;
  - the hips, chest, neck and head turn on top of the stance's own turn toward the camera;
  - the arms are aimed in the chest's frame (they follow the torso unless told otherwise), or reach a point by IK, and
    the hands can be turned to hold an item: the item hangs on RHandNb (ItemHoldBone), whose +Y is a sword's blade and
    +Z a gun's barrel.
With every parameter at rest body() is base() exactly, so an action authored to start and end at rest meets Wait1's
first frame (the engine never blends between actions). Registered into moves.MOVES like states.py.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig
import anims
from anims import Pose, base, leg_ik, heel_lift, STANCE, norm, cross, dot
from moves import MOVES

TAU = 2 * math.pi
NAMES = [j[0] for j in rig.JOINTS]


def state(name, frames, script=None):
    """Register an action: its length, a script builder (None keeps the template's) and a key-pose function."""
    def reg(fn):
        MOVES[name] = (frames, lambda k, fn=fn: (script() if script else None, fn()))
        return fn
    return reg


# ---------------------------------------------------------------------------------------------------------------- curves
def clamp(u, a=0.0, b=1.0):
    return a if u < a else b if u > b else u


def smooth(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def ease_out(u):
    u = clamp(u)
    return 1 - (1 - u) ** 2


def ease_in(u):
    u = clamp(u)
    return u * u


def lerp(a, b, u):
    if isinstance(a, (tuple, list)):
        return tuple(x + (y - x) * u for x, y in zip(a, b))
    return a + (b - a) * u


def _add(a, b, k=1.0):
    if isinstance(a, (tuple, list)):
        return tuple(x + k * y for x, y in zip(a, b))
    return a + k * b


def spline(t, keys):
    """A cubic Hermite through keys [(frame, value[, 'hold'])], values scalars or tuples. Tangents are Catmull-Rom's over
    uneven spacing, flat at the ends and at keys marked 'hold' (a pose that settles there). Outside the keys it holds."""
    ks = sorted(keys, key=lambda k: k[0])
    if t <= ks[0][0]: return ks[0][1]
    if t >= ks[-1][0]: return ks[-1][1]
    n = len(ks)

    def tan(i):
        if i == 0 or i == n - 1 or (len(ks[i]) > 2 and ks[i][2] == 'hold'):
            return _add(ks[i][1], ks[i][1], -1.0)             # zero, in the value's shape
        f0, v0 = ks[i - 1][0], ks[i - 1][1]
        f1, v1 = ks[i + 1][0], ks[i + 1][1]
        d = _add(v1, v0, -1.0)
        return tuple(x / (f1 - f0) for x in d) if isinstance(d, tuple) else d / (f1 - f0)

    for i in range(n - 1):
        (fa, va), (fb, vb) = ks[i][:2], ks[i + 1][:2]
        if fa <= t <= fb:
            h = fb - fa
            u = (t - fa) / h
            h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
            ma, mb = tan(i), tan(i + 1)
            if isinstance(va, (tuple, list)):
                return tuple(h00 * a + h10 * h * p + h01 * b + h11 * h * q for a, p, b, q in zip(va, ma, vb, mb))
            return h00 * va + h10 * h * ma + h01 * vb + h11 * h * mb
    return ks[-1][1]


def wave(t, n, cycles=1, phase=0.0):
    """A loop-safe sine: 0 at t = 0 and t = n, periodic over n, sin(2 pi cycles t / n - phase) + sin(phase)."""
    return math.sin(TAU * cycles * t / n - phase) + math.sin(phase)


def dip(t, n, cycles=1):
    """A loop-safe bump: 0 at the loop's ends (and every cycle's), 1 in the middle, with flat tangents at the seam."""
    return 0.5 - 0.5 * math.cos(TAU * cycles * t / n)


# ---------------------------------------------------------------------------------------------------------------- vectors
def rot_y(v, th):
    """World vector v turned th radians about +Y (as moves.spin: +Z toward +X for positive th)."""
    c, s = math.cos(th), math.sin(th)
    return (v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c)


def vec_mat(v, M):
    """Row vector v times the 3x3 part of M (local -> world for a joint's world matrix)."""
    return tuple(sum(v[i] * M[i][j] for i in range(3)) for j in range(3))


def mat_vec_t(v, M):
    """World -> local: v times M's transpose."""
    return tuple(sum(v[j] * M[i][j] for j in range(3)) for i in range(3))


def rodrigues(v, k, th):
    """v turned th radians about unit axis k."""
    k = norm(k)
    c, s = math.cos(th), math.sin(th)
    kv = cross(k, v)
    kd = dot(k, v)
    return tuple(v[i] * c + kv[i] * s + k[i] * kd * (1 - c) for i in range(3))


def xf(pt, M):
    """A point in a joint's frame to the model's space."""
    return tuple(rig.xform(pt, M))


def to_local(pt, M):
    """A model-space point into a joint's frame (M a world matrix: rows are its axes, then its origin)."""
    d = [pt[i] - M[3][i] for i in range(3)]
    return tuple(sum(d[j] * M[i][j] for j in range(3)) for i in range(3))


def world(p):
    sol = {k: {'t': v[0], 'r': v[1]} for k, v in p.solve().items()}
    return rig.world_mats(pose=sol)


def pos(W, joint):
    return tuple(W[joint][3][:3])


def slerp_dir(a, b, u):
    """Directions a to b by angle (normalised lerp is close enough for our small steps, but keeps unit length)."""
    return tuple(norm([x + (y - x) * u for x, y in zip(norm(a), norm(b))]))


# ---------------------------------------------------------------------------------------------------------------- the stance
S = STANCE
FEET = {'L': (1.3, rig.ANKLE_Y, S['fwd']), 'R': (-1.3, rig.ANKLE_Y, S['back'])}
TOE = {'L': S['toe_out'], 'R': -S['toe_out']}
_BASE = base()
_BW = world(_BASE)
CHEST0 = [row[:3] for row in _BW['WaistN'][:3]]
# base()'s arms are aimed in world directions; in the chest's frame they follow the torso when it turns or bends
ARM0 = {}
for _s, _sx in (('L', 1), ('R', -1)):
    ARM0[_s] = (mat_vec_t(norm((_sx * 0.28, -1, 0.12)), CHEST0), mat_vec_t(norm((_sx * 0.15, -0.9, 0.45)), CHEST0))


def body(crouch=0.0, lean=0.0, bob=0.0, root=(0, 0, 0), turn=0.0, tilt=(0, 0), hip=(0, 0, 0), waist=(0, 0, 0),
         neck=(0, 0, 0), head=(0, 0, 0), feet=None, arms=None, trans=None, stance_turn=True, flex=anims.ANKLE_FLEX):
    """A standing pose (see the module notes). feet: side -> (x, y, z) ankle target in the model's space, or a dict with
    pos, yaw (the foot's heading, radians toward +X; default the stance's toe-out, turned with `turn` when stance_turn)
    and pitch (toes down, for a lifted foot; a planted foot lifts its heel on its own). arms: side -> an arm spec (arm()).
    trans: TransN's translation (root-motion actions); the feet targets are in the same space, TransN included."""
    p = base(crouch=crouch, lean=lean, bob=bob)
    y0 = p.trans['YRotN']
    p.move('YRotN', (y0[0] + root[0], y0[1] + root[1], y0[2] + root[2])).rot('YRotN', (tilt[0], turn, tilt[1]))
    p.rot('HipN', (hip[0], S['hip_yaw'] + hip[1], hip[2]))
    p.rot('WaistN', (0.12 + lean + waist[0], S['chest_yaw'] + waist[1], waist[2]))
    if any(neck): p.rot('NeckN', tuple(neck))
    p.rot('HeadN', (head[0], S['head_yaw'] + head[1], head[2]))
    if trans is not None: p.move('TransN', tuple(trans))
    W = world(p)
    chest = [row[:3] for row in W['WaistN'][:3]]
    for s in 'LR':
        spec = (arms or {}).get(s)
        set_arm(p, s, spec, W, chest)
    feet = feet or {}
    t0 = trans or (0, 0, 0)
    for s in 'LR':
        f = feet.get(s)
        if f is None:
            f = {}
        elif not isinstance(f, dict):
            f = dict(pos=f)
        at = f.get('pos')
        if at is None:
            at = FEET[s]
            if turn and stance_turn: at = rot_y(at, turn)
            at = (at[0] + t0[0], at[1] + t0[1], at[2] + t0[2])
        yaw = f.get('yaw', TOE[s] + (turn if stance_turn else 0.0))
        plant(p, s, at, yaw, f.get('pitch'), W, flex)
    return p


def lift_heel(planted, f, shin, flex=anims.ANKLE_FLEX):
    """anims.heel_lift with the ankle's flex as a parameter (the idles keep the rear heel down through small dips)."""
    if flex == anims.ANKLE_FLEX:
        return heel_lift(planted, f, shin)
    d = norm([-x for x in shin])
    lean = math.atan2(dot(d, f), d[1])
    th = min(anims.HEEL_MAX, max(0.0, lean - flex))
    h, B = planted[1], anims.BALL
    du = -B * math.cos(th) + h * math.sin(th) + B
    dv = B * math.sin(th) + h * math.cos(th) - h
    return th, (planted[0] + f[0] * du, planted[1] + dv, planted[2] + f[2] * du)


def plant(p, side, ankle, yaw, pitch=None, W=None, flex=anims.ANKLE_FLEX):
    """Solve one leg so the ankle sits at `ankle` (model space), knee over the toes, foot heading `yaw`. A foot on the floor
    (pitch None) lifts its heel as base() does when the shin leans past the ankle's flex; pitch tips a lifted foot's toes
    down by that much."""
    W = W or world(p)
    hip = pos(W, f'{side}LegJA')
    fwd = (math.sin(yaw), 0.0, math.cos(yaw))
    if pitch is None and ankle[1] <= rig.ANKLE_Y + 0.05:
        target = ankle                                    # base()'s loop, step for step (so rest is base() exactly)
        for _ in range(4):
            thigh, shin = leg_ik(hip, target, fwd)
            heel, target = lift_heel(ankle, fwd, shin, flex)
    else:
        heel = pitch or 0.0
        thigh, shin = leg_ik(hip, ankle, fwd)
    p.aim(f'{side}LegJ', thigh)
    p.aim(f'{side}KneeJ', shin)
    c, sn = math.cos(heel), math.sin(heel)
    p.aim(f'{side}FootJ', (fwd[0] * c, -sn, fwd[2] * c), up=(-fwd[0] * sn, -c, -fwd[2] * sn))
    return p


def arm(up=None, fore=None, world_up=None, world_fore=None, reach=None, pole=None, hand=None, hand_up=None,
        hand_local=False, weight=1.0):
    """An arm spec for body(): directions in the chest's frame (up, fore: the upper arm and forearm; None keeps base()'s),
    or in the world (world_up, world_fore), or reach = the wrist's target (model space) with the elbow toward pole. hand,
    hand_up: the hand's direction (RHandN's +X, wrist to fingers) and its up (+Y, the back of the hand; the item's +Y is
    -hand_up), in the world unless hand_local (the chest's frame)."""
    return dict(up=up, fore=fore, wup=world_up, wfore=world_fore, reach=reach, pole=pole, hand=hand, hand_up=hand_up,
                hand_local=hand_local, weight=weight)


def set_arm(p, side, spec, W, chest):
    spec = spec or {}
    sx = 1 if side == 'L' else -1
    if chest is None:
        chest = [row[:3] for row in W['WaistN'][:3]]
    up_d = spec.get('wup') or vec_mat(spec.get('up') or ARM0[side][0], chest)
    fore_d = spec.get('wfore') or vec_mat(spec.get('fore') or ARM0[side][1], chest)
    w = spec.get('weight', 1.0)
    if spec.get('reach') is not None and w > 1e-6:
        sh = pos(W, f'{side}ShoulderJ')
        tgt = spec['reach']
        d = [t - s for t, s in zip(tgt, sh)]
        up, lo = rig.UPPER_ARM, rig.FOREARM
        dist = math.sqrt(dot(d, d)) or 1e-6
        L = min(dist, (up + lo) * 0.999)
        u = [x / dist for x in d]
        pole = spec.get('pole') or (sx * 0.6, -0.4, -0.5)
        v = norm([a - dot(pole, u) * b for a, b in zip(pole, u)])
        ca = clamp((up ** 2 + L ** 2 - lo ** 2) / (2 * up * L), -1, 1)
        sa = math.sqrt(max(0.0, 1 - ca * ca))
        elbow = [up * (ca * a + sa * b) for a, b in zip(u, v)]
        fore = [L * a - e for a, e in zip(u, elbow)]
        p.aim(f'{side}ShoulderJ', slerp_dir(up_d, elbow, w))       # weight < 1: part way from the aimed arm
        p.aim(f'{side}ArmJ', slerp_dir(fore_d, fore, w))
    else:
        p.aim(f'{side}ShoulderJ', norm(up_d))
        p.aim(f'{side}ArmJ', norm(fore_d))
    if spec.get('hand') is not None:
        h, hu = spec['hand'], spec.get('hand_up')
        if spec.get('hand_local'):
            h = vec_mat(h, chest)
            hu = vec_mat(hu, chest) if hu is not None else None
        p.aim(f'{side}HandN', norm(h), up=norm(hu) if hu is not None else None)


def hand_blend(p, side, direction, up, w):
    """Turn a hand toward (direction, up) by weight w from where the forearm leaves it (w 0 is the rest hand exactly)."""
    if w <= 1e-6: return p
    W = world(p)
    fore = [row[:3] for row in W[f'{side}ArmJ'][:3]]
    d0, u0 = fore[0], fore[1]
    d = slerp_dir(d0, direction, w)
    u = slerp_dir(u0, up, w)
    p.aim(f'{side}HandN', d, up=u)
    return p


def local_dir(v):
    """A world direction at rest (base()'s chest) in the chest's frame: arm specs are easiest to think of in the world."""
    return mat_vec_t(norm(v), CHEST0)


def sample(n, fn, step=1):
    """Keys for an n-frame action: fn(frame) -> Pose on every `step` frames and on the last."""
    fs = list(range(0, n, step)) + [n]
    return [(f, fn(f)) for f in fs]


def pose_diff(a, b):
    """The largest difference between two poses' local transforms (angles the short way round)."""
    sa, sb = a.solve(), b.solve()
    d = 0.0
    for j in sb:
        ta, ra = sa[j]; tb, rb = sb[j]
        ra = anims.unwrap(rb, ra)
        d = max(d, max(abs(x - y) for x, y in zip(ta + ra, tb + rb)))
    return d


def check_rest(keys, first=None, last=None):
    """How far the first and last keys are from the poses they must meet (base() unless given): ~0 at every seam."""
    return [(keys[0][0], pose_diff(keys[0][1], first or _BASE)), (keys[-1][0], pose_diff(keys[-1][1], last or _BASE))]


# ---------------------------------------------------------------------------------------------------------------- scripts
def tex(frame, idx=0, both=True):
    """0x28: the eye textures (Mario's order: 0 open, 1 half, 2 closed, 3 squint, 4/5 looking aside); both eyes, or one
    (idx 0 his right eye, 1 his left)."""
    import struct
    w = (0x28 << 26) | ((1 if both else 0) << 25) | ((0 if both else idx) << 18) | ((1 if both else 0) << 11) | frame
    return struct.pack('>I', w)


def foot_ik(flags=3):
    """0x34: the engine's foot placement on slopes (both feet), as Wait1's and the cast's standing actions set it."""
    import struct
    return struct.pack('>I', (0x34 << 26) | flags)


# ---------------------------------------------------------------------------------------------------------------- Wait1
WAIT1 = 50
IDLE_FLEX = math.radians(44)      # the idles' planted heels stay down through the sway (base() rests at 33.7 degrees)


def wait1_pose(t, n=WAIT1, amp=1.0):
    """The breathing idle at frame t of an n-frame loop (two breaths): the body settles a little on each exhale (knees
    give, chest and shoulders drop, the head nods after them), sways once side to side over the planted feet, and the
    arms drift. Every term is 0 at t = 0 and t = n with matching slopes, so the loop closes and starts on base()."""
    b = dip(t, n, 2)                                  # 0 at rest, 1 at the bottom of each breath
    s = wave(t, n, 1)                                 # the sway, once a loop
    s_lag = wave(t, n, 1, 0.5)
    b_lag = 0.5 - 0.5 * math.cos(TAU * 2 * t / n - 0.7) - (0.5 - 0.5 * math.cos(-0.7))
    b_lag2 = 0.5 - 0.5 * math.cos(TAU * 2 * t / n - 1.2) - (0.5 - 0.5 * math.cos(-1.2))
    k = amp
    arms = {}
    for sd, sx in (('L', 1), ('R', -1)):
        up0, fore0 = ARM0[sd]
        # upper arms sink and swing a touch on the exhale; forearms follow a beat later
        up = norm(_add(up0, (sx * 0.015 * s_lag, -0.02 * b, -0.035 * b + 0.02 * sx * s), k))
        fore = norm(_add(fore0, (sx * 0.02 * s_lag, -0.03 * b_lag, -0.05 * b_lag + 0.025 * sx * s_lag), k))
        arms[sd] = arm(up=up, fore=fore)
    # the pelvis barely drops: the stance's rear leg is all but straight, and any real dip lifts its heel (base's heel
    # lift), so the breath rocks the weight a little forward (along the rear leg's reach) and the chest does the rest
    return body(bob=-0.1 * b * k, lean=0.09 * b * k, root=(0.21 * s * k, 0, 0.25 * b * k),
                hip=(0, 0.035 * s * k, -0.04 * s * k), waist=(0.025 * b_lag * k, -0.03 * s_lag * k, 0.04 * s * k),
                head=(0.085 * b_lag2 * k, 0.045 * s_lag * k, -0.035 * s_lag * k), arms=arms, flex=IDLE_FLEX)


@state('Wait1', WAIT1)
def wait1():
    return sample(WAIT1, wait1_pose)


# ---------------------------------------------------------------------------------------------------------------- Wait2
WAIT2 = 150


def wait2_pose(t):
    """The second idle (the engine plays it after about one Wait1 loop in three, in a match too, and on the respawn
    platform): the doll lifts his right hand, turns it over at the wrist to look at it (a knock of wood), flexes it, shakes
    it loose, glances round toward the camera and settles back. The breath runs underneath; starts and ends on base()."""
    tb = t % WAIT1
    b = dip(tb, WAIT1, 2)
    lift = spline(t, [(0, 0), (14, 0), (34, 1, 'hold'), (86, 1), (100, 0.3), (112, 0.0, 'hold'), (150, 0)])
    look = spline(t, [(0, 0), (16, 0), (36, 1, 'hold'), (84, 1), (98, 0.15), (108, 0), (150, 0)])
    roll = spline(t, [(0, 0), (38, 0), (45, 1.0), (50, 1.0, 'hold'), (56, -0.15), (64, 0.9), (70, 0.9, 'hold'),
                      (78, 0.0, 'hold'), (150, 0)])
    flex = spline(t, [(0, 0), (70, 0), (73, 1), (77, 0), (150, 0)])
    shake = spline(t, [(0, 0), (94, 0), (97, 1), (100, -1), (103, 0.7), (106, -0.4), (109, 0.15), (112, 0), (150, 0)])
    glance = spline(t, [(0, 0), (106, 0), (116, 1, 'hold'), (126, 1), (138, 0, 'hold'), (150, 0)])
    lean_in = spline(t, [(0, 0), (20, 0), (38, 1, 'hold'), (86, 1), (104, 0), (150, 0)])
    up0, fore0 = ARM0['R']
    up = norm(lerp(up0, local_dir((-0.4, -0.8, 0.45)), lift))
    fore = norm(lerp(fore0, local_dir((0.3, 0.5, 0.8)), lift))
    fore = norm(_add(fore, local_dir((0.0, 0.3, -0.15)), 0.3 * shake))
    lup, lfore = ARM0['L']
    larm = arm(up=norm(_add(lup, (0.0, -0.02 * b, -0.03 * b))), fore=norm(_add(lfore, (0.0, -0.03 * b, -0.04 * b))))
    p = body(bob=-0.1 * b * 0.8 - 0.05 * lean_in, lean=0.06 * b * 0.8 + 0.1 * lean_in, root=(0, 0, 0.2 * b * 0.8 + 0.2 * lean_in),
             hip=(0, -0.06 * lean_in - 0.05 * glance, 0), waist=(0, -0.1 * lean_in - 0.12 * glance, 0.03 * lean_in),
             head=(0.34 * look + 0.05 * b, -0.12 * look - 0.45 * glance, 0.1 * look - 0.04 * glance),
             arms={'R': arm(up=up, fore=fore), 'L': larm}, flex=IDLE_FLEX)
    # the hand turns over about the forearm (the back of it to his face) and flexes back at the wrist
    W = world(p)
    fa = [row[:3] for row in W['RArmJ'][:3]]
    along, u0 = fa[0], fa[1]
    hu = rodrigues(u0, along, -1.7 * roll)
    hd = norm(_add(along, hu, 0.45 * flex))
    return hand_blend(p, 'R', hd, hu, lift)


def wait2_script():
    """The template's (the foot placement and a blink) plus the doll's wrist clacking as it turns over."""
    from fcmd import Script
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sound'))
    import wiring
    s = Script()
    s.raw(foot_ik(3)); s.raw(tex(1))
    s.at(3); s.raw(tex(2))
    s.at(15); s.raw(tex(1))
    s.at(21); s.raw(tex(0))
    s.at(46); s.raw(wiring.sfx(wiring.ID['LEDGE'], 0x38))
    s.at(65); s.raw(wiring.sfx(wiring.ID['LEDGE'], 0x30))
    s.at(98); s.raw(wiring.cue(wiring.ID['TECH'], 0x28))
    return s


@state('Wait2', WAIT2, wait2_script)
def wait2():
    return sample(WAIT2, wait2_pose)


# ---------------------------------------------------------------------------------------------------------------- Appeal
APPEAL = 110
# the cap's brim at its front right corner, by the curls, just outside the production model's band (glTF cap_band: its
# lower edge 2.4 over HeadN, the head 5.1 across); in HeadN's frame. His arms are short: the head leans into the hand.
BRIM = (-2.55, 2.45, 1.55)


def appeal_pose(t):
    """The taunt, a marionette's curtain call: a small dip, the right hand rises to the brim of his cap and tips it (the
    head nods with it), sweeps out in a flourish and across his middle as he bows stiffly from the waist (the left arm
    back), holds the bow, then his strings are yanked: he snaps upright, overshoots, wobbles and settles. Eyes close for
    the bow. Feet planted; starts and ends on base()."""
    dipA = spline(t, [(0, 0), (5, 1), (12, 0, 'hold'), (APPEAL, 0)])
    rise = spline(t, [(0, 0), (5, 0), (20, 1, 'hold'), (APPEAL, 1)])
    attach = spline(t, [(0, 0), (15, 0), (21, 1, 'hold'), (33, 1, 'hold'), (39, 0), (APPEAL, 0)])
    tip = spline(t, [(0, 0), (22, 0), (29, 1, 'hold'), (34, 1), (42, 0.2), (52, 0), (APPEAL, 0)])
    bow = spline(t, [(0, 0), (36, 0), (54, 1, 'hold'), (68, 1.06), (72, 0.95), (76, -0.2), (81, 0.1), (86, -0.05),
                     (91, 0.02), (96, 0, 'hold'), (APPEAL, 0)])
    bowpos = clamp(bow, 0, 1.1)
    face = spline(t, [(0, 0), (6, 0), (20, 1, 'hold'), (36, 1), (50, 0.2), (78, 0.4), (92, 0.6, 'hold'), (APPEAL, 0)])
    out = spline(t, [(0, 0), (33, 0), (41, 1), (48, 0), (APPEAL, 0)])        # the flourish, between the tip and the bow
    belly = spline(t, [(0, 0), (40, 0), (52, 1, 'hold'), (70, 1), (76, 0.1), (84, 0, 'hold'), (APPEAL, 0)])
    back = spline(t, [(0, 0), (38, 0), (54, 1, 'hold'), (70, 1), (76, 0), (80, 0.1), (86, 0, 'hold'), (APPEAL, 0)])
    ret = spline(t, [(0, 0), (76, 0), (80, 1), (104, 0.0, 'hold'), (APPEAL, 0)]) * (t > 74)   # the arms fly out on the yank
    # the body
    lean = 0.42 * bow + 0.04 * dipA
    p0 = dict(bob=-0.07 * dipA - 0.12 * bowpos, lean=lean, root=(0, 0, -0.45 * bowpos + 0.06 * dipA),
              hip=(0.14 * bow, -0.1 * face, 0), waist=(0.02 * tip, -0.18 * face * (1 - bowpos), 0),
              head=(0.12 * attach + 0.28 * tip + 0.3 * bow, -0.3 * face, 0.24 * attach), flex=IDLE_FLEX)
    lup, lfore = ARM0['L']
    lup = norm(_add(lerp(lup, local_dir((0.35, -0.75, -0.55)), back), (0.15, 0.25, 0.0), ret))
    lfore = norm(_add(lerp(lfore, local_dir((0.2, -0.7, -0.7)), back), (0.2, 0.35, 0.1), ret))
    p = body(arms={'L': arm(up=lup, fore=lfore)}, **p0)
    W = world(p)
    chest = W['WaistN']
    # the right wrist: a path in the chest's frame (rest, the rise, the flourish, the belly), pulled onto the brim
    rest = to_local(pos(_BW, 'RHandN'), _BW['WaistN'])
    path = [(0, rest), (5, _add(rest, (0.1, -0.25, -0.2))), (12, _add(rest, (-0.9, 1.2, 0.6))), (18, (-2.0, 3.6, 1.6)),
            (33, (-1.4, 4.2, 2.2)), (41, (-3.0, 2.2, 3.0)), (52, (0.3, 0.6, 1.9)), (70, (0.3, 0.6, 1.9)),
            (76, (-2.2, 0.4, 0.9)), (84, _add(rest, (-0.3, 0.1, 0.3))), (APPEAL, rest)]
    wl = spline(t, [k if i not in (0, len(path) - 1) else k + ('hold',) for i, k in enumerate(path)])
    wrist = xf(wl, chest)
    brim = xf(BRIM, W['HeadN'])
    hand_len = rig.HAND * 0.9
    to_brim = norm([b_ - w for b_, w in zip(brim, wrist)])
    brim_wrist = tuple(b_ - hand_len * d for b_, d in zip(brim, to_brim))
    target = lerp(wrist, brim_wrist, attach)
    act = spline(t, [(0, 0), (6, 0.5), (12, 1, 'hold'), (86, 1, 'hold'), (104, 0, 'hold'), (APPEAL, 0)])
    set_arm(p, 'R', arm(reach=target, pole=(-0.8, -0.3, -0.4), weight=act), W, None)
    # the hand: fingers onto the brim (back of the hand outward), open palm-up in the flourish, flat on his middle
    W = world(p)
    hw = pos(W, 'RHandN')
    head_out = norm(vec_mat((-1, 0, 0.3), W['HeadN']))
    fing = norm([b_ - w for b_, w in zip(brim, hw)])
    hand_blend(p, 'R', fing, head_out, attach)
    if out > 1e-4 and attach < 1e-4:
        hand_blend(p, 'R', norm(vec_mat((-0.6, 0.1, 0.8), chest)), norm(vec_mat((0, -1, 0), chest)), out)
    if belly > 1e-4:
        hand_blend(p, 'R', norm(vec_mat((1, 0, 0.1), chest)), norm(vec_mat((0, 0, 1), chest)), belly)
    return p


def appeal_script():
    """His own (the template's was Mario's grow, a colour flash and his voice): the arm's swish on the flourish, a creak
    of wood as he bows, eyes closed through it, the joints clicking straight when he snaps up, a rattle as he settles."""
    from fcmd import Script
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sound'))
    import wiring
    s = Script()
    s.raw(foot_ik(3))
    s.at(15); s.hand('R', 'grip', 6)                                # the fingers close on the brim (the Gate 2 hands)
    s.at(23); s.raw(wiring.sfx(wiring.ID['LEDGE'], 0x40))           # fingers on the brim
    s.at(35); s.hand('R', 'open', 5)                                # open for the flourish, to the end (the cut to Wait
    s.at(38); s.raw(wiring.sfx(wiring.ID['CAPE1'], 0x58))           # the flourish      lets the fingers go)
    s.at(45); s.raw(wiring.sfx(wiring.ID['TEETER'], 0x60))          # the bow creaks
    s.at(50); s.raw(tex(1))
    s.at(53); s.raw(tex(2))
    s.at(72); s.raw(tex(1))
    s.at(74); s.raw(tex(0)); s.raw(wiring.sfx(wiring.ID['JUMP'], 0x70))   # yanked upright
    s.at(81); s.raw(wiring.sfx(wiring.ID['RATTLE'], 0x48))
    return s


@state('Appeal', APPEAL, appeal_script)
def appeal():
    return sample(APPEAL, appeal_pose)


# ---------------------------------------------------------------------------------------------------------------- Entry
@state('Entry', 10)
def entry():
    """The match start: the engine grows him out of the trophy stand over EntryStart (30 frames) playing this, freezes the
    last pose through EntryEnd (30 more; no animation) and cuts to Wait1. The cast (Mario, Fox, Samus, Ness, Falcon) holds
    Wait1's first frame the whole time, so does he: any other pose would pop at the cut to Wait."""
    return [(0, base()), (10, base())]


# ---------------------------------------------------------------------------------------------------------------- victory
# The results screen plays these from GmRstMGe.dat (datkit DemoBuild.cs writes it and the demo table's rows 0-9, from
# anims.json "demo"). There the fighter stands at facing 0, so his +Z is toward the camera: each pose ends square to it.
# The winner's pose is the button held as the screen opens (B Win1, Y Win2, X Win3; otherwise one at random); everyone
# else claps (Lose, a loop). A win pose holds its last frame, which the panel freezes into its picture.
DEMO = {}
DEMO_ROWS = {}


def demo(name, frames, script=None):
    def reg(fn):
        DEMO[name] = (frames, script, fn)
        return fn
    return reg


SQUARE = {'L': (1.35, rig.ANKLE_Y, 0.15), 'R': (-1.35, rig.ANKLE_Y, -0.15)}   # feet side by side, facing the camera
SQ = dict(hip=(0, -S['hip_yaw'], 0), head=(0, -S['head_yaw'], 0))         # the stance's turn toward the side camera undone


def square_feet(t, t0, t1):
    """From the stance to square (the rear foot first, then the lead), over [t0, t1]."""
    m = (t0 + t1) / 2.0
    out = {}
    for s, a, b in (('R', t0, m + 1), ('L', m - 1, t1)):
        u = clamp((t - a) / float(b - a))
        frm, to = FEET[s], SQUARE[s]
        at = lerp(frm, to, smooth(u))
        lift = 0.45 * math.sin(PI * u) if 0 < u < 1 else 0.0
        out[s] = dict(pos=(at[0], at[1] + lift, at[2]), yaw=lerp(TOE[s], 0.5 * TOE[s], smooth(u)), pitch=0.25 * lift if lift else None)
    return out


PI = math.pi


def squared(u, **kw):
    """body() turned square to the camera by u (0 the stance, 1 square): the hips and head's stance turn undone."""
    hip = kw.pop('hip', (0, 0, 0)); head = kw.pop('head', (0, 0, 0))
    return body(hip=_add(hip, (0, -S['hip_yaw'] * u, 0)), head=_add(head, (0, -S['head_yaw'] * u, 0)), **kw)


def demo_script(*cmds):
    """A demo row's script: (frame, bytes) pairs."""
    from fcmd import Script
    s = Script()
    for f, b in sorted(cmds, key=lambda c: c[0]):
        if f > s.frame: s.at(f)
        s.raw(b)
    return s


def _hand(side, pose, blend=0):
    """0x29: a hand's pose (rig.HAND_POSE: fist, open, point, grip), blended over `blend` frames; it holds until the
    action changes, when the engine lets the fingers go back to the animation's (straight)."""
    from fcmd import Script
    return bytes(Script().hand(side, pose, blend).data)


def _snd(name, vol=0x60):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sound'))
    import wiring
    return wiring.cue(wiring.ID[name], vol)


def win1_pose(t):
    """Win1: the doll twirls once on the spot (a hop, a full turn toward the camera), lands square to it, points his gun
    hand straight at it, the left fist on his hip, a 'bang' kick of the wrist, and a wink held to the end."""
    turn = -TAU * smooth(spline(t, [(0, 0), (9, 0), (27, 1.0), (30, 1.0)]))
    lift = clamp(spline(t, [(0, 0), (11, 0), (16, 0.7), (22, 0.7), (27, 0), (120, 0)]), 0, 2)
    sq = smooth(spline(t, [(0, 0), (16, 0), (27, 1), (120, 1)]))
    dn = spline(t, [(0, 0), (8, 0.35), (11, 0.4), (14, -0.2), (22, -0.1), (28, 0.45), (33, 0.15, 'hold'), (120, 0.1)])
    point = spline(t, [(0, 0), (34, 0), (46, 1, 'hold'), (120, 1)])
    bang = spline(t, [(0, 0), (52, 0), (54, 1), (60, 0, 'hold'), (120, 0)])
    breath = 0.5 - 0.5 * math.cos(TAU * t / 40) if t > 60 else 0.0
    feet = {}
    for s in 'LR':
        a = rot_y(FEET[s], turn)
        at = lerp(a, SQUARE[s], sq)
        feet[s] = dict(pos=(at[0], at[1] + lift, at[2]), yaw=lerp(TOE[s] + turn, 0.5 * TOE[s], sq),
                       pitch=0.3 if lift > 1e-3 else None)
    p = squared(sq, crouch=max(dn, 0) * 0.8, bob=max(-dn, 0) * 1.2 + (lift * 0.9), turn=turn * (1 - 0) if t < 28 else 0.0,
                lean=0.1 * max(dn, 0) - 0.05 * point, head=(0.1 * point - 0.08 * bang + 0.02 * breath, 0.0, 0.12 * point),
                waist=(0, 0.25 * point, 0), feet=feet, stance_turn=False)
    W = world(p)
    ch = W['WaistN']
    # the gun hand out to his right, not in front of his face (pass 5: the finger foreshortened into a fist over his
    # eye), the finger 45 degrees out from the camera so it reads (at the camera it foreshortened behind the knuckles)
    aim = xf((-3.3, 3.3, 3.0), ch)
    aim = (aim[0], aim[1] + 0.9 * bang, aim[2] - 0.3 * bang)
    set_arm(p, 'R', arm(reach=aim, pole=(-0.8, -0.4, -0.3), weight=point), W, None)
    if point > 1e-4:
        hand_blend(p, 'R', norm((-0.8, 0.2 + 0.5 * bang, 0.75)), (-0.75, 0.3, -0.8), point)   # thumb up, the back out
    hipfist = xf((1.95, 0.2, 0.2), ch)
    set_arm(p, 'L', arm(reach=hipfist, pole=(1.0, 0.1, -0.4), weight=point), W, None)
    return p


def win2_pose(t):
    """Win2: a curtain call. He squares up to the camera, lifts his hand to the brim of his cap, tips it and bows stiffly
    from the waist, left arm behind his back, then rises slowly and ends with the brim pulled low over one eye."""
    sq = smooth(spline(t, [(0, 0), (4, 0), (16, 1), (120, 1)]))
    feet = square_feet(t, 4, 16)
    attach = spline(t, [(0, 0), (22, 0), (32, 1, 'hold'), (42, 1, 'hold'), (48, 0), (92, 0), (102, 1, 'hold'), (120, 1)])
    tip = spline(t, [(0, 0), (34, 0), (40, 1, 'hold'), (44, 1), (52, 0.2), (60, 0), (98, 0), (104, 0.55, 'hold'), (120, 0.55)])
    bow = spline(t, [(0, 0), (46, 0), (62, 1, 'hold'), (78, 1.03), (96, 0, 'hold'), (120, 0)])
    belly = spline(t, [(0, 0), (48, 0), (60, 1, 'hold'), (80, 1), (92, 0), (120, 0)])
    behind = spline(t, [(0, 0), (40, 0), (58, 1, 'hold'), (120, 1)])
    p = squared(sq, bob=-0.08 * bow, lean=0.42 * bow, root=(0, 0, -0.4 * bow), hip=(0.14 * bow, 0, 0),
                head=(0.12 * attach + 0.28 * tip + 0.3 * bow, -0.1 * attach, 0.2 * attach), feet=feet, flex=IDLE_FLEX)
    W = world(p)
    ch = W['WaistN']
    rest = to_local(pos(_BW, 'RHandN'), _BW['WaistN'])
    path = [(0, rest), (20, rest), (26, (-2.0, 3.6, 1.6)), (42, (-1.4, 4.2, 2.2)), (50, (-2.6, 2.4, 2.8)),
            (60, (0.3, 0.6, 1.9)), (80, (0.3, 0.6, 1.9)), (92, (-2.0, 2.6, 1.6)), (120, (-1.4, 4.2, 2.2))]
    wrist = xf(spline(t, path), ch)
    brim = xf(BRIM, W['HeadN'])
    to_b = norm([b_ - w for b_, w in zip(brim, wrist)])
    target = lerp(wrist, tuple(b_ - rig.HAND * 0.9 * d for b_, d in zip(brim, to_b)), attach)
    act = spline(t, [(0, 0), (20, 0), (26, 1), (120, 1)])
    set_arm(p, 'R', arm(reach=target, pole=(-0.8, -0.3, -0.4), weight=act), W, None)
    set_arm(p, 'L', arm(reach=xf((0.7, 0.1, -1.6), ch), pole=(1.0, -0.2, 0.2), weight=behind), W, None)
    W = world(p)
    hw = pos(W, 'RHandN')
    hand_blend(p, 'R', norm([b_ - w for b_, w in zip(brim, hw)]), norm(vec_mat((-1, 0, 0.3), W['HeadN'])), attach)
    if belly > 1e-4 and attach < 1e-4:
        hand_blend(p, 'R', norm(vec_mat((1, 0, 0.1), ch)), norm(vec_mat((0, 0, 1), ch)), belly)
    return p


def win3_pose(t):
    """Win3: the Star Road. He looks up, sinks, springs up throwing both arms up into a V, lands square to the camera in a
    wide stance and holds the V, chin up."""
    sq = smooth(spline(t, [(0, 0), (14, 0), (30, 1), (120, 1)]))
    sink = spline(t, [(0, 0), (12, 0), (22, 1, 'hold'), (26, 0.6), (30, -1), (34, -1.4, 'hold'), (38, -0.6), (41, 0), (44, 0.55),
                      (50, 0.2), (58, 0.1, 'hold'), (120, 0.1)])
    up = smooth(spline(t, [(0, 0), (22, 0), (32, 1), (120, 1)]))
    lift = clamp(-sink - 0.4, 0, 2) * 1.6 if 28 <= t <= 40 else 0.0
    wide = {'L': (1.75, rig.ANKLE_Y, 0.2), 'R': (-1.75, rig.ANKLE_Y, -0.2)}
    feet = {}
    for s in 'LR':
        at = lerp(FEET[s], wide[s], sq)
        feet[s] = dict(pos=(at[0], at[1] + lift, at[2]), yaw=lerp(TOE[s], 1.3 * TOE[s], sq), pitch=0.45 if lift > 1e-3 else None)
    look = spline(t, [(0, 0), (6, 0), (14, 1, 'hold'), (20, 0.5), (30, 1), (120, 1)])
    p = squared(sq, crouch=max(sink, 0), bob=max(-sink, 0) * 1.3, lean=0.3 * max(sink, 0) - 0.08 * up,
                head=(-0.42 * look, 0, 0), feet=feet, flex=IDLE_FLEX)
    W = world(p)
    ch = W['WaistN']
    act = spline(t, [(0, 0), (14, 0), (22, 1), (120, 1)])
    for s, sx in (('R', -1), ('L', 1)):
        back = (sx * 1.9, 0.6, -1.4)
        v = (sx * 4.2, 5.7, 0.3)
        wl = lerp(back, v, up)
        set_arm(p, s, arm(reach=xf(wl, ch), pole=(sx * 1.0, -0.4, -0.2), weight=act), W, None)
    return p


def lose_pose(t):
    """Lose (a loop, 30): square to the camera, a little slumped, clapping the winner politely: two wooden claps a loop."""
    c = 0.5 + 0.5 * math.cos(TAU * 2 * t / 30)            # 1 apart, 0 hands together (frames 7.5 and 22.5)
    p = squared(1.0, bob=-0.1, lean=0.1, head=(0.18 + 0.03 * c, 0, 0), feet={s: dict(pos=SQUARE[s], yaw=0.5 * TOE[s]) for s in 'LR'},
                flex=IDLE_FLEX)
    W = world(p)
    ch = W['WaistN']
    for s, sx in (('R', -1), ('L', 1)):
        w = (sx * (0.5 + 1.45 * c), 2.0 + 0.25 * c, 2.2 - 0.2 * c)
        set_arm(p, s, arm(reach=xf(w, ch), pole=(sx * 1.0, -0.6, -0.3)), W, None)
        hand_blend(p, s, norm(vec_mat((-sx * 0.3, 0.6, 1.0), ch)), norm(vec_mat((sx * 1.0, 0.1, 0.0), ch)), 1.0)
    return p


def hold_last(fn, n):
    return lambda: [(0, fn(n)), (10, fn(n))]


# the hands (0x29): the finger gun's pointing hand and the fist on his hip (Win1), the pinch on the brim, the palm on his
# middle and the fist behind his back (Win2), two fists in the V (Win3); flat palms for the clap (the animation's own).
# Each Wait row sets its pose's hands and eyes again at its first frame, since both reset on every action change.
demo('Win1', 120, lambda: demo_script((0, tex(0)), (12, _snd('CAPE2', 0x60)), (28, _snd('LAND', 0x58)), (36, _hand('R', 'point', 8)),
                                      (36, _hand('L', 'fist', 8)), (40, _snd('CAPE1', 0x50)), (54, _snd('LEDGE', 0x48)),
                                      (56, tex(2, 0, both=False))))(lambda: sample(120, win1_pose))
demo('Win2', 120, lambda: demo_script((0, tex(0)), (21, _hand('R', 'grip', 7)), (34, _snd('LEDGE', 0x40)), (42, _hand('L', 'fist', 10)),
                                      (46, _hand('R', 'open', 6)), (48, _snd('TEETER', 0x5C)), (60, tex(2)), (82, tex(1)),
                                      (86, tex(0)), (94, _hand('R', 'grip', 7)), (104, tex(1))))(lambda: sample(120, win2_pose))
demo('Win3', 120, lambda: demo_script((0, tex(0)), (20, _hand('R', 'fist', 8)), (20, _hand('L', 'fist', 8)), (28, _snd('JUMP', 0x70)),
                                      (40, _snd('LAND', 0x64)), (44, _snd('CAPE2', 0x50))))(lambda: sample(120, win3_pose))
demo('Lose', 30, lambda: demo_script((0, tex(1))))(lambda: sample(30, lose_pose))
demo('Win1Wait', 10, lambda: demo_script((0, tex(2, 0, both=False)), (0, _hand('R', 'point')), (0, _hand('L', 'fist'))))(hold_last(win1_pose, 120))
demo('Win2Wait', 10, lambda: demo_script((0, tex(1)), (0, _hand('R', 'grip')), (0, _hand('L', 'fist'))))(hold_last(win2_pose, 120))
demo('Win3Wait', 10, lambda: demo_script((0, tex(0)), (0, _hand('R', 'fist')), (0, _hand('L', 'fist'))))(hold_last(win3_pose, 120))
KIND, LOOP = 0x22, 0x40000000
DEMO_ROWS.update({0: ('Win1', KIND), 1: ('Win1Wait', KIND | LOOP), 2: ('Win2', KIND), 3: ('Win2Wait', KIND | LOOP),
                  5: ('Win3', KIND), 6: ('Win3Wait', KIND | LOOP), 7: ('Win1', KIND), 8: ('Win1Wait', KIND | LOOP),
                  9: ('Lose', KIND | LOOP)})


def demo_json():
    """anims.json "demo" (datkit DemoBuild.cs): the poses solved, and the rows that play them, each with its script."""
    anims_out = {name: anims.solve_keys(n, fn()) for name, (n, sc, fn) in DEMO.items()}
    rows = {}
    for i, (name, flags) in DEMO_ROWS.items():
        sc = DEMO[name][1]
        rows[str(i)] = dict(anim=name, flags=flags, script=(sc().bytes() if sc else b'\0\0\0\0').hex())
    return dict(file='GmRstMGe.dat', root='ftDemoResultMotionFileGeno', anims=anims_out, rows=rows)


import states_items                              # noqa: E402,F401 the item actions (they build on this module's toolkit)
