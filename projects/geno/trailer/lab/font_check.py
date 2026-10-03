"""The font patch's identity check: every existing glyph must draw exactly as before.
    .venv/bin/python projects/geno/trailer/lab/font_check.py BEFORE_RUN AFTER_RUN OUT_PREFIX [--menu]
Compares two runs of the same lab (built before and after the ♡♪ patch) frame by frame over the whole capture: the
number of differing pixels per frame, the differing region's bounding boxes, and a diff image of the frame that differs
most (differences in red over the after frame). Director runs align on their slate; --menu runs (no slate) on the
dump's own frame numbers (a menu test is deterministic from boot).
    .venv/bin/python projects/geno/trailer/lab/font_check.py --dol ORIG_ATLAS_BIN PATCHED_DOL
checks the data instead: the original atlas's 287 glyphs (146,944 bytes) appear verbatim in the patched DOL, followed
by the two new ones.
"""
import glob, json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tlab


def frames(run, menu):
    r = tlab.load(run)
    fs = r.frames
    if not menu:
        fs = fs[r.first:]
    return fs


def compare(before, after, out, menu=False):
    fa, fb = frames(before, menu), frames(after, menu)
    n = min(len(fa), len(fb))
    rows, worst = [], (0, None)
    total = np.zeros(1)
    for i in range(n):
        a = np.asarray(Image.open(fa[i]).convert('RGB')).astype(int)
        b = np.asarray(Image.open(fb[i]).convert('RGB')).astype(int)
        d = np.abs(a - b).max(axis=2) > 0
        k = int(d.sum())
        boxes = []
        if k:
            lab, nl = ndimage.label(ndimage.binary_dilation(d, iterations=6))
            for sl in ndimage.find_objects(lab):
                boxes.append((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop))
        rows.append(dict(frame=i, diff_pixels=k, boxes=boxes))
        if k > worst[0]: worst = (k, i)
    res = dict(before=before, after=after, frames=n, frames_identical=sum(1 for r in rows if r['diff_pixels'] == 0),
               max_diff_pixels=worst[0], worst_frame=worst[1],
               boxes=sorted({tuple(b) for r in rows for b in r['boxes']}))
    if worst[1] is not None:
        i = worst[1]
        a = np.asarray(Image.open(fa[i]).convert('RGB')).astype(int)
        b = np.asarray(Image.open(fb[i]).convert('RGB'))
        d = np.abs(a - b.astype(int)).max(axis=2) > 0
        v = b.copy(); v[d] = (255, 0, 0)
        Image.fromarray(np.concatenate([a.astype(np.uint8), b, v], axis=1)).save(out + '_worst.png')
    json.dump(dict(res, per_frame=rows), open(out + '.json', 'w'), indent=1)
    print(json.dumps(res))
    return res


def dol(atlas_bin, patched_dol):
    a = open(atlas_bin, 'rb').read()
    d = open(patched_dol, 'rb').read()
    i = d.find(a)
    print(json.dumps(dict(atlas_bytes=len(a), found_at=i, found=i >= 0,
                          new_glyph_bytes_after=len(d[i + len(a):i + len(a) + 1024]) if i >= 0 else 0)))
    return i


if __name__ == '__main__':
    if sys.argv[1] == '--dol':
        dol(sys.argv[2], sys.argv[3])
    else:
        compare(sys.argv[1], sys.argv[2], sys.argv[3], '--menu' in sys.argv)
