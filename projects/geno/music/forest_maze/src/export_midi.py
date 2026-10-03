"""Export the arrangement as a multitrack MIDI (200 BPM): lead, lead harmony, rhythm guitar (power chords, palm mutes on
a separate track), bass, drums (GM channel 10), plus section markers as text events.
    python export_midi.py OUT.mid"""
import sys
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
import pretty_midi as pm
import render as R, draft as Dr

GM = {'kick': 36, 'snare': 38, 'rim': 37, 'hat': 42, 'hatopen': 46, 'ride': 51, 'bell': 53, 'crash1': 49, 'crash2': 57,
      'china': 52, 'tom1': 50, 'tom2': 47, 'tom3': 45, 'ftom': 41}


def export(path):
    E = R.build_events(Dr.SECTIONS)
    notes, bm, lm = Dr.FINAL_HIT; t = E['end']
    E['rL'].append(dict(t=t, dur=2.2, notes=notes, vel=1.0, mute=0.0)); E['bass'].append((t, 2.2, bm, 1.0, 0.0))
    E['lead1'].append((t, 1.8, lm, 1.0, {})); E['drums'] += [(t, 'kick', 1.0), (t, 'crash1', 1.0), (t, 'china', 0.9)]
    m = pm.PrettyMIDI(initial_tempo=200.0)
    lead = pm.Instrument(30, name='Lead guitar'); harm = pm.Instrument(30, name='Lead guitar 2 (harmony)')
    ropen = pm.Instrument(30, name='Rhythm guitar (open)'); rmute = pm.Instrument(28, name='Rhythm guitar (palm mutes)')
    bass = pm.Instrument(34, name='Bass'); drums = pm.Instrument(0, is_drum=True, name='Drums')
    for (tt, d, p, v, f) in E['lead1']: lead.notes.append(pm.Note(int(min(127, v * 110)), int(p), tt, tt + d))
    for (tt, d, p, v, f) in E['lead2']: harm.notes.append(pm.Note(int(min(127, v * 100)), int(p), tt, tt + d))
    for e in E['rL']:
        inst = rmute if e.get('mute', 0) >= 0.5 else ropen
        for p in e['notes']: inst.notes.append(pm.Note(int(min(127, e.get('vel', 0.9) * 110)), int(p), max(0, e['t']), max(0, e['t']) + e['dur']))
    for (tt, d, p, v, mu) in E['bass']: bass.notes.append(pm.Note(int(min(127, v * 110)), int(p), max(0, tt), max(0, tt) + d))
    for (tt, p, v) in E['drums']: drums.notes.append(pm.Note(int(min(127, v * 120)), GM[p], max(0, tt), max(0, tt) + 0.05))
    m.instruments += [lead, harm, ropen, rmute, bass, drums]
    for (tt, name) in E['marks']: m.lyrics.append(pm.Lyric(name, tt))
    m.lyrics.append(pm.Lyric('FINAL HIT', t))
    m.write(path)
    print('wrote', path, 'end hit at', t)


if __name__ == '__main__':
    export(sys.argv[1])
