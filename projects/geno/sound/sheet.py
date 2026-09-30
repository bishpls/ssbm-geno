"""Contact sheets: waveform + spectrogram per sound, at the effective level (script vol applied), so the sheet reads as
the game will play them. Optionally Melee's reference sounds on the same scale for an A/B.

    .venv/bin/python projects/geno/sound/sheet.py [--decoded DIR] [--refs] [--out PNG]
"""
import os, sys, json, glob, argparse
import numpy as np, soundfile as sf
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
from loud import to32k

WORK = os.path.expanduser('~/games/melee/work/sfxbank/synth')


def cell(ax_w, ax_s, x, title, vmin=-100):
    t = np.arange(len(x)) / 32000 * 1000
    ax_w.plot(t, x, lw=0.5, color='#1f4e79'); ax_w.set_ylim(-0.6, 0.6); ax_w.set_xlim(0, 420)
    ax_w.axhline(0, color='#aaa', lw=0.3); ax_w.set_title(title, fontsize=7, loc='left'); ax_w.set_xticks([]); ax_w.set_yticks([])
    ax_s.specgram(np.pad(x, (0, max(0, 13440 - len(x)))) + 1e-7 * np.random.default_rng(0).standard_normal(max(13440, len(x))), NFFT=256, Fs=32000, noverlap=224, cmap='magma', vmin=vmin, vmax=-20)
    ax_s.set_ylim(0, 12000); ax_s.set_xlim(0, 0.42); ax_s.set_yticks([0, 4000, 8000]); ax_s.set_yticklabels(['0', '4k', '8k'], fontsize=5)
    ax_s.set_xticks([0, 0.1, 0.2, 0.3, 0.4]); ax_s.set_xticklabels(['0', '100', '200', '300', '400 ms'], fontsize=5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--decoded', help='directory of decoded bank WAVs named like the synth ones (the ADPCM round trip)')
    ap.add_argument('--refs', action='store_true', help="add Melee's movement sounds (effective level) for comparison")
    ap.add_argument('--out', default=os.path.join(WORK, 'plots', 'sheet_synth.png'))
    a = ap.parse_args()
    meta = json.load(open(os.path.join(WORK, 'sounds4.json')))
    items = []
    for m in meta:
        p = os.path.join(a.decoded or os.path.join(WORK, 'wav'), m['file'])
        x, sr = sf.read(p)
        x = to32k(x, sr) * m['vol'] / 255
        items.append((x, f'{m["sound_id"]} {m["name"][5:]}  {m["dur"] * 1000:.0f} ms @{sr // 1000}k  eff {m["eff_short"]:.0f}'))
    if a.refs:
        refs = json.load(open(os.path.join(WORK, 'ref', 'melee_ref.json')))
        for r in refs:
            if r['sound'] >= 100000: continue
            x, sr = sf.read(os.path.join(WORK, 'ref', f'ref_{r["sound"]:03d}.wav'))
            items.append((to32k(x, sr) * r['script_vol'] / 255, f'MELEE {r["sound"]} {r["use"][:26]}  eff {r["eff_short"]:.0f}'))
    cols = 5; rows = -(-len(items) // cols)
    fig = plt.figure(figsize=(cols * 3.2, rows * 2.3))
    gs = fig.add_gridspec(rows * 3, cols, hspace=0.6, wspace=0.12)
    for i, (x, title) in enumerate(items):
        r, c = divmod(i, cols)
        cell(fig.add_subplot(gs[r * 3, c]), fig.add_subplot(gs[r * 3 + 1:r * 3 + 3, c]), x, title)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    fig.savefig(a.out, dpi=110, bbox_inches='tight'); print(a.out)


if __name__ == '__main__':
    main()
