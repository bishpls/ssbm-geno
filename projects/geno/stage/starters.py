"""The six common starters, measured from the disc: main stage, ledges, platforms, blast zones, camera range and spawns.
    .venv/bin/python projects/geno/stage/starters.py dump        # datkit stage-dump of each into $MELEE_WORK/stage/dumps
    .venv/bin/python projects/geno/stage/starters.py write       # research/starters.{json,md} + the overlay diagrams
Numbers are world units (the engine's: Final Destination's ledges at x = +-85.57, the floor at y = 0), in world space as
the engine computes them at load (stage scale applied; joint-bound collision transformed; see datkit StageKit.cs).
In-game checks (director/starter_lab.py) are merged in when $MELEE_WORK/stage/lab/<stage>.json exists.
"""
import json, math, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
WORK = os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work'))
DISC = os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc'))
DUMPS = os.path.join(WORK, 'stage', 'dumps')
LAB = os.path.join(WORK, 'stage', 'lab')
RESEARCH = os.path.join(HERE, 'research')

# name: (file, title, director StKind name, options)
#   bind: a stage's code-side collision bindings (StageData.joints in the DOL), C:G:J (group, gobj, joint)
#   groups: the collision groups live in the layout measured (Pokemon Stadium's neutral form; the rest are its transformations)
#   code_moved: groups the stage's code moves (so the file's rest pose is not where they play)
STAGES = {
    'final_destination': ('GrNLa', 'Final Destination', 'final_destination', {}),
    'battlefield': ('GrNBa', 'Battlefield', 'battlefield', {}),
    'yoshis_story': ('GrSt', "Yoshi's Story", 'yoshis_story', {'code_moved': [0]}),
    'dream_land': ('GrOp', 'Dream Land', 'dream_land', {}),
    'fountain': ('GrIz', 'Fountain of Dreams', 'fountain', {'bind': '0:3:1,1:3:2,2:3:3', 'code_moved': [0, 1]}),
    'stadium': ('GrPs', 'Pokémon Stadium', 'stadium', {'groups': [4, 6]}),
}
ORDER = ['final_destination', 'battlefield', 'yoshis_story', 'dream_land', 'fountain', 'stadium']
SHORT = {'final_destination': 'FD', 'battlefield': 'BF', 'yoshis_story': 'YS', 'dream_land': 'DL', 'fountain': 'FoD', 'stadium': 'PS'}


def dump():
    os.makedirs(DUMPS, exist_ok=True)
    for name in ORDER:
        f, _, _, opt = STAGES[name]
        cmd = [os.path.join(ROOT, 'tools/machinima/melee/datkit.sh'), 'stage-dump', os.path.join(DISC, 'files', f + '.dat'),
               os.path.join(DUMPS, f + '.json'), '--joints']
        if opt.get('bind'): cmd += ['--bind', opt['bind']]
        subprocess.run(cmd, check=True)
        print('dumped', f)


def load(name):
    # STAGE_LAB_DUMP: measure a patched file instead (the stage-patch probe)
    alt = os.environ.get('STAGE_LAB_DUMP')
    return json.load(open(alt or os.path.join(DUMPS, STAGES[name][0] + '.json')))


def wall_x_at(lines, verts, side, y):
    """The stage's outer x at height y on one side: the outermost wall/ceiling/floor crossing at that height."""
    xs = []
    for l in lines:
        a, b = verts[l['v'][0]], verts[l['v'][1]]
        (x0, y0), (x1, y1) = a, b
        if min(y0, y1) - 1e-6 <= y <= max(y0, y1) + 1e-6 and abs(y1 - y0) > 1e-6:
            xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    if not xs:
        return None
    return min(xs) if side < 0 else max(xs)


