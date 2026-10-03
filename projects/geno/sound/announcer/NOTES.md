# GENO! — announcer name call spliced from the Melee announcer's own recordings

Work area: `~/games/melee/work/announcer/` (outside every git repo). Nothing on the disc was modified.
No TTS, voice-cloning or voice-conversion model was used. No paid API was called. Every sample in the candidates
comes from the announcer's recorded clips on Michael's US 1.02 disc. The edits are cuts, Praat PSOLA pitch and
duration changes, gains, and crossfades. The only local models used are recognizers, for judging: Whisper
small.en/medium.en/turbo, and wav2vec2 phoneme CTC `facebook/wav2vec2-lv-60-espeak-cv-ft`.

**Round 2 (current):** Michael listened to round 1. C was the best single take, and he loved D's long Mario "O".
The C + Mario-O hybrids, their ranking and the plan for injecting a take longer than slot 17 are in **§7**.
§1–§6 are round 1.

## 1. Ranking (best first)

| # | file | recipe (J + ee + n + o) | Whisper free (small / medium / turbo) | after real "Falco!" (s / m / t) | P(hit) s/m/t |
|---|------|---------------------------|---------------------------------------|----------------------------------|--------------|
| 1 | `geno_B_peach.wav` | Jigglypuff J + **Peach** ee + "No contest" n and n→o + Falco o | Gino! / Gino! / GINO! | GINO! / Geno! / GINO! | .75 / .96 / .91 |
| 2 | `geno_A_pichu.wav` | Jigglypuff J + **Pichu** ee + "No contest" n and n→o + Falco o | Gino! / Gino! / GINO! | GINO! / GINO! / Gino! | .85 / .99 / .89 |
| 3 | `geno_C_greenN.wav` | as A, but n from "Green team" | GINNO! / Gino! / Gino! | GINA! / GINO! / GINO! | .66 / .97 / .95 |
| 4 | `geno_D_marioO.wav` | as A, but the final o is Mario's (long, 1.22 s) | GINO! / Gino! / GINO! | GINOR! / Gee-Naw! / GINO! | .56 / .97 / .87 |
| 5 | `geno_E_recipe.wav` | the brief's recipe as written: Jiggly J + Pichu ee + Ness n + Falco o | JIMO! / JINGLE! / Jingle! | Jingle! ×3 | .34 / .73 / .04 |

Context files: `geno_A_pichu_after_falco.wav`, `geno_B_peach_after_falco.wav` (the real "Falco!", then 0.4 s of
silence, then the candidate), plus `geno_A_pichu_after_pichu.wav` and `geno_B_peach_after_peach.wav` (each
beside the call its vowel came from). All outputs are 12 kHz mono 16-bit, the bank's native rate. Loudness is
matched to the median of the real calls (RMS −11.3 dB).

"Gino" is the everyday English spelling of /ˈdʒiːnoʊ/, so it counts as a hit. For scale, Whisper gets the
announcer's real character names wrong about half the time: small.en was exact on 15/28 and turbo on 16/28. It
never gets his own "Falco!" right ("Funko", "Fucco", "Focal", "Fulco" ...). Against that baseline, three models giving "Gino/Geno"
in free and in-context transcription is a strong result.

P(hit) is Whisper forced choice. The decoder is teacher-forced to score " Geno!" and its same-sounding spellings
against 38 near-miss strings (Dino, Tino, Gina, Jingle, Jingo, Kino, Juno, "Gee, no", …). The softmax is taken
over that set.

**Why B over A:** the two are within noise on word recognition (18/18 vs 17/18 free-STT hits). B wins on the
"one take" measures. See §4.

**Why E fails:** Falco's "o" carries his /k/ release and formant transition, which every model hears as a /g/:
"Jin-GO", "Jingle". The fix is used in A–D. The n and the whole n→o release come from the announcer's
"**No** contest!", which is a real /n/+/oʊ/, and the cut into Falco's "o" is made later (0.45 s), after the /k/
transition.

## 2. Files, banks and IDs

- **Bank:** `~/games/melee/disc/files/audio/us/nr_name.ssm`. It has 52 mono DSP-ADPCM samples at **12,000 Hz**,
  the base (global) sample ID is **1476** (IDs 1476–1527), and the data size is 335,552 bytes. The
  Japanese-language set is `audio/nr_name.ssm`: 54 samples, base 1491, with its own `audio/smash2.sem`.
- **SFX IDs:** sem bank 51 holds 54 scripts, so the sound IDs are **510000–510053** (bank×10000+index). Script k
  plays sample 1476+k, except for two duplicate scripts. 510037 and 510038 both play idx37 "Game!", and 510048
  and 510049 both play idx47 "Time!". So idx38–47 map to 510039–510048, and idx48–51 map to 510050–510053.
- **Extracted:** `names/nr_name_NN_idSAMPLE.wav` (all 52), `names/labeled/NN_<text>.wav`, and the table
  `names/INDEX.tsv` (idx, sample ID, sfx IDs, CharacterKind, text, duration, whether US code references it).
  Other announcer banks are decoded into `banks/`: nr_select (sample IDs 295–317, "Choose your character" and so
  on), nr_vs (329–335, including **"No contest!"**, "Green team!", "Red team!", "Blue team!"), nr_1p, nr_title,
  the JP nr_name, and main.ssm. STT labels are in `banks/stt_other_banks.tsv`.
- **Who plays the name call:** `gm_80168C5C(CharacterKind)` in `gm_1601.c:4178` (C). It is a switch over kinds
  0..0x1D (the file has Shift-JIS bytes, so plain grep skips it; use `grep -a`) that calls `lbAudioAx_800243F4(510000+k)`. That function picks a per-name "track"
  (the synth group), and default 0xCA is used for unlisted IDs. It is called from the CSS
  (`mncharsel.c:2105/2180/2709`), the results screen (`gmresultplayer.c:1245` → `fn_80168E54`) and the 1P
  splash (`gm_1832.c:439`). Kind → sfx: Captain 510000,
  DK 510001, Fox 510005, G&W 510010, Kirby 510015, Bowser 510016, Link 510018, Luigi 510020, Mario 510021,
  Marth 510022, Mewtwo 510024, Ness 510026, Peach 510027, Pikachu 510029, ICs 510011, Jigglypuff 510013,
  Samus 510030, Yoshi 510031, Zelda 510033, Sheik 510032 (these two switch cases are swapped),
  Falco 510004, Y.Link 510019, Dr. Mario 510002, Roy 510012, Pichu 510028, Ganondorf 510006,
  Master Hand 510025, Giga Bowser 510008. The wireframes (0x1B/0x1C) fall through to no call.
