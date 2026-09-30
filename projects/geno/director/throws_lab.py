"""Throws lab (DESIGN §6f): Geno grabs a standing Fox on Final Destination and throws him, one try per slot, at chosen
percents and DI, and the report measures each throw from the director's log:
  - the carry: Fox's position every frame of the throw (POS), and where he leaves from on the release;
  - the launch: its angle and knockback, from Fox's first frames of flight (knockback x 0.03 is the launch speed; the
    gravity and knockback decay of those frames are added back) and the knockback formula's own value;
  - the projectile hits (IHIT) and their damage, and Fox's percent after;
  - the regrab race: after the release Fox mashes jump (and holds his DI), so his first action (a jump, an aerial jump, a
    tech, a landing he can act out of) is his first actionable frame; Geno's is the end of the throw. A regrab needs Fox
    grounded and unable to act by the time Geno's fastest grab could reach him.
Strips (every other frame of each throw, cropped on the pair) go to the board folder and --mp4 cuts a reel.

    .venv/bin/python tools/machinima/melee/build.py projects/geno throws_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol OUT --frames N --res 2 --quiet
    .venv/bin/python projects/geno/director/throws_lab.py --report OUT PLAN.json [BOARD_DIR] [--mp4 OUT.mp4]
LAB_SET picks a test set:
  look     each throw at 0%, no DI, a close side camera (strips, the reel); cam34 the same from a 3/4 camera; match
           the same on the game's own camera (the match framing). These three are watched: a sync slate before each
           try (the stage hidden on magenta for two frames), his animation frame every frame (FEET) and both fighters'
           hurtboxes (SHIELD's HURT lines) through the throw, for --board and --line
  di       each throw at 0% with no DI and full DI either side of the launch (angles, the stars DI slips)
  height   each throw at 0, 30 and 60% (peak height, airtime, landing); LAB_THROWER=fox or falco for the cast's
  regrab   each throw at 0-60% with no DI, full DI either side, and DI in and out, Fox mashing jump
  try      real regrab attempts after the up throw (a dash grab timed to his landing), no DI and DI in: Geno grabs on
           the frame he is free (the up throw's length, from poses_throws) and 2, 4 and 6 frames after
  weights  each throw at 0% on LAB_VICTIM (falco, falcon: throws use one weight for everyone, so the launch is Fox's)
  stars    the up throw at LAB_PCTS (0,30,60,90,120) with no DI and full DI either side, watched: the stars that hit
  kill     the back and forward throws near the ledge at 80-180%, no DI and full DI either side (a clean KO: Fox dies
           before he can act)
LAB_COLL=1 shows hitboxes and hurtboxes.

    .venv/bin/python projects/geno/director/throws_lab.py --board RUN PLAN OUT_DIR [BEFORE_RUN BEFORE_PLAN]
            [--only THROW --crop X0,Y0,X1,Y1 --width PX]
        a strip per throw of a watched run, labelled by his animation frame and aligned on the sync slates, the rows
        (before above) lined up on the blast (the release; the up throw's first star), so a longer wind-up shows as
        cells to the left; --crop (fractions of the image) and --only make a detail strip
    .venv/bin/python projects/geno/director/throws_lab.py --grip RUN PLAN [OUT.json]
        the held opponent against his holding hand, each frame to the release of each watched throw: the gap between
        the hand's hurtbox and their nearest one (+ apart, - overlapping; the up throw: the nearer hand; the back throw
        from the cannon's lock: the forearm, which the cannon sheathes), and their body's centre frame to frame: its
        steps while held and the pop into the flight (the release frame's step less the flight's first)
    .venv/bin/python projects/geno/director/throws_lab.py --line RUN PLAN
        the forward throw's read in the game: the rocket fist's line (his hand's path from the frame before the launch
        to the release) and how far the opponent's body (the mean of their hurtboxes' midpoints) and its top sit off
        it, each frame (+ above)
"""
import glob, json, math, os, shutil, subprocess, sys

GENO, FOX = 0, 1
L = 85.6                      # Final Destination's ledges at x = +-85.6
THROW_STICK = dict(fthrow=(80, 0), bthrow=(-80, 0), uthrow=(0, 80), dthrow=(0, -80))
LAUNCH = dict(fthrow=35, bthrow=145, uthrow=90, dthrow=40)          # design angles, facing right (the back throw's reversed)
MS = {14: 'Wait', 29: 'Fall', 24: 'KneeBend', 25: 'JumpF', 26: 'JumpB', 27: 'JumpAerialF', 28: 'JumpAerialB', 42: 'Landing',
      38: 'DamageFall', 75: 'DamageHi1', 78: 'DamageN1', 84: 'DamageAir1', 85: 'DamageAir2', 86: 'DamageAir3',
      87: 'DamageFlyHi', 88: 'DamageFlyN', 89: 'DamageFlyLw', 90: 'DamageFlyTop', 91: 'DamageFlyRoll', 183: 'DownBoundU',
      184: 'DownWaitU', 191: 'DownBoundD', 192: 'DownWaitD', 199: 'Passive', 200: 'PassiveStandF', 201: 'PassiveStandB',
      212: 'Catch', 213: 'CatchPull', 216: 'CatchWait', 219: 'ThrowF', 220: 'ThrowB', 221: 'ThrowHi', 222: 'ThrowLw',
      226: 'CapturePulledLw', 227: 'CaptureWaitLw', 223: 'CapturePulledHi', 224: 'CaptureWaitHi', 239: 'ThrownF',
      240: 'ThrownB', 241: 'ThrownHi', 242: 'ThrownLw', 236: 'EscapeAir', 35: 'FallSpecial', 43: 'LandingFallSpecial'}
