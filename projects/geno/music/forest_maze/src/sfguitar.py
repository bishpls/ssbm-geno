"""Sampled-guitar DI via FluidSynth + GeneralUser GS (real recorded guitar samples), for re-amping through NAM.
  lead_sf(notes, total)   : monophonic lead, program 27 (clean electric), pitch-bend vibrato, bends and legato slides
  rhythm_sf(events, total): power chords, program 28 (muted guitar) for palm mutes, 27 for open chords
Both return mono float32 at 48 kHz."""
import os, subprocess, tempfile, numpy as np, soundfile as sf, pretty_midi as pm
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401

SF2 = os.path.join(MUSIC, 'sf/GeneralUser-GS-main/GeneralUser-GS.sf2')
SR = 48000


def _render(midi, total):
    with tempfile.TemporaryDirectory() as d:
        mp, wp = os.path.join(d, 'x.mid'), os.path.join(d, 'x.wav')
        midi.write(mp)
        subprocess.run(['fluidsynth', '-ni', '-g', '1.0', '-r', str(SR), '-o', 'synth.reverb.active=0', '-o', 'synth.chorus.active=0',
                        '-F', wp, SF2, mp], check=True, capture_output=True)
        y, sr = sf.read(wp, dtype='float32')
    y = y.mean(1) if y.ndim > 1 else y
    n = int(total * SR)
    return np.pad(y, (0, max(0, n - len(y))))[:n]


def _bend_range(inst, semis, t=0.0):
    for cc, v in [(101, 0), (100, 0), (6, semis), (38, 0), (101, 127), (100, 127)]:
        inst.control_changes.append(pm.ControlChange(cc, v, t))


def lead_sf(notes, total, program=27, bend_semis=12, vib_rate=5.6, vib_depth=0.55, seed=0, slide=0.05, humanize=0.004):
    """Guitar-like phrasing: every note re-articulated (no synth portamento); in runs of short notes every other note is a
    softer hammer-on/pull-off; vibrato only on held notes and only upward (a guitarist bends the string sharp and back);
    bends on flagged notes rise from below; slides only where flagged."""
    rng = np.random.default_rng(seed)
    m = pm.PrettyMIDI(initial_tempo=200)
    inst = pm.Instrument(program, name='lead')
    _bend_range(inst, bend_semis)
    notes = sorted(notes, key=lambda x: x[0])
    rate = 250.0
    bends = []
    run = 0
    for i, nt in enumerate(notes):
        t, d, p, v = nt[:4]; fl = nt[4] if len(nt) > 4 else {}
        t = max(0.0, t + rng.normal(0, humanize))
        prev = notes[i - 1] if i > 0 else None
        joined = prev is not None and prev[0] + prev[1] >= nt[0] - 0.04
        run = run + 1 if (joined and d < 0.2) else 0
        hammer = run % 2 == 1 and abs(prev[2] - p) <= 3 if prev is not None else False
        vel = int(np.clip((0.7 if hammer else 0.97) * v * 127 * (1 + rng.normal(0, 0.05)), 30, 127))
        inst.notes.append(pm.Note(vel, int(p), t, t + max(0.03, d)))
        k = np.arange(0, d, 1 / rate)
        off = np.zeros_like(k)
        if fl.get('slide') and prev is not None:
            s_ = np.clip(k / slide, 0, 1); off += (prev[2] - p) * (1 - s_)
        b = fl.get('bend', 0)
        if b:
            tb = rng.uniform(0.09, 0.15)
            s_ = np.clip(k / tb, 0, 1); off += -b * (1 - np.sin(0.5 * np.pi * s_)) + 0.06 * b * np.sin(np.pi * s_)
        if d > 0.27:
            r_ = vib_rate * (1 + 0.08 * np.sin(2 * np.pi * rng.uniform(0.3, 0.7) * k + rng.uniform(0, 6))) + rng.normal(0, 0.3)
            ph = 2 * np.pi * np.cumsum(r_) / rate
            depth = fl.get('vib', vib_depth) * np.clip((k - 0.2) / 0.3, 0, 1) * (1 + 0.15 * rng.normal())
            off += depth * (0.5 - 0.5 * np.cos(ph))          # upward only
        for kk, o in zip(k, off):
            bends.append((t + kk, o))
    bends.sort()
    last = None
    for (t, o) in bends:
        val = int(np.clip(o / bend_semis * 8191, -8192, 8191))
        if val != last:
            inst.pitch_bends.append(pm.PitchBend(val, t)); last = val
    m.instruments.append(inst)
    return _render(m, total)


def rhythm_sf(events, total, seed=0, humanize=0.006, open_prog=27, mute_prog=28, detune_cents=0):
    rng = np.random.default_rng(seed)
    m = pm.PrettyMIDI(initial_tempo=200)
    mute = pm.Instrument(mute_prog, name='mutes'); opn = pm.Instrument(open_prog, name='open')
    if detune_cents:
        for inst in (mute, opn):
            _bend_range(inst, 2); inst.pitch_bends.append(pm.PitchBend(int(detune_cents / 200 * 8191), 0.0))
    for e in events:
        t = max(0.0, e['t'] + rng.normal(0, humanize))
        inst = mute if e.get('mute', 0) >= 0.5 else opn
        dur = e['dur'] * (1 + rng.normal(0, 0.08)) if e.get('mute', 0) >= 0.5 else e['dur']
        for si, p in enumerate(sorted(e['notes'])):
            v = int(np.clip(e.get('vel', 0.9) * 120 * (1 + rng.normal(0, 0.09)), 30, 127))
            inst.notes.append(pm.Note(v, int(p), t + si * 0.003, t + si * 0.003 + max(0.04, dur)))
    m.instruments += [mute, opn]
    return _render(m, total)


def bass_sf(events, total, program=34, seed=0):
    """events: (t, dur, midi, vel, mute) -> picked-bass DI (GS program 34)"""
    rng = np.random.default_rng(seed)
    m = pm.PrettyMIDI(initial_tempo=200)
    inst = pm.Instrument(program, name='bass')
    for (t, d, p, v, mu) in events:
        tt = max(0.0, t + rng.normal(0, 0.003))
        inst.notes.append(pm.Note(int(np.clip(v * 118 * (1 + rng.normal(0, 0.04)), 30, 127)), int(p), tt, tt + d * (0.7 if mu >= 0.5 else 1.0)))
    m.instruments.append(inst)
    return _render(m, total)
