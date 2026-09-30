"""Geno's normals: each move's length, move script (from DESIGN.md v1.2 §6 and §6b) and blockout key poses timed to
its hit frames. Numbers are starting points for the labs (projects/geno/director/labs), which measure what the game does
with them; change them here.

Conventions: frames are the usual 1-based frame data (a hitbox opened after s.at(7) is active from frame 7). Poses are
world-aimed (anims.Pose): +Z is where Geno faces, +X his left, +Y up; his right arm is the gun arm. Hitboxes sit on engine
parts with offsets in that joint's frame (+X runs down a limb from the joint).
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig
from anims import Pose, base, tuck, crouch_pose, down
from fcmd import Script, PUNCH, KICK, SWING_S, SWING_M, SWING_L
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sound'))
import wiring                                    # the wooden movement sounds (bank 55, 550028-550052)

FA = rig.FOREARM
MOVES = {}

# Geno's own sounds: bank 55 (geno.ssm, from the SNES game's; ~/games/melee/work/sfxbank), IDs 550000 + k. They play
# through command 0x11 with behavior 0, as Mario's scripts do
GE_SFX = dict(PULSE=550000, HANDGUN=550001, HANDCANNON=550002, DOUBLEPUNCH=550003, STARGUN=550004, STARGUN_HIT=550005,
              NAIR_SWIRL=550006, CAPE=550007, PROJ_HIT=550008, FINGERSHOT=550009, BEAM_CHARGE=550010, BEAM_STAR1=550011,
              BEAM_STAR2=550012, BEAM_STAR3=550013, BEAM_RELEASE=550014, BEAM_FIRE=550015, BEAM_FULL=550016,
              WHIRL_THROW=550017, WHIRL_HIT=550018, WHIRL_CRIT=550020, BLAST_MARK=550021,
              BLAST_COLUMNS=550022, FLASH_TRANSFORM=550023, FLASH_FIRE=550024, FLASH_EXPLOSION=550025,
              STARROAD_FOLD=550026, STARROAD_LAUNCH=550027,
              # the gun normals' sounds fitted to their moves (sound/gunfit.py; Michael: the long ones outlasted the moves):
              # the Hand Gun's rattle cut to four shots (14.5 frames), the Hand Cannon's ring and the Star Gun's cascade
              # faded out by 28 and 27 frames, so each ends by its move's end. The originals stay for the throws
              HANDGUN_SHORT=550056, HANDCANNON_SHORT=550057, STARGUN_SHORT=550058,
              # the Hand Cannon in two (Michael: its sound came out late): SMRPG's triple (cock, cock, boom 12 frames in)
              # played whole on the shot put the boom 12 frames after it. The second cock is cued 6 frames ahead of the
              # shot and the boom with its ring on the shot, so the boom lands on the first active frame
              HANDCANNON_COCK=550059, HANDCANNON_BOOM=550060,
              HANDCANNON_SHOT=550061)     # the back throw's single-shot blast (poses_throws.SFX; Michael, 2026-09-29)


def gs(s, name):
    return s.sound(GE_SFX[name], behavior=0)


# His own effects (EfGeData.dat: projects/geno/fx/efge.py, the gun normals' bursts in efge_normals.py), spawned by name:
# a generator's id follows its place in the file's list, so it's looked up as the scripts are built (efge.gid), never
# written in
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fx'))
_FX_IDS = {}                     # efge.ids(), once per build
NORMALS_FX = os.environ.get('GENO_NORMALS_FX', '1') != '0'     # 0 builds without the gun normals' bursts (an A/B)
MUZZLE = {'gun': ('HandN', 2.75), 'stargun': ('HandN', 2.46), 'cannon': ('ArmJ', 3.04)}   # geno_forms: each barrel's tip
FINGER_MUZZLE = 1.65             # the Finger Shot's tubes past the wrist (poses_air.FINGER_MUZZLE, GE_FINGER_MUZZLE)


def fx(s, name, part='TopN', off=(0.0, 0.0, 0.0), rng=(0.0, 0.0, 0.0)):
    """Spawn his effect `name` at engine part `part`, offset in that joint's frame (poses_ground.gfx)."""
    import poses_ground as PG
    if not _FX_IDS:
        import efge
        _FX_IDS.update(efge.ids())
    if name not in _FX_IDS:
        raise KeyError(f'no effect generator {name!r} in efge.py or its extensions')
    return PG.gfx(s, _FX_IDS[name], part, off, rng)


def burst_fx(s, form, r, y, z, tip=False, part='TopN'):
    """The burst that shows a gun blast's hitbox: form GUN, TAP, STAR or CANNON, sized for radius r, on the hitbox's
    own offset (y up, z forward on TopN, as burst() places the hitbox), spawned with it. tip: the Hand Gun's tip burst,
    which forms SMRPG's small star."""
    import efge_normals as EN
    if NORMALS_FX:
        fx(s, f'N_{form}_{"TIP_" if tip else ""}{EN.cls_name(r)}', part, (0.0, y, z))


def cls_name(r):
    import efge_normals as EN
    return EN.cls_name(r)


def muzzle_fx(s, form, side='R', at=None):
    """The flash at a weapon form's muzzle (MUZZLE: the barrel's tip on its joint), or `at` down the joint (a blast from
    a bare hand: the hand's own hitbox point on ArmJ)."""
    joint, x = MUZZLE[form] if at is None else ('ArmJ', at)
    if NORMALS_FX:
        fx(s, {'gun': 'N_GUN_FLASH', 'stargun': 'N_STAR_FLASH', 'cannon': 'N_CANNON_FLASH'}[form], f'{side}{joint}',
           (x, 0.0, 0.0))


# A grown limb's hurtboxes grow with it (the engine measures a hurtbox's radius in its bone's space), and his hitboxes
# don't ride the growth, so on some moves the growth costs more disjoint than the cast's own does
# (research/growth_cost.md). Those moves make the grown part intangible while it is grown, as Double Punch's flying
# fists are. GENO_GROW_INTANG=move,... overrides the set (an A/B; "none" for none). The jabs keep their full growth
# with no intangibility (Michael, 2026-09-29): they pay the hurtbox cost, as the cast's grown limbs do.
GROW_INTANG = {'utilt'}
if os.environ.get('GENO_GROW_INTANG'):
    GROW_INTANG = set(os.environ['GENO_GROW_INTANG'].split(',')) - {'', 'none'}


def grown_intangible(s, move, joints, on):
    """while `move`'s part is grown: its bones' hurtboxes intangible (on) or back (off)"""
    import anims
    if move in GROW_INTANG and not anims.NO_GROW:
        for j in joints:
            s.hurt(j, 2 if on else 0)


def move(name, frames, *aliases):
    def reg(fn):
        MOVES[name] = (frames, fn)
        for a in aliases:
            MOVES[a] = (frames, fn)
        return fn
    return reg


def arm(p, side, d, bend=0.0):
    """Point an arm along world direction d; bend 0..1 folds the forearm up toward the chest."""
    sx = 1 if side == 'L' else -1
    p.aim(f'{side}ShoulderJ', d)
    p.aim(f'{side}ArmJ', (d[0] * (1 - bend) - sx * 0.3 * bend, d[1] * (1 - bend) + 0.6 * bend, d[2] * (1 - bend) + 0.6 * bend))
    return p


def leg(p, side, thigh, shin):
    p.aim(f'{side}LegJ', thigh); p.aim(f'{side}KneeJ', shin)
    return p


# ---------------------------------------------------------------------------------------------------------------- shapes
# v1.2 geometry (DESIGN §6b): reach, size and disjoint set against the measured cast (research/cast_moves.md), shapes
# against research/aerial_shape.md. His arms are short (4.45), so the reach of the gun-arm moves lives in muzzle bursts:
# hitboxes on TopN (offsets from his position: y up, z forward, both facings) that no hurtbox follows. Limb hitboxes keep
# the part of each move that the body carries.
def burst(s, i, dmg, r, y, z, **kw):
    s.hitbox(i, 'TopN', dmg, r, (0, y, z), **kw)


def spin(d, th):
    """A world direction turned th radians about +Y (his facing is +Z)."""
    c, sn = math.cos(th), math.sin(th)
    return (d[0] * c + d[2] * sn, d[1], -d[0] * sn + d[2] * c)


# ---------------------------------------------------------------------------------------------------------------- jabs
def jab(side):
    """Finger taps: a short muzzle burst past the pointing finger (non-travelling), 3% (poses_ground.jab)."""
    def build(k):
        import poses_ground as PG
        s = Script()
        s.jab_window(False)
        s.at(3)
        grown_intangible(s, 'jab', [f'{side}HandN'], True)
        s.hitbox(0, f'{side}ArmJ', 3, 2.4, (FA + 0.6, 0, 0), angle=80, kbg=100, wdsk=22)
        burst(s, 1, 3, 3.6, 9.0, 12.4, angle=80, kbg=100, wdsk=22)
        burst_fx(s, 'TAP', 3.6, 9.0, 12.4)
        gs(s, 'PULSE')
        s.wait(2); s.clear()
        s.at(6); s.jab_window(True)
        grown_intangible(s, 'jab', [f'{side}HandN'], False)
        s.at(17); s.iasa()
        return s, PG.jab(side)
    return build


MOVES['Attack11'] = (18, jab('R'))
MOVES['Attack12'] = (18, jab('L'))


@move('Attack13', 30)
def jab3(k):
    """The push-away: both palms shove out and fire a burst that sends the opponent back to his range (poses_ground.jab3)."""
    import poses_ground as PG
    s = Script()
    s.at(5)
    grown_intangible(s, 'jab3', ['RHandN', 'LHandN'], True)
    for i, sd in enumerate('RL'):
        s.hitbox(i, f'{sd}ArmJ', 5, 2.6, (FA + 0.8, 0, 0), angle=40, kbg=90, bkb=40, sfx=(1, PUNCH))
    burst(s, 2, 5, 4.4, 8.6, 13.6, angle=40, kbg=90, bkb=40, sfx=(1, PUNCH))
    burst_fx(s, 'TAP', 4.4, 8.6, 13.6)
    gs(s, 'PULSE')
    s.wait(3); s.clear()
    s.at(9); grown_intangible(s, 'jab3', ['RHandN', 'LHandN'], False)
    s.at(26); s.iasa()
    return s, PG.jab3()


