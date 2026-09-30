"""Geno's normals against the measured cast: for every move type, where he sits on each axis that balances a normal.
Input: `datkit movedata` output per fighter (MOVEDATA dir, one PlXx code per .jsonl) and research/cast_attributes.csv.
    .venv/bin/python projects/geno/director/labs/cast_moves.py ~/games/melee/work/movedata [OUT.md]
Reach is measured the way the game plays the move: hitboxes placed by the fighter's own animation at each active frame
(lunges and stretched limbs included), in world units from the fighter's position, times ModelScale. Disjoint is how far
the hit reaches past the fighter's own hurtboxes in the move's direction (positive: the hit is out beyond the body);
hurtboxes the move script makes invincible or intangible on that frame don't count.
"""
import csv, json, os, statistics as st, sys

NAMES = {'Mr': 'Mario', 'Fx': 'Fox', 'Ca': 'Falcon', 'Dk': 'DK', 'Kb': 'Kirby', 'Kp': 'Bowser', 'Lk': 'Link', 'Sk': 'Sheik',
         'Ns': 'Ness', 'Pe': 'Peach', 'Pp': 'ICs', 'Pk': 'Pikachu', 'Ss': 'Samus', 'Ys': 'Yoshi', 'Pr': 'Puff', 'Mt': 'Mewtwo',
         'Lg': 'Luigi', 'Ms': 'Marth', 'Zd': 'Zelda', 'Cl': 'YLink', 'Dr': 'Doc', 'Fc': 'Falco', 'Pc': 'Pichu', 'Gw': 'G&W',
         'Gn': 'Ganon', 'Fe': 'Roy', 'Ge': 'GENO'}
CSV_NAME = {'Mr': 'Mario', 'Fx': 'Fox', 'Ca': 'Captain', 'Dk': 'Donkey', 'Kb': 'Kirby', 'Kp': 'Koopa', 'Lk': 'Link', 'Sk': 'Seak',
            'Ns': 'Ness', 'Pe': 'Peach', 'Pp': 'Popo', 'Pk': 'Pikachu', 'Ss': 'Samus', 'Ys': 'Yoshi', 'Pr': 'Purin', 'Mt': 'Mewtwo',
            'Lg': 'Luigi', 'Ms': 'Mars', 'Zd': 'Zelda', 'Cl': 'Clink', 'Dr': 'Drmario', 'Fc': 'Falco', 'Pc': 'Pichu',
            'Gw': 'Gamewatch', 'Gn': 'Ganon', 'Fe': 'Emblem'}
WATCH = ['Fx', 'Fc', 'Ms', 'Sk', 'Ca', 'Pe', 'Pr', 'Ss', 'Mr']          # the characters his balance is set against
MOVES = ['jab1', 'ftilt', 'utilt', 'dtilt', 'dash_attack', 'fsmash', 'usmash', 'dsmash', 'nair', 'fair', 'bair', 'uair', 'dair',
         'grab', 'dash_grab']
AERIAL_LAG = {'nair': 'NairLandingLag', 'fair': 'FairLandingLag', 'bair': 'BairLandingLag', 'uair': 'UairLandingLag',
              'dair': 'DairLandingLag'}
REACH = {'bair': 'reach_back', 'uair': 'reach_up', 'utilt': 'reach_up', 'usmash': 'reach_up', 'dair': 'reach_below'}
DISJ = {'uair': 'disjoint_up', 'utilt': 'disjoint_up', 'usmash': 'disjoint_up', 'dair': 'disjoint_down', 'bair': 'disjoint_back'}


def load(d):
    out = {}
    for f in os.listdir(d):
        code = f[:-6]
        if f.endswith('.jsonl') and code in NAMES:
            rows = (json.loads(l) for l in open(os.path.join(d, f)) if l.strip())
            out[code] = {o['move']: o for o in rows if 'move' in o}          # (body lines are the measured hurtboxes)
    return out


def attrs():
    p = os.path.join(os.path.dirname(__file__), '..', '..', 'research', 'cast_attributes.csv')
    return {r['fighter']: r for r in csv.DictReader(open(p))}


