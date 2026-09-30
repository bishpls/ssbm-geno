"""Geno's ground attacks, grab and throws: production animation (moves.py calls these for the keys of its moves).

The motion is authored as a Clip: a track per body parameter (the pelvis, the chest and the head as yaw, pitch and roll;
each wrist's target and its elbow's pole; each boot on the floor; ThrowN, where the grabbed opponent rides; TransN, the
root motion), keyed at the frames that matter and interpolated per channel on monotone cubic curves (Fritsch-Carlson: no
overshoot between keys, so every overshoot and settle is a key of its own, and equal neighbouring keys hold exactly). Each
frame is solved into a Pose by IK (two-bone arms reaching their wrist targets, two-bone legs planting the boots, the rear
heel rising on its ball past 35 degrees of shin lean as base() does) and keyed on every frame, so arcs survive the game's
linear keys. Frame 0 and the last frame are the idle's own Pose (anims.base(), Wait1 frame 0), or the crouch's or the
hold's where a move starts or ends there, so the cuts meet exactly.

Conventions are anims.py's: +Z is where he faces, +X his left, +Y up, world units. Yaw is about +Y, positive turning his
front toward his left (+X), so his right (gun) shoulder comes forward; the idle's hips and chest sit at -25 degrees (his
front toward the camera facing right). Pitch leans forward, roll lifts his left side.

Hit poses are exact: `Clip.reach` puts a point on the forearm (a hitbox on ArmJ, FA + tip down the bone) at a world point
on a frame, and `Clip.fist` flies the fist (HandN, translated down the forearm) to one, both resolved against that frame's
torso when the clip is baked, so a hitbox riding a bone stays where the design measured it.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig
import anims as A
from anims import Pose, STANCE as ST

UA, FA, HAND = rig.UPPER_ARM, rig.FOREARM, rig.HAND
THIGH, SHIN = A.THIGH, A.SHIN
DROP = ST['drop']
TAU = 2 * math.pi
D = math.radians


# ---------------------------------------------------------------------------------------------------------------- vectors
def add(*vs): return tuple(sum(c) for c in zip(*vs))
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def mul(a, k): return tuple(x * k for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))
def norm(a):
    l = length(a) or 1.0
    return tuple(x / l for x in a)
def lerp(a, b, t): return a + (b - a) * t
def vlerp(a, b, t): return tuple(lerp(x, y, t) for x, y in zip(a, b))
def roty(v, a):
    """v turned by a about +Y (+Z toward +X for positive a, as rig.rot_xyz(0, a, 0))"""
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c)


def frame(yaw, pitch=0.0, roll=0.0):
    """A segment's across (+X, his left) and up (+Y) axes: yawed, rolled (left side up for +roll), then pitched forward
    (locomotion.frame's convention, which base() matches: WaistN's local (0.12, 0, 0) under HipN's yaw)."""
    across = (math.cos(yaw), 0.0, -math.sin(yaw))
    up = (0.0, 1.0, 0.0)
    if roll:
        across, up = add(mul(across, math.cos(roll)), mul(up, math.sin(roll))), sub(mul(up, math.cos(roll)), mul(across, math.sin(roll)))
    if pitch:
        fwd = cross(across, up)
        up = add(mul(up, math.cos(pitch)), mul(fwd, math.sin(pitch)))
    return across, up


def unframe(across, up):
    """frame()'s inverse: (yaw, pitch, roll) of a segment's across and up axes"""
    roll = math.asin(max(-1.0, min(1.0, across[1])))
    yaw = math.atan2(-across[2], across[0])
    a0 = (math.cos(yaw), 0.0, -math.sin(yaw))
    up_r = sub(mul((0.0, 1.0, 0.0), math.cos(roll)), mul(a0, math.sin(roll)))
    fwd = cross(across, up_r)
    pitch = math.atan2(dot(up, fwd), dot(up, up_r))
    return yaw, pitch, roll


# ---------------------------------------------------------------------------------------------------------------- IK
def two_bone(root, target, l1, l2, pole):
    """Directions of the two bones from root that end at target (short of it if out of reach), bending toward pole."""
    d = sub(target, root)
    dist = length(d)
    u = norm(d)
    if dist >= l1 + l2 - 1e-7:                                  # straight (and short of the target if it's further)
        return u, u, dist <= l1 + l2 + 1e-6
    L = max(dist, abs(l1 - l2) + 1e-4)
    ca = (l1 * l1 + L * L - l2 * l2) / (2 * l1 * L)
    sa = math.sqrt(max(0.0, 1 - ca * ca))
    v = sub(pole, mul(u, dot(pole, u)))
    if length(v) < 1e-6:
        v = cross(u, (1.0, 0.0, 0.0)) if abs(u[0]) < 0.9 else cross(u, (0.0, 1.0, 0.0))
    v = norm(v)
    mid = add(mul(u, l1 * ca), mul(v, l1 * sa))
    return norm(mid), norm(sub(mul(u, L), mid)), True


ANKLE_FLEX, HEEL_MAX, BALL, SOLE = A.ANKLE_FLEX, A.HEEL_MAX, A.BALL, rig.ANKLE_Y


def heel_move(th):
    """(forward, up) the ankle moves when the heel rises th about the ball (anims.heel_lift's geometry)"""
    h = SOLE
    return (-BALL * math.cos(th) + h * math.sin(th) + BALL, BALL * math.sin(th) + h * math.cos(th) - h)


# ---------------------------------------------------------------------------------------------------------------- parameters
# A pose is a dict of these. Angles in radians; points in the body frame (TransN's: root motion carries the whole body).
#   pel            YRotN's translation: the pelvis's offset from the idle's (base(): crouch lowers it)
#   pyaw ppitch proll    the pelvis (HipN) frame        cyaw cpitch croll   the chest (WaistN) frame
#   hyaw hpitch hroll    the head: yaw in the world (it holds its gaze as the chest turns), pitch (+ chin down, the neck
#                  taking back 70% of the chest's lean) and roll local to the neck
#   R L            each wrist's target; Rpole Lpole the elbow's pole; Rwrist Lwrist HandN's local rotation (twist, bends);
#                  Rext Lext HandN's travel past the wrist, down the forearm (the rocket fist's launch)
#   LF RF          each boot's flat-footed ankle (x, height above its flat stance, z); Ltoe Rtoe its yaw; Lheel Rheel a heel
#                  lift (radians about the ball) added to the automatic one; Lkpole Rkpole the knee's pole (0: over the toes)
#   throw throwry  ThrowN in the world (the held opponent) and its yaw     trans  TransN (root motion)
VEC = {'pel', 'R', 'L', 'Rpole', 'Lpole', 'Rwrist', 'Lwrist', 'LF', 'RF', 'Lkpole', 'Rkpole', 'throw', 'trans', 'Rhand', 'Lhand'}
#   Rgrow Lgrow    the fist's scale (HandN, anims.apply_grow): the cast grow a limb on its hit frames to read at game
#                  distance (research/limb_scale.md); Clip.fist and Clip.launch pull HandN in by the growth, so a hitbox
#                  on HandN (offset `off` down the bone) stays where the design put it and the fist grows around it
#   Rtips Ltips    the fingertips' scale (the Nb joints): below 1 they tuck into the fist (Mario's forward smash, ~0.5)
#   Rarm Larm      the whole arm's scale (ShoulderJ): the dash attack's lead shoulder
#   Rhand Lhand    the fingers as weights of rig.HAND_POSES (fist, open, point, grip) and rig.RELAXED_HAND (the idle's loose
#                  curl, which anims.base() sets); all 0 is the bind pose (straight fingers: the run and the crouch). A clip
#                  living on relaxed poses fills a 4-weight key's remainder with the relaxed curl (Clip.key).
#                  Keyed in the animation rather than set by script part poses (Script.hand): the same shapes, but they
#                  blend on the move's own curves and return to the idle's bind pose by the last frame, where a part pose
#                  holds until the action changes and then snaps back
FIST, OPEN, POINT, GRIP, REST = (1.0, 0, 0, 0), (0, 1.0, 0, 0), (0, 0, 1.0, 0), (0, 0, 0, 1.0), (0.0, 0, 0, 0)
RELAXED = (0.0, 0, 0, 0, 1.0)
REACH = (0.0, 0.75, 0, 0.25)          # open and reaching, the fingers a little cupped (the grabs' flying hands)
HANDS = list(rig.HAND_POSES) + [rig.RELAXED_HAND]          # the weights' poses, left-hand form


def relaxed_in(p, side):
    """Does a Pose carry the relaxed curl on this hand (anims.base() keys it)?"""
    ref = rig.RELAXED_HAND if side == 'L' else rig.mirror_hand(rig.RELAXED_HAND)
    return all(max(abs(a - b) for a, b in zip(p.local.get(j, (9, 9, 9)), r)) < 1e-6 for j, r in ref.items())


def hand5(w, fill=0.0):
    """A hand weight as 5 (the relaxed curl last); a 4-weight one takes fill x its remainder as the relaxed curl."""
    w = tuple(w)
    return w if len(w) == 5 else w + (fill * max(0.0, 1.0 - sum(w)),)
OPTIONAL = {'throw', 'throwry', 'trans'}
ANGLES = {'pyaw', 'cyaw', 'hyaw', 'Ltoe', 'Rtoe', 'throwry'}      # tracks unwrapped between keys (turns and spins)          # untouched (the rest pose's) unless a clip keys them


def params_from_pose(p, heel_auto=True):
    """A solved Pose's parameters (so a clip can start or end on any pose and meet it exactly)."""
    sol = p.solve()
    W = rig.world_mats(pose={k: {'t': v[0], 'r': v[1]} for k, v in sol.items()})
    pos = lambda j: tuple(W[j][3][:3])
    row = lambda j, i: tuple(W[j][i][:3])
    tr = sol['TransN'][0]
    rel = lambda v: sub(v, tr)
    q = {}
    assert max(abs(x) for x in sol['YRotN'][1]) < 1e-9, 'a turned YRotN is not a pose parameter'
    q['pel'] = sub(rel(pos('HipN')), (0.0, rig.LEG_TOP - DROP, 0.0))
    if 'TransN' in p.trans: q['trans'] = tuple(p.trans['TransN'])      # the pelvis (base()'s stance=0 poses drop no hips)
    q['pyaw'], q['ppitch'], q['proll'] = unframe(row('HipN', 0), row('HipN', 1))
    q['cyaw'], q['cpitch'], q['croll'] = unframe(row('WaistN', 0), row('WaistN', 1))
    hr = sol['HeadN'][1]
    q['hpitch'] = hr[0] + 0.7 * (q['cpitch'] - 0.12)
    q['hyaw'] = hr[1] + q['cyaw']
    q['hroll'] = hr[2]
    for s in 'LR':
        sh, el, wr = pos(f'{s}ShoulderJ'), pos(f'{s}ArmJ'), pos(f'{s}HandN')
        q[s] = rel(wr)
        u = norm(sub(wr, sh))
        v = sub(sub(el, sh), mul(u, dot(sub(el, sh), u)))
        q[s + 'pole'] = norm(v) if length(v) > 1e-5 else norm(row(f'{s}ArmJ', 1))
        q[s + 'wrist'] = tuple(sol[f'{s}HandN'][1])
        q[s + 'ext'] = sol[f'{s}HandN'][0][0] - FA
        q[s + 'grow'], q[s + 'tips'], q[s + 'arm'] = A.grow_params(p, s)
        q[s + 'hand'] = RELAXED if relaxed_in(p, s) else (0.0, 0, 0, 0, 0)
        # the boot: its forward and pitch from FootJ (local X forward, local Y the sole's down), the flat ankle behind it
        ank = rel(pos(f'{s}FootJ'))
        fx, fy = row(f'{s}FootJ', 0), row(f'{s}FootJ', 1)
        th = math.atan2(-fx[1], math.hypot(fx[0], fx[2]))            # heel lift: the toe pitched down
        toe = math.atan2(fx[0], fx[2])
        f0 = (math.sin(toe), 0.0, math.cos(toe))
        du, dv = heel_move(th)
        flat = (ank[0] - f0[0] * du, ank[1] - dv, ank[2] - f0[2] * du)
        q[s + 'F'] = (flat[0], flat[1] - SOLE, flat[2])
        q[s + 'toe'] = toe
        q[s + 'heel'] = 0.0 if heel_auto else th
        hip, knee = pos(f'{s}LegJ'), pos(f'{s}KneeJ')
        u = norm(sub(pos(f'{s}FootJ'), hip))
        v = sub(sub(knee, hip), mul(u, dot(sub(knee, hip), u)))
        vf = sub(f0, mul(u, dot(f0, u)))
        # knees over the toes (base()'s pole, the foot's forward) is 0; any other knee keeps its own pole
        q[s + 'kpole'] = (0.0, 0.0, 0.0) if length(v) < 1e-5 or length(sub(norm(v), norm(vf))) < 1e-6 else norm(v)
    if heel_auto:                                   # the drawn ankle is the last pass's: correct the flat ankles until
        for _ in range(6):                          # assembling them reproduces it
            W2 = world(assemble(q, True))
            for s in 'LR':
                err = sub(rel(pos(f'{s}FootJ')), sub(tuple(W2[f'{s}FootJ'][3][:3]), q.get('trans', (0.0, 0.0, 0.0))))
                q[s + 'F'] = add(q[s + 'F'], err)
    if 'ThrowN' in p.trans:
        q['throw'] = add((0.0, rig.HIP_Y, 0.0), sol['YRotN'][0], p.trans['ThrowN'])
        q['throwry'] = p.local.get('ThrowN', (0, 0, 0))[1]
    return q


def assemble(q, heel_auto=True):
    """A parameter dict -> a Pose: the torso set, then the legs planted and the arms reaching by IK."""
    p = Pose()
    tr = q.get('trans', (0.0, 0.0, 0.0))
    if 'trans' in q: p.move('TransN', tr)
    pel = q['pel']
    p.move('YRotN', pel)
    p.move('HipN', (0.0, rig.LEG_TOP - rig.HIP_Y - DROP, 0.0))
    pa, pu = frame(q['pyaw'], q['ppitch'], q['proll'])
    p.aim('HipN', pa, pu)
    ca, cu = frame(q['cyaw'], q['cpitch'], q['croll'])
    p.aim('WaistN', ca, cu)
    p.rot('HeadN', (q['hpitch'] - 0.7 * (q['cpitch'] - 0.12), q['hyaw'] - q['cyaw'], q['hroll']))
    if 'throw' in q:
        p.move('ThrowN', sub(sub(q['throw'], (0.0, rig.HIP_Y, 0.0)), pel))
        p.rot('ThrowN', (0.0, q.get('throwry', 0.0), 0.0))
    # legs (body frame, TransN's origin): the hip sockets from the pelvis frame, as base() places them
    pelvis = (pel[0], rig.LEG_TOP - DROP + pel[1], pel[2])
    for s, sx in (('L', 1), ('R', -1)):
        hip = add(pelvis, mul(pa, sx * rig.HIP_X))
        x, lift, z = q[s + 'F']
        toe = q[s + 'toe']
        f = (math.sin(toe), 0.0, math.cos(toe))
        planted = (x, SOLE + lift, z)
        kp = q[s + 'kpole']
        pole = f if length(kp) < 1e-6 else kp
        heel, ankle = q[s + 'heel'], planted
        du, dv = heel_move(heel)
        ankle = (planted[0] + f[0] * du, planted[1] + dv, planted[2] + f[2] * du)
        for _ in range(4):                                   # as base(): the heel lift moves the ankle, which eases the lean
            th, sh = A.leg_ik(hip, ankle, pole)
            auto = 0.0
            if heel_auto:
                d = norm(mul(sh, -1.0))
                lean = math.atan2(dot(d, f), d[1])
                auto = min(HEEL_MAX, max(0.0, lean - ANKLE_FLEX))
            heel = auto + q[s + 'heel']
            du, dv = heel_move(heel)
            ankle = (planted[0] + f[0] * du, planted[1] + dv, planted[2] + f[2] * du)
        p.aim(f'{s}LegJ', th)
        p.aim(f'{s}KneeJ', sh)
        c, sn = math.cos(heel), math.sin(heel)
        p.aim(f'{s}FootJ', (f[0] * c, -sn, f[2] * c), up=(-f[0] * sn, -c, -f[2] * sn))
    # arms: the shoulders from the torso just set, then two-bone IK to the wrist targets
    W = rig.world_mats(pose={k: {'t': v[0], 'r': v[1]} for k, v in p.solve().items()})
    for s in 'LR':
        sh = sub(tuple(W[f'{s}ShoulderJ'][3][:3]), tr)
        up_d, fo_d, _ok = two_bone(sh, q[s], UA, FA, q[s + 'pole'])
        p.aim(f'{s}ShoulderJ', up_d)
        p.aim(f'{s}ArmJ', fo_d)
        wr = q[s + 'wrist']
        if max(abs(x) for x in wr) > 1e-9: p.rot(f'{s}HandN', tuple(wr))
        w = hand5(q.get(s + 'hand', REST))
        if max(abs(x) for x in w) > 1e-6:
            for j, r in fingers(s, w).items():
                p.rot(j, r)
        if abs(q[s + 'ext']) > 1e-9: p.move(f'{s}HandN', (FA + q[s + 'ext'], 0.0, 0.0))
        A.apply_grow(p, s, q.get(s + 'grow', 1.0), q.get(s + 'tips', 1.0), q.get(s + 'arm', 1.0))
    return p


def fingers(side, w):
    """finger joint -> local rotation for pose weights w: the poses (rig.HAND_POSES, rig.RELAXED_HAND; the right hand
    mirrored, as rig.part_poses_export does) blended with the bind pose by the weights' remainder (the thumbs' bind
    rotation isn't zero)"""
    w = hand5(w)
    rest = {j[0]: j[3] for j in rig.JOINTS}
    joints = set()
    for k, wk in enumerate(w):
        if abs(wk) > 1e-9: joints |= set(HANDS[k])
    out = {}
    for jl in joints:
        jn = 'R' + jl[1:] if side == 'R' else jl
        acc = [x * (1.0 - sum(w)) for x in rest[jn]]
        for k, wk in enumerate(w):
            r = HANDS[k].get(jl, rest[jl])
            if side == 'R': r = (-r[0], -r[1], r[2])
            for i in range(3): acc[i] += wk * r[i]
        out[jn] = tuple(acc)
    return out


def world(p):
    """joint name -> world 4x4 of a Pose"""
    return rig.world_mats(pose={k: {'t': v[0], 'r': v[1]} for k, v in p.solve().items()})


def shoulder(q, side, heel_auto=True):
    """a side's shoulder in the body frame for a parameter dict (the torso only matters)"""
    W = world(assemble(q, heel_auto))
    return sub(tuple(W[f'{side}ShoulderJ'][3][:3]), q.get('trans', (0.0, 0.0, 0.0)))


WAIT = params_from_pose(A.base())


def wait():
    return dict(WAIT)


# ---------------------------------------------------------------------------------------------------------------- curves
def pchip(xs, ys, flat_ends=True):
    """Monotone cubic interpolation (Fritsch-Carlson): no overshoot between keys, equal neighbours hold exactly. The ends
    ease (zero slope) when flat_ends: the moves leave and reach the idle at rest."""
    n = len(xs)
    if n == 1: return lambda x: ys[0]
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    if not flat_ends:
        m[0], m[-1] = d[0], d[-1]

    def f(x):
        if x <= xs[0]: return ys[0]
        if x >= xs[-1]: return ys[-1]
        i = 0
        while xs[i + 1] < x: i += 1
        t = (x - xs[i]) / h[i]
        t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * m[i] * h[i] + (-2 * t3 + 3 * t2) * ys[i + 1]
                + (t3 - t2) * m[i + 1] * h[i])
    return f