- **Correction to the decomp scaffold:** the CSS icon field (`icons[i].sfx`, 0xC2–0xDA) is **not** the name call.
  Those bank-0 scripts wait 60 ticks and then play main.ssm samples 136–139, which are short crowd shouts
  (STT: "HUAH!", "Ha ha!"). Geno's `0x83D61` therefore only silences that cheer. His name call needs a
  `gm_80168C5C` case (§8.3).

## 3. Method

1. **Decoder:** `tools/ssm.py` parses the .ssm (layout in §5) and decodes DSP-ADPCM. Its output matches the
   recordings (STT reads the names), and every file size reconciles to the header.
2. **Analysis:** this voice defeats the usual pitch trackers. Praat ac and pyin make octave errors and drop
   voicing, because the voice is shouted, processed and reverberant. `tools/hf0.py` is a harmonic-sum F0 tracker
   with a half-harmonic penalty and Viterbi smoothing, checked by hand against harmonic levels. The tracker gives
   the name-call cadence: the stressed syllable is at about 330–370 Hz, and the final syllable drops about 7
   semitones to about 220 Hz, then falls to about 150 Hz in a long reverberant tail (Falco, Pichu, Mario, Kirby,
   Zelda). Plots are in `plots/`.
3. **Segments** (source seconds; output spans are in `geno_candidates.json`):
   - J: Jigglypuff 0.012–0.076. This is the voiced /dʒ/ frication only, with its low-F0 voicing and no /ɪ/. The
     J from "Giant" was tried and sounded like "Dino/Tino" every time.
   - ee: Pichu 0.042–0.156 (recorded at about 345 Hz, so almost no shift is needed, stretched ×1.27) or Peach
     0.055–0.262 (about 272 Hz, so +4.2 semitones, compressed ×0.70). Also tried: Green, Giga, Sheik.
   - n: "No contest" 0.030–0.078, stretched to 75 ms (×1.56). C uses "Green team" 0.207–0.322. E uses Ness
     0.040–0.124.
   - n→o release: "No contest" 0.078–0.160, PSOLA'd to 250→205 Hz. This is the heaviest pitch edit in the call.
     It goes from +3 semitones at its start to −8 at its end, because the source rises while the target falls.
   - o and tail: Falco 0.450–0.817, untouched, with its own pitch, level and reverb tail. D uses Mario 0.43–1.267.
4. **Template:** Falco's own call. The ee follows his "FA" contour with a scoop from the J, like his natural
   onsets: 296→362→349→326 Hz over 145 ms. The n follows his /l/ fall, 318→224 Hz over 75 ms. The o is his
   actual "co".
5. **PSOLA:** Praat Manipulation overlap-add through parselmouth. The pulses come from our tracker, not Praat's.
   The ee keeps its own micro-prosody: only the trend is moved to the template, with the residual capped at ±4%.
   The n and the release follow the smooth template.
6. **Joins:** each side keeps 40 ms of margin. The next segment is aligned by cross-correlation within ±½ period,
   and the cut is snapped to a zero crossing. The crossfade is a correlation-adaptive raised cosine, normalised
   so that fo²+fi²+2r·fo·fi = 1. That avoids both the +3 dB bump an equal-power fade gives aligned audio and the
   dip a linear fade gives unlike sounds. Crossfades are 16 / 14 / 12 / 36 ms (J|ee, ee|n, n|release,
   release|o). The last one is vowel into vowel.
7. **Level and tail:** each segment is gain-matched to Falco's syllable level (the J to Jigglypuff's J/vowel
   ratio). The file ends in the source's own reverb tail with a 25 ms cos² finish, and the whole file is set to
   the bank's median RMS.

Scripts: `tools/candidates.py` (segment inventory, recipes, the exploration grid), `tools/final.py` (builds the
five deliveries and the context files), `tools/splice.py` (engine), `tools/evaluate.py`, `tools/phonecheck.py`,
`tools/onetake.py`, `tools/headtohead.py`. Exploration builds and all metrics are in `cands/` (`eval.json`,
`onetake.json`, `headtohead.json`, `phoneslots.txt`).

## 4. Judgement (objective checks)

**Phone-level check** (wav2vec2 phoneme CTC). This compares the likelihood of each slot's options with the other
slots held at /dʒ iː n oʊ/, so it checks sounds, not spelling. It gives the real "No" /o/ as "o" at 0.58, so "o",
"ɔ" and "ɔː" count as right for the final vowel.

| | dʒ | iː/i | n | back-rounded final |
|---|---|---|---|---|
| B peach | .62 | .91 | .99 | .74 |
| A pichu | .65 | .65 (ɪ .35) | .99 | .51 (ɑː .36) |
| C greenN | .22 (tʃ .26) | .89 | .88 | .35 (aʊ .45) |
| D marioO | .71 | .78 | .84 | .71 |
| E recipe | .46 | .92 | .34 | .79 |

**Seams:** the spectral step is the MFCC distance across ±10 ms, as a percentile of all natural 20 ms steps in the
28 real calls. Natural phone boundaries give 83 for n→o, 98 for ee→n and 97–99 for consonant→vowel; the middle of
a vowel gives 36–78.

- A: J|ee 98, ee|n 99, n|release 57, release|o 55
- B: 94, 99, 52, 50
- C: 98, 79, 86, 61
- D: 98, 99, 52, 88
- E: 98, 100, 98

The pitch across each seam (medians over 5–30 ms each side) moves in the template's direction, with no reversals.
ee|n is −1.3 to −2.0 semitones, n|release is within ±0.4, and release|o is −2.9 (Falco's own fall at that point is
about −1 semitone per 10 ms). Level steps at the seams are ≤ 2.6 dB. The natural n→o release in "No contest" is
itself −1.9 dB.

**Peach vs Pichu, head to head** (`cands/headtohead.json`). Everything is identical except the vowel's source
span. The comparison was repeated over six small build perturbations (n length, J crossfade, vowel length):

