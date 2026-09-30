"""Limb scale survey: which of the cast's attacks grow a body part while they hit (Mario's jab fist, the kicks' feet), by how
much and on which frames, against the move's active frames. Melee scales joints in the animation for readability at game
distance; scale is inherited down the chain (classical scale), so a scaled forearm grows the hand too.
For each fighter: `datkit fkdir` samples every move in its movedata (the attack actions), `datkit skel` names the joints
(PlCo's part table). A joint is listed when its own scale leaves 1 (by more than 5%); its effective scale is the product
down the chain, reported at the joint and at the chain's end (the hand or foot it carries).
    .venv/bin/python projects/geno/director/labs/limb_scale.py MOVEDATA OUT.md [OUT.json] [--fighters Mr,Fx,...]
"""
import json, os, re, subprocess, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
DATKIT = os.path.join(ROOT, 'tools/machinima/melee/datkit.sh')
DISC = os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc')) + '/files'
PARTS = ['TopN', 'TransN', 'XRotN', 'YRotN', 'HipN', 'WaistN', 'LLegJA', 'LLegJ', 'LKneeJ', 'LFootJA', 'LFootJ',
         'RLegJA', 'RLegJ', 'RKneeJ', 'RFootJA', 'RFootJ', 'WaistB', 'BustN', 'LShoulderN', 'LShoulderJA', 'LShoulderJ',
         'LArmJ', 'LHandN', 'L1stNa', 'L1stNb', 'L2ndNa', 'L2ndNb', 'L3rdNa', 'L3rdNb', 'L4thNa', 'L4thNb', 'LHandNb',
         'LThumbNa', 'LThumbNb', 'NeckN', 'HeadN', 'RShoulderN', 'RShoulderJA', 'RShoulderJ', 'RArmJ', 'RHandN',
         'R1stNa', 'R1stNb', 'R2ndNa', 'R2ndNb', 'R3rdNa', 'R3rdNb', 'R4thNa', 'R4thNb', 'RHandNb', 'RThumbNa',
         'RThumbNb', 'ThrowN', 'TransN2']
KIND = dict(Ca=0, Dk=1, Fx=2, Gw=3, Kb=4, Kp=5, Lk=6, Lg=7, Mr=8, Ms=9, Mt=10, Ns=11, Pe=12, Pk=13, Pp=14, Pr=15, Ss=16,
            Ys=17, Zd=18, Sk=19, Fc=20, Cl=21, Dr=22, Fe=23, Pc=24, Gn=25)
NAME = dict(Ca='Falcon', Dk='DK', Fx='Fox', Gw='G&W', Kb='Kirby', Kp='Bowser', Lk='Link', Lg='Luigi', Mr='Mario',
            Ms='Marth', Mt='Mewtwo', Ns='Ness', Pe='Peach', Pk='Pikachu', Pp='Popo', Pr='Puff', Ss='Samus', Ys='Yoshi',
            Zd='Zelda', Sk='Sheik', Fc='Falco', Cl='Y.Link', Dr='Doc', Fe='Roy', Pc='Pichu', Gn='Ganon')
TH = 0.05


def joint_names(code):
    out = subprocess.run([DATKIT, 'skel', f'{DISC}/PlCo.dat', str(KIND[code]), f'{DISC}/Pl{code}Nr.dat'],
                         capture_output=True, text=True).stdout
    names = {}
    for line in out.splitlines():
        m = re.match(r'\s*(\d+) p-?\d+\s+part (\d+)', line)
        if m:
            part = int(m.group(2))
            names[int(m.group(1))] = PARTS[part] if part < len(PARTS) else f'j{m.group(1)}'
    return names


