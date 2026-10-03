"""Round 2 (Michael's pick): C's head (Jigglypuff J + Pichu ee + "Green team" n, exactly as in geno_C_greenN)
with Mario's long final 'o'. Variants differ only in the O. Every sample is the announcer's own recording."""
import sys, os, json, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, soundfile as sf
from candidates import make_segs, rms_db, V_DB
from splice import Seg, build, write, load, SR
from final import FINAL

HERE = os.path.expanduser(os.environ.get('ANNOUNCER_WORK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'announcer')))   # the work folder (game audio)
C_CFG = FINAL['geno_C_greenN']
MARIO_O0 = 0.43          # start of Mario's o used in D (F0 ~242 Hz, matches the release's end pitch)
MARIO_END = 1.267        # end of the recording (natural decay from ~1.05 s)
BODY_END = 1.05          # Mario's o holds ~-10 dB to here, then decays ~ -60 dB/s
G_MARIO = V_DB - rms_db('mario', MARIO_O0, MARIO_O0 + 0.15)
G_FALCO = V_DB - rms_db('falco', 0.45, 0.60)

def c_head():
    """C's J + ee + n (up to 8 ms before the n|release crossfade): its RMS about its mean, and its mean (DC)."""
    x, _ = sf.read(os.path.join(HERE, 'geno_C_greenN.wav'))
    m = json.load(open(os.path.join(HERE, 'geno_candidates.json')))['geno_C_greenN']
    h = x[:int((m['joins'][2] - 0.008) * SR)]
    return np.std(h), np.mean(h)

def mario_seg(t0=MARIO_O0, t1=MARIO_END, **kw):
    return Seg('mario', t0, t1, gain_db=G_MARIO, label=kw.pop('label', 'o<mario'), **kw)

def assemble(o_segs, o_xf=(), release_end=240):
    cfg = dict(C_CFG)
    a, b, f = cfg['no_trans']
    cfg['no_trans'] = (a, b, (f[0], release_end))
    segs, xfs = make_segs(**cfg, o_segs=o_segs, o_xf=list(o_xf))
    y, joins, spans = build(segs, xfs[:len(segs) - 1])
    nz = np.nonzero(np.abs(y) > 1e-6)[0]; y = y[:nz[-1] + 1]      # trims end in their own fade: drop the zeros
    # level and DC: J+ee+n at exactly C's gain and offset, so the head is C's head sample for sample
    e = int((joins[2] - 0.008) * SR)
    sd, dc = c_head()
    y = (y - y[:e].mean()) * (sd / np.std(y[:e])) + dc
    n = int(0.025 * SR); y[-n:] *= np.cos(np.linspace(0, np.pi / 2, n)) ** 2
    pk = np.abs(y).max()
    if pk > 0.98: y *= 0.98 / pk
    return y, joins, spans, [s.label for s in segs]

def compressed(total, decay_natural=True):
    """PSOLA time-compress Mario's o body (pitch glide kept, just faster); the decay stays natural."""
    head = 0.378  # output time of the release|o seam in C-type builds
    o_len = total - head
    body = BODY_END - MARIO_O0; dec = MARIO_END - BODY_END
    if decay_natural:
        f = (o_len - dec) / body
        tier = [(0.0, f), ((BODY_END - MARIO_O0) / (MARIO_END - MARIO_O0) - 0.01, f),
                ((BODY_END - MARIO_O0) / (MARIO_END - MARIO_O0) + 0.01, 1.0), (1.0, 1.0)]
    else:
        f = o_len / (body + dec); tier = [(0.0, f), (1.0, f)]
    return [mario_seg(dur_tier=tier, floor=90, ceil=300)], f

def trimmed(total, fade=0.15):
    head = 0.378
    return [mario_seg(t1=MARIO_O0 + total - head, fade_out=fade)]

def bridged(falco_end, mario_from, xf=0.040):
    """C exactly through the start of Falco's o, then Falco's o crossfades into Mario's o at a pitch match."""
    return [Seg('falco', 0.45, falco_end, gain_db=G_FALCO, label='o<falco'),
            mario_seg(t0=mario_from, label='o<mario(tail)')], [xf]

VARIANTS = {}
def add(name, o_segs, o_xf=(), release_end=240, note=''):
    VARIANTS[name] = (o_segs, o_xf, release_end, note)

add('CD_full', [mario_seg()], note="Mario's o at full length (as in D)")
for tot in (1.00, 0.90):
    s, f = compressed(tot); add(f'CD_c{int(tot*100)}', s, note=f'o body PSOLA-compressed x{f:.2f}, natural decay')
    s, f = compressed(tot, decay_natural=False); add(f'CD_u{int(tot*100)}', s, note=f'whole o compressed x{f:.2f}')
    add(f'CD_t{int(tot*100)}', trimmed(tot), note='o trimmed, 150 ms -70 dB/s decay')
for fe, mf in ((0.47, 0.66), (0.49, 0.72), (0.52, 0.78)):
    s, xf = bridged(fe, mf); add(f'CD_b{int(fe*100)}_{int(mf*100)}', s, xf, release_end=205,
                                 note=f'C through Falco o 0.45-{fe}, into Mario o from {mf}')

FINALS = {  # delivered name <- variant (ranked; see NOTES.md section 7)
    'geno_CD_bridge': 'CD_b47_66',   # 1
    'geno_CD_100': 'CD_u100',        # 2
    'geno_CD_full': 'CD_full',       # 3
    'geno_CD_090': 'CD_c90',         # 4
}
CONTEXT = ('geno_CD_bridge', 'geno_CD_100', 'geno_CD_full')

def deliver():
    meta_p = os.path.join(HERE, 'cands', 'meta.json'); meta = json.load(open(meta_p))
    gc_p = os.path.join(HERE, 'geno_candidates.json'); gc = json.load(open(gc_p))
    for name, var in FINALS.items():
        o_segs, o_xf, rel, note = VARIANTS[var]
        y, joins, spans, labels = assemble(o_segs, o_xf, rel)
        for d in (HERE, os.path.join(HERE, 'cands')):
            write(os.path.join(d, name + '.wav'), y)
        meta[name] = gc[name] = dict(variant=var, note=note, joins=joins, spans=spans, labels=labels, dur=len(y) / SR,
                                     head='geno_C_greenN (identical through the n; head level matched to C)')
        print(f'{name:16s} <- {var:10s} {len(y)/SR:.3f}s peak={np.abs(y).max():.2f}  {note}')
    json.dump(meta, open(meta_p, 'w'), indent=1, default=str); json.dump(gc, open(gc_p, 'w'), indent=1, default=str)
    gap = np.zeros(int(0.40 * SR))
    for name in CONTEXT:
        c, _ = sf.read(os.path.join(HERE, name + '.wav'))
        write(os.path.join(HERE, name + '_after_falco.wav'), np.concatenate([load('falco'), gap, c]))
    print('context files:', ', '.join(n + '_after_falco.wav' for n in CONTEXT))

if __name__ == '__main__' and sys.argv[1:] == ['deliver']:
    deliver(); sys.exit()
if __name__ == '__main__':
    only = sys.argv[1:]
    out = os.path.join(HERE, 'cands'); meta_p = os.path.join(out, 'meta.json'); meta = json.load(open(meta_p))
    for name, (o_segs, o_xf, rel, note) in VARIANTS.items():
        if only and name not in only: continue
        y, joins, spans, labels = assemble(o_segs, o_xf, rel)
        write(os.path.join(out, name + '.wav'), y)
        meta[name] = dict(note=note, joins=joins, spans=spans, labels=labels, dur=len(y) / SR)
        print(f'{name:12s} {len(y)/SR:.3f}s peak={np.abs(y).max():.2f} rms={20*np.log10(np.sqrt(np.mean(y**2))):.1f}dB '
              f'joins={[round(j, 3) for j in joins]}  {note}', flush=True)
    json.dump(meta, open(meta_p, 'w'), indent=1, default=str)
