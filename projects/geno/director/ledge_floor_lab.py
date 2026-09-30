"""Ledge and floor lab: Geno's ledge catch from several approaches, every ledge action after it, and the floor states
(the knockdown bounce, the stand-ups, the get-up rolls, the jolt when hit lying, the techs), with a hop over each get-up
attack. Final Destination (ledges at x = +-85.6), hitbox display on.
  - catches: falling straight down near the ledge and farther out, drifting in from far out, fast-falling, and Star Road
    (up-B) into the ledge from above and from below;
  - ledge actions: climbs, rolls, jumps and the attack under and from 100%, each from a catch;
  - floor: DownBound U/D (the motion cue; the game then puts him in DownWait), then stand up, roll either way, or take a
    Fox jab (DownDamage); the techs by their motion cues; and a Fox short hop over each get-up attack.
Every try traces Geno (POS: cur_pos, motion and the hip joint's world position). The report measures how far the hip moves
on each frame across each motion change: a jump of more than ~2.5 units in one frame (the fastest he falls is 3.0,
fast-falling) is a pop.
    .venv/bin/python tools/machinima/melee/build.py projects/geno ledge_floor_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol OUT --frames N --res 2 --quiet
    .venv/bin/python projects/geno/director/ledge_floor_lab.py --report OUT PLAN.json [BOARD_DIR]
With BOARD_DIR: a strip of every frame around each catch (full-resolution crops) and of each try's key frames.
"""
import glob, json, math, os, sys

GENO, FOX = 0, 1
L = -85.6                                   # the left ledge
FALL, SPECIAL_HI = 29, None
DOWN_BOUND_U, DOWN_BOUND_D, PASSIVE, PASSIVE_F, PASSIVE_B = 183, 191, 199, 200, 201
MS = {14: 'Wait', 29: 'Fall', 183: 'DownBoundU', 184: 'DownWaitU', 185: 'DownDamageU', 186: 'DownStandU', 187: 'DownAttackU',
      188: 'DownFowardU', 189: 'DownBackU', 191: 'DownBoundD', 192: 'DownWaitD', 193: 'DownDamageD', 194: 'DownStandD',
      195: 'DownAttackD', 196: 'DownFowardD', 197: 'DownBackD', 199: 'Passive', 200: 'PassiveStandF', 201: 'PassiveStandB',
      252: 'CliffCatch', 253: 'CliffWait', 254: 'CliffClimbSlow', 255: 'CliffClimbQuick', 256: 'CliffAttackSlow',
      257: 'CliffAttackQuick', 258: 'CliffEscapeSlow', 259: 'CliffEscapeQuick', 260: 'CliffJumpSlow1', 261: 'CliffJumpSlow2',
      262: 'CliffJumpQuick1', 263: 'CliffJumpQuick2', 30: 'FallAerial', 35: 'FallSpecial'}