def metrics(code, mv, o, at):
    if not o or o.get('startup', -1) < 0:
        return None
    total = o['iasa'] if o['iasa'] > 0 else o['frames']
    if o.get('reach_down') is not None:
        o['reach_below'] = round(-o['reach_down'], 2)          # how far below the feet the hit reaches
    m = dict(startup=o['startup'], active=o['last_active'] - o['startup'] + 1, total=total, damage=o['damage_max'],
             reach=o.get(REACH.get(mv, 'reach_fwd')), radius=o.get('radius_max'), disjoint=o.get(DISJ.get(mv, 'disjoint_fwd')))
    if mv in AERIAL_LAG:
        if code == 'Ge':
            import importlib.util
            lag = {'nair': 14, 'fair': 16, 'bair': 18, 'uair': 16, 'dair': 24}[mv]
        else:
            lag = int(float(at[CSV_NAME[code]][AERIAL_LAG[mv]]))
        m['landing'] = lag
        m['l_cancel'] = lag // 2
    return m


sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'rig'))
import rig as _rig                                    # Geno's attributes straight from the rig (a copy here went stale)
GENO_ATTRS = {k: _rig.ATTRIBUTES[k] for k in ('JumpStartupLag', 'MaximumShorthopVerticalVelocity', 'InitialVerticalJumpVelocity',
              'Gravity', 'TerminalVelocity', 'FastFallTerminalVelocity', 'MaxAerialHorizontalSpeed', 'AerialSpeed', 'Friction',
              'InitialDashSpeed', 'InitialRunSpeed', 'Weight')}


def flight(v0, g, term, ff=None):
    """Frames from takeoff to landing and the apex, fast-falling from the apex if ff is given."""
    y, vy, t, apex = 0.0, v0, 0, 0.0
    while True:
        y += vy; t += 1; apex = max(apex, y)
        vy -= g
        if ff is not None and vy <= 0: vy = -ff
        elif vy < -term: vy = -term
        if y <= 0 or t > 400: return t, apex


def movement(at):
    rows = {}
    for code, nm in CSV_NAME.items():
        if code == 'Pp' or nm not in at: continue
        r = {k: float(v) for k, v in at[nm].items() if k != 'fighter'}
        rows[code] = r
    rows['Ge'] = {k: float(v) for k, v in GENO_ATTRS.items()}
    out = {}
    for code, r in rows.items():
        g, term, ff = r['Gravity'], r['TerminalVelocity'], r['FastFallTerminalVelocity']
        sh_t, sh_h = flight(r['MaximumShorthopVerticalVelocity'], g, term)
        shff_t, _ = flight(r['MaximumShorthopVerticalVelocity'], g, term, ff)
        fh_t, fh_h = flight(r['InitialVerticalJumpVelocity'], g, term)
        out[code] = dict(jumpsquat=int(r['JumpStartupLag']), sh_height=round(sh_h, 1), sh_air=sh_t, shff_air=shff_t,
                         fh_height=round(fh_h, 1), fh_air=fh_t, fall=term, ff=ff, air_speed=r['MaxAerialHorizontalSpeed'],
                         air_accel=r['AerialSpeed'], traction=r['Friction'], dash=r['InitialDashSpeed'], run=r['InitialRunSpeed'],
                         weight=int(r['Weight']))
    return out


def pct(vals, v):
    vals = sorted(x for x in vals if x is not None)
    if v is None or not vals: return None
    return round(100 * sum(1 for x in vals if x < v) / len(vals) + 50 / len(vals))


STANDARD = ['pummel', 'ledge_quick', 'ledge_slow', 'getup_u', 'getup_d']


