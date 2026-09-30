"""Where the hurtboxes go through the defensive and reactive states, across the cast: dodges, the shield's in and out,
hit reactions and tumble, techs, being grabbed, dizzy and sleep, the trip and the clank. From `datkit bodydata` (every
frame's hurtbox union: top, bottom, front and back from his position, facing +Z; TransN included, so a roll's path
counts). Everything is a share of the fighter's standing height (Wait1's hurtbox top), so a small fighter and a tall one
compare.
    .venv/bin/python projects/geno/director/labs/body_cover.py MOVEDATA_DIR [OUT.md]
MOVEDATA_DIR/body/Xx.jsonl is written first for any fighter missing it (the cast from the disc, Geno from
$MELEE_WORK/rig/out). Columns:
  - low: the lowest the top of the body gets (a crouch, a duck, a curl), mean: its average;
  - high: the highest top (a stretch, a launch);
  - front / back: how much farther the hurtboxes reach ahead of / behind his position than they do standing;
  - below: how much farther they reach below his position than standing (a tumble or a launch hanging down);
  - travel: where TransN ends (a roll's distance), in units.
"""
import json, os, statistics as st, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cast_moves import NAMES, WATCH

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
DISC = os.path.expanduser('~/games/melee/disc/files')
KIND = {'Mr': 0, 'Fx': 1, 'Ca': 2, 'Dk': 3, 'Kb': 4, 'Kp': 5, 'Lk': 6, 'Sk': 7, 'Ns': 8, 'Pe': 9, 'Pp': 10, 'Pk': 12, 'Ss': 13,
        'Ys': 14, 'Pr': 15, 'Mt': 16, 'Lg': 17, 'Ms': 18, 'Zd': 19, 'Cl': 20, 'Dr': 21, 'Fc': 22, 'Pc': 23, 'Gw': 24, 'Gn': 25,
        'Fe': 26, 'Ge': 34}
ACTIONS = {41: 'EscapeN', 42: 'EscapeF', 43: 'EscapeB', 44: 'EscapeAir', 37: 'GuardOn', 39: 'GuardOff', 40: 'GuardDamage',
           165: 'DamageHi1', 166: 'DamageHi2', 167: 'DamageHi3', 168: 'DamageN1', 169: 'DamageN2', 170: 'DamageN3',
           171: 'DamageLw1', 172: 'DamageLw2', 173: 'DamageLw3', 174: 'DamageAir1', 175: 'DamageAir2', 176: 'DamageAir3',
           177: 'DamageFlyHi', 178: 'DamageFlyN', 179: 'DamageFlyLw', 180: 'DamageFlyTop', 181: 'DamageFlyRoll',
           1: 'DamageFall', 0: 'WallDamage', 184: 'DownWaitU', 192: 'DownWaitD', 199: 'Passive', 200: 'PassiveStandF',
           201: 'PassiveStandB', 202: 'PassiveWall', 203: 'PassiveWallJump', 204: 'PassiveCeil', 213: 'StopWall',
           214: 'StopCeil', 226: 'CliffJumpSlow2', 228: 'CliffJumpQuick2', 251: 'CapturePulledHi', 252: 'CaptureWaitHi',
           253: 'CaptureDamageHi', 254: 'CapturePulledLw', 255: 'CaptureWaitLw', 256: 'CaptureDamageLw', 257: 'CaptureCut',
           258: 'CaptureJump', 205: 'FuraFura', 206: 'FuraSleepStart', 207: 'FuraSleepLoop', 208: 'FuraSleepEnd',
           215: 'MissFoot', 45: 'Rebound'}
AIR = ('EscapeAir', 'DamageAir', 'DamageFly', 'DamageFall', 'WallDamage', 'PassiveWall', 'PassiveCeil', 'Stop', 'CliffJump',
       'CaptureJump', 'MissFoot')


def measure(code, out, rig_out=None):
    if code == 'Ge':
        d = rig_out or os.path.join(os.environ.get('MELEE_WORK', os.path.expanduser('~/games/melee/work')), 'rig', 'out')
        files = [f'{d}/PlGe.dat', f'{d}/PlGeAJ.dat', f'{d}/PlGeNr.dat']
    else:
        files = [f'{DISC}/Pl{code}.dat', f'{DISC}/Pl{code}AJ.dat', f'{DISC}/Pl{code}Nr.dat']
    cmd = ['sh', f'{ROOT}/tools/machinima/melee/datkit.sh', 'bodydata', *files, f'{DISC}/PlCo.dat', str(KIND[code]), '-',
           ','.join(map(str, ACTIONS))]
    with open(out, 'w') as fo:
        subprocess.run(cmd, stdout=fo, stderr=subprocess.DEVNULL, check=True)