| | Pichu (A) | Peach (B) | Peach better in |
|---|---|---|---|
| free-STT hits (3 models × 6 builds) | 18/18 | 17/18 (one "Digno!") | — |
| Whisper forced P(hit), mean | **.915** | .873 | 0/6 |
| phone /iː/ (iː+i) | .81 | **.93** | 6/6 |
| phone final is back-rounded | .55 | **.74** | 6/6 |
| J→vowel seam, spectral percentile | 98 | **94** | 6/6 |
| F0 jump at the J→vowel seam (the scoop from the J's low voicing) | +4.3 st | +5.6 st | — |
| ee→n seam, spectral percentile / F0 | 99 / −1.5 st | 99 / −2.0 st | — |
| vowel HNR (dB) | 11.9 | **6.1** | — |
| PSOLA needed on the vowel | **+0.2 st, ×1.27** | +4.2 st, ×0.70 | — |

Neighbouring texture in the same file: the J has an HNR of 4.4 dB, the release 3.7 and Falco's "o" 3.1. Stressed
vowels in real calls range from 3.8 to 10.2. Pichu's vowel is recorded clean (11.1 dB at steady state) and the
×1.27 stretch lifts it further, so the "EE" is noticeably smoother than the rough syllables around it. Peach's
"ea" is rough like its neighbours.

Verdict: **the Peach vowel sounds more like one take**. It gives a spectrally smoother onset seam and a consistent voice
texture, and the phoneme recognizer is more certain it is /iː/ and that the final vowel is an announcer "o". The
Pichu vowel needs almost no pitch processing and does slightly better with Whisper. Both are clear "GENO!"s.
Listen to the two `*_after_falco.wav` files side by side to make the final call.

## 5. Adding the call to the game (research only; no disc files were touched)

**.ssm layout** (big-endian; checked against all 110 .ssm files, US and JP: data offset + data length equals the file size)

```
0x00 u32 entry_table_len (bytes)    0x04 u32 data_len (bytes)
0x08 u32 sound_count                0x0C u32 base_sample_id   (global ID of entry 0)
0x10 per sound: u32 channel_count, u32 sample_rate, then per channel 0x40 bytes:
     u16 loop_flag, u16 format(0=ADPCM), u32 loop_start_nibble, u32 end_nibble, u32 start_nibble,
     s16 coefs[16], u16 gain, u16 pred_scale, s16 yn1, s16 yn2, u16 loop_ps, s16 loop_yn1, s16 loop_yn2, u16 pad
data at align32(entry_table_len + 0x10); nibble addresses are relative to the data start (8-byte frames:
1 header byte + 14 nibbles). nr_name samples are packed back to back; the data ends in 16 bytes of padding.
```

Loader (`synth.c`, `HSD_SynthSFX*LoadCallback`): it reads the first 0x20 bytes, sends `data_len` to the bank's
ARAM cursor, and asserts *"Can't load SFX file; bank(id=%d) buffer overflow"* if that does not fit. It adds the
ARAM base to every address and registers each sound as `base_sample_id + i` in a 32-bucket hash. A lookup takes
the first matching ID, and newer loads are put in front.

**.sem layout** (`audio/us/smash2.sem`)

```
u32 0; u32 0; u32 bank_count(55); u32 first_script[55]; u32 total_scripts(4035); u32 script_offset[4035] ...
script = 32-bit commands, opcode in the top byte: 00 wait(ticks) 01 play(global sample ID) 02/03 loop
04/05 priority 06/07 volume 08/09 pan 0C/0D pitch(cents) 10-15 aux/mix sends 0E end 0F end+key-off; FD = ignored.
```

A sound ID is resolved as `bank = id / 10000`, `script = first_script[bank] + id % 10000`, and
`HSD_AudioSFXStartParam` rejects any index past that bank's last script. Each name-call script is
`01 <sample> | FD | 10 000030 | 04 00000F | 06 0000E5 | 0E`: play, aux send 0x30, priority 15, volume 0xE5.

**Recommended: reuse sfx 510017 (sample 1493).** In the US set that slot is the Japanese "Koopa!" leftover, and
510009 (sample 1485) is "Giga Koopa!". In the JP set the same two slots hold the English "Bowser!" and
"Giga Bowser!". So in both languages they are the other language's Bowser calls. I found no reference to 510003,
510009, 510014, 510017, 510038 or 510049 in the US code or data: a grep of every immediate and `.4byte` in
`build/GALE01/asm`, and the `lbAudioAx_800243F4` switch does not list them either. The steps:

1. Encode the chosen WAV as 12 kHz mono GC DSP-ADPCM (for example gc-dspadpcm-encode, DSPADPCM or VGAudio). That
   takes about 5.1 KB for A, B, C or E and about 8.4 KB for D.
2. In `audio/us/nr_name.ssm`, write the data **in place** into slot 17's 5,984 bytes (A, B, C and E fit; pad with
   silence frames). Then rewrite only that entry's header (end nibble, coefs, pred_scale; yn1 = yn2 = 0;
   loop_flag = 0). The file size, `data_len`, every other address, the FST and ARAM are unchanged. D does not fit
   slot 17 or slot 9 (7,672 bytes), so it would have to be appended (next item).
3. No change to the sem is needed. Script 510017 already plays sample 1493 with the name-call parameters.
4. Code: one `case CKind_Geno: lbAudioAx_800243F4(0x7C841);` in `gm_80168C5C` (`gm_1601.c`), which covers the
   CSS, results and 1P paths. The exact snippet is in §8.3. Optionally give Geno's CSS icon a real crowd cheer (for
   example 0xC6) in place of `0x83D61`.
5. For the Japanese-language setting, repeat step 2 on `audio/nr_name.ssm`, slot 17 (its sample 1508).

**Appending a new sample or ID (harder):**
- Global sample IDs are contiguous across banks: nr_name owns 1476–1527 and **1pend.ssm starts at 1528**. A 53rd
  sample would collide with it (the hash plays whichever bank loaded last). You would have to renumber the bases
  of 1pend, last and end (+1) and the six `01` commands in sem banks 52–54.
- A new sfx 510054 needs a 55th script in sem bank 51. That shifts `first_script[52..54]`, `total_scripts` and all
  later script offsets. It also needs the DOL table `s32_arr_803BB8D4[51]` raised from 0x7C865 to 0x7C866,
  because `lbAudioAx_80023130` and `lbAudioAx_800230C8` map sound IDs to banks with it.

**Size limits:**
- ARAM budget: the DOL's per-bank table `offsets_arr_803BC4E4[51]` is **348,160 bytes** for nr_name. It holds
  the larger of the JP and US sizes and feeds the bank-memory accounting. US data uses 335,552, so there are
  12,608 bytes of headroom, about 1.84 s of 12 kHz ADPCM. Going past it risks the ARAM overflow assert when
  nr_name loads next to other banks.
- Other limits: the sem index within a bank must stay below 10,000, and the play opcode carries a 24-bit sample
  ID.
- A file that grows needs an ISO rebuild (FST offsets). An in-place, same-size replacement does not.

## 6. Uncertainties

- **I can't listen.** I cannot play audio. Every judgement here comes from STT, a phoneme model and signal
  measures. Michael's round-1 listen (C best, D's O loved) overrides the §1 ranking.
