"""How far a move's drawn effect reaches against its hitboxes, from a pair of gunfx_lab runs (the same frames drawn on
black, GUNFX_COLL=0, and as collision capsules, GUNFX_COLL=2).
    .venv/bin/python projects/geno/fx/gunfxmeasure.py DRAWN_RUN CAPS_RUN [--out OUT.json] [--overlay DIR] [--seg a,b]
The capsule run is best made without the performer's own effects on the disc (Geno: no EfGeData.dat), since effects draw
over the capsules; a cast member's can't be removed, so their hitboxes are hull-filled (an effect inside a hitbox), and
intangible (blue) hurtboxes are read only for Geno, whose capsule run has no effects (a blue or purple effect would pass).
Per frame with a hitbox on screen, along the move's axis (the plan's: +x forward, -x back, +y up, -y down, x each side):
  body   the farthest hurtbox pixel (the yellow capsules)
  hit    the farthest hitbox pixel (the red capsules; red under a hurtbox draws orange)
  drawn  the farthest drawn pixel (luma > 40 on black, specks removed) within 6 units of the hitboxes' box
and, in units (res 2 at 137 back: 14.4 px/unit; the plan's camera):
  disjoint = hit - body, shown = drawn - body, ratio = shown / disjoint (1: the drawing reaches the hitbox's tip),
  past = drawn - hit (how far the drawing spills past the tip), cover = the share of the disjoint hitbox area (hitbox, not
  hurtbox) that is drawn.
Per segment: the frame of the largest disjoint, the mean cover over the active frames, and how many frames past the last
active one something is still drawn past the body (linger).
"""
import json, math, os, sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage import morphology

import fxsync

DIST = {'match': 137.0, 'mid': 80.0, 'close': 58.0}
FOV = 30.0
LUMA = 40
MARGIN = 6.0          # units round the hitboxes' box where drawn pixels count


def masks(c, intangible=False):
    """The capsule display's flat colours: a hitbox (128, 0, 0) (192, 0, 0 where two overlap); a half-transparent hurtbox,
    yellow (128, 128, 0 over black, 192, 128, 0 over a hitbox) or blue when intangible (0, 0, 128; over a hitbox purple).
    An effect drawn over a hitbox breaks its disc (Ness's PSI spark), so each hitbox region is closed over thin gaps and
    filled to its convex hull."""
    R, G, B = c[..., 0], c[..., 1], c[..., 2]
    red = (R > 100) & (G < 26) & (B < 26)
    orange = (abs(R - 192) < 22) & (abs(G - 128) < 18) & (B < 26)
    purple = (R > 24) & (G < 26) & (B > 100)
    yellow = (R > 100) & (abs(R - G) < 14) & (B < 26)
    blue = (R < 24) & (G < 26) & (B > 100)
    hurt = yellow | orange | (blue | purple if intangible else False)
    if red.sum() < 40:                   # a hitbox always shows some bare red: no red, no hitbox (an effect's warm ring)
        return np.zeros_like(red), hurt
    hit = ndimage.binary_closing(red | orange | (purple if intangible else False), structure=morphology.disk(6))
    hit = morphology.convex_hull_object(hit) if hit.any() else hit
    return hit, hurt


def specks(a):
    """The background's static specks (stars) in a frame: small lit components, grown a little, to mask out."""
    luma = (a[..., 0] * 299 + a[..., 1] * 587 + a[..., 2] * 114) // 1000
    m = luma > LUMA
    lab, n = ndimage.label(m)
    if not n:
        return m
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    keep = np.zeros(n + 1, bool); keep[1:] = sizes < 400
    return ndimage.binary_dilation(keep[lab], iterations=3)


def drawn_mask(a):
    luma = (a[..., 0] * 299 + a[..., 1] * 587 + a[..., 2] * 114) // 1000
    m = luma > LUMA
    lab, n = ndimage.label(m)
    if n:
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        keep = np.zeros(n + 1, bool); keep[1:] = sizes >= 25
        m = keep[lab]
    return m


def coord(axis, H, W):
    yy, xx = np.mgrid[0:H, 0:W]
    return {'+x': xx, '-x': -xx, '+y': -yy, '-y': yy}[axis]


def far(mask, u):
    return u[mask].max() if mask.any() else None


