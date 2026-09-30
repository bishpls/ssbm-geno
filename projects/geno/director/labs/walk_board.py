"""Strips from walk_lab captures: consecutive frames of one action, cropped around the fighter (the director's tracking
camera replayed from the POS log), one row per capture, so Geno's cycles sit beside Mario's and Samus's. The foot-slide
numbers come from footslide.py; this is for looking.

    .venv/bin/python projects/geno/director/labs/walk_board.py OUT.png RUN[:label] [RUN[:label] ...] --seg middle \
        --ms 16 [--skip 20] [--count 24] [--step 1] [--w 200]
RUN is a dolphin.py output folder of walk_lab (its osreport.log has the POS and MS lines). --seg picks the segment, --ms
the motion state (14 Wait, 15-17 WalkSlow/Middle/Fast, 18 Turn, 19 TurnRun, 20 Dash, 21 Run, 23 RunBrake); --skip frames
into it, then --count frames every --step. --from S starts at an absolute script frame instead.
"""
import argparse, json, os, re, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'machinima'))
from plates import is_slate

PPU = 35.44 * 62         # horizontal pixels per world unit x camera distance, at res 2 (1280 wide) and fov 30 (fitted)
# the dump shows logic frame s this many images after the opening slate's end (a reset's teleport: MS at s, image at s0+s-3)
LAG = -3


def load(run):
    log = open(os.path.join(run, 'osreport.log')).read().splitlines()
    pos, ms, marks = {}, [], {}
    for l in log:
        p = l.split()
        if not p: continue
        if p[0] == 'POS' and p[2] == '0': pos[int(p[1])] = (float(p[3]), float(p[4]), int(p[5]))
        elif p[0] == 'MS' and p[2] == '0': ms.append((int(p[1]), int(p[3])))
        elif p[0] == 'MARK': marks[int(p[2])] = int(p[1])
    fs = sorted(f for f in os.listdir(run) if re.fullmatch(r'f\d{5}\.png', f))
    i = 0
    while i < len(fs) and not is_slate(os.path.join(run, fs[i])): i += 1
    while i < len(fs) and is_slate(os.path.join(run, fs[i])): i += 1
    return dict(run=run, pos=pos, ms=ms, marks=marks, frames=fs, s0=i)


def tracker(d, cam_dist=62.0):
    """the director's smoothed tracking x per script frame (track_update: snap on the first frame, then 12% a frame)"""
    t, out = None, {}
    for s in sorted(d['pos']):
        x = d['pos'][s][0]
        t = x if t is None else t + (x - t) * 0.12
        out[s] = t
    return out


def leads(n=4000):
    """the camera's lead per script frame (walk_lab keys its tracking camera's x offset), from the lab's own keys"""
    import walk_lab_cams
    ks = walk_lab_cams.keys()
    out = [0.0] * n
    def ease(kind, u):
        if kind == 0: return 0.0
        if kind == 2: return 4 * u ** 3 if u < 0.5 else 1 - ((-2 * u + 2) ** 3) / 2
        return u
    for i, (s, kind, x) in enumerate(ks):
        s1, x1 = (ks[i + 1][0], ks[i + 1][2]) if i + 1 < len(ks) else (n, x)
        for f in range(max(0, s), min(n, s1)):
            out[f] = x + (x1 - x) * ease(kind, (f - s) / max(1, s1 - s))
    return out


LEADS = []


def frame(d, s, trk, w, cam_dist=62.0, h=1056, center=None):
    im = Image.open(os.path.join(d['run'], d['frames'][d['s0'] + s + LAG])).convert('RGB')
    if center is None:
        if not LEADS: LEADS.extend(leads())
        x, y, _ = d['pos'].get(s, (0, 0, 0))
        center = 666 + (x - trk.get(s, x) - LEADS[s]) * PPU / cam_dist
    box = (int(center - w / 2), 0, int(center + w / 2), h)
    return im.crop(box)


