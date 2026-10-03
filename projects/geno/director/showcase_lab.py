"""Showcase lab: Geno's whole moveset for the demo reel (labs/showcase_reel.py), on Final Destination with Fox as the target
where a move needs one, the hitbox display off, a steady side camera per move (tracking him where he travels), sound on and
music off. Every segment opens with a two-frame magenta sync slate and a click (the SFX cue) SYNC frames before its start,
so the reel lines up each segment's images and audio on its own anchor (the dump drops images on heavy frames).
    SHOW=main  SHOW_PART=a|b|c .venv/bin/python tools/machinima/melee/build.py projects/geno showcase_lab
        the moveset in three captures (parts of the SEGS list, so two can run while the third builds)
    SHOW=entry   the match start: both entrances (the director's entry flag)
    SHOW=costumes SHOW_COLORS=0,1,2,3   Genos in those costumes standing in a row (a line-up; two captures for six)
The results screens (the victory poses and the losing clap) are victory_lab's; Kirby's Geno hat is kirby_hat_lab's.
The plan (build/showcase_lab.plan.json) lists each segment: its label, start t (the first input), sync frame, and clips:
(caption, from, to) in frames from t, to None for "until he is idle again" (the reel reads the MS log).
"""
import json, os, sys
from dsl import Film

SHOW = os.environ.get('SHOW', 'main')
PART = os.environ.get('SHOW_PART', '')
GENO, FOX = 0, 1
SYNC = 10
CLICK = 173                    # the menu click the director's slate plays (lbAudioAx_80024030(1): sound 0xAD)
LEDGE = -85.6
FALL, DOWN_BOUND_U, DOWN_BOUND_D = 29, 183, 191
AWAY = 80.0                    # Fox's spot when a move needs no target (out of frame)

SEGS = []


def seg(label, n, clips, gx=-10.0, gface=1, fx=None, fface=None, fox_pct=0, g=(), fox=(), cam=(0.0, 11.0, 80.0, None),
        pre=None, away=AWAY, follow=None):
    """A segment of n frames. g, fox: the inputs, (at, frames, stick, cstick, buttons, trigger), at from t (the start).
    fx: Fox's x (None: out of frame, at `away`). cam: (x, y, dist, track): the camera's target point (an offset from the tracked
    fighter with track 'p0') and distance, side on. follow: the camera's height keyed along his jump, {frame: y} from t
    (a scripted follow: the tracker lags a jump). pre(f, t): extra cues (placing him in the air, a motion)."""
    SEGS.append(dict(label=label, n=n, clips=clips, gx=gx, gface=gface, fx=fx if fx is not None else away, fface=fface,
                     fox_pct=fox_pct, g=list(g), fox=list(fox), cam=cam, pre=pre, follow=follow))


# his jumps' heights (measured in the showcase captures: POS every 6 frames from the jump input), for the camera's follow:
# the frame's centre rides 8 above his feet, never below 11 (the floor stays in frame)
FH_PATH = {0: 0.0, 6: 2.8, 12: 16.5, 18: 25.6, 24: 30.0, 30: 29.8, 36: 24.8, 42: 15.2, 48: 1.7, 54: 0.0}
DJ_PATH = {0: 0.0, 6: 2.8, 12: 16.5, 18: 25.6, 24: 33.9, 30: 45.3, 36: 52.0, 42: 54.0, 48: 51.4, 54: 44.0, 60: 32.0,
           66: 18.2, 72: 4.4, 78: 0.0}
FOLLOW = lambda path: {k: max(11.0, y + 8.0) for k, y in path.items()}


def S(at, n, stick=(0, 0), c=(0, 0), btn='', trig=0):
    return (at, n, stick, c, btn, trig)


# the ground normals' spacing (Fox's x less Geno's; normals_lab, angles_lab): each hits a standing Fox
NEAR = dict(jab=7, ftilt=9, utilt=4, dtilt=7, fsmash=10, usmash=3, dsmash=7)
TILT = lambda st: [S(0, 4, st), S(2, 2, st, btn='A')]