def analyse(name):
    fname, title, dstage, opt = STAGES[name]
    d = load(name)
    c = d['collision']
    verts = [v['frame0'] for v in c['vertices']]
    groups = opt.get('groups')
    lines = [l for l in c['lines'] if groups is None or l['group'] in groups]
    floors = [l for l in lines if l['kind'] == 'floor']
    dt = [l for l in floors if l['drop_through']]
    solid = [l for l in floors if not l['drop_through']]
    moved = set(opt.get('code_moved', []))
    # platforms: drop-through floor lines chained end to end
    byi = {l['i']: l for l in dt}
    seen, plats = set(), []
    for l in sorted(dt, key=lambda l: verts[l['v'][0]][0]):
        if l['i'] in seen: continue
        chain, cur = [], l
        while cur is not None and cur['i'] not in seen:
            seen.add(cur['i']); chain.append(cur)
            cur = byi.get(cur['next'])
        pts = [verts[v] for x in chain for v in x['v']]
        x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
        ys = [p[1] for p in pts]
        grp = chain[0]['group']
        mv = grp in moved or any(g['i'] == grp and g['joint_animated'] for g in c['groups'])
        plats.append(dict(x0=round(x0, 4), x1=round(x1, 4), width=round(x1 - x0, 4), y=round(min(ys), 4), y_top=round(max(ys), 4),
                          lines=[x['i'] for x in chain], group=grp, moves=mv, material=chain[0]['material']))
    # main stage
    ledge_lines = [l for l in solid if l['ledge']]
    lv = [verts[v] for l in ledge_lines for v in l['v']]
    ll = min(lv, key=lambda p: p[0]); lr = max(lv, key=lambda p: p[0])
    centre = [l for l in solid if min(verts[l['v'][0]][0], verts[l['v'][1]][0]) <= 0 <= max(verts[l['v'][0]][0], verts[l['v'][1]][0])]
    floor_y = round(min(verts[centre[0]['v'][0]][1], verts[centre[0]['v'][1]][1]) if centre else 0.0, 4)
    for p in plats:
        p['height'] = round(p['y'] - floor_y, 4)
    # labels by position
    stat = [p for p in plats]
    if stat:
        ytop = max(p['y'] for p in stat)
        for p in plats:
            mid = (p['x0'] + p['x1']) / 2
            if len(plats) == 1: p['label'] = 'platform'
            elif abs(mid) < 5 and p['y'] == ytop and len(plats) >= 3: p['label'] = 'top'
            elif abs(mid) < 5 and len(plats) >= 3: p['label'] = 'centre'
            elif name == 'yoshis_story' and p['group'] == 0: p['label'] = 'randall'
            else: p['label'] = 'left' if mid < 0 else 'right'
    # under-ledge profile: how far in the stage's side is at depths below each ledge (the lip a recovery meets)
    body = [l for l in lines if l['group'] in {x['group'] for x in ledge_lines}]
    prof = {}
    for depth in (2, 5, 10, 20, 30, 40):
        L = wall_x_at(body, verts, -1, ll[1] - depth); R = wall_x_at(body, verts, 1, lr[1] - depth)
        prof[depth] = [None if L is None else round(L - ll[0], 3), None if R is None else round(lr[0] - R, 3)]
    ys_body = [verts[v][1] for l in body for v in l['v']]
    pts = {p['type']: p for p in d['points']}
    P = lambda t: pts[t]['frame0'][:2] if t in pts and pts[t]['frame0'] else None
    blast = dict(left=P(151)[0], top=P(151)[1], right=P(152)[0], bottom=P(152)[1])
    cam = dict(left=P(149)[0], top=P(149)[1], right=P(150)[0], bottom=P(150)[1], centre=P(148))
    spawns = [P(t) for t in range(4) if P(t)]
    respawns = [P(t) for t in range(4, 8) if P(t)]
    items = [P(t) for t in range(127, 147) if P(t)]
    gp = d['ground_param']
    vs_row = [s for s in gp['stage_params'] if s['stkind'] < 0x21]
    res = dict(
        name=name, title=title, file=fname + '.dat', director_stage=dstage, scale=d['scale'],
        main=dict(ledge_left=[round(ll[0], 4), round(ll[1], 4)], ledge_right=[round(lr[0], 4), round(lr[1], 4)],
                  width=round(lr[0] - ll[0], 4), floor_y=floor_y, depth=round(floor_y - min(ys_body), 3),
                  materials=sorted({l['material'] for l in solid}), undercut=prof,
                  slanted_edges=any(abs(verts[l['v'][0]][1] - verts[l['v'][1]][1]) > 0.01 for l in ledge_lines)),
        platforms=sorted(plats, key=lambda p: (p['x0'] + p['x1']) / 2),
        blast=blast, camera=cam, spawns=spawns, respawns=respawns, item_spawns=len(items),
        ceiling_above_floor=round(blast['top'] - floor_y, 3), bottom_below_floor=round(floor_y - blast['bottom'], 3),
        side_blast_from_ledge=[round(ll[0] - blast['left'], 3), round(blast['right'] - lr[0], 3)],
        music=dict(vs=vs_row), gobjs=len(d['gobjs']), dobjs=sum(g['dobjs'] for g in d['gobjs']),
        textures=sum(g['textures'] for g in d['gobjs']), animated_gobjs=sum(1 for g in d['gobjs'] if g['animated_joints']),
        lines=len(c['lines']), vertices=len(c['vertices']), groups=len(c['groups']), bytes=d['bytes'],
        outline=[[verts[l['v'][0]], verts[l['v'][1]], l['kind'], l['drop_through'], l['ledge']] for l in lines],
    )
    lab = os.path.join(LAB, name + '.json')
    if os.path.exists(lab):
        res['lab'] = json.load(open(lab))
    return res