class Clip:
    """Per-parameter key tracks over frames 0..n, starting and ending on given poses (default: Wait1 frame 0)."""

    def __init__(self, n, start=None, end=None, heel_auto=True):
        self.n = n
        self.heel_auto = heel_auto
        # start and end: a Pose (its parameters extracted) or a parameter dict (assembled; the fingers' weights kept)
        start, end = start or A.base(), end or A.base()
        self.start_pose = assemble(start, heel_auto) if isinstance(start, dict) else start
        self.end_pose = assemble(end, heel_auto) if isinstance(end, dict) else end
        self.q0 = dict(start) if isinstance(start, dict) else params_from_pose(start, heel_auto)
        self.q1 = dict(end) if isinstance(end, dict) else params_from_pose(end, heel_auto)
        for q in (self.q0, self.q1):
            for k in ('Rhand', 'Lhand'):
                if k in q: q[k] = hand5(q[k])
        # a clip that starts or ends on the idle (relaxed fingers) fills its 4-weight hand keys' remainder with the curl
        self.relax_fill = 1.0 if any(q.get(k, (0,) * 5)[4] > 0.5 for q in (self.q0, self.q1) for k in ('Rhand', 'Lhand')) else 0.0
        self.tracks = {}                 # param -> {frame: value}
        self.reaches = []                # (frame, side, point, tip, pole) resolved at bake
        self.fists = []                  # (frame, side, point, off, pole)
        self.free_ends = set()           # tracks whose ends keep their slope (root motion carries its speed through a cut)
        self.shots = []                  # (frame, side, point, fore, upper, tip, fit)
        self.launches = []               # (frame, side, point, ext, off, pole)

    def key(self, f, **kw):
        for k, v in kw.items():
            if k not in self.q0 and k not in OPTIONAL: raise KeyError(k)
            if k in ('Rhand', 'Lhand'): v = hand5(v, self.relax_fill)
            self.tracks.setdefault(k, {})[f] = tuple(v) if isinstance(v, (list, tuple)) else v
        return self

    def hold(self, f0, f1, **kw):
        self.key(f0, **kw)
        return self.key(f1, **kw)

    def reach(self, f, side, point, tip=0.0, pole=None):
        """On frame f the forearm's point FA + tip from the elbow (a hitbox on ArmJ at (FA + tip, 0, 0)) is at point."""
        self.reaches.append((f, side, tuple(point), tip, pole))
        return self

    def fist(self, f, side, point, off=0.0, pole=None):
        """On frame f the fist (HandN's point off down the bone: a hitbox on HandN at (off, 0, 0)) is at point, the arm
        straight toward it and the fist launched down the forearm (Rext) as far as it takes."""
        self.fists.append((f, side, tuple(point), off, pole))
        return self

    def shoot(self, f, side, point, fore, upper=None, tip=0.0, fit=(1.0, 1.0, 1.0)):
        """On frame f the forearm lies along fore with its point FA + tip from the elbow at point, the upper arm along upper
        (default fore: a straight arm, aimed); the pelvis is shifted (by fit's share per axis) to put the shoulder there.
        A fore of (None, y, z) picks its sideways slant so the shoulder needn't move sideways (the arm angles out or in)."""
        self.shots.append((f, side, tuple(point), fore, upper, tip, fit))
        return self

    def launch(self, f, side, point, upper, off=0.0):
        """On frame f the fist (HandN's point off down the bone) is at point, fired off the end of the forearm: the upper
        arm lies along `upper` (world), the forearm aims from the elbow at the point, and the fist flies the rest of the
        way (ext, as far as it takes; a rocket fist's short throw, the arm kicked back by it)."""
        self.launches.append((f, side, tuple(point), norm(upper), off))
        return self

    def curves(self, flat_ends=True):
        out = {}
        for k in set(self.q0) | set(self.tracks):
            ks = dict(self.tracks.get(k, {}))
            if k in self.q0: ks.setdefault(0, self.q0[k])
            if k in self.q1: ks.setdefault(self.n, self.q1[k])
            fr = sorted(ks)
            if k in ANGLES:                          # unwrap: each key the nearest turn to the one before
                for a, b in zip(fr, fr[1:]):
                    ks[b] = ks[b] + TAU * round((ks[a] - ks[b]) / TAU)
            v0 = ks[fr[0]]
            fe = flat_ends and k not in self.free_ends
            if isinstance(v0, tuple):
                out[k] = [pchip(fr, [ks[f][i] for f in fr], fe) for i in range(len(v0))]
            else:
                out[k] = pchip(fr, [ks[f] for f in fr], fe)
        return out

    def at(self, f, curves=None):
        cv = curves or self.curves()
        q = {k: (tuple(c(f) for c in c_) if isinstance(c_, list) else c_(f)) for k, c_ in cv.items()}
        for k in ('Rpole', 'Lpole'):
            q[k] = norm(q[k])
        return q

    def resolve(self):
        """Turn the reach and fist constraints into wrist (and ext) keys against each frame's torso."""
        cv = self.curves()
        self.fitted = {}
        for f, side, point, fore, upper, tip, fit in self.shots:
            q = self.at(f, cv)
            sh = shoulder(q, side, self.heel_auto)
            if fore[0] is None:
                fx = (point[0] - sh[0]) / (UA + FA + tip)
                k = math.sqrt(max(0.0, 1 - fx * fx)) / math.hypot(fore[1], fore[2])
                fore = (fx, fore[1] * k, fore[2] * k)
            fore = norm(fore)
            upper = norm(upper) if upper else fore
            elbow = sub(point, mul(fore, FA + tip))
            want = sub(elbow, mul(upper, UA))
            dl = tuple(d * k for d, k in zip(sub(want, sh), fit))
            self.fitted[f] = dl
            if max(abs(x) for x in dl) > 1.2: print(f'poses_ground: frame {f} {side} shot moves the pelvis {tuple(round(x, 2) for x in dl)}')
            self.key(f, pel=add(q['pel'], dl))
            wrist = add(elbow, mul(fore, FA))
            if 1 - dot(fore, upper) < 1e-6:
                pole = q[side + 'pole']
            else:
                pole = norm(sub(upper, fore))
            self.key(f, **{side: wrist, side + 'pole': pole, side + 'ext': 0.0})
        if self.shots:
            cv = self.curves()
        for f, side, point, tip, pole in self.reaches:
            q = self.at(f, cv)
            if pole is not None: q[side + 'pole'] = norm(pole); self.key(f, **{side + 'pole': norm(pole)})
            sh = shoulder(q, side, self.heel_auto)
            u, v, ok = two_bone(sh, point, UA, FA + tip, q[side + 'pole'])
            if not ok: print(f'poses_ground: frame {f} {side} reach short by {length(sub(point, sh)) - UA - FA - tip:.2f}')
            elbow = add(sh, mul(u, UA))
            self.key(f, **{side: add(elbow, mul(v, FA)), side + 'ext': 0.0})
        self.launched = {}
        for f, side, point, upper, off in self.launches:
            q = self.at(f, cv)
            off *= A.grown(q, side)
            sh = shoulder(q, side, self.heel_auto)
            elbow = add(sh, mul(upper, UA))
            v = norm(sub(point, elbow))
            ext = length(sub(point, elbow)) - FA - off
            if ext < 0: print(f'poses_ground: frame {f} {side} launch short: the fist sits {-ext:.2f} inside the forearm')
            wrist = add(elbow, mul(v, FA))
            w = sub(wrist, sh)
            e = sub(elbow, sh)
            pole = norm(sub(e, mul(norm(w), dot(e, norm(w)))))    # picks this elbow on the IK's circle
            self.launched[(f, side)] = ext
            self.key(f, **{side: wrist, side + 'ext': max(0.0, ext), side + 'pole': pole})
        for f, side, point, off, pole in self.fists:
            q = self.at(f, cv)
            off *= A.grown(q, side)     # a grown fist carries its hitbox offset out with it: pull HandN in to keep the box
            if pole is not None: self.key(f, **{side + 'pole': norm(pole)})
            sh = shoulder(q, side, self.heel_auto)
            d = sub(point, sh)
            dist = length(d)
            u = norm(d)
            ext = dist - (UA + FA) - off
            if ext >= 0:
                wrist = add(sh, mul(u, UA + FA))
            else:
                pl = norm(pole) if pole is not None else q[side + 'pole']
                a, b, _ = two_bone(sh, point, UA, FA + off, pl)
                wrist = add(add(sh, mul(a, UA)), mul(b, FA))
                ext = 0.0
            self.key(f, **{side: wrist, side + 'ext': ext})
        self.reaches, self.fists, self.shots, self.launches = [], [], [], []

    def keys(self):
        """[(frame, Pose)] for every frame, the first and last the start and end poses themselves."""
        self.resolve()
        cv = self.curves()
        out = []
        for f in range(self.n + 1):
            if f == 0: out.append((0, self.start_pose)); continue
            if f == self.n: out.append((f, self.end_pose)); continue
            out.append((f, assemble(self.at(f, cv), self.heel_auto)))
        return out

    def param(self, f):
        """the parameters on frame f (after resolving), for building on a frame's pose"""
        self.resolve()
        return self.at(f)


