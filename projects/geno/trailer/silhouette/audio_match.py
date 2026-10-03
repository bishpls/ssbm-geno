"""Is a reference sound in a capture's audio, and where: the peak normalised cross-correlation of the two signals' onset
envelopes (8 kHz mono, 10 ms hops), and its time in the capture.
    audio_match.py CAPTURE.wav REF.wav [REF2.wav ...]"""
import sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly, fftconvolve


def env(path, sr=8000, hop=80):
    r, y = wavfile.read(path)
    y = y.astype(np.float64)
    if y.ndim > 1: y = y.mean(axis=1)
    y /= (np.abs(y).max() or 1)
    from math import gcd
    g = gcd(int(r), sr); y = resample_poly(y, sr // g, int(r) // g)
    n = len(y) // hop
    e = np.sqrt((y[:n * hop].reshape(n, hop) ** 2).mean(axis=1))
    d = np.maximum(np.diff(e, prepend=e[0]), 0)            # onsets
    return d, sr / hop


cap, fps = env(sys.argv[1])
for ref in sys.argv[2:]:
    r, _ = env(ref)
    r = r[:min(len(r), len(cap))]
    num = fftconvolve(cap, r[::-1], mode='valid')
    c2 = np.convolve(cap ** 2, np.ones(len(r)), mode='valid')
    corr = num / (np.sqrt(c2 * (r ** 2).sum()) + 1e-12)
    k = int(np.argmax(corr))
    print(f'{ref.split("/")[-1]}: peak {corr[k]:.2f} at {k / fps:.2f} s (median {np.median(corr):.2f})')
