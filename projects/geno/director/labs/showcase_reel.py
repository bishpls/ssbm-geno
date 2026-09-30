"""The Geno showcase reel: every move once, cleanly framed and captioned, from showcase_lab captures (and victory_lab's
results screens, costume line-ups, Kirby's hat), cut on each segment's own sync slate, with the game's audio anchored on
each segment's click, as a 16:9 H.264 mp4 at 60 fps with a title card and an end card.

    .venv/bin/python projects/geno/director/labs/showcase_reel.py MANIFEST.json OUT.mp4 [--w 1920] [--crf 20] [--check]

MANIFEST lists the reel in order: {"card": "title"|"end", "frames": N}; {"run": RUN, "seg": LABEL} (every clip of that
showcase_lab segment; "clips": [i, ...] picks some); {"run": RUN, "results": CAPTION, "from": S, "frames": N,
"box": [x0, y0, x1, y1]} (a results screen: seconds after it appears, a crop in 0..1 of the frame);
{"lineup": [RUN_A, RUN_B], "frames": N} (the costumes); {"run": RUN, "kirby": [s0, s1], "caption": C}. RUN is a dolphin.py
folder with RUN.plan.json beside it. Game data: the output stays outside the repo.
--check writes a contact sheet of each clip's first, middle and last frames beside OUT, and a JSON of the cuts.
"""
import argparse, json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aerials_strips as A
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'machinima'))
from plates import is_slate

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..')
FONT = os.path.join(ROOT, 'engine', 'fonts', 'Archivo.ttf')
FPS, SR = 60, 48000
WAIT = 14
TAIL, LEAD = 10, 2
AUDIO_DELTA = -1           # the sound of logic frame s sits (s - sync + AUDIO_DELTA) frames after its segment's click
                           # (the director's click and a move's sounds reach the dump alike; aerials_reel's LAG + latency)
FADE = int(SR * 0.012)     # each clip's audio fades in and out over 12 ms: no clicks at the cuts


def font(size, weight='SemiBold'):
    f = ImageFont.truetype(FONT, size)
    try: f.set_variation_by_name(weight)
    except Exception: pass
    return f


class Run:
    """A capture: its images lined up per segment (sync slates), its log, its audio and each segment's click."""
    cache = {}

    def __init__(self, path):
        self.path = path
        self.plan = json.load(open(path + '.plan.json'))
        if isinstance(self.plan, dict): self.plan = self.plan['segs']       # kirby_hat_lab's plan
        self.d = A.load(path)
        A.align(self.d, self.plan)
        self.log = open(os.path.join(path, 'osreport.log'), errors='replace').read().splitlines()
        self.ms = {}
        for l in self.log:
            p = l.split()
            if len(p) > 3 and p[0] == 'MS':
                self.ms.setdefault(int(p[2]), []).append((int(p[1]), int(p[3])))
        self.audio = None

    @classmethod
    def get(cls, path):
        if path not in cls.cache: cls.cache[path] = cls(path)
        return cls.cache[path]

    def image(self, s):
        i = self.d['idx'](s)
        return Image.open(os.path.join(self.path, self.d['frames'][max(0, min(i, len(self.d['frames']) - 1))])).convert('RGB')

    def state(self, port, s):
        cur = None
        for f, st in self.ms.get(port, []):
            if f <= s: cur = st
        return cur

    def load_audio(self):
        if self.audio is None:
            import soundfile as sf
            y, sr = sf.read(os.path.join(self.path, 'dsp.wav'), always_2d=True)
            self.audio, self.sr = y, sr
            m = np.abs(y).max(axis=1)
            h = max(1, int(sr * 0.002))
            env = np.array([m[i:i + h].max() for i in range(0, len(m), h)])
            on = [i * h for i in range(1, len(env)) if env[i] > 0.02 and env[i - 1] <= 0.02]
            self.click0 = on[0]                                   # the opening slate's click: logic frame -8
            self.tpl = y[self.click0:self.click0 + int(sr * 0.06)].mean(axis=1)
        return self.audio

    def click(self, sync):
        """The dump sample where the click at logic frame `sync` starts: near its nominal place (from the opening click),
        found by correlating the opening click's first 60 ms."""
        y = self.load_audio(); sr = self.sr
        want = self.click0 + (sync + 8) / FPS * sr
        a, b = int(max(0, want - 0.25 * sr)), int(min(len(y), want + 0.6 * sr))
        seg = y[a:b].mean(axis=1)
        t = self.tpl - self.tpl.mean()
        c = np.correlate(seg - seg.mean(), t, mode='valid')
        n = np.sqrt(np.convolve(seg ** 2, np.ones(len(t)), mode='valid')) * np.sqrt((t ** 2).sum()) + 1e-9
        k = int(np.argmax(c / n))
        return a + k, float((c / n)[k])

    def audio_span(self, sync, s0, s1):
        y = self.load_audio(); sr = self.sr
        c, score = self.click(sync)
        if score < 0.6:                                   # no click at this sync (a lab without them): the nominal place
            c = self.click0 + (sync + 8) / FPS * sr
        a0 = c + (s0 - sync + AUDIO_DELTA) / FPS * sr
        n_out = int(round((s1 - s0) / FPS * SR))
        idx = a0 + np.arange(n_out) * (sr / SR)
        i0 = np.clip(np.floor(idx).astype(int), 0, len(y) - 2); fr = (idx - np.floor(idx))[:, None]
        out = y[i0] * (1 - fr) + y[i0 + 1] * fr
        return out, score