def metrics(o):
    """Heights as shares of standing height; front, back and below as how far past the fighter's own standing box they
    reach (so a fighter whose standing hurtboxes are narrow or tall compares by what the animation does)."""
    H, sb, sf, sk = o['stand'][0], o['stand'][1], o['stand'][2], o['stand'][3]
    per = o['per']
    if not per or H <= 0: return None
    tops = [p[1] for p in per]
    m = dict(low=min(tops) / H, mean=st.mean(tops) / H, high=max(tops) / H, front=(max(p[3] for p in per) - sf) / H,
             back=(max(p[4] for p in per) - sk) / H, below=max(0.0, -min(p[2] for p in per) + min(0.0, sb)) / H, travel=per[-1][6])
    return {k: round(v, 2) for k, v in m.items()}


def main(md, out=None, fresh=False):
    bd = os.path.join(md, 'body'); os.makedirs(bd, exist_ok=True)
    data = {}
    for code in KIND:
        if code == 'Pp': continue
        p = os.path.join(bd, f'{code}.jsonl')
        if fresh or not os.path.exists(p) or (code == 'Ge' and os.environ.get('BODY_FRESH_GE')):
            measure(code, p)
        for l in open(p):
            o = json.loads(l)
            data.setdefault(code, {})[ACTIONS.get(o['action'], o['action'])] = o
    lines = ['# Hurtboxes through the defensive and reactive states (measured)', '',
             __doc__.split('\n    .venv')[0].strip(), '', __doc__.split('Columns:\n', 1)[1].strip(), '',
             'Cast = the 25 others. `pct` is Geno\'s percentile in the cast. Heights are shares of standing height.', '']
    summary = {}
    cols = ['low', 'mean', 'high', 'front', 'back', 'below', 'travel']
    for name in ACTIONS.values():
        rows = {c: metrics(d[name]) for c, d in data.items() if name in d and d[name]['frames'] > 0}
        rows = {c: r for c, r in rows.items() if r}
        cast = {c: r for c, r in rows.items() if c != 'Ge'}
        if not cast: continue
        lines += [f'## {name}', '', '| | ' + ' | '.join(cols) + ' |', '|---|' + '---|' * len(cols)]
        med = {k: st.median([r[k] for r in cast.values()]) for k in cols}
        for label, fn in (('cast min', min), ('cast median', st.median), ('cast max', max)):
            lines.append(f'| {label} | ' + ' | '.join(f'{fn([r[k] for r in cast.values()]):.2f}' for k in cols) + ' |')
        for c in WATCH:
            if c in cast: lines.append(f'| {NAMES[c]} | ' + ' | '.join(str(cast[c][k]) for k in cols) + ' |')
        if 'Ge' in rows:
            g = rows['Ge']
            pc = lambda k: round(100 * sum(1 for r in cast.values() if r[k] < g[k]) / len(cast) + 50 / len(cast))
            lines.append('| **GENO now** | ' + ' | '.join(f'**{g[k]}**' for k in cols) + ' |')
            lines.append('| Geno pct | ' + ' | '.join(str(pc(k)) for k in cols) + ' |')
            summary[name] = dict(geno=g, median=med, pct={k: pc(k) for k in cols})
        lines.append('')
    text = '\n'.join(lines)
    if out:
        open(out, 'w').write(text + '\n')
        json.dump(summary, open(os.path.splitext(out)[0] + '.json', 'w'), indent=1)
    return summary


if __name__ == '__main__':
    s = main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, fresh='--fresh' in sys.argv)
    for name, r in s.items():
        off = [f"{k} {r['geno'][k]} (med {r['median'][k]:.2f}, p{r['pct'][k]})" for k in ('low', 'high', 'front', 'back', 'below')
               if (r['pct'][k] < 12 or r['pct'][k] > 88) and abs(r['geno'][k] - r['median'][k]) > 0.08]
        print(f'{name:16s}', '; '.join(off) if off else 'within the cast')