- **The judges are imperfect.** Whisper and the phoneme model are shaky on this voice. The phoneme model labels
  the real Jigglypuff J mostly /j/, and Whisper misses about half the real names. Differences below about 0.05 in
  P(hit) are noise.
- **Pitch tracking is hard on this voice.** Octave traps and reverb in the tails make the seam pitch figures
  approximate (±1 semitone).
- **The final vowel is open.** The phoneme model hears it as /ɔ/ (or /ɑː/ for A), not /oʊ/. The announcer's own
  "o" is monophthongal (the controls score "o"), so this is probably his accent, but it is the least certain
  sound.
- **Unused-slot claim.** "No references to 510017/510009" rests on grepping the decomp's immediates and data. An
  ID computed at runtime (base + offset from a table I did not find) is not fully ruled out. I did not test in
  Dolphin.
- **Not tested:** the DSP-ADPCM re-encode (the round trip of our 12 kHz PCM), and the ISO rebuild path.
- **main.ssm 136–139** being crowd cheers rests on STT of short clips.

## 7. Round 2: C's head with Mario's long "O"

### 7.1 Build

Every variant is built the same way up to the O:

- **The head is C's, exactly.** The first 0.289 s (the Jigglypuff J, the Pichu ee and the "Green team" n) match
  `geno_C_greenN.wav` to within 1 LSB. The same segments go through the same processing, and the gain and DC are
  matched to C over that span.
- **The O is the announcer's "Mario" call from 0.43 s to its end at 1.267 s.** Its pitch glides from 242 Hz down to
  about 90 Hz at a steady level of about −10 dB until 1.05 s, then decays naturally at about −60 dB/s.
- **The n→o release** is the same "No contest" piece as in C. It is PSOLA'd 250→240 Hz so it meets Mario's O at
  242 Hz. In the bridge it goes 250→205 Hz, exactly as in C.
- **Compression** is a Praat PSOLA duration tier with the recorded pitch preserved. The glide keeps its shape and
  simply runs faster.

**Fix found in testing:** on a duration-only edit, Praat's own pitch analysis octave-jumped in Mario's creaky tail,
and PSOLA shifted that tail up an octave. `splice.psola` now puts our tracker's pitch in the Manipulation for
duration-only edits. The fix does not affect any round-1 file: rebuilding A and C reproduces them to within 1 LSB.

Builder: `tools/hybrid.py` (`python tools/hybrid.py` builds the exploration grid into `cands/CD_*`;
`python tools/hybrid.py deliver` builds the deliverables and context files). Metadata is in `geno_candidates.json`.
The `cands/CD_*` grid files are exploration builds. The trim and bridge rows predate a 0.06 dB head-level fix, and
the delivered files are the ones that count.

### 7.2 Variants explored (10) and why four were kept

Whisper hits count Gino/Geno/GINNO/GEE-NOOO. The seam percentile is for the join into the O. For the bridge it is
the Falco→Mario join; its release→Falco join scores 52. For tail decay, natural calls range from −21 to −84 dB/s.

| variant | length | O treatment | free (s/m/t) | after "Falco!" (s/m/t) | mean P(hit) | seam % | tail dB/s |
|---|---|---|---|---|---|---|---|
| **bridge** (b47_66) | 1.00 s | C through Falco's o 0.45–0.47 → Mario's o from 0.66 (pitch match 184 Hz, 40 ms crossfade) | GINO / Gino / Gino | GINO / GENO / GINO | .92 | 52 → 89 | −67 |
| b49_72 | 0.96 s | Falco 0.45–0.49 → Mario from 0.72 | GINO / Gino / Gino | GINO / GINO / Gino | .90 | 62 → 87 | −65 |
| b52_78 | 0.94 s | Falco 0.45–0.52 → Mario from 0.78 | **GINA** / Gino / Gino | GINO / GINO / GINO | .89 | 62 → **71** | −62 |
| **full** | 1.22 s | Mario's o untouched (D's O) | GINNO / Gino / GINO | GINO / GEE-NOOO / GINO | .86 | 90 | −61 |
| **100** (u100) | 1.00 s | whole o ×0.74 | Gino ×3 | GINO / GENO / GINO | .90 | 84 | −73 |
| c100 | 1.00 s | body ×0.65, natural decay | Gino ×3 | GINO / **Genome** / GINO | .92 | 90 | −58 |
| t100 | 1.00 s | trimmed with a 150 ms fade | GINNO / Gino / Gino | **GINAW / Gee no** / Gino | .91 | 90 | **−144** |
| **090** (c90) | 0.90 s | body ×0.49, natural decay | Gino ×3 | GINO / **Genome** / GINO | .93 | **72** | −68 |
| u90 | 0.90 s | whole o ×0.62 | Gino ×3 | GINO / **Genome** / GINO | .93 | 88 | −62 |
| t90 | 0.90 s | trimmed with a 150 ms fade | GINNO / Gino / Gino | **GINAW / Gee no** / Geno | .93 | 90 | **−160** |

Reference, round-1 C: GINNO / Gino / Gino alone; GINA / GINO / GINO after "Falco!"; mean P(hit) .86; seam 61.
Round-1 D: seams 99 (ee|n from "No"), then 52 and 88.

- **Trims are out.** A gain fade cannot imitate his decay: it falls at −144 to −160 dB/s, about twice as steep as
  any real call, and Whisper medium hears "Gee no" after it.
- **Does the Falco bridge smooth the join?** Only partly. It moves the jump from release→vowel to vowel→vowel at a
  pitch match, and the worst seam drops from 90 to 87–89 (to 71 when more of Falco's o is kept, but small.en then
  hears "GINA"). It does keep C's /n/: the phoneme model gives n = .91 for the bridge (C: .88), but only .44–.58
  for every direct release→Mario build without Falco's o. The cost is that its final vowel scores "aʊ" .74, so check by
  ear that the O doesn't turn into "ow".
- **Pitch across the joins moves with the template in every deliverable:** ee|n −1.7 st, n|release −0.5 to −0.8 st,
  release|Mario −0.7 to +0.1 st, and in the bridge Falco|Mario −2.1 st over 60 ms, which is Falco's own fall rate.
  In the compressed builds the O's biggest 10 ms pitch step is −1.9 st in 090 at 0.41 s. That is Mario's own
  −0.9 st step at 0.44 s, played twice as fast. 100 shows a single −3.8 st step at 0.87 s, in the sparse, creaky part
  of the decay, which looks like tracker noise. (Tracker floor 85 Hz.)

### 7.3 Ranking (deliverables)