def standard(code, mv, o):
    """The standardized moves (pummel, ledge attacks under and from 100%, get-up attacks face up and down): frame data,
    intangibility, and coverage. Ledge attacks measure from the ledge corner (forward onto the stage, up from its floor),
    since the engine places a ledge action at ledge + TransN; `stands` is the first frame TransN has y >= 0 and z >= 0
    (on the stage), `ends` how far onto the stage he finishes. Get-ups measure each side: the first frame a hit is centred
    in front of / behind him, and the reach that way. (Game & Watch, Kirby and Mewtwo measure oddly on the root-motion and
    reach columns: G&W's animations don't move TransN, Mewtwo's TransN carries a constant lift, Kirby's hitboxes sit on
    his one body bone; the medians shrug them off.)"""
    if not o or o.get('startup', -1) < 0:
        return None
    total = o['iasa'] if o['iasa'] > 0 else o['frames']
    inv = o.get('intangible') or []
    m = dict(startup=o['startup'], active=o['last_active'] - o['startup'] + 1, total=total, damage=o['damage_max'],
             intangible=inv[-1][1] if inv else 0)
    if mv.startswith('ledge'):
        m.update(stands=o.get('stand'), reach=o.get('reach_fwd'), reach_up=o.get('reach_up'), ends=o.get('trans_end', [0, 0])[1])
    elif mv.startswith('getup'):
        fr, bk = o.get('front_frames'), o.get('back_frames')
        m.update(front=fr[0] if fr else None, back=bk[0] if bk else None, reach_front=o.get('reach_fwd'),
                 reach_back=o.get('reach_back'), reach_up=o.get('reach_up'))
    else:
        m.update(reach=o.get('reach_fwd'))
    return m


def standard_section(data, lines, summary):
    lines += ['## Pummel, ledge and get-up attacks', '',
              'Frames are 1-based; `intangible` is the last intangible frame (all start on frame 1); ledge reach is from the '
              'ledge corner onto the stage, `stands` the first frame on the stage, `ends` how far onto it he finishes; get-up '
              '`front` / `back` are the first frame each side is hit. None of these moves has an IASA: each plays to its end.',
              '']
    for mv in STANDARD:
        rows = {c: standard(c, mv, data[c].get(mv)) for c in data if c != 'Nn'}
        cast = {c: r for c, r in rows.items() if r and c != 'Ge'}
        g = rows.get('Ge')
        if not cast: continue
        cols = list(next(iter(cast.values())).keys())
        lines += [f'### {mv}', '', '| | ' + ' | '.join(cols) + ' |', '|---|' + '---|' * len(cols)]
        for label, fn in [('cast min', min), ('cast median', st.median), ('cast max', max)]:
            vals = []
            for c in cols:
                xs = [r[c] for r in cast.values() if r[c] is not None]
                vals.append(fn(xs) if xs else '')
            lines.append(f'| {label} | ' + ' | '.join(f'{v:.1f}' if isinstance(v, float) else str(v) for v in vals) + ' |')
        for c in WATCH:
            r = cast.get(c)
            if r: lines.append(f'| {NAMES[c]} | ' + ' | '.join(str(r[k]) for k in cols) + ' |')
        if g:
            lines.append('| **GENO now** | ' + ' | '.join(f'**{g[k]}**' for k in cols) + ' |')
            lines.append('| Geno pct | ' + ' | '.join(str(pct([r[k] for r in cast.values()], g[k])) for k in cols) + ' |')
            summary[mv] = {k: dict(geno=g[k], pct=pct([r[k] for r in cast.values()], g[k]),
                                   median=st.median([r[k] for r in cast.values() if r[k] is not None])) for k in cols}
        lines.append('')