# (label, kind, args); frames are offsets from the try's start t0
TESTS = [
    ('catch_fall_near', 'catch', dict(at=(L - 3, 8))),
    ('catch_fall_far', 'catch', dict(at=(L - 11, 6))),
    ('catch_drift_in', 'catch', dict(at=(L - 20, 30), drift=60)),
    ('catch_fastfall', 'catch', dict(at=(L - 4, 34), fastfall=True)),
    ('catch_starroad_down', 'catch', dict(at=(L - 30, 12), starroad=(70, -40))),     # down into the ledge: caught mid-travel
    ('catch_starroad_up', 'catch', dict(at=(L - 6, -26), starroad=(35, 75))),
    ('climb_quick', 'ledge', dict(pct=0, inp=dict(stick=(60, 0)))),
    ('climb_slow', 'ledge', dict(pct=120, inp=dict(stick=(60, 0)))),
    ('roll_quick', 'ledge', dict(pct=0, inp=dict(btn='R', trig=140))),
    ('roll_slow', 'ledge', dict(pct=120, inp=dict(btn='R', trig=140))),
    ('jump_quick', 'ledge', dict(pct=0, inp=dict(btn='X'))),
    ('jump_slow', 'ledge', dict(pct=120, inp=dict(btn='X'))),
    ('attack_quick', 'ledge', dict(pct=0, inp=dict(btn='A'))),
    ('bound_u_stand', 'floor', dict(motion=DOWN_BOUND_U, inp=dict(stick=(0, 80)))),
    ('bound_d_stand', 'floor', dict(motion=DOWN_BOUND_D, inp=dict(stick=(0, 80)))),
    ('roll_fwd_u', 'floor', dict(motion=DOWN_BOUND_U, inp=dict(stick=(80, 0)))),
    ('roll_back_u', 'floor', dict(motion=DOWN_BOUND_U, inp=dict(stick=(-80, 0)))),
    ('roll_fwd_d', 'floor', dict(motion=DOWN_BOUND_D, inp=dict(stick=(80, 0)))),
    ('roll_back_d', 'floor', dict(motion=DOWN_BOUND_D, inp=dict(stick=(-80, 0)))),
    ('jolt_u', 'floor', dict(motion=DOWN_BOUND_U, jab=True)),
    ('tech_in_place', 'floor', dict(motion=PASSIVE)),
    ('tech_roll_f', 'floor', dict(motion=PASSIVE_F)),
    ('tech_roll_b', 'floor', dict(motion=PASSIVE_B)),
    ('getup_u_hop_early', 'hop', dict(motion=DOWN_BOUND_U, hop=47)),
    ('getup_u_hop_late', 'hop', dict(motion=DOWN_BOUND_U, hop=52)),
    ('getup_d_hop_early', 'hop', dict(motion=DOWN_BOUND_D, hop=47)),
    ('getup_d_hop_late', 'hop', dict(motion=DOWN_BOUND_D, hop=52)),
    ('ledge_drop', 'ledge', dict(pct=0, inp=dict(stick=(-60, 0)))),        # let go (stick away) and fall: last, he dies
]
SLOT = {'catch': 150, 'ledge': 190, 'floor': 150, 'hop': 150}
POP = 2.5


def plan_tests():
    only = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
    return [t for t in TESTS if not only or any(t[0].startswith(o) for o in only)]


