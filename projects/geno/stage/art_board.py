"""One art pass, measured and boarded against t7 and M3 (art_pass.sh writes the renders into the pass folder).
    .venv/bin/python projects/geno/stage/art_board.py PASS_DIR     -> PASS_DIR/metrics.json, PASS_DIR/board.jpg
The numbers:
  - hero vs t7 (t7's camera, the same aspect): relative-luminance histograms (16 bins) and their overlap (1 = the same
    distribution), mean and spread of luminance, the value structure (mean luminance of the top, middle and bottom
    thirds), and hue-saturation histograms (12 hues x 3 saturations, weighted by saturation) with their overlap;
  - readability (lookmetrics.py) of the match framings at x 25 and x 55, against M3's and Final Destination's (0.275);
  - the edge lab's worst row and end errors in pixels, drawn as an overlay (red: the collision's edge and ends).
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'director'))
import lookmetrics  # noqa: E402

W = os.path.expanduser(os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'stage'))
T7 = os.path.join(W, 'targets', 't7.png')
M3 = {25: os.path.join(W, 'final', 'match_prod_x25.png'), 55: os.path.join(W, 'final', 'match_prod_x55.png')}


def lum(a):
    a = a / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return lin @ np.array([0.2126, 0.7152, 0.0722])


def stats(path, size=(640, 360)):
    im = Image.open(path).convert('RGB').resize(size, Image.LANCZOS)
    a = np.asarray(im).astype(float)
    Y = lum(a)
    hist = np.histogram(Y, 16, (0, 1))[0] / Y.size
    hsv = np.asarray(im.convert('HSV')).astype(float) / 255
    h, s = hsv[..., 0], hsv[..., 1]
    hb = np.minimum((h * 12).astype(int), 11); sb = np.minimum((s * 3).astype(int), 2)
    hs = np.zeros((12, 3))
    np.add.at(hs, (hb, sb), s)
    hs /= max(hs.sum(), 1e-9)
    thirds = [round(float(Y[i * size[1] // 3:(i + 1) * size[1] // 3].mean()), 3) for i in range(3)]
    return dict(Y=Y, hist=hist, hs=hs, mean=round(float(Y.mean()), 3), std=round(float(Y.std()), 3), thirds=thirds,
                sat=round(float(s.mean()), 3))


def overlap(a, b):
    return round(float(np.minimum(a, b).sum()), 3)


def bars(hists, labels, colours, w=420, h=120):
    im = Image.new('RGB', (w, h + 18), (250, 250, 250)); d = ImageDraw.Draw(im)
    n = len(hists[0]); bw = w / n
    m = max(max(x) for x in hists)
    for k, (hh, col) in enumerate(zip(hists, colours)):
        for i, v in enumerate(hh):
            x0 = i * bw + k * bw / len(hists)
            d.rectangle([x0, h - v / m * h, x0 + bw / len(hists) - 1, h], fill=col)
    for k, (lab, col) in enumerate(zip(labels, colours)):
        d.text((6 + k * 150, h + 4), lab, fill=col)
    return im


def edge_overlay(P, rep):
    """Crops of the edge lab's frames around each end, with the collision (red) drawn over them."""
    sys.argv = [sys.argv[0]]
    import edge_lab
    out = []
    for shot, fn in (('floor', 'edge_floor.png'), ('cap', 'edge_cap.png')):
        path = os.path.join(P, fn)
        if not os.path.exists(path):
            continue
        im = Image.open(path).convert('RGB'); Wd, H = im.size
        s = [x for x in edge_lab.SHOTS if x['name'] == shot][0]
        d = ImageDraw.Draw(im)
        d.line([(0, H / 2), (Wd, H / 2)], fill=(255, 0, 0), width=1)
        for x, z in s['ends']:
            ex, _ = edge_lab.project(x, s['y'], z, s['y'], Wd, H)
            d.line([(ex, H / 2 - 30), (ex, H / 2 + 30)], fill=(255, 0, 0), width=1)
        for x, z in s['ends']:
            ex, _ = edge_lab.project(x, s['y'], z, s['y'], Wd, H)
            c = im.crop((int(ex) - 40, int(H / 2) - 30, int(ex) + 40, int(H / 2) + 30)).resize((240, 180), Image.NEAREST)
            out.append((c, f'{shot} end x={x:g}'))
    return out


