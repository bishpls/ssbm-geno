"""A/B against Melee: effective loudness (sample x sem script vol x the command's vol, as the synth multiplies them) of
Geno's movement sounds next to Melee's own movement sounds, Mario's whole bank (attacks and voice) and Geno's round-3
attack sounds; a chart, and a listening file where each Melee movement sound plays alone and then with Geno's layer on
top, at Geno's own footfall timing. Reads the ADPCM-decoded bank (what the game plays).

    .venv/bin/python projects/geno/sound/abtest.py
Outputs (game-derived, never committed): ~/games/melee/work/sfxbank/synth/ab/
"""
import os, sys, json, struct, hashlib
import numpy as np, soundfile as sf
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
from loud import measure, to32k
from melee_ref import parse_sem, script_fields, SEM, SEM_SHA1, AUDIO

HOME = os.path.expanduser('~')
sys.path.insert(0, f'{HOME}/games/melee/work/announcer/tools')
import ssm

WORK = f'{HOME}/games/melee/work/sfxbank/synth'
OUT = os.path.join(WORK, 'ab')
BANK4 = f'{HOME}/games/melee/work/sfxbank/out4/geno.ssm'
R3 = f'{HOME}/games/melee/work/sfxbank/build/sounds.json'
FPS = 60.0


def cmd_gain(vol):                       # fighter command vol 0-127 -> doubled, clamped, /255
    return min(255, 2 * vol) / 255


def load_ref(sid):
    r = next(x for x in json.load(open(os.path.join(WORK, 'ref', 'melee_ref.json'))) if x['sound'] == sid)
    x, sr = sf.read(os.path.join(WORK, 'ref', f'ref_{sid:03d}.wav'))
    return to32k(x, sr) * r['script_vol'] / 255


def load_geno(name, meta):
    m = next(x for x in meta if x['name'] == name)
    x, sr = sf.read(os.path.join(WORK, 'decoded', m['file']))
    return to32k(x, sr) * m['vol'] / 255


def mix(events, dur):
    y = np.zeros(int(dur * 32000))
    for t, x, g in events:
        o = int(t * 32000); n = min(len(x), len(y) - o)
        if n > 0: y[o:o + n] += g * x[:n]
    return y


def mario_bank():
    """Every Mario sound (180000+) at its script volume, and Geno's round-3 attacks at theirs."""
    first, scripts = parse_sem(open(SEM, 'rb').read())
    b = ssm.parse(f'{AUDIO}/mario.ssm'); rows = []
    for k in range(first[19] - first[18]):
        f = script_fields(scripts[first[18] + k])
        if 'sample' not in f or not b['start'] <= f['sample'] < b['start'] + b['count']: continue
        s = b['sounds'][f['sample'] - b['start']]
        x = ssm.decode_channel(b, s['chans'][0]) / 32768 * f['vol'] / 255
        rows.append(measure(to32k(x, s['rate']))['short'])
    return rows


def geno_attacks():
    rows = []
    for m in json.load(open(R3)):
        x, sr = sf.read(os.path.join(os.path.dirname(R3), m['file']))
        rows.append(measure(x * m['vol'] / 255)['short'])
    return rows


