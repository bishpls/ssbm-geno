"""Geno's item actions: picking items up, throwing them (light and heavy, on the ground, dashing and in the air), carrying a
crate, the bat and sword swings, the Ray Gun, the Super Scope, the hammer, the parasol and the Screw Attack.

The engine drives the item: the pick-up and release frames and the item's flight are the template's scripts (kept, so
the timing is the cast's), and the item hangs on RHandNb (ItemHoldBone) in that bone's frame. The body is animated to
those frames: every action is a function of time sampled on every frame (states_misc: body(), the splines), starting and
ending on Wait1's first frame (base()) on the ground, or on Fall's first frame in the air (the engine never blends), and
the item is held the way the cast holds each kind (measured from their RHandNb in art/motion/fk):
  - swing items (bat, Beam Sword, fan, Star Rod, Lip's Stick), the hammer, the parasol and the Super Scope run along the
    bone's +Y (a blade out of the top of the fist);
  - the Ray Gun and Fire Flower point along +Z with +Y up (a pistol grip);
  - a crate, barrel or party ball hangs on ThrowN, not the hand (heavy items attach to the shield bone), by the centre
    of its -Z face; a crate is 15 a side, his height: he carries it on his head, arms up bracing its bottom.
Actions whose facing flips part way (the back throws, flags 0xC0) are authored in the old facing, as Turn is: the model
only turns at the next action, so they end on base() turned half round.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig
import anims
from anims import Pose, base, norm, cross, dot
from moves import MOVES
from states_misc import (state, spline, smooth, clamp, lerp, _add, body, arm, set_arm, hand_blend, world, pos, xf,
                         to_local, vec_mat, mat_vec_t, local_dir, sample, rot_y, rodrigues, slerp_dir, ARM0, FEET, TOE,
                         IDLE_FLEX, tex, foot_ik, _BW, _BASE, TAU, check_rest, S)

PI = math.pi
HAND = rig.HAND * 0.9                 # wrist (RHandN) to the grip (RHandNb)


# ---------------------------------------------------------------------------------------------------------------- helpers
def chest_of(W):
    return [row[:3] for row in W['WaistN'][:3]]


REST_WRIST = {s: to_local(pos(_BW, f'{s}HandN'), _BW['WaistN']) for s in 'LR'}


def cpath(t, keys, W):
    """A wrist path given in the chest's frame (spline through (frame, (x, y, z)) keys), to the model's space."""
    return xf(spline(t, keys), W['WaistN'])


def cdir(t, keys, W):
    """A direction given in the chest's frame (spline, normalised), to the model's space."""
    return norm(vec_mat(spline(t, keys), W['WaistN']))


def grip(p, side, blade=None, knuckles=None, barrel=None, top=None, w=1.0):
    """Turn the hand so the held item points where it should: a blade item (bat, sword, hammer, parasol, scope) along
    `blade` with the knuckles toward `knuckles`; a gun along `barrel` with its top toward `top`. RHandNb's +Y is the
    hand's -Y and its +Z the hand's +X (rig.py), so the hand's aim is (knuckles, -blade) or (barrel, -top)."""
    if blade is not None:
        b = norm(blade)
        k = [x - dot(norm(knuckles), b) * y for x, y in zip(norm(knuckles), b)]   # knuckles square to the blade
        if dot(k, k) < 0.12:               # the hint nearly along the blade: fall back on the knuckles pointing down
            d = (0, -1, 0)
            k = [x - dot(d, b) * y for x, y in zip(d, b)]
        k = norm(k)
        return hand_blend(p, side, k, [-x for x in b], w)
    k = norm(barrel)
    u = norm(top)
    u = norm([x - dot(u, k) * y for x, y in zip(u, k)])
    return hand_blend(p, side, k, [-x for x in u], w)


class Fixed:
    """A pose already solved (joint -> (t, r)), for keys blended between another action's pose and ours."""
    def __init__(self, sol):
        self.sol = sol

    def solve(self):
        return self.sol


def mix(a, b, u):
    """Blend two poses' local transforms (u 0 is a, 1 is b); rotations the short way round."""
    sa, sb = a.solve(), b.solve()
    out = {}
    for j in sa:
        ta, ra = sa[j]; tb, rb = sb[j]
        rb = anims.unwrap(ra, rb)
        out[j] = (tuple(x + (y - x) * u for x, y in zip(ta, tb)), tuple(x + (y - x) * u for x, y in zip(ra, rb)))
    return Fixed(out)


def as_pose(src):
    """Any keyed pose as a Pose whose every joint is set locally (so aims added afterwards override just those joints)."""
    p = Pose()
    for j, (t, r) in src.solve().items():
        p.move(j, t); p.rot(j, r)
    return p


_OTHER = {}


def other_pose(name, frames, which=0):
    """Another action's key pose (its first by default), from whoever authors it now: a registered state or
    anims.keys_for's blockout. Looked up when the keys are built (once per build), so it follows their changes."""
    if (name, which) not in _OTHER:
        _register_air()
        if name in MOVES:
            n, fn = MOVES[name]
            keys = fn(None)[1]
        else:
            keys = anims.keys_for(name, anims.FRAMES.get(name, frames))
        _OTHER[(name, which)] = keys[which][1] if which >= 0 else keys[-1][1]
    return _OTHER[(name, which)]


def _register_air():
    """states_air (the jumps, falls and crouch) registers into MOVES only when anims.build calls its register(); a check
    run outside the build registers it here, so both see the same Fall, JumpF and SquatWait. Its SquatWaitItem (SquatWait
    as is) is dropped so this file's, with the item hand lifted off the floor, is the one built."""
    import states_air
    states_air.REG.pop('SquatWaitItem', None)
    if 'Fall' not in MOVES:
        states_air.register()


def fall_pose():
    return other_pose('Fall', 20)


def run_pose():
    return other_pose('Run', 18)


def squat_keys():
    n = 130
    _register_air()
    if 'SquatWait' in MOVES:
        n, fn = MOVES['SquatWait']
        return n, fn(None)[1]
    return n, anims.keys_for('SquatWait', n)


def aerial(src, t_arms=None, lean=0.0, turn=0.0, roll=0.0, head=(0, 0, 0), waist=(0, 0, 0), legs=None, drop=0.0):
    """An airborne pose from another action's (Fall's) pose: the whole body leaned (pitch), turned (yaw) and rolled about
    its middle, the chest and head turned, the legs replaced if given ({side: (thigh, shin)} world aims, before the turn),
    the arms set by t_arms(p, W) after."""
    p = as_pose(src)
    y0 = p.trans.get('YRotN', rig.JOINTS[3][2])
    r0 = p.local.get('YRotN', (0, 0, 0))
    p.move('YRotN', (y0[0], y0[1] + drop, y0[2])).rot('YRotN', (r0[0] + lean, r0[1] + turn, r0[2] + roll))
    if any(waist):
        w0 = p.local.get('WaistN', (0, 0, 0))
        p.rot('WaistN', tuple(a + b for a, b in zip(w0, waist)))
    if any(head):
        h0 = p.local.get('HeadN', (0, 0, 0))
        p.rot('HeadN', tuple(a + b for a, b in zip(h0, head)))
    if legs:
        for s, (th, sh) in legs.items():
            p.aim(f'{s}LegJ', rot_y(th, turn)); p.aim(f'{s}KneeJ', rot_y(sh, turn))
    if t_arms:
        t_arms(p, world(p))
    return p


def hop_feet(turn, lift, spread=1.0):
    """Both feet during a hop that turns the body: the stance turned by `turn`, lifted `lift`, toes pointing down a little."""
    out = {}
    for s in 'LR':
        x, y, z = FEET[s]
        x, _, z = rot_y((x * spread, 0, z * spread), turn)
        out[s] = dict(pos=(x, y + lift, z), yaw=TOE[s] + turn, pitch=0.35 * clamp(lift / 0.8) if lift > 1e-3 else None)
    return out


def toes(side, heel, turn=0.0, fwd=0.0):
    """A planted foot's heel raised `heel` radians about the ball of the foot (as base()'s heel lift), for rising on the
    toes; fwd slides the whole foot along its heading."""
    x, y, z = FEET[side]
    x, _, z = rot_y((x, 0, z), turn)
    yaw = TOE[side] + turn
    f = (math.sin(yaw), 0.0, math.cos(yaw))
    B, h = anims.BALL, y
    du = -B * math.cos(heel) + h * math.sin(heel) + B
    dv = B * math.sin(heel) + h * math.cos(heel) - h
    return dict(pos=(x + f[0] * (du + fwd), y + dv, z + f[2] * (du + fwd)), yaw=yaw, pitch=heel)


def step_foot(side, t, t0, t1, frm, to, height=0.6, turn0=0.0, turn1=0.0):
    """A foot stepping from `frm` to `to` (ankle positions, model space) between frames t0 and t1: an arc, the toes
    dipping as it lifts and levelling to land; planted outside the step."""
    u = clamp((t - t0) / float(t1 - t0))
    e = smooth(u)
    at = lerp(frm, to, e)
    lift = height * math.sin(PI * u)
    yaw = TOE[side] + turn0 + (turn1 - turn0) * e
    if 0 < u < 1:
        return dict(pos=(at[0], at[1] + lift, at[2]), yaw=yaw, pitch=0.3 * math.sin(PI * u))
    return dict(pos=at, yaw=yaw)


def stance(side, turn=0.0, dz=0.0, dx=0.0):
    x, y, z = FEET[side]
    x, _, z = rot_y((x, 0, z), turn)
    return (x + dx, y, z + dz)


# ---------------------------------------------------------------------------------------------------------------- pick-ups
@state('LightGet', 8)
def light_get():
    """A quick dip for the item (the template attaches it on frame 2): knees give, the right hand sweeps down to the floor
    in front of his lead foot and scoops it up to his side."""
    floor = (-0.9, 0.9, 2.5)

    def f(t):
        d = spline(t, [(0, 0), (2, 1, 'hold'), (3, 0.9), (8, 0)])
        W0 = world(body(crouch=1.05 * d, lean=0.72 * d, root=(0, 0, 0.3 * d), head=(0.2 * d, 0, 0)))
        rest = xf(REST_WRIST['R'], W0['WaistN'])
        reach = spline(t, [(0, 0), (2, 1, 'hold'), (3, 1), (8, 0)])
        tgt = lerp(rest, floor, reach) if t <= 3 else lerp(rest, _add(floor, (0.1, 0.6, -0.4)), reach)
        p = body(crouch=1.05 * d, lean=0.72 * d, root=(0, 0, 0.3 * d), head=(0.2 * d, 0, 0),
                 arms={'R': arm(reach=tgt, pole=(-0.7, 0.2, -0.6), weight=reach),
                       'L': arm(up=norm(_add(ARM0['L'][0], (0.05, 0.1, 0.2), d)), fore=norm(_add(ARM0['L'][1], (0.05, 0.2, 0.2), d)))})
        return p
    return sample(8, f)


