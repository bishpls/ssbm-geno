"""Geno's NEW CHALLENGER silhouette (NtAppro.usd, the challenger screen's texture animation frame 12), from in-game
renders of the production model (trailer/director/silhouette_lab.py), treated exactly as Melee's eleven are.

    silhouette.py vanilla REF_DIR [--json OUT]
        measure the eleven vanilla silhouettes (datkit mdump's j12_m0_ta0_000..010.png): framing, fill, grey levels,
        edge band, holes. Prints a table; --json writes it.
    silhouette.py solve OUT_DIR NAME=RUN:INDEX ... [--fill F] [--keep-gap PX]
        each candidate NAME from a silhouette_lab matte run (RUN) and its Geno (INDEX, left to right): the coverage solved
        from the black and white renders, fitted into 96x160 the way the family is framed, area-averaged and quantised
        to I4. Writes OUT_DIR/NAME.png (the 96x160 I4 image as greyscale), NAME.bgra (for datkit), NAME_matte.png (the
        full-resolution coverage) and stats.json (the vanilla table's numbers for each).

What the vanilla eleven are (measured, `vanilla`): flat white on black, no shading or outline; every one of the 16 I4
levels appears, but only on the one-pixel antialiased edge (1.11-1.26 partial pixels per edge pixel, the signature of
coverage area-averaged from a sharp render, not a blur); one connected shape each; the bounding box centred in the frame
(x 47.0-47.5 of 47.5 for 10 of 11, Falco 52.5; y 79-82.5 of 79.5 for 9 of 11, Game & Watch and Jigglypuff lower at 92);
scaled per character to fill the frame, max(w / 96, h / 160) 0.84-0.99 (median 0.92), Jigglypuff alone at 0.67.
"""
import json, os, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'menus'))
W, H = 96, 160
VANILLA = ['gnw', 'luigi', 'marth', 'mewtwo', 'puff', 'falco', 'ylink', 'drmario', 'roy', 'pichu', 'ganon']
CKIND = [3, 7, 9, 10, 15, 20, 21, 22, 23, 24, 25]   # gmapproach.c's switch: frame 1 + the image index


def stats(g):
    """g: 96x160 I4 levels 0-15. The family's numbers."""
    ys, xs = np.nonzero(g)
    full, zero = g == 15, g == 0
    mid = ~full & ~zero
    m = g >= 8
    per = int((m & ~ndimage.binary_erosion(m)).sum())
    near_bg = ndimage.binary_dilation(zero, np.ones((3, 3)))
    filled = ndimage.binary_fill_holes(g > 0)
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    w, h = x1 - x0 + 1, y1 - y0 + 1
    return dict(bbox=[x0, y0, x1, y1], w=w, h=h, cx=(x0 + x1) / 2, cy=(y0 + y1) / 2, fill=round(max(w / W, h / H), 3),
                coverage=round(float(g.sum()) / 15 / (W * H), 3), levels=int(len(np.unique(g))), full=int(full.sum()),
                mid=int(mid.sum()), edge_band=round(mid.sum() / max(per, 1), 2), interior_mid=int((mid & ~near_bg).sum()),
                shapes=int(ndimage.label(g > 0)[1]), holes=int(ndimage.label(filled & zero)[1]),
                hist=np.bincount(g.ravel(), minlength=16).tolist())


def load_i4(path):
    a = np.asarray(Image.open(path).convert('RGBA'))
    return (a[..., 0].astype(int) + 8) // 17


def vanilla(ref, out=None):
    rows = {}
    for i, n in enumerate(VANILLA):
        g = load_i4(os.path.join(ref, f'j12_m0_ta0_{i:03d}.png'))
        rows[n] = dict(image=i, frame=i + 1, ckind=CKIND[i], **stats(g))
    print(f'{"":8s} {"bbox":>18s} {"w":>3s} {"h":>3s} {"cx":>5s} {"cy":>5s} {"fill":>5s} {"cov":>5s} lv {"band":>4s} sh ho')
    for n, r in rows.items():
        print(f'{n:8s} {str(r["bbox"]):>18s} {r["w"]:3d} {r["h"]:3d} {r["cx"]:5.1f} {r["cy"]:5.1f} {r["fill"]:5.2f} '
              f'{r["coverage"]:5.3f} {r["levels"]:2d} {r["edge_band"]:4.2f} {r["shapes"]:2d} {r["holes"]:2d}')
    if out: json.dump(rows, open(out, 'w'), indent=1)
    return rows


