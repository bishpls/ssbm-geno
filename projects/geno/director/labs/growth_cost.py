"""What limb growth costs a move: a grown limb's hurtboxes grow with it (the engine measures a hurtbox's radius in its
bone's space), so they stick out further on the hit frames. For the cast, datkit movedata with and without their scale
tracks (MOVEDATA_NOSCALE=1; measure_cast.sh into OUT); for Geno, his build with and without the growth (GENO_NO_GROW=1).
Per move and direction: how far the hurtboxes reach further ("hurt +") and how the disjoint changes. The cast's hitboxes
ride their grown bones, so their reach grows too and the net disjoint barely moves; Geno's hitboxes stay put (his fists
pull in by the growth), so his hurtbox growth comes off his disjoint whole. A Geno move is flagged when its disjoint
loss in its hit direction exceeds every Mario-family analog's (Mario, Luigi, Doc).
    .venv/bin/python projects/geno/director/labs/growth_cost.py MOVEDATA NOSCALE_DIR GENO_NOGROW.jsonl OUT.md [OUT.json]
"""
import json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = dict(Mr='Mario', Lg='Luigi', Dr='Doc', Fx='Fox', Ge='Geno')
DIRS = [('fwd', 'fwd'), ('back', 'back'), ('up', 'up'), ('down', 'down')]
# Geno's grown moves: (move, the direction it hits, the Mario-family analogs it is judged against)
GENO = [('jab1', 'fwd', ['Mr:jab1', 'Lg:jab1', 'Dr:jab1']), ('jab2', 'fwd', ['Mr:jab2', 'Lg:jab2', 'Dr:jab2']),
        ('jab3', 'fwd', ['Mr:jab3', 'Lg:jab3', 'Dr:jab3']), ('dash_attack', 'fwd', ['Lg:dash_attack', 'Mr:dash_attack']),
        ('utilt', 'up', ['Mr:utilt', 'Lg:utilt', 'Dr:utilt']), ('fsmash', 'fwd', ['Mr:fsmash', 'Lg:fsmash', 'Dr:fsmash']),
        ('fsmash_hi', 'fwd', ['Mr:fsmash_hi', 'Lg:fsmash_hi', 'Dr:fsmash_hi']),
        ('fsmash_lw', 'fwd', ['Mr:fsmash_lw', 'Lg:fsmash_lw', 'Dr:fsmash_lw']),
        ('nair', 'back', ['Mr:bair', 'Lg:bair', 'Dr:bair', 'Lg:nair']), ('grab', 'fwd', ['Mr:grab', 'Lg:grab', 'Dr:grab']),
        ('dash_grab', 'fwd', ['Mr:dash_grab', 'Lg:dash_grab', 'Dr:dash_grab']), ('pummel', 'fwd', ['Mr:pummel', 'Lg:pummel'])]


def load(p):
    return {m['move']: m for m in map(json.loads, open(p)) if 'move' in m} if os.path.exists(p) else {}


def cost(a, b):
    """per direction: hurtboxes reaching further (outward positive) and the disjoint change, a (grown) against b"""
    out = {}
    for d, _ in DIRS:
        ha, hb = a.get(f'hurt_{d}'), b.get(f'hurt_{d}')
        da, db = a.get(f'disjoint_{d}'), b.get(f'disjoint_{d}')
        sgn = -1 if d == 'down' else 1                    # hurt_down is a height: lower is further out
        out[d] = dict(hurt=None if ha is None or hb is None else round(sgn * (ha - hb), 2),
                      disj=None if da is None or db is None else round(da - db, 2), now=da)
    return out