def auto_end(run, t, frm, cap):
    """The frame he is idle again (Wait) after the move, plus TAIL; at most cap."""
    left = False
    for s in range(t + frm + 3, t + cap):
        st = run.state(0, s)
        if st != WAIT: left = True
        elif left: return min(s + TAIL, t + cap)
    return t + cap


def crop169(im, W):
    w, h = im.size
    hh = int(round(w * 9 / 16))
    y0 = (h - hh) // 2
    im = im.crop((0, y0, w, y0 + hh))
    return im.resize((W, int(round(W * 9 / 16))), Image.LANCZOS) if w != W else im


def caption(im, text, W):
    if not text: return im
    s = W / 1920
    f = font(int(40 * s))
    d = ImageDraw.Draw(im, 'RGBA')
    x0, y0 = int(56 * s), im.height - int(118 * s)
    tw = d.textlength(text, font=f)
    pad = int(22 * s)
    box = (x0, y0, x0 + tw + 2 * pad + int(10 * s), y0 + int(64 * s))
    d.rounded_rectangle(box, radius=int(12 * s), fill=(14, 16, 28, 178))
    d.rectangle((box[0], box[1] + int(12 * s), box[0] + int(5 * s), box[3] - int(12 * s)), fill=(255, 205, 64, 255))
    d.text((x0 + pad + int(10 * s), y0 + int(9 * s)), text, font=f, fill=(248, 248, 252, 255))
    return im


