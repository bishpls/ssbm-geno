# Forest Maze: the stage design sketch

A new Melee stage for the Geno project: **a competitively viable starter set in SMRPG's Forest Maze**, adding a platform
layout, a playmap, that the existing starters don't have (Michael's brief, 2026-09-29).

- `RULESETS.md`: how the stage list works and why each stage has its status, with sources.
- `SCOPE.md`: what building a stage takes, the pipeline and the first milestone.
- `research/starters.md`: the six starters measured from the disc and checked in game.
- `research/layouts.{csv,json}`: the numbers below; `layouts.py` generates them and the diagrams.

**Status: decided (Michael, 2026-09-29); building.** The calls are in §0; §6 keeps the questions as they were asked.

## 0. Decided (Michael, 2026-09-29)

- **Layout A, Clearing** (the single platform): "Stage A, the single-plat option, is my pick." It is built exactly as
  specced in §2-3: ledges ±70, one cap at 28 (x −27 to 27), blast zones ±225 / 200 / −120. The recommendation was B;
  A's lean toward Final Destination's archetypes and its room for Geno's lanes (§3) stay on the list for the playtests
  (§5).
- **A real stage-select slot:** "Build the proper stage select icon." Icon, name, preview, the random list and the
  stage count, not the temporary hook (SCOPE §5 step 4 (b)).
- **No Wiggler for now:** "An animating wiggler in the background is a cute idea but a lot of extra work for minimal
  gain for now; let's ship with static assets first." Static assets only.
- **Style targets approved:** "Approving the image model calls, but careful to keep to GameCube-era and Melee-specific
  aesthetics." Melee's texture density, lighting, palette and the polycount look of its nature stages; targets are
  references only.
- **Music: Forest Maze metal draft 2** ("forest maze metal draft 2 was better"), cut into a stage loop (§7).
- **No gap at the loop** (2026-09-30: "is the cut at 1:33? there's a very obvious gap in the music there"): draft 2's
  8th-note stop before the final hit played as a 150 ms hole on every wrap. The stage loop now has its own last bar of
  FINAL, re-rendered without the stop (`music_loopend.py`), so the fill runs into THEME A's downbeat; the trailer keeps
  the stop and the hit. Built for Michael's listen (`review_seam.html` in the stage music folder); SCOPE.md has the
  numbers.
