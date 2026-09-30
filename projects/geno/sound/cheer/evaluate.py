"""Judge the "Ge-no! Ge-no!" candidates with local recognizers only (no paid API, nothing generated):
 1. Whisper free transcription (small.en, medium.en, large-v3-turbo), alone and after a real chant (Kirby's
    "Kir-by! Kir-by!" then 0.3 s of silence) for context.
 2. Whisper forced choice (teacher-forced decoder log-likelihood, one encoder pass per file and model):
    - P(hit): " Geno! Geno!" and its same-sounding spellings against near-miss strings, softmaxed over the set;
    - cast choice: which of the 26 real chants' names plus Geno the file is, softmaxed over those 27. On the real chants
      this is the recognizer's baseline (how often it names the crowd's own chants right).
 3. wav2vec2 phoneme CTC (facebook/wav2vec2-lv-60-espeak-cv-ft): slot by slot, the likelihood of each option with the other
    slots held at /dʒ iː n oʊ/ in both cycles (onset, vowel, nasal, final).
 4. Seams: the MFCC step across each seam (+-10 ms) as a percentile of every natural 20 ms step in the 26 real chants, and
    the level step (dB) across it.

    .venv/bin/python projects/geno/sound/cheer/evaluate.py [NAME ...]         # candidates in cands.json -> cands/eval.json
    .venv/bin/python projects/geno/sound/cheer/evaluate.py --baseline         # the real chants: cast choice + free STT
"""
import glob, json, os, sys, warnings

warnings.filterwarnings('ignore')
import numpy as np
import soundfile as sf
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crowdsplice as cs  # noqa: E402

MODELS = os.environ.get('WMODELS', 'small.en,medium.en,turbo').split(',')
HITS = [' Geno! Geno!', ' Gino! Gino!', ' Jeno! Jeno!', ' Jino! Jino!', ' Geno, Geno!', ' Gino, Gino!', ' Geno. Geno.',
        ' Gino. Gino.', ' GENO! GENO!', ' GINO! GINO!', ' Geno!', ' Gino!']
MISSES = [' Dino! Dino!', ' Keno! Keno!', ' Zeno! Zeno!', ' Pino! Pino!', ' Chino! Chino!', ' Reno! Reno!', ' Nino! Nino!',
          ' Tino! Tino!', ' Gina! Gina!', ' Jenna! Jenna!', ' Gene! Gene!', ' Jean! Jean!', ' Genie! Genie!', ' Gee, no!',
          ' Jingo! Jingo!', ' Bingo! Bingo!', ' Juno! Juno!', ' Gemo! Gemo!', ' Jiggy! Jiggy!', ' Pichu! Pichu!',
          ' Peanut! Peanut!', ' Kino! Kino!', ' Go! Go!', ' Me, no!', ' Jeanie! Jeanie!', ' Jinx! Jinx!', ' Chino!',
          ' Dino!', ' Gina!', ' Jingle!', ' Genome!', ' Gino and Gino!', ' Ginny! Ginny!', ' Deano! Deano!']
CAST = {'Ca': ' Captain Falcon!', 'Cl': ' Young Link! Young Link!', 'Dk': ' Donkey Kong!', 'Dr': ' Doctor Mario!',
        'Fc': ' Falco!', 'Fe': " Roy's our boy!", 'Fx': ' Go Fox!', 'Gn': ' Ganondorf!', 'Gw': ' Game and Watch!',
        'Kb': ' Kirby! Kirby!', 'Kp': ' Bowser! Bowser!', 'Lg': ' Luigi!', 'Lk': ' Go Link!', 'Mr': ' Mario!',
        'Ms': ' Marth! Marth! Marth!', 'Mt': ' Mewtwo!', 'Ns': ' Ness! Ness! Ness!', 'Pc': ' Pichu!', 'Pe': ' Go Peach!',
        'Pk': ' Pikachu!', 'Pp': ' Ice Climbers!', 'Pr': ' Jigglypuff!', 'Sk': ' Sheik! Sheik!', 'Ss': ' Samus! Samus!',
        'Ys': ' Yoshi!', 'Zd': ' Zelda! Zelda!', 'Ge': ' Geno! Geno!'}
CONTEXT = 'Kb'          # the context chant (two syllables, two cycles, like "Ge-no! Ge-no!")
GAP = 0.3
_models = {}


def wmodel(name):
    import whisper
    if name not in _models:
        _models[name] = whisper.load_model(name, device='cpu')
    return _models[name]


def encode(m, x):
    import whisper
    audio = whisper.pad_or_trim(x.astype(np.float32))
    mel = whisper.log_mel_spectrogram(audio, n_mels=m.dims.n_mels).to(m.device)
    with torch.no_grad():
        return m.encoder(mel[None])


