"""'Sounds like one take' checks: level steps at seams, stressed-vowel HNR, spectral tilt spread across the word,
edge (noise-floor) levels and the reverb-tail decay, each against the real name calls."""
import sys, os, json, glob, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, soundfile as sf, parselmouth
from parselmouth.praat import call

HERE = os.path.expanduser(os.environ.get('ANNOUNCER_WORK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'announcer')))   # the work folder (game audio)
CHAR_IDX = [0, 1, 2, 4, 5, 6, 8, 10, 11, 12, 13, 15, 16, 18, 19, 20, 21, 22, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33]

def intensity(x, sr, hop=0.005, win=0.02):
    n, h = int(win * sr), int(hop * sr)
    e = np.array([np.sqrt(np.mean(x[i:i + n] ** 2) + 1e-12) for i in range(0, len(x) - n, h)])
    return (np.arange(len(e)) * h + n / 2) / sr, 20 * np.log10(e)

def level_step(x, sr, t):
    tt, db = intensity(x, sr)
    a = db[(tt > t - 0.025) & (tt < t - 0.005)].mean(); b = db[(tt > t + 0.005) & (tt < t + 0.025)].mean()
    return b - a

def natural_level_steps():
    d = []
    for i in CHAR_IDX:
        x, sr = sf.read(glob.glob(os.path.join(HERE, 'names', f'nr_name_{i:02d}_*.wav'))[0])
        tt, db = intensity(x, sr)
        act = db > db.max() - 20
        for k in range(len(tt)):
            t = tt[k]
            if 0.03 < t < tt[-1] - 0.03 and act[k]:
                d.append(abs(level_step(x, sr, t)))
    return np.sort(np.array(d))

def hnr(x, sr, a, b, floor=200):
    s = parselmouth.Sound(x[int(a * sr):int(b * sr)], sr)
    h = call(s, 'To Harmonicity (cc)', 0.005, floor, 0.1, 1.0).values[0]
    return float(np.mean(h[h > -100]))

def tilt(x, sr, a, b):
    """LTAS slope (dB/kHz) between 0.3 and 5 kHz."""
    s = x[int(a * sr):int(b * sr)]
    if len(s) < 256: return np.nan
    n = 512; w = np.hanning(n)
    frames = [s[i:i + n] * w for i in range(0, len(s) - n, n // 4)] or [np.pad(s, (0, n - len(s))) * w]
    P = np.mean([np.abs(np.fft.rfft(f)) ** 2 for f in frames], 0); f = np.fft.rfftfreq(n, 1 / sr)
    k = (f > 300) & (f < 5000)
    return float(np.polyfit(f[k] / 1000, 10 * np.log10(P[k] + 1e-12), 1)[0])

def tail_decay(x, sr):
    """dB/s slope of the last 200 ms envelope (reverb tail)."""
    tt, db = intensity(x, sr, hop=0.01, win=0.03)
    k = tt > tt[-1] - 0.2
    return float(np.polyfit(tt[k], db[k], 1)[0])

def edges(x, sr):
    n = int(0.005 * sr)
    f = lambda s: 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-9)
    return f(x[:n]), f(x[-n:])

if __name__ == '__main__':
    meta = json.load(open(os.path.join(HERE, 'cands', 'meta.json')))
    nat = natural_level_steps()
    # natural references
    ref_hnr, ref_tail, ref_tilt_sd = [], [], []
    for i in CHAR_IDX:
        x, sr = sf.read(glob.glob(os.path.join(HERE, 'names', f'nr_name_{i:02d}_*.wav'))[0])
        ref_tail.append(tail_decay(x, sr))
        L = len(x) / sr
        tl = [tilt(x, sr, a, a + 0.08) for a in np.arange(0.03, min(L - 0.25, 0.6), 0.08)]
        ref_tilt_sd.append(np.nanstd(tl))
    for n, a, b in [('pichu', 0.045, 0.15), ('peach', 0.05, 0.26), ('falco', 0.05, 0.18), ('kirby', 0.05, 0.2),
                    ('zelda', 0.07, 0.2), ('mario', 0.1, 0.3), ('yoshi', 0.07, 0.18), ('nocontest', 0.12, 0.36)]:
        x, sr = sf.read(os.path.join(HERE, 'src', n + '.wav')); ref_hnr.append((n, hnr(x, sr, a, b)))
    print('natural |level step| across 20 ms (dB): median %.2f, p95 %.2f' % (np.median(nat), np.percentile(nat, 95)))
    print('natural stressed-vowel HNR (dB):', ', '.join(f'{n} {v:.1f}' for n, v in ref_hnr))
    print('natural tail decay (dB/s): median %.0f [%.0f..%.0f]' % (np.median(ref_tail), min(ref_tail), max(ref_tail)))
    print('natural tilt s.d. across 80 ms windows (dB/kHz): median %.2f [%.2f..%.2f]' % (
        np.median(ref_tilt_sd), min(ref_tilt_sd), max(ref_tilt_sd)))
    out = {}
    for name in sys.argv[1:]:
        p = os.path.join(HERE, name + '.wav')
        if not os.path.exists(p): p = os.path.join(HERE, 'cands', name + '.wav')
        x, sr = sf.read(p)
        m = meta[name]; spans = m['spans']
        steps = [level_step(x, sr, j) for j in m['joins']]
        pct = [100 * np.searchsorted(nat, abs(s)) / len(nat) for s in steps]
        a, b = spans[1]; vh = hnr(x, sr, a + 0.01, b - 0.01)
        tl = [tilt(x, sr, s0, s1) for s0, s1 in spans[:-1]] + [tilt(x, sr, spans[-1][0], spans[-1][0] + 0.15)]
        e0, e1 = edges(x, sr)
        out[name] = dict(level_steps_db=[round(s, 2) for s in steps], level_step_pct=[round(p) for p in pct],
                         vowel_hnr=round(vh, 1), seg_tilts=[round(t, 2) for t in tl], tilt_sd=round(float(np.std(tl)), 2),
                         edge_db=(round(e0, 1), round(e1, 1)), tail_db_per_s=round(tail_decay(x, sr)))
        print(name, json.dumps(out[name], ensure_ascii=False))
    op = os.path.join(HERE, 'cands', 'onetake.json')
    old = json.load(open(op)) if os.path.exists(op) else {}
    old.update(out); json.dump(old, open(op, 'w'), indent=1)