# ================================================================================================================ the moves
# Hit points: where the blockout put each bone-carried hitbox on its active frames (the contract: within ~0.5), as
# (x, y, z) in the body frame. The TopN bursts don't move with the body, so only these constrain the poses.
HIT = dict(
    jab1=(-2.573, 9.393, 5.098), jab2=(2.14, 9.393, 6.716), jab3R=(-2.445, 9.155, 5.856), jab3L=(1.887, 9.155, 7.475),
    ftiltHi=(-2.326, 10.828, 4.556), ftiltS=(-2.363, 9.07, 4.929), ftiltLw=(-2.326, 7.313, 4.556),
    dtilt=(-2.291, 5.043, 5.491), dsmashF=(-2.698, 5.405, 5.574), dsmashB=(2.698, 5.405, -2.402),
    grabR=(-3.075, 8.007, 7.904), grabL=(2.27, 8.007, 9.523), dgrabR=(-2.532, 8.55, 2.785), dgrabL=(1.727, 8.55, 4.403))
# The grabs' reach: the grab boxes' far edge from his position (the table's reach: the far fist's point plus its 4.0
# radius). Michael, 2026-09-30: "I'm fine extending their range to make them visually read better as rocket fists ...
# Keep the range under all of the grapple grabs, and under Marth's but on the long end of the cast". The fists fly out
# to it (their flight longer, the timing the same) and the boxes ride them.
GRAB_REACH = {False: 16.0, True: 18.5}            # the standing grab, the dash grab (13.53, 16.37 until 2026-09-30)
_GRAB_BASE = {False: 13.53, True: 16.37}
for _dash, _names in ((False, ('grabR', 'grabL')), (True, ('dgrabR', 'dgrabL'))):
    for _n in _names:
        HIT[_n] = (HIT[_n][0], HIT[_n][1], round(HIT[_n][2] + GRAB_REACH[_dash] - _GRAB_BASE[_dash], 3))
GUN_TIP = 0.6                   # the gun-arm hitboxes sit FA + 0.6 down ArmJ


def side_sign(side): return 1 if side == 'L' else -1


def jab(side):
    """Attack11 (right, the gun hand) and Attack12 (left): a finger tap. One frame of load (the hand draws back, the hips
    dip, the chest winds away), a one-frame strike with the chest turning hard into it (the right hand turns his back
    toward the camera facing right, the left his front) and the arm straight down the line, the finger held out through
    the pop (3-4) with a flick of the wrist as it fires, a two-frame retract, and a settle into the idle by frame 18. By
    the jab window (frame 6) he is nearly back, so the next jab starts from close to its own first frame."""
    n = 18
    c = Clip(n)
    sx = side_sign(side)
    other = 'R' if side == 'L' else 'L'
    hit = HIT['jab1' if side == 'R' else 'jab2']
    turn = D(17) if side == 'R' else D(-68)            # the chest's yaw at the strike (idle -25)
    wind = D(-40) if side == 'R' else D(-12)           # ... and wound away from it on the load
    hipt = D(-14) if side == 'R' else D(-40)
    fore = (None, -0.02, 1.0)
    c.key(1, pel=(0.0, -0.75, -0.15), pyaw=D(-25) + (D(-4) if side == 'R' else D(3)), cyaw=wind, cpitch=0.16, hyaw=D(-8),
          hpitch=0.05, **{side: (sx * 1.9, 8.3, -0.2 if side == 'R' else 1.2), side + 'pole': (sx * 0.9, -0.3, -0.4),
                          other: (-sx * 1.7, 8.7, 2.1 if side == 'R' else 0.7), other + 'pole': (-sx * 0.6, -0.6, -0.5)})
    for f, k in ((2, 0.0), (3, 0.5), (4, 1.0)):
        c.key(f, pel=(0.0, -0.08, -0.05) if side == 'R' else (0.0, -0.08, 0.9), pyaw=hipt, cyaw=turn + sx * -D(2) * k,
              cpitch=0.18, hyaw=D(-6),
              hpitch=0.02, **{other: (-sx * 1.45, 8.9, 1.4), other + 'pole': (-sx * 0.5, -0.7, -0.5)})
        c.shoot(f, side, hit, fore, tip=GUN_TIP, fit=(0.0, 1.0, 1.0))
    c.key(3, **{side + 'wrist': (0.0, 0.0, 0.0)})
    c.key(1, **{side + 'hand': FIST, other + 'hand': (0.6, 0, 0, 0)})
    c.hold(2, 6, **{side + 'hand': POINT})
    c.key(6, **{other + 'hand': (0.5, 0, 0, 0)})
    c.key(12, **{side + 'hand': (0, 0, 0.25, 0), other + 'hand': REST})
    c.key(4, **{side + 'wrist': (0.0, 0.0, -sx * 0.35)})         # the pop flicks the finger up
    c.key(5, **{side: vlerp(hit, add(WAIT[side], (0.0, 1.0, 1.2)), 0.55), side + 'pole': (sx * 0.4, -0.9, -0.2)})
    c.key(6, pel=(0.0, -0.35, 0.2 if side == 'R' else 0.35), pyaw=D(-23), cyaw=D(-22) if side == 'R' else D(-30), cpitch=0.15,
          hyaw=D(-9), **{side: add(WAIT[side], (0.0, 0.8, 0.7)), side + 'pole': WAIT[side + 'pole'], side + 'wrist': (0.0, 0.0, 0.0),
                         other: add(WAIT[other], (0.0, 0.6, 0.4)), other + 'pole': WAIT[other + 'pole']})
    c.key(11, pel=(0.0, -0.18, 0.05), pyaw=D(-24.5), cyaw=D(-27) if side == 'R' else D(-23), cpitch=0.13, hyaw=D(-10),
          **{side: add(WAIT[side], (0.0, 0.25, 0.25)), other: add(WAIT[other], (0.0, 0.15, 0.1))})
    grow_keys(c, {f: 1.0 + (JAB_GROW[side] - 1.0) * k for f, k in JAB_EASE.items()}, sides=side)
    return c.keys()


def jab3():
    """Attack13, the push-away: both hands draw in to the chest (the load, 1-3), then both palms shove out square with a
    lunge of the hips (4-5), held through the pulse (5-7), kicked up by it (8-9) and eased home."""
    n = 30
    c = Clip(n)
    c.key(2, pel=(0.0, -0.95, -0.35), pyaw=D(-30), cyaw=D(-42), cpitch=0.04, hyaw=D(-8), hpitch=0.06,
          R=(-1.5, 8.7, 0.6), Rpole=(-0.9, -0.4, -0.3), L=(1.2, 8.7, 1.7), Lpole=(0.9, -0.4, -0.3),
          Rwrist=(0.0, 0.0, 0.4), Lwrist=(0.0, 0.0, -0.4))
    c.key(3, pel=(0.0, -1.05, -0.4), cyaw=D(-44), cpitch=0.02)
    c.key(1, Rhand=(0.5, 0.3, 0, 0), Lhand=(0.5, 0.3, 0, 0))
    c.hold(3, 13, Rhand=OPEN, Lhand=OPEN)
    c.key(20, Rhand=(0, 0.3, 0, 0), Lhand=(0, 0.3, 0, 0))
    for f, k in ((4, 0.75), (5, 1.0), (6, 1.02), (7, 1.03)):
        c.key(f, pel=(0.0, -0.9, 1.65 * k), pyaw=D(-18), cyaw=D(-24) + D(2) * (k - 1) * 30, cpitch=0.27, hyaw=D(-4),
              hpitch=-0.05, Rwrist=(0.0, 0.0, 0.55), Lwrist=(0.0, 0.0, -0.55))
    for f in (5, 6, 7):
        c.reach(f, 'R', HIT['jab3R'], 0.8, pole=(-0.4, -1.0, 0.0))
        c.reach(f, 'L', HIT['jab3L'], 0.8, pole=(0.4, -1.0, 0.0))
    c.key(4, R=(-2.3, 9.0, 3.6), L=(1.8, 9.0, 4.9))
    # the pulse kicks the palms up and rocks him back onto his heels
    c.key(9, pel=(0.0, -0.7, 1.1), cyaw=D(-12), cpitch=0.18, hpitch=-0.1, R=(-2.2, 10.2, 3.2), L=(1.7, 10.2, 4.6),
          Rwrist=(0.0, 0.0, 0.8), Lwrist=(0.0, 0.0, -0.8))
    c.key(13, pel=(0.0, -0.5, 0.6), pyaw=D(-20), cyaw=D(-20), cpitch=0.14, hyaw=D(-8), hpitch=0.0,
          R=(-2.3, 8.2, 2.0), L=(2.0, 8.0, 3.0), Rpole=(-0.5, -0.8, -0.3), Lpole=(0.5, -0.8, -0.3),
          Rwrist=(0.0, 0.0, 0.2), Lwrist=(0.0, 0.0, -0.2))
    c.key(20, pel=(0.0, -0.15, 0.15), pyaw=D(-24), cyaw=D(-26), cpitch=0.12, hyaw=D(-10),
          R=add(WAIT['R'], (0.0, 0.3, 0.3)), L=add(WAIT['L'], (0.0, 0.25, 0.25)), Rwrist=(0, 0, 0), Lwrist=(0, 0, 0))
    grow_keys(c, JAB3_GROW)
    return c.keys()


FTILT_HIT = {0.45: 'ftiltHi', 0.0: 'ftiltS', -0.45: 'ftiltLw'}


