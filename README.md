# Geno for Super Smash Bros. Melee

Geno, the star spirit in a wooden doll from *Super Mario RPG* (1996), added to *Super Smash Bros. Melee* as a
wholesale-new fighter. He isn't a costume or a clone over an existing character: he has his own fighter kind, skeleton,
model, animations, moveset, special moves, effects, sounds, menu art, costumes and Kirby copy ability, all built on the
[doldecomp Melee decompilation](https://github.com/doldecomp/melee). With him comes a new competitive stage, the Forest
Maze, a starter in SMRPG's forest with its own stage-select slot, a moving twilight sky and our own metal arrangement of
the Forest Maze theme.

**[How to play](HOW-TO-PLAY.md)**: patch your own Melee ISO with the release's xdelta, or build everything from source.
**[How it was made](MAKING-OF.md)**: Claude Code agents, directed by Michael Bishop, and the game measuring every change.

A moveset demo reel is attached to this repository's first release.

This is a non-commercial fan project. Geno and *Super Mario RPG* belong to Nintendo and Square Enix, and *Super Smash
Bros. Melee* belongs to Nintendo and HAL Laboratory. **This repository contains no game data**: no disc files, no
graphics or sounds extracted from either game, and no game builds. You supply your own copies. The player patch on the
release page is the one exception: it carries a compiled build and game-derived sound, applies only to your own disc
image, and is never committed here.

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

He's in VS mode and Training, in the character select's bottom row, right-hand cell. The single-player modes hide
him. His name tag, SMRPG's "♡♪!?", can be typed on VS mode's name-entry screen: the heart and the note are new keys.

## The Forest Maze

One mushroom cap at height 28 over a floor with ledges at ±70: open flanks for the ground game and a platform game only
in the centre. It sits at the left end of the stage select's bottom row, and Random can pick it. Its art is built in
Blender from code with light baked into vertex colours, as Melee's own stages are drawn (8,042 triangles, 868 KB), and it
costs the game less time a frame than Battlefield (7.67 ms against 8.26). `projects/geno/stage/DESIGN.md` and
`SCOPE.md` have the design and every measurement.

## What's here

| Path | What it is |
|---|---|
| `projects/geno/` | Everything specific to Geno: the rig, animations and move scripts (`rig/`), the model built from code in Blender (`model/`), effects (`fx/`), sounds and the sound-bank tools (`sound/`), the music's arrangement sources (`music/`), menu art (`menus/`), the Forest Maze (`stage/`), the challenger silhouette and name-tag glyph tools (`trailer/`), the in-game labs that measure every change (`director/`), research, and the design docs. |
| `tools/machinima/` | The kit that drives the game: `datkit` (C#, on HSDRaw) builds Melee's data files, `build.py` compiles the decomp with a lab director, and `dolphin.py` runs Dolphin headless and logs the game's state. |
| `decomp/geno.patch` | Every change to the decompilation, as one patch against upstream doldecomp/melee (see `decomp/README.md`). All of it sits inside `#ifndef MUST_MATCH`, so the matching build still reproduces the retail game byte for byte. |
| `audio/` | Our own arrangements, rendered as the game plays them: the victory fanfare and the Forest Maze's stage music (`audio/README.md`). |

`projects/geno/HANDOFF.md` is the working manual: the state of the project, the build and test commands, and the facts
learned the hard way about the engine.

## Changes

**Release prep (2026-10-02),** since Refresh 1:
- The Forest Maze is finished: production art built in Blender (art pass 2: scripted geometry, baked vertex colour, the
  floating cap), a moving twilight sky (cloud banks, twinkling stars, fireflies, the Star Road shooting star) wrapped for
  camera orbits, and a stage-music loop with a seamless wrap.
- Geno arrives as Melee's own challengers do: his NEW CHALLENGER silhouette, rendered from his model, and his prize
  screen.
- The ♡ and ♪ glyphs in the game's font and on the name-entry keyboard, for the name tag "♡♪!?".
- The director and film kit: Melee's own type, keying and hard-edit tools, the game camera hand-off, frame timings and a
  lag probe, and new cues for filming (star KOs, slow motion, metal, trophies, enemies, costume changes, HUD modes); an
  option to leave a fresh save's unlocks alone; release scripts (`projects/geno/release/`).
- The music's arrangement sources and the sound-capture tools are packaged here, with the rendered audio.
- How to play (with a player patch), the making-of, and a licence.

**Refresh 1 (2026-09-30):** playtest round 1 (the Whirl as a spiked sun, the Beam's slower charge, down B's early marks,
the Flash rebalanced, longer rocket grabs, the Cannon Charge dash attack, effects for every gun move) and the Forest
Maze's greybox.

**v0.1.0 (2026-09-29):** the first playtest build, with the moveset reel.

## How it was made

Geno was built with Claude Code (Anthropic's coding agent), directed by Michael Bishop. Michael made the design
calls; Claude agents did the engineering, modelling, animation, effects and sound work in parallel, each on its own
branch and sandbox, and verified every change in the running game. [MAKING-OF.md](MAKING-OF.md) tells the story with
the numbers, and the design changelog in `DESIGN.md` records who decided what.

## Licence

Code and tools: MIT. Documentation, art, design and audio: CC BY-NC 4.0. See [LICENSE](LICENSE) for the scope, what
neither covers, and the third-party notices.

## Credits

- The [doldecomp](https://github.com/doldecomp/melee) contributors, whose decompilation makes a new fighter possible.
- [HSDRaw](https://github.com/Ploaj/HSDLib), on which datkit reads and writes Melee's files.
- [Dolphin](https://dolphin-emu.org/).
- Archivo, the typeface used in the review boards (SIL Open Font License, `engine/fonts/OFL-archivo.txt`).
- *Super Mario RPG*'s music is by Yoko Shimomura; the arrangements in `audio/` are ours.
