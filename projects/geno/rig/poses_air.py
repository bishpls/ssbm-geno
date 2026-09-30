"""Geno's aerials, their landings and the specials' body motion: the production animation (moves.py keeps the scripts:
frame data, hitboxes, sounds and the flags the specials' C code polls, plus the weapon-form commands).

The motion: a few authored key poses per move (anims.Pose, world-aimed), and the motion between them made here, not by the
game. fighter-build writes linear keys, so a pose keyed every few frames moves at a constant speed between them; Melee's own
animations are Hermite splines whose easing lives in the key spacing (art/motion/MOTION_STUDY.md 2.1). So a Clip solves each
key pose to local joint rotations, interpolates them as quaternions with an ease per segment (or a Catmull-Rom spline through
neighbouring keys for arcs), lets chosen joints trail or lead their parents by a frame or two (overlap), and keys every frame.
Procedural stretches (the nair's spin, the charge's pulse) are keyed every frame from a function of time.

The style (shared with the ground attacks): a wooden puppet whose hands become weapons. Crisp 2-4 frame anticipation, the
transformation snapping on a key frame (the script's form commands), shots held through their active frames with the gun hand
kicking back, weighty recoveries, the torso turning hard into attacks with the distal segments trailing; tucked and doll-like
in the air.

Seams: every aerial starts and ends on moves.air_base() (the fall pose; one helper, so a new Fall updates them all), every
landing ends on anims.base() (Wait1 frame 0), specials start from base() or air_base() and hand off to what the engine chains
into. Frames here are animation frames; movedata and the labs pose a hitbox opened by s.at(n) on animation frame n, and shots
reach their pose a frame early and hold, so either reading of the first active frame shows the shot.
"""
import math, os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig, anims
from anims import Pose, base

NAMES = anims.NAMES
PARENT = anims.PARENT
REST = anims.REST


# ------------------------------------------------------------------------------------------------ rotations as quaternions
def _q_from_m(M):
    """3x3 row-vector rotation (rows = the local axes in world, as rig.rot_xyz) -> quaternion (w, x, y, z) of its transpose."""
    R = [[M[j][i] for j in range(3)] for i in range(3)]
    tr = R[0][0] + R[1][1] + R[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        q = (0.25 * s, (R[2][1] - R[1][2]) / s, (R[0][2] - R[2][0]) / s, (R[1][0] - R[0][1]) / s)
    elif R[0][0] > R[1][1] and R[0][0] > R[2][2]:
        s = math.sqrt(1.0 + R[0][0] - R[1][1] - R[2][2]) * 2
        q = ((R[2][1] - R[1][2]) / s, 0.25 * s, (R[0][1] + R[1][0]) / s, (R[0][2] + R[2][0]) / s)
    elif R[1][1] > R[2][2]:
        s = math.sqrt(1.0 + R[1][1] - R[0][0] - R[2][2]) * 2
        q = ((R[0][2] - R[2][0]) / s, (R[0][1] + R[1][0]) / s, 0.25 * s, (R[1][2] + R[2][1]) / s)
    else:
        s = math.sqrt(1.0 + R[2][2] - R[0][0] - R[1][1]) * 2
        q = ((R[1][0] - R[0][1]) / s, (R[0][2] + R[2][0]) / s, (R[1][2] + R[2][1]) / s, 0.25 * s)
    n = math.sqrt(sum(x * x for x in q))
    return tuple(x / n for x in q)


def _m_from_q(q):
    w, x, y, z = q
    R = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [[R[j][i] for j in range(3)] for i in range(3)]


def q_of(r):
    return _q_from_m(anims.m3(rig.rot_xyz(*r)))


def _euler(M):
    """anims.euler_xyz without its gimbal shortcut (it zeroes rz once |sin ry| > 0.9999, an error of up to ~0.8 deg there):
    the atan2 forms stay exact until cos(ry) itself vanishes."""
    ry = math.asin(max(-1.0, min(1.0, -M[0][2])))
    if math.hypot(M[0][0], M[0][1]) > 1e-9:
        return (math.atan2(M[1][2], M[2][2]), ry, math.atan2(M[0][1], M[0][0]))
    return (math.atan2(-M[2][1], M[1][1]), ry, 0.0)


def euler_near(q, prev=None):
    """The Euler XYZ angles of q, choosing among the equivalent triples ((rx, ry, rz) and (rx+pi, pi-ry, rz+pi), each up to
    2pi) the one nearest the previous frame's, so no channel jumps even where a spin passes the gimbal (ry = +-90 deg)."""
    rx, ry, rz = _euler(_m_from_q(q))
    if prev is None:
        return (rx, ry, rz)
    best = None
    for c in ((rx, ry, rz), (rx + math.pi, math.pi - ry, rz + math.pi)):
        c = tuple(v + 2 * math.pi * round((p - v) / (2 * math.pi)) for v, p in zip(c, prev))
        d = sum((a - b) ** 2 for a, b in zip(c, prev))
        if best is None or d < best[0]:
            best = (d, c)
    return best[1]


def _align(q, ref):
    return q if sum(a * b for a, b in zip(q, ref)) >= 0 else tuple(-x for x in q)


def slerp(a, b, u):
    b = _align(b, a)
    d = max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))
    if d > 0.9995:
        q = tuple(x + (y - x) * u for x, y in zip(a, b))
    else:
        th = math.acos(d)
        s0, s1 = math.sin((1 - u) * th) / math.sin(th), math.sin(u * th) / math.sin(th)
        q = tuple(s0 * x + s1 * y for x, y in zip(a, b))
    n = math.sqrt(sum(x * x for x in q))
    return tuple(x / n for x in q)


# ------------------------------------------------------------------------------------------------ easing
EASE = {
    'lin': lambda u: u,
    'in': lambda u: u * u,                           # accelerate into the key: a strike arrives at full speed
    'in3': lambda u: u * u * u,
    'out': lambda u: 1 - (1 - u) ** 2,              # decelerate into the key: follow-through, a settle
    'out3': lambda u: 1 - (1 - u) ** 3,
    'inout': lambda u: u * u * (3 - 2 * u),
    'io3': lambda u: 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2,
    'step': lambda u: 1.0 if u >= 1 else 0.0,        # hold, then snap on the key (a mechanical click)
}


class Solved:
    """A pose already solved to local (t, r) per joint: what anims.solve_keys needs from a key (its .solve()); scale: joint
    -> (x, y, z), a limb grown on its hit frames (Clip.grow)."""
    def __init__(self, d, scale=None):
        self.d = d
        self.scale = scale or {}

    def solve(self):
        return self.d


class Clip:
    """Key poses on an n-frame clip, interpolated per joint and keyed on every frame.

    key(f, pose, ease): the pose at frame f, reached from the previous key with `ease` (EASE, or 'spline': Catmull-Rom
    through the neighbouring keys, for arcs). lag: joint -> frames it trails (+) or leads (-) the clip's timing, faded out
    at both ends so the first and last frames are the keys' own."""
    def __init__(self, n, lag=None):
        self.n, self.keys, self.lag = n, [], dict(lag or {})
        self.grows = {}

    def grow(self, joint, curve):
        """A limb grown on its hit frames, as the cast's are (research/limb_scale.md): joint -> {frame: scale}, linear
        between the keys (the game's own keys are linear), 1 outside them. The growth scales everything the joint
        carries; the joint's aim is unchanged. GENO_NO_GROW builds without it."""
        import anims
        if not anims.NO_GROW: self.grows[joint] = dict(curve)
        return self

    def _grown(self, f):
        out = {}
        for j, cv in self.grows.items():
            ks = sorted(cv)
            if f <= ks[0]: v = cv[ks[0]]
            elif f >= ks[-1]: v = cv[ks[-1]]
            else:
                i = max(k for k in range(len(ks) - 1) if ks[k] <= f)
                a, b = ks[i], ks[i + 1]
                v = cv[a] + (cv[b] - cv[a]) * (f - a) / (b - a)
            if abs(v - 1.0) > 1e-6: out[j] = (v, v, v)
        return out

    def key(self, f, pose, ease='inout'):
        sol = pose.solve() if hasattr(pose, 'solve') else pose
        if not self.keys or f < self.keys[0][0]:
            self.first = sol
        self.keys.append((f, {j: (tuple(t), q_of(r)) for j, (t, r) in sol.items()}, ease))
        return self

    def hold(self, f, ease='lin'):
        """The previous key's pose again at f (a hold; with an ease it is a creep or a settle only if the poses differ)."""
        pf, pd, _ = self.keys[-1]
        self.keys.append((f, pd, ease))
        return self

    def _sample(self, j, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1][j]
        if t >= ks[-1][0]:
            return ks[-1][1][j]
        i = max(k for k in range(len(ks) - 1) if ks[k][0] <= t)
        (f0, a, _), (f1, b, ease) = ks[i], ks[i + 1]
        u = (t - f0) / ((f1 - f0) or 1)
        ta, qa = a[j]; tb, qb = b[j]
        if ease == 'spline':
            def nb(k):
                return ks[max(0, min(len(ks) - 1, k))]
            fp, P, _ = nb(i - 1); fn, N, _ = nb(i + 2)
            tp, qp = P[j]; tn, qn = N[j]
            qa2 = _align(qa, qp); qb2 = _align(qb, qa2); qn2 = _align(qn, qb2)
            h = f1 - f0
            ma = [(y - x) / ((f1 - fp) or 1) * h if i > 0 else 0.0 for x, y in zip(qp, qb2)]
            mb = [(y - x) / ((fn - f0) or 1) * h if i + 2 < len(ks) else 0.0 for x, y in zip(qa2, qn2)]
            h00, h10, h01, h11 = 2 * u ** 3 - 3 * u * u + 1, u ** 3 - 2 * u * u + u, -2 * u ** 3 + 3 * u * u, u ** 3 - u * u
            q = [h00 * x + h10 * m0 + h01 * y + h11 * m1 for x, m0, y, m1 in zip(qa2, ma, qb2, mb)]
            nq = math.sqrt(sum(x * x for x in q)); q = tuple(x / nq for x in q)
            ma = [(y - x) / ((f1 - fp) or 1) * h if i > 0 else 0.0 for x, y in zip(tp, tb)]
            mb = [(y - x) / ((fn - f0) or 1) * h if i + 2 < len(ks) else 0.0 for x, y in zip(ta, tn)]
            tt = tuple(h00 * x + h10 * m0 + h01 * y + h11 * m1 for x, m0, y, m1 in zip(ta, ma, tb, mb))
            return tt, q
        w = EASE[ease](u)
        return tuple(x + (y - x) * w for x, y in zip(ta, tb)), slerp(qa, qb, w)

    def frames(self):
        """[(frame, Solved)] for every frame 0..n."""
        self.keys.sort(key=lambda k: k[0])
        assert self.keys[0][0] == 0 and self.keys[-1][0] == self.n, (self.keys[0][0], self.keys[-1][0], self.n)
        out = []
        prev = {j: r for j, (t, r) in self.first.items()}      # frame 0 takes the first key's own angles
        big = max([abs(v) for v in self.lag.values()] + [0])
        ramp = max(2.0, 2.0 * big)
        for f in range(self.n + 1):
            env = min(1.0, f / ramp, (self.n - f) / ramp)
            d = {}
            for j in NAMES:
                t, q = self._sample(j, f - self.lag.get(j, 0.0) * env)
                r = euler_near(q, prev.get(j))
                prev[j] = r
                d[j] = (t, r)
            out.append((f, Solved(d, self._grown(f))))
        return out