def lab_merge(st):
    """Fold the in-game numbers in: checks for each drop and ledge, and moving platforms' measured ranges."""
    lab = st.get('lab')
    if not lab:
        return
    st['verified'] = dict(blast=lab.get('blast'), camera=lab.get('cam'), tests=[
        dict(label=t['label'], ok=t.get('ok'), measured=t.get('measured_y', t.get('measured')),
             expected=t.get('expect_y', t.get('ledge')), line=(t.get('line') or {}).get('id')) for t in lab.get('tests', [])])
    # the camera range the engine uses: from the file's points 148-150 when all three exist, else its default
    # (ground.c Ground_801C39C0 "use dummy CamRange": Pokemon Stadium has no 148)
    if lab.get('cam'):
        l, r, t, b = lab['cam']
        live = dict(left=l, right=r, top=t, bottom=b, centre=lab.get('cam_offset'))
        if any(abs(live[k] - st['camera'][k]) > 0.01 for k in ('left', 'right', 'top', 'bottom')):
            st['camera_file'] = st['camera']
        st['camera'] = live
    if lab.get('blast'):
        l, r, t, b = lab['blast']
        st['blast_checked'] = all(abs(x - y) < 0.01 for x, y in zip((l, r, t, b), (st['blast']['left'], st['blast']['right'], st['blast']['top'], st['blast']['bottom'])))
    st['live_at_start'] = lab.get('live_at_start')
    ser = lab.get('series', {})
    for p in st['platforms']:
        # the live line ids for this platform: match by the file's line indices (the engine keeps the file's numbering)
        for i in p['lines']:
            s = ser.get(str(i))
            if s:
                p['live'] = dict(y_min=round(s['y_min'] - st['main']['floor_y'], 3), y_max=round(s['y_max'] - st['main']['floor_y'], 3),
                                 x_min=s['x_min'], x_max=s['x_max'], samples=s['n'])
                if p['moves']:
                    p['height_range'] = [p['live']['y_min'], p['live']['y_max']]
                    p['x_range'] = [s['x_min'], s['x_max']]
                break


# ---------------------------------------------------------------- output
COLORS = {'final_destination': '#4C6EF5', 'battlefield': '#E8590C', 'yoshis_story': '#2F9E44', 'dream_land': '#AE3EC9',
          'fountain': '#1098AD', 'stadium': '#C92A2A'}


