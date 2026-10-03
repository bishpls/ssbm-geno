"""Signal chains and the mix bus (48 kHz). Guitars go through NAM captures (amps/), everything else through pedalboard."""
import numpy as np
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
from pedalboard import (Pedalboard, HighpassFilter, LowpassFilter, PeakFilter, LowShelfFilter, HighShelfFilter,
                        Compressor, Gain, Reverb, Delay, Limiter, Distortion, NoiseGate)
import pyloudnorm as pyln
import sys
from nam import NAM

SR = 48000
AMPS = os.path.join(MUSIC, 'amps/')
_cache = {}


def amp(name):
    if name not in _cache:
        _cache[name] = NAM(AMPS + name)
    return _cache[name]


RHYTHM_AMP = 'Phillipe P Bugera6262-Lead-NoDrive-Cab-ESR0,009.nam'   # 5150-style lead channel, cab included
LEAD_AMP = 'Phillipe P Bug1990-Lead-NoDrive-Cab-ESR0,011.nam'        # JCM-style lead, cab included
RHYTHM_AMP_R = 'Phillipe P Bug333-Lead-NoDrive-Cab-ESR0,007.nam'
BASS_DRIVE = 'Jason Z Tech21 dUg DP3X bass preamp pedal all dimed no shift.nam'


def norm_peak(x, p):
    m = np.abs(x).max()
    return x * (p / m) if m > 0 else x


def rhythm_chain(di, drive=0.45, tight=True, amp_name=None):
    x = norm_peak(di, drive)
    if tight:  # tube-screamer style tightening before the amp: cut lows, push mids
        x = Pedalboard([HighpassFilter(110), PeakFilter(750, 4.0, 0.8)])(x[None], SR)[0]
        x = norm_peak(x, drive)
    y = amp(amp_name or RHYTHM_AMP)(x)
    post = Pedalboard([HighpassFilter(80), LowpassFilter(8500), PeakFilter(300, -2.0, 1.0), PeakFilter(420, -1.5, 1.0), PeakFilter(1900, -3.0, 0.8),
                       NoiseGate(threshold_db=-55, ratio=4, release_ms=60)])
    return post(y[None], SR)[0]


def lead_chain(di, drive=0.3):
    x = norm_peak(di, drive)
    x = Pedalboard([HighpassFilter(180), PeakFilter(800, 2.5, 0.8), LowpassFilter(6000)])(x[None], SR)[0]
    x = norm_peak(x, drive)
    y = amp(LEAD_AMP)(x)
    return Pedalboard([HighpassFilter(200), HighpassFilter(200), LowpassFilter(8000), PeakFilter(1000, -2.5, 0.9), PeakFilter(3300, -3.0, 1.2)])((y - np.mean(y))[None], SR)[0]


def bass_chain(di):
    x = norm_peak(di, 0.5)
    low = Pedalboard([LowpassFilter(220), Compressor(-18, 4, 5, 80)])(x[None], SR)[0]
    d = amp(BASS_DRIVE)(norm_peak(x, 0.4))
    grit = Pedalboard([HighpassFilter(500), LowpassFilter(4500)])(d[None], SR)[0]
    y = norm_peak(low, 0.7) + 0.5 * norm_peak(grit, 0.7)
    return Pedalboard([Compressor(-14, 3, 10, 120), HighpassFilter(32)])(y[None], SR)[0]


def space(x, delay_s=0.225, fb=0.25, mix=0.16, room=0.35, wet=0.14):
    st = np.vstack([x, x])
    b = Pedalboard([Delay(delay_s, fb, mix), Reverb(room_size=room, damping=0.6, wet_level=wet, dry_level=1 - wet * 0.5, width=1.0)])
    return b(st, SR)


def pan(x, p):
    """equal-power pan, p in [-1, 1] -> (2, n)"""
    a = (p + 1) * np.pi / 4
    return np.vstack([np.cos(a) * x, np.sin(a) * x])


def db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def limiter(x, ceiling_db=-1.0, look_ms=1.5, release_ms=60, sr=SR):
    """lookahead peak limiter: gain = min(1, ceiling/peak) over a lookahead window, smoothed (instant attack in the
    lookahead, exponential release). x: (2, n)"""
    from scipy.ndimage import maximum_filter1d
    from scipy.signal import lfilter
    c = 10 ** (ceiling_db / 20)
    la = max(1, int(look_ms * sr / 1000))
    pk = np.abs(x).max(0)
    pk = maximum_filter1d(pk, size=2 * la + 1)
    g = np.minimum(1.0, c / (pk + 1e-12))
    # release smoothing: follow drops instantly, recover with a one-pole
    a = np.exp(-1.0 / (release_ms * sr / 1000))
    out = np.empty_like(g); cur = 1.0
    # vectorised approximation: run the one-pole on (1-g) with max-hold
    r = lfilter([1 - a], [1, -a], g)
    out = np.minimum(g, r)
    out = np.minimum(out, g)
    y = x * out[None]
    return np.clip(y, -c, c)