def ftilt(angle_y):
    """The forward tilts: Hand Gun, a quick draw. The gun hand drops to his hip as he dips and turns away (1-2) and snaps
    into the gun there (3); the arm swings up from the hip into the aim, straight down the line with the chest turning
    his gun shoulder at the target and the free arm swung back (4-6); held through the shot (7-9) as the barrel kicks up
    at the wrist, then the arm recoils (10-12), the aim settles and lowers, the gun folds back into the hand (16) and he
    eases home."""
    n = 30
    c = Clip(n)
    a = math.atan2(angle_y, 1.0)
    hit = HIT[FTILT_HIT[angle_y]]
    fore = (None, angle_y, 1.0)
    c.key(1, pel=(0.0, -0.5, -0.15), pyaw=D(-29), cyaw=D(-42), cpitch=0.14, hyaw=D(-6), hpitch=0.0,
          R=(-2.55, 6.9, -0.6), Rpole=(-0.7, 0.2, -0.7), L=(2.0, 7.6, 2.6), Lpole=(0.6, -0.5, -0.5))
    c.key(3, pel=(0.0, -0.8, -0.2), pyaw=D(-31), cyaw=D(-48), cpitch=0.12, hpitch=-0.2 * a,
          R=(-2.6, 6.6, -0.4), Rwrist=(0.0, 0.0, 0.5), L=(2.0, 7.9, 2.4))
    c.key(4, pel=(0.0, -0.8, 0.0), pyaw=D(-26), cyaw=D(-30), cpitch=0.14, R=(-2.7, 7.1, 1.6), Rpole=(-0.8, -0.2, -0.5),
          Rwrist=(0.0, 0.0, 0.3))
    c.key(5, pel=(0.0, -0.72, 0.2), pyaw=D(-16), cyaw=D(2), cpitch=0.16, R=vlerp((-2.7, 7.6, 2.9), hit, 0.5),
          Rwrist=(0.0, 0.0, 0.1), L=(2.1, 7.7, 0.2), Lpole=(0.6, -0.5, 0.4))
    # the aim's body: up leans back onto the rear foot and looks up the barrel; down sinks over the front knee
    bp = {0.45: (-0.46, 0.57, -0.08), 0.0: (-0.47, -0.1, 0.16), -0.45: (-0.3, -0.82, 0.42)}[angle_y]
    for f, k in ((6, 0.0), (7, 0.0), (8, 0.5), (9, 1.0)):
        c.key(f, pel=(0.0, bp[0], bp[1]), pyaw=D(-10), cyaw=D(14) - D(2) * k, cpitch=bp[2], hyaw=D(-3),
              hpitch=-0.6 * a, L=(2.4, 7.4 + 1.5 * angle_y, -1.3), Lpole=(0.6, -0.4, 0.6))
        c.shoot(f, 'R', hit, fore, tip=GUN_TIP, fit=(0.0, 1.0, 1.0))
    c.key(6, Rwrist=(0.0, 0.0, 0.0)); c.key(7, Rwrist=(0.0, 0.0, 0.0))
    c.key(1, Rhand=(0.6, 0, 0, 0), Lhand=(0.3, 0.3, 0, 0))
    c.hold(2, 15, Rhand=FIST)
    c.hold(5, 14, Lhand=OPEN)
    c.key(18, Rhand=(0, 0.6, 0, 0), Lhand=(0, 0.4, 0, 0))
    c.key(24, Rhand=(0, 0.15, 0, 0), Lhand=REST)
    c.key(8, Rwrist=(0.0, 0.0, 0.55))                              # the shot kicks the barrel up at the wrist
    c.key(9, Rwrist=(0.0, 0.0, 0.35))
    c.key(11, pel=(0.0, -0.55, 0.0), cyaw=D(6), cpitch=0.1, hpitch=-0.3 * a,
          R=add(hit, (0.1, 0.9, -1.3)), Rpole=(-0.3, -0.6, -0.6), Rwrist=(0.0, 0.0, 0.2))
    c.key(13, pel=(0.0, -0.52, 0.02), cyaw=D(8), R=add(hit, (0.05, 0.05, -0.7)), Rpole=(-0.25, -0.9, -0.3), Rwrist=(0.0, 0.0, -0.05))
    c.key(15, pel=(0.0, -0.48, 0.03), cyaw=D(4), R=add(hit, (0.0, -0.5, -1.2)), Rwrist=(0.0, 0.0, -0.1), L=(2.3, 7.3, -0.8))
    c.key(18, pel=(0.0, -0.35, 0.15), pyaw=D(-20), cyaw=D(-6), cpitch=0.13, hyaw=D(-8), hpitch=0.0,
          R=(-2.4, 7.0, 1.6), Rpole=(-0.4, -0.8, -0.5), Rwrist=(0, 0, 0), L=(2.3, 6.8, 1.0), Lpole=WAIT['Lpole'])
    c.key(24, pel=(0.0, -0.08, 0.02), pyaw=D(-24.5), cyaw=D(-23), cpitch=0.12, hyaw=D(-10),
          R=add(WAIT['R'], (0.0, 0.15, 0.2)), L=add(WAIT['L'], (0.0, 0.1, 0.05)))
    return c.keys()


def utilt():
    """Up tilt: the cape twirl. He sinks and winds the other way, arms folded across his chest (1-3), springs up off both
    boots and flings the arms out wide as he spins a full turn toward his gun side in the air (4-10), the capelet flaring
    up and out from the spin, lands (10), the arms fall and he settles. Frame 30 is the idle a full turn round, the same
    pose (every yaw ends 360 degrees on)."""
    n = 30
    c = Clip(n)
    for k in ('pyaw', 'cyaw', 'hyaw', 'Ltoe', 'Rtoe'):
        c.q1[k] -= TAU
    w = WAIT
    spin = {3: D(8), 4: D(-20), 5: D(-85), 6: D(-155), 7: D(-225), 8: D(-290), 9: D(-340), 10: D(-368), 11: D(-366),
            13: D(-361), 16: D(-360)}
    lift = {4: 0.15, 5: 0.55, 6: 0.85, 7: 0.95, 8: 0.8, 9: 0.45, 10: 0.0}
    hop = {3: -1.15, 4: -0.55, 5: 0.15, 6: 0.45, 7: 0.5, 8: 0.35, 9: -0.1, 10: -0.95, 11: -1.05, 12: -0.85, 14: -0.55,
           17: -0.3, 22: -0.1}
    c.key(2, pel=(0.0, -1.0, -0.1), pyaw=w['pyaw'] + D(6), cyaw=w['cyaw'] + D(12), cpitch=0.3, hyaw=w['hyaw'] + D(2),
          hpitch=0.15, R=(0.2, 8.4, 1.7), Rpole=(-0.9, -0.3, -0.2), L=(-0.2, 8.6, 1.9), Lpole=(0.9, -0.3, -0.2))
    for f, a in spin.items():
        kw = dict(pyaw=w['pyaw'] + a, cyaw=w['cyaw'] + a * 1.02, hyaw=w['hyaw'] + a + (D(-35) if 4 <= f <= 9 else 0.0),
                  cpitch=0.3 if f == 3 else (0.02 if 5 <= f <= 9 else 0.18), hpitch=0.15 if f == 3 else -0.15 if 5 <= f <= 9 else 0.05)
        if f in hop: kw['pel'] = (0.0, hop[f], 0.0)
        if 4 <= f <= 10:
            st = turned(wait(), a)
            kw.update(LF=(st['LF'][0], lift.get(f, 0.0), st['LF'][2]), RF=(st['RF'][0], lift.get(f, 0.0) * 0.8, st['RF'][2]),
                      Ltoe=st['Ltoe'], Rtoe=st['Rtoe'])
        elif f > 10:
            st = turned(wait(), -TAU)
            kw.update(LF=st['LF'], RF=st['RF'], Ltoe=st['Ltoe'], Rtoe=st['Rtoe'])
        if f == 3:
            kw.update(R=(0.1, 8.3, 1.6), L=(-0.3, 8.5, 1.8))
        elif 5 <= f <= 9:
            open_ = 1.0 if f >= 6 else 0.7
            kw.update(R=roty((-2.2 - 3.0 * open_, 11.4, 0.1), a), Rpole=roty((-0.1, -0.5, -0.9), a),
                      L=roty((2.2 + 3.0 * open_, 11.4, 0.4), a), Lpole=roty((0.1, -0.5, -0.9), a))
        elif f == 10:
            kw.update(R=roty((-4.2, 9.8, 0.3), a), L=roty((4.2, 9.8, 0.6), a))
        c.key(f, **kw)
    c.key(2, Rhand=(0.7, 0, 0, 0), Lhand=(0.7, 0, 0, 0))
    c.hold(5, 11, Rhand=OPEN, Lhand=OPEN)
    c.key(17, Rhand=(0, 0.4, 0, 0), Lhand=(0, 0.4, 0, 0))
    c.key(22, Rhand=REST, Lhand=REST)
    for f in (12, 14, 17, 22):
        c.key(f, pel=(0.0, hop.get(f, 0.0), 0.0))
    c.key(13, R=add(w['R'], (-0.5, 1.5, 0.1)), L=add(w['L'], (0.5, 1.4, 0.0)), Rpole=w['Rpole'], Lpole=w['Lpole'])
    c.key(17, R=add(w['R'], (-0.1, 0.4, 0.1)), L=add(w['L'], (0.1, 0.35, 0.0)), cpitch=0.13)
    c.key(22, R=add(w['R'], (0.0, 0.1, 0.03)), L=add(w['L'], (0.0, 0.08, 0.0)), cpitch=0.12)
    grow_keys(c, UTILT_GROW)
    return c.keys()


# the up tilt's head hitbox (the blockout's, on HeadN at (0, 2, 1.2)): its path on frames 6-10 as TopN bursts, since the
# twirl turns the head through a full circle
UTILT_HEAD_PATH = [(6, 11.829, 1.872), (7, 11.942, 1.608), (8, 12.041, 1.34), (9, 12.125, 1.069), (10, 12.194, 0.796)]


def dtilt():
    """Down tilt, from the crouch: the gun hand tucks back by the hip as the fingers snap into the Finger Shot's tubes (1-4),
    then thrusts low along the floor, the arm straight down the line (5-6), held through the shot (6-8) with a kick of the
    tubes, recoils (9-11), folds back into the hand and returns to the crouch."""
    n = 24
    cr = A.crouch_pose()
    c = Clip(n, start=cr, end=cr, heel_auto=False)
    q = c.q0
    rel = lambda **kw: {k: (add(q[k], v) if isinstance(v, tuple) else q[k] + v) for k, v in kw.items()}
    fore = (None, -0.26, 1.0)
    c.key(2, **rel(pel=(0.0, 0.0, -0.15), cyaw=D(-16), cpitch=0.04), R=add(q['R'], (0.2, 1.2, -1.4)), Rpole=(-0.8, -0.2, -0.5))
    c.key(4, **rel(pel=(0.0, 0.18, -0.25), cyaw=D(-20), cpitch=0.0), R=add(q['R'], (0.25, 1.1, -1.6)))
    c.key(5, **rel(pel=(0.0, 0.36, -0.3), cyaw=D(14), cpitch=-0.06), R=vlerp(add(q['R'], (0.2, 1.0, -1.2)), HIT['dtilt'], 0.6),
          L=add(q['L'], (0.1, 0.3, -0.9)))
    for f, k in ((6, 0.0), (7, 0.5), (8, 1.0)):
        c.key(f, **rel(pel=(0.0, 0.5, -0.35), cyaw=D(32) - D(2) * k, cpitch=-0.1, hpitch=-0.1), L=add(q['L'], (0.2, 0.4, -1.2)))
        c.shoot(f, 'R', HIT['dtilt'], fore, tip=GUN_TIP, fit=(0.0, 1.0, 1.0))
    c.key(6, Rwrist=(0, 0, 0)); c.key(7, Rwrist=(0.0, 0.0, 0.45)); c.key(8, Rwrist=(0.0, 0.0, 0.3))
    c.key(2, Rhand=(0.6, 0, 0, 0))
    c.hold(4, 12, Rhand=OPEN)
    c.key(17, Rhand=(0, 0.3, 0, 0))
    c.key(10, **rel(pel=(0.0, 0.35, -0.3), cyaw=D(16), cpitch=-0.05), R=add(HIT['dtilt'], (0.1, 0.7, -1.5)), Rwrist=(0.0, 0.0, 0.15))
    c.key(15, **rel(pel=(0.0, 0.1, -0.1), cyaw=D(3), cpitch=0.0), R=add(q['R'], (0.0, 0.3, 0.3)), Rpole=q['Rpole'],
          Rwrist=(0, 0, 0), L=q['L'])
    return c.keys()


# The dash attack's root motion (TransN along his facing): the charge drives him in to the shot (6), the recoil brakes
# him hard, and he skids to a stop
DASH_PATH = [(0, 0.0), (3, 4.5), (6, 11.0), (8, 14.0), (10, 16.0), (15, 19.5), (24, 21.5), (40, 22.0)]


def aim_from(q, side, d, reach):
    """a wrist target `reach` from that side's shoulder along direction d (the arm straight, aimed), on parameters q"""
    return add(shoulder(q, side), mul(norm(d), reach))


def on_arm(q, side, x):
    """the point x down that side's forearm (ArmJ), in the body frame, on parameters q"""
    W = world(assemble(q))
    return sub(tuple(rig.xform((x, 0.0, 0.0), W[f'{side}ArmJ'])), q.get('trans', (0.0, 0.0, 0.0)))


def run_pose():
    import locomotion
    return locomotion.anim('Run')[1][0][1]


