"""Geno's defensive and reactive states, blockout motion (the template's scripts stay: intangibility, sounds, timing):
dodges, the shield's in and out, hit reactions and tumble, the lying idle, the wall and ceiling techs, the ledge jump's
second part, being grabbed, dizzy and sleep, the trip and the clank.

The cast's conventions these follow (sampled with datkit fk/bodydata, research/body_moves.md):
  - a forward roll turns him round: the script reverses his facing on frame 20 (command 0x14) and the model follows at
    the next action, so the pose ends turned 180 degrees and meets Wait under the new facing;
  - a spot dodge twists the body toward the camera and back; an air dodge turns round with the limbs splayed;
  - hitstun snaps the torso back and flings the arms (high: the head; low: the knees buckle) and eases back to the idle;
  - DamageFlyRoll spins upright about the vertical; DamageFall tumbles end over end; both loop;
  - held by a grab, he hunches into the grabber and pushes (high) or leans away and flails (low).
Each state starts or ends where its neighbour does: first_pose() reads the next state's first key at build time, so the
seams hold if another state's animation changes. Frame counts are the template's.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig
from anims import base, tuck, guard_pose, keys_for
from moves import arm, MOVES
from states import state, lie, curl, rolled

TAU = 2 * math.pi


def first_pose(name, frames=20):
    """The first key pose of another state: its authored keys if it has them, else anims.keys_for's."""
    if name in MOVES:
        return MOVES[name][1](None)[1][0][1]
    return keys_for(name, frames)[0][1]


def _turn(p, R):
    t = lambda v: None if v is None else [sum(v[i] * R[i][j] for i in range(3)) for j in range(3)]
    p.aims = {j: (t(x), t(up)) for j, (x, up) in p.aims.items()}
    return t


def yawed(p, th):
    """The whole pose turned th radians about the vertical (positive: toward his left), limbs and all."""
    R = rig.rot_xyz(0, th, 0)
    t = _turn(p, R)
    y0 = p.trans.get('YRotN', (0, 0, 0))
    r0 = p.local.get('YRotN', (0, 0, 0))
    return p.move('YRotN', tuple(t(y0))).rot('YRotN', (r0[0], r0[1] + th, r0[2]))


MID = 1.0                     # the body's middle sits this far above XRotN (the hips' pivot)


def tipped(p, ax, height=None):
    """The whole pose tipped ax radians about his left-right axis (positive: the top goes forward). With height, it turns
    about the body's middle, held that high (a tumble in the air: head and feet stay above his position)."""
    R = rig.rot_xyz(ax, 0, 0)
    _turn(p, R)
    p.rot('XRotN', (ax, 0, 0))
    if height is not None:
        y = p.trans.get('YRotN', (0, 0, 0))
        p.move('XRotN', (0, height, 0)).move('YRotN', (y[0], y[1] - MID, y[2]))
    return p


def bend(p, joint, dx=0.0, dy=0.0, dz=0.0):
    """Add to a joint's local rotation (keeps what the base pose set: the stance's chest and head yaw)."""
    r = p.local.get(joint, (0, 0, 0))
    return p.rot(joint, (r[0] + dx, r[1] + dy, r[2] + dz))


def arms(p, l, r, lb=0.0, rb=0.0):
    """Both arms at once: arm(p, side, direction, bend)."""
    return arm(arm(p, 'L', l, bend=lb), 'R', r, bend=rb)


def legs(p, l, r, lk=(0, -1, 0.1), rk=(0, -1, 0.1)):
    """Both legs: thigh and shin directions (world), feet flat to the shin (sole along -Y of the shin's frame)."""
    for sd, th, sh in (('L', l, lk), ('R', r, rk)):
        p.aim(f'{sd}LegJ', th); p.aim(f'{sd}KneeJ', sh)
    return p