# ---------------------------------------------------------------------------------------------------------------- tilts
def ftilt(angle_y):
    """Hand Gun: a wrist blast down the barrel's line, disjointed past the hand; safe only at the tip. The hand snaps into
    the gun as it's drawn (frame 3) and folds back as he lowers it (16) (poses_ground.ftilt)."""
    def build(k):
        import poses_ground as PG
        s = Script()
        s.at(3); s.form('R', 'gun')
        s.at(7)
        s.hitbox(0, 'RArmJ', 9, 2.6, (FA + 0.6, 0, 0), angle=361, kbg=100, bkb=12, sfx=(1, PUNCH))
        burst(s, 1, 9, 3.6, 9.2 + angle_y * 12.5, 12.5, angle=361, kbg=100, bkb=12, sfx=(1, PUNCH))
        burst(s, 2, 10, 4.3, 9.2 + angle_y * 18.2, 18.2, angle=361, kbg=100, bkb=14, sfx=(1, PUNCH))
        muzzle_fx(s, 'gun')
        burst_fx(s, 'GUN', 3.6, 9.2 + angle_y * 12.5, 12.5)
        burst_fx(s, 'GUN', 4.3, 9.2 + angle_y * 18.2, 18.2, tip=True)
        gs(s, 'HANDGUN_SHORT')
        s.wait(3); s.clear()
        s.at(16); s.form('R', 'hand')
        s.at(28); s.iasa()
        return s, PG.ftilt(angle_y)
    return build


MOVES['AttackS3S'] = (30, ftilt(0.0))
MOVES['AttackS3Hi'] = (30, ftilt(0.45))
MOVES['AttackS3Lw'] = (30, ftilt(-0.45))


@move('AttackHi3', 30)
def utilt(k):
    """Up tilt: a spin of the cape upward: the doll twirls a full turn in a hop, arms flung wide, the capelet flaring; a
    disjointed arc from front to back (the cape has no hurtbox) (poses_ground.utilt)."""
    import poses_ground as PG
    s = Script()
    arc = [(6, 15.5, 7.0), (7, 18.5, 3.5), (8, 19.5, 0.0), (9, 18.5, -3.5), (10, 15.5, -7.0)]
    # the stars (Michael: extend the visual with stars; 2026-09-30: his own star particles, not the engine's flash). Each
    # active frame a gold star pops on the burst it's on over a warm glow, so the arc of stars traces the disjoint and
    # goes with it; at the top of the arc (8) a bigger star throws a ring of small ones; twinkles are shed from the
    # twirling hands, one hand a frame (efge_normals N_UTILT_*)
    for f in (4, 5):
        s.at(f)
        if NORMALS_FX:
            fx(s, 'N_UTILT_TRAIL', 'RHandN' if f % 2 else 'LHandN', (0.6, 0, 0))
    for (f, y, z), (_, hy, hz) in zip(arc, PG.UTILT_HEAD_PATH):
        s.at(f)
        burst(s, 0, 9, 5.0, y, z, angle=95, kbg=110, bkb=25, sfx=(1, KICK))
        # the head box, the blockout's path on HeadN kept frame by frame (the twirl turns the head a full circle)
        burst(s, 1, 9, 3.0, hy, hz, angle=95, kbg=110, bkb=25, sfx=(1, KICK))
        if NORMALS_FX and f != 8:
            fx(s, 'N_UTILT_GLINT', 'TopN', (0, y, z))
        if NORMALS_FX and f <= 9:
            fx(s, 'N_UTILT_TRAIL', 'RHandN' if f % 2 else 'LHandN', (0.6, 0, 0))
        if f == 6:
            gs(s, 'CAPE')
            s.cap('back', 2)
            grown_intangible(s, 'utilt', ['RHandN', 'LHandN'], True)
        if f == 8 and NORMALS_FX:
            fx(s, 'N_UTILT_TOP', 'TopN', (0, y, z))
    s.at(11); s.clear()
    grown_intangible(s, 'utilt', ['RHandN', 'LHandN'], False)
    s.at(16); s.cap('rest', 8)
    s.at(28); s.iasa()
    return s, PG.utilt()


@move('AttackLw3', 24)
def dtilt(k):
    """Down tilt: a low Finger Shot from the crouch that skips along the floor; low angle, trips at low percent, a
    knockdown source. A gun blast like the rest of his arsenal (v1.2), so its reach is disjoint (poses_ground.dtilt)."""
    import poses_ground as PG
    s = Script()
    s.at(4); s.form('R', 'fshot')
    s.at(6)
    s.hitbox(0, 'RArmJ', 6, 2.4, (FA + 0.6, 0, 0), angle=25, kbg=70, bkb=30, sfx=(0, PUNCH))
    burst(s, 1, 7, 3.4, 2.0, 10.0, angle=25, kbg=70, bkb=30, sfx=(0, PUNCH))
    burst(s, 2, 7, 4.0, 2.2, 15.4, angle=25, kbg=70, bkb=30, sfx=(0, PUNCH))
    if NORMALS_FX:                                # the Finger Shot's own muzzle puff at the tubes (efge FINGER_PUFF)
        fx(s, 'FINGER_PUFF', 'RHandN', (FINGER_MUZZLE, 0.0, 0.0))
    burst_fx(s, 'TAP', 3.4, 2.0, 10.0)            # the finger taps' burst on each sphere, the star at the tip
    burst_fx(s, 'TAP', 4.0, 2.2, 15.4)
    gs(s, 'PULSE')
    s.wait(3); s.clear()
    s.at(13); s.form('R', 'hand')
    s.at(22); s.iasa()
    return s, PG.dtilt()


@move('AttackDash', 40)
def dash_attack(k):
    """Cannon Charge (Michael, 2026-09-30: the shoulder dive was "visually unclear ... puny / unfinished"): out of the run
    the right arm folds into the Hand Cannon (2), he lunges with it thrust out level (4-5) and fires at point-blank on 6:
    the blast at the muzzle and down the barrel (9%, 6-9), then its lingering fire at the muzzle as he skids back on the
    recoil (6%, 10-15). The same frame data and knockback as the dive it replaces (startup 6, active 6-15, IASA 38;
    TransN root motion: the action is flagged for it). poses_ground.dash_attack."""
    import poses_ground as PG
    mz = MUZZLE['cannon'][1]                                   # the cannon's mouth down ArmJ
    s = Script()
    s.at(2); s.form('R', 'cannon')
    gs(s, 'HANDCANNON_COCK')                                   # the cock as the arm folds (the ka-chunk)
    s.at(6)
    s.hitbox(0, 'RArmJ', 9, 4.5, (mz, 0, 0), angle=60, kbg=60, bkb=60, sfx=(1, PUNCH))           # the blast
    s.hitbox(1, 'RArmJ', 9, 3.4, (0.8, 0, 0), angle=60, kbg=60, bkb=60, sfx=(1, PUNCH))          # the barrel
    if NORMALS_FX:                                # a heavier blast and shock ring at the mouth, a fire burst on the blast sphere
        fx(s, 'N_CANNON_HEAVY', 'RArmJ', (mz, 0.0, 0.0))
        fx(s, f'N_CANNON_{cls_name(4.5)}', 'RArmJ', (mz, 0.0, 0.0))
    gs(s, 'HANDCANNON_BOOM')

    def after(f):                                 # the skid (8-18): dust at his feet; smoke curling from the barrel to ~20
        if not NORMALS_FX:
            return
        if f in (8, 11, 14, 17):
            PG.gfx(s, 1025, 'TransN')             # the engine's skid dust (the run brake's)
        if f in (9, 12, 15, 18):
            fx(s, 'N_BARREL_SMOKE', 'RArmJ', (mz + 0.3, 0.0, 0.0))
    for f in (8, 9):
        s.at(f); after(f)
    s.at(10)
    s.remove(1)
    s.hitbox(0, 'RArmJ', 6, 4.0, (mz, 0, 0), angle=60, kbg=50, bkb=40, sfx=(0, PUNCH))           # its lingering fire
    if NORMALS_FX:
        fx(s, f'N_CANNON_{cls_name(4.0)}', 'RArmJ', (mz, 0.0, 0.0))
    for f in (11, 12, 14, 15):
        s.at(f); after(f)
    s.at(16); s.clear()
    for f in (17, 18):
        s.at(f); after(f)
    s.at(24); s.form('R', 'hand')
    s.at(38); s.iasa()
    return s, PG.dash_keys()


# ---------------------------------------------------------------------------------------------------------------- smashes
EXHAUST_STEP = 2.2      # units between exhaust puffs at most: N_EXHAUST's puffs (~1.9 across, growing) then overlap


def exhaust_trail(s, a, b, part='TopN', name='N_EXHAUST'):
    """A rocket's exhaust along its flight this frame: N_EXHAUST puffs from b (where the rocket's tail is now) back
    toward a (where it was last frame; None on the launch frame: one puff at b), EXHAUST_STEP apart at most, as offsets on
    `part` (TopN: x depth, y up, z forward). One puff a frame left gaps as wide as a frame's flight (~7 units for Double
    Punch); this fills them, so the trail is unbroken at any speed. Any flying fist can use it with its own path (the
    forward throw's: poses_throws.rocket_tails)."""
    if not NORMALS_FX:
        return
    if a is None:
        fx(s, name, part, b); return
    d = math.dist(a, b)
    n = max(1, math.ceil(d / EXHAUST_STEP))
    for k in range(n):                          # b, and n - 1 more back toward a (a itself is last frame's puff)
        t = k / n
        fx(s, name, part, tuple(bb + (aa - bb) * t for aa, bb in zip(a, b)))


