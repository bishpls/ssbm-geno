# Capturing Geno's SNES sounds from your own cartridge

Geno's attacks use *Super Mario RPG*'s own sound effects (Michael's call for this fan work), rendered from **your own
dump** of *Super Mario RPG: Legend of the Seven Stars* (USA, SHA-1 `a4f7539054c359fe3f360b0e6b72e394439fe9df`) through the
game's own sound driver. No sound from the game is in this repo: these scripts make them on your machine.

```sh
projects/geno/sound/capture/spcrender/build.sh       # once: the renderer
projects/geno/sound/capture/capture.sh               # ~40 s: SMRPG_ROM, SMRPG_WORK, SMRPG_SFX (paths.py), MESEN
```

How it works (the full method and the sound-by-sound table are in Geno's sound-bank notes):

1. **The audio state.** Mesen2 2.1.1 runs the cartridge headless (`--testrunner` with `drive.lua`). With no input the
   attract demo reaches a battle at about frame 3960; at frame 4100 the script dumps the 64 KB audio RAM, the DSP
   registers and the SPC700's state. `spcharness.build_spc()` turns that into an SPC image. At that moment the driver,
   the battle sound-effect set and the fixed effect samples are all resident.
2. **Rendering.** blargg's snes_spc 0.9.0 (the accurate DSP) with three small additions (`spcrender/`): a dry switch
   that mutes the echo return, a nosat switch that skips the voice-sum clamp (headroom), and DSP/RAM access. Python
   drives it through the APU ports exactly as the S-CPU does: key everything off, flush the echo, send the effect
   command, render until silence.
3. **Which sounds.** `build_geno.py` lists Geno's sounds by their ROM ids and the game's own sequencing (the Hand
   Cannon's triple trigger, the Blast's retrigger every 6 frames, the Hand Gun's cut at 36 frames), as the battle
   scripts play them, and renders each dry, wet (the battle echo) and without saturation (`geno/nosat/`, what the bank
   uses). `sweep.py` renders every battle effect id (`all/`; the bank's timed-hit sounds come from there).

The ids were identified from the game's battle-animation scripts (disassembled with the Super Mario RPG Randomizer's
`smrpgpatchbuilder`) and checked against SNES footage by spectrogram correlation; that research isn't needed to rebuild.

A fresh capture is close to the release's but not identical bit for bit (`../README.md`, "Measured"): the release's was
made with Mesen2's default random power-on RAM. `capture.sh` now zeroes it (`--snes.ramPowerOnState=AllZeros`), so a
capture is the same on every run; with random RAM, 3 of 3 fresh runs dumped a sound-CPU state that wouldn't render.

| File | What |
|---|---|
| `capture.sh` | the whole capture: Mesen dump, SPC image, `sweep.py`, `build_geno.py` |
| `drive.lua` | Mesen2's Lua driver (holds, screenshots, savestates, the audio-RAM dump); `capture.sh` fills in the work path |
| `spcharness.py` | the SPC image builder and the renderer's Python harness (the driver's port protocol) |
| `sfxparse.py` | reads the ROM's effect tables (for `sweep.py`) |
| `sweep.py`, `build_geno.py` | every battle effect alone; Geno's set |
| `paths.py` | `SMRPG_ROM`, `SMRPG_WORK`, `SMRPG_SFX`, `SPCRENDER_LIB` |
| `spcrender/` | `build.sh` (fetches snes_spc at `ec8ee2b` and builds it with `snes_spc_spcx.patch` and `spcx.cpp`) |

snes_spc is LGPL 2.1; our patch to it is under the same licence.
