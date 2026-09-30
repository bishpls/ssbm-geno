"""Geno's locomotion: the walks, the run, the dash, the run turnaround and the skid, generated from foot paths and IK.

Every frame is a pose spec in the body frame (+Z where he faces, +X his left, +Y up; model units = world units, ModelScale
1): the pelvis (position and frame), the chest and head, each arm's upper-arm and forearm directions, and each foot (ankle
position, the boot's forward and sole-down directions). `assemble` turns a spec into an anims.Pose: the knees come from
two-bone IK (anims.leg_ik) with a pole over the toes, and `turn` rotates the whole body about the vertical on YRotN (the
run turnaround's half-turn, as Mario's and Fox's TurnRun carry it).

Cycles (WalkSlow, WalkMiddle, WalkFast, Run). The engine plays a walk at rate |v| / slow_walk_max, mid_walk_point or
fast_walk_min and the run at |v| / run_animation_scaling (ftwalkcommon.c, ftCo_Run.c), so a stance foot that slides back
at exactly that attribute speed per animation frame stays put on the floor at any speed. Each foot:
  - stance: the boot rolls heel -> flat -> ball about fixed pivots on the floor (the loaf's heel 0.8 behind the ankle, its
    ball 1.3 ahead, the sole 0.95 below), carried back at the attribute speed;
  - swing: a Hermite path in the world from toe-off to the next heel strike, matching both ends' velocities, plus a lift.
The pelvis bobs (softly clamped so no leg ever straightens past ~20 degrees of knee bend), rolls, yaws and sways; the chest
counter-rotates; the arms swing opposite the legs with the elbows bending on the forward swing and trailing a frame or two;
the head holds its line. Walks fade from the idle's open stance (hips 25 degrees toward the camera) to side-on; the run is
side-on. Frame 0 of every walk is the left heel strike with the right foot behind, the idle's own stagger.

One-shots (Dash, TurnRun, RunBrake) are key specs on a spline, then foot contacts pinned to the floor at the body's
measured speed for that stretch. Their seams: Dash f0 and RunBrake's last frame are Wait1 frame 0 exactly; Dash f10 is Run
f0 (the dash hands over to the run after ten frames); TurnRun ends on Run f0 turned half round.

Footfalls (FOOTFALLS) drive the scripts (`scripts()`): the FootstepEffect dust and step sound, the wooden steps from bank 55
(sound/wiring.py) and the rumble, looped with SetLoop/ExecuteLoop (no pointers) and SetTimerAnimation, which waits for the
animation to wrap.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig
import anims as A

TAU = 2 * math.pi
ST = A.STANCE
THIGH, SHIN = A.THIGH, A.SHIN
LEG = THIGH + SHIN
HEEL, BALL, SOLE = 0.8, 1.3, rig.ANKLE_Y          # the boot's pivots from the ankle, and the ankle's height over its sole
ATTR = rig.ATTRIBUTES
# the attribute speeds a cycle is authored for (Mario's template values, which Geno keeps; rig.ATTRIBUTES may override)
SPEED = {'WalkSlow': ATTR.get('WalkAnimationSpeed', 0.18), 'WalkMiddle': ATTR.get('MidWalkPoint', 0.44),
         'WalkFast': ATTR.get('FastWalkSpeed', 0.7), 'Run': ATTR.get('RunAnimationScale', 1.45)}


# ---- small vector helpers (tuples)
def add(*vs): return tuple(sum(c) for c in zip(*vs))
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def mul(a, k): return tuple(x * k for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))
def norm(a):
    l = length(a) or 1.0
    return mul(a, 1 / l)
def lerp(a, b, t): return a + (b - a) * t
def vlerp(a, b, t): return tuple(lerp(x, y, t) for x, y in zip(a, b))
def roty(v, a):
    """rotate about +Y as rig.rot_xyz(0, a, 0) does (row vectors): +Z turns toward +X for positive a"""
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c)
def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)
def rad(d): return math.radians(d)


def hermite(p0, p1, m0, m1, s):
    s2, s3 = s * s, s * s * s
    return (2 * s3 - 3 * s2 + 1) * p0 + (s3 - 2 * s2 + s) * m0 + (-2 * s3 + 3 * s2) * p1 + (s3 - s2) * m1


def frame(yaw, pitch=0.0, roll=0.0):
    """a segment's across (+X, his left) and up (+Y) axes: yawed, rolled (left side up for +roll), then pitched forward"""
    across = (math.cos(yaw), 0.0, -math.sin(yaw))
    up = (0.0, 1.0, 0.0)
    if roll:
        across, up = add(mul(across, math.cos(roll)), mul(up, math.sin(roll))), sub(mul(up, math.cos(roll)), mul(across, math.sin(roll)))
    if pitch:
        fwd = cross(across, up)
        up = add(mul(up, math.cos(pitch)), mul(fwd, math.sin(pitch)))
    return across, up


# ---- specs and poses
def wait_spec():
    """Wait1 frame 0 (anims.base()) as a spec: the seams' target."""
    drop, yaw = ST['drop'], ST['hip_yaw']
    s = dict(turn=0.0, pel=(0.0, rig.LEG_TOP - drop, 0.0), pyaw=yaw, ppitch=0.0, proll=0.0,
             cyaw=yaw + ST['chest_yaw'], cpitch=0.12, croll=0.0, hpitch=0.0, hyaw=ST['head_yaw'], arm={}, foot={}, pole={})
    for side, sx in (('L', 1), ('R', -1)):
        s['arm'][side] = (norm((sx * 0.28, -1, 0.12)), norm((sx * 0.15, -0.9, 0.45)))
        toe = sx * ST['toe_out']
        f = (math.sin(toe), 0.0, math.cos(toe))
        s['foot'][side] = ((sx * ST['lat'], SOLE, ST['fwd'] if sx > 0 else ST['back']), f, (0.0, -1.0, 0.0))
        s['pole'][side] = f
    return s


def sockets(s):
    """the hip sockets (body frame) of a spec"""
    across, _ = frame(s['pyaw'], s['ppitch'], s['proll'])
    return {side: add(s['pel'], mul(across, sx * rig.HIP_X)) for side, sx in (('L', 1), ('R', -1))}


def rotx(v, a):
    """rotate about +X as rig.rot_xyz(a, 0, 0) does (row vectors): +Y turns toward +Z for positive a"""
    c, s = math.cos(a), math.sin(a)
    return (v[0], v[1] * c - v[2] * s, v[1] * s + v[2] * c)


