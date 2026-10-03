"""Draft 1 of the Forest Maze metal arrangement: 36 OB at 200 BPM (86.4 s) + the final hit's ring.
Sections (OB = one bar of the original = 2.4 s):
  INTRO 4 | THEME A 4 | THEME A' 4 | TRANS 4 | B 4 | C 4 | D 2 | BREAKDOWN 2 | SOLO 4 | FINAL (A' +2 semitones) 4 | hit"""
import sys
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
import arrange as A

H = A.STEP / 2     # our 16th (0.075 s)


def seq(tokens, unit=H):
    """'C#5:2 D#5:1 ...' in 16ths -> [(t, dur, midi, vel, flags)] relative"""
    out, t = [], 0.0
    for tok in tokens.split():
        n, d = tok.split(':'); d = float(d)
        fl = {}
        if n.endswith('^'): n = n[:-1]; fl['bend'] = 2          # whole-step bend up into the note
        if n != 'r':
            out.append((t * unit, d * unit * 0.97, A.S.midi(n), 1.0, fl))
        t += d
    return out


SOLO = seq(
    # OB1  C#m: the theme's opening run, slowed and sung, a bend into G#, then the answer | F#: the repeated A#
    'C#5:2 D#5:2 E5:2 F#5:2 G#5^:8 C#6:4 B5:2 G#5:2 A#5:4 A#5:4 '
    # OB2  E: the theme's second bar, doubled in speed | F#: arpeggio up | B: bend into D#
    'B5:2 G#5:1 A#5:1 B5:2 A#5:1 F#5:1 D#5:4 E5:4 F#5:2 A#5:2 C#6:2 F#6:2 D#6^:8 '
    # OB3  A (lydian): a turning 16th figure twice, a sweep, then E6 held
    'C#6:1 B5:1 A5:1 G#5:1 A5:1 B5:1 C#6:1 E6:1 C#6:1 B5:1 A5:1 G#5:1 A5:1 B5:1 C#6:1 E6:1 '
    'A5:1 C#6:1 E6:1 A6:1 E6:1 C#6:1 A5:1 E5:1 D#6:2 E6:6 '
    # OB4  B: descending fours | G#m: the run up into the key change
    'F#6:1 E6:1 D#6:1 B5:1 F#6:1 E6:1 D#6:1 B5:1 F#6:1 E6:1 D#6:1 B5:1 E6:1 D#6:1 C#6:1 A#5:1 E6:1 D#6:1 C#6:1 A#5:1 B5:4 '
    'G#5:1 A#5:1 B5:1 C#6:1 D#6:1 E6:1 F#6:1 G#6:1')


def _solo_harm():
    """twin lead a third below, chord-aware, for OB3 and the final climb"""
    chs = A.src_chords(1, 4)
    out = []
    for (t, d, p, v, f) in SOLO:
        if t < 2 * A.OB or (2 * A.OB + 24 * H <= t < 3 * A.OB + 24 * H):
            continue
        st = int(round(t / A.STEP)) % 64
        r, ivs, sym, ct = A.chord_at(chs, st)
        out.append((t, d, (p - 12) if t < 3 * A.OB else A.harm_note(p, sym, below=True), v * 0.85, f))
    return out


SOLO2 = _solo_harm()

# breakdown: (half-step, root pc or None, length in half-steps, mute)
C_, D_ = 1, 2
BD_PAT = [(0, C_, 3, 0.0), (3, C_, 1, 0.9), (6, C_, 1, 0.9), (8, D_, 3, 0.0), (12, C_, 1, 0.9), (14, C_, 1, 0.9),
          (16, C_, 3, 0.0), (19, C_, 1, 0.9), (22, C_, 1, 0.9), (24, D_, 4, 0.0), (28, C_, 1, 0.9), (30, C_, 1, 0.9)]
BD_PAT2 = BD_PAT[:9] + [(24, D_, 2, 0.0), (26, C_, 2, 0.0)]
def _ring(pat):   # open hits ring until the next hit
    out = []
    for i, (h, pc, ln, mu) in enumerate(pat):
        nxt = pat[i + 1][0] if i + 1 < len(pat) else 32
        out.append((h, pc, (nxt - h) if mu < 0.5 else ln, mu))
    return out
BD_PAT, BD_PAT2 = _ring(BD_PAT), _ring(BD_PAT2)
BD_HITS = [(h / 2, pc, ln / 2, mu) for (h, pc, ln, mu) in BD_PAT] + [((32 + h) / 2, pc, ln / 2, mu) for (h, pc, ln, mu) in BD_PAT2]
BD_DRUMS = []
for (st, pc, ln, mu) in BD_HITS:
    BD_DRUMS.append((st * A.STEP, 'kick', 1.0 if mu < 0.5 else 0.85))
    if mu < 0.5: BD_DRUMS.append((st * A.STEP, 'china', 0.85))
for ob in range(2):
    for s in (4, 12):
        BD_DRUMS.append(((ob * 16 + s) * A.STEP, 'snare', 1.0))
    for b in range(8):
        BD_DRUMS.append(((ob * 16 + 2 * b) * A.STEP, 'bell', 0.75 if b % 2 == 0 else 0.6))
# a fill in the last beat of the breakdown into the solo
for q, p in enumerate(['snare', 'tom1', 'tom2', 'ftom']):
    BD_DRUMS.append(((30 + q * 0.5) * A.STEP, p, 0.9))

# intro: lead pickup run into the theme (the theme's own opening run, twin in thirds)
PICKUP = [(3 * A.OB + 12 * A.STEP + i * A.STEP * 0.5, A.STEP * 0.48, p, 0.95, {}) for i, p in enumerate([61, 63, 64, 66, 68, 70, 71, 73])]

SECTIONS = [
    dict(name='INTRO', src=(1, 4), lead=None, riff='bounce', drums='half16', crash=True, fill=False, extra_lead=PICKUP, boom=True),
    dict(name='THEME A', src=(1, 4), lead='mel', lead_oct=1, riff='chug', drums='skank8', scale='C#dor'),
    dict(name="THEME A'", src=(5, 8), lead='harm', riff='chug', drums='skank16', scale='C#dor', fill=True),
    dict(name='TRANSITION', src=(9, 12), lead='mel', riff='trem', drums='trem', fill=True),
    dict(name='B', src=(13, 16), lead='harm', scale='F#dor', riff='open', drums='half16'),
    dict(name='C', src=(17, 20), lead='mel', riff='gallop', drums='skank8', fill=False),
    dict(name='D', src=(21, 22), lead='mel', riff='open', drums='halfride', fill=True),
    dict(name='BREAKDOWN', src=(11, 12), lead=None, riff='stop', hits=BD_HITS, drums='none', crash=True, extra_drums=BD_DRUMS,
         riser=True, boom=True),
    dict(name='SOLO', src=(1, 4), lead=None, riff='chug', drums='skank16', extra_lead=SOLO, extra_lead2=SOLO2, fill=False),
    dict(name='FINAL', src=(5, 8), lead='harm', key=2, riff='chug', drums='crashride16', scale='C#dor', fill=True, pads=True,
         riser=True),
]
# final hit: D#5 (key +2 of C#), lead on D#6
FINAL_HIT = ([39, 46, 51], 27, 75)
