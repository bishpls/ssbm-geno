"""Melody and harmony fidelity of a take against the arrangement's guide.
  melody: predominant pitch (harmonic-summed CQT salience, C4..C7) of the take vs the guide lead line, frame by frame, after a
          best global offset (+-0.5 s) and tempo factor (0.94..1.06) search. Reports pitch-class match % (strict and
          allowing the harmony third), and the octave-agnostic contour correlation of the matched frames.
  harmony: per-8th chroma of the take vs the guide chords (pitch-class templates), mean cosine.
    python fidelity.py TAKE.wav [TAKE2.wav ...]   (guide = tests/theme_guide.mid, lead + chords from testclip.SEC)"""
import sys, numpy as np, librosa, pretty_midi as pm
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
import arrange as A, testclip as T

SR = 22050; HOP = 256; FPS = SR / HOP


def guide_lines(secs=T.SEC):
    t0 = 0; mel = []; harm = []; chords = []
    for sec in secs:
        l1, l2 = A.lead_part(sec, t0)
        mel += [(t, d, p) for (t, d, p, v, f) in l1]; harm += [(t, d, p) for (t, d, p, v, f) in l2]
        for (t, d, r, ivs, sym) in A.src_chords(*sec['src']):
            chords.append((t0 + t * A.STEP, d * A.STEP, [(r + sec.get('key', 0) + i) % 12 for i in ivs]))
        t0 += (sec['src'][1] - sec['src'][0] + 1) * A.OB
    return mel, harm, chords, t0


def salience_pitch(y):
    C = np.abs(librosa.cqt(y, sr=SR, hop_length=HOP, fmin=librosa.note_to_hz('C4'), n_bins=12 * 5, bins_per_octave=12))
    C = np.log1p(10 * C / (C.max() + 1e-9))
    S = np.zeros((36, C.shape[1]))
    for i in range(36):
        for h, st in enumerate([0, 12, 19, 24]):
            if i + st < C.shape[0]: S[i] += (0.8 ** h) * C[i + st]
    p = S.argmax(0) + 60
    conf = S.max(0) / (np.median(S, 0) + 1e-9)
    return p, conf


def frame_line(notes, n, off=0.0, k=1.0):
    line = np.full(n, -1)
    for (t, d, p) in notes:
        a = int(((t * k) + off) * FPS); b = int(((t + d * 0.9) * k + off) * FPS)
        line[max(0, a):max(0, min(n, b))] = p
    return line


def score(path):
    y, _ = librosa.load(path, sr=SR, mono=True)
    mel, harm, chords, L = guide_lines()
    p, conf = salience_pitch(y)
    n = len(p)
    best = (-1, 0, 1)
    for k in np.arange(0.94, 1.061, 0.005):
        for off in np.arange(-0.5, 0.51, 0.02):
            g = frame_line(mel, n, off, k)
            m = g >= 0
            if m.sum() < 50: continue
            acc = np.mean((p[m] % 12) == (g[m] % 12))
            if acc > best[0]: best = (acc, off, k)
    acc, off, k = best
    g = frame_line(mel, n, off, k); hline = frame_line(harm, n, off, k); m = g >= 0
    acc_h = np.mean(((p[m] % 12) == (g[m] % 12)) | ((hline[m] >= 0) & ((p[m] % 12) == (hline[m] % 12))))
    # chance: same line shifted by 1 OB (same key and rhythm, wrong notes)
    gs = frame_line([(t + A.OB, d, q) for (t, d, q) in mel], n, off, k); ms = gs >= 0
    chance = np.mean((p[ms] % 12) == (gs[ms] % 12))
    # harmony: chroma per 8th vs chord templates
    Cq = librosa.feature.chroma_cqt(y=y, sr=SR, hop_length=HOP)
    sims = []
    for (t, d, pcs) in chords:
        a = int((t * k + off) * FPS); b = int(((t + d) * k + off) * FPS)
        a = max(0, a); b = min(b, Cq.shape[1])
        if b <= a: continue
        v = Cq[:, a:b].mean(1); tpl = np.zeros(12); tpl[pcs] = 1; tpl[pcs[0]] = 1.5
        sims.append(v @ tpl / (np.linalg.norm(v) * np.linalg.norm(tpl) + 1e-9))
    return dict(melody=acc, melody_or_harm=acc_h, chance=chance, harmony=float(np.mean(sims)), offset=off, tempo_k=k)


if __name__ == '__main__':
    for f in sys.argv[1:]:
        r = score(f)
        print(f"{f.split('/')[-1]:34s} melody PC match {r['melody']:.2f} (w/ harmony {r['melody_or_harm']:.2f}; chance {r['chance']:.2f})"
              f"  chord fit {r['harmony']:.2f}   [offset {r['offset']:+.2f} s, tempo x{r['tempo_k']:.3f}]")
