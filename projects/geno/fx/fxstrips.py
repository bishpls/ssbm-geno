"""Strips of lab runs for the effects review: before/after rows of the same moments, each segment lined up on its own
sync slate (fxsync.py), so a dropped dump image can't shift one row against another.
    .venv/bin/python projects/geno/fx/fxstrips.py OUT.png "TITLE" ROW [ROW ...]
      ROW = LABEL=RUN@SEGMENT:FROM:COUNT:STEP[:X,Y,W,H]
FROM is logic frames after the segment's start (fx_lab's plan: RUN.plan.json beside the run folder), so frame numbers
printed in each cell are the segment's own (+FROM). Every row gets the first row's cell size (its crop, CELL_W wide).
Game renders: keep the output out of the repo.
"""
import sys

from PIL import Image, ImageDraw

import fxsync

CELL_W = 360


def parse(row):
    label, rest = row.split('=', 1)
    parts = rest.split(':')
    run, seg = parts[0].split('@')
    first, count, step = int(parts[1]), int(parts[2]), int(parts[3])
    crop = tuple(int(v) for v in parts[4].split(',')) if len(parts) > 4 else None
    return label, run, seg, [first + i * step for i in range(count)], crop


def main():
    out, title, rows = sys.argv[1], sys.argv[2], [parse(r) for r in sys.argv[3:]]
    runs, cells = {}, []
    for label, run, seg, rels, crop in rows:
        r = runs.setdefault(run, fxsync.load(run))
        ims = []
        for rel in rels:
            p = r.path(seg, rel)
            im = Image.open(p).convert('RGB') if p else Image.new('RGB', (1280, 1056))
            if crop:
                x, y, w, h = crop; im = im.crop((x, y, x + w, y + h))
            ims.append((rel, im))
        cells.append((label, ims))
    for run, r in runs.items():
        print(run, 'segment offsets against the first (images dropped before each):', r.check())
    w0, h0 = cells[0][1][0][1].size
    cw, ch = CELL_W, int(CELL_W * h0 / w0)
    ncol = max(len(c[1]) for c in cells)
    lw = 130
    sheet = Image.new('RGB', (lw + ncol * (cw + 4), 28 + len(cells) * (ch + 4)), (16, 16, 20))
    d = ImageDraw.Draw(sheet)
    d.text((6, 8), title, fill=(255, 255, 255))
    for r, (label, ims) in enumerate(cells):
        y = 28 + r * (ch + 4)
        d.text((6, y + ch // 2 - 6), label, fill=(255, 220, 90))
        for c, (rel, im) in enumerate(ims):
            x = lw + c * (cw + 4)
            sheet.paste(im.resize((cw, ch), Image.LANCZOS), (x, y))
            d.text((x + 4, y + 3), f'+{rel}', fill=(255, 255, 0))
    sheet.save(out)
    print(out, sheet.size)


if __name__ == '__main__':
    main()
