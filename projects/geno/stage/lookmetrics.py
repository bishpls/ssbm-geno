"""Readability of a stage's background behind the fighters, as numbers (for style targets and in-game renders alike).
    .venv/bin/python projects/geno/stage/lookmetrics.py IMG[:x0,y0,x1,y1] ...     # the box is the play band (fractions)
For the play band (default: the middle 70% of the width, from 15% to 65% of the height, where fighters stand and fly at
match distance) it reports, on relative luminance Y (0-1):
  - mean_Y and the background's spread (std_Y);
  - busy: the mean gradient magnitude after a 2-pixel blur (fine texture and edges that compete with fighter outlines);
  - sat: mean HSV saturation;
  - contrast_vs_fighter: the mean |Y - 0.5| (Melee's fighters sit around mid luminance: a background far from it, darker
    or lighter, separates them), and the fraction of the band within 0.12 of mid (where a fighter's shading would blend);
  - readability: contrast_vs_fighter x (1 - blend_frac) / (1 + 8 busy), the score used to rank targets (higher reads
    better). Relative, not absolute: compare against the Melee references measured the same way.
"""
import json, sys
import numpy as np
from PIL import Image, ImageFilter


def metrics(path, box=(0.15, 0.15, 0.85, 0.65)):
    im = Image.open(path).convert('RGB')
    W, H = im.size
    b = im.crop((int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)))
    b = b.resize((320, int(320 * b.size[1] / b.size[0])), Image.LANCZOS)   # one scale for every source
    a = np.asarray(b).astype(float) / 255
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    Y = lin @ np.array([0.2126, 0.7152, 0.0722])
    Yg = np.asarray(Image.fromarray((Y * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))).astype(float) / 255
    gy, gx = np.gradient(Yg)
    busy = float(np.mean(np.hypot(gx, gy)) * 10)
    hsv = np.asarray(b.convert('HSV')).astype(float) / 255
    sep = float(np.mean(np.abs(Y - 0.5)))
    blend = float(np.mean(np.abs(Y - 0.5) < 0.12))
    return dict(image=path, mean_Y=round(float(Y.mean()), 3), std_Y=round(float(Y.std()), 3), busy=round(busy, 3),
                sat=round(float(hsv[..., 1].mean()), 3), contrast_vs_fighter=round(sep, 3), blend_frac=round(blend, 3),
                readability=round(sep * (1 - blend) / (1 + 8 * busy), 4))


if __name__ == '__main__':
    out = []
    for arg in sys.argv[1:]:
        p, _, bx = arg.partition(':')
        out.append(metrics(p, tuple(map(float, bx.split(','))) if bx else (0.15, 0.15, 0.85, 0.65)))
    print(json.dumps(out, indent=1))
