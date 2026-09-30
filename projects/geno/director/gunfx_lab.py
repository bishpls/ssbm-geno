"""Gun-move effects lab (geno-fxnormals): Geno's gun normals, and cast moves whose disjoint reads through a drawn effect,
each alone on a fixed camera, for before/after strips and for measuring how far the drawn effect reaches against the
hitboxes (fx/gunfxmeasure.py).
  GUNFX_SET   geno (default): jab, the three forward tilts, the smashes, the gun aerials, the ledge attacks, the get-ups
              sound: every gun move once for the sound audit (the aerials from a full hop, long segments for the tails),
              each slate with GENO_PULSE on its first frame, the audio's reference (sound/soundsync.py)
              cast: Samus's forward smash (a cannon blast), Ness's forward and back airs (PSI sparks), Pikachu's forward
              smash (a discharge); cast2: Mr. Game & Watch's up air (air puffs), Mewtwo's forward smash (a psychic burst),
              Marth's forward smash (the sword and its swoosh), Falco's laser
  GUNFX_COLL  0 (default) drawn, 2 the collision capsules only (hitboxes red): the same frames of a 0 and a 2 run give the
              drawn and the hit extents
  GUNFX_BG    black (default: the stage hidden, clean masks) or stage
  GUNFX_CAM   match (default: fixed, 137 back at fov 30, the game's framing of two fighters 42 apart, 14.4 px/unit at
              res 2), mid (80 back, 6 ahead: a whole gun blast close) or close (58 back, the ground attacks lab's)
  GUNFX_ONLY  a comma list of segment labels
    GUNFX_SET=geno GUNFX_COLL=0 .venv/bin/python tools/machinima/melee/build.py projects/geno gunfx_lab
Each segment opens with a two-frame magenta sync slate (fx/fxsync.py), and the plan (gunfx_lab.plan.json) carries each
segment's axis (the move's direction: +x forward, -x back, +y up, -y down, x both sides) for the measurement.
"""
import json, os, sys
from dsl import Film

SET = os.environ.get('GUNFX_SET', 'geno')
COLL = int(os.environ.get('GUNFX_COLL', '0'))
BLACK = os.environ.get('GUNFX_BG', 'black') == 'black'
CAM = os.environ.get('GUNFX_CAM', 'match')
ONLY = [x for x in os.environ.get('GUNFX_ONLY', '').split(',') if x]

LEDGE_X = -85.6
FALL, DOWN_BOUND_U, DOWN_BOUND_D = 29, 183, 191
X0 = 0.0                       # the performer's spot, facing right
FOX_JAB = int(os.environ.get('GUNFX_FOX_JAB', '17'))   # ledge_quick_hit: Fox's A, frames after Geno's (his ftilt hits 5 on)
AWAY = 70.0                    # everyone else, on the stage right of the frame (match camera: x -44 to 44)


def S(at, n, stick=(0, 0), c=(0, 0), btn=''):
    return (at, n, stick, c, btn)


