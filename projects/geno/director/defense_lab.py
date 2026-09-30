"""Defense lab: Geno's defensive and reactive states in game, on Final Destination with Fox: the rolls, spot dodge and air
dodge, hitstun on the ground and in the air, tumble from a launch and the landing, the techs, a shield break into the
dizzy, being grabbed, pummelled and thrown, Geno's own throw (the victim plays his Thrown entries), and a ledge jump.
Every try traces Geno (POS: cur_pos, motion, the hip joint): the report measures the hip's step across each change of
state (a step past ~2.5 units beyond his own movement is a pop), writes a strip of each try, and --mp4 cuts a sample
reel (a roll, a spot dodge, an air dodge, hitstun, tumble, a tech, a shield break into dizzy).
    .venv/bin/python tools/machinima/melee/build.py projects/geno defense_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol OUT --frames N --res 2 --quiet
    .venv/bin/python projects/geno/director/defense_lab.py --report OUT PLAN.json [BOARD_DIR] [--mp4 OUT.mp4]
"""
import glob, json, math, os, subprocess, sys

GENO, FOX = 0, 1
L = -85.6
FALL = 29
MS = {14: 'Wait', 29: 'Fall', 35: 'FallSpecial', 38: 'DamageFall', 178: 'GuardOn', 179: 'Guard', 180: 'GuardOff',
      181: 'GuardSetOff', 182: 'GuardReflect', 235: 'EscapeN', 233: 'EscapeF', 234: 'EscapeB', 236: 'EscapeAir',
      238: 'Rebound', 75: 'DamageHi1', 76: 'DamageHi2', 77: 'DamageHi3', 78: 'DamageN1', 79: 'DamageN2', 80: 'DamageN3',
      81: 'DamageLw1', 82: 'DamageLw2', 83: 'DamageLw3', 84: 'DamageAir1', 85: 'DamageAir2', 86: 'DamageAir3',
      87: 'DamageFlyHi', 88: 'DamageFlyN', 89: 'DamageFlyLw', 90: 'DamageFlyTop', 91: 'DamageFlyRoll', 183: 'DownBoundU',
      184: 'DownWaitU', 186: 'DownStandU', 191: 'DownBoundD', 192: 'DownWaitD', 194: 'DownStandD', 199: 'Passive',
      200: 'PassiveStandF', 201: 'PassiveStandB', 211: 'FuraFura', 212: 'Catch', 213: 'CatchPull', 216: 'CatchWait',
      217: 'CatchAttack', 219: 'ThrowF', 220: 'ThrowB', 223: 'CapturePulledHi', 224: 'CaptureWaitHi',
      225: 'CaptureDamageHi', 226: 'CapturePulledLw', 227: 'CaptureWaitLw', 228: 'CaptureDamageLw', 229: 'CaptureCut',
      239: 'ThrownF', 240: 'ThrownB', 252: 'CliffCatch', 253: 'CliffWait', 260: 'CliffJumpSlow1', 261: 'CliffJumpSlow2',
      262: 'CliffJumpQuick1', 263: 'CliffJumpQuick2', 205: 'ShieldBreakFly', 206: 'ShieldBreakFall',
      207: 'ShieldBreakDownU', 208: 'ShieldBreakDownD', 209: 'ShieldBreakStandU', 210: 'ShieldBreakStandD', 42: 'Landing',
      43: 'LandingFallSpecial', 25: 'JumpF', 24: 'KneeBend', 251: 'MissFoot'}
POP = 2.5