def assemble(s):
    """A spec -> a Pose. `turn` yaws the whole body on YRotN (TurnRun's and Turn's half turns); `flip` pitches it
    head-over-heels on XRotN (a somersault; + is forward) about the point `flipc` above his feet (default: his middle)."""
    p = A.Pose()
    psi = s['turn']
    phi, fc = s.get('flip', 0.0), s.get('flipc', 7.6)
    R = (lambda v: rotx(roty(v, psi), phi)) if phi else (lambda v: roty(v, psi))
    drop = ST['drop']
    px, py, pz = s['pel']
    hx, _, hz = roty((px, 0.0, pz), psi)
    # YRotN carries the bob, sway, surge and turn; HipN the idle's drop, as base() splits them
    p.move('YRotN', (hx, py - (rig.LEG_TOP - drop), hz))
    if psi: p.rot('YRotN', (0.0, psi, 0.0))
    if phi:                                              # XRotN turns about its own origin (HIP_Y): shift it so the
        c = (0.0, fc, 0.0)                               # body turns about fc instead
        off = sub((0.0, rig.HIP_Y, 0.0), c)
        p.move('XRotN', add(c, rotx(off, phi)))
        p.rot('XRotN', (phi, 0.0, 0.0))
    p.move('HipN', (0.0, rig.LEG_TOP - rig.HIP_Y - drop, 0.0))
    across, up = frame(s['pyaw'], s['ppitch'], s['proll'])
    p.aim('HipN', R(across), R(up))
    ca, cu = frame(s['cyaw'], s['cpitch'], s['croll'])
    p.aim('WaistN', R(ca), R(cu))
    p.rot('HeadN', (s['hpitch'], s['hyaw'], 0.0))
    for side, (upper, fore) in s['arm'].items():
        p.aim(f'{side}ShoulderJ', R(upper))
        p.aim(f'{side}ArmJ', R(fore))
    for side, hip in sockets(s).items():
        ankle, f, down = s['foot'][side]
        thigh, shin = A.leg_ik(hip, ankle, s['pole'][side])
        p.aim(f'{side}LegJ', R(thigh))
        p.aim(f'{side}KneeJ', R(shin))
        p.aim(f'{side}FootJ', R(f), up=R(down))
    return p


def reach(s):
    """each leg's hip-to-ankle distance over the leg's length (1 = straight)"""
    return {side: length(sub(s['foot'][side][0], hip)) / LEG for side, hip in sockets(s).items()}


def knee_bend(d):
    """knee flexion (deg, 0 = straight) for a hip-ankle distance d"""
    c = (THIGH ** 2 + SHIN ** 2 - d * d) / (2 * THIGH * SHIN)
    return 180 - math.degrees(math.acos(max(-1.0, min(1.0, c))))


# ---- the boot on the floor
def boot(pivot_z, x, pitch, toe):
    """ankle position, forward and sole-down directions for a boot rolling on the floor. pitch > 0 (toe up) pivots on the
    heel, < 0 (heel up) on the ball; pivot_z is where the flat boot's ankle would stand."""
    f0 = (math.sin(toe), 0.0, math.cos(toe))
    f = add(mul(f0, math.cos(pitch)), (0.0, math.sin(pitch), 0.0))
    down = add((0.0, -math.cos(pitch), 0.0), mul(f0, math.sin(pitch)))
    flat = (x, SOLE, pivot_z)
    if pitch >= 0:
        piv = add(flat, mul(f0, -HEEL), (0.0, -SOLE, 0.0))
        ankle = add(piv, mul(f, HEEL), mul(down, -SOLE))
    else:
        piv = add(flat, mul(f0, BALL), (0.0, -SOLE, 0.0))
        ankle = add(piv, mul(f, -BALL), mul(down, -SOLE))
    return ankle, f, down


def sole_min(ankle, f, down):
    """the boot's lowest point (heel, ball and toe tip of the sole)"""
    pts = [add(ankle, mul(f, a), mul(down, SOLE - b)) for a, b in ((-HEEL - 0.1, 0.05), (BALL, 0.0), (2.0, 0.19), (2.2, 0.5))]
    return min(p[1] for p in pts)


def arm_dirs(sx, swing, elbow, abd, cyaw, inward=0.25):
    """upper-arm and forearm directions (body frame) from the upper arm's forward swing, the elbow's bend and the arm's
    abduction (deg) in a chest yawed by cyaw; the forearm bends forward and a little in"""
    al, el, ab = rad(swing), rad(elbow), rad(abd)
    up = (sx * math.sin(ab), -math.cos(ab) * math.cos(al), math.cos(ab) * math.sin(al))
    fwd = (0.0, 0.0, 1.0)
    perp = norm(sub(fwd, mul(up, dot(fwd, up))))
    perp = norm(add(perp, (-sx * inward, 0.0, 0.0)))
    fore = add(mul(up, math.cos(el)), mul(perp, math.sin(el)))
    return roty(norm(up), cyaw), roty(norm(fore), cyaw)


# ---- cycles
# stride = speed x frames. T: the stance's travel (how far the body passes over a planted boot), which sets the duty
# (T / stride) and, centred on the pelvis (+ c), where the flat boot's ankle lands. ts, to: the boot's pitch at heel strike and toe-off (deg). flat, heel: when in the stance the boot
# lands flat and its heel starts to rise (fractions of the stance). lift, lift_at: the swing's extra ankle height and when
# (fraction of the swing) it peaks. h, bob, bob_low: pelvis height, bob (peak to peak) and where its low falls (cycle
# fraction after each strike). yaw: mean pelvis yaw (deg; negative = open toward the camera facing right), yaw_amp its
# swing; roll, sway. chest_yaw: the chest's mean (world), chest_amp its counter-swing; lean (deg). arm: the upper arm's
# mean forward angle and swing, elbow bend and its swing, abduction; lag, elbow_lag in frames.
GAITS = {
    'WalkSlow': dict(n=56, T=5.6, c=0.1, ts=14, to=-26, flat=0.3, heel=0.5, lift=0.45, lift_at=0.42, land=0.75, descent=0.08, lat=1.2,
                     toe=0.2, h=5.55, bob=0.3, bob_low=0.0, yaw=-14, yaw_amp=8, roll=3, sway=0.12, surge=0.06,
                     chest_yaw=-14, chest_amp=6, lean=11, arm=(4, 16), elbow=(44, 10), abd=13, lag=2, elbow_lag=2.5, tilt=3,
                     head_yaw=-7, nod=1.5),
    'WalkMiddle': dict(n=32, T=5.8, c=0.1, ts=18, to=-32, flat=0.3, heel=0.45, lift=0.7, lift_at=0.4, land=0.75, descent=0.12,
                       lat=1.15, toe=0.16, h=5.45, bob=0.5, bob_low=0.02, yaw=-9, yaw_amp=11, roll=4, sway=0.1, surge=0.08,
                       chest_yaw=-8, chest_amp=9, lean=15, arm=(6, 28), elbow=(50, 14), abd=14, lag=1.5, elbow_lag=2.5, tilt=4,
                       head_yaw=-4, nod=2.0),
    'WalkFast': dict(n=26, T=6.0, c=0.0, ts=20, to=-36, flat=0.28, heel=0.42, lift=1.0, lift_at=0.38, land=0.75, descent=0.15, lat=1.12,
                     toe=0.12, h=5.35, bob=0.65, bob_low=0.1, yaw=-4, yaw_amp=13, roll=5, sway=0.08, surge=0.1,
                     chest_yaw=-3, chest_amp=11, lean=18, arm=(8, 36), elbow=(56, 16), abd=15, lag=1.2, elbow_lag=2, tilt=5,
                     head_yaw=-2, nod=2.5),
    'Run': dict(n=18, T=6.4, c=-1.2, ts=10, to=-40, flat=0.2, heel=0.35, lift=0.8, lift_at=0.25, land=0.6, descent=0.25, lat=1.08,
                push=0.5, kick=0.5, toe=0.06, h=5.2, bob=1.0, bob_low=0.13, yaw=0, yaw_amp=20, roll=8, sway=0.06, surge=0.12, tilt=16,
                chest_yaw=0, chest_amp=13, lean=42, arm=(14, 48), elbow=(84, 16), abd=18, lag=1.0, elbow_lag=1.5,
                head_yaw=0, nod=3.0, offset=0.61),
}