def frame_measure(a, c, axis, ppu, bg=None, intangible=False):
    hit, hurt = masks(c, intangible)
    if hit.sum() < 40:
        return None
    drawn = drawn_mask(a)
    if bg is not None:
        drawn &= ~bg
    # only what touches the move: drawn components overlapping the hitboxes (grown 2 units) or the body (hurtboxes grown
    # 1): the background's twinkling stars come and go, and would read as reach
    # (a component off the body must also be bigger than a star speck, 0.6 square units: a twinkling star inside a
    # hitbox read as 12 units of reach)
    body = ndimage.binary_dilation(hurt, iterations=int(ppu))
    near = ndimage.binary_dilation(hit, iterations=int(2 * ppu))
    lab, n = ndimage.label(drawn)
    if n:
        sizes = np.bincount(lab.ravel(), minlength=n + 1)
        on_body = np.zeros(n + 1, bool); on_body[np.unique(lab[body & drawn])] = True
        by_hit = np.zeros(n + 1, bool); by_hit[np.unique(lab[near & drawn])] = True
        keep = on_body | (by_hit & (sizes >= 0.6 * ppu * ppu))
        keep[0] = False
        drawn = keep[lab]
    H, W = hit.shape
    ys, xs = np.nonzero(hit)
    m = int(MARGIN * ppu)
    box = np.zeros_like(hit)
    box[max(0, ys.min() - m):ys.max() + m, max(0, xs.min() - m):xs.max() + m] = True
    hy, hx = np.nonzero(hurt)
    if len(hx):
        box[max(0, hy.min()):hy.max() + 1, max(0, hx.min()):hx.max() + 1] = True
    out = {}
    sides = [(axis, np.ones_like(hit))]
    if axis == 'x':                                   # both sides: split at the body's centre
        cx = int(np.median(hx)) if len(hx) else W // 2
        left = np.zeros_like(hit); left[:, :cx] = True
        sides = [('+x', ~left), ('-x', left)]
    for ax, half in sides:
        u = coord(ax, H, W)
        hh = hit & half
        if hh.sum() < 40:
            continue
        b, h, d = far(hurt & half, u), far(hh, u), far(drawn & box & half, u)
        if b is None or h is None:
            continue
        dis = hh & ~hurt
        rec = dict(body=float(b), hit=float(h), drawn=None if d is None else float(d),
                   disjoint=(h - b) / ppu, shown=None if d is None else (d - b) / ppu,
                   past=None if d is None else (d - h) / ppu,
                   cover=float((drawn & dis).sum() / dis.sum()) if dis.sum() >= 40 else None)
        out[ax] = rec
    return out, hit, hurt, drawn


def measure(drawn_run, caps_run, seg):
    s, _ = drawn_run.segment(seg)
    ppu = None
    frames = []
    p0 = drawn_run.path(seg, 0)
    bg = specks(np.asarray(Image.open(p0).convert('RGB')).astype(int)) if p0 else None
    for rel in range(s['frames']):
        pd, pc = drawn_run.path(seg, rel), caps_run.path(seg, rel)
        if not pd or not pc:
            continue
        a = np.asarray(Image.open(pd).convert('RGB')).astype(int)
        c = np.asarray(Image.open(pc).convert('RGB')).astype(int)
        if ppu is None:
            ppu = a.shape[0] / (2 * DIST[s.get('cam', 'match')] * math.tan(math.radians(FOV / 2)))
        r = frame_measure(a, c, s['axis'], ppu, bg, intangible=s.get('char') == 'geno')
        frames.append((rel, r))
    return s, ppu, frames


def summary(s, frames):
    act = [(rel, r[0]) for rel, r in frames if r and r[0]]
    if not act:
        return None
    res = dict(active=[act[0][0], act[-1][0]], frames=len(act))
    for ax in sorted({k for _, r in act for k in r}):
        recs = [(rel, r[ax]) for rel, r in act if ax in r]
        rel, top = max(recs, key=lambda x: x[1]['disjoint'])
        covers = [r['cover'] for _, r in recs if r['cover'] is not None]
        shown = [r['shown'] for _, r in recs if r['shown'] is not None]
        res[ax] = dict(frame=rel, disjoint=round(top['disjoint'], 2),
                       shown=None if top['shown'] is None else round(top['shown'], 2),
                       ratio=None if top['shown'] is None or top['disjoint'] < 0.5 else round(top['shown'] / top['disjoint'], 2),
                       past=None if top['past'] is None else round(top['past'], 2),
                       shown_max=round(max(shown), 2) if shown else None,
                       cover_mean=round(float(np.mean(covers)), 2) if covers else None,
                       cover_first=None if recs[0][1]['cover'] is None else round(recs[0][1]['cover'], 2))
    return res