def shifted(p, dy=0.0, dz=0.0):
    """Move the body (YRotN) by dy up and dz forward in XRotN's frame: the hips driven back, or the whole body dropped
    below his position (the cast's airborne reactions hang low)."""
    y = p.trans.get('YRotN', (0, 0, 0))
    return p.move('YRotN', (y[0], y[1] + dy, y[2] + dz))


def air_start():
    return first_pose('Fall')


# ---------------------------------------------------------------------------------------------------------------- dodges
def gather(c=0.55, lean=0.35):
    """The dip before a roll: knees in, arms drawn to the chest."""
    return arms(base(crouch=c, lean=lean), (0.3, -0.3, 0.6), (-0.3, -0.3, 0.6), 0.6, 0.6)


@state('EscapeF', 32)
def roll_forward():
    """The forward roll: a dip, a curled roll along the floor that turns him round (the script reverses his facing on
    frame 20 and the model follows at Wait), and up facing back the way he came. The template's path: 35 units."""
    k = [(0, base()), (3, gather())]
    k += [(f, curl(0.3 + TAU * (f - 5) / 18, yaw=math.pi * min(1.0, (f - 5) / 16))) for f in range(5, 24)]
    k += [(26, yawed(base(crouch=0.6, lean=0.2), math.pi)), (32, yawed(base(), math.pi))]
    return k


@state('EscapeB', 32)
def roll_back():
    """The backward roll: a dip, a curled roll back along the floor, up facing the same way."""
    k = [(0, base()), (3, gather(0.6, -0.1))]
    k += rolled(5, 23, 32, a0=-0.2, turn=-TAU)
    k += [(26, base(crouch=0.6, lean=0.1)), (32, base())]
    return k


def ducked(tw, c):
    """The spot dodge: knees in, arms wrapped over the chest, the body twisted tw radians (negative: facing right, toward
    the camera)."""
    p = arms(base(crouch=c, lean=0.15), (0.4, 0.1, 0.5), (-0.4, 0.1, 0.5), 0.8, 0.8)
    bend(p, 'HeadN', 0.35)
    return yawed(p, tw)


@state('EscapeN', 23)
def spot_dodge():
    """The spot dodge: the doll ducks and spins toward the camera, holds, and turns back (the cast twists the same way)."""
    return [(0, base()), (2, ducked(-0.9, 0.45)), (4, ducked(-1.9, 0.6)), (8, ducked(-2.3, 0.62)), (14, ducked(-2.2, 0.6)),
            (17, ducked(-1.1, 0.4)), (20, ducked(-0.2, 0.15)), (23, base())]


def splay(open_=1.0):
    """Limbs flung out (a wall splat): arms up and out, legs apart."""
    p = tuck(0.3 * (1 - open_), arms=0.2)
    p = arms(p, (0.9, 0.5 * open_, 0.2), (-0.9, 0.5 * open_, 0.2))
    return legs(p, (0.45 * open_, -1, 0.15), (-0.45 * open_, -1, -0.1 * open_), (0.2 * open_, -1, 0.3), (-0.2 * open_, -1, 0.2))


def spinning(th, open_=1.0):
    """The air dodge's spin: knees drawn up, arms flung wide, leaning into the turn, the body dropped (the cast's air
    dodges fold and hang below their position), turned th about the vertical."""
    p = tuck(0.6 + 0.4 * open_, arms=0.2)
    p = arms(p, (0.9, 0.35 * open_, 0.15), (-0.9, 0.3 * open_, -0.15), 0.2, 0.2)
    bend(p, 'HeadN', 0.3 * open_)
    return tipped(yawed(shifted(p, dy=-2.4 * open_), th), 0.55 * open_)


@state('EscapeAir', 49)
def air_dodge():
    """The air dodge: he folds and spins round once in the air, arms flung out, and opens into the helpless fall
    (FallSpecial) facing forward."""
    end = first_pose('FallSpecial')
    return [(0, air_start()), (3, spinning(1.0, 0.7)), (7, spinning(2.4)), (12, spinning(3.3)), (18, spinning(4.0)),
            (24, spinning(4.8, 0.9)), (30, spinning(5.6, 0.6)), (37, spinning(6.1, 0.3)), (43, yawed(tuck(0.4, arms=0.4), TAU)),
            (49, yawed(end, TAU))]