THROWN = (239, 240, 241, 242)
# the dumped image first + s - LAG shows game frame s (measured: a Finger Shot spawned on frame s shows its flash there)
LAG = 4
ACT = {24, 25, 26, 27, 28, 199, 200, 201, 236, 14, 178, 179}             # states that show Fox acting (or free to)


SYNC = 20                     # a watched try's sync slate: this many frames before its t0
RIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rig')


def throw_def(name):
    """the throw as poses_throws defines it (its length, release, shots and events)"""
    sys.path.insert(0, RIG)
    import poses_throws
    return poses_throws.THROWS[name]


def tests():
    which = os.environ.get('LAB_SET', 'look')
    out = []
    if which in ('look', 'cam34', 'match'):
        for th in ('fthrow', 'bthrow', 'uthrow', 'dthrow'):
            out.append(dict(label=th, throw=th, pct=0, di=None, slot=170, watch=True,
                            cam=dict(cam34='34', match='game').get(which, 'side')))
    elif which == 'di':
        for th in ('fthrow', 'bthrow', 'uthrow', 'dthrow'):
            for di in (None, 'cw', 'ccw'):
                out.append(dict(label=f'{th}_{di or "none"}', throw=th, pct=0, di=di, slot=170, cam='wide'))
    elif which == 'height':                              # launch heights at 0-60% (compare with LAB_THROWER=fox, falco)
        for th in ('uthrow', 'fthrow', 'bthrow', 'dthrow'):
            for pct in (0, 30, 60):
                out.append(dict(label=f'{th}_{pct}', throw=th, pct=pct, di=None, slot=170, cam='wide'))
    elif which == 'try':                                  # real regrab attempts: Geno grabs on a chosen frame after the throw
        free = throw_def('ThrowHi').n - 1                 # his first free frame, from the throw's first
        for pct in (0, 20, 40):
            for at in (free, free + 2, free + 4, free + 6):
                for di in (None, 'in'):
                    out.append(dict(label=f'uthrow_{pct}_{di or "none"}_grab{at}', throw='uthrow', pct=pct, di=di, slot=200,
                                    cam='wide', grab_at=at, dash=True, mash=True))
    elif which == 'doubles':                              # the stars hit a bystander: Falco full-jumps over Geno during
        for di in ('cw', 'ccw'):                          # the salvo while Fox DIs away from it (LAB_SET=doubles adds Falco)
            out.append(dict(label=f'uthrow_0_{di}_bystander', throw='uthrow', pct=0, di=di, slot=170, cam='wide',
                            bystander=True))
    elif which == 'stars':                                # the up throw's salvo against simple DI (full left or right)
        pcts = [int(x) for x in os.environ.get('LAB_PCTS', '0,30,60,90,120').split(',')]
        for pct in pcts:
            for di in (None, 'cw', 'ccw'):
                out.append(dict(label=f'uthrow_{pct}_{di or "none"}', throw='uthrow', pct=pct, di=di, slot=170, cam='wide',
                                watch=True))
    elif which == 'weights':                              # the 0% launches (tumble or not) on a victim (LAB_VICTIM)
        for th in ('fthrow', 'bthrow', 'uthrow', 'dthrow'):
            for di in (None, 'in'):
                out.append(dict(label=f'{th}_0_{di or "none"}', throw=th, pct=0, di=di, slot=170, cam='wide'))
    elif which == 'regrab':
        for th in ('fthrow', 'bthrow', 'uthrow', 'dthrow'):
            for pct in (0, 20, 40, 60):
                for di in (None, 'cw', 'ccw', 'in', 'out'):
                    out.append(dict(label=f'{th}_{pct}_{di or "none"}', throw=th, pct=pct, di=di, slot=200, cam='wide', mash=True))
    elif which == 'kill':
        pcts = [int(x) for x in os.environ.get('LAB_PCTS', '80,100,120,140,160,180').split(',')]
        for th in ('bthrow', 'fthrow'):
            for pct in pcts:
                for di in (None, 'cw', 'ccw'):
                    out.append(dict(label=f'{th}_{pct}_{di or "none"}', throw=th, pct=pct, di=di, slot=520, cam='wide',
                                    ledge=True, mash=True))
    only = [x for x in os.environ.get('LAB_ONLY', '').split(',') if x]
    return [t for t in out if not only or t['label'] in only or t['throw'] in only]


def di_stick(t, face):
    """Full DI perpendicular to the throw's launch (cw or ccw of it), or in toward Geno / out away along the ground."""
    if t['di'] is None: return None
    if t['di'] in ('in', 'out'):
        return (-80 * face if t['di'] == 'in' else 80 * face, 0) if t['throw'] != 'bthrow' else \
               (80 * face if t['di'] == 'in' else -80 * face, 0)
    ang = LAUNCH[t['throw']]
    a = math.radians(ang + (90 if t['di'] == 'ccw' else -90))
    return (int(round(80 * math.cos(a))) * face, int(round(80 * math.sin(a))))


# ------------------------------------------------------------------------------------------------ the report
def first_frame(run):
    """the dumped frames, the index of the first frame after the opening slate (script frame 0), and the slate's first"""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'machinima'))
    from plates import is_slate
    frames = sorted(glob.glob(os.path.join(run, 'f*.png')))
    first = start = None
    for i, f in enumerate(frames[:400]):
        if is_slate(f):
            first = i + 1
            if start is None: start = i
        elif first is not None: break
    return frames, first, start


