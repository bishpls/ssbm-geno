"""Geno's menu art from in-game renders of the production model (director/portrait_lab.py): each costume's character
select portrait and stock icon, and costume 0's CSS icon face and VS Records face.
    .venv/bin/python projects/geno/menus/portrait.py OUT RUN:COSTUMES [RUN:COSTUMES ...] [--glyphs DIR]
e.g. portrait.py $MELEE_WORK/menus/geno ~/.../runs/portrait_a:0,1,2,3 ~/.../runs/portrait_b:4
RUN is a portrait_lab matte run (its osreport's MARK lines name each shot), COSTUMES the costume ids of its Genos, left to
right. Writes to OUT: matte/c<C>_k<K>.png (each shot solved to colour and coverage), and the art menus/build.py reads:
    csp_<C>.png    136x188 portrait, one per costume (the door portraits, the 1P and CPU doors)
    icon.png       64x56 CSS icon: costume 0's head in the icon frame, the name band in Melee's own letters
    stock_<C>.png  24x24 stock icon, one per costume (HUD, results panels, 1P select), 15 colours and transparency
    face.png       64x32 VS Records face (costume 0)
plus sheet.png, every output at scale. The icon frame and letters are cut from the disc's own icons (css/placeholder.py),
and every output is a render of the game: all of it stays in the work folder, never in git.

The matte: every shot is rendered twice while the game is frozen, on black (B) then on white (W). A pixel of coverage a
and colour F shows B = a F and W = a F + (1 - a), so a = 1 - (W - B) and the premultiplied colour is B: exact, with no key
colour to fight a costume and the antialiased edges intact.
"""
import os, re, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'css'))
import art  # noqa: E402

FRAMINGS = 1                     # portrait_lab's one framing: every piece of art is cropped from it

# crops, as fractions of the frame (res-independent; right follows from the aspect). Every costume uses the same boxes,
# so the doors line up. Measured on costume 0's matte at res 3 (1920x1584; portrait.py prints each shot's bounding box):
# the figure spans x 0.29-0.66, y 0.044-0.93, the knees at 0.70; the cap x 0.38-0.65 from y 0.042; the eyes y 0.27-0.30,
# x 0.48-0.63; the chin 0.38, the barrel below it. Vanilla portraits put the head at the top and crop at the thighs or
# knees; the icons and Records faces are close crops, the eyes large.
CSP_BOX = (0.26, 0.025, None, 0.73)
HEAD_BOX = (0.365, 0.035, None, 0.39)      # square: cap to chin (the stock icons)
ICON_BOX = (0.36, 0.14, None, 0.39)        # the icon's 58x38 window: the ribbon to the chin, the eyes a little below centre
FACE_BOX = (0.445, 0.215, None, 0.335)     # the Records face 2:1: under the brim, both eyes and the nose


def marks(run):
    out = {}
    for line in open(os.path.join(run, 'osreport.log'), errors='replace'):
        m = re.search(r'MARK (\d+) (\d+)', line)
        if m: out[int(m.group(2))] = int(m.group(1))
    return out


def load(run, f):
    return np.asarray(Image.open(os.path.join(run, f'f{f:05d}.png')).convert('RGB')).astype(np.float64) / 255


