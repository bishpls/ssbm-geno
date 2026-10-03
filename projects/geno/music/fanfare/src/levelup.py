"""Geno's victory fanfare: our own orchestral arrangement of Super Mario RPG's post-battle "Victory" / level-up music
(ROM track 9, Yoko Shimomura, 1996), transcribed exactly from the cartridge's sequence data (smrpg_seq.py, checked
note for note against the game's own sound driver in drvplay.py).

Form (D major, the original tempo: the driver's D1=66 gives a 16th of 12 ticks x 66/8000 s = 0.099 s, 151.5 BPM):
  bar 0  INTRO   the original's fanfare bar: the descending run A5..D5 with the thirds below, D5 on beat 3,
                 a tutti hit on D on beat 4 (the original's orchestra-hit sample), snare pickup
  bar 1  THEME   loop bar 1 (D): the bouncing melody in trumpets, horns an octave below (the original register)
  bar 2  THEME   loop bar 2 (Em)
  bar 3  RUN     loop bar 4 (A): the brass lands on A, the flutes' rising scale run (C#5..E6) with its harmony,
                 timpani roll and a suspended-cymbal swell into
  bar 4  FINAL   a D major tutti with a glockenspiel star-sparkle arpeggio, held, then released into the hall
(loop bar 3 repeats bar 1, so the fanfare goes I - ii - V - I without it.)

Every part is note data: {instrument: [(t_s, dur_s, midi, vel 0..1)]}; percussion as (t_s, name, vel).
"""
import numpy as np

T16 = 12 * 66 / 8000.0           # 0.099 s: the ROM tempo exactly
BAR = 16 * T16
N = {n: i for i, n in enumerate('C C# D D# E F F# G G# A A# B'.split())}


def m(name):
    """'A5' -> 81"""
    p, o = name[:-1], int(name[-1])
    return 12 * (o + 1) + N[p]


def seq(out, inst, bar, items, vel=0.8, gate=0.9, octave=0):
    """items: (pos16, name, len16[, vel]) within a bar"""
    for it in items:
        pos, name, ln = it[:3]
        v = it[3] if len(it) > 3 else vel
        out.setdefault(inst, []).append(((bar * 16 + pos) * T16, ln * T16 * gate, m(name) + 12 * octave, v))


def chord(out, inst, t16, names, ln16, vel, gate=1.0):
    for nm in names:
        out.setdefault(inst, []).append((t16 * T16, ln16 * T16 * gate, m(nm), vel))


# ------------------------------------------------------------------ the transcription (sounding pitch, ROM track 9)
# intro bar: ch0 flute run; ch3/ch4 xylophone thirds; ch1 synth bass; ch3/ch4 orchestra hit on beat 4
RUN0 = [(0, 'A5', 1), (1, 'D6', 1), (2, 'C#6', 1), (3, 'B5', 1), (4, 'A5', 1), (5, 'G5', 1), (6, 'F#5', 1), (7, 'E5', 1),
        (8, 'D5', 4)]
THIRD_HI = [(0, 'F#4', 1), (1, 'A4', 1), (2, 'A4', 1), (3, 'G4', 1), (4, 'F#4', 1), (5, 'E4', 1), (6, 'D4', 1),
            (7, 'A3', 1), (8, 'A3', 4)]
THIRD_LO = [(0, 'D4', 1), (1, 'F#4', 1), (2, 'F#4', 1), (3, 'E4', 1), (4, 'D4', 1), (5, 'A3', 1), (6, 'A3', 1),
            (7, 'G3', 1), (8, 'F#3', 4)]
BASS0 = [(0, 'D2', 2), (6, 'A2', 2), (8, 'D3', 1), (12, 'D2', 4)]
# loop bars (trumpet 1 melody and trumpet 2 harmony: ch0 / ch5, sounding A3..D4 / F#3..A3)
MEL = {1: [(0, 'A3', 1), (1, 'B3', 1), (3, 'A3', 1), (4, 'B3', 1), (6, 'A3', 1), (8, 'D4', 2), (10, 'C#4', 1),
           (12, 'B3', 1), (14, 'A3', 1)],
       2: [(0, 'G3', 1), (1, 'A3', 1), (3, 'G3', 1), (4, 'A3', 1), (6, 'G3', 1), (8, 'E3', 2), (10, 'F#3', 1),
           (12, 'G3', 1), (14, 'B3', 1)]}
