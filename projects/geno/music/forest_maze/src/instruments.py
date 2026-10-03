"""Instruments authored in code, all at 48 kHz:
  ks_string  : Karplus-Strong plucked string (fractional-delay tuned), pick-position comb, palm-mute damping
  guitar_di  : a DI electric guitar part from note events (strings of a power chord are separate KS voices)
  lead_di    : a sustaining lead-guitar DI from an oscillator with string-like spectral decay, vibrato, slides, bends
  bass_di    : a picked bass DI (KS, heavier), for amp/drive processing
Everything is deterministic given a seed."""
import numpy as np
from scipy.signal import lfilter, butter, sosfilt

SR = 48000


def m2f(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def ks_string(f0, dur, vel=1.0, mute=0.0, pick=0.13, bright=0.5, seed=0, decay=None, sr=SR, release=0.03):
    """One plucked string. mute 0..1 = palm-mute amount (short decay, dark). Returns float32 array of len dur+tail."""
    rng = np.random.default_rng(seed)
    n = int((dur + (0.08 if mute > 0.5 else 0.25)) * sr)
    P = sr / f0
    # loop filter: one-zero lowpass a*y[n] + (1-a)*y[n-1] (delay 1-a), gain g; tuning with first-order allpass
    a = 0.5 + 0.45 * bright * (1 - 0.8 * mute)            # higher a = brighter (less averaging)
    lp_delay = (1 - a)
    if decay is None:
        decay = (1.4 if mute < 0.5 else 0.12) * (110 / f0) ** 0.35 * (1 - 0.6 * mute) + 0.05
    # per-period gain from a t60-ish decay
    g = 10 ** (-3 / (decay * f0)) if decay > 0 else 0.99
    N = int(np.floor(P - lp_delay - 0.1)); frac = P - lp_delay - N
    c = (1 - frac) / (1 + frac)                              # allpass coefficient for delay `frac`
    # excitation: noise burst one period long, lowpassed by velocity, with pick-position comb
    L = max(2, int(P))
    exc = rng.uniform(-1, 1, L)
    b1 = 0.3 + 0.6 * vel * (1 - 0.5 * mute)
    exc = lfilter([b1], [1, -(1 - b1)], exc)
    d = max(1, int(pick * P))
    exc = exc - np.concatenate([np.zeros(d), exc[:-d]])
    x = np.zeros(n); x[:L] = exc * vel
    # denominator: (1 + c z^-1) - g z^-N (a + (1-a) z^-1)(c + z^-1)
    den = np.zeros(N + 3); den[0] = 1; den[1] += c
    fb = np.convolve([a, 1 - a], [c, 1])                     # 3 taps
    den[N:N + 3] -= g * fb
    y = lfilter([1, c], den, x)
    # note-off damping (fingers/palm lift): fast fade after dur
    k = int(dur * sr)
    if k < n:
        rel = int(release * sr)
        env = np.ones(n); env[k:k + rel] = np.linspace(1, 0, min(rel, n - k)); env[k + rel:] = 0
        y *= env
        y = y[:k + rel]
    return y.astype(np.float32)


def pickup(y, sr=SR):
    """Bridge humbucker-ish colour: resonant peak ~3.2 kHz, gentle HF rolloff, remove DC/sub."""
    sos = np.vstack([butter(2, 60, 'high', fs=sr, output='sos'), butter(2, 5200, 'low', fs=sr, output='sos')])
    y = sosfilt(sos, y)
    # resonant bump via a narrow band boost
    b = butter(2, [2800, 3700], 'band', fs=sr, output='sos')
    return (y + 0.6 * sosfilt(b, y)).astype(np.float32)


def place(buf, sig, t, gain=1.0, sr=SR):
    i = int(round(t * sr))
    if i >= len(buf): return
    j = min(len(buf), i + len(sig))
    buf[i:j] += gain * sig[:j - i]


def guitar_di(events, total, seed=0, humanize=0.006, sr=SR, tuning_cents=0.0):
    """events: list of dicts {t, dur, notes:[midi...], vel, mute}. Strum: low to high string offsets ~4 ms."""
    rng = np.random.default_rng(seed)
    buf = np.zeros(int(total * sr) + sr, np.float32)
    for k, e in enumerate(events):
        t = e['t'] + rng.normal(0, humanize)
        strum = e.get('strum', 0.004 if e.get('mute', 0) < 0.5 else 0.0015)
        for si, m in enumerate(sorted(e['notes'])):
            f = m2f(m + tuning_cents / 100 + rng.normal(0, 0.03))
            v = e.get('vel', 0.9) * (1 + rng.normal(0, 0.06))
            s = ks_string(f, e['dur'], vel=min(1.2, v), mute=e.get('mute', 0.0), pick=rng.uniform(0.1, 0.16),
                          bright=e.get('bright', 0.6), seed=int(rng.integers(1e9)))
            place(buf, s, max(0, t + si * strum), gain=1.0 / (1 + 0.25 * si))
    return pickup(buf[:int(total * sr)], sr)


def lead_di(notes, total, seed=0, sr=SR, vib_rate=5.6, vib_depth=0.28, slide=0.035, bend_long=0.0):
    """notes: list of (t, dur, midi, vel[, flags]) monophonic; legato when next starts <= end of previous.
    Additive saw-like source (bandlimited to 9 kHz) with per-note spectral decay; vibrato fades in on notes > 0.3 s;
    legato notes slide in over `slide` s; bend_long>0 bends long notes up from a semitone below."""
    rng = np.random.default_rng(seed)
    n = int(total * sr)
    pitch = np.full(n, np.nan); amp = np.zeros(n); bright = np.zeros(n); beta = np.full(n, 0.14)
    notes = sorted(notes, key=lambda x: x[0])
    for i, nt in enumerate(notes):
        t, d, m, v = nt[:4]; flags = nt[4] if len(nt) > 4 else {}
        i0 = int(t * sr); i1 = min(n, int((t + d) * sr))
        if i0 >= n: continue
        L = i1 - i0; tt = np.arange(L) / sr
        p = np.full(L, float(m))
        prev = notes[i - 1] if i > 0 else None
        legato = prev is not None and prev[0] + prev[1] >= t - 0.04 and not flags.get('pick', False)
        if legato:
            k = min(L, int(slide * sr)); p[:k] = prev[2] + (m - prev[2]) * (0.5 - 0.5 * np.cos(np.pi * np.arange(k) / k))
        bend = flags.get('bend', bend_long if d > 0.5 else 0)
        if bend:
            k = min(L, int(0.12 * sr)); p[:k] = m - bend + bend * np.sin(0.5 * np.pi * np.arange(k) / k)
        if d > 0.28:
            depth = flags.get('vib', vib_depth) * np.clip((tt - 0.18) / 0.25, 0, 1)
            p += depth * np.sin(2 * np.pi * (vib_rate + rng.normal(0, 0.3)) * tt + rng.uniform(0, 6))
        pitch[i0:i1] = p
        if not legato: beta[i0:] = rng.uniform(0.1, 0.2)
        nxt = notes[i + 1] if i + 1 < len(notes) else None
        joined = nxt is not None and nxt[0] - (t + d) < 0.04          # next note follows: no release gap
        env = 0.72 + 0.28 * np.exp(-tt / 0.09)
        if not legato:
            k = min(L, int(0.006 * sr)); env[:k] *= np.linspace(0, 1, k) ** 2
        if not joined:
            rel = min(L, int(0.03 * sr)); env[-rel:] *= np.linspace(1, 0, rel) ** 1.5
        amp[i0:i1] = v * env
        if joined and nxt[0] > t + d:   # bridge the tiny gap
            j1 = min(n, int(nxt[0] * sr)); amp[i1:j1] = v * env[-1]; pitch[i1:j1] = p[-1]
        bright[i0:i1] = np.exp(-tt / 0.6) if not legato else bright[i0 - 1] * np.exp(-tt / 0.6) if i0 > 0 else np.exp(-tt / 0.6)
    # fill pitch gaps (hold last) for phase continuity
    idx = np.where(~np.isnan(pitch))[0]
    if len(idx) == 0: return np.zeros(n, np.float32)
    pitch = np.interp(np.arange(n), idx, pitch[idx])
    flutter = sosfilt(butter(1, 6, 'low', fs=sr, output='sos'), rng.normal(0, 1, n)); flutter *= 0.05 / (np.std(flutter) + 1e-9)
    pitch = pitch + flutter
    f = m2f(pitch)
    ph = 2 * np.pi * np.cumsum(f) / sr
    sm = butter(2, 45, 'low', fs=sr, output='sos')           # ~4 ms smoothing of control signals (no clicks)
    amp = sosfilt(sm, amp); bright = sosfilt(sm, bright)
    y = np.zeros(n)
    for h in range(1, 40):
        fh = f * h
        mask = np.clip((9000 - fh) / 2500, 0, 1)
        if not mask.any(): break
        roll = (1.0 / h) * (0.5 + 0.5 * bright) ** (h / 4) * (0.25 + 0.75 * np.abs(np.sin(np.pi * h * beta)))
        y += mask * roll * np.sin(h * ph + h * 0.7 + 0.3 * np.sin(h))
    y *= amp
    # a real plucked-string transient under each picked note (KS, first 60 ms)
    for i, nt in enumerate(notes):
        prev = notes[i - 1] if i > 0 else None
        if prev is not None and prev[0] + prev[1] >= nt[0] - 0.04 and not (len(nt) > 4 and nt[4].get('pick')): continue
        ks = ks_string(m2f(nt[2]), 0.06, vel=nt[3], bright=0.7, seed=int(rng.integers(1e9)), release=0.03)
        i0 = int(nt[0] * sr); e = min(n, i0 + len(ks))
        if i0 < n: y[i0:e] += 0.6 * ks[:e - i0] / (np.abs(ks).max() + 1e-9) * np.linspace(1, 0, e - i0)
    # pick noise at picked note starts (high-passed, short)
    hp = butter(2, 2500, 'high', fs=sr, output='sos')
    for i, nt in enumerate(notes):
        t = nt[0]; i0 = int(t * sr)
        prev = notes[i - 1] if i > 0 else None
        if prev is not None and prev[0] + prev[1] >= t - 0.01: continue
        if i0 < n - 300:
            y[i0:i0 + 300] += nt[3] * 0.05 * sosfilt(hp, rng.uniform(-1, 1, 300)) * np.exp(-np.arange(300) / 60)
    return pickup(y.astype(np.float32), sr)


def bass_di(events, total, seed=0, sr=SR):
    """events: (t, dur, midi, vel, mute). KS with a darker loop and a longer, thicker excitation."""
    rng = np.random.default_rng(seed)
    buf = np.zeros(int(total * sr) + sr, np.float32)
    for (t, d, m, v, mute) in events:
        s = ks_string(m2f(m), d, vel=v, mute=mute, pick=0.2, bright=0.35, seed=int(rng.integers(1e9)),
                      decay=2.5 if mute < 0.5 else 0.25, release=0.02)
        place(buf, s, max(0, t + rng.normal(0, 0.003)))
    sos = butter(2, 30, 'high', fs=sr, output='sos')
    return sosfilt(sos, buf[:int(total * sr)]).astype(np.float32)
