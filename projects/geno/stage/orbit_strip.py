"""The orbit lab's shots as a strip (yaw across, pitch down) with each shot's void: the share of exactly black pixels (the
clear colour: nothing drawn there).
    .venv/bin/python projects/geno/stage/orbit_strip.py RUN_DIR OUT.png "label"      -> prints the worst void
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

run, out, label = sys.argv[1:4]
shots = [(p, y) for p in (20, 30) for y in range(-60, 61, 10)]
tw = 200; th = 113
img = Image.new('RGB', (13 * (tw + 4) + 60, 2 * (th + 22) + 30), 'white'); d = ImageDraw.Draw(img)
d.text((6, 4), label, fill=(0, 0, 0))
res = []
for k, (p, y) in enumerate(shots):
    f = os.path.join(run, f'f{3 * k + 10:05d}.png')
    im = Image.open(f).convert('RGB'); a = np.asarray(im)
    void = float((a.max(2) <= 2).mean())                        # the clear colour exactly (dark shading is not void)
    res.append(dict(pitch=p, yaw=y, void=round(void, 4)))
    col, row = (y + 60) // 10, (0 if p == 20 else 1)
    x0, y0 = 50 + col * (tw + 4), 22 + row * (th + 22)
    img.paste(im.resize((tw, th)), (x0, y0))
    d.text((x0 + 2, y0 + th + 2), f'yaw {y:+d}  void {void:.1%}', fill=(200, 0, 0) if void > 0.001 else (0, 0, 0))
    if col == 0:
        d.text((4, y0 + 40), f'{p} deg', fill=(0, 0, 0))
img.save(out)
worst = max(res, key=lambda r: r['void'])
json.dump(res, open(os.path.splitext(out)[0] + '.json', 'w'))
print(json.dumps(dict(worst=worst, shots=len(res))))