# ---------------------------------------------------------------------------------------------------------------- shield
# While he shields the engine poses his body from the fighter data's shield pose (anims.guard_pose, fitted by
# shieldfit.py) and ramps into it from GuardOn: these only shape the ramp in and the way out. ThrowN (the bubble's
# centre) stays where guard_pose puts it.
@state('GuardOn', 8)
def guard_on():
    """Into the shield: a quick duck, arms coming up to cross in front."""
    mid = arms(base(crouch=0.2, arms=0.3), (0.35, 0.1, 0.25), (-0.35, 0.1, 0.25), 0.7, 0.7)
    return [(0, base()), (3, mid), (8, guard_pose())]


@state('GuardOff', 15)
def guard_off():
    """Out of the shield: the arms drop, he straightens with a small settle."""
    return [(0, guard_pose()), (4, base(crouch=0.3, arms=0.2)), (9, base(crouch=0.05)), (15, base())]


@state('GuardDamage', 20)
def guard_damage():
    """Shieldstun: the hit rocks him back inside the bubble (torso and head only, so the bubble stays put)."""
    jolt = bend(bend(guard_pose(), 'WaistN', -0.3), 'HeadN', -0.1)
    return [(0, jolt), (4, bend(guard_pose(), 'WaistN', -0.1)), (10, guard_pose()), (20, guard_pose())]


# ---------------------------------------------------------------------------------------------------------------- hit reactions
def struck(where, a, air=False):
    """The instant after a hit, at strength a (0..1). N: the torso snaps back, the knees give, the arms fly up and out,
    the hips are driven back. Hi: the head and shoulders whip back, arms up. Lw: the knees buckle and he folds forward
    over them, hips thrown back. air: the knees draw up and the body hangs lower. (The cast's hitstun drops the body to
    ~0.75-0.85 of its height and drives the hurtboxes ~0.2 of it back: research/body_moves.md.)"""
    st = 0 if air else 1
    if where == 'Hi':
        p = base(crouch=0.45 * a, lean=-1.0 * a, arms=0.3 * a, stance=st)
        bend(p, 'HeadN', -0.7 * a)
        p = arms(p, (0.55, 0.7 * a, 0.3), (-0.55, 0.7 * a, 0.3), 0.3, 0.3)
        dz = -1.2 * a
    elif where == 'Lw':
        p = base(crouch=0.85 * a, lean=0.6 * a, stance=st)
        bend(p, 'HeadN', 0.3 * a)
        p = arms(p, (0.5, -0.3, 0.9), (-0.5, -0.3, 0.9), 0.15, 0.15)
        dz = -3.0 * a
    else:
        p = base(crouch=0.6 * a, lean=-0.8 * a, stance=st)
        bend(p, 'HeadN', -0.4 * a)
        p = arms(p, (0.55, 0.1 + 0.45 * a, 0.35), (-0.55, 0.1 + 0.45 * a, 0.35), 0.35, 0.35)
        dz = -1.3 * a
    shifted(p, dz=dz)
    if air:
        p = legs(p, (0.12, -0.4, 0.9 * a), (-0.12, -0.6, 0.7 * a), (0, -1, 0.2), (0, -1, 0.3))
        p = arms(p, (0.4, 0.3, 1), (-0.4, 0.25, 1), 0.05, 0.05)
        shifted(p, dy=-1.0 * a)
    return p


STRENGTH = {1: 0.7, 2: 0.85, 3: 1.0}
LENGTH = {1: 12, 2: 24, 3: 30}


