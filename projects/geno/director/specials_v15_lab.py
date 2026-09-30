"""Specials v1.5 lab (Michael's playtest, 2026-09-30): each group proves one fix in game, every case on a sync slate.
    SP_GROUP=beam       the Finger Shot window (B held 5, 12, 19 frames: Finger Shot; 21: the Beam), the stars at 40, 60,
                        80 (held 45, 65, 110: one, two, three stars, the last firing itself at 84), a timed release on
                        the third star (held 79), an aerial tap; then Kirby copies Geno and does the same (KBGE lines).
                        Logged: GENO CHARGE sound (it must start at frame 20, never on a Finger Shot), STAR, TIMED, MS
    SP_GROUP=whirl      no boomerang: the Whirl thrown up, straight and down (stick bent), side B pressed again at 14,
                        40, 70 and 100 frames; the disc's path every frame (ITEMS) and Geno's states (the re-press must
                        play nothing: no SpecialS); also Geno running during the re-press
    SP_GROUP=norecall   no recall at all (Michael, 2026-09-30): side B pressed in the travel, the grind, the hover (also
                        in the air), the spin-down after the hit, mashed through a whole throw, and just after and 37
                        frames after a despawn (the lockout); ITEMS and Geno's states show no return and no SpecialS
    SP_GROUP=absorb     Ness's PSI Magnet (Michael: bullets physical, the rest energy): the Finger Shot and the down throw's
                        shots hit him; every Beam level and the timed release, the up throw's stars, the Whirl, the Blast
                        (one and three columns) and the Flash are absorbed (the throw shots fired by the director's shoot)
    SP_GROUP=bmark      the forgiving mark: taps, steering forward and back, the deadzone, a tap then the stick, star 2
                        with the stick back and forward (all three marks), in the air, over the edge
    SP_GROUP=timed      the timed hit on SP_CHAR (fox, falco, captain) at 0 and 50%: thrown from 30 away, side B again
                        on each of several frames before contact; then one real follow-up (Geno dashes in behind it and
                        up-airs). Logged: GENO WHIRL crit, HIT/IHIT, the victim's POS and states
    SP_GROUP=link       Link's boomerang, tilt and smash input (the range to match), and Geno's Whirl, traced (ITEMS)
    SP_GROUP=blast      down B's marks: pressed with the stick back, neutral and forward (the mark at the press), a tap,
                        held past star 2 (the side marks) and to star 3 (Flash: the marks go), in the air; offstage and
                        high casts (the mark's placement); shield and roll held through every case (no cancel)
    SP_GROUP=meteor     the offstage column on SP_CHAR (fox, falco, marth) at 30/60/90%: where the spike leaves them
    SP_GROUP=dropb      the aerial down B's fall: pressed rising, at the apex, falling, and placed 104 up
    SP_GROUP=recover    the cast's straight-up recoveries (SP_CHAR) from the Star Road drop, for comparison
    SP_GROUP=starroad   drop from the ledge and Star Road straight up after 4-40 frames of fall: the ledge caught or not
    .venv/bin/python tools/machinima/melee/build.py projects/geno specials_v15_lab
"""
import json, os, sys
from dsl import Film

G = os.environ.get('SP_GROUP', 'beam')
CHAR = os.environ.get('SP_CHAR', 'fox')
GENO, OPP = 0, 1
SYNC = 10
LEDGE = 85.6
FALL, CLIFF_WAIT = 29, 253
SEGS = []


def seg(label, n, geno_x=-20.0, geno_face=1, opp_x=70.0, opp_face=-1, opp_pct=0, g=(), o=(), cam=(0, 12, 110),
        pre=None, items=0, feet=False, status=0):
    SEGS.append(dict(label=label, n=n, gx=geno_x, gf=geno_face, ox=opp_x, of=opp_face, pct=opp_pct, g=list(g), o=list(o),
                     cam=cam, pre=pre, items=items, status=status))


def S(at, n, stick=(0, 0), c=(0, 0), btn='', trig=0):
    return (at, n, stick, c, btn, trig)


players = [('geno', dict(x=-20, face=1)), (CHAR if G in ('timed', 'meteor') else 'fox', dict(x=70, face=-1))]
stage = 'final_destination'