def fist_tails(angle_y):
    """Double Punch's rocket tails per frame of the flight (14-18), per side, on TopN: each fist's hit point
    (poses_ground.fs_hits, where the fist is placed) less its back, 2.2 units along the flight (the hitbox sits 0.5 past
    HandN, the exhaust ring 0.3 behind it, times the fist's 2.8x growth)."""
    import poses_ground as PG
    H, p14 = PG.fs_hits(angle_y)
    tails = {}
    for k, sd in enumerate('RL'):
        pts = {14: p14[sd]}
        pts.update({f: H[f][k] for f in (15, 16, 17, 18)})
        tip = H[17][k]
        u = [t - p for t, p in zip(tip, p14[sd])]
        n = math.sqrt(sum(x * x for x in u)) or 1.0
        u = [x / n for x in u]
        tails[sd] = {f: tuple(p - 2.2 * x for p, x in zip(pts[f], u)) if f > 14 else tuple(pts[f])
                     for f in pts}
    return tails


def fsmash(angle_y):
    """Double Punch: both fists launch as rocket fists down their lines (hands have no hurtbox) and return
    (poses_ground.fsmash)."""
    def build(k):
        import poses_ground as PG
        s = Script()
        s.at(4); s.form('R', 'rocket'); s.form('L', 'rocket'); s.cap('low', 3)     # the cap pulled down: menace
        s.at(6); s.smash_charge()
        tails = fist_tails(angle_y)                     # the rockets' exhaust: an unbroken trail along the flight
        s.at(14); s.hurt('RHandN', 2); s.hurt('LHandN', 2)
        for sd in 'RL':
            exhaust_trail(s, None, tails[sd][14])
        for f, reach in [(15, 0.55), (16, 0.8), (17, 1.0)]:
            s.at(f)
            for i, sd in enumerate('RL'):
                s.hitbox(i, f'{sd}HandN', 16, 4.4, (0.5, 0, 0), angle=361, kbg=102, bkb=30, sfx=(2, PUNCH))
                exhaust_trail(s, tails[sd][f - 1], tails[sd][f])
            if f == 15:
                gs(s, 'DOUBLEPUNCH')
        s.at(18)
        for sd in 'RL':
            exhaust_trail(s, tails[sd][17], tails[sd][18])
        s.at(19); s.clear()
        s.at(24)
        for i, sd in enumerate('RL'):
            s.hitbox(i, f'{sd}HandN', 5, 3.0, (0.3, 0, 0), angle=45, kbg=50, bkb=20, sfx=(0, PUNCH))
        s.wait(3); s.clear()
        s.hurt('RHandN', 0); s.hurt('LHandN', 0)
        s.at(28); s.form('R', 'hand'); s.form('L', 'hand'); s.cap('rest', 10)
        s.at(44); s.iasa()
        return s, PG.fsmash(angle_y)
    return build


MOVES['AttackS4S'] = (45, fsmash(0.0))
MOVES['AttackS4Hi'] = (45, fsmash(0.4))
MOVES['AttackS4Lw'] = (45, fsmash(-0.4))


@move('AttackHi4', 40)
def usmash(k):
    """Star Gun: both wrists fire a column of stars straight up; his out-of-shield kill option (poses_ground.usmash)."""
    import poses_ground as PG
    s = Script()
    s.at(4); s.form('R', 'stargun'); s.form('L', 'stargun'); s.cap('low', 2)
    s.at(5); s.smash_charge()
    s.at(9)
    # kill lab: 36/34 killed Fox at 120% (no DI) and 140% (optimal DI), against a 105-115% target. The column reaches
    # 30.4 up (Michael, 2026-09-30: it "can't hit through a Battlefield platform to hit someone standing on it"; the
    # side platforms are 27.2 up and a standing Fox's feet reach ~0.6 below his position, so 26.8 grazed them): the top
    # sphere rises from 22 to 25.4, the lower from 18 to 17.5, still overlapping. Horizontal reach unchanged.
    burst(s, 0, 15, 5.4, 17.5, 0.5, angle=90, kbg=100, bkb=44, sfx=(2, KICK))
    burst(s, 1, 14, 5.0, 25.4, 0.5, angle=90, kbg=100, bkb=42, sfx=(2, KICK))
    # the wrists' flare lifts whoever stands beside him into the column: his out-of-shield kill has to hit an adjacent
    # opponent (lab: a column alone missed Fox 6.6 away). The front one keeps its strength; the back one is the sourspot
    # (Michael, 2026-09-30: "make the back a sourspot, don't weaken the front and top")
    burst(s, 2, 12, 5.2, 8.0, 5.0, angle=90, kbg=100, bkb=40, sfx=(1, KICK))
    burst(s, 3, 8, 5.2, 8.0, -5.0, angle=90, kbg=80, bkb=30, sfx=(1, KICK))
    for sd in 'RL':                               # both star guns flash, and stars spray over every sphere
        muzzle_fx(s, 'stargun', sd)
    for y, z, r in ((17.5, 0.5, 5.4), (25.4, 0.5, 5.0), (8.0, 5.0, 5.2)):           # the column and the front flare
        burst_fx(s, 'STAR', r, y, z)
    if NORMALS_FX:                                # the back sourspot: a smaller, lighter spray (pale, no glow)
        fx(s, 'N_STAR_SOUR', 'TopN', (0.0, 8.0, -5.0))
    gs(s, 'STARGUN_SHORT')
    s.cap('back', 2)                              # the crown tips back as he fires skyward
    s.wait(2)                                     # the stream keeps coming: a second spray up the column (11), to its top
    for y, z, r in ((21.5, 0.5, 4.4), (28.5, 0.5, 3.6)):
        burst_fx(s, 'STAR', r, y, z)
    s.wait(2); s.clear()
    s.at(18); s.form('R', 'hand'); s.form('L', 'hand'); s.cap('rest', 10)
    s.at(39); s.iasa()
    return s, PG.usmash()


@move('AttackLw4', 44)
def dsmash(k):
    """Twin Hand Cannons (Michael, 2026-09-28: like Mega Man's two-sided down smash): both arms fold into cannons and
    fire outward to both sides at once on frame 7, 12% each side at a low 30 degrees; covers rolls and knockdowns on both
    sides (poses_ground.dsmash). He opens square to the camera, so the left cannon is the front one."""
    import poses_ground as PG
    s = Script()
    s.at(2); s.form('R', 'cannon'); s.form('L', 'cannon'); s.cap('low', 2)
    gs(s, 'HANDCANNON_COCK')                        # the cock as the arms fold into cannons (the charge holds after it)
    s.at(4); s.smash_charge()
    s.at(7)
    s.hitbox(0, 'LArmJ', 12, 2.6, (FA + 0.6, 0, 0), angle=30, kbg=90, bkb=30, sfx=(1, PUNCH))      # in front
    burst(s, 1, 12, 4.7, 3.2, 12.6, angle=30, kbg=92, bkb=30, sfx=(1, PUNCH))
    s.hitbox(2, 'RArmJ', 12, 2.6, (FA + 0.6, 0, 0), angle=30, kbg=90, bkb=30, sfx=(1, PUNCH))      # behind
    burst(s, 3, 12, 4.7, 3.2, -12.6, angle=30, kbg=92, bkb=30, sfx=(1, PUNCH))
    for sd in 'LR':                                   # both cannons flash, a burst on each side's sphere
        muzzle_fx(s, 'cannon', sd)
    burst_fx(s, 'CANNON', 4.7, 3.2, 12.6)
    burst_fx(s, 'CANNON', 4.7, 3.2, -12.6)
    gs(s, 'HANDCANNON_BOOM'); gs(s, 'HANDCANNON_BOOM')          # a cannon each side: one doubled boom, on the shot
    s.wait(3); s.clear()
    for f in (10, 13, 14, 16, 19):                    # the held cannons smoke to ~22; the landing thud's dust on 14
        s.at(f)
        if NORMALS_FX and f == 14:
            PG.gfx(s, 1025, 'TransN')
        elif NORMALS_FX:
            for sd in 'LR':
                fx(s, 'N_BARREL_SMOKE', f'{sd}ArmJ', (MUZZLE['cannon'][1] + 0.3, 0.0, 0.0))
    s.at(28); s.form('R', 'hand'); s.form('L', 'hand'); s.cap('rest', 10)   # the smoking cannons held a while (24 until 2026-09-30)
    s.at(43); s.iasa()
    return s, PG.dsmash()


# ---------------------------------------------------------------------------------------------------------------- aerials
def air_base():
    """Every aerial's start and end pose: Fall frame 0 (states_air.fall_pose(), where the jumps end and the falls
    loop), a fresh Pose each call"""
    import states_air
    return states_air.fall_pose()


_NAIR_CORE = {}


def nair_stars():
    """The neutral air's spinning star core: on frames 3-12 a pair of stars on opposite sides of a circle round the core
    hitbox's centre (WaistN + (0, 1.3, 0) in the animation, on TopN), turned 45 degrees a frame from front-high over the top
    and round behind (the spin's direction), at the core's radius; gold on the clean hit (3-6, a glow at the core on 3),
    white twinkles on the late one (7-12). Returns stars(s, frame)."""
    if not _NAIR_CORE:
        import poses_air
        for f, p in poses_air.nair():
            if 3 <= f <= 12:
                W = rig.world_mats(pose={k: dict(t=v[0], r=v[1], s=p.scale.get(k)) for k, v in p.solve().items()})
                _NAIR_CORE[f] = tuple(rig.xform((0.0, 1.3, 0.0), W['WaistN']))

    def stars(s, f):
        if not NORMALS_FX or f not in _NAIR_CORE:
            return
        x, y, z = _NAIR_CORE[f]
        r = 4.6 if f <= 6 else 4.2
        a = math.radians(35 + 45 * (f - 3))              # from +z (front) toward +y (up): front-high, over the top, behind
        if f == 3:
            fx(s, 'N_NAIR_CORE', 'TopN', (0.0, y, z))
        for k in (0, 1):
            b = a + math.pi * k
            fx(s, 'N_NAIR_STAR' if f <= 6 else 'N_NAIR_TWINKLE', 'TopN', (0.0, y + r * math.sin(b), z + r * math.cos(b)))
    return stars


