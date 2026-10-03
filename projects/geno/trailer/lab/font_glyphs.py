"""♡ and ♪ for Melee's in-match font (the SIS atlas in main.dol: 32x32 I4 glyphs, 16 grey levels), so the name tag
"♡♪!?" (Geno's star-spirit name) draws in a match and can be typed on the name-entry screen.
The shapes follow SMRPG's own dialogue font, where the name prints as "♡♪!?": an outlined heart and a filled eighth
note with a flag (the US ROM's 16x12 2bpp dialogue font at 0x37C000, glyphs 4 and 5; read locally for reference only,
never committed). They are drawn upright at Melee's weight: its caps run rows 2-28 with 5-6 pixel strokes.
    .venv/bin/python projects/geno/trailer/lab/font_glyphs.py [--decomp DIR] [--board DIR] [--atlas SISLIB_FONT.BIN]
  --decomp: writes DIR/src/sysdolphin/baselib/sislib_font_geno.inc (the two glyphs' I4 bytes, appended to the atlas as
            glyphs 287 and 288 in non-matching builds) and prints their side bearings for the widths table
  --board:  review images: the glyphs at 8x, beside the game's own ! ? G E N O (--atlas) and SMRPG's (--rom)
The glyphs are drawn here (our art); nothing in the output is ROM-derived except the --rom reference image.
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

SS = 16                      # supersampling
TOP, BOT = 2, 28             # the cap height rows (the font's digits and capitals)
STROKE = 5.5                 # the font's median stroke (5-6)
HEART_STROKE = 3.8           # the outline's: at 5.5 the heart's lobes fill in (SNES: 1 of 7 pixels; the font's diagonals ~4)


def quant(a):
    return (np.round(np.clip(a, 0, 255) / 17.0) * 17).astype(np.uint8)


def heart_mask(S, top, bot, k):
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    h = (bot - top + 1) * k; w = h * 1.10; cx = S / 2; y0 = top * k
    r = w / 4.0
    d.ellipse((cx - 2 * r, y0, cx, y0 + 2 * r), fill=255)
    d.ellipse((cx, y0, cx + 2 * r, y0 + 2 * r), fill=255)
    d.polygon([(cx - 2 * r + k * .25, y0 + r * 1.2), (cx + 2 * r - k * .25, y0 + r * 1.2), (cx, y0 + h)], fill=255)
    return np.asarray(im) > 127


def heart(outline=True, cell=32):
    """SMRPG's ♡: an outlined heart (the SNES glyph is hollow), the stroke at Melee's weight. cell: the output size (32
    native; 128 for the engine's hi-res atlas, the same shape)"""
    k = SS * cell // 32; S = 32 * k
    m = heart_mask(S, TOP + 1, BOT, k)
    if outline:
        dist = ndimage.distance_transform_edt(m)
        m = m & (dist <= HEART_STROKE * k)
    im = Image.fromarray((m * 255).astype(np.uint8))
    a = np.asarray(im.resize((cell, cell), Image.LANCZOS)).astype(float)
    return quant(a) if cell == 32 else a.astype(np.uint8)


def note(cell=32):
    """SMRPG's ♪: a filled head at the bottom left, a stem up its right side, a flag curling down to the right"""
    k = SS * cell // 32; S = 32 * k
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    h = (BOT - TOP + 1) * k; y0 = TOP * k; st = STROKE * k
    hw, hh = h * 0.44, h * 0.30
    hx, hy = S / 2 - h * 0.13, y0 + h - hh / 2
    head = Image.new('L', (S, S), 0)
    ImageDraw.Draw(head).ellipse((hx - hw / 2, hy - hh / 2, hx + hw / 2, hy + hh / 2), fill=255)
    head = head.rotate(20, center=(hx, hy), resample=Image.BICUBIC)
    im = Image.fromarray(np.maximum(np.asarray(im), np.asarray(head)))
    d = ImageDraw.Draw(im)
    sx = hx + hw / 2 - st
    d.rectangle((sx, y0, sx + st, hy), fill=255)
    pts = [(sx + st * .5 + h * .30 * np.sin(u * 2.3), y0 + st * .3 + h * .52 * u) for u in np.linspace(0, 1, 24)]
    d.line(pts, fill=255, width=int(st * .9), joint='curve')
    a = np.asarray(im.resize((cell, cell), Image.LANCZOS)).astype(float)
    return quant(a) if cell == 32 else a.astype(np.uint8)


def bearings(g):
    """the widths table's (left, right): the ink's first column and 31 minus its last (kerning advance = ink + 2)"""
    xs = np.nonzero(g.max(axis=0) > 0)[0]
    return int(xs.min()), int(31 - xs.max())


def i4(g):
    """32x32 grey (multiples of 17) -> GX I4: 4x4 tiles of 8x8, each row 4 bytes, the left pixel in the high nibble"""
    v = (g // 17).astype(np.uint8)
    out = bytearray()
    for ty in range(4):
        for tx in range(4):
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append((v[ty * 8 + y, tx * 8 + x] << 4) | v[ty * 8 + y, tx * 8 + x + 1])
    return bytes(out)


def from_i4(b):
    im = np.zeros((32, 32), np.uint8); k = 0
    for ty in range(4):
        for tx in range(4):
            for y in range(8):
                for x in range(0, 8, 2):
                    im[ty * 8 + y, tx * 8 + x] = (b[k] >> 4) * 17; im[ty * 8 + y, tx * 8 + x + 1] = (b[k] & 15) * 17; k += 1
    return im


GLYPHS = [('♡', heart), ('♪', note)]    # atlas 287, 288


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--decomp'); ap.add_argument('--board'); ap.add_argument('--atlas'); ap.add_argument('--rom')
    a = ap.parse_args()
    gl = [(ch, f()) for ch, f in GLYPHS]
    for ch, g in gl:
        assert (from_i4(i4(g)) == g).all()
        print(ch, 'bearings', bearings(g), 'ink rows', np.nonzero(g.max(axis=1))[0][[0, -1]])
    if a.decomp:
        p = os.path.join(a.decomp, 'src', 'sysdolphin', 'baselib', 'sislib_font_geno.inc')
        lines = ['/* The heart and the note (atlas glyphs 287 and 288): 32x32 I4, drawn by projects/geno/trailer/lab/font_glyphs.py',
                 ' * (the animation-pipeline repo) after SMRPG\'s name for Geno. Appended to HSD_SisLib_FontAtlas in non-matching',
                 ' * builds only (sislib_font.c). Do not edit by hand. */']
        for ch, g in gl:
            b = i4(g)
            for r in range(0, 512, 16):
                lines.append(', '.join(f'0x{x:02X}' for x in b[r:r + 16]) + ',')
        open(p, 'w').write('\n'.join(lines) + '\n')
        print('wrote', p)
    if a.board:
        os.makedirs(a.board, exist_ok=True)
        for ch, g in gl:
            Image.fromarray(g).save(os.path.join(a.board, f'glyph_{"heart" if ch == "♡" else "note"}_v2.png'))
        cells = [g for ch, g in gl]
        if a.atlas:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import font_mock
            A = font_mock.atlas(a.atlas)
            cells += [A[236], A[235], A[16], A[14], A[23], A[24]]
        row = np.concatenate(cells, axis=1)
        Image.fromarray(row).resize((row.shape[1] * 8, 256), Image.NEAREST).save(os.path.join(a.board, 'glyphs_v2_row.png'))
        print('wrote', a.board)


if __name__ == '__main__':
    main()
