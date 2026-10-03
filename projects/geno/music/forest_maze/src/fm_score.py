"""Forest Maze (Super Mario RPG, Yoko Shimomura, 1996): our transcription of one loop, 22 bars of 4/4.
Transcribed from the SNES recording by basic-pitch (full mix + demucs stems, both loops) and corrected by analysis.
Written pitch = sounding pitch. Grid: 16ths. Original tempo 94.6 BPM (quarter), i.e. ~189 BPM felt in 8ths.

Form (bars): A 1-4 (theme, low octave) | A' 5-8 (theme, octave up) | T 9-12 (transition, bass riff over a C# pedal)
             | B 13-16 (the theme transposed up a 4th, into F# minor) | C 17-20 (descending answer, i-VII-VI-V twice)
             | D 21-22 (F# major, turnaround to C#m)
"""
import re

NOTE = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'E#': 5, 'F#': 6, 'Gb': 6, 'G': 7,
        'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11, 'B#': 0}


def midi(n):
    m = re.fullmatch(r'([A-G][#b]?)(-?\d)', n)
    name, octv = m.group(1), int(m.group(2))
    return 12 * (octv + 1) + NOTE[name] + (12 if name == 'B#' else 0)


A1 = 'C#4:1 D#4:1 E4:1 F#4:1 G#4:2 C#5:2 B4:2 G#4:2 A#4:2 A#4:2'
A2 = 'B4:2 G#4:1 A#4:1 B4:2 A#4:1 F#4:1 D#4:2 E4:2 D#4:4'
A3 = 'C#4:1 D#4:1 E4:1 F#4:1 E4:2 D#4:1 E4:1 F#4:2 E4:1 D#4:1 C#4:4'
A4 = 'F#4:2 E4:1 D#4:1 C#4:2 D#4:1 E4:1 F#4:2 E4:1 F#4:1 G#4:4'


def up(bar, k=12):
    out = []
    for tok in bar.split():
        n, d = tok.split(':')
        if n == 'r':
            out.append(tok)
        else:
            m = midi(n) + k
            names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            out.append(f'{names[m % 12]}{m // 12 - 1}:{d}')
    return ' '.join(out)


MELODY = [
    A1, A2, A3, A4,                                                    # A   (1-4)
    up(A1), up(A2), up(A3), up(A4),                                    # A'  (5-8)
    'r:16', 'r:16', 'r:16', 'r:12 C#5:1 B4:1 A4:1 G#4:1',              # T   (9-12)
    'F#4:1 G#4:1 A4:1 B4:1 C#5:2 F#5:2 E5:2 C#5:2 D#5:2 D#5:2',        # B   (13-16)
    'E5:2 C#5:1 D#5:1 E5:2 D#5:1 B4:1 B4:2 A4:1 F#4:1 G#4:2 B4:2',
    'F#4:1 G#4:1 A4:1 B4:1 A4:2 G#4:1 A4:1 B4:2 A4:1 G#4:1 F#4:4',
    'B4:2 A4:1 G#4:1 F#4:2 G#4:1 A4:1 B4:2 A4:1 B4:1 C#5:4',
    '~C#5:6 F#5:2 A5:2 G#5:1 F#5:1 E5:2 C#5:2',                         # C   (17-20)  (~ = tied over the bar)
    'F#5:2 E5:1 D5:1 C#5:2 B4:2 A4:2 G#4:2 A4:2 B4:2',
    'C#5:2 C#5:2 C#5:2 F#5:2 A5:2 G#5:1 F#5:1 E5:2 C#5:2',
    'F#5:2 E5:1 D5:1 C#5:2 B4:2 A4:2 G#4:2 A4:2 B4:2',
    'A#4:4 C#5:12',                                                    # D   (21-22)
    'C#5:12 G#4:4',
]

