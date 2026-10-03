"""Symphonic and electro layers for draft 2: note generators per section (on the 200 BPM clock).
Each generator returns {instrument: [(t, dur, midi, vel), ...]}; instruments are rendered by render2.py:
  VSCO 2 CE (sfizz): vln, vla, vc, cb (sustain), vln_spic, vla_spic, vln_trem, hn (horns sus), hn_stac, tbn, tpt, glock,
                     timp, timp_roll
  Surge XT (pedalboard): arp, pad, slead, sbass, bell
  GeneralUser GS (FluidSynth): choir"""
import sys
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
import arrange as A

STEP, OB, H = A.STEP, A.OB, A.STEP / 2


def chords_for(sec):
    """[(t_rel_s, dur_s, root_pc, ivs)] for the section (src bars, key applied)"""
    out = []
    for (t, d, r, ivs, sym) in A.src_chords(*sec['src']):
        out.append((t * STEP, d * STEP, (r + sec.get('key', 0)) % 12, [i for i in ivs if i != 13][:4], sym))
    return out


def voice(pcs, lo, hi, prev=None, n=3):
    """choose n chord tones in [lo, hi], closest to the previous voicing (smooth voice leading)."""
    cands = sorted(m for m in range(lo, hi + 1) if m % 12 in pcs)
    best = None
    import itertools
    for combo in itertools.combinations(cands, n):
        if len({c % 12 for c in combo}) < min(n, len(set(pcs))): continue
        if combo[-1] - combo[0] > 14: continue
        cost = sum(abs(a - b) for a, b in zip(combo, prev)) if prev else abs(sum(combo) / n - (lo + hi) / 2)
        if best is None or cost < best[0]: best = (cost, combo)
    return list(best[1]) if best else cands[:n]


def add(out, inst, t, d, p, v):
    out.setdefault(inst, []).append((t, d, int(p), v))


def strings_pad(sec, t0, out, vel=0.55, low=True):
    prev_v = prev_a = None
    for (t, d, r, ivs, sym) in chords_for(sec):
        pcs = [(r + i) % 12 for i in ivs]
        vv = voice(pcs, 64, 81, prev_v, 3); prev_v = vv
        va = voice(pcs, 55, 69, prev_a, 2); prev_a = va
        for p in vv: add(out, 'vln', t0 + t, d * 0.98, p, vel)
        for p in va: add(out, 'vla', t0 + t, d * 0.98, p, vel * 0.9)
        if low:
            root = 36 + ((r - 36) % 12)
            add(out, 'vc', t0 + t, d * 0.98, root + 12 if root + 12 <= 55 else root, vel * 0.8)


def strings_melody(sec, t0, out, inst='vln', vel=0.7, octave=0, bars=None, split_short=False):
    """the melody on one instrument; split_short sends 16th notes to the spiccato patch (sustain samples speak too slowly)"""
    b0, b1 = bars or sec['src']
    shift = ((b0 - sec['src'][0]) * 16) * STEP
    for (t, d, p) in A.src_notes('mel', b0, b1):
        target = inst + '_s' if (split_short and d == 1) else inst
        add(out, target, t0 + shift + t * STEP, d * STEP * (0.9 if target.endswith('_s') else 1.02), p + sec.get('key', 0) + 12 * octave,
            vel * (1.1 if target.endswith('_s') else 1.0))


def strings_spic(sec, t0, out, vel=0.6):
    """8th-note chord-tone ostinato (violins + violas), root-5th-octave-5th shape"""
    for (t, d, r, ivs, sym) in chords_for(sec):
        base = 61 + ((r - 61) % 12)   # C#4..C5
        shape = [base, base + 7, base + 12, base + 7]
        for k in range(int(round(d / STEP))):
            tt = t0 + t + k * STEP
            add(out, 'vln_spic', tt, STEP * 0.6, shape[k % 4] + 12, vel * (1.0 if k % 2 == 0 else 0.8))
            add(out, 'vla_spic', tt, STEP * 0.6, shape[k % 4], vel * 0.8)


def strings_trem(sec, t0, out, vel=0.5):
    prev = None
    for (t, d, r, ivs, sym) in chords_for(sec):
        pcs = [(r + i) % 12 for i in ivs]
        vv = voice(pcs, 60, 79, prev, 3); prev = vv
        for p in vv: add(out, 'vln_trem', t0 + t, d * 0.98, p, vel)


def brass_pad(sec, t0, out, vel=0.6):
    prev = None
    for (t, d, r, ivs, sym) in chords_for(sec):
        pcs = [(r + i) % 12 for i in ivs]
        v = voice(pcs, 53, 69, prev, 3); prev = v
        for p in v: add(out, 'hn', t0 + t, d * 0.97, p, vel)
        root = 37 + ((r - 37) % 12)
        add(out, 'tbn', t0 + t, d * 0.97, root if root >= 40 else root + 12, vel * 0.8)


def brass_stabs(sec, t0, out, vel=0.85):
    prev = None
    for (t, d, r, ivs, sym) in chords_for(sec):
        pcs = [(r + i) % 12 for i in ivs]
        v = voice(pcs, 55, 72, prev, 3); prev = v
        for p in v: add(out, 'hn_stac', t0 + t, 0.2, p, vel)
        add(out, 'tpt', t0 + t, 0.22, max(v) + (12 if max(v) < 64 else 0), vel * 0.9)


