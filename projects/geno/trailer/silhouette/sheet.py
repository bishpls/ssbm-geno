"""Side-by-side sheets of the vanilla silhouettes and Geno's candidates, for the review page.
    sheet.py OUT.png SCALE NAME=PATH ... [--game] [--cols N]   (vanilla=DIR: the eleven from datkit mdump's folder)
SCALE is an integer (nearest-neighbour: every I4 pixel visible). --game draws them as the challenger screen does: black
through the image's coverage onto the panel's navy (sampled from a capture), bilinear at the screen's ~4.27x (res 2)."""
import sys
import numpy as np
from PIL import Image, ImageDraw

args = sys.argv[1:]
game = '--game' in args
if game: args.remove('--game')
cols = 0
if '--cols' in args:
    j = args.index('--cols'); cols = int(args[j + 1]); del args[j:j + 2]
out, scale, items = args[0], int(args[1]), []
VANILLA = ['gnw', 'luigi', 'marth', 'mewtwo', 'puff', 'falco', 'ylink', 'drmario', 'roy', 'pichu', 'ganon']
for a in args[2:]:
    name, path = a.split('=', 1)
    if name == 'vanilla':                 # the eleven, from datkit mdump's folder
        items += [(n, f'{path}/j12_m0_ta0_{i:03d}.png') for i, n in enumerate(VANILLA)]
    else:
        items.append((name, path))
NAVY = (16, 16, 92)
tiles = []
for name, path in items:
    g = np.asarray(Image.open(path).convert('L'))
    if game:
        a = np.asarray(Image.fromarray(g).resize((96 * scale, 160 * scale), Image.BILINEAR), np.float64) / 255
        rgb = np.dstack([np.full(a.shape, c, np.float64) * (1 - a) for c in NAVY])
        im = Image.fromarray(rgb.round().astype(np.uint8), 'RGB')
    else:
        im = Image.fromarray(g).resize((96 * scale, 160 * scale), Image.NEAREST).convert('RGB')
    tiles.append((name, im))
pad, lab = 6 * max(1, scale // 2), 14
Wt, Ht = 96 * scale + pad, 160 * scale + pad + lab
cols = cols or len(tiles)
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new('RGB', (Wt * min(cols, len(tiles)) + pad, Ht * rows + pad), (60, 60, 60))
d = ImageDraw.Draw(sheet)
for k, (name, im) in enumerate(tiles):
    x, y = pad + (k % cols) * Wt, pad + (k // cols) * Ht
    sheet.paste(im, (x, y))
    d.text((x, y + 160 * scale + 2), name, fill=(255, 255, 255))
sheet.save(out)
print(out, sheet.size)
