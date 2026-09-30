"""Pummel, ledge-attack and get-up-attack lab: Geno's own versions of the standardized moves (DESIGN §6c), in game, with the
hitbox display on. Final Destination (ledges at x = +-85.6, floor y = 0).
  - pummels: grab Fox, pummel four times, then a throw (the throw still has to work after the pummels);
  - ledge attacks: Geno drops beside the left ledge (setpos + Fall), catches it, and attacks under 100% (the quick one) and
    from 100% (the slow one) at Fox standing near the lip and at the tip of the reach; his path (POS) shows the climb, and
    his state and position at the end show he stands on the stage;
  - get-up attacks: Geno is knocked down face up and face down (the DownBound motions; the game then puts him in
    DownWait) between two Foxes, one in front and one behind, and attacks: both should be hit.
    .venv/bin/python tools/machinima/melee/build.py projects/geno pummel_ledge_getup_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol OUT --frames N --res 2 --quiet
    .venv/bin/python projects/geno/director/pummel_ledge_getup_lab.py --report OUT PLAN.json [BOARD_DIR]
The report reads OUT/osreport.log (HIT, MS, POS, STATUS lines) and, with BOARD_DIR, writes a strip of each try from the
captured frames (script frame s is the capture's first frame after the opening magenta slate, plus s).
"""
import glob, json, os, sys

GENO, FOX, FOX2 = 0, 1, 2
LEDGE_X = -85.6
FALL, CLIFF_CATCH, CLIFF_WAIT, WAIT = 29, 252, 253, 14
DOWN_BOUND_U, DOWN_BOUND_D = 183, 191
MS_NAMES = {14: 'Wait', 29: 'Fall', 183: 'DownBoundU', 184: 'DownWaitU', 187: 'DownAttackU', 191: 'DownBoundD',
            192: 'DownWaitD', 195: 'DownAttackD', 212: 'Catch', 213: 'CatchPull', 216: 'CatchWait', 217: 'CatchAttack',
            219: 'ThrowF', 220: 'ThrowB', 221: 'ThrowHi', 222: 'ThrowLw', 252: 'CliffCatch', 253: 'CliffWait',
            256: 'CliffAttackSlow', 257: 'CliffAttackQuick'}

# (label, kind, args). Frame offsets are from the try's start t0.
TESTS = [
    ('pummel_fthrow', 'pummel', dict(throw=(80, 0), fox_pct=80)),
    ('pummel_dthrow', 'pummel', dict(throw=(0, -80), fox_pct=80)),
    ('ledge_quick_near', 'ledge', dict(pct=40, fox_x=LEDGE_X + 14)),
    ('ledge_quick_tip', 'ledge', dict(pct=40, fox_x=LEDGE_X + 26)),       # the tip: reach 23.25 + Fox's 4.65 of front body - 1.5
    ('ledge_slow_near', 'ledge', dict(pct=120, fox_x=LEDGE_X + 14)),
    ('ledge_slow_tip', 'ledge', dict(pct=120, fox_x=LEDGE_X + 26)),       # reach 22.8
    ('getup_up', 'getup', dict(motion=DOWN_BOUND_U, gap=13)),
    ('getup_down', 'getup', dict(motion=DOWN_BOUND_D, gap=13)),
    ('getup_up_tip', 'getup', dict(motion=DOWN_BOUND_U, gap=22)),        # reach 19.2 both ways
    ('getup_down_tip', 'getup', dict(motion=DOWN_BOUND_D, gap=22)),
]
SLOT = {'pummel': 250, 'ledge': 170, 'getup': 150}
END = 45                  # the end-of-try STATUS, before the next try's resets (a ledge try resets 40 frames early)
DROP = (float(os.environ.get('LEDGE_DROP_X', LEDGE_X - 5.0)), float(os.environ.get('LEDGE_DROP_Y', 4.0)))


def plan_tests():
    only = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
    return [t for t in TESTS if not only or t[0] in only]


