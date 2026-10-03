# Audio: our arrangements, rendered

Two pieces from *Super Mario RPG* (1996), composed by Yoko Shimomura, in our own arrangements, rendered and encoded as
the game plays them (HALPST streams, DSP-ADPCM). No game audio is mixed in: every note was played by the free instrument
libraries listed below, and the game was read only for the notes. The compositions belong to their owners; the
arrangements and these recordings are ours (CC BY-NC 4.0, see `LICENSE`).

| File | What it is | Length | Size | MD5 |
|---|---|---|---|---|
| `ff_geno.hps` | Geno's victory fanfare: SMRPG's post-battle "Victory" (level-up) music, arranged for orchestra, at Melee's fanfare loudness (-15 LUFS) | 7.99 s | 292,512 B | `b981e65ad7ed78e3bc22680a7b41aff4` |
| `gr_forestmaze.hps` | The Forest Maze stage track: the Forest Maze theme as symphonic metal at 200 BPM. A 9.6 s intro plays once, then 68 bars (81.6 s) loop, with the stage's own last bar so the wrap is seamless | 91.2 s | 3,337,152 B | `479eb18fc5a09785e1c77a9c550cd745` |

To use them, copy them into an extracted disc's `files/audio/` (the build steps in `HOW-TO-PLAY.md` do this). To listen
on a computer, vgmstream decodes `.hps` (`vgmstream-cli ff_geno.hps -o ff_geno.wav`).

The arrangement sources, the MIDI of every part and the renderers are in `projects/geno/music/` (its README has the
commands). A re-render gives the same arrangement and mix but not the same bytes: one synth starts at a random phase,
and the sample player's timing varies under load.

## Instruments and credits

- Drums: **Aasimonster2 drumkit by the DrumGizmo team, CC-BY 4.0** (the Forest Maze).
- Guitars and bass: Karoryfer's Emilyguitar and Growlybass (CC0), re-amped through NAM captures from
  `pelennor2170/NAM_models` (GPL-3.0 models).
- Orchestra: VS Chamber Orchestra 2 Community Edition (CC0), in both pieces.
- Synths: Surge XT's factory patches (GPL-3.0 software). Choir: GeneralUser GS (its licence allows use in music).
- Players: sfizz, Surge XT (hosted in pedalboard) and FluidSynth.
