"""Match the clean SNES WAVs (src_clean/) against the SNES-verified, music-suppressed clips from ~/games/melee/work/sfx.
For every reference clip: log-mel cross-correlation against every clean file (all offsets, either one may contain the
other), then for the top candidates an exact per-overlap Pearson score and a waveform cross-correlation at the best lag.
Writes build/match.json and prints a table."""
import os, sys, glob, json
import numpy as np, soundfile as sf, librosa
from scipy.signal import fftconvolve

HERE = os.path.expanduser(os.environ.get('SFXBANK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'sfxbank')))
CLEAN = os.path.join(HERE, 'src_clean')
CLIPS = os.path.join(os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work')), 'sfx', 'clips')
SR = 32000; HOP = 320        # 10 ms frames

def load(path):
    x, sr = sf.read(path)
    if x.ndim > 1: x = x.mean(1)
    return librosa.resample(x, orig_sr=sr, target_sr=SR, res_type='soxr_hq')

def mel(x):
    S = librosa.feature.melspectrogram(y=x, sr=SR, n_fft=1024, hop_length=HOP, n_mels=64, fmin=100, fmax=15000)
    D = librosa.power_to_db(S, ref=np.max, top_db=70)
    return D

def z(D):
    # remove each band's long-term level (the spectral envelope), keep the time-frequency structure
    E = D - D.mean(axis=1, keepdims=True)
    return (E - E.mean()) / (E.std() + 1e-9)

def xcorr_all(R, C):
    """sum over bands of the cross-correlation of globally z-scored spectrograms, per lag; normalised by the overlap."""
    Tr, Tc = R.shape[1], C.shape[1]
    acc = np.zeros(Tr + Tc - 1)
    for b in range(R.shape[0]):
        acc += fftconvolve(C[b], R[b][::-1], mode='full')
    lags = np.arange(-(Tr - 1), Tc)                      # lag = start of R inside C
    ov = np.minimum(Tc, lags + Tr) - np.maximum(0, lags)
    return lags, acc / (np.maximum(ov, 1) * R.shape[0]), ov

def pearson_at(Dr, Dc, lag):
    Tr, Tc = Dr.shape[1], Dc.shape[1]
    a0, a1 = max(0, -lag), min(Tr, Tc - lag)
    if a1 - a0 < 5: return -1, 0
    A = Dr[:, a0:a1]; B = Dc[:, a0 + lag:a1 + lag]
    A = (A - A.mean(axis=1, keepdims=True)).ravel(); B = (B - B.mean(axis=1, keepdims=True)).ravel()
    return float(np.corrcoef(A, B)[0, 1]), a1 - a0

def wave_corr(xr, xc, lag_frames):
    """waveform correlation near the spectral lag (±20 ms), normalised over the overlap."""
    best = 0; bl = 0
    base = lag_frames * HOP
    for d in range(-640, 641, 1):
        L = base + d
        a0, a1 = max(0, -L), min(len(xr), len(xc) - L)
        if a1 - a0 < 1600: continue
        A = xr[a0:a1]; B = xc[a0 + L:a1 + L]
        c = np.dot(A, B) / (np.linalg.norm(A) * np.linalg.norm(B) + 1e-9)
        if abs(c) > abs(best): best, bl = c, L
    return float(best), bl / SR

def main():
    clean = {os.path.basename(p)[:-4]: load(p) for p in sorted(glob.glob(os.path.join(CLEAN, '*.wav')))}
    cmel = {k: mel(v) for k, v in clean.items()}; cz = {k: z(v) for k, v in cmel.items()}
    refs = sorted(glob.glob(os.path.join(CLIPS, '*.wav')))
    out = {}
    for rp in refs:
        rn = os.path.basename(rp)[:-4]
        xr = load(rp); Dr = mel(xr); Rz = z(Dr)
        cands = []
        for k, Cz in cz.items():
            lags, sc, ov = xcorr_all(Rz, Cz)
            minov = int(0.6 * min(Rz.shape[1], Cz.shape[1]))
            m = ov >= minov
            if not m.any(): continue
            i = np.argmax(np.where(m, sc, -9)); cands.append((sc[i], k, int(lags[i])))
        cands.sort(reverse=True)
        top = []
        for s, k, lag in cands[:5]:
            best = (-1, lag, 0)
            for d in range(-3, 4):
                p, n = pearson_at(Dr, cmel[k], lag + d)
                if p > best[0]: best = (p, lag + d, n)
            wc, wl = wave_corr(xr, clean[k], best[1])
            top.append(dict(file=k, mel_xcorr=round(float(s), 3), pearson=round(best[0], 3), lag_s=round(best[1] * HOP / SR, 3),
                            overlap_s=round(best[2] * HOP / SR, 2), wave_corr=round(wc, 3), wave_lag_s=round(wl, 4),
                            clean_dur=round(len(clean[k]) / SR, 3)))
        top.sort(key=lambda t: -t['pearson'])
        out[rn] = dict(ref_dur=round(len(xr) / SR, 3), top=top)
        t0 = top[0]; t1 = top[1] if len(top) > 1 else None
        print(f"{rn:26s} {out[rn]['ref_dur']:5.2f}s -> {t0['file']:30s} r={t0['pearson']:.2f} w={t0['wave_corr']:+.2f} at {t0['lag_s']:+.2f}s "
              f"(clean {t0['clean_dur']:.2f}s)  | 2nd {t1['file'] if t1 else '-'} r={t1['pearson'] if t1 else 0:.2f}", flush=True)
    json.dump(out, open(os.path.join(HERE, 'build', os.environ.get('MATCH_OUT', 'match.json')), 'w'), indent=1)

if __name__ == '__main__':
    main()