# (label, slot frames, setup dict). g: Geno's inputs, f: Fox's inputs, each (offset, frames, stick, cstick, buttons, trig)
TESTS = [
    ('roll_f', 80, dict(g=[(0, 20, (0, 0), (0, 0), '', 140), (4, 3, (80, 0), (0, 0), '', 140)])),
    ('roll_b', 80, dict(g=[(0, 20, (0, 0), (0, 0), '', 140), (4, 3, (-80, 0), (0, 0), '', 140)])),
    ('spot_dodge', 60, dict(g=[(0, 20, (0, 0), (0, 0), '', 140), (4, 3, (0, -80), (0, 0), '', 140)])),
    ('air_dodge', 110, dict(g=[(0, 3, (0, 0), (0, 0), 'X', 0), (12, 3, (0, 0), (0, 0), '', 140)])),
    ('jab_hit', 60, dict(fox_x=9, f=[(5, 2, (0, 0), (0, 0), 'A', 0)])),
    ('ftilt_hit', 70, dict(fox_x=14, pct=40, f=[(5, 3, (-48, 0), (0, 0), '', 0), (7, 2, (-48, 0), (0, 0), 'A', 0)])),
    ('dtilt_hit', 70, dict(fox_x=13, pct=30, f=[(5, 6, (0, -60), (0, 0), '', 0), (9, 2, (0, -60), (0, 0), 'A', 0)])),
    ('air_hit', 90, dict(fox_x=4, pct=20, g=[(0, 3, (0, 0), (0, 0), 'X', 0)], f=[(6, 3, (0, 50), (0, 0), '', 0), (8, 2, (0, 50), (0, 0), 'A', 0)])),
    ('tumble_up', 260, dict(fox_x=5, pct=55, f=[(5, 3, (0, 0), (0, 80), '', 0)])),
    ('tumble_side', 260, dict(fox_x=14, pct=55, f=[(5, 3, (0, 0), (-80, 0), '', 0)])),
    ('tech_inplace', 60, dict(motion=199)),
    ('tech_roll', 70, dict(motion=200)),
    ('shield_break', 480, dict(fox_x=14, shieldhp=2, g=[(0, 60, (0, 0), (0, 0), '', 140)], f=[(20, 3, (0, 0), (-80, 0), '', 0)])),
    ('grabbed', 230, dict(fox_x=8, pct=40, f=[(3, 2, (0, 0), (0, 0), 'Z', 0), (45, 2, (0, 0), (0, 0), 'A', 0), (72, 2, (0, 0), (0, 0), 'A', 0),
                                              (99, 2, (0, 0), (0, 0), 'A', 0), (130, 3, (-80, 0), (0, 0), '', 0)])),
    ('geno_throws', 200, dict(fox_x=8, pct=40, g=[(3, 2, (0, 0), (0, 0), 'Z', 0), (50, 3, (-80, 0), (0, 0), '', 0)])),
    ('ledge_jump', 170, dict(ledge=True, g=[(50, 2, (0, 0), (0, 0), 'X', 0)])),
]
REEL = ['roll_f', 'spot_dodge', 'air_dodge', 'ftilt_hit', 'tumble_side', 'tech_roll', 'shield_break']


def plan_tests():
    only = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
    return [t for t in TESTS if not only or t[0] in only]


def first_frame(run):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'machinima'))
    from plates import is_slate
    frames = sorted(glob.glob(os.path.join(run, 'f*.png')))
    first = None
    for i, f in enumerate(frames[:400]):
        if is_slate(f): first = i + 1
        elif first is not None: break
    return frames, first


def report(run, plan_path, board=None, mp4=None):
    plan = json.load(open(plan_path))
    log = [l.split() for l in open(os.path.join(run, 'osreport.log'), errors='replace')]
    pos = {(int(l[1]), int(l[2])): (float(l[3]), float(l[4]), int(l[5]), float(l[6]), float(l[7]))
           for l in log if l and l[0] == 'POS' and len(l) >= 8}
    hits = [(int(l[1]), int(l[2]), int(l[3]), float(l[4])) for l in log if l and l[0] == 'HIT']
    frames, first = first_frame(run) if (board or mp4) else ([], None)
    worst = []
    for p in plan:
        t0, t1 = p['t0'], p['t0'] + p['slot'] - 25
        tr = [(s, *pos[(s, GENO)]) for s in range(t0, t1) if (s, GENO) in pos]
        seq, prev = [], None
        for s, x, y, m, hx, hy in tr:
            if m != prev: seq.append(f'{s - t0}:{MS.get(m, m)}'); prev = m
        print(f"== {p['label']}: " + ' '.join(seq))
        for f, a, v, d in hits:
            if t0 <= f < t1: print(f'   HIT +{f - t0}: port {a} -> {v}, {d}%')
        steps = []
        for (s0, *a), (s1, *b) in zip(tr, tr[1:]):
            steps.append((s1, math.hypot(b[3] - a[3], b[4] - a[4]), math.hypot(b[0] - a[0], b[1] - a[1]), a[2], b[2]))
        for s, d, own, m0, m1 in steps:
            if m0 == m1: continue
            around = [(d2, o2) for s2, d2, o2, *_ in steps if abs(s2 - s) <= 1]
            big, own2 = max(around)
            flag = '  POP' if big > max(POP, own2 + 1.5) else ''
            print(f'   +{s - t0} {MS.get(m0, m0)} -> {MS.get(m1, m1)}: hip {big:.2f} (he moved {own2:.2f}){flag}')
            worst.append((big - own2, big, p['label'], MS.get(m0, m0), MS.get(m1, m1)))
        if board and first is not None:
            strip(frames, first, p, board)
    print('\nlargest hip steps beyond his own movement, at changes of state:')
    for extra, big, label, a, b in sorted(worst, reverse=True)[:10]:
        print(f'  {extra:5.2f} ({big:.2f})  {label}: {a} -> {b}')
    if mp4 and first is not None:
        reel(frames, first, plan, mp4)