def table_md(all_):
    L = ['| | ' + ' | '.join(SHORT[n] for n in ORDER) + ' |', '|---|' + '---:|' * len(ORDER)]
    def row(label, f):
        L.append(f'| {label} | ' + ' | '.join(f(all_[n]) for n in ORDER) + ' |')
    fmt = lambda v: '—' if v is None else (f'{v:.2f}'.rstrip('0').rstrip('.') if isinstance(v, float) else str(v))
    row('stage scale', lambda s: fmt(s['scale']))
    row('ledges x', lambda s: f"±{fmt(s['main']['ledge_right'][0])}" if abs(s['main']['ledge_left'][0] + s['main']['ledge_right'][0]) < 0.01 else f"{fmt(s['main']['ledge_left'][0])} / {fmt(s['main']['ledge_right'][0])}")
    row('ledge y (floor 0)', lambda s: fmt(s['main']['ledge_right'][1] - s['main']['floor_y']))
    row('main width', lambda s: fmt(s['main']['width']))
    row('platforms', lambda s: str(len([p for p in s['platforms'] if p['label'] != 'randall'])) + (' + Randall' if any(p['label'] == 'randall' for p in s['platforms']) else ''))
    row('side plat. height', lambda s: ' / '.join(sorted({plat_h(p) for p in s['platforms'] if p['label'] in ('left', 'right')})) or '—')
    row('side plat. x (inner–outer)', lambda s: ' / '.join(f"{fmt(abs(p['x0'] if p['x0'] > 0 else p['x1']))}–{fmt(abs(p['x1'] if p['x0'] > 0 else p['x0']))}" for p in s['platforms'] if p['label'] == 'right') or '—')
    row('side plat. width', lambda s: ' / '.join(sorted({fmt(p['width']) for p in s['platforms'] if p['label'] in ('left', 'right')})) or '—')
    row('top plat. height', lambda s: ' / '.join(plat_h(p) for p in s['platforms'] if p['label'] == 'top') or '—')
    row('top plat. width', lambda s: ' / '.join(fmt(p['width']) for p in s['platforms'] if p['label'] == 'top') or '—')
    row('blast left / right', lambda s: f"{fmt(s['blast']['left'])} / {fmt(s['blast']['right'])}")
    row('blast top', lambda s: fmt(s['blast']['top']))
    row('blast bottom', lambda s: fmt(s['blast']['bottom']))
    row('ledge → side blast', lambda s: ' / '.join(sorted({fmt(v) for v in s['side_blast_from_ledge']})))
    row('camera x', lambda s: f"{fmt(s['camera']['left'])} / {fmt(s['camera']['right'])}")
    row('camera y', lambda s: f"{fmt(s['camera']['bottom'])} / {fmt(s['camera']['top'])}")
    row('undercut 10 below ledge', lambda s: fmt(s['main']['undercut'][10][1]))
    row('stage depth below floor', lambda s: fmt(s['main']['depth']))
    return '\n'.join(L)


def plat_h(p):
    f = lambda v: f'{v:.2f}'.rstrip('0').rstrip('.')
    if p.get('height_range'):
        lo, hi = p['height_range']
        return (f"sinks–{f(hi)} (moves)" if lo < 0 else f"{f(lo)}–{f(hi)} (moves)")
    if p['moves']:
        return f"{f(p['height'])} (moves)"
    if abs(p['y_top'] - p['y']) > 0.05:
        return f"{f(p['height'])}–{f(p['height'] + p['y_top'] - p['y'])}"
    return f(p['height'])