# ---------------------------------------------------------------------------------------------------------------- light throws
# The frame each throw's item leaves the hand, measured in game (items_lab --releases: the director's LETGO line, the hand's
# item slot emptying, with the action's animation frame). It is the script's release command's frame (0x14 0) every time.
# The poses were keyed one frame early (released on 6, 6, 8, 6, 6, 3, and 6, 6, 5, 6 in the air), so each is retimed onto
# its measured frame: the windup stretched to it and the follow-through fitted into what is left (retimed()).
RELEASE = dict(LightThrowF=7, LightThrowB=7, LightThrowHi=9, LightThrowLw=7, LightThrowDrop=7, LightThrowDash=4,
               LightThrowAirF=7, LightThrowAirB=7, LightThrowAirHi=6, LightThrowAirLw=7,
               LightThrowLw4=5)                 # the smash down throw lets go on 5 (its script): its own animation
KEYED = dict(LightThrowF=6, LightThrowB=6, LightThrowHi=8, LightThrowLw=6, LightThrowDrop=6, LightThrowDash=3,
             LightThrowAirF=6, LightThrowAirB=6, LightThrowAirHi=5, LightThrowAirLw=6, LightThrowLw4=6)


def retimed(name, n, fn):
    """fn (a pose of t keyed with its release on KEYED[name]) on the game's release frame RELEASE[name]: frames 0..rel map
    onto 0..keyed and rel..n onto keyed..n, so the first and last frames stay the idle's"""
    a, b = KEYED[name], RELEASE[name]
    return lambda t: fn(t * a / b if t <= b else a + (t - b) * (n - a) / (n - b))


def throw_f_pose(t):
    """LightThrowF (25; the item leaves the hand on frame 6): an overhand throw. The weight rocks back as the torso coils
    away and the arm cocks behind his head, the left hand points the way; the hips lead the whip forward, the arm comes
    over the top (released in front of his face), the weight lands on the front foot and the arm follows through across
    his body, then he settles back."""
    coil = spline(t, [(0, 0), (4, 1, 'hold'), (5, 0.3), (6, -0.6), (8, -1, 'hold'), (13, -0.8), (25, 0)])
    wt = spline(t, [(0, 0), (4, -0.35), (6, 0.2), (8, 0.55, 'hold'), (13, 0.45), (25, 0)])
    dn = spline(t, [(0, 0), (4, 0.3), (8, 1, 'hold'), (14, 0.7), (25, 0)])
    p = body(crouch=0.3 * dn, lean=0.1 * coil * -1 + 0.25 * clamp(-coil, 0, 1), root=(0, 0, wt),
             hip=(0, -0.25 * coil, 0), waist=(0, -0.45 * coil, 0.05 * coil), head=(0.05 * dn, 0.35 * coil, 0))
    W = world(p)
    rw = REST_WRIST['R']
    wrist = cpath(t, [(0, rw), (2, (-1.9, 1.8, -0.6)), (4, (-1.7, 4.1, -1.9), 'hold'), (5, (-1.4, 4.7, -0.2)),
                      (6, (-0.9, 4.0, 2.2)), (7, (-0.1, 2.4, 2.9)), (8, (0.6, 1.2, 2.4), 'hold'), (13, (0.5, 1.2, 2.2)),
                      (19, (-0.6, 0.2, 1.2)), (25, rw)], W)
    lw = REST_WRIST['L']
    lwrist = cpath(t, [(0, lw), (4, (1.4, 3.0, 2.6), 'hold'), (6, (1.6, 1.8, 1.0)), (8, (2.0, 0.6, -0.6), 'hold'),
                       (14, (1.9, 0.5, -0.2)), (25, lw)], W)
    act = spline(t, [(0, 0), (2, 1), (22, 1), (25, 0)])
    set_arm(p, 'R', arm(reach=wrist, pole=(-0.8, -0.5, -0.4), weight=act), W, None)
    set_arm(p, 'L', arm(reach=lwrist, pole=(0.8, -0.6, -0.3), weight=act), W, None)
    return p


state('LightThrowF', 25)(lambda: sample(25, retimed('LightThrowF', 25, throw_f_pose)))


def throw_b_pose(t):
    """LightThrowB (25; the facing flips on frame 2 and the item leaves on frame 6, thrown the way he had his back to):
    a hop and a half turn toward the camera, the arm whipping round and releasing as he comes about, landing in his
    stance facing the other way (authored in the old facing: it ends on base() turned half round)."""
    turn = -PI * smooth(spline(t, [(0, 0), (2, 0.04), (6, 0.85), (8, 1.0, 'hold'), (25, 1.0)]))
    hop = spline(t, [(0, 0), (1, -0.25), (2, -0.3), (4, 0.75), (6, 0.5), (7, 0), (8, -0.35), (11, -0.15), (25, 0)])
    lift = clamp(spline(t, [(0, 0), (2, 0), (4, 0.9), (6, 0.45), (7, 0), (25, 0)]), 0, 2)
    crouch = clamp(-hop, 0, 1) * 1.2
    p = body(crouch=crouch, bob=max(hop, 0) * 1.4, turn=turn, lean=0.2 * clamp(-hop, 0, 1),
             waist=(0, spline(t, [(0, 0), (2, 0.35), (5, -0.3), (8, -0.45, 'hold'), (14, -0.3), (25, 0)]), 0),
             head=(0.05 * spline(t, [(0, 0), (4, 1), (20, 1), (25, 0)]), spline(t, [(0, 0), (2, -0.35), (6, 0.2), (10, 0.1), (25, 0)]), 0),
             feet=hop_feet(turn, lift) if lift > 1e-4 else None)
    W = world(p)
    rw, lw = REST_WRIST['R'], REST_WRIST['L']
    wrist = cpath(t, [(0, rw), (2, (0.6, 1.8, 1.4)), (4, (-1.4, 3.2, -1.2)), (6, (-2.4, 3.4, 1.8)), (7, (-1.4, 2.6, 2.8)),
                      (9, (0.2, 1.4, 2.4), 'hold'), (14, (0.1, 1.2, 2.0)), (25, rw)], W)
    lwrist = cpath(t, [(0, lw), (3, (2.2, 2.4, -0.8)), (6, (2.3, 1.4, -1.6)), (9, (2.0, 0.8, -0.8), 'hold'), (25, lw)], W)
    act = spline(t, [(0, 0), (2, 1), (21, 1), (25, 0)])
    set_arm(p, 'R', arm(reach=wrist, pole=(-0.6, -0.6, -0.5), weight=act), W, None)
    set_arm(p, 'L', arm(reach=lwrist, pole=(0.8, -0.5, 0.3), weight=act), W, None)
    return p


state('LightThrowB', 25)(lambda: sample(25, retimed('LightThrowB', 25, throw_b_pose)))


def throw_hi_pose(t):
    """LightThrowHi (24; released on frame 8): he sinks, then springs up onto his toes whipping the arm straight up past
    his ear, the chest arching and the chin lifting to watch it go, and drops back into his stance."""
    sink = spline(t, [(0, 0), (4, 1, 'hold'), (6, 0.2), (8, -1, 'hold'), (11, -0.8), (15, 0.25), (19, 0), (24, 0)])
    up = clamp(-sink, 0, 1)
    down = clamp(sink, 0, 1)
    heel = 0.45 * up
    feet = {s: toes(s, heel) for s in 'LR'} if heel > 1e-4 else None
    p = body(crouch=0.55 * down, bob=0.55 * up, lean=0.25 * down - 0.22 * up, head=(0.15 * down - 0.45 * up, -0.1 * up, 0),
             waist=(0, -0.15 * down + 0.1 * up, 0), feet=feet)
    W = world(p)
    rw, lw = REST_WRIST['R'], REST_WRIST['L']
    wrist = cpath(t, [(0, rw), (4, (-1.9, 0.4, -1.4), 'hold'), (6, (-2.0, 2.4, 0.2)), (8, (-1.1, 5.4, 0.6)),
                      (10, (-0.9, 5.6, 0.2), 'hold'), (14, (-1.6, 3.0, 0.4)), (19, (-2.0, 0.8, 0.3)), (24, rw)], W)
    lwrist = cpath(t, [(0, lw), (4, (1.6, 1.0, 1.6), 'hold'), (8, (2.2, 1.4, -0.4), 'hold'), (14, (1.9, 0.6, 0.4)), (24, lw)], W)
    act = spline(t, [(0, 0), (3, 1), (20, 1), (24, 0)])
    set_arm(p, 'R', arm(reach=wrist, pole=(-0.9, 0.0, -0.4), weight=act), W, None)
    set_arm(p, 'L', arm(reach=lwrist, pole=(0.8, -0.6, -0.2), weight=act), W, None)
    return p


state('LightThrowHi', 24)(lambda: sample(24, retimed('LightThrowHi', 24, throw_hi_pose)))


def throw_lw_pose(t):
    """LightThrowLw (25; released on frame 6): the arm cocks up over his head as he rises, then he slams it down at the
    floor in front, folding into a low crouch over it, and rises."""
    rise = spline(t, [(0, 0), (4, 1, 'hold'), (5, 0.2), (6, -1), (9, -1.05, 'hold'), (14, -0.8), (25, 0)])
    up, down = clamp(rise, 0, 1), clamp(-rise, 0, 1.1)
    p = body(crouch=0.9 * down, bob=0.2 * up, lean=0.55 * down - 0.1 * up, root=(0, 0, 0.35 * down),
             head=(0.3 * down - 0.2 * up, 0, 0), waist=(0, -0.25 * up + 0.1 * down, 0))
    W = world(p)
    rw, lw = REST_WRIST['R'], REST_WRIST['L']
    wrist = cpath(t, [(0, rw), (4, (-1.3, 5.2, -1.0), 'hold'), (5, (-1.2, 4.2, 1.4)), (6, (-0.8, 0.6, 3.2)),
                      (9, (-0.7, -0.3, 3.1), 'hold'), (14, (-1.2, 0.2, 2.2)), (25, rw)], W)
    lwrist = cpath(t, [(0, lw), (4, (1.8, 1.0, 1.8), 'hold'), (6, (2.2, 0.6, -0.4)), (10, (2.0, 0.4, -0.3), 'hold'), (25, lw)], W)
    act = spline(t, [(0, 0), (3, 1), (21, 1), (25, 0)])
    set_arm(p, 'R', arm(reach=wrist, pole=(-0.9, 0.3, -0.3), weight=act), W, None)
    set_arm(p, 'L', arm(reach=lwrist, pole=(0.8, -0.5, -0.2), weight=act), W, None)
    return p


state('LightThrowLw', 25)(lambda: sample(25, retimed('LightThrowLw', 25, throw_lw_pose)))
state('LightThrowLw4', 25)(lambda: sample(25, retimed('LightThrowLw4', 25, throw_lw_pose)))


