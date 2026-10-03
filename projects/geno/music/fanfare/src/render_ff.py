"""Render the fanfare: VSCO 2 CE (CC0) through sfizz_render, one-shot orchestral cymbals, a hall, a master matched to
Melee's own fanfares (integrated loudness and true peak), a 32 kHz / 16-bit version for the HPS.
    python render_ff.py OUTDIR [--lufs -15.0] [--ceiling -1.5] [--hold 12]
Writes OUTDIR/levelup_fanfare_48k.wav (float master), levelup_fanfare_32k.wav (the HPS source), stems/*.wav, meta.json,
levelup_fanfare.mid (every part, for reading)."""
import os, sys, json, time, argparse
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'forest_maze', 'src'))   # sfz.py, music_paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfz, levelup as LU
import pretty_midi as pm

SR = 48000
from music_paths import MUSIC  # noqa: E402
LIB = os.path.join(MUSIC, 'libs', 'VSCO-2-CE-1.1.0')
# instrument -> VSCO patch
PATCH = {'fl_stac': 'FluteStac', 'fl2_stac': 'FluteStac', 'fl_sus': 'FluteSusVib', 'ob': 'OboeSusVib', 'ob_s': 'OboeStac',
         'cl': 'ClarinetSus', 'tpt_stac': 'TrumpetStac', 'tpt2_stac': 'TrumpetStac', 'tpt_sus': 'TrumpetSus',
         'tpt2_sus': 'TrumpetSus', 'hn_stac': 'FHornStac', 'hn_sus': 'FHornSus', 'tbn_stac': 'TromboneStac',
         'tbn_sus': 'TromboneSus', 'tuba_stac': 'TubaStac', 'tuba_sus': 'TubaSus', 'vln1_spic': 'ViolinEnsSpic',
         'vln2_spic': 'ViolinEnsSpic', 'vln1_sus': 'ViolinEnsSusVib', 'vln_trem': 'ViolinEnsTrem',
         'vla_spic': 'ViolaEnsSpic', 'vla_sus': 'ViolaEnsSusVib', 'vc_spic': 'CelloEnsSpic', 'vc_sus': 'CelloEnsSusVib',
         'cb_pizz': 'ContrabassPizz', 'cb_sus': 'ContrabassSusVB', 'glock': 'Glockenspiel', 'xylo': 'Xylophone',
         'timp': 'Timpani', 'timp_roll': 'TimpaniRolls', 'harp': 'Harp'}
# instrument -> (gain dB applied to the rendered patch, pan -1..1, bus). Gains are absolute (sfizz output scale), so a
# part's level follows its note velocities and density, like players in a hall.
MIX = {'fl_stac': (5.0, -0.08, 'hall'), 'fl2_stac': (-1.0, 0.05, 'hall'), 'fl_sus': (0.0, -0.05, 'hall'),
       'ob': (-3.0, 0.12, 'hall'), 'ob_s': (-3.0, 0.12, 'hall'), 'cl': (-4.0, 0.18, 'hall'),
       'tpt_stac': (5.0, 0.08, 'hall'), 'tpt2_stac': (2.0, 0.16, 'hall'), 'tpt_sus': (0.0, 0.08, 'hall'),
       'tpt2_sus': (-1.5, 0.16, 'hall'), 'hn_stac': (-5.0, -0.3, 'hall'), 'hn_sus': (0.0, -0.3, 'hall'),
       'tbn_stac': (0.0, 0.32, 'hall'), 'tbn_sus': (-1.0, 0.32, 'hall'), 'tuba_stac': (-3.0, 0.38, 'hall'),
       'tuba_sus': (-5.0, 0.38, 'hall'), 'vln1_spic': (2.0, -0.5, 'hall'), 'vln2_spic': (-4.0, -0.22, 'hall'),
       'vln1_sus': (-2.0, -0.5, 'hall'), 'vln_trem': (-4.0, -0.25, 'hall'), 'vla_spic': (-3.0, 0.22, 'hall'),
       'vla_sus': (-3.0, 0.22, 'hall'), 'vc_spic': (1.0, 0.42, 'hall'), 'vc_sus': (0.0, 0.42, 'hall'),
       'cb_pizz': (0.0, 0.5, 'hall'), 'cb_sus': (-4.0, 0.5, 'hall'), 'glock': (9.0, -0.15, 'hall'),
       'xylo': (-9.0, 0.1, 'hall'), 'timp': (0.0, 0.0, 'hall'), 'timp_roll': (0.0, 0.0, 'hall'),
       'harp': (-7.0, -0.35, 'hall')}
PERC = {'BD': (36, -9.0, 0.05), 'SN': (38, -6.0, 0.12), 'SN_roll': (37, -3.0, 0.12), 'tamb': (54, -4.0, 0.3),
        'triangle': (81, -12.0, -0.25)}
ONESHOT = {'crash': ('Percussion/cymbal-crash1_ff_rr1.wav', -7.0), 'sus_swell_end': ('Percussion/susCymb1-cresc-Short_v1.wav', -9.0)}