def main():
    assert hashlib.sha1(open(SEM, 'rb').read()).hexdigest() == SEM_SHA1
    os.makedirs(OUT, exist_ok=True)
    meta = json.load(open(os.path.join(WORK, 'sounds4.json')))
    rng = np.random.default_rng(7)
    step = lambda kind, side: load_geno(f'GENO_STEP_{kind}_{side}{rng.integers(1, 4)}', meta)

    # ------------------------------------------------------------------ listening file: Melee alone, then + Geno's layer
    segs, t, log = [], 0.0, []
    def seg(label, melee, geno, dur):
        nonlocal t
        a = mix(melee, dur); b = mix(melee + geno, dur)
        la, lb = measure(a)['short'], measure(b)['short']
        log.append(dict(label=label, t_melee=round(t, 2), t_with_geno=round(t + dur + 0.5, 2), melee_short=round(la, 1),
                        with_geno_short=round(lb, 1), rise_db=round(lb - la, 1)))
        segs.extend([a, np.zeros(16000), b, np.zeros(32000)]); t += 2 * dur + 1.5
    s443, s332 = load_ref(443), load_ref(332)
    # WalkMiddle: 45 frames, footfalls at frames 0 (R) and 22.5 (L); Melee's footstep command at vol 0x6E plays 443
    # (+ the surface step, here 332) - Geno's steps at the same vol
    for surf, extra in (('basic floor (443 only)', []), ('surface 332 + 443', [s332])):
        ev_m, ev_g = [], []
        for i in range(8):
            ft = i * 22.5 / FPS; side = 'R' if i % 2 == 0 else 'L'
            ev_m += [(ft, s443, cmd_gain(0x6E))] + [(ft, e, cmd_gain(0x6E)) for e in extra]
            ev_g += [(ft, step('WALK', side), cmd_gain(0x6E))]
        seg(f'walk (WalkMiddle), {surf}', ev_m, ev_g, 8 * 22.5 / FPS + 0.3)
    ev_m, ev_g = [], []
    for i in range(12):                  # Run: 20 frames, footfalls at 0 and 10, vol 0x7F
        ft = i * 10 / FPS; side = 'R' if i % 2 == 0 else 'L'
        ev_m += [(ft, s443, cmd_gain(0x7F)), (ft, s332, cmd_gain(0x7F))]
        ev_g += [(ft, step('RUN', side), cmd_gain(0x7F))]
    seg('run, surface 332 + 443', ev_m, ev_g, 12 * 10 / FPS + 0.3)
    one = lambda x, v=0x7F: [(0.05, x, cmd_gain(v))]
    seg('landing (443 at 0x7F)', one(s443), one(load_geno('GENO_LAND', meta)), 0.5)
    seg('jump (74)', one(load_ref(74)), one(load_geno('GENO_JUMP', meta)), 0.5)
    seg('double jump (74)', one(load_ref(74)), one(load_geno('GENO_JUMP_AIR', meta)), 0.6)
    seg('dash (0)', one(load_ref(0)), one(load_geno('GENO_CAPE2', meta)), 0.5)
    seg('roll (1)', one(load_ref(1)), [(0.1, load_geno('GENO_TECH', meta), 1.0)], 0.5)
    seg('knocked down (13)', one(load_ref(13)), one(load_geno('GENO_LAND_HEAVY', meta)), 0.6)
    solo = [np.zeros(16000)]
    for m in meta:
        solo += [load_geno(m['name'], meta), np.zeros(12000)]
    y = np.concatenate(segs + solo)
    pk = np.abs(y).max()
    sf.write(os.path.join(OUT, 'ab_movement.wav'), y / max(1.0, pk / 0.99), 32000, subtype='PCM_16')
    json.dump(log, open(os.path.join(OUT, 'ab_movement.json'), 'w'), indent=1)
    print('ab_movement.wav: Melee alone, then with Geno\'s layer (effective levels, 32 kHz); then each Geno sound solo')
    for r in log:
        print(f"  {r['label']:34s} melee {r['melee_short']:6.1f}  +geno {r['with_geno_short']:6.1f}  rise {r['rise_db']:+.1f} dB   "
              f"@{r['t_melee']:.1f}s/{r['t_with_geno']:.1f}s")

    # ------------------------------------------------------------------ the level chart (loudest 100 ms, effective)
    refs = json.load(open(os.path.join(WORK, 'ref', 'melee_ref.json')))
    groups = [
        ("Mario's bank (attacks, voice)", mario_bank(), '#9aa5b1'),
        ("Geno attacks (round 3)", geno_attacks(), '#5b8def'),
        ("Melee movement (bank 0)", [r['eff_short'] for r in refs if r['sound'] < 1000], '#e0a030'),
        ("Silent fighters' voice slots", [r['eff_short'] for r in refs if 260000 <= r['sound'] < 300000], '#c07ad0'),
        ("Geno movement (round 4)", [m['eff_short'] for m in meta], '#2a9d6a'),
    ]
    fig, ax = plt.subplots(figsize=(9, 3.6))
    for i, (lab, vals, col) in enumerate(groups):
        ax.scatter(vals, np.full(len(vals), i) + np.random.default_rng(i).uniform(-0.18, 0.18, len(vals)), s=14, color=col, alpha=0.8)
        ax.plot([np.median(vals)] * 2, [i - 0.3, i + 0.3], color='#222', lw=1.5)
    ax.set_yticks(range(len(groups))); ax.set_yticklabels([g[0] for g in groups], fontsize=8)
    ax.set_xlabel('effective loudness: loudest 100 ms, K-weighted (LUFS), at a full-volume command', fontsize=8)
    ax.grid(axis='x', alpha=0.3); ax.set_xlim(-45, -2)
    ax.set_title('Geno movement vs Melee (median bars)', fontsize=9, loc='left')
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'levels.png'), dpi=120)
    summary = {g[0]: dict(n=len(g[1]), median=round(float(np.median(g[1])), 1), min=round(float(np.min(g[1])), 1),
                          max=round(float(np.max(g[1])), 1)) for g in groups}
    json.dump(dict(groups=summary, ab=log), open(os.path.join(OUT, 'levels.json'), 'w'), indent=1)
    for k, v in summary.items(): print(f'  {k:32s} n={v["n"]:3d} median {v["median"]:6.1f}  range {v["min"]:6.1f} .. {v["max"]:6.1f}')


if __name__ == '__main__':
    main()