SH = [S(0, 2, btn='X')]        # a short hop; the aerial 7 frames later (aerials_lab)
FH = [S(0, 6, btn='X')]        # a full hop; the aerial 9 frames later
# (label, character, frames, steps, axis, kind): kind 'ground' (stand at X0), 'left' (the same, facing left: the inputs
# mirrored), 'ledge' (drop by the left ledge, catch it, attack at +40; args pct), 'getup' (knocked down, attack at +40;
# args motion)
GENO = [
    ('jab', 'geno', 50, [S(0, 2, btn='A')], '+x', 'ground'),
    ('jab123', 'geno', 70, [S(0, 2, btn='A'), S(8, 2, btn='A'), S(16, 2, btn='A')], '+x', 'ground'),
    ('ftilt', 'geno', 45, [S(0, 4, (48, 0)), S(2, 2, (48, 0), btn='A')], '+x', 'ground'),
    ('ftilt_hi', 'geno', 45, [S(0, 4, (42, 30)), S(2, 2, (42, 30), btn='A')], '+x', 'ground'),
    ('ftilt_lo', 'geno', 45, [S(0, 4, (42, -30)), S(2, 2, (42, -30), btn='A')], '+x', 'ground'),
    ('dtilt', 'geno', 50, [S(0, 30, (0, -60)), S(8, 2, (0, -60), btn='A')], '+x', 'ground'),
    ('pummel', 'geno', 80, [S(0, 2, btn='Z'), S(40, 2, btn='A')], '+x', 'pummel'),   # Fox held; the pummel hits ~49
    ('usmash', 'geno', 55, [S(0, 3, c=(0, 80))], '+y', 'ground'),
    ('dsmash', 'geno', 55, [S(0, 3, c=(0, -80))], 'x', 'ground'),
    ('fsmash', 'geno', 60, [S(0, 3, c=(80, 0))], '+x', 'ground'),
    ('fair', 'geno', 70, SH + [S(7, 2, c=(80, 0))], '+x', 'ground'),
    ('bair', 'geno', 70, SH + [S(7, 2, c=(-80, 0))], '-x', 'ground'),
    ('uair', 'geno', 70, SH + [S(7, 2, c=(0, 80))], '+y', 'ground'),
    ('dair', 'geno', 80, FH + [S(9, 2, c=(0, -80))], '-y', 'ground'),
    ('ftilt_left', 'geno', 45, [S(0, 4, (48, 0)), S(2, 2, (48, 0), btn='A')], '-x', 'left'),     # facing left
    ('fair_left', 'geno', 70, SH + [S(7, 2, c=(80, 0))], '-x', 'left'),
    ('bair_left', 'geno', 70, SH + [S(7, 2, c=(-80, 0))], '+x', 'left'),
    ('ledge_quick', 'geno', 150, [], '+x', ('ledge', 40)),
    ('ledge_slow', 'geno', 160, [], '+x', ('ledge', 120)),
    # the weapon forms reset on an interrupt: Fox forward-tilts him in the quick ledge attack once he is tangible (21)
    # with the Hand Gun out, before his own burst (24): hit, he leaves the action and the hand returns
    ('ledge_quick_hit', 'geno', 150, [], '+x', ('ledge', 40, 'hit')),
    ('getup_u', 'geno', 120, [], 'x', ('getup', DOWN_BOUND_U)),
    ('getup_d', 'geno', 120, [], 'x', ('getup', DOWN_BOUND_D)),
]
CAST = [
    ('samus_fsmash', 'samus', 60, [S(0, 3, c=(80, 0))], '+x', 'ground'),
    ('ness_fair', 'ness', 70, SH + [S(7, 2, c=(80, 0))], '+x', 'ground'),
    ('ness_bair', 'ness', 70, SH + [S(7, 2, c=(-80, 0))], '-x', 'ground'),
    ('pikachu_fsmash', 'pikachu', 70, [S(0, 3, c=(80, 0))], '+x', 'ground'),
]
CAST2 = [
    ('gnw_uair', 'gnw', 70, SH + [S(7, 2, c=(0, 80))], '+y', 'ground'),
    ('mewtwo_fsmash', 'mewtwo', 70, [S(0, 3, c=(80, 0))], '+x', 'ground'),
    ('marth_fsmash', 'marth', 60, [S(0, 3, c=(80, 0))], '+x', 'ground'),
    ('falco_laser', 'falco', 60, [S(0, 3, btn='B')], '+x', 'ground'),
]
# the sound audit (sound/gunfit.py): every gun move once, the aerials from a full hop so no landing sound falls in their
# sound's tail, each segment long enough for the tail to die
FH9 = lambda c: FH + [S(9, 2, c=c)]
SOUND = [
    ('jab', 'geno', 50, [S(0, 2, btn='A')], '+x', 'ground'),
    ('jab123', 'geno', 70, [S(0, 2, btn='A'), S(8, 2, btn='A'), S(16, 2, btn='A')], '+x', 'ground'),
    ('ftilt', 'geno', 70, [S(0, 4, (48, 0)), S(2, 2, (48, 0), btn='A')], '+x', 'ground'),
    ('ftilt_hi', 'geno', 70, [S(0, 4, (42, 30)), S(2, 2, (42, 30), btn='A')], '+x', 'ground'),
    ('ftilt_lo', 'geno', 70, [S(0, 4, (42, -30)), S(2, 2, (42, -30), btn='A')], '+x', 'ground'),
    ('dtilt', 'geno', 60, [S(0, 30, (0, -60)), S(8, 2, (0, -60), btn='A')], '+x', 'ground'),
    ('fair_fh', 'geno', 80, FH9((80, 0)), '+x', 'ground'),
    ('bair_fh', 'geno', 80, FH9((-80, 0)), '-x', 'ground'),
    ('uair_fh', 'geno', 80, FH9((0, 80)), '+y', 'ground'),
    ('usmash', 'geno', 80, [S(0, 3, c=(0, 80))], '+y', 'ground'),
    ('dsmash', 'geno', 80, [S(0, 3, c=(0, -80))], 'x', 'ground'),
    ('ledge_quick', 'geno', 150, [], '+x', ('ledge', 40)),
    ('ledge_slow', 'geno', 170, [], '+x', ('ledge', 120)),
    ('getup_u', 'geno', 130, [], 'x', ('getup', DOWN_BOUND_U)),
    ('getup_d', 'geno', 130, [], 'x', ('getup', DOWN_BOUND_D)),
    ('bthrow', 'geno', 150, [S(0, 2, btn='Z'), S(40, 3, (-80, 0))], '-x', 'pummel'),     # Fox grabbed, thrown back
]
# round 6 (Michael's playtest): the grabs' rocket fists, the up tilt's stars, the neutral air's spinning stars
ROUND6 = [
    ('grab', 'geno', 50, [S(0, 2, btn='Z')], '+x', 'ground'),
    ('dashgrab', 'geno', 70, [S(0, 10, (80, 0)), S(10, 2, (80, 0), btn='Z')], '+x', 'ground'),
    ('grab_left', 'geno', 50, [S(0, 2, btn='Z')], '-x', 'left'),
    ('dashgrab_left', 'geno', 70, [S(0, 10, (80, 0)), S(10, 2, (80, 0), btn='Z')], '-x', 'left'),
    ('utilt', 'geno', 50, [S(0, 4, (0, 50)), S(2, 2, (0, 50), btn='A')], '+y', 'ground'),
    ('nair', 'geno', 70, SH + [S(7, 2, btn='A')], 'x', 'ground'),
]
# round 7 (the moves round): up smash's taller column, the Cannon Charge dash attack, down smash re-paced, the longer grabs
ROUND7 = [
    ('usmash', 'geno', 55, [S(0, 3, c=(0, 80))], '+y', 'ground'),
    ('dsmash', 'geno', 60, [S(0, 3, c=(0, -80))], 'x', 'ground'),
    ('dashattack', 'geno', 70, [S(0, 12, (80, 0)), S(12, 2, (80, 0), btn='A')], '+x', 'ground'),
    ('dashattack_left', 'geno', 70, [S(0, 12, (80, 0)), S(12, 2, (80, 0), btn='A')], '-x', 'left'),
] + ROUND6[:4]
SEGS = {'geno': GENO, 'cast': CAST, 'cast2': CAST2, 'sound': SOUND, 'round6': ROUND6, 'round7': ROUND7}[SET]
if ONLY:
    SEGS = [s for s in SEGS if s[0] in ONLY]
