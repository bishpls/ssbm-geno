"""Measure how big projectiles are drawn against their hitboxes, from a pair of scale_lab runs (the same frames drawn on
black, SCALE_COLL=0, and as collision capsules only, SCALE_COLL=2).
    .venv/bin/python projects/geno/fx/scalemeasure.py DRAWN_RUN CAPSULE_RUN [OUT.json] [--seg g1,g2,...]
For every frame of each segment, the projectile is the largest blob right of the shooter (drawn: luma over a threshold on
black; hitbox: the capsules' red), kept when it's wholly in frame on both runs. Its bounding box, in units (the camera:
150 back, 30 degrees vertical; the horizontal scale from the pixel aspect, which a single round hitbox measures), gives
length (along the flight, x) and thickness (y). Pixels are square: the Beam's nose moves 79 px a frame at res 2 for its
6 units a frame (13.17 px/unit) against 13.14 vertically. The capsules are drawn swept from the last frame's position,
so a hitbox's instantaneous length is its drawn length less the projectile's speed (measured from its own track). Two
drawn thresholds: `glow` (luma > 40: anything you see) and `core`
(luma > 150: the bright body). Reported per segment: the median over the frames after the projectile reaches its full
length (the beams and lasers stretch out of the barrel first).
"""
import json, math, sys

import numpy as np
from PIL import Image
from scipy import ndimage

import fxsync

DIST, FOV, CAM_X, CAM_Y = 150.0, 30.0, 15.0, 12.0
SHOOTER_X = -30.0
GLOW, CORE = 40, 150


def ppu_y(h):
    return h / (2 * DIST * math.tan(math.radians(FOV / 2)))


def blob(mask, min_px=30):
    """The bounding box of every component of at least min_px pixels (a projectile with several hitbox spheres, or a
    volley of bullets, is several components: the lasers carry four spheres strung along their length)."""
    lab, n = ndimage.label(mask)
    if n == 0:
        return None
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    keep = [k + 1 for k in range(n) if sizes[k] >= min_px]
    if not keep:
        return None
    ys, xs = np.nonzero(np.isin(lab, keep))
    return xs.min(), xs.max(), ys.min(), ys.max(), int(sum(sizes[k - 1] for k in keep))


X0 = {'finger': 7.0}          # the region's left edge, units past the shooter (the volley trails ~28 behind its nose)
FROM = {'finger': 26}        # the first frame measured (the muzzle puff, near the hand, has faded)


def measure(drawn, caps, seg, x0_units=None):
    out = []
    s0 = drawn.segment(seg)[0]
    x0_units = X0.get(seg, 15.0) if x0_units is None else x0_units
    for rel in range(FROM.get(seg, 0), s0['frames']):
        pd, pc = drawn.path(seg, rel), caps.path(seg, rel)
        if not pd or not pc:
            continue
        a = np.asarray(Image.open(pd).convert('RGB')).astype(int)
        c = np.asarray(Image.open(pc).convert('RGB')).astype(int)
        H, W = a.shape[:2]
        py = ppu_y(H)
        left = int(W / 2 + (SHOOTER_X + x0_units - CAM_X) * py * ASPECT)
        luma = (a[..., 0] * 299 + a[..., 1] * 587 + a[..., 2] * 114) // 1000
        red = (c[..., 0] > 90) & (c[..., 0] > 2 * c[..., 1]) & (c[..., 0] > 2 * c[..., 2])
        region = np.zeros((H, W), bool); region[4:H - 4, left:W - 4] = True
        h = blob(red & region)
        if h:                               # the drawn projectile: within 8 units of the hitbox's rows (not stray dots)
            band = np.zeros((H, W), bool); m = int(8 * py)
            band[max(0, h[2] - m):min(H, h[3] + m), left:W - 4] = True
            region &= band
        g, k = blob((luma > GLOW) & region), blob((luma > CORE) & region)
        if not g or not h or g[4] < 30 or h[4] < 30:
            continue
        if min(g[0], h[0]) <= left + 1 or max(g[1], h[1]) >= W - 6:
            continue                                   # touching the region's edges: not wholly in view
        px = py * ASPECT
        rec = dict(rel=rel, nose=h[1] / px,
                   glow_len=(g[1] - g[0] + 1) / px, glow_thick=(g[3] - g[2] + 1) / py,
                   hit_len=(h[1] - h[0] + 1) / px, hit_thick=(h[3] - h[2] + 1) / py,
                   hit_box=(h[1] - h[0] + 1, h[3] - h[2] + 1))
        if k:
            rec.update(core_len=(k[1] - k[0] + 1) / px, core_thick=(k[3] - k[2] + 1) / py)
        out.append(rec)
    return out


def summary(recs):
    if not recs:
        return None
    full = max(r['hit_len'] for r in recs)
    late = [r for r in recs if r['hit_len'] >= 0.95 * full] or recs
    med = lambda k: float(np.median([r[k] for r in late if k in r])) if any(k in r for r in late) else None
    sp = [b['nose'] - a['nose'] for a, b in zip(recs, recs[1:]) if b['rel'] == a['rel'] + 1]
    speed = float(np.median(sp)) if sp else 0.0
    res = {k: med(k) for k in ('glow_len', 'glow_thick', 'core_len', 'core_thick', 'hit_len', 'hit_thick')}
    res.update(frames=len(late), speed=speed, hit_len_now=max(res['hit_len'] - speed, res['hit_thick']))
    return res


ASPECT = 1.0          # square pixels (measured: the docstring)


def main():
    drawn, caps = fxsync.load(sys.argv[1]), fxsync.load(sys.argv[2])
    out = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None
    segs = sys.argv[sys.argv.index('--seg') + 1].split(',') if '--seg' in sys.argv else [s['label'] for s, _ in drawn.offsets]
    res = {}
    for seg in segs:
        res[seg] = summary(measure(drawn, caps, seg))
        s = res[seg]
        if s:
            print(f"{seg:7s} drawn glow {s['glow_len']:5.1f} x {s['glow_thick']:4.1f}  core {s['core_len'] or 0:5.1f} x "
                  f"{s['core_thick'] or 0:4.1f}  hitbox {s['hit_len_now']:5.1f} x {s['hit_thick']:4.1f} (swept {s['hit_len']:4.1f}, "
                  f"{s['speed']:.1f}/frame)  glow/hit: thick {s['glow_thick'] / s['hit_thick']:.2f} "
                  f"len {s['glow_len'] / s['hit_len_now']:.2f}  ({s['frames']} frames)")
        else:
            print(seg, 'no frames with the projectile wholly in view')
    if out:
        json.dump(dict(aspect=ASPECT, segments=res), open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