class Cycle:
    """A gait cycle: foot paths, pelvis, torso, arms and head as functions of the phase 0..1 (frame = phase x n)."""
    def __init__(self, name, **over):
        g = dict(GAITS[name]); g.update(over)
        self.name, self.g = name, g
        self.n, self.v = g['n'], SPEED.get(name, 0.0)
        self.S = self.v * self.n                                  # stride per cycle, world units
        g['duty'] = g['T'] / self.S                               # the stance travel sets the duty
        g['strike'] = g['T'] / 2 + g['c']                         # centred on the pelvis, nudged by c
        self.off = g.get('offset', 0.0)                           # phase of frame 0 (the run starts mid-stance)
        self.strikes = {'L': 0.0, 'R': 0.5}
        self._heights = None

    # the stance foot's pitch at stance fraction u
    def pitch(self, u):
        g = self.g
        if u <= g['flat']:
            return rad(g['ts']) * 0.5 * (1 + math.cos(math.pi * u / g['flat']))
        if u <= g['heel']:
            return 0.0
        t = (u - g['heel']) / (1 - g['heel'])
        return rad(g['to']) * t ** g.get('to_pow', 1.7)

    def stance(self, side, p):
        """p: the foot's own phase (0 = heel strike), inside the stance: ankle, forward, down (body frame)"""
        g = self.g
        sx = 1 if side == 'L' else -1
        u = p / g['duty']
        z = g['strike'] - self.S * p
        return boot(z, sx * g['lat'], self.pitch(u), sx * g['toe'])

    def foot(self, side, p):
        """ankle, forward, down, contact (0..1) at the foot's phase p (0 = heel strike)"""
        g = self.g
        p %= 1.0
        b = g['duty']
        if p <= b:
            a, f, d = self.stance(side, p)
            return a, f, d, 1.0
        e = 1e-4
        a0, _, _ = self.stance(side, b)
        a0m, _, _ = self.stance(side, b - e)
        a1, _, _ = self.stance(side, 0.0)
        a1p, _, _ = self.stance(side, e)
        dur = 1 - b
        s = (p - b) / dur
        # the swing, in the body frame: a Hermite from toe-off to the next heel strike. It leaves with the stance's own
        # velocity (rolling off the ball: no slip at toe-off) and lands with `land` of the stance's backward velocity (1 is
        # a matched landing, which carries the foot out ahead and back; less trims that retraction to a short plant)
        m0 = mul(sub(a0, a0m), dur / e)
        m0 = (m0[0], m0[1] + g.get('kick', 0.0) * self.n * dur, m0[2] * g.get('push', 1.0))   # the heel's recovery
        m1 = mul(sub(a1p, a1), dur * g['land'] / e)
        m1 = (m1[0], -g.get('descent', 0.12) * self.n * dur, m1[2])      # the heel comes down onto the floor, not along it
        w = [hermite(a0[k], a1[k], m0[k], m1[k], s) for k in range(3)]
        pk = g['lift_at']
        gam = math.log(0.5) / math.log(pk)
        lift = g['lift'] * math.sin(math.pi * s ** gam) ** 2
        ankle = (w[0], w[1] + lift, w[2])
        # the boot's pitch: from toe-off's heel-up through a toe-down carry to heel strike's toe-up
        th0 = rad(g['to'])
        dth0 = (self.pitch(1.0) - self.pitch(1.0 - e / b)) / (e / b) / b * dur   # d(pitch)/ds at toe-off
        th = hermite(th0, rad(g['ts']), 0.35 * dth0, 0.0, s)       # the flick off the ball, eased
        sx = 1 if side == 'L' else -1
        toe = sx * g['toe']
        f0 = (math.sin(toe), 0.0, math.cos(toe))
        f = add(mul(f0, math.cos(th)), (0.0, math.sin(th), 0.0))
        d = add((0.0, -math.cos(th), 0.0), mul(f0, math.sin(th)))
        # keep the sole off the floor through the swing (it lands exactly at the strike)
        low = sole_min(ankle, f, d)
        clear = 0.12 * math.sin(math.pi * s)
        ankle = (ankle[0], ankle[1] + 0.05 * math.log(1 + math.exp((clear - low) / 0.05)), ankle[2])   # a soft floor
        return ankle, f, d, 0.0

    def feet(self, phi):
        return {side: self.foot(side, phi - st) for side, st in self.strikes.items()}

    # pelvis
    def pelvis_frame(self, phi):
        g = self.g
        yaw = rad(g['yaw']) - rad(g['yaw_amp']) * math.cos(TAU * (phi + 0.04))     # left hip forward at the left strike
        b = g['duty']
        roll = rad(g['roll']) * math.cos(TAU * (phi - b / 2))                        # the swing side drops
        return yaw, rad(g.get('tilt', 0.0)), roll

    def pelvis_xz(self, phi):
        g = self.g
        b = g['duty']
        x = g['sway'] * math.cos(TAU * (phi - b / 2))
        z = -g['surge'] * math.cos(2 * TAU * (phi - g['bob_low'] + 0.05))
        return x, z

    def heights(self, samples=240):
        """the pelvis height through the cycle: the bob, held under what the legs reach at `reach` of their length, then
        smoothed (a periodic Gaussian of `smooth` frames), so no knee straightens past ~20 degrees nor pops"""
        if self._heights: return self._heights
        g = self.g
        hs = []
        for i in range(samples):
            phi = i / samples
            des = g['h'] - g['bob'] / 2 * math.cos(2 * TAU * (phi - g['bob_low']))
            feet = self.feet(phi)
            yaw, pitch, roll = self.pelvis_frame(phi)
            x, z = self.pelvis_xz(phi)
            across, _ = frame(yaw, pitch, roll)
            lim = 1e9
            r = g.get('reach', 0.95) * LEG
            for side, sx in (('L', 1), ('R', -1)):
                a = feet[side][0]
                off = mul(across, sx * rig.HIP_X)
                dx, dz = a[0] - (x + off[0]), a[2] - (z + off[2])
                lim = min(lim, a[1] + math.sqrt(max(0.0, r * r - dx * dx - dz * dz)) - off[1])
            hs.append(min(des, lim))
        sig = g.get('smooth', 1.0) * samples / self.n
        ker = [math.exp(-0.5 * (j / sig) ** 2) for j in range(-int(3 * sig), int(3 * sig) + 1)]
        tot = sum(ker)
        half = len(ker) // 2
        self._heights = [sum(hs[(i + j - half) % samples] * w for j, w in enumerate(ker)) / tot for i in range(samples)]
        return self._heights

    def height(self, phi):
        hs = self.heights()
        x = (phi % 1.0) * len(hs)
        i = int(x); t = x - i
        return lerp(hs[i % len(hs)], hs[(i + 1) % len(hs)], t)

    def spec(self, phi):
        """the pose spec at cycle phase phi (the left strike at 0; frame = (phi - offset) x n)"""
        g = self.g
        s = dict(turn=0.0, arm={}, foot={}, pole={})
        yaw, pitch, roll = self.pelvis_frame(phi)
        x, z = self.pelvis_xz(phi)
        s['pel'] = (x, self.height(phi), z)
        s['pyaw'], s['ppitch'], s['proll'] = yaw, pitch, roll
        cyaw = rad(g['chest_yaw']) + rad(g['chest_amp']) * math.cos(TAU * (phi - 0.02))
        b = g['duty']
        s['cyaw'] = cyaw
        s['cpitch'] = rad(g['lean']) + rad(1.5) * math.cos(2 * TAU * (phi - g['bob_low'] - 0.12))
        s['croll'] = -0.5 * roll
        # the head keeps its line: it undoes the chest's yaw and lean, and nods a little after the bob
        s['hyaw'] = rad(g['head_yaw']) - cyaw
        s['hpitch'] = -s['cpitch'] + rad(4) + rad(g['nod']) * math.cos(2 * TAU * (phi - g['bob_low'] - 0.1))
        for side, sx in (('L', 1), ('R', -1)):
            a, f, d, _ = self.foot(side, phi - self.strikes[side])
            s['foot'][side] = (a, f, d)
            s['pole'][side] = norm((f[0] + 0.1 * sx, 0.0, max(0.3, f[2])))
            s['arm'][side] = self.arm(side, phi, cyaw)
        return s

    def arm(self, side, phi, cyaw):
        g = self.g
        sx = 1 if side == 'L' else -1
        # the right arm leads when the left leg does (phase 0); the arms trail the legs by `lag` frames
        swing = -sx * math.cos(TAU * (phi - g['lag'] / self.n))
        bend = -sx * math.cos(TAU * (phi - (g['lag'] + g['elbow_lag']) / self.n))   # more bend on the forward swing
        return arm_dirs(sx, g['arm'][0] + g['arm'][1] * swing, g['elbow'][0] + g['elbow'][1] * bend, g['abd'], cyaw)

    def frame_spec(self, f):
        return self.spec(f / self.n + self.off)


