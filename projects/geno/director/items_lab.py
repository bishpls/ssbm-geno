"""Items and character lab: Geno picks up the real items and uses each one (light throws in every direction, on the ground,
dashing and in the air; a crate carried and thrown; bat and Beam Sword swings; the Ray Gun; the Super Scope's rapid fire
and charge; the parasol; the hammer; the Screw Attack, worn and taken), then his taunt, his idle and the crouch with an
item. Each try spawns its item at his feet (the director's item cue, as the game's own drop), picks it up with A, and
drives the action by the pad, so the engine's own timing (the pick-up, the release frame) runs. The camera tracks him.
    .venv/bin/python tools/machinima/melee/build.py projects/geno items_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol OUT --frames N --res 2 --quiet
    .venv/bin/python projects/geno/director/items_lab.py --report OUT PLAN.json [BOARD_DIR]
    .venv/bin/python projects/geno/director/items_lab.py --releases OUT PLAN.json      # each throw's release frame
    .venv/bin/python projects/geno/director/items_lab.py --throws OUT PLAN.json BOARD_DIR [BEFORE_RUN]   # release strips
LAB_ONLY=a,b picks tries by label prefix; LAB_CAM=34 swings the camera that many degrees round (a 3/4 view); LAB_ENTRY=1
films the match start instead (his entrance on the trophy stand). With BOARD_DIR: a strip of every frame of each try's
actions (crops round him) and a contact sheet of the whole try.
"""
import glob, json, math, os, sys

GENO, FOX = 0, 1
# the decomp's motion states (ftCommon/forward.h) the report names
MS = {14: 'Wait', 15: 'WalkSlow', 16: 'WalkMiddle', 17: 'WalkFast', 18: 'Turn', 20: 'Dash', 21: 'Run', 24: 'KneeBend',
      25: 'JumpF', 26: 'JumpB', 27: 'JumpAerialF', 28: 'JumpAerialB', 29: 'Fall', 30: 'FallF', 31: 'FallB', 32: 'FallAerial',
      33: 'FallAerialF', 34: 'FallAerialB', 39: 'Squat', 40: 'SquatWait', 41: 'SquatRv', 42: 'Landing',
      92: 'LightGet', 93: 'HeavyGet', 94: 'LightThrowF', 95: 'LightThrowB', 96: 'LightThrowHi', 97: 'LightThrowLw',
      98: 'LightThrowDash', 99: 'LightThrowDrop', 100: 'LightThrowAirF', 101: 'LightThrowAirB', 102: 'LightThrowAirHi',
      103: 'LightThrowAirLw', 104: 'HeavyThrowF', 105: 'HeavyThrowB', 106: 'HeavyThrowHi', 107: 'HeavyThrowLw',
      108: 'LightThrowF4', 109: 'LightThrowB4', 110: 'LightThrowHi4', 111: 'LightThrowLw4', 112: 'LightThrowAirF4',
      113: 'LightThrowAirB4', 114: 'LightThrowAirHi4', 115: 'LightThrowAirLw4', 116: 'HeavyThrowF4', 117: 'HeavyThrowB4',
      118: 'HeavyThrowHi4', 119: 'HeavyThrowLw4', 120: 'SwordSwing1', 121: 'SwordSwing3', 122: 'SwordSwing4',
      123: 'SwordSwingDash', 124: 'BatSwing1', 125: 'BatSwing3', 126: 'BatSwing4', 127: 'BatSwingDash', 128: 'ParasolSwing1',
      132: 'HarisenSwing1', 136: 'StarRodSwing1', 140: 'LipstickSwing1', 144: 'ItemParasolOpen', 145: 'ItemParasolFall',
      146: 'ItemParasolFallSpecial', 147: 'ItemParasolDamageFall', 148: 'LGunShoot', 149: 'LGunShootAir',
      150: 'LGunShootEmpty', 151: 'LGunShootAirEmpty', 152: 'FireFlowerShoot', 153: 'FireFlowerShootAir', 154: 'ItemScrew',
      155: 'ItemScrewAir', 156: 'DamageScrew', 157: 'DamageScrewAir', 158: 'ItemScopeStart', 159: 'ItemScopeRapid',
      160: 'ItemScopeFire', 161: 'ItemScopeEnd', 162: 'ItemScopeAirStart', 163: 'ItemScopeAirRapid', 164: 'ItemScopeAirFire',
      165: 'ItemScopeAirEnd', 174: 'LiftWait', 175: 'LiftWalk1', 176: 'LiftWalk2', 177: 'LiftTurn', 264: 'AppealSR', 265: 'AppealSL',
      307: 'HammerWait', 308: 'HammerWalk', 309: 'HammerTurn', 310: 'HammerKneeBend', 311: 'HammerFall', 312: 'HammerJump',
      313: 'HammerLanding', 322: 'Entry', 323: 'EntryStart', 324: 'EntryEnd'}
