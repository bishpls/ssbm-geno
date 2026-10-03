"""Does each stem sound the pitches the arrangement wrote? For every note, the pitch whose (harmonic-summed) CQT energy
rises most at the attack, searched +-13 semitones around the written pitch."""
import os, sys, numpy as np, soundfile as sf, librosa
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import levelup as LU

def check(stem_path, ns, bells=False):
    x, sr = sf.read(stem_path); y = x.mean(1)
    hop = 128; fmin = librosa.note_to_hz('C1') * 2 ** (-1 / 36)   # 3 bins per semitone, centred on it
    C = np.abs(librosa.cqt(y, sr=sr, hop_length=hop, fmin=fmin, n_bins=96 * 3, bins_per_octave=36))
    C = C.reshape(96, 3, -1).max(1)                       # semitone bins, C1.. (midi 24..)
    H = C.copy() if bells else C + 0.5 * np.vstack([C[12:], np.zeros((12, C.shape[1]))]) + 0.33 * np.vstack([C[19:], np.zeros((19, C.shape[1]))])
    res = []
    for (t, d, p, v) in ns:
        i0 = int((t - 0.015) * sr / hop); i1 = int((t + 0.045) * sr / hop)
        if i0 < 0: i0 = 0
        rise = H[:, i1] - H[:, i0]
        lo, hi = max(0, p - 24 - 13), min(95, p - 24 + 13)
        k = lo + int(np.argmax(rise[lo:hi + 1]))
        res.append(k + 24 - p)
    res = np.array(res)
    return dict(n=len(res), exact=int(np.sum(res == 0)), up12=int(np.sum(res == 12)), down12=int(np.sum(res == -12)), other=[int(r) for r in res if r not in (0, 12, -12)])

if __name__ == '__main__':
    take = sys.argv[1]
    notes, perc, meta = LU.arrangement(final_hold16=10)
    for stem, ns in sorted(notes.items()):
        if stem == 'ob':
            continue
        # skip chord notes (simultaneous onsets): check the top note of each onset only
        by_t = {}
        for n_ in ns: by_t.setdefault(round(n_[0], 3), []).append(n_)
        tops = [max(g, key=lambda z: z[2]) for g in by_t.values()]
        r = check(f'{take}/stems/{stem}.wav', tops, bells=stem in ('glock', 'xylo', 'timp', 'timp_roll'))
        print('%-10s %s' % (stem, r))