@move('AttackAirN', 40)
def nair(k):
    """The spinning doll: a disjointed star core and a 360° spin that ends low behind him. Frame 3, his out-of-shield
    option, his crossup (low rear coverage) and the follow-in behind the Whirl. Clean 3-6, late 7-20."""
    s = Script()
    import poses_air
    s.at(2); s.lag_on(); s.hand('R', 'open', 2); s.hand('L', 'open', 2)          # the hands fling open with the arms
    stars = nair_stars()                          # the spinning star core (Michael, 2026-09-30: restored), frames 3-12
    s.at(3)
    s.hitbox(0, 'WaistN', 12, 5.0, (0, 1.3, 0), angle=45, kbg=80, bkb=25, sfx=(1, KICK))
    burst(s, 1, 12, 3.5, 7.0, 5.5, angle=45, kbg=80, bkb=25, sfx=(1, KICK))
    burst(s, 2, 12, 3.0, 9.0, -4.0, angle=45, kbg=80, bkb=25, sfx=(1, KICK))
    gs(s, 'NAIR_SWIRL')
    stars(s, 3)
    for f in (4, 5, 6):
        s.at(f); stars(s, f)
    s.at(7)
    s.hitbox(0, 'WaistN', 7, 4.6, (0, 1.3, 0), angle=30, kbg=60, bkb=15, sfx=(0, KICK))
    burst(s, 1, 7, 3.0, 4.0, 4.5, angle=30, kbg=60, bkb=15, sfx=(0, KICK))
    burst(s, 2, 7, 3.5, 3.0, -4.0, angle=30, kbg=60, bkb=15, sfx=(0, KICK))
    stars(s, 7)
    for f in (8, 9, 10):
        s.at(f); stars(s, f)
    s.at(11); grown_intangible(s, 'nair', ['RKneeJ'], True); stars(s, 11)
    s.at(12); stars(s, 12)
    s.at(13); s.remove(1)
    s.at(17); grown_intangible(s, 'nair', ['RKneeJ'], False)
    s.at(21); s.clear()
    s.at(28); s.lag_off()
    s.at(34); s.iasa()
    return s, poses_air.nair()


@move('AttackAirF', 36)
def fair(k):
    """Hand Gun burst forward: late, long and strong at the tip (Byleth's lance aerials were the reference, v1.2). A
    wall from chest to knee out to ~20 units, weak in the middle and nothing within ~6 units of him: point-blank is
    nair's job. From a short hop it meets standing opponents on the way up, not crouching ones."""
    import poses_air
    s = Script()
    s.at(2); s.lag_on(); s.hand('R', 'fist', 3)
    s.at(6); s.form('R', 'gun')                                                         # the snap, at the coil's peak
    s.at(9)
    burst(s, 0, 13, 4.6, 7.6, 15.5, angle=361, kbg=100, bkb=22, sfx=(2, PUNCH))        # the tip
    burst(s, 1, 7, 3.2, 7.0, 9.5, angle=361, kbg=80, bkb=10, sfx=(1, PUNCH))          # the middle
    muzzle_fx(s, 'gun')
    burst_fx(s, 'GUN', 3.2, 7.0, 9.5)
    burst_fx(s, 'GUN', 4.6, 7.6, 15.5, tip=True)
    gs(s, 'HANDGUN_SHORT')
    s.wait(3); s.clear()
    s.at(22); s.form('R', 'hand'); s.hand('R', 'open', 4)                               # back to a hand as the arm drops
    s.at(30); s.lag_off()
    s.at(34); s.iasa()
    return s, poses_air.fair()


@move('AttackAirB', 38)
def bair(k):
    """Hand Cannon backward: late, long and strong at the tip, his turnaround kill (the same treatment as fair)."""
    import poses_air
    s = Script()
    s.at(2); s.lag_on()
    s.at(4); gs(s, 'HANDCANNON_COCK')                                                   # the cock, 6 frames before the boom
    s.at(6); s.form('R', 'cannon')                                                      # the snap, the elbow coming forward
    s.at(10)
    burst(s, 0, 14, 4.8, 7.5, -15.5, angle=361, kbg=100, bkb=24, sfx=(2, PUNCH))       # the tip
    burst(s, 1, 8, 3.2, 7.2, -9.5, angle=361, kbg=80, bkb=12, sfx=(1, PUNCH))         # the middle
    muzzle_fx(s, 'cannon')
    burst_fx(s, 'CANNON', 3.2, 7.2, -9.5)
    burst_fx(s, 'CANNON', 4.8, 7.5, -15.5)
    gs(s, 'HANDCANNON_BOOM')
    s.wait(3); s.clear()
    s.at(24); s.form('R', 'hand'); s.hand('R', 'open', 4)                               # back to a hand as he unwinds
    s.at(31); s.lag_off()
    s.at(36); s.iasa()
    return s, poses_air.bair()


@move('AttackAirHi', 32)
def uair(k):
    """Star Gun upward: an overhead arc from front to back, for juggles."""
    import poses_air
    s = Script()
    s.at(2); s.lag_on(); s.hand('R', 'fist', 1)
    s.at(3); s.form('R', 'stargun')                                                     # the snap, at the bottom of the gather
    for f, y, z in [(5, 16.5, 4.5), (6, 18.5, 2.0), (7, 19.0, -0.5), (8, 18.0, -3.0), (9, 16.0, -5.0)]:
        s.at(f)
        burst(s, 0, 10, 4.8, y, z, angle=85, kbg=110, bkb=20, sfx=(1, KICK))
        burst_fx(s, 'STAR', 4.8, y, z)                  # a spray of stars on each frame's sphere: the arc, front to back
        if f == 5:
            muzzle_fx(s, 'stargun')
            s.hitbox(1, 'HeadN', 10, 3.0, (0, 2.6, 0), angle=85, kbg=110, bkb=20, sfx=(1, KICK))
            gs(s, 'STARGUN_SHORT')
    s.at(10); s.clear()
    s.at(19); s.form('R', 'hand'); s.hand('R', 'open', 4)
    s.at(24); s.lag_off()
    s.at(28); s.iasa()
    return s, poses_air.uair()


DAIR_CANNON = bool(os.environ.get('GENO_DAIR_CANNON'))     # the A/B: the Hand Cannon column down air
# The engine blends into an action from the pose before it over ftData+0x10's frames (anim frames; anims.py passes this to
# fighter-build with locomotion.BLEND). Down air's landing blends in over 6 (~5 game frames at the 24-frame lag's rate):
# a fist landed anywhere on its flight eases home instead of popping to the landing's first frame
BLEND = {} if DAIR_CANNON else {'LandingAirLw': 6}


@move('AttackAirLw', 52)
def dair(k):
    """A rocket fist straight down (Michael, 2026-09-29: "the rocket fist design, similar to ftilt and fsmash ... long and
    disjointed ... with the meteor on the close / startup hit"), slowed and readied (Michael, 2026-09-30: "yeah, slow it
    down. Probably give the startup animation a clear 'readying rocket punch' read"). The fist cocks back and the rocket
    readies (3-10), it fires off the forearm on 12 and flies out to 13.0 below him (16) and home (24), as Double Punch's
    fists do; intangible while it's out, the hitboxes on it. The meteor on 13-14 (270, airborne targets only, while the
    fist is near him; a grounded opponent gets the 8% pop), the weak tail on 15-19 (5%, no spike), landing lag 2-43 (it
    autocancels from 44), IASA 50. The exhaust trails it out, the fist grows on its hit frames, and it plays Double
    Punch's sound. poses_air.dair."""
    if DAIR_CANNON:
        return dair_cannon(k)
    import poses_air
    F = poses_air.dair_fists()
    tail = {f: (x, y + 2.2, z) for f, (x, y, z) in F.items()}      # the rocket's tail, behind the fist on its way down
    F = poses_air.DAIR_FIRE                                                             # 12 (was 8)
    s = Script()
    s.at(2); s.lag_on()
    s.at(5); s.form('R', 'rocket')                                                      # snapped on, cocked by his head
    s.at(F); s.hurt('RHandN', 2)                                                        # fired: intangible while it's out
    exhaust_trail(s, None, tail[F])
    s.at(F + 1)
    s.hitbox(0, 'RHandN', 12, 4.8, (0.5, 0, 0), angle=270, kbg=80, bkb=20, sfx=(2, PUNCH), grounded=0)   # the meteor
    s.hitbox(1, 'RHandN', 8, 4.2, (0.5, 0, 0), angle=60, kbg=70, bkb=15, sfx=(1, PUNCH))              # a grounded pop
    exhaust_trail(s, tail[F], tail[F + 1])
    gs(s, 'DOUBLEPUNCH')
    s.at(F + 2); exhaust_trail(s, tail[F + 1], tail[F + 2])
    s.at(F + 3)
    s.remove(1)
    s.hitbox(0, 'RHandN', 5, 3.4, (0.5, 0, 0), angle=65, kbg=40, bkb=10, sfx=(0, PUNCH))              # the weak tail
    exhaust_trail(s, tail[F + 2], tail[F + 3])
    s.at(F + 4); exhaust_trail(s, tail[F + 3], tail[F + 4])
    s.at(F + 8); s.clear()
    s.at(F + 12); s.hurt('RHandN', 0)                                                   # docked
    s.at(F + 15); s.form('R', 'hand'); s.hand('R', 'open', 4)
    s.at(44); s.lag_off()
    s.at(50); s.iasa()
    return s, poses_air.dair()