def hitstun(where, k, air=False):
    """A flinch: struck at once (the pose he holds through hitlag), a beat at the peak, a slow recovery through most of
    the stun, then back to the idle (the air ones to the fall) with a small overshoot."""
    n, a = LENGTH[k], STRENGTH[k]
    end = air_start() if air else base()
    over = base(crouch=0.1, lean=0.08) if not air else tuck(0.35, arms=0.35)
    return [(0, struck(where, a, air)), (max(2, round(n * 0.15)), struck(where, a * 1.05, air)),
            (round(n * 0.55), struck(where, a * 0.7, air)), (round(n * 0.8), struck(where, a * 0.25, air)),
            (round(n * 0.92), over), (n, end)]


for _w in ('Hi', 'N', 'Lw'):
    for _k in (1, 2, 3):
        state(f'Damage{_w}{_k}', LENGTH[_k])(lambda w=_w, k=_k: hitstun(w, k))
for _k in (1, 2, 3):
    state(f'DamageAir{_k}', LENGTH[_k])(lambda k=_k: hitstun('N', k, air=True))


def flail(ph):
    """Limbs thrown about in the tumble, at phase ph of the flail cycle (radians): the torso curled, arms flung out and
    bent, the knees bent and kicking out of step (kept in: the cast's tumbles reach ~0.2 of their height past the
    standing box)."""
    s, c = math.sin(ph), math.cos(ph)
    p = base(lean=0.65, stance=0)
    bend(p, 'HeadN', 0.35 + 0.15 * s)
    p = arms(p, (0.6, 0.3 + 0.3 * s, 0.4 + 0.2 * c), (-0.6, 0.3 - 0.3 * s, 0.4 - 0.2 * c), 0.75, 0.75)
    return legs(p, (0.25, 0.2 + 0.2 * c, 0.9), (-0.25, -0.2 - 0.2 * c, 0.9), (0.05, -1, -0.8 + 0.2 * s),
                (-0.05, -1, -0.6 - 0.2 * s))


FALL_H = 6.3                  # the tumble's middle above his position (the cast's hang ~0.05 of their height below it)
FALL_A0 = -1.2                # the tumble starts tipped back, the way a launch leaves him


@state('DamageFall', 29)
def tumble():
    """Tumble: end over end, backward, limbs flailing, one turn per loop (the cast's DamageFall loops the same way)."""
    return [(f, tipped(flail(TAU * f / 29 * 2), FALL_A0 - TAU * f / 29, FALL_H)) for f in range(0, 30, 2)] + \
           [(29, tipped(flail(TAU * 2), FALL_A0 - TAU, FALL_H))]


def launched(where, u, yaw=0.0):
    """Sent flying: N folds back with the limbs trailing forward, Hi tips back with them trailing down, Lw lies out low
    with them trailing back; u 0..1 how far into the fold. Knees bent and the body compact (the cast's launches are
    folded, their tops ~0.65-0.7 of their height)."""
    if where == 'Hi':
        p = arms(base(lean=-0.5 * u, stance=0), (0.35, -1, 0.1), (-0.35, -1, 0.1), 0.3, 0.3)
        bend(p, 'HeadN', -0.5 * u)
        p = legs(p, (0.1, -0.8, 0.5), (-0.1, -0.9, 0.3), (0, -1, -0.5), (0, -1, -0.3))
        return tipped(yawed(p, yaw), -0.8 * u, FALL_H - 1.0)
    if where == 'Lw':
        p = arms(base(lean=0.3 * u, stance=0), (0.3, 0.1, -1), (-0.3, 0.1, -1), 0.2, 0.2)
        p = legs(p, (0.1, -0.3, -1), (-0.1, -0.2, -1), (0, -0.6, -1), (0, -0.4, -1))
        return tipped(yawed(p, yaw), 1.1 * u, FALL_H - 1.5)
    p = arms(base(lean=-0.5 * u, stance=0), (0.3, -0.1, 1), (-0.3, 0.0, 1), 0.4, 0.4)
    bend(p, 'HeadN', -0.4 * u)
    p = legs(p, (0.1, -0.2, 1), (-0.1, -0.3, 1), (0, -1, 0.4), (0, -1, 0.3))
    return tipped(yawed(p, yaw), -1.0 * u, FALL_H - 0.8)