def throw_drop_pose(t):
    """LightThrowDrop (24; let go on frame 6; the engine pops the item up behind him, as the cast's toss it over the shoulder):
    a careless flick of the wrist, the item tossed up and back over his right shoulder, a little shrug, and back."""
    toss = spline(t, [(0, 0), (3, -0.3), (6, 0.7), (9, 1.0, 'hold'), (13, 0.8), (24, 0)])
    p = body(lean=-0.05 * max(toss, 0) + 0.05 * max(-toss, 0), hip=(0, -0.04 * toss, 0), waist=(0, -0.12 * toss, -0.03 * toss),
             head=(-0.05 * toss, 0.15 * toss, 0.04 * toss))
    W = world(p)
    rw = REST_WRIST['R']
    wrist = cpath(t, [(0, rw), (3, _add(rw, (0.1, 0.3, 0.9))), (6, (-1.9, 3.8, 0.9)), (9, (-1.8, 4.6, -0.8), 'hold'),
                      (13, (-2.0, 3.6, -0.5)), (24, rw)], W)
    act = spline(t, [(0, 0), (2, 1), (18, 1), (24, 0)])
    set_arm(p, 'R', arm(reach=wrist, pole=(-0.8, -0.5, 0.2), weight=act), W, None)
    return p


state('LightThrowDrop', 24)(lambda: sample(24, retimed('LightThrowDrop', 24, throw_drop_pose)))


def throw_dash_pose(t):
    """LightThrowDash (40, root motion: the template's slide; released on frame 3): out of the run the arm whips forward
    at once, the lead foot plants and he skids low behind it, leaning back against the slide, then straightens up."""
    run = run_pose()
    brace = spline(t, [(0, 0.3), (3, 0.8), (8, 1, 'hold'), (20, 0.85), (30, 0.3), (40, 0)])
    lean = spline(t, [(0, 0.45), (3, 0.5), (6, 0.1), (12, -0.12), (22, -0.05), (32, 0.05), (40, 0)])
    lead = spline(t, [(0, 0), (4, 1, 'hold'), (26, 1), (36, 0, 'hold'), (40, 0)])
    feet = {'L': dict(pos=stance('L', dz=1.2 * lead)), 'R': dict(pos=stance('R', dz=-0.6 * lead))}
    p = body(crouch=0.55 * brace, lean=lean, root=(0, 0, -0.2 * brace),
             hip=(0, 0.1 * brace, 0), waist=(0, spline(t, [(0, -0.3), (3, 0.4), (8, 0.35), (24, 0.15), (40, 0)]), 0),
             head=(-0.1 * brace, -0.1 * brace, 0), feet=feet)
    W = world(p)
    rw, lw = REST_WRIST['R'], REST_WRIST['L']
    wrist = cpath(t, [(0, (-1.8, 2.8, -1.2)), (2, (-1.3, 4.0, 1.0)), (3, (-0.6, 3.0, 2.9)), (5, (0.3, 1.4, 2.6)),
                      (8, (0.6, 0.8, 2.0), 'hold'), (22, (0.3, 0.7, 1.8)), (32, (-1.2, 0.3, 0.8)), (40, rw)], W)
    lwrist = cpath(t, [(0, (1.8, 1.4, 1.2)), (3, (2.1, 1.0, -0.8)), (8, (2.3, 1.8, -0.4), 'hold'), (22, (2.1, 1.4, 0.2)),
                       (40, lw)], W)
    act = spline(t, [(0, 1), (32, 1), (40, 0)])
    set_arm(p, 'R', arm(reach=wrist, pole=(-0.8, -0.5, -0.3), weight=act), W, None)
    set_arm(p, 'L', arm(reach=lwrist, pole=(0.8, -0.3, -0.4), weight=act), W, None)
    if t < 3:                                          # out of whatever frame of the run: blend over the throw's windup
        return mix(run, p, smooth(t / 3.0)) if t > 0 else run
    return p


state('LightThrowDash', 40)(lambda: sample(40, retimed('LightThrowDash', 40, throw_dash_pose)))


# ---------------------------------------------------------------------------------------------------------------- air throws
def src_arm(W, side):
    """An arm's current world directions (the upper arm and forearm), for blending from another action's pose."""
    return tuple(W[f'{side}ShoulderJ'][0][:3]), tuple(W[f'{side}ArmJ'][0][:3])


def air_arm(p, W, side, target, pole, w):
    """An arm reaching `target` by IK, by weight w from where the source pose (Fall's) holds it."""
    up, fore = src_arm(W, side)
    set_arm(p, side, arm(world_up=up, world_fore=fore, reach=target, pole=pole, weight=w), W, None)


def air_throw(name, n, rel, lean_k, turn_k, wrist_keys, lwrist_keys, knees=None, flip=False):
    """An aerial throw: Fall's pose, the body pitched/turned by keyed amounts, the arms along chest-frame paths."""
    def f(t):
        src = fall_pose()
        lean = spline(t, lean_k)
        turn = -PI * smooth(spline(t, turn_k)) if flip else spline(t, turn_k)
        act = spline(t, [(0, 0), (2, 1), (n - 5, 1), (n, 0)])
        k = spline(t, knees) if knees else 0.0
        legs = None
        if knees:
            legs = {s: ((sx * 0.1, -1 + 0.9 * k, 0.5 + 0.6 * k + 0.1 * sx), (0, -1, -0.2 - 0.5 * k)) for s, sx in (('L', 1), ('R', -1))}

        def arms(p, W):
            wr = cpath(t, wrist_keys, W)
            lw = cpath(t, lwrist_keys, W)
            air_arm(p, W, 'R', wr, (-0.8, -0.4, -0.4), act)
            air_arm(p, W, 'L', lw, (0.8, -0.5, -0.2), act)
        if k and act < 1e-6:
            legs = None
        p = aerial(src, arms, lean=lean, turn=turn, waist=(0, spline(t, [(0, 0), (3, -0.3), (rel, 0.3), (rel + 4, 0.35), (n, 0)]) * (0 if flip else 1), 0),
                   legs=legs if (knees and k > 1e-6) else None)
        return src if t == 0 else p
    return f


RW, LW = REST_WRIST['R'], REST_WRIST['L']
state('LightThrowAirF', 25)(lambda: sample(25, retimed('LightThrowAirF', 25, air_throw('LightThrowAirF', 25, 6,
      [(0, 0), (4, -0.2), (6, 0.15), (9, 0.3, 'hold'), (14, 0.25), (25, 0)], [(0, 0), (25, 0)],
      [(0, RW), (2, (-1.9, 1.8, -0.6)), (4, (-1.7, 4.0, -1.8), 'hold'), (5, (-1.3, 4.6, -0.1)), (6, (-0.8, 3.8, 2.3)),
       (8, (0.4, 1.6, 2.6), 'hold'), (14, (0.3, 1.4, 2.2)), (25, RW)],
      [(0, LW), (4, (1.5, 3.0, 2.4), 'hold'), (8, (2.0, 0.8, -0.6), 'hold'), (25, LW)]))))
state('LightThrowAirB', 25)(lambda: sample(25, retimed('LightThrowAirB', 25, air_throw('LightThrowAirB', 25, 6,
      [(0, 0), (3, 0.1), (6, -0.15), (10, -0.1), (25, 0)], [(0, 0), (2, 0.05), (6, 0.8), (9, 1.0, 'hold'), (25, 1.0)],
      [(0, RW), (2, (0.6, 1.8, 1.4)), (4, (-1.4, 3.2, -1.2)), (6, (-2.4, 3.4, 1.8)), (7, (-1.4, 2.6, 2.8)),
       (9, (0.2, 1.4, 2.4), 'hold'), (14, (0.1, 1.2, 2.0)), (25, RW)],
      [(0, LW), (3, (2.2, 2.4, -0.8)), (6, (2.3, 1.4, -1.6)), (9, (2.0, 0.8, -0.8), 'hold'), (25, LW)], flip=True))))
state('LightThrowAirHi', 25)(lambda: sample(25, retimed('LightThrowAirHi', 25, air_throw('LightThrowAirHi', 25, 5,
      [(0, 0), (3, 0.15), (5, -0.3), (8, -0.35, 'hold'), (14, -0.2), (25, 0)], [(0, 0), (25, 0)],
      [(0, RW), (3, (-1.9, 0.4, -1.2), 'hold'), (4, (-1.9, 2.6, 0.4)), (5, (-1.0, 5.3, 0.6)), (8, (-0.9, 5.5, 0.1), 'hold'),
       (14, (-1.6, 3.0, 0.4)), (25, RW)],
      [(0, LW), (3, (1.6, 1.0, 1.6), 'hold'), (6, (2.2, 1.2, -0.4), 'hold'), (25, LW)]))))
state('LightThrowAirLw', 25)(lambda: sample(25, retimed('LightThrowAirLw', 25, air_throw('LightThrowAirLw', 25, 6,
      [(0, 0), (4, -0.2), (6, 0.35), (9, 0.4, 'hold'), (15, 0.2), (25, 0)], [(0, 0), (25, 0)],
      [(0, RW), (4, (-1.3, 5.0, -0.8), 'hold'), (5, (-1.2, 3.8, 1.2)), (6, (-0.6, -0.6, 2.2)), (9, (-0.5, -1.2, 1.6), 'hold'),
       (15, (-1.2, 0.0, 1.4)), (25, RW)],
      [(0, LW), (4, (1.8, 1.4, 1.6), 'hold'), (7, (2.2, 1.2, -0.6), 'hold'), (25, LW)],
      knees=[(0, 0), (4, 0.2), (7, 0.9), (11, 0.9, 'hold'), (20, 0.2), (25, 0)]))))


def throwN_world(p, at, rot=(0, 0, 0)):
    """Put ThrowN (the heavy item's attachment, the lookup table's byte 0x11) at a model-space point with a model-space
    rotation (Euler XYZ), whatever YRotN is doing (ThrowN is YRotN's child)."""
    W = world(p)
    Y = W['YRotN']
    p.move('ThrowN', to_local(at, Y))
    R = rig.rot_xyz(*rot)
    Rl = [[sum(R[i][k] * Y[j][k] for k in range(3)) for j in range(3)] for i in range(3)]   # R . Y^T (row vectors)
    p.rot('ThrowN', anims.euler_xyz(Rl))
    return p


# ---------------------------------------------------------------------------------------------------------------- heavy items
# A crate, barrel or party ball hangs on ThrowN (ftpickupitem_800948A8: heavy items attach to the lookup table's byte 0x11,
# the shield bone, not the hand) by its model's attach joint, the centre of its -Z face: the item's centre is ThrowN plus
# 7.5 along ThrowN's local +Z, and a crate is 15 a side (ItCo.dat's joints and meshes; measured in game, pass 5). That is
# as tall as he is. His arms reach 13.6 over the floor beside his head, his head (5.9 across with the curls, the nose 4.7
# in front) and cap rise to 16.2: he can't hold it out in front (his arms don't reach past his nose) or over his head. He
# carries it on his head, as people carry loads, the crate's weight squashing his cap and his arms up either side of his
# head bracing its bottom: the cast's overhead carry, fitted to his reach. He tosses it up there (HeavyGet), walks
# carefully under it and pitches it off (the heavy throws).
CRATE = 7.5                                # half the crate's side
ATTACH = 7.5                               # the item's centre from ThrowN, along ThrowN's +Z
HEAD_TOP = (0.0, 3.1, 0.35)                # where the crate's bottom rests (HeadN's frame): inside the cap, above his brow
HEAVY_BODY = dict(crouch=0.32, lean=0.0, root=(0, 0, 0), hip=(0, -0.5 * S['hip_yaw'], 0), waist=(0, 0, 0),
                  head=(0.02, -0.7 * S['head_yaw'], 0))