| # | file | length | why |
|---|---|---|---|
| 1 | `geno_CD_bridge.wav` | 1.00 s | 6/6 Whisper hits (alone and after "Falco!"); mean P(hit) .92; keeps C's clear /n/ and C's own release→o join (52); natural tail (−67 dB/s, the median of the real calls) |
| 2 | `geno_CD_100.wav` | 1.00 s | 6/6 hits; Mario's O alone, uniformly ×0.74; seam 84; tail −73 |
| 3 | `geno_CD_full.wav` | 1.22 s | 6/6 hits (medium in context: "GEE-NOOO!"); D's O untouched; seam 90; lowest small.en P(hit) (.65) |
| 4 | `geno_CD_090.wav` | 0.90 s | best mean P(hit) (.93) and the smoothest direct join (72), but medium in context hears "Genome!" and the glide runs twice as fast |

Context files (the real "Falco!", 0.4 s of silence, then the candidate): `geno_CD_bridge_after_falco.wav`,
`geno_CD_100_after_falco.wav`, and `geno_CD_full_after_falco.wav`, added because it is the O Michael liked.

**Audition first:** `geno_CD_bridge_after_falco.wav` against `geno_CD_full_after_falco.wav`. These are the
objective pick and the untouched long O. Listen for "ow" at the bridge's Falco→Mario handoff (0.40 s into the call)
and for a "Gee… no" split in the full take. If the full O is right but too long, `geno_CD_100` is the same O at
1.0 s. `geno_CD_090` is only worth hearing if 0.9 s matters.

### 7.4 Injecting a take longer than slot 17 (research and plan only; the disc is untouched)

**What the loader does** (verified in `synth.s`, `HSD_SynthSFXSampleLoadCallback`):