def choir(sec, t0, out, vel=0.6):
    prev = None
    for (t, d, r, ivs, sym) in chords_for(sec):
        pcs = [(r + i) % 12 for i in ivs]
        v = voice(pcs, 57, 76, prev, 4 if len(pcs) >= 3 else 3); prev = v
        for p in v: add(out, 'choir', t0 + t, d * 0.99, p, vel)


def glock_melody(sec, t0, out, vel=0.6, octave=1, long_only=False, bars=None):
    b0, b1 = bars or sec['src']
    shift = ((b0 - sec['src'][0]) * 16) * STEP
    for (t, d, p) in A.src_notes('mel', b0, b1):
        if long_only and d < 2: continue
        q = p + sec.get('key', 0) + 12 * octave
        while q > 96: q -= 12
        while q < 67: q += 12
        add(out, 'glock', t0 + shift + t * STEP, 0.5, q, vel)


def bell_melody(sec, t0, out, vel=0.7, octave=1, bars=None):
    b0, b1 = bars or sec['src']
    shift = ((b0 - sec['src'][0]) * 16) * STEP
    for (t, d, p) in A.src_notes('mel', b0, b1):
        add(out, 'bell', t0 + shift + t * STEP, d * STEP * 0.9, p + sec.get('key', 0) + 12 * octave, vel)


def arp(sec, t0, out, vel=0.7, lo=61, pattern='up', start=0.0, end=None):
    """16th-note (our 16ths) chord arpeggio, two octaves, up or up-down"""
    for (t, d, r, ivs, sym) in chords_for(sec):
        pcs = sorted({(r + i) % 12 for i in ivs[:3]})
        base = [m for m in range(lo, lo + 24) if m % 12 in pcs]
        seqn = base if pattern == 'up' else base + base[-2:0:-1]
        n = int(round(d / H))
        for k in range(n):
            tt = t + k * H
            if tt < start or (end is not None and tt >= end): continue
            add(out, 'arp', t0 + tt, H * 0.9, seqn[k % len(seqn)], vel * (1.0 if k % 4 == 0 else 0.8))


def arp_ostinato(sec, t0, out, vel=0.7):
    """the transition's ostinato (transcription voice), octave up, each 8th split into note + octave above"""
    b0, b1 = sec['src']
    for (t, d, p) in A.src_notes('ost', b0, b1):
        q = p + sec.get('key', 0) + 12
        add(out, 'arp', t0 + t * STEP, H * 0.9, q, vel)
        add(out, 'arp', t0 + t * STEP + H, H * 0.9, q + 12, vel * 0.8)


def pad(sec, t0, out, vel=0.6):
    prev = None
    for (t, d, r, ivs, sym) in chords_for(sec):
        pcs = [(r + i) % 12 for i in ivs]
        v = voice(pcs, 55, 74, prev, 4 if len(pcs) >= 3 else 3); prev = v
        for p in v: add(out, 'pad', t0 + t, d * 0.99, p, vel)


def synth_lead(sec, t0, out, vel=0.7, octave=1, bars=None):
    b0, b1 = bars or sec['src']
    shift = ((b0 - sec['src'][0]) * 16) * STEP
    for (t, d, p) in A.src_notes('mel', b0, b1):
        add(out, 'slead', t0 + shift + t * STEP, d * STEP * 0.95, p + sec.get('key', 0) + 12 * octave, vel)


def synth_bass(sec, t0, out, vel=0.8):
    """offbeat 8ths (trance bass), octave 2"""
    for (t, d, r, ivs, sym) in chords_for(sec):
        root = 37 + ((r - 37) % 12)
        for k in range(int(round(d / STEP))):
            if k % 2 == 1: add(out, 'sbass', t0 + t + k * STEP, STEP * 0.8, root, vel)


def timp_hit(t, out, pc=1, vel=0.95):
    add(out, 'timp', t, 1.2, 37 + ((pc - 37) % 12) if 37 + ((pc - 37) % 12) <= 48 else 25 + ((pc - 25) % 12) + 12, vel)


def timp_roll(t, d, out, pc=1, vel=0.8):
    add(out, 'timp_roll', t, d, 37 + ((pc - 37) % 12), vel)


LAYERS = {'strings_pad': strings_pad, 'strings_melody': strings_melody, 'strings_spic': strings_spic, 'strings_trem': strings_trem,
          'brass_pad': brass_pad, 'brass_stabs': brass_stabs, 'choir': choir, 'glock_melody': glock_melody,
          'bell_melody': bell_melody, 'arp': arp, 'arp_ostinato': arp_ostinato, 'pad': pad, 'synth_lead': synth_lead,
          'synth_bass': synth_bass}


def section_layers(sec, t0):
    out = {}
    for spec in sec.get('layers', []):
        name, kw = (spec, {}) if isinstance(spec, str) else spec
        kw = dict(kw); win = kw.pop('win', None)
        tmp = {}
        LAYERS[name](sec, t0, tmp, **kw)
        for inst, ns in tmp.items():
            for (t, d, p, v) in ns:
                if win is None or (t0 + win[0] - 1e-6 <= t < t0 + win[1] - 1e-6):
                    out.setdefault(inst, []).append((t, d, p, v))
    for (t, pc) in sec.get('timp_hits', []):
        timp_hit(t0 + t, out, pc if pc is not None else (A.src_chords(*sec['src'])[0][2] + sec.get('key', 0)) % 12)
    for (t, d, pc) in sec.get('timp_rolls', []):
        timp_roll(t0 + t, d, out, pc)
    return out