def dash_attack():
    """Cannon Charge (Michael, 2026-09-30: the old shoulder dive was "visually unclear what action it's supposed to be ...
    puny / unfinished"): out of the run he plants the lead boot and draws the right arm back to his hip as it folds into
    the Hand Cannon (1-3, the ka-chunk); he lunges low and thrusts the cannon out level in front of him, the left hand
    clamping under the barrel (4-5); BOOM at point-blank (6): the recoil kicks the barrel up and throws his weight back,
    braking the charge, and he skids on his heels with the barrel smoking (7-15); the skid ends (18), the barrel comes
    down, the cannon folds back into the hand (24) and he rises into the idle. TransN carries the charge and the skid."""
    n = 40
    end = A.base().move('TransN', (0.0, 0.0, DASH_PATH[-1][1]))
    c = Clip(n, start=run_pose(), end=end, heel_auto=False)
    c.free_ends = {'trans'}
    zf = pchip([f for f, _ in DASH_PATH], [z for _, z in DASH_PATH], flat_ends=False)
    for f in range(1, n):
        c.key(f, trans=(0.0, 0.0, zf(f)))
    c.key(0, trans=(0.0, 0.0, 0.0))
    fwd = (0.06, -0.08, 1.0)                              # the barrel: level in front, a touch down
    # the plant and the draw: the right arm back to the hip as it folds into the cannon
    c.key(2, pel=(0.0, -0.9, -0.1), pyaw=D(-6), ppitch=0.15, proll=0.0, cyaw=D(-20), cpitch=0.25, croll=0.0, hyaw=D(-8),
          hpitch=0.05, R=(-2.3, 7.4, -1.4), Rpole=(-0.6, -0.4, -0.7), L=(1.6, 8.3, 1.2), Lpole=(0.6, -0.4, -0.7),
          LF=(1.05, 0.0, 1.1), Ltoe=D(6), Lheel=0.0, RF=(-1.1, 0.0, -1.4), Rheel=0.3)
    c.key(3, pel=(0.0, -1.0, -0.15), cyaw=D(-24), cpitch=0.28, R=(-2.35, 7.3, -1.6))
    # the lunge: low, the cannon thrust out level, the left hand under the barrel
    lunge = dict(pel=(0.0, -1.35, 0.6), pyaw=D(8), ppitch=0.3, cyaw=D(16), cpitch=0.42, hyaw=D(-2), hpitch=0.1,
                 LF=(1.05, 0.0, 1.6), RF=(-1.1, 0.25, -2.6), Rheel=0.7)
    c.key(5, **lunge)
    c.key(5, R=aim_from(c.at(5), 'R', fwd, UA + FA - 0.1), Rpole=(-0.8, -0.5, -0.2))
    c.key(4, pel=(0.0, -1.25, 0.35), cyaw=D(4), cpitch=0.36, R=add(aim_from(c.at(5), 'R', fwd, UA + FA - 0.1), (0.0, -0.3, -1.6)))
    # BOOM (6): the recoil kicks the barrel up and back and throws his weight onto his heels; held a beat (7-9)
    kick = dict(pel=(0.0, -1.2, -0.5), pyaw=D(4), ppitch=0.05, cyaw=D(10), cpitch=-0.12, hpitch=-0.14,
                LF=(1.05, 0.0, 1.9), RF=(-1.1, 0.0, -2.2), Rheel=0.2, Lheel=0.0)
    c.key(6, **lunge)
    c.key(6, R=aim_from(c.at(6), 'R', fwd, UA + FA - 0.05))
    c.key(8, **kick)
    c.key(8, R=aim_from(c.at(8), 'R', norm((0.05, 0.45, 0.9)), UA + FA - 0.35))
    c.key(10, **dict(kick, pel=(0.0, -1.25, -0.4), cpitch=-0.08))
    c.key(10, R=aim_from(c.at(10), 'R', norm((0.05, 0.38, 0.92)), UA + FA - 0.3))
    # the skid: on his heels, the smoking barrel sinking back to level
    c.key(15, pel=(0.0, -1.2, -0.2), pyaw=D(0), ppitch=0.08, cyaw=D(6), cpitch=0.02, hpitch=-0.04, Rheel=0.1)
    c.key(15, R=aim_from(c.at(15), 'R', norm((0.05, 0.12, 1.0)), UA + FA - 0.3))
    c.key(18, pel=(0.0, -1.05, -0.05), pyaw=D(-8), ppitch=0.05, cyaw=D(-6), cpitch=0.12, hyaw=D(-6), hpitch=0.02,
          RF=(-1.2, 0.0, -2.0), Rheel=0.0, Rtoe=D(-10))
    c.key(18, R=aim_from(c.at(18), 'R', norm((0.1, -0.25, 0.95)), UA + FA - 0.6))
    # the left hand under the barrel through the shot, flung off by the recoil, then down
    for f in (5, 6):
        q = c.at(f)
        c.key(f, L=add(on_arm(q, 'R', 1.2), (0.3, -0.6, 0.0)), Lpole=(0.6, -0.6, -0.4))
    c.key(8, L=(2.1, 8.9, 0.8), Lpole=(0.6, -0.4, -0.6))
    c.key(15, L=(2.0, 8.0, 1.2))
    c.key(24, pel=(0.0, -0.75, 0.05), pyaw=D(-18), ppitch=0.02, cyaw=D(-20), cpitch=0.2, hyaw=D(-9), hpitch=0.0,
          R=(-2.2, 7.8, 1.2), Rpole=(-0.6, -0.6, -0.4), L=add(WAIT['L'], (0.1, 0.5, 0.2)), Lpole=WAIT['Lpole'],
          LF=WAIT['LF'], Ltoe=WAIT['Ltoe'], RF=WAIT['RF'], Rtoe=WAIT['Rtoe'])
    c.key(30, pel=(0.0, -0.3, 0.02), pyaw=D(-23), cyaw=D(-25), cpitch=0.13, hyaw=D(-10),
          R=add(WAIT['R'], (-0.1, 0.4, 0.3)), Rpole=WAIT['Rpole'], L=add(WAIT['L'], (0.0, 0.15, 0.05)))
    c.key(35, pel=(0.0, -0.08, 0.0), cyaw=D(-25), cpitch=0.12, R=add(WAIT['R'], (0.0, 0.08, 0.05)), L=add(WAIT['L'], (0.0, 0.05, 0.0)))
    c.hold(2, 22, Rhand=FIST)
    c.hold(4, 7, Lhand=GRIP)
    c.key(10, Lhand=OPEN)
    c.key(26, Rhand=OPEN)
    c.key(32, Rhand=(0, 0.2, 0, 0), Lhand=(0, 0.2, 0, 0))
    return c


def dash_keys():
    return dash_attack().keys()


# The rocket fists' growth (anims.apply_grow, frame -> HandN's scale). The cast grow the striking limb on its first active
# frame and ease it back (research/limb_scale.md: Mario's jab fist 2.24x on frame 2, his forward smash's hand 1.44x on
# 12). The peak is set by the fist's size against the hitbox it carries, seen side-on (director/labs/fist_read.py,
# research/fist_read.md): on its first active frame Mario's fist fills 0.42 of his forward smash's hitbox radius (Doc
# 0.40) and 0.47 of his grab's; Geno's unscaled fist fills 0.15 of Double Punch's 4.4 and 0.175 of the grab's 4.0. So
# Double Punch peaks at 0.42 / 0.15 = 2.8 (the cast's largest growth is Mario's up tilt, 3.0; the grabs matched 0.47 at
# 2.7, then came down to Mario's cost, below). Double Punch holds it while the fists are out (15-19: a fist shrinking in flight reads as receding) and
# eases home as they return, back to 1 when they dock (27). The grabs ease back over three frames, as Mario's jab does, so
# a catch (CatchWait takes over on 9-10, at the rest scale) doesn't pop. The fingertips stay at 1: his fist pose already
# reads as one block (Mario's forward smash shrinks his splayed glove fingers; on Geno 0.55 only tucks in a knuckle).
FS_GROW = {14: 1.0, 15: 2.8, 18: 2.6, 19: 2.5, 21: 2.2, 23: 1.7, 24: 1.5, 26: 1.2, 27: 1.0}
# The grabs cost what Mario's own growth costs him (Michael, 2026-09-29: "around parity with Mario's"): the grown fist's
# hurtbox eats his forward disjoint (Mario's grab loses 0.67 to his growth, his dash grab 0.80; research/growth_cost.md),
# so the peaks are the ones that lose the same, 1.83 and 2.0 (2.7 lost 1.37 and 1.36), tangible as Mario's are
GRAB_PEAK = {False: 1.83, True: 2.0}                                   # the standing grab, the dash grab
GRAB_EASE = {-1: 0.0, 0: 1.0, 1: 0.706, 2: 0.235, 3: 0.059, 4: 0.0}    # from the grab frame: the share of the growth


# The rest of his body-contact normals (Michael, 2026-09-29: "make the change to the rest of the normals"), each sized so
# the grown part fills its nearest hitbox as the cast's analog does (research/fist_read.md; cover = the part's side-on
# equivalent radius over the hitbox's), on the cast's timing (the peak on the first active frame, eased back):
#   jab 1 / 2   the pointing hand, 2.0 / 1.8: Mario's jab 1 fist fills 0.64 of its box and his jab 2 fist 0.57; Geno's
#               hands fill 0.32 (0.32 x 2.0 = 0.64, 0.32 x 1.8 = 0.57). Back to 1 three frames on, as Mario's.
#   jab 3       both palms 2.2: Mario's jab 3 kick fills 0.70 at its peak; Geno's palms 0.31. Held through the pulse.
#   up tilt     both hands 2.1 on the arc: Mario's up tilt hand fills 0.31 of its box on its first active frame; Geno's
#               flung hands 0.15 of the 5.0 bursts.
#   pummel      the finger hand 1.25: Mario's pummel hands fill 0.19-0.21 (grown 1.03-1.1); Geno's 0.16.
#   dash attack the lead (gun) arm 1.3: the cast's dash attacks grow 1.3-1.4 (Fox's leg, Luigi's fists) and fill
#               0.37-0.43; Geno's arm fills 0.31 of the dive's box.
# (The neutral air's back kick, the shin 1.45, is poses_air.nair's.)
JAB_GROW = {'R': 2.0, 'L': 1.8}                            # jab 1 (right), jab 2 (left)
JAB_EASE = {2: 0.0, 3: 1.0, 4: 0.65, 5: 0.25, 6: 0.0}    # frame -> the share of the growth
JAB3_GROW = {4: 1.0, 5: 2.2, 6: 2.1, 7: 1.8, 9: 1.2, 10: 1.0}
UTILT_GROW = {5: 1.0, 6: 2.1, 9: 2.0, 11: 1.4, 13: 1.0}
PUMMEL_GROW = {8: 1.0, 9: 1.25, 11: 1.2, 14: 1.0}


def grow_keys(c, profile, at=0, sides='RL', what='grow'):
    for f, g in profile.items():
        c.key(at + f, **{f'{s}{what}': g for s in sides})


# The Double Punch's fist positions (x, y, z) per active frame: outbound (15-18) and the weak return (24-26)
FS_HIT = {
    0.0: {15: ((-3.928, 8.931, 15.944), (3.37, 8.931, 17.562)), 16: ((-4.584, 8.931, 21.404), (4.025, 8.931, 23.023)),
          17: ((-5.06, 8.931, 25.376), (4.502, 8.931, 26.994)), 18: ((-5.09, 8.931, 25.624), (4.532, 8.931, 27.243)),
          24: ((-3.229, 8.931, 10.119), (2.671, 8.931, 11.737)), 25: ((-2.912, 8.931, 7.471), (2.353, 8.931, 9.09)),
          26: ((-2.594, 8.931, 4.823), (2.035, 8.931, 6.442))},
    0.4: {15: ((-3.792, 14.911, 14.808), (3.234, 14.911, 16.426)), 16: ((-4.401, 16.941, 19.883), (3.843, 16.941, 21.502)),
          17: ((-4.844, 18.417, 23.574), (4.286, 18.417, 25.193)), 18: ((-4.872, 18.51, 23.805), (4.313, 18.51, 25.423)),
          24: ((-3.143, 12.745, 9.394), (2.584, 12.745, 11.013)), 25: ((-2.847, 11.761, 6.933), (2.289, 11.761, 8.552)),
          26: ((-2.552, 10.777, 4.473), (1.993, 10.777, 6.091))},
    -0.4: {15: ((-3.792, 2.952, 14.808), (3.234, 2.952, 16.426)), 16: ((-4.401, 0.922, 19.883), (3.843, 0.922, 21.502)),
           17: ((-4.844, -0.555, 23.574), (4.286, -0.555, 25.193)), 18: ((-4.872, -0.647, 23.805), (4.313, -0.647, 25.423)),
           24: ((-3.143, 5.117, 9.394), (2.584, 5.117, 11.013)), 25: ((-2.847, 6.102, 6.933), (2.289, 6.102, 8.552)),
           26: ((-2.552, 7.086, 4.473), (1.993, 7.086, 6.091))}}


# The Double Punch's torso per angle: straight, up (weight back, chest open to the sky) and down (bent over the front knee)
FS_BODY = {0.0: dict(pel=(0.0, -1.25, 1.5), pyaw=D(-12), cyaw=D(-12), cpitch=0.34, hpitch=0.0),
           0.4: dict(pel=(0.0, -0.95, 1.05), pyaw=D(-14), cyaw=D(-14), cpitch=0.02, hpitch=-0.45),
           -0.4: dict(pel=(0.0, -1.85, 1.35), pyaw=D(-12), cyaw=D(-10), cpitch=0.72, hpitch=0.25)}