def report(run, plan_path, board=None):
    plan = json.load(open(plan_path))
    log = [l.split() for l in open(os.path.join(run, 'osreport.log'), errors='replace')]
    hits = [(int(l[1]), int(l[2]), int(l[3]), float(l[4])) for l in log if l and l[0] == 'HIT']
    ms = [(int(l[1]), int(l[2]), int(l[3]), float(l[4]), float(l[5])) for l in log if l and l[0] == 'MS']
    pos = [(int(l[1]), int(l[2]), float(l[3]), float(l[4]), int(l[5])) for l in log if l and l[0] == 'POS']
    st = [(int(l[1]), int(l[2]), float(l[3]), float(l[4]), float(l[5]), int(l[6])) for l in log if l and l[0] == 'STATUS']
    frames = sorted(glob.glob(os.path.join(run, 'f*.png')))
    first = None
    if board and frames:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'machinima'))
        from plates import is_slate
        for i, f in enumerate(frames[:400]):
            if is_slate(f): first = i + 1
            elif first is not None: break
    for p in plan:
        t0, t1 = p['t0'], p['t0'] + p['slot']
        inside = lambda f: t0 - 20 <= f < t1
        print(f"== {p['label']} (t0 {t0})")
        seq = [(f, MS_NAMES.get(m, m), round(x, 1), round(y, 1)) for f, port, m, x, y in ms if port == GENO and inside(f)]
        print('  Geno states:', ' '.join(f'{f - t0}:{n}@({x},{y})' for f, n, x, y in seq))
        for f, a, v, d in hits:
            if inside(f): print(f'  HIT +{f - t0}: port {a} -> port {v}, {d}%')
        for f, port, q, x, y, m in st:
            if inside(f): print(f'  STATUS +{f - t0} port {port}: {q}% at ({x}, {y}) {MS_NAMES.get(m, m)}')
        tr = [(f - t0, round(x, 2), round(y, 2), MS_NAMES.get(m, m)) for f, port, x, y, m in pos if port == GENO and inside(f)]
        if tr and p['kind'] == 'ledge':
            att = [r for r in tr if str(r[3]).startswith('CliffAttack')]
            if att:
                a0 = att[0][0]
                print('  climb (frame of the attack: x - ledge, y):', ' '.join(f'{r[0] - a0 + 1}:({round(r[1] - LEDGE_X, 1)},{r[2]})' for r in att[::3]))
                after = [r for r in tr if r[0] > att[-1][0]][:3]
                print('  after:', after)
        if board and first is not None:
            strip(frames, first, p, board)


