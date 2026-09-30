# Geno for Super Smash Bros. Melee

Geno, the star spirit in a wooden doll from *Super Mario RPG* (1996), added to *Super Smash Bros. Melee* as a
wholesale-new fighter. He isn't a costume or a clone over an existing character: he has his own fighter kind, skeleton,
model, animations, moveset, special moves, effects, sounds, menu art, costumes and Kirby copy ability, all built on the
[doldecomp Melee decompilation](https://github.com/doldecomp/melee).

A moveset demo reel is attached to this repository's first release. A new stage, the Forest Maze (a competitive
starter in SMRPG's forest), is in progress: its greybox is playable, in its own stage-select slot, with our own
arrangement of the Forest Maze theme.

This is a non-commercial fan project. Geno and *Super Mario RPG* belong to Nintendo and Square Enix, and *Super Smash
Bros. Melee* belongs to Nintendo and HAL Laboratory. **This repository contains no game data**: no disc files, no
graphics or sounds extracted from either game, and no game builds. You supply your own copies (see below).

## What he plays like

A pressure zoner. He sends projectiles he can run in behind, pins shields with the Geno Whirl, crosses them up with a
spinning neutral air, and turns stray hits into knockdowns and edgeguards. He pays for it with a light body and a
finicky recovery. The design document, `projects/geno/DESIGN.md`, has every move's frame data, the reasoning behind
it, and a changelog of each design call.

- **Neutral B, Geno Beam:** tap for a Finger Shot volley. Hold to charge through three stars; the timed release, as in
  SMRPG, adds power and a burst of rainbow stars. It fires itself after the third star and can be shield-cancelled, but
  not stored.
- **Side B, Geno Whirl:** a spinning, spiked sun that grinds shields. Pressing side B again as it hits is SMRPG's
  timed hit: more damage and a small launch into a combo.
- **Up B, Star Road:** a flight in sixteen directions.
- **Down B, Geno Blast / Geno Flash:** the mark appears on the floor as soon as he casts, so the opponent can see it;
  release to call columns of light down onto it (three at the second star). Hold to the third star and he transforms
  into his cannon and fires a sun.
- **Normals:** his weapon forms from SMRPG. Hand Gun, Star Gun and Hand Cannon shots, and rocket fists on the forward
  smash, the grabs and a long, disjointed down air. Each shot draws its reach, measured against the cast's own
  hit effects.
- **Throws:** weapon throws. A Star Gun salvo up, a Hand Cannon blast back, a Rocket Fist forward and a point-blank
  Finger Shot down.
- Six costumes (Geno, Mario, Bowser, Mallow, Peach and Dark), his own victory poses and victory fanfare (our own
  arrangement), a crowd chant, and Kirby's copy ability with Geno's cap.

## What's here

| Path | What it is |
|---|---|
| `projects/geno/` | Everything specific to Geno: the rig, animations and move scripts (`rig/`), the model built from code in Blender (`model/`), effects (`fx/`), sounds and the sound bank tools (`sound/`), menu art (`menus/`), the in-game labs that measure every change (`director/`), research, and the design docs. |
| `tools/machinima/` | The kit that drives the game: `datkit` (C#, on HSDRaw) builds Melee's data files, `build.py` compiles the decomp with a lab director, and `dolphin.py` runs Dolphin headless and logs the game's state. |
| `decomp/geno.patch` | Every change to the decompilation, as one patch against upstream doldecomp/melee (see `decomp/README.md`). All of it sits inside `#ifndef MUST_MATCH`, so the matching build still reproduces the retail game byte for byte. |

`projects/geno/HANDOFF.md` is the working manual: the state of the project, the build and test commands, and the facts
learned the hard way about the engine.

## Building it

You need:
- your own copy of *Super Smash Bros. Melee* (NTSC 1.02), extracted to a folder;
- the doldecomp toolchain, with a checkout of doldecomp/melee at the base commit, patched with `decomp/geno.patch`;
- Python 3 with numpy, scipy, Pillow, soundfile and librosa; the .NET SDK (for datkit); Blender (for the model);
  and Dolphin to play;
- for the SMRPG sound effects, your own *Super Mario RPG* (USA) cartridge dump. The tools in
  `projects/geno/sound/rom_tools/` build the bank from captures rendered from it; the capture step itself isn't packaged
  here yet.

The scripts expect a working area under `~/games/melee` (the extracted disc in `disc/`, the decomp in `decomp/`, and
generated files in `work/`). The environment variables `MELEE_DISC`, `MELEE_DECOMP` and `MELEE_WORK` override each.
In outline:

1. Build the model: `projects/geno/model/build.sh`.
2. Build Geno's fighter files and install them, as in HANDOFF §4 ("The production model build").
3. Build the effect file: `projects/geno/fx/efge.py --install`.
4. Build and install the sound bank, and the menus: HANDOFF §4 and `projects/geno/sound/`.
5. The Forest Maze stage (optional): `projects/geno/stage/` (`stage_spec.py`, datkit `stage-build`, `music.py`), then
   `projects/geno/stage/install.sh`.
6. Play: `projects/geno/play.sh` builds the game and opens it in Dolphin.

Every build step keeps the original game rebuildable: `tools/machinima/melee/build.py --matching` must still produce
the retail `main.dol`.

## How it was made

Geno was built with Claude Code (Anthropic's coding agent), directed by Michael Bishop. Michael made the design
calls; Claude agents did the engineering, modelling, animation, effects and sound work in parallel, each on its own
branch and sandbox, and verified every change in the running game. The design changelog in `DESIGN.md` records who
decided what.

## Credits

- The [doldecomp](https://github.com/doldecomp/melee) contributors, whose decompilation makes a new fighter possible.
- [HSDRaw](https://github.com/Ploaj/HSDLib), on which datkit reads and writes Melee's files.
- [Dolphin](https://dolphin-emu.org/).
- Archivo, the typeface used in the review boards (SIL Open Font License, `engine/fonts/OFL-archivo.txt`).