def survey(code, moves, tmp):
    names = joint_names(code)
    spec = ','.join(f"{m['action']}={m['move']}" for m in moves)
    subprocess.run([DATKIT, 'fkdir', f'{DISC}/Pl{code}Nr.dat', f'{DISC}/Pl{code}.dat', f'{DISC}/Pl{code}AJ.dat', tmp, spec],
                   capture_output=True, text=True)
    rows = []
    for m in moves:
        p = os.path.join(tmp, f"{m['move']}.json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p))
        par = [j['p'] for j in d['joints']]
        nf = len(d['local'])
        own = {}                                                        # joint -> [(frame, own scale)]
        eff = [[1.0] * len(par) for _ in range(nf)]
        for f in range(nf):
            for j in range(len(par)):
                s = max(d['local'][f][j][6:9], key=lambda v: abs(v - 1))
                eff[f][j] = s * (eff[f][par[j]] if par[j] >= 0 else 1.0)
                if abs(s - 1) > TH:
                    own.setdefault(j, []).append((f, s))
        # keep the outermost scaled joints of each chain (a scaled parent's scaled children fold into its row)
        for j, fs in own.items():
            kids = [k for k in range(len(par)) if k != j and _under(par, k, j)]
            leaf = max(kids, key=lambda k: max(eff[f][k] for f in range(nf)), default=j)
            peak_f, peak = max(fs, key=lambda x: abs(x[1] - 1))
            rows.append(dict(fighter=code, move=m['move'], joint=names.get(j, f'j{j}'), frames=[fs[0][0], fs[-1][0]],
                             peak_frame=peak_f, own_peak=round(peak, 2),
                             eff_peak=round(max(eff[f][j] for f in range(nf)), 2),
                             end_joint=names.get(leaf, f'j{leaf}'),
                             end_eff_peak=round(max(eff[f][leaf] for f in range(nf)), 2),
                             active=m.get('windows'), startup=m.get('startup'), total=m.get('frames'),
                             radius_max=m.get('radius_max')))
    return rows


def _under(par, k, j):
    while par[k] >= 0:
        k = par[k]
        if k == j:
            return True
    return False


if __name__ == '__main__':
    a = sys.argv[1:]
    only = None
    if '--fighters' in a:
        i = a.index('--fighters'); only = a[i + 1].split(','); del a[i:i + 2]
    md, out_md = a[0], a[1]
    out_json = a[2] if len(a) > 2 else os.path.splitext(out_md)[0] + '.json'
    allrows = []
    for code in (only or [c for c in KIND if os.path.exists(f'{md}/{c}.jsonl')]):
        moves = [json.loads(l) for l in open(f'{md}/{code}.jsonl')]
        moves = [m for m in moves if 'move' in m]
        with tempfile.TemporaryDirectory() as tmp:
            allrows += survey(code, moves, tmp)
    json.dump(allrows, open(out_json, 'w'), indent=1)
    by = {}
    for r in allrows:
        by.setdefault((r['fighter'], r['move']), []).append(r)
    L = ['# Limb scale in the cast\'s attacks', '',
         'Which body parts grow (or shrink) while a move plays, from the animation data (`limb_scale.py`). "own" is the '
         'joint\'s own scale at its peak, "chain end" the effective scale at the hand or foot it carries (scale is '
         'inherited). Frames are the animation\'s, from 0; "active" the move\'s hit windows.', '',
         '| Fighter | Move | Active | Joint | Scaled frames (peak) | Own peak | Chain end (effective) |', '|---|---|---|---|---|---|---|']
    for (c, mv), rs in by.items():
        for r in sorted(rs, key=lambda r: -abs(r['end_eff_peak'] - 1)):
            L.append(f"| {NAME[c]} | {mv} | {r['active']} | {r['joint']} | {r['frames'][0]}-{r['frames'][1]} ({r['peak_frame']}) "
                     f"| {r['own_peak']} | {r['end_joint']} {r['end_eff_peak']} |")
    n_moves = sum(1 for c in KIND if os.path.exists(f'{md}/{c}.jsonl') and (not only or c in only)
                  for l in open(f'{md}/{c}.jsonl') if '"move"' in l)
    L += ['', f'{len(by)} of {n_moves} moves scale a body part.']
    open(out_md, 'w').write('\n'.join(L) + '\n')
    print(out_md, len(allrows), 'rows,', len(by), 'moves')