# Geno's fastest grabs from standing (DESIGN §9 regrab race; research/cast_moves.md): a standing grab's box is out on
# frame 7 with reach 13.5, a dash grab's on frame 9 with 16.4 (its slide included); a dash covers 1.35 on its first
# frame, then 0.08 more a frame to 1.6. Fox's body adds ~3.2 past his centre. Fox is grabbable on the ground (or within
# 3 units of it) and not lying down.
GRAB = (7, 13.5)
DASH_GRAB = (9, 16.4)
BODY = 3.2
DOWN_STATES = (183, 184, 191, 192)


def regrab(fp, g0, free, fox_act):
    """The earliest frame Geno's grab could land on Fox (standing grab, or a dash of k frames then a dash grab), against
    the frame Fox can first act. Returns (earliest grab frame or None, Fox's first action frame, verdict)."""
    best = None
    gx = g0[0]
    for k in range(0, 60):                                  # dash k frames (k = 0: a standing grab)
        moved = sum(min(1.6, 1.35 + 0.08 * i) for i in range(k))
        hit = free + k + (GRAB[0] - 1 if k == 0 else DASH_GRAB[0] - 1)
        reach = (GRAB[1] if k == 0 else DASH_GRAB[1]) + BODY
        if hit not in fp: continue
        fx, fy, fm = fp[hit]
        d = abs(fx - gx) - moved
        if d <= reach and fy <= 3.0 and fm not in DOWN_STATES:
            best = hit; break
    verdict = 'no regrab' if best is None or (fox_act is not None and fox_act <= best) else 'REGRAB'
    return verdict, best, fox_act


def analyse(log, p):
    t0, t1 = p['t0'], p['t0'] + p['slot'] - 10
    pos = {}
    for l in log:
        if l and l[0] == 'POS' and len(l) >= 8 and t0 <= int(l[1]) < t1:
            pos[(int(l[1]), int(l[2]))] = (float(l[3]), float(l[4]), int(l[5]))
    ms = [(int(l[1]), int(l[2]), int(l[3])) for l in log if l and l[0] == 'MS' and t0 <= int(l[1]) < t1]
    hits = [(int(l[1]), l[0], float(l[4] if l[0] == 'HIT' else l[3])) for l in log
            if l and l[0] in ('HIT', 'IHIT') and t0 <= int(l[1]) < t1]
    kbl = [l for l in log if l and l[0] == 'GENO' and len(l) > 2 and l[1] == 'THROWKB']
    fox = sorted((f, v) for (f, port), v in pos.items() if port == FOX)
    geno = sorted((f, v) for (f, port), v in pos.items() if port == GENO)
    r = dict(label=p['label'])
    thrown = [f for f, v in fox if v[2] in THROWN]
    throw_ms = [(f, m) for f, port, m in ms if port == GENO and m in (219, 220, 221, 222)]
    if not thrown or not throw_ms:
        r['error'] = 'no throw'; return r
    ts = throw_ms[0][0]
    rel = max(thrown) + 1
    r['throw_start'] = ts
    r['release'] = rel - ts                                  # frames from the throw's first frame
    fp = dict(fox)
    gp = dict(geno)
    face = p.get('face', 1)
    if rel in fp:
        r['release_pos'] = (round((fp[rel][0] - gp[ts][0]) * face, 2), round(fp[rel][1], 2))
    kb = [l for l in kbl if l in log[p['_lo']:p['_hi']]] if '_lo' in p else []
    if kb:
        k = kb[0]                                   # GENO THROWKB motion kb K angle A vel VX VY pct P
        vx, vy = float(k[8]), float(k[9])
        ang = math.degrees(math.atan2(vy, vx * face))
        r['kb'] = float(k[4]); r['hit_angle'] = int(k[6])
        r['launch_angle'] = round(ang if ang >= 0 else ang + 360, 1)
        r['kb'] = round((math.hypot(vx, vy) + 0.051) / 0.03, 1)     # the launch speed a frame on (kb_applied is spent)
        r['tumble'] = r['kb'] >= 80
        r['hitstun'] = int(r['kb'] * 0.4)
    after = [(f, v) for f, v in fox if f >= rel]
    if after:
        pk = max(after, key=lambda fv: fv[1][1])
        r['peak'] = (pk[0] - ts, round(pk[1][1], 1))                  # Fox's highest point (his position's y) and when
        gnd = [f for f, v in after if f > rel + 2 and v[1] <= 0.05]
        r['airtime'] = (gnd[0] - rel) if gnd else None
    down = [f for f, v in fox if f > rel and v[2] in (183, 191, 42, 199, 200, 201, 24, 14) and v[1] < 1.0]
    if down:
        r['lands'] = (down[0] - ts, round((fp[down[0]][0] - gp[ts][0]) * face, 1), MS.get(fp[down[0]][2], fp[down[0]][2]))
    r['hits'] = [(f - ts, kind, d) for f, kind, d in hits]
    if '_lo' in p:                                  # the up throw's stars: (animation frame, angle, spray toward his front)
        st = [l for l in log[p['_lo']:p['_hi']] if l[:3] == ['GENO', 'THROWSHOT', 'star']]
        if st:
            r['stars'] = [(int(l[3]), int(l[6]), int(l[8]) if len(l) > 8 else 0) for l in st]
            r['star_hits'] = sum(1 for _, kind, _ in hits if kind == 'IHIT')
    end = [f for f, port, m in ms if port == GENO and f > ts and m not in (219, 220, 221, 222)]
    r['geno_free'] = (end[0] - ts) if end else None
    act = [(f, m) for f, port, m in ms if port == FOX and f > rel and m in ACT]
    r['fox_act'] = (act[0][0] - ts, MS.get(act[0][1], act[0][1])) if act else None
    seq, prev = [], None
    for f, v in fox:
        if v[2] != prev and f >= ts: seq.append(f'{f - ts}:{MS.get(v[2], v[2])}'); prev = v[2]
    r['fox_states'] = ' '.join(seq)
    dead = [f for f, port, m in ms if port == FOX and f > rel and 0 <= m <= 10]
    acts = [f for f, port, m in ms if port == FOX and f > rel and m in (27, 28, 236, 35)]
    if dead:
        r['KO'] = 'clean KO' if not acts or dead[0] < acts[0] else 'KO after acting'
    elif p.get('ledge'):
        r['KO'] = 'lives'
    if end:
        v, best, fa = regrab(fp, gp[end[0]], end[0], act[0][0] if act else None)
        r['regrab'] = (v, 'grab at', best - ts if best else None, 'Fox acts at', fa - ts if fa else None)
    r['carry'] = [(f - ts, round((fp[f][0] - gp[ts][0]) * face, 2), round(fp[f][1], 2)) for f in thrown if f in fp]
    if r['carry']:                          # the carry's reach toward and away from him (Fox's position from Geno's)
        xs = [x for _, x, _ in r['carry']]
        r['carry_x'] = (min(xs), max(xs))
    return r