# the wrists: his forearms are 1.1 thick and their cuffs reach 1.1 past the wrist, his mitten hands 1.0 thick on the palm
# side (the production model): under its bottom, either side of his head and clear of it (it is 5.9 across), palms up
GRIP_UNDER = ((-4.3, -CRATE - 1.05, -0.2), (4.3, -CRATE - 1.05, -0.2))
GRIP_LOW = ((-3.4, -2.3, -CRATE - 1.2), (3.4, -2.3, -CRATE - 1.2))          # palms on its near face, low (the pick-up)
POLE_UP = (0.95, -0.1, 0.3)                # elbows out to the sides (the right arm mirrors x)
POLE_LOW = (0.7, -0.5, -0.5)


def attach_at(c, r):
    """ThrowN's place for an item centred at c with rotation r (model space)."""
    z = rig.rot_xyz(*r)[2][:3]
    return tuple(ci - ATTACH * zi for ci, zi in zip(c, z))


def crate_mat(c, r):
    m = rig.rot_xyz(*r)
    m[3] = [c[0], c[1], c[2], 1]
    return m


def crate_hands(c, r, pts):
    M = crate_mat(c, r)
    return tuple(xf(q, M) for q in pts)


def heavy_body(**extra):
    kw = dict(HEAVY_BODY)
    for k, v in extra.items():
        if k in kw and isinstance(v, tuple):
            kw[k] = _add(kw[k], v)
        elif k in kw:
            kw[k] = kw[k] + v
        else:
            kw[k] = v
    return body(**kw)


def on_head(W, dy=0.0, dz=0.0):
    """The crate's centre riding on his head: its bottom on the head's crown point (it rides his bob and sway, not the
    head's tilt: it stays level)."""
    b = xf(HEAD_TOP, W['HeadN'])
    return (b[0], b[1] + CRATE + dy, b[2] + dz)


def crate_palms(p, c, r, w, under=1.0):
    """Both palms flat on the crate: under its bottom, fingers pointing out from his head, a tray held up (under=1), or
    on its near face, fingers up (under=0), blended. (Fingers forward, the 2.7-long mittens stuck out past his face.)"""
    M = crate_mat(c, r)
    palm = norm(vec_mat(lerp((0, 0, 1), (0, 1, 0), under), M))          # the way the palm faces (into the crate)
    for sd, sx in (('R', -1), ('L', 1)):
        f = norm(vec_mat(lerp((-sx * 0.25, 1, 0), (sx, 0, 0.35), under), M))
        hand_blend(p, sd, f, [-x for x in palm], w)
    return p


def hands_on(p, c, r, grip, w=1.0, under=1.0, pole=POLE_UP):
    """Both wrists to crate-frame points (w blends from the arms' own pose), the palms turned onto it."""
    if w <= 1e-6:
        return p
    W = world(p)
    rh, lh = crate_hands(c, r, grip)
    set_arm(p, 'R', arm(reach=rh, pole=(-pole[0], pole[1], pole[2]), weight=w), W, None)
    set_arm(p, 'L', arm(reach=lh, pole=pole, weight=w), W, None)
    return crate_palms(p, c, r, w, under)


def place_crate(p, c, r=(0, 0, 0), grip=GRIP_UNDER, w=1.0, under=1.0, pole=POLE_UP):
    """ThrowN where the item centred at c (rotation r) hangs, and both hands on it."""
    throwN_world(p, attach_at(c, r), r)
    return hands_on(p, c, r, grip, w, under, pole)


def heavy_hold(sway=0.0, bob=0.0, feet=None, trans=None, tilt=(0.0, 0.0), turn=0.0):
    """The carry: the crate on his head, arms up either side bracing its bottom, knees bent under the weight, hips and
    head squared to it. HeavyGet ends here and LiftWait freezes it; the walks and heavy throws start from it. tilt
    (forward, sideways) rocks the crate on his head."""
    p = heavy_body(bob=bob, root=(sway, 0, 0), hip=(0, 0, -0.08 * sway), feet=feet, trans=trans, turn=turn)
    W = world(p)
    return place_crate(p, on_head(W), (tilt[0], turn, tilt[1]))


def heavy_get_pose(t):
    """HeavyGet (27; the engine hangs the crate on ThrowN on frame 2, from where it lies in front of him): he squats, his
    cheek turned to it and his palms low on its near face, drives up with his legs and flings it up and back over his
    head (the hands let go at 10), ducks under it with his arms up, and takes it on his head at 16, knees buckling; a
    wobble, and he settles into the carry."""
    n = 27
    if t >= n:
        return heavy_hold()
    hb = HEAVY_BODY
    crouch = spline(t, [(0, 0), (3, 0.9, 'hold'), (6, 0.95), (10, 0.05), (13, 0.12), (16, 0.3), (18, 0.62), (21, 0.28), (24, 0.38),
                        (27, hb['crouch'])])
    bob = clamp(spline(t, [(0, 0), (8, 0), (10, 0.35), (12, 0.2), (14, 0), (27, 0)]), 0, 1)
    lean = spline(t, [(0, 0), (3, 0.1, 'hold'), (6, 0.12), (10, -0.2), (13, -0.08), (16, 0.02), (18, 0.1), (21, -0.03), (27, hb['lean'])])
    rz = spline(t, [(0, 0), (3, 0.35), (7, 0.2), (11, -0.2), (16, 0), (27, 0)])
    hpitch = spline(t, [(0, 0), (3, 0.12), (7, 0.05), (10, -0.35), (13, -0.2), (16, 0.08), (18, 0.14), (22, 0.0), (27, hb['head'][0])])
    turned = spline(t, [(0, 0), (3, 1, 'hold'), (8, 1), (11, 0), (27, 0)])             # his cheek to the crate while he
    hyaw = -1.1 * smooth(turned) + (-0.7 * S['head_yaw']) * smooth(spline(t, [(0, 0), (10, 0), (16, 1), (27, 1)]))   # squats
    sq = smooth(spline(t, [(0, 0), (8, 0), (16, 1), (27, 1)]))
    p = body(crouch=crouch, bob=bob, lean=lean, root=(0, 0, rz), hip=(0, hb['hip'][1] * sq, 0), head=(hpitch, hyaw, 0))
    W = world(p)
    land = on_head(W)
    floor = (0.0, CRATE + 0.15, 5.4 + CRATE)
    # the crate: on the floor, lifted with the legs, flung (off his palms at 10), over his head and down onto it at 16
    if t <= 16:
        c = spline(t, [(0, floor), (2, floor, 'hold'), (6, (0.0, CRATE + 0.5, 5.3 + CRATE)), (8, (0.0, CRATE + 2.4, 5.1 + CRATE)),
                       (10, (0.0, CRATE + 6.5, 4.8 + CRATE)), (12, (0.0, 21.2, 10.8)), (13, (0.0, 24.3, 7.0)), (14, (0.0, 25.0, 3.0)),
                       (15, (0.0, 23.6, 1.2)), (16, land)])
        tip = spline(t, [(0, 0), (6, 0), (10, -0.12), (13, -0.08), (16, 0)])
    else:                                  # riding his head: it squashes him and rocks as he takes the weight
        c = land
        tip = 0.07 * math.sin(PI * (t - 16) / 5.5) * math.exp(-(t - 16) / 6.0)
    r = (tip, 0.0, 0.0)
    if t >= 2:                             # the engine takes it on frame 2; till then ThrowN rests (Wait1's, the seam)
        throwN_world(p, attach_at(c, r), r)
    # the hands: on its near face (to 10), off it and up (10-15), under its bottom from 15
    on_face = spline(t, [(0, 0), (3, 1, 'hold'), (9, 1), (11, 0), (27, 0)])
    if t <= 11 and on_face > 1e-6:
        return hands_on(p, c, r, GRIP_LOW, on_face, under=0.0, pole=POLE_LOW)
    up = smooth(spline(t, [(0, 0), (10, 0), (15, 1), (27, 1)]))
    if t < 15:                              # reaching up to catch it: the wrists rise toward where its bottom will be
        W = world(p)
        rh, lh = crate_hands(land, (0, 0, 0), GRIP_UNDER)
        for sd, h, pl in (('R', rh, (-POLE_UP[0], POLE_UP[1], POLE_UP[2])), ('L', lh, POLE_UP)):
            set_arm(p, sd, arm(reach=(h[0], h[1] - 1.2 * (1 - up), h[2] + 0.8 * (1 - up)), pole=pl, weight=up), W, None)
        return crate_palms(p, land, (0, 0, 0), up, 1.0)
    return hands_on(p, c, r, GRIP_UNDER, 1.0, 1.0)


state('HeavyGet', 27)(lambda: sample(27, heavy_get_pose))

HEAVY_STEP = 4.4                       # TransN per walk: Mario's 4.0 at Geno's world scale (anims.MARIO_SCALE)


def heavy_walk(first):
    """HeavyWalk1 / 2 (40 each, root motion; the engine alternates them while the stick is held and freezes the last pose
    in LiftWait between): two short careful steps under the crate, rear foot then front (Walk2 the other way round), the
    body rolling over each planted foot and the crate rocking a little on his head against the step, so each walk ends
    in the carry's stance and every seam meets. TransN is his own: the planted foot holds still on the floor."""
    def f(t):
        n = 40
        z = HEAVY_STEP * spline(t, [(0, 0), (10, 0.3), (20, 0.5), (30, 0.8), (40, 1.0)])
        order = ('R', 'L') if first else ('L', 'R')
        feet = {}
        for k, sd in enumerate(order):
            t0, t1 = (3, 18) if k == 0 else (23, 38)
            a = stance(sd)
            b = (a[0], a[1], a[2] + HEAVY_STEP)
            feet[sd] = step_foot(sd, t, t0, t1, a, b, height=0.45)
        sgn = 1 if first else -1
        sway = 0.22 * math.sin(TAU * t / n) * sgn
        bob = -0.12 * (0.5 - 0.5 * math.cos(TAU * 2 * t / n))
        tilt = (0.025 * math.sin(TAU * 2 * t / n), -0.03 * math.sin(TAU * t / n) * sgn)
        return heavy_hold(sway=sway, bob=bob, feet=feet, trans=(0, 0, z), tilt=tilt)
    return f