def match_eq(x, amount=0.75, max_db=8.0, ref=os.path.join(DATA, 'ref_tonal_curve.json')):
    """reference-matching EQ: move the mix's long-term 1/6-octave spectrum toward the metal reference curve
    (partial, clamped, smoothed), applied as a linear-phase FIR. x: (2, n)"""
    import json
    from scipy.signal import firwin2, fftconvolve
    from scipy.ndimage import gaussian_filter1d
    R = json.load(open(ref)); fc = np.array(R['freqs']); target = np.array(R['db'])
    mono = x.mean(0)
    N = 16384; hop = 4096
    frames = np.lib.stride_tricks.sliding_window_view(mono, N)[::hop] * np.hanning(N)
    P = (np.abs(np.fft.rfft(frames, axis=1)) ** 2).mean(0); fr = np.fft.rfftfreq(N, 1 / SR)
    ours = np.array([10 * np.log10(P[(fr >= c / 2 ** (1 / 12)) & (fr < c * 2 ** (1 / 12))].sum() + 1e-12) for c in fc])
    mid = (fc > 200) & (fc < 4000); ours = ours - ours[mid].mean()
    g = np.clip((target - ours) * amount, -max_db, max_db)
    g = gaussian_filter1d(g, 1.5)
    g[fc < 30] = np.minimum(g[fc < 30], 0)           # never boost sub-bass
    freqs = np.concatenate([[0], fc, [SR / 2]]); gains = 10 ** (np.concatenate([[g[0]], g, [g[-1]]]) / 20)
    h = firwin2(4097, freqs / (SR / 2), gains)
    y = np.vstack([fftconvolve(ch, h, mode='same') for ch in x]).astype(np.float32)
    return y, dict(zip(fc.round(0).astype(int).tolist(), g.round(1).tolist()))


def match_eq_fir(x, amount=0.75, max_db=8.0, ref=os.path.join(DATA, 'ref_tonal_curve.json')):
    """the FIR of match_eq, computed from x, so it can be applied identically to stems (it is linear)"""
    import json
    from scipy.signal import firwin2
    from scipy.ndimage import gaussian_filter1d
    R = json.load(open(ref)); fc = np.array(R['freqs']); target = np.array(R['db'])
    mono = x.mean(0); N = 16384; hop = 4096
    frames = np.lib.stride_tricks.sliding_window_view(mono, N)[::hop] * np.hanning(N)
    P = (np.abs(np.fft.rfft(frames, axis=1)) ** 2).mean(0); fr = np.fft.rfftfreq(N, 1 / SR)
    ours = np.array([10 * np.log10(P[(fr >= c / 2 ** (1 / 12)) & (fr < c * 2 ** (1 / 12))].sum() + 1e-12) for c in fc])
    mid = (fc > 200) & (fc < 4000); ours = ours - ours[mid].mean()
    g = gaussian_filter1d(np.clip((target - ours) * amount, -max_db, max_db), 1.5)
    g[fc < 30] = np.minimum(g[fc < 30], 0)
    freqs = np.concatenate([[0], fc, [SR / 2]]); gains = 10 ** (np.concatenate([[g[0]], g, [g[-1]]]) / 20)
    return firwin2(4097, freqs / (SR / 2), gains)


def limiter_gain(x, ceiling_db=-1.0, look_ms=1.5, release_ms=60, sr=SR):
    """the gain curve limiter() applies (so stems can share it)"""
    from scipy.ndimage import maximum_filter1d
    from scipy.signal import lfilter
    c = 10 ** (ceiling_db / 20)
    la = max(1, int(look_ms * sr / 1000))
    pk = maximum_filter1d(np.abs(x).max(0), size=2 * la + 1)
    g = np.minimum(1.0, c / (pk + 1e-12))
    a = np.exp(-1.0 / (release_ms * sr / 1000))
    r = lfilter([1 - a], [1, -a], g)
    return np.minimum(g, r)


def master(mixst, lufs=-10.0, ceiling=-1.0, match=True):
    x = Pedalboard([HighpassFilter(32), HighpassFilter(32)])(mixst.astype(np.float32), SR)
    if match:
        x, eqc = match_eq(x)
    bus = Pedalboard([Compressor(-16, 2.0, 25, 180)])
    y = bus(x.astype(np.float32), SR)
    meter = pyln.Meter(SR)
    L = meter.integrated_loudness(y.T)
    y = y * 10 ** ((lufs - L) / 20)
    for _ in range(3):   # limiting lowers loudness: re-aim and re-limit
        z = limiter(y, ceiling)
        Lz = meter.integrated_loudness(z.T)
        if abs(Lz - lufs) < 0.3: break
        y = y * 10 ** ((lufs - Lz) / 20)
    y = z
    return y, meter.integrated_loudness(y.T)
