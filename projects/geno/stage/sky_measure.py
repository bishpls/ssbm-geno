"""The sky's motion, measured (not only stills).
    .venv/bin/python projects/geno/stage/sky_measure.py readability OUT.json RUN_DIR [FROM TO]   every frame's readability
    .venv/bin/python projects/geno/stage/sky_measure.py flash OUT.json RUN_DIR [FROM TO]         per-frame change per region
    .venv/bin/python projects/geno/stage/sky_measure.py lines OUT.json IMAGE [IMAGE ...]          seams: 1-px full-width lines
readability: lookmetrics' score for each dumped frame (the match framing, fighters standing), min / mean / the frame of
the minimum, and the series. flash: the frame split into a 16 x 12 grid of regions; for each, the per-frame change of
mean relative luminance; the largest over all regions and frames, its 99.9th percentile, and where and when the largest
was (the flash_lab camera shows only the background, so every change is the background's own). lines: rows darker than
both neighbours by 4 levels across more than half the width (a card's edge filtering in its far row, a sliver of sky
between two cards); real edges (a platform's top) show too, so compare against a known-good frame.
"""
import glob, json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lookmetrics  # noqa: E402


def frames(run, lo=None, hi=None):
    fs = sorted(glob.glob(os.path.join(run, 'f[0-9]*.png')))
    return [f for f in fs if (lo is None or int(os.path.basename(f)[1:6]) >= lo) and (hi is None or int(os.path.basename(f)[1:6]) <= hi)]


def readability(out, run, lo=None, hi=None):
    fs = frames(run, lo, hi)
    r = [lookmetrics.metrics(f)['readability'] for f in fs]
    k = int(np.argmin(r))
    res = dict(frames=len(r), min=round(min(r), 4), mean=round(float(np.mean(r)), 4), p05=round(float(np.percentile(r, 5)), 4),
               min_frame=os.path.basename(fs[k]), series=[round(x, 4) for x in r])
    json.dump(res, open(out, 'w'))
    print(json.dumps({k: v for k, v in res.items() if k != 'series'}))


def flash(out, run, lo=None, hi=None, gx=16, gy=12):
    fs = frames(run, lo, hi)
    prev, worst, all_d = None, (0.0, None, None), []
    for f in fs:
        a = np.asarray(Image.open(f).convert('RGB')).astype(float) / 255
        lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
        Y = lin @ np.array([0.2126, 0.7152, 0.0722])
        H, W = Y.shape
        cells = Y[:H // gy * gy, :W // gx * gx].reshape(gy, H // gy, gx, W // gx).mean((1, 3))
        if prev is not None:
            d = np.abs(cells - prev)
            all_d.append(d.ravel())
            if d.max() > worst[0]:
                j = np.unravel_index(int(d.argmax()), d.shape)
                worst = (float(d.max()), os.path.basename(f), [int(j[1]), int(j[0])])
        prev = cells
    all_d = np.concatenate(all_d)
    res = dict(frames=len(fs), max_change=round(worst[0], 4), at_frame=worst[1], cell_xy=worst[2],
               p999=round(float(np.percentile(all_d, 99.9)), 5), mean=round(float(all_d.mean()), 6))
    json.dump(res, open(out, 'w'))
    print(json.dumps(res))


def lines(out, *images):
    res = {}
    for im in images:
        a = np.asarray(Image.open(im).convert('L')).astype(float)
        d = a[1:-1] - 0.5 * (a[:-2] + a[2:])
        res[os.path.basename(im)] = [[r + 1, round(float((d[r] < -4).mean()), 2)] for r in range(a.shape[0] - 2) if (d[r] < -4).mean() > 0.5]
    json.dump(res, open(out, 'w')); print(json.dumps(res))


if __name__ == '__main__':
    if sys.argv[1] == 'lines':
        lines(sys.argv[2], *sys.argv[3:]); sys.exit(0)
    mode, out, run = sys.argv[1:4]
    lo, hi = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (None, None)
    (readability if mode == 'readability' else flash)(out, run, lo, hi)
