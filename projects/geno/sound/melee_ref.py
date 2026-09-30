"""Measure Melee's own movement sounds (footsteps, landing, jump, dash, roll, down bound) as the game plays them, for
level-matching Geno's synthesized movement layer.

Reads the retail smash2.sem (install.sh's backup, SHA-1 checked) and the disc's main.ssm, read-only. Writes decoded
references and a loudness table to ~/games/melee/work/sfxbank/synth/ref/ (game-derived: never committed).

Gain chain (decomp): the fighter command's vol (0-127) is doubled and clamped to 255 (lbaudio_ax.c fn_80023750); the
sem script's 06 vol (0-255) is a second linear factor; the synth multiplies both /255 (synth.c HSD_Synth_80389334). So
effective dB = sample dB + 20 log10(script_vol / 255) + 20 log10(min(255, 2 cmd_vol) / 255).

    .venv/bin/python projects/geno/sound/melee_ref.py
"""
import os, sys, json, struct, hashlib
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(__file__))
from loud import measure, to32k

HOME = os.path.expanduser('~')
sys.path.insert(0, f'{HOME}/games/melee/work/announcer/tools')
import ssm

SEM = f'{HOME}/games/melee/work/orig/audio/us/smash2.sem'
SEM_SHA1 = '169b94078cba0f1da66c6a3947a080b971085ceb'
AUDIO = f'{HOME}/games/melee/disc/files/audio'
BANKS = ['main', 'samus', 'gw', 'mario']            # the ssm files holding the references (global sample ids)
OUT = f'{HOME}/games/melee/work/sfxbank/synth/ref'

# bank-0 sound ids and where Melee plays them (Mario's scripts via datkit; the material table in mplib.c)
REFS = {
    443: 'generic step + landing: every FootstepEffect (0x36) and LandingEffect (0x37); Landing at cmd vol 0x7F, walk 0x64/0x6E, run 0x7F',
    332: 'surface step (material table x4: 0x14C)', 335: 'surface step (0x14F)', 338: 'surface step (0x152)',
    341: 'surface step (0x155)', 344: 'surface step (0x158)', 347: 'surface step (0x15B)', 350: 'surface step (0x15E)',
    353: 'surface step (0x161, material 1)', 362: 'surface step (0x16A)', 365: 'surface step (0x16D)',
    75: 'metal landing (material 5 x20)', 76: 'metal landing (material 5 x20)',
    74: 'JumpF/JumpB/JumpAerialF/B frame 1, cmd vol 0x7F',
    0: 'Dash frame 1, cmd vol 0x7F', 5: 'RunBrake frame 1', 1: 'EscapeF/B (roll) frame 1', 2: 'EscapeN (spot dodge) frame 1',
    13: 'DownBoundU/D frame 22 (knocked down, hitting the floor)',
    # silent fighters' voice-table slots hold mechanical sounds: Samus (suit) and Game & Watch (beeps); Mario's voice for scale
    260066: 'Samus SFX_Jump', 260057: 'Samus SFX_LedgeGrab', 260060: 'Samus SFX_StarKO', 260069: 'Samus SFX_YouFreakinDied',
    290057: 'G&W SFX_Jump', 290042: 'G&W SFX_Dodge (teeter, spot/air dodge)',
    180058: 'Mario SFX_Jump (voice)', 180061: 'Mario SFX_DoubleJump (voice)', 180046: 'Mario SFX_LedgeGrab (voice)',
    180076: 'Mario SFX_Dodge (voice)', 180052: 'Mario SFX_StarKO (voice)',
}


def parse_sem(b):
    w = lambda o: struct.unpack('>I', b[o:o + 4])[0]
    nb = w(8); first = [w(12 + 4 * i) for i in range(nb)]; o = 12 + 4 * nb
    ns = w(o); o += 4; ptr = [w(o + 4 * i) for i in range(ns)]
    ends = ptr[1:] + [len(b)]
    return first, [b[p:e] for p, e in zip(ptr, ends)]


def script_fields(sc):
    words = [struct.unpack('>I', sc[i:i + 4])[0] for i in range(0, len(sc), 4)]
    f = {}
    for x in words:
        op, v = x >> 24, x & 0xFFFFFF
        if op == 1: f['sample'] = v
        elif op == 6: f['vol'] = v & 0xFF
        elif op == 4: f['prio'] = v
        elif op == 0x10: f['aux'] = v
        elif op == 0x0C: f['pitch'] = v - (1 << 16) if v & 0x8000 else v
    f['words'] = ' '.join(f'{x:08x}' for x in words)
    return f


def main():
    semb = open(SEM, 'rb').read()
    assert hashlib.sha1(semb).hexdigest() == SEM_SHA1, 'not the retail US smash2.sem'
    first, scripts = parse_sem(semb)
    banks = [ssm.parse(f'{AUDIO}/{n}.ssm') for n in BANKS]
    def sample(gid):
        b = next(b for b in banks if b['start'] <= gid < b['start'] + b['count'])
        return b, b['sounds'][gid - b['start']]
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for sid, use in REFS.items():
        f = script_fields(scripts[first[sid // 10000] + sid % 10000])
        bank, s = sample(f['sample'])
        x = ssm.decode_channel(bank, s['chans'][0]).astype(np.float64) / 32768
        sf.write(os.path.join(OUT, f'ref_{sid:03d}.wav'), x, s['rate'], subtype='PCM_16')
        m = measure(to32k(x, s['rate']))
        sv = 20 * np.log10(f['vol'] / 255)
        rows.append(dict(sound=sid, use=use, sample=f['sample'], rate=s['rate'], dur=round(len(x) / s['rate'], 3),
                         script_vol=f['vol'], script_db=round(sv, 2), aux=f.get('aux'), prio=f.get('prio'), pitch=f.get('pitch'),
                         script=f['words'], **m,
                         eff_peak=round(m['peak'] + sv, 2), eff_lufs=round(m['lufs'] + sv, 2), eff_short=round(m['short'] + sv, 2)))
    json.dump(rows, open(os.path.join(OUT, 'melee_ref.json'), 'w'), indent=1)
    print(f'{"id":>6} {"smp":>4} {"rate":>5} {"dur":>5} {"svol":>4} | {"peak":>6} {"LUFS":>6} {"short":>6} {"cent":>5} | '
          f'{"effPk":>6} {"effLU":>6} {"effSh":>6}  use')
    for r in rows:
        print(f'{r["sound"]:6d} {r["sample"]:4d} {r["rate"]:5d} {r["dur"]:5.3f} {r["script_vol"]:4d} | {r["peak"]:6.1f} '
              f'{r["lufs"]:6.1f} {r["short"]:6.1f} {r["centroid"]:5.0f} | {r["eff_peak"]:6.1f} {r["eff_lufs"]:6.1f} '
              f'{r["eff_short"]:6.1f}  {r["use"][:60]}')


if __name__ == '__main__':
    main()