# ---- building animations: dense keys (the game interpolates keys linearly)
def cycle_keys(name, step=1):
    c = Cycle(name)
    return [(f, assemble(c.frame_spec(f))) for f in range(0, c.n + 1, step)]


# ---- one-shots: key poses as channels on monotone splines, the feet pinned to the floor
BODY = ('turn', 'px', 'py', 'pz', 'pyaw', 'ppitch', 'proll', 'cyaw', 'cpitch', 'croll', 'hyaw', 'hpitch', 'flip')
ANGLES = {'turn', 'pyaw', 'cyaw', 'hyaw', 'oL', 'oR', 'flip'}


def to_channels(s, X):
    """a spec -> flat channels: the body in the body frame; the arms as directions; each foot in the model frame (the
    floor's frame, the facing the action started in) by the floor position of its ball (z in the world: + X, the body's
    travel; a planted boot that turns, turns about its ball), x, lift (its pivot's height over the floor), pitch and toe
    yaw"""
    ch = dict(turn=s['turn'], px=s['pel'][0], py=s['pel'][1], pz=s['pel'][2], pyaw=s['pyaw'], ppitch=s['ppitch'],
              proll=s['proll'], cyaw=s['cyaw'], cpitch=s['cpitch'], croll=s['croll'], hyaw=s['hyaw'], hpitch=s['hpitch'],
              flip=s.get('flip', 0.0))
    psi = s['turn']
    for side in 'LR':
        u, v = s['arm'][side]
        ch['u' + side], ch['v' + side] = u, v
        ankle, f, d = (roty(x, psi) for x in s['foot'][side])
        pitch = math.asin(max(-1.0, min(1.0, f[1])))
        toe = math.atan2(f[0], f[2])
        f0 = (math.sin(toe), 0.0, math.cos(toe))
        if pitch >= 0:
            piv = add(ankle, mul(f, -HEEL), mul(d, SOLE))
            flat = add(piv, mul(f0, HEEL))
        else:
            piv = add(ankle, mul(f, BALL), mul(d, SOLE))
            flat = add(piv, mul(f0, -BALL))
        ball = add(flat, mul(f0, BALL))                     # stored by the ball, so a planted boot turns about it
        ch['F' + side], ch['x' + side], ch['l' + side] = ball[2] + X, ball[0], piv[1]
        ch['t' + side], ch['o' + side] = pitch, toe
    return ch


def from_channels(ch, X):
    s = dict(turn=ch['turn'], pel=(ch['px'], ch['py'], ch['pz']), arm={}, foot={}, pole={})
    for k in BODY[4:]:
        s[k] = ch[k]
    psi = ch['turn']
    for side, sx in (('L', 1), ('R', -1)):
        s['arm'][side] = (norm(ch['u' + side]), norm(ch['v' + side]))
        o = ch['o' + side]
        ankle, f, d = boot(ch['F' + side] - X - BALL * math.cos(o), ch['x' + side] - BALL * math.sin(o), ch['t' + side], o)
        ankle = add(ankle, (0.0, ch['l' + side], 0.0))
        toe = ch['o' + side]
        pole = norm((math.sin(toe) + 0.1 * sx, 0.0, max(0.3, math.cos(toe))))
        s['foot'][side] = tuple(roty(x, -psi) for x in (ankle, f, d))
        s['pole'][side] = roty(pole, -psi)
    return s


def pchip(xs, ys):
    """monotone cubic interpolation (Fritsch-Carlson): no overshoot, and equal neighbouring keys hold exactly"""
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    if n == 2:
        m = [d[0], d[0]]
    else:
        m[0], m[-1] = d[0], d[-1]
        for i in range(1, n - 1):
            if d[i - 1] * d[i] <= 0:
                m[i] = 0.0
            else:
                w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
                m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
        for i in (0, n - 1):                                     # keep the ends monotone
            j = 0 if i == 0 else n - 2
            if m[i] * d[j] <= 0: m[i] = 0.0
            elif abs(m[i]) > 3 * abs(d[j]): m[i] = 3 * d[j]

    def f(x):
        if x <= xs[0]: return ys[0]
        if x >= xs[-1]: return ys[-1]
        i = max(k for k in range(n - 1) if xs[k] <= x)
        t = (x - xs[i]) / h[i]
        return hermite(ys[i], ys[i + 1], m[i] * h[i], m[i + 1] * h[i], t)
    return f


class Clip:
    """A one-shot: key channel sets at frames, interpolated channel by channel; X(f) is the body's travel along the
    facing the action started in (world units, the engine's own speeds), which pins every foot whose floor position
    holds still between keys."""
    def __init__(self, n, X, keys):
        self.n, self.X, self.keys = n, X, sorted(keys, key=lambda k: k[0])
        fr = [k[0] for k in self.keys]
        self.curves = {}
        for name in self.keys[0][1]:
            vals = [k[1][name] for k in self.keys]
            if name in ANGLES:                                   # keep each angle within a half turn of the key before
                for i in range(1, len(vals)):
                    vals[i] += TAU * round((vals[i - 1] - vals[i]) / TAU)
            if isinstance(vals[0], tuple):
                self.curves[name] = [pchip(fr, [v[i] for v in vals]) for i in range(len(vals[0]))]
            else:
                self.curves[name] = pchip(fr, vals)

    def channels(self, f):
        return {k: (tuple(c(f) for c in cv) if isinstance(cv, list) else cv(f)) for k, cv in self.curves.items()}

    def spec(self, f):
        return from_channels(self.channels(f), self.X(f))

    def keyed(self):
        return [(f, assemble(self.spec(f))) for f in range(self.n + 1)]


