""""Ge-no! Ge-no!" (JEE-no) for the crowd, spliced only from the crowd's own chants (survey.py decodes them).

The pieces (source seconds in the decoded 16 kHz chants; the crowd sings each name legato, so a syllable is 0.3-0.6 s):
  J   /dʒ/: Jigglypuff's chant-initial "J" (Pr 0.000-0.050; 'prl' keeps its /dʒ/->/ɪ/ release to 0.120), or the medial one
      in Luigi's "Lu-i-GI" (Lg 0.640-0.740, which runs straight on into its own "ee")
  EE  a stressed /iː/: Pichu's "PEE" (Pc 0.070-0.480, F2 ~2130 Hz), or Luigi's "gi" vowel (Lg 0.740-1.000, F2 ~2090)
  n   Ness's word-initial /n/ ("Ness! Ness!", Ns 0.775 and 1.555, 90 ms)
  o   Peach's "Go" vowel (Pe 0.100-0.500, "GO Peach!"), Mario's final "o" (Mr 0.860-, "Ma-ri-O!"), Falco's "-co" after
      its /k/ transition (Fc 0.970-)
The pitch: a crowd is mixed voices, but each chant has a common note. Jiggly's "J" (~250 Hz), Pichu's "PEE" (~245),
Ness's /n/ (~206) and Peach's "Go" (~201) share one register, so "GEE" falls about three semitones into "no" as in the
two-syllable chants. Mario's "o" (~249/414) is moved down 3 semitones to meet the /n/; Falco's (~139) is the low register
and is left as recorded (a bigger fall).
The rhythm: the two-syllable chants (Kirby, Bowser, Samus: "KIR-by! KIR-by!") run two cycles in 2.1-2.2 s, about 1.07 s
per cycle, the stressed syllable about 0.5 s. Each candidate is two such cycles: the first "no" cut off for the breath,
the second with a real chant's decay, and the file loudness-matched to the real chants.

    .venv/bin/python projects/geno/sound/cheer/candidates.py [NAME ...]    # the grid -> $CROWD_WORK/cands/*.wav + cands.json
"""
import json, os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crowdsplice as cs  # noqa: E402
from crowdsplice import Seg  # noqa: E402

CANDS = os.path.join(cs.WORK, 'cands')

# the real chants' loudness (survey + measure): every retail chant is peak-normalised to -3.0 dBFS, and their integrated
# loudness runs -12.7 to -15.7 LUFS, median -13.4
TARGET_LUFS = -13.4
PEAK_DBFS = -3.0
# syllable levels in the template (Kirby's "KIR" and "by", core RMS)
STRESS_DB, WEAK_DB = -11.7, -12.7


def lufs(y, sr=cs.SR):
    import pyloudnorm as pyln
    return pyln.Meter(sr).integrated_loudness(y)


def loudness_match(y):
    """Integrated loudness to the real chants' median, then capped at their -3 dBFS peak."""
    y = y * 10 ** ((TARGET_LUFS - lufs(y)) / 20)
    cap = 10 ** (PEAK_DBFS / 20)
    pk = np.abs(y).max()
    return y * cap / pk if pk > cap else y


def fade_edges(y, fin=0.004, fout=0.02):
    a, b = int(fin * cs.SR), int(fout * cs.SR)
    y = y.copy()
    y[:a] *= np.linspace(0, 1, a)
    y[len(y) - b:] *= np.cos(np.linspace(0, np.pi / 2, b)) ** 2
    return y


def piece(src, t0, t1, dur=None, semis=0.0, level=None, fade_out=0.0, layer=None, label=''):
    """A Seg gain-matched so its core RMS is `level` dB (the template syllable it plays)."""
    g = 0.0 if level is None else level - cs.span_db(src, t0, t1)
    return Seg(src, t0, t1, dur=dur, semis=semis, gain_db=g, fade_out=fade_out, layer=layer, label=label)


# a J is (src, t0, t1) or (src, t0, t1, layer): a layer mixes a second take over its start (see crowdsplice.Seg)
TCH = ('Pc', 0.505, 0.560)                  # Pichu's /tʃ/ ("Pi-CHU"): the crowd's strongest postalveolar frication
J = {'pr': ('Pr', 0.000, 0.050),            # Jigglypuff: the chant-initial /dʒ/
     'prl': ('Pr', 0.000, 0.120),           # the same with its release into /ɪ/
     'lg': ('Lg', 0.640, 0.740),            # Luigi: the medial /dʒ/ of "Lu-i-GI" (only with EE 'lg': one take)
     'pc': TCH,                             # Pichu's /tʃ/ alone, 55 ms (short frication reads as /dʒ/ word-initially)
     'pcs': ('Pc', 0.515, 0.560),           # the same, 45 ms (less of its start: shorter frication, less "ch")
     'pcl': ('Pc', 0.495, 0.570),           # the same, 75 ms
     'pcj': ('Pr', 0.000, 0.070, TCH + (-3.0, 0.0)),    # Jigglypuff's /dʒ/ with Pichu's /tʃ/ frication layered on
     'pcjl': ('Pr', 0.000, 0.120, TCH + (-3.0, 0.0))}   # the same with Jigglypuff's release into /ɪ/
EE = {'pc': ('Pc', 0.070, 0.480),           # Pichu "PEE"
      'lg': ('Lg', 0.740, 1.000)}           # Luigi "gi"