def shot_frames(run):
    """{MARK code of a black render: (black dump frame, white dump frame)}. The dump drops a frame or two around a freeze,
    so frames are found by content: each shot's white background is one run of frames, its black render the frame just
    before it (the camera cut three frames earlier); the runs, in order, are the MARK codes in order."""
    mk = marks(run)
    codes = sorted((f, c) for c, f in mk.items() if c % 2 == 0)
    names = sorted(n for n in os.listdir(run) if re.fullmatch(r'f\d{5}\.png', n))
    corner = {int(n[1:6]): np.asarray(Image.open(os.path.join(run, n)).convert('L').crop((0, 0, 8, 8))).mean() for n in names}
    fs = sorted(corner)
    runs, cur = [], None
    for fr in fs:
        if corner[fr] > 250:
            if cur and fr == cur[-1] + 1: cur.append(fr)
            else: cur = [fr]; runs.append(cur)
        else: cur = None
    if len(runs) != len(codes):
        sys.exit(f'{run}: {len(runs)} white renders in the dump, {len(codes)} shots in the osreport')
    out = {}
    for (_, c), r in zip(codes, runs):
        w = r[len(r) // 2]
        # the black render: of the (up to three) black frames just before, the one that agrees best with the white render
        # (a frame dropped near the camera's cut can leave the cut frame itself next to the white run)
        cands = [b for b in range(r[0] - 3, r[0]) if corner.get(b, 255) < 5]
        if not cands: sys.exit(f'{run}: no black render before frame {r[0]} (shot {c})')
        W = load(run, w)
        def partial(b):
            a = (1.0 - (W - load(run, b))).mean(axis=2)
            return ((a > 0.02) & (a < 0.98)).mean()
        out[c] = (min(cands, key=partial), w)
    return out


def matte(run, i, k, sf):
    """The Geno at position i, framing k: premultiplied RGBA (float) and the solve's consistency (0 is perfect)."""
    b, w = sf[1000 + 100 * i + 10 * k]
    B, W = load(run, b), load(run, w)
    a3 = 1.0 - (W - B)
    a = np.clip(a3.mean(axis=2), 0, 1)
    spread = float(np.abs(a3 - a3.mean(axis=2, keepdims=True)).max())   # channels should agree: 0 is a perfect solve
    # keep the fighter: the largest connected shape (the stage's background sparkles still draw with the stage hidden)
    from scipy import ndimage
    lab, n = ndimage.label(ndimage.binary_dilation(a > 0.02, iterations=3))
    if n > 1:
        keep = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
        a = np.where(keep, a, 0.0)
    return np.dstack([np.clip(B, 0, 1) * (a[..., None] > 0), a]), spread


def unpremul(p):
    a = p[..., 3:4]
    rgb = np.where(a > 1e-4, p[..., :3] / np.maximum(a, 1e-4), 0)
    return np.dstack([np.clip(rgb, 0, 1), a[..., 0]])


def to_img(rgba):
    return Image.fromarray((np.clip(rgba, 0, 1) * 255).round().astype(np.uint8), 'RGBA')


def crop(p, box, aspect):
    """A box (fractions of the frame; right from the aspect w/h) of a premultiplied image, cut exactly (pixels outside the
    frame are empty)."""
    H, W = p.shape[:2]
    l, t, _, b = box
    h = (b - t) * H
    w = h * aspect
    x0, y0 = int(round(l * W)), int(round(t * H))
    x1, y1 = x0 + int(round(w)), y0 + int(round(h))
    out = np.zeros((y1 - y0, x1 - x0, 4))
    sx0, sy0, sx1, sy1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = p[sy0:sy1, sx0:sx1]
    return out


def resize(p, size):
    """Premultiplied Lanczos resample (the transparent fringe doesn't darken the edges), then straight alpha."""
    chans = [np.asarray(Image.fromarray(p[..., c].astype(np.float32), 'F').resize(size, Image.LANCZOS), np.float64)
             for c in range(4)]
    q = np.clip(np.dstack(chans), 0, 1)
    q[..., :3] = np.minimum(q[..., :3], q[..., 3:4])
    return unpremul(q)


def csp(p):
    return to_img(resize(crop(p, CSP_BOX, 136 / 188), (136, 188)))


def stock(p):
    """24x24: art.py's treatment (22 px head, 1 px dark outline, 15 colours) on the rendered head."""
    head = to_img(unpremul(crop(p, HEAD_BOX, 1.0)))
    return art.stock_from(head)


def icon(p, frame_dir):
    """The 64x56 CSS icon: the head in the frame's 58x38 window (transparent around him, as the cast's), and the name band
    cut from the disc's own icons (placeholder.py)."""
    import placeholder
    placeholder.W = frame_dir
    ness = np.array(Image.open(os.path.join(frame_dir, 'j24_d1_t0.png')).convert('RGBA'))
    win = np.array(to_img(resize(crop(p, ICON_BOX, 58 / 38), (58, 38))))
    out = ness.copy()
    out[3:placeholder.B0, 3:61] = win
    out[placeholder.B0:placeholder.B1] = placeholder.name_band(
        [('j17_d1_t0.png', 3), ('j24_d1_t0.png', 1), ('j24_d1_t0.png', 0), ('j16_d1_t0.png', 4)])
    return Image.fromarray(out, 'RGBA')


def face(p):
    """64x32 opaque close-up of the eyes under the brim, as the Records faces are."""
    q = resize(crop(p, FACE_BOX, 2.0), (64, 32))
    bg = np.array([22, 36, 104]) / 255
    rgb = q[..., :3] * q[..., 3:4] + bg * (1 - q[..., 3:4])
    return Image.fromarray((rgb * 255).round().astype(np.uint8), 'RGB').quantize(256, dither=Image.Dither.NONE).convert('RGBA')


def main():
    args = sys.argv[1:]
    frame_dir = os.path.join(os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work')), 'css3')   # rig/prepare.py
    if '--glyphs' in args:
        i = args.index('--glyphs'); frame_dir = args[i + 1]; del args[i:i + 2]
    out, runs = args[0], args[1:]
    os.makedirs(os.path.join(out, 'matte'), exist_ok=True)
    shots = {}
    for spec in runs:
        run, cos = spec.rsplit(':', 1)
        sf = shot_frames(run)
        for i, c in enumerate(int(x) for x in cos.split(',')):
            for k in range(FRAMINGS):
                if 1000 + 100 * i + 10 * k not in sf: continue
                p, spread = matte(run, i, k, sf)
                shots[c, k] = p
                to_img(unpremul(p)).save(os.path.join(out, 'matte', f'c{c}_k{k}.png'))
                cov = p[..., 3]
                ys, xs = np.nonzero(cov > 0.5)
                H, W = cov.shape
                print(f'costume {c} framing {k}: {os.path.basename(run)} frames {sf[1000 + 100 * i + 10 * k]}, coverage {cov.mean():.3f}, '
                      f'partial {((cov > 0.02) & (cov < 0.98)).mean():.4f}, channel spread {spread:.3f}, '
                      f'box {xs.min() / W:.3f} {ys.min() / H:.3f} {xs.max() / W:.3f} {ys.max() / H:.3f}')
    costumes = sorted({c for c, _ in shots})
    written = []
    for c in costumes:
        csp(shots[c, 0]).save(os.path.join(out, f'csp_{c}.png'))
        stock(shots[c, 0]).save(os.path.join(out, f'stock_{c}.png'))
        written += [f'csp_{c}.png', f'stock_{c}.png']
    if 0 in costumes:
        icon(shots[0, 0], frame_dir).save(os.path.join(out, 'icon.png'))
        face(shots[0, 0]).save(os.path.join(out, 'face.png'))
        written += ['icon.png', 'face.png']
    import sheet
    sheet.rows(os.path.join(out, 'sheet.png'), [
        ('portraits 136x188, costumes ' + ' '.join(map(str, costumes)), 2, [os.path.join(out, f'csp_{c}.png') for c in costumes]),
        ('stock icons 24x24', 6, [os.path.join(out, f'stock_{c}.png') for c in costumes]),
    ] + ([('CSS icon 64x56 | VS Records face 64x32', 4, [os.path.join(out, 'icon.png'), os.path.join(out, 'face.png')])] if 0 in costumes else []))
    print('wrote', ', '.join(written), '->', out)


if __name__ == '__main__':
    main()
