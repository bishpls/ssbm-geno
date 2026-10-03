"""Per-section melody fidelity of a full take against the draft's lead line (pitch-class match of the predominant pitch).
    python secfid.py TAKE.wav [offset_s]"""
import sys, json
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
import numpy as np, librosa
import fidelity as F, draft as Dr, render as R
E = R.build_events(Dr.SECTIONS)
f = sys.argv[1]; off = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
y, _ = librosa.load(f, sr=F.SR); p, conf = F.salience_pitch(y); n = len(p)
lead = [(t, d, q) for (t, d, q, v, fl) in E['lead1']]
harm = [(t, d, q) for (t, d, q, v, fl) in E['lead2']]
g = F.frame_line(lead, n, off); h = F.frame_line(harm, n, off)
tot = []
out = []
for i, (t0, name) in enumerate(E['marks']):
    t1 = E['marks'][i + 1][0] if i + 1 < len(E['marks']) else E['end']
    a, b = int((t0 + off) * F.FPS), min(n, int((t1 + off) * F.FPS)); m = g[a:b] >= 0
    if m.sum() < 10:
        out.append(f'{name}: -'); continue
    s = np.mean((p[a:b][m] % 12) == (g[a:b][m] % 12))
    sh = np.mean(((p[a:b][m] % 12) == (g[a:b][m] % 12)) | ((h[a:b][m] >= 0) & ((p[a:b][m] % 12) == (h[a:b][m] % 12))))
    tot.append((m.sum(), s, sh))
    out.append(f'{name}: {s:.2f}/{sh:.2f}')
w = np.array([x[0] for x in tot])
print(f"{f.split('/')[-1]:28s} overall {np.average([x[1] for x in tot], weights=w):.2f}/{np.average([x[2] for x in tot], weights=w):.2f} | " + '  '.join(out))
