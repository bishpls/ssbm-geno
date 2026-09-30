"""Phone spans in the crowd chants: CTC forced alignment of a known phone string with the local wav2vec2 phoneme model
(facebook/wav2vec2-lv-60-espeak-cv-ft; a recognizer, used only to find where the sounds are). 20 ms frames.

    .venv/bin/python projects/geno/sound/cheer/align.py            # every chant in PHONES, printed and saved to align.json
"""
import json, os, sys, warnings

warnings.filterwarnings('ignore')
import numpy as np
import torch
from torchaudio.functional import forced_align

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crowdsplice as cs  # noqa: E402

MODEL = 'facebook/wav2vec2-lv-60-espeak-cv-ft'
# what the crowd chants, per fighter code, as espeak IPA phones (one token per phone in the model's vocab)
PHONES = {
    'Lg': 'l uː iː dʒ i', 'Pr': 'dʒ ɪ ɡ l i p ʌ f', 'Mr': 'm ɑː ɹ i oʊ', 'Ns': 'n ɛ s n ɛ s n ɛ s n ɛ s',
    'Gn': 'ɡ æ n ə n d ɔːɹ f', 'Kb': 'k ɜː b i k ɜː b i', 'Kp': 'b aʊ z ɚ b aʊ z ɚ', 'Ss': 's æ m ə s s æ m ə s',
    'Fc': 'f æ l k oʊ', 'Pe': 'ɡ oʊ p iː tʃ', 'Fx': 'ɡ oʊ f ɑː k s', 'Lk': 'ɡ oʊ l ɪ ŋ k', 'Pc': 'p iː tʃ uː',
    'Ys': 'j oʊ ʃ iː', 'Pk': 'p iː k ə tʃ uː', 'Dk': 'd ɑː ŋ k iː k ɑː ŋ', 'Dr': 'd ɑː k t ɚ m ɑː ɹ i oʊ',
    'Zd': 'z ɛ l d ə z ɛ l d ə', 'Sk': 'ʃ iː k ʃ iː k', 'Mt': 'm j uː t uː', 'Ms': 'm ɑːɹ θ m ɑːɹ θ m ɑːɹ θ',
    'Fe': 'ɹ ɔɪ z aʊɚ b ɔɪ', 'Gw': 'ɡ eɪ m æ n d w ɑː tʃ', 'Cl': 'j ʌ ŋ l ɪ ŋ k j ʌ ŋ l ɪ ŋ k',
    'Ca': 'k æ p t ɪ n f æ l k ə n', 'Pp': 'aɪ s k l aɪ m ɚ z aɪ s k l aɪ m ɚ z',
}
_m = {}


def model():
    if not _m:
        from transformers import Wav2Vec2ForCTC, Wav2Vec2FeatureExtractor
        from huggingface_hub import hf_hub_download
        _m['fe'] = Wav2Vec2FeatureExtractor.from_pretrained(MODEL)
        _m['model'] = Wav2Vec2ForCTC.from_pretrained(MODEL).eval()
        _m['vocab'] = json.load(open(hf_hub_download(MODEL, 'vocab.json')))
    return _m['fe'], _m['model'], _m['vocab']


def logprobs(x, sr=cs.SR):
    import librosa
    fe, m, _ = model()
    if sr != 16000:
        x = librosa.resample(x, orig_sr=sr, target_sr=16000)
    x = np.concatenate([np.zeros(1600), x, np.zeros(1600)])       # 100 ms pad each side
    with torch.no_grad():
        return torch.log_softmax(m(fe(x, sampling_rate=16000, return_tensors='pt').input_values).logits[0], -1)


def align(x, phones, sr=cs.SR):
    """[(phone, t0, t1, mean prob)] in seconds of x."""
    _, _, vocab = model()
    lp = logprobs(x, sr)
    ids = torch.tensor([[vocab[p] for p in phones.split()]], dtype=torch.int32)
    path, scores = forced_align(lp[None], ids, blank=vocab['<pad>'])
    path, scores = path[0].numpy(), scores[0].exp().numpy()
    out, k, prev = [], -1, None
    toks = phones.split()
    for i, (tok, sc) in enumerate(zip(path, scores)):
        if tok == vocab['<pad>']:
            prev = None; continue
        if tok != prev:
            k += 1; out.append([toks[k], i, i + 1, [sc]])
        else:
            out[-1][2] = i + 1; out[-1][3].append(sc)
        prev = tok
    return [(p, round(a * 0.02 - 0.1, 3), round(b * 0.02 - 0.1, 3), round(float(np.mean(s)), 2)) for p, a, b, s in out]


if __name__ == '__main__':
    codes = sys.argv[1:] or list(PHONES)
    res = {}
    for c in codes:
        spans = align(cs.load(c), PHONES[c])
        res[c] = spans
        print(f'{c}: ' + '  '.join(f'{p} {a:.2f}-{b:.2f} ({s:.2f})' for p, a, b, s in spans), flush=True)
    path = os.path.join(cs.WORK, 'chants', 'align.json')
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(res)
    json.dump(old, open(path, 'w'), indent=1, ensure_ascii=False)
