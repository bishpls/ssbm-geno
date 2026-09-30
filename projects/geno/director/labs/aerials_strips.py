"""Consecutive-frame strips from aerials_lab captures: one move per strip, Geno's row over the cast member's (the fixed wide
shot, each cropped around his logged position) or Geno alone (the tracking close-up, AERIALS_CAST=none: whole frames).

    .venv/bin/python projects/geno/director/labs/aerials_strips.py OUT.png RUN --slot fair_fh [--pad 3] [--tail 4] \
        [--step 1] [--w 170] [--all]
RUN is a dolphin.py output folder (osreport.log with MARK, MS and POS lines); the plan is director/build/aerials_lab.plan.json
(or --plan). Frames run from the move's first state (the first motion state 65 or over: aerials, landings and specials)
less --pad, to Wait (14) plus --tail; --all takes the whole slot. Each cell is tagged with the action frame (1 = the move's
first frame) and the motion state. Game data: keep the output outside the repo or in the gitignored board/.
Images line up with the log per segment when the plan gives each a 'sync' frame (a two-frame magenta slate the lab shows
there, as downb_lab does): the dump can drop images mid-run, so one constant offset (LAG) can be frames off by a later
segment. A drop inside a segment, after its slate, still shifts what follows it (heavy moments: hits, effects).
"""
import argparse, json, math, os, re, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'machinima'))
from plates import is_slate

LAG = -3                                  # the image of logic frame s: s0 + s + LAG (labs/walk_board.py), a run without syncs
SYNC_CAL = -1                             # with a segment's sync slate (plan 'sync' = its logic frame b, first shown in image
                                          # i_b): the image of logic frame s is i_b + (s - b) + SYNC_CAL, whatever was lost before
MSNAME = {14: 'Wait', 24: 'KneeBend', 25: 'JumpF', 27: 'JumpAerF', 29: 'Fall', 35: 'FallSpecial', 42: 'Landing',
          43: 'LandFallSp', 65: 'AirN', 66: 'AirF', 67: 'AirB', 68: 'AirHi', 69: 'AirLw', 70: 'LandAirN', 71: 'LandAirF',
          72: 'LandAirB', 73: 'LandAirHi', 74: 'LandAirLw'}
for k, n in enumerate(['NStart', 'NLoop', 'NEnd', 'AirNStart', 'AirNLoop', 'AirNEnd', 'S', 'AirS', 'HiStart', 'AirHiStart', 'Hi',
                       'Lw', 'AirLw', 'LwFlash', 'NFinger', 'AirNFinger', 'NCancel', 'AirNCancel']):
    MSNAME[343 + k] = n


def slate_runs(run, fs):
    """(first, last) image index of every magenta slate in the run, cached in the run folder."""
    cache = os.path.join(run, 'slates.json')
    if os.path.exists(cache) and json.load(open(cache)).get('n') == len(fs):
        return [tuple(r) for r in json.load(open(cache))['runs']]
    runs, i, sl = [], 0, [is_slate(os.path.join(run, f)) for f in fs]
    while i < len(fs):
        if sl[i]:
            j = i
            while j + 1 < len(fs) and sl[j + 1]: j += 1
            runs.append((i, j)); i = j + 1
        else: i += 1
    json.dump(dict(n=len(fs), runs=runs), open(cache, 'w'))
    return runs


def align(d, slots):
    """Per-segment image offsets from the sync slates: d['idx'](s) is the image of logic frame s. A segment whose slate
    is not found (or a plan without syncs) falls back to s0 + s + LAG. Prints each segment's offset against LAG."""
    runs = slate_runs(d['run'], d['frames'])[1:]
    spans, est = [], d['s0'] + LAG - SYNC_CAL          # each slate is looked for where the previous one left off
    for sl in sorted((sl for sl in slots if 'sync' in sl), key=lambda sl: sl['sync']):
        e = sl['sync'] + est
        near = [r for r in runs if abs(r[0] - e) <= 8]
        if not near: print(f"  {sl['label']}: no sync slate near image {e}; LAG {LAG}"); continue
        r = min(near, key=lambda r: abs(r[0] - e))
        est = r[0] - sl['sync']
        off = r[0] - sl['sync'] + SYNC_CAL
        spans.append((sl['sync'], sl['start'] + sl['frames'], off))
        print(f"  {sl['label']}: sync at image {r[0]}, logic {sl['sync']}: s -> image s{off:+d} (constant LAG: s{d['s0'] + LAG:+d})")
    def idx(s):
        for a, b, off in spans:
            if a <= s < b: return s + off
        return d['s0'] + s + LAG
    d['idx'] = idx
    return spans