def report(run, plan_path, board=None, mp4=None):
    plan = json.load(open(plan_path))
    log = [l.split() for l in open(os.path.join(run, 'osreport.log'), errors='replace')]
    # attribute the frameless GENO lines to the slot whose frames surround them in the log
    lastf, owner = 0, []
    for l in log:
        if l and l[0] in ('POS', 'MS', 'HIT', 'IHIT', 'MARK', 'LASER') and len(l) > 1 and l[1].lstrip('-').isdigit():
            lastf = int(l[1])
        owner.append(lastf)
    for p in plan:
        idx = [i for i, f in enumerate(owner) if p['t0'] <= f < p['t0'] + p['slot']]
        p['_lo'], p['_hi'] = (idx[0], idx[-1] + 1) if idx else (0, 0)
    frames, first, slate = first_frame(run) if (board or mp4) else ([], None, None)
    res = []
    for p in plan:
        r = analyse(log, p)
        res.append(r)
        print(f"== {r['label']}: " + ', '.join(f'{k} {v}' for k, v in r.items() if k not in ('label', 'carry', 'fox_states', 'hits')))
        print(f"   hits {r.get('hits')}")
        print(f"   {r.get('fox_states', '')}")
        if os.environ.get('LAB_CARRY'): print(f"   carry {r.get('carry')}")
        if board and first is not None and 'throw_start' in r:
            strip(frames, first, p, r, board)
    json.dump(res, open(os.path.join(run, 'throws_report.json'), 'w'), indent=1)
    if mp4 and first is not None:
        reel(frames, first, plan, res, mp4, run, slate)
    return res


def crop_box(w, h, cam):
    return (int(w * 0.14), int(h * 0.05), int(w * 0.86), int(h * 0.95)) if cam == 'side' else (0, 0, w, h)


def strip(frames, first, p, r, board, step=1, n=None):
    from PIL import Image, ImageDraw
    ts = r['throw_start']
    n = n or r.get('geno_free') or 40
    ims = []
    for k in range(-2, n + 4, step):
        i = first + ts + k - LAG
        if 0 <= i < len(frames):
            im = Image.open(frames[i]).convert('RGB'); w, h = im.size
            ims.append((k, im.crop(crop_box(w, h, p['cam']))))
    if not ims: return
    cw, ch = ims[0][1].size; sc = 240 / cw; W, H = int(cw * sc), int(ch * sc); cols = 10
    out = Image.new('RGB', (W * min(cols, len(ims)), H * ((len(ims) + cols - 1) // cols) + 20), (20, 20, 24))
    d = ImageDraw.Draw(out); d.text((6, 4), f"{p['label']}: release +{r.get('release')}", fill=(240, 240, 240))
    for j, (f, im) in enumerate(ims):
        x, y = (j % cols) * W, 20 + (j // cols) * H
        out.paste(im.resize((W, H)), (x, y)); d.text((x + 4, y + 4), f'{f:+d}', fill=(255, 255, 0))
    os.makedirs(board, exist_ok=True)
    out.save(os.path.join(board, f"throw_{p['label']}.png"))


def reel(frames, first, plan, res, mp4, run=None, slate=None):
    """Every throw at full speed, cropped and labelled, with the game's audio: the director clicks on the opening slate's
    first frame, which is where the DSP dump's samples are pinned to the frames (plates.game_audio's sync)."""
    from PIL import Image, ImageDraw
    tmp = os.path.splitext(mp4)[0] + '_frames'
    os.makedirs(tmp, exist_ok=True)
    for f in glob.glob(os.path.join(tmp, '*.jpg')): os.remove(f)
    k, spans = 0, []
    for p, r in zip(plan, res):
        if 'throw_start' not in r: continue
        span = []
        for j in range(-20, 100):
            i = first + r['throw_start'] + j - LAG
            if not 0 <= i < len(frames): continue
            im = Image.open(frames[i]).convert('RGB'); w, h = im.size
            im = im.crop(crop_box(w, h, p['cam'])).resize((960, 720))
            ImageDraw.Draw(im).text((12, 10), p['label'], fill=(255, 255, 255))
            im.save(os.path.join(tmp, f'{k:05d}.jpg'), quality=92); k += 1
            span.append(i)
        if span: spans.append((span[0], span[-1] + 1))
    video = os.path.splitext(mp4)[0] + '_video.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '60', '-i', os.path.join(tmp, '%05d.jpg'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', video], check=True)
    shutil.rmtree(tmp)                                     # the encoded reel replaces its frames
    wav = os.path.join(run, 'dsp.wav') if run else None
    if wav and os.path.exists(wav) and slate is not None:
        import numpy as np, soundfile as sf
        y, sr = sf.read(wav, always_2d=True)
        m = np.abs(y).max(axis=1); hop = max(1, int(sr * 0.002))
        env = np.array([m[i:i + hop].max() for i in range(0, len(m), hop)])
        on = [i * hop for i in range(1, len(env)) if env[i] > 0.02 and env[i - 1] <= 0.02]
        if on:
            c0 = on[0]                                      # the opening slate's click: its first frame
            per = sr / 60.0
            parts = [y[int(c0 + (a - slate) * per):int(c0 + (b - slate) * per)] for a, b in spans]
            out = os.path.splitext(mp4)[0] + '.wav'
            sf.write(out, np.clip(np.concatenate(parts), -1, 1), sr)
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', video, '-i', out, '-c:v', 'copy', '-c:a', 'aac',
                            '-b:a', '192k', '-shortest', mp4], check=True)
            os.remove(video); os.remove(out)
            print('reel', mp4, k, 'frames, with the game audio')
            return
    os.replace(video, mp4)
    print('reel', mp4, k, 'frames (no audio)')