def dair_cannon(k):
    """The Hand Cannon down air (until 2026-09-29, GENO_DAIR_CANNON=1 builds it): a Hand Cannon shot straight down: a blast column reaching ~13 below him (Michael, 2026-09-28: a cannon shot should
    read long; Falcon's reach is 12.5, the cast's max 13.9). The meteor sweetspot (270, cancellable) sits at the muzzle on
    frames 9-10; the column fades down the barrel line into a middle section and a weak tail that doesn't spike, the tail a
    frame behind the muzzle, as a shot travelling down (10-12). The meteor hits airborne targets only, so a grounded
    opponent under him gets the column (never spiked into the floor); offstage, near the muzzle, the meteor. Little rear
    coverage: behind a shield it's punishable, and nair stays the crossup tool."""
    import poses_air
    Z = 1.8                                                                             # the barrel line (the muzzle ~1.9-2.3)
    s = Script()
    s.at(2); s.lag_on()
    s.at(5); s.form('R', 'cannon')                                                      # the snap, at the top of the wind-up
    s.at(9)
    burst(s, 0, 12, 4.8, 2.0, Z, angle=270, kbg=80, bkb=20, sfx=(2, PUNCH), grounded=0)   # the meteor, at the muzzle
    burst(s, 1, 8, 4.2, -4.0, Z, angle=60, kbg=70, bkb=15, sfx=(1, PUNCH))              # the middle of the column
    muzzle_fx(s, 'cannon')                                                              # the blast: the meteor's muzzle
    burst_fx(s, 'CANNON', 4.8, 2.0, Z)
    burst_fx(s, 'CANNON', 4.2, -4.0, Z)
    gs(s, 'HANDCANNON')
    s.at(10)
    burst(s, 2, 5, 3.4, -9.6, Z, angle=65, kbg=40, bkb=10, sfx=(0, PUNCH))              # the tail: reaches 13.0 below
    burst_fx(s, 'CANNON', 3.4, -9.6, Z)                                                 # the column's end, a frame on
    s.at(11)
    burst(s, 0, 8, 4.4, 2.0, Z, angle=60, kbg=80, bkb=15, sfx=(1, PUNCH))               # the muzzle's sourspot
    s.at(13); s.remove(2)
    s.at(16); s.clear()
    s.at(23); s.form('R', 'hand'); s.hand('R', 'open', 4)
    s.at(32); s.lag_off()
    s.at(38); s.iasa()
    return s, poses_air.dair_cannon()


# The aerials' landing lag (the template's 30-frame animations and scripts, played over the lag: poses_air.landing): each
# lands in a squash with its move's limb still out and rises onto Wait1's first frame
for _name, _fn in (('LandingAirN', 'landing_n'), ('LandingAirF', 'landing_f'), ('LandingAirB', 'landing_b'),
                   ('LandingAirHi', 'landing_hi'), ('LandingAirLw', 'landing_lw')):
    MOVES[_name] = (30, lambda k, fn=_fn: (None, getattr(__import__('poses_air'), fn)()))


# ---------------------------------------------------------------------------------------------------------------- grab, throws
HOLD_T = (0, 2.4, 6.8)           # CatchWait's ThrowN (in YRotN's frame) ...
HOLD_YROT = (0, -2.2 * 0.1, 0.3 * 0.1)   # ... with the blockout CatchWait's YRotN (base(crouch=0.1)): the hold point in
# the world, (0, HIP_Y, 0) + HOLD_YROT + HOLD_T, is poses_ground.HOLD_W, where the production hold keeps the victim


def holding(p, t=HOLD_T, ry=3.1416):
    """Carry the grabbed opponent at ThrowN (in YRotN's frame), turned to face Geno."""
    return p.move('ThrowN', t).rot('ThrowN', (0, ry, 0))


_GRAB_TAILS = {}
FLY_OFF = 1.2                    # a fist this far off its socket is flying: the grabs' exhaust trail runs while it is


def grab_tails(frame, total, dash):
    """The grabs' rocket fists from their animation (poses_ground.grab), per frame: {frame: {side: (tail on TopN (x depth,
    y up, z forward), how far the fist is off its socket)}}; the tail is the exhaust ring 0.3 behind HandN, scaled with
    the fist, as moves.fist_tails and poses_throws.rocket_tails take it. Longer grabs change the path, and the trail
    follows."""
    key = (frame, total, dash)
    if key not in _GRAB_TAILS:
        import poses_ground as PG
        out = {}
        for f, p in PG.grab(frame, total, dash):
            W = rig.world_mats(pose={k: dict(t=v[0], r=v[1], s=p.scale.get(k)) for k, v in p.solve().items()})
            out[f] = {sd: (tuple(rig.xform((-0.3, 0.0, 0.0), W[f'{sd}HandN'])),
                           math.dist(rig.xform((0.0, 0.0, 0.0), W[f'{sd}HandN']), rig.xform((FA, 0.0, 0.0), W[f'{sd}ArmJ'])))
                      for sd in 'RL'}
        _GRAB_TAILS[key] = out
    return _GRAB_TAILS[key]


def grab(ext, frame, total, lunge=1.5):
    """The fists shoot out on the arm bones as rocket fists (his Double Punch, closing on the opponent): the grab boxes
    ride the hands, so the hands' hurtboxes travel with them (a body move, not a gun blast: little disjoint). The dash
    grab fires them too, a short way out of the run (poses_ground.grab)."""
    dash = lunge == 0.0
    def build(k):
        import poses_ground as PG
        s = Script()
        s.at(3); s.form('R', 'rocket'); s.form('L', 'rocket')
        launch = frame - 1 if dash else 5               # the fists fire off the arms: the rocket's launch star at each
        tails = grab_tails(frame, total, dash)          # socket, then its exhaust behind each fist while it flies
        # the trail only while a fist is well off its socket (FLY_OFF): the dash grab's fists barely leave (1.0 at most),
        # and puffs spawned there were left behind him by the slide, reading as an effect behind his body
        fly = [f for f in sorted(tails) if f > launch and any(tails[f][sd][1] > FLY_OFF for sd in 'RL')]

        puff = 'N_EXHAUST_QUICK' if dash else 'N_EXHAUST'   # the dash grab slides on through its puffs: they go in 6

        def rockets(f):
            if f == launch:
                for sd in 'RL':
                    if NORMALS_FX:                  # at the flying hand's wrist, as the forward throw's ignition
                        fx(s, 'N_ROCKET_FLARE', f'{sd}HandN', (-0.5, 0.0, 0.0))
                    if any(tails[g][sd][1] > FLY_OFF for g in fly):
                        exhaust_trail(s, None, tails[f][sd][0], name=puff)
            else:
                for sd in 'RL':
                    if tails[f][sd][1] > FLY_OFF or tails[f - 1][sd][1] > FLY_OFF:
                        exhaust_trail(s, tails[f - 1][sd][0], tails[f][sd][0], name=puff)
        s.at(launch); rockets(launch)
        for f in [f for f in fly if f < frame]:
            s.at(f); rockets(f)
        s.at(frame)
        if frame in fly:
            rockets(frame)
        grown_intangible(s, 'grab', ['RHandN', 'LHandN'], True)
        s.hitbox(0, 'RHandN', 0, 4.0, (0.6, 0, 0), angle=361, kbg=100, element=8, clank=1, rebound=0, sfx=(1, KICK))
        s.hitbox(1, 'LHandN', 0, 4.0, (0.6, 0, 0), angle=361, kbg=100, element=8, clank=1, rebound=0, sfx=(1, KICK))
        for f in (frame + 1,):
            s.at(f)
            if f in fly: rockets(f)
        s.at(frame + 2); s.clear()
        if frame + 2 in fly: rockets(frame + 2)
        s.release(0)   # ends the pull (CatchPull plays on in this animation until throw_flags_b3), as Mario's does
        s.at(frame + 3); grown_intangible(s, 'grab', ['RHandN', 'LHandN'], False)
        for f in [f for f in fly if f >= frame + 3]:
            s.at(f); rockets(f)
        # ThrowN is the hold joint (the lookup table's byte 0x11). From before the grab frame it sits at CatchWait's hold
        # point in the world (the victim rides it through the pull and into CatchWait), so the catch is one latch; it has
        # to be there by the grab frame, or the engine's pull check (fn_800DA054) breaks a point-blank grab.
        s.at(12 if not dash else 14); s.form('R', 'hand'); s.form('L', 'hand')
        return s, PG.grab(frame, total, dash)
    return build


MOVES['Catch'] = (30, grab(2.2, 7, 30))          # standard grab (~50th: reach ~13)
MOVES['CatchDash'] = (40, grab(-1.5, 9, 40, lunge=0.0))   # plus the slide (root motion, Mario's path)


@move('CatchWait', 30)
def catch_wait(k):
    """The hold: the left hand grips the opponent, the right waits cocked with its finger out (poses_ground.catch_wait)."""
    import poses_ground as PG
    return Script(), PG.catch_wait()


@move('CatchCut', 30)
def catch_cut(k):
    """The opponent breaks free: thrown off balance, then back to the idle (poses_ground.catch_cut)."""
    import poses_ground as PG
    return Script(), PG.catch_cut()


def throw(name):
    """A throw (DESIGN §6f: one weapon each): its script and animation are poses_throws.THROWS[name]'s, starting on
    CatchWait's frame 0 (the held opponent at HOLD_T) and ending on the idle's."""
    import poses_throws
    t = poses_throws.THROWS[name]
    MOVES[name] = (t.n, lambda k: (t.script(), t.keys()))


for _name in ('ThrowF', 'ThrowB', 'ThrowHi', 'ThrowLw'):
    throw(_name)


# ---------------------------------------------------------------------------------------------------------------- pummel
# The standardized moves (DESIGN §6c) sit at the cast's medians (research/cast_moves.md, "Pummel, ledge and get-up
# attacks"): their numbers are the game's shared vocabulary, so only the look and sound are his.
def hold_pose():
    """CatchWait's frame 0, the hold every grab action starts or ends on (CatchAttack, CatchCut, the throws): the left
    hand has the opponent by the collar, the right (gun) hand cocked at his chest with its finger out, ThrowN at HOLD_T
    (poses_ground.hold_params, which a poses_ground.Clip takes as its start or end)."""
    import poses_ground as PG
    return PG.hold_pose()


