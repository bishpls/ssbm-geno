"""Spectrogram + pitch + intensity plot with a fine time grid, for locating phone boundaries."""
import sys, numpy as np, parselmouth, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from parselmouth.praat import call

def plot(path, out, t0=None, t1=None, title=None, fmax=6000):
    snd = parselmouth.Sound(path)
    if t0 is not None: snd = snd.extract_part(t0, t1, preserve_times=True)
    x = snd.values[0]; sr = snd.sampling_frequency; ts = snd.xs()
    spec = snd.to_spectrogram(window_length=0.004, maximum_frequency=fmax, time_step=0.001, frequency_step=20)
    pitch = snd.to_pitch_ac(time_step=0.005, pitch_floor=180, pitch_ceiling=650)
    inten = snd.to_intensity(minimum_pitch=200, time_step=0.005)
    fmt = snd.to_formant_burg(time_step=0.005, max_number_of_formants=5, maximum_formant=5500, window_length=0.025)
    fig, ax = plt.subplots(3, 1, figsize=(16, 9), sharex=True, gridspec_kw=dict(height_ratios=[1, 3, 1.2]))
    ax[0].plot(ts, x, lw=0.4, color='k'); ax[0].set_ylabel('wave')
    S = 10 * np.log10(np.maximum(spec.values, 1e-12))
    ax[1].imshow(S, origin='lower', aspect='auto', extent=[spec.xmin, spec.xmax, 0, fmax], cmap='Greys', vmin=S.max() - 70, vmax=S.max())
    ft = fmt.xs()
    for k, c in zip(range(1, 4), ['r', 'g', 'b']):
        v = np.array([fmt.get_value_at_time(k, t) for t in ft])
        ax[1].plot(ft, v, '.', ms=2, color=c)
    ax[1].set_ylabel('Hz')
    f0 = pitch.selected_array['frequency']; f0[f0 == 0] = np.nan
    ax[2].plot(pitch.xs(), f0, 'b.-', ms=3, lw=0.6); ax[2].set_ylabel('F0', color='b')
    a2 = ax[2].twinx(); a2.plot(inten.xs(), inten.values[0], 'r', lw=0.8); a2.set_ylabel('dB', color='r')
    for a in ax:
        a.set_xticks(np.arange(np.floor(ts[0] * 20) / 20, ts[-1], 0.05))
        a.set_xticks(np.arange(np.floor(ts[0] * 100) / 100, ts[-1], 0.01), minor=True)
        a.grid(True, which='major', alpha=0.5); a.grid(True, which='minor', alpha=0.15)
    ax[0].set_title(title or path)
    plt.tight_layout(); plt.savefig(out, dpi=80); plt.close()

if __name__ == '__main__':
    p, o = sys.argv[1], sys.argv[2]
    t0 = float(sys.argv[3]) if len(sys.argv) > 3 else None
    t1 = float(sys.argv[4]) if len(sys.argv) > 4 else None
    plot(p, o, t0, t1)
