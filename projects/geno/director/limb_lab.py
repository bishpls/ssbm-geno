"""Limb lab: the rocket fists' growth in game (research/fist_read.md), beside Mario's grown fists. Geno (port 0) and Mario
(port 1) stand 42 apart on Final Destination and take turns; every attack whiffs (no hitlag), except the forward throw.
  mario_jab1, mario_fsmash, mario_fair   Mario's reference growth (the jab fist 2.24x, the forward smash's hand 1.44x,
                                         the forward air's fist 2.36x), toward Geno
  mario_bair, mario_utilt                the kick (legs 2.0x) and up tilt hand (to 3.0x) references
  geno_jab1, geno_jab2, geno_jab3, geno_utilt, geno_dashattack, geno_nair, geno_pummel (the body-contact normals), geno_fsmash, geno_fsmash_hi, geno_fsmash_lw, geno_grab, geno_dashgrab, geno_throwf (Mario held close, 40%)
LIMB_CAM=game (default) films with the game's own camera: the match framing players see, at the same spacing for every
segment (so every shot is at the same zoom); LIMB_CAM=close holds a fixed camera on the one who moves (dist LIMB_DIST,
default 58: his 27-unit Double Punch in frame). LIMB_COLL=1 shows the collision bubbles. LIMB_ONLY picks segments. Each segment opens with a two-frame sync
slate (the stage hidden on magenta), so the board lines each segment's images up with the log whatever the dump drops.
    LIMB_CAM=game .venv/bin/python tools/machinima/melee/build.py projects/geno limb_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --until 'DIRECTOR END' --res 2 --quiet
    .venv/bin/python projects/geno/director/limb_lab.py --board RUN [RUN.plan.json] OUT_DIR   # strips (PNG) per segment, a reel (mp4)
"""
import json, os, sys

GENO, MARIO = 0, 1
GX, MX = -21.0, 21.0
SYNC, LEAD = 10, 40
A = lambda at, n, stick=(0, 0), c=(0, 0), btn='': (at, n, stick, c, btn)
# (label, actor, frames, the actor's steps, Mario's x, the strip's animation frames (FEET's: the move's own numbering, as
#  the move scripts and datkit's movedata count them), the move: which of the actor's state changes after the input)
SEGS = [
    ('mario_jab1', MARIO, 50, [A(0, 2, btn='A')], MX, (1, 10), 1),
    ('mario_fsmash', MARIO, 70, [A(0, 3, c=(-80, 0))], MX, (8, 20), 1),
    ('mario_fair', MARIO, 90, [A(0, 2, btn='X'), A(6, 3, c=(-80, 0))], MX, (14, 26), 3),
    ('mario_bair', MARIO, 90, [A(0, 2, btn='X'), A(6, 3, c=(80, 0))], MX, (3, 14), 3),
    ('mario_utilt', MARIO, 50, [A(0, 4, (0, 50)), A(2, 2, (0, 50), btn='A')], MX, (2, 14), 1),
    ('geno_jab1', GENO, 45, [A(0, 2, btn='A')], MX, (1, 10), 1),
    ('geno_jab2', GENO, 55, [A(0, 2, btn='A'), A(8, 2, btn='A')], MX, (1, 9), 2),
    ('geno_jab3', GENO, 75, [A(0, 2, btn='A'), A(8, 2, btn='A'), A(16, 2, btn='A')], MX, (2, 12), 3),
    ('geno_utilt', GENO, 55, [A(0, 4, (0, 50)), A(2, 2, (0, 50), btn='A')], MX, (3, 14), 1),
    ('geno_dashattack', GENO, 75, [A(0, 12, (80, 0)), A(12, 2, (80, 0), btn='A')], MX + 20, (3, 15), 3),   # Dash, Run, AttackDash
    ('geno_nair', GENO, 80, [A(0, 6, btn='X'), A(8, 2, btn='A')], MX, (2, 22), 3),
    ('geno_pummel', GENO, 80, [A(0, 2, btn='Z'), A(30, 2, btn='A')], GX + 10, (5, 14), 4),
    ('geno_fsmash', GENO, 75, [A(0, 3, c=(80, 0))], MX, (12, 29), 1),
    ('geno_fsmash_hi', GENO, 75, [A(0, 3, (70, 40), btn='A')], MX, (12, 29), 1),
    ('geno_fsmash_lw', GENO, 75, [A(0, 3, (70, -40), btn='A')], MX, (12, 29), 1),
    ('geno_grab', GENO, 50, [A(0, 2, btn='Z')], MX, (3, 14), 1),
    ('geno_dashgrab', GENO, 70, [A(0, 10, (80, 0)), A(10, 2, (80, 0), btn='Z')], MX + 20, (5, 16), 2),
    ('geno_throwf', GENO, 120, [A(0, 2, btn='Z'), A(24, 4, (80, 0))], GX + 10, (15, 36), 4),
]