@move('CatchAttack', 24)
def pummel(k):
    """Finger to the chest: the left hand holds, the right draws back and jabs its finger in with a point-blank pop.
    3% on frame 9 of 24 (the cast's median), hitting only the held opponent, as the cast's pummels do. The animation is
    poses_ground.pummel, from and back to CatchWait's hold."""
    import poses_ground as PG
    s = Script()
    s.at(9)
    burst(s, 0, 3, 4.6, 7.5, 7.0, angle=80, kbg=100, wdsk=30, shield=1, sfx=(0, PUNCH), only_grabbed=1)
    gs(s, 'PULSE')
    s.wait(1); s.clear()
    return s, PG.pummel()


# ---------------------------------------------------------------------------------------------------------------- ledge attacks
# Ledge actions move by TransN from the ledge corner (the engine: pos = ledge + TransN, ftCo_CliffClimb_Phys), and he
# stands on the stage on the first frame TransN has z >= 0 and y >= 0; from then on TransN's forward steps are his ground
# movement. Both start from CliffWait's hang (Mario's template path at Geno's scale, anims.root_motion) and his hang pose.
HANG_T = (0, -10.689 * 1.1 * 15.24 / 14.27, -1.7155 * 1.1 * 15.24 / 14.27)    # CliffWait's TransN: (0, -12.557, -2.015)
LEDGE_HANDS = ((1.3, 0.25, 0.9), (-1.3, 0.25, 0.9))                            # palms flat on the stage past the corner


def rburst(s, i, dmg, r, y, z, **kw):
    """A burst from where he stands: TransN, the fighter's position in a root-motion action (TopN would measure from the
    ledge corner, since datkit poses TransN's path under it; the game zeroes TransN, so both are the same there)."""
    s.hitbox(i, 'TransN', dmg, r, (0, y, z), **kw)


def plant_hands(p, targets=LEDGE_HANDS, pole=(0, 0.2, -1)):
    """Two-bone IK: both arms reach for world points (palms on the ledge), elbows toward pole (splayed out to each side)."""
    solved = {k: {'t': v[0], 'r': v[1]} for k, v in p.solve().items()}
    W = rig.world_mats(pose=solved)
    up, lo = rig.UPPER_ARM, rig.FOREARM + 0.4
    for (side, sx), tgt in zip((('L', 1), ('R', -1)), targets):
        sh = W[f'{side}ShoulderJ'][3][:3]
        d = [t - s_ for t, s_ in zip(tgt, sh)]
        L = min(math.sqrt(sum(x * x for x in d)), (up + lo) * 0.999)
        u = [x / (math.sqrt(sum(y * y for y in d)) or 1) for x in d]
        pl = (pole[0] + 0.7 * sx, pole[1], pole[2])
        v = [a - sum(b * c for b, c in zip(pl, u)) * ui for a, ui in zip(pl, u)]
        vn = math.sqrt(sum(x * x for x in v)) or 1
        v = [x / vn for x in v]
        ca = (up ** 2 + L ** 2 - lo ** 2) / (2 * up * L)
        sa = math.sqrt(max(0.0, 1 - ca * ca))
        elbow = [up * (ca * a + sa * b) for a, b in zip(u, v)]
        p.aim(f'{side}ShoulderJ', elbow)
        p.aim(f'{side}ArmJ', [L * a - e for a, e in zip(u, elbow)])
    return p


def climb(ty, tz, lean, knee=0.0, legs=0.0):
    """A pull-up frame: TransN at (ty, tz) from the ledge corner, the torso leaning over the lip, palms planted.
    knee 0..1 draws the left knee up onto the lip (the right trails); legs 0..1 tucks both (the doll's stiff kick-up)."""
    p = base(stance=0, lean=lean).move('TransN', (0, ty, tz))
    for sd, sx, amt in (('L', 1, max(knee, legs)), ('R', -1, legs * 0.7)):
        p.aim(f'{sd}LegJ', (sx * 0.1, -1 + 1.3 * amt, 0.15 + 1.2 * amt)); p.aim(f'{sd}KneeJ', (0, -1, 0.1 - 0.5 * amt))
        p.aim(f'{sd}FootJ', (0, -0.3 + 0.2 * amt, 1), up=(0, -1, 0))   # up: where the sole faces
    return plant_hands(p)


def hang_grip(legs=0.0, lean=0.0):
    """CliffWait's hang (states.py): palms on the lip where the climbs plant them, arms bent to reach, legs dangling. Every
    ledge action starts from it (the engine never blends between actions)."""
    return climb(HANG_T[1], HANG_T[2], lean=lean, legs=legs)


def on_stage(z, crouch, **kw):
    return base(crouch=crouch, **kw).move('TransN', (0, 0, z))


def gun_low(p, side='R', down=-0.28, back_arm=True, fwd=1):
    """The gun arm levelled low along the floor, forward (fwd=1) or behind him (-1); the other arm swept back for
    balance."""
    sx = 1 if side == 'L' else -1
    arm(p, side, (sx * 0.08, down, fwd))
    if back_arm:
        arm(p, 'L' if side == 'R' else 'R', (-sx * 0.35, -0.5, -0.6 * fwd), bend=0.3)
    return p


@move('CliffAttackQuick', 55)
def ledge_quick(k):
    """Under 100%: a snap pull-up (a dip, then the doll yanked over the lip), feet on the corner on frame 18, and a Hand
    Gun burst on 24-28 that rakes up from the floor across the lip. Intangible 1-20, 8%, set knockback: the cast's
    medians."""
    s = Script()
    s.body(2)
    s.at(18); s.raw(wiring.cue(wiring.ID['STEP_RUN_R'], 0x6E))      # a running footfall as his feet hit the stage
    s.at(21); s.body(0)
    s.hand('R', 'fist', 2); s.form('R', 'gun')                          # the Hand Gun snaps on as he cocks it (21)
    for f, y, z in ((24, 4.5, 15.0), (26, 7.5, 14.5), (28, 10.5, 13.5)):      # the burst rakes up from the lip
        s.at(f)
        rburst(s, 0, 8, 5.0, y, z, angle=361, kbg=100, wdsk=90, shield=1, sfx=(1, PUNCH))
        rburst(s, 1, 8, 3.8, 4.5 + (y - 4.5) * 0.5, 8.5, angle=361, kbg=100, wdsk=90, shield=1, sfx=(1, PUNCH))
        burst_fx(s, 'GUN', 5.0, y, z, tip=f == 24, part='TransN')                  # the Hand Gun burst rakes up with it
        burst_fx(s, 'GUN', 3.8, 4.5 + (y - 4.5) * 0.5, 8.5, part='TransN')
        if f == 24:
            s.hitbox(2, 'RArmJ', 8, 2.6, (FA + 0.6, 0, 0), angle=361, kbg=100, wdsk=90, shield=1, sfx=(1, PUNCH))
            muzzle_fx(s, 'gun')
            gs(s, 'HANDGUN_SHORT')
    s.at(29); s.clear()
    s.at(33); s.form('R', 'hand'); s.hand('R', 'open', 4)                # folds back to a hand as he stands
    hy, hz = HANG_T[1], HANG_T[2]
    cock = lambda z: arm(on_stage(z, 0.75, lean=0.35), 'R', (-0.5, -0.3, 0.2), bend=0.5)
    shot = lambda z, d: gun_low(on_stage(z, 0.6, lean=0.3), down=d)
    keys = [(0, hang_grip()),
            (3, climb(hy - 0.5, hz, lean=0.1)),                        # the dip: weight into the hands
            (6, climb(hy - 0.9, hz, lean=0.15, legs=0.2)),
            (11, climb(hy + 5.0, hz + 0.1, lean=0.6, legs=0.6)),        # yanked up
            (14, climb(-4.0, hz + 0.3, lean=1.1, knee=1.0, legs=0.4)),   # over the lip, the left knee up
            (16, climb(-1.6, -1.0, lean=0.95, knee=1.0, legs=0.2)),      # the left foot on the lip
            (18, arm(on_stage(0.0, 0.85, lean=0.55), 'R', (-0.4, -0.5, 0.4), bend=0.4)),  # standing on the corner
            (21, cock(1.6)), (24, shot(3.0, -0.3)), (26, shot(3.5, 0.0)), (28, shot(4.0, 0.3)),
            (36, on_stage(5.6, 0.35)), (46, on_stage(6.8, 0.12)), (55, on_stage(7.2, 0.0))]
    return s, keys


@move('CliffAttackSlow', 70)
def ledge_slow(k):
    """From 100%: a heavy haul up (the strings slack), feet on the corner on frame 34, both hands drawn back and a
    two-handed Hand Cannon along the floor on 41-44. Intangible 1-37, 8%, set knockback: the cast's medians."""
    s = Script()
    s.body(2)
    s.at(34); s.raw(wiring.cue(wiring.ID['STEP_WALK_L'], 0x6E))     # a walking footfall onto the stage
    s.at(35); gs(s, 'HANDCANNON_COCK')                              # the cock, 6 frames before the boom
    s.at(38); s.body(0)
    s.form('R', 'cannon'); s.form('L', 'cannon')                        # both arms fold into Hand Cannons as he draws back
    s.at(41)
    rburst(s, 0, 8, 5.4, 6.0, 15.0, angle=361, kbg=100, wdsk=90, shield=1, sfx=(1, PUNCH))
    rburst(s, 1, 8, 4.2, 6.0, 8.5, angle=361, kbg=100, wdsk=90, shield=1, sfx=(1, PUNCH))
    for i, sd in ((2, 'R'), (3, 'L')):
        s.hitbox(i, f'{sd}ArmJ', 8, 2.6, (FA + 0.6, 0, 0), angle=361, kbg=100, wdsk=90, shield=1, sfx=(1, PUNCH))
        muzzle_fx(s, 'cannon', sd)
    burst_fx(s, 'CANNON', 5.4, 6.0, 15.0, part='TransN')                         # the two-handed Hand Cannon's blast
    burst_fx(s, 'CANNON', 4.2, 6.0, 8.5, part='TransN')
    gs(s, 'HANDCANNON_BOOM')
    s.wait(4); s.clear()
    s.at(50); s.form('R', 'hand'); s.form('L', 'hand'); s.hand('R', 'open', 4); s.hand('L', 'open', 4)   # after the recoil
    hy, hz = HANG_T[1], HANG_T[2]
    both = lambda p, d, bend=0.0: arm(arm(p, 'R', (-0.12, d, 1 - bend), bend=bend), 'L', (0.12, d, 1 - bend), bend=bend)
    drawn = lambda z: arm(arm(on_stage(z, 0.7, lean=-0.05), 'R', (-0.5, -0.2, -0.5), bend=0.6), 'L', (0.5, -0.2, -0.5), bend=0.6)
    keys = [(0, hang_grip()),
            (4, climb(hy - 0.6, hz, lean=0.1)),
            (10, climb(hy + 0.6, hz, lean=0.2)),
            (18, climb(hy + 4.0, hz + 0.1, lean=0.5, legs=0.3)),
            (26, climb(-4.6, hz + 0.3, lean=1.0, knee=0.8, legs=0.3)),
            (30, climb(-1.8, -1.2, lean=1.0, knee=1.0, legs=0.2)),
            (34, arm(arm(on_stage(0.0, 0.9, lean=0.6), 'R', (-0.3, -0.8, 0.5)), 'L', (0.3, -0.8, 0.5))),
            (38, drawn(1.0)), (41, both(on_stage(2.2, 0.55, lean=0.3), -0.25)), (44, both(on_stage(2.4, 0.55, lean=0.3), -0.2)),
            (47, both(on_stage(2.0, 0.6, lean=0.1), -0.1, 0.3)),               # the recoil rocks him back
            (54, on_stage(3.0, 0.35)), (62, on_stage(3.8, 0.12)), (70, on_stage(4.2, 0.0))]
    return s, keys


