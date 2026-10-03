"""Prototype retime for the SNES Geno charge: the sound is a train of ~55 ms up-glide grains whose pitch
steps upward, so drop grains (keep every k-th) instead of time-stretching: the pitch climbs faster while the
grain rhythm and timbre stay exactly SNES. usage: grain_retime.py IN.wav OUT.wav TARGET_SECONDS"""
import sys, numpy as np, soundfile as sf, librosa
inp, out, T = sys.argv[1], sys.argv[2], float(sys.argv[3])
y, sr = sf.read(inp, dtype='float32', always_2d=True); m = y.mean(1)
hop = 48; S = np.abs(librosa.stft(m, n_fft=1024, hop_length=hop)); f = librosa.fft_frequencies(sr=sr, n_fft=1024)
env = S[(f > 800) & (f < 6000)].sum(0); env = env - np.convolve(env, np.ones(81) / 81, 'same')
ac = np.correlate(env, env, 'full')[len(env) - 1:]; lag = np.arange(len(ac)) * hop / sr
w = (lag > 0.04) & (lag < 0.075); P = lag[w][np.argmax(ac[w])]
# grain boundaries at envelope minima near multiples of P
start = 0.05                                    # skip the attack; it is re-used as the first grain
b = [0]; t = start
while t + P < len(m) / sr:
    k0, k1 = int((t - P * 0.3) * sr / hop), int((t + P * 0.3) * sr / hop)
    k = k0 + int(np.argmin(np.convolve(S[(f > 800) & (f < 6000)].sum(0), np.ones(5) / 5, 'same')[k0:k1]))
    b.append(k * hop); t = k * hop / sr + P
b.append(len(m))
grains = [y[b[i]:b[i + 1]] for i in range(len(b) - 1)]
dur = len(m) / sr; ratio = dur / T
keep = sorted(set([0] + [int(round(i * ratio)) for i in range(1, int(len(grains) / ratio) + 1) if int(round(i * ratio)) < len(grains)] + [len(grains) - 1]))
xf = int(0.003 * sr); o = grains[keep[0]].copy()
for i in keep[1:]:
    g = grains[i]; r = np.linspace(0, 1, xf, dtype=np.float32)[:, None]
    o[-xf:] = o[-xf:] * (1 - r) + g[:xf] * r; o = np.concatenate([o, g[xf:]])
sf.write(out, o, sr, subtype='PCM_16')
print(f'grain period {P*1000:.1f} ms, {len(grains)} grains, kept {len(keep)} -> {len(o)/sr:.3f} s')
