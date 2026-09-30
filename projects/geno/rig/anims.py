"""Geno's blockout animations: key poses per action at exact frames, solved to the engine's Euler XYZ local rotations.

Poses are authored in world terms (where a bone points), then solved against the rig's rest frames, so a pose reads the
same whatever the local axis conventions. This first pass gives every action a placeholder motion by category, timed to
the action list's frame counts, so the body can be proven in game; the design-timed blockout replaces it move by move.

    .venv/bin/python projects/geno/rig/anims.py ACTIONS.txt OUT.json    # ACTIONS.txt: `datkit actions` output (names, frames)
"""
import json, math, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig

NAMES = [j[0] for j in rig.JOINTS]
REST = {j[0]: (j[2], j[3]) for j in rig.JOINTS}
PARENT = {j[0]: j[1] for j in rig.JOINTS}
ENGINE_OWNED = {'TopN', 'TransN2'}


# ---- rotation helpers (row vectors, rows of a rotation matrix are the local axes in world space)
def m3(m): return [row[:3] for row in m[:3]]
def mul3(a, b): return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def tr3(a): return [[a[j][i] for j in range(3)] for i in range(3)]
def norm(v):
    l = math.sqrt(sum(x * x for x in v)) or 1
    return [x / l for x in v]
def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def dot(a, b): return sum(x * y for x, y in zip(a, b))


def euler_xyz(M):
    ry = math.asin(max(-1, min(1, -M[0][2])))
    if abs(M[0][2]) < 0.9999:
        rz, rx = math.atan2(M[0][1], M[0][0]), math.atan2(M[1][2], M[2][2])
    else:
        rz, rx = 0.0, math.atan2(-M[2][1], M[1][1])
    return (rx, ry, rz)