def cam_pair(gx, fx, y=11.0, d=80.0):
    return ((gx + fx) / 2.0, y, d, None)


# ---- the idle and movement
seg('wait1', 110, [('Idle', 0, 96)], gx=0, cam=(0, 10.5, 58, None))
seg('wait2', 175, [('Idle 2', 0, 120)], gx=0, cam=(0, 10.5, 58, None), pre=lambda f, t: f.anim(t, GENO, 3))
seg('walk', 100, [('Walk', 0, 76)], gx=-35, g=[S(0, 64, (52, 0))], cam=(6, 11, 72, 'p0'), away=-AWAY)
seg('dash', 70, [('Dash', 0, 44)], gx=-35, g=[S(0, 9, (80, 0))], cam=(8, 11, 76, 'p0'), away=-AWAY)
seg('run', 115, [('Run', 0, 92)], gx=-55, g=[S(0, 62, (80, 0))], cam=(10, 11, 84, 'p0'), away=-AWAY)
seg('crouch', 90, [('Crouch', 0, 70)], gx=0, g=[S(0, 50, (0, -80))], cam=(0, 9, 58, None))
seg('shorthop', 80, [('Short hop', -2, None)], gx=0, g=[S(0, 2, btn='X')], cam=(0, 14, 76, None))
seg('fullhop', 100, [('Full hop', -2, None)], gx=0, g=[S(0, 8, btn='X')], cam=(0, 11, 96, None), follow=FOLLOW(FH_PATH))
seg('doublejump', 130, [('Double jump', -2, None)], gx=0, g=[S(0, 6, btn='X'), S(22, 3, btn='X')], cam=(0, 11, 100, None), follow=FOLLOW(DJ_PATH))

# ---- ground attacks (Fox at 0%, standing in range)
def ground(label, caption, key, g, n=90, gx=-10.0, pct=0, clip_from=-3, d=78.0, y=11.0):
    fx = gx + NEAR[key]
    seg(label, n, [(caption, clip_from, None)], gx=gx, fx=fx, fox_pct=pct, g=g, cam=cam_pair(gx, fx + 6, y, d))


ground('jab', 'Jab 1, 2, 3', 'jab', [S(0, 2, btn='A'), S(8, 2, btn='A'), S(16, 2, btn='A')], n=90)
ground('ftilt_hi', 'Forward tilt · up', 'ftilt', TILT((44, 26)))
ground('ftilt', 'Forward tilt', 'ftilt', TILT((48, 0)))
ground('ftilt_lw', 'Forward tilt · down', 'ftilt', TILT((44, -26)))
ground('utilt', 'Up tilt', 'utilt', TILT((0, 50)))
ground('dtilt', 'Down tilt', 'dtilt', [S(0, 8, (0, -60)), S(5, 2, (0, -60), btn='A')])
seg('dash_attack', 100, [('Dash attack', -2, None)], gx=-40, fx=-6, g=[S(0, 12, (80, 0)), S(12, 2, (80, 0), btn='A')],
    cam=(-18, 11, 92, None))
ground('fsmash_hi', 'Forward smash · up', 'fsmash', [S(0, 2, (72, 42), btn='A')], n=100, d=90)
ground('fsmash', 'Forward smash · charged', 'fsmash', [S(0, 2, (80, 0), btn='A'), S(2, 44, btn='A')], n=150, d=90)
ground('fsmash_lw', 'Forward smash · down', 'fsmash', [S(0, 2, (72, -42), btn='A')], n=100, d=90)
ground('usmash', 'Up smash', 'usmash', [S(0, 3, c=(0, 80))], n=100, d=90, y=15)
ground('dsmash', 'Down smash', 'dsmash', [S(0, 3, c=(0, -80))], n=100, d=90)

