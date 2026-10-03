"""Phone-level forced choice with a local wav2vec2 phoneme CTC model (espeak IPA): CTC log-likelihood of
/dʒ iː n oʊ/ against near-miss phone strings, softmaxed over the set. Lexicon-free, so it checks the sounds,
not the spelling."""
import sys, os, json, warnings
warnings.filterwarnings('ignore')
import numpy as np, soundfile as sf, librosa, torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2FeatureExtractor
from huggingface_hub import hf_hub_download
MODEL = 'facebook/wav2vec2-lv-60-espeak-cv-ft'
fe = Wav2Vec2FeatureExtractor.from_pretrained(MODEL)
model = Wav2Vec2ForCTC.from_pretrained(MODEL).eval()
vocab = json.load(open(hf_hub_download(MODEL, 'vocab.json')))
TARGET = 'dʒ iː n oʊ'
ALTS = ['dʒ ɪ n oʊ', 'dʒ ɪ ŋ ɡ oʊ', 'dʒ iː n ə', 'ɡ iː n oʊ', 'tʃ iː n oʊ', 'dʒ iː m oʊ', 'dʒ iː d oʊ', 'd iː n oʊ',
        'ʒ iː n oʊ', 'dʒ eɪ n oʊ', 'dʒ iː n uː', 'dʒ iː n ɔ', 'dʒ ɛ n oʊ', 'dʒ iː ŋ oʊ', 'dʒ iː l oʊ', 'dʒ iː oʊ',
        'dʒ iː n ɡ oʊ', 'p iː n oʊ', 'dʒ ɪ m oʊ', 'dʒ iː n oʊ k', 'z iː n oʊ', 'k iː n oʊ', 'dʒ iː n ɑː', 'dʒ iː n aʊ']
def logprobs(path):
    x, sr = sf.read(path)
    x = librosa.resample(x, orig_sr=sr, target_sr=16000)
    x = np.concatenate([np.zeros(1600), x, np.zeros(1600)])
    inp = fe(x, sampling_rate=16000, return_tensors='pt')
    with torch.no_grad():
        return torch.log_softmax(model(inp.input_values).logits[0], -1)
def score(lp, seq):
    ids = torch.tensor([[vocab[p] for p in seq.split()]])
    return -torch.nn.functional.ctc_loss(lp[:, None, :], ids, torch.tensor([lp.shape[0]]), torch.tensor([ids.shape[1]]),
                                         blank=vocab['<pad>'], reduction='sum').item()
def check(path):
    lp = logprobs(path)
    s = {q: score(lp, q) for q in [TARGET] + ALTS}
    v = np.array(list(s.values())); p = np.exp(v - v.max()); p /= p.sum()
    pr = dict(zip(s, p)); best = max(ALTS, key=lambda q: s[q])
    return pr[TARGET], best, pr[best]
SLOTS = {
    'onset': (['dʒ', 'tʃ', 'ʒ', 'ʃ', 'ɡ', 'd', 'z', 'k', 'p', 'j'], lambda x: f'{x} iː n oʊ'),
    'vowel': (['iː', 'ɪ', 'eɪ', 'ɛ', 'i'], lambda x: f'dʒ {x} n oʊ'),
    'nasal': (['n', 'm', 'ŋ', 'd', 'l', 'ŋ ɡ', 'n d', ''], lambda x: f'dʒ iː {x} oʊ'.replace('  ', ' ')),
    'final': (['oʊ', 'ɔ', 'aʊ', 'ɑː', 'ə', 'uː', 'ʌ', 'o', 'ɔː'], lambda x: f'dʒ iː n {x}'),
}
def slots(path):
    lp = logprobs(path); out = {}
    for k, (opts, f) in SLOTS.items():
        s = np.array([score(lp, f(o)) for o in opts]); p = np.exp(s - s.max()); p /= p.sum()
        out[k] = sorted(zip(opts, p), key=lambda z: -z[1])
    return out
def fmt(out):
    return '  '.join(f"{k}: " + ' '.join(f"{o or '∅'}={p:.2f}" for o, p in v[:3]) for k, v in out.items())

if __name__ == '__main__' and os.environ.get('SLOTS'):
    for p in sys.argv[1:]:
        print(f'{os.path.basename(p):28s}', fmt(slots(p)))
    sys.exit()
if __name__ == '__main__':
    for p in sys.argv[1:]:
        pt, b, pb = check(p)
        print(f'{os.path.basename(p):28s} P(/{TARGET}/)={pt:.3f}  best alt=/{b}/ ({pb:.3f})')