def plan_segs():
    only = [x for x in os.environ.get('LIMB_ONLY', '').split(',') if x]
    return [s for s in SEGS if not only or s[0] in only]


def build(out):
    from dsl import Film
    cam = os.environ.get('LIMB_CAM', 'game')
    dist = float(os.environ.get('LIMB_DIST', 58))
    segs = plan_segs()
    t, plan = 70, []
    for label, actor, n, steps, mx, span, nth in segs:
        plan.append(dict(label=label, actor=actor, start=t + LEAD, frames=n, sync=t + LEAD - SYNC, span=span, nth=nth,
                         mx=mx, cam=cam, dist=dist))
        t += LEAD + n
    f = Film(len_s=(t + 30) / 60)
    f.setup(players=[('geno', dict(x=GX, face=1)), ('mario', dict(x=MX, face=-1))], seed=5,
            coll=int(os.environ.get('LIMB_COLL', 0)))
    if cam == 'game':
        f.game_camera()
    ports = {GENO: f.port(GENO), MARIO: f.port(MARIO)}
    for i, p in enumerate(plan):
        label, actor, n, steps, mx, span, nth = segs[i]
        t0 = p['start']
        f.reset(t0 - LEAD, GENO, GX, 1); f.reset(t0 - LEAD, MARIO, mx, -1)
        f.percent(t0 - LEAD + 2, GENO, 0); f.percent(t0 - LEAD + 2, MARIO, 40)
        if cam == 'close':
            ax, d = (GX, 1) if actor == GENO else (mx, -1)
            track = 'p0' if label in ('geno_dashgrab', 'geno_dashattack') else None
            at = (8.0, 9.0, 0.0) if track else (ax + 12 * d, 9.0, 0.0)
            if label == 'geno_nair':                     # the full hop's apex (~30 up; the tracker lags a jump): the kick
                at = (ax, 34.0, 0.0)                     # lands behind him
            f.orbit(t0 - LEAD, at=at, dist=dist, yaw=0, pitch=4, fov=30,
                    ease='cut', track=track)
        f.cue(t0 - SYNC, 'stage', a=0); f.cue(t0 - SYNC, 'bgcolor', a=255, b=0, c=255)
        f.cue(t0 - SYNC + 2, 'stage', a=1); f.cue(t0 - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
        for at, k, stick, c, btn in steps:
            ports[actor].hold(t0 + at, k, stick=stick, c=c, btn=btn)
        ports[GENO].trace(t0 - 2, t0 + n - 1); ports[MARIO].trace(t0 - 2, t0 + n - 1)
        for k in range(n):                          # FEET lines carry the actor's animation frame: the strips' labels
            f.feet(t0 + k, actor)
        f.mark(t0, i, label)
    f.emit(out)
    json.dump(plan, open(os.path.splitext(out)[0] + '.plan.json', 'w'), indent=1)


def anim_frames(run):
    """(logic frame, port) -> (motion state, animation frame), from the FEET lines"""
    out = {}
    for l in open(os.path.join(run, 'osreport.log'), errors='replace'):
        q = l.split()
        if len(q) >= 15 and q[0] == 'FEET' and q[3] == '0':
            out[(int(q[1]), int(q[2]))] = (int(q[13]), float(q[14]))
    return out


def move_frames(d, af, p):
    """animation frame -> logic frame of the move (the actor's nth state change from the input on), from FEET"""
    ch = [(f, st) for f, st in d['ms'][p['actor']] if p['start'] <= f < p['start'] + p['frames']]
    f0, st = ch[p['nth'] - 1] if len(ch) >= p['nth'] else (p['start'], None)
    out = {}
    for s in range(f0, p['start'] + p['frames']):
        ms, fa = af.get((s, p['actor']), (None, None))
        if ms != st: break
        out.setdefault(int(round(fa)), s)
    return out


def board(run, plan_path, out_dir):
    """A strip per segment (every animation frame of its span, as FEET logs them; the camera's whole frame), each segment
    aligned on its own sync slate."""
    from PIL import Image, ImageDraw
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labs'))
    import aerials_strips as AS
    plan = json.load(open(plan_path))
    d = AS.load(run); AS.align(d, plan)
    os.makedirs(out_dir, exist_ok=True)
    tag = os.environ.get('LIMB_TAG', os.path.basename(run.rstrip('/')))
    W0, H0 = Image.open(os.path.join(run, d['frames'][0])).size
    af = anim_frames(run)
    out = {}
    for p in plan:
        mf = move_frames(d, af, p)
        a, b = p['span']
        cells = []
        for k in range(a, b + 1):
            if k not in mf: continue
            s = mf[k]
            idx = d['idx'](s)
            if not 0 <= idx < len(d['frames']): continue
            im = Image.open(os.path.join(run, d['frames'][idx])).convert('RGB')
            im = im.resize((W0 // (4 if p['cam'] == 'game' else 3), H0 // (4 if p['cam'] == 'game' else 3)), Image.LANCZOS)
            dr = ImageDraw.Draw(im)
            dr.rectangle([0, 0, 40, 13], fill=(0, 0, 0)); dr.text((3, 1), f'{k}', fill=(255, 255, 255))
            cells.append(im)
        if not cells: continue
        cols = int(os.environ.get('LIMB_COLS', 6 if p['cam'] == 'game' else 9))
        cw, ch = cells[0].size
        rows = (len(cells) + cols - 1) // cols
        sheet = Image.new('RGB', (cw * min(cols, len(cells)), ch * rows + 18), (20, 20, 24))
        ImageDraw.Draw(sheet).text((5, 3), f"{p['label']} ({tag}, {p['cam']} camera): the move's animation frames (FEET), as "
                                           f"its script counts them", fill=(240, 240, 240))
        for i, im in enumerate(cells):
            sheet.paste(im, ((i % cols) * cw, 18 + (i // cols) * ch))
        path = os.path.join(out_dir, f"{tag}_{p['label']}.png")
        sheet.save(path); out[p['label']] = path
        print('wrote', path)
    return out


_ALIGNED = {}


def frame_of(run, plan_path, label, k):
    """the full image of a segment's move on its animation frame k, aligned on the segment's slate"""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labs'))
    import aerials_strips as AS
    plan = {p['label']: p for p in json.load(open(plan_path))}
    key = (run, plan_path)
    if key not in _ALIGNED:
        import contextlib, io
        d = AS.load(run)
        with contextlib.redirect_stdout(io.StringIO()): AS.align(d, list(plan.values()))
        _ALIGNED[key] = d
    d = _ALIGNED[key]
    p = plan[label]
    mf = move_frames(d, anim_frames(run), p)
    return os.path.join(run, d['frames'][d['idx'](mf[k])])


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--board':
        run = sys.argv[2]
        plan = sys.argv[3] if len(sys.argv) > 4 else run.rstrip('/') + '.plan.json'
        board(run, plan, sys.argv[-1])
    else:
        build(sys.argv[1])
