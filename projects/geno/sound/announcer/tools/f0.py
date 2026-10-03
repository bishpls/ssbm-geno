import numpy as np, parselmouth
from parselmouth.praat import call
def pitch_obj(snd, floor=220, ceil=560, step=0.005):
    if isinstance(snd, str): snd = parselmouth.Sound(snd)
    # time step, floor, max candidates, very accurate, silence thr, voicing thr, octave cost, octave-jump cost, v/uv cost, ceiling
    return call(snd, 'To Pitch (ac)', step, floor, 15, 'yes', 0.01, 0.2, 0.03, 0.9, 0.14, ceil)
def contour(snd, **kw):
    p = pitch_obj(snd, **kw)
    t = p.xs(); f = p.selected_array['frequency'].copy(); f[f == 0] = np.nan
    return t, f
if __name__ == '__main__':
    import sys
    for path in sys.argv[1:]:
        t, f = contour(path)
        s = ' '.join(f'{v:3.0f}' if not np.isnan(v) else '  .' for v in f[::2])
        print(f'{path.split("/")[-1][:-4]:11s}', s)
