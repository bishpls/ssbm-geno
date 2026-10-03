# Forest Maze: the technical scope

What adding a new stage to Melee takes, worked out from the decomp (`src/melee/gr`, `mp`, `mn`, `gm`, `lb`) and the
disc's stage files, with the pipeline planned by analogy with Geno's (`datkit fighter-build` from a spec and a glTF).
The design sketch is DESIGN.md; the measurements are `research/starters.md`.

## Decided (Michael, 2026-09-29)

- Layout A (Clearing), built by `stage-build` from the spec, with static assets only (no Wiggler).
- **The real stage-select slot** (§2.8), not the temporary hook: the greybox milestone (M1) includes it.
- The music is Forest Maze metal draft 2, cut into a stage loop under a new music id (§2.7).
- Style targets by image model are approved, kept to GameCube-era, Melee-specific looks (M2), before production art (M3).

Milestones: **M1** a playable greybox in a real stage-select slot, with the music loop, verified in game; **M2** style
targets; **M3** production art after Michael picks a target.

## M1: built (2026-09-30)

A playable greybox Forest Maze (layout A, Clearing) in a real stage-select slot, with its own music loop. Everything
below is measured in game on the sandbox disc (`~/games/melee/sandbox/geno-stage`); the main disc is untouched.

**The slot: the unused Akaneia stage (a compromise, and a good one).** The stage select stores each entry's stage kind in
a byte (`mnStageSel_803F06D0[].stkind`, u8), so the new StKind 286 planned in §2.1 can't be stored there. Melee already
has a dummied stage in the VS range: StKind 0x15 (`St_Kind_Akaneia`) maps to GrKind 0x1A (`Gr_Kind_Unk26`), whose
`stage_datas` entry is NULL, and whose menu text (0x19) is "アカネイア". The Forest Maze takes that pair: no table grows,
every "VS stage < 0x21" assumption holds, it isn't in the unlock table (so always unlocked), and its sound row (no bank,
reverb 1) is Fountain's. The decomp points `stage_datas[0x1A]` at `grFm_StageData` (non-matching only).