# ------------------------------------------------------------------------------------------------ the watched sets
def watched(run):
    """a watched run's per-frame logs: FEET {s: (motion, anim frame)} for Geno, HURT {(s, port): [(a, b)]}, the SHIELD
    centre (ThrowN, Geno's shield bone) {s: (x, y)}, and the up throw's shots [(line index, anim frame)]"""
    feet, hurt, centre, shots = {}, {}, {}, []
    for i, l in enumerate(open(os.path.join(run, 'osreport.log'), errors='replace')):
        q = l.split()
        if len(q) >= 15 and q[0] == 'FEET' and q[2] == str(GENO) and q[3] == '0':
            feet[int(q[1])] = (int(q[13]), float(q[14]))
        elif len(q) >= 10 and q[0] == 'HURT':
            hurt.setdefault((int(q[1]), int(q[2])), []).append(
                (tuple(float(x) for x in q[4:6]), tuple(float(x) for x in q[7:9])))
        elif len(q) >= 11 and q[0] == 'SHIELD' and q[2] == str(GENO):
            centre[int(q[1])] = (float(q[8]), float(q[9]))
    return feet, hurt, centre


def anim_frames(feet, p, motion):
    """{anim frame: first logic frame showing it} within a try, for one motion state"""
    out = {}
    for s_, (ms, a) in sorted(feet.items()):
        if p['t0'] <= s_ < p['t0'] + p['slot'] and ms == motion: out.setdefault(int(round(a)), s_)
    return out


MOTION = dict(fthrow=219, bthrow=220, uthrow=221, dthrow=222)


def fist_line(run, plan_path):
    """The forward throw's read in the game, frame by frame to the release: the fist's line (his right hand's path, the
    RHandN hurtbox's base, from the frame before the launch to the release, in the stage plane) and the opponent's body
    (the mean of their hurtboxes' midpoints) and top (their highest capsule end) off it, perpendicular (+ above). The
    release is the run's own (blast); the launch, the first frame the fist leaves the forearm (the hand's distance from the elbow grows 0.25 in a frame)."""
    plan = [p for p in json.load(open(plan_path)) if p['throw'] == 'fthrow' and p.get('watch')]
    feet, hurt, centre = watched(run)
    log = open(os.path.join(run, 'osreport.log'), errors='replace').read().splitlines()
    out = {}
    for p in plan:
        fr = anim_frames(feet, p, MOTION['fthrow'])
        hand = lambda a: hurt[(fr[a], GENO)][8][0]            # rig.HURTBOXES[8]: RHandN, its base at the joint
        release = blast(log, p, fr)
        if release is None: continue
        reach = lambda a: math.dist(hand(a), hurt[(fr[a], GENO)][6][0])   # [6]: RArmJ, its base at the elbow
        launch = next((a for a in range(release - 8, release + 1) if a in fr and a - 1 in fr and
                       reach(a) - reach(a - 1) > 0.25), None)
        if launch is None: continue
        o = hand(launch - 1); e = hand(release)
        u = (e[0] - o[0], e[1] - o[1]); n = math.hypot(*u); u = (u[0] / n, u[1] / n)
        up = (-u[1], u[0]) if u[0] >= 0 else (u[1], -u[0])
        off = lambda pt: (pt[0] - o[0]) * up[0] + (pt[1] - o[1]) * up[1]
        rows = []
        for a in range(1, release + 1):
            if a not in fr or (fr[a], FOX) not in hurt: continue
            caps = hurt[(fr[a], FOX)]
            mids = [((x[0] + y[0]) / 2, (x[1] + y[1]) / 2) for x, y in caps]
            c = (sum(m[0] for m in mids) / len(mids), sum(m[1] for m in mids) / len(mids))
            top = max(off(pt) for cap in caps for pt in cap)
            rows.append((a, round(off(c), 2), round(top, 2), round(off(centre[fr[a]]), 2) if fr[a] in centre else None))
        out[p['label']] = dict(launch=launch, release=release, deg=round(math.degrees(math.atan2(u[1], abs(u[0]))), 1),
                               rows=rows)
    return out


