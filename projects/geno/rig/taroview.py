"""Look at throw-victim animations (the shared 52-node layout) as stick figures on Mario's skeleton: a cast member's
(by name, e.g. TFoxThrowB) or one of Geno's throws' (poses_throws.VICTIM_CLIPS), every few frames, side and front.
    .venv/bin/python projects/geno/rig/taroview.py OUT.png NAME[,NAME...] [--step 2]
"""
import argparse, math, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import taro

LIMB = (90, 200, 255)


def draw_fig(d, pts, par, ox, oy, S, view, col=LIMB, xrot=None):
    c, s = math.cos(view), math.sin(view)
    P = lambda p: (ox + (p[0] * c + p[2] * s) * S, oy - p[1] * S)
    for j, p in pts.items():
        q = par.get(j, -1)
        if q is None or q < 0 or q not in pts: continue
        left = p[0] > pts[q][0] + 0.3 and abs(p[0]) > 0.8
        d.line([P(pts[q]), P(p)], fill=(255, 150, 90) if (p[0] + pts[q][0]) / 2 > 0.6 else col, width=2)
    if xrot is not None:
        x, y = P(pts[xrot]); d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(255, 230, 90))


def sheet(out, names, step=2, cell=170, S=7.0):
    rows = []
    for nm in names:
        fr = taro.load(nm)
        rows.append((nm, [(f, fr[f]) for f in range(0, len(fr), step)]))
    cols = max(len(r[1]) for r in rows)
    img = Image.new('RGB', (cell * cols, 2 * cell * len(rows)), (40, 42, 52))
    d = ImageDraw.Draw(img)
    for ri, (nm, frames) in enumerate(rows):
        for ci, (f, pose) in enumerate(frames):
            pts, par, xr = taro.skeleton_world(pose, 1.0)
            for vi, view in enumerate((math.pi / 2, 0.0)):         # side (facing right), front
                ox, oy = ci * cell + cell // 2, (2 * ri + vi) * cell + int(cell * 0.62)
                d.line([(ci * cell + 6, oy + int(0.0 * S)), ((ci + 1) * cell - 6, oy)], fill=(80, 80, 100))
                off = pts[xr]
                sh = {j: (p[0] - off[0], p[1] - off[1] + 5.67, p[2] - off[2]) for j, p in pts.items()}
                draw_fig(d, sh, par, ox, oy, S, view, xrot=xr)
                d.text((ci * cell + 4, (2 * ri + vi) * cell + 3), f'{nm} {f}' if vi == 0 else 'front', fill=(230, 230, 230))
    img.save(out); print('wrote', out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('names'); ap.add_argument('--step', type=int, default=2)
    a = ap.parse_args()
    sheet(a.out, a.names.split(','), a.step)