SLOT = 170
SYNC = 20

A, Z, X = 'A', 'Z', 'X'
tilt = lambda sx, sy, at: [(at, 3, (sx, sy), A)]      # stick and button together (a lead would walk first)
hop = [(24, 6, (0, 0), X)]                             # a full hop: airborne from +30
air = lambda sx, sy: hop + [(32, 3, (sx, sy), A)]     # thrown just after take-off (a smash throw: the same animation)
ramp = lambda at, n, sy: [(at + k, 1, (0, int(sy * (k + 1) / 4)), '') for k in range(3)] + [(at + 3, n, (0, sy), '')]
# (label, item, [(frame offset from the pick-up, frames, stick, buttons)]); frame 0 presses A over the item. After each
# try but the last two, Z throws or drops whatever he still holds, so the next pick-up finds its own item.
TESTS = [
    ('drop', 'bat', [(30, 3, (0, 0), Z)]),             # first, away from where the others' discards land (it stays down)
    # light throws with a bat (Z and a direction throws any held item; the animations are the same for every item, and a
    # bat neither walks off like Mr. Saturn, slides like a Freezie, nor breaks open like a capsule)
    ('throw_f', 'bat', [(30, 3, (48, 0), Z)]),
    ('throw_b', 'bat', [(30, 3, (-48, 0), Z)]),
    ('throw_hi', 'bat', [(30, 3, (0, 52), Z)]),
    ('throw_lw', 'bat', [(30, 3, (0, -52), Z)]),
    ('throw_dash', 'bat', [(24, 14, (80, 0), ''), (36, 2, (80, 0), Z)]),
    ('air_f', 'bat', hop + [(26, 9, (48, 0), ''), (32, 3, (48, 0), Z)]),   # the stick held first: not a smash
    ('air_b', 'bat', hop + [(26, 9, (-48, 0), ''), (32, 3, (-48, 0), Z)]),   # the stick held first: not a smash
    ('air_hi', 'bat', hop + [(26, 9, (0, 52), ''), (32, 3, (0, 52), Z)]),   # the stick held first: not a smash
    ('air_lw', 'bat', hop + [(26, 9, (0, -52), ''), (32, 3, (0, -52), Z)]),   # the stick held first: not a smash
    # smash throws (the stick flicked with Z): the same animations as the light throws, their own scripts
    ('throw_f4', 'bat', [(30, 3, (80, 0), Z)]),
    ('throw_b4', 'bat', [(30, 3, (-80, 0), Z)]),
    ('throw_hi4', 'bat', [(30, 3, (0, 80), Z)]),
    ('throw_lw4', 'bat', [(30, 3, (0, -80), Z)]),
    ('air_f4', 'bat', hop + [(32, 3, (80, 0), Z)]),
    ('air_b4', 'bat', hop + [(32, 3, (-80, 0), Z)]),
    ('air_hi4', 'bat', hop + [(32, 3, (0, 80), Z)]),
    ('air_lw4', 'bat', hop + [(32, 3, (0, -80), Z)]),
    ('squat_item', 'bat', [(24, 70, (0, -80), '')]),
    ('bat_1', 'bat', [(30, 2, (0, 0), A)]),
    ('bat_3', 'bat', tilt(48, 0, 30)),
    ('bat_4', 'bat', [(30, 3, (80, 0), A)]),
    ('bat_dash', 'bat', [(24, 14, (80, 0), ''), (36, 2, (80, 0), A)]),
    ('sword_1', 'sword', [(30, 2, (0, 0), A)]),
    ('sword_3', 'sword', tilt(48, 0, 30)),
    ('sword_4', 'sword', [(30, 3, (80, 0), A)]),
    ('sword_dash', 'sword', [(24, 14, (80, 0), ''), (36, 2, (80, 0), A)]),
    ('raygun', 'raygun', [(30, 2, (0, 0), A), (70, 6, (0, 0), X), (84, 2, (0, 0), A)]),
    ('scope_rapid', 'scope', [(30, 2, (0, 0), A), (38, 2, (0, 0), A), (46, 2, (0, 0), A)]),
    ('scope_charge', 'scope', [(30, 50, (0, 0), A)]),
    ('scope_air', 'scope', hop + [(32, 2, (0, 0), A), (40, 2, (0, 0), A)]),
    ('parasol', 'parasol', hop + ramp(58, 90, 64)),
    ('flower', 'flower', [(30, 30, (0, 0), A)]),
    ('hammer', 'hammer', [(30, 50, (60, 0), ''), (95, 40, (0, 0), ''), (150, 30, (-60, 0), ''), (200, 6, (0, 0), X)]),
    ('screw', 'screw', [(30, 6, (0, 0), X), (48, 2, (0, 0), X)]),
    # heavy last: a thrown crate that breaks open may roll for an item drop, and with the director's items off the pick
    # table is empty and the game hangs (itdrop.c -> it_8026C65C; a lab artifact: in play the table exists)
    ('heavy_walk_f', 'crate', [(50, 90, (60, 0), ''), (145, 3, (48, 0), A)]),
    ('heavy_b', 'crate', [(50, 3, (-48, 0), A)]),
    ('heavy_hi', 'crate', [(50, 3, (0, 52), A)]),
    ('heavy_lw', 'crate', [(50, 3, (0, -52), A)]),
]
KEEPS = ('hammer', 'drop')                             # unthrowable, or already put down: no discard (the screw throws)
# the character tries: no item
CHAR = [
    ('blind', None, []),                               # ItemBlind: no state plays it; the director's anim cue does (below)
    ('taunt', None, [(10, 2, (0, 0), 'DU')]),
    ('taunt3q', None, [(10, 2, (0, 0), 'DU')]),
    ('idle', None, []),
    ('idle3q', None, []),
]