state('HeavyWalk1', 40)(lambda: sample(40, heavy_walk(True)))
state('HeavyWalk2', 40)(lambda: sample(40, heavy_walk(False)))


def heavy_throw(n, rel, kind):
    """Heavy throws from the carry (LiftWait's frozen pose) to base(), the crate pitched off his head. The engine lets go
    on `rel` (the template's release command: F and B 18, Hi 14, Lw 11), placing the thrown crate at the centre it had
    (ThrowN plus its attach offset, read that frame and the one before), so ThrowN follows the crate's path two frames
    past it. F dips and drives up, pushing it forward off his head so it tips away; Hi dips deeper and springs onto his
    toes, arms shoving it straight up; Lw shoves it forward off his head and bows after it as it tips over in front of
    him; B hops round with it riding his head (the facing flips after the release: authored in the old facing, so the
    heave and the rest of it are half a turn round), then heaves it like F."""
    hb = HEAVY_BODY
    hs = 0 if kind != 'B' else 11                     # B: the heave starts after the hop round

    def pose_at(t):
        rest = smooth(spline(t, [(0, 0), (rel + 3, 0), (n - 2, 1), (n, 1)]))
        turn, feet = 0.0, None
        if kind == 'B':
            turn = -PI * smooth(spline(t, [(0, 0), (3, 0), (10, 1.0, 'hold'), (n, 1.0)]))
            lift = clamp(spline(t, [(0, 0), (3, 0), (6, 0.8), (8, 0.5), (10, 0), (n, 0)]), 0, 2)
            if lift > 1e-4:
                feet = hop_feet(turn, lift)
        if kind in ('F', 'B'):
            crouch = spline(t, [(0, hb['crouch']), (hs + 2, 0.34), (hs + 3, 0.5), (rel - 6, 0.68, 'hold'), (rel - 1, 0.0), (rel + 2, -0.25),
                                (rel + 7, 0.3), (rel + 13, 0.15), (n, 0)] if kind == 'F' else
                            [(0, hb['crouch']), (2, 0.6), (4, -0.2), (7, -0.15), (10, 0.6), (12, 0.66, 'hold'), (rel - 1, 0.0),
                             (rel + 2, -0.25), (rel + 7, 0.3), (rel + 13, 0.15), (n, 0)])
            lean = spline(t, [(0, hb['lean']), (rel - 6, -0.05, 'hold'), (rel - 1, 0.12), (rel + 3, 0.3), (rel + 9, 0.2), (n, 0)])
            hp = spline(t, [(0, hb['head'][0]), (rel - 6, 0.05), (rel - 1, -0.1), (rel + 3, 0.1), (n, 0)])
            contact = spline(t, [(0, 1), (rel - 3, 1), (rel - 1, 0.6), (rel + 1, 0), (n, 0)])
        elif kind == 'Hi':
            crouch = spline(t, [(0, hb['crouch']), (6, 0.85, 'hold'), (rel - 1, -0.3), (rel + 3, -0.32, 'hold'), (rel + 8, 0.35), (n, 0)])
            lean = spline(t, [(0, hb['lean']), (6, 0.04), (rel, -0.1), (rel + 5, -0.05), (n, 0)])
            hp = spline(t, [(0, hb['head'][0]), (6, 0.1), (rel, -0.45), (rel + 6, -0.3), (n, 0)])
            contact = spline(t, [(0, 1), (rel - 2, 1), (rel, 0.55), (rel + 2, 0), (n, 0)])
        else:   # Lw: shoved forward off his head; it tips over in front of him and he bows after it
            crouch = spline(t, [(0, hb['crouch']), (3, 0.2), (7, 0.4), (rel, 0.7), (rel + 5, 0.8, 'hold'), (rel + 10, 0.5), (n, 0)])
            lean = spline(t, [(0, hb['lean']), (3, -0.1), (7, 0.05), (rel, 0.3), (rel + 5, 0.45, 'hold'), (rel + 11, 0.3), (n, 0)])
            hp = spline(t, [(0, hb['head'][0]), (3, -0.08), (7, 0.05), (rel, 0.2), (rel + 6, 0.2), (n, 0)])
            contact = spline(t, [(0, 1), (4, 1), (6, 0.7), (8, 0), (n, 0)])
        bob = 0.0
        if crouch < 0:                   # rising onto the toes
            bob, crouch = -crouch * 1.4, 0.0
            if feet is None:
                feet = {sd: toes(sd, 0.5 * clamp(bob / 0.35), turn) for sd in 'LR'}
        hq = lambda a: a * (1 - rest)
        p = body(crouch=crouch, bob=bob, lean=lean, turn=turn, hip=(0, hq(hb['hip'][1]), 0),
                 head=(hp, hq(hb['head'][1]), 0), feet=feet)
        return p, turn, contact

    def crate_at(t, W, turn):
        """The crate's centre and rotation at t (to rel), from his head's place in pose W."""
        seat = on_head(W)
        if kind == 'Lw':
            L = rel - 11                                  # the keys were laid out for a release on 10: shifted with it
            c = spline(t, [(0, seat), (3, _add(seat, (0, 0.3, 0.6))), (5 + L + 1, (0, 20.3, 5.5)), (7 + L + 1, (0, 17.5, 10.0)),
                           (9 + L + 1, (0, 12.5, 13.5)), (rel, (0, 10.0, 14.2))])
            tipx = spline(t, [(0, 0), (3, 0.05), (5 + L + 1, 0.35), (7 + L + 1, 0.9), (9 + L + 1, 1.35), (rel, PI / 2)])
            return c, (tipx, turn, 0.0)
        if kind in ('F', 'B'):
            path = [(hs, (0, 0, 0)), (rel - 6, (0, 0, 0)), (rel - 3, (0, 1.0, 1.2)), (rel, (0, 3.2, 5.2))]
            tip = [(hs, 0.0), (rel - 5, -0.04), (rel - 2, 0.12), (rel, 0.5)]
        else:
            path = [(0, (0, 0, 0)), (6, (0, 0, 0)), (rel - 4, (0, 0.9, 0.1)), (rel - 2, (0, 2.4, 0.2)), (rel, (0, 4.8, 0.3))]
            tip = [(0, 0.0), (rel - 2, 0.0), (rel, -0.05)]
        return _add(seat, rot_y(spline(t, path), turn)), (spline(t, tip), turn, 0.0)

    def f(t):
        if t == 0:
            return heavy_hold()
        p, turn, contact = pose_at(t)
        W = world(p)
        if t <= rel:
            c, r = crate_at(t, W, turn)
        else:                                             # after the release: where it was going (ThrowN only, to rel+2)
            pr, tr, _ = pose_at(rel)
            pq, tq, _ = pose_at(rel - 1)
            c1, r = crate_at(rel, world(pr), tr)
            c0, _ = crate_at(rel - 1, world(pq), tq)
            c = tuple(a + (a - b) * (t - rel) for a, b in zip(c1, c0))
        if t <= rel + 2:
            throwN_world(p, attach_at(c, r), r)
        # the hands: under its bottom (Lw: shoving its bottom, which faces him as it tips), then off it and home
        if contact > 1e-6:
            hands_on(p, c, r, GRIP_UNDER, contact, 1.0)
        else:
            follow = spline(t, [(rel, 1.0), (rel + 4, 0.8), (n - 6, 0.0), (n, 0.0)])
            if follow > 1e-6:
                W = world(p)
                at = crate_hands(c if t <= rel + 2 else crate_at(rel, world(pose_at(rel)[0]), turn)[0], r, GRIP_UNDER)
                for sd, h, pl in (('R', at[0], (-POLE_UP[0], POLE_UP[1], POLE_UP[2])), ('L', at[1], POLE_UP)):
                    set_arm(p, sd, arm(reach=h, pole=pl, weight=follow), W, None)
        return p
    return f


state('HeavyThrowF', 40)(lambda: sample(40, heavy_throw(40, 18, 'F')))
state('HeavyThrowB', 40)(lambda: sample(40, heavy_throw(40, 18, 'B')))
state('HeavyThrowHi', 30)(lambda: sample(30, heavy_throw(30, 14, 'Hi')))
state('HeavyThrowLw', 30)(lambda: sample(30, heavy_throw(30, 11, 'Lw')))


# ---------------------------------------------------------------------------------------------------------------- swings
def forearm_dir(p, side='R'):
    W = world(p)
    return tuple(W[f'{side}ArmJ'][0][:3])


def swing(n, body_k, wrist_k, blade_k, lwrist_k, feet_fn=None, start=None, grip_k=None):
    """A swing with a bat or sword (their hitboxes ride the item: the blade's arc is the hit): body parameters, the
    wrists' paths and the blade's direction, all keyed in the chest's frame; the fist stays in line with the forearm and
    turns the blade. start: another action's pose to come out of over the first frames (the dash swing)."""
    def f(t):
        kw = {k: spline(t, v) for k, v in body_k.items()}
        root = (0, 0, kw.pop('rz', 0.0))
        waist = (0, kw.pop('wy', 0.0), 0)
        hip = (0, kw.pop('hy', 0.0), 0)
        head = (kw.pop('hp', 0.0), kw.pop('hdy', 0.0), 0)
        p = body(root=root, waist=waist, hip=hip, head=head, feet=feet_fn(t) if feet_fn else None, **kw)
        W = world(p)
        act = spline(t, [(0, 0), (2, 1), (n - 6, 1), (n, 0)])
        set_arm(p, 'R', arm(reach=cpath(t, wrist_k, W), pole=(-0.7, -0.6, -0.3), weight=act), W, None)
        set_arm(p, 'L', arm(reach=cpath(t, lwrist_k, W), pole=(0.8, -0.5, -0.2), weight=act), W, None)
        g = spline(t, grip_k or [(0, 0), (2, 1), (n - 8, 1), (n, 0)])
        grip(p, 'R', blade=cdir(t, blade_k, W), knuckles=forearm_dir(p), w=g)
        if start is not None and t < 3:
            return start() if t == 0 else mix(start(), p, smooth(t / 3.0))
        return p
    return f


# Swing1 (24; the blade hits on frames 5-6): an overhead chop
state('Swing1', 24)(lambda: sample(24, swing(24,
    dict(crouch=[(0, 0), (3, 0.05), (5, 0.3), (8, 0.35, 'hold'), (14, 0.25), (24, 0)],
         lean=[(0, 0), (3, -0.08), (5, 0.25), (8, 0.3, 'hold'), (14, 0.2), (24, 0)],
         rz=[(0, 0), (3, -0.2), (5, 0.35), (8, 0.4, 'hold'), (14, 0.3), (24, 0)],
         wy=[(0, 0), (3, -0.25), (5, 0.15), (8, 0.2, 'hold'), (24, 0)],
         hp=[(0, 0), (3, -0.1), (6, 0.15), (14, 0.1), (24, 0)]),
    [(0, RW), (2, (-1.4, 4.1, -0.5)), (3, (-1.3, 4.5, 0.0), 'hold'), (5, (-0.8, 2.6, 3.0)), (6, (-0.5, 1.3, 3.2)),
     (8, (-0.4, 0.5, 2.8), 'hold'), (14, (-0.6, 0.6, 2.4)), (24, RW)],
    [(0, (0, 0.5, 0.5)), (2, (0, 0.5, -0.9)), (3, (0, 0.8, -0.6)), (5, (0, 0.3, 1)), (6, (0, -0.2, 1)),
     (8, (0, -0.6, 0.8), 'hold'), (14, (0, -0.3, 1.0)), (24, (0, 0.5, 0.5))],
    [(0, LW), (3, (1.5, 2.6, 2.0), 'hold'), (6, (2.0, 0.9, -0.8)), (9, (2.0, 0.8, -0.7), 'hold'), (24, LW)])))

