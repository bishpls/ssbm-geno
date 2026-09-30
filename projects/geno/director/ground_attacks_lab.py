"""Ground attacks lab: Geno's ground normals, grab and throws, one try each, filmed close on a fixed camera per try (the
production animation's review: rig/poses_ground.py). The attacks whiff (Fox stands well out of reach, so no hitlag
freezes the animation); the grab states hold Fox (the hold and two pummels, a hold he breaks out of; the throws are the
throws lab's). Final Destination.
    LAB_VIEWS=side,34 LAB_COLL=1 .venv/bin/python tools/machinima/melee/build.py projects/geno ground_attacks_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol OUT --frames N --res 2 --quiet
    .venv/bin/python projects/geno/director/ground_attacks_lab.py --board OUT PLAN.json BOARD_DIR
LAB_CHAR=mario (or samus, fox, ...) films another fighter doing the same tries, for the cast beside him. LAB_ONLY picks tries.
The board writes a consecutive-frame strip of each try (script frame s is the capture's first frame after the opening
magenta slate, plus s) and an mp4 of the whole run.
"""
import glob, json, os, sys

GENO, FOX = 0, 1
GX = -20.0                 # every try starts here, facing right
FAR = 60.0                 # Fox out of reach for the whiffs
CLOSE = GX + 10.0          # Fox in grab range

A = lambda at, n, stick=(0, 0), c=(0, 0), btn='': (at, n, stick, c, btn)
# (label, Fox's x, frames, inputs relative to t0 (at, n, stick, cstick, buttons), the action Geno performs first)
TESTS = [
    ('Attack11', FAR, 30, [A(0, 2, btn='A')]),
    ('Attack123', FAR, 70, [A(0, 2, btn='A'), A(8, 2, btn='A'), A(16, 2, btn='A')]),
    ('AttackS3S', FAR, 40, [A(0, 4, (48, 0)), A(2, 2, (48, 0), btn='A')]),
    ('AttackS3Hi', FAR, 40, [A(0, 4, (42, 30)), A(2, 2, (42, 30), btn='A')]),
    ('AttackS3Lw', FAR, 40, [A(0, 4, (42, -30)), A(2, 2, (42, -30), btn='A')]),
    ('AttackHi3', FAR, 40, [A(0, 4, (0, 50)), A(2, 2, (0, 50), btn='A')]),
    ('AttackLw3', FAR, 45, [A(0, 30, (0, -60)), A(8, 2, (0, -60), btn='A')]),
    ('AttackDash', FAR + 12, 70, [A(0, 12, (80, 0)), A(12, 2, (80, 0), btn='A')]),
    ('AttackS4S', FAR, 60, [A(0, 3, c=(80, 0))]),
    ('AttackS4Hi', FAR, 60, [A(0, 3, (70, 40), btn='A')]),
    ('AttackS4Lw', FAR, 60, [A(0, 3, (70, -40), btn='A')]),
    ('AttackHi4', FAR, 55, [A(0, 3, c=(0, 80))]),
    ('AttackLw4', FAR, 55, [A(0, 3, c=(0, -80))]),
    ('Catch', FAR, 45, [A(0, 2, btn='Z')]),
    ('CatchDash', FAR + 12, 65, [A(0, 10, (80, 0)), A(10, 2, (80, 0), btn='Z')]),
    ('Pummel', CLOSE, 110, [A(0, 2, btn='Z'), A(40, 2, btn='A'), A(70, 2, btn='A')]),
    ('CatchCut', CLOSE, 200, [A(0, 2, btn='Z')]),
]
LEAD = 24                  # frames before the input filmed in each try


def plan_tests():
    only = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
    return [t for t in TESTS if not only or t[0] in only]


def camera(f, t, cx, view, track=None):
    """a fixed camera on x = cx, or (track='p0') following Geno with cx as the offset"""
    at = (cx, 9.5 if os.environ.get('LAB_HIGH') else 7.5, 0.0)
    if view == '34':
        f.orbit(t, at=at, dist=58, yaw=38, pitch=8, fov=30, ease='cut', track=track)     # in front of him
    else:
        f.orbit(t, at=at, dist=58, yaw=0, pitch=4, fov=30, ease='cut', track=track)


