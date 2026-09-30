"""Geno's states around the locomotion: the standing turn, the jumpsquat, the jumps and double jumps, the falls, the
landings, the crouch, dropping through a platform and teetering at an edge. Key poses on monotone splines, solved every
frame (locomotion.assemble: two-bone IK for the legs, aims for the rest), registered into moves.MOVES (register()) with no
script (the template's scripts, sounds and flags stay).

A pose is a dict of named parameters (degrees and model units, body frame: +Z where he faces, +X his left):
  turn, flip        the whole body's yaw (YRotN) and somersault pitch (XRotN, + forward) about flipc above his feet
  py, pz, px        the pelvis; pyaw, ppitch, proll its frame (pyaw is absolute: the idle is -25, toward the camera)
  cyaw, cpitch, croll the chest (cyaw absolute, cpitch the forward lean); hyaw, hpitch the head, relative to the chest
  aL, aR            arms: (forward swing, elbow bend, abduction) in the chest's yaw
  legs              'plant': each foot is fL/fR = (x, lift, z, pitch, toe yaw), the ankle's floor spot (a planted boot
                    rolls on its heel or ball, as in the walks); 'free': each leg is lL/lR = (thigh swing, knee bend,
                    spread, ankle flex), from the hip socket (air poses)
Every parameter is interpolated on its own monotone curve (locomotion.pchip), so holds hold and nothing overshoots.

The seams, since actions never blend (Wait1 is anims.base(); Fall is fall()): the Turn starts on Wait1 frame 0 and ends on
it turned half round; KneeBend drops straight into the squat; the jumps end on Fall frame 0, the double jumps on
FallAerial frame 0; Landing, LandingFallSpecial and SquatRv end on Wait1 frame 0; Squat ends on the crouch that
SquatWait loops and the crouching attacks start from (anims.crouch_pose is crouch() now); Pass ends on Fall frame 0;
Ottotto ends on OttottoWait frame 0.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig
import anims as A
import locomotion as L
from locomotion import rad, roty, norm, add, sub, mul, arm_dirs, boot, frame, BALL, SOLE, THIGH, SHIN, LEG

TAU = 2 * math.pi
ST = A.STANCE
REG = {}                   # name -> (frames, fn): moves.MOVES entries, added by register() (moves.air_base imports this
                           # module while moves is still loading, so it can't import moves at the top)


def state(name, frames):
    def reg(fn):
        REG[name] = (frames, lambda k, fn=fn: (None, fn()))
        return fn
    return reg


def register():
    import moves
    moves.MOVES.update(REG)


# ---------------------------------------------------------------------------------------------------------------- poses
WAIT = dict(turn=0.0, flip=0.0, flipc=7.6, px=0.0, py=rig.LEG_TOP - ST['drop'], pz=0.0,
            pyaw=math.degrees(ST['hip_yaw']), ppitch=0.0, proll=0.0,
            cyaw=math.degrees(ST['hip_yaw'] + ST['chest_yaw']), cpitch=math.degrees(0.12), croll=0.0,
            hyaw=math.degrees(ST['head_yaw']), hpitch=0.0, legs='plant',
            fL=(ST['lat'], 0.0, ST['fwd'], 0.0, math.degrees(ST['toe_out'])),
            fR=(-ST['lat'], 0.0, ST['back'], 0.0, -math.degrees(ST['toe_out'])))


def _arm_from_base(sx):
    """the idle's arm directions as (swing, elbow, abduction), fitted to base()'s aims"""
    up = norm((sx * 0.28, -1, 0.12)); fo = norm((sx * 0.15, -0.9, 0.45))
    def err(x):
        u, v = arm_dirs(sx, *x, rad(WAIT['cyaw']))
        return sum((a - b) ** 2 for a, b in zip(u, up)) + sum((a - b) ** 2 for a, b in zip(v, fo))
    x, step = [5.0, 20.0, 15.0], 8.0
    while step > 1e-4:                                     # coordinate descent
        moved = False
        for i in range(3):
            for d in (step, -step):
                y = list(x); y[i] += d
                if err(y) < err(x): x, moved = y, True
        if not moved: step /= 2
    return tuple(x)


WAIT_ARMS = {}


def spec(p):
    """a pose dict -> a locomotion spec. The idle's arms are its exact aims when aL/aR are 'wait'."""
    s = dict(turn=rad(p['turn']), flip=rad(p['flip']), flipc=p['flipc'], pel=(p['px'], p['py'], p['pz']),
             pyaw=rad(p['pyaw']), ppitch=rad(p['ppitch']), proll=rad(p['proll']), cyaw=rad(p['cyaw']),
             cpitch=rad(p['cpitch']), croll=rad(p['croll']), hyaw=rad(p['hyaw']), hpitch=rad(p['hpitch']),
             arm={}, foot={}, pole={})
    for side, sx in (('L', 1), ('R', -1)):
        a = p['a' + side]
        s['arm'][side] = (norm(a[:3]), norm(a[3:])) if len(a) == 6 else arm_dirs(sx, *a, s['cyaw'])
    socks = L.sockets(s)
    for side, sx in (('L', 1), ('R', -1)):
        if p['legs'] == 'plant':
            x, lift, z, t, o = p['f' + side]
            a0, f, d = boot(0.0, 0.0, rad(t), rad(o))
            ankle = add(a0, (x, lift, z))
        else:
            sw, kn, spread, flex = p['l' + side]
            hip = socks[side]
            sw, kn, sp = rad(sw), rad(kn), rad(spread)
            th = (sx * math.sin(sp), -math.cos(sp) * math.cos(sw), math.cos(sp) * math.sin(sw))
            sh = (sx * math.sin(sp), -math.cos(sp) * math.cos(sw - kn), math.cos(sp) * math.sin(sw - kn))
            ankle = add(hip, mul(th, THIGH * 0.999), mul(sh, SHIN * 0.999))
            t = math.degrees(sw - kn) + flex
            o = sx * 8.0
            _, f, d = boot(0.0, 0.0, rad(t), rad(o))
        s['foot'][side] = (ankle, f, d)
        toe = rad(o)
        s['pole'][side] = (math.sin(toe), 0.0, math.cos(toe))              # knees over the toes, as base() has them
    return s


