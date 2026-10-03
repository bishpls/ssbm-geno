"""Export draft 2 as a multitrack MIDI (200 BPM): band (lead, lead 2, rhythm open/mutes, bass, drums) + every orchestral,
choir and synth part, one track each, named with the instrument used, plus section markers.
    python export_midi2.py OUT.mid"""
import sys
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
import pretty_midi as pm
import render2 as R2, draft2 as D2

GM = {'kick': 36, 'kick808': 35, 'snare': 38, 'clap': 39, 'rim': 37, 'hat': 42, 'hatopen': 46, 'ride': 51, 'bell': 53,
      'crash1': 49, 'crash2': 57, 'china': 52, 'tom1': 50, 'tom2': 47, 'tom3': 45, 'ftom': 41}
NAMES = {'vln_mel_s': ('Violins melody, short notes (VSCO2 ViolinEnsSpic)', 45), 'vln_mel': ('Violins melody (VSCO2 ViolinEnsSusVib)', 40), 'hn_mel': ('Horns melody (VSCO2 FHornSus)', 60),
         'fl_mel': ('Flute melody (VSCO2 FluteSusVib)', 73), 'vln': ('Violins (VSCO2)', 48), 'vla': ('Violas (VSCO2)', 48),
         'vc': ('Cellos (VSCO2)', 48), 'cb': ('Basses (VSCO2)', 48), 'vln_spic': ('Violins spiccato (VSCO2)', 45),
         'vla_spic': ('Violas spiccato (VSCO2)', 45), 'vln_trem': ('Violins tremolo (VSCO2)', 44), 'hn': ('Horns (VSCO2)', 60),
         'hn_stac': ('Horns staccato (VSCO2)', 60), 'tbn': ('Trombones (VSCO2)', 57), 'tpt': ('Trumpet staccato (VSCO2)', 56),
         'glock': ('Glockenspiel (VSCO2)', 9), 'timp': ('Timpani (VSCO2)', 47), 'timp_roll': ('Timpani rolls (VSCO2)', 47),
         'arp': ('Synth arp (Surge XT: Saw Pluck)', 81), 'pad': ('Supersaw pad (Surge XT: Tarnce)', 90),
         'slead': ('Synth lead (Surge XT: Saw Octaves)', 81), 'sbass': ('Synth bass (Surge XT: Tight Bassline)', 38),
         'bell': ('Music box (Surge XT: Magic Music Box)', 10), 'choir': ('Choir (GeneralUser GS Choir Aahs + Voice Oohs)', 52)}


def export(path):
    E, layers, pumps, segs, total = R2.build(D2.SECTIONS, D2.FINAL_HIT)
    m = pm.PrettyMIDI(initial_tempo=200.0)
    tr = lambda name, prog, drum=False: pm.Instrument(prog, is_drum=drum, name=name)
    lead = tr('Lead guitar (Emilyguitar DI -> NAM)', 30); harm = tr('Lead guitar 2 (harmony)', 30)
    ropen = tr('Rhythm guitar open (Emilyguitar DI -> NAM)', 30); rmute = tr('Rhythm guitar palm mutes', 28)
    bass = tr('Bass (Growlybass DI)', 34); drums = tr('Drums (Aasimonster kit + synth clap/808)', 0, True)
    for (t, d, p, v, f) in E['lead1']: lead.notes.append(pm.Note(int(min(127, v * 110)), int(p), t, t + d))
    for (t, d, p, v, f) in E['lead2']: harm.notes.append(pm.Note(int(min(127, v * 100)), int(p), t, t + d))
    for e in E['rL']:
        inst = rmute if e.get('mute', 0) >= 0.5 else ropen
        for p in e['notes']: inst.notes.append(pm.Note(int(min(127, e.get('vel', 0.9) * 110)), int(p), max(0, e['t']), max(0, e['t']) + e['dur']))
    for (t, d, p, v, mu) in E['bass']: bass.notes.append(pm.Note(int(min(127, v * 110)), int(p), max(0, t), max(0, t) + d))
    for (t, p, v) in E['drums']: drums.notes.append(pm.Note(int(min(127, v * 120)), GM[p], max(0, t), max(0, t) + 0.05))
    m.instruments += [lead, harm, ropen, rmute, bass, drums]
    for inst, ns in sorted(layers.items()):
        name, prog = NAMES[inst]
        t_ = tr(name, prog)
        for (t, d, p, v) in ns: t_.notes.append(pm.Note(int(max(1, min(127, v * 127))), int(p), max(0, t), max(0, t) + d))
        m.instruments.append(t_)
    for (t, name) in E['marks']: m.lyrics.append(pm.Lyric(name, t))
    m.lyrics.append(pm.Lyric('FINAL HIT', E['end']))
    m.write(path)
    print('wrote', path, len(m.instruments), 'tracks; final hit at', E['end'])


if __name__ == '__main__':
    export(sys.argv[1])
