"""A sky pass, boarded: art pass 2 (before) against this pass at t7's camera (by its horizon) and both match framings,
the readability of every frame across the full cycle (both framings, against Final Destination's 0.275), the flash
measure against Battlefield's and Final Destination's backgrounds, and the budget.
    .venv/bin/python projects/geno/stage/sky_board.py PASS_DIR      -> PASS_DIR/board.jpg, PASS_DIR/metrics.json
"""
import json, os, sys
from PIL import Image, ImageDraw

P = sys.argv[1]; S = os.path.dirname(P); B = os.path.join(S, 'before')
m = dict(budget=open(os.path.join(P, 'budget.txt')).read().strip())
for X in (25, 55):
    c = json.load(open(os.path.join(P, f'cycle_x{X}.json')))
    m[f'cycle_x{X}'] = {k: c[k] for k in ('frames', 'min', 'mean', 'p05', 'min_frame')}
m['flash'] = {'forest_maze': json.load(open(os.path.join(P, 'flash.json')))}
for s in ('battlefield', 'final_destination'):
    f = os.path.join(S, f'flash_{s}.json')
    if os.path.exists(f):
        m['flash'][s] = json.load(open(f))
json.dump(m, open(os.path.join(P, 'metrics.json'), 'w'), indent=1)
Wb = 1320; board = Image.new('RGB', (Wb, 2400), 'white'); d = ImageDraw.Draw(board); y = 6
d.text((8, y), f"{os.path.basename(P)}   {m['budget']}", fill=(0, 0, 0)); y += 18


def pair(a, b, la, lb, h):
    global y
    ia, ib = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
    ia = ia.resize((int(ia.size[0] * h / ia.size[1]), h)); ib = ib.resize((int(ib.size[0] * h / ib.size[1]), h))
    board.paste(ia, (6, y + 14)); board.paste(ib, (12 + ia.size[0], y + 14))
    d.text((8, y), la, fill=(0, 0, 0)); d.text((14 + ia.size[0], y), lb, fill=(0, 0, 0)); y += h + 20


pair(os.path.join(B, 'hero.png'), os.path.join(P, 'hero.png'), "before (art pass 2), t7's camera by its horizon", 'this pass', 360)
for X in (25, 55):
    c = m[f'cycle_x{X}']
    pair(os.path.join(B, f'match_x{X}.png'), os.path.join(P, f'match_x{X}.png'), f'before x{X}',
         f"this pass x{X}; over the full cycle: min {c['min']}, mean {c['mean']} ({c['frames']} frames; FD 0.275)", 330)
for X in (25, 55):                                             # the per-frame series
    c = json.load(open(os.path.join(P, f'cycle_x{X}.json')))
    s = c['series']; w, h = 640, 120
    im = Image.new('RGB', (w, h + 16), (250, 250, 250)); g = ImageDraw.Draw(im)
    lo, hi = 0.2, 0.4
    Y = lambda v: h - (v - lo) / (hi - lo) * h
    g.line([(0, Y(0.275)), (w, Y(0.275))], fill=(220, 60, 60))
    g.line([(i * w / len(s), Y(v)) for i, v in enumerate(s)], fill=(40, 70, 200), width=2)
    g.text((4, h + 2), f"x{X} readability per frame over the full cycle (red: FD 0.275; axis {lo}-{hi})", fill=(0, 0, 0))
    board.paste(im, (6 + (X == 55) * 650, y))
y += 150
for k, (st, f) in enumerate(m['flash'].items()):
    d.text((8, y + 16 * k), f"flash {st}: largest per-frame change of a region's luminance {f['max_change']} (at {f['at_frame']}, cell {f['cell_xy']}), p99.9 {f['p999']}", fill=(0, 0, 0))
y += 60
x = 6
for fn in ('flash_view.png',):
    im = Image.open(os.path.join(P, fn)).convert('RGB').resize((420, 346)); board.paste(im, (x, y)); x += 430
for n in ('base.png', 'ledge.png', 'hero23.png'):
    im = Image.open(os.path.join(P, n)).convert('RGB'); im = im.resize((280, int(280 * im.size[1] / im.size[0]))); board.paste(im, (x, y)); x += 290
y += 360
board.crop((0, 0, Wb, y)).save(os.path.join(P, 'board.jpg'), quality=86)
print(json.dumps({k: v for k, v in m.items()}, indent=None)[:1500])
