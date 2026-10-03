"""Measure the prize screen's message lines in a capture: each line's ink extent against the text box, and how much the
game's box fitting squeezed it (its ink width over its width at the font's natural advance, estimated from the line with
the most room). Melee's own messages are two lines; the box is 435 wide at 640 x 480 (ifprize.c: x 105, w 435).
    prize_text.py FRAME.png [FRAME.png ...]"""
import sys
import numpy as np
from PIL import Image

for path in sys.argv[1:]:
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    H, W = a.shape[:2]
    k = W / 640.0
    # the text box: x 105-540, y 202-277 at 640x480; the dump is 1.2173 tall per wide... use measured rows: white ink
    x0, x1 = int(100 * k), int(545 * k)
    y0, y1 = int(0.32 * H), int(0.68 * H)
    white = (a[..., 0] > 200) & (a[..., 1] > 200) & (a[..., 2] > 200)
    sub = white[y0:y1, x0:x1]
    rows = sub.any(axis=1)
    lines, cur = [], None
    for y, r in enumerate(rows):
        if r and cur is None: cur = y
        if not r and cur is not None:
            if y - cur > 4: lines.append((cur, y))
            cur = None
    out = []
    for ly0, ly1 in lines:
        cols = np.nonzero(sub[ly0:ly1].any(axis=0))[0]
        out.append(dict(y=(ly0 + y0, ly1 + y0), x=(int(cols[0] + x0), int(cols[-1] + x0)), w=int(cols[-1] - cols[0] + 1),
                        h=ly1 - ly0))
    box = 435 * k
    print(path.split('/')[-2:], f'box {box:.0f}px')
    for o in out:
        print(f'   line y {o["y"]} x {o["x"]} w {o["w"]} ({o["w"] / box:.2f} of the box) h {o["h"]}')