def travel(vs):
    """X(f) from per-frame displacements vs[k] (the move from frame k-1 to k), linear between frames"""
    cum = [0.0]
    for v in vs[1:]: cum.append(cum[-1] + v)
    def X(f):
        if f <= 0: return 0.0
        i = int(f)
        if i >= len(cum) - 1: return cum[-1] + (f - (len(cum) - 1)) * (vs[-1] if vs else 0.0)
        return lerp(cum[i], cum[i + 1], f - i)
    return X


def body_key(base, **kw):
    """channels from a base channel set, with body overrides in degrees (pyaw, ppitch, proll, cyaw, cpitch, croll, hyaw,
    hpitch), pel=(x, y, z), and arms=((L swing, elbow, abd), (R swing, elbow, abd)) in the chest's yaw"""
    ch = dict(base)
    for k in ('pyaw', 'ppitch', 'proll', 'cyaw', 'cpitch', 'croll', 'hyaw', 'hpitch', 'turn', 'flip'):
        if k in kw: ch[k] = rad(kw[k])
    if 'pel' in kw: ch['px'], ch['py'], ch['pz'] = kw['pel']
    if 'arms' in kw:
        for side, sx, a in (('L', 1, kw['arms'][0]), ('R', -1, kw['arms'][1])):
            ch['u' + side], ch['v' + side] = arm_dirs(sx, *a, ch['cyaw'])
    for side in 'LR':
        if side in kw:          # a foot: F and x where its flat ankle stands (at its toe yaw o), or B and bx where its ball
            d = kw[side]        # does; l (lift), t (pitch, deg), o (toe yaw, deg)
            for k, v in d.items():
                if k in ('t', 'o', 'l'): ch[k + side] = rad(v) if k != 'l' else v
            o = ch['o' + side]
            if 'B' in d: ch['F' + side] = d['B']
            elif 'F' in d: ch['F' + side] = d['F'] + BALL * math.cos(o)
            if 'bx' in d: ch['x' + side] = d['bx']
            elif 'x' in d: ch['x' + side] = d['x'] + BALL * math.sin(o)
    return ch


# The engine's own speeds, per animation frame k (the move from frame k-1 to k), measured in game (walk_lab: POS, and the
# FEET cue's animation frame):
#  - Dash: Dash_Enter plays its first frame on entry, so frame 1 is the first on screen (frame 0, Wait1's pose, never
#    shows). Held: 1.45, 1.55, then the run speed 1.6; Run takes over after frame 10, so frame 11 is Run frame 0.
#    Released, it loses 0.08 a frame (Fox's traction) from wherever the stick let go, and frame 17 is Wait1 frame 0.
#  - RunBrake: from 1.6, 0.08 a frame; the script's flag at 11 freezes the pose until he stops, then 11-18 play standing.
#  - TurnRun: from 1.6, 0.1 a frame to a stop (frame 9 holds, the script's flag, until then); then 0.1 a frame faster the
#    other way, and Run from frame 17 (the new facing).
# the drive frames average a dash from standing (0, 1.45, 1.55, 1.6) and a dash-dance dash, which starts against its
# own momentum (-0.32, 1.13, 1.23, 1.33...), so the drive boot slips about half a unit in either; the strike and the
# hand-over to Run are exact at the run speed; a released dash's stop averages a tap and a longer press
DASH_V = [0, 0, 1.29, 1.39, 1.47, 1.52, 1.57, 1.6, 1.6, 1.6, 1.6, 1.6, 0.9, 0.82, 0.74, 0.66, 0.58, 0.0, 0.0]
DASH_RUN = 11          # the dash's frame 11 is the run's frame 0
DASH_STRIKE = 9        # the right heel lands (the run's frame 16)


def run_key(f_run, X):
    return to_channels(Cycle('Run').frame_spec(f_run), X)


