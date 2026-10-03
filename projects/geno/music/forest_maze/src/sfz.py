"""Headless SFZ rendering through sfizz_render (sfizz 1.2.3 CLI, macOS build; runs under Rosetta).
    y = render(SFZ_PATH, pretty_midi.Instrument(...), total_s)   -> (2, n) float32 at 48 kHz
The instrument's notes, pitch bends and CCs are written to a temporary one-track MIDI file."""
import os, subprocess, tempfile, numpy as np, soundfile as sf, pretty_midi as pm
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401

SFIZZ = os.path.join(MUSIC, 'tools/sfizz-1.2.3-macos/usr/local/bin/sfizz_render')
LIBS = os.path.join(MUSIC, 'libs')
SR = 48000
ENV = dict(os.environ, DYLD_LIBRARY_PATH=os.path.join(MUSIC, 'tools/sfizz-1.2.3-macos/usr/local/lib'))

PATHS = {
    'emily': LIBS + '/emilyguitar/emily_basic.sfz',
    'emily_clean': LIBS + '/emilyguitar/emily_clean.sfz',
    'growly': LIBS + '/growlybass/growlybass_clean.sfz',
}


def vsco(name):
    return f'{LIBS}/VSCO-2-CE-1.1.0/{name}.sfz'


def render(sfz, inst, total, tempo=200.0, polyphony=128):
    m = pm.PrettyMIDI(initial_tempo=tempo)
    inst.program = 0; inst.is_drum = False
    m.instruments.append(inst)
    # a silent marker note at the end so sfizz renders the full length (plus tails)
    with tempfile.TemporaryDirectory() as d:
        mp, wp = os.path.join(d, 'x.mid'), os.path.join(d, 'x.wav')
        m.write(mp)
        r = subprocess.run([SFIZZ, '--sfz', sfz, '--midi', mp, '--wav', wp, '-s', str(SR), '-b', '1024', '-q', '3',
                            '-p', str(polyphony)], capture_output=True, text=True, env=ENV)
        if r.returncode != 0 or not os.path.exists(wp):
            raise RuntimeError(f'sfizz_render failed: {r.stderr[-800:]} {r.stdout[-800:]}')
        y, sr = sf.read(wp, dtype='float32', always_2d=True)
    assert sr == SR, sr
    y = y.T
    n = int(total * SR)
    if y.shape[1] < n:
        y = np.pad(y, ((0, 0), (0, n - y.shape[1])))
    return y[:, :n]


def notes_inst(notes, name='x'):
    """notes: iterable of (t, dur, midi, vel 0..1)"""
    inst = pm.Instrument(0, name=name)
    for (t, d, p, v) in notes:
        inst.notes.append(pm.Note(int(np.clip(v * 127, 1, 127)), int(p), max(0.0, t), max(0.0, t) + max(0.02, d)))
    return inst