def blast(log, p, fr):
    """the blast's animation frame in a try: the release (the first frame the opponent is out of the thrown state; the
    back throw's release is the shot), or the up throw's first star (its THROWSHOT line, between the try's MARK lines)"""
    if p['throw'] == 'uthrow':
        on = False
        for l in log:
            q = l.split()
            if q[:1] == ['MARK']: on = int(q[1]) == p['t0']
            elif on and l.startswith('GENO THROWSHOT star'): return int(q[3])
        return None
    fox = sorted((int(q[1]), int(q[5])) for q in (l.split() for l in log)
                 if q[:1] == ['POS'] and len(q) >= 8 and q[2] == str(FOX) and p['t0'] <= int(q[1]) < p['t0'] + p['slot'])
    held = [s_ for s_, m in fox if m in THROWN]
    if not held: return None
    rel = max(held) + 1
    inv = {s_: a for a, s_ in fr.items()}
    return inv.get(rel)


def seg_dist(a0, a1, b0, b1):
    """the closest distance between segments a0-a1 and b0-b1 (3D)"""
    import numpy as np
    p, q, r_, s_ = (np.array(x, float) for x in (a0, a1, b0, b1))
    d1, d2, r = q - p, s_ - r_, p - r_
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    if a < 1e-9 and e < 1e-9: return float(np.linalg.norm(p - r_))
    if a < 1e-9: sc, tc = 0.0, min(1.0, max(0.0, f / e))
    else:
        c = d1 @ r
        if e < 1e-9: sc, tc = min(1.0, max(0.0, -c / a)), 0.0
        else:
            b = d1 @ d2; den = a * e - b * b
            sc = min(1.0, max(0.0, (b * f - c * e) / den)) if den > 1e-9 else 0.0
            tc = (b * sc + f) / e
            if tc < 0: tc, sc = 0.0, min(1.0, max(0.0, -c / a))
            elif tc > 1: tc, sc = 1.0, min(1.0, max(0.0, (b - c) / a))
    return float(np.linalg.norm((p + d1 * sc) - (r_ + d2 * tc)))


# the holding part per throw and frame (rig.HURTBOXES: 4 LArmJ, 7 LHandN, 8 RHandN)
HOLD = dict(fthrow=lambda a: (8,), bthrow=lambda a: (7,) if a < 20 else (4,), uthrow=lambda a: (7, 8),
            dthrow=lambda a: (7,))


def capsules(run):
    """every HURT line in 3D with its radius: {(frame, port): [(a, b, r)]}"""
    out = {}
    for l in open(os.path.join(run, 'osreport.log'), errors='replace'):
        q = l.split()
        if len(q) >= 11 and q[0] == 'HURT':
            out.setdefault((int(q[1]), int(q[2])), []).append(
                (tuple(float(x) for x in q[4:7]), tuple(float(x) for x in q[7:10]), float(q[10])))
    return out


def grip(run, plan_path):
    """per watched throw: [(animation frame, gap, the body centre's step)] to the release, the gap's summary over the held
    frames, and the release's pop (the release frame's step against the flight's first: jerk = their difference) (--grip)"""
    import numpy as np
    plan = [p for p in json.load(open(plan_path)) if p.get('watch')]
    feet = watched(run)[0]
    caps = capsules(run)
    state = {}
    for l in open(os.path.join(run, 'osreport.log'), errors='replace'):
        q = l.split()
        if q[:1] == ['POS'] and len(q) >= 8 and q[2] == str(FOX): state[int(q[1])] = int(q[5])
    out = {}
    for p in plan:
        fr = anim_frames(feet, p, MOTION[p['throw']])
        held = [s_ for s_ in range(p['t0'], p['t0'] + p['slot']) if state.get(s_) in THROWN]
        if not fr or not held: continue
        rel_s = max(held) + 1
        inv = {s_: a for a, s_ in fr.items()}
        cen = {s_: np.mean([[(x[i] + y[i]) / 2 for i in range(3)] for x, y, _ in caps[(s_, FOX)]], axis=0)
               for s_ in range(min(held) - 1, rel_s + 4) if (s_, FOX) in caps}
        rows = []
        for s_ in held:
            a = inv.get(s_)
            if a is None or (s_, FOX) not in caps or (s_, GENO) not in caps: continue
            mine = caps[(s_, GENO)]
            gap = min(seg_dist(mine[k][0], mine[k][1], va, vb) - mine[k][2] - vr
                      for k in HOLD[p['throw']](a) for va, vb, vr in caps[(s_, FOX)])
            step = float(np.linalg.norm(cen[s_] - cen[s_ - 1])) if s_ - 1 in cen and s_ in cen else None
            rows.append((a, round(gap, 2), round(step, 2) if step is not None else None))
        pop = None
        if all(k in cen for k in (rel_s - 2, rel_s - 1, rel_s, rel_s + 1)):
            v_in, v_rel, v_out = cen[rel_s - 1] - cen[rel_s - 2], cen[rel_s] - cen[rel_s - 1], cen[rel_s + 1] - cen[rel_s]
            pop = dict(step_in=round(float(np.linalg.norm(v_in)), 2), step_release=round(float(np.linalg.norm(v_rel)), 2),
                       step_out=round(float(np.linalg.norm(v_out)), 2), jerk=round(float(np.linalg.norm(v_rel - v_out)), 2))
        gaps = [g for _, g, _ in rows]
        steps = [(a, st) for a, _, st in rows if st is not None]
        big = max(steps, key=lambda x: x[1]) if steps else None
        out[p['label']] = dict(release=inv.get(rel_s), rows=rows, pop=pop,
                               gap=dict(mean=round(float(np.mean(gaps)), 2), max=round(max(gaps), 2),
                                        min=round(min(gaps), 2)) if gaps else None,
                               max_step=big)
    return out