def main(d, out=None):
    data, at = load(d), attrs()
    lines = ['# Geno\'s normals against the cast (measured)', '',
             'Cast = the 25 others (Nana excluded). Reach and disjoint are world units in the move\'s direction (bair back, '
             'uair/utilt/usmash up, dair down); startup and totals are frames; `pct` is Geno\'s percentile in the cast '
             '(higher = longer reach, bigger, later, more lag, more damage).', '']
    summary = {}
    for mv in MOVES:
        rows = {c: metrics(c, mv, data[c].get(mv), at) for c in data if c != 'Nn'}
        cast = {c: r for c, r in rows.items() if r and c != 'Ge'}
        g = rows.get('Ge')
        cols = ['startup', 'active', 'total', 'damage', 'reach', 'radius', 'disjoint'] + (['landing', 'l_cancel'] if mv in AERIAL_LAG else [])
        lines += [f'## {mv}', '', '| | ' + ' | '.join(cols) + ' |', '|---|' + '---|' * len(cols)]
        for label, fn in [('cast min', min), ('cast median', st.median), ('cast max', max)]:
            vals = [fn([r[c] for r in cast.values() if r[c] is not None]) if any(r[c] is not None for r in cast.values()) else '' for c in cols]
            lines.append(f'| {label} | ' + ' | '.join(f'{v:.1f}' if isinstance(v, float) else str(v) for v in vals) + ' |')
        for c in WATCH:
            r = cast.get(c)
            if r: lines.append(f'| {NAMES[c]} | ' + ' | '.join(str(r[k]) for k in cols) + ' |')
        if g:
            lines.append('| **GENO now** | ' + ' | '.join(f'**{g[k]}**' for k in cols) + ' |')
            lines.append('| Geno pct | ' + ' | '.join(str(pct([r[k] for r in cast.values()], g[k])) for k in cols) + ' |')
            summary[mv] = {k: dict(geno=g[k], pct=pct([r[k] for r in cast.values()], g[k]),
                                   median=st.median([r[k] for r in cast.values() if r[k] is not None])) for k in cols}
        lines.append('')
    standard_section(data, lines, summary)
    mv = movement(at)
    cols = ['jumpsquat', 'sh_height', 'sh_air', 'shff_air', 'fh_height', 'fh_air', 'fall', 'ff', 'air_speed', 'air_accel',
            'traction', 'dash', 'run', 'weight']
    lines += ['## Movement (from each fighter\'s attributes; airtimes in frames from takeoff, apex heights in units)', '',
              '| | ' + ' | '.join(cols) + ' |', '|---|' + '---|' * len(cols)]
    cast = {c: r for c, r in mv.items() if c != 'Ge'}
    for label, fn in [('cast min', min), ('cast median', st.median), ('cast max', max)]:
        lines.append(f'| {label} | ' + ' | '.join(f'{fn([r[c] for r in cast.values()]):g}' for c in cols) + ' |')
    for c in WATCH:
        if c in mv: lines.append(f'| {NAMES[c]} | ' + ' | '.join(f'{mv[c][k]:g}' for k in cols) + ' |')
    lines.append('| **GENO now** | ' + ' | '.join(f'**{mv["Ge"][k]:g}**' for k in cols) + ' |')
    lines.append('| Geno pct | ' + ' | '.join(str(pct([r[k] for r in cast.values()], mv['Ge'][k])) for k in cols) + ' |')
    # the short-hop, fast-fall, L-cancel cycle for each aerial: jumpsquat + max(fast-fallen airtime, the hit) + L-cancelled lag
    lines += ['', '## SHFFL cycle per aerial (frames: jumpsquat + fast-fallen short hop, or the hit if later + L-cancelled lag)', '',
              '| | ' + ' | '.join(AERIAL_LAG) + ' |', '|---|' + '---|' * len(AERIAL_LAG)]
    cyc = {}
    for c in list(cast) + ['Ge']:
        row = {}
        for a in AERIAL_LAG:
            m = metrics(c, a, data.get(c, {}).get(a), at)
            if not m: continue
            row[a] = mv[c]['jumpsquat'] + max(mv[c]['shff_air'], m['startup'] + 1) + m['l_cancel']
        cyc[c] = row
    for label, fn in [('cast min', min), ('cast median', st.median), ('cast max', max)]:
        lines.append(f'| {label} | ' + ' | '.join(f'{fn([cyc[c][a] for c in cast if a in cyc[c]]):g}' for a in AERIAL_LAG) + ' |')
    for c in WATCH:
        if c in cyc: lines.append(f'| {NAMES[c]} | ' + ' | '.join(str(cyc[c].get(a, '')) for a in AERIAL_LAG) + ' |')
    lines.append('| **GENO now** | ' + ' | '.join(f"**{cyc['Ge'].get(a, '')}**" for a in AERIAL_LAG) + ' |')
    summary['movement'] = mv['Ge']; summary['shffl'] = cyc['Ge']
    text = '\n'.join(lines)
    if out:
        open(out, 'w').write(text); json.dump(summary, open(os.path.splitext(out)[0] + '.json', 'w'), indent=1)
    print(text)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