if G == 'beam':
    for h in (5, 12, 19, 21, 45, 65, 79, 110):
        seg(f'hold{h}', 150, g=[S(0, h, btn='B')], opp_x=30)
    seg('air_tap15', 110, g=[S(0, 3, btn='X'), S(8, 15, btn='B')], opp_x=30)
    players = [('geno', dict(x=-20, face=1)), ('kirby', dict(x=70, face=-1))]
    # Kirby copies Geno (the timed_lab swallow), then the same holds
    seg('kb_copy', 200, geno_x=6, geno_face=-1, opp_x=-12, opp_face=1, o=[S(0, 35, btn='B'), S(62, 6, (0, -80))])
    for h in (15, 45, 110):
        seg(f'kb_hold{h}', 150, geno_x=30, geno_face=-1, opp_x=-20, opp_face=1, o=[S(0, h, btn='B')])
elif G == 'whirl':
    for bend, name in (((60, 60), 'up'), ((60, 0), 'straight'), ((60, -60), 'down')):
        for re in (14, 40, 70, 100):
            seg(f'{name}_re{re}', 190, geno_x=-40, g=[S(0, 3, bend, btn='B'), S(re, 3, (60, 0), btn='B')], items=170)
    seg('run_re', 190, geno_x=-60, g=[S(0, 3, (60, 0), btn='B'), S(26, 40, (80, 0)), S(40, 3, (80, 0), btn='B')], items=170)
elif G == 'norecall':
    # side B at every phase with the Whirl out: it never comes back and nothing plays (the press is the timed-hit check
    # in flight, nothing otherwise); the timed hit still lands; 30 frames of lockout after every despawn
    B = lambda at: S(at, 3, (60, 0), btn='B')
    AWAY = dict(geno_x=-40, opp_x=-90, opp_face=1)             # Fox behind him: the throw hits nothing (travel, hover)
    seg('travel_hover', 200, **AWAY, g=[B(0), B(20), B(50), B(100), B(125)], items=180)
    seg('air_hover', 200, **AWAY, g=[B(0), S(95, 3, btn='X'), B(102)], items=180)
    seg('mash_all', 200, **AWAY, g=[B(0)] + [B(k) for k in range(6, 136, 6)], items=180)
    seg('grind_hover', 200, geno_x=-30, opp_x=5, o=[S(0, 110, trig=140)], g=[B(0), B(40), B(60), B(95)], items=180)
    seg('spin_down', 150, geno_x=-30, opp_x=0, g=[B(0), B(36), B(44)], cam=(-5, 18, 110), items=130)
    seg('timed_spin', 150, geno_x=-30, opp_x=0, g=[B(0), B(24), B(36)], cam=(-5, 18, 110), items=130)
    seg('mash_hit', 150, geno_x=-30, opp_x=0, g=[B(0)] + [B(k) for k in range(6, 60, 5)], cam=(-5, 18, 110), items=130)
    seg('lockout', 260, **AWAY, g=[B(0), B(145), B(172)], items=240)
elif G == 'absorb':
    # Michael (2026-09-30): bullets are physical, the rest energy. Ness (30%) holds PSI Magnet from frame 0; each of
    # Geno's projectiles meets it. Absorbed: no IHIT, the item gone at the magnet, Ness's percent down (STATUS every 5)
    players = [('geno', dict(x=-20, face=1)), ('ness', dict(x=40, face=-1))]
    MAGNET = [S(0, 3, (0, -80), btn='B'), S(3, 160, btn='B')]
    FINGER, BEAM = 237, 238                                  # It_Kind_Geno_Finger, It_Kind_Geno_Beam (ITEMS kinds)

    def shoot(kind, state, speed):
        return lambda f, t: f.shoot(t + 30, GENO, kind, state, speed)
    for label, ox, g, pre in (
            ('finger', 20, [S(30, 3, btn='B')], None),
            ('finger_cue', 20, [], shoot(FINGER, 0, 4.0)),
            ('dthrow_shot', 20, [], shoot(FINGER, 1, 4.0)),
            ('beam1', 50, [S(10, 45, btn='B')], None),
            ('beam2', 50, [S(10, 65, btn='B')], None),
            ('beam3', 50, [S(10, 110, btn='B')], None),
            ('beam_timed', 50, [S(10, 79, btn='B')], None),
            ('upthrow_star', 30, [], shoot(BEAM, 3, 6.5)),
            ('whirl', 25, [S(20, 3, (60, 0), btn='B')], None),
            ('blast', 30, [S(20, 3, (0, -80), btn='B')], None),
            ('blast_star2', 30, [S(20, 30, (0, -80), btn='B')], None),
            ('flash', 10, [S(20, 75, (0, -80), btn='B')], None)):
        seg(label, 200, opp_x=ox, opp_pct=30, g=g, o=MAGNET, pre=pre, items=160, status=5)
