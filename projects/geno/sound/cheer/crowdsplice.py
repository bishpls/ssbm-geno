"""Concatenative splicer for Melee's crowd chants: cut the crowd's own recorded chants, time-scale and pitch-shift each piece,
gain-match, and crossfade. No synthesis, TTS or voice conversion: every output sample comes from the chants on the disc
(decoded by survey.py into $CROWD_WORK/chants), only cut, resampled or overlap-added, scaled and mixed at the seams.

A chant is a crowd (a chorus in a room), not one voice, so the announcer's pitch-synchronous PSOLA (one F0, one pulse
train) is the wrong tool: it imposes a single periodicity and makes a chorus buzz. The pieces here are moved with
- WSOLA (waveform-similarity overlap-add, 46 ms Hann grains) for duration; it keeps the chorus texture;
- varispeed (band-limited resampling) for pitch, which moves the formants with the pitch; used only for shifts up to
  about +-2 semitones, where a crowd's vowel still reads (WSOLA then restores the duration).
Seams are raised-cosine crossfades normalised by the correlation of the two overlaps (fo^2 + fi^2 + 2 r fo fi = 1): an
equal-power fade for unlike crowd sounds, amplitude-complementary for correlated ones.
"""
import glob, os
from dataclasses import dataclass

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

SR = 16000
WORK = os.path.expanduser(os.environ.get('CROWD_WORK', '~/games/melee/work/crowd'))
_cache = {}


def load(code, lang='us'):
    """A chant by fighter code ('Mr', 'Lg', ...) as float64 at 16 kHz."""
    key = (code, lang)
    if key not in _cache:
        p = glob.glob(os.path.join(WORK, 'chants', f'{lang}_{code}_*.wav'))
        assert len(p) == 1, (code, p)
        x, sr = sf.read(p[0])
        assert sr == SR
        _cache[key] = x.astype(np.float64)
    return _cache[key]


def wsola(x, factor, win=0.046, tol=0.012):
    """Time-scale x by `factor` (output length = factor * input) with WSOLA: Hann grains at 50 % overlap on the output,
    each taken from near its nominal input position where it best continues the previous grain."""
    if abs(factor - 1) < 1e-3:
        return x.copy()
    n = int(win * SR) // 2 * 2; h = n // 2; d = int(tol * SR)
    w = np.hanning(n + 1)[:n]
    L = int(round(len(x) * factor))
    xp = np.concatenate([np.zeros(n + d), x, np.zeros(2 * n + d)])
    off = n + d
    out = np.zeros(L + 2 * n); norm = np.zeros(L + 2 * n)
    prev = off                                    # input index the previous grain was taken from
    k = 0
    while k * h < L + h:
        nominal = off + int(round(k * h / factor))
        if k == 0:
            best = nominal
        else:
            target = xp[prev + h:prev + h + n]    # the natural continuation of the previous grain
            lo, hi = nominal - d, nominal + d
            seg = xp[lo:hi + n]
            c = np.correlate(seg, target, 'valid')
            e = np.sqrt(np.convolve(seg ** 2, np.ones(n), 'valid')) + 1e-9
            best = lo + int(np.argmax(c / e))
        out[k * h:k * h + n] += xp[best:best + n] * w
        norm[k * h:k * h + n] += w
        prev = best; k += 1
    norm[norm < 1e-6] = 1
    return (out / norm)[:L]


def pitch_shift(x, semis):
    """Varispeed by `semis` semitones, then WSOLA back to the original length."""
    if abs(semis) < 1e-3:
        return x.copy()
    r = 2 ** (semis / 12)
    # resample to len/r: played at SR the pitch goes up by r
    up, down = _ratio(1 / r)
    y = resample_poly(x, up, down)
    return wsola(y, len(x) / len(y))


def _ratio(r, den=1000):
    from math import gcd
    a, b = int(round(r * den)), den
    g = gcd(a, b)
    return a // g, b // g