def pan(x, p):
    """mono (n,) or stereo (2, n) -> stereo with constant-power pan (stereo input is balanced, not collapsed)"""
    a = (p + 1) * np.pi / 4
    gl, gr = np.cos(a) * np.sqrt(2), np.sin(a) * np.sqrt(2)
    if x.ndim == 1:
        return np.vstack([x * gl, x * gr])
    return np.vstack([x[0] * min(1.0, gl), x[1] * min(1.0, gr)])


def fit(x, n):
    return x[..., :n] if x.shape[-1] >= n else np.pad(x, [(0, 0)] * (x.ndim - 1) + [(0, n - x.shape[-1])])


def render_parts(notes, perc, total):
    n = int(total * SR)
    stems = {}
    for inst, ns in notes.items():
        if inst == 'ob':   # oboe: 16ths on the staccato patch, the held note on the vibrato one
            short = [x for x in ns if x[1] < 0.2]; long_ = [x for x in ns if x[1] >= 0.2]
            parts = [('ob_s', short), ('ob', long_)]
        else:
            parts = [(inst, ns)]
        for name, nn in parts:
            if not nn:
                continue
            y = sfz.render(f'{LIB}/{PATCH[name]}.sfz', sfz.notes_inst(nn), total)
            g, p, bus = MIX[name]
            stems[name] = fit(pan(y.mean(0) if y.shape[0] == 2 and name in ('timp', 'timp_roll') else y, p) * 10 ** (g / 20), n)
    # GM-style percussion (one sfizz pass per voice so each gets its own level and pan)
    for name, (key, g, p) in PERC.items():
        ev = [(t, 0.3, key, v) for (t, nm, v) in perc if nm == name]
        if not ev:
            continue
        y = sfz.render(f'{LIB}/GM-StylePerc.sfz', sfz.notes_inst(ev), total)
        stems['perc_' + name] = fit(pan(y, p) * 10 ** (g / 20), n)
    for name, (path, g) in ONESHOT.items():
        ev = [(t, v) for (t, nm, v) in perc if nm == name]
        if not ev:
            continue
        w, sr = sf.read(f'{LIB}/{path}', dtype='float32', always_2d=True)
        w = w.T if w.shape[1] == 2 else np.vstack([w[:, 0], w[:, 0]])
        if sr != SR:
            from scipy.signal import resample_poly
            from math import gcd
            q = gcd(SR, sr); w = resample_poly(w, SR // q, sr // q, axis=1).astype(np.float32)
        out = np.zeros((2, n), np.float32)
        if name == 'sus_swell_end':                  # a swell is placed so that its PEAK lands on t; its decay is cut
            env = np.abs(w).max(0); pk = int(np.argmax(env)); cut = pk + int(0.25 * SR)
            w = w[:, :cut].copy(); f = int(0.2 * SR); w[:, -f:] *= np.linspace(1, 0, f)[None]
        for (t, v) in ev:
            i = int(t * SR) - (pk if name == 'sus_swell_end' else 0)
            a, b = max(0, i), min(n, i + w.shape[1])
            out[:, a:b] += v * w[:, a - i:b - i]
        stems['perc_' + name] = out * 10 ** (g / 20)
    return stems


ROOM = [0.7]


def hall(x):
    from pedalboard import Pedalboard, Reverb, HighpassFilter, LowpassFilter
    wet = Pedalboard([HighpassFilter(180), LowpassFilter(9000),
                      Reverb(room_size=ROOM[0], damping=0.45, wet_level=1.0, dry_level=0.0, width=1.0)])(x.astype(np.float32), SR)
    return wet


def master(mix, lufs, ceiling_dbtp):
    """HPF, gentle glue compression, loudness to target, true-peak-safe limiting (4x oversampled detector)."""
    import pyloudnorm as pyln
    from pedalboard import Pedalboard, HighpassFilter, Compressor
    from scipy.signal import resample_poly
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    meter = pyln.Meter(SR)
    from pedalboard import PeakFilter
    x = Pedalboard([HighpassFilter(30), PeakFilter(220, 4.0, 0.8), Compressor(threshold_db=-18, ratio=1.8, attack_ms=20, release_ms=200)])(mix.astype(np.float32), SR)
    k = 10 ** ((lufs - meter.integrated_loudness(x.T)) / 20)
    c = 10 ** (ceiling_dbtp / 20)
    for _ in range(6):
        y = x * k
        up = np.abs(resample_poly(y, 4, 1, axis=1)).max(0)
        pk = up.reshape(-1, 4).max(1)[:y.shape[1]]
        need = np.minimum(1.0, c / np.maximum(pk, 1e-9))
        g = minimum_filter1d(need, int(0.004 * SR))               # look-ahead-ish hold
        g = uniform_filter1d(g, int(0.002 * SR))
        g = np.minimum(g, need)
        z = y * g[None]
        L = meter.integrated_loudness(z.T)
        if abs(L - lufs) < 0.1:
            break
        k *= 10 ** ((lufs - L) / 20)
    tp = 20 * np.log10(np.abs(resample_poly(z, 4, 1, axis=1)).max())
    return z.astype(np.float32), L, tp, float(20 * np.log10(g.min()))


def to_32k(x48):
    from scipy.signal import resample_poly
    y = resample_poly(x48, 2, 3, axis=1)
    rng = np.random.default_rng(1)
    d = (rng.random(y.shape) - rng.random(y.shape)) / 32768.0       # TPDF dither
    return np.clip(np.round((y + d) * 32767), -32768, 32767).astype(np.int16).T


def trim_tail(x, sr, floor_db=-66, fade=0.08):
    """end the file where the ring-out falls below floor_db (short-term), with a short fade to digital silence"""
    m = np.abs(x).max(0)
    hop = int(0.01 * sr)
    env = np.array([m[i:i + hop].max() for i in range(0, len(m), hop)])
    above = np.where(20 * np.log10(env + 1e-12) > floor_db)[0]
    end = min(len(m), (above[-1] + 1) * hop + int(0.05 * sr))
    y = x[:, :end].copy()
    f = min(int(fade * sr), end)
    y[:, end - f:] *= np.linspace(1, 0, f)[None] ** 2
    return y


def write_midi(notes, perc, path):
    mid = pm.PrettyMIDI(initial_tempo=LU.meta_bpm if hasattr(LU, 'meta_bpm') else 151.515)
    for inst, ns in sorted(notes.items()):
        I = pm.Instrument(0, name=inst)
        for (t, d, p, v) in ns:
            I.notes.append(pm.Note(int(np.clip(v * 127, 1, 127)), int(p), t, t + max(0.02, d)))
        mid.instruments.append(I)
    D = pm.Instrument(0, is_drum=True, name='percussion')
    keys = {'BD': 35, 'SN': 38, 'SN_roll': 38, 'tamb': 54, 'triangle': 81, 'crash': 49, 'sus_swell_end': 52}
    for (t, nm, v) in perc:
        D.notes.append(pm.Note(int(np.clip(v * 127, 1, 127)), keys[nm], t, t + 0.1))
    mid.instruments.append(D)
    mid.write(path)


def render(outdir, lufs=-15.0, ceiling=-1.5, hold=10, reverb_mix=0.18, release_s=0.5, room=0.7, tail=(0.15, 0.85), form='short'):
    os.makedirs(os.path.join(outdir, 'stems'), exist_ok=True)
    ROOM[0] = room
    notes, perc, meta = LU.arrangement(final_hold16=hold, form=form)
    total = meta['release_t'] + 3.0
    t0 = time.time()
    stems = render_parts(notes, perc, total)
    dry = sum(stems.values())
    n = dry.shape[1]; tt = np.arange(n) / SR
    rel = meta['release_t']
    g = np.where(tt < rel, 1.0, 10 ** (-(tt - rel) / release_s * 60 / 20)).astype(np.float32)   # -60 dB in release_s
    dry = dry * g[None]
    wet = hall(dry)
    mix = dry + reverb_mix * wet
    # the ring-out: like Melee's own fanfares (Mario: -20 dB to -60 dB in 0.85 s), the hall is faded too
    a_, b_ = rel + tail[0], rel + tail[1]
    g2 = np.where(tt < a_, 1.0, 10 ** (-np.clip(tt - a_, 0, None) / (b_ - a_) * 60 / 20)).astype(np.float32)
    mix = mix * g2[None]
    z, L, tp, gr = master(mix, lufs, ceiling)
    z = trim_tail(z, SR)
    sf.write(os.path.join(outdir, 'levelup_fanfare_48k.wav'), z.T, SR, subtype='FLOAT')
    x32 = to_32k(z)
    sf.write(os.path.join(outdir, 'levelup_fanfare_32k.wav'), x32, 32000, subtype='PCM_16')
    k = z.shape[1]
    for name, s in stems.items():
        sf.write(os.path.join(outdir, 'stems', name + '.wav'), s[:, :k].T, SR, subtype='FLOAT')
    write_midi(notes, perc, os.path.join(outdir, 'levelup_fanfare.mid'))
    meta.update(lufs=round(L, 2), true_peak_dbtp=round(tp, 2), limiter_max_gr_db=round(gr, 2), seconds=round(k / SR, 3),
                render_s=round(time.time() - t0, 1), reverb_mix=reverb_mix, hold16=hold, release_s=release_s, room=room, tail=list(tail))
    json.dump(meta, open(os.path.join(outdir, 'meta.json'), 'w'), indent=1)
    return meta


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('outdir'); ap.add_argument('--lufs', type=float, default=-15.0)
    ap.add_argument('--ceiling', type=float, default=-1.5); ap.add_argument('--hold', type=int, default=10)
    ap.add_argument('--release', type=float, default=0.5); ap.add_argument('--room', type=float, default=0.7)
    ap.add_argument('--form', default='short', choices=['short', 'full'])
    ap.add_argument('--reverb', type=float, default=0.18)
    a = ap.parse_args()
    print(json.dumps(render(a.outdir, a.lufs, a.ceiling, a.hold, a.reverb, a.release, a.room, form=a.form), indent=1))
