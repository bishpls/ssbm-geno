"""Per-section melody fidelity for draft 2: the reference is whatever carries the tune in that section (guitar lead, or
the strings/bell melody where the guitars drop out), pitch-class match of the take's predominant pitch.
    python secfid2.py TAKE.wav"""
import sys
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
import numpy as np, librosa
import fidelity as F, render2 as R2, draft2 as D2
E, layers, pumps, segs, total = R2.build(D2.SECTIONS, D2.FINAL_HIT)
f = sys.argv[1]
y, _ = librosa.load(f, sr=F.SR); p, conf = F.salience_pitch(y); n = len(p)
lead = [(t, d, q) for (t, d, q, v, fl) in E['lead1'] if t < E['end'] - 0.01]
harm = [(t, d, q) for (t, d, q, v, fl) in E['lead2']]
alt = [(t, d, q) for inst in ('bell',) for (t, d, q, v) in layers.get(inst, [])]
glade = [(t, d, q) for inst in ('vln_mel', 'vln_mel_s') for (t, d, q, v) in layers.get(inst, []) if 62.4 <= t < 72.0]
ref = F.frame_line(lead + alt + glade, n); h = F.frame_line(harm, n)
tot, out = [], []
for i, (t0, name) in enumerate(E['marks']):
    t1 = E['marks'][i + 1][0] if i + 1 < len(E['marks']) else E['end']
    a, b = int(t0 * F.FPS), min(n, int(t1 * F.FPS)); m = ref[a:b] >= 0
    if m.sum() < 10: out.append(f'{name}: -'); continue
    s = np.mean((p[a:b][m] % 12) == (ref[a:b][m] % 12))
    sh = np.mean(((p[a:b][m] % 12) == (ref[a:b][m] % 12)) | ((h[a:b][m] >= 0) & ((p[a:b][m] % 12) == (h[a:b][m] % 12))))
    tot.append((m.sum(), s, sh)); out.append(f'{name}: {s:.2f}/{sh:.2f}')
w = np.array([x[0] for x in tot])
print(f"{f.split('/')[-2] + '/' + f.split('/')[-1]:30s} overall {np.average([x[1] for x in tot], weights=w):.2f}/{np.average([x[2] for x in tot], weights=w):.2f} | " + '  '.join(out))