def report(run, plan_path, board=None):
    plan = json.load(open(plan_path))
    log = [l.split() for l in open(os.path.join(run, 'osreport.log'), errors='replace')]
    pos = {}
    for l in log:
        if l and l[0] == 'POS' and len(l) >= 8:
            pos[(int(l[1]), int(l[2]))] = (float(l[3]), float(l[4]), int(l[5]), float(l[6]), float(l[7]))
    hits = [(int(l[1]), int(l[2]), int(l[3]), float(l[4])) for l in log if l and l[0] == 'HIT']
    catches = [l for l in log if l[:2] == ['GENO', 'CATCH']]
    frames = sorted(glob.glob(os.path.join(run, 'f*.png')))
    first = None
    if board and frames:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'machinima'))
        from plates import is_slate
        for i, f in enumerate(frames[:400]):
            if is_slate(f): first = i + 1
            elif first is not None: break
    worst = []
    for p in plan:
        t0, t1 = p['t0'], p['t0'] + p['slot'] - 45
        tr = [(s, *pos[(s, GENO)]) for s in range(t0, t1) if (s, GENO) in pos]
        seq, prev = [], None
        for s, x, y, m, hx, hy in tr:
            if m != prev: seq.append(f'{s - t0}:{MS.get(m, m)}'); prev = m
        print(f"== {p['label']}: " + ' '.join(seq))
        for f, a, v, d in hits:
            if t0 <= f < t1: print(f'   HIT +{f - t0}: port {a} -> {v}, {d}%')
        # the hip's step on each frame; the biggest around each motion change
        steps = []                                   # (frame, the hip's step, the fighter's own step, motions)
        for (s0, *a), (s1, *b) in zip(tr, tr[1:]):
            d = math.hypot(b[3] - a[3], b[4] - a[4])
            steps.append((s1, d, math.hypot(b[0] - a[0], b[1] - a[1]), a[2], b[2]))
        steps = [(s, d, m0, m1, own) for s, d, own, m0, m1 in steps]
        changes = [(s, d, m0, m1) for s, d, m0, m1, own in steps if m0 != m1]
        for s, d, m0, m1 in changes:
            around = [(d2, own) for s2, d2, a2, b2, own in steps if abs(s2 - s) <= 1]
            big, own = max(around)
            # a pop: the body jumps more than the fighter himself moves (falling, a jump's launch, the star's travel)
            flag = '  POP' if big > max(POP, own + 1.5) else ''
            print(f'   +{s - t0} {MS.get(m0, m0)} -> {MS.get(m1, m1)}: hip moves {big:.2f} a frame{flag}')
            worst.append((big, p['label'], MS.get(m0, m0), MS.get(m1, m1)))
        inner = [(d, s) for s, d, m0, m1, own in steps if m0 == m1]
        if inner:
            d, s = max(inner)
            print(f'   largest step inside an action: {d:.2f} at +{s - t0} ({MS.get(pos[(s, GENO)][2], "?")})')
        end = tr[-1] if tr else None
        if end: print(f'   end: {MS.get(end[3], end[3])} at ({end[1] - L if p["kind"] in ("catch", "ledge") else end[1]:.1f}, {end[2]:.1f})')
        if p['kind'] == 'hop':
            fx = [(s - t0, *pos[(s, FOX)][:2]) for s in range(t0 + 55, t0 + 72) if (s, FOX) in pos]
            print('   Fox (frame: x, feet y):', ' '.join(f'{f}:({x:.1f},{y:.1f})' for f, x, y in fx[::2]))
        if board and first is not None:
            cat = next((s for s, x, y, m, hx, hy in tr if m == 252), None)
            if p['kind'] == 'catch' and cat is not None:          # every frame across the grab
                p = dict(p, strip=[k - t0 for k in range(cat - 4, cat + 13)])
            strip(frames, first, p, board)
    print('\nbiggest hip steps across motion changes:')
    for big, label, a, b in sorted(worst, reverse=True)[:12]:
        print(f'  {big:5.2f}  {label}: {a} -> {b}')
    if catches:
        print('\ncatch offsets (where he was, less where the path would put him):', ' '.join(f'({c[3]},{c[4]})' for c in catches))


