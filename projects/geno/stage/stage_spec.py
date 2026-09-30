"""The Forest Maze stage spec: what datkit stage-build writes into GrFm.dat.
    .venv/bin/python projects/geno/stage/stage_spec.py [OUT.json] [--layout clearing]
From a layout in layouts.py (Michael's pick, 2026-09-29: A, Clearing) it lays out, in world units (stage scale 1):
  - the collision: vertices, lines in the engine's order (floors, ceilings, right walls, left walls), each with its
    prev/next links around the perimeter, surface kind, pass-through and ledge bits and material, in one line group;
    the winding the vanilla stages use (floors left to right, right walls down, ceilings right to left, left walls up);
    a side segment steeper than 45 degrees is a wall, a shallower one a ceiling;
  - the general points: spawns, respawns, item spawns, the camera range with its centre (148) and the blast zones;
  - the stage's music row (StKind 0x15, the Akaneia slot the decomp gives the stage);
  - the greybox model: map gobjs of flat-shaded boxes built from the same outline, so every top edge is its collision
    line (the play plane's front face is at z = +FRONT, the fighters' plane z = 0 runs through the top surfaces).
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layouts  # noqa: E402

ST_KIND = 0x15            # St_Kind_Akaneia, which maps to Gr_Kind_Unk26 (0x1A): the decomp's grforest.h
BGM = 0x64                # gr_forestmaze.hps (lbaudio_ax.c, non-matching), falling back to Battlefield's when absent
FRONT, BACK = 22.0, -30.0  # the play plane's depth: its front and back faces
CAP_T = 3.5               # the cap's thickness below its top surface
MATERIAL = {'floor': 'Grass', 'ledge': 'Grass', 'wall': 'Wood', 'ceiling': 'Wood', 'platform': 'Wood'}
MAT_ID = {'Basic': 0, 'Rock': 1, 'Grass': 2, 'Dirt': 3, 'Wood': 4}
SURF = {'floor': 1, 'ceiling': 2, 'right_wall': 4, 'left_wall': 8}
# greybox colours (sRGB): the stump's mossy top, its bark, the cap, the background
COL = {'top': (112, 150, 74), 'bark': (104, 76, 52), 'under': (78, 58, 42), 'cap': (178, 58, 44), 'cap_under': (226, 214, 188),
       'back': (46, 78, 58), 'trunk': (70, 60, 48), 'ground_back': (58, 72, 44)}


def collision(c):
    """-> vertices [[x, y]], lines [dict], group dict."""
    L, fy = layouts.BODY['ledge_x'], layouts.BODY['floor_y']
    prof = layouts.BODY['profile']
    right = [(L - i, fy - d) for i, d in prof]                 # ledge corner downward, then in
    left = [(-x, y) for x, y in right]
    ledge_len = 8.0
    # the perimeter, clockwise: floor left to right, down the right side, the underside right to left, up the left side
    ring = [(-L, fy), (-L + ledge_len, fy), (L - ledge_len, fy)] + right + [p for p in reversed(left)][:-1]
    V = [list(map(float, p)) for p in ring]
    n = len(ring)
    segs = []
    for k in range(n):
        a, b = ring[k], ring[(k + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        if abs(dy) < 1e-9 and dx > 0: kind = 'floor'
        elif abs(dy) > abs(dx): kind = 'right_wall' if dy < 0 else 'left_wall'
        else: kind = 'ceiling' if dx < 0 else 'floor'
        ledge = kind == 'floor' and (a[0] == -L or b[0] == L)
        segs.append(dict(v=[k, (k + 1) % n], kind=kind, ledge=ledge, drop=False))
    for k, s in enumerate(segs):
        s['ring_prev'], s['ring_next'] = (k - 1) % n, (k + 1) % n
    # platforms: their own vertices, no links
    for p in c['platforms']:
        i = len(V); V += [[p['x0'], p['y']], [p['x1'], p['y']]]
        segs.append(dict(v=[i, i + 1], kind='floor', ledge=False, drop=True, ring_prev=None, ring_next=None))
    # the engine's order: all floors, ceilings, right walls, left walls (each range contiguous); links remapped
    order = [k for kind in ('floor', 'ceiling', 'right_wall', 'left_wall') for k, s in enumerate(segs) if s['kind'] == kind]
    new = {old: i for i, old in enumerate(order)}
    lines = []
    for old in order:
        s = segs[old]
        mat = 'platform' if s['drop'] else ('ledge' if s['ledge'] else ('floor' if s['kind'] == 'floor' else
                                                                          'ceiling' if s['kind'] == 'ceiling' else 'wall'))
        lines.append(dict(v=s['v'], kind=s['kind'], surface=SURF[s['kind']], drop=s['drop'], ledge=s['ledge'],
                          prev=new[s['ring_prev']] if s['ring_prev'] is not None else -1,
                          next=new[s['ring_next']] if s['ring_next'] is not None else -1,
                          material=MAT_ID[MATERIAL[mat]]))
    rng = {}
    for kind in ('floor', 'ceiling', 'right_wall', 'left_wall'):
        idx = [i for i, l in enumerate(lines) if l['kind'] == kind]
        rng[kind] = [idx[0] if idx else 0, len(idx)]
    xs, ys = [v[0] for v in V], [v[1] for v in V]
    margin = 8.0                                             # Final Destination's bounding margin
    group = dict(ranges=rng, bounds=[min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin],
                 vertices=[0, len(V)])
    return V, lines, group


def box(x0, x1, y0, y1, z0, z1, cols, skip=()):
    """An axis-aligned box as triangles with flat normals: faces top, bottom, front (+z), back, left, right."""
    P = {'top': [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)],
         'bottom': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
         'front': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
         'back': [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
         'left': [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
         'right': [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)]}
    N = {'top': (0, 1, 0), 'bottom': (0, -1, 0), 'front': (0, 0, 1), 'back': (0, 0, -1), 'left': (-1, 0, 0), 'right': (1, 0, 0)}
    out = []
    for f, q in P.items():
        if f in skip: continue
        col = cols.get(f, cols.get('side'))
        out.append(dict(tris=[[q[0], q[1], q[2]], [q[0], q[2], q[3]]], normal=N[f], color=col))
    return out


def prism(outline, z0, z1, cols):
    """The stage body: the collision outline (a clockwise ring in x, y) extruded from z0 to z1. Top faces from the floor
    lines, side faces from each segment, and the front and back caps triangulated as a fan (the outline is convex)."""
    faces = []
    n = len(outline)
    for k in range(n):
        (ax, ay), (bx, by) = outline[k], outline[(k + 1) % n]
        dx, dy = bx - ax, by - ay
        nx, ny = -dy, dx                                      # clockwise ring (y up): the outward normal is (-dy, dx)
        ln = math.hypot(nx, ny) or 1
        nrm = (nx / ln, ny / ln, 0)
        q = [(ax, ay, z1), (bx, by, z1), (bx, by, z0), (ax, ay, z0)]
        col = cols['top'] if ny / ln > 0.7 else (cols['under'] if ny / ln < -0.7 else cols['bark'])
        faces.append(dict(tris=[[q[0], q[2], q[1]], [q[0], q[3], q[2]]], normal=nrm, color=col))
    cx = sum(p[0] for p in outline) / n; cy = sum(p[1] for p in outline) / n
    for z, nz in ((z1, 1), (z0, -1)):
        for k in range(n):
            a, b = outline[k], outline[(k + 1) % n]
            t = [(cx, cy, z), (a[0], a[1], z), (b[0], b[1], z)]
            if nz > 0: t = [t[0], t[2], t[1]]               # front face counter-clockwise seen from +z
            faces.append(dict(tris=[t], normal=(0, 0, nz), color=cols['bark']))
    return faces


def spec(name='clearing'):
    c = layouts.CANDIDATES[name]
    V, lines, group = collision(c)
    L = layouts.BODY['ledge_x']
    ring = [tuple(v) for v in V[:group['vertices'][1] - 2 * len(c['platforms'])]]
    b, cam = layouts.BLAST, layouts.CAMERA
    pts = [dict(type=148, name='DeltaAngleCamera', x=cam['centre'][0], y=cam['centre'][1]),
           dict(type=149, name='TopLeftBoundary', x=cam['left'], y=cam['top']),
           dict(type=150, name='BottomRightBoundary', x=cam['right'], y=cam['bottom']),
           dict(type=151, name='TopLeftBlastZone', x=b['left'], y=b['top']),
           dict(type=152, name='BottomRightBlastZone', x=b['right'], y=b['bottom'])]
    for i, (x, y) in enumerate(c['spawns']):
        pts.append(dict(type=i, name=f'Player{i + 1}Spawn', x=x, y=y + 10.0))      # 10 above the surface, as FD's
    for i, (x, y) in enumerate(c['respawns']):
        pts.append(dict(type=4 + i, name=f'Player{i + 1}Respawn', x=x, y=y))
    cap = c['platforms'][0]
    items = [(0, cap['y'] + 10), (-45, 10), (45, 10), (0, 70), (-55, 30), (55, 30), (-25, 60), (25, 60)]
    for i, (x, y) in enumerate(items):
        pts.append(dict(type=127 + i, name=f'ItemSpawn{i + 1}', x=x, y=y))
    # the greybox model
    stage = prism(ring, BACK, FRONT, COL)
    for p in c['platforms']:
        stage += box(p['x0'], p['x1'], p['y'] - CAP_T, p['y'], -14.0, 14.0,
                     dict(top=COL['cap'], bottom=COL['cap_under'], side=COL['cap']))
    back = box(-420, 420, -260, 320, -260, -250, dict(front=COL['back']), skip=('top', 'bottom', 'back', 'left', 'right'))
    back += box(-420, 420, -60, -40, -250, -60, dict(top=COL['ground_back'], side=COL['ground_back']), skip=('bottom', 'back'))
    for x, w, z in ((-150, 26, -150), (-95, 18, -110), (95, 20, -120), (160, 30, -170), (0, 34, -200)):
        back += box(x - w / 2, x + w / 2, -60, 320, z - w / 2, z + w / 2, dict(side=COL['trunk']), skip=('top', 'bottom'))
    return dict(
        name='Forest Maze', file='GrFm.dat', layout=name, st_kind=ST_KIND, scale=1.0,
        collision=dict(vertices=V, lines=lines, group=group), points=pts,
        stage_param=dict(st_kind=ST_KIND, bgm=BGM, bgm_alt=-1, bgm_sd=BGM, bgm_sd_alt=-1, behaviour=0, alt_chance=0),
        gobjs=[dict(kind='points'), dict(kind='stage', faces=stage, lit=True), dict(kind='back', faces=back, lit=True,
               fog=dict(start=180.0, end=520.0, color=[64, 92, 70]))],
    )


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else os.path.expanduser(
        os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'stage', 'forest_maze.spec.json'))
    lay = sys.argv[sys.argv.index('--layout') + 1] if '--layout' in sys.argv else 'clearing'
    s = spec(lay)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(s, open(out, 'w'), indent=1)
    col = s['collision']
    print(f"{out}: {len(col['vertices'])} vertices, {len(col['lines'])} lines, {len(s['points'])} points, "
          f"{sum(len(f['tris']) for g in s['gobjs'] for f in g.get('faces', []))} triangles")
    for i, l in enumerate(col['lines']):
        print(i, l['kind'], col['vertices'][l['v'][0]], col['vertices'][l['v'][1]], 'prev', l['prev'], 'next', l['next'],
              'drop' if l['drop'] else '', 'ledge' if l['ledge'] else '')