# ---- aerials (short hops onto a standing Fox; up air meets him jumping; down air from a full hop over him)
def aerial(label, caption, gx, gface, fx, g, fox=(), n=100, y=13.0, d=95.0):
    seg(label, n, [(caption, -2, None)], gx=gx, gface=gface, fx=fx, g=g, fox=fox, cam=cam_pair(gx, fx, y, d))


aerial('nair', 'Neutral air', -15, 1, -10, [S(0, 2, btn='X'), S(18, 2, btn='A')])
aerial('fair', 'Forward air', -26, 1, -10, [S(0, 2, btn='X'), S(12, 2, c=(80, 0))])
aerial('bair', 'Back air', -26, -1, -10, [S(0, 2, btn='X'), S(12, 2, c=(-80, 0))])     # sticks are facing-relative: back
aerial('uair', 'Up air', -11, 1, -10, [S(0, 2, btn='X'), S(8, 2, c=(0, 80))], fox=[S(2, 6, btn='X')], y=16, d=110)
seg('dair', 120, [('Down air · rocket fist', 26, None)], gx=-11, fx=-10, g=[S(0, 6, btn='X'), S(33, 2, c=(0, -80))],
    cam=(-10.5, 20, 116, None))

# ---- specials (v1.5's timings, as specials_v15_lab holds them: the Beam's stars at 40, 60, 80, the timed release on the third;
# the Flash at the third star, frame 61)
seg('finger', 80, [('Neutral B · Finger Shot', -2, None)], gx=-40, fx=20, g=[S(0, 2, btn='B')], cam=(-10, 12, 120, None))
seg('beam1', 110, [('Neutral B · Geno Beam, 1 star', -2, None)], gx=-40, fx=20, g=[S(0, 45, btn='B')], cam=(-10, 12, 120, None))
seg('beam2', 130, [('Geno Beam · 2 stars', -2, None)], gx=-40, fx=20, g=[S(0, 65, btn='B')], cam=(-10, 12, 120, None))
seg('beam3', 140, [('Geno Beam · 3 stars', -2, None)], gx=-40, fx=20, g=[S(0, 110, btn='B')], cam=(-10, 12, 120, None))
seg('beam_timed', 150, [('Geno Beam · timed release', -2, None)], gx=-40, fx=20, fox_pct=60, g=[S(0, 79, btn='B')],
    cam=(-10, 12, 120, None))
seg('whirl', 150, [('Side B · Geno Whirl', -2, 80)], gx=-40, fx=5, g=[S(0, 3, (60, 0), btn='B')], cam=(-15, 12, 110, None))
seg('whirl_shield', 175, [('Geno Whirl · on a shield', -2, 132)], gx=-40, fx=-5, g=[S(0, 3, (60, 0), btn='B')],
    fox=[S(-4, 110, trig=140)], cam=(-20, 12, 100, None))
seg('starroad', 150, [('Up B · Star Road', -2, None)], gx=-10, g=[S(0, 3, (0, 80), btn='B'), S(4, 14, (0, 80))],
    cam=(0, 14, 130, 'p0'))
seg('starroad_angle', 150, [('Star Road · angled', -2, None)], gx=-45, g=[S(0, 3, (0, 80), btn='B'), S(4, 14, (60, 60))],
    cam=(6, 10, 130, 'p0'), away=-AWAY)
seg('blast', 110, [('Down B · Geno Blast', -2, 70)], gx=-35, fx=15, fox_pct=30, g=[S(0, 3, (0, -80), btn='B')],
    cam=(-10, 22, 150, None))
seg('blast_wide', 140, [('Geno Blast · widened', -2, 98)], gx=-35, fx=15, fox_pct=30, g=[S(0, 30, (0, -80), btn='B')],
    cam=(-10, 22, 150, None))
seg('flash', 230, [('Down B, held · Geno Flash', -2, 206)], gx=-30, fx=0, fox_pct=30, g=[S(0, 75, (0, -80), btn='B')],
    cam=(-8, 22, 150, None))

