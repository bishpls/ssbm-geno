"""Starter lab: check the offline stage numbers (datkit stage-dump) against the engine, one starter per run.
Fox drops onto each platform's centre and onto the main stage and is logged standing (STATUS, GROUND: the floor line under
him); Falco falls past each ledge and is logged hanging on it; the stage's live collision, blast zones and camera range are
dumped at the start (every line) and then twice a second for a minute (floors), so moving platforms (Fountain of Dreams,
Randall) and Pokemon Stadium's first transformation show up as they happen.
    STAGE_LAB=battlefield .venv/bin/python tools/machinima/melee/build.py projects/geno/stage starter_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --logonly --until 'DIRECTOR END' --frames 5000 --quiet
    .venv/bin/python projects/geno/stage/director/starter_lab.py --report RUN [OUT.json]
Targets come from $MELEE_WORK/stage/dumps/<file>.json (projects/geno/stage/starters.py dump).
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import starters  # noqa: E402

FOX, FALCO = 0, 1
PORT = lambda tc: FALCO if tc['label'] == 'ledge_left' else FOX     # Falco hangs on the left ledge, Fox (last) on the right
TEST = 60           # frames per drop
SERIES = int(os.environ.get('STAGE_LAB_SERIES', 3600))   # frames of the over-time dump
EVERY = 30


def plan(name):
    st = starters.analyse(name)
    tests = []
    m = st['main']
    for p in st['platforms']:
        if p['label'] == 'randall':
            continue                                        # Randall circles under the stage: the series measures it
        x = (p['x0'] + p['x1']) / 2
        y = p['y_top'] + 30 if not p['moves'] else 90
        tests.append(dict(kind='platform', label=p['label'], x=round(x, 3), y=round(y, 3), expect_y=p['y'],
                          moves=p['moves'], lines=p['lines']))
    # the main stage: the middle of the widest stretch of floor no platform (moving ones at any height) covers
    cover = sorted([(p['x0'], p['x1']) for p in st['platforms'] if p['label'] != 'randall'])
    lo, hi = m['ledge_left'][0] + 4, m['ledge_right'][0] - 4
    gaps, x = [], lo
    for a, b in cover:
        if a > x: gaps.append((x, min(a, hi)))
        x = max(x, b)
    if x < hi: gaps.append((x, hi))
    g = max(gaps, key=lambda g: g[1] - g[0])
    x_main = round((g[0] + g[1]) / 2, 3)
    y_main = m['floor_y']
    for a_, b_, kind, dtp, ledge in st['outline']:                 # the floor's own height at that x
        if kind == 'floor' and not dtp and min(a_[0], b_[0]) <= x_main <= max(a_[0], b_[0]) and b_[0] != a_[0]:
            y_main = a_[1] + (b_[1] - a_[1]) * (x_main - a_[0]) / (b_[0] - a_[0])
    tests.append(dict(kind='main', label='main', x=x_main, y=40.0, expect_y=round(y_main, 4)))
    for side, (lx, ly) in (('left', m['ledge_left']), ('right', m['ledge_right'])):
        out = -1 if side == 'left' else 1
        tests.append(dict(kind='ledge', label=f'ledge_{side}', x=round(lx + out * 7.0, 3), y=round(ly + 8.0, 3), ledge=[lx, ly]))
    return st, tests


def build(out_c):
    from dsl import Film
    name = os.environ.get('STAGE_LAB', 'battlefield')
    st, tests = plan(name)
    n = 40 + TEST * len(tests) + SERIES + 20
    f = Film(len_s=n / 60.0)
    f.setup(players=[('fox', dict(x=-20, face=1)), ('falco', dict(x=20, face=-1))], stage=st['director_stage'], seed=1)
    f.grdump(5, every=True)
    t = 40
    for k, tc in enumerate(tests):
        port = PORT(tc)
        f.mark(t, k, tc['label'])
        # Fall (a fighter standing on a line is held to it through a setpos), then teleport above the target. Each fighter
        # hangs on a ledge once, as its last drop: a setpos from CliffWait leaves him on his old ledge, and Fall from
        # CliffWait (even after a reset) trips lbvector's position assert
        f.cue(t + 2, 'motion', port, 29)
        f.setpos(t + 2, port, tc['x'], tc['y'])
        if tc['kind'] == 'ledge':
            f.face(t, port, -1 if tc['x'] > 0 else 1)      # facing the stage: the catch box is on the facing side
        f.status(t + TEST - 2, port)
        f.grdump(t + TEST - 2)
        t += TEST
    # park the fighters on the main stage and watch the stage for a minute
    f.reset(t, FOX, -20, 1)
    f.reset(t, FALCO, 20, -1)
    for s in range(t + 2, t + SERIES, EVERY):
        f.grdump(s)
    f.cue(t + SERIES, 'end')
    f.emit(out_c)
    json.dump(dict(stage=name, tests=tests, start=40, test=TEST), open(os.path.splitext(out_c)[0] + '.plan.json', 'w'), indent=1)


def report(run, out=None):
    log = [l.split() for l in open(os.path.join(run, 'osreport.log'), errors='replace')]
    stage_lines = [l for l in log if l and l[0] == 'STAGE']
    lines, ground, status = {}, [], []
    for l in log:
        if not l:
            continue
        if l[0] == 'LINE' and len(l) >= 9:
            lines.setdefault(int(l[1]), []).append(dict(id=int(l[2]), flags=int(l[3], 16), lo=int(l[4], 16),
                                                        a=[float(l[5]), float(l[6])], b=[float(l[7]), float(l[8])]))
        elif l[0] == 'GROUND' and len(l) >= 8:
            ground.append(dict(s=int(l[1]), port=int(l[2]), x=float(l[3]), y=float(l[4]), air=int(l[5]), line=int(l[6]), motion=int(l[7]),
                               ledge=int(l[8]) if len(l) > 8 else -1))
        elif l[0] == 'STATUS' and len(l) >= 7:
            status.append(dict(s=int(l[1]), port=int(l[2]), x=float(l[4]), y=float(l[5]), motion=int(l[6])))
    s0 = stage_lines[0] if stage_lines else None
    res = dict(run=run, stage=None, blast=None, cam=None, tests=[], series={})
    if s0:
        i = s0.index('blast'); c = s0.index('cam'); o = s0.index('offset')
        res.update(grkind=int(s0[3]), stkind=int(s0[5]), blast=[float(v) for v in s0[i + 1:i + 5]],
                   cam=[float(v) for v in s0[c + 1:c + 5]], cam_offset=[float(v) for v in s0[o + 1:o + 3]])
    # the tests, from the plan beside the build (copied into the run by the caller) or re-planned
    plan_path = os.path.join(run, 'plan.json')
    pl = json.load(open(plan_path)) if os.path.exists(plan_path) else None
    if pl:
        res['stage'] = pl['stage']
        for k, tc in enumerate(pl['tests']):
            s_at = pl['start'] + pl['test'] * (k + 1) - 2          # the frame STATUS and the grdump log (script frames)
            port = PORT(tc)
            st = [x for x in status if x['port'] == port and x['s'] == s_at]
            gr = [x for x in ground if x['port'] == port and x['s'] == s_at]
            st, gr = (st[-1] if st else None), (gr[-1] if gr else None)
            row = dict(tc, status=st, ground=gr)
            if gr and gr['line'] >= 0 and gr['s'] in lines:
                ln = [x for x in lines[gr['s']] if x['id'] == gr['line']]
                row['line'] = ln[0] if ln else None
            if tc['kind'] in ('platform', 'main') and st:
                standing = st['motion'] == 14 and gr is not None and gr['air'] == 0
                if tc.get('moves'):                          # a moving platform: grounded on its line, wherever it is
                    row['ok'] = gr is not None and gr['air'] == 0 and gr['line'] in tc['lines']   # (landing lag counts)
                else:
                    row['ok'] = standing and abs(st['y'] - tc['expect_y']) < 0.05
                row['measured_y'] = st['y']
            if tc['kind'] == 'ledge' and st:
                # the corner held: the outer end of the ledge line (the engine's own ledge, not the hang offset)
                ln = [x for x in lines.get(gr['s'], []) if gr and x['id'] == gr['ledge']] if gr else []
                corner = None
                if ln:
                    a_, b_ = ln[0]['a'], ln[0]['b']
                    corner = min(a_, b_) if tc['x'] < 0 else max(a_, b_)
                row['ledge_line'] = gr['ledge'] if gr else None
                row['measured'] = corner
                row['hang'] = [st['x'], st['y']]
                row['ok'] = st['motion'] == 253 and corner is not None and abs(corner[0] - tc['ledge'][0]) < 0.01 and abs(corner[1] - tc['ledge'][1]) < 0.01
            res['tests'].append(row)
    # over time: every drop-through (platform) floor line's height, and the set of live floor lines
    series = {}
    for s, ls in sorted(lines.items()):
        for x in ls:
            live = x['flags'] & 0x10000 and not x['flags'] & 0x40000   # LINE_FLAG_ENABLED, not LINE_FLAG_HIDDEN
            if live and x['flags'] & 1 and x['lo'] & 0x100:          # a live floor, drop-through
                series.setdefault(x['id'], []).append([s, round(x['a'][0], 3), round(x['a'][1], 3), round(x['b'][0], 3), round(x['b'][1], 3)])
    res['series'] = {str(k): dict(n=len(v), y_min=min(min(r[2], r[4]) for r in v), y_max=max(max(r[2], r[4]) for r in v),
                                  x_min=min(min(r[1], r[3]) for r in v), x_max=max(max(r[1], r[3]) for r in v), first=v[0], last=v[-1])
                     for k, v in series.items()}
    res['series_raw'] = {str(k): v for k, v in series.items()}
    if lines:
        s_first = min(lines)
        res['live_at_start'] = sorted(x['id'] for x in lines[s_first] if x['flags'] & 0x10000 and not x['flags'] & 0x40000)
    if out:
        json.dump(res, open(out, 'w'), indent=1)
    for tr in res['tests']:
        print(tr['label'], tr.get('ok'), tr.get('measured_y', tr.get('measured')), 'expect', tr.get('expect_y', tr.get('ledge')),
              'line', (tr.get('line') or {}).get('id'))
    print('blast', res['blast'], 'cam', res['cam'], 'offset', res.get('cam_offset'))
    for k, v in res['series'].items():
        print('platform line', k, {kk: vv for kk, vv in v.items() if kk not in ('first', 'last')})
    return res


if __name__ == '__main__':
    if sys.argv[1] == '--report':
        report(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        build(sys.argv[1])
