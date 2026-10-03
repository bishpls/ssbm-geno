"""Write the transcription as MIDI (melody / bass / harmony on separate tracks) and a resynthesis aligned to the recording.
    python transcribe_out.py            -> ../transcription/forest_maze_transcription.mid (1 loop, 94.625 BPM)
                                          ../transcription/resynth_aligned.mid (2 loops, offset to the recording's downbeat)"""
import sys, subprocess, pretty_midi as pm
sys.path.insert(0, '.')
import fm_score as S
BPM = 94.625; S16 = 60 / BPM / 4; DOWN = 0.690


def chord_voicing(root, ivs, lo=52):
    # close voicing starting at or above `lo` (E3)
    r = root
    while r + 12 < lo + 12 and r < lo: r += 12
    return [r + i for i in ivs if not (i == 13)] + ([r + 13] if 13 in ivs else [])


def build(loops=1, offset=0.0, prog_mel=73, prog_bass=33, prog_ch=48, stacc=0.85):
    m = pm.PrettyMIDI(initial_tempo=BPM)
    mel = pm.Instrument(prog_mel, name='melody'); bas = pm.Instrument(prog_bass, name='bass'); har = pm.Instrument(prog_ch, name='harmony')
    ost = pm.Instrument(46, name='ostinato')
    for L in range(loops):
        base = offset + L * 88 * 4 * S16
        for t, d, p in S.notes(S.MELODY):
            mel.notes.append(pm.Note(100, p, base + t * S16, base + (t + d * stacc) * S16))
        for t, d, p in S.notes(S.BASS):
            bas.notes.append(pm.Note(100, p, base + t * S16, base + (t + d * stacc) * S16))
        for t, d, r, ivs, sym in S.chords():
            for p in chord_voicing(r, ivs):
                har.notes.append(pm.Note(64, p, base + t * S16, base + (t + d) * S16 - 0.01))
        for t, d, p in S.notes(S.OSTINATO):
            ost.notes.append(pm.Note(80, p, base + t * S16, base + (t + d * stacc) * S16))
    m.instruments += [mel, bas, har, ost]
    for s, b0, b1 in S.SECTIONS:
        m.lyrics.append(pm.Lyric(s, offset + (b0 - 1) * 16 * S16))
    return m


if __name__ == '__main__':
    build(1).write('../transcription/forest_maze_transcription.mid')
    build(2, DOWN).write('../transcription/resynth_aligned.mid')
    sf = '../sf/GeneralUser-GS-main/GeneralUser-GS.sf2'
    subprocess.run(['fluidsynth', '-ni', '-g', '0.6', '-r', '44100', '-F', '../transcription/resynth_aligned.wav', sf,
                    '../transcription/resynth_aligned.mid'], check=True, capture_output=True)
    print('wrote transcription MIDI + resynth')