class Pose:
    """Joint name -> (t, r) local overrides, built up by aims and local rotations, solved in hierarchy order; plus a
    per-joint scale (grow), exported as its own channel."""
    def __init__(self):
        self.aims, self.local, self.trans, self.scale = {}, {}, {}, {}

    def grow(self, joint, s):
        """Scale a joint about its origin, and with it everything it carries (the engine's classical scale: a child's
        offset and mesh grow with its parent), as the cast grow a limb on its hit frames for readability (Mario's jab:
        the upper arm 1.4 and the hand 1.6, a 2.24x fist; research/limb_scale.md). Uniform scales only where a child is
        aimed: solve() places rotations without scale, which a uniform parent scale leaves true. s: a factor or (x, y, z)."""
        self.scale[joint] = (float(s),) * 3 if isinstance(s, (int, float)) else tuple(float(v) for v in s)
        return self

    def aim(self, joint, x, up=None):
        """Point the joint's local +X (its bone) along world direction x; up (world) sets the twist."""
        self.aims[joint] = (norm(x), norm(up) if up else None)
        return self

    def rot(self, joint, r):
        self.local[joint] = r
        return self

    def move(self, joint, t):
        self.trans[joint] = t
        return self

    def solve(self):
        out, W = {}, {}
        for name, parent, t, r in rig.JOINTS:
            t = self.trans.get(name, t)
            if name in self.aims:
                x, up = self.aims[name]
                Pw = m3(W[parent]) if parent else [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
                rest_w = mul3(m3(rig.rot_xyz(*REST[name][1])), Pw)       # the rest frame in world, for the twist reference
                up = up or rest_w[1]
                y = norm([u - dot(up, x) * xi for u, xi in zip(up, x)])
                if dot(y, y) < 1e-6: y = norm(cross(rest_w[2], x))
                z = cross(x, y)
                Rl = mul3([x, y, z], tr3(Pw))
                r = euler_xyz(Rl)
            elif name in self.local:
                r = self.local[name]
            out[name] = (tuple(t), tuple(r))
            m = rig.local_mat(t, r)
            W[name] = rig.mat_mul(m, W[parent]) if parent else m
        return out


# ---- the vocabulary of poses (world directions; +Z is where he faces, +X his left, +Y up)
# The standing stance. The cast's Wait1 (disc, frame 0) staggers the feet along the facing axis by 18-42% of height (median
# ~31%; only DK stands square, and sideways), and feet side by side read as one spindly leg from the side-on camera. Samus
# (38%, left foot forward) turns her hips 20° toward the camera facing right, shoulders 9°, head 1°: Geno takes her stance
# (Michael: Samus-style), with toes turned out as in the remake art and the pelvis dropped so the knees stay soft, and turns
# further toward the camera (Michael chose B of three in game: hips 25°, shoulders 25°, head 10°; Samus's own numbers read
# as full profile on him). Feet in model units: fwd/back along +Z, lat either side (his hips are 1.0 out).
STANCE = dict(fwd=1.8, back=-2.0, lat=1.3, toe_out=0.26, drop=0.45, hip_yaw=-0.44, chest_yaw=0.0, head_yaw=0.26)
THIGH, SHIN = rig.LEG_TOP - rig.KNEE_Y, rig.KNEE_Y - rig.ANKLE_Y


def leg_ik(hip, ankle, pole):
    """Two-bone IK: thigh and shin directions that put the ankle at `ankle` (short of it if out of reach), knee toward pole."""
    d = [a - h for a, h in zip(ankle, hip)]
    u = norm(d)
    L = min(math.sqrt(dot(d, d)), (THIGH + SHIN) * 0.999)
    ca = (THIGH ** 2 + L ** 2 - SHIN ** 2) / (2 * THIGH * L)
    sa = math.sqrt(max(0.0, 1 - ca * ca))
    v = norm([p - dot(pole, u) * ui for p, ui in zip(pole, u)])
    knee = [THIGH * (ca * ui + sa * vi) for ui, vi in zip(u, v)]
    return knee, [L * ui - k for ui, k in zip(u, knee)]


def base(arms=0.0, crouch=0.0, lean=0.0, bob=0.0, stance=1.0):
    """Standing: arms down and a little forward, knees soft, feet planted in the stance. crouch 0..1 lowers the body over
    the planted feet. stance 0 is the square blockout stance (runs, crouch, lying down, hanging: poses that set the legs)."""
    p = Pose()
    S = STANCE
    yrot = (0, -2.2 * crouch + bob, 0.3 * crouch)
    p.move('YRotN', yrot)
    yaw, drop = S['hip_yaw'] * stance, S['drop'] * stance
    p.move('HipN', (0, rig.LEG_TOP - rig.HIP_Y - drop, 0)).rot('HipN', (0, yaw, 0))
    p.rot('WaistN', (0.12 + lean, S['chest_yaw'] * stance, 0))
    for hand in (rig.RELAXED_HAND, rig.mirror_hand(rig.RELAXED_HAND)):   # relaxed fingers unless a move keys its own
        for n, r in hand.items():
            p.rot(n, r)
    if stance: p.rot('HeadN', (0, S['head_yaw'] * stance, 0))
    pelvis = (0, rig.LEG_TOP - drop + yrot[1], yrot[2])
    across = (math.cos(yaw), 0, -math.sin(yaw))             # HipN's +X (his left) in world, turned by the yaw
    for s, sx in (('L', 1), ('R', -1)):
        p.aim(f'{s}ShoulderJ', (sx * (0.28 + 0.5 * arms), -1 + arms, 0.12))
        p.aim(f'{s}ArmJ', (sx * (0.15 + 0.3 * arms), -0.9 + arms, 0.45))
        toe = sx * S['toe_out'] * stance
        f = (math.sin(toe), 0, math.cos(toe))                       # the foot's forward, level
        heel = 0.0
        if stance:
            hip = [c + sx * rig.HIP_X * a for c, a in zip(pelvis, across)]
            planted = (sx * S['lat'], rig.ANKLE_Y, (S['fwd'] if sx > 0 else S['back']) * stance)
            ankle = planted
            for _ in range(4):                                     # the heel lift moves the ankle, which eases the lean
                thigh, shin = leg_ik(hip, ankle, f)                 # knees track over the toes
                heel, ankle = heel_lift(planted, f, shin)
            p.aim(f'{s}LegJ', thigh)
            p.aim(f'{s}KneeJ', shin)
        else:
            k = 0.2 + 1.3 * crouch
            p.aim(f'{s}LegJ', (sx * 0.05, -1, k * 0.6))
            p.aim(f'{s}KneeJ', (0, -1, -k * 0.55))
        # FootJ's local Y points down in the bind pose (FootJA's rest turn), so `up` is the way the sole faces. A lifted
        # heel pitches the foot toe-down about the ball of the foot.
        c, sn = math.cos(heel), math.sin(heel)
        p.aim(f'{s}FootJ', (f[0] * c, -sn, f[2] * c), up=(-f[0] * sn, -c, -f[2] * sn))
    return p


ANKLE_FLEX, HEEL_MAX, BALL = math.radians(35), math.radians(40), 1.3   # the boot is one rigid loaf: pivot near its toe


def heel_lift(planted, f, shin):
    """A planted foot's heel rises once the shin leans forward past ANKLE_FLEX, pivoting BALL ahead of the ankle, as a
    person's rear heel does in a deep crouch. The idle's rear shin (34°) stays under it and keeps the foot flat; the boot's
    cuff follows the shin in the model, so the ankle bend itself doesn't clip. Returns (heel pitch, the ankle's new position)."""
    d = norm([-x for x in shin])                                 # ankle -> knee
    lean = math.atan2(dot(d, f), d[1])                           # forward lean of the shin in the foot's plane
    th = min(HEEL_MAX, max(0.0, lean - ANKLE_FLEX))
    h = planted[1]                                               # the ankle's height over the sole
    du = -BALL * math.cos(th) + h * math.sin(th) + BALL          # the ankle moves forward and up about the ball
    dv = BALL * math.sin(th) + h * math.cos(th) - h
    return th, (planted[0] + f[0] * du, planted[1] + dv, planted[2] + f[2] * du)


# ThrowN in YRotN's frame while shielding: the shield sphere's centre. shieldfit.py finds the centre that needs the smallest
# sphere around the guard pose's hurtboxes; this one also sits on the body's middle front to back (within 0.2), since the
# stance turned toward the camera (hips and shoulders 25°) moved the body 1.5 forward of the old centre. At full shield
# (radius 7.9) head and knees sit 0.66 inside and the cap 0.6, so nothing pokes; a worn shield starts to show the head and
# knees, as it should.
SHIELD_CENTRE = (0, 0.96, 1.1)
# The shield's tilt: the Guard animation (370 frames) is a table the engine samples at 10 + the stick's angle (0 forward,
# 90 up), blended by how far the stick is pushed. Mario's ThrowN path (his Guard, node 59) from his neutral centre, as
# (degrees, up, forward), scaled by the two shields' full radii (7.9 / 6.8).
TILT = [(0, 0, 2.5), (45, 2.7, 1.8), (90, 4.0, 0), (135, 2.7, -2.35), (180, 0, -3.0), (225, -2.2, -1.75), (270, -3.3, -0.1),
        (315, -2.15, 1.5), (360, 0, 2.5)]
TILT_SCALE = 7.9 / 6.8


def guard_pose(centre=None):
    """Shielding: knees bent, arms drawn in front, the head ducked and the cap's point flopped down behind him (so the whole
    model fits the bubble, not only the hurtboxes), ThrowN (the shield's centre) at the middle of the body."""
    return base(crouch=0.35, arms=0.5).rot('HeadN', (0.3, 0, 0)).rot('CapMidN', (-1.2, 0, 0)).rot('CapTipN', (-1.0, 0, 0)) \
        .move('ThrowN', centre or SHIELD_CENTRE)


def crouch_pose():
    """Crouching: states_air.crouch_pose() (the boots planted in the idle's stagger by IK, the body folded forward over
    the knees, the head up; hurtbox top 10.5, Fox's crouch-to-stand ratio), so the crouch, the crouching attacks and
    anything else that starts from the crouch all meet it."""
    import states_air
    return states_air.crouch_pose()


def crouch_pose_blockout():
    """The blockout crouch (feet side by side, the head rolled onto its side: its hurtbox top was 9.5)."""
    p = base(lean=0.3, stance=0)
    p.move('YRotN', (0, -3.0, 0.5))
    p.aim('HeadN', (0, 1, 0.25))
    for s, sx in (('L', 1), ('R', -1)):
        p.aim(f'{s}LegJ', (sx * 0.25, -0.5, 1)); p.aim(f'{s}KneeJ', (0, -0.45, -0.9))
        p.aim(f'{s}FootJ', (0, 0, 1), up=(0, -1, 0))           # sole down (see base)
        p.aim(f'{s}ShoulderJ', (sx * 0.35, -0.8, 0.6)); p.aim(f'{s}ArmJ', (sx * 0.2, -0.6, 0.8))
    return p


def stride(phase, amp=0.8, arms=0.0, crouch=0.1, bob=0.15):
    """A single stepping pose at phase 0..1 (legs apart, arms counter-swung), for one-off steps like the ledge climb's step
    onto the stage (states.py). Not the locomotion: walks, runs and dashes are locomotion.py's foot paths and IK."""
    p = base(arms=arms, crouch=crouch, bob=bob * abs(math.cos(2 * math.pi * phase)), stance=0)   # runs are side-on
    s = math.sin(2 * math.pi * phase)
    for side, sx, sign in (('L', 1, 1), ('R', -1, -1)):
        swing = sign * s * amp
        lift = max(0, -sign * s) * amp * 0.9
        p.aim(f'{side}LegJ', (sx * 0.05, -1, swing))
        p.aim(f'{side}KneeJ', (0, -1, swing - lift * 1.4))
        p.aim(f'{side}ShoulderJ', (sx * 0.3, -1, -swing * 0.7))
        p.aim(f'{side}ArmJ', (sx * 0.15, -0.6, 0.6 - swing * 0.5))
    return p



def tuck(amount=1.0, arms=0.6):
    """Airborne: knees drawn up, the left leading and the right trailing (not side by side, as on the ground)."""
    p = base(arms=arms, stance=0)
    for s, sx, lead in (('L', 1, 1.25), ('R', -1, 0.7)):
        a = amount * lead
        p.aim(f'{s}LegJ', (sx * 0.1, -1 + a * 0.6, 0.9 * a + 0.12 * sx))
        p.aim(f'{s}KneeJ', (0, -1, -0.4 * a))
    return p


def strike(kind, t):
    """An attack at progress t 0..1: wind-up to 0.25, the hit at 0.35, recovery after."""
    k = min(1, t / 0.25) if t < 0.25 else (1 - min(1, (t - 0.25) / 0.1) * 2 if t < 0.35 else -1 + min(1, (t - 0.35) / 0.65))
    ext = max(0, -k)                              # 1 at the hit, fading out through recovery
    p = base(crouch=0.25 if 'Lw' in kind else 0.1)
    if 'Air' in kind:
        p = tuck(0.6, arms=0.3)
    if 'Hi' in kind:
        p.aim('RShoulderJ', (-0.3, -1 + 2 * ext, 0.2)); p.aim('RArmJ', (-0.2, -0.5 + 1.5 * ext, 0.3))
    elif 'Lw' in kind or 'AirLw' in kind:
        p.aim('RLegJ', (-0.3 * ext, -1, 1.2 * ext)); p.aim('RKneeJ', (-0.3 * ext, -1 + 0.6 * ext, 1.4 * ext))
    elif 'AirB' in kind:
        p.aim('LLegJ', (0.05, -1 + 0.3 * ext, -1.4 * ext)); p.aim('LKneeJ', (0, -1 + 0.4 * ext, -1.6 * ext))
    else:                                           # forward: the right arm (his gun arm) thrusts
        p.aim('RShoulderJ', (-0.3 + 0.3 * ext, -1 + 1.0 * ext, 0.1 + 1.2 * ext))
        p.aim('RArmJ', (-0.15 + 0.15 * ext, -0.6 + 0.6 * ext, 0.5 + 1.0 * ext))
    return p


def lie_offset(rx, height):
    """YRotN's translation that puts it (the body's pivot) at `height` above the floor, straight under XRotN, when XRotN
    is tipped by rx: the translation is in XRotN's tipped frame (row vectors, local = world . M^T)."""
    M = rig.rot_xyz(rx, 0, 0)
    w = (0, height - rig.HIP_Y, 0)
    return tuple(sum(w[j] * M[i][j] for j in range(3)) for i in range(3))


def down(face_up=True, tip=1.45, height=None):
    """Lying on the floor: the body tipped flat, legs and arms laid along it (aims are world, so they follow the floor).
    The pivot lies over his position, low enough that the blocks rest on the floor (the old offset, (0, 1 - HIP_Y, 0), was
    applied in the tipped frame and left him floating ~4 units up and ~5.6 forward or back)."""
    p = base(stance=0)
    rx = -tip if face_up else tip
    p.move('YRotN', lie_offset(rx, height if height is not None else (2.2 if face_up else 2.0)))
    p.rot('XRotN', (rx, 0, 0))
    along = 1 if face_up else -1                  # the direction his feet lie
    for s, sx in (('L', 1), ('R', -1)):
        p.aim(f'{s}LegJ', (sx * 0.15, -0.12, along)); p.aim(f'{s}KneeJ', (sx * 0.05, -0.05, along))
        p.aim(f'{s}FootJ', (0, 1 if face_up else -1, 0.2 * along), up=(0, 0, along))   # up: where the sole faces (FootJ's local Y)
        p.aim(f'{s}ShoulderJ', (sx * 0.5, -0.1, along)); p.aim(f'{s}ArmJ', (sx * 0.3, -0.05, along))
    return p


def hang():
    p = base(arms=2.0, stance=0)
    for s, sx in (('L', 1), ('R', -1)):
        p.aim(f'{s}ShoulderJ', (sx * 0.2, 1, 0.3)); p.aim(f'{s}ArmJ', (sx * 0.1, 1, 0.2))
    return p


def recoil(t):
    p = base(lean=-0.5 * (1 - t))
    p.aim('HeadN', (0, 1, -0.3 * (1 - t)))
    return p


def keys_for(name, frames):
    """Key poses (frame, Pose) for an action by name."""
    n = max(1, frames)
    at = lambda u: round(u * n)
    if name.startswith('Guard'):     # every shield action (on, hold, off, stun, reflect): the shield centres on ThrowN
        # (the lookup table's byte 0x11); Mario's shield animations lift it 1.5 above the hips and a little forward, and
        # left at rest it sat at his feet
        g = guard_pose
        if name == 'Guard':
            c = SHIELD_CENTRE
            tilt = lambda up, fwd: guard_pose((c[0], c[1] + up * TILT_SCALE, c[2] + fwd * TILT_SCALE))
            return [(0, g()), (9, g())] + [(10 + d, tilt(up, fwd)) for d, up, fwd in TILT]
        return [(0, g()), (n, g())]   # GuardOn too: covered from its first frame
    if re.match(r'Wait|Rebirth|Appeal|Entry|Ottotto|Stop|Pass|Sleep|Furafura', name):
        return [(at(u), base(bob=0.08 * math.sin(2 * math.pi * u))) for u in (0, 0.25, 0.5, 0.75, 1)]
    if re.match(r'Walk|Run$|Dash|TurnRun|RunDirect|RunBrake', name):   # foot paths and IK, keyed every frame
        import locomotion
        frames_, keys = locomotion.anim('Run' if name == 'RunDirect' else name)
        assert frames_ == n, f'{name}: FRAMES says {n}, locomotion {frames_}'
        return keys
    if name in ('Squat', 'SquatWait', 'SquatWait1', 'SquatWait2', 'SquatWaitItem'):
        return [(0, crouch_pose() if name != 'Squat' else base(crouch=0.5)), (n, crouch_pose())]
    if name == 'SquatRv':
        return [(0, crouch_pose()), (n, base())]
    if re.match(r'RunBrake|Turn$|Landing|Squat|Crouch', name):
        c = 0.9 if 'Squat' in name or 'Landing' in name else 0.4
        return [(0, base(crouch=c)), (n, base(crouch=c * (0.2 if name in ('SquatRv', 'Landing') else 1)))]
    if re.match(r'KneeBend|Jump|Fall|Cliff(Jump|Escape)', name):
        return [(0, tuck(0.3)), (at(0.5), tuck(0.8)), (n, tuck(0.5))]
    if re.match(r'Escape', name):                 # rolls, spot dodge, air dodge
        return [(0, base(crouch=0.6)), (at(0.5), tuck(1.0, arms=0.2)), (n, base(crouch=0.3))]
    if re.match(r'Attack', name):
        return [(at(u), strike(name, u)) for u in (0, 0.25, 0.35, 0.6, 1)]
    if re.match(r'Damage|Thrown|CapturePulled|Shouldered', name):
        return [(0, recoil(0)), (n, recoil(1))]
    if re.match(r'Down', name):
        up = not re.search(r'D$|Bound?D|StandD|WaitD|DamageD|AttackD|ForwardD|BackD', name)
        return [(0, down(up)), (n, down(up))]
    if re.match(r'Cliff', name):
        return [(0, hang()), (n, hang())]
    if re.match(r'Catch|Throw|Capture', name):
        p = base(arms=1.0)
        return [(0, base()), (at(0.4), p), (n, base())]
    return [(0, base()), (n, base())]


def unwrap(prev, cur):
    return tuple(c + 2 * math.pi * round((p - c) / (2 * math.pi)) for p, c in zip(prev, cur))


UNIT = (1.0, 1.0, 1.0)
# The limbs' growth, as a clip's parameters (poses_ground, poses_throws): Rgrow / Lgrow scale HandN (the fist, its fingers
# and the rocket ring, and a hitbox's offset on it), Rtips / Ltips the four fingertips (the Nb joints), which Mario's
# forward smash shrinks to ~0.5 so the fist reads as one mass, Rarm / Larm the whole arm (ShoulderJ). poses_air's clips
# grow joints directly (Clip.grow).
FINGERTIPS = ('1stNb', '2ndNb', '3rdNb', '4thNb')


def grow_params(pose, side):
    """(grow, tips, arm) of a pose's hand on `side`: the hand's, the fingertips' and the whole arm's (ShoulderJ) scale"""
    return (pose.scale.get(f'{side}HandN', UNIT)[0], pose.scale.get(f'{side}{FINGERTIPS[0]}', UNIT)[0],
            pose.scale.get(f'{side}ShoulderJ', UNIT)[0])


NO_GROW = bool(os.environ.get('GENO_NO_GROW'))     # an A/B: the build without the growth (every clip's grow keys ignored)


def grown(q, side):
    """a clip parameter dict's fist scale on `side`, as the build will play it (1 under GENO_NO_GROW)"""
    return 1.0 if NO_GROW else q.get(side + 'grow', 1.0)


def apply_grow(pose, side, grow=1.0, tips=1.0, arm=1.0):
    """grow: the hand (HandN); tips: the fingertips; arm: the whole arm from the shoulder (ShoulderJ: the upper arm, the
    forearm and the hand with it, so an arm grown this way reaches further than its IK placed it)"""
    if NO_GROW: return pose
    if abs(arm - 1.0) > 1e-6: pose.grow(f'{side}ShoulderJ', arm)
    if abs(grow - 1.0) > 1e-6: pose.grow(f'{side}HandN', grow)
    if abs(tips - 1.0) > 1e-6:
        for j in FINGERTIPS: pose.grow(f'{side}{j}', tips)
    return pose


def solve_keys(n, keys):
    """Key poses -> per-joint tracks, keeping only joints a pose moves (never TopN, TransN2 or the JA rest joints). A
    joint a pose grows (Pose.grow) also gets an "s" track (fighter-build writes it as SCAX/Y/Z)."""
    tracks, prev = {}, {}
    for f, pose in keys:
        sol = pose.solve()
        sc = getattr(pose, 'scale', {})
        for ji, jn in enumerate(NAMES):
            t, r = sol[jn]
            if jn in prev: r = unwrap(prev[jn], r)
            prev[jn] = r
            tracks.setdefault(ji, {'r': [], 't': [], 's': []})
            tracks[ji]['r'].append([min(f, n), *r]); tracks[ji]['t'].append([min(f, n), *t])
            tracks[ji]['s'].append([min(f, n), *sc.get(jn, UNIT)])
    keep = {}
    for ji, tr in tracks.items():
        jn = NAMES[ji]
        grown = any(max(abs(v - 1.0) for v in k[1:]) > 1e-4 for k in tr['s'])
        if jn in ENGINE_OWNED or jn.endswith('JA'):
            assert not grown, f'{jn} is the engine\'s or a rest joint: grow the joint it carries instead'
            continue
        rt, rr = REST[jn]
        moved = any(max(abs(a - b) for a, b in zip(k[1:], rr)) > 1e-4 for k in tr['r']) or \
                any(max(abs(a - b) for a, b in zip(k[1:], rt)) > 1e-4 for k in tr['t'])
        if moved or grown: keep[str(ji)] = tr if grown else {'r': tr['r'], 't': tr['t']}
    return dict(frames=n, tracks=keep)


# Actions whose flags' top bit is set move the fighter by the animation's TransN translation (the engine reads it as
# velocity: ft_80085030, ftCommon_8007D6A4): rolls, tech rolls, getups, ledge actions, dash attack and dash grab. An
# animation that leaves TransN still leaves him standing still, so each one borrows Mario's path (datkit rootmotion,
# cached as mr_rootmotion.json next to the actions list) at Mario's world scale, with ledge offsets stretched to Geno's
# height, unless Geno's own keys move TransN.
ROOT_MOTION = 0x80000000
# v1.3: shorter movement animations than Mario's template. A dash released to neutral plays the whole Dash animation (22)
# before Wait; the run flag stays at frame 11 (the script), so dash dancing and running are unchanged. RunBrake is the skid
# (Fox 18), TurnRun the run's turnaround (Fox 20). The walk and run cycles are one stride each at the attribute speed
# (locomotion.GAITS; the engine scales their playback by speed): WalkSlow 56, WalkMiddle 32, WalkFast 26, Run 18.
FRAMES = {'Dash': 18, 'RunBrake': 18, 'TurnRun': 18, 'WalkSlow': 56, 'WalkMiddle': 32, 'WalkFast': 26, 'Run': 18}
# Actions the template points at another action's figatree, which Geno animates on their own (states_air.py,
# states_items.py): the jumpsquat (the cast plays Landing's opening; the engine plays whatever KneeBend points at and
# jumps on frame 5), the helpless landing (Landing's again in the template) and the smash down throw (the down throw's)
OWN_ANIM = {15: 'KneeBend', 36: 'LandingFallSpecial',
            99: 'LightThrowLw4'}      # the smash down throw lets go on 5, the down throw on 7: the template shares their animation
MARIO_SCALE, HEIGHT_RATIO = 1.1, 15.24 / 14.27


def root_motion(tracks, cached, name, n=None):
    ji = str(NAMES.index('TransN'))
    if ji in tracks and any(abs(v) > 1e-4 for k in tracks[ji]['t'] for v in k[1:]): return tracks
    k = MARIO_SCALE * (HEIGHT_RATIO if name.startswith('Cliff') else 1.0)
    rest_t, rest_r = REST['TransN']
    last = cached['t'][-1][0] if cached['t'] else 0
    ts = n / last if n and last else 1.0       # a shortened animation plays Mario's path faster (same distance)
    t = [[f * ts, rest_t[0] + x * k, rest_t[1] + y * k, rest_t[2] + z * k] for f, x, y, z in cached['t']]
    tracks[ji] = {'t': t, 'r': [[t[0][0], *rest_r], [t[-1][0], *rest_r]]}
    return tracks


def still_transn(tracks):
    """A root-motion action whose TransN holds still (CliffWait's hang, the wall and ceiling techs' offsets) would get one
    constant key from fighter-build (a track whose keys all match becomes one key), which the game evaluates once: the
    engine takes TransN out of the skeleton every frame (ftAnim_8006E054 zeroes the joint), so from the second frame the
    hang read as 0 and he was drawn standing on the ledge corner. A 2e-4 nudge on the last key keeps two linear keys,
    evaluated every frame."""
    ji = str(NAMES.index('TransN'))
    tr = tracks.get(ji)
    if tr and len(tr['t']) >= 1 and all(max(abs(a - b) for a, b in zip(k[1:], tr['t'][0][1:])) < 1e-5 for k in tr['t']):
        first, last = tr['t'][0], list(tr['t'][-1])
        if last[0] == first[0]:
            last[0] = first[0] + 1
        last[1:] = [v + 2e-4 for v in last[1:]]      # every channel: fighter-build collapses each on its own
        tr['t'] = [first, last]
    return tracks


# The wooden puppet's movement sounds (bank 55, 550028-550052; projects/geno/sound/wiring.py): his voice-table slots and
# script cues. The walks' and the run's footsteps are in their own looping scripts (locomotion.scripts(), on the cycles'
# footfalls), so their cues are skipped here; Dash, TurnRun and RunBrake take theirs from wiring.CUES. Frame 0 is the
# action's first frame.
FOOTFALL_CUES = {('WalkSlow', None), ('WalkMiddle', None), ('WalkFast', None), ('Run', None)}


def sound_wiring():
    if os.environ.get('GENO_NO_SOUNDS'):          # an A/B: the build without them (the voice table stays silenced)
        return {}, {}
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sound'))
    import wiring
    voices = {f: v for f, off, v, how in wiring.VOICE_TABLE}
    cues = {}
    expand = {'LandingAirN/F/B/Hi/Lw': ['LandingAir' + k for k in ('N', 'F', 'B', 'Hi', 'Lw')],
              'EscapeF / EscapeB': ['EscapeF', 'EscapeB'], 'DownBoundU / DownBoundD': ['DownBoundU', 'DownBoundD'],
              'DownStandU / DownStandD': ['DownStandU', 'DownStandD'],
              'DownForwardU/D, DownBackU/D': ['DownForwardU', 'DownForwardD', 'DownBackU', 'DownBackD']}
    for acts, n, lst in wiring.CUES:
        for name in expand.get(acts, [acts]):
            for fr, ids, vol, note in lst:
                if (name, None) in FOOTFALL_CUES or (name, fr) in FOOTFALL_CUES: continue
                cues.setdefault(name, []).append([fr, wiring.cue(ids, vol).hex().upper()])
    return voices, cues


def build(actions_txt, out):
    rx = re.compile(r'^\s*(\d+) 0x\w+ off\s+(\d+) size\s+(\d+) flags (\w+) script\s+\d+ frames\s+([\d.]+)\s+(\S*)')
    import moves
    import states_air                            # the turn, jumps, falls, landings, crouch, platforms, edge
    states_air.register()
    authored = moves.build_all()                 # Geno's own moves: length, script, key poses
    anims, table, scripts, passthrough = {}, [], {}, {}
    rm_path = os.path.join(os.path.dirname(actions_txt), 'mr_rootmotion.json')
    rootmo = json.load(open(rm_path)) if os.path.exists(rm_path) else {}
    for line in open(actions_txt):
        m = rx.match(line)
        if not m: continue
        idx, off, size, flags, frames, sym = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4), float(m.group(5)), m.group(6)
        name = re.sub(r'^Ply\w+?5K_Share_ACTION_|_figatree$', '', sym) if sym else ''
        name = OWN_ANIM.get(idx, name)
        table.append(dict(index=idx, name=name, flags=int(flags, 16)))
        if sym.startswith('PlyTaro') and name not in authored:
            # what the victim plays while Geno throws it (TMarioThrow*): keyed to the shared 52-node skeleton every fighter
            # can play (kind 0x21), so fighter-build copies the template's own until Geno's throws get victim animations
            passthrough[name] = dict(sym=sym, off=off, size=size)
            continue
        if name in authored and authored[name][1] is not None:
            scripts[name] = authored[name][1].hex()
        if not name or name in anims: continue
        if name in authored:
            n, _, keys = authored[name]
        else:
            n = FRAMES.get(name, max(1, int(round(frames))))
            keys = keys_for(name, n)
        anims[name] = solve_keys(n, keys)
        if int(flags, 16) & ROOT_MOTION and str(idx) in rootmo and not sym.startswith('PlyTaro'):
            anims[name]['tracks'] = root_motion(anims[name]['tracks'], rootmo[str(idx)], name, FRAMES.get(name))
        if int(flags, 16) & ROOT_MOTION:
            still_transn(anims[name]['tracks'])
    if False:
        tracks = {}
        prev = {}
        for f, pose in keys:
            sol = pose.solve()
            for ji, jn in enumerate(NAMES):
                t, r = sol[jn]
                if jn in prev: r = unwrap(prev[jn], r)
                prev[jn] = r
                tracks.setdefault(ji, {'r': [], 't': []})
                tracks[ji]['r'].append([min(f, n), *r]); tracks[ji]['t'].append([min(f, n), *t])
        # only joints a pose moves get tracks, and never the engine's own: TopN carries facing, TransN2 is the model
        # origin, and the JA joints hold each limb's rest frame (Melee's animations leave all of them alone)
        keep = {}
        for ji, tr in tracks.items():
            jn = NAMES[ji]
            if jn in ENGINE_OWNED or jn.endswith('JA'): continue
            rt, rr = REST[jn]
            moved = any(max(abs(a - b) for a, b in zip(k[1:], rr)) > 1e-4 for k in tr['r']) or \
                    any(max(abs(a - b) for a, b in zip(k[1:], rt)) > 1e-4 for k in tr['t'])
            if moved: keep[str(ji)] = tr
        anims[name] = dict(frames=n, tracks=keep)
    import poses_throws                           # what a fighter Geno throws plays: a cast member's own, or authored
    passthrough.update(poses_throws.victims(passthrough))
    import locomotion                             # the walks', run's, dash's and run turnaround's own scripts
    scripts.update(locomotion.scripts())
    # template scripts that carried Mario's hits: his down air's landing hit (2% x2 for 3 frames) goes; its landing effect
    # (command 0x37) stays
    scripts['LandingAirLw'] = 'DC000423000001BB00007F40' + '00000000'
    # Geno's own specials replace the template's from 0x127 (the decomp's ftGe_Submotion order)
    table = [t for t in table if t['index'] < 0x127]
    for k, name in enumerate(moves.SPECIAL_NAMES):
        table.append(dict(index=0x127 + k, name=name, flags=getattr(moves, 'SPECIAL_FLAGS', {}).get(name, 0)))
        n, sc, keys = authored[name]
        if sc is not None: scripts[name] = sc.hex()   # even an empty one: never the template's special
        anims[name] = solve_keys(n, keys)
    import articles
    arts = [dict(a, ext={str(k): v for k, v in a.get('ext', {}).items()}) for a in articles.ARTICLES]
    # the shield pose: while shielding the engine sets every joint below TransN from this static pose (ftAnim_8006FA58 with
    # ftData+0x20), so it, not the Guard animations, places his body and the shield (ThrowN)
    shield_pose = {str(NAMES.index(n)): [list(t), list(r)] for n, (t, r) in guard_pose().solve().items()}
    voices, cues = sound_wiring()
    demo = getattr(sys.modules.get('states_misc'), 'demo_json', None)   # his results-screen poses (states_misc.py)
    json.dump(dict(prefix='PlyGeno5K_Share_ACTION_', actions=table, anims=anims, scripts=scripts, articles=arts,
                   shield_pose=shield_pose, voices=voices, cues=cues, blend={**locomotion.BLEND, **getattr(moves, "BLEND", {})},
                   part_poses=rig.part_poses_export(), passthrough=passthrough, **(dict(demo=demo()) if demo else {})), open(out, 'w'))
    print(f'{len(table)} actions, {len(anims)} animations, {len(scripts)} authored scripts -> {out}')


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
