"""Loudness, peak, stereo and envelope landmarks of a WAV (the same measures as the vanilla fanfare table)."""
import sys, json, numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import resample_poly

def measure(path):
    x, sr = sf.read(path, always_2d=True); x = x.astype(np.float64)
    L = pyln.Meter(sr).integrated_loudness(x)
    tp = 20 * np.log10(np.abs(resample_poly(x, 4, 1, axis=0)).max())
    m, s = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    hop = int(0.05 * sr)
    rms = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop, hop)])
    db = 20 * np.log10(rms + 1e-9); top = db.max()
    last = lambda k: round(float(np.where(db > top - k)[0][-1] * 0.05), 2)
    # short-term loudness (3 s) max, momentary max
    return dict(file=path.split('/')[-1], dur=round(len(x) / sr, 2), sr=sr, lufs=round(L, 1), tp=round(tp, 1),
                corr=round(float(np.corrcoef(x[:, 0], x[:, 1])[0, 1]), 2),
                side_db=round(float(10 * np.log10(np.sum(s ** 2) / np.sum(m ** 2))), 1),
                last_within20=last(20), last_within40=last(40), last_within60=last(60))

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(json.dumps(measure(p)))

def contour(path, step=0.2, win=0.4):
    """momentary loudness (400 ms, K-weighted) every `step` s"""
    x, sr = sf.read(path, always_2d=True)
    meter = pyln.Meter(sr, block_size=win)
    out = []
    for t in np.arange(0, len(x) / sr - win, step):
        seg = x[int(t * sr):int((t + win) * sr)]
        try: out.append((round(float(t), 2), round(meter.integrated_loudness(seg), 1)))
        except Exception: out.append((round(float(t), 2), -99))
    return out

BANDS = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 12500]

def ltas(path):
    """long-term spectrum in octave bands (dB, normalised to the 1 kHz band) over the non-silent part"""
    from scipy.signal import welch
    x, sr = sf.read(path, always_2d=True); x = x.mean(1)
    f, P = welch(x, sr, nperseg=8192)
    out = []
    for fc in BANDS:
        lo, hi = fc / 2 ** 0.5, min(fc * 2 ** 0.5, sr / 2 - 1)
        mm = (f >= lo) & (f < hi)
        out.append(10 * np.log10(P[mm].sum() + 1e-20))
    ref = out[BANDS.index(1000)]
    return [round(v - ref, 1) for v in out]