def cap_centre(d, s, fallback, want_y=False):
    """Geno's screen x from his blue cap (the tracking camera's lag varies): the median column of cap-blue pixels"""
    import numpy as np
    im = np.asarray(Image.open(os.path.join(d['run'], d['frames'][d['s0'] + s + LAG])).convert('RGB').resize((320, 264)))
    band = im[20:180].astype(int)
    m = (band[..., 2] > 150) & (band[..., 0] < 90) & (band[..., 1] < 150) & (band[..., 2] - band[..., 1] > 70)
    ys, xs = np.nonzero(m)
    if len(xs) <= 40: return fallback
    return (float(np.median(xs)) * 4, (float(np.median(ys)) + 20) * 4) if want_y else float(np.median(xs)) * 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('runs', nargs='+')
    ap.add_argument('--seg', type=int, default=None, help='segment index (MARK)'); ap.add_argument('--ms', type=int)
    ap.add_argument('--skip', type=int, default=0); ap.add_argument('--count', type=int, default=20)
    ap.add_argument('--step', type=int, default=1); ap.add_argument('--from', dest='start', type=int)
    ap.add_argument('--w', type=int, default=560); ap.add_argument('--scale', type=float, default=0.42)
    ap.add_argument('--top', type=int, default=180); ap.add_argument('--bottom', type=int, default=880)
    ap.add_argument('--cols', type=int, default=8)
    ap.add_argument('--cap-at', dest='cap_at', type=int, default=150, help='capxy: the cap this far below the crop top')
    ap.add_argument('--follow', default='cap', help='cap (Geno rows: find his blue cap; others replay the camera) or pos (replay the camera from POS)')
    a = ap.parse_args()
    rows = []
    for spec in a.runs:
        run, _, label = spec.partition(':')
        d = load(os.path.expanduser(run))
        trk = tracker(d)
        if a.start is not None:
            s0 = a.start
        else:
            seg_t = d['marks'][a.seg] if a.seg is not None else 0
            cands = [s for s, m in d['ms'] if m == a.ms and s >= seg_t] if a.ms is not None else [seg_t]
            s0 = cands[0] + a.skip
        ss = [s0 + k * a.step for k in range(a.count)]
        rows.append((label or os.path.basename(run), ss, d, trk))
    cw = int(a.w * a.scale); ch = int((a.bottom - a.top) * a.scale)
    cols = min(a.cols, a.count)
    per = (a.count + cols - 1) // cols
    img = Image.new('RGB', (110 + cw * cols, (ch + 16) * per * len(rows) + 6), (30, 30, 36))
    dr = ImageDraw.Draw(img)
    for r, (label, ss, d, trk) in enumerate(rows):
        for k, s in enumerate(ss):
            rr, cc = r * per + k // cols, k % cols
            x0, y0 = 110 + cc * cw, 6 + rr * (ch + 16)
            if k % cols == 0: dr.text((6, y0 + ch // 2), label, fill=(230, 230, 240))
            if d['s0'] + s + LAG >= len(d['frames']): continue
            c, top = None, a.top
            if a.follow == 'cap' and 'geno' in label.lower(): c = cap_centre(d, s, None)
            if a.follow == 'capxy' and 'geno' in label.lower():
                cy = cap_centre(d, s, None, want_y=True)
                if cy: c, top = cy[0], int(min(1056 - (a.bottom - a.top), max(0, cy[1] - a.cap_at)))
            im = frame(d, s, trk, a.w, center=c).crop((0, top, a.w, top + a.bottom - a.top)).resize((cw, ch), Image.LANCZOS)
            img.paste(im, (x0, y0 + 14))
            ms = [m for t, m in d['ms'] if t <= s][-1:] or [0]
            dr.text((x0 + 4, y0), f'+{s - ss[0]}  s{s} ms{ms[0]}', fill=(255, 230, 120))
    img.save(a.out)
    print('wrote', a.out, img.size)


if __name__ == '__main__':
    main()