def main(P):
    m = dict(pass_dir=P)
    if os.path.exists(os.path.join(P, 'budget.txt')):
        m['budget'] = open(os.path.join(P, 'budget.txt')).read().strip()
    t7, hero = stats(T7), stats(os.path.join(P, 'hero.png'))
    m['hero_vs_t7'] = dict(lum_overlap=overlap(t7['hist'], hero['hist']), hue_sat_overlap=overlap(t7['hs'].ravel(), hero['hs'].ravel()),
                           mean=[t7['mean'], hero['mean']], std=[t7['std'], hero['std']], thirds=[t7['thirds'], hero['thirds']],
                           sat=[t7['sat'], hero['sat']])
    m['readability'] = {}
    for X in (25, 55):
        p = os.path.join(P, f'match_x{X}.png')
        m['readability'][f'x{X}'] = lookmetrics.metrics(p)['readability']
        m['readability'][f'm3_x{X}'] = lookmetrics.metrics(M3[X])['readability'] if os.path.exists(M3[X]) else None
    rep = json.load(open(os.path.join(P, 'edge.json'))) if os.path.exists(os.path.join(P, 'edge.json')) else None
    if rep:
        m['edges'] = dict(ok=rep['ok'], **{s['shot']: dict(row_px=s['row_err_px'], end_px=s['end_err_px'], ends=[e['err_px'] for e in s['ends']]) for s in rep['shots']})
    json.dump(m, open(os.path.join(P, 'metrics.json'), 'w'), indent=1)
    # the board
    Wb = 1300
    board = Image.new('RGB', (Wb, 2000), (255, 255, 255)); d = ImageDraw.Draw(board)
    y = 6
    d.text((8, y), f"{os.path.basename(P)}   {m.get('budget', '')}", fill=(0, 0, 0)); y += 18
    def pair(a, b, la, lb, h):
        nonlocal y
        ia, ib = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
        ia = ia.resize((int(ia.size[0] * h / ia.size[1]), h)); ib = ib.resize((int(ib.size[0] * h / ib.size[1]), h))
        board.paste(ia, (6, y + 14)); board.paste(ib, (12 + ia.size[0], y + 14))
        d.text((8, y), la, fill=(0, 0, 0)); d.text((14 + ia.size[0], y), lb, fill=(0, 0, 0))
        y += h + 20
    hv = m['hero_vs_t7']
    pair(T7, os.path.join(P, 'hero.png'), 't7 (target)', f"pass: lum overlap {hv['lum_overlap']}, hue overlap {hv['hue_sat_overlap']}, "
         f"mean Y {hv['mean'][0]}/{hv['mean'][1]}, thirds {hv['thirds'][0]} / {hv['thirds'][1]}", 360)
    for X in (25, 55):
        if os.path.exists(M3[X]):
            pair(M3[X], os.path.join(P, f'match_x{X}.png'), f"M3 x{X} (readability {m['readability'][f'm3_x{X}']})",
                 f"pass x{X} (readability {m['readability'][f'x{X}']}; Final Destination 0.275)", 330)
    hb = bars([t7['hist'], hero['hist']], ['t7 luminance', 'pass luminance'], [(200, 120, 60), (60, 90, 200)])
    hs = bars([t7['hs'].sum(1), hero['hs'].sum(1)], ['t7 hue (12 bins)', 'pass hue'], [(200, 120, 60), (60, 90, 200)])
    board.paste(hb, (6, y)); board.paste(hs, (440, y)); y += hb.size[1] + 8
    x = 6
    for c, lab in edge_overlay(P, rep):
        board.paste(c, (x, y + 14)); d.text((x, y), lab, fill=(0, 0, 0)); x += 250
    if rep:
        d.text((x + 6, y + 30), f"edges ok {rep['ok']}", fill=(0, 0, 0))
        for k, s in enumerate(rep['shots']):
            d.text((x + 6, y + 50 + 16 * k), f"{s['shot']}: row {s['row_err_px']} px, ends {[e['err_px'] for e in s['ends']]} px", fill=(0, 0, 0))
    y += 200
    for n, fn in enumerate(('base.png', 'ledge.png', 'cap.png')):
        p = os.path.join(P, fn)
        if os.path.exists(p):
            im = Image.open(p).convert('RGB'); im = im.resize((420, int(420 * im.size[1] / im.size[0])))
            board.paste(im, (6 + n * 430, y))
    y += 250
    board.crop((0, 0, Wb, y)).save(os.path.join(P, 'board.jpg'), quality=86)
    print(json.dumps({k: v for k, v in m.items() if k != 'pass_dir'}))


if __name__ == '__main__':
    main(sys.argv[1])
