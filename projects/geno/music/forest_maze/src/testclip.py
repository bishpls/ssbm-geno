"""The test segment every route renders: the theme (transcription bars 1-8) at 200 BPM = 8 OB = 19.2 s + a final hit.
Writes tests/theme_guide.mid (lead + bass, for conditioning) and tests/theme_guide.wav (GM render, 32 kHz mono)."""
import sys, subprocess, pretty_midi as pm, numpy as np
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
import arrange as A

SEC = [
    dict(name='A', src=(1, 4), lead='mel', lead_oct=1, riff='chug', drums='skank', scale='C#dor'),
    dict(name="A'", src=(5, 8), lead='harm', lead_oct=0, riff='chug', drums='skank16', scale='C#dor', fill=True),
]
END = 8 * A.OB


def guide_midi(path):
    m = pm.PrettyMIDI(initial_tempo=A.BPM)
    lead = pm.Instrument(30, name='lead'); bass = pm.Instrument(34, name='bass')
    t0 = 0
    for sec in SEC:
        l1, l2 = A.lead_part(sec, t0)
        for (t, d, p, v, fl) in l1:
            lead.notes.append(pm.Note(int(100 * v), p, t, t + d))
        for (t, d, p, v, mute) in A.bass_part(dict(sec, riff='bounce'), t0):
            bass.notes.append(pm.Note(90, p + 12, t, t + d))
        t0 += (sec['src'][1] - sec['src'][0] + 1) * A.OB
    # final hit on C#
    lead.notes.append(pm.Note(100, 61, END, END + 1.0)); bass.notes.append(pm.Note(100, 37, END, END + 1.0))
    m.instruments += [lead, bass]
    m.write(path)


if __name__ == '__main__':
    import os
    os.makedirs(os.path.join(MUSIC, 'tests'), exist_ok=True)
    p = os.path.join(MUSIC, 'tests/theme_guide')
    guide_midi(p + '.mid')
    subprocess.run(['fluidsynth', '-ni', '-g', '0.7', '-r', '32000', '-F', p + '_st.wav',
                    os.path.join(MUSIC, 'sf/GeneralUser-GS-main/GeneralUser-GS.sf2'), p + '.mid'], check=True, capture_output=True)
    subprocess.run(['/opt/homebrew/bin/ffmpeg', '-loglevel', 'error', '-y', '-i', p + '_st.wav', '-ac', '1', '-t', '20.5', p + '.wav'], check=True)
    print('wrote', p + '.wav')