# ---------------------------------------------------------------------------------------------------------------- get-up attacks
# From DownWaitU / DownWaitD (anims.down: on his back with his feet toward the front, or on his face with his head toward
# it) to Wait's standing pose. Hand Gun blasts along the floor to both sides, intangible through the second: face up the
# front first (his down smash's order), face down the back first. 6% each, the cast's push (361, 50 growth, 80 base).
def getup_hits(s, first, second, front_first, vulnerable):
    """Each shot is two frames: a low blast along the floor, then it blooms upward, so the pair covers the cast's height
    on that side (research/getup_cover.md: ~14-15 at the top, ~12-13 at 8 and 14 units, ~11 over his body). The firing
    hand is a Hand Gun from 3 frames before its shot to 3 after (the right in front, the left behind). The intangibility
    ends on `vulnerable`, in the same frame order."""
    def shot(f, front):
        sg, sd = (1, 'R') if front else (-1, 'L')
        s.at(f)
        burst(s, 0, 6, 5.4, 4.6, sg * 13.8, angle=361, kbg=50, bkb=80, shield=1, sfx=(1, PUNCH))     # low, along the floor
        burst(s, 1, 6, 4.4, 6.5, sg * 7.6, angle=361, kbg=50, bkb=80, shield=1, sfx=(1, PUNCH))
        s.hitbox(2, f'{sd}ArmJ', 6, 2.6, (FA + 0.6, 0, 0), angle=361, kbg=50, bkb=80, shield=1, sfx=(1, PUNCH))
        muzzle_fx(s, 'gun', sd)                                                   # the Hand Gun burst, then its bloom
        burst_fx(s, 'GUN', 5.4, 4.6, sg * 13.8, tip=True)
        burst_fx(s, 'GUN', 4.4, 6.5, sg * 7.6)
        gs(s, 'HANDGUN_SHORT')
        s.wait(1)
        burst(s, 0, 6, 5.4, 9.0, sg * 13.0, angle=361, kbg=50, bkb=80, shield=1, sfx=(1, PUNCH))     # the bloom
        burst(s, 1, 6, 4.4, 8.5, sg * 7.0, angle=361, kbg=50, bkb=80, shield=1, sfx=(1, PUNCH))
        burst_fx(s, 'GUN', 5.4, 9.0, sg * 13.0)
        burst_fx(s, 'GUN', 4.4, 8.5, sg * 7.0)
        s.wait(1); s.clear()

    def gun_on(sd):
        s.hand(sd, 'fist', 2); s.form(sd, 'gun')

    def gun_off(sd):
        s.form(sd, 'hand'); s.hand(sd, 'open', 4)

    events = [(vulnerable, 2, lambda: s.body(0))]
    for f, front in ((first, front_first), (second, not front_first)):
        sd = 'R' if front else 'L'
        events += [(f - 3, 0, lambda sd=sd: gun_on(sd)), (f, 1, lambda f=f, front=front: shot(f, front)),
                   (f + 3, 0, lambda sd=sd: gun_off(sd))]
    for f, _, act in sorted(events, key=lambda e: (e[0], e[1])):
        s.at(f); act()


def crouch_low(lean=0.25, crouch=0.8):
    """The low crouch he fires the get-ups from, feet planted in his stance."""
    return base(crouch=crouch, lean=lean)


@move('DownAttackU', 50)
def getup_u(k):
    """Face up: the doll jerks upright off his back as if his strings were yanked, into a low crouch, and fires low in
    front (19-20), then swings the other gun behind (24-25). Intangible 1-25."""
    s = Script()
    s.body(2)
    s.at(3); s.raw(wiring.cue(wiring.ID['TECH'], 0x6E))
    getup_hits(s, 19, 24, front_first=True, vulnerable=26)
    gather = down(True)
    for sd, sx in (('L', 1), ('R', -1)):
        gather.aim(f'{sd}LegJ', (sx * 0.2, 0.5, 0.7)); gather.aim(f'{sd}KneeJ', (0, -0.3, 1))
    front = lambda d=-0.28: arm(gun_low(crouch_low(0.3), 'R', down=d, back_arm=False), 'L', (0.35, -0.4, -0.2), bend=0.5)
    back = lambda d=-0.28: arm(gun_low(crouch_low(0.1), 'L', down=d, back_arm=False, fwd=-1), 'R', (-0.35, -0.4, 0.2), bend=0.5)
    keys = [(0, down(True)), (5, gather), (12, arm(arm(crouch_low(0.4, 0.9), 'R', (-0.4, -0.3, 0.3), bend=0.6), 'L', (0.4, -0.3, 0.3), bend=0.6)),
            (16, arm(crouch_low(0.35), 'R', (-0.5, -0.3, 0.2), bend=0.5)), (19, front()), (20, front(0.1)), (22, front(0.1)),
            (24, back()), (25, back(0.1)), (27, back(0.1)), (33, crouch_low(0.1, 0.6)), (42, base(crouch=0.25)), (50, base())]
    return s, keys


@move('DownAttackD', 50)
def getup_d(k):
    """Face down: a push-up that snaps him into a low crouch, firing low behind (19-20) as he rises, then in front
    (25-26). Intangible 1-26."""
    s = Script()
    s.body(2)
    s.at(3); s.raw(wiring.cue(wiring.ID['TECH'], 0x6E))
    getup_hits(s, 19, 25, front_first=False, vulnerable=27)
    press = down(False, tip=1.05, height=3.4)                        # the push-up: arms straight under the shoulders
    for sd, sx in (('L', 1), ('R', -1)):
        press.aim(f'{sd}ShoulderJ', (sx * 0.3, -1, 0.3)); press.aim(f'{sd}ArmJ', (sx * 0.1, -1, 0.1))
    back = lambda d=-0.28: arm(gun_low(crouch_low(0.2), 'L', down=d, back_arm=False, fwd=-1), 'R', (-0.35, -0.4, 0.2), bend=0.5)
    front = lambda d=-0.28: arm(gun_low(crouch_low(0.3), 'R', down=d, back_arm=False), 'L', (0.35, -0.4, -0.2), bend=0.5)
    keys = [(0, down(False)), (6, press), (13, arm(crouch_low(0.5, 0.95), 'L', (0.5, -0.3, -0.2), bend=0.5)),
            (16, arm(crouch_low(0.3), 'L', (0.5, -0.3, -0.3), bend=0.5)), (19, back()), (20, back(0.1)), (22, back(0.1)),
            (25, front()), (26, front(0.1)), (28, front(0.1)), (34, crouch_low(0.1, 0.6)), (42, base(crouch=0.25)), (50, base())]
    return s, keys


# ---------------------------------------------------------------------------------------------------------------- form lab
# GENO_FORM_LAB=1 turns the taunt into a lab (director/form_lab.py): both arms held out, every weapon form on both hands
# (30 frames each), then the four hand poses and the three cap poses. Never in a shipping build.
FORM_LAB_STEP = 30


def form_lab(k):
    import rig
    s = Script()
    t = 1
    for form in rig.FORMS:
        s.at(t); s.form('R', form); s.form('L', form)
        s.hand('R', 'open' if form == 'fshot' else 'fist'); s.hand('L', 'open' if form == 'fshot' else 'fist')
        t += FORM_LAB_STEP
    s.at(t); s.form('R', 'hand'); s.form('L', 'hand')
    for pose in rig.HAND_POSE:
        s.at(t); s.hand('R', pose, 4); s.hand('L', pose, 4)
        t += FORM_LAB_STEP
    for pose in rig.CAP_POSE:
        s.at(t); s.cap(pose, 6)
        t += FORM_LAB_STEP
    s.at(t)
    hold = base()
    arm(hold, 'R', (-0.75, 0.15, 0.9)); arm(hold, 'L', (0.85, -0.1, 0.7))
    return s, [(0, base()), (6, hold), (t - 6, hold), (t, base())]


if os.environ.get('GENO_FORM_LAB'):
    FORM_LAB_FRAMES = FORM_LAB_STEP * (7 + 4 + 3) + 2
    MOVES['Appeal'] = (FORM_LAB_FRAMES, form_lab)


def build_all():
    """name -> (frames, script bytes or None, key poses)"""
    out = {}
    for name, (frames, fn) in MOVES.items():
        s, keys = fn(None)
        out[name] = (frames, s.bytes() if s else None, keys)
    return out