def board(run, plan_path, out_dir, before=None, before_plan=None, crop=None, only=None, width=230):
    """A strip per throw of a watched run (and the same throw from a before run above it): each animation frame from
    the wind-up to past the blast, labelled by the frame (FEET), each try aligned on its sync slate, the rows lined up
    on the blast (outlined in red), so a longer wind-up shows as cells to the left. crop (fractions x0, y0, x1, y1 of
    the image) and only (one throw) make a detail strip, e.g. on him alone."""
    from PIL import Image, ImageDraw
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labs'))
    import aerials_strips as AS, contextlib, io
    runs = ([(before, before_plan or before.rstrip('/') + '.plan.json')] if before else []) + [(run, plan_path)]
    rows_for = []
    for r, pp in runs:
        plan = json.load(open(pp))
        d = AS.load(r)
        with contextlib.redirect_stdout(io.StringIO()): AS.align(d, plan)
        log = open(os.path.join(r, 'osreport.log'), errors='replace').read().splitlines()
        rows_for.append((r, plan, d, watched(r)[0], log))
    LEAD, TAIL = dict(fthrow=17, bthrow=16, uthrow=12, dthrow=14), dict(fthrow=8, bthrow=8, uthrow=10, dthrow=8)
    os.makedirs(out_dir, exist_ok=True)
    made = {}
    for th in (only,) if only else ('fthrow', 'bthrow', 'uthrow', 'dthrow'):
        rows, cam = [], None
        for r, plan, d, feet, log in rows_for:
            p = next((p for p in plan if p['throw'] == th and p.get('watch')), None)
            if p is None: continue
            cam = p['cam']
            fr = anim_frames(feet, p, MOTION[th])
            anchor = blast(log, p, fr) if fr else None
            if anchor is None: continue
            cells = []
            for a in range(anchor - LEAD[th], anchor + TAIL[th] + 1):
                i = d['idx'](fr[a]) if a in fr else -1
                if not 0 <= i < len(d['frames']): cells.append(None); continue
                im = Image.open(os.path.join(r, d['frames'][i])).convert('RGB')
                w, h = im.size
                box = (int(w * 0.12), int(h * 0.06), int(w * 0.95), int(h * 0.8)) if cam != 'game' else \
                      (int(w * 0.1), int(h * (0.04 if th == 'uthrow' else 0.26)), int(w * 0.9), int(h * 0.76))
                if crop: box = (int(w * crop[0]), int(h * crop[1]), int(w * crop[2]), int(h * crop[3]))
                im = im.crop(box); im = im.resize((width, int(width * im.height / im.width)))
                dr = ImageDraw.Draw(im)
                if a == anchor: dr.rectangle([0, 0, im.width - 1, im.height - 1], outline=(255, 40, 40), width=3)
                dr.rectangle([0, 0, 24, 13], fill=(0, 0, 0)); dr.text((3, 1), str(a), fill=(255, 255, 255))
                cells.append(im)
            rows.append((os.path.basename(r.rstrip('/')), anchor, max(fr), cells))
        if not rows or not any(c for *_, cs in rows for c in cs): continue
        cw, ch = next(c for *_, cs in rows for c in cs if c is not None).size
        n = max(len(cs) for *_, cs in rows)
        per = (n + 1) // 2                                # two bands, each with every run's row: the columns stay aligned
        sheet = Image.new('RGB', (cw * per, (ch + 16) * len(rows) * 2 + 10), (20, 20, 24))
        dr = ImageDraw.Draw(sheet)
        for band in range(2):
            for j, (name, anchor, last, cells) in enumerate(rows):
                y = (band * len(rows) + j) * (ch + 16) + band * 10
                dr.text((4, y + 2), f"{th} ({name}): the blast on animation frame {anchor} (outlined), the throw's last "
                                    f"frame {last}", fill=(240, 240, 240))
                for i, im in enumerate(cells[band * per:(band + 1) * per]):
                    if im is not None: sheet.paste(im, (i * cw, y + 16))
        path = os.path.join(out_dir, f"throw_{th}_{cam}{'_detail' if crop else ''}.png")
        sheet.save(path); made[th] = path
    return made


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--grip':
    res = grip(sys.argv[2], sys.argv[3])
    for lab, r in res.items():
        print(f"{lab}: released on {r['release']}; gap (+ apart, - overlapping) {r['gap']}; the largest step while held "
              f"{r['max_step']}; the release {r['pop']}")
        print('   ' + ' '.join(f'{a}:{g:+.1f}' for a, g, _ in r['rows']))
    if len(sys.argv) > 4: json.dump(res, open(sys.argv[4], 'w'), indent=1)
    sys.exit()

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--line':
    for lab, r in fist_line(sys.argv[2], sys.argv[3]).items():
        print(f"{lab}: the fist launches on {r['launch']}, {r['deg']} deg up, the release {r['release']}")
        print('frame  centre_off  top_off  ThrowN_off')
        for row in r['rows']: print('%5d %10.2f %8.2f %10s' % row)
    sys.exit()

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--board':
    a = sys.argv[2:]
    kw = {}
    if '--crop' in a:
        i = a.index('--crop'); kw['crop'] = [float(x) for x in a[i + 1].split(',')]; del a[i:i + 2]
    if '--only' in a:
        i = a.index('--only'); kw['only'] = a[i + 1]; del a[i:i + 2]
    if '--width' in a:
        i = a.index('--width'); kw['width'] = int(a[i + 1]); del a[i:i + 2]
    print(board(a[0], a[1], a[2], a[3] if len(a) > 3 else None, a[4] if len(a) > 4 else None, **kw)); sys.exit()

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--report':
    a = sys.argv[2:]
    mp4 = a[a.index('--mp4') + 1] if '--mp4' in a else None
    a = [x for x in a if x not in ('--mp4', mp4)]
    report(a[0], a[1], a[2] if len(a) > 2 else None, mp4); sys.exit()

