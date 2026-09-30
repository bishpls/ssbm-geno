"""Geno's throws (DESIGN.md §6f): one weapon each. moves.py registers them; this module holds their animation and scripts.

    ThrowF   Rocket Fist: held at arm's length, the fist rockets off carrying them, lets go, and flies back to his wrist
    ThrowB   Hand Cannon: swung round behind him as he turns, the arm folds open into the cannon, and the launch is the shot
    ThrowHi  Star Gun salvo: popped straight up, the Star Gun points skyward and fires three small stars into them
    ThrowLw  Point-blank Finger Shot: pinned to the floor, a volley from the Finger Shot's tubes, then the knockdown bounce

The toolkit (the Clip: per-parameter key tracks on monotone cubic curves, solved every frame by IK and keyed on every
frame) is poses_ground.py's (the ground-attacks lane, geno-atk-ground e5dc4f9), copied here so the two lanes merge without
touching each other's files; fold the copies into one module once both are in. Its one change: a clip that starts on a
pose carries that pose's fingers (params_from_pose fits the hand-pose weights), so a throw leaves CatchWait's grip and
point without a pop.

The seam: every throw starts on CatchWait's frame 0 (whatever moves.py registers for CatchWait; the held opponent at
moves.HOLD_T) and ends on the idle's frame 0 (anims.base()), or, for the back throw, on the idle turned round: the script's
release reverses his facing (command 0x14, 1) and the model takes the new facing at the next action.

The held opponent rides ThrowN. The decomp names that part FtPart_TransN2 (52), but its Fighter_Part enum is one short from
part 16 on (PlCo.dat's parts table has WaistB and BustN at 16 and 17): part 52 is the table's "Throw", rig.py's ThrowN, the
joint the cast's throws animate, and the real TransN2 (part 53) carries nothing (lab: Fox follows ThrowN). ftCo_800DB368
constrains the opponent's XRotN (their hip pivot) to its position; its rotation is the opponent's own animation, the
thrower's entries 262-265 on the shared 52-node layout (VICTIMS below). On the release frame the opponent leaves from
ThrowN's position (ftCo_800DDDE4).

Frames: a script command at(n) runs on the frame the game shows animation frame n, so an event and its pose share a
number. Weight-dependent throws (his: the template's mask is 0) play at 100 / the opponent's weight: 1.33x on Fox.
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
#                  Rgrow Lgrow the fist's scale (HandN), Rtips Ltips the fingertips' (anims.apply_grow; poses_ground.py)
#   LF RF          each boot's flat-footed ankle (x, height above its flat stance, z); Ltoe Rtoe its yaw; Lheel Rheel a heel
#                  lift (radians about the ball) added to the automatic one; Lkpole Rkpole the knee's pole (0: over the toes)
#   throw throwry  ThrowN in the world (the held opponent) and its yaw     trans  TransN (root motion)
VEC = {'pel', 'R', 'L', 'Rpole', 'Lpole', 'Rwrist', 'Lwrist', 'LF', 'RF', 'Lkpole', 'Rkpole', 'throw', 'trans', 'Rhand', 'Lhand'}
#   Rhand Lhand    the fingers as weights of rig.HAND_POSES (fist, open, point, grip); all 0 is the bind pose the idle shows.
#                  Keyed in the animation rather than set by script part poses (Script.hand): the same shapes, but they
#                  blend on the move's own curves and return to the idle's bind pose by the last frame, where a part pose
#                  holds until the action changes and then snaps back
# (this module: a fifth weight, the relaxed hand every pose carries once rig.RELAXED_HAND exists (geno 80a59fb: anims.base()
# curls the fingers loosely), so a clip meets the idle's fingers exactly; without it the fifth basis is empty)
HAND_BASES = list(rig.HAND_POSES) + [getattr(rig, 'RELAXED_HAND', {j: (0.0, 0.0, 0.0) for j in rig.HAND_POSES[0]})]
FIST, OPEN, POINT, GRIP, REST = (1.0, 0, 0, 0, 0), (0, 1.0, 0, 0, 0), (0, 0, 1.0, 0, 0), (0, 0, 0, 1.0, 0), (0.0, 0, 0, 0, 0)
RELAXED = (0, 0, 0, 0, 1.0)
OPTIONAL = {'throw', 'throwry', 'trans', 'Rbar', 'Rbarw', 'Lbar', 'Lbarw', 'yrot'}
#   yrot           (this module's addition) YRotN's yaw: the whole body's turn, which the cast's back throws carry there
#                  (Fox's and Mario's end with YRotN at pi). Every other parameter is in the world, so it changes no
#                  pose; it decides which joint holds a turn at the cut into the next action (see throw_b)
#   Rbar Rbarw     (this module's addition) a weapon's barrel: HandN turned to point along Rbar (a body-frame direction),
#                  by the weight Rbarw from the forearm's own line (0) to it (1), so a Star Gun can aim up off a forearm
#                  that reaches forward past his head
ANGLES = {'pyaw', 'cyaw', 'hyaw', 'Ltoe', 'Rtoe', 'throwry'}      # tracks unwrapped between keys (turns and spins)          # untouched (the rest pose's) unless a clip keys them


REST_R = {j[0]: j[3] for j in rig.JOINTS}


def hand_weights(sol, side):
    """The fingers of a solved pose as weights of HAND_BASES (fist, open, point, grip, relaxed), fitted by least squares
    over every finger joint's rotation (the right hand mirrored, as fingers() does); REST when they sit at the bind pose.
    So a clip starting (or ending) on a pose carries its fingers."""
    joints = list(rig.HAND_POSES[0])
    if all(max(abs(a - b) for a, b in zip(sol[side + j[1:]][1], REST_R[side + j[1:]])) < 1e-6 for j in joints):
        return REST
    K = len(HAND_BASES)
    rows, rhs = [], []
    for j in joints:
        r = sol[side + j[1:]][1]
        for c in range(3):
            rows.append([HAND_BASES[k][j][c] * (-1 if side == 'R' and c < 2 else 1) for k in range(K)])
            rhs.append(r[c])
    M = [[sum(rw[i] * rw[k] for rw in rows) for k in range(K)] for i in range(K)]
    b = [sum(rw[i] * y for rw, y in zip(rows, rhs)) for i in range(K)]
    for i in range(K):                                       # Gauss-Jordan on the normal equations
        piv = max(range(i, K), key=lambda r_: abs(M[r_][i]))
        M[i], M[piv], b[i], b[piv] = M[piv], M[i], b[piv], b[i]
        if abs(M[i][i]) < 1e-9: continue
        for r_ in range(K):
            if r_ != i:
                f = M[r_][i] / M[i][i]
                M[r_] = [x - f * y for x, y in zip(M[r_], M[i])]
                b[r_] -= f * b[i]
    w = [round(b[i] / M[i][i], 4) if abs(M[i][i]) > 1e-9 else 0.0 for i in range(K)]
    if any(abs(x - 1.0) < 1e-3 for x in w) and sum(abs(x) for x in w) < 1.0 + 1e-2:
        w = [1.0 if abs(x - 1.0) < 1e-3 else 0.0 for x in w]   # an exact basis pose (the fit's noise dropped)
    return tuple(w)


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
        q[s + 'hand'] = hand_weights(sol, s)
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
    yr = q.get('yrot', 0.0)
    if abs(yr) > 1e-9: p.rot('YRotN', (0.0, yr, 0.0))
    p.move('HipN', (0.0, rig.LEG_TOP - rig.HIP_Y - DROP, 0.0))
    pa, pu = frame(q['pyaw'], q['ppitch'], q['proll'])
    p.aim('HipN', pa, pu)
    ca, cu = frame(q['cyaw'], q['cpitch'], q['croll'])
    p.aim('WaistN', ca, cu)
    p.rot('HeadN', (q['hpitch'] - 0.7 * (q['cpitch'] - 0.12), q['hyaw'] - q['cyaw'], q['hroll']))
    if 'throw' in q:                                # ThrowN hangs off YRotN: its offset in YRotN's (turned) frame
        p.move('ThrowN', roty(sub(sub(q['throw'], (0.0, rig.HIP_Y, 0.0)), pel), -yr))
        p.rot('ThrowN', (0.0, q.get('throwry', 0.0) - yr, 0.0))
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
        w = q.get(s + 'hand', REST)
        if max(abs(x) for x in w) > 1e-6:
            for j, r in fingers(s, w).items():
                p.rot(j, r)
        if abs(q[s + 'ext']) > 1e-9: p.move(f'{s}HandN', (FA + q[s + 'ext'], 0.0, 0.0))
        A.apply_grow(p, s, q.get(s + 'grow', 1.0), q.get(s + 'tips', 1.0), q.get(s + 'arm', 1.0))
        w = q.get(s + 'barw', 0.0)
        if w > 1e-4 and s + 'bar' in q:                     # the barrel off the forearm's line, toward Rbar
            fore = norm(fo_d)
            p.aim(f'{s}HandN', norm(vlerp(fore, norm(q[s + 'bar']), min(1.0, w))))
    return p


def fingers(side, w):
    """finger joint -> local rotation for pose weights w (rig.HAND_POSES blended; the right hand mirrored, as
    rig.part_poses_export does)"""
    out = {}
    for k, wk in enumerate(w):
        if abs(wk) < 1e-9: continue
        for j, r in HAND_BASES[k].items():
            if side == 'R': j, r = 'R' + j[1:], (-r[0], -r[1], r[2])
            acc = out.setdefault(j, [0.0, 0.0, 0.0])
            for i in range(3): acc[i] += wk * r[i]
    return {j: tuple(v) for j, v in out.items()}


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
        self.tracks = {}                 # param -> {frame: value}
        self.reaches = []                # (frame, side, point, tip, pole) resolved at bake
        self.fists = []                  # (frame, side, point, off, pole)
        self.free_ends = set()           # tracks whose ends keep their slope (root motion carries its speed through a cut)
        self.shots = []                  # (frame, side, point, fore, upper, tip, fit)

    def key(self, f, **kw):
        for k, v in kw.items():
            if k not in self.q0 and k not in OPTIONAL: raise KeyError(k)
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
            if max(abs(x) for x in dl) > 1.2: print(f'poses_throws: frame {f} {side} shot moves the pelvis {tuple(round(x, 2) for x in dl)}')
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
            if not ok: print(f'poses_throws: frame {f} {side} reach short by {length(sub(point, sh)) - UA - FA - tip:.2f}')
            elbow = add(sh, mul(u, UA))
            self.key(f, **{side: add(elbow, mul(v, FA)), side + 'ext': 0.0})
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
        self.reaches, self.fists, self.shots = [], [], []

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


def turned(q, a):
    """a parameter dict turned by a about +Y (the whole body, as if its facing had turned)"""
    q = dict(q)
    for k in ('pyaw', 'cyaw', 'hyaw', 'Ltoe', 'Rtoe'):
        q[k] = q[k] + a
    for k in ('pel', 'R', 'L', 'Rpole', 'Lpole', 'LF', 'RF', 'Lkpole', 'Rkpole', 'throw'):
        if k in q: q[k] = roty(q[k], a)
    if 'throwry' in q: q['throwry'] += a
    return q


# ================================================================================================================ the throws
import fcmd
from fcmd import Script, KICK, PUNCH, SWING_S, SWING_M, SWING_L

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sound'))
import wiring

SFX = dict(HANDCANNON=550002, DOUBLEPUNCH=550003, STARGUN=550004, FINGERSHOT=550009, PROJ_HIT=550008,   # moves.GE_SFX
           # the back throw's one chunky single-shot blast (Michael, 2026-09-29: SMRPG's Hand Cannon fires several big
           # shots, and 550002's cock-cock-boom read as a double shot; sound/gunfit.py shot()): its attack is its peak,
           # so cued on the BOOM frame it lands on it
           HANDCANNON_SHOT=550061)


def gfx(s, gid, part, off=(0.0, 0.0, 0.0), rng=(0.0, 0.0, 0.0), follow=False):
    """0x0A GraphicEffect: effect `gid` (the common effects, EfCoData: every fighter has them) at engine part `part` (rig
    PARTS, resolved through his parts table: useCommonBoneIDs), offset in that joint's frame. Layout per the decomp's
    spawn_gfx_0..4 (ftAction_80071028): bone:8 common:1 destroyOnStateChange:1; the id's 16 bits; offsets x, y | z,
    range x | range y, z in 1/256 units. follow keeps the effect only while the action lasts."""
    bone = fcmd.PARTS.index(part) if isinstance(part, str) else part
    fx = lambda v: int(round(v * 256)) & 0xFFFF
    w = fcmd.bits([(0x0A, 6), (bone, 8), (1, 1), (1 if follow else 0, 1), (0, 1), (0, 15)])
    w += fcmd.bits([(gid, 16), (0, 16)])
    w += fcmd.bits([(fx(off[0]), 16), (fx(off[1]), 16)])
    w += fcmd.bits([(fx(off[2]), 16), (fx(rng[0]), 16)])
    w += fcmd.bits([(fx(rng[1]), 16), (fx(rng[2]), 16)])
    return s.raw(w)


# Common effects (EfCoData, loaded for every fighter; ids surveyed from the cast's scripts, datkit script)
# (projects/geno/director/fx_survey: each one spawned in turn in front of him, filmed)
FX_FLASH = 1012         # a bright star-shaped flash in a ring, ~4 frames: the cannon's muzzle flash
FX_SMOKE = 1043         # a dark puff of smoke that drifts and fades: the cannon's smoke
FX_SPARK = 1062         # a tiny red spark: a Finger Shot tube's flash
FX_STARS = 1299         # a scatter of little blue stars: the Star Gun's muzzle
FX_IMPACT = 1030        # green spikes off the floor: Fox's and Falcon's down-throw slam
_EFGE = {}


def efge_gid(name):
    """His own effects (EfGeData.dat), by name, resolved at build time (projects/geno/fx/efge.py; ids follow the list)."""
    if not _EFGE:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fx'))
        import efge
        _EFGE.update(efge.ids())
    return _EFGE[name]


class Throw:
    """One throw: its length, release, numbers, events (forms, hand poses, shots, effects, sounds) and its clip."""

    def __init__(self, name, n, release, hit, back=False, muzzle=0.0):
        self.name, self.n, self.release, self.hit, self.back, self.muzzle = name, n, release, hit, back, muzzle
        self.shots, self.form_keys, self.events, self.cmds = [], [], {}, []

    def form(self, f, side, form):
        self.form_keys.append((f, side, form)); self.note(f, f'{side}:{form}')
        return self

    def shot(self, *frames):
        self.shots += frames
        for f in frames: self.note(f, 'shot')
        return self

    def at(self, f, label, fn):
        """a script command on frame f (fn(script))"""
        self.cmds.append((f, fn)); self.note(f, label)
        return self

    def note(self, f, label):
        self.events[f] = (self.events.get(f, '') + ' ' + label).strip()

    def forms_at(self, f):
        out = {}
        for k, side, form in sorted(self.form_keys):
            if k <= f: out[side] = form
        return out

    def script(self):
        s = Script()
        dmg, angle, kbg, wdsk, bkb = self.hit
        s.throw(0, dmg, angle, kbg, wdsk, bkb, sfx=(0, KICK))
        s.throw(1, 3, 361, 100, 0, 20, sfx=(0, KICK))       # a bystander the thrown opponent hits (the cast's: 3%)
        ev = [(f, 0, (lambda s, side=side, form=form: s.form(side, form))) for f, side, form in self.form_keys]
        ev += [(f, 1, (lambda s: s.flag())) for f in self.shots]
        ev += [(f, 2, fn) for f, fn in self.cmds]
        ev += [(self.release, 3, (lambda s: (s.release(0), s.release(1)) if self.back else s.release(0)))]
        for f, _, fn in sorted(ev, key=lambda e: (e[0], e[1])):
            if f > s.frame: s.at(f)
            fn(s)
        return s

    def keys(self, start=None):
        return self.build(start)


def kachunk(t, f, side, form):
    """A weapon form locking on: the joints rattle as the arm folds (f - 1), the form shows (f), and it locks with a
    wooden clack (f + 1): the sound half of the ka-chunk (the clip keys the arm's snap and settle)."""
    t.at(f - 1, 'ka', lambda s: s.raw(wiring.cue(wiring.ID['RATTLE'], 0x74)))
    t.form(f, side, form)
    t.at(f + 1, 'chunk', lambda s: s.raw(wiring.cue(wiring.ID['LEDGE'], 0x7F)))
    return t


def unfold(t, f, side):
    """A weapon form opening back into the hand: a rattle and the hand (f), a softer clack (f + 1)."""
    t.at(f - 1, 'ka', lambda s: s.raw(wiring.cue(wiring.ID['RATTLE'], 0x5A)))
    t.form(f, side, 'hand')
    t.at(f + 1, 'chunk', lambda s: s.raw(wiring.cue(wiring.ID['LEDGE'], 0x5A)))
    return t


def catch_wait_pose():
    """CatchWait's frame 0 as moves.py registers it: every throw starts there."""
    import moves
    return moves.MOVES['CatchWait'][1](None)[1][0][1]


def start_params(start=None):
    """The throw's first frame: CatchWait's (a Pose) unless given (a Pose or a parameter dict, for previews)."""
    if start is None: start = catch_wait_pose()
    return (start, dict(start) if isinstance(start, dict) else params_from_pose(start))


# The ground-attacks lane's CatchWait (geno-atk-ground, poses_ground.hold_params): the left hand has the opponent by the
# collar at arm's length, the right (gun) hand cocked at his chest, finger ready. The throws are designed from it (it is
# the hold they will start on once that lane is in), and throwview.py --hold ground previews them from it.
HOLD_W = add((0.0, rig.HIP_Y, 0.0), (0, -2.2 * 0.1, 0.3 * 0.1), (0, 2.4, 6.8))     # moves.HOLD_YROT + HOLD_T: (0, 8.78, 6.83)
GROUND_HOLD = dict(WAIT, pel=(0.0, -0.45, 0.25), pyaw=D(-22), cyaw=D(-16), cpitch=0.2, hyaw=D(-6), hpitch=0.04,
                   L=(1.05, 8.85, 4.05), Lpole=(0.7, -0.6, -0.4), Lwrist=(0.0, 0.0, -0.25),
                   R=(-1.75, 8.45, 1.75), Rpole=(-0.8, -0.5, -0.4), Rwrist=(0.0, 0.0, -0.2),
                   throw=HOLD_W, throwry=math.pi, Lhand=GRIP, Rhand=POINT)


def carried(keys, frames, point, offset, hold=None, blend_to=0, point_f=None):
    """Glue the held opponent (ThrowN) to a point that moves with the body: point(world mats, TransN) -> body-frame point,
    plus offset(frame) -> body-frame offset, on the given frames; with hold, eased from that fixed point (CatchWait's hold)
    onto the moving one by frame blend_to. ThrowN is a leaf under YRotN (untilted), so its local translation is the target
    less YRotN's position."""
    out = []
    for f, p in keys:
        if f in frames:
            W = world(p)
            tr = p.trans.get('TransN', (0.0, 0.0, 0.0))
            target = add(point_f(W, tr, f) if point_f else point(W, tr), offset(f))
            if hold is not None and f < blend_to:
                u = f / float(blend_to); u = u * u * (3 - 2 * u)
                target = vlerp(hold, target, u)
            y = sub(tuple(W['YRotN'][3][:3]), tr)
            d = sub(target, y)                      # into YRotN's frame (its rows are its axes in the world)
            p.move('ThrowN', tuple(dot(d, tuple(W['YRotN'][i][:3])) for i in range(3)))
        out.append((f, p))
    return out


def joint(W, name, tr, off=(0.0, 0.0, 0.0)):
    """a joint's point (off in its frame) in the body frame"""
    m = W[name]
    pt = tuple(sum((off[i] if i < 3 else 1.0) * m[i][j] for i in range(4)) for j in range(3))
    return sub(pt, tr)


# ---------------------------------------------------------------------------------------------------------------- forward
def aim_from(q, side, d, reach=UA + FA):
    """a wrist target `reach` from that side's shoulder along direction d (the arm straight, aimed), on pose q"""
    return add(shoulder(q, side), mul(norm(d), reach))


THROWF_GROW = {22: 1.0, 23: 2.8, 27: 2.6, 30: 2.4, 33: 2.0, 35: 1.6, 37: 1.2, 38: 1.0}
# The forward throw's lift (Michael, 2026-09-29: "a clear 'victim rises slightly, holding-hand rises slightly to match'
# piece before the rocket shot"): the fist's line passed over their head (throwview --line: their highest joint 2.4
# below it at the launch, their body's centre 5.7 below), so the rocket read as flying past them. The opponent's pivot
# rises from a hand below his fist to above it, on the line, and their hanging body lifts with it (Fox's victim frames
# run back from the sag to the carried pose).
GRIP_F = {0: (0.7, -1.1, 3.7), 15: (0.7, -1.1, 3.7), 19: (0.5, 1.5, 2.9), 27: (0.5, 1.5, 2.9)}


def throw_f(start=None):
    """Rocket Fist, in beats, on the right (gun) fist, the camera's side facing right. The right hand takes the held
    opponent by the collar from the left (1-4) and sets them at arm's length, aimed a little up (4-8), and holds them
    there a beat (8-11); the fist locks into the rocket, jolting back and snapping home with a clack (11-15); the lift:
    he straightens and hoists them up onto the fist's line, the arm rising with them, held a beat (15-20); the prime:
    the left hand clamps on the right forearm, the fist draws back down its line and he sinks to brace (21-22);
    ignition (23): a flash behind the fist and it blasts off down the forearm carrying them, the recoil driving him
    back onto his heels, held at its peak (25-29); it lets them go at full reach (27) and hangs, then flies back and
    docks on the wrist with a clack (38), the arm giving with it; the rocket opens back into the hand (41) and he
    settles."""
    t = THROWS['ThrowF']
    st, q0 = start_params(start)
    n = t.n
    c = Clip(n, start=st)
    aim = (-0.1, math.sin(D(22)), math.cos(D(22)))       # the fist's line: up 22 degrees, a touch across to his right
    lift = (-0.1, math.sin(D(27)), math.cos(D(27)))      # the arm raised with them on the lift
    set_ = dict(pel=(0.0, -0.75, -0.25), pyaw=D(-12), cyaw=D(8), cpitch=0.04, croll=0.0, hyaw=D(-4), hpitch=0.06,
                L=(2.3, 7.9, -0.9), Lpole=(0.5, -0.4, -0.8), Lwrist=(0.0, 0.0, -0.2), Rwrist=(0.0, 0.0, 0.0),
                Rpole=(-0.8, -0.5, -0.3))
    c.key(2, pel=(0.0, -0.6, 0.1), pyaw=D(-18), cyaw=D(-4), cpitch=0.14, R=(-1.2, 8.9, 3.6), Rpole=(-0.8, -0.6, -0.3))
    arm = lambda f, back=0.0, d=aim: c.key(f, R=aim_from(c.at(f), 'R', d, UA + FA - back))
    c.key(6, **set_); arm(6, 0.2)
    c.key(8, **dict(set_, pel=(0.0, -0.78, -0.22))); arm(8, 0.1)
    c.key(11, **dict(set_, pel=(0.0, -0.8, -0.2), hpitch=0.08)); arm(11, 0.1)            # the hold
    c.key(12, **dict(set_, pel=(0.0, -0.84, -0.28))); arm(12, 0.55)                     # ka: the fist jolts back ...
    c.key(13, **dict(set_, pel=(0.0, -0.8, -0.18))); arm(13, -0.15)                     # ... and snaps home (chunk)
    c.key(15, **dict(set_, pel=(0.0, -0.82, -0.22))); arm(15, 0.1)
    # the lift: up out of the crouch, the chest opening, the arm rising with them; held a beat at the top
    risen = dict(set_, pel=(0.0, -0.42, -0.12), cpitch=-0.04, hpitch=0.0, Lheel=0.25, Rheel=0.2)
    c.key(18, **dict(risen, pel=(0.0, -0.46, -0.14))); arm(18, 0.05, lift)
    c.key(20, **risen); arm(20, 0.05, lift)
    # the prime: the fist (and they with it) draws back 1.2 down its line as the left hand clamps on, and he sinks to brace
    brace = dict(set_, pel=(0.0, -0.72, -0.08), pyaw=D(-10), cyaw=D(12), cpitch=0.1, hpitch=0.1, Lheel=0.0, Rheel=0.0)
    c.key(21, **dict(risen, pel=(0.0, -0.5, -0.3))); arm(21, 1.2, lift)
    c.key(22, **brace); arm(22, 0.9, lift)
    recoil = dict(set_, pel=(0.0, -0.6, -1.15), pyaw=D(-16), cyaw=D(-6), cpitch=-0.24, hpitch=-0.18, hyaw=D(-2))
    c.key(23, **dict(brace, pel=(0.0, -0.66, -0.45))); arm(23, 0.2, lift)
    for f in (25, 29):
        c.key(f, **recoil); arm(f, 0.0, lift)
    c.key(33, **dict(set_, pel=(0.0, -0.75, -0.7), cyaw=D(2), cpitch=-0.1, hpitch=0.0)); arm(33)
    c.key(37, **dict(set_, pel=(0.0, -0.8, -0.45), cyaw=D(6), cpitch=0.0)); arm(37)
    c.key(39, **dict(set_, pel=(0.0, -0.82, -0.62), cyaw=D(3), cpitch=-0.06)); arm(39, 0.6)   # the dock knocks the arm back
    c.key(41, **dict(set_, pel=(0.0, -0.75, -0.45))); arm(41, 0.35)
    c.key(46, pel=(0.0, -0.4, -0.12), pyaw=D(-22), cyaw=D(-18), cpitch=0.1, hyaw=D(-9), hpitch=0.02,
          R=add(WAIT['R'], (-0.2, 1.3, 1.2)), Rpole=WAIT['Rpole'], L=add(WAIT['L'], (0.0, 0.4, 0.2)), Lpole=WAIT['Lpole'],
          Rwrist=WAIT['Rwrist'], Lwrist=WAIT['Lwrist'])
    c.key(51, pel=(0.0, -0.06, 0.0), pyaw=D(-25), cyaw=D(-25), cpitch=0.12, R=add(WAIT['R'], (0.0, 0.1, 0.08)),
          L=add(WAIT['L'], (0.0, 0.04, 0.0)))
    # the left hand braces the right forearm for the shot (21-29), then lets go
    for f in (22, 23, 25, 29):
        q = c.at(f)
        grip = add(joint(world(assemble(q)), 'RArmJ', (0.0, 0.0, 0.0), (0.9, 0.0, 0.0)), (0.35, -0.4, 0.0))
        c.key(f, L=grip, Lpole=(0.6, -0.6, -0.4))
    c.key(33, L=(2.2, 8.0, 0.4))
    # the fist's flight down the forearm: the burn (an accelerating launch), the hang at full reach, the return (ease in
    # and out) and the dock
    for f, e in ((0, 0.0), (22, 0.0), (23, 0.4), (24, 1.6), (25, 3.6), (26, 6.0), (27, 8.6), (28, 9.8), (29, 10.2),
                 (30, 10.3), (31, 10.0), (33, 8.4), (35, 5.2), (37, 1.8), (38, 0.0), (n, 0.0)):
        c.key(f, Rext=e)
    # the rocket fist grows as it ignites and holds its size while it carries them out (poses_ground.FS_GROW: Double
    # Punch's peak and shape), easing home on the return, back to 1 as it docks
    for f, g in THROWF_GROW.items():
        c.key(f, Rgrow=g)
    c.hold(0, 1, Lhand=q0['Lhand'], Rhand=q0['Rhand'])
    c.key(3, Lhand=OPEN)
    c.hold(3, 37, Rhand=GRIP)
    c.hold(21, 30, Lhand=GRIP)
    c.key(34, Lhand=OPEN)
    c.key(42, Rhand=OPEN)
    c.key(47, Lhand=(0, 0.2, 0, 0, 0.8 * RELAXED[4]), Rhand=(0, 0.2, 0, 0, 0.8 * RELAXED[4]))
    keys = c.keys()
    # the opponent: from CatchWait's hold point onto the right fist's grip by frame 4 (their chest a hand past his fist:
    # held at arm's length), then lifted onto the fist's line (15-19) and riding it to the release
    gf = sorted(GRIP_F)
    grip = [pchip(gf, [GRIP_F[k][i] for k in gf]) for i in range(3)]
    return carried(keys, range(1, t.release + 1), lambda W, tr: joint(W, 'RHandN', tr),
                   lambda f: tuple(g(f) for g in grip), hold=q0['throw'], blend_to=4)


THROWS = {}
THROWS['ThrowF'] = t = Throw('ThrowF', 55, 27, hit=(8, 35, 70, 0, 64))
kachunk(t, 12, 'R', 'rocket')
t.at(21, 'prime', lambda s: s.raw(wiring.cue(wiring.ID['RATTLE'], 0x50)))     # the fist drawn back: a soft rattle
unfold(t, 41, 'R')
# The ignition is the Rocket Fist's own launch (Michael, 2026-09-29: "We should remove the explosion effect from fthrow"):
# a small white four-point star at the wrist (efge ROCKET_LAUNCH), and the exhaust an unbroken trail behind the flying
# fist (moves.exhaust_trail, as Double Punch's), out (23-27, to the release) and back (33-37, docked 38). No cannon-style
# flash, smoke or sparks.
ROCKET_OUT, ROCKET_BACK = range(23, 28), range(33, 38)
_TAILS = {}


def rocket_tails():
    """The rocket fist's tail each frame of the forward throw, on TopN (x depth, y up, z forward): its exhaust ring, 0.3
    behind HandN down the bone, scaled with the fist as the engine scales an offset on a joint (moves.fist_tails'
    rule for Double Punch), from the throw's own animation."""
    if not _TAILS:
        for f, p in THROWS['ThrowF'].keys():
            if f not in ROCKET_OUT and f not in ROCKET_BACK and f + 1 not in ROCKET_BACK: continue
            W = rig.world_mats(pose={k: dict(t=v[0], r=v[1], s=p.scale.get(k)) for k, v in p.solve().items()})
            _TAILS[f] = tuple(rig.xform((-0.3, 0.0, 0.0), W['RHandN']))
    return _TAILS


def _exhaust(s, f):
    import moves                                           # (moves registers the throws: imported when the scripts build)
    tails = rocket_tails()
    moves.exhaust_trail(s, None if f == ROCKET_OUT[0] else tails[f - 1], tails[f])


t.at(23, 'ignition', lambda s: (s.sound(SFX['DOUBLEPUNCH'], behavior=0), gfx(s, efge_gid('ROCKET_LAUNCH'), 'RHandN', (-0.5, 0, 0))))
for _f in list(ROCKET_OUT) + list(ROCKET_BACK):
    t.at(_f, 'exhaust', lambda s, f=_f: _exhaust(s, f))
t.at(27, 'swing', lambda s: s.sound(SWING_L))
t.at(38, 'dock', lambda s: s.raw(wiring.cue(wiring.ID['LEDGE'], 0x7F)))
t.build = throw_f


# ---------------------------------------------------------------------------------------------------------------- up
def throw_hi(start=None):
    """Star Gun salvo, in beats. He sinks and gets both hands under the held opponent (1-3) and heaves them up (4-8), onto
    his left hand overhead (9), the right letting go; the right arm cocks and snaps up into the Star Gun beneath them,
    which locks with a clack (9-11), the forearm up and out past his face and the barrel skyward; the aim, held (11-15:
    Michael, 2026-09-29, "a brief pose establishing the arm cannon position, then followed by the star shots"), sighting
    up the barrel at them, a tense on 15; the left hand pops them up off his fingertips (16, the release) and the stars
    chase them up at once (17, 20, 23: Michael, 2026-09-29, the salvo should "reliably link (with simple DI at least)"
    at low percents, so the aim comes before the release, not after), each kicking the barrel and the body; he holds
    the gun up on them, lowers it (33-39), it folds back into the hand (40) and he settles."""
    t = THROWS['ThrowHi']
    st, q0 = start_params(start)
    n = t.n
    rel = t.release
    c = Clip(n, start=st)
    c.key(3, pel=(0.0, -1.4, 0.2), pyaw=D(-20), cyaw=D(-14), cpitch=0.36, hpitch=0.16, hyaw=D(-6),
          L=(0.9, 7.3, 3.7), Lpole=(0.7, -0.6, -0.3), R=(-0.7, 6.8, 3.5), Rpole=(-0.8, -0.6, -0.2),
          Lwrist=(0.0, 0.0, 0.0), Rwrist=(0.0, 0.0, 0.0))
    c.key(5, pel=(0.0, -1.3, 0.2), cpitch=0.3)
    c.key(7, pel=(0.0, -0.5, 0.05), cpitch=0.08, hpitch=-0.1, L=(0.8, 10.3, 3.7), R=(-0.8, 10.0, 3.6))
    # overhead on the left hand; the right lets go and drops to cock
    c.key(9, pel=(0.0, 0.15, -0.05), pyaw=D(-20), cyaw=D(-16), cpitch=-0.08, hpitch=-0.32,
          L=(0.6, 13.6, 2.4), Lpole=(0.8, -0.2, -0.5), R=(-1.9, 9.8, 1.6), Rpole=(-0.9, -0.5, -0.3), Lheel=0.3, Rheel=0.3)
    up = (0.0, 1.0, 0.06)                                   # the barrel: skyward, where they fly
    fore = (-0.14, 0.52, 0.84)                             # the forearm reaches up and out, clear of his face
    c.key(10, R=(-2.2, 9.3, 1.0))                          # the arm cocks as the gun forms (ka)
    c.key(11, R=add(aim_from(c.at(11), 'R', fore), (0.0, 0.25, 0.15)), Rpole=(-0.9, -0.3, -0.3))   # snaps up past its line
    c.key(12, pel=(0.0, 0.08, -0.05), cpitch=-0.12, hpitch=-0.45)                                   # locks (chunk)
    c.key(12, R=add(aim_from(c.at(12), 'R', fore), (0.0, -0.12, -0.06)))
    # the aim, held: he settles onto the gun, sighting up the barrel at them (12-14), and tenses before the pop (15)
    c.key(14, pel=(0.0, 0.05, -0.06), cpitch=-0.16, hpitch=-0.55, L=(0.6, 13.7, 2.3))
    c.key(14, R=aim_from(c.at(14), 'R', fore))
    c.key(15, pel=(0.0, -0.05, -0.02), cpitch=-0.14, hpitch=-0.52, L=(0.65, 13.2, 2.5), Lheel=0.2, Rheel=0.2)
    c.key(15, R=add(aim_from(c.at(15), 'R', fore), (0.0, -0.06, 0.03)))
    # the pop (release): up onto his toes, the left arm flicking them up off his fingertips, and following through
    c.key(rel, pel=(0.0, 0.3, -0.1), cpitch=-0.14, hpitch=-0.55, L=(0.55, 14.3, 2.1), Lheel=0.4, Rheel=0.35)
    c.key(rel + 2, pel=(0.0, 0.1, -0.1), L=(0.9, 12.6, 2.1), Lheel=0.15, Rheel=0.15)
    c.key(rel + 7, pel=(0.0, -0.3, -0.05), cpitch=-0.12, hpitch=-0.58, L=(2.3, 9.4, 0.7), Lpole=(0.8, -0.4, -0.4),
          Lheel=0.0, Rheel=0.0)
    c.key(10, Rbar=up, Rbarw=0.0)
    c.key(11, Rbar=up, Rbarw=1.0)
    for sh in t.shots:                                    # each shot kicks the barrel down and back, the body dips
        q = c.at(sh)
        a = aim_from(q, 'R', fore)
        c.key(sh, pel=q['pel'], R=a)
        c.key(sh + 1, pel=add(q['pel'], (0.0, -0.32, -0.16)), R=add(a, (0.0, -0.5, -0.45)))
        c.key(sh + 2, pel=add(q['pel'], (0.0, -0.1, -0.05)), R=add(a, (0.0, -0.12, -0.1)))
    # the gun held up on them as they fly (the eyes following them up), then lowered
    last = t.shots[-1]
    c.key(last + 3, Rbarw=1.0)
    c.key(last + 8, pel=(0.0, -0.3, 0.0), cpitch=-0.18, hpitch=-0.7, R=add(aim_from(c.at(last + 8), 'R', fore), (0.0, 0.1, 0.0)))
    c.key(38, Rbarw=0.0)
    c.key(35, pel=(0.0, -0.3, 0.0), cpitch=-0.02, hpitch=-0.3, R=add(aim_from(c.at(35), 'R', fore), (0.0, -0.4, -0.2)))
    c.key(39, pel=(0.0, -0.35, 0.0), cpitch=0.06, hpitch=-0.05, R=(-2.1, 10.2, 2.0), L=add(WAIT['L'], (0.2, 0.5, 0.2)))
    c.key(44, pel=(0.0, -0.22, 0.0), pyaw=D(-23), cyaw=D(-22), cpitch=0.1, hpitch=0.0, R=add(WAIT['R'], (-0.3, 1.0, 0.7)),
          Rpole=WAIT['Rpole'], Lpole=WAIT['Lpole'])
    c.key(49, pel=(0.0, -0.05, 0.0), cyaw=D(-25), cpitch=0.12, R=add(WAIT['R'], (0.0, 0.1, 0.06)), L=add(WAIT['L'], (0.0, 0.03, 0.0)))
    c.hold(0, 1, Lhand=q0['Lhand'], Rhand=q0['Rhand'])
    c.key(3, Rhand=OPEN)
    c.hold(4, rel + 1, Lhand=OPEN)
    c.hold(4, 8, Rhand=OPEN)
    c.hold(10, 37, Rhand=FIST)
    c.key(44, Lhand=(0, 0.2, 0, 0, 0.8 * RELAXED[4]), Rhand=(0, 0.2, 0, 0, 0.8 * RELAXED[4]))
    keys = c.keys()
    # the opponent: from the hold onto both hands (their hips on his palms) by frame 3, heaved up, onto the left hand
    # alone by 9, held there through the aim, and popped up off his fingertips on the last frames (the release point is
    # high, for the flight's height: where the salvo meets them)
    both = lambda W, tr: vlerp(joint(W, 'LHandN', tr), joint(W, 'RHandN', tr), 0.5)
    left = lambda W, tr: joint(W, 'LHandN', tr)
    u = pchip([0, 7, 9], [0.0, 0.0, 1.0])
    lift = pchip([0, rel - 3, rel - 2, rel - 1, rel], [1.4, 1.4, 2.3, 4.2, 6.7])
    fwd = pchip([0, 7, 9, rel - 3, rel], [1.1, 1.1, 1.3, 1.3, 1.65])   # (the release where the old one's was: the same flight)
    return carried(keys, range(1, rel + 1), None, lambda f: (0.1, lift(f), fwd(f)),
                   hold=q0['throw'], blend_to=3,
                   point_f=lambda W, tr, f: vlerp(both(W, tr), left(W, tr), u(f)))


THROWS['ThrowHi'] = t = Throw('ThrowHi', 54, 16, hit=(4, 90, 100, 0, 86), muzzle=2.4)
t.shot(17, 20, 23)
kachunk(t, 10, 'R', 'stargun')
unfold(t, 40, 'R')
t.at(6, 'cap back', lambda s: s.cap('back', 3))
t.at(16, 'swing', lambda s: s.sound(SWING_M))
for f in t.shots:
    t.at(f, 'stars', lambda s: gfx(s, efge_gid('N_STAR_FLASH'), 'RHandN', (2.6, 0, 0)))   # geno-fx: the Star Gun's own muzzle
t.at(33, 'cap rest', lambda s: s.cap('rest', 8))
t.build = throw_hi


# ---------------------------------------------------------------------------------------------------------------- down
def throw_lw(start=None):
    """Point-blank Finger Shot, in beats. He dips (1-3) and hauls the held opponent up overhead on his left arm (4-10),
    holds them there a beat (10-12), and slams them down onto their back in front of him (12-15), crouching over them to
    pin them with the left hand, the body jolting on the impact; a beat (16-18); the right hand comes up and its fingers
    open into the Finger Shot's tubes with a clack (19-22); three point-blank shots (24, 28, 32), each kicking his arm up;
    a beat on the smoking tubes, then the pin shoves them away (35) and they bounce into the knockdown; he stands, the
    tubes fold back (40) and he settles."""
    t = THROWS['ThrowLw']
    st, q0 = start_params(start)
    n = t.n
    c = Clip(n, start=st)
    c.key(3, pel=(0.0, -1.0, 0.05), pyaw=D(-22), cyaw=D(-18), cpitch=0.28, hpitch=0.1, L=(0.95, 7.9, 3.8),
          Lpole=(0.7, -0.6, -0.3), R=(-1.6, 8.3, 1.3), Rpole=(-0.8, -0.5, -0.4), Lwrist=(0.0, 0.0, 0.0))
    c.key(8, pel=(0.0, 0.1, -0.2), cyaw=D(-14), cpitch=-0.14, hpitch=-0.3, L=(0.8, 13.0, 2.1), Lpole=(0.8, 0.0, -0.5),
          R=(-1.9, 9.8, 0.8), Lheel=0.2, Rheel=0.1)
    c.key(10, pel=(0.0, 0.25, -0.3), cyaw=D(-13), cpitch=-0.2, hpitch=-0.36, L=(0.75, 13.4, 1.6), R=(-1.9, 10.0, 0.5), Lheel=0.3)
    c.key(12, pel=(0.0, 0.2, -0.32), cpitch=-0.22, hpitch=-0.36, L=(0.75, 13.5, 1.5), Lheel=0.3)       # the beat at the top
    c.key(14, pel=(0.0, -1.7, 0.7), cpitch=0.5, hpitch=0.25, L=(0.95, 6.5, 4.6), Lheel=0.0, Rheel=0.0)
    c.key(15, pel=(0.0, -2.5, 1.1), pyaw=D(-20), cyaw=D(-18), cpitch=0.75, hpitch=0.45, L=(0.95, 3.6, 5.0),
          Lpole=(0.7, 0.3, -0.6), R=(-1.9, 6.4, 1.6), Rpole=(-0.8, 0.3, -0.5))                       # impact
    c.key(17, pel=(0.0, -2.2, 0.95), cpitch=0.66, hpitch=0.38, L=(0.95, 3.9, 4.9))                     # the jolt settles
    c.key(18, pel=(0.0, -2.25, 0.95), cpitch=0.67)
    down = (-0.15, -0.8, 0.55)                             # the tubes aimed down at their chest
    c.key(19, R=(-2.0, 8.2, 1.2))                           # the hand comes up (ka)
    c.key(21, pel=(0.0, -2.15, 0.9), cyaw=D(-12), cpitch=0.64, hpitch=0.42)
    c.key(21, R=add(aim_from(c.at(21), 'R', down, UA + FA - 0.3), (0.0, -0.35, 0.2)), Rpole=(-0.9, 0.3, -0.4))  # snaps down
    c.key(22, R=add(aim_from(c.at(22), 'R', down, UA + FA - 0.3), (0.0, 0.1, -0.05)))                          # locks
    for sh in t.shots:
        q = c.at(sh)
        a = aim_from(q, 'R', down, UA + FA - 0.3)
        c.key(sh, pel=(0.0, -2.1, 0.9), R=a)
        c.key(sh + 1, pel=(0.0, -1.9, 0.78), R=add(a, (0.0, 0.8, -0.35)))
        c.key(sh + 2, pel=(0.0, -2.05, 0.87), R=add(a, (0.0, 0.25, -0.1)))
    c.key(34, pel=(0.0, -2.05, 0.9), cpitch=0.62, L=(0.95, 4.0, 4.9))
    c.key(35, pel=(0.0, -1.8, 0.7), cpitch=0.5, L=(1.0, 4.6, 5.5))                                      # the shove
    c.key(38, pel=(0.0, -1.4, 0.4), cpitch=0.4, hpitch=0.2, L=(1.3, 6.4, 3.6), R=(-2.0, 7.4, 1.8))
    c.key(44, pel=(0.0, -0.5, 0.12), pyaw=D(-24), cyaw=D(-23), cpitch=0.18, hpitch=0.05, L=add(WAIT['L'], (0.1, 0.5, 0.3)),
          R=add(WAIT['R'], (-0.1, 0.6, 0.4)), Lpole=WAIT['Lpole'], Rpole=WAIT['Rpole'], Rwrist=WAIT['Rwrist'], Lwrist=WAIT['Lwrist'])
    c.key(48, pel=(0.0, -0.08, 0.0), cyaw=D(-25), cpitch=0.12, L=add(WAIT['L'], (0.0, 0.06, 0.0)), R=add(WAIT['R'], (0.0, 0.06, 0.0)))
    c.hold(0, 1, Lhand=q0['Lhand'], Rhand=q0['Rhand'])
    c.hold(3, 34, Lhand=GRIP)
    c.key(36, Lhand=OPEN)
    c.hold(3, 18, Rhand=POINT)
    c.key(44, Lhand=(0, 0.2, 0, 0, 0.8 * RELAXED[4]), Rhand=(0, 0.2, 0, 0, 0.8 * RELAXED[4]))
    keys = c.keys()
    # the opponent rides the left hand up and down, then lies pinned at its heel (their chest under his palm)
    return carried(keys, range(1, t.release + 1), lambda W, tr: joint(W, 'LHandN', tr),
                   lambda f: (-0.8, -0.6, 2.0), hold=q0['throw'], blend_to=4)


THROWS['ThrowLw'] = t = Throw('ThrowLw', 52, 35, hit=(2, 40, 50, 0, 80), muzzle=1.6)
t.shot(24, 28, 32)
kachunk(t, 20, 'R', 'fshot')
unfold(t, 40, 'R')
t.at(8, 'swing', lambda s: s.sound(SWING_S))
t.at(15, 'slam', lambda s: (gfx(s, FX_IMPACT, 'TopN', (0, 0, 5.0)), s.raw(wiring.cue(wiring.ID['LAND_HEAVY'], 0x7F)), s.sound(0x9)))
for f in t.shots:
    t.at(f, 'spark', lambda s: gfx(s, FX_SPARK, 'RHandN', (1.7, 0, 0)))
t.at(35, 'shove', lambda s: s.sound(SWING_S))
t.build = throw_lw


# ---------------------------------------------------------------------------------------------------------------- back
def at_mouth(W, tr, reach=5.2):
    """the held opponent's pivot out past the left forearm's end: held by the collar at arm's length (their chest a hand
    beyond his fingers), then against the Hand Cannon's mouth (its barrel runs down the forearm, ArmJ, and ends ~3 past the
    elbow); `reach` down the forearm from the elbow, their hips 2.7 below"""
    return add(joint(W, 'LArmJ', tr, (reach, 0.0, 0.0)), (0.0, -2.7, 0.0))


def throw_b(start=None):
    """Hand Cannon, in two beats: the move, then the blast.
    The move: a counter-turn to wind up (1-3), then he spins round to his left in a hop (4-12), the held opponent swung
    wide at the end of his straight left arm, rising as they come round, and brought up short in front of him, held at
    arm's length by the collar (13-19).
    The blast: the arm folds open into the wood-and-brass cannon, drawn back a touch and snapped forward to lock with a
    clack, its mouth against their chest (20-24); the right hand clamps under the barrel and he braces, the barrel
    lifting onto its 35 degrees (24-29); the prime (Michael, 2026-09-29: "prime the hit, then deliver the blast"): he
    rocks back, drawing the barrel off their chest with a rattle (30), and rams it home with a clack (31), a beat;
    BOOM (33): the release is the shot, a flash and smoke at the muzzle and the boom, the recoil kicking the barrel up
    and driving him back onto his heels, held a beat at its peak (33-37). He lowers it, folds the cannon back into the
    hand (48) and settles into the idle turned round (the facing the release reversed)."""
    t = THROWS['ThrowB']
    st, q0 = start_params(start)
    n = t.n
    # the idle turned round, the turn carried by YRotN (the cast's back throws end with YRotN at pi): the engine blends
    # into Wait1 over 6 frames from the last pose's joints, and the release's reversed facing takes the model round at the
    # cut, so only a turn on YRotN (which the flip replaces) meets the idle; a turn held on the hips would spin back
    end = dict(turned(wait(), math.pi), yrot=math.pi)
    aim = lambda deg: roty((0.0, math.sin(D(deg)), math.cos(D(deg))), math.pi)      # up `deg` toward the new front

    def clip(swing=None):
        c = Clip(n, start=st, end=end)
        c.key(0, yrot=0.0)
        c.key(12, yrot=math.pi)                            # (no pose changes: the world parameters compensate)
        yaws = [(3, D(-36), D(-32)), (5, D(-10), D(10)), (7, D(45), D(75)), (9, D(105), D(132)), (11, D(145), D(160)),
                (13, D(156), D(166)), (19, D(158), D(164)), (29, D(160), D(166)), (32, D(160), D(166)), (37, D(162), D(170)),
                (47, D(157), D(160))]
        for f, py, cy in yaws:
            c.key(f, pyaw=py, cyaw=cy, hyaw=cy + D(6))
        c.key(3, pel=(0.0, -0.85, 0.1), cpitch=0.24, hpitch=0.08, R=(-1.8, 8.2, 1.1))
        c.key(5, pel=(0.0, -0.4, 0.0), cpitch=0.1, croll=D(-8))
        c.key(7, pel=(0.0, 0.35, 0.0), cpitch=0.02, croll=D(-12))    # the hop, leaning out against the swing
        c.key(9, pel=(0.0, 0.3, 0.0), croll=D(-10))
        c.key(12, pel=(0.0, -0.8, 0.0), cpitch=0.14, croll=0.0)     # landed, turned, braking the swing
        c.key(14, pel=(0.0, -0.6, 0.0), cpitch=0.08)
        c.key(19, pel=(0.0, -0.55, 0.0), cpitch=0.1)
        # the feet turn with the hips through the hop: each frame of 4..12 its idle place turned by the hips' yaw so far
        py0 = q0['pyaw']
        cv = c.curves()
        for f in range(4, 13):
            th = c.at(f, cv)['pyaw'] - py0
            lift = max(0.0, math.sin(math.pi * (f - 4) / 8.0)) * 0.9
            for sd in 'LR':
                x, _, z = roty(q0[sd + 'F'], th)
                c.key(f, **{sd + 'F': (x, lift, z), sd + 'toe': q0[sd + 'toe'] + th})
        for sd in 'LR':
            c.key(13, **{sd + 'F': end[sd + 'F'], sd + 'toe': end[sd + 'toe']})
        # the left arm: straight at them through the swing; brought up short in front (13), held; the ka-chunk; the aim
        if swing:
            for f, pt in swing.items():
                q = c.at(f)
                sh = shoulder(q, 'L')
                d = sub(add(pt, (0.0, 2.7, 0.0)), sh)          # reaching for their chest
                c.key(f, L=add(sh, mul(norm(d), min(UA + FA - 0.1, length(d) - 0.7))),
                      Lpole=roty((0.6, -0.6, -0.4), q['cyaw']), Lwrist=(0.0, 0.0, 0.0))
        for f, deg, reach in ((13, 22, UA + FA - 0.1), (15, 26, UA + FA - 0.2), (19, 25, UA + FA - 0.2),
                              (20, 24, UA + FA - 0.75), (21, 28, UA + FA + 0.0), (22, 26, UA + FA - 0.25),
                              (24, 27, UA + FA - 0.1), (26, 33, UA + FA - 0.1), (29, 35, UA + FA - 0.1),
                              (30, 36, UA + FA - 0.3), (31, 35, UA + FA + 0.05), (32, 35, UA + FA + 0.0)):   # the prime
            c.key(f, L=aim_from(c.at(f), 'L', aim(deg), reach), Lpole=(0.0, -0.5, 0.8), Lwrist=(0.0, 0.0, 0.0))
        c.key(24, pel=(0.0, -0.8, -0.2), cpitch=0.16, hpitch=0.05)       # braced
        c.key(29, pel=(0.0, -0.9, -0.3), cpitch=0.2, hpitch=0.08)
        c.key(30, pel=(0.0, -0.78, 0.8), cpitch=-0.04, hpitch=-0.02)                 # the prime: rocked back ...
        c.key(31, pel=(0.0, -0.97, -0.45), cpitch=0.24, hpitch=0.1)                  # ... rammed home ...
        c.key(32, pel=(0.0, -0.95, -0.36), cpitch=0.22, hpitch=0.1)                  # ... and braced a beat
        # BOOM: the recoil, held a beat at its peak, then the recovery
        c.key(34, pel=(0.0, -0.95, 1.2), cpitch=-0.28, hpitch=-0.3)
        c.key(34, L=aim_from(c.at(34), 'L', aim(68), UA + FA - 0.4))
        c.key(37, pel=(0.0, -1.0, 1.35), cpitch=-0.3, hpitch=-0.28)
        c.key(37, L=aim_from(c.at(37), 'L', aim(72), UA + FA - 0.45))
        c.key(41, pel=(0.0, -0.85, 0.9), cpitch=-0.12, hpitch=-0.1)
        c.key(41, L=aim_from(c.at(41), 'L', aim(50), UA + FA - 0.6))
        c.key(46, pel=(0.0, -0.6, 0.4), cpitch=0.04, hpitch=0.0, L=roty((2.2, 8.4, 1.6), math.pi), Lpole=roty((0.8, -0.5, -0.4), math.pi))
        c.key(52, pel=(0.0, -0.2, 0.08), cpitch=0.12, L=add(end['L'], (0.0, 0.35, 0.0)), Lpole=end['Lpole'],
              R=add(end['R'], (0.0, 0.25, 0.0)), Rpole=end['Rpole'])
        # the right arm flung out to balance the spin, then clamped under the barrel for the shot, flung by the recoil
        c.key(7, R=roty((-2.6, 8.8, -1.6), c.at(7)['cyaw']), Rpole=roty((-0.6, -0.5, -0.6), c.at(7)['cyaw']))
        c.key(13, R=roty((-2.3, 8.0, 0.4), math.pi + D(8)), Rpole=roty((-0.7, -0.5, -0.5), math.pi))
        c.key(20, R=roty((-2.1, 8.2, 0.9), math.pi + D(8)))
        for f in (24, 29, 32):
            qq = c.at(f)
            under = add(joint(world(assemble(qq)), 'LArmJ', (0.0, 0.0, 0.0), (1.4, 0.0, 0.0)), (0.0, -0.55, 0.0))
            c.key(f, R=under, Rpole=roty((-0.9, -0.6, 0.2), math.pi))
        c.key(35, R=roty((-2.6, 9.2, -0.4), math.pi + D(10)))
        # the muzzle's locator: the left hand, hidden inside the cannon from 21 to 44, turned about and slid out to the
        # muzzle, so an effect that trails behind its joint (the smoke) pours out of the barrel
        c.hold(21, 46, Lwrist=(0.0, math.pi, 0.0), Lext=1.2)
        c.key(20, Lwrist=(0.0, 0.0, 0.0), Lext=0.0)
        c.key(47, Lwrist=(0.0, 0.0, 0.0), Lext=0.0)
        c.hold(0, 1, Lhand=q0['Lhand'], Rhand=q0['Rhand'])
        c.hold(3, 19, Lhand=GRIP, Rhand=OPEN)
        c.hold(23, 33, Rhand=GRIP)
        c.key(36, Rhand=OPEN)
        c.key(49, Lhand=OPEN)
        c.key(53, Lhand=(0, 0.2, 0, 0, 0.8 * RELAXED[4]), Rhand=(0, 0.2, 0, 0, 0.8 * RELAXED[4]))
        return c

    # the swing's path: bearing round him (0 in front, turning to his left), distance from his axis and height, from the
    # hold to where the arm brings them up short in front (frame 13)
    c = clip()
    k13 = c.keys()[13][1]
    m13 = at_mouth(world(k13), k13.trans.get('TransN', (0.0, 0.0, 0.0)))
    polar = lambda p: (math.atan2(p[0], p[2]), math.hypot(p[0], p[2]), p[1])
    b0, r0, h0 = polar(q0['throw'])
    b1, r1, h1 = polar(m13)
    b1 += TAU * round((D(175) - b1) / TAU)
    pk = [(0, b0, r0, h0), (3, D(-10), 6.6, 8.5), (5, D(28), 8.0, 9.0), (7, D(90), 8.8, 9.8), (9, D(140), 8.6, 10.2),
          (11, D(172), 7.8, 9.8), (13, b1, r1, h1)]
    fr = [k[0] for k in pk]
    cb, cr, ch = (pchip(fr, [k[i] for k in pk], False) for i in (1, 2, 3))
    swing = {f: (cr(f) * math.sin(cb(f)), ch(f), cr(f) * math.cos(cb(f))) for f in range(1, 13)}
    c = clip(swing)
    keys = c.keys()
    ks = carried(keys, range(1, 13), lambda W, tr: (0.0, 0.0, 0.0), lambda f: swing[f])
    # the barrel shoves into their chest as it locks; on the prime it draws back off them, leaving them hanging where
    # they were (29), then rams home into them, a touch further
    reach = pchip([13, 21, 23, 29, 31, 33], [5.2, 5.2, 6.3, 6.2, 6.3, 6.25])
    k29 = dict(ks)[29]
    hung = at_mouth(world(k29), k29.trans.get('TransN', (0.0, 0.0, 0.0)), reach(29))
    return carried(ks, range(13, t.release + 1), lambda W, tr: (0.0, 0.0, 0.0), lambda f: (0.0, 0.0, 0.0),
                   point_f=lambda W, tr, f: hung if f == 30 else at_mouth(W, tr, reach(f)))


THROWS['ThrowB'] = t = Throw('ThrowB', 59, 33, hit=(10, 35, 75, 0, 62), back=True)
kachunk(t, 21, 'L', 'cannon')
t.at(30, 'prime', lambda s: s.raw(wiring.cue(wiring.ID['RATTLE'], 0x50)))     # drawn back: a soft rattle ...
t.at(31, 'ram', lambda s: s.raw(wiring.cue(wiring.ID['LEDGE'], 0x60)))        # ... rammed home: a clack
unfold(t, 48, 'L')
t.at(5, 'swing', lambda s: s.sound(SWING_L))
t.at(12, 'land', lambda s: s.raw(wiring.cue(wiring.ID['LAND'], 0x70)))
t.at(32, 'cap back', lambda s: s.cap('back', 1))
t.at(33, 'BOOM', lambda s: (s.sound(SFX['HANDCANNON_SHOT'], behavior=0), gfx(s, FX_FLASH, 'LArmJ', (3.3, 0, 0)),
                            gfx(s, FX_SMOKE, 'LHandN')))
t.at(36, 'smoke', lambda s: gfx(s, FX_SMOKE, 'LHandN'))
t.at(43, 'cap rest', lambda s: s.cap('rest', 8))
t.build = throw_b


# ================================================================================================================ the victims
# What the opponent plays while Geno throws them: his action entries 262-265, animations on the shared 52-node layout
# (PlCo.dat's "Taro" parts, kind 0x21) that any fighter plays, from the throw's first frame at the throw's speed (so a
# victim's frame n is the throw's frame n). The template's are Mario's (TMarioThrow*), timed and posed to Mario's throws.
# Each of Geno's takes the cast member's whose motion fits it (Fox's forward, up and down throws are the rocket ride,
# the toss and the pin, near enough frame for frame), copied at build time from that fighter's AJ file on the disc (game
# data stays on the disc: nothing is committed), or one composed here (taro.py) from the cast's poses where none fits:
# the back throw's swing round him.
VICTIM_ENTRY = dict(ThrowF='TMarioThrowF', ThrowB='TMarioThrowB', ThrowHi='TMarioThrowHi', ThrowLw='TMarioThrowLw')


def victim_b():
    """The back throw's victim: held facing him (the cast's held pose, Mario's back throw's first frame), turned with him
    as he swings them round (the body's yaw follows ThrowN's bearing from him, so they keep facing him), pitched head-in
    and feet-out by the swing's speed, then hanging in front of the cannon's mouth for the shot."""
    import taro
    t = THROWS['ThrowB']
    held = taro.load('TMarioThrowB')[0]
    fling = taro.load('TFoxThrowF')[12]                   # carried horizontally: the legs out behind
    keys = dict(t.keys())
    bearing, prev = [], None
    for f in range(t.n + 1):
        x, _, z = joint(world(keys[min(f, t.release)]), 'ThrowN', keys[min(f, t.release)].trans.get('TransN', (0.0, 0.0, 0.0)))
        a = math.atan2(x, z)
        if prev is not None: a += TAU * round((prev - a) / TAU)
        bearing.append(a); prev = a
    c = taro.Clip(t.n, 'PlyTaro_Share_ACTION_TGenoThrowB_figatree')
    for f in range(t.n + 1):
        w = (bearing[min(f + 1, t.n)] - bearing[max(f - 1, 0)]) / 2        # the swing's speed, radians a frame
        lean = max(-0.9, min(0.9, 2.2 * w))
        k = min(1.0, abs(w) / 0.35)
        body = taro.blend(held, fling, 0.55 * k)
        c.set(f, taro.turned(body, yaw=bearing[min(f, t.release)] - bearing[0], pitch=lean))
    return c.entry()


def timed(throw, donor, pairs):
    """A cast member's victim animation retimed to one of Geno's throws: pairs of (his frame, the donor's frame), linear
    between them (the donor slerped between its frames), so its beats (the lift, the slam, the shots' jolts, the
    launch) land on his."""
    def entry():
        import taro
        fr = taro.load(donor)
        t = THROWS[throw]
        c = taro.Clip(t.n, f'PlyTaro_Share_ACTION_TGeno{throw}_figatree')
        xs, ys = [a for a, _ in pairs], [b for _, b in pairs]
        for f in range(t.n + 1):
            k = max(i for i in range(len(xs)) if xs[i] <= f or i == 0)
            if k + 1 < len(xs):
                u = ys[k] + (ys[k + 1] - ys[k]) * (f - xs[k]) / float(xs[k + 1] - xs[k])
            else:
                u = ys[-1]
            c.set(f, taro.at(fr, u))
        return c.entry()
    return entry


def victim_f():
    """The forward throw's victim: Fox's rocket ride, retimed to his beats. Fox's holds them by the collar and they sag
    (its frames 0-9: their top drops 3.4 below the pivot) before it flings them out (10-12). His: held at arm's length,
    sagging a little (to 15); on the lift the sag runs back (to Fox's frame 2, 15-19), so the body rises with the pivot;
    held there (to 22); then from the ignition blended straight into Fox's fling (its 10-12, 23-27), not back down
    through the sag."""
    import taro
    fr = taro.load('TFoxThrowF')
    t = THROWS['ThrowF']
    c = taro.Clip(t.n, 'PlyTaro_Share_ACTION_TGenoThrowF_figatree')
    held_to = 22
    u = pchip([0, 12, 15, 19, held_to], [0.0, 4.5, 5.0, 2.0, 2.5])
    held = taro.at(fr, u(held_to))
    for f in range(t.n + 1):
        if f <= held_to:
            pose = taro.at(fr, u(f))
        elif f <= t.release:
            k = (f - held_to) / float(t.release - held_to)
            pose = taro.blend(held, taro.at(fr, 9.5 + 2.5 * k), k * k * (3 - 2 * k))
        else:
            pose = taro.at(fr, 12 + 11.0 * (f - t.release) / (t.n - t.release))
        c.set(f, pose)
    return c.entry()


def victim_lw():
    """The down throw's victim: Fox's pin retimed (the lift, the slam onto their back, the lying pose: his frames 0-22 on
    Fox's 0-21), then lying still under his palm through the shots, each a flinch (a quarter of the way toward Fox's own
    jolt pose, its frame 26, and back over two frames) and so into the release. Authored 2026-09-29: Fox's frames 25-34
    roll the body over below its pivot (their middle drops ~7 units), which on his pin held them ~3.5 units into the floor
    (in game their lowest hurtbox at -4.5 to -6 over his frames 26-34; Fox's own down throw's -1 to -2) and popped them
    8 units up on the release (twice Fox's own pop)."""
    import taro
    fr = taro.load('TFoxThrowLw')
    t = THROWS['ThrowLw']
    c = taro.Clip(t.n, 'PlyTaro_Share_ACTION_TGenoThrowLw_figatree')
    u = pchip([0, 4, 10, 12, 15, 22], [0.0, 5.0, 10.0, 14.0, 16.0, 21.5])
    lying, jolt = taro.at(fr, 21.5), taro.at(fr, 26)
    flinch = {0: 0.3, 1: 0.15, 2: 0.05}
    for f in range(t.n + 1):
        if f <= 22:
            c.set(f, taro.at(fr, u(f)))
        else:
            k = max([flinch.get(f - sh, 0.0) for sh in t.shots])
            c.set(f, taro.blend(lying, jolt, k) if k else lying)
    return c.entry()


# (his frame, Fox's): Fox's up throw tosses them on its 8th, his on 16, from his left hand overhead.
VICTIM = dict(
    ThrowF=victim_f,
    ThrowHi=timed('ThrowHi', 'TMarioThrowHi', [(0, 0), (9, 4), (THROWS['ThrowHi'].release - 1, 13),
                                              (THROWS['ThrowHi'].release, 15), (THROWS['ThrowHi'].n, 18)]),
    ThrowLw=victim_lw,
    ThrowB=victim_b)


def victims(passthrough):
    """anims.json passthrough entries for the throws' victims (anims.build merges them over the template's)."""
    import taro
    out = {}
    for throw, v in VICTIM.items():
        key = next(k for k in passthrough if k.endswith(VICTIM_ENTRY[throw]))   # the action table's name for 262-265
        if callable(v):
            out[key] = v()
        else:
            file, off, size, sym = taro.find(v)
            with open(file, 'rb') as fh:
                fh.seek(off); assert sym.encode() in fh.read(size), f'{file}: {sym} is not at {off}'
            out[key] = dict(sym=sym, off=off, size=size, file=file)
    return out


def victim_poses(name):
    """the victim's pose on each frame of a throw (for throwview): {frame: taro pose}"""
    import taro
    v = VICTIM.get(name)
    if v is None: return {}
    if callable(v):
        e = v()
        poses = {}
        for f in range(e['frames'] + 1):
            pose = {}
            for n, tr in e['tracks'].items():
                r = tuple(tr['r'][f][1:])
                tt = tuple(tr['t'][f][1:]) if 't' in tr else None
                pose[int(n)] = (tt, r)
            poses[f] = pose
        return poses
    fr = taro.load(v)
    return {f: fr[min(f, len(fr) - 1)] for f in range(THROWS[name].n + 1)}
