"""Objective checks for candidate calls:
 1. Whisper free transcription (small.en, medium.en; no prompt).
 2. Whisper forced choice: log-likelihood of ' Geno!' (and same-sounding spellings) vs near-miss names, softmaxed
    over the set -> P(hit). Uses teacher forcing on the decoder; no generation bias.
 3. Pitch continuity at each seam (robust harmonic-sum F0, semitone jump across the seam).
 4. Spectral discontinuity at each seam: MFCC distance between frames 10 ms either side, as a percentile of the
    same statistic over all natural frame pairs in the announcer's real name calls (100 = worse than any natural)."""
import sys, os, json, glob, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, soundfile as sf, librosa, torch, whisper
from hf0 import hf0

HERE = os.path.expanduser(os.environ.get('ANNOUNCER_WORK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'announcer')))   # the work folder (game audio)
HITS = [' Geno!', ' Gino!', ' Jeno!', ' Jino!', ' Genno!', ' Gino.', ' Geno.']
MISSES = [' Keno!', ' Zeno!', ' Pino!', ' Chino!', ' Deno!', ' Dino!', ' Reno!', ' Nino!', ' Gina!', ' Jenna!',
          ' Gene!', ' Jean!', ' Beano!', ' Tino!', ' Jello!', ' Gemo!', ' Genie!', ' Cheeto!', ' Kino!', ' Shino!',
          ' Gee, no!', ' Hino!', ' Veno!', ' Leno!', ' Yeno!', ' Dano!', ' Juno!', ' Gyno!',
          ' Jingo!', ' Jingle!', ' Jimo!', ' Jedo!', ' Tingo!', ' Jinno!', ' Jego!', ' Jingo.', ' Jingle.', ' Game on!']

_models = {}
def model(name):
    if name not in _models:
        _models[name] = whisper.load_model(name, device='cpu')
    return _models[name]

def transcribe(path, name):
    r = model(name).transcribe(path, fp16=False, language='en', temperature=0.0)
    return r['text'].strip()

def forced(path, name='small.en'):
    m = model(name)
    tok = whisper.tokenizer.get_tokenizer(multilingual=m.is_multilingual, language='en', task='transcribe')
    audio = whisper.pad_or_trim(whisper.load_audio(path))
    mel = whisper.log_mel_spectrogram(audio, n_mels=m.dims.n_mels)[None]
    with torch.no_grad():
        enc = m.encoder(mel)
        scores = {}
        for text in HITS + MISSES:
            ids = list(tok.sot_sequence_including_notimestamps) + tok.encode(text) + [tok.eot]
            t = torch.tensor([ids])
            lp = torch.log_softmax(m.decoder(t[:, :-1], enc), -1)[0]
            n0 = len(tok.sot_sequence_including_notimestamps)
            s = sum(lp[i - 1, ids[i]].item() for i in range(n0, len(ids)))
            scores[text] = s
    v = np.array(list(scores.values())); p = np.exp(v - v.max()); p /= p.sum()
    probs = dict(zip(scores, p))
    p_hit = sum(probs[h] for h in HITS)
    best_miss = max(MISSES, key=lambda k: scores[k])
    return p_hit, best_miss.strip(), probs[best_miss]

def mfcc_frames(x, sr):
    return librosa.feature.mfcc(y=x, sr=sr, n_mfcc=13, n_fft=256, win_length=240, hop_length=24, n_mels=40,
                                fmax=6000, center=True)[1:]  # drop c0 (level)

_nat = None
def natural_dist():
    global _nat
    if _nat is None:
        d = []
        for p in sorted(glob.glob(os.path.join(HERE, 'names', 'nr_name_*.wav')))[:34]:
            x, sr = sf.read(p)
            M = mfcc_frames(x, sr)
            e = librosa.feature.rms(y=x, frame_length=240, hop_length=24)[0]
            k = 10  # 10 frames of 2 ms = 20 ms apart
            for i in range(0, M.shape[1] - k):
                if e[i] > 0.1 * e.max() and e[i + k] > 0.1 * e.max():
                    d.append(np.linalg.norm(M[:, i] - M[:, i + k]))
        _nat = np.sort(np.array(d))
    return _nat

def seam_spectral(x, sr, t):
    M = mfcc_frames(x, sr)
    i = int(round(t * sr / 24))
    a, b = i - 5, i + 5
    if a < 0 or b >= M.shape[1]: return np.nan, np.nan
    d = np.linalg.norm(M[:, a] - M[:, b])
    nat = natural_dist()
    return d, 100.0 * np.searchsorted(nat, d) / len(nat)

def seam_step(x, sr, t):
    """F0 step across the seam: nearest voiced 5 ms frames within 10 ms on each side (semitones)."""
    tt, f0, sc, v = hf0(x, sr, hop=0.005)
    b = [i for i in range(len(tt)) if v[i] and t - 0.010 <= tt[i] < t]
    a = [i for i in range(len(tt)) if v[i] and t < tt[i] <= t + 0.010]
    if not a or not b: return np.nan
    return 12 * np.log2(f0[a[0]] / f0[b[-1]])

def seam_pitch(x, sr, t):
    tt, f0, sc, v = hf0(x, sr, hop=0.005)
    def med(lo, hi):
        k = (tt >= lo) & (tt <= hi) & v
        return np.median(f0[k]) if k.sum() else np.nan
    fa, fb = med(t - 0.030, t - 0.005), med(t + 0.005, t + 0.030)
    return fa, fb, 12 * np.log2(fb / fa) if fa == fa and fb == fb else np.nan

def evaluate(path, joins, labels, models=('small.en', 'medium.en')):
    x, sr = sf.read(path)
    r = dict(file=os.path.basename(path))
    for mname in models:
        r[f'stt_{mname}'] = transcribe(path, mname)
    # in context: the real 'Falco!' call, 0.35 s of the bank's silence, then the candidate
    xf, _ = sf.read(os.path.join(HERE, 'src', 'falco.wav'))
    ctx = np.concatenate([xf, np.zeros(int(0.35 * sr)), x])
    cp = os.path.join(HERE, 'cands', '_ctx_tmp.wav'); sf.write(cp, ctx, sr)
    for mname in models:
        r[f'ctx_{mname}'] = transcribe(cp, mname)
    for mname in models:
        ph, bm, pm = forced(path, mname)
        r[f'phit_{mname}'] = round(float(ph), 3); r[f'bestmiss_{mname}'] = f'{bm} ({pm:.2f})'
    seams = []
    for k, t in enumerate(joins):
        fa, fb, st = seam_pitch(x, sr, t)
        d, pct = seam_spectral(x, sr, t)
        seams.append(dict(seam=f'{labels[k]} | {labels[k + 1]}', t=round(t, 3), f0_before=round(float(fa), 1),
                          f0_after=round(float(fb), 1), jump_st=round(float(st), 2),
                          step_st=round(float(seam_step(x, sr, t)), 2), mfcc_d=round(float(d), 1),
                          pct_vs_natural=round(float(pct), 1)))
    r['seams'] = seams
    return r

if __name__ == '__main__':
    meta = json.load(open(os.path.join(HERE, 'cands', 'meta.json')))
    names = sys.argv[1:] or list(meta)
    models = tuple(os.environ.get('WMODELS', 'small.en,medium.en').split(','))
    res = {}
    for n in names:
        p = os.path.join(HERE, 'cands', n + '.wav')
        r = evaluate(p, meta[n]['joins'], meta[n]['labels'], models=models)
        res[n] = r
        print(json.dumps(r, ensure_ascii=False), flush=True)
    op = os.path.join(HERE, 'cands', 'eval.json')
    old = json.load(open(op)) if os.path.exists(op) else {}
    old.update(res); json.dump(old, open(op, 'w'), indent=1, ensure_ascii=False)
