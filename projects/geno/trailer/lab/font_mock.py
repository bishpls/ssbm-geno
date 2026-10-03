"""The "♥♪!?" name tag: the two glyphs the game's font lacks, drawn in its style, and a mock of the tag in a capture.
The in-match name tag (ifnametag.c) draws through the SIS text system with the font built into main.dol
(HSD_SisLib_FontAtlas: 287 glyphs, 32x32 I4; lbl_8040C8C0 maps Shift-JIS to glyph; HSD_SisLib_8040CB00 the side bearings).
♪ (81 F4) and ♥ (not in CP932; Shift_JIS-2004 83 BC) have no glyph, so the game drops them: "♥♪!?" shows as "!?".
    .venv/bin/python projects/geno/trailer/lab/font_mock.py ATLAS_BIN RUN S OUT_DIR
ATLAS_BIN: the decomp's build/GALE01/bin/sysdolphin/baselib/sislib_font.bin (extracted from your own main.dol).
Writes glyph_heart.png / glyph_note.png (32x32, 16 grey levels: what a font patch would add), glyphs_row.png (them beside
the game's own ! ? G E N O at 4x), and tag_mock.png (frame S of RUN with its "!?" tag redrawn as "♥♪!?"). A mock, not a
capture: the real thing needs the font patch (FEASIBILITY.md, shot 4).
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw

SS = 8                                         # supersampling for the drawn glyphs


def atlas(path):
    b = open(path, 'rb').read()
    out = []
    for i in range(len(b) // 512):
        d = b[i * 512:(i + 1) * 512]
        im = np.zeros((32, 32), np.uint8); k = 0
        for ty in range(4):
            for tx in range(4):
                for y in range(8):
                    for x in range(0, 8, 2):
                        v = d[k]; k += 1
                        im[ty * 8 + y, tx * 8 + x] = (v >> 4) * 17
                        im[ty * 8 + y, tx * 8 + x + 1] = (v & 15) * 17
        out.append(im)
    return out


def bbox(g):
    ys, xs = np.nonzero(g > 60)
    return xs.min(), ys.min(), xs.max(), ys.max()


def quant(a):
    """to the font's 16 grey levels"""
    return (np.round(a / 17.0) * 17).clip(0, 255).astype(np.uint8)


def draw_heart(top, bottom, cell=32):
    """top, bottom: the cap height in the 32-pixel cell; cell: the output size (32 native, 128 for the hi-res atlas)"""
    k = SS * cell / 32.0
    S = int(32 * k); im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    h = (bottom - top + 1) * k; w = h * 1.08; cx = S / 2; y0 = top * k
    r = w / 4.0
    d.ellipse((cx - 2 * r, y0, cx, y0 + 2 * r), fill=255)
    d.ellipse((cx, y0, cx + 2 * r, y0 + 2 * r), fill=255)
    d.polygon([(cx - 2 * r + k * 0.35, y0 + r * 1.25), (cx + 2 * r - k * 0.35, y0 + r * 1.25), (cx, y0 + h)], fill=255)
    a = np.asarray(im.resize((cell, cell), Image.LANCZOS)).astype(float)
    return quant(a) if cell == 32 else a.astype(np.uint8)


def draw_note(top, bottom, stroke, cell=32):
    k = SS * cell / 32.0
    S = int(32 * k); im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    h = (bottom - top + 1) * k; y0 = top * k; st = stroke * k
    hw, hh = h * 0.40, h * 0.28                 # the head: a tilted ellipse at the bottom left
    hx, hy = S / 2 - h * 0.12, y0 + h - hh / 2
    head = Image.new('L', (S, S), 0); dh = ImageDraw.Draw(head)
    dh.ellipse((hx - hw / 2, hy - hh / 2, hx + hw / 2, hy + hh / 2), fill=255)
    head = head.rotate(22, center=(hx, hy), resample=Image.BICUBIC)
    im = Image.fromarray(np.maximum(np.asarray(im), np.asarray(head)))
    d = ImageDraw.Draw(im)
    sx = hx + hw / 2 - st * 0.9                 # the stem up the head's right side
    d.rectangle((sx, y0, sx + st, hy), fill=255)
    # the flag: a thick curve from the stem's top down to the right
    pts = []
    for k in range(21):
        u = k / 20.0
        pts.append((sx + st * 0.5 + h * 0.34 * np.sin(u * 2.2), y0 + h * 0.55 * u))
    d.line(pts, fill=255, width=int(st * 0.95), joint='curve')
    a = np.asarray(im.resize((cell, cell), Image.LANCZOS)).astype(float)
    return quant(a) if cell == 32 else a.astype(np.uint8)


