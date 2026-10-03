# The announcer's "Geno!"

Melee's announcer calls each fighter's name. Geno's is spliced from the announcer's **own recorded calls on your
disc**: cut, pitch- and time-shaped with Praat's PSOLA, level-matched and crossfaded. Nothing is synthesized, cloned or
generated (Michael's call, as a fan work). The call is J from "Jigglypuff", ee from "Pichu", n from "Green team!",
and the long O of "Mario" (round 2, Michael's pick `geno_CD_full`). `NOTES.md` has the method, the candidates, the
checks and the game-format verification.

```sh
projects/geno/sound/announcer/build.sh      # -> $MELEE_WORK/announcer/out/nr_name.ssm (from $MELEE_DISC)
projects/geno/sound/announcer/install.sh    # backs the retail bank up once, then installs; --restore puts it back
```

**Measured (2026-10-02):** from a retail disc, `build.sh` rebuilds the installed bank byte for byte (SHA-1
`ba2e1d699dca...`) in a few seconds.

| File | What |
|---|---|
| `tools/sources.py` | decodes the 20 clips the splice cuts from (`audio/us/nr_name.ssm`, `audio/us/nr_vs.ssm`) into the work folder |
| `tools/splice.py`, `tools/hf0.py` | the splicer (PSOLA through parselmouth, pitch from our own harmonic-sum tracker, correlation-normalised crossfades) |
| `tools/candidates.py`, `tools/final.py`, `tools/hybrid.py` | round 1's five candidates, round 2's C+D hybrids and the delivered take |
| `tools/dspenc.py`, `tools/verify_encoder.py`, `tools/ssm.py` | a Python port of the reference DSP-ADPCM encoder (jackoalan/gc-dspadpcm-encode, MIT), its check, the `.ssm` reader |
| `tools/patch_bank.py` | appends the call to the US bank and points entry 17 (sound 510017) at it |
| `tools/evaluate.py`, `phonecheck.py`, `onetake.py`, `headtohead.py`, `stt.py` | ranking only: Whisper and wav2vec2 transcribe the candidates; nothing they output is used as audio |
| `tools/inject_plan.py`, `phones.py`, `spec.py`, `plotcand.py`, `f0.py` | research and plots |

Paths: `MELEE_DISC`, `MELEE_WORK`, `ANNOUNCER_WORK` (default `$MELEE_WORK/announcer`), `ANNOUNCER_SRC_BANK`.