1. It copies each sound's `nch, rate, channel[0x40]` block to a node.
2. For every channel it adds `2 × (bank ARAM base)`, in nibbles, to three fields: loop_start (+0x04), end (+0x08)
   and current (+0x0C). The decomp's `if (e + 0x10 != NULL)` is a pointer test that is always true (`addic. r0,
   r4, 0x10; beq`), so loop_start is always relocated too.
3. At play time, `AXSetVoiceAddr` takes channel +0x00..0x13, `AXSetVoiceAdpcm` takes +0x10..0x37 (coefs, gain,
   ps, yn1, yn2) and `AXSetVoiceAdpcmLoop` takes +0x38..0x3D.

So all addresses in the file are nibble offsets from the start of this file's data block, and entry 17 can point
anywhere inside it.

**Conventions every existing entry follows** (checked on all 106 entries, US 52 + JP 54):

- start ≡ 2 (mod 16), i.e. each sample begins on an 8-byte frame;
- loop_start = start;
- end = 2B + nibbles(N) − 1, where B is the data byte of the first frame and nibbles(N) = 16·⌊N/14⌋ +
  (N mod 14 ? N mod 14 + 2 : 0);
- ps = that first frame's header byte;
- gain = yn1 = yn2 = 0, loop_ps = loop_yn1 = loop_yn2 = 0, loop_flag = 0, format = 0.

**Recommended: append, then repoint entry 17.** File `audio/us/nr_name.ssm`, all values big-endian:

1. Encode the chosen WAV (12 kHz mono, as delivered) with a GC DSP-ADPCM encoder that writes the standard 0x60-byte
   `.dsp` header, such as gc-dspadpcm-encode, VGAudio or DSPADPCM. The coefficients and the initial predictor/scale
   come from that header. They are specific to the encode and cannot be precomputed.
2. Append the encoded frames (from the `.dsp` body at 0x60; frames × 8 bytes) at data byte **B = 335,552**. That is
   file offset 0xEC0 + B = **0x52D80**, the current end of file, after the existing 16 zero pad bytes. Zero-pad to
   a multiple of 32 bytes.
3. Header 0x04 `data_len` = 335,552 + that padded size.
4. Entry 17's channel, file **0x4E0–0x51F** = `.dsp` header bytes 0x0C–0x4B: loop_flag, format, sa, ea, ca,
   coefs[16] (0x4F0–0x50F), gain (0x510), **ps (0x512)**, yn1 and yn2 (0x514/0x516), loop ps/yn1/yn2
   (0x518–0x51D), pad. Then add 2B = 671,104 to **0x4E4** (loop start), **0x4E8** (end) and **0x4EC**
   (current). 0x4D8 (nch 1) and 0x4DC (rate 12,000) stay.
5. Nothing else changes: count 52, base ID 1476, the entry-table length, the data offset 0xEC0, the sem
   (510017 already plays sample 1493 with the name-call parameters) and every other entry.
6. Code: the `case CKind_Geno` in `gm_80168C5C`; see §8.3.

**Maximum and alignment:**

- **Budget:** data_len ≤ **348,160**, the DOL's `offsets_arr_803BC4E4[51]`, which is the ARAM the scene loader
  books for nr_name (`fn_800268B4` / `fn_800267B0` load and evict banks by these booked sizes). The synth DMAs the
  file's real data_len, so going over under-books ARAM and risks *"Can't load SFX file; bank(id=2) buffer
  overflow"*. That leaves **12,608 B = 1,576 frames = 22,064 samples = 1.839 s**.
- **Frames:** each sample must start on an 8-byte frame (start nibble ≡ 2 mod 16).
- **data_len:** a multiple of 32. That is the ARAM DMA and DVD read granularity, and the next bank's ARAM base
  follows this one.
- **File length:** exactly 0xEC0 + data_len, because the DVD read of data_len must not run past EOF. The entry
  table does not change, so the data offset stays 0xEC0.
- **Raising the budget:** the decomp DOL is rebuilt for Geno anyway, so the budget can be lifted by raising
  `offsets_arr_803BC4E4[51][0]`. That makes bank evictions a little more frequent.
- **Repacking:** this project boots the extracted disc folder in Dolphin, which builds the FST at boot, so a longer
  file needs no repack there. A distributable ISO needs an FST-aware rebuild. Keep a pristine copy of the file
  before patching.

**No-growth alternative for takes up to 1.119 s:** US slot 9 ("Giga Koopa", the Japanese name, which the US game
never plays; same evidence as slot 17) owns 7,672 B at data byte 68,760. Write the take there, pad the rest of the
region with zero frames, and point entry 17 at it (start = loop_start = **137,522**). data_len, file size and every
other entry stay unchanged. Entry 9 can be left alone. Bridge, 100 and 090 fit; full (8,360 B) does not.

**Japanese setting** (`audio/nr_name.ssm`, base sample 1491, its own sem): there is no headroom, because its
data_len is exactly 348,160. Its slot 9 (English "Giga Bowser", never played under the JP setting) holds 8,544 B at
data byte 67,888, i.e. 1.246 s, so every variant, full included, fits in place with entry 17 at start **135,778**.

**Byte budget per deliverable** (from `tools/inject_plan.py`, which only reads the disc files; output in
`cands/inject_plan.txt`):

| file | samples | ADPCM bytes | slot 17 (5,984) | US slot 9 (7,672) | US append: data_len / file size / budget left | entry 17 end nibble if appended | JP slot 9 (8,544) |
|---|---|---|---|---|---|---|---|
| geno_CD_bridge | 12,020 | 6,872 | no | yes (end 151,257) | 342,432 / 346,208 / 5,728 | 684,841 (0xA7329) | yes (end 149,513) |
| geno_CD_100 | 12,044 | 6,888 | no | yes (end 151,285) | 342,464 / 346,240 / 5,696 | 684,869 (0xA7345) | yes (end 149,541) |
| geno_CD_full | 14,625 | 8,360 | no | **no** | 343,936 / 347,712 / 4,224 | 687,818 (0xA7ECA) | yes (end 152,490) |
| geno_CD_090 | 10,843 | 6,200 | no | yes (end 149,912) | 341,760 / 345,536 / 6,400 | 683,496 (0xA6DE8) | yes (end 148,168) |

For every appended variant, start = loop_start = 671,106 (0xA3D82).

**Uncertain or untested:**

- the encoder round trip (12 kHz PCM → ADPCM);
- whether the ARAM prefetch past `end` matters. I believe it doesn't: the voice stops at `end`, and the bytes after
  it are zero padding;
- the slot 9 / slot 17 "never played" evidence (a grep, as in §6);
- none of it has been run in Dolphin.

## 8. Round 3: `geno_CD_full` in the game's format (Michael's pick)

### 8.1 Encoder and verification

`tools/dspenc.py` is a line-by-line Python port of the reference DSP-ADPCM encoder in jackoalan/gc-dspadpcm-encode
(`grok.c`, MIT): `DSPCorrelateCoefs` for the eight coefficient pairs and `DSPEncodeFrame` for the frames. It keeps C
integer semantics throughout: truncating division, arithmetic shifts, `lround`, and the `0.4999999f` rounding
constant. The frame loop is `main.c`'s: 14-sample frames, the last one zero-padded, history carried from each
frame's decoded samples.

To check the port, the reference `grok.c` was compiled from source in the scratchpad (`refenc`, a harness around
`grok.c`). Nothing from it was kept. Run `REFENC=<path> python tools/verify_encoder.py`; results are in
`out/encoder_verification.json`.

| check | result |
|---|---|
| Python port vs compiled reference C, on geno_CD_full and three decoded bank clips (Falco, Mario, Pichu) | coefficients and **every frame byte-identical** (1045/1045, 701/701, 1087/1087, 613/613 frames) |
| geno_CD_full: encode → decode vs the 12 kHz source | **SNR 32.02 dB** (rms error 240 LSB, peak 2832); 14,625 samples → 1,045 frames = 8,360 B; ps = 0x25 |
| Re-encoding the game's own clips (decode → fresh encode → decode) | SNR 34.4 / 33.2 / 35.7 dB (Falco / Pichu / Mario), the same quality class as Geno's 32.0 dB |
| Frame encoder with the **game's stored coefficients** on our decode of the stored clips | reproduces **691/701, 609/613, 1058/1087 stored frames bit for bit**. That would be impossible if our nibble order, sign, rounding or history convention were wrong. The rest are frames where the reference's greedy scale search stops one step below the scale in the game's data. The header ps equals the first frame byte in every entry. |
| Independent decoder: vgmstream r2117 (its own HAL .SSM parser and DSP decoder) | **52/52 streams bit-exact** vs our decoder, on both the original and the patched bank. Patched stream 18 vs the source WAV: SNR 32.02 dB. vgmstream stops 1–3 samples earlier; that is its own sample-count rounding. |

### 8.2 Patched bank: `out/nr_name.ssm`

Built by `tools/patch_bank.py` from `disc/files/audio/us/nr_name.ssm`, which was read and never written. Full report
in `out/patch_report.json`.

- **Original:** 339,328 B, SHA-1 `17d1619185bf043bebe205055ad241e183754c0b`.
- **Patched:** 347,712 B, SHA-1 `ba2e1d699dcad375b41028fc1544eae52cae43a5`.
- **Appended data:** 8,360 B of ADPCM plus 24 B of zero padding at data byte 335,552 (file 0x52D80–0x54E3F).
- **data_len:** 335,552 → **343,936**. That leaves 4,224 B of the 348,160 B the DOL books for this bank.
- **Entry 17** (file 0x4D8; channel at 0x4E0):
  - loop_flag 0, format 0;
  - loop_start = start = **671,106** (0xA3D82), end = **687,818** (0xA7ECA);
  - coefs (-424,-178) (2664,-1242) (1736,-881) (3492,-1739) (362,-559) (2809,-1021) (1666,45) (3508,-1590);
  - gain 0, **ps 0x25**, yn1 = yn2 = 0, loop ps/yn 0.
- **Read back with `tools/ssm.py`:** entry 17 decodes to 14,625 samples, identical to the encoder's own decode, at
  SNR 32.02 dB vs the WAV.
  - The other 51 entries are **byte-identical** (51/51) and decode identically (51/51).
  - The old data region (335,552 B) is byte-identical.
  - The only bytes that differ inside the original's length are 0x6–0x7 (data_len) and 0x4E5–0x513 (entry 17's
    channel block). Everything else is the appended tail.
- **Also written:** `out/geno_CD_full.dsp`, a standard 0x60-header .dsp of the same encode, for other tools.

**Install:** run `out/install.sh` by hand; it has not been run.

- It checks the SHA-1 of the patched file and of the disc file.
- It backs the original up once to `~/games/melee/work/orig/audio/us/nr_name.ssm`, a subfolder because the JP bank
  has the same file name.
- It refuses to proceed if the disc file is neither the original nor the patch.
- It copies the patch in and verifies the copy.
- `install.sh --restore` puts the original back.

The JP-language bank (`audio/nr_name.ssm`) is not patched. See §7.4 (slot 9 in place) if the JP setting needs it.

### 8.3 Code side (not applied; the decomp is untouched)

- **The sound ID** is 510017 = **0x7C841** (bank 51 × 10000 + script 17). Script 510017 already plays sample 1493
  = entry 17 with the name-call parameters. It lies inside nr_name's range {0x7C830, 0x7C865} in
  `s32_arr_803BB8D4`, and `HSD_AudioSFXStartParam` accepts it (script 17 of 54).
- **Play it the way retail names are played:** `lbAudioAx_800243F4(0x7C841)`. 0x7C841 is not one of that function's
  track cases, so it gets the default synth group 0xCA. No other name uses 0xCA, so a second Geno call cuts off the
  first, as with other names.
- **All name calls go through one C function:** `gm_80168C5C` in `src/melee/gm/gm_1601.c:4178-4265`, a switch over
  CharacterKind 0..26 and 29. It has no case for 0x22, so Geno is silent today. `CKind_Geno` = 0x22
  (`ft/forward.h:176`). Its callers:
  - the CSS: `mncharsel.c:2105` (`mnCharSel_8025FB50`), `:2180` (`mnCharSel_8025FDEC`) and `:2709-2710`
    (`mnCharSel_CursorThink`);
  - the results-screen winner call: `gmresultplayer.c:1245` → `fn_80168E54` (`gm_1601.c:4268`, which does the
    Zelda/Sheik swap, then calls `gm_80168C5C` in non-team matches);
  - the 1P VS splash: `gm_1832.c:439`.

  So **one edit covers every path.** Add a case at the end of the switch in `gm_1601.c`, after `case 29:` (line
  4263):
```c
    case 29:
        lbAudioAx_800243F4(0x7C838);
        break;
