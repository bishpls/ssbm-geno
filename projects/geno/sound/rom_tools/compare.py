"""Aligned spectrogram comparison: a separated SNES reference clip against candidate clean files (best band-normalised
lag), for visual confirmation. usage: compare.py OUT.png REF_NAME CAND [CAND ...]"""
import os, sys, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import match as M

def best_lag(Dr, Dc):
    Rz, Cz = M.z(Dr), M.z(Dc)
    lags, sc, ov = M.xcorr_all(Rz, Cz)
    m = ov >= int(0.6 * min(Rz.shape[1], Cz.shape[1]))
    i = np.argmax(np.where(m, sc, -9)); lag = int(lags[i])
    best = max(((M.pearson_at(Dr, Dc, lag + d)[0], lag + d) for d in range(-3, 4)))
    return best[1], best[0]

def show(ax, D, t0, title):
    ax.imshow(D, origin='lower', aspect='auto', extent=[t0, t0 + D.shape[1] * M.HOP / M.SR, 0, 64], cmap='magma')
    ax.set_title(title, fontsize=8); ax.tick_params(labelsize=6); ax.grid(alpha=0.2)

if __name__ == '__main__':
    out, ref = sys.argv[1], sys.argv[2]; cands = sys.argv[3:]
    xr = M.load(os.path.join(M.CLIPS, ref + '.wav')); Dr = M.mel(xr)
    fig, axs = plt.subplots(1 + len(cands), 1, figsize=(14, 2.1 * (1 + len(cands))))
    show(axs[0], Dr, 0, f'REF {ref} (separated, SNES video)')
    for ax, c in zip(axs[1:], cands):
        xc = M.load(os.path.join(M.CLEAN, c + '.wav')); Dc = M.mel(xc)
        lag, p = best_lag(Dr, Dc)
        # show the candidate shifted so the aligned part sits under the reference
        show(ax, Dc, -lag * M.HOP / M.SR, f'{c}  r={p:.2f}  (ref starts at {lag * M.HOP / M.SR:+.2f}s in the file)')
    for ax in axs:
        ax.set_xlim(-0.1, max(Dr.shape[1] * M.HOP / M.SR, 0.5) + 0.3)
    plt.tight_layout(); plt.savefig(out, dpi=62); plt.close()
