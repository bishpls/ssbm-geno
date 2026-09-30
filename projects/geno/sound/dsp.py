"""Procedural-audio primitives for Geno's movement sounds (a carved wooden doll: hollow body, ball joints, wooden/leather
boots, felt cap, cloth cape). Everything is synthesized from scratch at FS and is a pure function of its parameters and
a numpy Generator, so every sound is reproducible from its seed.

- modal():      struck-wood modal synthesis: a contact-force pulse (Hertz-like half-sine, shorter = harder = brighter)
                convolved with a sum of exponentially damped modes. Mode decay follows a loss factor eta: tau = 1/(pi f eta).
- stick_slip(): a friction oscillator (driver, spring, static/kinetic friction with a noisy surface): the slip events of a
                creaking joint, as an impulse train whose rate follows the driving speed.
- cloth():      band-limited noise with a moving centre, a flutter (flapping) amplitude modulation and optional snaps.
- rattle():     ball joints knocking in their sockets: bouncing sequences of tiny bright ticks (intervals and heights
                shrinking by a restitution coefficient).
"""
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt, sosfiltfilt, resample_poly, lfilter

FS = 48000


def n_(sec): return max(1, int(round(sec * FS)))


def t_(dur): return np.arange(n_(dur)) / FS


def place(y, x, at, gain=1.0):
    """Add x into y at time `at` (s), growing y if needed."""
    o = int(round(at * FS))
    if o + len(x) > len(y): y = np.pad(y, (0, o + len(x) - len(y)))
    y[o:o + len(x)] += gain * x
    return y


def pulse(tau, shape=1.5):
    """A contact force: half-sine^shape of duration tau, unit area (the momentum it transfers)."""
    n = max(2, n_(tau))
    x = np.sin(np.pi * (np.arange(n) + 0.5) / n) ** shape
    return x / x.sum()


def modes_ir(modes, dur, rng=None, jitter=0.0):
    """Impulse response of a set of modes (freq Hz, eta loss factor, gain). jitter: relative random detune per mode."""
    t = t_(dur); h = np.zeros_like(t)
    for f, eta, g in modes:
        if rng is not None and jitter: f = f * (1 + jitter * rng.standard_normal())
        if f > 0.45 * FS: continue
        tau = 1.0 / (np.pi * f * eta)
        h += g * np.exp(-t / tau) * np.sin(2 * np.pi * f * t)
    return h


def modal(modes, hits, dur, rng=None, jitter=0.0, rough=0.0):
    """Strike a modal body. hits: [(time s, force, contact tau s)]. rough: surface-roughness noise riding on each contact
    (relative), which excites the body with a little broadband grain."""
    exc = np.zeros(n_(dur))
    for at, force, tau in hits:
        p = pulse(tau) * force
        if rough and rng is not None:
            p = p * (1 + rough * rng.standard_normal(len(p)))
        exc = place(exc, p, at)
    h = modes_ir(modes, dur, rng, jitter)
    return fftconvolve(exc, h)[:len(exc)]


def noise(dur, rng):
    return rng.standard_normal(n_(dur))


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, min(hi, 0.45 * FS)], 'bandpass', fs=FS, output='sos'), x)


def hp(x, fc, order=2, zero_phase=False):
    s = butter(order, fc, 'highpass', fs=FS, output='sos')
    return sosfiltfilt(s, x) if zero_phase else sosfilt(s, x)


def lp(x, fc, order=2):
    return sosfilt(butter(order, min(fc, 0.45 * FS), 'lowpass', fs=FS, output='sos'), x)


def env_ar(n, attack, decay, curve=1.0):
    """Attack (s) then exponential decay with time constant `decay` (s)."""
    t = np.arange(n) / FS
    a = np.clip(t / max(attack, 1e-6), 0, 1) ** curve
    return a * np.exp(-np.maximum(t - attack, 0) / decay)


def click(tau, rng, lo=2500, amp=1.0):
    """The direct contact click of hard on hard: a very short high-passed noise burst."""
    x = noise(tau * 4, rng) * env_ar(n_(tau * 4), tau * 0.1, tau)
    return amp * hp(x, lo, order=2)


def scuff(dur, rng, lo=1500, hi=7000, attack=0.001):
    """Sole or palm rubbing the floor on contact: a short band-passed noise burst."""
    n = n_(dur)
    return bp(noise(dur, rng), lo, hi, order=2) * env_ar(n, attack, dur / 4)