# ------------------------------------------------------------------------------------------------ pose helpers
def ab():
    """The fall pose every aerial starts from and returns to: moves.air_base(), the one helper."""
    import moves
    return moves.air_base()


def world(p):
    sol = p.solve()
    return rig.world_mats(pose={k: {'t': v[0], 'r': v[1]} for k, v in sol.items()})


def pos(p, joint, off=(0, 0, 0)):
    return rig.xform(off, world(p)[joint])


def norm(v):
    l = math.sqrt(sum(x * x for x in v)) or 1.0
    return tuple(x / l for x in v)


def spin(d, th):
    """A world direction turned th radians about +Y (positive: toward his left, +X)."""
    c, s = math.cos(th), math.sin(th)
    return (d[0] * c + d[2] * s, d[1], -d[0] * s + d[2] * c)


def mix(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


_REST = {}


def rest_arm(side, air=True):
    """The upper arm's and forearm's world directions in the fall pose (air) or Wait1's (ground): where a move's arm
    starts from and returns to, so the in-betweens head straight for the pose instead of detouring through another."""
    key = (side, air)
    if key not in _REST:
        W = world(ab() if air else base())
        _REST[key] = (tuple(W[f'{side}ShoulderJ'][0][:3]), tuple(W[f'{side}ArmJ'][0][:3]))
    return _REST[key]


def setrot(p, j, r):
    p.aims.pop(j, None)
    p.local[j] = tuple(r)
    return p


def torso(p, lean=0.0, yaw=0.0, roll=0.0, hip_yaw=None, hip_lean=0.0):
    """The chest (WaistN) leaned forward (+), turned (+ toward his left) and rolled (+ his right shoulder up); the hips turn
    part of the way unless hip_yaw is given. The arms are world-aimed, so aim them after turning."""
    setrot(p, 'WaistN', (0.12 + lean, yaw * 0.6 if hip_yaw is None else yaw - hip_yaw, roll))
    setrot(p, 'HipN', (hip_lean, yaw * 0.4 if hip_yaw is None else hip_yaw, 0.0))
    return p


def head(p, yaw=0.0, pitch=0.0, roll=0.0, neck=0.4):
    """The head turned (+ his left), pitched (+ down) and rolled relative to the chest, split between the neck and head."""
    setrot(p, 'NeckN', (pitch * neck, yaw * neck, roll * neck))
    setrot(p, 'HeadN', (pitch * (1 - neck), yaw * (1 - neck), roll * (1 - neck)))
    return p


def arm_dirs(p, side, upper, fore, hand=None, up=None):
    """The arm by world directions: upper arm, forearm (the barrel of an arm form) and hand (default: along the forearm)."""
    p.aim(f'{side}ShoulderJ', norm(upper), up)
    p.aim(f'{side}ArmJ', norm(fore), up)
    if hand is not None:
        p.aim(f'{side}HandN', norm(hand), up)
    else:
        p.aims.pop(f'{side}HandN', None); p.local.pop(f'{side}HandN', None)
    return p


def arm_at(p, side, target, bend=0.0, pole=(0, -1, 0), up=None, hand=None):
    """Point the arm's line from its shoulder at a world point (a muzzle's aim): straight (bend 0), or with the elbow
    dropped toward pole by `bend` radians while the forearm still aims along the line."""
    sh = pos(p, f'{side}ShoulderJ')
    d = norm([t - s for t, s in zip(target, sh)])
    if bend:
        pl = norm([a - sum(x * y for x, y in zip(pole, d)) * b for a, b in zip(pole, d)])
        upper = norm([math.cos(bend) * a + math.sin(bend) * b for a, b in zip(d, pl)])
        return arm_dirs(p, side, upper, d, hand, up)
    return arm_dirs(p, side, d, d, hand, up)


def fold_arm(p, side, upper, fold, across=0.0, up=None):
    """A bent arm: the upper arm along `upper`, the forearm folded back toward the chest by `fold` (0 straight, 1 fully
    folded), swung `across` the body (+ toward his centre line)."""
    sx = 1 if side == 'L' else -1
    u = norm(upper)
    fwd = norm((-sx * across, 0.35, 1.0))
    fore = norm(mix(u, fwd, fold)) if fold < 1 else fwd
    return arm_dirs(p, side, u, fore, None, up)


def legs(p, l_thigh, l_shin, r_thigh, r_shin, foot=None):
    for s, th, sh in (('L', l_thigh, l_shin), ('R', r_thigh, r_shin)):
        p.aim(f'{s}LegJ', norm(th)); p.aim(f'{s}KneeJ', norm(sh))
        if foot == 'point':                  # toes pointed down along the shin (a doll in flight)
            d = norm(sh)
            p.aim(f'{s}FootJ', norm((d[0], d[1] - 0.25, d[2] + 0.9)), up=(0, -0.3, -1))
        elif foot is not None:
            p.aim(f'{s}FootJ', norm(foot), up=(0, -1, 0))
    return p


def air_tuck(p, amount=1.0, spread=0.0, lead=1.25, trail=0.7):
    """Knees drawn up by `amount` (the air_base's own is ~0.55), the left leading and the right trailing, `spread` apart."""
    for s, sx, k in (('L', 1, lead), ('R', -1, trail)):
        a = amount * k
        p.aim(f'{s}LegJ', norm((sx * (0.1 + spread), -1 + a * 0.6, 0.9 * a + 0.12 * sx)))
        p.aim(f'{s}KneeJ', norm((sx * spread * 0.5, -1, -0.4 * a)))
    return p


def lift(p, dy=0.0, dz=0.0):
    """Move the body (YRotN, the pivot above his position) up and forward: a recoil's jolt, a dip."""
    t = p.trans.get('YRotN', REST['YRotN'][0])
    p.move('YRotN', (t[0], t[1] + dy, t[2] + dz))
    return p


def chain(side, limb, frames):
    """A lag for a whole limb (every joint of it the same), so the limb stays itself while it trails the body."""
    js = {'arm': ['ShoulderJ', 'ArmJ', 'HandN'], 'leg': ['LegJ', 'KneeJ', 'FootJ'], 'fore': ['ArmJ', 'HandN']}[limb]
    return {side + j: frames for j in js}


def yaw_body(p, th):
    """Turn the whole body about the vertical through the pivot (YRotN): a spin."""
    setrot(p, 'YRotN', (0.0, th, 0.0))
    return p


# ------------------------------------------------------------------------------------------------ the move library
# Each builder returns [(frame, Solved)] for moves.py. They are filled in below, move by move.


def pitch_up(d, a):
    """A direction raised by `a` radians in its own vertical plane (a gun's kick)."""
    h = math.hypot(d[0], d[2]) or 1e-9
    el = math.atan2(d[1], h) + a
    return (d[0] / h * math.cos(el), math.sin(el), d[2] / h * math.cos(el))


def kicked(p, side, d, a, bend=0.5):
    """The gun arm along d, kicked up by a: the forearm rises most, the upper arm less (the elbow gives), the hand most."""
    arm_dirs(p, side, pitch_up(d, a * bend), pitch_up(d, a), pitch_up(d, a * 1.3))
    return p


# ------------------------------------------------------------------------------------------------ forward air
FAIR_TIP = (0.0, 7.6, 15.5)          # moves.fair's tip burst (TopN: y up, z forward): the Hand Gun's line runs through it


def fair():
    """Hand Gun forward (hit 9-11). The gun arm cocks back as the chest opens to the camera (frames 1-4, the form snapping
    on at 5), then the torso whips round and the arm shoots straight down the burst's line, a frame early (8), and holds;
    the barrel kicks up over 10-11 and settles; a weighty recovery from 18 into the fall pose by 32."""
    def body(yaw, lean, tuck_amt, hy=0.0, hp=0.0):
        p = ab()
        torso(p, lean=lean, yaw=yaw)
        head(p, yaw=hy, pitch=hp)
        air_tuck(p, tuck_amt)
        return p

    def cocked(k=1.0):
        # the gun arm drawn back like a piston: the elbow back and low, the fist at the chest, the barrel level at the target
        p = body(-0.5 * k, 0.05, 0.55 + 0.35 * k, hy=0.35 * k)
        (ru, rf), (lu, lf) = rest_arm('R'), rest_arm('L')
        arm_dirs(p, 'R', mix(ru, (-0.35, -0.55, -0.75), k), mix(rf, (0.12, -0.08, 1.0), k))
        arm_dirs(p, 'L', mix(lu, (0.25, -0.25, 0.95), k), mix(lf, (-0.05, 0.25, 1.0), k))
        return p

    def shot(kick=0.0, creep=0.0):
        p = body(0.4, 0.18 - 0.1 * kick, 0.7, hy=-0.35, hp=0.08)
        legs(p, (0.15, -0.15, 1.0), (0.05, -1.0, 0.05), (-0.1, -0.95, -0.4), (-0.05, -0.55, -0.85))
        sh = pos(p, 'RShoulderJ')
        d = norm([t - s for t, s in zip(FAIR_TIP, sh)])
        kicked(p, 'R', pitch_up(d, -creep), kick)
        arm_dirs(p, 'L', (0.35, -0.45, -0.85), (0.2, -0.75, -0.6))
        lift(p, dy=0.15 * kick, dz=-0.25 * kick)
        return p

    c = Clip(36, lag=dict(chain('L', 'arm', 1.0), **chain('L', 'leg', 1.5), **chain('R', 'leg', 2.0), HeadN=-1.5, NeckN=-1.5))
    c.key(0, ab())
    c.key(2, cocked(0.6), 'out')
    c.key(4, cocked(1.0), 'out')
    c.key(6, cocked(1.08), 'inout')          # the form snaps on here (script): a last squeeze of the coil
    c.key(8, shot(), 'in')                    # the strike arrives at speed, a frame before the first active frame
    c.key(9, shot(0.06), 'out')
    c.key(10, shot(0.26), 'out')              # the kick
    c.key(11, shot(0.34), 'out')
    c.key(13, shot(0.12), 'inout')            # settles, a touch high
    c.key(18, shot(0.05, creep=0.08), 'inout')   # the hold creeps down
    c.key(24, cocked(0.15), 'inout')          # the arm drops and the chest unwinds: weighty
    c.key(30, ab(), 'out')
    c.key(36, ab(), 'lin')
    return c.frames()


def spun_pose(p, th):
    """The whole pose turned th about the vertical through his pivot: YRotN turns, and every world aim turns with it (the
    limbs are aimed in world space, so they would otherwise stay put while the body spins under them)."""
    for j, (x, up) in list(p.aims.items()):
        p.aims[j] = (spin(x, th), spin(up, th) if up else None)
    return yaw_body(p, th)


def tilt_pose(p, a):
    """The whole pose pitched forward by a (head forward and down) about his pivot, the world-aimed limbs with it."""
    c, sn = math.cos(a), math.sin(a)
    rot = lambda v: (v[0], v[1] * c - v[2] * sn, v[1] * sn + v[2] * c)
    for j, (x, up) in list(p.aims.items()):
        p.aims[j] = (rot(x), rot(up) if up else None)
    r = p.local.get('YRotN', (0.0, 0.0, 0.0))
    return setrot(p, 'YRotN', (r[0] + a, r[1], r[2]))


def reach(p, side, target, pole=(0, -1, -0.3), grip=0.35):
    """Two-bone IK: the hand (`grip` past the wrist) on a world point, the elbow toward pole."""
    sh = pos(p, f'{side}ShoulderJ')
    up_l, lo_l = rig.UPPER_ARM, rig.FOREARM + grip
    d = [t - s for t, s in zip(target, sh)]
    dl = math.sqrt(sum(x * x for x in d)) or 1e-6
    u = [x / dl for x in d]
    L = min(dl, (up_l + lo_l) * 0.995)
    v = norm([a - sum(x * y for x, y in zip(pole, u)) * b for a, b in zip(pole, u)])
    ca = (up_l ** 2 + L ** 2 - lo_l ** 2) / (2 * up_l * L)
    sa = math.sqrt(max(0.0, 1 - ca * ca))
    elbow = [up_l * (ca * a + sa * b) for a, b in zip(u, v)]
    return arm_dirs(p, side, elbow, [L * a - e for a, e in zip(u, elbow)])


# ------------------------------------------------------------------------------------------------ neutral air
def nair():
    """The spinning doll (hits 3-6 clean, 7-20 late): a one-frame coil against the turn, the arms flung out, one full turn
    toward his right by frame 13 (his front sweeps past the camera facing right), the top opening into a split as it slows,
    the left knee low in front and the right leg low behind (the late bursts: the low-back crossup), held to 20, then the
    doll folds back into the fall. The star core rides WaistN: the body turns about his vertical and barely leans, so it
    stays where it was."""
    def coil():
        p = ab()
        air_tuck(p, 1.0)
        torso(p, lean=0.12, yaw=0.15)
        head(p, pitch=0.15)
        fold_arm(p, 'R', (-0.35, -0.55, 0.5), 0.85, 0.5)
        fold_arm(p, 'L', (0.35, -0.55, 0.5), 0.85, 0.5)
        return spun_pose(p, 0.3)

    def top(th, openk, trail, drop=0.0, split=0.0):
        """Spinning at th: the arms out (openk 0 drawn in .. 1 flung out), trailing the turn, dropping low-back as it ends;
        the legs tucked, opening into the split."""
        p = ab()
        air_tuck(p, 0.9 * (1 - split))
        torso(p, lean=0.04 + 0.16 * split)
        head(p, pitch=-0.05 + 0.05 * split)
        for s, sx, tilt in (('R', -1, 0.12), ('L', 1, -0.1)):
            out = spin((sx, tilt - 0.25 * drop, -0.45 * drop), trail * -sx)      # ending as wings, out and back
            u = norm(mix((sx * 0.35, -0.55, 0.5), out, openk))
            arm_dirs(p, s, u, norm(mix(u, spin(u, 0.35 * trail * -sx), 0.5)))
        if split:
            # a spinning back kick as the top slows: the front knee tucked up, the rear leg kicked out low behind him (the
            # low-back crossup); a split with both legs out read as a stride in the air
            legs(p, mix((0.1, -0.2, 0.9), (0.15, 0.3, 0.95), split), mix((0.0, -1.0, -0.3), (0.05, -1.0, -0.05), split),
                 mix((-0.1, -0.2, 0.3), (-0.1, -0.66, -0.75), split), mix((0.0, -1.0, -0.4), (-0.08, -0.62, -0.78), split),
                 foot='point' if split > 0.5 else None)
        return spun_pose(p, th)

    # the turn: fast off the fling, slowing into the split (radians, toward his right)
    TH = {2: -0.05, 3: -0.75, 4: -1.55, 5: -2.35, 6: -3.1, 7: -3.8, 8: -4.45, 9: -5.0, 10: -5.5, 11: -5.9, 12: -6.15,
          13: -6.283}
    c = Clip(40, lag=dict(chain('R', 'fore', 1.0), **chain('L', 'fore', 1.0), HeadN=-1.0))
    c.key(0, ab())
    c.key(1, coil(), 'out')
    for f in range(2, 14):
        k = (f - 2) / 11.0
        c.key(f, top(TH[f], min(1.0, (f - 1) / 2.0), 0.35 * (1 - k), drop=max(0.0, (f - 8) / 5.0),
                     split=max(0.0, min(1.0, (f - 7) / 5.0))), 'lin')
    c.key(15, top(-2 * math.pi - 0.06, 1.0, -0.05, drop=1.05, split=1.05), 'out')      # the last of the turn overshoots
    c.key(20, top(-2 * math.pi, 1.0, 0.0, drop=1.0, split=0.95), 'inout')
    c.key(24, top(-2 * math.pi, 0.45, 0.0, drop=0.6, split=0.25), 'inout')     # the doll folds back up, weighty
    c.key(30, spun_pose(ab(), -2 * math.pi), 'out')
    c.key(40, spun_pose(ab(), -2 * math.pi), 'lin')
    # the back kick's shin and boot grow as it lands behind him (Michael, 2026-09-29, the body-contact normals). The cast's
    # kicks fill 0.50-0.72 of their hitbox at their peak (Mario's up air, jab 3, back air); Geno's shin and boot fill 0.48
    # of the late back burst, so 1.3 (0.62, inside the cast's range). It pops on the frame the kick is fully out (12), as
    # Mario's jab fist pops, and eases back by 18: a ramp from 9 grew the shin on frame 11, the move's best back-disjoint
    # frame (3.8), and cost 0.29 of it (research/growth_cost.md); the grown shin reaches up to 0.86 further back on 12-17
    c.grow('RKneeJ', NAIR_KICK_GROW)
    return c.frames()


NAIR_KICK_GROW = {11: 1.0, 12: 1.3, 13: 1.27, 16: 1.08, 18: 1.0}


# ------------------------------------------------------------------------------------------------ back air
BAIR_TIP = (0.0, 7.5, -15.5)


def bair():
    """Hand Cannon backward (hit 10-12). The head leads round (frame 1), the chest turns to his right so the gun arm swings
    behind him and folds, elbow forward, the cannon snapping on at 6 with its muzzle already on the target; at 9 the arm
    shoves straight back down the burst's line and holds; the shot at 10 kicks the cannon up and jolts the doll forward,
    legs swinging under; he unwinds from 20 and settles into the fall by 34."""
    def turned(k, lean=0.0):
        p = ab()
        torso(p, lean=lean, yaw=-1.25 * k)
        head(p, yaw=-1.15 * k, pitch=0.05 * k)
        air_tuck(p, 0.55 + 0.4 * k)
        return p

    def loaded(k=1.0):
        p = turned(k, lean=-0.05)
        sh = pos(p, 'RShoulderJ')
        d = norm([t - s for t, s in zip(BAIR_TIP, sh)])
        ru, rf = rest_arm('R')
        upper = norm(mix(ru, (-0.2, -0.45, 0.85), k))                          # the elbow comes forward and up
        arm_dirs(p, 'R', upper, norm(mix(rf, d, k)))
        arm_dirs(p, 'L', (0.35, -0.7, 0.55), (0.25, -0.35, 0.9))
        return p

    def shot(kick=0.0, creep=0.0):
        p = turned(1.05, lean=0.22 + 0.12 * kick)
        legs(p, (0.1, -0.62, 0.78), (0.05, -0.95, 0.25), (-0.12, -0.75, 0.62), (-0.05, -1.0, 0.0))
        sh = pos(p, 'RShoulderJ')
        d = norm([t - s for t, s in zip(BAIR_TIP, sh)])
        kicked(p, 'R', pitch_up(d, -creep), kick, bend=0.35)
        arm_dirs(p, 'L', (0.3, -0.35, 0.9), (0.15, -0.05, 1.0))
        lift(p, dy=0.1 * kick, dz=0.55 * kick)
        return p

    c = Clip(38, lag=dict(chain('L', 'arm', 1.5), **chain('L', 'leg', 2.0), **chain('R', 'leg', 2.5), HeadN=-1.5, NeckN=-1.5))
    c.key(0, ab())
    c.key(3, turned(0.5), 'inout')
    c.key(6, loaded(0.85), 'out')             # the cannon snaps on (script)
    c.key(8, loaded(1.0), 'inout')
    c.key(9, shot(), 'in')                    # shoved back down the line, a frame before the first active frame
    c.key(10, shot(0.12), 'out')
    c.key(11, shot(0.42), 'out')              # the kick and the jolt forward
    c.key(12, shot(0.5), 'out')
    c.key(15, shot(0.18), 'inout')
    c.key(20, shot(0.1, creep=0.1), 'inout')
    c.key(27, turned(0.3), 'inout')           # unwinding, the arm coming round
    c.key(33, ab(), 'out')
    c.key(38, ab(), 'lin')
    return c.frames()


# ------------------------------------------------------------------------------------------------ up air
UAIR_ARC = [(4.5, 16.5), (2.0, 18.5), (-0.5, 19.0), (-3.0, 18.0), (-5.0, 16.0)]    # moves.uair's bursts, frames 5-9 (z, y)


def uair():
    """Star Gun upward (the head hitbox at 5, the burst arc 5-9 front to back). A quick gather (the gun arm drops low in
    front, knees up) and the form snapping on at 3; the arm swings up to the first burst by 5 and sweeps overhead through
    the arc, the body stretching and arching back behind it, legs kicking down; the follow-through carries it past the top
    and it folds back into the fall by 28. The head stays over the body at 5, where its hitbox rides."""
    def gather():
        p = ab()
        air_tuck(p, 0.8)
        torso(p, lean=0.2)
        head(p, pitch=0.1)
        arm_dirs(p, 'R', (-0.3, -0.85, 0.45), (-0.15, -0.6, 0.8))
        arm_dirs(p, 'L', (0.35, -0.8, 0.3), (0.2, -0.85, 0.5))
        return p

    def swing(i, arch=0.0, legs_down=0.0, extra=0.0, hp=0.0):
        """The gun arm on burst i's line (fractional i sweeps between them), the body arched back by `arch`."""
        p = ab()
        air_tuck(p, 0.55 * (1 - legs_down))
        if legs_down:
            legs(p, (0.1, -0.95, 0.45 - 0.3 * arch), (0.02, -1.0, -0.3), (-0.1, -1.0, 0.2 - 0.35 * arch), (-0.02, -1.0, -0.45))
        torso(p, lean=0.1 - arch, yaw=-0.35 * min(1.0, legs_down * 1.5), roll=0.12 * legs_down)
        head(p, pitch=hp, yaw=0.2 * legs_down)
        k = max(0.0, min(len(UAIR_ARC) - 1.0, i)); a = int(min(k, len(UAIR_ARC) - 2)); u = k - a
        z, y = mix(UAIR_ARC[a], UAIR_ARC[a + 1], u)
        sh = pos(p, 'RShoulderJ')
        d = norm((0.0, y - sh[1], z - sh[2]))
        d = norm((-0.42, d[1], d[2]))                 # out from his side: straight up it hides behind the big head
        if extra:                                     # the follow-through past the last burst, on down the back
            ph = math.atan2(d[2], d[1]) - extra
            d = norm((-0.42, math.cos(ph), math.sin(ph)))
        arm_dirs(p, 'R', d, d)
        arm_dirs(p, 'L', (0.8, -0.3, 0.45 - 0.4 * arch), (0.6, -0.55, 0.5 - 0.5 * arch))
        return p

    c = Clip(32, lag=dict(chain('L', 'arm', 1.5), **chain('L', 'leg', 1.5), **chain('R', 'leg', 2.0), HeadN=-1.0, NeckN=-1.0))
    c.key(0, ab())
    c.key(2, gather(), 'out')
    c.key(3, gather(), 'lin')                 # the Star Gun snaps on (script)
    c.key(5, swing(0, arch=0.0, legs_down=0.5, hp=-0.1), 'in')
    for f, i, ar in ((6, 1, 0.08), (7, 2, 0.16), (8, 3, 0.24), (9, 4, 0.3)):
        c.key(f, swing(i, arch=ar, legs_down=0.8, hp=-0.1 - ar), 'lin')
    c.key(11, swing(4, arch=0.36, legs_down=0.9, extra=0.35, hp=-0.45), 'out')
    c.key(13, swing(4, arch=0.34, legs_down=0.85, extra=0.42, hp=-0.4), 'out')
    c.key(17, swing(4, arch=0.28, legs_down=0.7, extra=0.38, hp=-0.3), 'inout')
    c.key(23, gather(), 'inout')
    c.key(28, ab(), 'out')
    c.key(32, ab(), 'lin')
    return c.frames()


# ------------------------------------------------------------------------------------------------ down air
DAIR_AIM = (0.0, -13.0, 1.3)         # moves.dair's blast column (TopN): the cannon points straight down its line


# ---- down air: the rocket fist (Michael, 2026-09-29: "the rocket fist design, similar to ftilt and fsmash ... long and
# disjointed ... with the meteor on the close / startup hit"). The fist fires straight down off the forearm, out to the
# old column's reach and back, as Double Punch's do. The hitboxes ride it (moves.dair: RHandN, 0.5 down the bone).
DAIR_LINE_Z = 1.8                     # the fist's vertical line, in front of him (the old column's barrel line)
DAIR_OFF = 0.5                        # the hitbox's offset down HandN (grows with the fist)
# the fist's centre (the hitbox's point) per frame, height on TopN: launched on 8, the meteor near him on 9 (the old
# muzzle's +2.0), down to -9.6 on 12 (its 3.4 tail reaches 13.0 below, the old column's reach), home by 20
DAIR_FIST_Y = {8: 4.2, 9: 1.5, 10: -3.0, 11: -7.0, 12: -9.6, 13: -9.6, 14: -8.2, 15: -5.8, 16: -3.2, 17: -0.6,
               18: 1.8, 19: 3.6}
# the fist's growth on its hit frames (Double Punch's peak, 2.8: research/fist_read.md), held while it flies out (a
# shrinking fist reads as receding), eased home as it returns
DAIR_GROW = {7: 1.0, 9: 2.8, 10: 2.8, 12: 2.6, 14: 2.4, 16: 2.0, 18: 1.5, 19: 1.25, 20: 1.0}


def _dair_grow(f):
    ks = sorted(DAIR_GROW)
    if f <= ks[0]: return DAIR_GROW[ks[0]]
    if f >= ks[-1]: return DAIR_GROW[ks[-1]]
    a = max(k for k in ks if k <= f); b = min(k for k in ks if k > f)
    return DAIR_GROW[a] + (DAIR_GROW[b] - DAIR_GROW[a]) * (f - a) / (b - a)


def dair_punch(kick=0.0, dip=0.0, fist_y=None, f=None):
    """The punch: the doll pitched forward over a straight right arm, the forearm vertical on the fist's line in front
    of his tucked legs; kick lifts the body and bends the elbow a touch (the launch's recoil, the dock's jolt). fist_y:
    the fist launched down the forearm to that height (ext on HandN), its growth for frame f."""
    p = ab()
    legs(p, (0.15, -0.9, -0.3), (0.05, -0.75, -0.65), (-0.15, -0.85, -0.45), (-0.05, -0.62, -0.78), foot='point')
    torso(p, lean=0.28 - 0.1 * kick + 0.08 * dip)
    head(p, pitch=0.3 - 0.15 * kick)
    arm_dirs(p, 'L', (0.85, -0.1, -0.5), (0.7, -0.45, -0.2))            # the free arm flung back for balance
    tilt_pose(p, 0.3 - 0.08 * kick + 0.05 * dip)
    lift(p, dy=0.7 * kick - 0.4 * dip)
    sh = pos(p, 'RShoulderJ')
    dz = max(-0.95, min(0.95, (DAIR_LINE_Z - sh[2]) / 1.8))              # the elbow onto the line (upper arm 1.8)
    dx = 0.35 * (-sh[0]) / 1.8 * 0.5
    u = norm((dx, -math.sqrt(max(0.0, 1 - dx * dx - dz * dz)), dz))
    u = pitch_up(u, 0.25 * kick) if kick else u
    arm_dirs(p, 'R', u, (0.0, -1.0, 0.0), up=(0, 0, 1))
    if fist_y is not None:
        g = _dair_grow(f) if f is not None else 1.0
        wrist_y = pos(p, 'RHandN')[1]
        ext = max(0.0, wrist_y - fist_y - DAIR_OFF * g)
        t = p.trans.get('RHandN', anims.REST['RHandN'][0])
        p.move('RHandN', (t[0] + ext, t[1], t[2]))
    return p


def dair_windup(k=1.0):
    """Cocked: the right fist drawn up beside his head, elbow up and back, the chest opened and the knees tucked; the
    left hand low in front."""
    p = ab()
    air_tuck(p, 0.55 + 0.55 * k, spread=0.15 * k)
    torso(p, lean=-0.12 * k, roll=0.15 * k)
    head(p, pitch=0.2 * k)
    (ru, rf), (lu, lf) = rest_arm('R'), rest_arm('L')
    arm_dirs(p, 'R', mix(ru, (-0.45, 0.55, -0.7), k), mix(rf, (0.1, 0.95, 0.3), k))
    arm_dirs(p, 'L', mix(lu, (0.6, -0.5, 0.6), k), mix(lf, (0.2, -0.6, 0.8), k))
    lift(p, dy=0.3 * k)
    return p


def dair():
    """The rocket fist down: cocked beside his head (3-6, the rocket rings snapping on at 4), the arm drives straight down
    as the doll pitches over it (7), the fist fires off the forearm on 8 and is at the old muzzle on 9 (the meteor, near
    him), out to 13.0 below by 12, held a frame, and flies home, docking on 20 with a jolt through the arm. The arm kicks
    up at the launch and the body bucks; the fist is intangible while it's out (moves.dair)."""
    c = Clip(40, lag=dict(chain('L', 'arm', 1.5), **chain('L', 'leg', 1.5), **chain('R', 'leg', 2.0), HeadN=-1.0))
    c.key(0, ab())
    c.key(3, dair_windup(0.75), 'out')
    c.key(5, dair_windup(1.0), 'out')
    c.key(6, dair_windup(1.05), 'lin')
    c.key(7, dair_punch(0.0, 0.0), 'in')                     # driven straight down
    c.key(8, dair_punch(0.15, fist_y=DAIR_FIST_Y[8], f=8), 'lin')      # fired
    kick = {9: 0.55, 10: 0.45, 11: 0.35, 12: 0.28, 13: 0.24, 14: 0.2, 15: 0.16, 16: 0.12, 17: 0.08, 18: 0.05, 19: 0.02}
    for f in range(9, 20):
        c.key(f, dair_punch(kick[f], fist_y=DAIR_FIST_Y[f], f=f), 'lin')
    c.key(20, dair_punch(0.0, dip=1.0, fist_y=None), 'lin')   # docked: the jolt through the arm
    c.key(22, dair_punch(0.0, dip=0.4), 'inout')
    c.key(28, dair_windup(0.0), 'inout')
    c.key(33, ab(), 'out')
    c.key(40, ab(), 'lin')
    c.grow('RHandN', DAIR_GROW)
    return c.frames()


def dair_fists():
    """The fist's centre per frame {f: (x, y, z)} (TopN: x depth, y up, z forward), as the hitbox sits: HandN plus DAIR_OFF
    down the bone times the growth. For the exhaust trail and the measurements."""
    out = {}
    for k, sol in dair():
        W = rig.world_mats(pose={j: {'t': v[0], 'r': v[1]} for j, v in sol.solve().items()})
        out[k] = tuple(rig.xform((DAIR_OFF * _dair_grow(k), 0, 0), W['RHandN']))
    return out


def dair_cannon():
    """The Hand Cannon down air (until 2026-09-29; kept for the A/B): Hand Cannon straight down (the meteor at the muzzle on 9-10, the column through 15). The knees pull up and apart
    while the gun arm rises overhead, the cannon snapping on at the top (5); the arm drives straight down, a frame early,
    the doll diving forward over it so the barrel clears his silhouette; the shot at 9 bucks him up while the barrel holds
    vertical down the column (the elbow gives), shaking through the blast; it lets go at 22 and settles into the fall."""
    def gather(k=1.0):
        p = ab()
        air_tuck(p, 0.55 + 0.6 * k, spread=0.25 * k)
        torso(p, lean=-0.1 * k)
        head(p, pitch=0.25 * k)
        (ru, rf), (lu, lf) = rest_arm('R'), rest_arm('L')
        arm_dirs(p, 'R', mix(ru, (-0.35, 0.8, 0.35), k), mix(rf, (-0.1, 0.3, -0.95), k))
        arm_dirs(p, 'L', mix(lu, (0.9, 0.1, 0.3), k), mix(lf, (0.8, -0.4, 0.4), k))
        return p

    def blast(kick=0.0, shake=0.0):
        """Diving: the doll pitched forward so the barrel, straight down from a lowered shoulder, clears his silhouette
        (his arms are short: from an upright body the muzzle only reaches his hips); the legs trail behind. The recoil
        lifts the body and bends the elbow; the barrel stays on the column's line."""
        p = ab()
        legs(p, (0.12, -0.95, -0.1), (0.05, -0.85, -0.55), (-0.12, -0.92, -0.3), (-0.05, -0.7, -0.7), foot='point')
        torso(p, lean=0.32 - 0.08 * kick, roll=shake * 0.5)
        head(p, pitch=-0.2 - 0.12 * kick, roll=-shake)       # the crown kept back over him (the ECB top-front bone)
        arm_dirs(p, 'L', (0.9, 0.2 + shake, -0.1), (0.8, -0.2, 0.35))
        tilt_pose(p, 0.38 - 0.1 * kick)
        sh = pos(p, 'RShoulderJ')
        d = norm([t - s for t, s in zip((sh[0] * 1.1, DAIR_AIM[1], DAIR_AIM[2]), sh)])
        d = norm((d[0], d[1], d[2] + 0.04 * math.sin(7.0 * shake)))
        arm_dirs(p, 'R', pitch_up(d, 0.45 * kick), d)            # the elbow gives; the barrel holds the line
        lift(p, dy=0.9 * kick + shake * 0.3)
        return p

    c = Clip(40, lag=dict(chain('L', 'arm', 1.5), **chain('L', 'leg', 1.5), **chain('R', 'leg', 2.0), HeadN=-1.0))
    c.key(0, ab())
    c.key(3, gather(0.7), 'out')
    c.key(5, gather(1.0), 'out')              # the cannon snaps on (script)
    c.key(6, gather(1.04), 'lin')
    c.key(8, blast(), 'in')                    # driven straight down, a frame before the meteor
    c.key(9, blast(0.1), 'lin')               # the shot
    c.key(10, blast(0.7), 'out')               # bucked up by it
    c.key(11, blast(0.55, 0.06), 'out')
    for f, sh in ((12, -0.05), (13, 0.05), (14, -0.04), (15, 0.03)):
        c.key(f, blast(0.45 - 0.04 * (f - 12), sh), 'inout')     # the column shakes him through its frames
    c.key(19, blast(0.2), 'inout')
    c.key(22, blast(0.12), 'inout')
    c.key(28, gather(0.0), 'inout')
    c.key(33, ab(), 'out')
    c.key(40, ab(), 'lin')
    return c.frames()


# ------------------------------------------------------------------------------------------------ ground helpers
def stand(crouch=0.0, lean=0.0, yaw=0.0, roll=0.0, bob=0.0, hy=0.0, hp=0.0):
    """Standing in his stance (anims.base: the feet planted by IK), the chest turned (yaw, + his left) and leaned relative to
    the stance's hips, which stay put so the feet stay planted; the head keeps the stance's turn plus hy."""
    p = base(crouch=crouch, lean=lean, bob=bob)
    setrot(p, 'WaistN', (0.12 + lean, yaw, roll))
    head(p, yaw=anims.STANCE['head_yaw'] + hy, pitch=hp)
    return p


def aim_muzzle(p, side, y, muzzle, spread=-0.06, bend=0.0):
    """The arm straight forward (and `spread` out to the side), pitched so a muzzle `muzzle` past the wrist sits at height
    y: a projectile's spawn height is gameplay, so the new weapon forms keep the old spawn heights."""
    sh = pos(p, f'{side}ShoulderJ')
    L = rig.UPPER_ARM + rig.FOREARM + muzzle
    dy = max(-0.9, min(0.9, (y - sh[1]) / L))
    d = norm((spread, dy, math.sqrt(max(0.0, 1 - dy * dy - spread * spread))))
    if bend:
        return arm_dirs(p, side, pitch_up(d, -bend), pitch_up(d, bend * 0.4))
    return arm_dirs(p, side, d, d)


# ------------------------------------------------------------------------------------------------ landings
# The landing-lag animations keep the template's 30 frames (their scripts' timers and effects are Mario's), and the engine
# plays them over the landing lag (rate (30 + 0.1) / lag: nair 14, fair 16, bair 18, uair 16, dair 24; L-cancelled half).
# Frame 0 is the impact, a hard cut from wherever the aerial was: the doll hits in a squash with the move's limb still out,
# bottoms out by frame 3 and rises, weighty, onto Wait1's first frame.
def landing(residue, depth=1.0):
    """residue(k) -> a standing pose at squash k (1 the impact .. 0 standing) carrying the aerial's leftover."""
    c = Clip(30, lag=dict(chain('R', 'arm', 1.5), **chain('L', 'arm', 2.0), HeadN=1.0))
    c.key(0, residue(0.9 * depth, 1.0), 'lin')
    c.key(3, residue(1.05 * depth, 0.85), 'out')
    c.key(12, residue(0.55 * depth, 0.45), 'inout')
    c.key(22, residue(0.12 * depth, 0.1), 'inout')
    c.key(30, base(), 'out')
    return c.frames()


def landing_n():
    def r(k, left):
        p = stand(crouch=k, lean=0.35 * k, yaw=-0.2 * left)
        arm_dirs(p, 'R', mix(rest_arm('R', False)[0], (-0.9, -0.5, -0.3), left), mix(rest_arm('R', False)[1], (-0.8, -0.6, 0.0), left))
        arm_dirs(p, 'L', mix(rest_arm('L', False)[0], (0.9, -0.5, -0.3), left), mix(rest_arm('L', False)[1], (0.8, -0.6, 0.0), left))
        return p
    return landing(r)


def landing_f():
    def r(k, left):
        p = stand(crouch=k, lean=0.3 * k, yaw=0.5 * left)
        arm_dirs(p, 'R', mix(rest_arm('R', False)[0], (-0.1, -0.35, 1.0), left), mix(rest_arm('R', False)[1], (-0.05, -0.5, 1.0), left))
        return p
    return landing(r)


def landing_b():
    def r(k, left):
        p = stand(crouch=k, lean=0.3 * k + 0.1 * left, yaw=-0.9 * left, hy=-0.6 * left)
        arm_dirs(p, 'R', mix(rest_arm('R', False)[0], (-0.25, -0.45, -1.0), left), mix(rest_arm('R', False)[1], (-0.2, -0.6, -1.0), left))
        arm_dirs(p, 'L', mix(rest_arm('L', False)[0], (0.35, -0.6, 0.7), left), mix(rest_arm('L', False)[1], (0.2, -0.4, 0.9), left))
        return p
    return landing(r)


def landing_hi():
    def r(k, left):
        p = stand(crouch=k, lean=0.3 * k - 0.15 * left, hp=-0.25 * left)
        arm_dirs(p, 'R', mix(rest_arm('R', False)[0], (-0.4, 0.75, -0.5), left), mix(rest_arm('R', False)[1], (-0.3, 0.5, -0.8), left))
        return p
    return landing(r)


def landing_lw():
    def r(k, left):
        p = stand(crouch=k, lean=0.45 * k, hp=0.2 * left)
        arm_dirs(p, 'R', mix(rest_arm('R', False)[0], (-0.2, -0.85, 0.5), left), mix(rest_arm('R', False)[1], (-0.1, -0.95, 0.35), left))
        arm_dirs(p, 'L', mix(rest_arm('L', False)[0], (0.8, -0.3, 0.2), left), mix(rest_arm('L', False)[1], (0.6, -0.7, 0.3), left))
        return p
    return landing(r, depth=1.15)


# ------------------------------------------------------------------------------------------------ neutral B
# Spawn heights. The shots used to spawn at FtPart_RHandN, which on his skeleton is the elbow (the decomp's part enum is
# one short from part 16: ftgeno_specials.c GE_PART_RHAND): the Finger Shot at 9.33 up on the ground and 10.0 in the
# air, the Beam 9.31 and 10.09, 1.2 (2.0 in the air) in front of him. Now they leave the muzzle, at those same heights
# on the fire frame (the height decides which bodies a level shot meets), ~4.3 units further forward.
FINGER_Y, FINGER_Y_AIR, BEAM_Y, BEAM_Y_AIR = 9.33, 10.0, 9.31, 10.09
FINGER_MUZZLE, BEAM_MUZZLE = 1.65, 1.78       # past the wrist (ftgeno_specials.c GE_FINGER_MUZZLE, GE_BEAM_MUZZLE)


def _body(air, crouch=0.0, lean=0.0, yaw=0.0, tuck=0.55, hy=0.0, hp=0.0):
    if air:
        p = ab()
        torso(p, lean=lean, yaw=yaw)
        head(p, yaw=hy, pitch=hp)
        air_tuck(p, tuck)
        return p
    return stand(crouch=crouch, lean=lean, yaw=yaw, hy=hy, hp=hp)


def gather(air, k=1.0):
    """Neutral B's first frames: the gun hand drawn back to the hip, the other hand covering it, a dip."""
    p = _body(air, crouch=0.28 * k, lean=0.12 * k, yaw=-0.25 * k, tuck=0.55 + 0.3 * k, hy=0.2 * k)
    (ru, rf), (lu, lf) = rest_arm('R', air), rest_arm('L', air)
    arm_dirs(p, 'R', mix(ru, (-0.4, -0.75, -0.55), k), mix(rf, (0.05, -0.35, 1.0), k))
    arm_dirs(p, 'L', mix(lu, (0.3, -0.8, 0.5), k), mix(lf, (-0.55, -0.25, 0.8), k))
    return p


def beam_aim(air, pulse=0.0, kick=0.0, lean=0.0, yaw=0.3):
    """The charge: square to the target, low and wide, the Beam barrel level at its spawn height, the other hand bracing the
    gun arm's forearm."""
    p = _body(air, crouch=0.2 + 0.04 * pulse, lean=0.08 + lean, yaw=yaw, tuck=0.75, hy=-0.25, hp=0.05)
    aim_muzzle(p, 'R', BEAM_Y_AIR if air else BEAM_Y, BEAM_MUZZLE)
    if kick:
        d = norm([b - a for a, b in zip(pos(p, 'RArmJ'), pos(p, 'RHandN'))])
        kicked(p, 'R', d, kick, bend=0.45)
    W = world(p)
    grip = rig.xform((0.7, 0.0, 0.0), W['RArmJ'])                 # the left hand on the gun arm's forearm
    reach(p, 'L', (grip[0] + 0.5, grip[1] - 0.45, grip[2] - 0.2), pole=(1.0, -1.0, -0.2))
    return p


def beam_start(air):
    c = Clip(8, lag=dict(chain('L', 'arm', 1.0)))
    c.key(0, ab() if air else base())
    c.key(3, gather(air, 1.0), 'out')
    c.key(6, gather(air, 1.08), 'inout')     # a tap leaves here for the Finger Shot
    c.key(8, beam_aim(air), 'in')             # the snap out to the aim: the Loop's first frame, the barrel appearing
    return c.frames()


def beam_loop(air):
    """20 frames, closed: the charge hums (a breath of the crouch), and at loop frame 12, where each star lights (every 20
    frames from the press; the start is 8), the barrel gives a small kick."""
    c = Clip(20)
    for f in range(21):
        br = math.sin(2 * math.pi * f / 20)
        kick = 0.07 * max(0.0, 1 - abs(f - 13) / 3.0) if 10 <= f <= 16 else 0.0
        c.key(f, beam_aim(air, pulse=br, kick=kick), 'lin')
    return c.frames()


def beam_fire(air):
    """The release (the Beam at 8): a brace, the shot, a big kick up and back that rocks the doll, a weighty recovery."""
    rest = ab() if air else base()
    c = Clip(33, lag=dict(chain('L', 'arm', 1.5), HeadN=1.0))
    c.key(0, beam_aim(air), 'lin')
    c.key(3, beam_aim(air, pulse=1.5, kick=-0.08, lean=0.08), 'out')      # the brace
    c.key(7, beam_aim(air, pulse=1.0), 'inout')
    c.key(8, beam_aim(air, pulse=1.0), 'lin')                             # the shot: the Beam spawns on this pose
    c.key(9, beam_aim(air, pulse=0.8, kick=0.3, lean=-0.1), 'out')
    c.key(10, beam_aim(air, pulse=0.5, kick=0.5, lean=-0.2), 'out')       # the kick
    c.key(14, beam_aim(air, kick=0.2, lean=-0.1), 'inout')
    c.key(20, beam_aim(air, kick=0.1, lean=-0.05), 'inout')
    c.key(26, gather(air, 0.3), 'inout')
    c.key(33, rest, 'out')
    return c.frames()


def mix_pose(a, b, u):
    """A pose u of the way from a to b (their solved local rotations slerped, translations lerped): an in-between key."""
    sa, sb = a.solve(), b.solve()
    return Solved({j: (tuple(x + (y - x) * u for x, y in zip(sa[j][0], sb[j][0])),
                       euler_near(slerp(q_of(sa[j][1]), q_of(sb[j][1]), u), sa[j][1])) for j in sa})


def beam_cancel(air):
    """The shield cancel (8 frames, then Wait or Fall; a held shield comes in on Wait's first frame): the charge fizzles
    out of the barrel, which shivers and sags as the hum dies, the arm pulls it back in and the barrel folds back into a
    hand (the script's snap on frame 4), and the doll straightens onto Wait1's first frame (or the fall pose)."""
    rest = ab() if air else base()

    def fold(k):
        """The gun arm drawn back in: the elbow dropping back, the barrel tipping down past the hip."""
        p = _body(air, crouch=0.2 - 0.05 * k, lean=0.1 - 0.06 * k, yaw=0.3 - 0.2 * k, tuck=0.75, hy=-0.25 + 0.1 * k)
        arm_dirs(p, 'R', mix((-0.35, -0.55, 0.55), (-0.4, -0.85, -0.2), k), mix((0.05, -0.45, 1.0), (-0.1, -0.95, 0.35), k))
        arm_dirs(p, 'L', (0.35, -0.8, 0.35), (0.2, -0.85, 0.45))
        return p

    c = Clip(8, lag=dict(chain('L', 'arm', 1.0), HeadN=-1.0))
    c.key(0, beam_aim(air), 'lin')                                  # the frame of the press: still charging
    c.key(1, beam_aim(air, pulse=-2.0, kick=-0.32, lean=0.05), 'out')     # the charge drains: the barrel sags, he slumps
    c.key(2, beam_aim(air, pulse=-1.5, kick=-0.12, lean=-0.03), 'out')    # a last shiver
    c.key(3, fold(0.6), 'in')                                       # pulled in
    c.key(4, fold(1.0), 'out')                                      # folded back into a hand (the script's snap)
    c.key(6, mix_pose(fold(1.0), rest, 0.65), 'inout')
    c.key(8, rest, 'out')
    return c.frames()


def finger_aim(air, kick=0.0, lean=0.0):
    p = _body(air, crouch=0.15, lean=0.1 + lean, yaw=0.25, tuck=0.7, hy=-0.2)
    aim_muzzle(p, 'R', FINGER_Y_AIR if air else FINGER_Y, FINGER_MUZZLE)
    if kick:
        d = norm([b - a for a, b in zip(pos(p, 'RArmJ'), pos(p, 'RHandN'))])
        kicked(p, 'R', d, kick, bend=0.35)
    arm_dirs(p, 'L', (0.3, -0.75, -0.55), (0.15, -0.9, -0.3))
    return p


def finger(air):
    """Finger Shot (fires at 10 on the ground, 7 in the air): from the gather a tap leaves it in, the hand cocks, the fingers
    snap into tubes, the arm snaps out level and the shot flicks the hand up; a quick return."""
    n, fire = (24, 7) if air else (34, 10)
    rest = ab() if air else base()
    c = Clip(n, lag=dict(chain('L', 'arm', 1.5), HeadN=-1.0))
    c.key(0, gather(air, 1.0), 'lin')
    c.key(fire - 5 if not air else 2, gather(air, 1.12), 'out')          # the cock, where the tubes snap on
    c.key(fire - 1, finger_aim(air), 'in')
    c.key(fire, finger_aim(air), 'lin')                                   # the shot spawns on this pose
    c.key(fire + 1, finger_aim(air, kick=0.38, lean=-0.06), 'out')        # the flick
    c.key(fire + 4, finger_aim(air, kick=0.1), 'inout')
    c.key(fire + (8 if air else 12), finger_aim(air, kick=0.05), 'inout')
    c.key(n, rest, 'inout')
    return c.frames()


# ------------------------------------------------------------------------------------------------ side B: the Whirl
WHIRL_ELBOW = {False: (9.11, 1.21), True: (10.0, 1.98)}     # the disc's spawn (the elbow, frame 12): up, forward


def whirl(air):
    """The Geno Whirl, a sidearm throw of a disc of light (it leaves at 12): the hand comes up spinning it, the chest winds
    to the camera with the arm swung back behind him, then unwinds hard; the elbow leads round and the forearm whips out
    after it, letting go in front at 12 (the elbow passes the old spawn point then: the disc spawns on the elbow), and
    follows through across his body; a weighty recovery."""
    n = 28
    rest = ab() if air else base()

    def body(yaw, crouch, lean=0.1):
        return _body(air, crouch=crouch, lean=lean, yaw=yaw, tuck=0.75, hy=-0.6 * yaw)

    def up():
        p = body(-0.15, 0.12)
        arm_dirs(p, 'R', (-0.45, -0.55, 0.6), (0.3, 0.1, 0.95))
        arm_dirs(p, 'L', (0.3, -0.85, 0.3), (0.15, -0.7, 0.6))
        return p

    def level(th, y=-0.1):
        return norm((-math.cos(th), y, math.sin(th)))

    def swing(th_u, th_f, yaw, crouch, elbow=None, drop=0.0):
        """The upper arm at th_u round the body (0 straight out to his right, pi/2 ahead), the forearm at th_f; with
        `elbow` (up, forward) the upper arm is aimed so the elbow sits there."""
        p = body(yaw, crouch, lean=0.1 + 0.1 * math.sin(th_u))
        u = level(th_u, -0.1 - drop)
        if elbow:
            sh = pos(p, 'RShoulderJ')
            dy, dz = elbow[0] - sh[1], elbow[1] - sh[2]
            dx = -math.sqrt(max(0.05, rig.UPPER_ARM ** 2 - dy * dy - dz * dz))
            u = norm((dx, dy, dz))
        arm_dirs(p, 'R', u, level(th_f, -0.08 - drop))
        arm_dirs(p, 'L', spin((0.6, -0.4, 0.7), -0.3 * yaw), spin((0.4, -0.3, 0.85), -0.3 * yaw))
        return p

    c = Clip(n, lag=dict(chain('L', 'arm', 1.5), HeadN=-1.5, NeckN=-1.5))
    c.key(0, rest)
    c.key(3, up(), 'out')
    c.key(7, swing(-0.75, -0.95, -0.95, 0.32), 'inout')                 # wound back: the chest to the camera
    c.key(9, swing(0.05, -0.35, -0.35, 0.28), 'in')                     # the elbow leads, the forearm trails
    c.key(11, swing(0.45, 0.85, 0.3, 0.22), 'spline')
    c.key(12, swing(0.8, 1.65, 0.55, 0.2, elbow=WHIRL_ELBOW[air]), 'spline')   # the release: the forearm snaps out
    c.key(15, swing(1.8, 2.45, 0.85, 0.22, drop=0.2), 'out')            # through, across his body
    c.key(19, swing(1.85, 2.35, 0.75, 0.2, drop=0.3), 'inout')
    c.key(n, rest, 'inout')
    return c.frames()


# ------------------------------------------------------------------------------------------------ down B: Geno Blast
def _cast(air, creep=0.0, kick=0.0):
    """Down B's casting pose, shared by the Blast and the Flash until he commits (SMRPG starts both with the arms to the
    sky): both arms raised in a wide V, up, forward and out to his sides (straight up they vanish behind his big head),
    the chest lifted, the head tipped up. creep raises it a touch through the hold; kick is a star lighting."""
    # the chest leans back so the hands, high and forward, clear his face in profile (a big head: his arms can't reach
    # above it, so from the side a raised arm reads only in front of it)
    p = _body(air, crouch=0.04 - 0.04 * kick, lean=-0.3 - 0.08 * kick, yaw=0.3, tuck=0.45, hy=-0.2, hp=-0.45 - 0.1 * kick)
    up = creep + 0.12 * kick
    arm_dirs(p, 'R', pitch_up(norm((-0.45, 0.78, 0.5)), up), pitch_up(norm((-0.3, 0.86, 0.48)), up * 1.3))
    arm_dirs(p, 'L', pitch_up(norm((0.5, 0.78, 0.4)), up), pitch_up(norm((0.36, 0.86, 0.4)), up * 1.3))
    if kick:
        lift(p, dy=0.25 * kick)
    return p


def _dip(air):
    p = _body(air, crouch=0.22, lean=0.18, yaw=-0.2, tuck=0.8, hp=0.15)
    fold_arm(p, 'R', (-0.35, -0.7, 0.25), 0.9, 0.3)
    fold_arm(p, 'L', (0.35, -0.7, 0.25), 0.9, 0.3)
    return p


def blast_charge(air):
    """Down B's charge (SpecialLw / SpecialAirLw, both Blast and Flash): a dip, the arms thrown up to the sky by 8, the
    casting pose held and creeping while the stars light, a kick as the second lights (move frame 25). The release
    (blast_release) or the Flash (frame 49) cuts in from it; the charge never runs past 49."""
    rest = ab() if air else base()
    c = Clip(52, lag=dict(chain('L', 'arm', 1.5), HeadN=-1.5, NeckN=-1.0))
    c.key(0, rest)
    c.key(3, _dip(air), 'out')
    c.key(7, _cast(air, -0.04), 'out')
    c.key(9, _cast(air), 'inout')                   # arrived: the earliest release (a tap's mark) is frame 10
    c.key(24, _cast(air, 0.03), 'inout')
    c.key(25, _cast(air, 0.03, kick=1.0), 'out')    # the second star
    c.key(28, _cast(air, 0.04, kick=0.3), 'inout')
    c.key(32, _cast(air, 0.05), 'inout')
    c.key(49, _cast(air, 0.08), 'inout')            # the third star: the Flash (or, airborne, the release) takes over
    c.key(52, _cast(air, 0.08), 'lin')
    return c.frames()


def blast_release(air):
    """Down B's release (SpecialLwEnd / SpecialAirLwEnd): from the casting pose the gun hand snaps down to point along
    the floor at the mark (placed on this first frame), a crisp stop with a small overshoot; he holds the point through
    the tell and recovers where a tap's Blast did (the ground version 43 frames, the air one 27, into the fall)."""
    n = 27 if air else 43
    rest = ab() if air else base()

    def point(k=0.0, creep=0.0):
        p = _body(air, crouch=0.16, lean=0.16, yaw=0.3, tuck=0.6, hy=-0.25, hp=0.12)
        d = pitch_up(norm((-0.06, -0.3, 1.0)), -0.08 * k + creep)
        arm_dirs(p, 'R', d, d)
        arm_dirs(p, 'L', (0.45, -0.75, -0.35), (0.3, -0.85, -0.1))
        return p

    c = Clip(n, lag=dict(chain('L', 'arm', 1.5), HeadN=-1.0))
    c.key(0, _cast(air, 0.05), 'lin')
    c.key(1, point(), 'in')                         # snapped down at the mark
    c.key(2, point(1.0), 'out')                     # the overshoot
    c.key(5, point(-0.2), 'inout')
    if air:
        c.key(12, point(0.0, 0.04), 'inout')
        c.key(18, point(0.0, 0.08), 'inout')
    else:
        c.key(14, point(0.0, 0.03), 'inout')
        c.key(22, point(0.0, 0.06), 'inout')
        c.key(32, gather(False, 0.25), 'inout')
    c.key(n, rest, 'out')
    return c.frames()


FLASH_SUN = (0.0, 14.0, 30.0)          # the sun's centre (GE_FLASH_AHEAD, GE_FLASH_HIGH): the cannon aims at it


def flash():
    """Geno Flash (the sun fires at 54). SMRPG's Flash curls him into a ball that unfolds into a blue-and-gold cannon on a
    carriage. He curls up under the glow; from 23 to 76 the cannon (flash_cannon_keys, on its own joints) is shown in his
    place while his hidden body plays on here (a braced stance, arms at the sun, rocked by the kick of the shot), which is
    what his hurtboxes follow; from 76 he stands out of the second glow. Entered from the Blast's hold (frame 48)."""
    def ball(k=1.0, shiver=0.0):
        p = stand(crouch=0.25 + 0.8 * k, lean=0.55 * k, roll=shiver, hp=0.5 * k)
        fold_arm(p, 'R', (-0.25, -0.6, 0.6), 0.95, 0.6)
        fold_arm(p, 'L', (0.25, -0.6, 0.6), 0.95, 0.6)
        return p

    def cannon(kick=0.0, creep=0.0, lean=0.0):
        p = stand(crouch=0.5 - 0.1 * kick, lean=0.12 + lean, yaw=0.15, hy=-0.1, hp=-0.1)
        for s in 'RL':
            sh = pos(p, f'{s}ShoulderJ')
            d = norm([t - q for t, q in zip((sh[0] * 0.35, FLASH_SUN[1], FLASH_SUN[2]), sh)])
            d = pitch_up(d, creep)
            if kick:
                kicked(p, s, d, kick, bend=0.4)
            else:
                arm_dirs(p, s, d, d)
        return p

    c = Clip(94, lag=dict(chain('L', 'arm', 1.0), HeadN=-1.0))
    c.key(0, blast_hold())
    c.key(5, ball(0.6), 'out')
    c.key(10, ball(1.0), 'out')
    for f, sh in ((13, 0.02), (16, -0.02), (19, 0.025), (22, -0.02)):
        c.key(f, ball(1.0, sh), 'inout')      # charging, shivering
    c.key(27, cannon(creep=-0.08), 'out')     # unfolds: the cannons snap on (script)
    c.key(40, cannon(creep=0.0), 'inout')
    c.key(51, cannon(creep=0.04), 'inout')
    c.key(53, cannon(creep=-0.03, lean=0.06), 'out')    # the brace
    c.key(54, cannon(kick=0.15), 'in')
    c.key(57, cannon(kick=0.6, lean=-0.25), 'out')      # the kick of the shot
    c.key(64, cannon(kick=0.3, lean=-0.1), 'inout')
    c.key(72, cannon(kick=0.15), 'inout')
    c.key(82, gather(False, 0.4), 'inout')
    c.key(94, base(), 'out')
    return flash_cannon_keys(c.frames())


# ------------------------------------------------------------------------------------------------ Geno Flash's cannon
# The cannon (projects/geno/model/geno_cannon.py) rides its own joints (rig.CANNON_JOINTS), shown by moves.flash_cannon
# from FLASH_CANNON_ON (23) to FLASH_CANNON_OFF (76) while his hidden body keeps the motion above, so his hurtboxes are
# exactly the Flash's own. Its motion, per channel (frame: value, the ease into that key; EASE), under the glow (spawned
# on 1 and again on 60, moves.s_flash, so a pulse peaks on each swap): it drops out of the glow small and nose down,
# grows past full size, lands on its wheels with a bounce and rolls back into place, raises the barrel to aim at the sun
# (FLASH_SUN), dips before the shot on 49 (ftGe_FlashFireball), kicks up and rolls back with a hop on 50-53, rolls
# forward again, then folds (the barrel down, the whole cannon shrinking up into the glow) as Geno comes back on 76.
CANNON_CHANNELS = dict(
    scale={0: (0.42, 'lin'), 23: (0.42, 'lin'), 26: (1.10, 'out'), 28: (0.96, 'inout'), 31: (1.0, 'inout'),
           66: (1.0, 'lin'), 71: (0.9, 'in'), 76: (0.42, 'in'), 94: (0.42, 'lin')},
    lift={0: (2.4, 'lin'), 23: (2.4, 'lin'), 26: (0.5, 'in'), 28: (0.0, 'in'), 30: (0.25, 'out'), 32: (0.0, 'in'),
          49: (0.0, 'lin'), 51: (0.35, 'out'), 54: (0.0, 'in'), 66: (0.0, 'lin'), 70: (0.3, 'out'), 76: (2.6, 'in'),
          94: (2.6, 'lin')},
    z={0: (0.8, 'lin'), 23: (0.8, 'lin'), 28: (0.3, 'in'), 33: (0.0, 'out'), 49: (0.0, 'lin'), 51: (-1.6, 'out'),
       53: (-1.9, 'out'), 58: (-1.2, 'inout'), 66: (-0.4, 'inout'), 76: (0.2, 'inout'), 94: (0.2, 'lin')},
    pitch={0: (-30.0, 'lin'), 23: (-30.0, 'lin'), 26: (-8.0, 'out'), 28: (2.0, 'lin'), 32: (20.2, 'out'),
           37: (14.7, 'inout'), 42: (17.2, 'inout'), 47: (16.2, 'inout'), 48: (15.3, 'inout'), 49: (16.9, 'in'),
           50: (25.2, 'out'), 52: (27.2, 'out'), 57: (18.7, 'inout'), 62: (15.7, 'inout'), 66: (16.9, 'inout'),
           71: (4.0, 'in'), 76: (-30.0, 'in'), 94: (-30.0, 'lin')},
)
CANNON_AIM = 16.9          # degrees: the barrel on the sun's centre from the muzzle on the shot (FLASH_SUN; cannon_aim())


def cannon_channel(ch, f):
    ks = sorted(CANNON_CHANNELS[ch])
    if f <= ks[0]: return CANNON_CHANNELS[ch][ks[0]][0]
    if f >= ks[-1]: return CANNON_CHANNELS[ch][ks[-1]][0]
    i = max(k for k in range(len(ks) - 1) if ks[k] <= f)
    a, b = ks[i], ks[i + 1]
    va, (vb, ease) = CANNON_CHANNELS[ch][a][0], CANNON_CHANNELS[ch][b]
    return va + (vb - va) * EASE[ease]((f - a) / (b - a))


def cannon_pose(f):
    """The cannon's joints at frame f: {joint: (t, r)} local, and CannonN's scale."""
    rt = {n: (t, r) for n, p, t, r in rig.JOINTS}
    z, lift, k = cannon_channel('z', f), cannon_channel('lift', f), cannon_channel('scale', f)
    pitch = math.radians(cannon_channel('pitch', f))
    wr = rig.CANNON_AXLE[1]
    out = {'CannonN': ((0.0, lift, z), (0.0, 0.0, 0.0)),
           'CannonBarrelN': (rt['CannonBarrelN'][0], (-pitch, 0.0, 0.0)),            # -X: the muzzle (+Z) up
           'CannonWheelN': (rt['CannonWheelN'][0], (z / wr, 0.0, 0.0))}             # rolling with the carriage
    return out, {'CannonN': (k, k, k)}


# The hidden body curls into the cannon (Michael, 2026-09-29: "Makes sense on the cannon hurtbox change, but careful not
# to make it too small"), so his hurtboxes follow its silhouette, as Samus's become her Morph Ball's: his spine lies along
# the barrel, the head at the muzzle, the hips at the breech, the legs folded back over the breech and down the trail, the
# arms down the wheels. It rides the barrel's frame each frame (the aim, the kick, the roll back and the hop), cuts in from
# the ball as the cannon comes in (CURL_IN) and blends back out to the Flash's own pose over CURL_OUT, so the body he shows
# on 22 and from 76 on is unchanged. The parameters were fitted to the cannon's side silhouette by director/labs/cannon_hurt.py fit (the
# numbers are in DESIGN §12): s, d the hips along and across the barrel from the trunnions; dp the spine's pitch off the
# bore; wb, nb, hb the waist, neck and head bent; the arms' and legs' world directions in the side view (radians from
# straight down, + forward), left and right apart so their capsules spread.
CURL = dict(s=-1.896, d=0.37, dp=0.005, wb=0.0, nb=0.0, hb=-0.002, auL=-0.164, afL=-0.206, auR=-0.34, afR=0.148,
            tuL=1.041, tsL=-0.46, tuR=-1.206, tsR=0.795)
CURL_ON = os.environ.get('GENO_FLASH_CURL', '1') != '0'     # 0 builds without the curl (an A/B: the body's own pose)
CURL_IN = (22, 23)                 # the ball (visible on 22), then the curl: a cut, hidden from 23 (a blend dipped the area)
CURL_OUT = (66, 73)                # the curl back to the Flash's own pose, settled before he shows on 76


def barrel_frame(f):
    """The barrel at frame f: the trunnions' world point, the bore's direction and its up (the side view)."""
    cj, sc = cannon_pose(f)
    k = sc['CannonN'][0]
    t = cj['CannonN'][0]
    piv = (0.0, t[1] + k * rig.CANNON_TRUNNION[1], t[2] + k * rig.CANNON_TRUNNION[2])
    p = math.radians(cannon_channel('pitch', f))
    return piv, (0.0, math.sin(p), math.cos(p)), (0.0, math.cos(p), -math.sin(p)), p


def curl_pose(f, P=None):
    """The hidden body curled into the cannon at frame f (CURL, or the parameters P being fitted)."""
    P = dict(CURL, **(P or {}))
    piv, ax, up, pitch = barrel_frame(f)
    hip = [c + ax[i] * P['s'] + up[i] * P['d'] for i, c in enumerate(piv)]
    p = Pose()
    # the hips' world point through YRotN (unrotated, so HipN's origin sits at its local offset below it)
    hn = dict((n, t) for n, par, t, r in rig.JOINTS)['HipN']
    xr = dict((n, t) for n, par, t, r in rig.JOINTS)['XRotN']
    p.move('YRotN', (hip[0] - xr[0] - hn[0], hip[1] - xr[1] - hn[1], hip[2] - xr[2] - hn[2]))
    th = math.pi / 2 - pitch - P['dp']                     # HipN's local +Y (the spine) along the bore
    p.move('HipN', hn).rot('HipN', (th, 0.0, 0.0))
    p.rot('WaistN', (P['wb'], 0.0, 0.0)).rot('NeckN', (P['nb'], 0.0, 0.0)).rot('HeadN', (P['hb'], 0.0, 0.0))
    side = lambda a, lat: norm((lat, -math.cos(a), math.sin(a)))
    for s_, sx in (('L', 1), ('R', -1)):
        arm_dirs(p, s_, side(P['au' + s_], sx * 0.25), side(P['af' + s_], sx * 0.15))
        p.aim(f'{s_}LegJ', side(P['tu' + s_], sx * 0.2)); p.aim(f'{s_}KneeJ', side(P['ts' + s_], sx * 0.1))
    return p


def _mat(t, r):
    return np.array(rig.local_mat(t, r))


def _tr(M, prev_r):
    """(t, r) of a local 4x4 (row vectors), the Euler angles nearest prev_r."""
    return tuple(float(v) for v in M[3, :3]), euler_near(_q_from_m(M[:3, :3].tolist()), prev_r)


def flash_cannon_keys(frames, curl=True):
    """The Flash's frames with the cannon's joints keyed on every one, and (curl) the hidden body curled into it from
    CURL_IN to CURL_OUT (the body's joints are the Flash's own outside them). Through the curl the neck keeps the Flash's
    own world transform and the head its own world turn (only its place moves, to the muzzle): the capelet and the cap's
    point hang from them (rig.DYNAMICS), so their physics sees the motion it always did, and they come out of the fold
    as they did before the curl (measured with the dynamics trace: DESIGN §12)."""
    out = []
    for f, sol in frames:
        d = dict(sol.solve())
        if curl and CURL_ON and CURL_IN[0] < f < CURL_OUT[1]:
            u = min(1.0, (f - CURL_IN[0]) / (CURL_IN[1] - CURL_IN[0]), (CURL_OUT[1] - f) / (CURL_OUT[1] - CURL_OUT[0]))
            u = EASE['inout'](max(0.0, u))
            c = curl_pose(f).solve()
            b = {j: (tuple(x + (y - x) * u for x, y in zip(d[j][0], c[j][0])),
                     euler_near(slerp(q_of(d[j][1]), q_of(c[j][1]), u), d[j][1])) for j in d}
            Ws = {k: np.array(v) for k, v in rig.world_mats(pose={k: {'t': v[0], 'r': v[1]} for k, v in d.items()}).items()}
            Wc = {k: np.array(v) for k, v in rig.world_mats(pose={k: {'t': v[0], 'r': v[1]} for k, v in c.items()}).items()}
            Wb = {k: np.array(v) for k, v in rig.world_mats(pose={k: {'t': v[0], 'r': v[1]} for k, v in b.items()}).items()}
            neck = Ws['NeckN']                                   # the neck where the Flash puts it
            b['NeckN'] = _tr(neck @ np.linalg.inv(Wb['WaistN']), d['NeckN'][1])
            # the head: the Flash's own turn, its capsule's centre moved u of the way to the curl's
            hc = np.array(rig.HURTBOXES[0][1]) * 0.5 + np.array(rig.HURTBOXES[0][2]) * 0.5
            assert rig.HURTBOXES[0][0] == 'HeadN'
            want = np.append(hc, 1.0) @ Ws['HeadN'] * (1 - u) + np.append(hc, 1.0) @ Wc['HeadN'] * u
            H = Ws['HeadN'].copy()
            H[3, :3] = want[:3] - hc @ H[:3, :3]
            b['HeadN'] = _tr(H @ np.linalg.inv(neck), d['HeadN'][1])
            d = b
        cj, sc = cannon_pose(f)
        d.update(cj)
        out.append((f, Solved(d, dict(sol.scale, **sc))))
    return out

def cannon_aim(f=49):
    """(the barrel's pitch, the pitch that points the muzzle at the sun's centre) at frame f, in degrees."""
    cj, sc = cannon_pose(f)
    k = sc['CannonN'][0]
    t = cj['CannonN'][0]
    piv = [t[0], t[1] + k * rig.CANNON_TRUNNION[1], t[2] + k * rig.CANNON_TRUNNION[2]]
    p = math.radians(cannon_channel('pitch', f))
    mz = [piv[0], piv[1] + k * rig.CANNON_MUZZLE * math.sin(p), piv[2] + k * rig.CANNON_MUZZLE * math.cos(p)]
    want = math.degrees(math.atan2(FLASH_SUN[1] - mz[1], FLASH_SUN[2] - mz[2]))
    return math.degrees(p), want, mz


def blast_hold():
    """The charge's pose at frame 49, where it turns into Geno Flash (the engine cuts, it doesn't blend)."""
    fr = dict(blast_charge(False))
    return fr[49]


# ------------------------------------------------------------------------------------------------ up B: Star Road
def fold(air, k=1.0, shiver=0.0):
    """Folded into a ball for the cannon: knees to the chest, head down, the Hand Cannons pointing down past his feet."""
    if air:
        p = ab()
        air_tuck(p, 0.55 + 0.75 * k)
        torso(p, lean=0.55 * k, roll=shiver)
        head(p, pitch=0.45 * k)
    else:
        p = stand(crouch=0.2 + 0.85 * k, lean=0.6 * k, roll=shiver, hp=0.45 * k)
    for s, sx in (('R', -1), ('L', 1)):
        u, f = rest_arm(s, air)
        arm_dirs(p, s, mix(u, (sx * 0.62, -0.8, 0.12), min(1.0, k)), mix(f, (sx * 0.45, -0.9, -0.05), min(1.0, k)))
    return p


def starroad_start(air):
    """Star Road's fold (the sound at 6) and aim (to 18, then the launch): a dip, the doll folding into a ball with the
    Hand Cannons (the thrusters: SMRPG's cannon form has no art yet) pointing down, shivering as it builds, a last squeeze."""
    c = Clip(18)
    c.key(0, ab() if air else base())
    c.key(3, fold(air, 0.45), 'out')
    c.key(6, fold(air, 1.0), 'out')
    for f, sh in ((8, 0.03), (10, -0.03), (12, 0.035), (14, -0.03)):
        c.key(f, fold(air, 1.0, sh), 'inout')
    c.key(17, fold(air, 1.12, 0.0), 'inout')          # the squeeze before the shot
    c.key(18, fold(air, 1.12, 0.0), 'lin')
    return c.frames()


def starroad_travel():
    """The flight (the code pitches XRotN so his body's up is the path, and ends the travel at 20): shot out of the fold
    into a straight doll, legs together and toes pointed, the Hand Cannons down his sides blasting back like thrusters,
    spiralling once round the path. XRotN is never keyed here (the code owns it). The launch hitbox rides WaistN on frames
    1-4, so the body sits where the old pose had it."""
    def straight(twist, stretch=1.0):
        p = base(stance=0)
        lift(p, dy=-0.45)                               # the old pose's waist height (its stance dropped the hips 0.45)
        setrot(p, 'WaistN', (0.02, 0.0, 0.0))
        head(p, pitch=0.2)
        legs(p, (0.07, -1, 0.02 * stretch), (0.03, -1, -0.05), (-0.07, -1, 0.02 * stretch), (-0.03, -1, -0.05), foot='point')
        for s, sx in (('R', -1), ('L', 1)):
            arm_dirs(p, s, (sx * 0.62, -0.8, -0.1 * stretch), (sx * 0.38, -0.92, -0.2 * stretch))
        return spun_pose(p, twist)

    c = Clip(30)
    c.key(0, straight(0.0, 1.4), 'lin')
    c.key(2, straight(-0.3, 0.8), 'out')
    c.key(4, straight(-0.8, 1.0), 'inout')
    for f in range(6, 22, 2):
        c.key(f, straight(-0.8 - 2 * math.pi * (f - 4) / 18.0 * 0.95, 1.0), 'lin')
    c.key(30, straight(-0.8 - 2 * math.pi * 1.05, 1.0), 'out')
    return c.frames()
