"""Hitbox sweep charts: each move's hit spheres at every active frame, drawn around the fighter's measured standing body
(facing right, feet on the line), coloured from the first active frame (yellow) to the last (red), so the shape of the
coverage reads at a glance: an arc that sweeps front to back (crossups, landing behind a shield) versus a narrow column
straight down, a forward wall, a late back hit. From `datkit movedata` (per-frame geometry, lunges and stretches included).
    .venv/bin/python projects/geno/director/labs/sweeps.py MOVEDATA OUT.png [moves] [fighters]
"""
import json, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from aerial_profile import load
from cast_moves import NAMES, WATCH

LOW = 4.0        # units above his feet that count as "near the feet"


def fit(cells):
    """One scale and origin for every cell: the union of all spheres and bodies, in units."""
    z0, z1, y0, y1 = -10.0, 15.0, -5.0, 20.0
    for o, body in cells:
        for f, spheres in (o or {}).get('geo', []):
            for cy, cz, r in spheres:
                z0, z1, y0, y1 = min(z0, cz - r), max(z1, cz + r), min(y0, cy - r), max(y1, cy + r)
        if body: z0, y1 = min(z0, -body['back']), max(y1, body['top'])
    s = min(7.0, 420 / (z1 - z0), 330 / (y1 - y0))
    return s, int((z1 - z0) * s) + 24, int((y1 - y0) * s) + 44, 12 - z0 * s, 22 + y1 * s


def cell(o, body, label, geom):
    S, CW, CH, ox, oy = geom
    img = Image.new('RGB', (CW, CH), (32, 34, 44))
    d = ImageDraw.Draw(img)
    for gx in range(-60, 61, 5):                              # a 5-unit grid
        d.line([(ox + gx * S, 0), (ox + gx * S, CH)], fill=(44, 46, 58))
    for gy in range(-30, 45, 5):
        d.line([(0, oy - gy * S), (CW, oy - gy * S)], fill=(44, 46, 58))
    d.line([(0, oy), (CW, oy)], fill=(120, 120, 140))
    if body:
        d.rectangle([ox - body['back'] * S, oy - body['top'] * S, ox + body['front'] * S, oy], outline=(90, 150, 230), width=2)
    geo = o.get('geo', []) if o else []
    n = max(1, len(geo) - 1)
    for i, (f, spheres) in enumerate(geo):
        u = i / n
        col = (255, int(230 * (1 - u) + 40 * u), int(60 * (1 - u)))
        for cy, cz, r in spheres:
            x, y = ox + cz * S, oy - cy * S
            d.ellipse([x - r * S, y - r * S, x + r * S, y + r * S], outline=col, width=2)
    d.text((6, 6), label, fill=(235, 235, 245))
    if o and o.get('startup', -1) >= 0:
        d.text((6, CH - 16), f"f{o['startup']}-{o['last_active']}  {o['damage_max']}%", fill=(200, 200, 215))
    return img


def shape(o):
    geo = [(f, sp) for f, sp in (o or {}).get('geo', []) if sp]
    if not geo: return None
    every = [s for f, sp in geo for s in sp]
    low = [(cy, cz, r) for cy, cz, r in every if cy - r <= LOW]
    mean = lambda sp: sum(cz for cy, cz, r in sp) / len(sp)
    return dict(front=max(cz + r for cy, cz, r in every), back=max(r - cz for cy, cz, r in every),
                up=max(cy + r for cy, cz, r in every), below=max(r - cy for cy, cz, r in every),
                low_front=max((cz + r for cy, cz, r in low), default=None), low_back=max((r - cz for cy, cz, r in low), default=None),
                sweep=(mean(geo[0][1]), mean(geo[-1][1])))


def table(mv, moves, fighters):
    n = lambda v: '-' if v is None else f'{v:.0f}'
    lines = [f'Units from the fighter\'s position (facing right), times ModelScale. Low = spheres reaching within {LOW:g} units of '
             'the feet. Low back is crossup coverage (hitting a shield or body as he lands behind it); sweep is where the hit sits '
             'on its first active frame, then its last (+ in front, - behind). Bair is measured as the game places it (behind: '
             'negative front).', '']
    for m in moves:
        lines += [f'## {m}', '', '| | front | back | up | below feet | low front | low back | sweep |', '|---|---|---|---|---|---|---|---|']
        for c in fighters:
            h = shape(mv.get(c, {}).get(m))
            if not h: continue
            nm = f'**{NAMES[c]}**' if c == 'Ge' else NAMES[c]
            lines.append(f"| {nm} | {n(h['front'])} | {n(h['back'])} | {n(h['up'])} | {n(h['below'])} | {n(h['low_front'])} | "
                         f"{n(h['low_back'])} | {h['sweep'][0]:+.0f} → {h['sweep'][1]:+.0f} |")
        lines.append('')
    return '\n'.join(lines)


def main(movedata, out, moves=None, fighters=None):
    mv, bodies = load(movedata)
    moves = (moves or 'nair,fair,bair,uair,dair').split(',')
    fighters = (fighters or 'Ge,Ms,Fx,Fc,Sk,Pe,Ca').split(',')
    if out.endswith('.md'):
        open(out, 'w').write('# Aerial and move shapes (measured)\n\n' + table(mv, moves, fighters) + '\n')
        print('wrote', out); return
    cells = [[(mv.get(c, {}).get(m), bodies.get(c, {}).get('stand')) for m in moves] for c in fighters]
    geom = fit([x for row in cells for x in row])
    CW, CH = geom[1], geom[2]
    sheet = Image.new('RGB', (CW * len(moves), CH * len(fighters)), (20, 20, 26))
    for r, c in enumerate(fighters):
        for k, m in enumerate(moves):
            o, body = cells[r][k]
            sheet.paste(cell(o, body, f'{NAMES[c]} {m}', geom), (k * CW, r * CH))
    sheet.save(out)
    print('wrote', out, f'({geom[0]:.1f} px per unit)')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], *(sys.argv[3:5]))
