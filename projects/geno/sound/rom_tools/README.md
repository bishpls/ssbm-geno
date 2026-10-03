# The bank's tools

Rounds 3 and 4 of Geno's sound bank (bank 55). `../build_bank.sh` runs them in order; each writes to `$SFXBANK`
(default `$MELEE_WORK/sfxbank`), outside the repo.

| File | What |
|---|---|
| `build_sounds_rom.py` | round 3: the 28 SNES captures (`$SMRPG_SFX/geno/nosat`) cut, retimed and levelled for Melee -> `build/NN_NAME.wav`, `build/sounds.json` |
| `grain_retime.py` | the Beam charge's retime: drops whole grains of SMRPG's up-glide train, so the climb peaks on Melee's frame 45 without time-stretching |
| `build_bank.py` | round 3's bank: DSP-ADPCM encode, `geno.ssm`, the scripts in both `smash2.sem` (read from the disc while retail, else `$MELEE_WORK/orig/audio`), a vgmstream cross-check of every entry -> `out/` |
| `build_bank4.py` | round 4: the 25 synthesized movement sounds appended -> `out4/` and `out4/install.sh` |
| `geno_sfx_ids_r3.json` | round 3's id table (names, uses, scripts, sources); round 4 extends it |
| `make_patch.py` | the decomp diff that first booked bank 55 (already in `decomp/geno.patch`) |
| `build_sounds.py` | rounds 1-2 (from SNES video clips, superseded); round 3 reuses its fades, filters and loudness helpers |
| `match.py`, `compare.py`, `sheet.py` | the matching of clips to the clean SNES recordings, and spectrogram sheets (research) |

`build_bank.py` and `build_bank4.py` check their output against the reference build; with a fresh capture round 3
differs (`../README.md`, "Measured") and round 4 notes it. Paths: `SFXBANK`, `MELEE_WORK`, `MELEE_DISC`, `SMRPG_SFX`,
`VGMSTREAM` (the vgmstream CLI).
