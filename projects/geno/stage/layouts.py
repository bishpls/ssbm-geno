"""Forest Maze candidate layouts as stage specs, measured against the six starters.
    .venv/bin/python projects/geno/stage/layouts.py        # research/layouts.{json,csv} + a diagram per candidate
A spec is what `stage-build` will take (SCOPE.md §3): the main stage's ledges and side profile, the platforms, blast zones,
camera range and spawn points, in world units. `outline()` turns a spec into the collision lines the build would write,
so the diagrams show exactly the geometry a fighter would meet, and `measure()` reports it the way starters.py reports the
vanilla stages.
"""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import starters  # noqa: E402

# The shared body: a mossy stump top, ledges at +-70 (140 wide: between Battlefield's 136.8 and Dream Land's 154.5, the
# five starters' mean is 140.2). Under each ledge the bark wall drops straight for 6, then the roots slope in: 3.5 in at 10
# below the ledge (Yoshi's Story 3.3, Fountain 1.9, Battlefield's lip 13.2, Final Destination 0), no lip to catch an up-B.
# Profile points are (inset from the ledge, depth below it).
BODY = dict(ledge_x=70.0, floor_y=0.0, profile=[(0, 0), (0, 6), (14, 22), (30, 34), (52, 40)])
# Blast zones at the five starters' medians: 155 past each ledge (Battlefield 155.6), top 200 (Battlefield), bottom 120
# below (between Battlefield's 108.8 and Dream Land's 123; the median is 123)
BLAST = dict(left=-225.0, right=225.0, top=200.0, bottom=-120.0)
CAMERA = dict(left=-160.0, right=160.0, top=140.0, bottom=-55.0, centre=[0.0, 30.0])

CANDIDATES = {
    'clearing': dict(
        title='A. Clearing: one wide mushroom cap',
        blurb='One wide platform over the centre; open flanks to both ledges',
        platforms=[dict(x0=-27.0, x1=27.0, y=28.0, look='giant mushroom cap')],
        spawns=[[-45.0, 0.0], [45.0, 0.0], [-15.0, 28.0], [15.0, 28.0]],
        respawns=[[-40.0, 80.0], [40.0, 80.0], [-13.0, 80.0], [13.0, 80.0]],
        nearest='battlefield'),
    'boughs': dict(
        title='B. Twin Boughs: two inboard branches',
        blurb='Two platforms close over the centre with a narrow gap; open flanks',
        # at 28, as the Clearing's cap (Battlefield's sides 27.2): every fighter's full hop but Jigglypuff's, Kirby's and
        # Ganondorf's (multi-jumps, 27.3) clears it, so a camper on the boughs stays in reach (Dream Land's 30.1 doesn't:
        # Mario, Doc, Game & Watch and Link top out near 29)
        platforms=[dict(x0=-40.0, x1=-10.0, y=28.0, look='branch'), dict(x0=10.0, x1=40.0, y=28.0, look='branch')],
        spawns=[[-50.0, 0.0], [50.0, 0.0], [-25.0, 28.0], [25.0, 28.0]],
        respawns=[[-40.0, 80.0], [40.0, 80.0], [-13.0, 80.0], [13.0, 80.0]],
        nearest='stadium'),
    'hollow': dict(
        title='C. Hollow: the inverted triangle',
        blurb='A low log in the centre, two high caps toward the ledges',
        # the sides stop at Dream Land's height (30.2, the highest perch any starter has within 20 of a ledge) and 10
        # inside the ledges (Battlefield 10.8); the log is the lowest static platform in the pool (Yoshi's Story 23.45),
        # at heights Fountain of Dreams' moving platforms pass through all the time
        platforms=[dict(x0=-60.0, x1=-34.0, y=30.0, look='shelf mushroom'), dict(x0=-16.0, x1=16.0, y=18.0, look='log'),
                   dict(x0=34.0, x1=60.0, y=30.0, look='shelf mushroom')],
        spawns=[[-45.0, 0.0], [45.0, 0.0], [0.0, 18.0], [0.0, 0.0]],
        respawns=[[-40.0, 80.0], [40.0, 80.0], [-13.0, 80.0], [13.0, 80.0]],
        nearest='battlefield'),
}


def outline(spec):
    """The collision a spec builds, as starters.py's outline rows: [a, b, kind, drop_through, ledge]. The floor runs ledge
    to ledge in three lines (the outer 8 at each end carry the ledge flag, as the vanilla stages' end lines do); each side
    wall follows the profile down and in; a ceiling closes the bottom."""
    L, fy = BODY['ledge_x'], BODY['floor_y']
    rows = [[[-L, fy], [-L + 8, fy], 'floor', False, True], [[-L + 8, fy], [L - 8, fy], 'floor', False, False],
            [[L - 8, fy], [L, fy], 'floor', False, True]]
    prof = BODY['profile']
    for side in (-1, 1):
        pts = [[side * (L - i), fy - d] for i, d in prof]
        for a, b in zip(pts, pts[1:]):
            rows.append([a, b, 'right_wall' if side > 0 else 'left_wall', False, False])
    bl, br = [-(L - prof[-1][0]), fy - prof[-1][1]], [L - prof[-1][0], fy - prof[-1][1]]
    rows.append([br, bl, 'ceiling', False, False])
    for p in spec['platforms']:
        rows.append([[p['x0'], p['y']], [p['x1'], p['y']], 'floor', True, False])
    return rows