def plan_tests():
    only = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
    tests = CHAR + TESTS
    return [t for t in tests if not only or any(t[0].startswith(o) for o in only)]


def report(run, plan_path, board=None):
    plan = json.load(open(plan_path))
    log = [l.split() for l in open(os.path.join(run, 'osreport.log'), errors='replace')]
    ms = [(int(l[1]), int(l[2]), int(l[3])) for l in log if l and l[0] == 'MS' and len(l) >= 4]
    items = [' '.join(l) for l in log if l and l[0] == 'ITEM']
    frames = sorted(glob.glob(os.path.join(run, 'f*.png')))
    first = None
    if frames:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'machinima'))
        from plates import is_slate
        for i, f in enumerate(frames[:400]):
            if is_slate(f): first = i + 1
            elif first is not None: break
    for l in items: print(l)
    for p in plan:
        t0, t1 = p['t0'], p['t0'] + p['slot']
        seq = [(s - t0, m) for s, port, m in ms if port == GENO and t0 - 30 <= s < t1]
        print(f"== {p['label']} ({p['item']}): " + ' '.join(f'{f}:{MS.get(m, m)}' for f, m in seq))
        if board and first is not None:
            spans = []                              # every frame of each of his actions but the idles
            for k, (f, m) in enumerate(seq):
                end = seq[k + 1][0] if k + 1 < len(seq) else p['slot']
                if m in (14, 29) or f < -5: continue
                spans.append((MS.get(m, str(m)), max(f - 2, -5), min(end + 2, p['slot'])))
            if p['label'].startswith(('idle', 'taunt')):
                spans = [('Wait' if p['label'].startswith('idle') else 'Appeal', 8, p['slot'] - 2)]
            for name, a, b in spans:
                strip(frames, first, t0, a, b, board, f"{p['label']}_{name}")
            sheet(frames, first, t0, p['slot'], board, p['label'])


def crop(frames, first, s):
    from PIL import Image
    i = first + s
    if not (0 <= i < len(frames)): return None
    im = Image.open(frames[i]).convert('RGB')
    w, h = im.size
    return im.crop((int(w * 0.28), int(h * 0.1), int(w * 0.72), int(h * 0.9)))