def free(m, enc):
    import whisper
    opts = whisper.DecodingOptions(language='en', temperature=0.0, fp16=False, without_timestamps=True)
    return whisper.decode(m, enc[0], opts).text.strip()


def scores(m, enc, texts, prefix=''):
    import whisper
    tok = whisper.tokenizer.get_tokenizer(multilingual=m.is_multilingual, language='en', task='transcribe')
    sot = list(tok.sot_sequence_including_notimestamps)
    pre = tok.encode(prefix) if prefix else []
    out = {}
    with torch.no_grad():
        for t in texts:
            ids = sot + pre + tok.encode(t) + [tok.eot]
            x = torch.tensor([ids])
            lp = torch.log_softmax(m.decoder(x[:, :-1], enc), -1)[0]
            n0 = len(sot) + len(pre)
            out[t] = sum(lp[i - 1, ids[i]].item() for i in range(n0, len(ids)))
    return out


def softmax(d):
    v = np.array(list(d.values())); p = np.exp(v - v.max()); p /= p.sum()
    return dict(zip(d, p))


def whisper16(x, sr=cs.SR):
    import librosa
    return librosa.resample(x, orig_sr=sr, target_sr=16000) if sr != 16000 else x


def with_context(y):
    c = cs.load(CONTEXT)
    return np.concatenate([c, np.zeros(int(GAP * cs.SR)), y])


def judge_whisper(m, y):
    r = {}
    for tag, audio, prefix in (('alone', y, ''), ('ctx', with_context(y), CAST[CONTEXT])):
        enc = encode(m, whisper16(audio))
        r[f'free_{tag}'] = free(m, enc)
        p = softmax(scores(m, enc, HITS + MISSES, prefix))
        r[f'p_hit_{tag}'] = round(float(sum(p[h] for h in HITS)), 3)
        bm = max(MISSES, key=lambda k: p[k]); r[f'best_miss_{tag}'] = (bm.strip(), round(float(p[bm]), 3))
        if tag == 'alone':
            pc = softmax(scores(m, enc, list(CAST.values())))
            r['cast_geno'] = round(float(pc[CAST['Ge']]), 3)
            top = max(pc, key=pc.get); r['cast_top'] = (top.strip(), round(float(pc[top]), 3))
    return r


def release():
    """Free the loaded recognizer (the machine is shared: one model in memory at a time)."""
    import gc
    _models.clear()
    try:
        import align
        align._m.clear()
    except Exception:
        pass
    gc.collect()


# ---- phonemes
SLOTS = {
    'onset': ['dʒ', 'tʃ', 'ʒ', 'ʃ', 'ɡ', 'd', 'z', 'k', 'p', 'j'],
    'vowel': ['iː', 'ɪ', 'eɪ', 'ɛ', 'i', 'aɪ'],
    'nasal': ['n', 'm', 'ŋ', 'd', 'l', 'ŋ ɡ', 't', ''],
    'final': ['oʊ', 'ɔ', 'aʊ', 'ɑː', 'ə', 'uː', 'ʌ', 'o', 'ɔː', 'i'],
}
BASE = dict(onset='dʒ', vowel='iː', nasal='n', final='oʊ')
BACK_ROUNDED = {'oʊ', 'o', 'ɔ', 'ɔː'}


def ctc_score(lp, seq, vocab):
    ids = torch.tensor([[vocab[p] for p in seq.split()]])
    return -torch.nn.functional.ctc_loss(lp[:, None, :], ids, torch.tensor([lp.shape[0]]), torch.tensor([ids.shape[1]]),
                                         blank=vocab['<pad>'], reduction='sum').item()


def judge_phones(y):
    import align
    _, _, vocab = align.model()
    lp = align.logprobs(y)
    out = {}
    for slot, opts in SLOTS.items():
        s = []
        for o in opts:
            ph = dict(BASE); ph[slot] = o
            one = ' '.join(p for p in (ph['onset'], ph['vowel'], ph['nasal'], ph['final']) if p)
            s.append(ctc_score(lp, one + ' ' + one, vocab))
        s = np.array(s); p = np.exp(s - s.max()); p /= p.sum()
        out[slot] = sorted(((o or '∅', round(float(q), 3)) for o, q in zip(opts, p)), key=lambda z: -z[1])[:3]
    fin = dict(out['final'])
    out['p_back_rounded'] = round(sum(v for k, v in fin.items() if k in BACK_ROUNDED), 3)
    return out


# ---- seams
def mfcc(x):
    import librosa
    return librosa.feature.mfcc(y=x, sr=cs.SR, n_mfcc=13, n_fft=512, win_length=400, hop_length=40, n_mels=40,
                                fmax=7000)[1:]


_nat = None