def coverage(run, i, keep_gap=24):
    """The Geno at position i: coverage 0-1 at the dump's resolution. Parts of the model separated by up to keep_gap
    pixels stay (his hair curls stand off the brim); anything farther (stray effects, the stage's sparkles) goes."""
    import portrait                       # menus/portrait.py: the black/white difference matte
    sf = portrait.shot_frames(run)
    b, w = sf[1000 + 100 * i]
    B, Wh = portrait.load(run, b), portrait.load(run, w)
    a3 = 1.0 - (Wh - B)
    a = np.clip(a3.mean(axis=2), 0, 1)
    spread = float(np.abs(a3 - a3.mean(axis=2, keepdims=True)).max())
    lab, n = ndimage.label(ndimage.binary_dilation(a > 0.02, iterations=keep_gap))
    dropped = 0.0
    if n > 1:
        keep = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
        dropped = float(a[~keep].sum())
        a = np.where(keep, a, 0.0)
    return a, dict(black=b, white=w, spread=round(spread, 4), dropped_px=round(dropped, 1))


def fit(a, fill=0.94, cx=47.5, cy=79.5):
    """Fit the coverage into 96x160 as the family is: the bounding box (coverage over half) centred at (cx, cy), scaled
    so max(w / 96, h / 160) = fill; area-averaged (box filter) down from the render, so the edge is one pixel of exact
    coverage. Returns the I4 levels (0-15, rounded) and the scale (output pixels per render pixel)."""
    ys, xs = np.nonzero(a > 0.5)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    s = fill / max((x1 - x0) / W, (y1 - y0) / H)              # output pixels per render pixel
    # the render box that maps onto the 96x160 frame: the bbox centre lands on (cx, cy) + 0.5 (pixel centres)
    bx0 = (x0 + x1) / 2 - (cx + 0.5) / s
    by0 = (y0 + y1) / 2 - (cy + 0.5) / s
    box = (bx0, by0, bx0 + W / s, by0 + H / s)
    pad = int(max(W, H) / s) + 2                             # the box may run past the render: pad with empty
    ap = np.pad(a.astype(np.float32), pad)
    im = Image.fromarray(ap, 'F').resize((W, H), Image.BOX, box=tuple(v + pad for v in box))
    cov = np.clip(np.asarray(im, np.float64), 0, 1)
    return np.rint(cov * 15).astype(int), s


def write(out, name, g, a=None):
    v = (g * 17).astype(np.uint8)
    Image.fromarray(v, 'L').save(os.path.join(out, f'{name}.png'))
    bgra = np.dstack([v, v, v, np.full_like(v, 255)])
    open(os.path.join(out, f'{name}.bgra'), 'wb').write(bgra.tobytes())
    if a is not None:
        Image.fromarray((np.clip(a, 0, 1) * 255).round().astype(np.uint8), 'L').save(os.path.join(out, f'{name}_matte.png'))


def solve(out, specs, fill=0.94, keep_gap=24):
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, 'stats.json')
    allst = json.load(open(path)) if os.path.exists(path) else {}
    for spec in specs:
        name, rest = spec.split('=', 1)
        run, idx = rest.rsplit(':', 1)
        a, info = coverage(run, int(idx), keep_gap)
        g, s = fit(a, fill)
        write(out, name, g, a)
        st = stats(g)
        allst[name] = dict(run=run, index=int(idx), scale=round(s, 4), render_px=list(a.shape[::-1]), **info, **st)
        print(f'{name:14s} {str(st["bbox"]):>18s} w {st["w"]:3d} h {st["h"]:3d} fill {st["fill"]:.2f} cov {st["coverage"]:.3f} '
              f'levels {st["levels"]} band {st["edge_band"]:.2f} shapes {st["shapes"]} holes {st["holes"]} '
              f'spread {info["spread"]} dropped {info["dropped_px"]} (render px {1 / s:.1f} per pixel)')
    json.dump(allst, open(path, 'w'), indent=1)


if __name__ == '__main__':
    args = sys.argv[1:]
    opt = {}
    for k in ('--fill', '--keep-gap', '--json'):
        if k in args:
            j = args.index(k); opt[k] = args[j + 1]; del args[j:j + 2]
    if args[0] == 'vanilla':
        vanilla(args[1], opt.get('--json'))
    elif args[0] == 'solve':
        solve(args[1], args[2:], float(opt.get('--fill', 0.94)), int(opt.get('--keep-gap', 24)))
    else:
        sys.exit(__doc__)