@dataclass
class Seg:
    src: str                 # fighter code of the chant
    t0: float                # core start (s)
    t1: float                # core end (s)
    dur: float = None        # output core duration (s); None keeps it
    semis: float = 0.0       # pitch shift (varispeed + WSOLA)
    gain_db: float = 0.0
    fade_out: float = 0.0    # s: a cos^2 cut-off over the core's last fade_out (the crowd stopping for breath)
    layer: tuple = None      # (src, t0, t1, gain_db, at): a second crowd take mixed in `at` s into the core (5 ms fades)
    label: str = ''


def render(s: Seg, margin):
    """(y, pre, post): the processed core with `margin` of processed source on each side (for the crossfades)."""
    x = load(s.src)
    a, b = int(round(s.t0 * SR)), int(round(s.t1 * SR)); m = int(round(margin * SR))
    lo, hi = max(0, a - m), min(len(x), b + m)
    y = x[lo:hi].copy(); pre, post = a - lo, hi - b
    if s.semis:
        y = pitch_shift(y, s.semis)
    if s.dur is not None:
        core = y[pre:len(y) - post]
        f = s.dur * SR / len(core)
        if abs(f - 1) > 1e-3:
            # stretch the core, keep the margins at 1x, joined inside the margins with short fades
            whole = wsola(y, f)
            # rebuild: margins stay unscaled so seams line up with the source's own timing
            pre_s, post_s = int(round(pre * f)), int(round(post * f))
            y = np.concatenate([y[:pre], whole[pre_s:len(whole) - post_s], y[len(y) - post:]])
    if s.layer is not None:
        ls, l0, l1, lg, at = s.layer
        z = load(ls)[int(round(l0 * SR)):int(round(l1 * SR))].copy()
        f = int(0.005 * SR)
        z[:f] *= np.linspace(0, 1, f); z[-f:] *= np.linspace(1, 0, f)
        i = pre + int(round(at * SR))
        y[i:i + len(z)] += z[:max(0, len(y) - i)] * 10 ** (lg / 20)
    y = y * 10 ** (s.gain_db / 20)
    if s.fade_out > 0:
        n, e = int(s.fade_out * SR), len(y) - post
        y[e - n:e] *= np.cos(np.linspace(0, np.pi / 2, n)) ** 2
        y[e:] = 0
    return y, pre, post


def join(a, a_end, b, b_start, xf):
    """Overlap-add b onto a with a correlation-normalised raised-cosine crossfade of xf samples centred on a_end/b_start."""
    h = xf // 2
    h = min(h, a_end, len(a) - a_end, b_start, len(b) - b_start)
    oa, ob = a[a_end - h:a_end + h], b[b_start - h:b_start + h]
    r = float(np.clip(np.dot(oa, ob) / (np.linalg.norm(oa) * np.linalg.norm(ob) + 1e-9), 0.0, 1.0)) if h else 0.0
    u = np.sin(np.linspace(0, np.pi / 2, 2 * h)) ** 2
    fo, fi = 1 - u, u
    nm = np.sqrt(fo ** 2 + fi ** 2 + 2 * r * fo * fi)
    mix = oa * fo / nm + ob * fi / nm
    return np.concatenate([a[:a_end - h], mix, b[b_start + h:]]), a_end


def build(segs, xfades, margin=0.06):
    """Concatenate segs (each core placed right after the previous one), crossfading xfades[i] seconds at each seam.
    Returns (y, seams, spans) in output seconds."""
    y, pre, post = render(segs[0], margin)
    out = y[pre:].copy()                          # the first segment starts at its core (no lead-in)
    end = len(out) - post
    spans, seams = [(0.0, end / SR)], []
    for s, xf in zip(segs[1:], xfades):
        yb, preb, postb = render(s, margin)
        xs = int(round(xf * SR)) // 2 * 2
        out, c = join(out, end, yb, preb, xs)
        off = c - preb
        end = off + len(yb) - postb
        seams.append(c / SR); spans.append((c / SR, end / SR))
    return out[:end], seams, spans


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(np.asarray(x) ** 2)) + 1e-12)


def span_db(code, t0, t1):
    x = load(code)
    return rms_db(x[int(t0 * SR):int(t1 * SR)])


def write(path, y, sr=SR):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, np.clip(y, -1, 1), sr, subtype='PCM_16')