def dash():
    n = 18
    X = travel(DASH_V)
    W = to_channels(wait_spec(), 0.0)
    R0 = run_key(0, X(DASH_RUN))
    rF = R0['FR']                                              # where the right boot plants (the run's own stance)
    k = {}
    k[0] = W
    # 1 (the first frame on screen; he has not moved yet): the load. The pelvis drops and tips forward, the rear (right)
    # heel lifts off its ball, the arms cock
    k[1] = body_key(W, pel=(0.0, 5.12, 0.15), pyaw=-16, ppitch=8, cyaw=-12, cpitch=18, hyaw=5, hpitch=-14,
                    arms=((30, 46, 14), (-32, 36, 16)),
                    L=dict(F=1.8, t=0, o=8, x=1.25), R=dict(F=-2.0, t=-30, o=-8, x=-1.25))
    # 2-4: the drive. The right foot leaves, heel flicking up, and its knee drives through; the left pushes off its ball
    k[2] = body_key(W, pel=(0.0, 5.0, 0.25), pyaw=-9, ppitch=12, cyaw=-6, cpitch=26, hyaw=3, hpitch=-22,
                    arms=((46, 60, 15), (-46, 44, 17)),
                    L=dict(F=1.8, t=-10, o=6, x=1.2), R=dict(F=X(2) - 2.65, t=-55, o=-6, x=-1.18, l=0.9))
    k[3] = body_key(W, pel=(0.0, 5.05, 0.3), pyaw=-4, ppitch=15, cyaw=-2, cpitch=38, hyaw=2, hpitch=-33,
                    arms=((55, 72, 16), (-50, 52, 18)),
                    L=dict(F=1.8, t=-25, o=4, x=1.15), R=dict(F=X(3) - 1.2, t=-40, o=-4, x=-1.12, l=1.5))
    k[4] = body_key(W, pel=(0.0, 5.2, 0.3), pyaw=0, ppitch=16, cyaw=0, cpitch=44, hyaw=0, hpitch=-39,
                    arms=((54, 80, 17), (-48, 58, 18)),
                    L=dict(F=1.8, t=-45, o=3, x=1.12), R=dict(F=X(4) + 0.7, t=-15, o=-3, x=-1.1, l=1.85))
    # 5-8: off the floor: the lunge, left leg trailing, right knee high then reaching for the floor
    k[5] = body_key(W, pel=(0.0, 5.35, 0.25), pyaw=3, ppitch=16, cyaw=-1, cpitch=46, hyaw=1, hpitch=-41,
                    arms=((48, 84, 17), (-42, 64, 18)),
                    L=dict(F=X(5) - 3.7, t=-62, o=3, x=1.1, l=0.55), R=dict(F=X(5) + 2.3, t=0, o=-3, x=-1.1, l=1.75))
    k[6] = body_key(W, pel=(0.0, 5.42, 0.2), pyaw=5, ppitch=16, cyaw=-2, cpitch=44, hyaw=2, hpitch=-39,
                    arms=((34, 86, 17), (-30, 70, 18)),
                    L=dict(F=X(6) - 3.7, t=-64, o=3, x=1.1, l=1.5), R=dict(F=X(6) + 3.2, t=8, o=-3, x=-1.1, l=1.3))
    k[7] = body_key(W, pel=(0.0, 5.32, 0.15), pyaw=5, ppitch=15, cyaw=-4, cpitch=40, hyaw=4, hpitch=-35,
                    arms=((18, 84, 17), (-14, 76, 18)),
                    L=dict(F=X(7) - 2.9, t=-55, o=3, x=1.1, l=2.2), R=dict(F=X(7) + 3.7, t=12, o=-3, x=-1.1, l=0.8))
    k[8] = body_key(W, pel=(0.0, 5.12, 0.1), pyaw=4, ppitch=15, cyaw=-4, cpitch=37, hyaw=4, hpitch=-32,
                    arms=((8, 80, 17), (-6, 78, 18)),
                    L=dict(F=X(8) - 1.7, t=-45, o=3, x=1.1, l=2.4), R=dict(F=X(8) + 3.5, t=12, o=-3, x=-1.1, l=0.35))
    # 9-11: the right heel lands where the run's stance has it, and the dash becomes the run's frames 16, 17, 0
    for f, fr in ((9, 16), (10, 17), (11, 0)):
        c = run_key(fr, X(f))
        c['FR'], c['lR'] = rF, 0.0
        if f == DASH_STRIKE: c['tR'] = max(c['tR'], rad(10))
        k[f] = c
    # 11-17 (a released dash plays out): the left boot swings through and plants as a brake, both skid, and he settles
    # into Wait1's stance; frame 17 is Wait1 frame 0 (a released dash hands over to Wait there)
    k[12] = body_key(R0, pel=(0.0, 5.0, 0.05), pyaw=-6, ppitch=6, cyaw=-6, cpitch=14, hyaw=2, hpitch=-8,
                     arms=((10, 60, 16), (-12, 50, 16)),
                     L=dict(F=X(12) + 3.0, t=18, o=6, x=1.2, l=0.35), R=dict(F=rF, t=-20, o=-6, x=-1.2, l=0.0))
    k[13] = body_key(k[12], pel=(0.0, 4.95, -0.05), ppitch=3, cpitch=6, hpitch=-2, arms=((4, 50, 15), (-6, 44, 15)),
                     L=dict(F=X(13) + 2.7, t=16, l=0.0), R=dict(F=X(13) - 3.1, t=-26, l=0.0))
    k[15] = body_key(k[13], pel=(0.0, 5.12, -0.05), pyaw=-18, ppitch=0, cyaw=-18, cpitch=4, hyaw=6, hpitch=0,
                     arms=((2, 34, 14), (-2, 32, 14)),
                     L=dict(F=X(15) + 2.1, t=4, o=12, l=0.0), R=dict(F=X(15) - 2.3, t=-10, o=-12, l=0.25))
    k[17] = dict(W); k[18] = dict(W)
    for f in (17, 18):
        for side in 'LR':
            k[f]['F' + side] = W['F' + side] + X(f)
    return Clip(n, X, list(k.items()))


BRAKE_V = [0] + [1.52 - 0.08 * k for k in range(1, 12)] + [0.0] * 7     # frames 12+: he has stopped (the hold at 11)
BRAKE_HOLD = 11


def brake():
    """RunBrake, 18 frames: the left boot swings through and plants ahead, heel dug in, and both boots skid while he sits
    back against the slide; the pose at 11 holds (the script's flag) until he stops; then he rises, the front boot steps
    back into the idle's stagger, and frame 17 is Wait1 frame 0."""
    n = 18
    X = travel(BRAKE_V)
    W = to_channels(wait_spec(), 0.0)
    k = {0: run_key(0, 0.0)}
    k[2] = body_key(k[0], pel=(0.0, 4.95, -0.1), pyaw=-6, ppitch=6, proll=0, cyaw=-4, cpitch=12, croll=0, hyaw=2,
                    hpitch=-8, arms=((34, 62, 20), (18, 70, 22)),
                    L=dict(F=X(2) + 3.2, t=22, o=8, x=1.2, l=0.45), R=dict(F=X(2) - 1.4, t=-24, o=-8, x=-1.2, l=0.0))
    k[3] = body_key(k[2], pel=(0.0, 4.7, -0.35), ppitch=2, cpitch=4, hpitch=-2, arms=((40, 58, 22), (26, 66, 24)),
                    L=dict(F=X(3) + 3.0, t=24, l=0.0), R=dict(F=X(3) - 1.8, t=-18, l=0.0))
    # the skid: both boots ride the slide (their floor position moves with him), the body sits back and judders a little
    for f, y, cp, ar in ((5, 4.55, -4, (44, 54)), (7, 4.6, -6, (40, 58)), (9, 4.56, -5, (42, 56)), (11, 4.6, -6, (40, 58))):
        k[f] = body_key(k[3], pel=(0.0, y, -0.45), ppitch=-2, cpitch=cp, hpitch=-cp + 2,
                        arms=((ar[0], ar[1], 22), (ar[0] - 14, ar[1] + 8, 24)),
                        L=dict(F=X(f) + 2.9, t=22), R=dict(F=X(f) - 2.0, t=-16))
    # standing up (he has stopped: X holds): the front boot steps back to the idle's +1.8, the rear heel settles
    k[13] = body_key(k[11], pel=(0.0, 4.95, -0.3), pyaw=-14, ppitch=0, cyaw=-12, cpitch=4, hyaw=6, hpitch=-2,
                     arms=((22, 44, 18), (8, 44, 18)), L=dict(F=X(13) + 2.5, t=6, o=12, l=0.45), R=dict(F=X(13) - 2.0, t=-6, o=-12))
    k[15] = body_key(k[13], pel=(0.0, 5.4, -0.05), pyaw=-22, cyaw=-22, cpitch=6, hyaw=10, hpitch=0,
                     arms=((8, 30, 15), (4, 30, 15)), L=dict(F=X(15) + 1.8, t=0, o=14, l=0.0), R=dict(F=X(15) - 2.0, t=0, o=-14))
    for f in (17, 18):
        k[f] = dict(W)
        for side in 'LR': k[f]['F' + side] = W['F' + side] + X(f)
    return Clip(n, X, list(k.items()))


# frames 0-9 slow from 1.6 by 0.1; the hold at 9 slides the last 1.4; then the other way, 0.1 faster each frame
TURN_V = [0] + [1.5 - 0.1 * k for k in range(1, 10)] + [1.4 - 0.2] + [-0.1 * j for j in range(3, 10)] + [-1.0]
TURN_HOLD = 9