BASS = [
    'C#2:2 G#2:2 C#2:2 G#2:2 C#2:2 G#2:2 F#2:2 C#3:2',
    'E2:2 B1:2 E2:2 B1:2 F#2:2 C#2:2 B1:2 F#2:2',
    'A1:2 r:2 A1:2 r:2 A1:2 r:2 A1:2 r:2',
    'B1:2 F#2:2 B1:2 F#2:2 B1:2 F#2:2 G#1:2 D#2:2',
] * 2 + [
    'C#2:3 C#2:1 C#3:2 C#2:2 C#2:3 C#2:1 C#3:2 C#2:2',
    'B1:3 B1:1 B2:2 B1:2 B1:3 B1:1 B2:2 B1:2',
    'C#2:3 C#2:1 C#3:2 C#2:2 C#2:3 C#2:1 C#3:2 C#2:2',
    ' '.join(['C#2:1 G#2:1 C#3:1 G#2:1'] * 4),
    'F#2:2 C#3:2 F#2:2 C#2:2 F#2:2 C#2:2 B1:2 F#2:2',
    'A1:2 E2:2 A1:2 E2:2 B1:2 F#2:2 E2:2 B2:2',
    'D2:2 A2:2 D2:2 A2:2 D2:2 A2:2 D2:2 A2:2',
    'E2:2 B2:2 E2:2 B2:2 E2:2 B2:2 C#2:2 G#2:2',
    'F#2:2 C#3:2 F#2:2 C#3:2 F#2:2 C#3:2 E2:2 C#3:2',
    'D2:2 A2:2 D2:2 A2:2 C#2:2 G#2:2 C#2:2 G#2:2',
    'F#2:2 C#3:2 F#2:2 C#3:2 F#2:2 C#3:2 E2:2 C#3:2',
    'D2:2 A2:2 D2:2 A2:2 C#2:2 G#2:2 C#2:2 G#2:2',
    'F#2:2 F#2:2 C#3:2 C#2:2 F#2:2 C#2:2 F#2:2 C#2:2',
    'F#2:2 F#2:2 C#3:2 F#2:2 F#2:2 F#2:1 A#2:1 G#2:2 D#3:2',
]

# the transition's 16th-note ostinato (bars 9-11), an inner voice around C3-C4 under the held chords
OSTINATO = ['r:16'] * 8 + [
    'G#3:1 C#4:1 G#3:1 C#4:1 G#3:1 C#4:1 G#3:1 C#4:1 G#3:1 B3:1 G#3:1 B3:1 F#3:1 A3:1 F#3:1 A3:1',
    'G#3:1 D3:1 G#3:1 D3:1 G#3:1 D3:1 G#3:1 D3:1 F#3:1 D3:1 F#3:1 D3:1 E3:1 D3:1 E3:1 D3:1',
    'D3:1 B2:1 D3:1 B2:1 D3:1 B2:1 D3:1 B2:1 D3:1 G#2:1 D3:1 G#2:1 D3:1 G#2:1 D3:1 G#2:1',
] + ['r:16'] * 11

# chord symbol @ 16th slot within the bar
CHORDS = [
    'C#m@0 F#@12', 'E@0 F#@8 B@12', 'A@0', 'B@0 G#m@12',
    'C#m@0 F#@12', 'E@0 F#@8 B@12', 'A@0', 'B@0 G#m@12',
    'C#@0 C#7@8', 'Bm6@0', 'C#7b9@0', 'C#7@0',
    'F#m@0 B@12', 'A@0 B@8 E@12', 'D@0', 'E@0 C#@12',
    'F#m@0 E@12', 'D@0 C#@8', 'F#m@0 E@12', 'D@0 C#@8',
    'F#@0', 'F#@0 G#m@12',
]
SECTIONS = [('A', 1, 4), ("A'", 5, 8), ('T', 9, 12), ('B', 13, 16), ('C', 17, 20), ('D', 21, 22)]

QUAL = {'': [0, 4, 7], 'm': [0, 3, 7], 'm7': [0, 3, 7, 10], 'm6': [0, 3, 7, 9], '7b9': [0, 4, 7, 10, 13], '5': [0, 7],
        '7': [0, 4, 7, 10], 'sus4': [0, 5, 7]}


def chord_pcs(sym):
    m = re.fullmatch(r'([A-G][#b]?)(.*)', sym)
    return NOTE[m.group(1)], QUAL[m.group(2)]


def notes(bars, bar0=0):
    """-> list of (start16, dur16, midi) over the bars; checks each bar sums to 16."""
    out = []
    for i, bar in enumerate(bars):
        t = (bar0 + i) * 16
        tot = 0
        for tok in bar.split():
            n, d = tok.split(':'); d = int(d)
            if n.startswith('~'):                       # tie: extend the previous note of this pitch
                p = midi(n[1:])
                k = max(i for i, x in enumerate(out) if x[2] == p)
                out[k] = (out[k][0], out[k][1] + d, p)
            elif n != 'r':
                out.append((t + tot, d, midi(n)))
            tot += d
        assert tot == 16, f'bar {bar0 + i + 1} sums to {tot}: {bar}'
    return out


def chords(bars=CHORDS, bar0=0):
    """-> list of (start16, dur16, root_pc, intervals)"""
    ev = []
    for i, bar in enumerate(bars):
        for tok in bar.split():
            s, at = tok.split('@')
            ev.append([(bar0 + i) * 16 + int(at), s])
    out = []
    for k, (t, s) in enumerate(ev):
        t1 = ev[k + 1][0] if k + 1 < len(ev) else (bar0 + len(bars)) * 16
        r, q = chord_pcs(s)
        out.append((t, t1 - t, r, q, s))
    return out


if __name__ == '__main__':
    print(len(notes(MELODY)), 'melody notes;', len(notes(BASS)), 'bass notes;', len(chords()), 'chords')
