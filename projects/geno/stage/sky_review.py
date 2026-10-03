"""The sky's review assets, from a sky pass and its checks (sky_pass.sh and the release checks write PASS_DIR):
before/after composites, the readability plots (the full cycle, and the shooting star at real speed), the shooting
star's full-resolution crop and strip, and the tables (flash, performance, budget, the vanilla census).
    .venv/bin/python projects/geno/stage/sky_review.py PASS_DIR OUT_DIR
"""
import csv, glob, json, os, sys
import numpy as np
from PIL import Image, ImageDraw

P, O = sys.argv[1:3]
S = os.path.dirname(P); B = os.path.join(S, 'before')
W = os.path.dirname(S)
os.makedirs(O, exist_ok=True)


def pair(a, b, la, lb, out, h=528):
    ia, ib = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
    ia = ia.resize((round(ia.size[0] * h / ia.size[1]), h), Image.LANCZOS); ib = ib.resize((round(ib.size[0] * h / ib.size[1]), h), Image.LANCZOS)
    o = Image.new('RGB', (ia.size[0] + ib.size[0] + 12, h + 26), 'white'); d = ImageDraw.Draw(o)
    o.paste(ia, (0, 26)); o.paste(ib, (ia.size[0] + 12, 26)); d.text((4, 6), la, fill=(0, 0, 0)); d.text((ia.size[0] + 16, 6), lb, fill=(0, 0, 0))
    o.save(os.path.join(O, out), quality=90)


m = json.load(open(os.path.join(P, 'metrics.json')))
pair(os.path.join(B, 'hero.png'), os.path.join(P, 'hero.png'), "art pass 2's sky, t7's camera by its horizon (10 degrees down)", 'the new sky, the same camera', 'hero_before_after.jpg', 480)
pair(os.path.join(W, 'targets', 't7.png'), os.path.join(P, 'hero.png'), 't7 (the target)', 'the new sky in game', 't7_vs_hero.jpg', 480)
for X in (25, 55):
    c = m[f'cycle_x{X}']
    pair(os.path.join(B, f'match_x{X}.png'), os.path.join(P, f'match_x{X}.png'), f"art pass 2's sky, x{X}",
         f"the new sky, x{X} (full cycle: min {c['min']}, mean {c['mean']})", f'match_x{X}_before_after.jpg')


def plot(series, title, out, lo=0.24, hi=0.36, marks=()):
    w, h = 900, 220
    im = Image.new('RGB', (w, h + 40), (252, 252, 252)); g = ImageDraw.Draw(im)
    Y = lambda v: 10 + (hi - v) / (hi - lo) * h
    for v in np.arange(lo, hi + 1e-9, 0.02):
        g.line([(40, Y(v)), (w, Y(v))], fill=(225, 225, 225)); g.text((2, Y(v) - 6), f'{v:.2f}', fill=(90, 90, 90))
    g.line([(40, Y(0.275)), (w, Y(0.275))], fill=(210, 50, 50), width=2)
    g.text((w - 250, Y(0.275) + 3), "Final Destination's 0.275", fill=(210, 50, 50))
    for k, (s, col, lab) in enumerate(series):
        pts = [(40 + i * (w - 40) / max(1, len(s) - 1), Y(v)) for i, v in enumerate(s)]
        g.line(pts, fill=col, width=2); g.text((50 + k * 300, h + 20), f'{lab}: min {min(s):.4f}, mean {np.mean(s):.4f}', fill=col)
    for f0, f1, lab in marks:
        g.rectangle([40 + f0 * (w - 40), 10, 40 + f1 * (w - 40), h + 10], outline=(240, 170, 40), width=2); g.text((42 + f0 * (w - 40), 12), lab, fill=(200, 120, 20))
    g.text((4, h + 4), title, fill=(0, 0, 0))
    im.save(os.path.join(O, out))


cyc = {X: json.load(open(os.path.join(P, f'cycle_x{X}.json')))['series'] for X in (25, 55)}
plot([(cyc[25], (40, 70, 200), 'x25'), (cyc[55], (30, 150, 90), 'x55')],
     'Readability of every frame across the full cycle (every clock 24x: 631 frames = the 240 s cloud cycle, the star loop 4x)', 'readability_cycle.png')
