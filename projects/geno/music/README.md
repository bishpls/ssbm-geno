# Geno's music: the arrangement sources

Our own arrangements of two pieces from *Super Mario RPG* (1996), both composed by Yoko Shimomura: the Forest Maze theme,
as a symphonic-metal stage track, and the post-battle "Victory" (level-up) music, as Geno's victory fanfare. The
melodies belong to their owners; the arrangements, the code and the renders are ours. Nothing here is a rip: no game
audio is mixed in, and the renders use only the free instrument libraries listed below.

| Piece | In the game | Sources here | Rendered by |
|---|---|---|---|
| Forest Maze, metal draft 2 (the stage's loop) | `audio/gr_forestmaze.hps` | `forest_maze/` | `forest_maze/src/render2.py`, then `../stage/music_loopend.py` and `../stage/music.py build` |
| Victory fanfare | `audio/ff_geno.hps` | `fanfare/` | `fanfare/src/render_ff.py`, then `tools/machinima/melee/audio/hps.py encode` |

## Forest Maze (`forest_maze/`)

- `src/fm_score.py`: the transcription of the original (one 22-bar loop, melody, bass, harmony and the transition's
  16th ostinato), made with basic-pitch on the recording and corrected by hand against pitch maps.
  `midi/forest_maze_transcription.mid` is the same, as MIDI.
- `src/arrange.py`, `draft.py`, `draft2.py`: the arrangement at 200 BPM (INTRO, THEME A/A', TRANSITION, B, C, D, GLADE,
  SOLO, FINAL, the final hit at 91.2 s = frame 5472). `orch.py`, `drumpat.py`: the orchestral, synth and drum parts.
  `midi/forest_maze_metal_arrangement_draft2.mid` (26 tracks): every part, named with its instrument.
- `src/render2.py` (with `sfz.py`, `guitars2.py`, `surgepatch.py`, `drumkit.py`, `nam.py`, `mix.py`, `instruments.py`):
  the renderer: DI guitars and bass re-amped through NAM captures, the orchestra and synths, buses, a linear master and
  stems that sum to it. `render.py`, `sfguitar.py`: draft 1's renderer (render2 reuses parts of it).
- `src/export_midi2.py`, `fidelity.py`, `secfid2.py`: the MIDI export and the melody-fidelity measure.
- `data/`: the cue sheets (section marks per draft) and `ref_tonal_curve.json`, the master EQ's target (numbers only: a
  long-term spectrum measured from the style references).

```sh
export GENO_MUSIC=~/games/melee/work/music
cd projects/geno/music/forest_maze/src
../../../../../.venv/bin/python -c \
  "import render2 as R2, draft2 as D2, drumkit as DK; R2.render(D2.SECTIONS, '$GENO_MUSIC/takes/x', D2.FINAL_HIT, DK.Kit())"   # ~3 min
cd -   # back to the repo root
.venv/bin/python projects/geno/stage/music_loopend.py          # ~8 min: the stage's own last bar (no stop before the loop)
.venv/bin/python projects/geno/stage/music.py build            # the stage stream: intro once, a 68-bar loop, 32 kHz DSP-ADPCM
```

**Measured (2026-10-02):** `export_midi2.py` regenerates `midi/forest_maze_metal_arrangement_draft2.mid` byte for byte
from these sources. The audio renders are not bit-repeatable: Surge XT starts its oscillators at a random phase, and
sfizz streams sample tails on a thread, so renders under load differ (`../stage/music_loopend.py` explains and guards
it). A re-render is the same arrangement with the same mix, not the same bytes; the rendered tracks themselves are in
the public repo's `audio/`.

## Victory fanfare (`fanfare/`)

- `src/smrpg_seq.py`: reads the music sequence of your own cartridge (track 9, "Victory") and interprets it: notes,
  lengths, repeats, tempo, transposition. `src/drvplay.py` and `spclog.py` play it through the game's own sound driver
  (the capture's `spcharness`, with `spclog/`'s DSP-write log) to check every key-on against the interpreter.
- `src/levelup.py`: the arrangement (D major at the original tempo, 7.99 s: intro bar, theme, the run, a held tutti),
  whose tables are that transcription. `midi/geno_levelup_fanfare.mid`: every part.
- `src/render_ff.py`: the render (VSCO 2 CE through sfizz, a hall, a master matched to Melee's own fanfares' loudness).
  `measure.py`, `melfid.py`, `bpcheck.py`, `pitchcheck.py`, `cqtview.py`, `findff.py`: the checks.

```sh
cd projects/geno/music/fanfare/src && ../../../../../.venv/bin/python render_ff.py OUT        # 32 kHz master in OUT
.venv/bin/python tools/machinima/melee/audio/hps.py encode OUT/levelup_fanfare_32k.wav ff_geno.hps
```

## Instruments (none of them are in this repo)

Put them under `GENO_MUSIC` (default `~/games/melee/work/music`) as `src/music_paths.py` lists.

| Instrument | Licence | Used for |
|---|---|---|
| sfizz 1.2.3 (`sfizz_render`) | BSD-2-Clause | plays every SFZ below |
| Karoryfer Emilyguitar, Growlybass | CC0 | DI guitars and bass |
| VS Chamber Orchestra 2 Community Edition 1.1.0 | CC0 | strings, brass, woodwinds, glockenspiel, xylophone, timpani, cymbals (both pieces) |
| Surge XT 1.3.4 (VST3) and its factory patches, hosted in pedalboard | GPL-3.0 (the software; renders are ours) | arp, supersaw pad, music box |
| GeneralUser GS (FluidSynth 2.6.1) | GeneralUser GS License v2.0: free use in music, private or commercial | choir |
| Aasimonster2 drum kit (DrumGizmo) | **CC BY 4.0: credit "Aasimonster2 drumkit by the DrumGizmo team, CC-BY 4.0"** | drums (the Forest Maze) |
| NAM captures from `pelennor2170/NAM_models` | GPL-3.0 (the models; renders are ours) | guitar and bass amps |

Python: pedalboard 0.9.25, pretty_midi, mido, pyloudnorm, torch (NAM), librosa, soundfile.
