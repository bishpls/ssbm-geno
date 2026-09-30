"""The stage select's name plates against the Forest Maze's icon: for each hovered target of sss_forest's names run, the
name's ink (pixels at least 80 brighter than the no-hover baseline and near white) in the lower left, its extent, and how
many of its pixels fall on the Forest Maze's icon rectangle; plus crops for review.
    .venv/bin/python projects/geno/stage/director/names_report.py RUN PLAN.json OUT_DIR [ICON_X ICON_Y]
ICON is the icon's centre in stage-select units (default -4.0, -9.1); pixels from the bottom row's measured spacing."""
import json, os, sys
import numpy as np
from PIL import Image

run, plan, out = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
ix, iy = (float(sys.argv[4]), float(sys.argv[5])) if len(sys.argv) > 5 else (-4.0, -9.1)
os.makedirs(out, exist_ok=True)
F = lambda n: np.asarray(Image.open(os.path.join(run, f'f{n:05d}.png')).convert('RGB')).astype(int)
base = F(plan['baseline'])
# the bottom row at res 1: Battlefield's icon centre (1.3, -9.1) at pixel (334, 365), 11.3 px a unit
cx, cy = 334 + (ix - 1.3) * 11.3, 365 - (iy + 9.1) * 11.3
rect = (int(cx - 28), int(cy - 26), int(cx + 28), int(cy + 26))
rows = []
for t in plan['targets']:
    im = F(t['shot'])
    d = (im - base).mean(2)
    ink = (d > 80) & (im.min(2) > 170)
    ink[:250, :] = False; ink[:, 340:] = False                   # the name plate's quarter of the screen
    ys, xs = np.nonzero(ink)
    x0, x1, y0, y1 = rect
    over = int(ink[y0:y1, x0:x1].sum())
    rows.append(dict(target=t['name'], frame=t['shot'], ink_px=int(ink.sum()), ink_right=int(xs.max()) if len(xs) else None,
                     ink_bottom=int(ys.max()) if len(ys) else None, on_icon_px=over))
    Image.fromarray(im[260:470, 0:340].astype(np.uint8)).save(os.path.join(out, f"hover_{t['name']}.png"))
json.dump(dict(icon_rect=rect, rows=rows), open(os.path.join(out, 'names.json'), 'w'), indent=1)
for r in rows: print(r)
print('icon rect', rect)