# ------------------------------------------------------------------------------------------------ the film
from dsl import Film
T = tests()
f = Film(len_s=(sum(t['slot'] for t in T) + 110) / 60)
PLAYERS = [(os.environ.get('LAB_THROWER', 'geno'), dict(x=-7, face=1)), (os.environ.get('LAB_VICTIM', 'fox'), dict(x=0, face=-1))]
if any(t.get('bystander') for t in T):
    PLAYERS.append(('falco', dict(x=-40, face=1)))
f.setup(players=PLAYERS, seed=5,
        coll=int(os.environ.get('LAB_COLL', '0')))
if any(t['cam'] == 'game' for t in T):
    f.game_camera()
geno, fox = f.port(GENO), f.port(FOX)
plan, t0 = [], 70
for i, t in enumerate(T):
    gx = (L - 22) if t.get('ledge') and t['throw'] == 'fthrow' else (L - 8 if t.get('ledge') else -7)
    face = 1 if not t.get('ledge') or t['throw'] == 'fthrow' else -1
    if t.get('ledge') and t['throw'] == 'bthrow':
        gx = L - 22                                     # his back to the ledge: the back throw sends Fox off it
    fx = gx + 7 * face
    f.reset(t0 - 30, GENO, gx, face); f.reset(t0 - 30, FOX, fx, -face)
    f.percent(t0 - 26, GENO, 0); f.percent(t0 - 26, FOX, t['pct'])
    f.mark(t0, i, t['label'])
    if t['cam'] == 'side':
        hi = t['throw'] == 'uthrow'                     # the up throw: room above for the flight and the stars
        f.cam(t0 - 20, eye=(4 * face, 20 if hi else 13, 92 if hi else 66), at=(4 * face, 19 if hi else 11, 0), fov=34,
              ease='cut', track='p0')
    elif t['cam'] == '34':
        hi = t['throw'] == 'uthrow'
        f.orbit(t0 - 20, at=(3 * face, 19 if hi else 11, 0), dist=90 if hi else 66, yaw=-38 * face, pitch=8, fov=34,
                ease='cut', track='p0')
    elif t['cam'] != 'game':
        f.cam(t0 - 20, eye=(20 * face, 26, 150), at=(20 * face, 20, 0), fov=34, ease='cut', track='p0')
    extra = {}
    if t.get('watch'):                                  # the sync slate, his animation frame, both fighters' hurtboxes
        f.cue(t0 - SYNC, 'stage', a=0); f.cue(t0 - SYNC, 'bgcolor', a=255, b=0, c=255)
        f.cue(t0 - SYNC + 2, 'stage', a=1); f.cue(t0 - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
        for k in range(36, 41 + 75):
            f.feet(t0 + k, GENO)
        for k in range(40, 41 + 50):
            f.shield(t0 + k, GENO); f.shield(t0 + k, FOX)
        extra = dict(sync=t0 - SYNC, start=t0 + 36, frames=80)
    geno.hold(t0, 2, btn='Z')
    st = THROW_STICK[t['throw']]
    geno.hold(t0 + 40, 3, stick=st, dir=face)
    di = di_stick(t, face)
    if di:
        fox.hold(t0 + 36, 40, stick=di)                 # held through the throw: the release reads it
    if t.get('grab_at'):                                # frames from the throw's first frame (it starts a frame after the input)
        g = t0 + 41 + t['grab_at'] - 1
        if t.get('dash'):                               # dash toward where he lands, then a dash grab
            geno.hold(g - 6, 6, stick=(80, 0), dir=face)
        geno.hold(g, 2, btn='Z', stick=(80, 0) if t.get('dash') else (0, 0), dir=face)
    if t.get('mash'):
        for k in range(0, min(t['slot'] - 100, 200), 4):   # after the throw starts: jump, jump, jump (stopping before
            fox.hold(t0 + 56 + k, 2, stick=di or (0, 0), btn='X')   # the next slot's reset, so he is standing for it)
    if t.get('ledge'):
        for k in range(260, t['slot'] - 60, 20):         # off the respawn platform whenever it arrives
            fox.hold(t0 + k, 4, stick=(0, -80))
    fox.trace(t0 - 2, t0 + t['slot'] - 12); geno.trace(t0 - 2, t0 + t['slot'] - 12)
    if t.get('bystander'):                              # Falco beside Geno, full-jumping into the stars' line
        f.reset(t0 - 30, 2, gx - 3 * face, face)
        f.port(2).hold(t0 + 41 + 12, 8, btn='X')
        f.port(2).trace(t0 - 2, t0 + t['slot'] - 12)
    f.status(t0 + t['slot'] - 14, FOX)
    plan.append(dict(t0=t0, face=face, **extra, **t))
    t0 += t['slot']
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