def fly(where):
    """DamageFly: struck, folded into the launch, holding it with a flutter while the body keeps turning over, and
    opening into the tumble's first frame (hitstun ends it wherever it is; then DamageFall)."""
    k = [(0, struck(where, 1.0, air=True)), (4, launched(where, 1.0))]
    for f in (10, 16):
        k.append((f, launched(where, 0.92 + 0.08 * (f % 3))))
    k += [(22, tipped(flail(-0.8), FALL_A0 + (0.05 if where == 'N' else 0.5), FALL_H)), (29, tumble()[0][1])]   # N keeps turning back
    return k


for _w in ('Hi', 'N', 'Lw'):
    state(f'DamageFly{_w}', 29)(lambda w=_w: fly(w))


@state('DamageFlyTop', 60)
def fly_top():
    """Sent straight up (and the shield break's launch): folded back, limbs trailing, turning slowly about the vertical for
    two turns, then opening into the tumble."""
    k = [(0, struck('Hi', 1.0, air=True))]
    for f in range(4, 49, 4):
        k.append((f, launched('Hi', 1.0, yaw=TAU * 2 * (f - 4) / 44)))
    k += [(54, tipped(flail(-0.8), FALL_A0 + 0.6, FALL_H)), (60, tumble()[0][1])]
    return k


def pirouette(th):
    """The spinning launch: upright, arms out and down, hanging a little low, turned th."""
    p = arms(base(stance=0, lean=-0.15), (0.5, -0.8, 0.1), (-0.5, -0.8, -0.1), 0.4, 0.4)
    bend(p, 'HeadN', -0.2, 0, 0.2)
    p = legs(p, (0.08, -1, 0.1), (-0.12, -1, -0.25), (0, -1, 0), (0, -1, 0.2))
    return yawed(shifted(p, dy=-1.8), th)


@state('DamageFlyRoll', 16)
def spin():
    """The spinning launch: upright, arms out, one turn about the vertical per loop (the cast's DamageFlyRoll)."""
    return [(f, pirouette(TAU * f / 16)) for f in range(0, 17, 2)]


def crumple(u, drop=1.0):
    """Slammed flat against a wall, then crumpling off it: u 0 flat (limbs spread, head back), 1 folded and dropped;
    drop scales how far the body falls below his position (a hard wall splat drops, a bonk barely)."""
    p = splay(1.0 - 0.6 * u)
    bend(p, 'HeadN', -0.5 * (1 - u) + 0.3 * u)
    p = arms(p, (0.4, 0.3, 1), (-0.4, 0.2, 1), 0.0, 0.0)
    p = legs(p, (0.3, -0.3 + 0.4 * u, 0.9), (-0.3, -0.5 + 0.3 * u, 0.8), (0, -0.6, 0.6), (0, -0.7, 0.5))
    return tipped(shifted(p, dy=(-2.4 - 1.0 * u) * drop), 0.3 + 0.2 * u)


@state('WallDamage', 40)
def wall_splat():
    """Slammed into a wall: squashed flat against it for a beat, crumpling, then peeling off into the tumble."""
    return [(0, crumple(0.0)), (6, crumple(0.2)), (14, crumple(0.7)), (22, tipped(flail(-1.6), FALL_A0 + 0.9, FALL_H)),
            (31, tipped(flail(-0.8), FALL_A0 + 0.4, FALL_H)), (40, tumble()[0][1])]


# ---------------------------------------------------------------------------------------------------------------- the floor and the walls
def breath(face_up, u):
    """Lying, breathing: the chest lifts a touch and the head lolls, u 0..1 through the breath."""
    p = lie(face_up)
    w = math.sin(math.pi * u)
    return bend(bend(p, 'WaistN', (0.06 if face_up else -0.06) * w, 0.03 * w), 'HeadN', 0, 0.12 * w, 0.05 * w)


