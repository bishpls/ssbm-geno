"""Melody fidelity of a mix: at the middle of each lead-line note, the most salient pitch (harmonic-summed CQT) in the
lead's register; pitch-class match against the transcription (chance ~ 1/7 for a diatonic tune)."""
import os, sys, numpy as np, soundfile as sf, librosa
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import levelup as LU

def salience(y, sr, hop=256):
    fmin = librosa.note_to_hz('C2') * 2 ** (-1 / 36)
    C = np.abs(librosa.cqt(y, sr=sr, hop_length=hop, fmin=fmin, n_bins=84 * 3, bins_per_octave=36)).reshape(84, 3, -1).max(1)
    H = C.copy()
    for h, w in ((2, 0.6), (3, 0.4), (4, 0.3)):
        k = int(round(12 * np.log2(h)))
        H[:-k] += w * C[k:]
    return H  # semitone rows from C2 (midi 36)

def fidelity(path, lines, lo_hi):
    y, sr = sf.read(path, always_2d=True); y = y.mean(1)
    H = salience(y, sr); hop = 256
    res = {}
    for name, ns in lines.items():
        lo, hi = lo_hi[name]
        hits = 0; n = 0; octs = 0
        for (t, d, p) in ns:
            i = int((t + min(d, 0.2) * 0.5) * sr / hop)
            seg = H[lo - 36:hi - 36 + 1, i]
            top = lo + int(np.argmax(seg))
            n += 1; hits += (top % 12 == p % 12); octs += (top == p)
        res[name] = dict(n=n, pc_match=round(hits / n, 2), exact=round(octs / n, 2))
    return res

if __name__ == '__main__':
    T = LU.T16
    def line(bar, items, octave=0):
        return [((bar * 16 + pos) * T, ln * T, LU.m(nm) + 12 * octave) for (pos, nm, ln) in items]
    lines = {'intro run (flutes)': line(0, LU.RUN0),
             'theme bar 1 (trumpet 1)': line(1, LU.MEL[1], 1), 'theme bar 2 (trumpet 1)': line(2, LU.MEL[2], 1),
             'V-bar run (flute 1)': line(3, LU.RUN1)}
    rng = {'intro run (flutes)': (72, 96), 'theme bar 1 (trumpet 1)': (60, 84), 'theme bar 2 (trumpet 1)': (60, 84),
           'V-bar run (flute 1)': (72, 96)}
    for p in sys.argv[1:]:
        print(p.split('/')[-2], fidelity(p, lines, rng))
