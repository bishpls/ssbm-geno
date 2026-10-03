"""CQT images of WAVs, stacked, with a 16th grid (0.099 s) and bar lines."""
import sys, numpy as np, soundfile as sf, librosa, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
out = sys.argv[1]; files = sys.argv[2:]
fig, axs = plt.subplots(len(files), 1, figsize=(24, 4.2 * len(files)), squeeze=False)
for ax, f in zip(axs[:, 0], files):
    y, sr = sf.read(f, always_2d=True); y = y.mean(1)
    C = librosa.amplitude_to_db(np.abs(librosa.cqt(y, sr=sr, hop_length=256, fmin=librosa.note_to_hz('C1'), n_bins=96)), ref=np.max)
    ax.imshow(C, aspect='auto', origin='lower', vmin=-60, vmax=0, cmap='magma', extent=[0, len(y) / sr, 0, 96])
    ax.set_yticks(range(0, 96, 12)); ax.set_yticklabels(['C%d' % o for o in range(1, 9)])
    for b in range(8): ax.axvline(b * 1.584, color='c', lw=0.6, alpha=0.6)
    ax.set_title(f.split('/')[-2] + '/' + f.split('/')[-1]); ax.set_xticks(np.arange(0, len(y) / sr, 0.5))
plt.tight_layout(); plt.savefig(out, dpi=55)