for _up, _nm in ((True, 'DownWaitU'), (False, 'DownWaitD')):
    state(_nm, 70)(lambda up=_up: [(0, lie(up)), (35, breath(up, 0.5)), (70, lie(up))])


def cling(u=0.0):
    """A wall tech: folded against the wall behind him, hands flat on it, knees drawn up (u: 0 pressed, 1 pushing off);
    low, as the cast's are."""
    p = tuck(1.2 - 0.5 * u, arms=0.2)
    p = arms(p, (0.5, 0.4, -1), (-0.5, 0.5, -1), 0.4 * (1 - u), 0.4 * (1 - u))
    bend(bend(p, 'HeadN', 0.3), 'WaistN', 0.4 * (1 - u))
    return shifted(p, dy=-2.4 * (1 - 0.5 * u))


@state('PassiveWall', 26)
def wall_tech():
    return [(0, cling(0.0)), (10, cling(0.15)), (18, cling(0.6)), (26, air_start())]


@state('PassiveWallJump', 40)
def wall_tech_jump():
    """Kicking off the wall: legs driving back, arms swinging up, then up into the fall."""
    kick = shifted(legs(arms(tuck(0.2, arms=0.2), (0.4, 1, 0.3), (-0.4, 1, 0.3)), (0.1, -0.7, -0.8), (-0.1, -0.8, -0.6)), dy=-1.0)
    return [(0, cling(0.0)), (5, cling(0.4)), (9, kick), (18, shifted(tuck(0.9, arms=0.5), dy=-1.5)), (30, tuck(0.4, arms=0.4)),
            (40, air_start())]


@state('PassiveCeil', 26)
def ceiling_tech():
    """Against the ceiling: hands and feet up flat to it, then dropping away into the fall."""
    up = lambda: legs(arms(tuck(0.9, arms=0.2), (0.4, 1, 0.1), (-0.4, 1, -0.1)), (0.2, 0.4, 0.8), (-0.2, 0.3, 0.8))
    return [(0, up()), (10, bend(up(), 'HeadN', -0.2)), (18, tuck(0.6, arms=0.6)), (26, air_start())]


@state('StopWall', 20)
def wall_bonk():
    """Bumped into a wall without teching: squashed against it, crumpling, then dropping away."""
    return [(0, crumple(0.0, 0.2)), (5, crumple(0.3, 0.2)), (12, shifted(tuck(0.8, arms=0.5), dy=-0.4)), (20, air_start())]


@state('StopCeil', 5)
def ceiling_bonk():
    """Head into the ceiling: the head snaps down, arms up."""
    p = bend(arms(tuck(0.4, arms=0.2), (0.5, 1, 0.2), (-0.5, 1, 0.2)), 'HeadN', 0.6)
    return [(0, p), (5, air_start())]


# ---------------------------------------------------------------------------------------------------------------- the ledge jump
def cliff_jump2(n):
    """The ledge jump's rise: from the tuck the first part ends in, knees snap up to his chest (the cast's ledge jumps tuck
    and hang low), then he opens into the fall."""
    ball = shifted(arms(bend(tuck(1.3, arms=0.5), 'WaistN', 0.45), (0.4, 0.2, 1), (-0.4, 0.2, 1), 0.2, 0.2), dy=-3.2, dz=-2.8)
    return [(0, tuck(0.3)), (round(n * 0.2), ball), (round(n * 0.5), shifted(tuck(1.0, arms=0.6), dy=-1.2)),
            (round(n * 0.8), tuck(0.5, arms=0.5)), (n, air_start())]


state('CliffJumpQuick2', 24)(lambda: cliff_jump2(24))
state('CliffJumpSlow2', 30)(lambda: cliff_jump2(30))