def wait_pose():
    """Wait1 frame 0 as a pose dict: its arms are base()'s own aims (as direction pairs); WAIT_ARMS holds the nearest
    (swing, elbow, abduction), to vary from"""
    p = dict(WAIT)
    if not WAIT_ARMS:
        WAIT_ARMS['L'], WAIT_ARMS['R'] = _arm_from_base(1), _arm_from_base(-1)
    for side, sx in (('L', 1), ('R', -1)):
        p['a' + side] = norm((sx * 0.28, -1, 0.12)) + norm((sx * 0.15, -0.9, 0.45))
    return p


def arms_as_dirs(p):
    q = dict(p)
    for side, sx in (('L', 1), ('R', -1)):
        a = q['a' + side]
        if len(a) == 3:
            u, v = arm_dirs(sx, *a, rad(q['cyaw']))
            q['a' + side] = tuple(u) + tuple(v)
    return q


def turned(p, deg):
    q = dict(p); q['turn'] = p['turn'] + deg
    return q


# ---------------------------------------------------------------------------------------------------------------- curves
def keyed(n, keys, exact=None):
    """keys: {frame: pose dict}. Every numeric parameter on its own monotone curve; tuples per component. `exact`:
    {frame: spec} to use as-is at those frames (Wait1's own arms, Fall's frame 0), so the seams match to the bit.
    Returns [(frame, Pose)] for every frame 0..n."""
    fr = sorted(keys)
    keys = {f: arms_as_dirs(keys[f]) for f in fr}                # arms interpolate as directions
    first = keys[fr[0]]
    curves = {}
    for name, v0 in first.items():
        if isinstance(v0, str): continue
        vals = [keys[f][name] for f in fr]
        if isinstance(v0, tuple):
            curves[name] = [L.pchip(fr, [v[i] for v in vals]) for i in range(len(v0))]
        else:
            curves[name] = L.pchip(fr, vals)
    out = []
    for f in range(n + 1):
        if exact and f in exact:
            out.append((f, L.assemble(exact[f]))); continue
        p = {k: (tuple(c(f) for c in cv) if isinstance(cv, list) else cv(f)) for k, cv in curves.items()}
        p['legs'] = first['legs']
        out.append((f, L.assemble(spec(p))))
    return out


def wait_spec_turned(deg=0.0):
    s = L.wait_spec()
    if deg:
        s = dict(s); s['turn'] = rad(deg)
    return s


def base_exact(deg=0.0):
    """Wait1 frame 0 (anims.base()) itself, as a Pose, optionally turned (YRotN) by deg"""
    p = A.base()
    if deg:
        p.rot('YRotN', (0.0, rad(deg), 0.0))
        # base()'s aims are world directions: turn them too
        for j, (x, up) in list(p.aims.items()):
            p.aims[j] = (roty(x, rad(deg)), roty(up, rad(deg)) if up else None)
    return p


