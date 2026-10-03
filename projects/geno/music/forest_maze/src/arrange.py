"""The metal arrangement of Forest Maze as data + part generators.

Clock: 200 BPM in 4/4 (one beat = 0.3 s = 18 frames at 60 fps). One bar of the original (16 sixteenths at 94.6 BPM)
becomes two bars here: the original 16th is our 8th (0.15 s). Positions below are in original-bar units ("OB",
2.4 s) and steps of 0.15 s (16 per OB); drums also use half-steps (our 16ths, 0.075 s).

A section spec:
  {name, src:(b0,b1) bars of the transcription, ob: length in OB, key: semitones transposition,
   lead: None|'mel'|'mel+3'|'mel8' (octave), lead_oct: octave shift for the melody,
   riff: 'chug'|'bounce'|'open'|'gallop'|'trem'|'stop', drums: 'skank'|'skank16'|'half'|'half16'|'blast'|'build'|'none',
   fill: bool (fill in the last half OB), crash: bool}
"""
import sys, re
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
import numpy as np
import fm_score as S

BPM = 200.0
STEP = 60 / BPM / 2          # 0.15 s: an 8th here, a 16th of the original
OB = 16 * STEP               # 2.4 s

NOTE = S.NOTE
SCALES = {  # pitch classes used for diatonic harmony per section
    'C#dor': [1, 3, 4, 6, 8, 10, 11],      # B major collection
    'F#dor': [6, 8, 9, 11, 1, 3, 4],       # F# dorian (E major collection)
    'F#min': [6, 8, 9, 11, 1, 2, 4],       # F# natural minor
}


def diatonic_up(m, scale, steps=2):
    pcs = sorted(set(scale))
    pc = m % 12
    if pc not in pcs:  # chromatic: parallel major third
        return m + 4
    i = pcs.index(pc)
    j = i + steps
    oct_ = j // len(pcs)
    return m - pc + pcs[j % len(pcs)] + 12 * oct_ + (12 if pcs[j % len(pcs)] < pc and oct_ == 0 else 0)


CHORD_SCALE = {   # the scale a harmony voice may use over each chord (keeps the colour tones the melody itself uses)
    'C#m': [1, 3, 4, 6, 8, 10, 11], 'F#': [6, 8, 10, 11, 1, 3, 4], 'E': [4, 6, 8, 10, 11, 1, 3], 'B': [11, 1, 3, 4, 6, 8, 10],
    'A': [9, 11, 1, 3, 4, 6, 8], 'G#m': [8, 10, 11, 1, 3, 4, 6], 'F#m': [6, 8, 9, 11, 1, 3, 4], 'D': [2, 4, 6, 8, 9, 11, 1],
    'C#': [1, 2, 5, 6, 8, 9, 11], 'C#7': [1, 2, 5, 6, 8, 9, 11], 'C#7b9': [1, 2, 5, 6, 8, 9, 11], 'Bm6': [11, 1, 2, 4, 6, 8, 9],
}


def harm_note(m, sym, below=False, override=None):
    """a diatonic third above (or below) m in the chord's scale; chromatic melody notes get a parallel third."""
    sc = sorted((override or {}).get(sym) or CHORD_SCALE.get(sym, CHORD_SCALE['C#m']))
    pc = m % 12
    if pc not in sc:
        return m + (-3 if below else 4)
    i = sc.index(pc)
    j = (i - 2) if below else (i + 2)
    q = sc[j % len(sc)]
    iv = (q - pc) % 12 if not below else -((pc - q) % 12)
    return m + iv


def src_notes(voice, b0, b1):
    """notes (start_step, dur_steps, midi) of a transcription voice for bars b0..b1 (1-based), re-based to 0."""
    bars = {'mel': S.MELODY, 'bass': S.BASS, 'ost': S.OSTINATO}[voice]
    ns = S.notes(bars)
    lo, hi = (b0 - 1) * 16, b1 * 16
    return [(t - lo, d, p) for (t, d, p) in ns if lo <= t < hi]


def src_chords(b0, b1):
    out = []
    for (t, d, r, ivs, sym) in S.chords():
        lo, hi = (b0 - 1) * 16, b1 * 16
        if lo <= t < hi:
            out.append((t - lo, d, r, ivs, sym))
    return out


def root_midi(pc, lo=37):
    """chord root in the rhythm guitars' register: drop-C# (lowest string C#2 = 37)."""
    m = lo + ((pc - lo) % 12)
    return m