# ---------------------------------------------------------------------------------------------------------------- held by a grab
def held(hi, u):
    """Grabbed. High: bent into the grabber at the waist with the hips pushed back, hands drawn in to push, knees soft
    (the cast's stay near full height with the hurtboxes shifted back). Low: leaning away, arms flailing behind, a leg
    braced. u 0..1: the struggle's sway."""
    s = math.sin(TAU * u)
    if hi:
        p = base(crouch=0.15 + 0.04 * s, lean=0.15 + 0.06 * s)
        p = arms(p, (0.3, -0.6 + 0.1 * s, 0.4), (-0.3, -0.6 - 0.1 * s, 0.4), 0.7, 0.7)
        return shifted(bend(p, 'HeadN', 0.2, 0.1 * s), dz=-1.6)
    p = base(crouch=0.3, lean=-0.35 + 0.06 * s)
    p = arms(p, (0.5, 0.3 + 0.2 * s, -0.8), (-0.5, 0.3 - 0.2 * s, -0.8), 0.2, 0.2)
    return bend(p, 'HeadN', -0.2, 0.15 * s)


def pulled(hi):
    """Pulled into the grab: yanked toward the grabber, arms flung back, then into the hold."""
    yank = lambda: shifted(arms(base(crouch=0.2, lean=0.3), (0.4, 0.8, -0.6), (-0.4, 0.8, -0.6), 0.1, 0.1), dz=-0.8)
    return [(0, yank()), (6, bend(yank(), 'HeadN', 0.3)), (14, held(hi, 0.9)), (20, held(hi, 0.0))]


def pummeled(hi):
    """A pummel: a flinch back from the hit, then the hold again."""
    fl = lambda: bend(bend(held(hi, 0.0), 'WaistN', -0.35), 'HeadN', -0.45)
    return [(0, fl()), (4, fl()), (12, held(hi, 0.1)), (20, held(hi, 0.0))]


for _hi, _s in ((True, 'Hi'), (False, 'Lw')):
    state(f'CaptureWait{_s}', 50)(lambda hi=_hi: [(f, held(hi, f / 50)) for f in (0, 12, 25, 38, 50)])
    state(f'CapturePulled{_s}', 20)(lambda hi=_hi: pulled(hi))
    state(f'CaptureDamage{_s}', 20)(lambda hi=_hi: pummeled(hi))


@state('CaptureCut', 30)
def grab_break():
    """Broken free on the ground: shoved back a step, knees giving, arms up, then settling to the idle."""
    shove = lambda: shifted(bend(arms(base(crouch=0.6, lean=-0.45), (0.5, 0.6, 0.3), (-0.5, 0.6, 0.3), 0.2, 0.2), 'HeadN', -0.3), dz=-1.6)
    return [(0, shove()), (6, shove()), (16, shifted(base(crouch=0.4, lean=-0.1), dz=-0.6)), (24, base(crouch=0.08)), (30, base())]


@state('CaptureJump', 50)
def grab_break_air():
    """Broken free in the air: popped up and back, balled up, arms flung up, then opening into the fall."""
    pop = lambda: shifted(bend(legs(arms(tuck(1.0, arms=0.3), (0.5, 0.6, 1), (-0.5, 0.6, 1)), (0.2, -0.2, 1), (-0.2, -0.3, 1),
                                        (0, -0.8, 0.5), (0, -0.8, 0.4)), 'HeadN', -0.3), dy=-1.6, dz=-2.8)
    return [(0, pop()), (10, pop()), (24, shifted(tuck(0.9, arms=0.5), dy=-1.0)), (38, tuck(0.4, arms=0.4)), (50, air_start())]


# ---------------------------------------------------------------------------------------------------------------- dizzy, sleep, trip, clank
def dizzy(u):
    """Shield-broken and dizzy: the doll's strings gone slack. The body sways round a slow circle, the head lolls the other
    way, the arms hang and swing, the knees soft."""
    s, c = math.sin(TAU * u), math.cos(TAU * u)
    p = base(crouch=0.25 + 0.05 * s, lean=0.15 + 0.2 * s)
    bend(bend(p, 'WaistN', 0.0, 0.1 * c, 0.2 * c), 'HeadN', 0.35 - 0.2 * s, -0.25 * c, -0.35 * c)
    return arms(p, (0.2 + 0.2 * c, -1, 0.15 * s), (-0.2 + 0.2 * c, -1, -0.15 * s))