HAR = {1: [(0, 'F#3', 1), (1, 'G3', 1), (3, 'F#3', 1), (4, 'G3', 1), (6, 'F#3', 1), (8, 'A3', 2), (10, 'A3', 1),
           (12, 'G3', 1), (14, 'F#3', 1)],
       2: [(0, 'E3', 1), (1, 'F#3', 1), (3, 'E3', 1), (4, 'F#3', 1), (6, 'E3', 1), (8, 'C#3', 2), (10, 'D3', 1),
           (12, 'E3', 1), (14, 'G3', 1)]}
# ch3/ch4 xylophone offbeat pairs (16ths 2,3 of every beat) per bar: (upper, lower)
OFF = {1: ('A4', 'F#4'), 2: ('B4', 'G4'), 3: ('C#5', 'A4')}
# ch1 synth bass: dotted 8th, 16th, 16th, (rest), long, 16th, 16th, 8th
def bass_bar(root, fifth):
    return [(0, root, 3), (3, fifth, 1), (4, fifth, 1), (6, root, 5), (11, root, 1), (12, fifth, 1), (14, root, 2)]
BASS = {1: bass_bar('D2', 'A2'), 2: bass_bar('E2', 'B2'), 3: bass_bar('A1', 'E2')}
# loop bar 4: ch0 lands on C#3 then the flute run; ch5 lands on A2 then its flute harmony
RUN1 = [(2, 'C#5', 1), (3, 'D5', 1), (4, 'E5', 1), (5, 'F#5', 1), (6, 'G5', 1), (7, 'A5', 1), (8, 'B5', 1), (9, 'A5', 1),
        (10, 'B5', 1), (11, 'C#6', 1), (12, 'D6', 1), (13, 'C#6', 1), (14, 'D6', 1), (15, 'E6', 1)]
RUN2 = [(7, 'F#5', 1), (8, 'G5', 1), (9, 'F#5', 1), (10, 'G5', 1), (11, 'A5', 1), (12, 'B5', 1), (13, 'A5', 1),
        (14, 'B5', 1), (15, 'C#6', 1)]
# ch2 drums: bass drum (BD) / snare (SN) per bar; ch6/ch7 hi-hat + tambourine
DRUMS = {1: [(0, 'BD'), (4, 'SN'), (6, 'BD'), (10, 'BD'), (11, 'BD'), (12, 'SN')],
         2: [(0, 'BD'), (4, 'SN'), (6, 'BD'), (10, 'BD'), (11, 'BD'), (12, 'SN'), (14, 'SN'), (15, 'SN')],
         3: [(0, 'BD'), (4, 'SN'), (6, 'BD'), (10, 'BD'), (11, 'BD'), (12, 'SN'), (14, 'BD'), (15, 'SN')]}
TAMB = [0, 2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15]