def natural_steps():
    """|MFCC step| across 20 ms at every active frame of the 26 real chants."""
    global _nat
    if _nat is None:
        d = []
        for p in sorted(glob.glob(os.path.join(cs.WORK, 'chants', 'us_*.wav'))):
            x, _ = sf.read(p)
            M = mfcc(x); k = 4                                   # 10 ms = 4 hops of 2.5 ms
            e = 20 * np.log10(np.sqrt(np.convolve(x ** 2, np.ones(400) / 400, 'same')[::40][:M.shape[1]]) + 1e-9)
            for i in range(k, M.shape[1] - k):
                if e[i] > e.max() - 20:
                    d.append(np.linalg.norm(M[:, i + k] - M[:, i - k]))
        _nat = np.sort(np.array(d))
    return _nat


def seam_stats(y, seams):
    nat = natural_steps(); M = mfcc(y); k = 4; out = []
    for t in seams:
        i = int(round(t * cs.SR / 40))
        d = np.linalg.norm(M[:, min(i + k, M.shape[1] - 1)] - M[:, max(i - k, 0)])
        pct = 100.0 * np.searchsorted(nat, d) / len(nat)
        a = y[max(0, int((t - 0.025) * cs.SR)):int((t - 0.005) * cs.SR)]
        b = y[int((t + 0.005) * cs.SR):int((t + 0.025) * cs.SR)]
        out.append(dict(t=round(t, 3), spec_pct=round(pct, 1), level_step=round(cs.rms_db(b) - cs.rms_db(a), 2)))
    return out


def evaluate(names, models=MODELS, phones=True):
    """Model by model (one recognizer loaded at a time), every candidate; results merge into cands/eval.json."""
    meta = json.load(open(os.path.join(cs.WORK, 'cands', 'cands.json')))
    path = os.path.join(cs.WORK, 'cands', 'eval.json')
    res = json.load(open(path)) if os.path.exists(path) else {}
    ys = {}
    for n in names:
        y, sr = sf.read(meta[n]['path']); assert sr == cs.SR
        ys[n] = y
        res.setdefault(n, {}).setdefault('whisper', {})
        res[n]['seams'] = seam_stats(y, meta[n]['seams'])
    for mn in models:
        m = wmodel(mn)
        for n in names:
            v = res[n]['whisper'][mn] = judge_whisper(m, ys[n])
            print(f"{n:28s} {mn:10s} free '{v['free_alone']}' | ctx '{v['free_ctx']}' | P(hit) {v['p_hit_alone']:.2f} / ctx "
                  f"{v['p_hit_ctx']:.2f} (miss {v['best_miss_alone'][0]}) | cast P(Geno) {v['cast_geno']:.2f}", flush=True)
            json.dump(res, open(path, 'w'), indent=1, ensure_ascii=False)
        release()
    if phones:
        for n in names:
            ph = res[n]['phones'] = judge_phones(ys[n])
            print(f'{n:28s} phones ' + '  '.join(f"{k}: " + ' '.join(f'{o}={p:.2f}' for o, p in ph[k]) for k in SLOTS)
                  + f"  back-rounded {ph['p_back_rounded']:.2f}  seams "
                  + ' '.join(f"{s['spec_pct']:.0f}%/{s['level_step']:+.1f}dB" for s in res[n]['seams']), flush=True)
            json.dump(res, open(path, 'w'), indent=1, ensure_ascii=False)
        release()
    return res


def baseline(models=MODELS):
    """The recognizers on the real chants: free transcription and cast choice (is the right name the top pick?)."""
    out = {}
    files = [p for p in sorted(glob.glob(os.path.join(cs.WORK, 'chants', 'us_*.wav'))) if os.path.basename(p).split('_')[1] in CAST]
    for name in models:
        m = wmodel(name)
        for p in files:
            code = os.path.basename(p).split('_')[1]
            x, _ = sf.read(p); enc = encode(m, whisper16(x))
            pc = softmax(scores(m, enc, list(CAST.values())))
            top = max(pc, key=pc.get)
            out.setdefault(code, {})[name] = dict(free=free(m, enc), p_right=round(float(pc[CAST[code]]), 3), top=top.strip(),
                                                  p_geno=round(float(pc[CAST['Ge']]), 3))
            r = out[code][name]
            print(f"{code} {name}: '{r['free']}' P(right) {r['p_right']:.2f} top {r['top']} P(Geno) {r['p_geno']:.2f}", flush=True)
        release()
        right = sum(out[c][name]['top'] == CAST[c].strip() for c in out)
        print(f'{name}: cast choice top-1 right on {right}/{len(out)} real chants', flush=True)
    json.dump(out, open(os.path.join(cs.WORK, 'chants', 'baseline.json'), 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    if '--baseline' in sys.argv:
        baseline()
    else:
        meta = json.load(open(os.path.join(cs.WORK, 'cands', 'cands.json')))
        names = [a for a in sys.argv[1:] if not a.startswith('--')] or list(meta)
        evaluate(names, phones='--no-phones' not in sys.argv)
