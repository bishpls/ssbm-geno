import sys, os, json, numpy as np, soundfile as sf, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
from hf0 import hf0
HERE = os.path.expanduser(os.environ.get('ANNOUNCER_WORK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'announcer')))   # the work folder (game audio)
def plot(names, out, refs=()):
    meta = json.load(open(os.path.join(HERE, 'cands', 'meta.json')))
    items = [(n, os.path.join(HERE, 'cands', n + '.wav'), meta[n]['joins'], meta[n]['labels']) for n in names]
    items += [(r, os.path.join(HERE, 'src', r + '.wav'), [], []) for r in refs]
    fig, axs = plt.subplots(len(items), 1, figsize=(15, 3.3 * len(items)))
    axs = np.atleast_1d(axs)
    for ax, (n, p, joins, labels) in zip(axs, items):
        x, sr = sf.read(p)
        import librosa
        S = librosa.stft(x, n_fft=512, hop_length=12, win_length=96)
        D = 20 * np.log10(np.abs(S) + 1e-6)
        ax.imshow(D, origin='lower', aspect='auto', extent=[0, len(x) / sr, 0, sr / 2], cmap='gray_r', vmin=D.max() - 65, vmax=D.max())
        t, f0, sc, v = hf0(x, sr, hop=0.005)
        f = f0.copy(); f[~v] = np.nan
        ax2 = ax.twinx(); ax2.plot(t, f, 'r.-', ms=2, lw=0.8); ax2.set_ylim(100, 450); ax2.set_ylabel('F0', color='r')
        for j in joins: ax.axvline(j, color='c', lw=1.2)
        ax.set_title(n + ('   ' + ' | '.join(labels) if labels else ''))
        L=max(0.85,len(x)/sr); ax.set_xlim(0, L); ax.set_xticks(np.arange(0, L, 0.05)); ax.grid(alpha=0.2)
    plt.tight_layout(); plt.savefig(out, dpi=62); plt.close()
if __name__ == '__main__':
    out = sys.argv[1]; names = [a for a in sys.argv[2:] if not a.startswith('ref:')]
    refs = [a[4:] for a in sys.argv[2:] if a.startswith('ref:')]
    plot(names, out, refs)
