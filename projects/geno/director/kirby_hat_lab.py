"""Kirby hat lab: Kirby's Geno hat (PlKbCpGe.dat, rig/kirby_hat.py build) in game. Each segment opens with a two-frame
magenta sync slate (SYNC frames before its start), so strips line their images up with the log (labs/kirby_hat_board.py).
    KBHAT=costumes KBHAT_COLORS=0,1,2 .venv/bin/python tools/machinima/melee/build.py projects/geno kirby_hat_lab
        three Kirbys in those costumes copy Geno in turn (the hat appears on the swallow), line up (match distance, side
        and 3/4), then the first one: close-ups (side, 3/4), crouch, jumps, the copy's Finger Shot, full Beam and air
        charge, and the taunt, which drops the copy and the hat
    KBHAT=compare:luigi|mario|link [KBHAT_GENO_COLOR=3] ...
        one Kirby copies Geno, another copies Luigi, Mario or Link; side by side under one fixed camera (the vanilla cap
        next to Geno's at the same scale), close and at match distance, side and 3/4, and both jumping; then the
        Geno-hat Kirby beside the Geno he copied, in that Geno's costume (KBHAT_GENO_COLOR: 3 is Mallow)
The log: KBCOPY/KBLOSE (copies), MS (states), POS (positions, for crops), MARK (segments).
"""
import json, os, sys
from dsl import Film

MODE = os.environ.get('KBHAT', 'costumes')
GENO_COLOR = int(os.environ.get('KBHAT_GENO_COLOR', '0'))    # Geno's costume (0 Geno, 1 Mario, 2 Bowser, 3 Mallow, 4 Peach)
SYNC = 10
MATCH = 220                     # the match camera's distance on Final Destination with the players close (the kirby labs)
CLOSE = 42
HEAD = 6.5                      # Kirby's head centre above his position (model scale 0.92: body sphere centre 5.1, hat top 12.4)
SEGS, plan = [], []


def seg(label, n):
    def reg(fn):
        SEGS.append((label, n, fn)); return fn
    return reg


def slate(t):
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)


def swallow(p, t0):
    p.hold(t0, 35, btn='B'); p.hold(t0 + 62, 6, stick=(0, -80))


def close(t, port, yaw, x=None):
    """a close-up: tracking port 0 or 1 (the director tracks only those), else fixed on x"""
    if x is None and port < 2:
        f.orbit(t, at=(0, HEAD, 0), dist=CLOSE, yaw=yaw, pitch=6, fov=30, ease='cut', track=f'p{port}')
    else:
        f.orbit(t, at=(x, HEAD, 0), dist=CLOSE, yaw=yaw, pitch=6, fov=30, ease='cut')


def wide(t, yaw, x=0.0):
    f.orbit(t, at=(x, 10, 0), dist=MATCH, yaw=yaw, pitch=5, fov=30, ease='cut')


if MODE == 'costumes':
    COLORS = [int(c) for c in os.environ.get('KBHAT_COLORS', '0,1,2').split(',')]
    K = list(range(len(COLORS))); GENO = len(COLORS)
    players = [('kirby', dict(x=-55 + 20 * i, face=1, color=c)) for i, c in enumerate(COLORS)] + [('geno', dict(x=55, face=-1, color=GENO_COLOR))]

    def park(t0, active=None):
        for i in K:
            if i != active:
                f.reset(t0 - 18, i, -60 + 12 * i, 1)

    for i in K:
        def _copy(t0, i=i):
            park(t0, i); f.reset(t0 - 18, i, -12, 1); f.reset(t0 - 18, GENO, 6, -1)
            for k in K + [GENO]: f.percent(t0 - 16, k, 0)
            close(t0 - 18, i, 0, x=-9); swallow(f.port(i), t0)
            for k in (40, 120, 190): f.status(t0 + k, i)
        seg(f'copy_c{COLORS[i]}', 200)(_copy)

    def lineup(t0):
        for j, i in enumerate(K): f.reset(t0 - 18, i, -24 + 24 * j, 1)
        f.reset(t0 - 18, GENO, 58, -1)
    seg('lineup_match_side', 90)(lambda t0: (lineup(t0), wide(t0 - 18, 0)))
    seg('lineup_match_34', 90)(lambda t0: (lineup(t0), wide(t0 - 18, 35)))
    seg('lineup_close_34', 90)(lambda t0: (lineup(t0), f.orbit(t0 - 18, at=(0, 8, 0), dist=95, yaw=35, pitch=5, fov=30, ease='cut')))

    def solo(t0, yaw=0):
        park(t0, 0); f.reset(t0 - 18, 0, 0, 1); f.reset(t0 - 18, GENO, 58, -1); close(t0 - 18, 0, yaw)
    seg('idle_side', 120)(lambda t0: solo(t0, 0))
    seg('idle_34', 120)(lambda t0: solo(t0, 40))
    seg('idle_back34', 120)(lambda t0: solo(t0, -40))
    seg('crouch', 70)(lambda t0: (solo(t0), f.port(0).crouch(t0 + 5, 45)))
    seg('jumps', 150)(lambda t0: (solo(t0), [f.port(0).hold(t0 + k, 3, btn='X') for k in (5, 30, 50, 70, 90)]))
    seg('tap', 90)(lambda t0: (solo(t0), f.port(0).hold(t0 + 5, 3, btn='B')))
    seg('charge', 150)(lambda t0: (solo(t0), f.port(0).hold(t0 + 5, 70, btn='B')))
    seg('air_charge', 140)(lambda t0: (solo(t0), f.port(0).hold(t0 + 3, 6, btn='X'), f.port(0).hold(t0 + 13, 26, btn='B')))
    seg('taunt', 200)(lambda t0: (solo(t0), f.port(0).taunt(t0 + 5), f.status(t0 + 60, 0), f.status(t0 + 190, 0)))