# Swing3 (42; hits 8-10): a flat forehand, right to left across his front, held through
state('Swing3', 42)(lambda: sample(42, swing(42,
    dict(crouch=[(0, 0), (6, 0.15, 'hold'), (9, 0.35), (12, 0.4, 'hold'), (24, 0.35), (34, 0.1), (42, 0)],
         lean=[(0, 0), (6, -0.05, 'hold'), (9, 0.15), (12, 0.2, 'hold'), (24, 0.15), (42, 0)],
         rz=[(0, 0), (6, -0.3, 'hold'), (9, 0.45), (12, 0.5, 'hold'), (24, 0.4), (42, 0)],
         wy=[(0, 0), (6, -0.55, 'hold'), (8, -0.2), (10, 0.45), (12, 0.55, 'hold'), (24, 0.45), (34, 0.1), (42, 0)],
         hy=[(0, 0), (6, -0.2, 'hold'), (10, 0.25), (24, 0.2), (42, 0)],
         hdy=[(0, 0), (6, 0.35, 'hold'), (10, -0.2), (24, -0.15), (42, 0)]),
    [(0, RW), (3, (-2.2, 2.4, -1.0)), (6, (-2.5, 2.7, -1.7), 'hold'), (8, (-1.8, 2.6, 2.3)), (9, (-0.2, 2.5, 3.1)),
     (10, (1.3, 2.4, 2.4)), (12, (1.9, 2.2, 1.5), 'hold'), (24, (1.7, 2.0, 1.3)), (32, (0.0, 1.0, 1.5)), (42, RW)],
    [(0, (0, 0.5, 0.5)), (3, (0, 0.6, -0.8)), (6, (-0.2, 0.3, -1.0), 'hold'), (8, (-1.0, 0.05, 0.5)), (9, (0, 0, 1)),
     (10, (0.9, 0, 0.6)), (12, (0.7, 0.05, 0.5), 'hold'), (24, (0.7, 0.0, 0.5)), (32, (0.1, 0.3, 1.0)), (42, (0, 0.5, 0.5))],
    [(0, LW), (6, (1.2, 2.0, 2.4), 'hold'), (10, (2.0, 1.2, -1.2)), (12, (2.1, 1.2, -1.2), 'hold'), (24, (2.0, 1.0, -0.9)), (42, LW)])))


def swing4_feet(t):
    """The step in: the lead foot slides forward into the smash and back after it."""
    L0 = stance('L')
    L1 = (L0[0], L0[1], L0[2] + 1.8)
    if t <= 19:
        return {'L': step_foot('L', t, 14, 18, L0, L1, height=0.4)}
    return {'L': step_foot('L', t, 40, 48, L1, L0, height=0.35)}


# Swing4 (60; the charge holds on 13, hits 18-23): a big overhead diagonal smash with a step in
state('Swing4', 60)(lambda: sample(60, swing(60,
    dict(crouch=[(0, 0), (12, 0.25, 'hold'), (13, 0.27), (16, 0.2), (18, 0.55), (23, 0.6, 'hold'), (36, 0.5), (46, 0.2), (60, 0)],
         lean=[(0, 0), (12, -0.15, 'hold'), (13, -0.16), (16, -0.05), (18, 0.4), (23, 0.5, 'hold'), (36, 0.4), (46, 0.1), (60, 0)],
         rz=[(0, 0), (12, -0.45, 'hold'), (13, -0.47), (16, -0.1), (18, 0.9), (23, 1.0, 'hold'), (36, 0.9), (46, 0.2), (60, 0)],
         wy=[(0, 0), (12, -0.6, 'hold'), (13, -0.62), (16, -0.35), (18, 0.25), (21, 0.45), (23, 0.5, 'hold'), (36, 0.4), (60, 0)],
         hy=[(0, 0), (12, -0.25, 'hold'), (18, 0.15), (36, 0.1), (60, 0)],
         hp=[(0, 0), (12, -0.15), (17, 0.0), (19, 0.2), (36, 0.15), (60, 0)],
         hdy=[(0, 0), (12, 0.4, 'hold'), (18, -0.1), (36, -0.05), (60, 0)]),
    [(0, RW), (6, (-1.9, 3.2, -1.4)), (12, (-1.6, 4.6, -1.9), 'hold'), (13, (-1.6, 4.7, -2.0)), (15, (-1.7, 4.9, -1.1)),
     (17, (-1.4, 4.3, 1.9)), (18, (-0.8, 2.6, 3.6)), (19, (0.2, 1.3, 3.4)), (21, (1.2, 0.5, 2.6)), (23, (1.6, 0.3, 2.0), 'hold'),
     (36, (1.4, 0.4, 1.8)), (46, (-0.4, 0.8, 1.2)), (60, RW)],
    [(0, (0, 0.5, 0.5)), (6, (0, 0.4, -1)), (12, (0.1, -0.2, -1), 'hold'), (13, (0.1, -0.22, -1)), (15, (0, 0.9, -0.4)),
     (17, (0, 0.7, 0.7)), (18, (0, 0, 1)), (19, (0.2, -0.5, 0.8)), (21, (0.4, -0.75, 0.5)), (23, (0.35, -0.8, 0.5), 'hold'),
     (36, (0.35, -0.75, 0.55)), (46, (0.1, 0.3, 1.0)), (60, (0, 0.5, 0.5))],
    [(0, LW), (12, (1.4, 2.6, 2.2), 'hold'), (18, (2.0, 1.4, -0.6)), (23, (2.2, 1.2, -1.4), 'hold'), (36, (2.1, 1.1, -1.1)),
     (60, LW)], feet_fn=swing4_feet)))


def lunge_feet(t):
    """The dash swing's lunge: the lead foot forward, the rear leg reaching back (the whole stance slides on the dash's
    momentum), gathered back under him to stand."""
    L0, R0 = stance('L'), stance('R')
    L1, R1 = (L0[0], L0[1], 3.6), (R0[0], R0[1], -3.4)
    if t <= 6:
        u = smooth(t / 3.0)
        return {'L': dict(pos=lerp(L0, L1, u)), 'R': dict(pos=lerp(R0, R1, u))}
    return {'R': step_foot('R', t, 30, 38, R1, (R0[0], R0[1], -0.2), height=0.5),
            'L': dict(pos=lerp(L1, L0, smooth((t - 36) / 8.0)))} if t < 44 else \
           {'R': dict(pos=lerp((R0[0], R0[1], -0.2), R0, smooth((t - 44) / 2.0)))}


# SwingDash (46; hits 3-7): out of the run into a long lunge, the blade thrust out level, sliding on
state('SwingDash', 46)(lambda: sample(46, swing(46,
    dict(crouch=[(0, 0.3), (3, 1.0), (6, 1.05, 'hold'), (28, 1.0), (36, 0.6), (42, 0.2), (46, 0)],
         lean=[(0, 0.4), (3, 0.55), (6, 0.6, 'hold'), (28, 0.55), (38, 0.2), (46, 0)],
         rz=[(0, 0), (3, 0.4), (28, 0.35), (38, 0.1), (46, 0)],
         wy=[(0, 0), (2, -0.3), (4, 0.35), (6, 0.4, 'hold'), (28, 0.35), (40, 0.05), (46, 0)],
         hp=[(0, 0), (3, -0.35), (28, -0.3), (40, -0.05), (46, 0)]),
    [(0, (-1.8, 1.6, -0.6)), (2, (-2.0, 2.2, -0.2)), (3, (-1.2, 2.6, 2.8)), (5, (-0.7, 2.7, 3.7), 'hold'), (28, (-0.8, 2.5, 3.5)),
     (38, (-1.2, 1.2, 1.6)), (46, RW)],
    [(0, (0, 0.6, 0.6)), (2, (-0.3, 0.3, -0.9)), (3, (-0.4, 0.1, 0.9)), (5, (0, 0.05, 1), 'hold'), (28, (0, 0.05, 1)),
     (38, (0, 0.1, 1.0)), (46, (0, 0.5, 0.5))],
    [(0, (1.8, 1.4, 1.2)), (3, (2.0, 1.2, -1.6)), (6, (2.1, 1.4, -2.0), 'hold'), (28, (2.0, 1.3, -1.8)), (46, LW)],
    feet_fn=lunge_feet, start=run_pose, grip_k=[(0, 0.5), (2, 1), (38, 1), (46, 0)])))


# ---------------------------------------------------------------------------------------------------------------- guns
AIM = dict(crouch=[(0, 0), (4, 0.2, 'hold'), (7, 0.2), (9, 0.24), (14, 0.2, 'hold'), (22, 0.1), (30, 0)],
           rz=[(0, 0), (4, 0.3, 'hold'), (7, 0.3), (9, 0.05), (14, 0.28, 'hold'), (22, 0.1), (30, 0)],
           lean=[(0, 0), (4, 0.05, 'hold'), (7, 0.05), (9, -0.06), (14, 0.04, 'hold'), (30, 0)],
           wy=[(0, 0), (4, 0.4, 'hold'), (7, 0.4), (9, 0.3), (14, 0.4, 'hold'), (22, 0.15), (30, 0)],
           hdy=[(0, 0), (4, -0.32, 'hold'), (14, -0.32), (22, -0.1), (30, 0)],
           hp=[(0, 0), (4, 0.05), (7, 0.05), (9, -0.07), (14, 0.05), (30, 0)])
AIM_WRIST = [(0, RW), (3, (-1.6, 2.9, 2.6)), (5, (-1.4, 3.0, 3.4), 'hold'), (7, (-1.4, 3.0, 3.4)), (8, (-1.4, 3.35, 3.0)),
             (10, (-1.45, 3.45, 2.9)), (14, (-1.4, 3.0, 3.3), 'hold'), (22, (-1.8, 1.6, 1.6)), (30, RW)]
# the kick: 17-19 degrees (pass 5's 45-55 threw the gun up past his cap; the cast's is small)
AIM_BARREL = [(0, (0, -0.5, 1)), (3, (0, 0, 1)), (5, (0, 0, 1), 'hold'), (7, (0, 0, 1)), (8, (0, 0.3, 1)), (10, (0, 0.34, 1)),
              (14, (0, 0.02, 1), 'hold'), (22, (0, -0.5, 1)), (30, (0, -0.5, 1))]
