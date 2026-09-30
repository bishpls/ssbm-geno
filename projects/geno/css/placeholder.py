"""Placeholder CSS art for the blocky-rig phase: Geno's icon face (64x56, the name band in Melee's own letters) and one
character-select portrait (136x188). The face is drawn here; the name band is cut from the disc's NESS, LUIGI and MARIO
icons, so the output is derived from game data: it goes to the work folder (outside the repo), never into git.
    .venv/bin/python projects/geno/css/placeholder.py WORK       # WORK holds datkit texdump output (j16/j17/j24_d1_t0.png)
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw

W = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/games/melee/work/css3')
BLUE, BLUE_HI, BLUE_LO = (38, 64, 168), (72, 104, 210), (22, 36, 104)
SKIN, SKIN_LO, BROWN, GOLD = (240, 200, 150), (206, 160, 112), (120, 72, 40), (236, 196, 64)


B0, B1 = 41, 56        # the name band and the icon's bottom border
G0, G1 = 43, 51        # the letters' rows


def band_glyphs(path):
    """The name band's letters as (x0, x1) column spans of light pixels (inside the frame's side borders)."""
    im = np.array(Image.open(path).convert('RGBA'))
    band = im[G0:G1]
    light = (band[..., :3].min(axis=2) > 150) & (band[..., 3] > 0)
    cols = light.any(axis=0)
    cols[:2] = cols[-2:] = False
    spans, x = [], 0
    while x < len(cols):
        if cols[x]:
            x0 = x
            while x < len(cols) and cols[x]: x += 1
            spans.append((x0, x))
        x += 1
    return im, spans


def name_band(word_src):
    """Compose a band from (source icon, glyph index) pairs at NESS's letter positions."""
    ness, ness_spans = band_glyphs(os.path.join(W, 'j24_d1_t0.png'))
    out = ness.copy()
    band = out[G0:G1]
    for x0, x1 in ness_spans:                      # clear NESS's letters to the band colour
        band[:, x0:x1] = band[:, 3:4]
    for (x0, x1), (src, gi) in zip(ness_spans, word_src):
        im, spans = band_glyphs(os.path.join(W, src))
        g0, g1 = spans[gi]
        cx = (x0 + x1) // 2 - (g1 - g0) // 2
        band[:, cx:cx + (g1 - g0)] = im[G0:G1, g0:g1]
    return out[B0:B1]


def face(size, scale):
    """Geno's head and collar, drawn big and downsampled: a wide-brimmed blue hat, a wooden doll's face, a blue cape."""
    w, h = size
    S = 4
    im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = lambda *v: [int(round(x * S * scale)) for x in v]
    ox = (w - 64 * scale) / 2 * S
    def box(*v): x0, y0, x1, y1 = k(*v); return [x0 + ox, y0, x1 + ox, y1]
    d.ellipse(box(8, 40, 58, 70), fill=BLUE_LO)                      # cape and collar
    d.ellipse(box(14, 42, 52, 64), fill=BLUE)
    d.ellipse(box(20, 16, 46, 46), fill=SKIN_LO)                      # head
    d.ellipse(box(21, 16, 45, 44), fill=SKIN)
    d.ellipse(box(26, 28, 30, 33), fill=(20, 20, 30)); d.ellipse(box(35, 28, 39, 33), fill=(20, 20, 30))
    d.ellipse(box(27, 29, 28, 30), fill=(255, 255, 255)); d.ellipse(box(36, 29, 37, 30), fill=(255, 255, 255))
    d.ellipse(box(31, 32, 34, 36), fill=SKIN_LO)                      # nose
    d.ellipse(box(4, 15, 62, 25), fill=BLUE_LO)                       # brim
    d.ellipse(box(5, 14, 61, 23), fill=BLUE)
    d.chord(box(17, 0, 49, 30), 180, 360, fill=BLUE)                  # crown
    d.chord(box(21, 2, 41, 24), 190, 290, fill=BLUE_HI)
    d.rectangle(box(18, 12, 48, 15), fill=GOLD)                       # band
    return im.resize((w, h), Image.LANCZOS)


def main():
    out = os.path.join(W, 'geno')
    os.makedirs(out, exist_ok=True)
    icon = face((64, 56), 0.84)
    arr = np.array(Image.open(os.path.join(W, 'j24_d1_t0.png')).convert('RGBA'))   # NESS's frame
    inner = np.array(icon)
    arr[3:B0, 3:61] = inner[3:B0, 3:61]
    arr[B0:B1] = name_band([('j17_d1_t0.png', 3), ('j24_d1_t0.png', 1), ('j24_d1_t0.png', 0), ('j16_d1_t0.png', 4)])
    Image.fromarray(arr).save(os.path.join(out, 'icon.png'))
    face((136, 188), 2.0).save(os.path.join(out, 'csp_0.png'))
    print('wrote', out)


if __name__ == '__main__':
    main()
