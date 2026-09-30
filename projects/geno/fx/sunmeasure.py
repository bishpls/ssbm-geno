"""Measure Geno Flash's sun (and the cast's PK Flash) against its hitbox, frame by frame, from flash_scale_lab runs: a
capsule run (SCALE_COLL=2: the hitbox in red) and drawn runs on black (SCALE_COLL=0) of the same frames.
    .venv/bin/python projects/geno/fx/sunmeasure.py CAPS_RUN SEG LABEL=DRAWN_RUN [LABEL=DRAWN_RUN ...] [--json OUT]
For every frame with a hitbox, the hitbox is the largest red blob: its centre, and its radius (the half-size of its
box); a blob that isn't round (under 0.65 of its box filled: the red flash's particles, which the capsule run still
draws) is not a hitbox. Each drawn run is thresholded on luma (`faint` > 14: a soft glow's last trace on black; `glow`
> 40: anything you see; `core` > 150: the bright body), and the blob
that holds the hitbox's centre is walked round from that centre in 5-degree sectors: each sector's farthest pixel is the
drawn edge there. Reported in units (the camera: 260 back, 30 degrees; square pixels): the median edge (the body's
outline, a corona's typical reach), its 90th percentile (the tongues' tips) and the maximum. The sectors toward the
caster (he stands inside the grown sun) are left out. A drawn run of a disc-only build (flash_model FLASH_PARTS=disc)
gives the disc's own edge.
Frames before the hitbox (the fireball in flight) report the drawn blob nearest the sun's spot, round its own centre.
"""
import json, math, sys

import numpy as np
from PIL import Image
from scipy import ndimage

import fxsync

DIST, FOV = 260.0, 30.0
FAINT, GLOW, CORE = 14, 40, 150
CASTER_DIR = math.atan2(4.0, -30.0)       # image angle (y down) from the sun's centre (0, 14) to him (-30, ~10)
SKIP = math.radians(40)
SECTORS = 72


def ppu(h):
    return h / (2 * DIST * math.tan(math.radians(FOV / 2)))


def luma(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.int32)
    return (a[..., 0] * 299 + a[..., 1] * 587 + a[..., 2] * 114) // 1000