AIM_LWRIST = [(0, LW), (4, (1.9, 1.2, -1.0), 'hold'), (8, (2.0, 1.5, -1.2)), (14, (1.9, 1.2, -1.0), 'hold'), (30, LW)]


def shoot_pose(t, air=False):
    """ItemShoot (30; the shot on frame 7; the template squints his eyes as he aims): the gun arm comes up level, the chest
    turns side on behind it, the shot kicks the arm and his head up and back, he levels again, and lowers it. In the air
    (ItemShootAir) the same arms on Fall's pose."""
    kw = {k: spline(t, v) for k, v in AIM.items()}
    act = spline(t, [(0, 0), (2, 1), (24, 1), (30, 0)])
    g = spline(t, [(0, 0), (3, 1), (22, 1), (30, 0)])
    if air:
        def arms(p, W):
            air_arm(p, W, 'R', cpath(t, AIM_WRIST, W), (-0.8, -0.6, -0.2), act)
            air_arm(p, W, 'L', cpath(t, AIM_LWRIST, W), (0.8, -0.5, 0.2), act)
        src = fall_pose()
        if t in (0, 30): return src
        p = aerial(src, arms, lean=0.5 * kw['lean'], waist=(0, kw['wy'], 0), head=(kw['hp'], kw['hdy'], 0))
    else:
        p = body(crouch=kw['crouch'], lean=kw['lean'], root=(0, 0, kw['rz']), waist=(0, kw['wy'], 0), head=(kw['hp'], kw['hdy'], 0))
        W = world(p)
        set_arm(p, 'R', arm(reach=cpath(t, AIM_WRIST, W), pole=(-0.8, -0.6, -0.2), weight=act), W, None)
        set_arm(p, 'L', arm(reach=cpath(t, AIM_LWRIST, W), pole=(0.8, -0.5, 0.2), weight=act), W, None)
    b = norm(spline(t, AIM_BARREL))
    return grip(p, 'R', barrel=b, top=cross(b, (1, 0, 0)) if abs(b[0]) < 0.9 else (0, 1, 0), w=g)


state('ItemShoot', 30)(lambda: sample(30, shoot_pose))
state('ItemShootAir', 30)(lambda: sample(30, lambda t: shoot_pose(t, air=True)))


# ---------------------------------------------------------------------------------------------------------------- the Super Scope
SCOPE = dict(crouch=0.25, rz=0.25, lean=0.08, wy=0.35, hdy=-0.3, hp=0.02)
SCOPE_R = (-1.5, 3.2, 0.9)            # the grip at his right shoulder, the barrel (the item's +Y) level ahead
SCOPE_L = (0.1, 2.7, 2.9)             # the left hand under the barrel


def scope_pose(t, k, air=False, recoil=0.0):
    """The Super Scope on his shoulder, blended by k (0 at rest, 1 aiming) with recoil 0..1 (the barrel kicks up, his
    body rocks back)."""
    s = SCOPE
    kw = dict(crouch=s['crouch'] * k, lean=s['lean'] * k - 0.12 * recoil, rz=s['rz'] * k - 0.3 * recoil, wy=s['wy'] * k,
              hdy=s['hdy'] * k, hp=s['hp'] * k - 0.1 * recoil)
    rw = lerp(RW, _add(SCOPE_R, (0, 0.2 * recoil, -0.35 * recoil)), smooth(k))
    lw = lerp(LW, _add(SCOPE_L, (0, 0.3 * recoil, -0.3 * recoil)), smooth(k))
    if k < 0.5:                        # hoisting: the hands swing out and up rather than through his chest
        bulge = math.sin(PI * k * 2) * 0.9 if k > 0 else 0.0
        rw = _add(rw, (-0.6 * bulge, 0, 0.3 * bulge))
        lw = _add(lw, (0.5 * bulge, 0, 0.6 * bulge))
    barrel = norm((0, 0.2 * recoil - 0.02, 1))       # a kick of 10 degrees a rapid shot, 24 the charged one (pass 5: 41
                                                     # and 63 read as the scope flung up)
    act = smooth(clamp(k * 3))
    if air:
        def arms(p, W):
            air_arm(p, W, 'R', xf(rw, W['WaistN']), (-0.7, -0.8, -0.2), act)
            air_arm(p, W, 'L', xf(lw, W['WaistN']), (0.6, -0.8, 0.2), act)
        p = aerial(fall_pose(), arms, lean=0.5 * kw['lean'], waist=(0, kw['wy'], 0), head=(kw['hp'], kw['hdy'], 0))
    else:
        p = body(crouch=kw['crouch'], lean=kw['lean'], root=(0, 0, kw['rz']), waist=(0, kw['wy'], 0),
                 head=(kw['hp'], kw['hdy'], 0))
        W = world(p)
        set_arm(p, 'R', arm(reach=xf(rw, W['WaistN']), pole=(-0.7, -0.8, -0.2), weight=act), W, None)
        set_arm(p, 'L', arm(reach=xf(lw, W['WaistN']), pole=(0.6, -0.8, 0.2), weight=act), W, None)
    return grip(p, 'R', blade=barrel, knuckles=(0, -1, 0.2), w=smooth(clamp(k * 1.5)))   # the cast's: the grip's Z down


def scope_state(name, n, air, k_keys, r_keys, rest_ends=()):
    def f(t):
        if air and ((t == 0 and 0 in rest_ends) or (t == n and n in rest_ends)):
            return fall_pose()
        return scope_pose(t, spline(t, k_keys), air, spline(t, r_keys))
    state(name, n)(lambda: sample(n, f))


for _air, _pre in ((False, 'ItemScope'), (True, 'ItemScopeAir')):
    # Start (15): hoisted onto his shoulder; Rapid (7, a loop; a shot on frame 2): a small kick; Fire (29; the charged shot
    # on frame 2): a big kick, back to aim, lowered (the engine goes to Wait or Fall after it); End (19): lowered
    scope_state(_pre + 'Start', 15, _air, [(0, 0), (10, 1.0), (15, 1.0)], [(0, 0), (15, 0)], rest_ends=(0,))
    scope_state(_pre + 'Rapid', 7, _air, [(0, 1), (7, 1)], [(0, 0), (2, 0), (3, 1.0), (4, 0.7), (7, 0)])
    scope_state(_pre + 'Fire', 29, _air, [(0, 1), (16, 1, 'hold'), (29, 0)],
                [(0, 0), (2, 0), (3, 2.2), (6, 1.4), (12, 0.2), (16, 0), (29, 0)], rest_ends=(29,))
    scope_state(_pre + 'End', 19, _air, [(0, 1), (4, 0.95), (19, 0)], [(0, 0), (19, 0)], rest_ends=(19,))


# ---------------------------------------------------------------------------------------------------------------- the hammer
HAMMER = 16
S_HIP = anims.STANCE['hip_yaw']          # the stance's hip turn (undone to square up)


def hammer_pose(t, move):
    """The hammer (16, a loop; the engine carries the frame between standing and walking, so both share the swing): both
    hands on the handle, it goes up behind his head and smashes down in front, over and over, the body folding into each
    blow. Standing (ItemHammerWait) the feet stay planted and the knees give with it; walking (ItemHammerMove) he runs
    with it, two steps a swing, the stride sized to his walk speed (1.0 a frame) so the planted foot holds still."""
    ph = TAU * t / HAMMER
    ph2 = ph + 0.45 * math.sin(ph)                      # fast down, slower up
    th = math.radians(30 - 78 * math.cos(ph2))         # the handle's angle from straight up, forward positive
    blade = (0, math.cos(th), math.sin(th))
    fold = 0.5 - 0.5 * math.cos(ph2)                    # 0 overhead, 1 at the smash
    feet = None
    bob = 0.0
    if move:
        feet = {}
        for s, off in (('L', 0.0), ('R', 0.5)):
            u = (t / HAMMER + off) % 1.0                # 0..0.5 planted (moving back), 0.5..1 swinging forward
            x = FEET[s][0] * 0.7
            if u < 0.5:
                z = 4.0 - 16.0 * u
                feet[s] = dict(pos=(x, rig.ANKLE_Y, z), yaw=0.0)
            else:
                v = (u - 0.5) * 2
                z = -4.0 + 8.0 * smooth(v)
                feet[s] = dict(pos=(x, rig.ANKLE_Y + 1.1 * math.sin(PI * v), z), yaw=0.0, pitch=0.5 * math.sin(PI * v))
        bob = -0.25 * (0.5 - 0.5 * math.cos(2 * TAU * t / HAMMER))
    p = body(crouch=0.25 + 0.3 * fold, bob=bob, lean=0.1 + 0.45 * fold, root=(0, 0, 0.35 * fold - 0.1),
             hip=(0.1 * fold, -S_HIP + (0.12 * math.sin(ph) if move else 0.0), 0), waist=(0, -0.1, 0),   # square
             head=(-0.25 + 0.25 * fold, 0.2, 0), feet=feet, stance_turn=True)
    W = world(p)
    c = (-0.4, 2.8, 0.7)
    wr = _add(c, (0, 2.5 * math.cos(th), 2.5 * math.sin(th)))
    ch = W['WaistN']
    rwrist = xf(wr, ch)
    bw = norm(vec_mat(blade, ch))
    lwrist = tuple(a + 0.75 * b + d for a, b, d in zip(rwrist, bw, vec_mat((0.55, 0, 0), ch)))
    set_arm(p, 'R', arm(reach=rwrist, pole=(-0.8, -0.3, -0.5)), W, None)
    set_arm(p, 'L', arm(reach=lwrist, pole=(0.8, -0.3, -0.5)), W, None)
    grip(p, 'R', blade=bw, knuckles=(1, 0, 0))
    grip(p, 'L', blade=bw, knuckles=(-1, 0, 0))
    return p


def hammer_script():
    """Every hammer state plays ItemHammerWait or ItemHammerMove, switching as he stops and moves. The template's Wait
    squinted and sent model part 2 to pose 2 over 10 frames, which is Geno's cap pulled low (rig.CAP_POSE): kept, as the
    frenzy's menace, but on both and snapped, since part poses reset on every action change and a blend would bob the cap
    at each switch. The left hand grips the handle below the right (the right's grip is the item's, ftGe_Init_OnItemPickup)."""
    from fcmd import Script
    s = Script()
    s.raw(tex(3)); s.cap('low', 0); s.hand('L', 'grip', 0)
    return s


state('ItemHammerWait', HAMMER, hammer_script)(lambda: sample(HAMMER, lambda t: hammer_pose(t % HAMMER, False) if t < HAMMER else hammer_pose(0, False)))
state('ItemHammerMove', HAMMER, hammer_script)(lambda: sample(HAMMER, lambda t: hammer_pose(t % HAMMER, True) if t < HAMMER else hammer_pose(0, True)))


# ---------------------------------------------------------------------------------------------------------------- the parasol
PARASOL_R = (-3.0, 5.5, 0.4)           # the fist beside his (big: 5.1 across) head, the shaft (the item's +Y) straight up