elif MODE.startswith('compare:'):
    OTHER = MODE.split(':')[1]
    KG, KX, GENO, X = 0, 1, 2, 3
    players = [('kirby', dict(x=-40, face=1)), ('kirby', dict(x=-55, face=1)), ('geno', dict(x=6, face=-1, color=GENO_COLOR)),
               (OTHER, dict(x=55, face=-1))]

    def _copy(t0, k, donor):
        others = [p for p in (KG, KX, GENO, X) if p not in (k, donor)]
        f.reset(t0 - 18, k, -12, 1); f.reset(t0 - 18, donor, 6, -1)
        f.reset(t0 - 18, others[0], -58, 1); f.reset(t0 - 18, others[1], 58, -1)
        for p in (KG, KX, GENO, X): f.percent(t0 - 16, p, 0)
        close(t0 - 18, k, 0, x=-9); swallow(f.port(k), t0); f.status(t0 + 150, k)
    seg('copy_geno', 200)(lambda t0: _copy(t0, KG, GENO))
    seg(f'copy_{OTHER}', 200)(lambda t0: _copy(t0, KX, X))

    def pair(t0):       # Geno's hat on the left, the vanilla cap on the right, both facing right
        f.reset(t0 - 18, KG, -8, 1); f.reset(t0 - 18, KX, 8, 1); f.reset(t0 - 18, GENO, -58, 1); f.reset(t0 - 18, X, 58, -1)
    for yaw, name in ((0, 'side'), (35, '34'), (-35, 'back34')):
        seg(f'pair_close_{name}', 80)(lambda t0, yaw=yaw: (pair(t0), f.orbit(t0 - 18, at=(0, 8, 0), dist=70, yaw=yaw, pitch=5, fov=30, ease='cut')))
    seg('pair_match_side', 80)(lambda t0: (pair(t0), wide(t0 - 18, 0)))

    def with_geno(t0):  # the Geno-hat Kirby beside the Geno he copied (his costume: KBHAT_GENO_COLOR)
        f.reset(t0 - 18, KG, -8, 1); f.reset(t0 - 18, GENO, 10, -1); f.reset(t0 - 18, KX, -58, 1); f.reset(t0 - 18, X, 58, -1)
    seg('with_geno_34', 80)(lambda t0: (with_geno(t0), f.orbit(t0 - 18, at=(0, 10, 0), dist=80, yaw=25, pitch=5, fov=30, ease='cut')))
    # jumps on a fixed wider camera (the tracking close-up lags a rising Kirby): the jump and two puffed midair jumps
    seg('pair_jumps', 110)(lambda t0: (pair(t0), f.orbit(t0 - 18, at=(0, 24, 0), dist=120, yaw=15, pitch=3, fov=30, ease='cut'),
                                       [f.port(p).hold(t0 + k, 3, btn='X') for p in (KG, KX) for k in (5, 32, 52)]))
else:
    sys.exit(f'KBHAT={MODE}: costumes or compare:luigi|mario|link')

LEAD = 70
f = Film(len_s=(LEAD + sum(n for _, n, _ in SEGS) + 40) / 60)
f.setup(players=players, seed=5, coll=0)
f.cam(0, eye=(0, 30, 230), at=(0, 14, 0), fov=30, ease='cut')
t = LEAD
for i, (label, n, fn) in enumerate(SEGS):
    slate(t); fn(t); f.mark(t, i, label)
    plan.append(dict(label=label, start=t, frames=n, sync=t - SYNC))
    t += n
f.emit(sys.argv[1])
json.dump(dict(mode=MODE, segs=plan), open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
