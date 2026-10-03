"""Which fighters have a crowd chant, and what it is.

Reads every Pl??.dat's ftData+0x4C (FtSFX) +0x34 (the chant id, SBM_PlayerSFXTable.SFX_Cheer), resolves each id through
smash2.sem (bank = id / 10000, script = first_script[bank] + id % 10000) to its play commands and global sample ids, finds
the .ssm that owns each sample (base_sample_id + index) and decodes the chant to 16-bit WAV at its native rate.

Reads the disc, never writes it. Everything it writes is game-derived and goes to $CROWD_WORK (default
~/games/melee/work/crowd), outside every repo.

    .venv/bin/python projects/geno/sound/cheer/survey.py [--disc DIR]
"""
import argparse, glob, json, os, struct, sys

ANN_TOOLS = os.path.expanduser(os.environ.get('ANN_TOOLS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'announcer', 'tools')))
sys.path.insert(0, ANN_TOOLS)
import numpy as np
import ssm  # noqa: E402  (the announcer's .ssm parser and DSP-ADPCM decoder)

WORK = os.path.expanduser(os.environ.get('CROWD_WORK', '~/games/melee/work/crowd'))
NONE, SILENT = 540000, 540001

# CharacterKind order (ft/forward.h) -> fighter file code
FIGHTERS = [('Mario', 'Mr'), ('Fox', 'Fx'), ('Captain Falcon', 'Ca'), ('DK', 'Dk'), ('Kirby', 'Kb'), ('Bowser', 'Kp'),
            ('Link', 'Lk'), ('Sheik', 'Sk'), ('Ness', 'Ns'), ('Peach', 'Pe'), ('Popo', 'Pp'), ('Nana', 'Nn'),
            ('Pikachu', 'Pk'), ('Samus', 'Ss'), ('Yoshi', 'Ys'), ('Jigglypuff', 'Pr'), ('Mewtwo', 'Mt'), ('Luigi', 'Lg'),
            ('Marth', 'Ms'), ('Zelda', 'Zd'), ('Young Link', 'Cl'), ('Dr. Mario', 'Dr'), ('Falco', 'Fc'), ('Pichu', 'Pc'),
            ('Mr. Game & Watch', 'Gw'), ('Ganondorf', 'Gn'), ('Roy', 'Fe'), ('Master Hand', 'Mh'), ('Crazy Hand', 'Ch'),
            ('Wireframe M', 'Bo'), ('Wireframe F', 'Gl'), ('Giga Bowser', 'Gk'), ('Sandbag', 'Sb'), ('Geno', 'Ge')]


def hsd_roots(b):
    fsize, dsize, nrel, nroot, nref = struct.unpack('>5I', b[:20])
    data = b[0x20:0x20 + dsize]
    o = 0x20 + dsize + 4 * nrel
    roots = [struct.unpack('>2I', b[o + 8 * i:o + 8 * i + 8]) for i in range(nroot)]
    strtab = 0x20 + dsize + 4 * nrel + 8 * (nroot + nref)
    out = {}
    for off, so in roots:
        s = b[strtab + so:b.index(b'\0', strtab + so)].decode()
        out[s] = off
    return data, out


def chant_id(path):
    b = open(path, 'rb').read()
    data, roots = hsd_roots(b)
    name = next(k for k in roots if k.startswith('ftData'))
    ft = roots[name]
    sfx = struct.unpack('>I', data[ft + 0x4C:ft + 0x50])[0]
    return name, struct.unpack('>I', data[sfx + 0x34:sfx + 0x38])[0]


def parse_sem(b):
    w = lambda o: struct.unpack('>I', b[o:o + 4])[0]
    nb = w(8); first = [w(12 + 4 * i) for i in range(nb)]; o = 12 + 4 * nb
    ns = w(o); o += 4; ptr = [w(o + 4 * i) for i in range(ns)]
    ends = ptr[1:] + [len(b)]
    return dict(nb=nb, first=first, ns=ns, scripts=[b[p:e] for p, e in zip(ptr, ends)])


def script_cmds(s):
    return [(w >> 24, w & 0xFFFFFF) for w in struct.unpack(f'>{len(s) // 4}I', s[:len(s) // 4 * 4])]


def resolve(sem, sid):
    bank, k = divmod(sid, 10000)
    if bank >= sem['nb']:
        return None
    i = sem['first'][bank] + k
    last = sem['first'][bank + 1] if bank + 1 < sem['nb'] else sem['ns']
    if i >= last:
        return dict(bank=bank, script=None)
    return dict(bank=bank, script=i, cmds=script_cmds(sem['scripts'][i]))


def sample_index(audio_dir):
    """global sample id -> (ssm file, index, rate, nsamples)"""
    idx = {}
    for p in sorted(glob.glob(os.path.join(audio_dir, '*.ssm'))):
        bk = ssm.parse(p)
        for s in bk['sounds']:
            idx[s['id']] = (os.path.basename(p), s['index'], s['rate'])
    return idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--disc', default=os.environ.get('MELEE_DISC', os.path.expanduser('~/games/melee/disc')))
    ap.add_argument('--lang', default='us', choices=['us', 'jp'])
    a = ap.parse_args()
    files = os.path.join(a.disc, 'files')
    audio = os.path.join(files, 'audio', 'us') if a.lang == 'us' else os.path.join(files, 'audio')
    sem = parse_sem(open(os.path.join(audio, 'smash2.sem'), 'rb').read())
    smp = sample_index(audio)
    os.makedirs(os.path.join(WORK, 'chants'), exist_ok=True)
    rows, seen = [], {}
    for kind, (name, code) in enumerate(FIGHTERS):
        p = os.path.join(files, f'Pl{code}.dat')
        if not os.path.exists(p):
            continue
        root, cid = chant_id(p)
        row = dict(kind=kind, fighter=name, file=f'Pl{code}.dat', chant=cid)
        r = resolve(sem, cid) if cid not in (NONE,) else None
        if r and r.get('cmds'):
            plays = [v for op, v in r['cmds'] if op == 0x01]
            row.update(bank=r['bank'], script=r['script'], cmds=' '.join(f'{op:02X}:{v:06X}' for op, v in r['cmds']),
                       samples=plays, where=[smp.get(s) for s in plays])
            for s in plays:
                if s in smp and s not in seen:
                    f, i, rate = smp[s]
                    bk = ssm.parse(os.path.join(audio, f))
                    x = ssm.decode_channel(bk, bk['sounds'][i]['chans'][0])
                    out = os.path.join(WORK, 'chants', f'{a.lang}_{code}_{name.replace(" ", "").replace(".", "").replace("&", "")}_{cid}_s{s}.wav')
                    ssm.write_wav(out, x, rate)
                    seen[s] = out
                    row.setdefault('wav', []).append(dict(path=out, rate=rate, n=len(x), sec=round(len(x) / rate, 3)))
        elif r:
            row.update(bank=r['bank'], script=r['script'])
        rows.append(row)
    for r in rows:
        print(f"{r['kind']:2d} {r['fighter']:18s} {r['file']:9s} chant {r['chant']:6d}  "
              f"{r.get('cmds', '') if r['chant'] != NONE else '(none)'}  {r.get('where', '')}")
        for w in r.get('wav', []):
            print(f"      {w['rate']} Hz {w['sec']} s  {w['path']}")
    json.dump(rows, open(os.path.join(WORK, f'chants/survey_{a.lang}.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
