"""Get-up attack coverage across the cast: how high the hits reach on each side, whether they cover the space over the
fighter's own body, and how high an opponent must be to clear them (jump clearance), from `datkit movedata` geometry (every
active frame's spheres in the fighter's space: facing +z, feet at y = 0).
    .venv/bin/python projects/geno/director/labs/getup_cover.py MOVEDATA [OUT.md]
For each move, top(z) is the highest point any hitbox covers at horizontal offset z over all active frames. Reported:
  - side top: the highest point covered in front (z > 0) and behind (z < 0);
  - top at 8 / 14 units: the height covered where an opponent stands close in and at mid range, each side;
  - over body: the highest point covered within 3 units of his centre (0: nothing over him);
  - clear at d: the height an opponent's feet must be above, at centre distance d, to pass over untouched (the highest
    coverage within W of d; W = 3, an airborne body's half-width), at d = 0 (a hop straight over him), 8 and 14.
"""
import json, math, os, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cast_moves import NAMES, WATCH

MOVES = ['getup_u', 'getup_d']
W = 3.0


def load(d):
    out = {}
    for f in os.listdir(d):
        c = f[:-6]
        if f.endswith('.jsonl') and c in NAMES and c != 'Nn':
            for l in open(os.path.join(d, f)):
                o = json.loads(l)
                if o.get('move') in MOVES: out.setdefault(c, {})[o['move']] = o
    return out


def profile(o, z0=-30.0, z1=30.0, step=0.25):
    """z -> (top, bottom) of the union of every active frame's spheres."""
    prof = {}
    for f, spheres in o.get('geo', []):
        for y, zc, r in spheres:
            z = math.ceil((zc - r - z0) / step) * step + z0
            while z <= zc + r:
                h = math.sqrt(max(0.0, r * r - (z - zc) ** 2))
                t, b = prof.get(round(z, 2), (-1e9, 1e9))
                prof[round(z, 2)] = (max(t, y + h), min(b, y - h))
                z += step
    return prof


def metrics(o):
    p = profile(o)
    top = lambda a, b: max([t for z, (t, _) in p.items() if a <= z <= b] or [0.0])
    return dict(front_top=round(top(0.01, 99), 1), back_top=round(top(-99, -0.01), 1),
                front_8=round(top(7.5, 8.5), 1), back_8=round(top(-8.5, -7.5), 1),
                front_14=round(top(13.5, 14.5), 1), back_14=round(top(-14.5, -13.5), 1),
                over_body=round(top(-3, 3), 1), clear_0=round(top(-W, W), 1),
                clear_8=round(max(top(8 - W, 8 + W), top(-8 - W, -8 + W)), 1),
                clear_14=round(max(top(14 - W, 14 + W), top(-14 - W, -14 + W)), 1))


def main(d, out=None):
    data = load(d)
    intro = __doc__.split('\n    .venv')[0].strip() + '\n' + __doc__.split('.md]\n', 1)[1].strip()
    lines = ['# Get-up attacks: coverage (measured)', '', intro, '',
             'Units are world units; heights from his feet. `pct` is Geno\'s percentile in the cast (25 others).', '']
    summary = {}
    for mv in MOVES:
        rows = {c: metrics(m[mv]) for c, m in data.items() if mv in m and m[mv].get('geo')}
        cast = {c: r for c, r in rows.items() if c != 'Ge'}
        cols = list(next(iter(cast.values())).keys())
        lines += [f'## {mv}', '', '| | ' + ' | '.join(cols) + ' |', '|---|' + '---|' * len(cols)]
        for label, fn in [('cast min', min), ('cast median', st.median), ('cast max', max)]:
            lines.append(f'| {label} | ' + ' | '.join(f'{fn([r[c] for r in cast.values()]):.1f}' for c in cols) + ' |')
        for c in WATCH:
            if c in cast: lines.append(f'| {NAMES[c]} | ' + ' | '.join(str(cast[c][k]) for k in cols) + ' |')
        if 'Ge' in rows:
            g = rows['Ge']
            pc = lambda k: round(100 * sum(1 for r in cast.values() if r[k] < g[k]) / len(cast) + 50 / len(cast))
            lines.append('| **GENO now** | ' + ' | '.join(f'**{g[k]}**' for k in cols) + ' |')
            lines.append('| Geno pct | ' + ' | '.join(str(pc(k)) for k in cols) + ' |')
            summary[mv] = dict(geno=g, median={k: st.median([r[k] for r in cast.values()]) for k in cols})
        lines.append('')
    text = '\n'.join(lines)
    if out:
        open(out, 'w').write(text + '\n')
    print(text)
    return summary


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