| Piece | Where | Measured |
|---|---|---|
| Stage file `GrFm.dat` (8.8 KB) | `datkit stage-build` from `stage_spec.py` (spec) + Battlefield's file (template) | `stage-dump` = spec to 0.001; `starter_lab` in game: cap 28.0 (x -27 to 27), floor 0, ledges (±70, 0) held, blast zones ±225 / 200 / -120, camera ±160 / 140 / -55 centred (0, 30): **5/5 pass** |
| Greybox art | the spec's faces: the stump (collision outline extruded z -30..22), the cap box (z ±14), a fogged back card and trunks | **edge lab**: both top surfaces on the image's centre row (0 px), ends within 0.06 px (stump) and 0.24 px (cap) of the collision at 6.57 px/unit |
| Stage code | decomp `src/melee/gr/grforest.c` (Battlefield's pattern, 3 gobjs, static), `ground.c` table entry | logs `GRFOREST INIT grkind 26 stkind 21` on load |
| Stage select | `datkit menus-stage` edits `MnSlMap.usd`: a 20th position joint (x -4.0, the bottom row's left end), the icon as image 7 of the single icons, the name plate scaled 0.84 and moved 2.4 left, the name as image 30 (frame 600), the hologram as segment 30 (frames 1500-1549, free in the vanilla file); decomp `mnstagesel.c`: entry 29, Random moves to 30, none to 31 (`MNSS_*` macros, vanilla values when matching) | menu test: hover 29, name and hologram show, A loads the Forest Maze |
| Where the icon sits | **the bottom row's left end (-4.0, -9.1), Michael's call (2026-09-30)**, as a single icon (the bottom row's model, image 7) | see "The icon's place" below |
| Random list | `gm_1601.c` random-switch index 29 → StKind 0x15 (the table's spare 30th entry), its 29-stage loops to 30; `mnstagesel.c` random picker over 30 | START with nothing hovered picks at random (Venom in the test run); the Forest Maze is in the pool by construction (stage_mask bit 29 is on by default) |
| Random Stage Switch menu | `mnstagesw.c`: a 30th row (column 2's 15th; the rows are built in code), its name from menu text 0x19, relabelled "Forest Maze" in `SdMenu.usd`; column 2's last row `MNSW_LAST` | code only: the menu wasn't opened in a test |
| Stage count | `mncount.c` and `mndatadel.c` loop to 30 | code only |
| Music | `gr_forestmaze.hps`, HPS id 0x64 (`lbaudio_ax.c`, next to Geno's fanfare 0x63; falls back to Battlefield's when absent); the stage's music row plays it | see below |
| VS flow | menu test `sss_forest.py` (look / flow / back) | pick Fox and Falco, the Forest Maze, a 110 s match, pause-quit, results, character select, stage select, START: a random stage loads |

**The icon's place (2026-09-30).** Michael asked for the bottom row's open left end. There, every hovered name's right
end ran over the icon: `names_report.py` counted 420-1073 name pixels on its rectangle (x 246-302 at res 1) for the
Forest Maze, Battlefield, Final Destination, Dream Land, Kongo Jungle 64, Princess Peach's Castle and Yoshi's Story. The
widest names span x 15-288, so the plate can't move left (they'd leave the screen) or up (the middle block sits above).
The fix is data only, in `MnSlMap.usd`: the name plate's joint (StageNameModel j1, the tilt) is scaled 0.84 about its
centre and moved 2.4 left. Every name now ends at x 224-239, with 0 pixels on the icon, and still starts on screen; the
names are 16% smaller than vanilla. `menus-stage` now builds from vanilla copies (`$MELEE_WORK/stage/vanilla`), since the
main disc carries the installed files.

**The music loop** (`music.py build`, from metal draft 2):
- Intro 0-9.6 s once; the loop from Theme A's downbeat (9.6 s) to the end of the final chorus (91.2 s), 81.6 s (68 bars at
  200 BPM), leaving out the final hit.
- **The loop's last bar is the stage's own** (2026-09-30). M1's stream kept draft 2's 8th-note stop before the hit, so every
  wrap had a 150 ms hole: 10 ms RMS fell 36 dB below its surroundings at 91.17 s, where the deepest dip anywhere else in
  FINAL is 4.7 dB (Michael: "a very obvious gap"). `music_loopend.py` re-renders draft 2 without the stop, in two passes of
  the arrangement's own renderer: pass 1 records every whole-song normaliser (DI peaks into the amps, stem and layer RMS,
  the master EQ and gain), and pass 2 replays them, since left free the cellos alone would have moved 12 dB. Pass 2 leaves
  pass 1 at 91.058 s, where the stop began. Two renderers aren't repeatable: Surge XT starts its oscillators at a random
  phase (the synth sections differ run to run; FINAL has none), and sfizz_render, which streams sample tails on a
  background thread, renders notes short when the machine is loaded (renders beside other work differed from draft 2's
  orchestra at -18 dB in FINAL, where clean ones differ at -66 to -76). So each sfizz render repeats until two runs
  agree sample for sample (6 of 45 parts disagreed on their first two runs under this session's load), and both passes
  are checked against draft 2. The re-render matches draft 2 in FINAL to -74 dB; the stream takes draft 2 up to
  90.0 s and the re-render after it. The loop's last 4 ms cross into the 4 ms before the loop start, so the waveform runs
  on across the jump (without it, a 0.27 full-scale step). Seam: deepest dip -2.7 dB, inside THEME A (the loop's last
  0.3 s: -1.4); wrap step 1.3x the median (the first pass's intro-to-theme join: 1.1x); HF burst -1.1 dB (a mid-loop
  downbeat: -1.5). Offline: the stream's in-game seam is not yet re-captured.
- 32 kHz stereo DSP-ADPCM, 52 blocks. The loop starts exactly on the downbeat: 16 samples of silence lead the stream, so
  the loop start (307216) is a whole number of 56-sample groups, and `hps.py`'s new `exact_loop` cuts the block before it
  short, as HAL's own streams vary their block sizes. ADPCM SNR 33.3 / 33.6 dB (one coefficient set per channel over a
  dense metal mix; a vanilla stream re-encodes at 42.8).
- Level: the six starters' streams measure -15.3 to -11.0 LUFS (median -12.8), true peaks -4.6 to +0.1 dBTP. The cut
  is gained -2.8 dB to -12.8 LUFS, true peak -3.5 dBTP.
- **The seam, in game (M1's stream, with the stop):** a 110 s match's audio dump matches the stream sample for sample
  (correlation 0.98-0.998 at 30, 60 and 85 s; 0 samples offset) and wraps at 110.40 s (91.2 s into it) to the loop start (0 samples, correlation
  0.998). At the wrap the high-frequency burst is +1.87 dB over its surroundings; 32% of the arrangement's own downbeats
  in the same capture burst more (median +0.69, p90 +3.14), and the sample step is 0.63 of the local 99th percentile:
  a downbeat, not a click. (Dolphin labels its DSP dump 32028 Hz; the stream plays at 32000 samples per second of it.)

**Kept:** the matching build matches (`08e0bf20`); `remeasure.sh` leaves `projects/geno/research` unchanged.

## The sky: a twilight that moves (2026-09-30)

Michael, on art pass 2: "Are we doing anything about the dull static purple skybox?" Then: "Small Star Road nod sounds
good to me." The shooting star is on by default (`STAR_ROAD=0` turns it off).

**How Melee animates its backgrounds (the census, `stage-dump`'s `anim_census`; `board/sky/census.csv`):**
- Battlefield's sky scrolls its textures (UV tracks) and moves joints.
- Final Destination fades materials (alpha tracks) and scrolls textures.
- Fountain of Dreams' sparkles are 35 joints scaling in and out.
- Yoshi's Story scales and moves joints, and swaps one texture's image.
- In every case the motion is the map file's own animation set 0. The ground code attaches it at the gobj's init
  (`grAnime_801C8138`), the ground's proc advances it every frame, and a per-set flag at +0x28 of the model group loops
  it. `grforest.c` already made that call, so the decomp is unchanged.

**The sky (`forest_scene.py`'s `sky()`, `forest_tex.py`), behind everything in the unfogged stage group:**
- **The painted backdrop:** indigo, violet, a rose-gold band, and a dusky glow over the trees. The colours are placed by
  world height from the logged match cameras. x25's frame top meets the backdrop at y 142, and the fighters' band
  starts at 78; for x55 those are 195 and 123. So the warm glow sits low and dim, where the fighters are, and the
  brightest band sits above them.
- **The treeline:** two canopy layers, blended with soft edges. They make the backdrop read as a sky seen through a
  forest.
  - Each crown is a disc, round on the card, with lobes bumping its upper rim, noise on the rim, and a mass below that
    widens downward; a few crowns are taller, with slightly pointed tops.
  - The farther ridge is lighter and cooler (atmospheric falloff) and peeks above the nearer one.
  - The coordinator's catch: an earlier cut of tiny crowns rendered as a city skyline, because at 1-4 texels wide they
    became columns.
- **Stars:** four additive star fields in the indigo, fading in above the glow. Each has its own material-alpha twinkle
  (3.0, 3.9, 4.8 and 5.8 s): staggered, as Final Destination fades.
- **Clouds:** three cloud banks, warm undersides and cool tops. Each drifts by a texture scroll, seamless, at its own
  cycle (240, 180 and 150 s), as Battlefield's sky scrolls.
- **The shooting star:** a joint. Two events in a 62 s loop, at 22 s and 51 s, 0.67 s each. It crosses the open sky
  between the near trunks.
- **Fireflies:** six small additive glows low in the forest, each drifting and pulsing on its own 7-13 s loop, as
  Fountain's sparkles.
- **`stage-build`** now writes child joints, joint, material and texture animation tracks, per-axis texture wrap and
  additive cards.
- **Two sky studies** from the image model, as references only.

**Off the match axis.** The trailer lab found a black gap in its trophy orbit, and the trailer will orbit the stump and
use a diagonal SMRPG battle camera:
- **The sky wraps the stage:** every layer (backdrop, stars, clouds, both canopy ridges) is an elliptical wall around the
  origin. Behind the stage it's as deep as the old flat card (z -700 to -640), so the match framings are unchanged; it
  reaches 1300 to each side and around the front.
- **Seamless all round:** textures tile a whole number of times around each wall, so the cloud scrolls stay seamless.
- **The ground:** the forest floor, cliff and mist widen to the walls, and a fogged ravine floor closes the front below
  the stage.
- **Measured** on 26 shots from `director/orbit_lab.py`: yaw -60 to +60 degrees every 10, the camera pitched 20 and 30
  degrees above the stump top, 160 units out. Void is the share of exactly black pixels, the clear colour where
  nothing is drawn; near-black ambient occlusion at the bushes' feet is not void. The result is 0 in every shot,
  against up to 7.8% on art pass 2 at +-60 degrees.

**At t7's angle.** t7's horizon sits ~18% from the top, which means a camera ~10 degrees down. The 23 degrees derived
earlier came from the stump-top ellipse, which the image model draws too open; at 23 degrees no sky can be in frame. At
10 degrees the sky fills the gaps above the trees.

**Measured in motion:**
- **Readability across the whole cycle.** A build with every clock 24x faster makes 631 frames cover the 240 s cloud
  cycle and the star loop four times. Every frame is measured:

  | Framing | Min | Mean |
  |---|---|---|
  | x25 | 0.283 | 0.290 |
  | x55 | 0.349 | 0.352 |

  Measured the same way, Final Destination's own minimum is 0.2753 (mean 0.296), and art pass 2's static sky gave 0.2726.
  The fighters' idle poses move all of them. The first cut of the sky dropped x25 to 0.207: its glow sat on the
  metric's blend band, right behind the fighters. The fixes were to dim the low glow, raise the treeline, move the
  clouds above the band, soften the treeline's edge, and calm the stump top's rings.
- **The shooting star at real speed,** still cameras, frames 150-300 around an event: x25 min 0.282, x55 min 0.349.
- **Flash.** The largest per-frame change of any region's mean luminance, with the camera on the sky and treeline, is
  0.0017 over 30 s. Battlefield's background gives 0.024 and Final Destination's 0.014.
- **Busy time:** 7.67 ms a frame (p99 9.70), against Battlefield's 8.26 (p99 10.23) and art pass 2's 7.53. The counter
  was proven live.
- **The file:** 868 KB (8,042 triangles, 33 meshes, 721 KB of textures). The canopy's two 512 x 128 layers and the
  wrap cost ~220 KB and ~830 triangles; bushes, trunks and far mushrooms gave back ~700 triangles.

**Found on the way:**
- An animation tree one level off: the ground code loads a model group under a wrapper joint. The shooting star's
  scale-0 track landed on the stage's mesh joint and hid the whole play plane, except for the 0.67 s of each event. That
  was a 0.25 "flash".
- A cloud texture's faint alpha floor.
- Two one-pixel seams: the treeline's top edge filtering in its bottom row (now clamped vertically), and a sliver of
  sky under the treeline card (now extended). `sky_measure.py lines` finds such seams.
- A capture run in parallel with another on the same sandbox: one run's build replaced the other's DOL mid-capture (a
  results screen in place of a match still). The overlapping runs were discarded and rerun alone.

**Short of the brief:**
- The glow low on the horizon is dimmer and duskier than a sunset. Brighter, it sits on the readability metric's blend
  luminance right behind the fighters, so the bright warm light is in the band above them and on the cloud undersides.
- The shooting star is small by design, about 50 px long at 1280 wide.

## Art pass 2: richer, toward t7 (2026-09-30)

Michael: "t7 is the right direction, let's aim for a richer art pass." M3 had t7's palette and layout, but it read as a
greybox with textures. This pass closes most of the gap. `STAGE_ART=forest2` is the default; `forest` (M3) and
`greybox` still build.

**How it's made (all in code):**
- **`blender/forest_scene.py`** (headless Blender, seeded and reproducible) builds every mesh in Melee's units. It bakes
  the light into vertex colours with Blender's BVH: 24 ambient-occlusion rays, a warm key with shadow rays (the cap
  casts none), a cool sky fill, and a peach rim from the glow behind.
- **Why vertex colours:** Melee's own stages are drawn that way. A render-mode census of seven vanilla stages (now in
  `stage-dump`) finds them overwhelmingly `VERTEX, TEX0`, an unlit vertex colour times a CMPR texture: Green Greens is
  141 of 196 meshes. They add alpha cards for foliage. M3's lit materials were part of why it read flat.
- **`forest_tex.py`** paints 17 textures with numpy. They're tileable by construction (FFT-filtered noise), and
  painterly (value bands, soft noise, hard strokes for grooves, rings and spots). The branch, canopy and mist cards
  are RGB5A3 with alpha.
- **`stage-build`** now takes vertex-colour materials and alpha-cut or blended cards. **`menus-stage`** takes a
  low-poly hologram from the spec (336 triangles of the new shapes).
- **The references:** 3 image-model detail studies (stump, cap, background layers) in t7's style. They're references
  only; nothing from the image model is in the game.

**The model:**
- **The stump.** A rounded, irregular top at y 0, with growth rings concentric with its outline and a small real
  corner at each ledge; a smooth rounded end would project past the ledge from a near camera. A thick mossy lip rolls
  over the rim. It overhangs only away from the corners and never rises above the top.
- **Its body.** In front of the fighters' plane it stays inside the collision's hull: under the lip, the front undercuts
  back behind the plane by y -18. Behind the plane, a round trunk narrows to a waist near the hull's width, then flares
  onto the forest floor at y -60 with seven buttress roots.
- **The cap.** It floats, as t7's does. It's a lens: flat along the fighters' plane at y 28, from x -27 to 27 exactly,
  and domed only front to back. The rim rolls out only below the top, and there are gills underneath and SMRPG's
  spots on top.
- **The background:**
  - near trunks with root flares, some pale birch-like ones (toned down);
  - mid-distance trunks in a softer bark, and far trunks fading into purple fog;
  - the purple path winding back, 20 bush clusters and 8 mushroom clusters;
  - branch cards framing the top corners;
  - a twilight backdrop outside the fog.
- **The floor.** It lies only behind the stage. Its front edge is a mossy cliff lip; below that, a misty ravine.
- **Why a ravine, not t7's grass in front:** grass in front of or under the stage would read as a floor, and would hide
  fighters falling past it.
- **The glow** sits where the match camera shows it: the top of the frame, through the trunk gaps, just above the
  fighters' band.

**Eight render-and-measure passes** (`director/art_pass.sh` and `art_board.py`, in `board/m4/passes.csv`). Each pass:
- renders a hero shot at t7's angle (23 degrees down, from t7's stump-top ellipse) beside t7;
- renders both match framings with fighters, beside M3;
- measures luminance and hue histograms against t7, readability, and the edge lab with its collision overlay.

| Pass | Triangles | Luminance / hue overlap with t7 | Readability x25 (FD 0.275) / x55 | Edges | What changed |
|---|---|---|---|---|---|
| 1 | 8,208 | 0.88 / 0.48 | 0.135 / 0.121 | floor end 1.17 px (fail) | first build |
| 2 | 8,220 | 0.97 / 0.53 | 0.228 / 0.288 | pass | the glow out of the band; buttress roots; ledge corner; mist |
| 3 | 8,372 | 0.95 / 0.55 | 0.229 / 0.288 | pass | the stump as a stump: undercut rim, waist, flared base |
| 5 | 7,868 | 0.93 / 0.54 | 0.267 / 0.332 | pass | calmer platforms, irregular bark, side roots |
| **8** | **7,868** | **0.93 / 0.54** | **0.280 / 0.336** | **pass** | deeper cap and spots, moss toned (production) |

Readability's losses were in the platforms, not the background: the cap's spots and the stump top's tan sat at the
metric's blend luminance. Toning them brought x25 from 0.135 to 0.280, at the price of a darker frame than t7's (mean
luminance 0.040 against 0.052).

**The cap: floating, measured.** A thick tapered stem with a skirt, behind the fighters' plane, costs 0.015 of
readability at x25, putting it under Final Destination's 0.275 (0.265 against 0.280), and 0.012 at x55. It's also a pale
column right behind centre stage, where fighters spend the most time.

**Budget and performance:**
- **The file:** 550 KB, 7,868 triangles, 19 meshes, 19 textures (416 KB). The vanilla stages run 452-1,119 KB and
  8.3k-13.6k triangles.
- **CPU:** busy 7.53 ms a frame (p99 9.55, max 12.95), against Battlefield's 8.26 (p99 10.23) and M3's 7.54. The
  counter was proven live every run. The GPU isn't timed.

**Checks:**
- `starter_lab` 5/5.
- Edges: the rows 0 px; the floor ends ±0.17 px; the cap ends ±0.41 px.
- Stage select: the new icon, the regenerated hologram, the name unchanged; A loads the stage, and Random still works.
- Music: the reel's audio matches the stage track (waveform correlation 0.54, against 0.12 for the reversed track).
- The matching build gives `08e0bf20134d`; the remeasure diff is empty; the play build is on the sandbox.

**Found on the way:**
- The review reels had been muxed with the audio aligned at the start. Dolphin's audio dump begins at boot, about
  12.6 s before the first frame, so the reels' first 12 s were silent and the music late; M3's reel was affected too.
  `director/mux_reel.sh` now aligns the ends, and both reels are re-muxed.
- An onset-envelope music check can't tell the track from its reverse when fighters' sound effects dominate, so the
  check is a waveform correlation with a reversed-track control.

**What still falls short of t7, and why:**
- **The foreground.** t7's stump sits in grass, bushes and big mushrooms. Ours has a misty ravine in front, because
  nothing may read as a floor near the fighters' plane or hide a falling fighter. The base's flare below the collision's
  bottom (y -40) is visual only, behind the fighters.
- **The hero's top third is darker than t7's.** At t7's angle the camera looks down onto the floor; the glow is placed
  for the match camera.
- **The cap is a lens, not a round dome.** Its top is the collision's flat 54-unit line; a dome along it would float
  above or sink below fighters' feet.
- **Darker and less saturated overall** (hue overlap 0.54), the price of readability.
- **The bark is procedural:** less painterly depth than t7's, and soft in close-ups.
- **The hologram reads faint,** as M3's did.
- **The branches** show only when the camera zooms out.
- **The GPU cost isn't measured.**

## M3: production art (2026-09-30)

Built from style target t7 (DESIGN.md "M2") by code: `forest_art.py` writes the textures (procedural, numpy) and the
geometry; no image-model output is in the stage. `STAGE_ART=greybox` still builds the greybox for A/B
(`stage_spec.py`).

**The model:**
- **The play plane:** the stump is the unchanged collision outline extruded: a cut-wood top with a mossy rim at y = 0,
  a moss lip under the front edge, and bark sides that follow the collision under the ledges. The mushroom cap's top is
  flat at y = 28 and widest at x = ±27 on the fighters' plane; its rim curls in and down, with cream gills and a pale
  stem set back (z = −9).
- **The background (fogged):** umber and pale-barked trunks with root flares, a forest floor far below the stage
  (y = −100, behind z = −80) with the purple path winding back, bushes, orange-red mushroom clusters, three canopy
  cards and a twilight haze card. Fog runs from 110 to 520 in dusky purple.
- **`stage-build`** now takes textured materials (raw BGRA, encoded CMPR) with per-vertex UVs and smooth normals.

**Budget:**
- Measured first: the starters and forest stages run 452-1,119 KB, 61-213 meshes and 8,285-13,597 triangles.
- The Forest Maze is **127 KB, 15 meshes, 1,392 triangles and 12 textures** (`board/m3/budgets.csv`).

**Performance** (`board/m3/perf.csv`; `director/perf_lab.py` with `run_perf.sh`):
- **The test:** four level-9 CPUs (Geno, Fox, Pikachu, Ness) for 60 s at the console's CPU clock. It logs the engine's own
  timing of every frame (`HSD_PerfLastStat`, via the director's PERF cue): the logic, the draw submission, and "busy",
  their sum, out of a 16.7 ms frame. It also logs lag frames.
- **The result.** The Forest Maze keeps the CPU busy **7.54 ms a frame** (p99 9.57, max 13.08), against Battlefield's
  8.26 and Fountain of Dreams' 12.29. Its art costs 0.09 ms over the greybox (7.45), and the decoration 0.04 ms (7.50
  without it).
- **Lag frames:** 4 a minute on every stage, the greybox included, spaced exactly 1000 frames apart. That's Melee's
  controller polling drifting against the frame (an extra pad sample), not slowdown.
- **The lag counter is proven live in every run.** A deliberate 40 ms stall at frame 60 must log a lag frame, or
  `run_perf.sh` aborts. Battlefield with the emulated CPU at 0.4× drops 965 frames: the positive control. It's clean at
  0.5×, which matches its 8.3 ms busy time.
- **Not measured:** Dolphin doesn't time the GPU, so the triangle and texture budgets above stand in for it.

**The 07:49 incident (the first performance numbers were void):**
- **The cause.** `build.py`'s lag hook was a second HOOKS entry that edited the first hook's flush block in place. The
  first hook's text then no longer matched, so the next build inserted the plain block again, ahead of the lag block.
  The plain block resets the queue count to 1, so the lag call never fired. It happened at 07:22 and again at 07:49.
- **What was void:** every lag number before this section was written. That covers:
  - M3's first "0 lag frames" table: production, greybox, no decoration, Battlefield, Fountain, and the reel, which ran
    at the labs' 2× clock anyway;
  - the whole 1.0-0.45× clock sweep.

  The first art pass's "3 lag frames", with the decoration halved in response, was the polling drift: every stage shows
  it. The halving wasn't needed; the decoration costs 0.04 ms.
- **The fix:**
  - The lag call lives inside the one flush hook.
  - `hook()` upgrades a lone plain block, and collapses a doubled pair, before hooking, then exits unless `gmscene.c`
    has exactly one flush block with the call. It's tested from the decomp's HEAD and from the doubled state.
  - `run_perf.sh` checks the source after each build and the stall probe after each run.

**Checks, in game:**

| Check | Result |
|---|---|
| `starter_lab` against the spec | **5/5**: cap 28.0, floor 0, ledges (±70, 0) held, blast zones and camera range exact |
| Edge lab (the play plane built without its background, so the silhouette is clean) | both top surfaces 0 px off; stump ends within 0.06 px, cap ends within 0.59 px |
| Readability at the reference framing | 0.274 (Final Destination 0.275, Battlefield 0.40, the forest counterpicks 0.04-0.09) |
| Readability at the wide framing | 0.339 |
| Stage select | the icon is now a render of the finished stage; the hologram comes from the production play plane; the name and the 0.84 plate are unchanged; hover and select load the stage |
| Music | the reel's audio carries the stream (the loop itself is unchanged since M1's seam check) |
| Matching build | still matches (`08e0bf20`) |
| `remeasure.sh` | research unchanged |

**Compromises, plainly:**
- **The SMRPG references are demo screens, not the battle backdrop.** The Forest Maze battle backdrop is
  LC_LZ3-compressed, and the tooling's codec covers only 4 of its ~15 commands. The attract demo's two Forest Maze
  scenes, VRAM and palettes are the references instead. Without the tilemaps, the tile sheets show each tile in one
  palette.
- **The first five targets came out as 2D paintings.** Only three are real GameCube-style renders; t7 is one of them.
- **Procedural textures and simple geometry.** The stump is a clean extrusion of the collision: its roots are in the
  texture and in the underside's shape, and none reach past the collision, where they would mislead recoveries. The
  look is GameCube-plausible but plainer than Nintendo's hand-painted stages.
- **The pale-bark motif is subdued.** A bright pale trunk behind the cap competed with fighters, so it was darkened and
  moved off-centre.
- **The decoration is thinner than the first pass.** It was halved against a "lag" that turned out to be polling drift
  (the 07:49 incident above). The fuller set measured nothing on the CPU and is still far inside the triangle budget, so
  it can come back (`forest_art.py`'s bush and cluster counts) if Michael wants the denser floor.
- **Performance is measured on the CPU side only** (above).

## 0. Summary

| Piece | What it is | Estimate (agent-days) | Risk |
|---|---|---|---|
| Stage kind and tables | GrKind 0x47, a new StKind (286), `stage_datas` / `stage_id_map` / sound rows | 0.5 | low |
| Stage code | `grforest.c`: StageData, callbacks, OnInit (points, camera, blast zones); static, no hazards | 0.5 | low |
| `stage-build`: collision, points, params | datkit, from the stage spec (`layouts.py`), GrNBa.dat as the template | 1-1.5 | low (probe below) |
| Greybox model | the spec's outline extruded into boxes, per-part colours, one light | 0.5-1 | medium (static-mesh import) |
| Selection | an SSS slot: icon, name, preview, cursor box, random list | 2-3 | **high** (the SSS is a fixed grid in one model) |
| Music | the loop cut, variable HPS blocks, HPS id 0x64, the stage's music row | 1 (after Michael's pick) | low |
| Production art | stump, boughs, trunks, mushrooms, canopy, 3-4 background layers, fog, lights; Melee's look | 5-8, plus review rounds | medium (look under Melee's lighting) |
| Ambient effects | falling leaves (stage particles), light shafts | 1 | low |
| Records, random switch, counts | `mnstagesw` 29 → 30, `mncount`, `mndatadel`, `stage_mask` bit 29 | 0.5 | medium (hard-coded 29s) |
| **To the greybox milestone** | §5 | **about 3-4** | |
| **To a finished stage** | | **about 12-18** | |
| On hold | single-player modes; Japanese menus (`MnSlMap.dat`, the name texture) | about 0.5 each | |