def parasol_pose(t, k, sway=0.0, bounce=0.0):
    """Hanging from the open parasol, blended in by k: the right arm straight up by his head, the body hanging below it
    turned a little toward the camera, legs together and toes down; sway swings him like a pendulum."""
    src = fall_pose()
    legs = {s: ((sx * 0.08, -1, 0.12 + 0.2 * sway), (0, -1, 0.05 + 0.3 * sway)) for s, sx in (('L', 1), ('R', -1))}

    def arms(p, W):
        rw = xf(_add(PARASOL_R, (0.0, -0.4 * bounce, 0.0)), W['WaistN'])
        air_arm(p, W, 'R', rw, (-0.8, 0.0, -0.5), smooth(k))
        air_arm(p, W, 'L', xf(_add(LW, (0.3, -0.2, -0.2)), W['WaistN']), (0.8, -0.3, 0.3), 0.6 * smooth(k))
    p = aerial(src, arms, turn=-0.3 * k, lean=-0.05 * k, roll=0.04 * sway, drop=-0.3 * bounce,
               head=(-0.12 * k + 0.05 * bounce, -0.1 * k, 0), legs=legs if k > 1e-3 else None)
    if k < 1 and k > 1e-3:
        p = mix(src, p, smooth(k))
        return grip(as_pose(p), 'R', blade=(0, 1, 0), knuckles=(0.3, 0, 1), w=smooth(k))
    return grip(p, 'R', blade=(0, 1, 0), knuckles=(0.3, 0, 1), w=smooth(k)) if k > 1e-3 else p


@state('ItemParasolOpen', 16)
def parasol_open():
    """ItemParasolOpen (16; the template opens it on frame 4): out of the jump or fall the arm thrusts the parasol up, it
    catches the air (he drops into the arm and bounces), and he settles hanging from it."""
    return sample(16, lambda t: parasol_pose(t, spline(t, [(0, 0), (5, 1.0), (16, 1.0)]),
                                           bounce=spline(t, [(0, 0), (5, 0), (8, 1.0), (11, -0.3), (14, 0.1), (16, 0)])))


@state('ItemParasolFall', 76)
def parasol_fall():
    """ItemParasolFall (76, a loop): drifting under it, swinging gently once a loop."""
    from states_misc import wave
    return sample(76, lambda t: parasol_pose(t, 1.0, sway=wave(t, 76, 1)), step=2)


# ---------------------------------------------------------------------------------------------------------------- the Screw Attack
def tucked():
    """A tight ball: knees pulled up to the chest, shins folded under, arms hugging the shins, chin down."""
    p = anims.tuck(1.25, arms=0.2)
    for s, sx in (('L', 1), ('R', -1)):
        p.aim(f'{s}LegJ', (sx * 0.15, 0.55, 0.85)); p.aim(f'{s}KneeJ', (0, -0.95, 0.1))
        p.aim(f'{s}FootJ', (0, -0.3, 1), up=(0, -1, 0))
        p.aim(f'{s}ShoulderJ', (sx * 0.35, -0.55, 0.8)); p.aim(f'{s}ArmJ', (sx * 0.1, -0.9, -0.15))
    p.rot('WaistN', (0.8, 0, 0)).rot('HeadN', (0.45, 0, 0))
    return p


def flipped(src, th, centre_y=7.6):
    """src turned th radians forward about his left-right axis, about the middle of his body."""
    p = aerial(src, lean=th)
    W = world(p)
    c = [0.5 * (a + b) for a, b in zip(pos(W, 'WaistN'), pos(W, 'HipN'))]
    y0 = p.trans['YRotN']
    p.move('YRotN', (y0[0] - c[0], y0[1] + centre_y - c[1], y0[2] - c[2]))
    return p


def screw_keys(first):
    """ItemScrew / ItemScrewAir (40; the jump or the double jump while wearing it): he tucks into a ball and somersaults
    forward twice, the item's hitboxes spinning round him, and opens out into the fall."""
    def f(t):
        tk = spline(t, [(0, 0), (5, 1, 'hold'), (30, 1, 'hold'), (38, 0), (40, 0)])
        th = TAU * 2 * smooth(spline(t, [(0, 0), (4, 0.02), (33, 1.0), (40, 1.0)]))
        src = first() if t < 20 else fall_pose()
        tp = tucked()
        if tk >= 1 - 1e-6:
            return flipped(tp, th)
        base_p = flipped(src, th)
        return mix(base_p, flipped(tp, th), smooth(tk)) if tk > 1e-6 else (src if t in (0,) else fall_pose() if t == 40 else base_p)
    return f


state('ItemScrew', 40)(lambda: sample(40, screw_keys(lambda: other_pose('JumpF', 55))))
state('ItemScrewAir', 40)(lambda: sample(40, screw_keys(lambda: other_pose('JumpAerialF', 60))))


def splayed():
    p = anims.tuck(0.25, arms=0.0)
    for s, sx in (('L', 1), ('R', -1)):
        p.aim(f'{s}ShoulderJ', (sx * 1.0, 0.25, -0.2)); p.aim(f'{s}ArmJ', (sx * 0.9, 0.5, -0.3))
        p.aim(f'{s}LegJ', (sx * 0.45, -1, -0.25)); p.aim(f'{s}KneeJ', (sx * 0.2, -1, -0.5))
    p.rot('HeadN', (-0.3, 0, 0))
    return p


@state('ItemScrewDamage', 40)
def screw_damage():
    """Hit by someone's Screw Attack (DamageScrew, 40): flung spinning backward twice, limbs thrown out like a dropped doll,
    and into the tumble (DamageFall's first pose)."""
    def f(t):
        th = -TAU * 2 * spline(t, [(0, 0), (4, 0.15), (30, 0.95), (36, 1.0), (40, 1.0)])
        end = other_pose('DamageFall', 29)
        p = flipped(splayed(), th)
        u = smooth((t - 30) / 10.0)
        return mix(p, end, u) if u > 0 else p
    return sample(40, f)


# ---------------------------------------------------------------------------------------------------------------- the rest
@state('ItemBlind', 240)
def item_blind():
    """ItemBlind (240, looped; flags 0x40000000). No state in the game plays it: none of the 341 common motion states
    names the animation, and no fighter's idle lists (ftData+0x24, +0x28; `datkit chances`) do; it is played in a lab by
    the director's anim cue (items_lab 'blind'). The cast's is a blinded grope: crouched, the arms out in front feeling for
    something, the head turning (Fox's, Mario's). Geno's, a dazzled doll: knees soft and bobbing, the head ducked and
    turning, the right forearm raised across his brow against the light and the left arm stretched out groping,
    open-handed, sweeping side to side; halfway through the right hand gives up shading and gropes out too, both arms
    feeling ahead as the cast's do (his right shoulder sits back in his stance, so it reaches across in front of him).
    From Wait1's first frame and back to it."""
    n = 240
    op = rig.HAND_POSES[1]                                   # open, left-hand form
    rel = rig.RELAXED_HAND

    def fingers(p, side, w):
        for j, r in op.items():
            r0 = rel.get(j, r)
            if side == 'R': j, r, r0 = 'R' + j[1:], (-r[0], -r[1], r[2]), (-r0[0], -r0[1], r0[2])
            p.rot(j, tuple(a + (b - a) * w for a, b in zip(r0, r)))

    def f(t):
        env = smooth(clamp(t / 16.0)) * smooth(clamp((n - t) / 16.0))
        swap = smooth(clamp((t - 112) / 24.0))                # 0: the right shades; 1: it gropes too
        bob = math.sin(TAU * t / 40)
        look = math.sin(TAU * t / 60)
        p = body(crouch=(0.28 + 0.06 * bob) * env, lean=0.08 * env, bob=0.05 * bob * env,
                 waist=(0.04 * env, (0.18 - 0.3 * swap) * env + 0.06 * look * env, 0.03 * bob * env),
                 head=(0.22 * env, 0.32 * look * env, 0.07 * math.sin(TAU * t / 24) * env))
        W = world(p)
        for side, sx in (('L', 1), ('R', -1)):
            grope = 1.0 if side == 'L' else swap              # this arm's share of groping (the rest is shading)
            sweep = math.sin(TAU * (t + (0 if side == 'L' else 24)) / 48)
            if side == 'L':
                reach_g = (0.9 + 0.9 * sweep, 7.4 + 0.3 * math.sin(TAU * t / 32), 4.7 + 0.2 * math.cos(TAU * t / 48))
            else:
                reach_g = (-0.5 + 0.6 * sweep, 7.9 + 0.3 * math.sin(TAU * t / 28), 3.6 + 0.2 * math.cos(TAU * t / 48))
            reach_s = xf((sx * 1.35, 1.25, 2.25), W['HeadN'])   # the wrist beside his face, the hand across the brow
            tgt = tuple(g * grope + h * (1 - grope) for g, h in zip(reach_g, reach_s))
            pole = tuple(g * grope + h * (1 - grope) for g, h in zip((sx * 0.6, -0.8, 0.0), (sx * 0.9, -0.5, 0.2)))
            set_arm(p, side, arm(reach=tgt, pole=pole, weight=env), W, None)
            fingers(p, side, env)
        W = world(p)
        for side, sx in (('L', 1), ('R', -1)):
            shade = 0.0 if side == 'L' else 1 - swap
            if shade * env > 1e-3:                            # the shading hand turns across the brow, its back to the light
                hand_blend(p, side, (-sx * 0.55, 0.65, 0.35), (0.0, 0.25, 1.0), shade * env)
        return p
    return sample(n, f, step=2)


@state('SquatWaitItem', 130)
def squat_wait_item():
    """Crouching with an item (130): SquatWait's own motion, whoever authors it, with the item hand lifted off the floor
    and out to his side (the cast's does the same). The engine swaps SquatWait for this on SquatWait's first frame with no
    blend (ftData+0x10's entry for it is 0), so the lift eases in over the first 10 frames from Squat's last pose and out
    over the last 10 back to it: the loop seam is exact, and once a cycle the hand settles and lifts the item again."""
    n, keys = squat_keys()
    out = []
    for f, p in keys:
        g = f * 130.0 / n
        env = smooth(clamp(g / 10.0)) * smooth(clamp((130.0 - g) / 10.0))
        q = as_pose(p)
        if env > 1e-6:
            W = world(q)
            w0 = pos(W, 'RHandN')
            set_arm(q, 'R', arm(reach=(w0[0] - 0.7, max(w0[1], 1.2) + 1.0, w0[2] - 0.3), pole=(-0.9, -0.2, -0.3)), W, None)
            q = mix(as_pose(p), q, env) if env < 1 - 1e-6 else q
        else:
            q = p
        out.append((round(g), q))
    return out



import states_air                                   # noqa: E402 its SquatWaitItem (SquatWait as is) is dropped from what
states_air.REG.pop('SquatWaitItem', None)           # its register() adds, so the one above (the item hand lifted) is built