# ---- grab, pummel, throws (every grab ends in a throw: a reset mid-grab leaves the engine's grab link stale)
seg('grab_fthrow', 190, [('Grab', -3, 40), ('Pummel', 40, 112), ('Forward throw', 112, None)], gx=-10, fx=-3, fox_pct=20,
    g=[S(0, 2, btn='Z'), S(50, 2, btn='A'), S(80, 2, btn='A'), S(114, 3, (80, 0))], cam=(-5, 11, 84, None))
seg('dashgrab_bthrow', 150, [('Dash grab', -2, 44), ('Back throw', 44, None)], gx=-40, fx=-6, fox_pct=20,
    g=[S(0, 10, (80, 0)), S(10, 2, (80, 0), btn='Z'), S(58, 3, (-80, 0))], cam=(-18, 11, 92, None))
seg('uthrow', 150, [('Up throw', 38, None)], gx=-10, fx=-3, fox_pct=20, g=[S(0, 2, btn='Z'), S(48, 3, (0, 80))],
    cam=(-6, 22, 110, None))
seg('dthrow', 140, [('Down throw', 38, None)], gx=-10, fx=-3, fox_pct=20, g=[S(0, 2, btn='Z'), S(48, 3, (0, -80))],
    cam=(-6, 11, 84, None))

# ---- the ledge and the floor
def on_ledge(f, t, pct):
    f.percent(t - 14, GENO, pct)                      # after the segment's own reset of his percent (t - 22)
    f.port(GENO).hold(t - 20, 3, btn='X')             # airborne first: a grounded fighter teleported offstage snaps back
    f.setpos(t - 12, GENO, LEDGE - 5.0, 4.0); f.face(t - 12, GENO, 1); f.cue(t - 12, 'motion', GENO, FALL)


seg('ledge_quick', 130, [('Ledge attack', 24, None)], gx=LEDGE + 10, gface=-1, fx=LEDGE + 16, fox_pct=0,
    g=[S(40, 2, btn='A')], cam=(LEDGE + 16, 6, 80, None), pre=lambda f, t: on_ledge(f, t, 40))
seg('ledge_slow', 150, [('Ledge attack · 100% or more', 24, None)], gx=LEDGE + 10, gface=-1, fx=LEDGE + 16, fox_pct=0,
    g=[S(40, 2, btn='A')], cam=(LEDGE + 16, 6, 80, None), pre=lambda f, t: on_ledge(f, t, 120))
seg('getup_u', 130, [('Get-up attack · face up', 26, None)], gx=0, fx=13, g=[S(40, 2, btn='A')], cam=(2, 8, 72, None),
    pre=lambda f, t: f.cue(t, 'motion', GENO, DOWN_BOUND_U))
seg('getup_d', 130, [('Get-up attack · face down', 26, None)], gx=0, fx=13, g=[S(40, 2, btn='A')], cam=(2, 8, 72, None),
    pre=lambda f, t: f.cue(t, 'motion', GENO, DOWN_BOUND_D))

# ---- defence and the taunt
seg('shield', 80, [('Shield', -2, 56)], gx=0, g=[S(0, 50, trig=140)], cam=(0, 10, 62, None))
seg('roll_f', 80, [('Roll · forward', -2, None)], gx=-15, g=[S(0, 20, trig=140), S(4, 3, (80, 0), trig=140)],
    cam=(0, 10, 76, None))
seg('roll_b', 80, [('Roll · back', -2, None)], gx=15, g=[S(0, 20, trig=140), S(4, 3, (-80, 0), trig=140)],
    cam=(0, 10, 76, None))
seg('spotdodge', 70, [('Spot dodge', -2, None)], gx=0, g=[S(0, 20, trig=140), S(4, 3, (0, -80), trig=140)],
    cam=(0, 10, 62, None))
