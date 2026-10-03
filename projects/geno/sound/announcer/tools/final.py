"""Build the delivered GENO candidates + context files into ~/games/melee/work/announcer/."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, soundfile as sf
from candidates import make, IY_PITCH_SCOOP
from splice import SR, write, load

HERE = os.path.expanduser(os.environ.get('ANNOUNCER_WORK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'announcer')))   # the work folder (game audio)
TARGET_RMS_DB = -11.3   # median RMS of the 28 real character name calls in nr_name.ssm

# shared by every candidate unless overridden
COMMON = dict(j='jiggly', j_end=0.076, iy_pitch=IY_PITCH_SCOOP, t_iy=0.145, t_n=0.075,
              no_trans=(0.078, 0.160, (250, 205)), o_start=0.450, xf=(0.016, 0.014, 0.012, 0.036))
VOWEL = {'pichu': dict(iy='pichu', iy_span=(0.042, 0.156)),
         'peach': dict(iy='peach', iy_span=(0.055, 0.262))}

FINAL = {
    # A/B: the head-to-head pair; everything identical except where the stressed /i:/ comes from
    'geno_A_pichu': dict(COMMON, **VOWEL['pichu'], n='no'),
    'geno_B_peach': dict(COMMON, **VOWEL['peach'], n='no'),
    # C: /n/ from "Green team" (a real vowel->nasal context), else as A
    'geno_C_greenN': dict(COMMON, **VOWEL['pichu'], n='green'),
    # D: final syllable from "Mario" (its long falling 'o' and tail) instead of Falco
    'geno_D_marioO': dict(COMMON, **VOWEL['pichu'], n='no', o='mario', o_start=0.43,
                          no_trans=(0.078, 0.160, (250, 240))),
    # E: the brief's recipe as written: J Jigglypuff, /i:/ Pichu, /n/ Ness, /o/ Falco (no n->o transition)
    'geno_E_recipe': dict(j='jiggly', j_end=0.076, iy_pitch=IY_PITCH_SCOOP, t_iy=0.145, t_n=0.085, **VOWEL['pichu'], n='ness',
                          o='falco', o_start=0.392, xf=(0.016, 0.014, 0.012)),
}

def level(y):
    y = y - y.mean()
    g = 10 ** ((TARGET_RMS_DB - 20 * np.log10(np.sqrt(np.mean(y ** 2)))) / 20)
    y = y * g
    pk = np.abs(y).max()
    if pk > 0.98: y *= 0.98 / pk
    # the bank's calls end in their reverb tail at about -45 dB; finish the last 25 ms the same way
    n = int(0.025 * SR); y[-n:] *= np.cos(np.linspace(0, np.pi / 2, n)) ** 2
    return y

if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'cands'), exist_ok=True)
    meta = {}
    for name, cfg in FINAL.items():
        y, joins, spans, labels = make(**cfg)
        y = level(y)
        write(os.path.join(HERE, name + '.wav'), y)
        # also into cands/ so tools/evaluate.py can pick them up with their seam metadata
        write(os.path.join(HERE, 'cands', name + '.wav'), y)
        meta[name] = dict(cfg={k: (list(v) if isinstance(v, tuple) else v) for k, v in cfg.items()}, joins=joins,
                          spans=spans, labels=labels, dur=len(y) / SR)
        print(f'{name:15s} {len(y)/SR:.3f}s peak={np.abs(y).max():.2f} joins={[round(j, 3) for j in joins]} {labels}')
    mp = os.path.join(HERE, 'cands', 'meta.json')
    old = json.load(open(mp)) if os.path.exists(mp) else {}; old.update(meta); json.dump(old, open(mp, 'w'), indent=1, default=str)
    json.dump(meta, open(os.path.join(HERE, 'geno_candidates.json'), 'w'), indent=1, default=str)
    # context files: a real call, the bank's own inter-call silence, then the candidate
    gap = np.zeros(int(0.40 * SR))
    def ctx(ref, cand, out):
        r = load(ref); c, _ = sf.read(os.path.join(HERE, cand + '.wav'))
        write(os.path.join(HERE, out), np.concatenate([r, gap, c]))
    ctx('falco', 'geno_A_pichu', 'geno_A_pichu_after_falco.wav')
    ctx('falco', 'geno_B_peach', 'geno_B_peach_after_falco.wav')
    ctx('pichu', 'geno_A_pichu', 'geno_A_pichu_after_pichu.wav')
    ctx('peach', 'geno_B_peach', 'geno_B_peach_after_peach.wav')
    print('context files written')