# ... and its held pose (the charge freezes frame 6): coiled low, fists chambered behind him, the angle in the chamber
FS_HELD = {0.0: dict(pel=(0.0, -1.95, -0.95), cpitch=-0.06, hpitch=0.12, R=(-2.4, 7.8, 0.0), L=(-0.3, 8.2, 0.9)),
           0.4: dict(pel=(0.0, -2.3, -1.05), cpitch=0.05, hpitch=-0.25, R=(-2.4, 6.9, 0.1), L=(-0.3, 7.2, 1.0)),
           -0.4: dict(pel=(0.0, -1.6, -0.8), cpitch=0.1, hpitch=0.35, R=(-2.3, 9.0, -0.1), L=(-0.4, 9.4, 0.8))}
# (the fists are chambered side by side in front of his chest, rocket rings showing: drawn back beside him, the capelet
# hides them from the side camera)
FS_LAUNCH = (0.32, 0.7)        # where the fists are on frames 15 and 16, from the arm's end (14) to the tip (17)
FS_DEPTH = (-2.3, 2.1)         # the fists' depth (x: R, L)


def fs_hits(angle_y):
    """The fists' hit points per active frame: the blockout's tip (17, 18) and return (24-26); frames 15 and 16 on the
    line from where the fists leave the arms to the tip (the blockout launched them 10 units in one frame, so the first
    outgoing boxes sat past a close opponent: a half-charged or angled Double Punch whiffed at close range)."""
    # the fists fly parallel from the shoulders (the blockout splayed them to a depth of +-5, where a 4.4 box barely
    # reaches an opponent's body at depth 0)
    H = {f: tuple((FS_DEPTH[k],) + tuple(p[1:]) for k, p in enumerate(v)) for f, v in FS_HIT[angle_y].items()}
    c = fsmash_clip(angle_y, resolve=False)
    q = c.at(14)
    out = {}
    for k, side in enumerate('RL'):
        sh = shoulder(q, side)
        tip = H[17][k]
        p14 = add(sh, mul(norm(sub(tip, sh)), UA + FA + 0.5))
        out[side] = p14
        for f, t in zip((15, 16), FS_LAUNCH):
            H[f] = tuple(vlerp(p14, tip, t) if kk == k else H[f][kk] for kk in range(2)) if f in H else None
    return H, out


def fsmash_clip(angle_y, resolve=True):
    n = 45
    c = Clip(n)
    a = math.atan2(angle_y, 1.0)
    B, Hd = FS_BODY[angle_y], FS_HELD[angle_y]
    c.key(2, pel=vlerp((0.0, 0.0, 0.0), Hd['pel'], 0.7), pyaw=D(-34), cyaw=D(-50), cpitch=0.04, hyaw=D(-8),
          hpitch=0.6 * Hd['hpitch'], R=vlerp(WAIT['R'], Hd['R'], 0.75), Rpole=(-0.6, -0.5, -0.6),
          L=vlerp(WAIT['L'], Hd['L'], 0.75), Lpole=(0.7, -0.5, -0.5), Rwrist=(0.0, 0.0, 0.3), Lwrist=(0.0, 0.0, -0.3))
    for f, k in ((4, 0.0), (6, 0.35), (9, 0.75), (12, 1.0)):      # the charge pose (6, held while A is), creeping on
        c.key(f, pel=add(Hd['pel'], (0.0, -0.15 * k, -0.12 * k)), pyaw=D(-38) - D(3) * k, cyaw=D(-58) - D(5) * k,
              cpitch=Hd['cpitch'] - 0.04 * k, hyaw=D(-6), hpitch=Hd['hpitch'],
              R=add(Hd['R'], (0.0, -0.1 * k, -0.25 * k)), Rpole=(-0.6, -0.5, -0.6), L=add(Hd['L'], (0.0, -0.1 * k, -0.25 * k)),
              Lpole=(0.7, -0.5, -0.5), LF=(1.3, 0.0, 1.8), RF=(-1.3, 0.0, -2.0))
    c.key(4, pel=add(Hd['pel'], (0.0, 0.06, 0.05)))              # the rockets snap on (4): a jolt through the doll
    # the thrust (14) and the flight (15-22): square to the target, lunging, the arms straight down the fists' lines
    for f in (14, 15, 16, 17, 18, 19, 21, 22):
        k = min(1.0, (f - 14) / 3.0)
        c.key(f, pel=add(B['pel'], (0.0, -0.05 * k, 0.1 * k)), pyaw=B['pyaw'], cyaw=B['cyaw'], cpitch=B['cpitch'] + 0.03 * k,
              hyaw=D(-4), hpitch=B['hpitch'], Rwrist=(0, 0, 0), Lwrist=(0, 0, 0))
    for f in (23, 24, 25, 26):
        c.key(f, pel=add(B['pel'], (0.0, 0.05, -0.15)), pyaw=B['pyaw'], cyaw=B['cyaw'] - D(2), cpitch=B['cpitch'] - 0.03,
              hpitch=B['hpitch'])
    for f in (2, 4, 6, 9, 12, 13):
        c.key(f, Rext=0.0, Lext=0.0)
    # the strike's first frame (13): uncoiling, the fists coming through at the hips on their way out
    c.key(13, pel=vlerp(add(Hd['pel'], (0.0, -0.15, -0.12)), B['pel'], 0.55), pyaw=D(-22), cyaw=D(-26),
          cpitch=0.5 * (Hd['cpitch'] + B['cpitch']), hpitch=0.5 * (Hd['hpitch'] + B['hpitch']),
          R=vlerp(add(Hd['R'], (0.0, -0.1, -0.3)), (-2.3, 8.0 + 4 * a, 3.2), 0.6),
          L=vlerp(add(Hd['L'], (0.0, -0.1, -0.3)), (2.0, 8.0 + 4 * a, 4.0), 0.6), Rpole=(-0.5, -0.5, -0.6), Lpole=(0.5, -0.5, -0.6))
    c.hold(2, 27, Rhand=FIST, Lhand=FIST)
    grow_keys(c, FS_GROW)
    c.key(30, Rhand=OPEN, Lhand=OPEN)
    c.key(38, Rhand=(0, 0.2, 0, 0), Lhand=(0, 0.2, 0, 0))
    # docking: the fists slam home and knock him back
    c.key(27, pel=(0.0, -1.0, 0.7), pyaw=D(-20), cyaw=D(-28), cpitch=0.1 + 0.3 * B['cpitch'], hyaw=D(-8), hpitch=0.4 * B['hpitch'],
          R=(-2.2, 8.4 + 3 * a, 2.2), Rpole=(-0.5, -0.8, -0.3), L=(1.9, 8.4 + 3 * a, 3.4), Lpole=(0.5, -0.8, -0.3),
          Rext=0.0, Lext=0.0, Rwrist=(0.0, 0.0, 0.35), Lwrist=(0.0, 0.0, -0.35))
    c.key(30, pel=(0.0, -0.85, 0.5), cyaw=D(-24), cpitch=0.14, hpitch=0.0, R=(-2.3, 7.6, 1.6), L=(2.0, 7.5, 2.6),
          Rwrist=(0, 0, 0), Lwrist=(0, 0, 0))
    c.key(36, pel=(0.0, -0.4, 0.15), pyaw=D(-24), cyaw=D(-26), cpitch=0.12, hyaw=D(-10), hpitch=0.0,
          R=add(WAIT['R'], (0.0, 0.4, 0.4)), Rpole=WAIT['Rpole'], L=add(WAIT['L'], (0.0, 0.35, 0.3)), Lpole=WAIT['Lpole'])
    c.key(41, pel=(0.0, -0.1, 0.03), cyaw=D(-25), R=add(WAIT['R'], (0.0, 0.08, 0.08)), L=add(WAIT['L'], (0.0, 0.06, 0.05)))
    if not resolve:
        return c
    H, p14 = fs_hits(angle_y)
    for k, side in enumerate('RL'):
        c.fist(14, side, p14[side], 0.5)
        for f in (15, 16, 17, 18, 24, 25, 26):
            c.fist(f, side, H[f][k], 0.5 if f < 20 else 0.3)
        tip = H[18][k]
        c.fist(19, side, add(tip, (0.0, 0.0, 0.1)), 0.5)
        for f, t in ((21, 0.3), (22, 0.62), (23, 0.85)):
            c.fist(f, side, vlerp(tip, H[24][k], t), 0.3)
    return c


def fsmash(angle_y):
    """Double Punch: both fists chambered behind him as he coils low and turns away (1-4), the angle already in the
    chamber (low for the up punch, high for the down); the hands snap into rocket fists (4) in the charge pose (6, the
    pose held while A is), which creeps on (6-13); the body uncoils into a lunge square to the target, leaning back for
    the up angle and over the front knee for the down, both arms driving straight down the fists' lines (13-14), and the
    fists launch from the arms (15) to the tip (17-18), hover, and are reeled back in (19-26), docking with a jolt that
    rocks him back (27); the hands return (28) and he recovers."""
    return fsmash_clip(angle_y).keys()


def usmash():
    """Star Gun: he drops into a deep squat with both hands crossed low (1-4), the hands snapping into star guns (4); the
    charge squat creeps (5-8); then he springs up onto his toes, both arms punching up in a wide V (9: straight up they
    hide behind his big head), and holds the stream (9-12) as the barrels chatter; the arms come down, the guns fold
    back (18) and he settles."""
    n = 40
    c = Clip(n)
    c.key(2, pel=(0.0, -1.7, -0.25), pyaw=D(-24), cyaw=D(-22), cpitch=0.46, hyaw=D(-10), hpitch=-0.2,
          R=(-1.6, 5.4, 1.5), Rpole=(-0.9, 0.2, -0.4), L=(1.4, 5.5, 1.9), Lpole=(0.9, 0.2, -0.4))
    # the held pose (5): sunk deep, the star guns pulled down by his hips pointing at the floor, eyes on the sky
    for f, k in ((4, 0.0), (5, 0.3), (6, 0.6), (7, 1.0)):
        c.key(f, pel=(0.0, -2.45 - 0.1 * k, -0.35), pyaw=D(-24), cyaw=D(-20), cpitch=0.62 + 0.03 * k, hpitch=-0.45 - 0.04 * k,
              R=(-0.9, 4.1 - 0.1 * k, 2.0), Rpole=(-0.9, 0.3, -0.3), L=(0.7, 4.2 - 0.1 * k, 2.3), Lpole=(0.9, 0.3, -0.3),
              Rwrist=(0.0, 0.0, -0.4), Lwrist=(0.0, 0.0, 0.4))
    # the spring (8): legs driving, the guns coming up past his chest
    c.key(8, pel=(0.0, -0.9, -0.1), pyaw=D(-22), cyaw=D(-18), cpitch=0.12, hyaw=D(-10), hpitch=-0.42,
          R=(-2.9, 9.8, 0.5), Rpole=(-0.7, -0.5, -0.5), L=(2.9, 9.9, 0.8), Lpole=(0.7, -0.5, -0.5),
          Rwrist=(0.0, 0.0, -0.2), Lwrist=(0.0, 0.0, 0.2))
    # the stream (9-12): arms thrust up in a wide V, clear of his big head from any side, the barrels chattering
    for f, k in ((9, 0.0), (10, 1.0), (11, 0.3), (12, 1.0)):
        c.key(f, pel=(0.0, 0.35, 0.0), pyaw=D(-20), cyaw=D(-16), cpitch=-0.12, hyaw=D(-10), hpitch=-0.45,
              R=(-3.7, 13.8 - 0.25 * k, 0.2), Rpole=(-0.6, -0.4, -0.7), L=(3.7, 13.8 - 0.25 * (1 - k), 0.5),
              Lpole=(0.6, -0.4, -0.7), Rwrist=(0.0, 0.0, 0.12 * k), Lwrist=(0.0, 0.0, -0.12 * (1 - k)))
    c.key(2, Rhand=(0.6, 0, 0, 0), Lhand=(0.6, 0, 0, 0))
    c.hold(4, 16, Rhand=FIST, Lhand=FIST)
    c.key(19, Rhand=(0, 0.7, 0, 0), Lhand=(0, 0.7, 0, 0))
    c.key(26, Rhand=(0, 0.15, 0, 0), Lhand=(0, 0.15, 0, 0))
    c.key(14, pel=(0.0, 0.2, 0.0), cpitch=-0.08, hpitch=-0.35, R=(-3.6, 13.5, 0.1), L=(3.6, 13.5, 0.4),
          Rwrist=(0, 0, 0), Lwrist=(0, 0, 0))
    c.key(18, pel=(0.0, -0.5, 0.0), pyaw=D(-23), cyaw=D(-22), cpitch=0.1, hpitch=-0.05, R=(-2.4, 10.4, 0.6),
          Rpole=(-0.8, -0.4, -0.3), L=(2.3, 10.4, 1.2), Lpole=(0.8, -0.4, -0.3))
    c.key(23, pel=(0.0, -0.55, 0.0), pyaw=D(-25), cyaw=D(-26), cpitch=0.14, hyaw=D(-10), hpitch=0.02,
          R=add(WAIT['R'], (-0.1, 0.6, 0.3)), Rpole=WAIT['Rpole'], L=add(WAIT['L'], (0.1, 0.5, 0.2)), Lpole=WAIT['Lpole'])
    c.key(31, pel=(0.0, -0.12, 0.0), cyaw=D(-24.5), cpitch=0.12, R=add(WAIT['R'], (0.0, 0.1, 0.05)), L=add(WAIT['L'], (0.0, 0.08, 0.04)))
    return c.keys()