seg('airdodge', 110, [('Air dodge', -2, None)], gx=0, g=[S(0, 3, btn='X'), S(12, 3, trig=140)], cam=(0, 16, 84, None))
seg('taunt', 160, [('Taunt', -2, None)], gx=0, g=[S(0, 2, btn='DU')], cam=(0, 10.5, 58, None))

PARTS = {'a': (0, 26), 'b': (26, 42), 'c': (42, len(SEGS))}      # the moves to the aerials; the specials and throws; the rest


def main():
    if SHOW == 'entry':
        f = Film(len_s=6.5)
        f.setup(players=[('geno', dict(x=-12, face=1)), ('fox', dict(x=AWAY, face=-1))], seed=3, entry=True)
        f.orbit(0, at=(-60, 13, 0), dist=66, yaw=0, pitch=0, fov=30, ease='cut')     # the entrance plays at the spawn, x -60
        f.emit(sys.argv[1])
        json.dump([dict(label='entry', start=0, frames=330, clips=[['Entrance', 4, 108]])],
                  open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
        return
    if SHOW == 'costumes':
        cols = [int(c) for c in os.environ.get('SHOW_COLORS', '0,1,2,3').split(',')]
        X = [-27, -9, 9, 27][:len(cols)]
        f = Film(len_s=5.0)
        f.setup(players=[('geno', dict(x=x, face=1, color=c)) for x, c in zip(X, cols)], seed=5)
        f.orbit(0, at=(0, 11, 0), dist=92, yaw=0, pitch=0, fov=30, ease='cut')
        for i, x in enumerate(X):                  # the match's spawn points aren't the setup's x: stand them where wanted
            f.reset(20, i, x, 1)
        f.emit(sys.argv[1])
        json.dump([dict(label='costumes', start=0, frames=280, colors=cols, x=X)],
                  open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
        return
    a, b = PARTS.get(PART, (0, len(SEGS)))
    segs = SEGS[a:b]
    t, plan = 60, []
    total = t + sum(s['n'] for s in segs) + 40
    f = Film(len_s=total / 60)
    f.setup(players=[('geno', dict(x=-10, face=1)), ('fox', dict(x=AWAY, face=-1))], seed=3, coll=0)
    geno, fox = f.port(GENO), f.port(FOX)
    for i, sg in enumerate(segs):
        fx = sg['fx']
        fface = sg['fface'] or (-1 if fx > sg['gx'] else 1)
        f.reset(t - 24, GENO, sg['gx'], sg['gface']); f.reset(t - 24, FOX, fx, fface)
        f.percent(t - 22, GENO, 0); f.percent(t - 22, FOX, sg['fox_pct'])
        cx, cy, d, track = sg['cam']
        f.orbit(t - 12, at=(cx, cy, 0), dist=d, yaw=0, pitch=0, fov=30, ease='cut', track=track)
        if sg['follow']:
            ks = sorted(sg['follow'])
            for k in ks:
                f.orbit(t + k + 3, at=(cx, sg['follow'][k], 0), dist=d, yaw=0, pitch=0, fov=30,
                        ease='cut' if k == ks[-1] else 'linear')
        f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
        f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
        f.sfx(t - SYNC, CLICK)
        if sg['pre']:
            sg['pre'](f, t)
        for at, n, stick, c, btn, trig in sg['g']:
            geno.hold(t + at, n, stick=stick, c=c, btn=btn, trig=trig, dir=sg['gface'])
        for at, n, stick, c, btn, trig in sg['fox']:
            fox.hold(t + at, n, stick=stick, c=c, btn=btn, trig=trig, dir=fface)
        geno.trace(t - 2, t + sg['n'] - 26); fox.trace(t - 2, t + sg['n'] - 26)
        f.mark(t, i, sg['label'])
        plan.append(dict(label=sg['label'], start=t, frames=sg['n'] - 24, sync=t - SYNC, clips=sg['clips']))
        t += sg['n']
    f.emit(sys.argv[1])
    json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)


main()