def strip(frames, first, t0, a, b, board, name, cols=10):
    from PIL import Image, ImageDraw
    ims = [(k, crop(frames, first, t0 + k)) for k in range(a, b)]
    ims = [(k, im) for k, im in ims if im is not None]
    if not ims: return
    if len(ims) > 60:                                # long actions: every other frame
        ims = ims[::2]
    cw, ch = ims[0][1].size
    sc = 200 / cw
    W, H = int(cw * sc), int(ch * sc)
    out = Image.new('RGB', (W * min(cols, len(ims)), H * ((len(ims) + cols - 1) // cols) + 20), (20, 20, 24))
    d = ImageDraw.Draw(out)
    d.text((6, 4), name, fill=(240, 240, 240))
    for n, (k, im) in enumerate(ims):
        x, y = (n % cols) * W, 20 + (n // cols) * H
        out.paste(im.resize((W, H)), (x, y))
        d.text((x + 4, y + 4), f'+{k}', fill=(255, 255, 0))
    os.makedirs(board, exist_ok=True)
    out.save(os.path.join(board, f'strip_{name}.png'))


def sheet(frames, first, t0, slot, board, label):
    strip(frames, first, t0, -10, slot, board, f'{label}_sheet', cols=16)


def releases(run, plan_path):
    """per throw try: the throw's state and the animation frame its item left the hand on (the director's LETGO line: the
    hand's item slot empties), from the run's log"""
    plan = json.load(open(plan_path))
    log = [l.split() for l in open(os.path.join(run, 'osreport.log'), errors='replace')]
    out = {}
    for p in plan:
        t0, t1 = p['t0'], p['t0'] + p['slot'] - 64
        for l in log:
            if l and l[0] == 'LETGO' and l[2] == str(GENO) and t0 <= int(l[1]) < t1:
                out[p['label']] = dict(s=int(l[1]), state=int(l[4]), name=MS.get(int(l[4]), l[4]), anim=float(l[6]))
                break
    return out


def throws_board(run, plan_path, board, labels=None, before=None):
    """A strip per throw try: the throw's animation frames from 1 to 8 past the release, labelled by the action's own
    frame (FEET), each try aligned on its sync slate; the frame the item left the hand (LETGO) is outlined in red. With
    before (another run of the same lab), its row goes above."""
    from PIL import Image, ImageDraw
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labs'))
    import aerials_strips as AS, contextlib, io
    plan = json.load(open(plan_path))
    rows_for = []
    for r in ([before] if before else []) + [run]:
        d = AS.load(r)
        with contextlib.redirect_stdout(io.StringIO()): AS.align(d, plan)
        feet = {}
        for l in open(os.path.join(r, 'osreport.log'), errors='replace'):
            q = l.split()
            if len(q) >= 15 and q[0] == 'FEET' and q[2] == str(GENO) and q[3] == '0':
                feet[int(q[1])] = (int(q[13]), float(q[14]))
        rows_for.append((r, d, feet, releases(r, plan_path)))
    os.makedirs(board, exist_ok=True)
    out = {}
    for p in plan:
        if labels and p['label'] not in labels: continue
        rows = []
        for r, d, feet, rel in rows_for:
            if p['label'] not in rel: continue
            st, ra = rel[p['label']]['state'], rel[p['label']]['anim']
            fr = {}
            for s_, (ms, a) in sorted(feet.items()):
                if p['t0'] <= s_ < p['t0'] + p['slot'] and ms == st: fr.setdefault(int(round(a)), s_)
            cells = []
            for k in range(1, int(ra) + 9):
                if k not in fr: continue
                i = d['idx'](fr[k])
                if not 0 <= i < len(d['frames']): continue
                im = Image.open(os.path.join(r, d['frames'][i])).convert('RGB')
                w, h = im.size
                im = im.crop((int(w * 0.25), int(h * 0.12), int(w * 0.75), int(h * 0.88))).resize((200, int(200 * 0.76 * h / (0.5 * w))))
                dr = ImageDraw.Draw(im)
                if k == int(ra):
                    dr.rectangle([0, 0, im.width - 1, im.height - 1], outline=(255, 40, 40), width=4)
                dr.rectangle([0, 0, 64, 13], fill=(0, 0, 0))
                dr.text((3, 1), f'{k}' + (' let go' if k == int(ra) else ''), fill=(255, 255, 255))
                cells.append(im)
            rows.append((os.path.basename(r.rstrip('/')), rel[p['label']], cells))
        if not rows: continue
        cw, ch = rows[0][2][0].size
        n = max(len(c) for _, _, c in rows)
        sheet_ = Image.new('RGB', (cw * n, (ch + 16) * len(rows) + 4), (20, 20, 24))
        dr = ImageDraw.Draw(sheet_)
        for j, (name, rel, cells) in enumerate(rows):
            y = j * (ch + 16)
            dr.text((4, y + 2), f"{p['label']} ({name}): {rel['name']}, the item left the hand on animation frame {rel['anim']:g}",
                    fill=(240, 240, 240))
            for i, im in enumerate(cells):
                sheet_.paste(im, (i * cw, y + 16))
        path = os.path.join(board, f"throw_{p['label']}.png")
        sheet_.save(path); out[p['label']] = path
    return out


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--releases':
    for k, v in releases(sys.argv[2], sys.argv[3]).items(): print(k, v)
    sys.exit()

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--throws':
    print(throws_board(sys.argv[2], sys.argv[3], sys.argv[4], before=sys.argv[5] if len(sys.argv) > 5 else None)); sys.exit()

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--report':
    report(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None); sys.exit()

from dsl import Film
yaw = float(os.environ.get('LAB_CAM', 0))
if os.environ.get('LAB_ENTRY'):
    # the match start: the director's entry flag plays every fighter's entrance (EntryStart, EntryEnd, then Wait)
    f = Film(len_s=6.0)
    f.setup(players=[('geno', dict(x=-10, face=1)), ('fox', dict(x=40, face=-1))], seed=3, entry=True)
    f.orbit(0, at=(0, 7, 0), dist=48, yaw=yaw, pitch=4, fov=30, ease='cut', track='p0')
    f.emit(sys.argv[1])
    json.dump([dict(label='entry', item=None, t0=0, slot=330)], open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
    sys.exit()

tests = plan_tests()
slots = [SLOT + 60 + (70 if t[0].startswith('heavy_walk') else 0) + (310 if t[0].startswith(('idle', 'blind')) else 0) +
         (420 if t[0] == 'hammer' else 0) for t in tests]    # the hammer lasts about 8 s: gone before the next try
f = Film(len_s=(sum(slots) + 120) / 60)
f.setup(players=[('geno', dict(x=0, face=1)), ('fox', dict(x=70, face=-1))], seed=3)
geno, fox = f.port(GENO), f.port(FOX)
dist = float(os.environ.get('LAB_DIST', 52))
f.orbit(0, at=(0, 7, 0), dist=dist, yaw=yaw, pitch=4, fov=30, ease='cut', track='p0')
plan, t0 = [], 100
X0 = -30.0
for (label, item, steps), slot in zip(tests, slots):
    # each try's camera: side on (or LAB_CAM), a 3/4 view for the tries labelled ...3q
    # airborne tries look from farther and higher (the tracking lags a full hop), dashes from farther (it lags a dash)
    high = label.startswith(('air', 'scope_air', 'parasol', 'screw'))
    far = high or 'dash' in label
    f.orbit(t0 - 66, at=(0, 16 if high else 7, 0), dist=dist * (1.5 if far else 1), yaw=35 if label.endswith('3q') else yaw,
            pitch=4, fov=30, ease='cut', track='p0')
    x0 = 10.0 if label == 'drop' else X0
    f.reset(t0 - 64, GENO, x0, 1)
    f.reset(t0 - 64, FOX, 80, -1)
    if item:
        f.item(t0 - 60, item, x0, 2.0)             # it drops to his feet
        geno.hold(t0, 2, btn=A)                     # the pick-up
    for at, n, stick, btn in steps:
        geno.hold(t0 + at, n, stick=stick, btn=btn)
    if item and label not in KEEPS:
        geno.hold(t0 + slot - 92, 3, stick=(60, 0), btn=Z)   # rid of it before the next try's reset (at slot - 64, which cuts
                                                         # a throw short of its release): thrown forward, away (a neutral
                                                         # Z drops a bat at his feet, where the next pick-up is)
    if os.environ.get('LAB_TRACE'):                  # the director's per-frame POS lines for him (the hip joint's path)
        geno.trace(t0 - 5, t0 + slot - 60)
    if label == 'blind':                             # ItemBlind (action 148) through the engine's idle-variant player,
        f.reset(t0 - 64, FOX, x0 + 16, -1)           # Geno's and, beside him, Fox's (the cast's own)
        f.anim(t0 + 10, GENO, 148); f.anim(t0 + 10, FOX, 148)
    # a sync slate per try (the stage hidden on magenta for two frames) and his animation frame every frame (FEET), so the
    # strips line each try's images up with the log and label them by the action's own frames
    f.cue(t0 - SYNC, 'stage', a=0); f.cue(t0 - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t0 - SYNC + 2, 'stage', a=1); f.cue(t0 - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    for k in range(-2, slot - 64):
        f.feet(t0 + k, GENO)
    f.mark(t0, len(plan), label)
    plan.append(dict(label=label, item=item, t0=t0, slot=slot, sync=t0 - SYNC, start=t0 - 2, frames=slot - 62))
    t0 += slot
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