def as_stage(name):
    """A candidate in starters.analyse()'s shape, for the shared drawing and table code."""
    c = CANDIDATES[name]
    L, fy = BODY['ledge_x'], BODY['floor_y']
    plats = []
    for p in sorted(c['platforms'], key=lambda p: p['x0']):
        mid = (p['x0'] + p['x1']) / 2
        lab = 'top' if abs(mid) < 5 and len(c['platforms']) != 1 and p['y'] == max(q['y'] for q in c['platforms']) else \
              'centre' if abs(mid) < 5 else ('left' if mid < 0 else 'right')
        plats.append(dict(x0=p['x0'], x1=p['x1'], width=p['x1'] - p['x0'], y=p['y'], y_top=p['y'], height=p['y'] - fy,
                          moves=False, label=lab, material='Wood', lines=[]))
    undercut = {}
    for depth in (2, 5, 10, 20, 30, 40):
        pr = BODY['profile']
        for (i0, d0), (i1, d1) in zip(pr, pr[1:]):
            if d0 <= depth <= d1:
                ins = i0 + (i1 - i0) * (depth - d0) / (d1 - d0) if d1 != d0 else i1
                undercut[depth] = [round(ins, 3), round(ins, 3)]
                break
    return dict(name=name, title=c['title'], candidate=True, scale=1.0,
                main=dict(ledge_left=[-L, fy], ledge_right=[L, fy], width=2 * L, floor_y=fy, depth=BODY['profile'][-1][1],
                          undercut=undercut, slanted_edges=False, materials=['Grass']),
                platforms=plats, blast=dict(BLAST), camera=dict(CAMERA), spawns=c['spawns'], respawns=c['respawns'],
                ceiling_above_floor=BLAST['top'] - fy, bottom_below_floor=fy - BLAST['bottom'],
                side_blast_from_ledge=[-L - BLAST['left'], BLAST['right'] - L], outline=outline(c))


def measure(s):
    """The numbers the design argues with, for a starter or a candidate."""
    m = s['main']
    ps = [p for p in s['platforms'] if p['label'] != 'randall']
    W = m['width']
    # a moving platform counts at the middle of its travel (Fountain's sides: sunk to 23.6)
    hs = sorted(p['height'] if not p.get('height_range') else sum(p['height_range']) / 2 for p in ps)
    outer = [max(abs(p['x0']), abs(p['x1'])) for p in ps]
    inner_gap = None
    if ps:
        xs = sorted((p['x0'], p['x1']) for p in ps)
        # the widest stretch of floor that no platform covers, and how far the outermost platform sits inside the ledge
        gaps, x = [], m['ledge_left'][0]
        for a, b in xs:
            if a > x: gaps.append(a - x)
            x = max(x, b)
        gaps.append(m['ledge_right'][0] - x)
        inner_gap = max(gaps)
    return dict(
        stage=s['title'], main_width=round(W, 2), ledge_to_side_blast=round(min(s['side_blast_from_ledge']), 2),
        top_above_floor=round(s['ceiling_above_floor'], 2), bottom_below_floor=round(s['bottom_below_floor'], 2),
        platforms=len(ps), lowest=round(hs[0], 2) if hs else None, highest=round(hs[-1], 2) if hs else None,
        tiers=len({round(h) for h in hs}), coverage=round(sum(p['width'] for p in ps) / W, 3),
        widest_open_floor=round(inner_gap if inner_gap is not None else W, 2),
        outer_platform_inside_ledge=round(m['ledge_right'][0] - max(outer), 2) if outer else None,
        undercut_10=m['undercut'][10][1], moving=sum(1 for p in ps if p['moves']),
        # the highest perch within 20 of a ledge (a moving platform at the top of its travel)
        highest_above_ledge_zone=round(max(((p['height_range'][1] if p.get('height_range') else p['height']) for p in ps
                                            if max(abs(p['x0']), abs(p['x1'])) > m['ledge_right'][0] - 20), default=0), 2))


def write():
    all_ = {n: starters.analyse(n) for n in starters.ORDER}
    for s in all_.values():
        starters.lab_merge(s)
    cands = {n: as_stage(n) for n in CANDIDATES}
    rows = [measure(all_[n]) for n in starters.ORDER] + [measure(cands[n]) for n in CANDIDATES]
    keys = list(rows[0].keys())
    res = os.path.join(HERE, 'research')
    with open(os.path.join(res, 'layouts.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(keys)
        for r in rows: w.writerow([r[k] if r[k] is not None else '' for k in keys])
    # the five starters' envelope (Stadium, now a counterpick, listed apart)
    five = [measure(all_[n]) for n in starters.ORDER if n != 'stadium']
    env = {k: [min(r[k] for r in five if isinstance(r[k], (int, float))), max(r[k] for r in five if isinstance(r[k], (int, float)))]
           for k in keys if k != 'stage' and any(isinstance(r[k], (int, float)) for r in five)}
    json.dump(dict(body=BODY, blast=BLAST, camera=CAMERA, candidates=CANDIDATES, measured=rows, starter_envelope=env,
                   outlines={n: cands[n]['outline'] for n in CANDIDATES}), open(os.path.join(res, 'layouts.json'), 'w'), indent=1)
    for n, c in CANDIDATES.items():
        near = all_[c['nearest']]
        starters.draw({c['nearest']: near}, os.path.join(res, f'layout_{n}'), only=[c['nearest']],
                      extra=[(c['title'], cands[n], '#1B5E20')], title=f"{c['title']} over {near['title']}", panels=False)
    starters.draw(all_, os.path.join(res, 'layouts_over_starters'),
                  extra=[(cands[n]['title'], cands[n], col) for n, col in zip(CANDIDATES, ('#1B5E20', '#8D6E00', '#5D4037'))],
                  title='The candidates (dashed) over the six starters')
    for r in rows:
        print({k: r[k] for k in keys})
    print('envelope', env)


if __name__ == '__main__':
    write()
