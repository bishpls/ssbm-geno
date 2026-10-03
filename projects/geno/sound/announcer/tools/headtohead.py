"""Pichu-vowel vs Peach-vowel, everything else identical, repeated over small build perturbations."""
import sys, os, json, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from final import COMMON, VOWEL, level
from candidates import make
from splice import write, SR
import evaluate as ev, phonecheck as pc
from onetake import hnr
HERE = os.path.expanduser(os.environ.get('ANNOUNCER_WORK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'announcer')))   # the work folder (game audio)
perturb = {'as delivered': {}, 't_n=70ms': dict(t_n=0.070), 't_n=82ms': dict(t_n=0.082),
           'J xfade 22ms': dict(xf=(0.022, 0.014, 0.012, 0.036)), 't_iy=135ms': dict(t_iy=0.135), 't_iy=155ms': dict(t_iy=0.155)}
rows = []
for pn, pd in perturb.items():
    for v in ['pichu', 'peach']:
        cfg = dict(COMMON, **VOWEL[v], n='no'); cfg.update(pd)
        y, joins, spans, labels = make(**cfg); y = level(y)
        p = os.path.join(HERE, 'cands', 'quick', f'h2h_{pn.replace(" ", "_").replace("=", "")}_{v}.wav'); write(p, y)
        P = [ev.forced(p, m)[0] for m in ('small.en', 'medium.en', 'turbo')]
        T = [ev.transcribe(p, m) for m in ('small.en', 'medium.en', 'turbo')]
        sl = pc.slots(p); d = dict(sl['onset']).get('dʒ', 0); i = dict(sl['vowel']); iv = i.get('iː', 0) + i.get('i', 0)
        nn = dict(sl['nasal']).get('n', 0); f = dict(sl['final']); fr = sum(f.get(k, 0) for k in ('o', 'oʊ', 'ɔ', 'ɔː'))
        seams = [round(ev.seam_spectral(y, SR, j)[1]) for j in joins]
        steps = [round(float(ev.seam_pitch(y, SR, j)[2]), 2) for j in joins]
        a, b = spans[1]; h = hnr(y, SR, a + 0.01, b - 0.01)
        r = dict(perturbation=pn, vowel=v, P_mean=round(float(np.mean(P)), 3), P=[round(float(q), 3) for q in P], stt=T,
                 dZ=round(d, 2), iy=round(iv, 2), n=round(nn, 2), final_back_rounded=round(fr, 2), seam_pct=seams,
                 seam_f0_jump_st=steps, vowel_hnr=round(h, 1))
        rows.append(r); print(json.dumps(r, ensure_ascii=False), flush=True)
json.dump(rows, open(os.path.join(HERE, 'cands', 'headtohead.json'), 'w'), indent=1, ensure_ascii=False)
for k in ('P_mean', 'dZ', 'iy', 'n', 'final_back_rounded', 'vowel_hnr'):
    a = [r[k] for r in rows if r['vowel'] == 'pichu']; b = [r[k] for r in rows if r['vowel'] == 'peach']
    print(f"{k:20s} pichu {np.mean(a):.3f}  peach {np.mean(b):.3f}  peach higher {sum(y > x for x, y in zip(a, b))}/{len(a)}")
a = [r['seam_pct'][0] for r in rows if r['vowel'] == 'pichu']; b = [r['seam_pct'][0] for r in rows if r['vowel'] == 'peach']
print('J->vowel seam pct: pichu', a, ' peach', b)
hits = lambda v: sum(any(w in t.lower().replace('-', '') for w in ('gino', 'geno', 'jeno', 'jino')) for r in rows if r['vowel'] == v for t in r['stt'])
print('free STT phonetic hits: pichu', hits('pichu'), '/18  peach', hits('peach'), '/18')