def strip(frames, first, p, board):
    from PIL import Image, ImageDraw
    t0 = p['t0']
    picks = [t0 + k for k in p['strip']]
    full = p['kind'] == 'catch'
    ims = []
    for s in picks:
        i = first + s
        if 0 <= i < len(frames):
            im = Image.open(frames[i]).convert('RGB')
            w, h = im.size
            box = (int(w * 0.25), int(h * 0.2), int(w * 0.75), int(h * 0.8)) if full else (int(w * 0.1), int(h * 0.12), int(w * 0.9), int(h * 0.88))
            ims.append((s - t0, im.crop(box)))
    if not ims: return
    cw, ch = ims[0][1].size
    sc = (420 if full else 320) / cw
    cols = 8 if full else 6
    W, H = int(cw * sc), int(ch * sc)
    out = Image.new('RGB', (W * min(cols, len(ims)), H * ((len(ims) + cols - 1) // cols) + 20), (20, 20, 24))
    d = ImageDraw.Draw(out)
    d.text((6, 4), p['label'], fill=(240, 240, 240))
    for k, (f, im) in enumerate(ims):
        x, y = (k % cols) * W, 20 + (k // cols) * H
        out.paste(im.resize((W, H)), (x, y))
        d.text((x + 4, y + 4), f'+{f}', fill=(255, 255, 0))
    os.makedirs(board, exist_ok=True)
    out.save(os.path.join(board, f"lab_{p['label']}.png"))


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--report':
    report(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None); sys.exit()

from dsl import Film
tests = plan_tests()
f = Film(len_s=(sum(SLOT[k] for _, k, _ in tests) + 110) / 60)
# LAB_CHAR=mario runs the same tries on a cast member (the get-up hops' baseline)
f.setup(players=[(os.environ.get('LAB_CHAR', 'geno'), dict(x=-40, face=1)), ('fox', dict(x=40, face=-1))], seed=9, coll=1)
geno, fox = f.port(GENO), f.port(FOX)
plan, t0 = [], 70


def drop(t0, at, face=1):
    f.reset(t0 - 40, GENO, L + 12, 1)
    geno.hold(t0 - 30, 3, btn='X')                  # airborne first: a grounded fighter teleported offstage snaps back
    f.setpos(t0, GENO, *at); f.face(t0, GENO, face); f.cue(t0, 'motion', GENO, FALL)


for i, (label, kind, a) in enumerate(tests):
    slot = SLOT[kind]
    f.mark(t0, i, label)
    f.reset(t0 - 40, FOX, 40, -1)
    f.percent(t0 - 36, GENO, a.get('pct', 0)); f.percent(t0 - 36, FOX, 0)
    if kind in ('catch', 'ledge'):
        f.cam(t0 - 20, eye=(L + 4, -2, 120), at=(L + 4, -2, 0), fov=30, ease='cut')
        drop(t0, a.get('at', (L - 3, 8)))
        if a.get('drift'):
            geno.hold(t0 + 1, 60, stick=(a['drift'], 0))
        if a.get('fastfall'):
            geno.hold(t0 + 8, 2, stick=(0, -80))       # a flick down once falling: then let go (holding down refuses the ledge)
        if a.get('starroad'):
            geno.hold(t0 + 2, 3, stick=(0, 80), btn='B')
            geno.hold(t0 + 6, 14, stick=a['starroad'])
        if kind == 'ledge':
            inp = a['inp']
            geno.hold(t0 + 50, 3, stick=inp.get('stick', (0, 0)), btn=inp.get('btn', ''), trig=inp.get('trig', 0))
            strip = [48, 50, 51, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72, 76, 80, 84, 90, 96, 104, 112, 124, 136]
        else:
            strip = list(range(0, 60, 2))
    else:
        z = float(os.environ.get('LAB_ZOOM', 1))         # LAB_ZOOM=2.5: close enough to read the boots
        f.cam(t0 - 20, eye=(0, 10 - 3 * (1 - 1 / z), 100 / z), at=(0, 6 - 2 * (1 - 1 / z), 0), fov=30, ease='cut')
        f.reset(t0 - 40, GENO, 0, 1)
        if kind == 'hop':
            f.reset(t0 - 38, FOX, 14, -1)
        elif a.get('jab'):
            f.reset(t0 - 38, FOX, 9, -1)
        f.cue(t0, 'motion', GENO, a['motion'])
        if a.get('inp'):
            geno.hold(t0 + 40, 3, stick=a['inp'].get('stick', (0, 0)))
        if a.get('jab'):
            fox.hold(t0 + 36, 2, btn='A')
        if kind == 'hop':
            geno.hold(t0 + 40, 2, btn='A')              # the get-up attack starts at +41: hits from +59
            fox.hold(t0 + a['hop'], 2, btn='X')
            fox.hold(t0 + a['hop'] + 2, 24, stick=(-80, 0))
            fox.trace(t0 + 50, t0 + 80)
        strip = [0, 2, 4, 6, 8, 10, 13, 16, 20, 26, 30, 34, 38, 41, 44, 47, 50, 53, 56, 59, 62, 65, 68, 72, 76, 80, 86, 92]
    geno.trace(t0 - 5, t0 + slot - 45)
    plan.append(dict(label=label, kind=kind, t0=t0, slot=slot, strip=strip))
    t0 += slot
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