def turnrun():
    """TurnRun, 18 frames in the old facing: the left boot plants ahead and he pivots a quarter turn toward the camera
    into a low sideways skid (frame 9 holds, the script's flag, until the slide stops); then he finishes the half turn,
    pushes off the left boot and runs: frame 17 is Run frame 0 turned half round (the engine flips his facing there)."""
    n = 18
    X = travel(TURN_V)
    k = {0: run_key(0, 0.0)}
    k[2] = body_key(k[0], turn=-12, pel=(0.0, 4.9, -0.1), pyaw=-10, ppitch=4, cyaw=-12, cpitch=10, hyaw=-20, hpitch=-6,
                    arms=((30, 64, 22), (20, 70, 24)),
                    L=dict(F=X(2) + 3.0, t=22, o=-10, x=1.2, l=0.3), R=dict(F=X(2) - 1.6, t=-22, o=-14, x=-1.2, l=0.0))
    k[4] = body_key(k[2], turn=-55, pel=(0.1, 4.6, -0.2), pyaw=-4, ppitch=0, proll=-6, cyaw=-6, cpitch=2, croll=-8,
                    hyaw=-28, hpitch=-2, arms=((36, 60, 30), (40, 62, 34)),
                    L=dict(F=X(4) + 2.9, t=18, o=-40, x=1.0, l=0.0), R=dict(F=X(4) - 2.6, t=-10, o=-50, x=-0.9, l=0.0))
    k[7] = body_key(k[4], turn=-85, pel=(0.15, 4.5, -0.1), pyaw=0, proll=-9, cyaw=-2, cpitch=0, croll=-12, hyaw=-34,
                    arms=((40, 58, 36), (44, 60, 40)),
                    L=dict(F=X(7) + 2.9, t=14, o=-70, x=0.6), R=dict(F=X(7) - 3.0, t=-4, o=-80, x=-0.5))
    # the push the other way. Frame 9 holds while he slides to a stop (the boots ride along), so frame 10's boots stand
    # where frame 9 left them relative to his body; from there the right boot (the new front) is planted and turns on its
    # ball while he comes round over it, and the left drives off its ball and swings through into the run
    R17 = Cycle('Run').frame_spec(0)
    R17['turn'] = -math.pi
    end = to_channels(R17, X(17))
    rB, rX = end['FR'], end['xR']
    lB = X(10) + 2.3                                      # the left ball: planted ahead (the old way) through the hold
    k[9] = body_key(k[7], turn=-95, pel=(0.15, 4.5, -0.1), proll=-8, croll=-10, hyaw=-38,
                    L=dict(B=lB - (X(10) - X(9)), bx=0.6, t=10, o=-85), R=dict(B=X(9) - 3.0, bx=-0.5, t=-4, o=-95))
    k[10] = body_key(k[9], turn=-105, pel=(0.1, 4.55, 0.0), proll=-6, croll=-6, hyaw=-30,
                     L=dict(B=lB, bx=0.6, t=4, o=-90), R=dict(B=X(10) - 3.0, bx=-0.5, t=-12, o=-112, l=0.25))
    k[12] = body_key(k[10], turn=-138, pel=(0.05, 4.7, 0.1), pyaw=4, ppitch=8, proll=-2, cyaw=0, cpitch=16, croll=-2,
                     hyaw=-14, hpitch=-12, arms=((-10, 70, 20), (34, 76, 20)),
                     L=dict(B=lB, bx=0.6, t=-30, o=-122), R=dict(B=5.7, bx=-0.8, t=-4, o=-150, l=0.95))
    k[13] = body_key(k[12], turn=-156, pel=(0.02, 4.8, 0.12), pyaw=5, ppitch=10, cyaw=1, cpitch=21, croll=-1, hyaw=-8,
                     hpitch=-17, arms=((-20, 74, 19), (38, 78, 19)),
                     L=dict(B=lB - 0.3, bx=0.7, t=-52, o=-142, l=0.35), R=dict(B=5.1, bx=-1.0, t=6, o=-168, l=0.55))
    k[15] = body_key(k[13], turn=-178, pel=(0.0, 4.85, 0.15), pyaw=4, ppitch=11, cyaw=1, cpitch=26, croll=0, hyaw=-2,
                     hpitch=-22, arms=((-34, 78, 18), (42, 80, 18)),
                     L=dict(B=lB - 2.2, bx=1.0, t=-60, o=-175, l=1.6), R=dict(B=rB, bx=rX, t=10, o=-180, l=0.0))
    k[17] = end
    k[18] = dict(end)
    k[18]['FL'] = end['FL'] - X(17) + X(18)
    return Clip(n, X, list(k.items()))


# ---- footfalls and scripts
def footfalls(name):
    """(frame, side, event) for a cycle: 'strike' when a heel lands, 'off' when a toe leaves (rounded frames)"""
    c = Cycle(name)
    out = []
    for side, st in c.strikes.items():
        for ev, ph in (('strike', st), ('off', st + c.g['duty'])):
            out.append((int(round(((ph - c.off) % 1.0) * c.n)) % c.n, side, ev))
    return sorted(out)


def _w(x): return bytes.fromhex(x)
def _timer(f): return (0x08000000 | int(f)).to_bytes(4, 'big')
LOOP = (0x0C000000 | 0x3FFFFFF).to_bytes(4, 'big')        # SetLoop: 67 million passes (no pointer, unlike GoTo)
LOOP_END = _w('10000000')                                   # ExecuteLoop
WAIT_WRAP = _w('20000000')                                  # SetTimerAnimation: wait until the animation wraps
END = _w('00000000')
# FootstepEffect (0x36: dust at the left or right foot bone, the floor's own step sound, else 443) and Rumble, as
# Mario's walk and run templates have them; GraphicEffect dust (ids 1022 run puff, 1023 dash, 1025 skid) on TransN
STEP = {'L': 'D8000000000001BB0000', 'R': 'D8020000000001BB0000'}
RUMBLE = {'walk': 'AC026000', 'run': 'AC02A000', 'dash': 'AC028000'}
GFX = {'run': '2800000003FE0000000000000000000000000000', 'dash': '2800000003FF0000000000000000000000000000',
       'skid': '2800000004010000000000000000000000000000'}


