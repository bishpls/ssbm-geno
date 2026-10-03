# How Geno was made

Geno was built with Claude Code (Anthropic's coding agent), directed by Michael Bishop. The work ran from 27 September to
2 October 2026: the first commit of the new fighter kind on the first day, a playable build with his own model, moveset,
sounds and menus by the third, and the Forest Maze stage with a moving sky by the fourth. Michael made the design calls.
Claude agents did the engineering, modelling, animation, effects, sound and stage work, in parallel, and measured every
change in the running game.

This document is about how that worked and what was hard. The numbers in it come from the project's own documents and
logs. Paths are relative to `projects/geno/` unless given in full; `DESIGN.md` is the design and its changelog,
`HANDOFF.md` the working manual, `ART.md` the look and the model, and `stage/SCOPE.md` and `stage/DESIGN.md` the stage.

## The method

### Michael directs; the agents build

Every design decision is Michael's, and `DESIGN.md` records each one with his words and the date. A few that shaped
the character:

- **A true zoner** (27 September). Smash has never quite had one, and the reference was Nu-13 in BlazBlue: Calamity
  Trigger: screen control that feels overwhelming to face (DESIGN.md §1).
- **No meter.** A per-character resource doesn't fit Melee's own design sensibility, so Geno Flash became the third
  star of down B instead of a super (DESIGN.md §4, §11).
- **Aggressive, not patient** (v1.2). "Exciting to play and to watch", the opposite of a camper: projectiles he runs in
  behind, a strong neutral air out of shield and as a crossup. He pays for it with fragility: weight 80 (it had been 88),
  a fall speed of 2.3, a finicky recovery (DESIGN.md §1, §3, §11).
- **Air speed and fall speed are the balance levers,** ahead of weight, because they set his offence and neutral as well
  as his defence (DESIGN.md §3).
- **Planted, not slippery** (v1.3, after his first hand playtest): a slower dash and run that visibly accelerate,
  jumpsquat 5, a lower full hop, less air drift (DESIGN.md changelog, v1.3).
- **Down B is either-or** (28 September). Holding to the end used to fire a Blast and then a Flash, and the Blast
  combo'd into the Flash. Now the release decides: a tap or an early release is the Blast, a hold to the third star is
  the Flash alone (DESIGN.md changelog).
- **The 1996 proportions,** a big round wooden head and big boots, with a floppy stocking cap like Link's, two orange
  paper curls and black eyes. The 2023 remake was a design reference only; nothing was extracted from it (ART.md
  "Decided"; HANDOFF.md §1).

He also gave notes from watching the agents' Dolphin windows, the way a director watches dailies: the first throws were
"too fast, no ka-chunk", so every throw gained a hold and a mechanical lock before its blast. Then "Sort of like a
shotgun pump-chunk-shot, it's very visually satisfying to prime the hit, then deliver the blast", so each throw gained a
prime beat, at a cost in frame advantage he accepted (DESIGN.md §6f). Every round of agent work ended with a local
review page in the browser: strips, before-and-after boards and in-game video with the game's own audio, judged in
game rather than in Blender (HANDOFF.md §2).

### Parallel agents, each in its own sandbox

Each workstream (the model, the throws, the aerials and specials, the effects, the fanfare, the crowd chant, the stage
and so on) was one agent on its own branch. Each had a git worktree of the project and a sandbox of its own: a worktree
of the decompilation on a matching branch, an APFS clone of the extracted disc, its own Dolphin profile and a work folder
(HANDOFF.md §3, §4). One command (`tools/machinima/melee/sandbox.sh NAME`) sets the environment variables every tool
honours, so an agent's builds and test runs never touch the shared disc.

Finished work merged into two integration branches, one for the project and one for the decompilation, in the same
order every time: merge both, resolve conflicts, re-measure the research, then the matching check (HANDOFF.md §4,
"Merging an agent's work"). The rules that came out of this were learned the hard way:

- An unguarded lab build once overwrote the shared decompilation's director and put a lab build on the main disc in
  place of Michael's playtest build. `build.py` now refuses to run from an agent's worktree unless it is pointed at a
  sandbox (HANDOFF.md §5).
- Every worktree shares one repository and so one stash list, and one agent's `stash pop` took another agent's stash.
  Work in progress is committed to its own branch instead (HANDOFF.md §5).
- Frame dumps run 50-100 MB a second of play, and once filled the disk to 98%. Frames are deleted once their strips and
  videos exist (HANDOFF.md §2, §4).

### Labs: the game measures every change

The labs are the core of the method. `tools/machinima/melee/build.py` compiles a director into the decompilation: it
boots straight into a match or into the game's own menus, writes scripted controller input, moves the camera and fires
cues every frame, and reports through the game's own debug output (`OSReport`) what happened: motion-state changes,
every hit with its damage, hitboxes, positions, percent (`tools/machinima/README.md`). `dolphin.py` runs the build in
Dolphin headless with pinned settings, dumping every frame and the audio.

So a claim like "forward smash hits on frame 15" or "the back throw kills Fox at 140% with no DI" is a lab run, not a
reading of the data. A kill-percent sweep reads only the log, so 60 tests run in about three minutes (HANDOFF.md §4).
There are 68 lab scripts for the fighter in `director/` and 9 more for the stage in `stage/director/`. Michael's own
playtests cover the crash hunting: CPU soak tests caught nothing in 13 runs, so Michael dropped them as a merge
step (HANDOFF.md §4).

The measurements themselves get checked. The lag counter that the stage's performance numbers depend on was once
silently dead: a second build hook re-inserted an older block of code ahead of the lag call, so it never fired, and the
first lag measurements were void. Now every performance run stalls the game for 40 ms at frame 60 on purpose
and aborts unless that stall logs a lag frame (stage/SCOPE.md, "The 07:49 incident").

### The matching build

Every change to the game's code sits inside `#ifndef MUST_MATCH`. With the flag set, the same tree still compiles to
the retail `main.dol` byte for byte (SHA-1 `08e0bf20134d...`), and that check runs after every merge (HANDOFF.md §1,
§4). It keeps the project honest about what it changed: nothing reaches the original game's code paths except through
a guarded hook.

## The hardest problems

### A 27th fighter in an engine built for 26

Geno is fighter kind 0x22, and kind 0x21 had to stay the engine's "none" value, so every per-character table grew to
0x23 entries (decompilation commit "New fighter kind 0x22 (Geno), scaffold stage"). The tables nobody thinks about were
the problem:

- **Invisible hands.** A visibility group without a default stays hidden. Geno's spawn and respawn callback has to set
  every group to its default model, or his hands render hidden (`ftGe_Init_OnDeath` in the decompilation;
  HANDOFF.md §5).
- **The post-match freeze.** The results screen read three per-character tables past their ends for kind 0x22: the
  series emblem, the victory-pose files, and a scale table that gave him scale 0, which asserts in the knockback code.
  He borrows Mario's rows there.
- **Kirby read garbage.** Kirby's copy-hat preload walks every character kind, and its table stopped at 0x20, so
  kind 0x22 read the next table's bytes as a pointer, in any VS match with a Kirby in it. The same audit found the CPU's
  attack tables and the VS records list (both in the decompilation's history, "Per-kind tables Geno reads past").
- **The GPU misparsed a model.** The GameCube reads display lists only from 32-byte boundaries, and HSDRaw wrote small
  blocks on 4-byte boundaries. The Whirl's borrowed model landed misaligned and the GPU misread it on every frame it was
  on screen. datkit now flags every buffer it clones as aligned, and `datkit pobjcheck` checks new models.
- **Throws ride the wrong joint.** A thrown opponent rides the thrower's `ThrowN` joint, not the one the decompilation's
  parts enum suggests (it is one entry short), and plays shared victim animations on a separate 52-node skeleton
  (HANDOFF.md §5).

### Frame data that holds in game

The design gives every move a target (`DESIGN.md` §5-6), and the labs check it on the production build: every normal
hits on its designed frame, and the tilts, smashes and grab connect at their measured tips (DESIGN.md §6b, "Measured").
Neutral air comes out on frame 3. Reach, hitbox size and disjoint are set as percentiles of the cast, measured by
replaying each cast member's move scripts on their own skeletons (`research/cast_moves.md`): Double Punch is the long
disjoint, set at about the 85th percentile of reach (30.9 units, measured); the gun blasts' disjoint sits at or above the
top of the cast, the grab's at the 33rd percentile.

The design is written as invariants the labs assert, because Melee has no combo breaker and every loop has to end on
its own (DESIGN.md §8). One example is the shield gap: no sequence of his hits on a shield may leave fewer than 5 frames
between shieldstun ending and the next hit. The Whirl's grind hits land 15, 28 and 41 frames after contact, each leaving
that gap, measured against Fox in every case (HANDOFF.md §5).

### The throws

The invariant was no regrab on Fox, Falco or Falcon from 0 to 60% (DESIGN.md §6f). Each throw is one of his weapons,
built in beats, and measured on Fox at Final Destination:

- **The up throw** used to peak around 17 units and fall back onto him. It now peaks at 27.6 units on Fox at 0%,
  between Fox's own up throw (27.1) and Falco's (35.5).
- **Its three Star Gun stars** are real projectiles, and at first full DI kept all three off. The levers were chosen by
  replaying salvos against the logged flights offline (`director/labs/star_sim.py`, which matched the game's hits frame
  for frame): aim before the release, faster stars, and the widest star sprayed the way their knockback carries them.
  Now all three hit with no DI and with full DI either way at 0-80% on all three opponents.
- **The regrab.** With no DI, a dash grab out of the up throw caught Fox at 0 and 20%. After the aim moved before the
  release, none of twelve timed attempts did.

### The specials

- **The Geno Beam's cancel** matches Samus's charge-shot cancel frame for frame (8 frames), and the air cancel follows
  Mewtwo's, except that the stars are lost rather than stored: Michael's call, to set him apart from Samus and Mewtwo
  (HANDOFF.md §6.2; DESIGN.md §5). A timed release, SMRPG's timed hit, measured 18.7 damage against 17 for the
  automatic release.
- **Geno Blast's columns** used to end at Geno's own height when he cast in the air, so an aerial Blast whiffed. Each
  column now raycasts to the floor under its own mark (HANDOFF.md §6.2).
- **The Geno Whirl** pressed on through a shield and ended past the shielder's centre. It now presses only up to the
  shield's front, is knocked back by each grind hit and settles 5 units in front (DESIGN.md changelog, 29 September).

### The model, built from code

The model is built in Blender by script, not by an image-to-3D model: `model/geno_geo.py` generates every mesh, UV and
skin weight on the rig's skeleton, `model/paint.py` paints the textures procedurally in 3D, and `model/build.sh` runs it
end to end (ART.md "Look"; the model's first commit). Image generation made style targets only.

- **The budget is the cast's.** 5,034 triangles, where the cast clusters at 4,600-5,050; a 397-triangle low model for
  the off-screen magnifier (Mario's is 332, Link's 391); a 71-joint skeleton, plus three joints appended later for the
  Flash's cannon (ART.md "Budget"; HANDOFF.md §5; DESIGN.md §12).
- **Melee's lighting.** It lifts textures about 1.2x on the lit side, and a white highlight at shininess 50 on every
  specular material blew out the nose and washed the wood to peach. Gate 1d, judged in game beside Mario, went matte,
  with dim specular maps only on wood, leather and brass (the way Mario's shoes are set up), and rebuilt the double-sided paper curls as two single-sided
  layers, because the GameCube lit their back faces dark brown (the model's Gate 1d commit; HANDOFF.md §5).
- **Weapon forms.** His hands transform as in SMRPG: Finger Shot tubes, Hand Gun, Star Gun, Hand Cannon, the Beam's
  barrel and the rocket fist, each a model part the move scripts switch to. A form adds 104-180 triangles on its hand.
  For Geno Flash his whole body becomes SMRPG's blue-and-gold cannon on its carriage, 1,344 triangles shown only while
  his body is hidden, with his hurtboxes curled inside it (ART.md "Weapon forms"; DESIGN.md §12).
- **Cape and cap** are Melee dynamics chains with no hurtboxes, as Marth's and Ganondorf's capes are: four chains, three
  body spheres to keep the back off his chest, waist and pelvis, tuned as felt (ART.md "Cape and scarf").
- **The capelet's front panels** cut through his arms when they rose. Collision spheres couldn't fix it, so the fix is
  in the skinning, fitted by measuring the panel area inside the arms on every action's frames: with an arm raised, the
  cut area fell from 1.27 to 0.36 square units a frame (ART.md "Cape and scarf").
- **Six costumes,** Michael's set: Geno and the SMRPG party's colours (Mario, Bowser, Mallow, Peach) plus a black-and-red
  Dark. Each recolours the felt in OKLab and keeps the texture's shading. The menu portraits and stock icons are renders
  of the production model in game, difference-matted from a pass on black and a pass on white (DESIGN.md §12).

### Limb growth, and what it costs

Melee's fighters grow their limbs on hit frames: Mario's jab hand is 2.24 times its size on its first active frame
(`research/fist_read.md`). Geno's fists and grabs grow the same way, but there's a catch: a grown limb's hurtboxes grow
with it, and the cast's hitboxes ride the grown bone while Geno's don't, so the growth comes straight off his
disjoint. `research/growth_cost.md` measures it against the Mario family, and the grab was set by building candidates
until it cost exactly what Mario's does: 1.83x for the grab and 2.0x for the dash grab, a disjoint cost of 0.67 and
0.80 units (DESIGN.md changelog, 29 September).

### Effects, measured against the cast

Geno has his own effect file, `EfGeData.dat`, loaded with him: particle generators and textures drawn in code in
SMRPG's visual vocabulary (`fx/efge.py`; `fx/EFFECTS.md` maps Melee's effect system). The gun normals' reach is muzzle
bursts no hurtbox follows, and at first nothing was drawn there. The measurement came first: across the cast, a drawn
disjoint typically reaches 0.90-1.01 of its hitboxes' reach past the body (Marth's forward smash 0.90, Ness's aerials
0.94, Falco's laser 1.01), and Geno's drew 0.0-0.1. Now every gun normal draws 0.82-0.99 (DESIGN.md changelog, "the gun
normals show their hits"; HANDOFF.md §7).

### Sound: from the cartridge, and spliced, never cloned

Geno's sounds are his own bank in the game's sound system (bank 55, `geno.ssm`; HANDOFF.md §5):

- **His attacks** are SMRPG's own sound effects, rendered from the cartridge by its own sound driver and edited to Melee
  timing (`sound/rom_tools/`). Each gun sound's key transient was then checked against the move's first active frame in
  the game's audio: the Hand Cannon's boom landed 11.9 frames late, and now every gun sound lands within 0.3 frames of
  its shot (`sound/soundsync.py`).
- **His movement sounds** are synthesized from scratch for a wooden doll, 25 of them (knocks, clacks, creaks, cape
  flaps), levelled against Melee's own movement sounds through the game's gain chain (`sound/synth.py`, `sound/melee_ref.py`). Like SMRPG's
  Geno he is otherwise silent: no voice, no KO cry (DESIGN.md §12).
- **The announcer's "Geno!"** is a splice of the announcer's own recorded syllables. Michael's rule was no voice
  cloning, no text-to-speech and no voice conversion of the announcer or the crowd. The splices were cut and joined
  with pitch-synchronous editing and crossfades, with speech models used only to rank candidates (HANDOFF.md §1, §6.4).
- **The crowd's "Ge-no! Ge-no!"** is spliced the same way from the crowd's own chants: Pichu's "ch" and "PEE", Ness's
  "n" and Mario's "o" lowered three semitones. In game, the captured audio correlates 0.98 with it (DESIGN.md changelog,
  28 September).
- **His victory fanfare** is our own orchestral arrangement of SMRPG's post-battle level-up music, transcribed from the
  cartridge's sequence data and checked against its sound driver: 7.99 s at -15.0 LUFS, like Mario's. In the results
  screen's captured audio it correlates 0.53, against 0.04 for Mario's fanfare (DESIGN.md §12; HANDOFF.md §6.3). Its
  stream writer, `tools/machinima/melee/audio/hps.py`, decodes all 20 vanilla fanfares bit-exactly.

### The Forest Maze

A new starter stage in SMRPG's forest, meant to be fair for game 1 of a set (stage/DESIGN.md §1). The layout is
Michael's pick of three: "Stage A, the single-plat option, is my pick", one mushroom cap at height 28 over a floor with
ledges at ±70. It adds a playmap the starter list lacks: open flanks for the ground game and a platform game only in the
centre (stage/DESIGN.md §0-1).

- **A real slot.** The stage select stores each stage's kind in one byte, so a new stage number couldn't fit. Melee
  already had a dummied stage in the VS range (internally "Akaneia", with no data), and the Forest Maze takes it: no
  table grows, and it's always unlocked (stage/SCOPE.md, "M1: built").
- **Checked against the spec.** `starter_lab` passes 5 of 5 (the cap, floor, ledges, blast zones and camera range), and
  the drawn edges sit within a pixel of the collision (stage/SCOPE.md).
- **Art, measured.** The art is scripted Blender with light baked into vertex colours, the way Melee's own stages are
  drawn. The first production pass was 1,392 triangles and 127 KB; the vanilla stages run 8.3k-13.6k triangles and
  452-1,119 KB. The second pass and the sky brought it to 8,042 triangles and 868 KB. The CPU is busy 7.67 ms a frame
  against Battlefield's 8.26 (stage/SCOPE.md, M3, "Art pass 2" and "The sky").
- **Readable.** A readability score (the background's contrast against fighters' mid tones, penalised for busy detail;
  `stage/lookmetrics.py`) has a minimum of 0.283 at the reference framing over the sky's whole animation cycle, against
  Final Destination's 0.275. The largest frame-to-frame change in the sky's brightness is 0.0017, against Battlefield's
  0.024 (stage/SCOPE.md, "The sky").
- **The sky moves** as Melee's do, from the map file's own animation set: twinkling star fields, cloud banks drifting on
  150-240 s loops, fireflies, and a small shooting star for Star Road. It wraps the stage, so a camera orbiting ±60°
  sees no void (stage/SCOPE.md, "The sky").
- **The music** is our own metal arrangement of the Forest Maze theme, cut into a stage loop: a 9.6 s intro, then 81.6 s
  (68 bars at 200 BPM) that loops. The first cut had a 150 ms hole at every wrap ("there's a very obvious gap in the
  music there"), so the loop's last bar was re-rendered without it. The sample-based renderer isn't repeatable under load,
  so each of its renders repeats until two runs agree sample for sample. Michael: "New loop is excellent" (stage/SCOPE.md; stage/DESIGN.md
  §0).

### The challenger screen and the name tag

Geno arrives the way Melee's unlockable characters do. His NEW CHALLENGER silhouette is rendered in game from his
model, matted and quantised to the same 4-bit format as the eleven vanilla silhouettes, and beating him opens the prize
screen with his own two messages (decompilation: `gmapproach.c`, `ifprize.c`).

In SMRPG, the star spirit's own name is "♡♪!?". Melee's in-match font has neither glyph, so the heart and the note were
drawn in code at the font's weight, appended to the font as glyphs 287 and 288, and added to two blank keys of the
name-entry keyboard. Existing glyphs are untouched: before-and-after captures are pixel-identical outside the two new keys
(decompilation: `sislib_font_geno.inc`).

An in-engine reveal trailer, filmed with the same director, is in production.

## Getting it to players

The release was checked the same way as everything else, by measuring. A fresh clone of doldecomp at the base commit
takes the patch cleanly and still builds the retail game byte for byte, and with the playtest's director it rebuilds
the playtest's game byte for byte too. From a clean clone, the build tools rebuild the model, the fighter files,
Kirby's cap, the effects, the announcer's call, the stage and the sound tables byte-identical to the playtest build's,
and the sound bank from the cartridge in about a minute (the same on every run since its emulator powers on with zeroed
RAM). The player patch, applied to a clean retail ISO, gives the Geno ISO byte for byte with both the old and the new
xdelta, and a wrong source ISO is rejected. A lab with an emulated memory card showed that the play build never touches a
player's save: a whole session wrote nothing, while the game's own boot created its save file on the same card at
once. On a fresh save, with none of Melee's unlocks, Geno and the Forest Maze are both there, and Random can pick the
stage (`HOW-TO-PLAY.md`).

## By the numbers

- 392 commits to the project between 27 September and 2 October 2026, and 145 on the decompilation.
- 36 workstream branches, merged into two integration branches.
- 77 lab scripts that drive the real game: 68 for the fighter, 9 for the stage.
- 90 files changed in the decompilation (7,746 lines added); the retail `main.dol` still rebuilds byte for byte.
- 217 Python files (38,446 lines) for the fighter and stage, and 5,820 lines of C# in datkit.
- 5,034 triangles, 71 joints, 6 costumes, and a design document revised through v1.5, with every call in its changelog.

## Still open

Single-player modes and the Japanese menu files are on hold, by Michael's call: the single-player select screens hide
Geno (Training excepted) rather than crash (HANDOFF.md §7; DESIGN.md §12).
