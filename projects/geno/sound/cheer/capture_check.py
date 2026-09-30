"""Is the chant in the game's audio? Finds each play of a chant WAV in a lab's Dolphin dump (dsp.wav) by normalised
cross-correlation, and reports where the plays start, how well each matches, and the capture's level against the source.

    .venv/bin/python projects/geno/sound/cheer/capture_check.py RUN_DIR CHANT.wav [--plays 8] [--spec OUT.png]
"""
import argparse, json, os

import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, resample_poly


def mono(path):
    x, sr = sf.read(path)
    return (x.mean(1) if x.ndim > 1 else x), sr


def ncc(hay, needle):
    """Normalised cross-correlation of needle at every offset of hay."""
    n = len(needle)
    num = fftconvolve(hay, needle[::-1], 'valid')
    e = np.sqrt(np.maximum(fftconvolve(hay ** 2, np.ones(n), 'valid'), 1e-12))
    return num / (e * np.linalg.norm(needle) + 1e-12)


def check(run, chant, plays=8):
    x, sr = mono(os.path.join(run, 'dsp.wav'))
    c, csr = mono(chant)
    c = resample_poly(c, sr, csr) if csr != sr else c
    r = ncc(x, c)
    found = []
    rr = r.copy()
    for _ in range(plays + 2):
        i = int(np.argmax(rr))
        if rr[i] < 0.2:
            break
        found.append((i / sr, float(rr[i])))
        rr[max(0, i - len(c) // 2):i + len(c) // 2] = 0
    found.sort()
    lvl = [20 * np.log10(np.sqrt(np.mean(x[int(t * sr):int(t * sr) + len(c)] ** 2)) + 1e-12) for t, _ in found]
    return dict(rate=sr, seconds=round(len(x) / sr, 2), plays=[dict(t=round(t, 3), ncc=round(v, 3), rms_db=round(l, 1))
                                                               for (t, v), l in zip(found, lvl)],
                gaps=[round(b[0] - a[0], 3) for a, b in zip(found, found[1:])], max_ncc_anywhere=round(float(r.max()), 3))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('run'); ap.add_argument('chant'); ap.add_argument('--plays', type=int, default=8)
    a = ap.parse_args()
    res = check(a.run, a.chant, a.plays)
    print(json.dumps(res, indent=1))
    json.dump(res, open(os.path.join(a.run, 'chant_check.json'), 'w'), indent=1)