def hitbox(path):
    c = np.asarray(Image.open(path).convert('RGB')).astype(np.int32)
    red = (c[..., 0] > 90) & (c[..., 0] > 2 * c[..., 1]) & (c[..., 0] > 2 * c[..., 2])
    lab, n = ndimage.label(red)
    if n == 0:
        return None
    sizes = ndimage.sum(red, lab, range(1, n + 1))
    k = int(np.argmax(sizes)) + 1
    if sizes[k - 1] < 30:
        return None
    ys, xs = np.nonzero(lab == k)
    w, h = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    if len(xs) < 0.65 * w * h or len(xs) < 300:
        return None
    return (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2, (w + h) / 4


def edges(mask, cx, cy, skip=True):
    """The drawn blob holding (cx, cy) (or the nearest one), walked round from there: each sector's farthest pixel."""
    lab, n = ndimage.label(mask)
    if n == 0:
        return None
    k = lab[int(round(cy)), int(round(cx))]
    if k == 0:
        d = ndimage.distance_transform_edt(lab == 0, return_indices=True)[1]
        k = lab[d[0][int(round(cy)), int(round(cx))], d[1][int(round(cy)), int(round(cx))]]
    ys, xs = np.nonzero(lab == k)
    if len(xs) < 20:
        return None
    ang = np.arctan2(ys - cy, xs - cx)
    rad = np.hypot(xs - cx, ys - cy)
    sec = ((ang + math.pi) / (2 * math.pi) * SECTORS).astype(int) % SECTORS
    far = np.zeros(SECTORS)
    np.maximum.at(far, sec, rad)
    mids = -math.pi + (np.arange(SECTORS) + 0.5) * 2 * math.pi / SECTORS
    keep = np.ones(SECTORS, bool)
    if skip:
        keep = np.abs((mids - CASTER_DIR + math.pi) % (2 * math.pi) - math.pi) > SKIP
    far = far[keep & (far > 0)]
    if len(far) == 0:
        return None
    return dict(med=float(np.median(far)), p90=float(np.percentile(far, 90)), max=float(far.max()), n=int(len(far)))


def blob_centre(mask, near):
    lab, n = ndimage.label(mask)
    if n == 0:
        return None
    best = None
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        if len(xs) < 20:
            continue
        cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
        d = math.hypot(cx - near[0], cy - near[1])
        if best is None or d < best[0]:
            best = (d, cx, cy)
    return best[1:] if best else None


def measure(caps, seg, drawn):
    s0 = caps.segment(seg)[0]
    rows = []
    for rel in range(s0['frames']):
        pc = caps.path(seg, rel)
        if not pc:
            continue
        h = hitbox(pc)
        H = np.asarray(Image.open(pc)).shape[0]
        u = ppu(H)
        row = dict(rel=rel)
        if h:
            row['hit'] = h[2] / u
        for name, run in drawn.items():
            pd = run.path(seg, rel)
            if not pd:
                continue
            L = luma(pd)
            for thr, tag in ((FAINT, '_faint'), (GLOW, ''), (CORE, '_core')):
                e = edges(L > thr, h[0], h[1]) if h else None
                if e:
                    row[f'{name}{tag}'] = {k: (v / u if k != 'n' else v) for k, v in e.items()}
        rows.append(row)
    return rows


def travel(caps, seg, drawn, before=8):
    """The fireball's frames: the few before the first hitbox, the drawn blob nearest the sun's spot (its box's
    half-size, units) and its distance from the spot."""
    s0 = caps.segment(seg)[0]
    first = None
    for rel in range(s0['frames']):
        pc = caps.path(seg, rel)
        h = hitbox(pc) if pc else None
        if h:
            first, spot = rel, h[:2]
            break
    if first is None:
        return []
    rows = []
    for rel in range(max(0, first - before), first + 2):
        row = dict(rel=rel)
        for name, run in drawn.items():
            pd = run.path(seg, rel)
            if not pd:
                continue
            L = luma(pd)
            u = ppu(L.shape[0])
            lab, n = ndimage.label(L > GLOW)
            best = None
            for k in range(1, n + 1):
                ys, xs = np.nonzero(lab == k)
                if len(xs) < 12:
                    continue
                cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
                if abs(cy - spot[1]) > 30 * u:
                    continue
                d = math.hypot(cx - spot[0], cy - spot[1])
                if best is None or d < best[0]:
                    best = (d, ((xs.max() - xs.min()) + (ys.max() - ys.min()) + 2) / 4)
            if best:
                row[name] = dict(r=best[1] / u, off=best[0] / u)
        rows.append(row)
    return rows


def main():
    a = [x for x in sys.argv[1:]]
    out = a[a.index('--json') + 1] if '--json' in a else None
    if out:
        i = a.index('--json'); del a[i:i + 2]
    caps, seg = fxsync.load(a[0]), a[1]
    drawn = {kv.split('=', 1)[0]: fxsync.load(kv.split('=', 1)[1]) for kv in a[2:]}
    rows = [r for r in measure(caps, seg, drawn) if 'hit' in r]
    names = list(drawn)
    print(f"{seg}: radii in units; per drawn run: glow median edge / 90th percentile / max (x hitbox), faint median, core median")
    print('  rel   hit  ' + '  '.join(f'{n:>40s}' for n in names))
    for r in rows:
        cells = []
        for n in names:
            e, fa, co = r.get(n), r.get(n + '_faint'), r.get(n + '_core')
            if not e:
                cells.append(' ' * 40); continue
            cells.append(f"{e['med']:5.1f}/{e['p90']:5.1f}/{e['max']:5.1f} ({e['med'] / r['hit']:4.2f})  "
                         f"f {fa['med'] if fa else 0:5.1f} c {co['med'] if co else 0:5.1f}")
        print(f"  {r['rel']:3d}  {r['hit']:5.1f}  " + '  '.join(f'{c:>40s}' for c in cells))
    tr = travel(caps, seg, drawn)
    if tr:
        print(f"{seg}: the frames before the hitbox (the fireball): drawn radius / distance from the sun's centre, units")
        for r in tr:
            print(f"  {r['rel']:3d}  " + '  '.join(f"{n}: {r[n]['r']:5.1f} / {r[n]['off']:5.1f}" if n in r else f'{n}: -'
                                                for n in names))
    if out:
        json.dump(dict(seg=seg, rows=rows, travel=tr), open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