#ifndef MUST_MATCH
    case CKind_Geno: /* animation-pipeline: "GENO!", nr_name.ssm entry 17 (out/nr_name.ssm) */
        lbAudioAx_800243F4(0x7C841);
        break;
#endif
    }
}
```
  `gm_1601.c` contains Shift-JIS bytes: edit it with a tool that preserves the file's encoding (see the machinima
  README note on Shift-JIS). CKind_Geno is visible there, since the file already uses `CharacterKind`.
- **The CSS icon's own sound stays `0x83D61`** (key-off, silent). That field is a separate delayed bank-0 sound
  (scripts 0xC2–0xDA play main.ssm samples 136–139, short crowd shouts), not the name call. It could become e.g.
  0xC6 to match the other icons.

## 9. Geno's own sound bank (research and plan only)

Sources: `lb/lbaudio_ax.c` (written AX below), `sysdolphin/baselib/{axdriver,synth}.c`, `ft/ftaction.c`,
`ft/ft_0877.c`, `ft/ft_0881.c`, `gm/gmvs.c`, `mn/mncharsel.c`, and the disc's `smash2.sem`. Line numbers are at `ext`
HEAD 670c443 plus local edits.

### 9.1 How Melee loads a fighter's bank

- **Kind → bank.** `lbl_803BB3C0[CharacterKind]` (AX:128-143) = {bank byte, u64 bank bit}. Only `.x8`, the bit, is
  ever read, by `lbAudioAx_80026E84` (AX:2009-2015). The scaffold maps Geno to `{0x12, 0x40000}` = mario.ssm.
- **Per match.** `gm_Scene_Vs_OnEnter` → `fn_8016E730` (gmvs.c:1994-2025) → `lbAudioAx_8002785C` (AX:2178-2220).
  It ORs `80026E84(ckind)` for every occupied slot, adds the stage's bank (`80026EBC`) and a few special cases
  (Kirby opponents in 1P add kirbytm; two stages add Fox/Falco), and then runs:
  1. `80026F2C(0xC)`: clears the fighter and stage requests.
  2. `8002702C(0xC, mask)`: requests the new set.
  3. `80027168`: accounts, evicts, and queues async `HSD_SynthSFXLoad`s into synth bank 2.
  4. `80027648`: blocks until all are loaded, then locks them.

  CSS exit (mncharsel.c:5522-5557, gmvsmelee.c:129-148) starts the same loads early. Other modes use the same
  pattern.
- **Residency is a cache.** Wanted banks load. Unwanted ones stay until space is needed, then are evicted by class
  (`s32_arr_803BB5D0[i][2]`; fighters are 3) and index (`fn_800267B0`, AX:1870-1895), followed by
  `HSD_SynthSFXBankDeflag(2)`. The accounting uses the *booked* size `offsets_arr_803BC4E4[i][0]`, not the file.
  The synth separately asserts on a real overflow (synth.c:259-264).
- **Per-bank tables**, 0x38 rows each, with row 55 a zero sentinel:
  - `s32_arr_803BB5D0` = {budget class, load priority, eviction class, size-variant threshold};
  - `s32_arr_803BB8D4` = {first, last sound ID};
  - `offsets_arr_803BC4E4` = {booked ARAM bytes, flag}. The flag is never read; it is 1 where the US and JP files
    differ.
- **Bank-group masks** (AX:2032-2095): the fighter group (flag 4) is `0x00800003FFFFFFC0`, i.e. banks 6–33 **plus
  bit 55**. HAL left a fighter slot at 55, but the apply loops stop at 54 (`ARRAY_SIZE(...) - 1`).
- **smash2.sem → samples.** Layout: `0, 0, bank_count (55), first_script[55], total (4035), ptr[4035], 0`, then the
  scripts (pointers are file offsets, ascending). A script is 32-bit commands with the opcode in the top byte.
  - `01` plays a *global* sample ID (24-bit, = the .ssm base + index).
  - The other opcodes set aux send, priority, volume, pan and pitch (`0C`); `0E` ends.
  - Mario: 94 scripts over his 32 samples, many of them pitch variants. A typical script is
    `01 smp | FD smp | 10 aux | 04 prio | 06 vol | 0E`.
- **The language folder is global:** `/audio/us/` when the saved language is US, else `/audio/`
  (`setup_audio_lang`, AX:2222-2237). Every bank and the sem exist in both folders.
- **ARAM budget**, set at init (AX:2427-2447). Synth bank 2 (fighters and stages) = the largest class-3 bank
  (nr_select 239,264) + the **four largest class-4 banks** (pikachu 613,088 + falco 599,712 + zs 590,176 + kirby
  586,208) + the largest class-5 bank (last 663,136) = **3,291,584 B**. All SFX ARAM totals 6,248,864 B, and the rest
  of ARAM is the game's ARAM heap.

### 9.2 Recommendation: a new bank 55, `geno.ssm`

Alternatives considered:

- **Append to mario.ssm** (the scaffold's bank): no. Sample IDs are global and contiguous per file, and Marth starts
  at 815, right after Mario's 783–814. Growing Mario would renumber 36 later banks' bases and 1,916 of the sem's
  4,035 play commands. Mario would also carry Geno's ARAM.
- **Extend end.ssm** (bank 54): no. It is permanent (class 1, synth bank 1), so Geno's sounds would hold ARAM all
  session, and 540001 (0x83D61) is the engine's key-off sentinel.
- **Replace any existing bank:** no, it breaks that fighter, stage or mode.

A new bank 55 moves nothing:

- Global sample IDs continue after end.ssm's 1533, so **1534+**.
- Its sem scripts go after script 4034.
- Its sound IDs are **550000 + k** (0x86470 + k).
- The fighter-group mask already includes bit 55.

**New files:** identical copies in `audio/` and `audio/us/`.

- `geno.ssm`: header {entry-table length, data_len, N, **base 1534**}, N 0x48-byte entries, data at
  align32(header), data_len a multiple of 32. Mario's clips are 32 kHz mono. Encode with `tools/dspenc.py`
  (verified in §8.1) and write the file the way `tools/patch_bank.py` writes entries.
- `smash2.sem` (both):
  - set bank_count (offset 8) 55 → 56 and insert `first_script[55] = 4035`;
  - set total 4035 → 4035 + M and append M pointers;
  - add 4·(1+M) to every existing pointer;
  - append the M scripts at the end.
  
  About 28 B per script; the sem sits in main RAM (the audio heap).

**DOL edits** (`lbaudio_ax.c`, under `#ifndef MUST_MATCH`):