N = [('Ns', 0.775, 0.865), ('Ns', 1.555, 1.635)]   # Ness: the 2nd and 3rd "N-" (one per cycle)
# each "o": (the first cycle's "o", cut off for the breath; the last cycle's vowel; the decay that ends the file). A piece
# is (src, t0, t1, semis). The decay is time-scaled (WSOLA) so the file is exactly two cycles long and loops on the beat,
# as the retail chants do (the game replays the sample back to back).
O = {'pe': (('Pe', 0.100, 0.560, 0.0), ('Pe', 0.100, 0.350, 0.0), ('Mr', 1.100, 1.625, -3.0)),  # Peach's "Go"; Mario's decay
     'mr': (('Mr', 0.860, 1.300, -3.0), ('Mr', 0.860, 1.100, -3.0), ('Mr', 1.100, 1.625, -3.0)),  # Mario's "o" and decay
     'fc': (('Fc', 0.970, 1.410, 0.0), ('Fc', 0.970, 1.220, 0.0), ('Fc', 1.750, 1.985, 0.0))}     # Falco's "o" and decay
XF = dict(j_ee=0.016, ee_n=0.024, n_o=0.016, o_tail=0.040, o_j=0.030)
EE_DUR, O1_DUR = 0.46, 0.44


def head(j, ee, n):
    """J + EE at the stressed level, n at the weak level."""
    jj = J[j]
    return ([piece(*jj[:3], level=STRESS_DB, layer=jj[3] if len(jj) > 3 else None, label='J'),
             piece(*EE[ee], dur=EE_DUR, level=STRESS_DB, label='EE'),
             piece(*n, level=WEAK_DB, label='n')], [XF['j_ee'], XF['ee_n'], XF['n_o']])


def make(j, ee, o):
    """Two cycles "GEE-no! GEE-no!", each Jlen + 0.46 + 0.09 + 0.44 s (1.04-1.11 s; the retail two-syllable chants'
    cycle is about 1.07 s)."""
    o1, o2, tail = O[o]
    s1, x1 = head(j, ee, N[0])
    s1.append(piece(*o1[:3], dur=O1_DUR, semis=o1[3], level=WEAK_DB, fade_out=0.06, label='o'))
    jl, nl = J[j][2] - J[j][1], N[0][2] - N[0][1]
    c1 = jl + EE_DUR + nl + O1_DUR
    s2, x2 = head(j, ee, N[1])
    s2.append(piece(*o2[:3], semis=o2[3], level=WEAK_DB, label='o'))
    used = jl + EE_DUR + (N[1][2] - N[1][1]) + (o2[2] - o2[1])
    # the decay continues the vowel: its first 50 ms at the level of the vowel's last 50 ms (gain-matching a decay's mean
    # to a syllable level would lift its start above the vowel)
    edge = WEAK_DB + (cs.span_db(o2[0], o2[2] - 0.05, o2[2]) - cs.span_db(*o2[:3]))
    s2.append(piece(*tail[:3], dur=c1 - used, semis=tail[3], level=edge + (cs.span_db(*tail[:3]) - cs.span_db(tail[0], tail[1], tail[1] + 0.05)),
                    label='tail'))
    return s1 + s2, x1 + [XF['o_j']] + x2 + [XF['o_tail']]



RECIPES = {}
for _je in [('pr', 'pc'), ('prl', 'pc'), ('pr', 'lg'), ('prl', 'lg'), ('lg', 'lg'), ('pc', 'pc'), ('pc', 'lg'),
            ('pcj', 'pc'), ('pcj', 'lg'), ('pcjl', 'pc'), ('pcjl', 'lg'), ('pcs', 'pc'), ('pcl', 'pc')]:
    for _o in O:
        RECIPES[f'{_je[0]}_{_je[1]}_ns_{_o}'] = (lambda a, b, c: (lambda: make(a, b, c)))(*_je, _o)


def render(name):
    segs, xfs = RECIPES[name]()
    y, seams, spans = cs.build(segs, xfs)
    y = loudness_match(fade_edges(y))
    path = os.path.join(CANDS, name + '.wav')
    cs.write(path, y)
    return dict(name=name, path=path, sec=round(len(y) / cs.SR, 3), seams=[round(s, 3) for s in seams],
                spans=[(round(a, 3), round(b, 3)) for a, b in spans], lufs=round(lufs(y), 2),
                peak_dbfs=round(20 * np.log10(np.abs(y).max()), 2),
                segs=[dict(label=s.label, src=s.src, t0=s.t0, t1=s.t1, dur=s.dur, semis=s.semis, gain_db=round(s.gain_db, 2),
                           fade_out=s.fade_out, layer=s.layer) for s in segs], xf=xfs)


if __name__ == '__main__':
    names = [a for a in sys.argv[1:] if a in RECIPES] or list(RECIPES)
    p = os.path.join(CANDS, 'cands.json')
    meta = json.load(open(p)) if os.path.exists(p) else {}
    for n in names:
        meta[n] = render(n)
        print(f"{n:18s} {meta[n]['sec']:.2f} s  {meta[n]['lufs']:.1f} LUFS  peak {meta[n]['peak_dbfs']:.1f}  seams {meta[n]['seams']}")
    json.dump(meta, open(p, 'w'), indent=1)