# --------------------------------------------------------------------------------------------- part generators
def lead_part(sec, t0):
    """-> list of (t, dur, midi, vel, flags) for lead 1 and lead 2 (harmony)"""
    if not sec.get('lead'):
        return [], []
    b0, b1 = sec['src']
    k = sec.get('key', 0) + 12 * sec.get('lead_oct', 0)
    l1, l2 = [], []
    for (t, d, p) in src_notes('mel', b0, b1):
        tt = t0 + t * STEP
        dur = d * STEP * (0.98 if d >= 2 else 0.9)
        v = 0.9 if d == 1 else 1.0
        fl = {}
        if d >= 4 and sec.get('bends', True):
            fl['bend'] = 1 if (t // 16) % 2 == 0 else 0
        l1.append((tt, dur, p + k, v, fl))
        if sec.get('lead') == 'harm':
            r, ivs, sym, ct = chord_at(src_chords(b0, b1), t)
            h = (p - 12) if sec.get('harm_mode') == 'octave' else harm_note(p, sym, below=sec.get('harm_below', False), override=sec.get('harm_scales'))
            l2.append((tt, dur, h + k, v * 0.9, fl))
    return l1, l2


def chord_at(chs, step):
    for (t, d, r, ivs, sym) in chs:
        if t <= step < t + d:
            return r, ivs, sym, t
    return chs[-1][2], chs[-1][3], chs[-1][4], chs[-1][0]


def rhythm_part(sec, t0):
    """-> events for guitar_di: dicts {t, dur, notes, vel, mute}"""
    b0, b1 = sec['src']; key = sec.get('key', 0)
    chs = src_chords(b0, b1)
    nsteps = (b1 - b0 + 1) * 16
    riff = sec.get('riff', 'chug')
    ev = []
    def pc_notes(r, ivs, open_=False):
        root = root_midi((r + key) % 12)
        third_minor = 3 in ivs and 4 not in ivs
        n = [root, root + 7]
        if open_:
            n.append(root + 12)
        return n
    prev_sym = None
    for s in range(nsteps):
        r, ivs, sym, ct = chord_at(chs, s)
        change = (s == ct)
        t = t0 + s * STEP
        if riff == 'chug':
            if change or s % 16 == 0:
                # accent: open power chord, ring until next change or 2 steps
                ev.append(dict(t=t, dur=STEP * 1.9, notes=pc_notes(r, ivs, True), vel=1.0, mute=0.0))
            elif s % 2 == 1 or True:
                ev.append(dict(t=t, dur=STEP * 0.85, notes=pc_notes(r, ivs)[:1] if s % 4 else pc_notes(r, ivs), vel=0.85, mute=0.85))
        elif riff == 'bounce':
            # the original's root-fifth bounce: muted root on even steps... open fifth-chord stabs on the original off-beats
            if change:
                ev.append(dict(t=t, dur=STEP * 1.9, notes=pc_notes(r, ivs, True), vel=1.0, mute=0.0))
            elif s % 4 == 2:
                ev.append(dict(t=t, dur=STEP * 0.9, notes=pc_notes(r, ivs, True), vel=0.95, mute=0.35))
            else:
                ev.append(dict(t=t, dur=STEP * 0.8, notes=pc_notes(r, ivs)[:1], vel=0.85, mute=0.9))
        elif riff == 'open':
            if change:
                nxt = min([c[0] for c in chs if c[0] > s] + [nsteps])
                ev.append(dict(t=t, dur=(nxt - s) * STEP * 0.97, notes=pc_notes(r, ivs, True), vel=1.0, mute=0.0))
        elif riff == 'gallop':
            if change:
                ev.append(dict(t=t, dur=STEP * 1.9, notes=pc_notes(r, ivs, True), vel=1.0, mute=0.0))
            elif s % 2 == 0:
                ev.append(dict(t=t, dur=STEP * 0.85, notes=pc_notes(r, ivs)[:1], vel=0.9, mute=0.9))
            else:
                for h in (0, 0.5):
                    ev.append(dict(t=t + h * STEP, dur=STEP * 0.42, notes=pc_notes(r, ivs)[:1], vel=0.8, mute=0.95))
        elif riff == 'offbeat':
            # electro-metal: open accent on chord changes, palm-muted root-fifth on the offbeat 8ths (between the kicks)
            if change:
                ev.append(dict(t=t, dur=STEP * 0.95, notes=pc_notes(r, ivs, True), vel=1.0, mute=0.0))
            elif s % 2 == 1:
                ev.append(dict(t=t, dur=STEP * 0.8, notes=pc_notes(r, ivs), vel=0.92, mute=0.85))
        elif riff == 'stop':
            pass
    if riff == 'stop':
        # hits: (step (float ok), root pc or None = chord root, length in steps, mute 0..1)
        for h in sec.get('hits', []):
            st, pc, ln, mu = (h + (None, 1.8, 0.0)[len(h) - 1:]) if isinstance(h, tuple) else (h, None, 1.8, 0.0)
            r, ivs, sym, ct = chord_at(chs, int(st))
            rr = (pc - key) % 12 if pc is not None else r
            ev.append(dict(t=t0 + st * STEP, dur=STEP * ln * 0.95, notes=pc_notes(rr, ivs, mu < 0.5), vel=1.0 if mu < 0.5 else 0.9, mute=mu))
    if riff == 'trem':
        # tremolo-picked ostinato (our 16ths) from the transcription's transition voice, an octave up
        for (t, d, p) in src_notes('ost', b0, b1):
            for h in (0, 0.5):
                ev.append(dict(t=t0 + (t + h) * STEP, dur=STEP * 0.45, notes=[p + key + 12], vel=0.8, mute=0.3))
    return ev


def bass_part(sec, t0):
    """the original bass line, an octave down (5-string range), following the rhythm style."""
    b0, b1 = sec['src']; key = sec.get('key', 0)
    ev = []
    riff = sec.get('riff', 'chug')
    if riff in ('chug', 'gallop'):
        chs = src_chords(b0, b1)
        for s in range((b1 - b0 + 1) * 16):
            r, ivs, sym, ct = chord_at(chs, s)
            root = 25 + ((r + key - 25) % 12)          # C#1..C2
            ev.append((t0 + s * STEP, STEP * 0.9, root, 0.9, 0.3))
    elif riff == 'stop':
        chs = src_chords(b0, b1)
        for h in sec.get('hits', []):
            st, pc, ln, mu = (h + (None, 1.8, 0.0)[len(h) - 1:]) if isinstance(h, tuple) else (h, None, 1.8, 0.0)
            r, ivs, sym, ct = chord_at(chs, int(st))
            rr = pc if pc is not None else (r + key) % 12
            ev.append((t0 + st * STEP, STEP * ln * 0.95, 25 + ((rr - 25) % 12), 1.0, min(mu, 0.6)))
    else:
        for (t, d, p) in src_notes('bass', b0, b1):
            ev.append((t0 + t * STEP, d * STEP * 0.92, p + key - 12, 0.95, 0.0))
    return ev