chars = []
for s in SEGS:
    if s[1] not in chars:
        chars.append(s[1])
if any(s[5] == 'pummel' or (isinstance(s[5], tuple) and 'hit' in s[5]) for s in SEGS) and 'fox' not in chars:
    chars.append('fox')                        # the pummel's held opponent
SYNC = 10
LEAD = 30
total = 70 + sum(LEAD + s[2] for s in SEGS) + 40
f = Film(len_s=total / 60)
f.setup(players=[(c, dict(x=AWAY + 5 * i, face=1)) for i, c in enumerate(chars)], seed=5, coll=COLL)


def camera(t, x, y):
    if CAM == 'close':
        f.cam(t, eye=(x, y, 58), at=(x, y, 0), fov=30, ease='cut')
    elif CAM == 'mid':
        f.cam(t, eye=(x + 6, y, 80), at=(x + 6, y, 0), fov=30, ease='cut')
    else:
        f.cam(t, eye=(x, y, 137), at=(x, y, 0), fov=30, ease='cut')


camera(0, X0, 12)
if BLACK:
    f.cue(1, 'stage', a=0); f.cue(1, 'bgcolor', a=0, b=0, c=0)
t, plan = 70 + LEAD, []
for label, char, n, steps, axis, kind in SEGS:
    port = chars.index(char)
    who = f.port(port)
    for p, c in enumerate(chars):
        if p != port and not (c == 'fox' and (kind == 'pummel' or (isinstance(kind, tuple) and 'hit' in kind))):
            f.reset(t - LEAD, p, AWAY + 5 * p, 1)
    f.percent(t - LEAD + 2, port, 0)
    if kind == 'pummel':                        # grab Fox standing in reach, pummel once
        fox = chars.index('fox')
        f.reset(t - LEAD, port, X0, 1); f.reset(t - LEAD, fox, X0 + 10, -1); f.percent(t - LEAD + 2, fox, 60)
        camera(t - LEAD, X0 + 4, 12)
        for at, k, stick, c, btn in steps:
            who.hold(t + at, k, stick=stick, c=c, btn=btn)
    elif kind in ('ground', 'left'):            # left: the same inputs mirrored, facing left
        face = -1 if kind == 'left' else 1
        f.reset(t - LEAD, port, X0, face)
        camera(t - LEAD, X0 + (4 if axis in ('+x',) else -4 if axis == '-x' else 0), 12 if axis != '+y' else 16)
        for at, k, stick, c, btn in steps:
            who.hold(t + at, k, stick=stick, c=c, btn=btn, dir=face)
        if label.startswith('dashattack'):          # the dash carries him out of a fixed frame: follow him
            d = {'close': 58, 'mid': 80}.get(CAM, 137)
            f.cam(t + 2, eye=(4 * face, 10, d), at=(4 * face, 10, 0), fov=30, ease='cut', track='p0')
    elif kind[0] == 'ledge':
        # the pummel/ledge lab's staging: airborne first, set beside the left ledge falling, catch it, attack at +40
        f.reset(t - LEAD, port, LEDGE_X + 10, -1)
        f.percent(t - LEAD + 4, port, kind[1])
        who.hold(t - LEAD + 6, 3, btn='X')
        f.setpos(t, port, LEDGE_X - 5.0, 4.0); f.face(t, port, 1); f.cue(t, 'motion', port, FALL)
        who.hold(t + 40, 2, btn='A')
        camera(t - LEAD, LEDGE_X + 14, 6)
        if 'hit' in kind:                       # Fox, 17 in from the corner facing him, forward-tilts to land on ~23
            fox = chars.index('fox')
            f.reset(t - LEAD, fox, LEDGE_X + 17.0, -1); f.percent(t - LEAD + 2, fox, 0)
            f.port(fox).hold(t + 40 + FOX_JAB - 2, 4, stick=(48, 0), dir=-1)
            f.port(fox).hold(t + 40 + FOX_JAB, 2, stick=(48, 0), btn='A', dir=-1)
            f.status(t + 40 + 30, port)
    else:
        f.reset(t - LEAD, port, X0, 1)
        f.cue(t, 'motion', port, kind[1])
        who.hold(t + 40, 2, btn='A')
        camera(t - LEAD, X0, 10)
    # the sync slate: the stage hidden on magenta for two frames, SYNC frames before the segment
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=0 if BLACK else 1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    if SET == 'sound':                          # the audio's reference: a sharp pulse (550000) on the slate's first frame
        f.sfx(t - SYNC, 550000)
    who.trace(t - 2, t + n - 1)
    f.mark(t, len(plan), label)
    plan.append(dict(label=label, char=char, port=port, start=t, frames=n, sync=t - SYNC, axis=axis,
                     kind=kind if isinstance(kind, str) else kind[0], cam=CAM))
    t += n + LEAD
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