def main():
    md, ns, geno_ng, out_md = sys.argv[1:5]
    out_json = sys.argv[5] if len(sys.argv) > 5 else os.path.splitext(out_md)[0] + '.json'
    ls = json.load(open(os.path.join(HERE, '..', '..', 'research', 'limb_scale.json')))
    peak = {}
    for r in ls:
        k = (r['fighter'], r['move']); peak[k] = max(peak.get(k, 1.0), r['end_eff_peak'])
    cast = {}
    for code in sorted({f for f, _ in peak}):
        a, b = load(f'{md}/{code}.jsonl'), load(f'{ns}/{code}.jsonl')
        for mv, m in a.items():
            if peak.get((code, mv), 1.0) >= 1.1 and mv in b and m.get('hurt_fwd') is not None:
                cast[f'{code}:{mv}'] = dict(scale=peak[(code, mv)], cost=cost(m, b[mv]))
    g, gn = load(f'{md}/Ge.jsonl'), load(geno_ng)
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../rig/moves.py')).read()
    m = __import__('re').search(r'^GROW_INTANG = \{([^}]*)\}', src, __import__('re').M)
    intang = ', '.join(sorted(x.strip(" '\"") for x in m.group(1).split(',') if x.strip())) if m else 'none'
    rows, L = [], ['# What limb growth costs a move', '',
                   'From `director/labs/growth_cost.py`. A grown limb\'s hurtboxes grow with it (the engine measures a hurtbox\'s '
                   'radius in its bone\'s space), so on the hit frames they reach further: "hurt +" (world units, outward). The '
                   'cast\'s hitboxes ride their grown bones, so their net disjoint barely moves; Geno\'s stay put, so his hurtbox '
                   'growth comes off his disjoint whole. A Geno move is **flagged** when its disjoint loss in its hit direction '
                   'exceeds every Mario-family analog\'s. Moves in `moves.GROW_INTANG` (' + intang + ') make the grown part '
                   'intangible while grown, so their hurt + is negative: its hurtboxes are gone on those frames. The jabs keep '
                   'their full growth and pay its cost (Michael, 2026-09-29), so they stay flagged by design.', '',
                   '## Geno', '',
                   '| Move | Direction | Hurt + | Disjoint before | Disjoint now | Change | Mario family (change) | Flag | Other directions (hurt + / disjoint change) |',
                   '|---|---|---|---|---|---|---|---|---|']
    for mv, d, analogs in GENO:
        if mv not in g or mv not in gn: continue
        c = cost(g[mv], gn[mv])[d]
        an = [(k, cast[k]['cost'][d]['disj']) for k in analogs if k in cast and cast[k]['cost'][d]['disj'] is not None]
        worst = min([v for _, v in an], default=0.0)
        flag = c['disj'] is not None and c['disj'] < min(worst, 0.0) - 0.05
        rows.append(dict(move=mv, dir=d, hurt=c['hurt'], before=gn[mv].get(f'disjoint_{d}'), now=g[mv].get(f'disjoint_{d}'),
                         change=c['disj'], analogs=dict(an), flag=flag))
        call = cost(g[mv], gn[mv])
        other = [f"{o} {call[o]['hurt']:+.2f} / {call[o]['disj']:+.2f}" for o, _ in DIRS if o != d and call[o]['hurt'] is not None
                 and call[o]['disj'] is not None and (abs(call[o]['hurt']) > 0.02 or abs(call[o]['disj']) > 0.02)]
        L.append(f"| {mv} | {d} | {c['hurt']} | {gn[mv].get(f'disjoint_{d}')} | {g[mv].get(f'disjoint_{d}')} | {c['disj']} | "
                 f"{', '.join(f'{NAME[k[:2]]} {k[3:]} {v:+.2f}' for k, v in an) or 'none grow'} | {'**yes**' if flag else ''} | "
                 f"{', '.join(other)} |")
    L += ['', '## The cast (every move that grows a limb 1.1x or more)', '']
    for d, _ in DIRS:
        h = sorted(v['cost'][d]['hurt'] for v in cast.values() if v['cost'][d]['hurt'] is not None)
        j = sorted(v['cost'][d]['disj'] for v in cast.values() if v['cost'][d]['disj'] is not None)
        if h and j:
            L.append(f'- {d}: hurt + median {st.median(h):.2f}, 90th {h[int(0.9 * len(h))]:.2f}, max {h[-1]:.2f}; '
                     f'disjoint change median {st.median(j):+.2f}, 10th {j[int(0.1 * len(j))]:+.2f}, min {j[0]:+.2f} '
                     f'({len(h)} moves)')
    L += ['', '| Fighter | Move | Largest scale | Hurt + fwd / back / up / down | Disjoint change fwd / back / up / down |',
          '|---|---|---|---|---|']
    for k, v in cast.items():
        if k[:2] not in ('Mr', 'Lg', 'Dr'): continue
        c = v['cost']
        L.append(f"| {NAME[k[:2]]} | {k[3:]} | {v['scale']} | " + ' / '.join(str(c[d]['hurt']) for d, _ in DIRS) + ' | ' +
                 ' / '.join(str(c[d]['disj']) for d, _ in DIRS) + ' |')
    open(out_md, 'w').write('\n'.join(L) + '\n')
    json.dump(dict(geno=rows, cast=cast), open(out_json, 'w'), indent=1)
    print(out_md, len(rows), 'Geno moves,', sum(r['flag'] for r in rows), 'flagged')


if __name__ == '__main__':
    main()