- **M1 built (2026-09-30):** the greybox Clearing, selectable from its own stage-select slot (the bottom row's left end, Michael 2026-09-30), with the
  draft 2 loop; SCOPE.md "M1: built" has every measurement.

## M2: style targets (2026-09-30, decided by the stated criteria; Michael reviews in the morning)

**References** (all local, `$MELEE_WORK/stage`):
- **SMRPG's Forest Maze, from Michael's ROM.** The title screen's attract demo plays two Forest Maze scenes: R257, the
  fight at Bowyer's pad (~frame 4400-4750), and R260, Mario jumping on Wiggler (~6350-6550). Mesen2's test runner plays
  it with no input (`smrpg/drive_fm.lua`), screenshots it, and dumps VRAM and CGRAM at frames 4560 and 6450.
  `smrpg_forest.py` decodes them: the palettes (CGRAM, BGR555), the tiles (4bpp) in each background palette, the
  screens and motif crops.
  - A battle backdrop ("BF00 Forest Maze") would be the best side view. It's LC_LZ3-compressed, and the only Python
    codec in the tooling handles 4 of its ~15 commands, so it wasn't decoded; the demo route has the game decompress
    for us.
- **Melee's forest and nature stages from the disc:** Kongo Jungle, Jungle Japes, Great Bay, Yoshi's Island and Green
  Greens (plus Battlefield and Final Destination), rendered at match distance by `director/ref_lab.py`.

**The motifs that make it Forest Maze** (from the decoded screens):
- dark umber ground and trunk interiors with pale-edged bark (the posts and trunk edges catch a thin light rim);
- clusters of glossy round orange-red mushrooms, growing out of deep green bushes;
- purple paths in shadow;
- dark spiky trunk stubs;
- a dim, warm twilight rather than daylight.

The stage carries all of them: the pale-barked trunks, the orange-red cap, the mushroom clusters and bushes on the
forest floor, the purple path, and the twilight fog.

**Targets:** 8 generations with `~/animation-pipeline/tools/imagegen.py`, each conditioned on the two SMRPG screens and
one or two Melee renders.
- The first five came back as 2D paintings.
- The next three used wording that asks for a real-time GameCube render.

**Criteria, written before scoring:**

| # | Criterion | Weight | How |
|---|---|---|---|
| C1 | Fighters stay readable over the background | 30% | measured: `lookmetrics.py` over the play band (the background's distance from fighters' mid luminance, penalised for busy fine detail); 5 = 0.30, Final Destination's level |
| C2 | Platform edges and the stage outline read at match distance | 20% | judged, 1-5 |
| C3 | Faithful to the SMRPG motifs above | 20% | judged, 1-5 |
| C4 | Fits Melee's GameCube look | 20% | judged, 1-5 |
| C5 | Buildable within budget | 10% | judged, 1-5 |

**Scores** (`board/m3/scores.csv`; the Melee references measured the same way: Battlefield 0.40, Final Destination
0.27, the forest counterpicks 0.04-0.09):

| Target | Readability | C1 | C2 | C3 | C4 | C5 | Weighted |
|---|---|---|---|---|---|---|---|
| **t7 twilight umber and purple (3D)** | 0.283 | 4.7 | 5 | 5 | 4 | 4 | **4.61, the pick** |
| t3 twilight (painting) | 0.252 | 4.2 | 4 | 5 | 2 | 3 | 3.76, the runner-up by score (t7's direction as a painting) |
| t6 green-gold light shafts (3D) | 0.213 | 3.5 | 3 | 4 | 4 | 4 | 3.65, the runner-up in a different direction |
| t8 readable daylight (3D) | 0.135 | 2.2 | 4 | 4 | 4 | 4 | 3.46 |
| t4 hollow trunk interior | 0.216 | 3.6 | 4 | 4 | 2 | 2 | 3.28 |
| t1 / t5 / t2 (paintings) | 0.10-0.17 | 1.7-2.8 | 3-4 | 4 | 1-2 | 3 | 2.41-2.94 |

t7 is built in M3 (SCOPE.md "M3": the model, budget, performance, checks and compromises). If Michael prefers light
shafts, t6 is the fallback: the same geometry, with a green-gold palette and additive shaft cards.

**Michael, 2026-09-30:** "t7 is the right direction, let's aim for a richer art pass. It's a very good first step!"
Art pass 2 (`forest_art2.py`, Blender-built with baked vertex colour; SCOPE.md) replaced M3 as the production art the same day.

**Michael, 2026-09-30, on pass 2:** "Much better! Are we doing anything about the dull static purple skybox?" The sky
rework followed: a painted twilight sky with drifting clouds and twinkling stars. **Michael:** "Small Star Road nod
sounds good to me": a rare, small shooting star high in the sky, on by default (a flag turns it off).

**Michael, 2026-09-30, on the stage music:** "is the cut at 1:33? there's a very obvious gap in the music there." The
loop had kept draft 2's 8th-note stop before the FINAL HIT; FINAL's last bar was re-rendered for the loop without it
(`music_loopend.py`). **Michael:** "New loop is excellent."

## 1. What a starter has to be

"Starter" here means Michael's sense (2026-09-29): **fair enough for game 1 of a set, with no severely game-altering
geometry and no strong character favourability.** RULESETS.md §3-5 derives this from why each stage has its status. The
hard rules are the ones whose breach got a stage banned or demoted:

| # | Rule | Where it comes from |
|---|---|---|
| 1 | **Static**, or moving slowly and predictably. Nothing that deals damage or knockback | Every hazard stage was banned; Fountain's platforms and Randall are the most motion a starter has |
| 2 | **Symmetric** left and right: collision, blast zones, camera | Striking assumes neither side is better. The vanilla asymmetries are small (Yoshi's Story's blast zones differ by 2.1, Dream Land's side platforms by 0.1) |
| 3 | **Grabbable ledges at both ends, no walk-offs** | Walk-offs are banned outright; Mute City's and Rainbow Cruise's missing ledges were cited |
| 4 | **No solid walls or ceilings on the stage's top**: only pass-through platforms above the floor | Walls give wall infinites: Corneria's fin, Peach's Castle, Yoshi's Island's ramps, Green Greens' blocks, Stadium's transformations |
| 5 | **No cave of life, no stalling terrain** | Yoshi's Island's blocks, Brinstar, Rainbow Cruise's paths |
| 6 | **The side under each ledge must not eat recoveries** more than Battlefield's does | Battlefield's lip is its one standing complaint [RULESETS S7] |
| 7 | **Blast zones and ceiling inside the starters' range, and not at its ends** | Yoshi's Story's small zones and Dream Land's big ones are the pool's two leans |
| 8 | **No camping geometry**: no pair of high platforms far apart; no perch within 20 of a ledge higher than the pool's highest (Dream Land's 30.2) | Kongo Jungle 64's circle camping got it banned |
| 9 | **A calm background** that never crosses the play plane, and a readable foreground | Fountain's reflection lag gets it banned in doubles; clutter is noise |
| 10 | **Its lean must be moderate and different** from the five starters' leans | A sixth starter earns its place with a new playmap, never an outlier (RULESETS §5) |

### Where the starters differ (measured)

`research/layouts.csv`; the five starters' range, with Pokémon Stadium (a counterpick now) apart:

| Axis | Five starters | Stadium | What it changes |
|---|---|---|---|
| Main width | 112 (YS) to 171.1 (FD) | 175.5 | Room for dash dancing and camping versus pressure |
| Ledge to side blast zone | 117.6 (YS) to 177.7 (DL) | 142.3 | Horizontal kill percents; recovery room |
| Ceiling above the floor | 168 (YS) to 250 (DL) | 180 | Vertical kills: Fox's up throw to up air versus floaty characters |
| Bottom below the floor | 91 (YS) to 146.3 (FoD) | 111 | Spikes and meteors |
| Platforms | 0 (FD) or 3 | 2 | Escape, tech and pressure options |
| Lowest platform | 23.5 (YS) to 30.1 (DL); FoD's sides sink below the floor and rise to 23.6 | 25 | Whether tilts hit through; how much landing and tech |
| Platform coverage (their widths over the stage's) | 0 (FD); **64-84%** for every 3-platform stage | 34% | How much of the floor has a platform over it |
| **Widest open floor** (no platform above) | **10.8-15.9** on every 3-platform stage; FD all of it | 50 | Room to play on the ground with nothing overhead |
| Outer platform's distance inside the ledge | −3.5 (YS, past the ledge) to 14.2 | 32.8 | Whether a ledge has a perch above it |
| Inset 10 below the ledge | 0 (FD) to 13.2 (BF's lip) | 7.6 | Recoveries that reach the side before the ledge |

**The gap in the pool.** Every platform starter covers the whole stage: nowhere on Battlefield, Yoshi's Story, Dream Land
or Fountain is more than 16 units of floor clear of a platform. Final Destination is all floor. Nothing sits between:
**open flanks where the ground game runs, with a platform game only in the centre.** Pokémon Stadium has that shape (50
open, 34% covered). But Stadium is a counterpick for its size, its low ceiling and its transformations, not for its
platforms [RULESETS §3]. A median-sized, median-blast-zone stage with open flanks and a central platform set is a new
playmap, and nothing in the pool rules it out.

## 2. The shared body

All three candidates share one body, set at the starters' median so the platform layout is the only new variable. The
spec lives in `layouts.py`, `BODY`, `BLAST` and `CAMERA`:

- **Ledges at ±70**, 140 wide: between Battlefield's 136.8 and Dream Land's 154.5; the five starters average 140.2.
- **Floor flat at y = 0 to the ledges.** No slanted edges: Yoshi's Story's slope is a quirk, not a feature to copy.
- **The side under each ledge:** a straight bark wall for 6, then the roots slope in. It sits 3.5 in at 10 below the
  ledge (Yoshi's Story 3.3, Fountain 1.9, Battlefield 13.2) and 12.3 in at 20, with the underside at −40.
  - No lip. A recovery aimed at the ledge meets a wall first, never an overhang.
  - Geno's Star Road slides along a steep wall (DESIGN §5 of Geno's).
- **Blast zones ±225 / 200 / −120.** That is 155 past each ledge (Battlefield 155.6, the median), the ceiling at the
  median 200, and the bottom 120 below (between Battlefield's 108.8 and the median 123).
- **Camera** x ±160, y −55 to 140, centred on (0, 30): Battlefield's proportions. The general points must include the
  camera-centre point 148: Stadium lacks it, so the engine ignores its camera points and uses a default range
  (`research/starters.md`).
- **Spawns** are symmetric on the floor at ±45 to ±50, plus two on the platforms. Respawns sit at 80 high (Battlefield's
  80).

## 3. Three layouts

Diagrams are at the same scale as the starters: `research/layout_<name>.svg` shows each candidate over its nearest starter,
and `research/layouts_over_starters_panels.svg` shows all nine side by side. Numbers are world units, floor at 0.

| | A. Clearing | B. Twin Boughs | C. Hollow |
|---|---|---|---|
| Platforms | 1: x −27 to 27 (54 wide) at **28** | 2: x ±10 to ±40 (30 wide each) at **28**; a 20 gap between them | 3: centre log x ±16 (32 wide) at **18**; side caps x ±34 to ±60 (26 wide) at **30** |
| Coverage | 38.6% | 42.9% | 60% |
| Widest open floor | **43** (each flank) | **30** (each flank) | 18 |
| Outer platform inside the ledge | 43 | 30 | 10 (Battlefield 10.8) |
| Nearest starter (overlay) | Battlefield | Pokémon Stadium | Battlefield |
| What's new | The first **one-platform** starter: FD's ground at the flanks, one cap in the middle | A **split cap** over the centre: platform play in the middle, open flanks | The **inverted triangle**: the centre is the *lowest* platform, the high ground is at the sides |

Every measured value (`research/layouts.csv`) sits inside the five starters' range with one exception: how far the
outermost platform sits inside the ledge. A is 43 and B is 30; the platform starters run −3.5 to 14.2, and Stadium is
32.8. Together with the flanks' open floor, which is inside the range only because Final Destination is all floor, this
is the point: the gap between the platform stages and Final Destination. C stays inside the range on every axis.

### A. Clearing (one wide mushroom cap)

- **Neutral:** at each flank, 43 units of Final Destination: dash dancing, lasers and grounded zoning with nothing
  overhead. In the middle, one cap to land on, pressure from and escape to.
- **Platform movement and tech:** there is only one platform, so no platform-to-platform play. Wavelands, shield drops
  and platform tech chases happen in the middle only. At 28 it is Battlefield's side-platform height: up tilts and up
  smashes reach it as they do there.
- **Edgeguarding and recovery:** Final Destination's ledges. No side platform for the edgeguarder to wait on, or for a
  recovering fighter to land on. The body's straight wall and moderate slope forgive more than Battlefield's lip.
- **Combos and juggles:** near the ledges, Final Destination's chaingrabs, Marth's kens and Falco's pillars run into the
  edge. In the middle, the cap extends juggles and gives the juggled fighter one landing spot.
- **Camping:** there's nothing to circle, and a fighter sitting on one cap is under every up tilt.
- **Lean: toward Final Destination's archetypes, softened.** It helps grapplers and chaingrabbers (the Ice Climbers,
  Marth) and laser users (Fox, Falco) on the flanks. It hurts floaty and platform characters (Jigglypuff, Peach, Sheik)
  less than Final Destination does.
- **Geno:** his best case. The Whirl's ground lane runs 43 uninterrupted, and the Beam passes under the cap. The cap is
  the opponent's way over his zoning, and the median width keeps his lanes shorter than Final Destination's. **Mild home
  field.**

### B. Twin Boughs (two inboard branches)

- **Neutral:** 30 units of open ground at each flank. Over the centre, two boughs side by side at 28. The 20 gap between
  them opens the space above to anyone jumping up through it, and air drift crosses it.
- **Platform movement and tech:** the most of the three. Wavelands from bough to bough, shield drops, tech chases on
  either one, and the pass-through gap. At 28, every fighter's full hop clears it except Jigglypuff's, Kirby's (both
  multi-jumpers) and Ganondorf's (27.3). Dream Land's 30.1 is out of full-hop reach for Mario, Doctor Mario, Game &
  Watch and Link (full hops near 29, from `cast_attributes.csv`).
- **Edgeguarding and recovery:** as in A, with no perch above either ledge.
- **Combos and juggles:** in the centre, the boughs give Battlefield's side-platform juggles (up air to platform,
  platform tech chases). At the flanks, Final Destination's.
- **Camping:** two platforms at one height is the Kongo Jungle 64 pattern, but neither of its ingredients is here. The
  boughs are low (28, reachable from the ground), 20 apart rather than wide apart, and the ceiling is the median, not a
  high one. **This is the risk to test** (§5).
- **Lean: balanced.** The flanks serve grounded, projectile and grab characters; the centre serves platform and floaty
  ones. It is Pokémon Stadium's two-platform idea turned inward, on a stage 35 narrower with its ceiling 20 higher, and
  without the transformations that made Stadium a counterpick.
- **Geno:** neutral. His lanes are 30 long, and the boughs give opponents cover over the Beam and a route past the
  Whirl. His Blast marks the floor under a target, so it answers campers on the boughs.

### C. Hollow (the inverted triangle)

- **Neutral:** a low log (18) in the centre, the most contested spot, so the centre fight happens on and under a low
  platform. The high caps (30) sit near the ledges.
- **Platform movement and tech:** low-platform play in the centre, like Yoshi's Story's lows but lower: shine and SHFFL
  on the platform, and tilts through it. At 18 it is lower than any static starter platform (Yoshi's Story's 23.45); only
  Fountain's moving platforms pass through that height.
- **Edgeguarding and recovery:** the side caps are Battlefield-like perches for ledge trapping (10 inside the ledge, as
  Battlefield's 10.8; at 30, Dream Land's height, the pool's highest near a ledge).
- **Combos and juggles:** a fighter retreating from the centre goes *toward* the ledges and the high caps. That inverts
  Battlefield's and Dream Land's retreat upward to the centre top.
- **Camping:** nothing to circle; the centre is too low to camp.
- **Lean: toward Yoshi's Story's fast fallers and platform characters (Fox, Falco, Sheik, Marth)**, milder than Yoshi's
  Story because the blast zones are the median.
- **Geno:** neutral. The log stands clear of his standing projectiles and the ground lane.
- **Why it's third:** it adds a second Yoshi's Story-style lean to the pool rather than filling the gap. The
  first version (sides at 40) broke rule 8 and was retuned to 30 to pass.

### Recommendation: **B, Twin Boughs** (Michael picked A, §0)

It fills the gap in §1, open flanks with a central platform game, while leaning least toward any archetype. It is also
the least favourable of the three to Geno, which is what "not a home-field stage" asks for.
- A is the purest statement of the gap but leans toward Final Destination's archetypes and gives Geno the most room.
- C is the most novel, but it duplicates Yoshi's Story's lean.

B's one open question, bough camping, is measurable before any art exists (§5).

## 4. Forest Maze: art direction

**The setting** (SMRPG, 1996): a dense wood of huge trunks, giant mushrooms, fallen logs and hollow stumps under a closed
canopy, lit by shafts of light through the leaves. Wiggler wanders it, and so do Geno's first scenes.

**Adapted to Melee's look:**
- Melee's polygon budget, texturing and lighting.
- Painted textures, with no pixel art dropped in.
- Soft warm key light from above left through the canopy, with a cool fill.
- Distance fog for depth, as Melee's own stages use per gobj.

**The foreground (the play plane) reads first:**
- **The main stage** is the top of a colossal mossy stump. A flat, cut-grain top with a mossy rim stops exactly at the
  ledges. Straight bark down 6 under each ledge, then the root flare slopes in: the collision profile, drawn.
- **The platforms** (B: two boughs) are thick horizontal branches from trunks set back in depth.
  - Their top surface sits exactly at 28 and ends exactly at ±10 and ±40.
  - The foliage and bark underside hangs below the line and never rises above it.
  - The trunks holding them sit well behind the play plane, darker and desaturated, so they read as background, not
    walls. A shelf mushroom or a mushroom cap does the same job for layouts A and C.
- **The rule for every platform edge:** the collision line is the top of the visible silhouette, within half a unit. It
  is measured, not eyeballed: a render of the stage with the collision drawn over it, the edge pixels compared per
  platform, as the Battlefield probe below does.

**The background (calm, layered, no hazards):**
1. The middle distance: trunks and giant mushroom stems in two or three depth layers, fading into warm green fog.
2. The canopy: a ceiling of leaves with slow-drifting light shafts, so it stays readable and never flashes.
3. Far back: the maze's pale green haze, and a hint of the Forest Maze's winding path.
4. Motion is ambient only: a few leaves drifting (a stage particle bank, sparse), and swaying light. **Wiggler**, if at
   all, walks slowly far in the back, small and never near the play plane. Michael's call.

**Things to avoid:**
- a busy high-contrast floor texture;
- anything bright moving behind the fighters' heads;
- dark shadows under the platforms where a fighter's silhouette would vanish;
- a reflection effect (Fountain's lag).

**References** (local only):
- SMRPG's Wiggler sprites (SPR0287, SPR0127, SPR0130), decoded by `fx/smrpg_sprites.py` into `$MELEE_WORK/stage/ref/`.
- The Forest Maze's rooms are map tiles, not sprites. Capturing them means Mesen and a room warp in the Lua drive
  (`~/games/smrpg/work/drive.lua`), which is not done yet.
- Style targets from an image model, as Geno's were (ART.md), are a paid call and wait for Michael's go-ahead.
- The 2023 remake is a design reference only.

## 5. Tests before art (the measurements that decide the layout)

The body and layouts are specs (`layouts.py`). The greybox (SCOPE.md §5) makes each playable, and then:
1. **Geometry:** `starter_lab`, pointed at the new stage, must match the spec to 0.01 on every platform, both ledges,
   the blast zones and the camera range. That is the same check the six starters pass, 32 of 32.
2. **Bough camping (B):** Jigglypuff and Peach CPUs, or scripted hops, cycling bough to bough against Fox, Marth and
   Falco chasers. Measure how often the chaser can reach the camper per second, and the frames from a hop to a
   reachable position. Compare against the same drill on Battlefield's and Dream Land's platforms.
3. **Recovery:** every cast member's up-B into the ledge from below and level, 10 to 40 below. The rate of catches
   against Battlefield's and Final Destination's, and Geno's Star Road along the body's wall.
4. **Kill percents:** Fox's up throw to up air, Marth's forward smash at the ledge, and Geno's finishers
   (`kill_lab` / `finisher_lab`), against the median-blast-zone expectation.
5. **Michael plays it.** The greybox is for his hands before any art.

## 6. Decisions for Michael

1. **The layout:** B (recommended), A, or C, or a tweak of one.
2. **Its numbers:** the body's ±70 and the median blast zones, or shifted toward one side of the range.
3. **Wiggler in the background:** yes (small, slow, far back) or no.
4. **Style targets:** approve the paid image-model call for Forest Maze stage targets (ART.md's method).
5. **Music:** the arrangement (metal draft 2 or the electro GLADE), for the loop cut below.

## 7. Music: what the stage needs

- **The stage's music row.** `grGroundParam` has one row per StKind the file serves (the new StKind included, or the game
  hangs on load with "not found stage param"). The row holds:
  - the main song id and an optional alt id with its chance;
  - the sudden-death ids;
  - a behaviour flag (Battlefield's is 6, with a 12% alt).
- **A new HPS id:** `gr_forestmaze.hps` past the vanilla table, resolved as `ff_geno.hps` was (SCOPE.md §2.7).
- **A loop cut:** the vanilla starters' streams run 63-162 s and loop from a point 3.6-21.5 s in:

| Stage | Stream | Length | Loop starts |
|---|---|---|---|
| Battlefield | `sp_zako.hps` | 86.0 s | 10.75 s |
| Final Destination | `sp_end.hps` | 89.4 s | 5.38 s |
| Yoshi's Story | `ystory.hps` | 118.8 s | 14.34 s |
| Dream Land | `old_kb.hps` | 67.8 s | 3.58 s |
| Fountain of Dreams | `izumi.hps` | 162.5 s | 12.54 s |
| Pokémon Stadium | `pstadium.hps` | 62.9 s | 21.50 s |

- **What that means for the arrangement:**
  - Draft 2 is a 97 s piece ending on a final hit at 91.2 s. The stage needs an intro, then a body that loops without
    the final hit: the solo's last bar must lead back into the loop start.
  - HPS loops jump to a **block start**. Measured on Dream Land's `old_kb.hps` (2026-09-29): HAL's encoder does not
    keep blocks at 0x8000 per channel. Blocks 0-1 are full; from the loop block on they are 0x7F80, and the last few
    0x7F60. **So a block boundary, and the loop point, can fall on any 14-sample ADPCM frame (0.44 ms)**: cut a short
    block before the loop start, and the loop lands on the downbeat with no lead-in silence and no tempo change.
  - Stage streams are 32 kHz stereo DSP-ADPCM, as the fanfare was.
  - Loudness should match the vanilla stage streams (measure them, as the fanfare was matched).
- **What `hps.py` does today:**
  - `hps.py check old_kb.hps` decodes identically to vgmstream (max difference 0) and re-encodes at 42.8 dB SNR, with
    the same block count and loop block.
  - Its writer uses fixed 0x8000 blocks, so `encode --loop-start` rounds the loop down to a 1.792 s boundary.
  - **To do:** a variable block before the loop start, so the loop is exact.
  - **Then check in game:** a lab capturing `dsp.wav` across the loop point.