def scripts():
    """Geno's own scripts for the looping walks and run (their footsteps land on the new footfalls) and for Dash and
    TurnRun (the dash dust at the push-off; TurnRun's hold flag at 9, where its skid holds, instead of the template's 18,
    which was the 18-frame animation's last frame, so the turnaround ended before the flag and he stood, then turned).
    The wooden steps (bank 55) for Dash, TurnRun and RunBrake come from sound/wiring.py's cues."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sound'))
    import wiring
    I = wiring.ID
    out = {}
    for name, vol, kind in (('WalkSlow', 0x64, 'walk'), ('WalkMiddle', 0x6E, 'walk'), ('WalkFast', 0x6E, 'walk'),
                            ('Run', 0x7F, 'run')):
        ev = footfalls(name)
        steps = [(f, s) for f, s, e in ev if e == 'strike']
        wood = {'L': I['STEP_RUN_L' if kind == 'run' else 'STEP_WALK_L'], 'R': I['STEP_RUN_R' if kind == 'run' else 'STEP_WALK_R']}
        def step(s):
            return _w(STEP[s] + f'{vol:02X}40') + _w(RUMBLE[kind]) + wiring.cue(wood[s], vol)
        body = b''
        at0 = [s for f, s in steps if f == 0]
        for f, s in steps:
            if f == 0: continue
            body += _timer(f) + step(s)
        if kind == 'run':                                      # a puff of dust as each toe leaves
            evs = sorted([(f, s, 'step') for f, s in steps] + [(f, s, 'off') for f, s, e in ev if e == 'off'])
            body = b''
            for f, s, e in evs:
                body += _timer(f) + (step(s) if e == 'step' else _w(GFX['run']))
        # a step on frame 0 fires as the loop wraps (not on entry: from Wait he is already standing on it)
        out[name] = LOOP + body + WAIT_WRAP + b''.join(step(s) for s in at0) + LOOP_END + END
    # Dash: Mario's commands (rumble, the dash sound, the run flag at 11) with the dust at the push-off
    out['Dash'] = (_timer(0) + _w(RUMBLE['dash']) + _w('440000000000000000007F40') + _w('4C000000') +
                   _timer(2) + _w(GFX['dash']) + _timer(11) + _w('4C000001') + END)
    out['TurnRun'] = (_timer(0) + _w('A0000004A0040004') + _w(GFX['skid']) + _timer(6) + _w('A0000000A0040000') +
                      _timer(TURN_HOLD) + _w(GFX['skid']) + _w('4D000001') + END)
    return {k: v.hex().upper() for k, v in out.items()}


# The engine blends into an action from the pose before it over ftData+0x10's frames whenever the caller passes no blend
# (Fighter_ChangeMotionState): 6 on Wait1, the walks and Run in every template. A blend holds the old pose still while
# the body moves, so a planted boot drifts forward through it (in game: 3.3 units over the run's first four frames out of
# the dash). The run is only ever entered where its frame 0 is already on screen (Dash frame 10, TurnRun's end), so it
# cuts cleanly instead; the walks keep theirs, which smooths their speed changes (their frame counts differ).
BLEND = {'Run': 0}


ONESHOTS = {'Dash': dash, 'RunBrake': brake, 'TurnRun': turnrun}


def anim(name):
    """(frames, keys) for a locomotion action, or None"""
    if name in GAITS:
        c = Cycle(name)
        return c.n, cycle_keys(name)
    if name in ONESHOTS:
        c = ONESHOTS[name]()
        return c.n, c.keyed()
    return None


def report(name):
    """numbers for a cycle: reach, knee bend, pelvis, feet"""
    c = Cycle(name)
    rows = []
    for f in range(c.n):
        s = c.frame_spec(f)
        r = reach(s)
        rows.append((f, s['pel'][1], r['L'], r['R'], knee_bend(r['L'] * LEG), knee_bend(r['R'] * LEG)))
    rmax = max(max(r[2], r[3]) for r in rows)
    kmin = min(min(r[4], r[5]) for r in rows)
    kmax = max(max(r[4], r[5]) for r in rows)
    hs = [r[1] for r in rows]
    print(f'{name}: n={c.n} v={c.v} stride={c.S:.2f} ({c.S / LEG:.2f} L) duty={c.g["duty"]} reach max {rmax:.3f} knee '
          f'{kmin:.0f}-{kmax:.0f} deg, pelvis {min(hs):.2f}-{max(hs):.2f} (bob {max(hs) - min(hs):.2f})')
    return rows


if __name__ == '__main__':
    for nm in (sys.argv[1:] or list(GAITS)):
        report(nm)


# ---- checks on the solved poses (what the game will play)
def sole_points(W, side):
    """world positions of the boot's heel and ball pivots (the sole under them), from FootJ's world matrix"""
    m = W[f'{side}FootJ']
    return [rig.xform((a, SOLE, 0.0), m) for a in (-HEEL, BALL)]


def slide(name, keys=None, speed=None, tol=0.03):
    """Foot slide of a cycle as the game plays it: each frame's pose, carried forward at the attribute speed; a sole pivot
    counts as planted while it is within tol of the floor. Returns per foot the worst drift (world units) of a planted
    pivot over one stance, and the worst frame-to-frame slip."""
    if keys is None:
        c = Cycle(name); keys = cycle_keys(name); speed = c.v
    out = {}
    for side in 'LR':
        pts = []
        for f, pose in keys:
            W = rig.world_mats(pose={k: {'t': v[0], 'r': v[1]} for k, v in pose.solve().items()})
            pts.append([(p[0], p[1], p[2] + speed * f) for p in sole_points(W, side)])
        worst, slip = 0.0, 0.0
        for k in range(2):                                   # heel, ball
            run = []
            for i, fr in enumerate(pts):
                if fr[k][1] < tol:
                    run.append(fr[k])
                    if len(run) > 1:
                        slip = max(slip, math.hypot(run[-1][0] - run[-2][0], run[-1][2] - run[-2][2]))
                else:
                    if len(run) > 1:
                        worst = max(worst, max(math.hypot(a[0] - run[0][0], a[2] - run[0][2]) for a in run))
                    run = []
            if len(run) > 1:
                worst = max(worst, max(math.hypot(a[0] - run[0][0], a[2] - run[0][2]) for a in run))
        out[side] = (worst, slip)
    return out


def metrics(name):
    """the gait.py numbers for a cycle, straight from the specs (knee bend from the IK distance)"""
    c = Cycle(name)
    g = c.g
    out = dict(frames=c.n, stride_L=c.S / LEG, duty=g['duty'])
    ks, kw, ay = [], [], []
    for f in range(c.n):
        phi = f / c.n + c.off
        s = c.spec(phi)
        r = reach(s)
        for side in 'LR':
            p = (phi - c.strikes[side]) % 1.0
            k = knee_bend(r[side] * LEG)
            (ks if p <= g['duty'] else kw).append(k)
            ay.append((side, s['foot'][side][0][1]))
    a = [y for sd, y in ay if sd == 'L']
    hs = [c.height(f / c.n) for f in range(c.n)]
    out.update(knee_stance=(min(ks), max(ks)), knee_swing_max=max(kw), lift_L=(max(a) - min(a)) / LEG,
               bob_L=(max(hs) - min(hs)) / LEG, pelvis=(min(hs), max(hs)))
    return out


def approach(name):
    """how the heels come down: per foot, the worst horizontal speed (world units per animation frame) of a sole point
    while it hovers within 0.15 of the floor before touching (a skim reads as a skid into the step)"""
    c = Cycle(name)
    keys = [(f / 4, assemble(c.spec(f / 4 / c.n + c.off))) for f in range(4 * c.n + 1)]
    worst = 0.0
    for side in 'LR':
        prev = None
        for f, pose in keys:
            W = rig.world_mats(pose={k: {'t': v[0], 'r': v[1]} for k, v in pose.solve().items()})
            pts = [(p[0], p[1], p[2] + c.v * f) for p in sole_points(W, side)]
            if prev:
                for a, b in zip(prev, pts):
                    if 0.01 < b[1] < 0.15:
                        worst = max(worst, math.hypot(b[0] - a[0], b[2] - a[2]) * 4)
            prev = pts
    return worst


def lint(limit=0.975):
    """frames where a leg reaches past `limit` of its length (the knee near straight, where IK stops being smooth)"""
    out = []
    for name in list(GAITS) + list(ONESHOTS):
        if name in GAITS:
            c = Cycle(name)
            specs = [(f, c.frame_spec(f)) for f in range(c.n)]
        else:
            c = ONESHOTS[name]()
            specs = [(f, c.spec(f)) for f in range(c.n + 1)]
        for f, s in specs:
            for side, r in reach(s).items():
                if r > limit: out.append((name, f, side, round(r, 3)))
    return out