# The twin Hand Cannons (Michael, 2026-09-28: Mega Man's two-sided down smash): he opens square to the camera (chest
# -80 degrees, the orientation study's option A: his front shows facing right), so the left cannon points forward and the
# right one back, and both fire at once on frame 7. The front arm box keeps the blockout's height and reach (y 5.4,
# z 5.6); the back one mirrors it.
DS_FRONT, DS_BACK = (0.3, 5.405, 5.574), (0.3, 5.405, -5.574)
DS_FORE_F, DS_FORE_B = (0.0, -0.32, 1.0), (0.0, -0.32, -1.0)


def dsmash():
    """Twin Hand Cannons, both sides at once, the motion spread over the whole move (Michael, 2026-09-30: "extend the
    animation ... so it's not purely frontloaded"; the frame data stays). The wind-up reads within the startup: he rises
    a touch and gathers both arms in (1), then drops hard into a wide, braced squat turning square to the camera as both
    forearms fold open into cannons (2); the held pose (3-5, frozen while A is held) has both cannons cocked low to either
    side; they swing up level (6) and fire together (7-9). The recoil kicks both muzzles up and in and bounces him up off
    his heels (10-12); he comes down with a thud (14), bounces once (16), and holds the smoking cannons out while they
    shudder and sink (17-24); the cannons fold back into hands (28) and he rises slowly into the idle (28-43)."""
    n = 44
    c = Clip(n)
    feet = dict(LF=(1.6, 0.0, 2.35), RF=(-1.6, 0.0, -2.55), Ltoe=D(2), Rtoe=D(-38))
    sq = dict(pyaw=D(-62), cyaw=D(-80), hyaw=D(-22))
    c.key(1, pel=(0.0, -0.25, 0.0), pyaw=D(-36), cyaw=D(-46), cpitch=0.04, hyaw=D(-12), hpitch=-0.04,
          L=(0.7, 8.4, 1.3), Lpole=(0.2, -0.2, 1.0), R=(-1.3, 8.4, -0.4), Rpole=(-0.2, -0.2, -1.0))      # the gather
    c.key(2, pel=(0.0, -2.2, 0.0), cpitch=0.32, hpitch=0.1, **dict(sq, pyaw=D(-55), cyaw=D(-72)), **feet)
    for f, k in ((3, 0.0), (4, 0.35), (5, 0.6)):          # the held pose: braced low, both cannons cocked down and out
        c.key(f, pel=(0.0, -2.75 - 0.08 * k, 0.0), cpitch=0.36, hpitch=0.12, **sq, **feet,
              L=(-0.9, 4.7 - 0.1 * k, 4.1), Lpole=(-0.2, 0.6, 1.0), R=(-0.9, 4.7 - 0.1 * k, -4.1), Rpole=(-0.2, 0.6, -1.0))
    c.key(6, pel=(0.0, -2.55, 0.0), cpitch=0.3, hpitch=0.08, **sq,
          L=(0.2, 5.9, 4.3), R=(0.2, 5.9, -4.3), Lpole=(0.1, 0.3, 1.0), Rpole=(0.1, 0.3, -1.0))
    for f in (7, 8, 9):                                    # the blast, held through the active frames
        c.key(f, pel=(0.0, -2.45, 0.0), cpitch=0.26, hpitch=0.05, **sq)
        c.reach(f, 'L', DS_FRONT, GUN_TIP, pole=(0.0, 0.4, 1.0))
        c.reach(f, 'R', DS_BACK, GUN_TIP, pole=(0.0, 0.4, -1.0))
    # the recoil: both muzzles kick up and in, the doll bounces up off his heels and comes down with a thud
    c.key(10, pel=(0.0, -1.95, 0.0), cpitch=0.14, hpitch=-0.1, **sq,
          L=add(DS_FRONT, (0.0, 1.5, -1.1)), R=add(DS_BACK, (0.0, 1.5, 1.1)), Lpole=(0.0, 0.3, 1.0), Rpole=(0.0, 0.3, -1.0))
    c.key(12, pel=(0.0, -1.75, 0.0), cpitch=0.1, hpitch=-0.12, L=add(DS_FRONT, (0.0, 1.8, -1.4)), R=add(DS_BACK, (0.0, 1.8, 1.4)))
    c.key(14, pel=(0.0, -2.85, 0.0), cpitch=0.36, hpitch=0.12, L=add(DS_FRONT, (0.0, 0.5, -1.3)), R=add(DS_BACK, (0.0, 0.5, 1.3)))
    c.key(16, pel=(0.0, -2.55, 0.0), cpitch=0.3, hpitch=0.06, L=add(DS_FRONT, (0.0, 0.8, -1.4)), R=add(DS_BACK, (0.0, 0.8, 1.4)))
    # the smoking cannons held out, shuddering as they sink
    for f, dy in ((18, 0.45), (19, 0.62), (20, 0.4), (21, 0.52), (22, 0.3)):
        c.key(f, L=add(DS_FRONT, (0.0, dy, -1.5)), R=add(DS_BACK, (0.0, dy, 1.5)))
    c.key(18, pel=(0.0, -2.6, 0.0), cpitch=0.3)
    c.key(24, pel=(0.0, -2.5, 0.0), cpitch=0.3, **sq, L=(-0.5, 4.9, 4.0), R=(-0.5, 4.9, -4.0), **feet)
    c.key(28, pel=(0.0, -2.1, 0.0), pyaw=D(-54), cyaw=D(-66), cpitch=0.26, hyaw=D(-18), hpitch=0.06,
          L=(0.3, 6.6, 2.4), R=(-1.0, 6.6, -1.6), Lpole=(0.2, -0.2, 1.0), Rpole=(-0.2, -0.2, -1.0))
    c.key(33, pel=(0.0, -1.3, 0.0), pyaw=D(-42), cyaw=D(-48), cpitch=0.2, hyaw=D(-13), hpitch=0.03,
          L=add(WAIT['L'], (0.1, 0.8, 0.4)), R=add(WAIT['R'], (-0.2, 0.8, -0.2)), Lpole=WAIT['Lpole'], Rpole=WAIT['Rpole'],
          LF=WAIT['LF'], RF=WAIT['RF'], Ltoe=WAIT['Ltoe'], Rtoe=WAIT['Rtoe'])
    c.key(38, pel=(0.0, -0.5, 0.0), pyaw=D(-28), cyaw=D(-30), cpitch=0.14, hyaw=D(-10), hpitch=0.0,
          R=add(WAIT['R'], (0.0, 0.3, 0.1)), L=add(WAIT['L'], (0.0, 0.3, 0.1)))
    c.key(42, pel=(0.0, -0.1, 0.0), cyaw=D(-25), cpitch=0.12, R=add(WAIT['R'], (0.0, 0.05, 0.02)), L=add(WAIT['L'], (0.0, 0.04, 0.02)))
    c.hold(2, 28, Rhand=FIST, Lhand=FIST)
    c.key(31, Rhand=(0, 0.6, 0, 0), Lhand=(0, 0.6, 0, 0))
    c.key(38, Rhand=(0, 0.15, 0, 0), Lhand=(0, 0.15, 0, 0))
    return c.keys()


# ================================================================================================================ grab, throws
def _hold_w():
    import moves                                  # the hold point's single source: moves.HOLD_T and HOLD_YROT
    return add((0.0, rig.HIP_Y, 0.0), moves.HOLD_YROT, moves.HOLD_T)


HOLD_W = _hold_w()                                # CatchWait's hold point in the world: (0, 8.78, 6.83)
FACE = math.pi                                   # the held opponent faces him


def hold_params(breath=0.0):
    """CatchWait: the left hand has the opponent by the collar at arm's length, the right (gun) hand cocked at his chest,
    finger ready; knees soft, leaning a little into the hold. breath -1..1 is the loop's rise and fall."""
    q = wait()
    q.update(pel=(0.0, -0.45 + 0.07 * breath, 0.25), pyaw=D(-22), cyaw=D(-16) - D(1.5) * breath, cpitch=0.2 + 0.015 * breath,
             hyaw=D(-6), hpitch=0.04,
             L=(1.05, 8.85 + 0.03 * breath, 4.05), Lpole=(0.7, -0.6, -0.4), Lwrist=(0.0, 0.0, -0.25),
             R=(-1.75, 8.45 + 0.08 * breath, 1.75), Rpole=(-0.8, -0.5, -0.4), Rwrist=(0.0, 0.0, -0.2),
             throw=HOLD_W, throwry=FACE, Lhand=GRIP, Rhand=POINT)
    return q


def hold_pose(breath=0.0):
    return assemble(hold_params(breath))


def catch_wait():
    """The hold, breathing: one slow rise and fall a loop, the victim steady at the hold point."""
    n = 30
    c = Clip(n, start=hold_params(), end=hold_params())
    q = hold_params(1.0)
    c.key(15, **{k: q[k] for k in ('pel', 'cyaw', 'cpitch', 'L', 'R')})
    return c.keys()