elif G == 'bmark':
    # the forgiving mark: the stick read every frame until star 2 (frame 25) or B let go, the one mark sliding between
    # 36, 50 and 64 ahead; star 2 marks all three whatever the stick. Fox stands well away (x 120: out of every column)
    D = (0, -80)
    far = dict(opp_x=120, items=150, cam=(22, 14, 150))                 # the camera frames 36-64 ahead of him
    for st, name in (((-36, -70), 'tap_back'), (D, 'tap_neutral'), ((36, -70), 'tap_fwd')):
        seg(name, 170, g=[S(0, 3, st, btn='B')], **far)
    seg('steer_fwd', 170, g=[S(0, 3, D, btn='B'), S(3, 5, btn='B'), S(8, 12, (80, 0), btn='B')], **far)
    seg('steer_back', 170, g=[S(0, 3, (36, -70), btn='B'), S(3, 4, btn='B'), S(7, 13, (-80, 0), btn='B')], **far)
    seg('steer_back_mid', 170, g=[S(0, 3, D, btn='B'), S(3, 6, (-80, 0), btn='B'), S(9, 11, btn='B')], **far)
    # the deadzone: 0.375 keeps mid; 0.56 goes far; back to 0.375 stays far; 0.19 returns to mid
    seg('deadzone', 170, g=[S(0, 3, D, btn='B'), S(3, 5, (30, 0), btn='B'), S(8, 4, (45, 0), btn='B'),
                            S(12, 5, (30, 0), btn='B'), S(17, 5, (15, 0), btn='B')], **far)
    seg('tap_then_fwd', 170, g=[S(0, 3, D, btn='B'), S(3, 20, (80, 0))], **far)        # B let go at 3: locked at mid
    seg('star2_back', 190, g=[S(0, 3, (-36, -70), btn='B'), S(3, 27, (-80, 0), btn='B')], **far)
    seg('star2_fwd', 190, g=[S(0, 3, (36, -70), btn='B'), S(3, 27, (80, 0), btn='B'), S(30, 20, (-80, 0))], **far)
    seg('air_steer', 190, g=[S(0, 3, btn='X'), S(10, 3, D, btn='B'), S(13, 10, (80, 0), btn='B')], **far)
    # off the right edge: 36 ahead is on the stage, 50 and 64 over the void (the stage's plane, the void look)
    seg('edge_steer', 170, geno_x=LEDGE - 40, g=[S(0, 3, (-36, -70), btn='B'), S(3, 6, (-80, 0), btn='B'),
                                                  S(9, 5, btn='B'), S(14, 8, (80, 0), btn='B')], opp_x=-60, items=150,
        cam=(80, 10, 150))
elif G == 'timed':
    FOLLOW = {'uair': [S(44, 6, btn='X'), S(52, 2, c=(0, 80))], 'nair': [S(46, 2, btn='X'), S(52, 2, btn='A')],
              'utilt': [S(48, 4, (0, 50)), S(50, 2, (0, 50), btn='A')], 'fsmash_up': [S(48, 2, (72, 42), btn='A')]}
    for pct in (0, 50):
        for p in (22, 24, 26):                         # the re-press, frames after the throw (contact ~ +27)
            seg(f'p{pct}_re{p}', 150, geno_x=-30, opp_x=0, opp_pct=pct, g=[S(0, 3, (60, 0), btn='B'), S(p, 2, (60, 0), btn='B')],
                cam=(-5, 18, 110))
        # the follow-ups: he dashes in behind it from IASA, re-presses at 24, then each option
        for name, fu in FOLLOW.items():
            seg(f'p{pct}_{name}', 160, geno_x=-30, opp_x=0, opp_pct=pct,
                g=[S(0, 3, (60, 0), btn='B'), S(24, 20, (80, 0)), S(24, 2, (80, 0), btn='B')] + fu, cam=(-5, 18, 110))
elif G == 'link':
    players = [('link', dict(x=-40, face=1)), ('geno', dict(x=-40, face=1))]
    seg('link_tilt', 150, geno_x=-60, opp_x=-80, opp_face=1, g=[S(0, 4, (50, 0)), S(2, 2, (50, 0), btn='B')], items=140)
    seg('link_smash', 150, geno_x=-60, opp_x=-80, opp_face=1, g=[S(0, 3, (80, 0), btn='B')], items=140)
    seg('geno_whirl', 170, geno_x=60, geno_face=-1, opp_x=-60, opp_face=1, o=[S(0, 3, (60, 0), btn='B')], items=160)