# ---------------------------------------------------------------------------------------------------------------- specials
# Geno's own action-table entries after the 295 common ones, in the order the decomp's ftGe_Submotion lists them
# (src/melee/ft/kinds/ftGeno/ftgeno.h). flag() marks the frame the C code spawns a projectile on.
def special(name, frames, script, keys):
    MOVES[name] = (frames, lambda k, s=script, ks=keys: (s(), ks()))


def s_beam_start():
    s = Script(); s.at(2); s.hand('R', 'open', 3); return s          # the hand opens as it draws back (the gather)


def s_beam_loop():
    s = Script(); s.form('R', 'beam'); return s                     # the barrel snaps on with the aim (every action sets it)


def s_beam_fire():
    s = Script(); s.form('R', 'beam')
    s.at(8); s.flag()                                               # the fire sound is the code's (by stars)
    s.at(22); s.form('R', 'hand'); s.hand('R', 'open', 4)
    s.at(33); s.interruptible(); return s


def s_beam_cancel():
    # the shield cancel (8 frames, Samus's and Mewtwo's length; the stars are lost): the barrel shows on the first frame
    # (the action change reset it), the charge fizzles out with the wooden rattle, and the barrel folds back into a hand
    s = Script(); s.form('R', 'beam'); s.hand('R', 'open'); s.raw(wiring.cue(wiring.ID['RATTLE'], 0x7F))
    s.at(4); s.form('R', 'hand'); s.hand('R', 'open', 3)
    return s


def s_finger(fire, iasa, snap, revert):
    def f():
        s = Script(); s.hand('R', 'open')
        s.at(snap); s.form('R', 'fshot')                            # the fingers snap into tubes at the cock
        s.at(fire); s.flag(); gs(s, 'FINGERSHOT')
        s.at(revert); s.form('R', 'hand'); s.hand('R', 'open', 3)
        s.at(iasa); s.interruptible(); return s
    return f


def s_whirl():
    # v1.2: spawns frame 12, IASA 24, so he can run in behind it
    s = Script(); s.hand('R', 'open', 2); s.at(12); s.flag(); gs(s, 'WHIRL_THROW'); s.at(24); s.interruptible(); return s


def s_fold():
    # the Star Guns power it (Michael, 2026-09-30: "it should show the star guns powering it"; was the Hand Cannons)
    s = Script(); s.at(6); gs(s, 'STARROAD_FOLD'); s.form('R', 'stargun'); s.form('L', 'stargun'); s.cap('low', 3); return s


SR_TRAIL_EVERY = 3        # geno-fx (Michael, 2026-09-30): a star from his waist every 3 frames of the flight


def s_launch():
    s = Script(); s.form('R', 'stargun'); s.form('L', 'stargun')
    s.at(1); s.hitbox(0, 'WaistN', 7, 3.6, (0, 1.2, 0), angle=50, kbg=60, bkb=45, sfx=(1, PUNCH)); gs(s, 'STARROAD_LAUNCH')
    # geno-fx: the launch's burst of no-damage stars from both hands (the guns that power the jump), and a light trail
    # (EfGeData.dat SR_BURST, SR_TRAIL: small cream-white stars, not the gold of the hitting moves' stars)
    fx(s, 'SR_BURST', 'RHandN'); fx(s, 'SR_BURST', 'LHandN'); fx(s, 'SR_TRAIL', 'WaistN')
    s.wait(4); s.clear()
    for f in range(1 + 2 * SR_TRAIL_EVERY, 20, SR_TRAIL_EVERY):
        s.at(f); fx(s, 'SR_TRAIL', 'WaistN')
    return s


def s_blast_charge():
    # down B's charge (Blast or Flash): the hands open as they go up to the sky. v1.5 (Michael, 2026-09-30): the mark shows
    # from the move's first frame (the C code places it from the stick at the press), so its sound plays there
    s = Script(); gs(s, 'BLAST_MARK'); s.at(2); s.hand('R', 'open', 3); s.hand('L', 'open', 3); return s


def s_blast_release():
    # the release: the marks already shown are armed on the first frame (the C code, on the flag: they strike 32 frames
    # on), the point snapping down; interruptible 28 frames after the release (a tap's 38)
    s = Script(); s.flag(); s.hand('R', 'point'); s.hand('L', 'open')
    s.at(29); s.interruptible(); return s


# Geno Flash's full-body cannon (DESIGN §12, ART.md "Geno Flash's cannon"; the model is projects/geno/model/geno_cannon.py,
# its motion poses_air.cannon_pose). From FLASH_CANNON_ON to FLASH_CANNON_OFF the body group shows its option 1, the
# cannon, in place of his whole body, and both arm groups show none (rig.cannon_commands); every group reverts on any
# action change (a hit, a grab, a KO), so an interrupted Flash is Geno again on the change. The swaps sit on the glow's
# pulses: the first glow (spawned on 1) peaks on 5, 11, 17 and 23 and has faded by 29 (measured: the region's mean
# brightness 0.22 bare, 0.39 at a peak, 0.29 on 26), so the cannon comes in on 23. The fireball leaves the
# cannon's muzzle (ftGe_FlashMuzzle: CannonBarrelN, rig.CANNON_MUZZLE along it) on the C's FLASH_FIREBALL frame (49),
# with the Hand Cannon's muzzle flash where the muzzle is on that frame, and the sun spawns on the flag (54). A second
# glow covers the fold back.
FLASH_CANNON_ON, FLASH_CANNON_OFF = 23, 76     # both on a pulse of the glow (measured in flash_cannon_lab)
FLASH_SHOT = 49                 # ftgeno_specials.c GE_FLASH_FIREBALL_FRAME
FLASH_GLOW_OUT = 60             # the second glow: its pulses peak on 64, 70, 76 (the fold back) and 82


def flash_cannon(s, on):
    for g, o in rig.cannon_commands(on):
        s.model(g, o)
    if not on:
        s.hand('R', 'open', 4); s.hand('L', 'open', 4)


def flash_muzzle(f=FLASH_SHOT):
    """The cannon's muzzle at Flash frame f, in TopN's frame (y up, z forward): where the script's muzzle flash goes."""
    import poses_air
    return poses_air.cannon_aim(f)[2]


def s_flash():
    s = Script(); s.at(1); gs(s, 'FLASH_TRANSFORM'); s.hand('R', 'point'); s.cap('low', 4)
    fx(s, 'FLASH_GLOW', 'TopN', (0.0, 7.0, 0.0))              # geno-fx: SMRPG's yellow glow as he becomes the cannon
    s.at(FLASH_CANNON_ON); flash_cannon(s, True); s.cap('rest', 3)
    if NORMALS_FX:
        mz = flash_muzzle()
        s.at(FLASH_SHOT); fx(s, 'N_CANNON_FLASH', 'TopN', (0.0, mz[1], mz[2]))
    s.at(54); s.flag(); gs(s, 'FLASH_FIRE')
    s.at(FLASH_GLOW_OUT); fx(s, 'FLASH_GLOW', 'TopN', (0.0, 7.0, 0.0))    # and again as it folds back into Geno
    s.at(FLASH_CANNON_OFF); flash_cannon(s, False)
    return s


def _pa(fn, *a):
    return lambda: getattr(__import__('poses_air'), fn)(*a)


SPECIALS = [
    ('SpecialNStart', 8, s_beam_start, _pa('beam_start', False)),
    ('SpecialNLoop', 20, s_beam_loop, _pa('beam_loop', False)),
    ('SpecialNEnd', 33, s_beam_fire, _pa('beam_fire', False)),
    ('SpecialAirNStart', 8, s_beam_start, _pa('beam_start', True)),
    ('SpecialAirNLoop', 20, s_beam_loop, _pa('beam_loop', True)),
    ('SpecialAirNEnd', 33, s_beam_fire, _pa('beam_fire', True)),
    ('SpecialS', 28, s_whirl, _pa('whirl', False)),
    ('SpecialAirS', 28, s_whirl, _pa('whirl', True)),
    ('SpecialHiStart', 18, s_fold, _pa('starroad_start', False)),
    ('SpecialAirHiStart', 18, s_fold, _pa('starroad_start', True)),
    ('SpecialHi', 30, s_launch, _pa('starroad_travel')),
    ('SpecialLw', 64, s_blast_charge, _pa('blast_charge', False)),   # down B's charge: the release decides (Blast), or
    ('SpecialAirLw', 64, s_blast_charge, _pa('blast_charge', True)), # the third star (Flash, grounded)
    ('SpecialLwFlash', 94, s_flash, _pa('flash')),
    ('SpecialNFinger', 34, s_finger(10, 34, 5, 22), _pa('finger', False)),
    ('SpecialAirNFinger', 24, s_finger(7, 24, 3, 15), _pa('finger', True)),
    ('SpecialNCancel', 8, s_beam_cancel, _pa('beam_cancel', False)),      # the decomp's ftGe_SM order: these two last
    ('SpecialAirNCancel', 8, s_beam_cancel, _pa('beam_cancel', True)),
    ('SpecialLwEnd', 43, s_blast_release, _pa('blast_release', False)),    # down B's release: the Blast's mark
    ('SpecialAirLwEnd', 27, s_blast_release, _pa('blast_release', True)),
]
for _name, _frames, _script, _keys in SPECIALS:
    special(_name, _frames, _script, _keys)
SPECIAL_NAMES = [n for n, *_ in SPECIALS]
# action flags (anims.build writes them into the table): 0x40000000 loops the animation (the engine's x594_b1_loop, as the
# Falls and Samus's charge hold have it). The charge's 20-frame hum repeats for as long as B is held; without it the
# animation stopped on its last frame after one pass
SPECIAL_FLAGS = {'SpecialNLoop': 0x40000000, 'SpecialAirNLoop': 0x40000000}

import states                                    # noqa: E402,F401 the ledge and floor states around the moves (animation only)
import states_defense                            # noqa: E402,F401 dodges, shield, hit reactions, grabs, dizzy (animation only)
import states_misc                               # noqa: E402,F401 the idles, the taunt, the entrance, victory; the items