def grab(frame, total, dash=False):
    """Catch (frame 7) and CatchDash (frame 9): the hands draw in and snap into the rocket fists, the arms punch out and
    the hands fly open to the grab point (their boxes ride them), and on a whiff reel back in, still open; the hands return and he
    recovers from the overreach. ThrowN sits at the hold point in the world from before the grab frame, so a catch
    latches there. The dash grab starts from the run and sits back into the slide (the template's root motion carries
    him) as the fists fire off his arms a short way, since its boxes sit close to him."""
    n = total
    c = Clip(n, start=run_pose() if dash else None, heel_auto=not dash)
    g0 = frame
    tr, tl = (HIT['dgrabR'], HIT['dgrabL']) if dash else (HIT['grabR'], HIT['grabL'])
    if dash:
        # out of the run: he plants and sits back into the slide, the fists chambered at his hips as they snap into
        # rocket fists (3); the arms punch out (6-7) and the fists fire off them (8), closing on the grab point (9-10: the
        # boxes, where the blockout had them), then reel back in (11-12) as he rises toward the hold
        c.key(3, pel=(0.0, -1.2, -0.1), pyaw=D(-8), ppitch=0.12, proll=0.0, cyaw=D(-24), cpitch=0.3, croll=0.0, hyaw=D(-6),
              hpitch=0.05, R=(-2.1, 7.2, -0.9), Rpole=(-0.5, -0.3, -0.8), L=(1.7, 7.4, -0.3), Lpole=(0.5, -0.3, -0.8),
              LF=(1.1, 0.0, 1.5), Ltoe=D(10), Lheel=0.0, RF=(-1.15, 0.0, -1.3), Rheel=0.25)
        c.key(5, pel=(0.0, -1.45, -0.35), pyaw=D(-12), ppitch=0.05, cyaw=D(-26), cpitch=0.22, hpitch=0.02,
              R=(-2.2, 7.1, -1.1), L=(1.8, 7.3, -0.5), LF=(1.15, 0.0, 1.7), RF=(-1.2, 0.0, -2.1), Rheel=0.35)
        for f in (2, 3, 5):
            c.key(f, Rext=0.0, Lext=0.0)
        # the punch (7), the fists firing (8) and closing on the grab point (9-10), the arms kicked back by the launch,
        # elbows dropping; the fists reeled home (11-12)
        body = {7: ((0.0, -1.45, -0.35), 0.24), 8: ((0.0, -1.5, -0.6), 0.16), 9: ((0.0, -1.5, -0.8), 0.1),
                10: ((0.0, -1.45, -0.8), 0.1), 11: ((0.0, -1.35, -0.6), 0.14), 12: ((0.0, -1.25, -0.4), 0.18)}
        for f, (pel, cp) in body.items():
            c.key(f, pel=pel, pyaw=D(-14), ppitch=0.04, cyaw=D(-18), cpitch=cp, hpitch=-0.03,
                  Rwrist=(0.0, 0.0, 0.0), Lwrist=(0.0, 0.0, 0.0))
        # the kick back (0: the arm straight at the fist) and where the fist is on its way out and back in; on 7 and 12
        # the fist is on the arm
        for f, k, dz in ((7, None, -1.6), (8, 0.9, -0.5), (9, 1.0, 0.0), (10, 1.0, 0.0), (11, 0.95, -0.6), (12, None, -1.8)):
            for side, sx, tgt in (('R', -1, tr), ('L', 1, tl)):
                pt = add(tgt, (0.0, -0.3 if dz else 0.0, dz))
                if k is None:
                    c.fist(f, side, pt, HAND * 0.8, pole=(sx * 0.6, -0.7, -0.3))
                    continue
                straight = norm(sub(pt, shoulder(c.at(f), side)))
                kicked = norm((sx * 0.25, -0.9, 0.3))
                c.launch(f, side, pt, norm(vlerp(straight, kicked, k)), HAND * 0.8)
        # the release frame (11: a caught opponent cuts to CatchWait here) rises toward the hold
        c.key(g0 + 2, pel=(0.0, -1.1, 0.0))
        c.key(15, pel=(0.0, -1.0, 0.2), pyaw=D(-16), ppitch=0.08, cyaw=D(-22), cpitch=0.3, R=(-2.4, 7.6, 1.8),
              L=(1.9, 7.7, 2.6), RF=(-1.2, 0.0, -2.2), Rheel=0.4, Rext=0.0, Lext=0.0)
        c.key(22, pel=(0.0, -0.7, 0.2), pyaw=D(-22), ppitch=0.03, cyaw=D(-24), cpitch=0.2, hyaw=D(-9),
              R=add(WAIT['R'], (0.0, 0.6, 0.6)), Rpole=WAIT['Rpole'], L=add(WAIT['L'], (0.0, 0.5, 0.4)), Lpole=WAIT['Lpole'],
              LF=WAIT['LF'], Ltoe=WAIT['Ltoe'], RF=WAIT['RF'], Rtoe=WAIT['Rtoe'], Rheel=0.0)
        c.key(31, pel=(0.0, -0.15, 0.03), pyaw=D(-25), ppitch=0.0, cyaw=D(-25), cpitch=0.12, hyaw=D(-10), hpitch=0.0,
              R=add(WAIT['R'], (0.0, 0.1, 0.1)), L=add(WAIT['L'], (0.0, 0.08, 0.05)))
    else:
        c.key(2, pel=(0.0, -0.6, -0.25), pyaw=D(-28), cyaw=D(-40), cpitch=0.1, hyaw=D(-7), hpitch=0.06,
              R=(-1.9, 8.2, -0.4), Rpole=(-0.7, -0.3, -0.6), L=(1.5, 8.4, 0.5), Lpole=(0.7, -0.3, -0.6),
              Rwrist=(0.0, 0.0, 0.3), Lwrist=(0.0, 0.0, -0.3))
        c.key(3, pel=(0.0, -0.7, -0.3), cyaw=D(-42), R=(-1.95, 8.15, -0.55), L=(1.5, 8.35, 0.35))
        for f in (2, 3, 4):
            c.key(f, Rext=0.0, Lext=0.0)
        c.key(4, pel=(0.0, -0.75, 0.5), pyaw=D(-20), cyaw=D(-22), cpitch=0.24, R=(-2.5, 8.4, 2.9), L=(1.9, 8.4, 4.0),
              Rpole=(-0.5, -0.7, -0.4), Lpole=(0.5, -0.7, -0.4), Rwrist=(0, 0, 0), Lwrist=(0, 0, 0))
        for f, k in ((5, 0.55), (6, 0.85)):
            c.key(f, pel=(0.0, -0.8, 0.8 + 0.1 * k), pyaw=D(-16), cyaw=D(-18), cpitch=0.28, hpitch=0.0)
        for f in (g0, g0 + 1):
            c.key(f, pel=(0.0, -0.82, 0.95), pyaw=D(-15), cyaw=D(-17), cpitch=0.3, hpitch=-0.02)
            c.fist(f, 'R', tr, 0.6); c.fist(f, 'L', tl, 0.6)
        # the fists' flight out along their lines
        sr, sl = shoulder(c.at(5), 'R'), shoulder(c.at(5), 'L')
        c.fist(5, 'R', vlerp(sr, tr, 0.72), 0.6); c.fist(5, 'L', vlerp(sl, tl, 0.72), 0.6)
        c.fist(6, 'R', vlerp(sr, tr, 0.92), 0.6); c.fist(6, 'L', vlerp(sl, tl, 0.92), 0.6)
        # a whiff: the fists reel in (9-11) and he recovers from the overreach
        # 9-10 (a catch cuts to CatchWait here): the body settles back toward the hold as the fists reel in; on a whiff
        # they come home (12) and he sags out of the reach
        c.fist(9, 'R', vlerp(sr, tr, 0.85), 0.6); c.fist(9, 'L', vlerp(sl, tl, 0.85), 0.6)
        c.fist(10, 'R', vlerp(sr, tr, 0.6), 0.6); c.fist(10, 'L', vlerp(sl, tl, 0.6), 0.6)
        c.key(9, pel=(0.0, -0.62, 0.5), pyaw=D(-18), cyaw=D(-17), cpitch=0.24)
        c.key(10, pel=(0.0, -0.58, 0.4), pyaw=D(-19), cyaw=D(-17), cpitch=0.22)
        c.key(12, pel=(0.0, -0.66, 0.35), cyaw=D(-18), cpitch=0.26, R=(-2.4, 8.2, 3.0), L=(1.9, 8.2, 4.1), Rext=0.0, Lext=0.0)
        c.key(16, pel=(0.0, -0.8, 0.3), pyaw=D(-20), cyaw=D(-21), cpitch=0.3, hpitch=0.05,
              R=(-2.5, 7.0, 2.0), Rpole=(-0.5, -0.8, -0.3), L=(2.1, 7.0, 2.8), Lpole=(0.5, -0.8, -0.3))
        c.key(22, pel=(0.0, -0.45, 0.25), pyaw=D(-23), cyaw=D(-24), cpitch=0.18, hyaw=D(-9), hpitch=0.0,
              R=add(WAIT['R'], (0.0, 0.4, 0.4)), Rpole=WAIT['Rpole'], L=add(WAIT['L'], (0.0, 0.35, 0.3)), Lpole=WAIT['Lpole'])
        c.key(27, pel=(0.0, -0.1, 0.03), cyaw=D(-25), cpitch=0.12, R=add(WAIT['R'], (0.0, 0.08, 0.08)), L=add(WAIT['L'], (0.0, 0.06, 0.05)))
    for f in range(g0 - 2, n):
        c.key(f, throw=HOLD_W, throwry=FACE)
    # the hands (Michael, 2026-09-30: "The grabs read as rocket PUNCHES, not grabs. They should probably be mostly-open-
    # palm"): chambered as fists, they open as they launch and fly out open and reaching, the fingers a little cupped,
    # and stay open on a whiff and on the return (a catch cuts to CatchWait's grip)
    launch = g0 - 1 if dash else g0 - 2
    c.hold(2, launch - 2, Rhand=FIST, Lhand=FIST)
    c.hold(launch, n - 12, Rhand=REACH, Lhand=REACH)
    c.key(n - 4, Rhand=(0, 0.2, 0, 0), Lhand=(0, 0.2, 0, 0))
    grow_keys(c, {f: 1.0 + (GRAB_PEAK[dash] - 1.0) * k for f, k in GRAB_EASE.items()}, at=g0)
    return c.keys()


def catch_cut():
    """CatchCut: the opponent breaks free and the doll is thrown off balance: the holding arm flung up, the body pushed
    back onto its heels (1-6), a wobble (6-12), and he rights himself into the idle."""
    n = 30
    c = Clip(n, start=hold_params())
    c.key(2, Lhand=OPEN, Rhand=OPEN)
    c.key(14, Lhand=(0, 0.3, 0, 0), Rhand=(0, 0.3, 0, 0))
    c.key(2, pel=(0.0, -0.5, -0.5), pyaw=D(-26), cyaw=D(-34), cpitch=-0.08, hyaw=D(-14), hpitch=-0.3,
          L=(2.2, 11.2, 1.8), Lpole=(0.8, 0.2, -0.5), R=(-2.9, 9.6, 0.4), Rpole=(-0.7, -0.2, -0.6),
          Rwrist=(0, 0, 0), Lwrist=(0, 0, 0))
    c.key(5, pel=(0.0, -0.65, -1.0), pyaw=D(-30), cyaw=D(-40), cpitch=-0.16, hyaw=D(-16), hpitch=-0.22,
          L=(2.6, 10.8, 0.6), R=(-3.1, 9.2, -0.6))
    c.key(9, pel=(0.0, -0.7, -0.85), cyaw=D(-30), cpitch=-0.02, hpitch=-0.05, L=(2.5, 9.2, 0.8), R=(-2.9, 8.6, 0.2))
    c.key(13, pel=(0.0, -0.55, -0.45), pyaw=D(-24), cyaw=D(-22), cpitch=0.16, hyaw=D(-9), hpitch=0.06,
          L=add(WAIT['L'], (0.2, 1.2, 0.4)), R=add(WAIT['R'], (-0.2, 1.3, 0.3)), Lpole=WAIT['Lpole'], Rpole=WAIT['Rpole'])
    c.key(19, pel=(0.0, -0.25, -0.1), pyaw=D(-25), cyaw=D(-26), cpitch=0.12, hpitch=0.0,
          L=add(WAIT['L'], (0.0, 0.3, 0.1)), R=add(WAIT['R'], (0.0, 0.35, 0.1)))
    c.key(25, pel=(0.0, -0.06, 0.0), cyaw=D(-25), L=add(WAIT['L'], (0.0, 0.05, 0.0)), R=add(WAIT['R'], (0.0, 0.06, 0.0)))
    return c.keys()


def pummel():
    """CatchAttack: the left hand keeps its grip; the right draws back past his ear (5-7) and jabs the finger into the
    opponent's chest with a point-blank pop (9), held (9-12), and cocks back to the hold."""
    n = 24
    q = hold_params()
    c = Clip(n, start=q, end=q)
    base_ = {k: q[k] for k in ('pel', 'pyaw', 'cyaw', 'cpitch', 'hyaw', 'hpitch', 'L')}
    c.key(3, **dict(base_, cyaw=D(-24), R=(-1.9, 9.0, 0.7), Rwrist=(0.0, 0.0, -0.3)))
    c.hold(5, 7, **dict(base_, pel=(0.0, -0.5, 0.1), cyaw=D(-30), cpitch=0.16, R=(-1.95, 9.45, -0.05), Rpole=(-0.7, 0.1, -0.7),
                        Rwrist=(0.0, 0.0, -0.4)))
    c.key(7, R=(-1.95, 9.5, -0.2))
    c.key(8, **dict(base_, pel=(0.0, -0.52, 0.4), cyaw=D(4), cpitch=0.24, R=(-1.2, 9.3, 3.2), Rpole=(-0.6, -0.7, -0.4),
                    Rwrist=(0.0, 0.0, 0.0)))
    c.hold(9, 11, **dict(base_, pel=(0.0, -0.52, 0.45), cyaw=D(10), cpitch=0.25, R=(-0.7, 9.15, 3.9),
                         Rpole=(-0.7, -0.6, -0.4)))
    c.key(10, Rwrist=(0.0, 0.0, 0.3)); c.key(9, Rwrist=(0, 0, 0)); c.key(12, Rwrist=(0.0, 0.0, 0.1))
    c.key(15, **dict(base_, cyaw=D(-12), R=(-1.5, 8.8, 2.4), Rwrist=(0.0, 0.0, -0.1)))
    for f in range(0, n + 1):
        c.key(f, throw=HOLD_W, throwry=FACE)
    grow_keys(c, PUMMEL_GROW, sides='R')
    return c.keys()


def turned(q, a):
    """a parameter dict turned by a about +Y (the whole body, as if its facing had turned)"""
    q = dict(q)
    for k in ('pyaw', 'cyaw', 'hyaw', 'Ltoe', 'Rtoe'):
        q[k] = q[k] + a
    for k in ('pel', 'R', 'L', 'Rpole', 'Lpole', 'LF', 'RF', 'Lkpole', 'Rkpole', 'throw'):
        if k in q: q[k] = roty(q[k], a)
    if 'throwry' in q: q['throwry'] += a
    return q


# ================================================================================================================ effects
def gfx(s, gid, part, off=(0.0, 0.0, 0.0), rng=(0.0, 0.0, 0.0)):
    """Script command 0x0A, GraphicEffect: common effect `gid` (EfCoData, every fighter has them) at engine part `part`,
    offset in that joint's frame and scattered by +-rng (decomp ftAction_80071028 -> ftCo_8009F834: offset x, y | z,
    range x | range y, z in 1/256 units; bone:8 useCommonBoneIDs:1 destroyOnStateChange:1)."""
    import fcmd
    bone = fcmd.PARTS.index(part) if isinstance(part, str) else part
    q = lambda v: int(round(v * 256)) & 0xFFFF
    w = fcmd.bits([(0x0A, 6), (bone, 8), (1, 1), (0, 1), (0, 1), (0, 15)])
    w += fcmd.bits([(gid, 16), (0, 16)])
    w += fcmd.bits([(q(off[0]), 16), (q(off[1]), 16)])
    w += fcmd.bits([(q(off[2]), 16), (q(rng[0]), 16)])
    w += fcmd.bits([(q(rng[1]), 16), (q(rng[2]), 16)])
    return s.raw(w)


# Common effects, sized against a radius-5 hitbox in game (director/fx_scale_lab.py; ids 1000-1103 and 1290-1305 surveyed)
FX_STAR_GLINT = 1011    # a white four-point star glint with a halo, radius ~4.5, one frame: the pop at the top of an arc
FX_STAR_RING = 1012     # a bright star in a gold ring, radius ~3.5 growing to ~6 as it fades over ~8 frames
FX_TWINKLE = 1008       # a dense scatter of little white-blue twinkles over radius ~4 that drift and linger ~20 frames
FX_SPARKLE = 1010       # a sparser scatter of twinkles, ~10 frames
FX_SPARK = 1062         # a small red spark, radius ~2, two or three frames (the rocket fist's ignition)
