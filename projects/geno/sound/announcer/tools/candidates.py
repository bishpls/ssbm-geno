"""Candidate 'GENO!' builds. Every sample is from the announcer's recorded calls (see NOTES.md for sources)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from splice import Seg, build, finish, write, load, SR

HERE = os.path.expanduser(os.environ.get('ANNOUNCER_WORK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'announcer')))   # the work folder (game audio)

def rms_db(name, a, b):
    x = load(name)[int(a * SR):int(b * SR)]
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)))

# ---- template: Falco's own call (FAL-co), measured with tools/hf0.py -------------------------------------
# FA vowel 0.045-0.185: 339 -> 366/372 peak -> 349 plateau -> 326 ; /l/ 0.185-0.255: 321 -> 225 ; 'co' natural.
IY_PITCH = [(0.0, 340), (0.12, 364), (0.3, 356), (0.55, 349), (0.8, 338), (1.0, 326)]
N_PITCH = [(0.0, 318), (0.35, 285), (0.7, 250), (1.0, 224)]
T_IY, T_N = 0.160, 0.085       # durations (FA vowel ~140 ms + onset; /l/ ~70-90 ms)
V_DB, N_DB = rms_db('falco', 0.05, 0.18), -9.6

# ---- segment inventory (core spans in each source, seconds) ----------------------------------------------
J = {
    'jiggly': Seg('jigglypuff', 0.012, 0.080, label='J<Jigglypuff'),
    'giant': Seg('giant', 0.004, 0.050, label='J<Giant'),
}
J_RATIO = {'jiggly': rms_db('jigglypuff', 0.012, 0.08) - rms_db('jigglypuff', 0.085, 0.15),
           'giant': rms_db('giant', 0.004, 0.05) - rms_db('giant', 0.06, 0.2)}
IY = {
    'pichu': ('pichu', 0.040, 0.152),
    'peach': ('peach', 0.040, 0.262),
    'green': ('greenteam', 0.092, 0.203),
    'giga': ('gigabowser', 0.045, 0.140),
    'sheik': ('sheik', 0.140, 0.360),
}
N = {
    'ness': ('ness', 0.040, 0.124),
    'green': ('greenteam', 0.207, 0.322),
    'no': ('nocontest', 0.030, 0.078),
}
O = {  # the final syllable keeps its recorded pitch, level and reverb tail
    'falco': ('falco', 0.392, 0.8170),
    'mario': ('mario', 0.385, 1.2670),
}

IY_PITCH_SCOOP = [(0.0, 296), (0.07, 330), (0.16, 362), (0.3, 356), (0.55, 349), (0.8, 338), (1.0, 326)]

def make(**kw):
    segs, xfs = make_segs(**kw)
    y, joins, spans = build(segs, xfs[:len(segs) - 1])
    return finish(y), joins, spans, [s.label for s in segs]

def make_segs(j='jiggly', iy='pichu', n='ness', o='falco', xf=(0.010, 0.014, 0.012), iy_pitch=IY_PITCH,
         n_pitch=N_PITCH, t_iy=T_IY, t_n=T_N, o_start=None, no_trans=None, j_end=None, iy_span=None, n_span=None,
         jitter=True, o_segs=None, o_xf=None):
    """Segment list + crossfades. o_segs (list of Seg) replaces the single final-syllable segment; o_xf gives the
    crossfades between those extra segments."""
    segs = []
    js = J[j]
    if j_end is not None: js = Seg(js.src, js.t0, j_end, label=js.label)
    iy_src, a, b = IY[iy]
    if iy_span: a, b = iy_span
    g_iy = V_DB - rms_db(iy_src, a, b)
    js = Seg(js.src, js.t0, js.t1, gain_db=g_iy + rms_db(iy_src, a, b) - rms_db(js.src, js.t0, js.t1) + J_RATIO[j],
             label=js.label)
    segs.append(js)
    segs.append(Seg(iy_src, a, b, dur=t_iy, pitch=iy_pitch, gain_db=g_iy, floor=200, ceil=460, label=f'iy<{iy}',
                    keep_jitter=jitter))
    n_src, a2, b2 = N[n]
    if n_span: a2, b2 = n_span
    segs.append(Seg(n_src, a2, b2, dur=t_n, pitch=n_pitch, gain_db=N_DB - rms_db(n_src, a2, b2), floor=140, ceil=420,
                    label=f'n<{n}', keep_jitter=False))
    if no_trans:  # optional n->o transition from "No contest" (PSOLA'd down to the final-syllable pitch)
        a3, b3, f = no_trans
        segs.append(Seg('nocontest', a3, b3, pitch=[(0, f[0]), (1, f[1])],
                        gain_db=V_DB - rms_db('nocontest', a3, b3), floor=150, ceil=420, label='n>o<No',
                        keep_jitter=False))
    if o_segs is None:
        o_src, a4, b4 = O[o]
        if o_start is not None: a4 = o_start
        segs.append(Seg(o_src, a4, b4, gain_db=V_DB - rms_db(o_src, a4, min(b4, a4 + 0.15)), label=f'o<{o}'))
        xfs = list(xf) + [xf[-1]] * (len(segs) - 1 - len(xf))
    else:
        nhead = len(segs)
        segs += list(o_segs)
        xfs = list(xf)[:nhead] + [xf[-1]] * max(0, nhead - len(xf))
        xfs = xfs[:nhead] + list(o_xf or [])
        xfs += [xfs[-1]] * (len(segs) - 1 - len(xfs))
    return segs, xfs

CONFIGS = {
    # brief recipe (J Jigglypuff, iy Pichu, n Ness, o Falco) and its Peach twin
    'recipe_pichu': dict(j='jiggly', iy='pichu', n='ness', o='falco'),
    'recipe_peach': dict(j='jiggly', iy='peach', n='ness', o='falco'),
    # n from "Green team" (real vowel->nasal context)
    'greenN_pichu': dict(j='jiggly', iy='pichu', n='green', o='falco'),
    'greenN_peach': dict(j='jiggly', iy='peach', n='green', o='falco'),
    # iy AND n from "Green" (the join sits inside the vowel instead of at the nasal)
    'green_iyn': dict(j='jiggly', iy='green', n='green', o='falco'),
    # n + n->o transition from "No contest"
    'noN_pichu': dict(j='jiggly', iy='pichu', n='no', o='falco', no_trans=(0.078, 0.110, (230, 222)), o_start=0.405),
    'noN_peach': dict(j='jiggly', iy='peach', n='no', o='falco', no_trans=(0.078, 0.110, (230, 222)), o_start=0.405),
    # alternates
    # round 2: scooped vowel onset, shorter J, longer No transition, Falco 'o' after its /k/ transition
    'r2_pichu': dict(j='jiggly', j_end=0.074, iy='pichu', iy_pitch=IY_PITCH_SCOOP, n='no',
                     no_trans=(0.078, 0.125, (232, 222)), o_start=0.425),
    'r2_peach': dict(j='jiggly', j_end=0.074, iy='peach', iy_pitch=IY_PITCH_SCOOP, n='no',
                     no_trans=(0.078, 0.125, (232, 222)), o_start=0.425),
    'r2_ness_pichu': dict(j='jiggly', j_end=0.074, iy='pichu', iy_pitch=IY_PITCH_SCOOP, n='ness',
                          no_trans=(0.078, 0.125, (232, 222)), o_start=0.425),
    'r2_long_pichu': dict(j='jiggly', j_end=0.074, iy='pichu', iy_pitch=IY_PITCH_SCOOP, t_iy=0.195, n='no',
                          no_trans=(0.078, 0.125, (232, 222)), o_start=0.425),
    'r2_green_pichu': dict(j='jiggly', j_end=0.074, iy='pichu', iy_pitch=IY_PITCH_SCOOP, n='green',
                           no_trans=(0.078, 0.125, (232, 222)), o_start=0.425),
    # round 3: jitter-preserving PSOLA; crossfade and /n/ length variants
    'r3_pichu': dict(j='jiggly', j_end=0.074, iy='pichu', iy_pitch=IY_PITCH_SCOOP, n='no',
                     no_trans=(0.078, 0.125, (232, 222)), o_start=0.425, xf=(0.010, 0.014, 0.012, 0.024)),
    'r3_peach': dict(j='jiggly', j_end=0.074, iy='peach', iy_pitch=IY_PITCH_SCOOP, n='no',
                     no_trans=(0.078, 0.125, (232, 222)), o_start=0.425, xf=(0.010, 0.014, 0.012, 0.024)),
    'r3_pichu_n70': dict(j='jiggly', j_end=0.074, iy='pichu', iy_pitch=IY_PITCH_SCOOP, n='no', t_n=0.070,
                         no_trans=(0.078, 0.125, (232, 222)), o_start=0.425, xf=(0.010, 0.014, 0.012, 0.024)),
    'r3_pichu_xf36': dict(j='jiggly', j_end=0.074, iy='pichu', iy_pitch=IY_PITCH_SCOOP, n='no',
                          no_trans=(0.078, 0.135, (232, 222)), o_start=0.425, xf=(0.010, 0.014, 0.012, 0.036)),
    'r3_green_pichu': dict(j='jiggly', j_end=0.074, iy='pichu', iy_pitch=IY_PITCH_SCOOP, n='green',
                           no_trans=(0.078, 0.125, (232, 222)), o_start=0.425, xf=(0.010, 0.014, 0.012, 0.024)),
    'r3_green_peach': dict(j='jiggly', j_end=0.074, iy='peach', iy_pitch=IY_PITCH_SCOOP, n='green',
                           no_trans=(0.078, 0.125, (232, 222)), o_start=0.425, xf=(0.010, 0.014, 0.012, 0.024)),
    'r3_mario_pichu': dict(j='jiggly', j_end=0.074, iy='pichu', iy_pitch=IY_PITCH_SCOOP, n='no', o='mario',
                           no_trans=(0.078, 0.125, (250, 244)), o_start=0.40, xf=(0.010, 0.014, 0.012, 0.024)),
    # round 4: smooth pitch on /n/ and the n->o transition, 36 ms vowel-vowel crossfade into Falco's 'o'
    'r4_pichu': dict(j='jiggly', j_end=0.074, iy='pichu', iy_pitch=IY_PITCH_SCOOP, n='no', t_n=0.075,
                     no_trans=(0.078, 0.135, (232, 222)), o_start=0.425, xf=(0.010, 0.014, 0.012, 0.036)),
    'r4_peach': dict(j='jiggly', j_end=0.074, iy='peach', iy_pitch=IY_PITCH_SCOOP, n='no', t_n=0.075,
                     no_trans=(0.078, 0.135, (232, 222)), o_start=0.425, xf=(0.010, 0.014, 0.012, 0.036)),
    'r4_green_pichu': dict(j='jiggly', j_end=0.074, iy='pichu', iy_pitch=IY_PITCH_SCOOP, n='green', t_n=0.075,
                           no_trans=(0.078, 0.135, (232, 222)), o_start=0.425, xf=(0.010, 0.014, 0.012, 0.036)),
    'r4_greeniyn': dict(j='jiggly', j_end=0.074, iy='green', iy_pitch=IY_PITCH_SCOOP, n='green', t_n=0.075,
                        no_trans=(0.078, 0.135, (232, 222)), o_start=0.425, xf=(0.010, 0.006, 0.012, 0.036)),
    'r4_ness_pichu': dict(j='jiggly', j_end=0.074, iy='pichu', iy_pitch=IY_PITCH_SCOOP, n='ness', t_n=0.075,
                          no_trans=(0.078, 0.135, (232, 222)), o_start=0.425, xf=(0.010, 0.014, 0.012, 0.036)),
    'giantJ_pichu': dict(j='giant', iy='pichu', n='ness', o='falco'),
    'mario_o_pichu': dict(j='jiggly', iy='pichu', n='ness', o='mario'),
    'giga_iy': dict(j='jiggly', iy='giga', n='ness', o='falco'),
    'sheik_iy': dict(j='jiggly', iy='sheik', n='ness', o='falco'),
}

if __name__ == '__main__':
    out = os.path.join(HERE, 'cands'); os.makedirs(out, exist_ok=True)
    only = sys.argv[1:]
    meta = {}
    for name, cfg in CONFIGS.items():
        if only and name not in only: continue
        y, joins, spans, labels = make(**cfg)
        write(os.path.join(out, f'{name}.wav'), y)
        meta[name] = dict(cfg={k: v for k, v in cfg.items()}, joins=joins, spans=spans, labels=labels, dur=len(y) / SR)
        print(f'{name:16s} dur={len(y)/SR:.3f}s joins={[round(j,3) for j in joins]}')
    mp = os.path.join(out, 'meta.json')
    old = json.load(open(mp)) if os.path.exists(mp) else {}
    old.update(meta); json.dump(old, open(mp, 'w'), indent=1, default=str)
