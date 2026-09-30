"""Geno's menu art outside the character select screen, derived from his CSS art and from the disc's own lettering.
    .venv/bin/python projects/geno/menus/art.py ART GLYPHS OUT
ART holds css-geno's inputs (icon.png 64x56, csp_0.png 136x188); GLYPHS holds `datkit mdump` output of the vanilla
GmRst.usd results panel (the winner banner j10_m1_ta0_NNN.png and the name labels j33_m0_ta0_NNN.png). Writes to OUT:
    stock.png   24x24, 16 colours with transparency: stock icon (results panels, in-match HUD, 1P character select)
    face.png    64x32 opaque: the VS Records row/column face (MnMaAll.usd)
    banner.png  256x28 intensity: the results winner banner, "GENO" spliced from the banner font's own glyphs
    label.png   120x24 intensity: the results panel name label, spliced the same way
and a raw .bgra next to each (what datkit reads). The lettering is cut from game textures, so every output is derived
from game data: it stays in the work folder, never in git.
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter

# banner and label glyph sources: (source image index, glyph slot) in the vanilla name animations.
# indices: 7 LUIGI, 8 MARIO, 11 NESS, 22 ROY. NESS is the template (a 4-letter name: its letter size and spacing).
TEMPLATE = 11
GENO = [(7, 3), (11, 1), (11, 0), (8, 4)]          # G from LUIGI, E and N from NESS, O from MARIO

OUTLINE = (24, 20, 44)


def load(path):
    return np.array(Image.open(path).convert('RGBA'))


def spans(a, th=0):
    """Glyphs as column spans of non-empty pixels."""
    cols = a[..., 3].max(axis=0) > th
    out, x = [], 0
    while x < len(cols):
        if cols[x]:
            x0 = x
            while x < len(cols) and cols[x]: x += 1
            out.append((x0, x))
        x += 1
    return out


def rows(a, x0, x1, th=0):
    r = np.nonzero(a[:, x0:x1, 3].max(axis=1) > th)[0]
    return r.min(), r.max()


def splice(glyph_dir, pattern, word, gap=None, centre=None):
    """Compose WORD from (source, slot) glyphs at the template's letter size, spacing and baseline."""
    tpl = load(os.path.join(glyph_dir, pattern % TEMPLATE))
    ts = spans(tpl)
    base = max(rows(tpl, x0, x1)[1] for x0, x1 in ts)                      # template baseline (lowest inked row)
    gaps = [ts[i + 1][0] - ts[i][1] for i in range(len(ts) - 1)]
    gap = gap if gap is not None else int(round(sum(gaps) / len(gaps)))
    centre = centre if centre is not None else (ts[0][0] + ts[-1][1]) / 2
    pieces = []
    for src, slot in word:
        a = load(os.path.join(glyph_dir, pattern % src))
        x0, x1 = spans(a)[slot]
        g = a[:, x0:x1].copy()
        # align this glyph's source baseline to the template's (sources differ by a row in the label font)
        sb = max(rows(a, s0, s1)[1] for s0, s1 in spans(a))
        dy = base - sb
        if dy: g = np.roll(g, dy, axis=0); (g[:dy] if dy > 0 else g[dy:])[...] = 0
        pieces.append(g)
    width = sum(p.shape[1] for p in pieces) + gap * (len(pieces) - 1)
    out = np.zeros_like(tpl)
    x = int(round(centre - width / 2))
    for p in pieces:
        out[:, x:x + p.shape[1]] = np.maximum(out[:, x:x + p.shape[1]], p)
        x += p.shape[1] + gap
    return out


def stock(csp):
    """24x24 from a portrait: the whole head (hat, face, collar). The box is placed so the hat's gold band lands on one
    pixel row."""
    return stock_from(csp, (10, 1.2, 130, 121.2))