def keyed_poses(n, keys, exact_poses=None):
    """keyed(), with whole Poses at chosen frames (exact seams)"""
    out = keyed(n, keys)
    if exact_poses:
        out = [(f, exact_poses.get(f, p)) for f, p in out]
    return out


# ---------------------------------------------------------------------------------------------------------------- turn
@state('Turn', 12)
def turn():
    """The standing turn, 12 frames, authored in the old facing (the engine flips his facing but not the model's until the
    next action): the head leads and the chest winds after it while the boots stay planted, then a little hop spins
    the legs half round toward the camera (his front sweeps past it facing right, as the cast's right-openers turn) and
    he lands in the idle's stagger, facing the other way. A dash dance shows frame 1: the head already turned, the knees
    dipping."""
    W = wait_pose()
    WA = WAIT_ARMS
    k = {0: W}
    k[1] = dict(W, py=5.3, hyaw=W['hyaw'] - 55, cyaw=W['cyaw'] - 12, hpitch=-4,
                aL=(WA['L'][0] + 8, WA['L'][1] + 14, WA['L'][2] + 8), aR=(WA['R'][0] - 6, WA['R'][1] + 10, WA['R'][2] + 10))
    k[2] = dict(k[1], py=5.08, hyaw=W['hyaw'] - 80, cyaw=W['cyaw'] - 30, cpitch=12, hpitch=-6,
                aL=(WA['L'][0] + 18, 40, 26), aR=(WA['R'][0] - 2, 36, 28),
                fL=(W['fL'][0], 0.0, W['fL'][2], -12, W['fL'][4]), fR=(W['fR'][0], 0.0, W['fR'][2], -20, W['fR'][4]))
    # the hop: both boots leave, the legs draw in under him and spin with the pelvis
    tuck = lambda f, lift, t: (f[0] * 0.8, lift, f[2] * 0.62, t, f[4])
    k[3] = dict(k[2], turn=-22, py=5.4, cyaw=W['cyaw'] - 28, hyaw=W['hyaw'] - 70, fL=tuck(W['fL'], 0.2, -24), fR=tuck(W['fR'], 0.25, -28))
    k[5] = dict(k[3], turn=-100, py=5.82, pz=0.05, cyaw=W['cyaw'] - 8, hyaw=W['hyaw'] - 42, cpitch=6, hpitch=-3,
                fL=tuck(W['fL'], 0.55, -18), fR=tuck(W['fR'], 0.6, -22), aL=(WA['L'][0] + 10, 34, 30), aR=(WA['R'][0] + 4, 34, 32))
    k[7] = dict(k[5], turn=-168, py=5.5, cyaw=W['cyaw'] + 4, hyaw=W['hyaw'] - 10,
                fL=(W['fL'][0], 0.15, W['fL'][2] * 0.9, 6, W['fL'][4]), fR=(W['fR'][0], 0.12, W['fR'][2] * 0.9, 4, W['fR'][4]))
    k[8] = dict(k[7], turn=-180, py=5.12, cyaw=W['cyaw'], hyaw=W['hyaw'] + 4, cpitch=12, hpitch=-5,
                fL=W['fL'], fR=W['fR'], aL=(WA['L'][0] + 6, 30, 22), aR=(WA['R'][0] + 2, 30, 24))
    k[10] = dict(k[8], py=5.42, cpitch=9, hpitch=-1, hyaw=W['hyaw'] + 1, aL=W['aL'], aR=W['aR'])
    k[12] = turned(W, -180)
    for f in k:
        if f >= 8: k[f] = dict(k[f], turn=-180)
    return keyed_poses(12, k, {0: base_exact(), 12: base_exact(-180)})


# ---------------------------------------------------------------------------------------------------------------- checks
def hurt_top(pose):
    """the highest point of his hurt capsules (world y) in a Pose: the crouch contract"""
    sol = pose.solve()
    W = rig.world_mats(pose={k: {'t': v[0], 'r': v[1]} for k, v in sol.items()})
    return max(rig.xform(p, W[j])[1] + r for j, a, b, r, h, g in rig.HURTBOXES for p in (a, b))


CROUCH_TOP = 10.5         # the crouch contract: Fox's crouch-to-stand ratio (10.8 of 15.6) on his standing top (15.0)


def crouch_params(py=3.0, lean=52.0):
    """The crouch: the boots stay planted in the idle's stagger (the rear heel up on its ball), the pelvis sits down and
    back, the body folds forward over the knees and the head comes up to look ahead."""
    W = wait_pose()
    return dict(W, py=py, pz=-0.35, ppitch=14, cpitch=lean, hpitch=-lean * 0.4, hyaw=W['hyaw'] + 4,
                aL=(30, 62, 24), aR=(24, 66, 22),
                fL=W['fL'], fR=(W['fR'][0], 0.0, W['fR'][2], -28, W['fR'][4]))