def strip(frames, first, p, board):
    """A strip of the try's key frames, cropped around the action."""
    from PIL import Image, ImageDraw
    t0 = p['t0']
    picks = [t0 + k for k in p['strip']]
    ims = []
    for s in picks:
        i = first + s
        if 0 <= i < len(frames):
            im = Image.open(frames[i]).convert('RGB')
            w, h = im.size
            ims.append((s - t0, im.crop((int(w * 0.12), int(h * 0.12), int(w * 0.88), int(h * 0.88)))))
    if not ims: return
    cw, ch = ims[0][1].size
    sc = 360 / cw
    cols = 6
    out = Image.new('RGB', (int(cw * sc) * min(cols, len(ims)), int(ch * sc) * ((len(ims) + cols - 1) // cols) + 20), (20, 20, 24))
    d = ImageDraw.Draw(out)
    d.text((6, 4), p['label'], fill=(240, 240, 240))
    for k, (f, im) in enumerate(ims):
        x, y = (k % cols) * int(cw * sc), 20 + (k // cols) * int(ch * sc)
        out.paste(im.resize((int(cw * sc), int(ch * sc))), (x, y))
        d.text((x + 4, y + 4), f'+{f}', fill=(255, 255, 0))
    os.makedirs(board, exist_ok=True)
    out.save(os.path.join(board, f"lab_{p['label']}.png"))


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--report':
    report(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None); sys.exit()

from dsl import Film
tests = plan_tests()
n = sum(SLOT[k] for _, k, _ in tests) + 110
f = Film(len_s=n / 60)
f.setup(players=[('geno', dict(x=-7, face=1)), ('fox', dict(x=0, face=-1)), ('fox', dict(x=20, face=-1, color=1))],
        seed=7, coll=1)
geno, fox, fox2 = f.port(GENO), f.port(FOX), f.port(FOX2)
plan, t0 = [], 70
for i, (label, kind, a) in enumerate(tests):
    slot = SLOT[kind]
    f.mark(t0, i, label)
    if kind == 'pummel':
        f.cam(t0 - 20, eye=(-3, 10, 70), at=(-3, 8, 0), fov=30, ease='cut')
        f.reset(t0 - 18, GENO, -7, 1); f.reset(t0 - 18, FOX, 0, -1); f.reset(t0 - 18, FOX2, 40, -1)
        f.percent(t0 - 16, GENO, 0); f.percent(t0 - 16, FOX, a['fox_pct'])
        geno.hold(t0, 2, btn='Z')
        for k in range(4):                                   # CatchAttack plays 24 frames, then CatchWait takes A again
            geno.hold(t0 + 50 + 28 * k, 2, btn='A')
        geno.hold(t0 + 170, 3, stick=a['throw'])
        f.status(t0 + 168, FOX); f.status(t0 + slot - END, FOX); f.status(t0 + slot - END, GENO)
        strip = [0, 8, 30, 50, 56, 58, 59, 60, 64, 78, 87, 106, 115, 134, 143, 170, 180, 200]
    elif kind == 'ledge':
        f.cam(t0 - 20, eye=(LEDGE_X + 12, 0, 110), at=(LEDGE_X + 12, 0, 0), fov=30, ease='cut')
        f.reset(t0 - 40, GENO, LEDGE_X + 10, -1); f.reset(t0 - 40, FOX, a['fox_x'], -1); f.reset(t0 - 40, FOX2, 40, -1)
        f.percent(t0 - 36, GENO, a['pct']); f.percent(t0 - 36, FOX, 0)
        geno.hold(t0 - 30, 3, btn='X')                       # airborne first: a grounded fighter teleported offstage snaps back
        f.setpos(t0, GENO, *DROP); f.face(t0, GENO, 1); f.cue(t0, 'motion', GENO, FALL)
        geno.hold(t0 + 40, 2, btn='A')
        geno.trace(t0, t0 + slot - 10)
        f.status(t0 + 39, GENO); f.status(t0 + slot - END, GENO); f.status(t0 + slot - END + 1, FOX)
        strip = [0, 20, 41, 44, 48, 52, 55, 57, 58, 60, 62, 64, 65, 68, 72, 76, 80, 84, 90, 100, 112, 130]
    else:
        g = a['gap']
        f.cam(t0 - 20, eye=(0, 10, 90), at=(0, 6, 0), fov=30, ease='cut')
        f.reset(t0 - 18, GENO, 0, 1); f.reset(t0 - 18, FOX, g, -1); f.reset(t0 - 18, FOX2, -g, 1)
        f.percent(t0 - 16, GENO, 0); f.percent(t0 - 16, FOX, 0); f.percent(t0 - 16, FOX2, 0)
        f.cue(t0, 'motion', GENO, a['motion'])
        geno.hold(t0 + 40, 2, btn='A')
        f.status(t0 + slot - END, GENO); f.status(t0 + slot - END + 1, FOX); f.status(t0 + slot - END + 1, FOX2)
        strip = [0, 20, 39, 41, 46, 52, 56, 58, 59, 60, 62, 64, 65, 66, 70, 76, 84, 92, 100, 110]
    plan.append(dict(label=label, kind=kind, t0=t0, slot=slot, strip=strip))
    t0 += slot
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