def stock_from(img, box=None):
    """24x24: a head image (or its BOX) filtered down to 22 px, a hard silhouette, Melee's 1 px dark outline; a light
    unsharp mask and a little saturation give the crisp, vivid read of the game's own stock icons."""
    csp = img
    box = box or (0, 0, img.width, img.height)
    # premultiplied downsample so the transparent fringe doesn't darken the edge colours
    a = np.array(csp).astype(np.float64) / 255
    pm = np.dstack([a[..., :3] * a[..., 3:4], a[..., 3:4]])
    pim = Image.fromarray((pm * 255).round().astype(np.uint8), 'RGBA')
    sm = pim.resize((22, 22), Image.LANCZOS, box=box).filter(ImageFilter.UnsharpMask(radius=1, percent=80, threshold=0))
    small = np.array(sm).astype(np.float64) / 255
    al = small[..., 3]
    rgb = np.where(al[..., None] > 0.02, small[..., :3] / np.maximum(al[..., None], 1e-6), 0)
    grey = rgb.mean(axis=2, keepdims=True)
    rgb = grey + (rgb - grey) * 1.15
    m = np.zeros((24, 24), bool); m[1:23, 1:23] = al > 0.5
    canvas = np.zeros((24, 24, 4))
    canvas[1:23, 1:23, :3] = np.clip(rgb, 0, 1)
    canvas[m, 3] = 1
    ring = np.zeros_like(m)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ring |= np.roll(np.roll(m, dy, 0), dx, 1)
    ring &= ~m
    canvas[ring, :3] = np.array(OUTLINE) / 255; canvas[ring, 3] = 1
    canvas[~(m | ring)] = 0
    img = Image.fromarray((canvas * 255).round().astype(np.uint8), 'RGBA')
    return quantize(img, 15)


def quantize(img, n):
    """n opaque colours plus transparency (a CI4 palette holds 16 entries): k-means seeded by farthest-point picks, so
    a small but distinct colour (the hat's gold band, the eyes) keeps its own entry instead of averaging away."""
    a = np.array(img)
    solid = a[..., 3] > 127
    px = a[solid, :3].astype(np.float64)
    uniq = np.unique(px, axis=0)
    if len(uniq) <= n:
        centres = uniq
    else:
        centres = [px[np.argmin(px.sum(axis=1))]]                       # start from the darkest (the outline)
        d = np.full(len(px), np.inf)
        while len(centres) < n:
            d = np.minimum(d, ((px - centres[-1]) ** 2).sum(axis=1))
            centres.append(px[np.argmax(d)])
        centres = np.array(centres)
        for _ in range(20):
            lab = ((px[:, None] - centres[None]) ** 2).sum(axis=2).argmin(axis=1)
            for k in range(n):
                if (lab == k).any(): centres[k] = px[lab == k].mean(axis=0)
    lab = ((px[:, None] - centres[None]) ** 2).sum(axis=2).argmin(axis=1)
    out = np.zeros_like(a)
    out[solid, :3] = centres[lab].round().astype(np.uint8); out[solid, 3] = 255
    return Image.fromarray(out, 'RGBA')


def face(csp):
    """64x32 opaque close-up of the eyes under the brim, like the Records faces; gaps filled with the brim's shade."""
    box = (38, 37, 98, 67)
    bg = Image.new('RGBA', csp.size, (22, 36, 104, 255))
    bg.alpha_composite(csp)
    return bg.crop(box).resize((64, 32), Image.LANCZOS).convert('RGB').quantize(256, dither=Image.Dither.NONE).convert('RGBA')


def bgra(img, path):
    r, g, b, a = img.convert('RGBA').split()
    open(path, 'wb').write(Image.merge('RGBA', (b, g, r, a)).tobytes())


def main():
    art, glyphs, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    csp = Image.open(os.path.join(art, 'csp_0.png')).convert('RGBA')
    assert csp.size == (136, 188), csp.size
    res = {
        'stock': stock(csp),
        'face': face(csp),
        'banner': Image.fromarray(splice(glyphs, 'j10_m1_ta0_%03d.png', GENO), 'RGBA'),
        'label': Image.fromarray(splice(glyphs, 'j33_m0_ta0_%03d.png', GENO), 'RGBA'),
    }
    for k, im in res.items():
        im.save(os.path.join(out, k + '.png'))
        bgra(im, os.path.join(out, k + '.bgra'))
        print(f'{k}: {im.size[0]}x{im.size[1]}, {len(set(map(tuple, np.array(im).reshape(-1, 4))))} colours')


if __name__ == '__main__':
    main()