def strip(frames, first, p, board):
    from PIL import Image, ImageDraw
    t0, n = p['t0'], p['slot'] - 25
    step = max(2, n // 24)
    ims = []
    for k in range(0, n, step):
        i = first + t0 + k
        if 0 <= i < len(frames):
            im = Image.open(frames[i]).convert('RGB'); w, h = im.size
            ims.append((k, im.crop((int(w * 0.2), int(h * 0.15), int(w * 0.8), int(h * 0.85)))))
    if not ims: return
    cw, ch = ims[0][1].size; sc = 300 / cw; W, H = int(cw * sc), int(ch * sc); cols = 8
    out = Image.new('RGB', (W * min(cols, len(ims)), H * ((len(ims) + cols - 1) // cols) + 20), (20, 20, 24))
    d = ImageDraw.Draw(out); d.text((6, 4), p['label'], fill=(240, 240, 240))
    for j, (f, im) in enumerate(ims):
        x, y = (j % cols) * W, 20 + (j // cols) * H
        out.paste(im.resize((W, H)), (x, y)); d.text((x + 4, y + 4), f'+{f}', fill=(255, 255, 0))
    os.makedirs(board, exist_ok=True)
    out.save(os.path.join(board, f"def_{p['label']}.png"))


def reel(frames, first, plan, mp4):
    """The sample reel: each try in REEL cropped to Geno and labelled, at 60 fps."""
    from PIL import Image, ImageDraw
    tmp = os.path.splitext(mp4)[0] + '_frames'
    os.makedirs(tmp, exist_ok=True)
    for f in glob.glob(os.path.join(tmp, '*.jpg')): os.remove(f)
    k = 0
    for p in plan:
        if p['label'] not in REEL: continue
        n = min(p['slot'] - 25, 330)
        for j in range(n):
            i = first + p['t0'] + j
            if not 0 <= i < len(frames): continue
            im = Image.open(frames[i]).convert('RGB'); w, h = im.size
            im = im.crop((int(w * 0.1), int(h * 0.1), int(w * 0.9), int(h * 0.9))).resize((960, 720))
            ImageDraw.Draw(im).text((12, 10), p['label'].replace('_', ' '), fill=(255, 255, 255))
            im.save(os.path.join(tmp, f'{k:05d}.jpg'), quality=90); k += 1
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '60', '-i', os.path.join(tmp, '%05d.jpg'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', mp4], check=True)
    print('reel', mp4, k, 'frames')


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--report':
    a = sys.argv[2:]
    mp4 = a[a.index('--mp4') + 1] if '--mp4' in a else None
    a = [x for x in a if x not in ('--mp4', mp4)]
    report(a[0], a[1], a[2] if len(a) > 2 else None, mp4); sys.exit()

from dsl import Film
tests = plan_tests()
f = Film(len_s=(sum(s for _, s, _ in tests) + 110) / 60)
f.setup(players=[('geno', dict(x=0, face=1)), ('fox', dict(x=40, face=-1))], seed=13, coll=0)
geno, fox = f.port(GENO), f.port(FOX)
plan, t0 = [], 70
for i, (label, slot, a) in enumerate(tests):
    f.mark(t0, i, label)
    if a.get('ledge'):
        f.cam(t0 - 20, eye=(L + 4, 2, 120), at=(L + 4, 2, 0), fov=30, ease='cut')
        f.reset(t0 - 40, GENO, L + 12, 1); f.reset(t0 - 40, FOX, 40, -1)
        geno.hold(t0 - 30, 3, btn='X')
        f.setpos(t0, GENO, L - 3, 8); f.face(t0, GENO, 1); f.cue(t0, 'motion', GENO, FALL)
    else:
        f.cam(t0 - 20, eye=(0, 14, 120), at=(0, 12, 0), fov=34, ease='cut', track='p0')
        f.reset(t0 - 30, GENO, 0, 1); f.reset(t0 - 30, FOX, a.get('fox_x', 40), -1 if a.get('fox_x', 40) > 0 else 1)
    f.percent(t0 - 26, GENO, a.get('pct', 0)); f.percent(t0 - 26, FOX, 30)
    if 'motion' in a:
        f.cue(t0, 'motion', GENO, a['motion'])
    if 'shieldhp' in a:
        f.cue(t0 + 8, 'shieldhp', GENO, a['shieldhp'])
    for at, n, stick, c, btn, trig in a.get('g', []):
        geno.hold(t0 + at, n, stick=stick, c=c, btn=btn, trig=trig)
    for at, n, stick, c, btn, trig in a.get('f', []):
        fox.hold(t0 + at, n, stick=stick, c=c, btn=btn, trig=trig)
    geno.trace(t0 - 2, t0 + slot - 25)
    plan.append(dict(label=label, t0=t0, slot=slot))
    t0 += slot
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
