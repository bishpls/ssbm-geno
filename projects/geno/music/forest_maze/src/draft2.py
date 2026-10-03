"""Draft 2 of the Forest Maze metal arrangement: symphonic + electro colour, the dark breakdown replaced by GLADE.
38 OB at 200 BPM = 91.2 s to the final hit (frame 5472 at 60 fps), then a ~4.8 s ring-out.
  INTRO 4 | THEME A 4 | THEME A' 4 | TRANSITION 4 | B 4 | C 4 | D 2 | GLADE (electro) 2 | GLADE (build) 2 | SOLO 4 | FINAL (+2) 4 | hit"""
import sys
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
import arrange as A
from draft import seq, H, PICKUP

# the solo, kept inside a real guitar's range (<= E6, 24 frets)
SOLO = seq(
    'C#5:2 D#5:2 E5:2 F#5:2 G#5^:8 C#6:4 B5:2 G#5:2 A#5:4 A#5:4 '                       # C#m | F#: the opening run, sung
    'B5:2 G#5:1 A#5:1 B5:2 A#5:1 F#5:1 D#5:4 E5:4 F#5:2 A#5:2 C#6:4 D#6^:8 '             # E F# | B: bar 2 doubled, up to a bend
    'C#6:1 B5:1 A5:1 G#5:1 A5:1 B5:1 C#6:1 E6:1 C#6:1 B5:1 A5:1 G#5:1 A5:1 B5:1 C#6:1 E6:1 '   # A lydian turn
    'E5:1 A5:1 C#6:1 E6:1 C#6:1 A5:1 E5:1 C#5:1 D#6:2 E6:6 '
    'E6:1 D#6:1 B5:1 A#5:1 E6:1 D#6:1 B5:1 A#5:1 D#6:1 C#6:1 A#5:1 F#5:1 D#6:1 C#6:1 A#5:1 F#5:1 '   # B: descending fours
    'C#6:1 B5:1 G#5:1 F#5:1 B5:4 E6:1 D#6:1 C#6:1 B5:1 A#5:1 G#5:1 F#5:1 E5:1')           # G#m: scale run down into D#5


def _solo_harm():
    chs = A.src_chords(1, 4); out = []
    for (t, d, p, v, f) in SOLO:
        in_turn = 2 * A.OB <= t < 2 * A.OB + 16 * H
        in_run = t >= 3 * A.OB + 24 * H
        if not (in_turn or in_run): continue
        st = int(round(t / A.STEP)) % 64
        r, ivs, sym, ct = A.chord_at(chs, st)
        out.append((t, d, (p - 12) if in_turn else A.harm_note(p, sym, below=True), v * 0.85, f))
    return out


SOLO2 = _solo_harm()
OB = A.OB

PICKUP_B = [(t - 2 * OB, dur, p, v, f) for (t, dur, p, v, f) in PICKUP]

SECTIONS = [
    # INTRO A: the hook first, on music box + glockenspiel, over a light half-time groove (no double kick)
    dict(name='INTRO', src=(1, 2), lead=None, riff='bounce', drums='half16', crash=True, boom=True,
         layers=[('bell_melody', dict(octave=1)), ('glock_melody', dict(octave=2)), ('brass_stabs', dict(win=(0, 0.1)))],
         timp_hits=[(0.0, None)], bus_gain={'guitars': -4.0, 'drums': -2.0}),
    # INTRO B: the build: arp + strings swell, double kick enters, guitar pickup run into the theme
    dict(name='INTRO (build)', src=(3, 4), lead=None, riff='bounce', drums='half16', crash=False, extra_lead=PICKUP_B,
         layers=[('arp', dict(vel=0.7)), ('strings_pad', dict(vel=0.6)), ('bell_melody', dict(octave=1, bars=(3, 3), vel=0.5))],
         bus_gain={'synth': 2.0, 'orch': 3.0}),
    dict(name='THEME A', src=(1, 4), lead='mel', lead_oct=1, riff='chug', drums='skank8', riser=True,
         layers=[('strings_pad', dict(vel=0.45, low=False))]),
    dict(name="THEME A'", src=(5, 8), lead='harm', harm_below=True, riff='chug', drums='skank16', fill=True,
         layers=[('strings_pad', dict(vel=0.55)), ('glock_melody', dict(octave=1, vel=0.45, long_only=True))]),
    dict(name='TRANSITION', src=(9, 12), lead='mel', riff='trem', drums='trem', fill=True, riser=True,
         layers=['arp_ostinato', ('strings_trem', dict(vel=0.55))], bus_gain={'synth': 2.0}),
    dict(name='B', src=(13, 16), lead='harm', riff='open', drums='half16',
         layers=[('strings_pad', dict(vel=0.55)), ('choir', dict(vel=0.5)), ('glock_melody', dict(octave=1, vel=0.4, long_only=True))],
         timp_hits=[(0.0, 6)]),
    dict(name='C', src=(17, 20), lead='mel', riff='gallop', drums='skank8',
         layers=[('strings_spic', dict(vel=0.55)), ('glock_melody', dict(octave=1, vel=0.45))]),
    dict(name='D', src=(21, 22), lead='mel', riff='open', drums='halfride', fill=True, riser=True,
         layers=[('choir', dict(vel=0.55)), ('strings_trem', dict(vel=0.6))],
         timp_rolls=[(4.2, 0.6, 1)]),
    # GLADE: the forest clearing, symphonic metal: heavy half-time with double kick, guitars ring open power chords over the
    # original's bouncy bass line; the theme sung by the strings with choir and glockenspiel; a pumping pad and a high
    # arp shimmer underneath (the electro colour)
    dict(name='GLADE', src=(1, 2), lead=None, riff='open', drums='half16', crash=True, boom=True, pump=True, riser=True,
         layers=[('strings_melody', dict(inst='vln_mel', octave=1, vel=0.9, split_short=True)), ('glock_melody', dict(octave=2, vel=0.5)),
                 ('choir', dict(vel=0.6)), ('pad', dict(vel=0.5)), ('arp', dict(vel=0.55, lo=73))],
         bus_gain={'orch': 5.0, 'guitars': -2.0}),
    dict(name='GLADE (build)', src=(3, 4), lead=None, riff='chug', drums='skank16', fill=True, riser=False, pump=False,
         layers=[('strings_melody', dict(inst='vln_mel', octave=1, vel=0.95, split_short=True)), ('glock_melody', dict(octave=2, vel=0.5)),
                 ('choir', dict(vel=0.6)), ('arp', dict(vel=0.55, lo=73))],
         bus_gain={'orch': 5.0, 'guitars': -1.0}, timp_rolls=[(4.2, 0.6, 1)]),
    dict(name='SOLO', src=(1, 4), lead=None, riff='chug', drums='skank16', extra_lead=SOLO, extra_lead2=SOLO2,
         layers=[('strings_pad', dict(vel=0.4, low=False))]),
    dict(name='FINAL', src=(5, 8), lead='harm', harm_below=True, key=2, riff='chug', drums='crashride16', fill=True, riser=True,
         layers=[('strings_melody', dict(inst='vln_mel', octave=0, vel=0.7)), ('choir', dict(vel=0.5)),
                 ('glock_melody', dict(octave=1, vel=0.5))],
         timp_hits=[(0.0, None)]),
]
FINAL_HIT = ([39, 46, 51], 27, 75)     # D#5 power chord, D#1 bass, D#5 lead; orchestra on D# major