def load(run):
    log = open(os.path.join(run, 'osreport.log'), errors='replace').read().splitlines()
    pos, ms = {k: {} for k in range(4)}, {k: [] for k in range(4)}
    for l in log:
        p = l.split()
        if len(p) < 4: continue
        if p[0] == 'POS' and p[2] in ('0', '1', '2', '3'): pos[int(p[2])][int(p[1])] = (float(p[3]), float(p[4]))
        elif p[0] == 'MS' and p[2] in ('0', '1', '2', '3'): ms[int(p[2])].append((int(p[1]), int(p[3])))
    fs = sorted(f for f in os.listdir(run) if re.fullmatch(r'f\d{5}\.png', f))
    i = 0
    while i < len(fs) and not is_slate(os.path.join(run, fs[i])): i += 1
    while i < len(fs) and is_slate(os.path.join(run, fs[i])): i += 1
    d = dict(pos=pos, ms=ms, frames=fs, s0=i, run=run)
    d['idx'] = lambda s: d['s0'] + s + LAG
    return d


def state_at(ms, s):
    cur = None
    for f, st in ms:
        if f <= s: cur = (f, st)
    return cur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('run'); ap.add_argument('--slot', required=True)
    ap.add_argument('--plan', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build', 'aerials_lab.plan.json'))
    ap.add_argument('--pad', type=int, default=3); ap.add_argument('--tail', type=int, default=4)
    ap.add_argument('--step', type=int, default=1); ap.add_argument('--w', type=int, default=170)
    ap.add_argument('--all', action='store_true'); ap.add_argument('--cols', type=int, default=0)
    ap.add_argument('--dist', type=float, default=110); ap.add_argument('--at', type=float, default=20)
    ap.add_argument('--ports', default='', help='the ports to crop, one row each (default 0, or 0,1 with a cast member)')
    ap.add_argument('--state', type=int, default=65, help="the move's first state: the first state at least this")
    ap.add_argument('--alone', action='store_true', help='Geno alone (AERIALS_CAST=none): his row only, --dist 84 --at 22')
    a = ap.parse_args()
    slots = json.load(open(a.plan)); plan = {p['label']: p for p in slots}
    sl = plan[a.slot]; d = load(a.run); align(d, slots)
    t0, t1 = sl['start'], sl['start'] + sl['frames'] - 1
    ms0 = [(f, st) for f, st in d['ms'][0] if t0 <= f <= t1]
    if a.all or not ms0:
        s_from, s_to = t0, t1
    else:
        first = next((f for f, st in ms0 if st >= a.state), ms0[0][0])
        wait = next((f for f, st in ms0 if st == 14 and f > first), t1)
        s_from, s_to = first - a.pad, min(t1, wait + a.tail)
    frames = list(range(s_from, s_to + 1, a.step))
    first = next((f for f, st in ms0 if st >= a.state), s_from)
    W0, H0 = Image.open(os.path.join(a.run, d['frames'][0])).size
    cw = a.w; ch = int(cw * 1.25)
    if a.alone and a.dist == 110: a.dist, a.at = 84, 22
    scale = H0 / (2 * a.dist * math.tan(math.radians(15)))       # pixels per unit on his plane (fov 30, fixed camera)
    ports = [int(x) for x in a.ports.split(',')] if a.ports else [0] if a.alone or not d['ms'][1] else [0, 1]
    cols = a.cols or len(frames)
    rows = math.ceil(len(frames) / cols) * len(ports)
    img = Image.new('RGB', (cw * min(cols, len(frames)), ch * rows + 22), (30, 30, 38))
    dr = ImageDraw.Draw(img)
    dr.text((6, 4), f'{a.slot}  ({os.path.basename(a.run)})  frame 1 = the move\'s first frame', fill=(230, 230, 240))
    for k, s in enumerate(frames):
        idx = d['idx'](s)
        if idx < 0 or idx >= len(d['frames']): continue
        im = Image.open(os.path.join(a.run, d['frames'][idx])).convert('RGB')
        for pi, p in enumerate(ports):
            dx = 0 if a.alone else (15 if p == 0 else -15) if not a.ports else 0
            x, y = d['pos'][p].get(s, d['pos'][p].get(s - 1, (dx, 0)))
            hw, hh = 12.0, 15.0
            cx, cy = W0 / 2 + x * scale, H0 / 2 - (y + 7.5 - a.at) * scale
            box = (int(cx - hw * scale), int(cy - hh * scale), int(cx + hw * scale), int(cy + hh * scale))
            cell = im.crop(box).resize((cw, ch), Image.LANCZOS)
            r, c = divmod(k, cols)
            ox, oy = c * cw, 22 + (r * len(ports) + pi) * ch
            img.paste(cell, (ox, oy))
            st = state_at(d['ms'][p], s)
            tag = f'{s - first + 1}' + (f' {MSNAME.get(st[1], st[1])}' if st else '')
            dr.text((ox + 4, oy + 3), tag, fill=(255, 230, 120) if p == 0 else (160, 200, 255))
    img.save(a.out)
    print('wrote', a.out, len(frames), 'frames')


if __name__ == '__main__':
    main()