The feasibility probe (Part D, §6) retired the biggest pipeline risk:
- a stage file written back through HSDRaw loads and plays identically (6/6 checks on the round-tripped Battlefield);
- a platform moved in collision and model together lands a fighter on the new height, and the model moved with it.

## 1. How the engine holds a stage

- **Two kinds.** `StKind` is the stage as chosen: 286 values, VS stages 0x00-0x20, then single-player and event
  variants. `stage_id_map[StKind]` gives the `GrKind`, the archive: 111 kinds, `gr/forward.h`. `stage_datas[GrKind]` is
  the `StageData` in the DOL (`ground.c`):
  - its callbacks per map gobj;
  - the archive's name (`"/GrNBa.dat"`);
  - `on_init` / `on_load` / `on_start` / `on_demo_init`;
  - `on_touch_line` and `on_check_shadow_render`;
  - an optional code-side collision binding table.
- **Loading** (`grDatFiles_801C6038`). The archive's `map_head` is required, and `grGroundParam` is required in
  practice. Everything else is optional and null-checked: `coll_data` (without it, a default collision loads),
  `itemdata`, `ALDYakuAll`, `map_ptcl`/`map_texg` (the stage's particle bank), `yakumono_param` (stage-code tuning),
  `map_plit` and `quake_model_set`.
- **Per-StKind parameters.** `grGroundParam` holds one row per StKind the archive serves: the music, the item-frequency
  multipliers and the sudden-death music. **A missing row hangs the game** on load ("not found stage param in DAT",
  `Ground_801C28CC`). The new file must carry a row for the new StKind.
- **Map gobjs.** `map_head.ModelGroups[i]` is map gobj `i`: a joint tree with meshes, its joint, material and shape
  animations, and optionally its own camera, lights, fog and collision links. The stage's code creates the ones it uses
  (`Ground_801C1A20`), each under a root scaled by `grGroundParam`'s stage scale.
- **General points.** `map_head.GeneralPoints` is a list of joint trees with (joint index, point type) pairs. Joint
  indices count depth first from the tree's root = 0, not entering an INSTANCE joint's children (`Ground_801C34AC`). The
  types:
  - 0-3 spawns, 4-7 respawns (5-7 fall back to 4);
  - 127-146 item spawns;
  - 148 the camera centre, 149/150 the camera range's corners, 151/152 the blast zones' corners;
  - 199-208 targets, 252-259 bumpers.
  - At init the stage code calls `Ground_801C39C0` (the camera range, relative to 148) and `Ground_801C3BB4` (the blast
    zones). **Without point 148 the engine ignores 149/150 and uses a default range**, ±170 / 120 / −60. Pokémon Stadium
    does this, measured in game.

## 2. The pieces

### 2.1 Stage kind and table entries (decomp, all inside `#ifndef MUST_MATCH`)

*Superseded in M1: the stage takes the unused Akaneia slot (StKind 0x15, GrKind 0x1A), not new kinds; see "M1: built".*

- `GrKind` **0x47** (`Gr_Kind_ForestMaze`): `stage_datas[0x47]` is currently a `grTe_StageData` filler. Point it at
  `grFm_StageData`.
- `lbAudioAx`'s stage sound table (`s32_arr_803BB6B0[0x6F][3]`, indexed by GrKind) already has a row 0x47. Set it:
  - [0] is the stage's sound-bank bit, 55 for none; a forest ambience bank is optional.
  - [1] and [2] are the reverb settings.
- `StKind` **286** (0x11E, `St_Kind_ForestMaze`), appended to `stage_id_map` (286 entries today) → `Gr_Kind_ForestMaze`.
  To check at build time: every table indexed by StKind, and `u16` storage (fine).
- **Unlocks:** none needed. `gm_80164430` returns true for any GrKind outside the 11-entry unlockable table.
- The director's `dsl.STAGE` gets `forest_maze: 286`, and labs can pick it the day the file exists.

### 2.2 The map file (`GrFm.dat`)

The roots, as the vanilla starters carry them (datkit `stage-dump` lists them):
- `map_head`;
- `coll_data`;
- `grGroundParam`;
- optional: `itemdata`, `ALDYakuAll`, `map_plit`, `map_ptcl` + `map_texg`, `quake_model_set`, `yakumono_param`.

A static starter needs `map_head`, `coll_data` and `grGroundParam`, plus `map_ptcl`/`map_texg` if leaves fall.

Map gobjs, following Battlefield's arrangement (7 gobjs, 452 KB):

| gobj | Content | Code |
|---|---|---|
| 0 | the general points' joint tree (no meshes; Battlefield's 22 joints) | `grAnime_801C8138` |
| 1 | the main stage and platforms (the play plane), bound to the collision | `Ground_InitMapCollAndAnim` on init, `Ground_UpdateMapColl` each frame (Battlefield's gobj 6; its flags `(1<<30)\|(1<<31)`) |
| 2-4 | background layers (trunks, canopy, far haze), each with its own fog and lights, some with slow joint or material animation | `grAnime_801C8138` + `grMaterial_801C94D8` |

The vanilla starters' budgets:

| Stage | File size | Gobjs | Meshes (DObjs) | Textures |
|---|---|---|---|---|
| Final Destination | 611 KB | 10 | 92 | 68 |
| Battlefield | 452 KB | 7 | 61 | 49 |
| Yoshi's Story | 825 KB | 4 | 195 | 171 |
| Dream Land | 657 KB | 8 | 79 | 84 |
| Fountain of Dreams | 1,119 KB | 5 | 197 | 193 |
| Pokémon Stadium | 1,469 KB | 3 | 122 | 115 |

(Stadium's transformations live in `GrPs1-4.dat`.) The Forest Maze should stay within the starters' range, about 1 MB
and 200 meshes: the stage shares memory with four fighters.

### 2.3 Collision

`coll_data` (HSDRaw `SBM_Coll_Data`; the engine's `MapCollData`, `mp/types.h`) holds:
- **Vertices** (x, y), in stage units: world ÷ stage scale.
- **Lines**, sorted into five contiguous ranges: floors, ceilings, right walls, left walls, dynamic. Each line has:
  - two vertex indices;
  - `prev` and `next` links to the lines it joins. At +4 and +6: **HSDRaw names these the other way round**; our tools
    use the engine's names;
  - alternate-group links (−1 when unused);
  - a surface kind: 1 floor, 2 ceiling, 4 right wall, 8 left wall;
  - a property byte: 0x01 pass-through, 0x02 ledge. The live flags show them as 0x100 and 0x200;
  - a material (sound and effects: Basic, Rock, Grass, Wood...).
- **Line groups** ("joints" in the engine): per group, the index and count of each kind of line, a bounding box, and a
  vertex range.
  - A map gobj's `CollisionLinks` (group, −1, joint index) binds a group to a joint. Its vertices are then in that
    joint's space and follow it (`mpLib_80055E9C`: vertex × joint matrix): the moving platforms.
  - Stage code can bind groups too (`StageData.joints`, Fountain of Dreams' `grIz_803E0D60`).
  - A static stage binds its groups to the stage gobj's root, or leaves them unbound. Unbound vertices are world ×
    stage scale.
- **Winding** (read from the six starters):
  - floors run left to right;
  - right walls top to bottom;
  - left walls bottom to top;
  - ceilings right to left.
  - The solid is on the right of each line's direction.
- **Grabbable ledges.** A floor line carries the ledge flag; its end that meets a wall is the corner a fighter hangs from.
  - The vanilla stages flag only the short end segments (Final Destination: 10.57 at each end; Battlefield: 8.4), and
    split the floor there.
  - The lab reads the corner the engine uses: `mv.co.cliff.ledge_id` in CliffWait, then that line's outer vertex. It
    matches the file to 0.001 on all six starters.
- **Pass-through platforms.** Floor lines with the pass-through property, `prev`/`next` −1, top surface only. A fighter
  lands from above and drops through with down.
- **Islands.** `mpIsland` builds connected floor chains at load (for the CPU and ledges): a main stage must be one
  chain, ledge to ledge.

What stage-build writes from the spec:
- vertices and lines in the engine's order and winding, the links, flags, materials, ranges and groups;
- group bounds;
- the ledge split;
- every value checked against `stage-dump` of the result and the in-game GRDUMP (§4).

### 2.4 Camera, blast zones, spawns, items

- **General points** (§1): one joint tree, root at 0, a child joint per point. It carries:
  - 148, 149, 150 (camera);
  - 151, 152 (blast zones);
  - 0-3 (spawns), 4-7 (respawns);
  - item spawns 127+. Battlefield has 8; `Stage_80224FDC` picks among them.
- **`grGroundParam`:**
  - stage scale (1.0 for ours);
  - the camera's fov, distance range, tilt and pan, track ratio, smoothing, pause-camera limits, and fixed-camera
    pose. Start from Battlefield's and tune in game;
  - item spawn weights per item (0x68-0xAE; items are off in competitive play);
  - the per-StKind rows (§2.7);
  - bubble (off-screen indicator) colours.

### 2.5 Lighting, fog, backgrounds

- **Lights.** Each map gobj carries `HSD_Light`s (Battlefield: 2 per gobj, Final Destination 2-3). `map_plit` holds the
  lights the fighters are lit by (`Ground_801C49B4` returns it, or a default set; `ftCo_09F4.c` builds the fighters'
  lights from it). Fighters take their lighting from the stage: a warm key from above left through the
  canopy, a cool fill, and ambient green bounce. Judge them on Geno and the cast in game, as the model's materials were
  (Melee brightens textures ×1.2 on the lit side, HANDOFF §5).
- **Fog.** `HSD_FogDesc` per gobj (type, start, end, colour). The background layers fade into warm green haze; the play
  plane has none.
- **Backgrounds.** Real 3D depth: layers at increasing z, so the match camera's moves give parallax for free. A gobj with
  its own camera (`callbacks[i].flags_b2`) renders as a separate backdrop (a skybox); the canopy could use one.
- **Performance.** No reflections (Fountain's lesson), few translucent layers, and textures sized to Melee's (Battlefield
  49 textures). Dolphin shows a missed frame as two logic frames per image, and the director's frame-sync hook drops
  them. A measure for heavy frames is to do.

### 2.6 The stage's own code (`gr/grforest.c`)

From `grbattle.c` (436 lines), minus its background-swap state machine. What a static starter needs:
- a `StageData`: GrKind 0x47, callbacks, `"/GrFm.dat"`, `OnInit`, `OnDemoInit`, `OnLoad`, `OnStart`, `callback4`
  (false), `on_touch_line` (NULL), `on_check_shadow_render` (true) and `flags2` 1;
- `OnInit`:
  - create gobjs 0, 1 and the background layers through the Battlefield pattern (`grBattle_80219D84`);
  - `Ground_801C39C0()` (camera);
  - `Ground_801C3BB4()` (blast zones);
  - `grLib_801C9A10()`;
- per gobj: init (`grAnime_801C8138`, or `Ground_InitMapCollAndAnim` for the play plane), a proc
  (`Ground_UpdateMapColl` for the play plane), and empty callbacks.

What a static starter leaves out:
- `yakumono_param`;
- hazards;
- `on_touch_line` (it returns a DynamicsDesc for surfaces that push fighters);
- the random background swaps;
- the demo-fight placement (BF places the four points for the title demo);
- `grZakoGenerator` (Multi-Man Melee's wire frames);
- any code-side collision bindings.

About 150 lines, all in a new non-matching file, plus the `configure.py` entry.

### 2.7 Music

- **An HPS id past the table,** as the fanfare did:
  - `hps_files[]` gets `"gr_forestmaze.hps"` at 0x64 (0x63 is `ff_geno.hps`);
  - `lbAudioAx_80023F28` resolves it and falls back to Battlefield's `sp_zako.hps` when the disc lacks it.
- **The stage's music row** in `grGroundParam`:
  - StKind 286;
  - `bgm` = 0x64;
  - `bgm_alt` = the other arrangement (0x65) with a chance, or −1;
  - sudden-death ids;
  - the behaviour flag. Behaviour 0 plays the main song only; Battlefield uses 6, alt at 12%, gated on `gm_80164ABC`.
- **The stream itself** (DESIGN §7): a loop cut of the chosen arrangement, 32 kHz DSP-ADPCM, with the loop start on a
  downbeat.
  - The vanilla stage streams vary their block sizes to put the boundary where the loop needs it; `hps.py` must learn
    that (0.5 day).
  - The stage list's music is in a table of its own; the Sound Test's song list is optional.

### 2.8 Selecting it: the stage select screen

**`mnstagesel.c`.**
- `mnStageSel_803F06D0[30]`: 29 stages plus random. Per entry: the icon joint, a state, the icon's animation frame, an
  index into the random list, the StKind, and the cursor box's half-extents and scale.
- The layout is fixed:
  - 11 stacked pairs of icons (22 stages);
  - 5 "special" icons (the past stages);
  - 2 large icons (Battlefield, Final Destination);
  - Random.
- `NUM_STAGES 29`, and 0x1D / 0x1E appear as bare numbers throughout.

**`MnSlMap.usd` (US) / `MnSlMap.dat` (JP).** One root, `MnSelectStageDataTable`. Twelve models:
- `PositionModel` has 20 joints, the icon positions: 19 slots and a root;
- the icon models (large, double, special, random) show a stage's icon by animation frame;
- `StageNameModel` shows the name by frame (20 × index);
- `StagePreviewModel` has 113 joints, the preview by frame (50 × index);
- the cursor and the Now Loading box.

**A 30th stage needs:**
- a new position joint;
- an icon frame, a name frame and a preview frame, textures added to those models' material animations;
- the table grown to 31, with `NUM_STAGES` and the 0x1D / 0x1E literals made symbolic;
- the random picker's pairing rule (`i < 22` pairs neighbours) left alone.

A new icon slot where nothing is today may need the layout reflowed. The alternative is a second "page": a button on the
SSS swaps the grid to a page of new stages, the 20XX/m-ex convention.

This is the Geno CSS work over again (`MenusGeno.cs`), on a less-explored file. **The riskiest piece.**

### 2.9 Records, the random list, counts

- **The random-stage list:** `GamePrefs.stage_mask` (u32; bits 0-28 now). The new stage takes bit 29. The default prefs
  are `U32_MAX`, so new saves have it on.
  - `gm_80164330`'s loops (`0x1D`) and `lbl_803B7808` (index → StKind) grow by one.
  - `mnstagesw.c` (the Random Stage Switch menu) has a fixed 29-entry grid (`mnStageSw_803ED4C4`, the icon table,
    `x2[NUM_STAGES]`, `x40[NUM_STAGES]` text objects) and needs a row and icon.
- **Counts:** `mncount.c` counts unlocked stages to 29 (the Data menu's stage count); `mndatadel.c` loops 0x1D.
- **Records:** VS Records keep no per-stage table. Tournament mode picks stages from its own list (`gmtoulib.c`); leave
  the new stage out of it.
- **Save data:** no format change; bit 29 already exists in the u32.

### 2.10 On hold (Michael, 2026-09-29): what they'd need

- **Single-player modes** (Classic, Adventure, All-Star, Events, Training, Home-Run, Multi-Man, Target Test) choose
  StKinds from their own tables. None picks the new stage unless we add it, so nothing is needed for them not to break.
  - Training mode picks its stage from the SSS: it follows §2.8, and needs the stage's music row (it plays the VS row).
  - All-Star or Event use would need their own StKind rows (in the stage file's params) and table entries.
- **Japanese menus:** `MnSlMap.dat` gets the same icon, preview and a Japanese name texture. The stage file has no
  language data.

## 3. The pipeline: `stage-build`, by analogy with `fighter-build`

`fighter-build` takes a rig spec, an animation spec, a glTF and template files (PlMr.dat, PlCo.dat) and writes a
fighter. `stage-build` does the same for a stage:

```
datkit.sh stage-build SPEC.json MODEL.gltf TEMPLATE_GrNBa.dat OUT/GrFm.dat [--layers BG.gltf,...] [--stkind 286]
```

- **The spec** (the stage spec in `layouts.py`, emitted as JSON):
  - the main stage's outline (ledges, side profile, floor segments and their materials, ledge splits);
  - platforms;
  - blast zones, camera range and centre;
  - spawns, respawns, item spawns;
  - the StKind rows (music ids);
  - the gobj list (which glTF node trees become which gobj, their fog, lights and animation).
- **The model:** a glTF with named node trees: `stage` (the play plane), `bg_*` layers. They are static meshes on rigid
  joints, simpler than Geno's skinned model.
- **The template:** Battlefield's file, for `grGroundParam`'s camera fields and the conventions of each root. As with
  `PlMr`, only what we replace changes.

**HSDRaw already reads and writes:**
- `SBM_Map_Head` (general points, model groups, splines, lights, MOBJs);
- `SBM_Map_GOBJ` (joint tree, anims, camera, lights, fog, collision links);
- `SBM_Coll_Data` (vertices, lines, groups);
- `SBM_GroundParam` (every field named, the StKind rows as `BGMData`);
- `SBM_GeneralPoints`;
- the whole HSD scene graph (JOBJ/DOBJ/MOBJ/TOBJ/POBJ, lights, fog, animation, particles);
- `SBM_MnSelectStageDataTable` for the SSS.

**The probe shows it writes a stage file the game loads unchanged (§6).**

Its gaps and quirks:
- HSDRaw names the line links the other way round (prev at +4, next at +6);
- its arrays are sized from their buffers, not the count fields, and a rewrite pads the vertex buffer to 0x20. Keep the
  count fields (`stage-patch` does);
- it repacks the file: a round trip is 13 KB smaller and not byte-identical, but equal as the engine reads it.

**What we write ourselves** (datkit C#, alongside `FighterBuild.cs`):
1. **Collision from the spec:** order, winding, links, flags, groups, bounds, the ledge split. 0.5 day.
2. **General points:** a joint tree from the spec's points. 0.25 day.
3. **`grGroundParam`:** copy the template's, set the scale and our StKind rows. 0.25 day.
4. **Map gobjs from the glTF:** reuse `GltfModel.cs`'s mesh and texture path for rigid, unskinned meshes (one joint per
   part). Per gobj lights and fog from the spec. 0.5-1 day, the main unknown: `GltfModel` is built for envelope-skinned
   fighters.
5. **The decomp side:** `grforest.c` and the table entries (§2.1, §2.6), hand-written once; a generated header
   (`gr_forest_ids.h`: GrKind, StKind, HPS id, gobj indices), as `ftgeno_*.h` are generated.
6. **The SSS:** a `menus-stage` command in the `MenusGeno.cs` style, for the icon, name and preview frames and the new
   position (§2.8).

**Verification** (the measurement loop, already built this round):
- `datkit stage-dump` on the output, against the spec, to 0.001;
- `starter_lab` pointed at the new StKind: every platform, both ledges, the blast zones and camera in game (GRDUMP);
- **edge match:** a front-camera render with each platform's collision projected on it; the model's top edge within one
  pixel of the collision line, per platform. The probe measured it this way (§6).

## 4. Tools built this round

- **`datkit stage-dump`** (`StageKit.cs`): a stage file in world space as the engine computes it, as JSON. It covers:
  - the stage scale;
  - joint-bound collision;
  - joint indices counted the engine's way;
  - animated joints' ranges;
  - camera and blast points;
  - music rows;
  - gobj budgets.
- **`datkit stage-patch`:** moves a joint and a collision line by world units, writing back through HSDRaw (the probe).
- **The director's `grdump` cue** (`DIR_GRDUMP` = 21): logs each frame it runs.
  - `STAGE`: the live blast zones, camera range and offset.
  - `LINE`: each live collision line after joint binding, with its flags.
  - `GROUND`: each fighter's floor line, and in the cliff states the ledge line it holds.
- **`stage/director/starter_lab.py`** (+ `run_starters.sh`):
  - drops a fighter onto every platform and the main stage;
  - hangs a fighter on each ledge;
  - dumps the live stage twice a second for a minute (three for Fountain of Dreams), so moving platforms and
    transformations are measured, not assumed.
- **`stage/starters.py`, `stage/layouts.py`:** the analysis, the tables, the envelope and the diagrams.

## 5. First milestone: the greybox

A greybox Forest Maze that **is selectable, loads, plays, has correct ledges and blast zones, and has placeholder art**,
as Geno's blocky rig was.

1. The layout Michael picks (DESIGN §6), as a spec.
2. `stage-build` writes `GrFm.dat`:
   - collision, points and params from the spec;
   - a greybox model with the play plane in flat colours (the stump brown, the platforms a lighter wood, each platform's
     top edge exactly on its collision);
   - one background card at depth, in fog green;
   - Battlefield's camera params and lights.
3. The decomp: GrKind 0x47, StKind 286, `grforest.c`, the stage's music row playing Battlefield's music until the
   arrangement lands.
4. **Selection, two options (Michael's call):**
   - (a) **a temporary hook**: on the SSS, Z on Battlefield's icon picks the Forest Maze. 0.25 day, and the greybox is
     playable at once;
   - (b) **the real slot** (§2.8). 2-3 days more before anyone plays it.
   - Recommendation: (a) for the greybox, (b) as milestone 2 alongside the art. **Michael chose (b) for M1**
     (2026-09-29).
5. **Acceptance, measured:**
   - `starter_lab` on the new stage: every platform's height and extent, both ledges, blast zones and camera range
     match the spec to 0.01 in game;
   - the edge match within a pixel;
   - a Geno-versus-Fox playthrough, captured with game audio;
   - Michael plays it.
   - The matching build still matches (`08e0bf20`).
6. Then DESIGN §5's tests (bough camping, recovery, kill percents) on the greybox before any art.

## 6. The feasibility probe (Part D, 2026-09-29)

**Question:** can we author collision and move visuals together, write the stage file back through HSDRaw, and have the
game honour both?

**Method:**
- `datkit stage-patch` on the sandbox copy of Battlefield (`GrNBa.dat`, stage scale 0.8):
  - the left platform's joint (gobj 6, joint 13) moved up 8 world units (10 file units);
  - its collision line (line 2, vertices 23-24) moved up by the same.
- Installed on the sandbox disc only; the lab built against the patched dump.

**Results:**
- **Round trip, no edits.** HSDRaw repacks the file (452,171 → 439,139 bytes, not byte-identical). The dump is equal as
  the engine reads it (count fields kept). **In game, the full `starter_lab` passes 6/6**: platforms at 27.2 / 54.4 /
  27.2, ledges ±68.4, blast zones ±224 / 200 / −108.8, camera ±160 / 136 / −47.2.
- **Moved platform.** Fox falls onto the left platform and stands at **y = 35.20** (Wait, grounded, on line 2). The
  live collision logs line 2 at −57.6 to −20.0, y 35.200.
- **Visual.** In a res-2 front-camera frame, the moved platform's rim sits **65 px above the unmoved right platform's**,
  8.3 units at 7.8 px per unit (8 intended; ±0.13 per pixel of rim). Fox's feet sit on the moved model's surface. The
  frames are local: `~/games/melee/sandbox/geno-stage/board/probe_moved_*.png`.
- **The disc was restored** (`GrNBa.dat` byte-identical to the main disc's), and the frame dumps deleted.

**What it retires:**
- HSDRaw writing stage files the game loads;
- the collision and joint conventions (stage scale, joint indexing, unbound groups);
- our measurement loop.

**What it doesn't:**
- a file built from scratch rather than patched;
- new gobjs;
- a new GrKind or StKind;
- the SSS.