1. `ssm_files[]`: `"geno.ssm"` at index 55; the NULL moves to 56.
2. **Move the bank count and "none" sentinel from 55 to 56.**
   - Grow the [0x38] arrays to [0x39]: AX:115-119 (the five state arrays), AX:145 `s32_arr_803BB5D0`, AX:237
     `s32_arr_803BB8D4`, `offsets_arr_803BC4E4`, and `used[56]` → [57]. Row 56 becomes the zero sentinel row
     (`{0x83D60, 0x83D60}` and booked size 0).
   - Change `< 55` → `< 56` at AX:684, 1859, 1879, 1905, 1948, 1967, 1983, 2100, 2124, 2136, 2156, 2162, 2257 and
     2514; `< 56` → `< 57` at 2469.
   - Also change `800230C8` (`i >= 55`, AX:389), `80023130` (loop AX:405, `return 55` AX:413) and `80023220`
     (`idx < 55`, AX:418).
   - In `fn_80023254` (AX:424-460), the empty marker 55 → 56 and the bounds 55/56 → 56/57. The budget sort relies
     on the sentinel row's booked size being 0.
   - `80026F2C`/`8002702C` use `ARRAY_SIZE-1` and follow automatically.
   - **Leave `80026EBC`'s `== 55` (AX:2026) alone.** That is the stage table's own "no bank" value, and no stage
     maps to Geno.
3. **Rows for bank 55:**
   - `s32_arr_803BB5D0[55] = {0x04, 0x02, 0x03, M}`: fighter class, load priority 2, eviction class 3, no size
     variants;
   - `s32_arr_803BB8D4[55] = {550000, 550000 + M - 1}`;
   - `offsets_arr_803BC4E4[55] = {data_len of geno.ssm, 0}`.
4. `lbl_803BB3C0[CKind_Geno] = {0x37, 1ULL << 55}`, replacing the scaffold's Mario bank.
5. **Sound-ID gates:**
   - `lbAudioAx_800237A8` (AX:571) silences every ID ≥ 540001, and this is the path for script command 0x11
     behavior 0 (`ft_PlaySFX`), items and stages. Let 550000…550000+M−1 through, e.g.
     `if (id >= 0x83D61 && !(id >= 550000 && id < 550000 + M))`.
   - Do the same for `lbAudioAx_800263E8` (AX:1751, `< 0x83D60`; positional sounds, script command 0x27) and
     `lbAudioAx_80023130` (AX:404).
   - Tracked plays (behaviors 1–6, the voice tracks) have no clamp beyond the sem's bounds.
6. **Optional:** giant/tiny pitch variants need a `case 55:` in `ft_80087D0C` (ft_0877.c:311-421) and three
   scripts per sound (normal, +1, +2), as Mario has. Without it Geno keeps one pitch. The Kirby-copy remap
   (`800233EC`) doesn't list 55, so Kirby copying Geno just plays Geno's IDs, which are loaded because Geno is in
   the match.
7. Nothing else is needed. `HSD_AudioSFXStartParam` takes the bank count and script table from the sem, the synth
   hash has no ID limit, and the play opcode carries 24-bit sample IDs.

**Byte budget:**

- Keep `geno.ssm`'s data_len **≤ 586,208 B**, the current 4th-largest fighter bank (Kirby). Then the init formula
  leaves synth bank 2 at 3,291,584 B. The ARAM layout and ARAM heap stay exactly as today, and any four fighters
  including Geno fit within the existing worst case.
- A bigger bank still works: the formula grows synth bank 2 automatically, taking the space from the ARAM heap.
- For scale: Mario's bank is 32 clips, 21.2 s, 372,736 B. 32 kHz ADPCM costs about 18.3 KB/s, so 25 sounds of about
  0.6 s ≈ 275 KB, and 16 kHz halves that.

**Fighter data:**

- **SoundEffect (0x11)** is 3 words (ftaction.c:575-659; lb/types.h:835-847): `opcode:6 | behavior:8 | 18 unused`,
  then the **full 32-bit sound ID** (no mask), then `pad:16 | volume:8 | pan:8`.
  - behavior 0 = untracked `ft_PlaySFX`; 1–6 = tracked voice/SFX tracks; 10–15 = stop a track.
  - Behaviors 7–9 consume only 2 words and would desync a script.
- **What Geno's scripts need:**
  - His generic swing and hit sounds from main.ssm (bank 0, IDs below 0x210, always resident) can stay.
  - His Mario-bank IDs (180000–180093) must become 550000+k once the Mario mapping is removed, or they only sound
    when Mario is also in the match.
- **`ftData+0x4C` → `FtSFX`** (ft/types.h:658-677) holds:
  - the random attack-voice array played by command 0x12;
  - the KO, Star KO, jump, damage-voice (two arrays), tech, ledge, heavy-pickup and grab sounds;
  - the crowd chant (0x83D60 = none).
  
  `PlGe.dat`'s FtSFX (datkit `fighter-build`) should point at Geno's IDs, or at 0x83D60 for none.

### 8.4 Encoder note (added with the sfxbank round 3)

On SNES renders with near-periodic looped waveforms, `DSPCorrelateCoefs` divides by zero into an unused matrix row. C
stores inf there; the Python port raised, and now does IEEE division instead. The default clang arm64 build of the
reference fuses multiply-adds (FMA), which changes a few coefficients on such inputs. Built with `-ffp-contract=off`
(strict IEEE), the reference matches the port byte for byte on all 29 test clips. The patched nr_name.ssm above is
unaffected: the updated encoder reproduces its appended data exactly.