elif G == 'blast':
    # the stick at the press: down B needs y below -0.55 and |x| under 0.6 (past 0.6 it's side B); the mark reads x past 0.25
    for st, name in (((-36, -70), 'back'), ((0, -80), 'neutral'), ((36, -70), 'fwd')):
        seg(f'tap_{name}', 120, g=[S(0, 3, st, btn='B')], opp_x=35)
    seg('hold30', 140, g=[S(0, 30, (0, -80), btn='B')], opp_x=35)
    seg('flash', 210, g=[S(0, 75, (0, -80), btn='B')], opp_x=15)
    seg('air_hold40', 150, g=[S(0, 6, btn='X'), S(10, 40, (0, -80), btn='B')], opp_x=35)
    # cancels: shield or roll held (with B) through the charge, the release and the Flash
    seg('shield_tap', 120, g=[S(0, 1, (0, -80), btn='B'), S(1, 2, (0, -80), btn='B', trig=140), S(3, 100, trig=140)], opp_x=35)
    seg('shield_hold30', 140, g=[S(0, 1, (0, -80), btn='B'), S(1, 29, (0, -80), btn='B', trig=140), S(30, 90, trig=140)], opp_x=35)
    seg('roll_hold30', 140, g=[S(0, 1, (0, -80), btn='B'), S(1, 29, (80, -80), btn='B', trig=140), S(30, 90, (80, 0), trig=140)], opp_x=35)
    seg('shield_flash', 210, g=[S(0, 1, (0, -80), btn='B'), S(1, 74, (0, -80), btn='B', trig=140), S(75, 120, (80, 0), trig=140)], opp_x=15)
    seg('air_shield40', 150, g=[S(0, 6, btn='X'), S(10, 1, (0, -80), btn='B'), S(11, 39, (0, -80), btn='B', trig=140),
                                S(50, 80, trig=140)], opp_x=35)
    # placement: near the right ledge casting forward (the mark offstage), high over the stage, and offstage high
    seg('edge_fwd', 120, geno_x=LEDGE - 10, g=[S(0, 3, (36, -70), btn='B')], opp_x=-60,
        opp_face=1, cam=(LEDGE + 10, 12, 130))
    def high(x, y):
        return lambda f, t: (f.port(GENO).hold(t - 20, 3, btn='X'), f.setpos(t - 2, GENO, x, y), f.cue(t - 2, 'motion', GENO, FALL))
    seg('high_stage', 120, geno_x=0, g=[S(0, 3, (0, -80), btn='B')], opp_x=-60, opp_face=1, pre=high(0, 60), cam=(25, 30, 150))
    seg('off_high', 120, geno_x=LEDGE - 10, g=[S(0, 3, (0, -80), btn='B')], opp_x=-60, opp_face=1,
        pre=high(LEDGE + 20, 40), cam=(LEDGE + 30, 20, 150))
elif G == 'meteor':
    # the offstage column on SP_CHAR (fox, falco, marth) at 30, 60 and 90%: Geno at the right ledge marks near (the mark 25
    # ahead, 19 past the ledge, on the stage's plane); the target is placed falling into the column as it strikes and does
    # nothing after, so its position when the hitstun ends says how deep the spike leaves it (against its recovery)
    for pct in (30, 60, 90):
        def place(f, t):
            f.port(OPP).hold(t + 20, 3, btn='X'); f.setpos(t + 36, OPP, LEDGE + 19, 16); f.cue(t + 36, 'motion', OPP, FALL)
            f.setpos(t + 84, OPP, 20, 10)          # measured by then (the hitstun's end): brought back before it's KO'd
        seg(f'pct{pct}', 200, geno_x=LEDGE - 6, opp_x=LEDGE - 40, opp_face=-1, opp_pct=pct,
            g=[S(0, 3, (-36, -70), btn='B')], pre=place, cam=(LEDGE + 10, 0, 150))