def overlay(drawn_run, seg, frames, ppu, out_dir, span=(-2, 8)):
    """The drawn frames of the active window with the hitbox (red) and hurtbox (yellow) outlines and the three lines."""
    act = [rel for rel, r in frames if r and r[0]]
    if not act:
        return None
    rels = list(range(act[0] + span[0], act[0] + span[1]))
    cells = []
    byrel = dict(frames)
    for rel in rels:
        p = drawn_run.path(seg, rel)
        if not p:
            continue
        im = Image.open(p).convert('RGB')
        r = byrel.get(rel)
        if r:
            _, hit, hurt, drawn = r
            a = np.asarray(im).copy()
            eh = hit & ~ndimage.binary_erosion(hit, iterations=2)
            eu = hurt & ~ndimage.binary_erosion(hurt, iterations=1)
            a[eu] = (255, 230, 0); a[eh] = (255, 40, 40)
            im = Image.fromarray(a)
        cells.append((rel, im))
    # crop round everything that's lit in any cell
    boxes = [np.asarray(im).sum(2) > 150 for _, im in cells]
    anym = np.any(boxes, axis=0)
    ys, xs = np.nonzero(anym)
    pad = 30
    x0, x1, y0, y1 = max(0, xs.min() - pad), xs.max() + pad, max(0, ys.min() - pad), ys.max() + pad
    cw = 300
    ch = int(cw * (y1 - y0) / max(1, x1 - x0))
    sheet = Image.new('RGB', (len(cells) * (cw + 3), ch + 22), (14, 14, 18))
    d = ImageDraw.Draw(sheet)
    d.text((4, 4), f'{seg}: red = hitbox outline, yellow = hurtbox ({ppu:.1f} px/unit)', fill=(240, 240, 240))
    for i, (rel, im) in enumerate(cells):
        sheet.paste(im.crop((x0, y0, x1, y1)).resize((cw, ch), Image.LANCZOS), (i * (cw + 3), 22))
        r = byrel.get(rel)
        txt = f'+{rel}'
        if r and r[0]:
            for ax, q in r[0].items():
                txt += f"  {ax} dis {q['disjoint']:.1f}" + (f" shown {q['shown']:.1f}" if q['shown'] is not None else '') + \
                       (f" cov {q['cover']:.2f}" if q['cover'] is not None else '')
        d.text((i * (cw + 3) + 3, 24), txt, fill=(255, 255, 0))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f'measure_{seg}.png')
    sheet.save(path)
    return path


def main():
    drawn_run, caps_run = fxsync.load(sys.argv[1]), fxsync.load(sys.argv[2])
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
    ov = sys.argv[sys.argv.index('--overlay') + 1] if '--overlay' in sys.argv else None
    segs = sys.argv[sys.argv.index('--seg') + 1].split(',') if '--seg' in sys.argv else [s['label'] for s, _ in drawn_run.offsets]
    res = {}
    for seg in segs:
        s, ppu, frames = measure(drawn_run, caps_run, seg)
        sm = summary(s, frames)
        res[seg] = dict(summary=sm, ppu=ppu,
                        frames=[dict(rel=rel, **{ax: q for ax, q in r[0].items()}) for rel, r in frames if r and r[0]])
        if ov:
            res[seg]['overlay'] = overlay(drawn_run, seg, frames, ppu, ov)
        if not sm:
            print(f'{seg:16s} no hitbox found'); continue
        for ax in [k for k in sm if k in ('+x', '-x', '+y', '-y')]:
            q = sm[ax]
            print(f"{seg:16s} {ax}  active {sm['active'][0]}-{sm['active'][1]} ({sm['frames']})  disjoint {q['disjoint']:5.1f}  "
                  f"shown {q['shown'] if q['shown'] is not None else '-':>5}  ratio {q['ratio'] if q['ratio'] is not None else '-':>5}  "
                  f"past {q['past'] if q['past'] is not None else '-':>5}  shown max {q['shown_max']}  cover mean "
                  f"{q['cover_mean']} first {q['cover_first']}  (frame {q['frame']})")
    if out:
        json.dump(res, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
