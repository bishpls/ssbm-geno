"""Local phoneme recognizer (wav2vec2 espeak CTC). Prints phone string and per-frame (20ms) spans."""
import sys, os, warnings, numpy as np, soundfile as sf, librosa, torch
warnings.filterwarnings('ignore')
from transformers import Wav2Vec2ForCTC, Wav2Vec2FeatureExtractor
import json
MODEL = os.environ.get('PMODEL', 'facebook/wav2vec2-lv-60-espeak-cv-ft')
fe = Wav2Vec2FeatureExtractor.from_pretrained(MODEL)
model = Wav2Vec2ForCTC.from_pretrained(MODEL).eval()
from huggingface_hub import hf_hub_download
vocab = json.load(open(hf_hub_download(MODEL, 'vocab.json')))
inv = {v: k for k, v in vocab.items()}
EN = set('n s t ə l a i k d m ɛ ɾ e ɪ p o ɐ z ð f j v b ɹ ʊ iː r w ʌ u ɡ æ aɪ ʃ h ɔ ɑː ŋ ɚ eɪ uː oʊ ᵻ θ aʊ ɑ dʒ əl ɜː ʒ tʃ ɔː ɑːɹ ɔːɹ ʔ ɛɹ ɪɹ ɔɪ ʊɹ oːɹ aɪɚ aɪə ɒ n̩ əʊ'.split())
MASK = np.array([0.0 if (inv[i] in EN or inv[i] in ('<pad>',)) else -1e9 for i in range(len(inv))], dtype=np.float32)
def recognize(path, spans=False):
    x, sr = sf.read(path)
    if x.ndim > 1: x = x.mean(1)
    x = librosa.resample(x, orig_sr=sr, target_sr=16000)
    x = np.concatenate([np.zeros(1600), x, np.zeros(1600)])  # 100 ms pad
    inp = fe(x, sampling_rate=16000, return_tensors='pt')
    with torch.no_grad():
        logits = model(inp.input_values).logits[0]
    if not os.environ.get('ALLPHONES'): logits = logits + torch.from_numpy(MASK)
    ids = logits.argmax(-1).numpy()
    probs = logits.softmax(-1).numpy()
    out, segs, prev = [], [], None
    for i, k in enumerate(ids):
        tok = inv[int(k)]
        if k != prev and tok not in ('<pad>', '<s>', '</s>', '<unk>'):
            out.append(tok); segs.append((round(i * 0.02 - 0.1, 3), tok, round(float(probs[i, k]), 2)))
        prev = k
    return ' '.join(out), segs
if __name__ == '__main__':
    for p in sys.argv[1:]:
        s, segs = recognize(p)
        print(f"{os.path.basename(p)}\t/{s}/")
        if os.environ.get('SPANS'): print('   ', segs)