elif G == 'recover':
    # the cast's straight-up recoveries from the same drop (hanging on the left ledge, dropped, up B after 8 frames)
    players = [(CHAR, dict(x=-60, face=1)), ('fox', dict(x=60, face=-1))]
    UPB = {'fox': [S(0, 3, (0, 80), btn='B'), S(3, 40, (0, 80))], 'falco': [S(0, 3, (0, 80), btn='B'), S(3, 40, (0, 80))]}
    for k in (8,):
        def hang(f, t):
            f.port(GENO).hold(t - 30, 3, btn='X'); f.setpos(t - 22, GENO, -LEDGE - 5, 4); f.face(t - 22, GENO, 1)
            f.cue(t - 22, 'motion', GENO, FALL)
        seg(f'{CHAR}_drop{k}', 200, geno_x=-LEDGE + 10, opp_x=60,
            g=[S(8, 3, (0, -80))] + [(8 + k + at, n, st, c, b, tr) for at, n, st, c, b, tr in UPB.get(CHAR, [S(0, 3, (0, 80), btn='B'), S(3, 30, (0, 80))])],
            pre=hang, cam=(-LEDGE, -20, 170))
elif G == 'dropb':
    # the aerial down B's fall (the effects agent: placed 104 up, on the floor 9 frames later): down B pressed in a full
    # hop's rise, at its apex and falling, and placed 104 up (airborne first, or teleported while standing)
    DOWN = (0, -80)
    for name, at in (('rise', 8), ('apex', 24), ('fall', 36)):
        seg(name, 140, geno_x=0, opp_x=-70, opp_face=1, g=[S(0, 6, btn='X'), S(at, 3, DOWN, btn='B')], cam=(0, 30, 160))
    def up104(f, t):
        f.port(GENO).hold(t - 20, 3, btn='X'); f.setpos(t - 2, GENO, 0, 104); f.cue(t - 2, 'motion', GENO, FALL)
    seg('placed104', 160, geno_x=0, opp_x=-70, opp_face=1, g=[S(0, 3, DOWN, btn='B')], pre=up104, cam=(0, 50, 200))
    def up104g(f, t):
        f.setpos(t - 2, GENO, 0, 104)
    seg('placed104_grounded', 160, geno_x=0, opp_x=-70, opp_face=1, g=[S(0, 3, DOWN, btn='B')], pre=up104g, cam=(0, 50, 200))
elif G == 'starroad':
    for k in (4, 8, 12, 16, 20, 24, 28, 32, 36, 40):
        def hang(f, t):
            f.port(GENO).hold(t - 30, 3, btn='X'); f.setpos(t - 22, GENO, -LEDGE - 5, 4); f.face(t - 22, GENO, 1)
            f.cue(t - 22, 'motion', GENO, FALL)
        seg(f'drop{k}', 170, geno_x=-LEDGE + 10, opp_x=60, g=[S(8, 3, (0, -80)), S(8 + k, 3, (0, 80), btn='B'), S(12 + k, 14, (0, 80))],
            pre=hang, cam=(-LEDGE, -20, 170))

ONLY = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
if ONLY:
    SEGS = [s for s in SEGS if s['label'] in ONLY]
f = Film(len_s=(60 + sum(s['n'] for s in SEGS) + 40) / 60)
f.setup(players=players, stage=stage, seed=5, coll=1)
geno, opp = f.port(GENO), f.port(OPP)
t, plan = 60, []
for i, s in enumerate(SEGS):
    f.reset(t - 40, GENO, s['gx'], s['gf']); f.reset(t - 40, OPP, s['ox'], s['of'])
    f.percent(t - 38, GENO, 0); f.percent(t - 38, OPP, s['pct'])
    cx, cy, d = s['cam']
    f.orbit(t - 12, at=(cx, cy, 0), dist=d, yaw=0, pitch=0, fov=30, ease='cut')
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    if s['pre']:
        s['pre'](f, t)
    for at, n, st, c, b, tr in s['g']:
        geno.hold(t + at, n, stick=st, c=c, btn=b, trig=tr, dir=s['gf'])
    for at, n, st, c, b, tr in s['o']:
        opp.hold(t + at, n, stick=st, c=c, btn=b, trig=tr, dir=s['of'])
    for k in range(s['items']):
        f.items(t + k)
    for k in range(0, s['n'] - 40, s['status'] or s['n']):
        if s['status']:
            f.status(t + k, OPP)
    geno.trace(t - 2, t + s['n'] - 42); opp.trace(t - 2, t + s['n'] - 42)
    f.mark(t, i, s['label'])
    plan.append(dict(label=s['label'], start=t, frames=s['n'] - 40, sync=t - SYNC))
    t += s['n']
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