CROUCH = crouch_params()


def crouch_spec(breath=0.0):
    p = dict(CROUCH)
    p['py'] += 0.07 * breath
    p['cpitch'] += 1.6 * breath
    p['hpitch'] -= 1.0 * breath
    return spec(arms_as_dirs(p))


# ---------------------------------------------------------------------------------------------------------------- crouch
@state('Squat', 8)
def squat():
    """Down into the crouch in three frames (the cast's 3-4), a small overshoot, settled by 8 (= SquatWait frame 0)."""
    W, C = wait_pose(), CROUCH
    k = {0: W,
         1: dict(W, py=4.6, cpitch=22, hpitch=-6, ppitch=6, pz=-0.1, aL=(14, 34, 22), aR=(10, 36, 20),
                 fR=(W['fR'][0], 0.0, W['fR'][2], -10, W['fR'][4])),
         3: dict(C, py=C['py'] - 0.12, cpitch=C['cpitch'] + 4, hpitch=C['hpitch'] - 2),
         5: dict(C, py=C['py'] + 0.04),
         8: C}
    return keyed_poses(8, k, {0: base_exact(), 8: L.assemble(crouch_spec())})


@state('SquatWait', 130)
def squat_wait():
    """The crouch, breathing: two slow breaths in 130 frames, the chest and head easing with them."""
    return [(f, L.assemble(crouch_spec(math.sin(TAU * 2 * f / 130)))) for f in range(131)]


@state('SquatWaitItem', 130)
def squat_wait_item():
    return squat_wait()


@state('SquatRv', 10)
def squat_rv():
    """Up out of the crouch: the chest lifts first, the legs push, a small overshoot, Wait1 frame 0 at 10."""
    W, C = wait_pose(), CROUCH
    k = {0: C,
         2: dict(C, py=C['py'] + 0.35, cpitch=C['cpitch'] - 14, hpitch=C['hpitch'] + 6),
         5: dict(W, py=4.7, pz=-0.15, ppitch=6, cpitch=18, hpitch=-4, aL=(12, 32, 22), aR=(10, 34, 20),
                 fR=(W['fR'][0], 0.0, W['fR'][2], -8, W['fR'][4])),
         8: dict(W, py=W['py'] + 0.05),
         10: W}
    return keyed_poses(10, k, {0: L.assemble(crouch_spec()), 10: base_exact()})


def crouch_pose():
    """the crouch as a Pose (anims.crouch_pose returns this: the crouching attacks start and end on it)"""
    return L.assemble(crouch_spec())


# ---------------------------------------------------------------------------------------------------------------- air
# The fall: his idle's opening, nearly side-on, knees soft and a little apart (the left leading, as in his tuck), toes
# hanging, arms lifted out to the sides; a slow flutter keeps it alive (the cape and cap point are physics).
def cactus(sx, arms, s, c):
    """a falling arm, a puppet's balance: the upper arm out to the side, the forearm up and forward, flapping (raw
    directions, body frame)"""
    up = (sx * 0.9, -0.2 + 0.012 * arms + 0.16 * s, -0.05)
    fore = (sx * 0.3, 0.5 + 0.2 * c + 0.01 * arms, 0.85)
    return tuple(norm(up)) + tuple(norm(fore))


def fall_params(ph=0.0, lean=0.0, legs=0.0, arms=0.0, aerial=False):
    """ph: the flutter's phase (0..1). lean: the drift variants' lean (+ forward, FallF; - back, FallB); legs: their legs
    trailing (+) or leading (-); arms: + raised (the double jump's falls lift them a little more)."""
    c, s = math.cos(TAU * ph), math.sin(TAU * ph)
    return dict(WAIT, turn=0.0, flip=0.0, px=0.0, py=5.75 + 0.06 * s, pz=0.0, pyaw=-10 + 2 * s, ppitch=4 + lean * 0.6,
                proll=1.5 * c, cyaw=-12 + 3 * s, cpitch=4 + lean, croll=-1.0 * c, hyaw=6 - 2 * s, hpitch=-3 - lean * 0.7,
                legs='free',
                lL=(22 - legs + 5 * s, 48 + 6 * c, 6, -22), lR=(-4 - legs - 5 * s, 30 - 6 * c, 5, -30),
                aL=cactus(1, arms, s, c), aR=cactus(-1, arms, -s, c))