def draw(all_, out_base, overlay=True, extra=None, only=None, title=None, panels=True):
    """Side views at one scale: the overlay (all together) and small multiples. extra: [(label, stage dict, colour)] drawn
    on top (the candidates). Writes OUT.svg and OUT.png."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams['svg.fonttype'] = 'none'          # text stays text: small, diffable SVGs
    names = only or ORDER
    items = [(all_[n]['title'], all_[n], COLORS[n]) for n in names] + (extra or [])

    def outline(ax, s, col, lw=1.6, alpha=1.0, blast=False, label=None, dashes=None):
        first = True
        for a, b, kind, dtp, ledge in s['outline']:
            if dtp:
                ax.plot([a[0], b[0]], [a[1], b[1]], color=col, lw=lw + 1.4, alpha=alpha, solid_capstyle='butt',
                        label=label if first else None, **({'dashes': dashes} if dashes else {}))
            else:
                ax.plot([a[0], b[0]], [a[1], b[1]], color=col, lw=lw, alpha=alpha, label=label if first else None,
                        **({'dashes': dashes} if dashes else {}))
            first = False
        for p in s['platforms']:
            if p.get('height_range'):
                lo, hi = p['height_range']
                xs = p.get('x_range') or [p['x0'], p['x1']]
                # Randall travels beside both ledges (its x range spans the stage): a box on each side
                spots = [xs[0], xs[1] - p['width']] if xs[1] - xs[0] > 2 * p['width'] + 1 else [min(xs[0], p['x0'])]
                for x0 in spots:
                    ax.add_patch(matplotlib.patches.Rectangle((x0, s['main']['floor_y'] + lo), p['width'], hi - lo,
                                                              color=col, alpha=0.14 * alpha, lw=0))
        for side in ('ledge_left', 'ledge_right'):
            x, y = s['main'][side]
            ax.plot([x], [y], 'o', color=col, ms=4, alpha=alpha)
        if blast:
            b = s['blast']
            ax.plot([b['left'], b['right'], b['right'], b['left'], b['left']], [b['bottom'], b['bottom'], b['top'], b['top'], b['bottom']],
                    color=col, lw=1.0, alpha=0.8 * alpha, dashes=(4, 3))

    # the overlay: stages, then the blast zones
    fig, axes = plt.subplots(1, 2, figsize=(18, 7.5), gridspec_kw=dict(width_ratios=[1.25, 1]))
    ax = axes[0]
    for lab, s, col in items:
        outline(ax, s, col, label=lab, dashes=(5, 2) if s.get('candidate') else None)
    ax.set_xlim(-110, 110); ax.set_ylim(-70, 75); ax.set_aspect('equal'); ax.grid(alpha=0.25)
    ax.axhline(0, color='#888', lw=0.6)
    ax.set_title((title or 'The six starters overlaid') + ' — stage and platforms (thick = pass-through, dots = ledges)', fontsize=11)
    ax.legend(loc='lower center', fontsize=9, ncol=3, frameon=False)
    ax2 = axes[1]
    for lab, s, col in items:
        outline(ax2, s, col, lw=1.0, blast=True, dashes=(5, 2) if s.get('candidate') else None)
    ax2.set_xlim(-270, 270); ax2.set_ylim(-160, 265); ax2.set_aspect('equal'); ax2.grid(alpha=0.25)
    ax2.set_title('Blast zones (dashed) at the same scale', fontsize=11)
    for a in axes:
        a.set_xlabel('x (world units)'); a.set_ylabel('y')
    fig.tight_layout()
    fig.savefig(out_base + '.svg'); fig.savefig(out_base + '.png', dpi=110)
    plt.close(fig)
    if not panels:
        return
    # small multiples
    n = len(items); cols = 3; rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(18, 4.3 * rows))
    for k, (lab, s, col) in enumerate(items):
        ax = axes.flat[k]
        outline(ax, s, col)
        for sp in s['spawns']:
            ax.plot([sp[0]], [sp[1]], 'v', color='#555', ms=5)
        for p in s['platforms']:
            if p['label'] == 'randall':
                xs = p.get('x_range') or [p['x0'], p['x1']]
                ax.text(xs[0] + p['width'] / 2, p['y'] - 7, 'Randall', ha='center', fontsize=8, color=col)
                continue
            top = p['y_top'] if not p.get('height_range') else s['main']['floor_y'] + p['height_range'][1]
            ax.text((p['x0'] + p['x1']) / 2, top + 2.5, plat_h(p), ha='center', fontsize=8, color=col)
        m = s['main']
        ax.text(0, -12, f"ledges ±{abs(m['ledge_right'][0]):.1f}" if abs(m['ledge_left'][0] + m['ledge_right'][0]) < 0.01 else f"ledges {m['ledge_left'][0]:.1f} / {m['ledge_right'][0]:.1f}", ha='center', fontsize=9, color=col)
        b = s['blast']
        ax.text(0, -60, f"blast {b['left']:.0f} / {b['right']:.0f} / top {b['top']:.0f} / bottom {b['bottom']:.0f}", ha='center', fontsize=8, color='#555')
        ax.set_xlim(-110, 110); ax.set_ylim(-68, 72); ax.set_aspect('equal'); ax.grid(alpha=0.25); ax.axhline(0, color='#888', lw=0.6)
        ax.set_title(lab, fontsize=11, color=col)
    for k in range(n, rows * cols):
        axes.flat[k].axis('off')
    fig.tight_layout()
    fig.savefig(out_base + '_panels.svg'); fig.savefig(out_base + '_panels.png', dpi=100)
    plt.close(fig)


HEAD = """# The six starters, measured

Generated by `projects/geno/stage/starters.py write` (do not edit by hand). For the Forest Maze stage (DESIGN.md).

- **From the disc:** `datkit stage-dump` reads each `Gr*.dat` the way the engine loads it:
  - the stage scale is applied;
  - collision bound to a joint is transformed by it (Fountain's side platforms by the stage code's own binding table);
  - joints are counted the engine's way.
  Units are the engine's world units: Final Destination's ledges at ±85.57, the floor at 0. Heights are measured from
  the main floor at the stage's centre.
- **In game:** `director/starter_lab.py` builds a match on each stage and checks it (`run_starters.sh`):
  - Fox drops onto every platform and the main stage, and is logged standing (the floor line under him);
  - Falco and Fox hang on the left and right ledges, logged with the ledge line the engine holds;
  - the director's `grdump` cue logs the live collision, blast zones and camera range at the start, then twice a second
    for a minute (three for Fountain of Dreams).
  **All 32 checks pass**, and the live blast zones equal the file's on all six. The camera range differs on one stage
  (Pokémon Stadium, below).
