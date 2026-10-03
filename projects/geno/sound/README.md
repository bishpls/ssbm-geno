# Geno's sounds

Everything here is code, plus the 25 movement sounds we synthesized (`wav/`, made by `synth.py`). The game audio it works
on (SNES renders from your own *Super Mario RPG* cartridge, Melee's own recordings from your disc) and everything built
from it stay in your work folders, never in git.

| What | Where in the game | Built by | From |
|---|---|---|---|
| His sound bank (bank 55, `geno.ssm`, 62 sounds) and both `smash2.sem` | `audio/geno.ssm`, `audio/us/geno.ssm`, `audio/smash2.sem`, `audio/us/smash2.sem` | `build_bank.sh` | your SMRPG (USA) ROM, your disc |
| The announcer's "Geno!" (sound 510017) | `audio/us/nr_name.ssm` | `announcer/build.sh`, `announcer/install.sh` | your disc |

## The bank, in one step

```sh
projects/geno/sound/build_bank.sh      # MELEE_DISC, MELEE_WORK; SMRPG_ROM (or SMRPG_SFX if already captured)
```

The steps it runs, in order:

1. **`capture/`**: Geno's SNES sounds, rendered from your cartridge dump through the game's own sound driver (Mesen2
   dumps the audio RAM from the attract demo's battle; blargg's snes_spc renders each effect). Skipped when
   `$SMRPG_SFX/geno/nosat/` exists.
2. **`rom_tools/build_sounds_rom.py`**, then **`rom_tools/build_bank.py`**: round 3, the 28 SNES sounds cut and timed for
   Melee and encoded as DSP-ADPCM (`announcer/tools/dspenc.py`), plus the scripts in `smash2.sem`.
3. **`rom_tools/build_bank4.py`**: round 4, the 25 wooden movement sounds (`wav/`, `sounds4.json`) appended; its
   `out4/install.sh` puts them on the disc.
4. **`timed.py`** (SMRPG's timed-hit sounds, 550054-550055), **`gunfit.py`** (the gun sounds cut to their moves,
   550056-550061), **`cheer/survey.py`** and **`cheer/candidates.py`** (the crowd's "Ge-no! Ge-no!", spliced from the
   disc's own chants: Michael's pick, `pc_pc_ns_mr`), then **`cheer/bank.py`** appends them all (550053-550061) and
   installs the bank.

**Measured (2026-10-02):** from the release's captures and a retail disc, `build_bank.sh` reproduces the installed bank
and both `smash2.sem` byte for byte (`geno.ssm` SHA-1 `5b43522c85e6...`) in about 25 seconds. A fresh capture renders
a hair differently: the same lengths and levels (within 0.04 dB), waveform correlation 0.91-1.0 on the tonal sounds,
lower on the noise-driven ones (the swirl, the Flash's explosion), because the attract demo's audio state (the noise
generator, the driver's tick phase) isn't identical from one Mesen run to the next. So a bank built from your own
capture plays the same sounds but has a different hash; `build_bank4.py` notes that and carries on
(`BANK_STRICT=1` makes it an error).

The decomp side (bank 55's slot, its ARAM booking, the id gate `LBAX_GENO_SFX_LAST`) is in `decomp/geno.patch`.

## Tools this needs

The repo's Python (numpy, scipy, soundfile, librosa, pyloudnorm, Pillow), plus:
- Mesen2 2.1.1 (GPL-3), for the capture's audio-RAM dump;
- a C++ compiler, for blargg's snes_spc 0.9.0 (LGPL 2.1; `capture/spcrender/build.sh` fetches it and applies our patch);
- vgmstream-cli (r2117 here), the independent decoder `build_bank.py` checks every encode against;
- for the announcer: praat-parselmouth 0.4.7 (Praat 6.1.38). Its ranking scripts (`evaluate.py`, `phonecheck.py`,
  `headtohead.py`) also use openai-whisper and transformers (wav2vec2), only to compare candidates.

## Other files

- `wiring.py`: the voice table, the sound cues and footfalls in his move scripts.
- `synth.py`: the movement sounds (modal wood knocks, stick-slip creaks, cape flutter, rattles), deterministic per seed.
- `soundaudit.py`, `soundsync.py`, `melee_ref.py`, `abtest.py`, `sheet.py`, `loud.py`, `dsp.py`: checks against
  Melee's own sounds (levels, sync to the animation, A/B files).
