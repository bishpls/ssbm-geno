"""Find a fanfare in a Dolphin DSP dump: normalised cross-correlation of the mono mix against the reference WAVs."""
import os, sys, numpy as np, soundfile as sf
from scipy.signal import fftconvolve, resample_poly
_FF = os.path.join(os.path.expanduser(os.environ.get('GENO_MUSIC', '~/games/melee/work/music')), 'fanfare')
REFS = {'geno': os.path.join(_FF, 'geno_levelup_fanfare.wav'),
        'mario': os.path.join(_FF, 'vanilla', 'ff_mario.wav')}

def find(path, sr_ref=32000):
    x, sr = sf.read(path, always_2d=True); m = x.mean(1)
    m = resample_poly(m, 32000, sr) if sr != 32000 else m            # the DSP runs at ~32028 Hz: bring it to the ref rate
    out = {}
    for name, p in REFS.items():
        r, _ = sf.read(p, always_2d=True); r = r.mean(1)
        c = fftconvolve(m, r[::-1], mode='valid')
        e = np.maximum(fftconvolve(m ** 2, np.ones(len(r)), mode='valid'), 1e-12)
        cc = c / (np.sqrt(e) * np.sqrt(np.sum(r ** 2)))
        k = int(np.argmax(cc))
        out[name] = (round(k / 32000, 3), round(float(cc[k]), 3))
    return out, len(m) / 32000

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p, find(p))