@state('FuraFura', 120)
def furafura():
    return [(f, dizzy(f / 120)) for f in range(0, 121, 15)]


def asleep(u=0.0):
    """Asleep on his feet, sagging on his strings: knees gone, bent at the waist, head on his chest, arms hanging (the
    cast's sleep sags to ~0.55 of their height); u a breath."""
    w = math.sin(math.pi * u)
    p = base(crouch=0.95 + 0.04 * w, lean=0.35 + 0.05 * w)
    bend(p, 'HeadN', 0.7 + 0.08 * w, 0, 0.12)
    p = arms(p, (0.25, -1, -0.25), (-0.25, -1, -0.25))
    return shifted(p, dz=-1.6)


@state('FuraSleepStart', 30)
def sleep_start():
    """Nodding off: two dips of the head, then he sags."""
    return [(0, base()), (8, bend(base(crouch=0.15), 'HeadN', 0.4)), (12, bend(base(crouch=0.1), 'HeadN', 0.1)),
            (22, bend(asleep(0.0), 'HeadN', -0.2)), (30, asleep(0.0))]


@state('FuraSleepLoop', 110)
def sleep_loop():
    return [(0, asleep(0.0)), (55, asleep(1.0)), (110, asleep(0.0))]


@state('FuraSleepEnd', 60)
def sleep_end():
    """Waking with a start: the head snaps up and the arms jerk out, a shake of the head, and the idle."""
    start = lambda: bend(arms(base(crouch=0.1, lean=-0.25), (0.8, 0.3, 0.2), (-0.8, 0.3, 0.2)), 'HeadN', -0.3)
    return [(0, asleep(0.0)), (4, start()), (10, bend(start(), 'HeadN', 0.1, 0.3)), (16, bend(base(), 'HeadN', 0, -0.3)),
            (22, bend(base(), 'HeadN', 0, 0.2)), (30, base(crouch=0.1)), (60, base())]


@state('MissFoot', 26)
def trip():
    """A trip: a foot shoots out, he goes over backward, arms flailing, falling onto his back (the cast's trips drop below
    their position), and into the tumble (DamageFall), which lands him at once."""
    slip = legs(arms(base(stance=0, lean=-0.3), (0.7, 0.6, 0.3), (-0.7, 0.7, 0.2)), (0.1, -0.5, 0.9), (-0.1, -1, 0.1))
    over = lambda: legs(arms(base(stance=0, lean=-0.5), (0.6, 0.8, 0.5), (-0.6, 0.9, 0.4)), (0.1, 0.2, 1), (-0.1, -0.2, 1))
    return [(0, base()), (3, slip), (8, tipped(over(), -0.6, 4.2)), (14, tipped(over(), -1.1, 2.6)),
            (20, tipped(flail(-0.8), FALL_A0 + 0.1, 4.0)), (26, tumble()[0][1])]


@state('Rebound', 30)
def clank():
    """Clanked: thrown back onto the rear foot, knees bent, arms pulled in, a wobble, and back to the idle."""
    back = lambda: shifted(bend(arms(base(crouch=0.8, lean=-0.35), (0.4, 0.0, 0.5), (-0.4, 0.0, 0.5), 0.7, 0.7), 'HeadN', -0.25), dz=-1.3)
    return [(0, back()), (5, back()), (12, shifted(arms(base(crouch=0.5, lean=-0.2), (0.4, -0.1, 0.5), (-0.4, -0.1, 0.5), 0.6, 0.6), dz=-1.0)),
            (18, back()), (26, base(crouch=0.12)), (30, base())]
