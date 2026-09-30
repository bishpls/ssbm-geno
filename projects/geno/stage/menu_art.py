"""The Forest Maze's stage-select art, greybox edition: the icon (64x56, 256 colours), the name (224x56 intensity) and the
hologram preview's mesh (drawn in game from the spec). Writes raw BGRA the datkit menus-stage command reads, and PNGs.
    .venv/bin/python projects/geno/stage/menu_art.py OUT_DIR [NAME_REF.png]
The name's small line is copied pixel for pixel from a vanilla name ("Mushroom Kingdom", Princess Peach's Castle's, when
NAME_REF is the decoded image 0 of StageNameModel), so it matches the others; the big line is set in Big Shoulders
Display Black (OFL, vendored in engine/fonts) with the vanilla names' forward slant. The icon draws the stage from the
spec's outline in the greybox colours. Both are placeholders until the production art (M3). Output stays local.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layouts, stage_spec  # noqa: E402

FONT = os.path.expanduser('~/animation-pipeline/engine/fonts/BigShouldersDisplay.ttf')


def name_image(ref=None):
    W, H = 224, 56
    img = Image.new('L', (W, H), 0)
    if ref and os.path.exists(ref):
        r = np.asarray(Image.open(ref).convert('RGBA'))
        small = r[:16, :, 3]                                        # the small line's rows (1-15)
        img.paste(Image.fromarray(small), (0, 0))
    big = Image.new('L', (W * 2, 64), 0)
    d = ImageDraw.Draw(big)
    f = ImageFont.truetype(FONT, 50)
    try:
        f.set_variation_by_axes([900])                             # Black
    except Exception:
        pass
    text = 'Forest Maze'
    w = d.textlength(text, font=f)
    d.text(((W * 2 - w) / 2, -6), text, fill=255, font=f)
    # the vanilla big lines lean forward about 12 degrees
    sh = 0.21
    big = big.transform(big.size, Image.AFFINE, (1, sh, -sh * 32, 0, 1, 0), resample=Image.BICUBIC)
    box = big.getbbox()
    crop = big.crop(box)
    tw, th = crop.size
    target_h = 36
    tw2 = int(tw * target_h / th)
    if tw2 > 206: tw2 = 206
    crop = crop.resize((tw2, target_h), Image.LANCZOS)
    img.paste(crop, ((W - tw2) // 2, 17), crop)
    return img


def icon_image():
    W, H = 64, 56
    S = 4                                                          # supersample
    im = Image.new('RGB', (W * S, H * S), (30, 52, 38))
    d = ImageDraw.Draw(im)
    # a canopy gradient and a few trunks behind
    for y in range(H * S):
        t = y / (H * S)
        d.line([(0, y), (W * S, y)], fill=(int(24 + 30 * t), int(46 + 40 * t), int(34 + 20 * t)))
    for x, w in ((10, 7), (24, 5), (44, 6), (56, 8)):
        d.rectangle([x * S, 0, (x + w) * S, H * S], fill=(58, 48, 38))
    # the stage in world units -> icon pixels: 160 wide window centred on (0, 4)
    sc = W * S / 170.0
    ox, oy = W * S / 2, H * S * 0.52
    P = lambda x, y: (ox + x * sc, oy - y * sc)
    spec = stage_spec.spec('clearing')
    V = spec['collision']['vertices']
    ring = [tuple(v) for v in V[:len(V) - 2]]
    d.polygon([P(*p) for p in ring], fill=stage_spec.COL['bark'])
    L = layouts.BODY['ledge_x']
    d.rectangle([*P(-L, 0), *P(L, -3)], fill=stage_spec.COL['top'])
    cap = layouts.CANDIDATES['clearing']['platforms'][0]
    d.rectangle([*P(cap['x0'], cap['y']), *P(cap['x1'], cap['y'] - stage_spec.CAP_T)], fill=stage_spec.COL['cap'])
    im = im.resize((W, H), Image.LANCZOS).quantize(colors=250, method=Image.Quantize.MEDIANCUT).convert('RGB')
    return im


def bgra(img):
    a = np.asarray(img.convert('RGBA')).copy()
    return a[..., [2, 1, 0, 3]].tobytes()


def main(out, ref=None):
    os.makedirs(out, exist_ok=True)
    n = name_image(ref)
    rgba = Image.merge('RGBA', (n, n, n, n))                      # intensity: the I4 encoder averages R, G and B
    open(os.path.join(out, 'name.bgra'), 'wb').write(bgra(rgba)); rgba.save(os.path.join(out, 'name.png'))
    ic = icon_image()
    open(os.path.join(out, 'icon.bgra'), 'wb').write(bgra(ic)); ic.save(os.path.join(out, 'icon.png'))
    print('wrote', out, 'icon colours', len(ic.getcolors(4096) or []))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