def build(out):
    from dsl import Film
    views = os.environ.get('LAB_VIEWS', 'side,34').split(',')
    tests = [(v,) + t for t in plan_tests() for v in views]
    char = os.environ.get('LAB_CHAR', 'geno')
    t, plan = 70, []
    for view, label, fx, slot, steps in tests:
        plan.append(dict(label=label, view=view, t0=t + LEAD, slot=slot, fx=fx))
        t += LEAD + slot + 20
    f = Film(len_s=(t + 30) / 60)
    f.setup(players=[(char, dict(x=GX, face=1)), ('fox', dict(x=FAR, face=-1))], seed=3,
            coll=int(os.environ.get('LAB_COLL', 1)))
    geno, fox = f.port(GENO), f.port(FOX)
    camera(f, 0, GX + 5, 'side')
    for i, ((view, label, fx, slot, steps), p) in enumerate(zip(tests, plan)):
        t0 = p['t0']
        f.reset(t0 - LEAD, GENO, GX, 1)
        f.reset(t0 - LEAD, FOX, fx, -1)
        f.percent(t0 - LEAD + 2, GENO, 0); f.percent(t0 - LEAD + 2, FOX, 40 if label != 'CatchCut' else 0)
        if label in ('AttackDash', 'CatchDash'):
            camera(f, t0 - LEAD, GX + 5, view)
            camera(f, t0 + 2, 3.0, view, track='p0')           # follow the dash, a little ahead of him
        else:
            camera(f, t0 - LEAD, GX + (1 if label == 'CatchCut' else 5), view)
        f.mark(t0, i, label)
        for at, n, stick, c, btn in steps:
            geno.hold(t0 + at, n, stick=stick, c=c, btn=btn)
        f.status(t0 + slot - 2, GENO)
    f.emit(out)
    json.dump(plan, open(os.path.splitext(out)[0] + '.plan.json', 'w'), indent=1)


def board(run, plan_path, out_dir):
    """A strip per try (every frame from the input to the end of its slot) and an mp4 of the run."""
    from PIL import Image, ImageDraw
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'machinima'))
    from plates import is_slate
    plan = json.load(open(plan_path))
    frames = sorted(glob.glob(os.path.join(run, 'f*.png')))
    first = None
    for i, fr in enumerate(frames[:400]):
        if is_slate(fr): first = i + 1
        elif first is not None: break
    first = first or 0
    os.makedirs(out_dir, exist_ok=True)
    tag = os.environ.get('LAB_TAG', os.path.basename(run.rstrip('/')))
    crop = [float(x) for x in os.environ.get('LAB_CROP', '0.2,0.06,0.8,0.94').split(',')]
    rng = os.environ.get('LAB_RANGE')                  # a:b, frames of each try (1 = the input frame)
    only = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
    for p in plan:
        if only and p['label'] not in only: continue
        fr = list(range(p['t0'] - 1, p['t0'] + p['slot']))
        if rng:
            a, b = map(int, rng.split(':'))
            fr = list(range(p['t0'] + a - 1, p['t0'] + b))
        imgs = []
        for s in fr:
            k = first + s
            if k >= len(frames): break
            im = Image.open(frames[k]).convert('RGB')
            w, h = im.size
            im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
            im = im.resize((im.width // 2, im.height // 2))
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, 44, 14], fill=(0, 0, 0))
            d.text((3, 2), f'{s - p["t0"] + 1}', fill=(255, 255, 255))
            imgs.append(im)
        if not imgs: continue
        cols = int(os.environ.get('LAB_COLS', 16))
        cw, ch = imgs[0].size
        rows = (len(imgs) + cols - 1) // cols
        sheet = Image.new('RGB', (cw * min(cols, len(imgs)), ch * rows + 20), (20, 20, 24))
        ImageDraw.Draw(sheet).text((6, 4), f'{p["label"]} {p.get("view", "")} ({tag}): frame 1 = the input frame', fill=(240, 240, 240))
        for i, im in enumerate(imgs):
            sheet.paste(im, ((i % cols) * cw, 20 + (i // cols) * ch))
        path = os.path.join(out_dir, f'{tag}_{p["label"]}_{p.get("view", "side")}.png')
        sheet.save(path)
        print('wrote', path)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--board':
        board(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        build(sys.argv[1])