def arrangement(final_hold16=12, seed=7, form='short'):
    """-> (notes {inst: [...]}, perc [(t, name, vel)], meta). form 'short': intro, loop bars 1-2, the V bar, the final
    chord (I ii V I); 'full': intro, loop bars 1-3 (bar 3 repeats bar 1), the V bar, the final chord."""
    o = {}
    P = []
    # ---------------- bar 0: intro fanfare
    seq(o, 'fl_stac', 0, RUN0[:8], 0.85, 0.75)
    seq(o, 'fl_sus', 0, RUN0[8:], 0.8, 0.95)
    seq(o, 'vln1_spic', 0, RUN0[:8], 0.8, 0.75)
    seq(o, 'vln1_spic', 0, RUN0[8:], 0.85, 0.6)
    # VSCO's glockenspiel and xylophone sound an octave above the key (like the real instruments sound above
    # written; measured), so keys here are one octave below the sounding pitch wanted.
    seq(o, 'glock', 0, RUN0, 0.62, 1.0)                       # sounds A6..D7: the sparkle an octave over the flutes
    seq(o, 'xylo', 0, THIRD_HI, 0.62, 1.0)                    # the original's xylophone thirds, sounding an octave up
    seq(o, 'xylo', 0, [x if m(x[1]) >= m('G3') else (x[0], x[1][:-1] + str(int(x[1][-1]) + 1), x[2]) for x in THIRD_LO],
        0.55, 1.0)                                            # (F#3 is below the patch: that one note an octave up)
    seq(o, 'vln2_spic', 0, THIRD_HI, 0.7, 0.9)
    seq(o, 'vla_spic', 0, THIRD_LO, 0.7, 0.9)
    seq(o, 'cl', 0, THIRD_HI[8:], 0.6, 0.95)
    seq(o, 'vc_spic', 0, BASS0[:3], 0.8, 0.85)
    seq(o, 'cb_pizz', 0, BASS0[:3], 0.8, 1.0)
    # the tutti hit on beat 4 (the SNES orchestra hit on D)
    hit = 12
    chord(o, 'tpt_stac', hit, ['D5', 'A4'], 3, 0.95)
    chord(o, 'hn_stac', hit, ['F#4', 'D4', 'A3'], 3, 0.9)
    chord(o, 'tbn_stac', hit, ['A3', 'D3'], 3, 0.9)
    chord(o, 'tuba_stac', hit, ['D2'], 3, 0.9)
    chord(o, 'vln1_spic', hit, ['D5', 'A5'], 2, 0.9)
    chord(o, 'vla_spic', hit, ['F#4', 'D4'], 2, 0.85)
    chord(o, 'vc_spic', hit, ['D3'], 2, 0.9)
    chord(o, 'cb_pizz', hit, ['D2'], 2, 0.95)
    chord(o, 'timp', hit, ['D2'], 4, 0.95)
    P += [(hit * T16, 'crash', 0.75), (hit * T16, 'BD', 0.95)]
    # timpani roll on the dominant under the run, crescendo into the hit; snare pickup (the original's 32nds)
    o.setdefault('timp_roll', []).append((0.0, 11.5 * T16, m('A2'), 0.55))
    for k in range(22):                                          # snare roll in 32nds, pp -> mf (the original drum roll)
        P.append((k * T16 / 2, 'SN_roll', 0.18 + 0.5 * k / 21))
    P += [(15 * T16, 'SN', 0.7), (15.5 * T16, 'SN', 0.8)]
    # ---------------- the theme (loop bars 1-2, or 1-3 in the full form: bar 3 repeats bar 1)
    theme = [(1, 1), (2, 2)] + ([(3, 1)] if form == 'full' else [])
    VB = theme[-1][0] + 1               # the V bar
    FB = VB + 1                         # the final bar
    for b, src in theme:
        seq(o, 'tpt_stac', b, MEL[src], 0.88, 0.85, octave=1)    # trumpets sing it an octave up
        seq(o, 'tpt2_stac', b, HAR[src], 0.8, 0.85, octave=1)
        seq(o, 'hn_stac', b, MEL[src], 0.8, 0.9)                 # horns in the original register
        seq(o, 'hn_stac', b, HAR[src], 0.72, 0.9)
        up, lo = OFF[src]
        for beat in range(4):
            for k in (2, 3):
                pos = beat * 4 + k
                seq(o, 'xylo', b, [(pos, up, 1)], 0.5, 1.0)
                seq(o, 'xylo', b, [(pos, lo, 1)], 0.45, 1.0)
                seq(o, 'vln2_spic', b, [(pos, up, 1)], 0.58, 0.7)
                seq(o, 'vla_spic', b, [(pos, lo, 1)], 0.58, 0.7)
        for (pos, nm, ln) in BASS[src]:
            inst_c = 'vc_sus' if ln >= 5 else 'vc_spic'
            seq(o, inst_c, b, [(pos, nm, ln)], 0.8, 0.9)
            seq(o, 'cb_pizz', b, [(pos, nm, ln)], 0.85, 1.0)
        for (pos, d) in DRUMS[src]:                               # loop bar 3's drums are bar 1's
            P.append(((b * 16 + pos) * T16, d, 0.85 if d == 'BD' else 0.62))
        for pos in TAMB:
            P.append(((b * 16 + pos) * T16, 'tamb', 0.55 if pos % 4 == 0 else 0.4))
    # ---------------- the V bar and the run (loop bar 4)
    b = VB
    # the brass lands on A (an 8th, as the original's trumpets do) and leaves the run exposed; horns and trombones
    # hold the dominant softly underneath, the timpani roll and the cymbal swell carry the build
    seq(o, 'tpt_stac', b, [(0, 'C#5', 2)], 0.85, 0.9)
    seq(o, 'tpt2_stac', b, [(0, 'A4', 2)], 0.8, 0.9)
    chord(o, 'hn_stac', b * 16, ['E4', 'C#4'], 2, 0.8, 0.9)
    chord(o, 'hn_sus', b * 16 + 4, ['E4', 'C#4', 'A3'], 12, 0.5, 0.97)
    chord(o, 'tbn_sus', b * 16 + 8, ['G3', 'E3'], 8, 0.5, 0.97)      # A7 colour enters on beat 3
    chord(o, 'tuba_sus', b * 16, ['A1'], 16, 0.55, 0.97)
    seq(o, 'fl_stac', b, RUN1, 0.85, 0.75)
    seq(o, 'vln1_spic', b, RUN1, 0.82, 0.75)
    seq(o, 'glock', b, RUN1[::2], 0.55, 1.0)                    # the star sparkle rides the run in 8ths
    seq(o, 'fl2_stac', b, RUN2, 0.75, 0.75)
    seq(o, 'ob', b, RUN2, 0.55, 0.9)
    up, lo = OFF[3]
    for beat in range(4):
        for k in (2, 3):
            seq(o, 'xylo', b, [(beat * 4 + k, up, 1)], 0.42, 1.0)
            seq(o, 'xylo', b, [(beat * 4 + k, lo, 1)], 0.38, 1.0)
    for (pos, nm, ln) in BASS[3]:
        seq(o, 'vc_spic', b, [(pos, nm, min(ln, 3))], 0.8, 0.85, octave=1 if m(nm) < m('C2') else 0)   # cello range
        seq(o, 'cb_pizz', b, [(pos, nm, ln)], 0.85, 1.0)
    o.setdefault('timp_roll', []).append(((b * 16 + 8) * T16, 8 * T16, m('A2'), 0.7))
    for (pos, d) in DRUMS[3]:
        P.append(((b * 16 + pos) * T16, d, 0.85 if d == 'BD' else 0.65))
    for pos in TAMB:
        P.append(((b * 16 + pos) * T16, 'tamb', 0.5 if pos % 4 == 0 else 0.38))
    P.append(((FB * 16) * T16, 'sus_swell_end', 0.8))               # the swell peaks on the final downbeat
    # ---------------- the final chord
    f = FB * 16
    H = final_hold16
    chord(o, 'tpt_sus', f, ['F#5'], H, 0.9)
    chord(o, 'tpt2_sus', f, ['D5'], H, 0.88)
    chord(o, 'hn_sus', f, ['A4', 'F#4', 'D4'], H, 0.85)
    chord(o, 'tbn_sus', f, ['A3', 'D3'], H, 0.85)
    chord(o, 'tuba_sus', f, ['D2'], H, 0.85)
    chord(o, 'fl_sus', f, ['F#6', 'D6'], H, 0.8)
    chord(o, 'ob', f, ['A5'], H, 0.7)
    chord(o, 'cl', f, ['F#5'], H, 0.7)
    chord(o, 'vln1_sus', f, ['D6', 'A5'], H, 0.85)
    chord(o, 'vln_trem', f, ['F#5', 'D5'], H, 0.75)
    chord(o, 'vla_sus', f, ['A4', 'F#4'], H, 0.8)
    chord(o, 'vc_sus', f, ['D3', 'A2'], H, 0.85)
    chord(o, 'cb_sus', f, ['D2'], H, 0.85)
    chord(o, 'tpt_stac', f, ['F#5'], 2, 0.95)                       # accent layers on the downbeat
    chord(o, 'tpt2_stac', f, ['D5'], 2, 0.92)
    chord(o, 'vln1_spic', f, ['D6', 'A5'], 2, 0.95)
    chord(o, 'cb_pizz', f, ['D2'], 2, 1.0)
    chord(o, 'timp', f, ['D2'], 2, 1.0)
    o.setdefault('timp_roll', []).append(((f + 2) * T16, (H - 2) * T16, m('D2'), 0.62))
    # glockenspiel star sparkle: A5 D6 F#6 A6 (sounding) in 16ths, then the top rings
    seq(o, 'glock', FB, [(0, 'A4', 4), (1, 'D5', 4), (2, 'F#5', 4), (3, 'A5', 8)], 0.7, 1.0)   # sounds A5 D6 F#6 A6
    chord(o, 'harp', f, ['D3', 'A3', 'D4', 'F#4', 'A4', 'D5'], 8, 0.7)
    P += [(f * T16, 'crash', 1.0), (f * T16, 'BD', 1.0), ((f + 1) * T16, 'triangle', 0.6)]
    # humanize: small timing and velocity jitter (fixed seed), never on the downbeat hits
    rng = np.random.default_rng(seed)
    for inst, ns in o.items():
        jt = 0.004 if inst.endswith(('_stac', '_spic', 'pizz')) else 0.006
        o[inst] = [(max(0.0, t + (rng.normal(0, jt) if t > 0 else 0)), d, p, float(np.clip(v * rng.normal(1, 0.04), 0.05, 1)))
                   for (t, d, p, v) in ns]
    meta = dict(T16=T16, bar=BAR, form=form, final_t=f * T16, release_t=(f + H) * T16, bpm=60 / (4 * T16))
    return o, P, meta


if __name__ == '__main__':
    o, P, meta = arrangement()
    print(meta)
    for k, v in sorted(o.items()):
        print('%-10s %3d notes  range %s..%s' % (k, len(v), min(x[2] for x in v), max(x[2] for x in v)))
