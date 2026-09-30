"""Loudness and brightness measures shared by the synth and the Melee reference check.

All measures run at 32 kHz (Melee's mixer rate), so a 16 kHz sample is upsampled first, as the AX resampler would.
- peak:     sample peak, dBFS
- lufs:     max momentary loudness (BS.1770 K-weighting, 400 ms window, 50 ms hop, padded), the sfxbank NOTES' measure
- short:    max loudness over 100 ms K-weighted windows (10 ms hop): closer to how a short click is heard
- centroid: energy-weighted spectral centroid, Hz
- hf:       share of energy above 4 kHz, dB relative to the total (brightness)
- harsh:    share of energy in 2.5-5 kHz (the ear's most sensitive band), dB relative to the total
"""
import numpy as np
import pyloudnorm as pyln
from scipy.signal import resample_poly, lfilter

SR = 32000


def to32k(x, rate):
    if rate == SR: return np.asarray(x, dtype=np.float64)
    from math import gcd
    g = gcd(int(rate), SR)
    return resample_poly(np.asarray(x, dtype=np.float64), SR // g, int(rate) // g)


_meter = pyln.Meter(SR, block_size=0.4)


def momentary_max(y):
    w, h = int(0.4 * SR), int(0.05 * SR)
    yy = np.pad(y, (0, max(0, w - len(y))))
    return max(_meter.integrated_loudness(yy[i:i + w]) for i in range(0, len(yy) - w + 1, h))


def _kweight(y):
    for f in _meter._filters.values():
        y = lfilter(f.b, f.a, y)
    return y


def short_max(y, win=0.1, hop=0.01):
    k = _kweight(np.pad(y, (0, int(win * SR))))
    w, h = int(win * SR), int(hop * SR)
    ms = max(np.mean(k[i:i + w] ** 2) for i in range(0, len(k) - w + 1, h))
    return -0.691 + 10 * np.log10(ms + 1e-20)


def spectrum_stats(y):
    Y = np.abs(np.fft.rfft(y * np.hanning(len(y)), n=max(4096, 1 << int(np.ceil(np.log2(len(y))))))) ** 2
    f = np.fft.rfftfreq(2 * (len(Y) - 1), 1 / SR)
    tot = Y.sum() + 1e-20
    return float((f * Y).sum() / tot), 10 * np.log10(Y[f > 4000].sum() / tot + 1e-20), \
        10 * np.log10(Y[(f > 2500) & (f < 5000)].sum() / tot + 1e-20)


OCT = (125, 250, 500, 1000, 2000, 4000, 8000)


def bands(y):
    """Octave-band energy (dB relative to the total) at OCT centres."""
    Y = np.abs(np.fft.rfft(y * np.hanning(len(y)), 1 << 15)) ** 2
    f = np.fft.rfftfreq(1 << 15, 1 / SR); tot = Y.sum() + 1e-20
    return [round(10 * np.log10(Y[(f >= c / 2 ** 0.5) & (f < c * 2 ** 0.5)].sum() / tot + 1e-12), 1) for c in OCT]


def measure(y):
    c, hf, harsh = spectrum_stats(y)
    return dict(peak=round(20 * np.log10(np.abs(y).max() + 1e-20), 2), lufs=round(momentary_max(y), 2),
                short=round(short_max(y), 2), centroid=round(c), hf=round(hf, 1), harsh=round(harsh, 1), bands=bands(y))