def fall_keys(n, lean=0.0, legs=0.0, arms=0.0, cycles=1):
    return keyed(n, {f: fall_params(cycles * f / n, lean, legs, arms) for f in range(0, n + 1, max(1, n // 10))} | {n: fall_params(0, lean, legs, arms)})


def fall_pose(lean=0.0, legs=0.0, arms=0.0):
    """Fall frame 0 (and FallF, FallB) as a Pose: where every jump ends"""
    return L.assemble(spec(arms_as_dirs(fall_params(0.0, lean, legs, arms))))


@state('Fall', 20)
def fall():
    return fall_keys(20)


@state('FallF', 20)
def fall_f():
    """drifting forward (the engine blends it in by drift, on Fall's own frame): leaning into it, legs trailing"""
    return fall_keys(20, lean=14, legs=14)


@state('FallB', 20)
def fall_b():
    """drifting back: sitting back, legs out in front"""
    return fall_keys(20, lean=-12, legs=-16)


AER = 8               # the double jump's falls: the same pose, arms a little higher, a quicker flutter


@state('FallAerial', 10)
def fall_aerial():
    return fall_keys(10, arms=AER)


@state('FallAerialF', 10)
def fall_aerial_f():
    return fall_keys(10, lean=14, legs=14, arms=AER)


@state('FallAerialB', 10)
def fall_aerial_b():
    return fall_keys(10, lean=-12, legs=-16, arms=AER)


# Helpless (after Star Road): the marionette with its strings cut. Limp arms trail up as he drops, the head lolls back and
# to one side, the legs dangle apart; a loose shiver (6 frames) instead of the fall's flutter.
def limp_params(ph=0.0, lean=0.0, legs=0.0):
    c, s = math.cos(TAU * ph), math.sin(TAU * ph)
    return dict(WAIT, turn=0.0, flip=0.0, px=0.0, py=5.8, pz=0.0, pyaw=-18, ppitch=-6 + lean * 0.5, proll=3 + 1.2 * s,
                cyaw=-22, cpitch=-10 + lean, croll=5 + 1.5 * s, hyaw=18 + 2 * c, hpitch=-24 - 2 * s, legs='free',
                lL=(10 - legs + 3 * c, 22 + 3 * s, 12, -38), lR=(-2 - legs - 3 * c, 16 - 3 * s, 10, -42),
                aL=(168 + 5 * s, 24 + 4 * c, 30), aR=(160 - 5 * s, 30 - 4 * c, 36))


def limp_keys(n, lean=0.0, legs=0.0):
    return keyed(n, {f: limp_params(f / n, lean, legs) for f in range(n + 1)} | {n: limp_params(0, lean, legs)})


@state('FallSpecial', 6)
def fall_special():
    return limp_keys(6)


@state('FallSpecialF', 6)
def fall_special_f():
    return limp_keys(6, lean=12, legs=12)


@state('FallSpecialB', 6)
def fall_special_b():
    return limp_keys(6, lean=-10, legs=-12)


# ---------------------------------------------------------------------------------------------------------------- jumps
@state('KneeBend', 8)
def knee_bend():
    """The jumpsquat (5 frames, jump_startup_time). His own animation now: the template shared Landing's figatree (the
    cast's convention), but the engine plays whatever KneeBend points at and jumps on frame 5. A crisp squat: already
    dipping on the first frame, deepest on 2-3 (the hips down half a leg, 17% of his height, the knees at ~60 degrees:
    the cast's 17-39% and 33-64 degrees, for his short legs) with the arms swung back and the rear heel up, the push
    starting on 4; frames 5-8 never show (the jump takes over), they hold the push."""
    W = wait_pose()
    WA = WAIT_ARMS
    heel = lambda t: (W['fR'][0], 0.0, W['fR'][2], t, W['fR'][4])
    k = {0: dict(W, py=4.4, pz=-0.15, ppitch=9, cpitch=22, hpitch=-8, aL=(-8, 30, 22), aR=(-14, 30, 20), fR=heel(-8)),
         1: dict(W, py=3.6, pz=-0.28, ppitch=13, cpitch=32, hpitch=-14, aL=(-30, 36, 24), aR=(-36, 34, 22), fR=heel(-18)),
         2: dict(W, py=3.1, pz=-0.34, ppitch=15, cpitch=38, hpitch=-17, aL=(-42, 40, 24), aR=(-46, 38, 22), fR=heel(-24)),
         3: dict(W, py=3.05, pz=-0.34, ppitch=15, cpitch=39, hpitch=-17, aL=(-46, 42, 24), aR=(-50, 40, 22), fR=heel(-26)),
         4: dict(W, py=3.4, pz=-0.26, ppitch=13, cpitch=33, hpitch=-12, aL=(-28, 36, 24), aR=(-32, 34, 22), fR=heel(-30),
                 fL=(W['fL'][0], 0.0, W['fL'][2], -6, W['fL'][4])),
         8: dict(W, py=3.9, pz=-0.15, ppitch=11, cpitch=28, hpitch=-8, aL=(-10, 30, 24), aR=(-14, 30, 22), fR=heel(-36),
                 fL=(W['fL'][0], 0.0, W['fL'][2], -14, W['fL'][4]))}
    return keyed(8, k)


def launch(back=False):
    """JumpF/JumpB frame 0: the legs just straightened under him (the squat's push), toes pointed, arms thrown up"""
    return dict(WAIT, py=6.0, pz=0.0, pyaw=-14, ppitch=-2 if not back else -6, proll=0, cyaw=-14, cpitch=-2 if not back else -8,
                croll=0, hyaw=4, hpitch=-8, legs='free',
                lL=(4, 14, 5, -45), lR=(-10, 18, 5, -48), aL=(166, 18, 22), aR=(128, 26, 24))


@state('JumpF', 55)
def jump_f():
    """The jump: frame 0 is the push's end (legs straight, arms flung up); the left knee comes up and the right leg
    trails in a jaunty rising pose that drifts through the rise, then settles into the fall by 55 (Fall frame 0)."""
    L0 = launch()
    rise = dict(L0, py=5.9, pyaw=-10, ppitch=6, cpitch=6, hpitch=-4, lL=(72, 112, 8, -20), lR=(-18, 64, 6, -34),
                aL=(140, 34, 34), aR=(-18, 44, 30))
    k = {0: L0,
         3: dict(rise, lL=(50, 88, 7, -26), lR=(-16, 44, 6, -40), aL=(156, 26, 30), aR=(50, 40, 28), ppitch=2, cpitch=2),
         7: rise,
         24: dict(rise, lL=(68, 106, 8, -20), lR=(-14, 60, 6, -32), aL=(132, 38, 38), aR=(-8, 44, 32), py=5.88),
         38: dict(rise, lL=(50, 84, 7, -22), lR=(-8, 48, 6, -32), aL=(96, 40, 46), aR=(30, 44, 44), ppitch=5, cpitch=5),
         55: fall_params(0.0)}
    return keyed_poses(55, k, {55: fall_pose()})


@state('JumpB', 60)
def jump_b():
    """Jumping backward: he rocks back as he leaves, both knees drawn up in front, arms forward for balance; the fall
    by 60."""
    L0 = launch(back=True)
    rise = dict(L0, py=5.9, pyaw=-8, ppitch=-10, cpitch=-8, hpitch=4, lL=(60, 104, 8, -18), lR=(40, 92, 7, -22),
                aL=(122, 40, 22), aR=(108, 44, 20))
    k = {0: L0,
         3: dict(rise, lL=(40, 76, 7, -26), lR=(22, 60, 6, -30), ppitch=-6, cpitch=-6),
         7: rise,
         28: dict(rise, lL=(56, 98, 8, -20), lR=(36, 86, 7, -24), ppitch=-8, cpitch=-6, aL=(110, 42, 34), aR=(98, 46, 32)),
         42: dict(rise, lL=(38, 70, 7, -22), lR=(14, 52, 6, -28), ppitch=-2, cpitch=-2, aL=(86, 42, 44), aR=(74, 44, 42)),
         60: fall_params(0.0)}
    return keyed_poses(60, k, {60: fall_pose()})


def tuck_ball(flip):
    """a tight somersault tuck, knees to the chest, hands on the shins"""
    return dict(WAIT, flip=flip, py=6.1, pz=0.2, pyaw=-8, ppitch=20, cyaw=-8, cpitch=38, hyaw=0, hpitch=18, legs='free',
                lL=(105, 150, 10, -30), lR=(98, 148, 9, -32), aL=(62, 96, 20), aR=(58, 100, 18))


@state('JumpAerialF', 60)
def jump_aerial_f():
    """The double jump forward: a kick off the air (legs snap straight, arms up), then a tight forward somersault, the
    whole body turning once over 5-19 about his middle, opening out of it into the fall (FallAerial frame 0 at 60)."""
    kick = dict(launch(), py=6.1, lL=(-6, 10, 5, -50), lR=(-18, 14, 5, -50), aL=(168, 18, 22), aR=(158, 20, 24), cpitch=-4)
    k = {0: kick,
         3: dict(tuck_ball(0), flip=20),
         6: dict(tuck_ball(0), flip=95),
         9: dict(tuck_ball(0), flip=190),
         12: dict(tuck_ball(0), flip=280),
         16: dict(tuck_ball(0), flip=340, lL=(80, 124, 9, -28), lR=(70, 118, 8, -30), cpitch=26, hpitch=8),
         20: dict(fall_params(0, arms=AER), flip=360, lL=(40, 70, 7, -24), lR=(10, 44, 6, -30), cpitch=8),
         32: dict(fall_params(0.2, arms=AER), flip=360),
         60: dict(fall_params(0, arms=AER), flip=360)}
    out = keyed(60, k)
    return out[:-1] + [(60, fall_pose(arms=AER))]


@state('JumpAerialB', 90)
def jump_aerial_b():
    """The double jump backward: the same kick, then a back somersault (a turn back over 5-21), opening into the fall."""
    kick = dict(launch(back=True), py=6.1, lL=(-2, 12, 5, -50), lR=(-12, 16, 5, -50), aL=(168, 18, 22), aR=(158, 20, 24))
    k = {0: kick,
         3: dict(tuck_ball(0), flip=-18),
         6: dict(tuck_ball(0), flip=-85),
         10: dict(tuck_ball(0), flip=-185),
         14: dict(tuck_ball(0), flip=-280),
         18: dict(tuck_ball(0), flip=-338, lL=(80, 124, 9, -28), lR=(70, 118, 8, -30), cpitch=24, hpitch=6),
         22: dict(fall_params(0, arms=AER), flip=-360, lL=(34, 66, 7, -24), lR=(22, 52, 6, -30), cpitch=-6),
         40: dict(fall_params(0.3, arms=AER), flip=-360),
         90: dict(fall_params(0, arms=AER), flip=-360)}
    out = keyed(90, k)
    return out[:-1] + [(90, fall_pose(arms=AER))]


# ---------------------------------------------------------------------------------------------------------------- landings
def landing_keys(n, depth=1.0, slow=1.0):
    """Down onto the planted boots: the pelvis drops through the impact to its lowest on frame 2 (the cast: 2-6), the
    arms swing down and forward, the rear heel peels up; he is still low when the lag ends (4) and rises into Wait1 frame
    0 by n. depth scales how far he sinks, slow stretches the recovery."""
    W = wait_pose()
    WA = WAIT_ARMS
    heel = lambda t: (W['fR'][0], 0.0, W['fR'][2], t, W['fR'][4])
    d = lambda y: W['py'] - (W['py'] - y) * depth
    k = {0: dict(W, py=d(4.1), pz=-0.12, ppitch=8, cpitch=18 * depth, hpitch=-10, aL=(38, 30, 34), aR=(30, 34, 32), fR=heel(-10)),
         2: dict(W, py=d(3.1), pz=-0.3, ppitch=14, cpitch=32 * depth, hpitch=-16, aL=(20, 44, 30), aR=(12, 46, 28), fR=heel(-24)),
         4: dict(W, py=d(3.2), pz=-0.3, ppitch=13, cpitch=30 * depth, hpitch=-14, aL=(12, 46, 28), aR=(6, 48, 26), fR=heel(-22)),
         round(9 * slow): dict(W, py=d(4.05), pz=-0.2, ppitch=9, cpitch=20 * depth, hpitch=-8, aL=(8, 36, 24), aR=(12, 34, 20), fR=heel(-10)),
         round(16 * slow): dict(W, py=5.25, pz=-0.05, ppitch=3, cpitch=11, hpitch=-2, aL=(WA['L'][0] + 4, 24, 22), aR=(WA['R'][0] + 3, 22, 10)),
         round(23 * slow): dict(W, py=5.6),
         n: W}
    return keyed_poses(n, k, {n: base_exact()})


@state('Landing', 29)
def landing():
    return landing_keys(29)


@state('LandingFallSpecial', 30)
def landing_fall_special():
    """The heavy landing (out of the helpless fall; the engine stretches it over the special's landing lag, and a wavedash
    slides on it): a deeper sink, the hands near the knees, the head bowed, a slower rise."""
    return landing_keys(30, depth=1.35, slow=1.15)


# ---------------------------------------------------------------------------------------------------------------- platforms
@state('Pass', 29)
def pass_():
    """Dropping through a platform (he is falling from the first frame): the crouch's knees pull up into a tuck as the
    platform passes, the arms rise, then the legs let down into the fall (Fall frame 0 at 29)."""
    k = {0: dict(WAIT, py=4.3, pz=-0.2, pyaw=-18, ppitch=12, cyaw=-18, cpitch=34, hpitch=-8, legs='free',
                 lL=(62, 118, 8, -10), lR=(26, 112, 6, -24), aL=(34, 58, 26), aR=(26, 62, 24)),
         4: dict(WAIT, py=5.3, pz=-0.1, pyaw=-14, ppitch=10, cyaw=-14, cpitch=18, hpitch=12, legs='free',
                 lL=(78, 132, 9, -18), lR=(52, 126, 8, -26), aL=(150, 34, 30), aR=(140, 38, 28)),
         10: dict(WAIT, py=5.8, pyaw=-12, ppitch=4, cyaw=-12, cpitch=4, hpitch=6, legs='free',
                  lL=(34, 62, 8, -30), lR=(4, 40, 6, -36), aL=(164, 26, 34), aR=(154, 30, 32)),
         18: dict(fall_params(0.0), aL=(104, 40, 52), aR=(94, 44, 50), hpitch=0),
         29: fall_params(0.0)}
    return keyed_poses(29, k, {29: fall_pose()})


# ---------------------------------------------------------------------------------------------------------------- the edge
EDGE_L = (1.15, 0.0, 0.55)     # the front boot's ankle at the edge (its toe over the drop), the rear one behind
EDGE_R = (-1.2, 0.0, -1.5)


def teeter_params(t, lean, leg, wind, head=0.0):
    """t unused; lean (deg forward), leg (0..1: the rear leg lifting back as a counterweight), wind (deg: the arms'
    circle phase)"""
    W = wait_pose()
    lift = leg * 1.9
    return dict(W, py=5.3 - 0.35 * max(0.0, lean) / 40, pz=-0.2 - 0.018 * lean, pyaw=-10, ppitch=lean * 0.5,
                cyaw=-8, cpitch=lean, hyaw=6, hpitch=-lean * 0.2 + head,
                fL=(EDGE_L[0], 0.0, EDGE_L[2], -4 if lean > 20 else 0, 10),
                fR=(EDGE_R[0], lift, EDGE_R[2] - 1.4 * leg, -40 * leg, -10),
                aL=(wind, 26, 38), aR=(wind - 140, 30, 40))


OTT_N = 185
CIRCLES = 4                    # windmill turns per loop


def teeter(f):
    u = f / OTT_N
    lean = 20 + 22 * math.sin(TAU * 2 * u - 0.6) + 4 * math.sin(TAU * 5 * u)        # two big lurches, a nervous tremble
    leg = max(0.0, math.sin(TAU * 2 * u - 0.9)) ** 1.5                                 # the counterweight leg on each lurch
    wind = 40 + 360 * CIRCLES * u
    return teeter_params(u, lean, leg, wind, head=4 * math.sin(TAU * 3 * u))


@state('OttottoWait', OTT_N)
def ottotto_wait():
    """Teetering on an edge, facing the drop: the front toe over it, he lurches forward twice a loop, windmilling (four
    turns a loop) and swinging the rear leg back as a counterweight, then catches himself and sways back; a nervous
    tremble on top. The loop closes on itself (185)."""
    k = {f: teeter(f) for f in range(0, OTT_N + 1, 4)}
    k[OTT_N] = teeter(0)
    return keyed(OTT_N, k)


@state('Ottotto', 13)
def ottotto():
    """Reaching the edge: the front boot hops back from over the drop to the edge while he lurches forward and the arms
    fling up into the windmill; frame 13 is OttottoWait frame 0."""
    W = wait_pose()
    k = {0: W,
         2: dict(W, py=5.4, cpitch=16, ppitch=6, hpitch=-6, aL=(40, 30, 30), aR=(20, 34, 32),
                 fL=(W['fL'][0], 0.0, W['fL'][2], -14, W['fL'][4])),
         5: dict(W, py=5.35, pz=-0.1, cpitch=24, ppitch=10, hpitch=-10, aL=(90, 26, 36), aR=(-40, 30, 38),
                 fL=((W['fL'][0] + EDGE_L[0]) / 2, 0.55, (W['fL'][2] + EDGE_L[2]) / 2, 10, 10),
                 fR=(EDGE_R[0], 0.0, EDGE_R[2], 0, -10)),
         8: dict(teeter(0), fL=(EDGE_L[0], 0.0, EDGE_L[2], 0, 10), aL=(12, 26, 38), aR=(-120, 30, 40),
                 fR=(W['fR'][0] * 0.6 + EDGE_R[0] * 0.4, 0.35, (W['fR'][2] + EDGE_R[2]) / 2, -12, -12)),
         11: dict(teeter(0), fR=(EDGE_R[0], 0.0, EDGE_R[2], 0, -10)),
         13: teeter(0)}
    k[5]['fR'] = W['fR']
    return keyed(13, k)