def mix_db(y, x, db, at=0.0):
    """Add x into y at `at` (s), scaled so its energy sits `db` relative to y's energy."""
    g = np.sqrt(np.sum(y ** 2) / (np.sum(x ** 2) + 1e-20) * 10 ** (db / 10))
    return place(y, x, at, g)


def tv_bandpass(x, fc, q):
    """Time-varying 2-pole resonant bandpass (centre fc[n], constant Q): a state-variable filter, sample by sample."""
    y = np.zeros_like(x); lo = bd = 0.0
    for i in range(len(x)):
        f = 2 * np.sin(np.pi * min(fc[i], 0.2 * FS) / FS)
        hi = x[i] - lo - bd / q
        bd += f * hi; lo += f * bd
        y[i] = bd
    return y


def stick_slip(dur, speed, normal, rng, mu_s=1.0, mu_k=0.62, rough=0.12, k=1.0):
    """Stick-slip friction as slip events. speed(t) and normal(t) are arrays (arbitrary units) over dur.
    The spring force builds at k*speed; it slips when it passes mu_s*N (times a rough-surface factor), dropping to
    mu_k*N. Returns an impulse train (one impulse per slip, height = the force released)."""
    n = n_(dur); out = np.zeros(n); F = 0.0
    thr = mu_s * (1 + rough * rng.standard_normal())
    for i in range(n):
        F += k * speed[i] / FS
        if F >= thr * normal[i]:
            drop = F - mu_k * normal[i]
            out[i] = drop
            F = mu_k * normal[i]
            thr = mu_s * (1 + rough * rng.standard_normal())
    return out


def rattle(start, rng, n_joints=3, d0=(0.010, 0.022), e=(0.55, 0.75), amp0=1.0, bounces=(4, 8),
           modes_base=None, tau=0.00025, spread=0.012, dur=0.25):
    """Ball joints knocking: each joint is a small bright modal ping (random 2-6 kHz modes) that bounces, the intervals
    and heights shrinking by a restitution coefficient e. Returns a signal of length dur."""
    y = np.zeros(n_(dur))
    for j in range(n_joints):
        f0 = rng.uniform(1500, 2700) if modes_base is None else modes_base * rng.uniform(0.9, 1.1)
        ms = [(f0, 0.05, 1.0), (f0 * rng.uniform(1.55, 1.75), 0.06, 0.6), (f0 * rng.uniform(2.3, 2.7), 0.07, 0.35)]
        ee = rng.uniform(*e); d = rng.uniform(*d0); a = amp0 * rng.uniform(0.6, 1.0)
        t = start + rng.uniform(0, spread)
        hits = []
        for b in range(rng.integers(bounces[0], bounces[1] + 1)):
            if t > dur - 0.01: break
            hits.append((t, a * rng.uniform(0.8, 1.2), tau * rng.uniform(0.7, 1.4)))
            t += d * rng.uniform(0.85, 1.15); d *= ee; a *= ee ** 0.8
        y += modal(ms, hits, dur, rng, jitter=0.01)
    return y


def resample(x, rate):
    from math import gcd
    g = gcd(FS, rate)
    return resample_poly(x, rate // g, FS // g, window=('kaiser', 8.0))


def finish(x, rate, tail_db=-42, fade_ms=10, hp_hz=60):
    """High-pass (DC/rumble), resample to the bank rate, cut the tail once its envelope stays below tail_db of the peak
    (in the game mix a -42 dB tail on a -25 LUFS sound is far under everything else), and fade the end."""
    x = hp(x, hp_hz, order=2)
    y = resample(x, rate)
    a = np.abs(y); pk = a.max()
    w = max(1, int(0.002 * rate))
    env = np.maximum.accumulate(a[::-1])[::-1]                 # the loudest sample from here to the end
    env = np.convolve(env, np.ones(w) / w, mode='same')
    idx = np.nonzero(env > pk * 10 ** (tail_db / 20))[0]
    end = min(len(y), idx[-1] + 1) if len(idx) else len(y)
    y = y[:end].copy()
    nf = min(len(y) // 3, int(fade_ms * rate / 1000))
    y[-nf:] *= np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
    lead = np.nonzero(a[:end] > pk * 1e-3)[0]
    if len(lead) and lead[0] > 2: y = y[lead[0] - 2:]
    return y