def card(kind, W, k, n):
    H = int(round(W * 9 / 16)); s = W / 1920
    im = Image.new('RGB', (W, H), (12, 13, 24))
    g = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array([[[12, 13, 24]]]) * (1 - g) + np.array([[[30, 36, 78]]]) * g).astype(np.uint8)
    im = Image.fromarray(np.repeat(arr, W, axis=1))
    d = ImageDraw.Draw(im)
    fade = min(1.0, k / 12.0, (n - 1 - k) / 12.0)
    col = lambda c: tuple(int(v * fade + 12 * (1 - fade)) for v in c)
    if kind == 'title':
        big, mid, small = font(int(180 * s), 'Black'), font(int(46 * s), 'Medium'), font(int(30 * s), 'Regular')
        lines = [('GENO', big, (255, 214, 92)), ('for Super Smash Bros. Melee', mid, (236, 238, 248)),
                 ('Moveset showcase', small, (170, 178, 214))]
    else:
        big, mid, small = font(int(96 * s), 'Bold'), font(int(40 * s), 'Medium'), font(int(28 * s), 'Regular')
        lines = [('ssbm-geno', big, (255, 214, 92)), ('Geno from Super Mario RPG, a new fighter built on the Melee decompilation', small, (220, 224, 240)),
                 ('A fan work. Captured in game.', small, (170, 178, 214))]
    hs = [d.textbbox((0, 0), t, font=f)[3] for t, f, _ in lines]
    gap = int(28 * s); y = (H - sum(hs) - gap * (len(lines) - 1)) // 2
    for (t, f, c), h in zip(lines, hs):
        w = d.textlength(t, font=f); d.text(((W - w) / 2, y), t, font=f, fill=col(c)); y += h + gap
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('manifest'); ap.add_argument('out')
    ap.add_argument('--w', type=int, default=1920); ap.add_argument('--crf', type=int, default=20)
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    W = a.w; H = int(round(W * 9 / 16))
    man = json.load(open(a.manifest))
    base = os.path.dirname(os.path.abspath(a.manifest))
    rp = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
    # the clips: (kind, frames: list of callables -> Image, audio array or None, caption, info)
    clips = []
    for e in man:
        if 'card' in e:
            clips.append(dict(kind='card', n=e['frames'], card=e['card'], cap='', info=e['card']))
        elif 'seg' in e:
            run = Run.get(rp(e['run']))
            sg = next(p for p in run.plan if p['label'] == e['seg'])
            clips_ = sg.get('clips') or [[e.get('caption', ''), e.get('from', 0), e.get('to')]]
            if 'from' in e and 'clips' not in sg: clips_ = [[e.get('caption', ''), e['from'], e.get('to')]]
            for ci, (cap, frm, to) in enumerate(clips_):
                if 'clips' in e and ci not in e['clips']: continue
                t = sg['start']
                s0 = t + frm - (LEAD if frm < 0 else 0)
                s1 = t + to if to is not None else auto_end(run, t, max(frm, 0), sg['frames'] - 1)   # before the next resets
                if 'to' in e: s1 = t + e['to']
                clips.append(dict(kind='lab', run=run, sync=sg.get('sync', -8), s0=s0, s1=s1, cap=e.get('caption', cap), info=f"{os.path.basename(run.path)}:{sg['label']}:{s0}-{s1}"))
        elif 'results' in e:
            e = dict(e, run=rp(e['run']))
            clips.append(dict(kind='results', run=e['run'], e=e, cap=e['results'], info=e['results']))
        elif 'lineup' in e:
            e = dict(e, lineup=[rp(r) for r in e['lineup']])
            clips.append(dict(kind='lineup', e=e, cap=e.get('caption', 'Costumes'), info='lineup'))
    total = 0
    for c in clips:
        if c['kind'] == 'lab': c['n'] = c['s1'] - c['s0']
        elif c['kind'] in ('results', 'lineup'): c['n'] = c['e']['frames']
        total += c['n']
    print(f'{len(clips)} clips, {total} frames ({total / FPS:.1f} s)')
    tmp = os.path.splitext(a.out)[0]
    wav = tmp + '_audio.wav'
    audio, cuts, t_out = [], [], 0
    for c in clips:
        n = c['n']
        if c['kind'] == 'lab':
            y, score = c['run'].audio_span(c['sync'], c['s0'], c['s1'])
            c['click_score'] = score
        elif c['kind'] == 'results':
            y = results_audio(c, n)
        else:
            y = np.zeros((int(round(n / FPS * SR)), 2))
        y = y[:, :2] if y.shape[1] >= 2 else np.repeat(y, 2, axis=1)
        want = int(round(n / FPS * SR))
        y = np.pad(y, ((0, max(0, want - len(y))), (0, 0)))[:want]
        if len(y) > 2 * FADE:
            ramp = np.linspace(0, 1, FADE)[:, None]
            y[:FADE] *= ramp; y[-FADE:] *= ramp[::-1]
        audio.append(y)
        cuts.append(dict(at=t_out, frames=n, info=c['info'], caption=c['cap'], click=c.get('click_score')))
        t_out += n
    import soundfile as sf
    sf.write(wav, np.clip(np.concatenate(audio), -1, 1), SR)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-i', wav, '-c:v', 'libx264', '-preset', 'slow', '-crf', str(a.crf), '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', a.out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    sheet = []
    for ci, c in enumerate(clips):
        n = c['n']
        for k in range(n):
            if c['kind'] == 'card':
                im = card(c['card'], W, k, n)
            elif c['kind'] == 'lab':
                im = caption(crop169(c['run'].image(c['s0'] + k), W), c['cap'], W)
            elif c['kind'] == 'results':
                im = caption(results_frame(c, k, W), c['cap'], W)
            else:
                im = caption(lineup_frame(c, k, W), c['cap'], W)
            if a.check and k in (0, n // 2, n - 1):
                sheet.append((ci, k, im.resize((W // 6, H // 6))))
            pr.stdin.write(im.tobytes())
    pr.stdin.close(); pr.wait()
    json.dump(cuts, open(tmp + '_cuts.json', 'w'), indent=1)
    if a.check and sheet:
        cw, ch = sheet[0][2].size
        rows = math.ceil(len(clips))
        S = Image.new('RGB', (cw * 3 + 360, (ch + 4) * rows), (20, 20, 26)); d = ImageDraw.Draw(S)
        for ci, k, im in sheet:
            col = 0 if k == 0 else (2 if k == clips[ci]['n'] - 1 else 1)
            S.paste(im, (360 + col * cw, ci * (ch + 4)))
            d.text((6, ci * (ch + 4) + 6), f"{ci}: {clips[ci]['cap']}\n{clips[ci]['info']}\n{clips[ci]['n']} f", fill=(230, 230, 240))
        S.save(tmp + '_sheet.jpg', quality=88)
    print('wrote', a.out, f'{t_out / FPS:.1f} s')


# ---- the results screens (victory_lab): no sync slate. The screen's first image is where the frame goes dark after
# "Game!" (its black backdrop); the audio is anchored on the victory music's onset, since the scene's load plays silence
# the dump has no images for
def results_start(run):
    if hasattr(run, 'res0'): return run.res0
    fs = run.d['frames']
    lum = lambda i: np.asarray(Image.open(os.path.join(run.path, fs[i])).convert('L').resize((64, 52)), dtype=np.float32).mean()
    prev = None
    run.res0 = None
    for i in range(len(fs) // 3, len(fs)):
        v = lum(i)
        if prev is not None and prev > 28 and v < prev - 4:
            run.res0 = i; break
        prev = v
    return run.res0


def results_frame(c, k, W):
    """The results screen as the game draws it, 4:3 pillarboxed into 16:9 (the pose fills the height)."""
    e = c['e']; run = Run.get(e['run'])
    i0 = results_start(run) + int(round(e['from'] * FPS))
    im = Image.open(os.path.join(run.path, run.d['frames'][min(i0 + k, len(run.d['frames']) - 1)])).convert('RGB')
    x0, y0, x1, y1 = e.get('box', [0, 0, 1, 1])
    w, h = im.size
    im = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
    H = int(round(W * 9 / 16))
    full = im
    im = im.resize((int(round(im.width * H / im.height)), H), Image.LANCZOS)
    out = Image.new('RGB', (W, H), (0, 0, 0))
    if 'inset' in e:                                  # the screen at the left, a close-up of one of its boxes at the right
        out.paste(im, (0, 0))
        a0, b0, a1, b1 = e['inset']
        z = full.crop((int(a0 * full.width), int(b0 * full.height), int(a1 * full.width), int(b1 * full.height)))
        zw = W - im.width - int(40 * W / 1920)
        zh = int(z.height * zw / z.width)
        out.paste(z.resize((zw, zh), Image.LANCZOS), (im.width + int(20 * W / 1920), (H - zh) // 2))
    else:
        out.paste(im, ((W - im.width) // 2, 0))
    return out


def results_audio(c, n):
    e = c['e']; run = Run.get(e['run'])
    y = run.load_audio(); sr = run.sr
    i0 = results_start(run)
    nom = run.click0 + (i0 - run.d['s0'] + 8) / FPS * sr
    w = int(sr * 0.01)
    rms = lambda a: float(np.sqrt((y[a:a + w] ** 2).mean()))
    quiet, onset = 0, None
    for a in range(int(nom), len(y) - w, w):
        r = rms(a)
        if r < 0.005: quiet += 1
        elif r > 0.02 and quiet >= 50: onset = a; break
        else: quiet = 0
    if onset is None: onset = nom
    c['onset'] = (onset - nom) / sr
    a0 = onset + e['from'] * sr + e.get('audio_shift', 0) * sr
    idx = a0 + np.arange(int(round(n / FPS * SR))) * (sr / SR)
    i = np.clip(idx.astype(int), 0, len(y) - 1)
    return y[i] * e.get('gain', 1.0)


def lineup_frame(c, k, W):
    e = c['e']
    H = int(round(W * 9 / 16))
    out = Image.new('RGB', (W, H), (10, 10, 18))
    tiles = []
    for rpath in e['lineup']:
        run = Run.get(rpath)
        pl = run.plan[0]
        im = Image.open(os.path.join(run.path, run.d['frames'][min(run.d['s0'] + 90 + k, len(run.d['frames']) - 1)])).convert('RGB')
        w, h = im.size
        sc = h / (2 * 92 * math.tan(math.radians(15)))
        for x in pl['x']:
            cx, cy = w / 2 + x * sc, h / 2 - (8.5 - 11) * sc
            tiles.append(im.crop((int(cx - 8.5 * sc), int(cy - 11.5 * sc), int(cx + 8.5 * sc), int(cy + 11.5 * sc))))
    gap = int(10 * W / 1920)
    tw = (W - gap * (len(tiles) + 1)) // len(tiles)
    for j, t in enumerate(tiles):
        th = int(t.height * tw / t.width)
        out.paste(t.resize((tw, th), Image.LANCZOS), (gap + j * (tw + gap), (H - th) // 2 - int(30 * W / 1920)))
    return out


if __name__ == '__main__':
    main()