- **Pokémon Stadium** is measured in its neutral form: collision groups 4 and 6, the ones live at the start; its four
  transformations are other groups in the same file.
- **Moving platforms:**
  - Fountain of Dreams' side platforms sink below the floor and rise to 22.1-23.6 in three minutes of logging; they move
    independently. The top platform is static.
  - Randall rises from 33.3 to 13.7 below the floor beside each ledge in turn.

The diagrams (our own drawings from these numbers) are `starters_overlay.svg` (all six overlaid, and their blast zones at
one scale) and `starters_overlay_panels.svg` (one panel each, with spawns). The data is `starters.json`.
"""


def write():
    os.makedirs(RESEARCH, exist_ok=True)
    all_ = {n: analyse(n) for n in ORDER}
    for s in all_.values():
        lab_merge(s)
    js = {n: {k: v for k, v in s.items() if k not in ('outline', 'lab')} for n, s in all_.items()}
    json.dump(js, open(os.path.join(RESEARCH, 'starters.json'), 'w'), indent=1)
    draw(all_, os.path.join(RESEARCH, 'starters_overlay'))
    md = HEAD
    md += '\n## Headline table\n\n' + table_md(all_) + '\n'
    md += '\n## Per stage\n'
    for n in ORDER:
        s = all_[n]
        m = s['main']
        md += f"\n### {s['title']} (`{s['file']}`, stage scale {s['scale']})\n\n"
        md += f"- Main stage: ledges at ({m['ledge_left'][0]}, {m['ledge_left'][1]}) and ({m['ledge_right'][0]}, {m['ledge_right'][1]}), width {m['width']}; floor at y = {m['floor_y']}"
        md += f"; surface {', '.join(m['materials'])}{'; slanted edges' if m['slanted_edges'] else ''}.\n"
        md += f"- Under the ledges, the side's inset (units in from the ledge) at 5 / 10 / 20 / 30 below: " + \
              ' / '.join(str(m['undercut'][d][1]) for d in (5, 10, 20, 30)) + f"; the stage body reaches {m['depth']} below the floor.\n"
        for p in s['platforms']:
            md += f"- Platform `{p['label']}`: x {p['x0']} to {p['x1']} (width {p['width']}), height {plat_h(p)} above the floor"
            md += f"{', moves' if p['moves'] else ', static'}; {p['material']}.\n"
        b, c = s['blast'], s['camera']
        md += f"- Blast zones: left {b['left']}, right {b['right']}, top {b['top']}, bottom {b['bottom']} (ceiling {s['ceiling_above_floor']} above the floor, bottom {s['bottom_below_floor']} below; side zones {s['side_blast_from_ledge'][0]} / {s['side_blast_from_ledge'][1]} past the ledges).\n"
        md += f"- Camera range (in game): x {c['left']} to {c['right']}, y {c['bottom']} to {c['top']}, centred on {c['centre']}."
        if s.get('camera_file'):
            cf = s['camera_file']
            md += f" The file's points say x {cf['left']} to {cf['right']}, y {cf['bottom']} to {cf['top']}, but it has no camera-centre point (148), so the engine uses its default range (`Ground_801C39C0`: \"use dummy CamRange\")."
        md += '\n'
        md += f"- Spawns: {', '.join(f'({p[0]}, {p[1]})' for p in s['spawns'])}; respawns: {', '.join(f'({p[0]}, {p[1]})' for p in s['respawns'])}; {s['item_spawns']} item spawn points.\n"
        md += f"- File: {s['bytes']} bytes, {s['gobjs']} map gobjs ({s['animated_gobjs']} animated), {s['dobjs']} meshes, {s['textures']} textures; collision {s['vertices']} vertices, {s['lines']} lines in {s['groups']} groups.\n"
        v = s.get('verified')
        if v:
            ok = [t for t in v['tests'] if t['ok']]
            md += f"- **In game** (`starter_lab`): {len(ok)}/{len(v['tests'])} checks pass: " + '; '.join(
                f"{t['label']} {'ok' if t['ok'] else 'FAIL'} {t['measured']}" for t in v['tests']) + '.'
            if v['blast']:
                md += f" Live blast zones {v['blast']}, camera {v['camera']}."
            md += '\n'
    open(os.path.join(RESEARCH, 'starters.md'), 'w').write(md)
    print(table_md(all_))
    return all_


if __name__ == '__main__':
    {'dump': dump, 'write': write}[sys.argv[1]]()