st = {c: json.load(open(os.path.join(P, f'star_readability_{c}.json')))['series'] for c in ('match25', 'match')}
# the star is on screen in frames 189-224 of those captures (150-300 measured)
plot([(st['match25'], (40, 70, 200), 'x25'), (st['match'], (30, 150, 90), 'x55')],
     'Readability at real speed across a shooting star (frames 150-300 of a still-camera capture)', 'readability_star.png',
     marks=[((189 - 150) / 150, (224 - 150) / 150, 'the shooting star on screen')])
# the shooting star at full resolution
fs = sorted(glob.glob(os.path.join(P, 'star_match', 'f*.png'))); prev = None; hits = []
for f in fs:
    a = np.asarray(Image.open(f).convert('L')).astype(float)[:420]
    if prev is not None and (a - prev).max() > 20:
        y, x = np.unravel_index(int((a - prev).argmax()), a.shape); hits.append((int(os.path.basename(f)[1:6]), int(x), int(y)))
    prev = a
f0, x0, y0 = hits[0]
mid = Image.open(os.path.join(P, 'star_match', f'f{f0 + 14:05d}.png')).convert('RGB')
mid.crop((x0 - 60, y0 - 60, x0 + 260, y0 + 140)).save(os.path.join(O, 'star_crop_fullres.png'))
strip = Image.new('RGB', (6 * 214, 182), 'white'); d = ImageDraw.Draw(strip)
for i, f in enumerate(range(f0, f0 + 36, 6)):
    c = Image.open(os.path.join(P, 'star_match', f'f{f:05d}.png')).convert('RGB').crop((x0 - 40, y0 - 40, x0 + 170, y0 + 120))
    strip.paste(c, (i * 214, 0)); d.text((i * 214 + 4, 166), f'+{f - f0} frames ({(f - f0) / 60:.2f} s)', fill=(0, 0, 0))
strip.save(os.path.join(O, 'star_strip.png'))
full = mid.copy(); ImageDraw.Draw(full).rectangle((x0 - 60, y0 - 60, x0 + 260, y0 + 140), outline=(255, 230, 0), width=4)
full.resize((640, 528), Image.LANCZOS).save(os.path.join(O, 'star_in_frame.png'))
# the canopy silhouette, old (a skyline of small columns) against new (round crowns), the same still x55 camera, full res
old = os.path.join(S, 'final3', 'star_match', 'f00150.png')      # the skyline cut (before the canopy redraw)
if os.path.exists(old):
    box = (330, 170, 950, 470)
    a_, b_ = Image.open(old).convert('RGB').crop(box), Image.open(os.path.join(P, 'star_match', 'f00150.png')).convert('RGB').crop(box)
    o = Image.new('RGB', (a_.size[0] * 2 + 12, a_.size[1] + 24), 'white'); d = ImageDraw.Draw(o)
    o.paste(a_, (0, 24)); o.paste(b_, (a_.size[0] + 12, 24))
    d.text((4, 6), 'before: the canopy as small columns (read as a skyline)', fill=(0, 0, 0))
    d.text((a_.size[0] + 16, 6), 'after: round, bushy crowns in two layers (full resolution, x55)', fill=(0, 0, 0))
    o.save(os.path.join(O, 'canopy_old_new.png'))
# the orbit: art pass 2 against the wrapped sky
ob, oa = os.path.join(S, 'orbit', 'orbit_before.png'), os.path.join(P, 'orbit.png')
if os.path.exists(ob) and os.path.exists(oa):
    ia, ib = Image.open(ob).convert('RGB'), Image.open(oa).convert('RGB')
    o = Image.new('RGB', (max(ia.size[0], ib.size[0]), ia.size[1] + ib.size[1] + 10), 'white')
    o.paste(ia, (0, 0)); o.paste(ib, (0, ia.size[1] + 10)); o.save(os.path.join(O, 'orbit_before_after.png'))
# tables
fl = m['flash']
with open(os.path.join(O, 'flash.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['background (real speed)', 'frames', "largest per-frame change of a region's mean luminance", 'at frame', '99.9th percentile'])
    for k, lab in (('forest_maze', 'Forest Maze, the new sky (clouds, twinkles, the shooting star at ~22 s)'), ('battlefield', 'Battlefield'), ('final_destination', 'Final Destination')):
        v = fl[k]; w.writerow([lab, v['frames'], v['max_change'], v['at_frame'], v['p999']])
    w.writerow(['Regions: a 16 x 12 grid of the frame; flash_lab frames the sky and treeline above the fighters (their own motion out of frame).', '', '', '', ''])
print('ok', f0, x0, y0)
