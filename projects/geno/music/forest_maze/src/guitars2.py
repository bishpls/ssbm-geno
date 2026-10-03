"""Draft 2 guitars and bass from CC0 DI samples through sfizz: Karoryfer Emilyguitar (Epiphone, recorded direct, 4 velocity
layers x 3 round robins, low string also sampled in Db) and Karoryfer Growlybass. The DI goes to the NAM amps in mix.py.
  rhythm_di(events, total, seed, detune_cents)  -> mono DI   (palm mutes are short notes, darkened before the amp)
  lead_di(notes, total, seed, ...)               -> mono DI   (re-picked notes, hammer-ons in runs, upward vibrato, bends)
  bass_di(events, total, seed)                   -> mono DI"""
import os, re, numpy as np, pretty_midi as pm
from scipy.signal import butter, sosfilt
import sfz

SR = 48000
LIBS = sfz.LIBS


def _extended(src, lo=None, hi=None, tag='ext'):
    """copy an SFZ next to itself with its outermost key ranges widened (so notes past the sampled range pitch-shift
    from the nearest sample instead of going silent)"""
    s = open(src, errors='ignore').read()
    los = [int(x) for x in re.findall(r'lokey=(\d+)', s)]; his = [int(x) for x in re.findall(r'hikey=(\d+)', s)]
    if lo is not None: s = re.sub(rf'lokey={min(los)}\b', f'lokey={lo}', s)
    if hi is not None: s = re.sub(rf'hikey={max(his)}\b', f'hikey={hi}', s)
    dst = src.replace('.sfz', f'_{tag}.sfz')
    open(dst, 'w').write(s)
    return dst


GROWLY = _extended(sfz.PATHS['growly'], lo=21, tag='ext21')


def _di(y):
    return y.mean(0).astype(np.float32)


def rhythm_di(events, total, seed=0, detune_cents=0, humanize=0.005):
    rng = np.random.default_rng(seed)
    opn = pm.Instrument(0, name='open'); mut = pm.Instrument(0, name='mute')
    for e in events:
        t = max(0.0, e['t'] + rng.normal(0, humanize))
        muted = e.get('mute', 0) >= 0.5
        inst = mut if muted else opn
        dur = e['dur'] * (0.55 if muted else 1.0) * (1 + rng.normal(0, 0.08))
        for si, p in enumerate(sorted(e['notes'])):
            v = int(np.clip(e.get('vel', 0.9) * (100 if muted else 118) * (1 + rng.normal(0, 0.08)), 20, 127))
            inst.notes.append(pm.Note(v, int(p), t + si * (0.0015 if muted else 0.004), t + si * 0.003 + max(0.045, dur)))
    for inst in (opn, mut):
        if detune_cents:
            inst.pitch_bends.append(pm.PitchBend(int(detune_cents / 1200 * 8191), 0.0))
    a = _di(sfz.render(sfz.PATHS['emily'], opn, total)) if opn.notes else np.zeros(int(total * SR), np.float32)
    b = _di(sfz.render(sfz.PATHS['emily'], mut, total)) if mut.notes else np.zeros(int(total * SR), np.float32)
    b = sosfilt(butter(2, 1800, 'low', fs=SR, output='sos'), b).astype(np.float32) * 1.2   # palm: darker, tighter
    return a + b


def lead_inst(notes, seed=0, vib_rate=5.6, vib_depth=0.5, slide=0.05, humanize=0.004, bend_range=12):
    rng = np.random.default_rng(seed)
    inst = pm.Instrument(0, name='lead')
    notes = sorted(notes, key=lambda x: x[0])
    rate = 250.0
    bends = []; run = 0
    for i, nt in enumerate(notes):
        t, d, p, v = nt[:4]; fl = nt[4] if len(nt) > 4 else {}
        t = max(0.0, t + rng.normal(0, humanize))
        prev = notes[i - 1] if i > 0 else None
        joined = prev is not None and prev[0] + prev[1] >= nt[0] - 0.04
        run = run + 1 if (joined and d < 0.2) else 0
        hammer = prev is not None and run % 2 == 1 and abs(prev[2] - p) <= 3
        vel = int(np.clip((0.62 if hammer else 0.95) * v * 127 * (1 + rng.normal(0, 0.05)), 20, 127))
        inst.notes.append(pm.Note(vel, int(p), t, t + max(0.03, d)))
        k = np.arange(0, d, 1 / rate); off = np.zeros_like(k)
        b = fl.get('bend', 0)
        if b:
            tb = rng.uniform(0.09, 0.15); s_ = np.clip(k / tb, 0, 1)
            off += -b * (1 - np.sin(0.5 * np.pi * s_)) + 0.06 * b * np.sin(np.pi * s_)
        if d > 0.27:
            r_ = vib_rate * (1 + 0.08 * np.sin(2 * np.pi * rng.uniform(0.3, 0.7) * k + rng.uniform(0, 6))) + rng.normal(0, 0.3)
            ph = 2 * np.pi * np.cumsum(r_) / rate
            depth = fl.get('vib', vib_depth) * np.clip((k - 0.2) / 0.3, 0, 1) * (1 + 0.15 * rng.normal())
            off += depth * (0.5 - 0.5 * np.cos(ph))
        bends += [(t + kk, o) for kk, o in zip(k, off)]
    bends.sort(); last = None
    for (t, o) in bends:
        val = int(np.clip(o / bend_range * 8191, -8192, 8191))
        if val != last: inst.pitch_bends.append(pm.PitchBend(val, t)); last = val
    return inst


def lead_di(notes, total, seed=0, **kw):
    return _di(sfz.render(sfz.PATHS['emily_clean'], lead_inst(notes, seed=seed, **kw), total))


def bass_di(events, total, seed=0):
    rng = np.random.default_rng(seed)
    inst = pm.Instrument(0, name='bass')
    for (t, d, p, v, mu) in events:
        tt = max(0.0, t + rng.normal(0, 0.003))
        inst.notes.append(pm.Note(int(np.clip(v * 115 * (1 + rng.normal(0, 0.05)), 20, 127)), int(p), tt, tt + max(0.04, d * (0.6 if mu >= 0.5 else 1.0))))
    return _di(sfz.render(GROWLY, inst, total))