def main(atlas_bin, run, s, out):
    os.makedirs(out, exist_ok=True)
    G = atlas(atlas_bin)
    zero = G[0]                                  # the atlas order: 0-9, A-Z, a-z, kana, punctuation, symbols, kanji
    t, b = bbox(zero)[1], bbox(zero)[3]
    stroke = 4
    heart = draw_heart(t + 1, b)
    note = draw_note(t, b, stroke)
    Image.fromarray(heart).save(os.path.join(out, 'glyph_heart.png'))
    Image.fromarray(note).save(os.path.join(out, 'glyph_note.png'))
    q_i, bang_i = 235, 236                       # the atlas's ？ and ！ (atlas.png: after 、。，．・：；)
    letters = {'♥': heart, '♪': note, '!': G[bang_i], '?': G[q_i], 'G': G[10 + 6], 'E': G[10 + 4], 'N': G[10 + 13],
               'O': G[10 + 14]}
    row = np.concatenate([letters[c] for c in '♥♪!?GENO'], axis=1)
    Image.fromarray(row).resize((row.shape[1] * 4, 128), Image.NEAREST).save(os.path.join(out, 'glyphs_row.png'))
    # the mock: frame s of the run, its "!?" tag erased and redrawn "♥♪!?" at the same scale (x 0.727 of y, the tag's
    # 0.4 x 0.55 text scale)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tlab
    r = tlab.load(run)
    im = r.img(s); a = np.asarray(im).astype(int)
    m = (a[:, :, 0] > 230) & (a[:, :, 1] > 230) & (a[:, :, 2] > 230)
    ys, xs = np.nonzero(m[:a.shape[0] // 2])
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    plate = a[y0 - 4, x0 - 6].copy()
    out_im = a.copy()
    out_im[y0 - 2:y1 + 3, x0 - 3:x1 + 4] = plate
    gh = y1 - y0 + 1                              # the glyphs' drawn height (the atlas cap height)
    sc = gh / (b - t + 1); sx = sc * 0.4 / 0.55
    cells = []
    for c in '♥♪!?':
        g = letters[c]; bb = bbox(g)
        cells.append(g[:, max(0, bb[0] - 2):bb[2] + 3])
    pen = []
    for g in cells:
        w = max(1, int(round(g.shape[1] * sx))); h = int(round(32 * sc))
        pen.append(np.asarray(Image.fromarray(g).resize((w, h), Image.LANCZOS)).astype(float) / 255)
    gap = int(round(4 * sx))                      # the game's side bearings ("! ?" in the capture)
    total = sum(p.shape[1] for p in pen) + gap * (len(pen) - 1)
    cx = (x0 + x1) / 2; X = int(round(cx - total / 2)); Y = int(round(y0 - t * sc))
    for p in pen:
        H, W = p.shape
        reg = out_im[Y:Y + H, X:X + W].astype(float)
        out_im[Y:Y + H, X:X + W] = (reg * (1 - p[:, :, None]) + 255 * p[:, :, None]).astype(int)
        X += W + gap
    mock = Image.fromarray(out_im.clip(0, 255).astype(np.uint8))
    mock.save(os.path.join(out, 'tag_mock.png'))
    pad = 70
    box = (x0 - pad * 2, y0 - pad, x1 + pad * 2, y1 + pad * 4)
    Image.fromarray(a.astype(np.uint8)).crop(box).resize(((box[2] - box[0]) * 3, (box[3] - box[1]) * 3), Image.NEAREST).save(
        os.path.join(out, 'tag_game_crop.png'))
    mock.crop(box).resize(((box[2] - box[0]) * 3, (box[3] - box[1]) * 3), Image.NEAREST).save(os.path.join(out, 'tag_mock_crop.png'))
    print('glyph cap height', b - t + 1, 'tag text', (x0, y0, x1, y1), '! =', bang_i, '? =', q_i)


if __name__ == '__main__':
    main(*sys.argv[1:3], int(sys.argv[3]), sys.argv[4])
