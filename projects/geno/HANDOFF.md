# Geno: handoff (2026-09-28)

Michael is moving the Geno work to another Claude account. That session can't resume the agents that were running here,
so everything it needs is in this file, the repo, and the local folders it points to. Read this first, then
`projects/geno/DESIGN.md` (the design, frame data, every decision and its changelog), `projects/geno/ART.md` (the look,
the model, the weapon-form interface), the repo's `CLAUDE.md`, and `docs/SESSIONS.md` (how parallel work is split).

## 0. Where things stand

Geno (Super Mario RPG) is a new Melee fighter, kind 0x22, built on doldecomp: his own model, skeleton, animations,
moveset, specials, sounds, menus, results screen and Kirby copy. Everything reviewed is merged:

| Integration branch | Where | Tip |
|---|---|---|
| repo `geno` | `~/animation-pipeline-geno` | 7dba9b2 |
| decomp `ext` | `~/games/melee/decomp` | 97841e5 |

**Merged and verified in game:**
- the Gate 2 production model (weapon forms, hand and cap poses);
- cape and cap physics;
- locomotion and every movement state (turn, jumps, falls, landings, crouch, platform drop, teeter);
- defence, damage and knockdown states;
- ledge work and get-ups;
- items, the taunt, the entrance and the idles;
- victory poses (`GmRstMGe.dat`);
- production ground attacks, the grab and CatchWait;
- Kirby's copy and his Geno hat (`rig/kirby_hat.py build --install`; DESIGN §12);
- the Geno Beam v1.4 (no store; it fires itself just past the third star);
- the relaxed default hand.

The original matching build still matches (`08e0bf20`), and a 3-minute CPU soak (Geno against Kirby) runs clean.

**Four workstreams were paused mid-way** (§6): the throws, the aerials and specials, the victory fanfare, and the crowd
cheer. Each has its own branches, worktree and sandbox, and all its work, finished or not, is committed there. Nothing
lives only in a dirty tree.

**The demo build.** Michael plays this: `~/animation-pipeline-geno-demo/projects/geno/demo.sh`, on branch `geno-demo`
with sandbox `geno-demo`. It's `geno` plus the committed, pre-WIP state of the throws, the aerials and specials, and the
fanfare. The crowd cheer isn't in it. (Its CPU soak was reported as passing but actually stopped at frame 3639 of
11000 with Dolphin exiting; see §4's note on soaks.)

**Suggested order:**
1. Aerials and specials (§6.2): nearly done; it needs its report, review and merge.
2. Fanfare (§6.3): nearly done; Michael listens, then merge.
3. Throws (§6.1): verify and finish.
4. Crowd cheer (§6.4): candidates, Michael's pick, then inject.
5. The backlog (§7).

## 1. Rules (not negotiable)

- **Game data never enters git:** disc files, extracted assets, builds, renders or frame dumps, game audio or SFX
  captures, reference recordings, ROM-derived material, `.hps`/`.dat` outputs. They live under `~/games/...`. The ROM stays
  at `~/games/smrpg`. The repo is public; the `geno` branches have never been pushed.
- **Never push or publish without asking.** Scan the whole history for keys before any push. Commit with Michael's
  identity. Keys live in `.env` / `.env.local`; never print or commit them. Log paid API calls in `tools/ledger.jsonl`,
  and don't make one without asking.
- **Never extract from the 2023 remake.** Its art is a design reference only.
- **Public release policy (Michael, 2026-10-02):** ssbm-geno ships source (no game data in git, ever) **and** an xdelta
  patch for players applied to their own NTSC 1.02 ISO, as a GitHub release asset only. That one artifact may carry
  game-derived data (the compiled DOL, the SMRPG-derived sound bank, the announcer splice). Rendered audio of our own
  arrangements is included in the repo. Licence: MIT for code, CC BY-NC 4.0 for docs and art. Publishing still waits
  on Michael's go.
- **Unlocks (Michael, 2026-10-02):** Geno and the Forest Maze are always available, with no unlock conditions. "Anyway
  going through the trouble of downloading this will have already long been through the single-player unlock
  experience." Geno: forced unlocked in VS and Training (`mncharsel.c`), hidden in the 1P modes (no save row for him).
  The Forest Maze: `gm_80164430` treats stages outside its 11-entry unlock table as unlocked, and kind 0x15 isn't in it.
  The player build may unlock all of Melee's own content too.
- **Voices:** no voice cloning, TTS or voice conversion of the announcer or the crowd. The announcer's "Geno!" and the
  crowd cheer are splices of their real recordings (Michael's call, as a fan work).
- **Music:** our own arrangements only, never rips. References are analysed, not mixed in.
- **Video-generation models are off by default** (repo `CLAUDE.md`).
- **Decomp:** every non-matching change goes inside `#ifndef MUST_MATCH`, and the matching build must still match
  (§4). Some sources are Shift-JIS, so use `grep -a`.
- **Peer GPU box:** game-derived data only in `/srv/work`, never the bucket. Don't spin it up without asking.

## 2. How Michael works

- **He makes the design calls.** Bring a recommendation, not a survey, and one question at a time when you can. He
  answers fast and changes his mind when he sees something in game. Record every call in DESIGN.md (the relevant row
  plus the changelog) or ART.md "Decided".
- **Review in the browser.** Every review round ends with a local page opened in Chrome:
  `tools/machinima/melee/art/review_page.py OUT.html "Title" --open [--note ...] FILE::caption ...`. It takes images and
  mp4s, and `#Heading` starts a section. Show in-game video with game audio: Dolphin frames plus `dsp.wav` through
  ffmpeg. Game renders never go to claude.ai Artifacts.
- **Judge in game, not in Blender or offline.** Materials and poses that looked right in Blender broke under Melee's
  lighting. Verify any critic's or agent's claim at full resolution before acting on it.
- **He watches the agents' Dolphin windows** and gives notes from them: throws "too fast, no ka-chunk", "the up throw
  barely displaces", "down air hitbox is short", and so on. Treat these as design input, fix them, and reply.
- **Machine limits:** 16 GB RAM, and the disk filled to 98% once from frame dumps (§4). Keep concurrent Dolphins to two
  (`DOLPHIN_SLOTS=2`), keep agents to about five at once, and delete frame PNGs once their strips and videos are made.
  Another session of his (a Melee hyperpop edit) sometimes runs its own Dolphins.

## 3. Where everything is

**Repo worktrees** (`git -C ~/animation-pipeline-geno worktree list`):

| Worktree `~/animation-pipeline-geno-*` | Branch | State |
|---|---|---|
| (none) | `geno` | integration |
| `demo` | `geno-demo` | Michael's demo build |
| `throws`, `atk-air`, `fanfare`, `cheer` | `geno-<name>` | **paused**, §6 |
| `anim`, `atk-ground`, `cape`, `kirby`, `model`, `moves`, `walk`, plus older `import`, `menus`, `motion`, `sound`, `spec` | various | merged; safe to remove |

**Decomp:**
- `~/games/melee/decomp` is branch `ext`, the integration branch.
- Each sandbox has a decomp worktree at `~/games/melee/sandbox/<name>/decomp` on branch `<name>`, in the same repo, so
  `git -C ~/games/melee/decomp merge geno-atk-air` works.
- `~/games/melee/decomp-match` is an older matching checkout (detached); the matching check now uses `build.py --matching`.
- `decomp-soback` belongs to the other session. Don't touch it.

**Sandboxes** (`~/games/melee/sandbox/<name>`):
- Each has `decomp/`, `disc/` (an APFS clone of the disc), `dolphin-user/`, `work/` (`rig/` and `movedata/` copied, the
  rest linked to the shared `~/games/melee/work`), plus `runs/` and `boards/`.
- On 2026-09-28 the finished sandboxes' frame PNGs were deleted; the paused ones' were kept.

**Shared local data:**
- `~/games/melee/disc`: the extracted disc. My labs used it, and `play.sh` defaults to it.
- `~/games/dolphin-play`: Michael's Dolphin profile with his controller set up.
- `~/games/melee/work/`:
  - `art/`: `model/` (the live model export `geno.gltf`/`.bin`, `geno_tex/`, and every board), `target/` (style targets and
    the remake reference crops), `motion/` (the cast study: `MOTION_STUDY.md`, per-action FK in `fk/<Code>/`,
    skeleton maps), `spec/`.
  - `rig/`: the build outputs; `out/` is what `play.sh` installs.
  - `movedata/`: the cast's measured moves.
  - `music/`: Forest Maze arrangements (`NOTES.md`) and `fanfare/` (§6.3).
  - `announcer/`: the "Geno!" splices (`NOTES.md`).
  - `sfxbank/`: his sound bank and the DSP-ADPCM tools.
  - `crowd/`: the cheer's work area.
  - `handoff/transcripts/`: full transcripts of this session and every agent (§8).
- `~/games/melee/sandbox/model_snap_2`: a complete, frozen Gate 2 model (`geno.gltf`, `.bin`, `_low`, `.melee.json`,
  `geno_tex/`). Build with `GENO_MODEL=<dir>`. A snapshot must include the `.bin` files; the first ones didn't.

## 4. Build, test, play

Run these from a repo worktree, using its `.venv`, a symlink to the main repo's. The working directory resets between
commands, so use absolute paths.

- **Blocks build and measurements:** `sh projects/geno/rig/remeasure.sh` builds `PlGe*.dat` and `GmRstMGe.dat` into
  `$MELEE_WORK/rig/out` from `rig.py`, `anims.py` and `moves.py`, then rewrites `projects/geno/research/*.md`. Commit the
  research whenever it moves.
  It rebuilds only Geno's movedata (`Ge.jsonl`); the cast's `$MELEE_WORK/movedata/<Xx>.jsonl` are static. When datkit
  `movedata` changes (2026-09-29: hurtboxes now grow with a scaled bone), regenerate the cast's files too and copy them
  to the main work folder, or a later remeasure quietly reverts the cast's numbers in the research.
- **The production model build:**
  1. `GENO_MODEL=1 .venv/bin/python projects/geno/rig/rig.py $W/rig_model.json` (`1` means the live export; a folder
     means a snapshot).
  2. `.venv/bin/python projects/geno/rig/anims.py $W/mr_actions.txt $W/anims.json`
  3. `tools/machinima/melee/datkit.sh fighter-build $W/rig_model.json $W/anims.json $DISC/files/PlMr.dat $DISC/files/PlCo.dat OUT Ge Geno 0`
- **Costumes:** with `GENO_MODEL` set, step 1 also writes a recoloured model folder per costume beside the rig json
  (`model/costumes.py`; `GENO_COSTUMES=Nr,Re,...` picks another set), and step 3 writes a `PlGe<Cc>.dat` for each. The
  decomp's `ftgeno_costumes.h` comes from `costumes.py --c`; regenerate it when the set changes.
- **Install:** delete the disc's old costume files (`rm $DISC/files/PlGe[A-Z][a-z].dat`, as `play.sh` does), then copy
  `OUT/PlGe*.dat` and `OUT/GmRstMGe.dat` to `$DISC/files/`, and `ff_geno.hps` to `$DISC/files/audio/`. Without
  `GmRstMGe.dat` the results screen can break. The game counts the costume files at boot, so a stale one would be offered.
- **Menu art** (after a model or costume change): `PORTRAIT_LAB=0,1,2,3` and then `PORTRAIT_LAB=4,5` builds of
  `director/portrait_lab.py`, each run at `--res 3`; `menus/portrait.py $MELEE_WORK/menuart RUN_A:0,1,2,3 RUN_B:4,5`;
  `menus/build.py $MELEE_WORK/menuart`; then `sh $MELEE_WORK/menus/out/install.sh` (it honours `MELEE_DISC`).
  `menus/reel.py` turns a capture into an mp4 with its game audio.
- **Labs:** `projects/geno/director/<lab>.py`, built with `tools/machinima/melee/build.py projects/geno <lab>`, which
  compiles the director into `$MELEE_DECOMP` and installs `main.dol`. Run with
  `DOLPHIN_SLOTS=2 tools/machinima/dolphin.py run $DISC/sys/main.dol OUT --frames N [--until 'DIRECTOR END'] --res 1|2 --quiet`.
  The game's OSReport lines land in `OUT/osreport.log`. Main labs:
  - `normals_lab`, `smash_charge_lab`, `angles_lab`, `ground_attacks_lab`, `dsmash_lab`;
  - `specials_lab`, `whirl_lab`, `starroad_lab`, `timed_lab` (atk-air), `aerials_lab` (atk-air);
  - `throws_lab` (throws; its watched sets `LAB_SET=look`, `cam34`, `match` log a sync slate, his animation frame and
    both fighters' hurtboxes per frame, for `--board` (before/after strips lined up on the blast) and `--line` (the
    forward throw's opponent against the rocket fist's line, in game; `rig/throwview.py --line` measures the same
    offline)), `kill_lab` (with `finisher_lab`, the cast's finishers the same way; both read only the log, so run them
    with `dolphin.py run ... --logonly`: no dumps, unthrottled, a 60-test sweep in ~3 minutes);
  - `pummel_ledge_getup_lab`, `ledge_floor_lab`, `defense_lab`;
  - `walk_lab`, `air_lab`, `items_lab`, `victory_lab`, `kirby_lab`, `cape_lab`, `form_lab` (`GENO_FORM_LAB=1`);
  - `capelet_lab` (the arms against the capelet's front panels, move by move with sync slates; `CAPE_CAM=q34|side|match`),
    `lowface_lab` (`LOWFACE_MODE=bubble`: the magnifier bubbles, the low models; `high`: the high models at the bubbles'
    pixels; `LOWFACE_FACE=-1` faces left);
  - `cast_look` (`CAST_LOOK`, `CAST_DIST`, `CAST_AT`, `CAST_X`, `CAST_PITCH`), `fx_scale_lab`, `cpu_soak`.
- **Parallel work:** `eval "$(sh tools/machinima/melee/sandbox.sh NAME)"` creates or points at a private sandbox and
  exports `MELEE_DECOMP`, `MELEE_DISC`, `MELEE_WORK` and `DOLPHIN_USER`. Every tool honours them. Give each agent one.
  - Keep long-lived sandboxes current with `git -C ~/games/melee/sandbox/NAME/decomp merge ext`. A stale one rendered
    Gate 2's hands hidden.
  - Every lab rewrites the decomp and disc it's pointed at.
  - Run the setup in Python or bash, not zsh, when the list of paths is in a variable. zsh doesn't word-split
    unquoted variables, which bit twice.
- **The matching check:** `.venv/bin/python tools/machinima/melee/build.py --matching` must end with the trophies line
  and `shasum build/GALE01/main.dol` = `08e0bf20134d...`. It copies the original DOL to the disc, so rebuild a lab
  afterwards.
- **Play:** `projects/geno/play.sh` (the main disc and `~/games/dolphin-play`; `GENO_COLL=1` shows hitboxes), or
  `demo.sh` on the demo branch. `play.sh` installs whatever is in `$MELEE_WORK/rig/out`, so build the production model
  there first.
- **Frame dumps:** a lab run at `--res 2` writes ~50-100 MB a second of play. After strips and mp4s exist, delete the
  PNG frames: `find RUN -name 'f[0-9][0-9][0-9][0-9][0-9].png' -delete`. The logs and wavs are small.

**Merging an agent's work:**
1. `git -C ~/animation-pipeline-geno merge --no-ff geno-<name>`, then `git -C ~/games/melee/decomp merge --no-ff geno-<name>`.
2. Resolve conflicts.
   - Two agents often add a director cue with the same number. Renumber, keeping `director.h`, `director.c` and
     `dsl.py`'s `CUE` in step.
   - The decomp's `src/melee/director/*` are copies `build.py` writes. Resolve them to the repo's merged copies.
3. `remeasure.sh`, and commit the research.
4. The matching check.
5. Tell any still-running agents what changed under them.

No CPU soaks (Michael, 2026-09-29): in 13 runs they never caught a bug, and his hand playtests stress the build further.
Crash hunting is his playtests plus the targeted labs. `cpu_soak` stays as a lab, not a merge step.

## 5. Hard-won facts (read before touching the area)

- **The public release (2026-10-02):** `release/slice.sh SLICE_DIR [GENO_REF] [EXT_REF]` rebuilds ssbm-geno (the trailer's
  production material stays out; `audio/` gets the two rendered arrangements); `release/keyscan.sh DIR` scans a tree
  and its whole history. The player build never touches a memory card (measured: `director/fresh_save_lab.py`'s card run
  wrote nothing over a whole session, while its cardboot control, the game's own boot, created the save at once), and
  it unlocks Melee's characters and stages in memory only (not All-Star mode). On a fresh save (`Menu(unlock=False)`)
  Geno and the Forest Maze are there and Random can pick the stage (the director's SSSRANDOM line: 19 entries, 29
  included). The 1P modes can't be booted into directly (Classic asserts in lbarchive.c): go through `boot='menu'`.
  The SNES capture zeroes Mesen2's power-on RAM; with its random default the dump often wouldn't render. The playtest
  DOL rebuilds byte for byte from a fresh doldecomp clone, `geno.patch` and the director it was built with.

- **Agent builds go to their sandbox:** `build.py` from an agent worktree (`animation-pipeline-<name>`) now refuses to
  run unless `MELEE_DECOMP` and `MELEE_DISC` are set (eval `sandbox.sh NAME`). On 2026-09-30 an unguarded lab build
  overwrote the shared decomp's director and put a lab DOL on the main disc in place of Michael's playtest build.

- **Never `git stash` in a worktree:** every Geno worktree shares one repository and so one stash list. One agent's
  `stash pop` took another agent's stash (2026-09-29; no damage, the pop conflicted). Commit WIP to your own branch.
- **`build.py --matching` puts the retail DOL on the disc it builds for.** On the main disc, always follow it with the play
  build and check that build succeeded (2026-09-30: a merge slip broke the play build after a matching check, and the
  main disc was left on retail Melee until it was fixed). After resolving conflicts in `director.c`, `director.h` or
  `dsl.py`, build before committing; the cue table is checked against the enum in a few lines of Python (all names and
  numbers equal).
- **Main's film kit is merged into geno (2ef4d85, 2026-09-30):** SO BACK's Melee type, keying, hard-edit grammar,
  Immediate XFB (no lost frame), `gamecam`/`glass` (cues 40/41) and `menu_hold`. Cue numbers: geno 1–25, main 40–41,
  the trailer 50 and up. `reset()` keeps geno's default `fresh=True` (stale moves cleared); main's films pass
  `fresh=False`. POS lines now end `hipx hipy vx vy kbx kby air jumps pct`, so the hip stays at fields 6–7. Builds take
  a lock and run ninja with 6 jobs (`MELEE_JOBS`). Boards drawn from captures after this merge include a frame the old
  captures lost (after script frame 7), so they shift by one against older boards. The merge's review:
  `~/games/melee/sandbox/geno-mainmerge/boards/geno_mainmerge_review.html`.
- **The trailer's director cues (2026-09-30):** 50–63 (round 1: star KO, slow motion, metal, trophy tools, enemies,
  costume respawn, HUD modes, item trace, pin and clear) and 64–68 (round 2: floor placement, the star-run contact KO,
  the Peach's Castle Banzai Bill via `grCastle_DirectorBill`, a bone trace, and a press on the first frame a state
  allows it). `projects/geno/trailer/lab/FEASIBILITY.md` lists them. **Resets now link the fighter to the floor line
  within ±10 of y = 0 under the new x** (a reset from the Forest Maze's cap had put him back on the cap; one just off
  the respawn platform asserted). On flat stages that's the line he was on: `whirl_shield_lab` still gives 15/28/41.
  A reset where no floor is found logs `RESET NOFLOOR`.
- **The trailer film crew's cues (Parts One and Three, 2026-10-02; branch geno-film1):** 75 `DIR_KBVEL` (a launch with no
  hit: knockback velocity, decaying as a hit's does), 76 `DIR_HOLDENTRY` (hold the entry's trophy stand: with
  `DIR_ANIMRATE` 0, a doll), 77 `DIR_EYES` (the eye texture's frame through `ftAnim_80070458`, so it holds through action
  changes), 78 `DIR_HOLDDEAD` (a star KO's respawn waits after the twinkle: a clean sky). `DIR_PERCENT` now also sets the
  HUD's copy (`Player_SetHUDDamage`), and `Menu(music=False)` mutes the menus' music for a scored plate. The montage crew
  numbers 69-74. HUD-on plates keep Melee's own projection and deliver the bottom 16:9 band (the 16:9 projection stretches
  the 2D HUD 1.47x): `projects/geno/trailer/film/part1_3/crew.py` (`hudcam`, `crop='hud'`).
  79 `DIR_RNGLOCK` reseeds the game's RNG at the start of every frame. **The camera is not free of the game state:**
  what the film camera sees changes the random draws (the stage's effects draw when drawn), so two cameras on one script
  can play different matches (9.x's take B: Peach's smash picked another item and Bowser lived). Lock it for any
  multi-camera run with a random outcome; the setup's seed then picks the draws. `DIR_HUD` 3 is the whole HUD without the
  off-screen magnifier bubbles (a film camera frames tighter than the game's).
- **The shieldhp cue spawned an item until 98e0485** (2026-09-30). The `DIR_SHIELDHP` case fell through into `DIR_ITEM`,
  so every shieldhp cue also dropped an item whose kind was the shield value at stage centre. `whirl_shield_lab` was
  rerun with the fix (Fox, all 8 cases): grind hits at 15, 28 and 41 frames and the 45-frame hover, as DESIGN says, so
  its numbers stand. `defense_lab` (animation pops) wasn't rerun: the barrel it spawned couldn't change a pop check.

**Rig and animation:**
- The rig: `projects/geno/rig/rig.py` holds 71 joints, depth-first. The decomp's
  `src/melee/ft/kinds/ftGeno/ftgeno_rig.inc` is generated with `rig.py --c OUT` (not `rig.py --c` alone, which writes a
  file named `--c`). `FTGE_JOINT_COUNT` must match. Moving joint positions doesn't change the parts table.
- `anims.base()` is every pose's root and the idle's frame 0. It holds:
  - STANCE: feet staggered by IK; hips and shoulders 25° toward the camera, head 10° (Michael chose B of three);
  - `heel_lift` past 35° of shin lean;
  - the relaxed hand (`rig.RELAXED_HAND` / `rig.mirror_hand()`);
  - FootJ's `up` is the direction the **sole** faces, because its local Y points down in the bind pose. Getting it wrong
    renders the boots upside down.
  Every action must start and end exactly on its neighbour's pose.
- **Actions do blend.** ftData+0x10 byte 0 is a per-action default blend (Wait1, the walks and Run had 6). Geno's Run is
  0, set by `locomotion.BLEND` through fighter-build.
- **KneeBend** (the jumpsquat) plays whatever animation its entry points at. Geno's has its own, and the engine jumps on
  frame 5.
- **Dash:** frame 0 never shows, and frame 11 hands over to Run.
- **Flag-bit-31 actions** (rolls, getups, ledge, dash attack) move by TransN. A still track becomes one key that the game
  evaluates once, so hold offsets with `anims.still_transn`.
- **Smash charge:** the script's `smash_charge` frame freezes the animation while A is held (up to 60 frames), with a
  shake and a flash, then resumes. So the charge-frame pose is what players stare at. Damage scales ×1.367 at full.
- **Angled forward tilt and forward smash** are picked when the fighter's table has their animations. Geno has all three
  angles.
- **Throws:**
  - The victim rides the thrower's **ThrowN**, not TransN2 (the decomp's part enum is one short).
  - The victim plays the thrower's entries 262-265, keyed to the shared 52-node "Taro" skeleton, kind 0x21. anims.json
    `passthrough` copies or retimes donors.
  - The back throw reverses facing mid-action, so spin in the animation and end turned round (on YRotN).
  - Throws are weight-dependent unless flagged independent; Geno's are independent.

- **Limb growth (scale keys, 2026-09-29):** `Pose.grow(joint, s)`; poses_ground and poses_throws clips key
  `Rgrow`/`Lgrow` (HandN) and `Rtips`/`Ltips` (the fingertips). anims.json tracks carry `s`, which fighter-build writes as
  SCAX/Y/Z linear keys. The joints and the hand-pose animation joints carry classical scale, as the cast's do. The engine
  resets every joint's scale to rest on each animation change, so an interrupted growth never sticks. `Clip.fist` and
  `Clip.launch` pull HandN in by the growth, so a hitbox on HandN stays where the design put it. A hurtbox on a grown bone
  grows in radius too, not only in length (lbColl_80006E58 measures it in the bone's space; datkit movedata does the
  same since 7eda5a6), while hitbox radii don't grow. `GENO_NO_GROW=1` builds without it. His hitboxes don't ride a
  grown bone, so the growth costs him disjoint the cast's doesn't: remeasure writes `research/growth_cost.md` (his build
  with and without it, the cast with and without their scale tracks) and flags a move that loses more than its
  Mario-family analogs. The jabs' and up tilt's grown hands are intangible while grown (`moves.GROW_INTANG`;
  `GENO_GROW_INTANG=move,...` to try another set). poses_air clips grow joints with `Clip.grow(joint, {frame: s})`. `director/labs/fist_read.py` measures a fist against its hitbox; `director/limb_lab.py` films it with the
  game's own camera (`Film.game_camera()`, which logs CAM lines) or a close one.
- **Frame numbers:** the attacks show animation frame 1 on their first frame (frame 0 never shows); Catch and CatchDash
  show frame 0 first. Their scripts count with the animation, so frame data is unaffected, but a strip labelled by action
  frame is one off for the grabs. Label strips by the logged animation frame (the director's FEET cue).
- **The match camera:** at 42 units apart on Final Destination the game's camera sits 137 from the stage at fov 30, 14.4
  px per unit in a res-2 dump (1280x1056; Melee projects at aspect 1.2173, so keep the dump's own shape).

**Model and data:**
- **Weapon forms and hand poses** (ART.md "Weapon forms: the interface"): `s.form(side, form)`, `s.hand`, `s.cap`.
  Visibility groups and part poses reset on every action change, including a special's ground-to-air switch, so set
  them in every action. The decomp's `ftGe_Init_OnDeath` defaults every group to option 0 (f84b957); without it the hands
  render hidden.
- **Whole-body alternates:** visibility group 0 (the body) has an option 1, Geno Flash's cannon (`model/geno_cannon.py`,
  `rig.cannon_commands`), on three joints of its own after TransN2 (71-73; nothing gameplay reads). The low and metal
  models carry the same option (datkit builds a metal model per body option). `director/flash_cannon_lab.py` and
  `director/labs/cannon_board.py check` compare hurtboxes, hits and actions before and after; the hidden body curls into
  the cannon so the hurtboxes follow it (`poses_air.curl_pose`, measured by `labs/cannon_hurt.py`, the numbers in
  `research/flash_hurtboxes.md`); the director logs VIS lines
  (every group's option, on change).
- **Materials:** Melee's lights brighten textures (×1.2 on the lit side). Only masked, dim specular (Mario's shoe
  technique); the importer now reads a material's specular colour. Double-sided surfaces light wrong on the back (the
  curls), so make them two single-sided layers.
- **The importer** moves vertices by the difference between the glTF's joints and the rig's. When the modeller moves a
  chain joint, `rig.py`'s JOINTS must take the same positions (the Gate 1b and 1c merges did this).
- **Cape and cap dynamics:** `rig.py DYNAMICS` (four chains, three body spheres, a pull toward the modelled shape). Guard
  hands the cap chain back to the animation. `rig/dynsim.py` replays a run offline.
- **The capelet's skinning** (`geno_geo.CAPE_ARM`): measure a change with `model/cape_clip.py FK_DIR OUT.json` (the panel
  area inside the arms, per action and frame; FK from `datkit fkdir`) and `cape_clip.py table BEFORE AFTER`; refit with
  `model/cape_fit.py`; look at chosen frames offline with `model/pose_look.py` (Blender, the model posed on FK frames).
- **The ledge-grab box** is at the cast's median proportions for his height: `rig.LEDGE_GRAB` 12.8 / 16.7 / 12.1, written
  by fighter-build. The catch eases from where he grabbed over 6 frames (the decomp's `ftcliffcommon.c` hook).
- **The shield** is centred on his body (`anims.SHIELD_CENTRE` (0, 0.96, 1.1)), and every hurtbox sits 0.66 inside at
  full health. Re-run `rig/shieldfit.py` after any stance or guard change.

**Tools:**
- **datkit's graphic-effect command:** the bone is bits 6-13, remapped only when it's a plain joint index; bits 32-47 are
  the effect id. HSDRaw's names for that command are wrong (fixed e3e02bc). Useful effect ids (`fx_scale_lab`):
  1010-1012 are stars, sparkles and a ring, 1043 smoke, 1062 a spark; 1006, 1032, 1034-5, 1047-51 and 1056 are empty.
- **The Beam:** the timed bonus (+10%, ±3 frames of a star's flash) was designed but never implemented until the
  atk-air branch (ed18584, `timed_lab`). v1.4 has no store: a shield cancel loses the stars, and it auto-fires at frame
  64. Kirby's copy mirrors it and reads Geno's numbers from `ftGe_BeamNumbers`.
- `meshstats` for a new kind needs `--rig RIG.json`.
- **Sound:**
  - His bank is 55 (`geno.ssm`, 550000-550052).
  - fighter-build silences Mario's voice bank in the template's scripts (540001 is silent).
  - Wiring: `projects/geno/sound/wiring.py` (voice table, cues, footfalls).

## 6. Paused workstreams

Each has a repo worktree `~/animation-pipeline-geno-<name>` and a decomp branch `geno-<name>` (worktree in the sandbox),
with its full agent transcript in `~/games/melee/work/handoff/transcripts/agent-<name>.jsonl`. To resume one, start an
agent in that worktree and sandbox with a brief built from its section here. The transcript holds the detail: search it
with grep or jq, it's too big to read whole.

### 6.1 Throws (`throws`): MERGED 2026-09-28 (geno c3e84f4, ext 8541139)
Merged and verified on Fox, Falco and Falcon (DESIGN §6f has the numbers); it matches the original build, and the soak runs clean.
Michael's open call: with no DI, Fox can be dash-regrabbed after the up throw at 0-20% (any DI escapes, which is within the rule).
Since the held Star Gun aim (2026-09-29, 5 frames longer) that is once in twelve tries, at 20%.
**Design** (DESIGN §6f; Michael's notes in the changelog): one weapon each, with weight. Anticipation, a hold, the
weapon locking with a ka-chunk, then the release and follow-through.

| Throw | Design | Numbers |
|---|---|---|
| Forward | **Rocket Fist**: the ignition reads as a cannon blast; Michael kept it | 8%, 35° toward the ledge |
| Back | **Hand Cannon**: the move, then the blast; the shot launches them, never a toss | 10%, his kill throw |
| Up | **Star Gun salvo**: pop, beat, three stars (real projectiles); must launch to a clear height like Fox's and Falco's | 4% + 3×1% |
| Down | **point-blank Finger Shot**: pin, beat, three shots (real projectiles) into the tech-chase knockdown | 2% + 3×1% |

Invariant: no regrab on Fox, Falco or Falcon at 0-60%.

**Done** (f3870af, bf039fb; decomp 4c55ed8 `ftGe_Throw_Anim`):
- all four throws, built in beats on CatchWait's frame 0;
- the projectile hook;
- victim animations retimed from the cast (`taro.py`);
- weight-independent throws;
- the back throw ending turned round;
- `throws_lab` (launch, height, DI, regrabs, kills; the "weights" and "height" sets).

**Verified** (2026-09-28): 57b93bb reviewed and kept; `geno` and `ext` merged in (repo 33fc30d, decomp f91848f); every
check run on the production model and written into DESIGN §6f (c786cbe) with the measured numbers. The throw shots leave
the right hand's part 40 (the hand, not the elbow). Strips, reels with game audio and a local review page are in
`~/games/melee/sandbox/geno-throws/board/` (`review_throws.html`).

**Next:** Michael's calls (below), then merge.
- The up throw with no DI: a dash grab out of the throw catches Fox at 0-20% (DESIGN §6f, Regrabs). Accept it, or lower
  the pop's height or angle.
- The stars draw as the Beam article's red laser bolts, not stars; star art is a separate job.

### 6.2 Aerials, landings, specials' body motion (`atk-air`): MERGED 2026-09-28 (geno eaa9e85, ext 1647842)
Merged and verified: timing unchanged except down air; down air reach 13.0; the timed release works (18.7 against
17.0); the shots leave the muzzle (the right-hand part was the elbow). It matches the original build, and a 3-minute
CPU soak runs clean. The reel is `~/games/melee/sandbox/geno-atk-air/geno_aerials_specials.mp4`. Michael's open calls
are listed in its report: Star Road's thrusters, the Blast's and Whirl's bare hands, a sound-only cancel, placeholder
chime and sparkle, shots 4.3 further forward, and down air's downward disjoint of 14.5 against the cast's maximum of 8.9.
Follow-ups merged (geno fe2fc09, ext b889e44): the Beam's shield cancel matches Samus's frame for frame (8 frames, stars
lost; a sideways smash rolls out with no lag; the air cancel follows Mewtwo's), and the timed release plays SMRPG's
timed-hit bells (550054).
Down B either-or merged 2026-09-29 (geno 75290e8, ext 6412ee6): a tap or any release is the Blast (three columns once
star 2 lit), held to star 3 grounded is Geno Flash only; the mark comes at the release (stick read then), IASA release
+ 28. Each column raycasts to the floor under its own mark (an airborne cast used to end its column at Geno's height and
whiff). The tell stands on the floor (Blast `lift` 40). Landing mid-charge keeps the charge with no landing lag, as Link's
bow and Mewtwo's Shadow Ball do (their SpecialAirNLoop_Coll switch to the ground loop). Matching, unchanged research,
3-minute soak clean (9 down Bs). Review: `~/games/melee/sandbox/geno-atk-air/review_downb_fix.html`. Open: Michael's
call on the one-frame landing sink (the air collision box's bottom is his knees; vanilla sinks too).

**Design:**
- The ART.md form table (Hand Gun forward air, Star Gun up air, Hand Cannon back air and down air, Beam neutral B, Finger
  Shot tap).
- **Down air** is a long Hand Cannon blast column, ~13 below him: meteor at the muzzle on frames 9-10, a weak tail at
  5-6% that doesn't spike (DESIGN bf9363b).
- **The Beam's timed release** (+10%, chime, sparkle).
- **Geno Flash's** full-body cannon was stubbed with the Hand Cannon until its art existed (it did from 2026-09-29,
  geno-cannon: DESIGN §12).
- `moves.air_base()` is Fall frame 0 (`states_air.fall_pose()`), and every aerial starts and ends on it.

**Done:**
- repo f35b610, d1feca3, 2a1cbc9, 2d038d4 (down air), 966656b (nair pass 3: a flying back kick), fc2f82b (the Blast's
  call wider), 573af35 (`timed_lab`);
- decomp 46ab725 (the look survives the ground/air switch; shots leave the muzzle), ed18584 (the timed release;
  measured 18.7 timed, 17 auto, 11 untimed two-star);
- final strips (139 boards) in the sandbox's `boards/`.
The agent was checking the cancel, the timed release and seams in its final capture when it stopped.

**Next:**
1. Finish that check.
2. Re-measure: down air's reach should be ~13 ± 0.5, plus the aerial shape and profile numbers.
3. An mp4 of every move (`labs/aerials_reel.py`) and a review page, then merge.
4. Check up air and any overhead pose for arms hidden behind his big head (they need a wide V).

### 6.3 Victory fanfare (`fanfare`): MERGED 2026-09-28 (geno 66002c3, ext c263001)
Merged, and verified in game on the main build: in `victory_lab`'s captured audio, Geno's fanfare correlates at 0.53 and
Mario's at 0.04. `play.sh` installs `ff_geno.hps` from `~/games/melee/work/music/fanfare/`. Still open: Michael's listen.

**Design:** our own arrangement of SMRPG's post-battle "Victory" (level-up) music, Michael's choice. Mario's
`ff_mario.hps` is the fallback.

**Done:**
- `~/games/melee/work/music/fanfare/`, per its `NOTES.md`:
  - transcribed from the cartridge's sequence data (track 9) and checked against the game's own sound driver;
  - arranged for Melee in 7.99 s at -15 LUFS;
  - `geno_levelup_fanfare.wav`, the A/B file `ab_mario_then_geno.wav`, and `ff_geno.hps`;
  - the source is `src/`.
- Repo dc69586: `tools/machinima/melee/audio/hps.py` (HALPST read and write; all 20 vanilla fanfares round-trip
  bit-exactly) on `dspadpcm.py`.
- Decomp 1823870: `ff_geno.hps` is HPS id 0x63, Geno's victory row points at it, and it falls back to Mario's if the
  file is missing.

**WIP:** 04403f0 (DESIGN notes, `victory_lab` and a director change, unverified).

**Next:**
1. Michael listens to the A/B file and the demo (he hasn't yet).
2. Merge the decomp and the tool.
3. Make `play.sh` and `remeasure.sh` (or an install step) copy `ff_geno.hps` to the disc's `audio/`, since only the demo
   disc has it now.
4. Tidy §12's fanfare note in DESIGN.md.

### 6.4 Crowd cheer (`cheer`): MERGED 2026-09-28 (geno 93f7ae1, ext 37830e1)
Merged, with Michael's pick, candidate #2 (`shortlist/2_pc_pc_ns_mr.wav`), installed (bank 55 sound 550053, his chant field;
`bank.py CHANT.wav` then `--install` rebuilds it; the bank for the main disc is `~/games/melee/work/crowd/out_main`). Also SMRPG's timed-hit sounds 550054 and 550055. Verified in game (0.98 correlation in `cheer_lab`).
**Goal:** Melee's crowd chants some fighters' names. Geno has no chant, or a borrowed wrong one; nobody has checked
which. Make "Ge-no! Ge-no!" (JEE-no) by splicing the crowd's own recorded chants (for example "Ji" from Jigglypuff's,
"no" from a -no or -o name), as the announcer call was made (`~/games/melee/work/announcer/NOTES.md`: cuts, Praat PSOLA
and crossfades, with Whisper and wav2vec2 used only for ranking).

**Done:** early stage. 25e0da9 has the analysis and splice tools in `projects/geno/sound/cheer/` (`survey`, `align`,
`crowdsplice`, `candidates`, `evaluate`), unverified. The agent was writing the bank tool that appends the chant to
`geno.ssm`. The generic gasp and cheer system is `src/melee/sfx/crowdsfx.c`; the per-character chant table wasn't found
yet. `lb/lbaudio_ax.c`'s `lbl_803BB3C0` is the bank-per-character table, not the chant.

**Next:**
1. Find the chant table and its trigger, and what Geno plays now (check kind 0x22 for overruns).
2. Make 3-5 candidates, ranked and loudness-matched, in `~/games/melee/work/crowd/`.
3. A review page, and **Michael's pick**.
4. Inject: a bank slot or an append, plus the decomp row inside `#ifndef MUST_MATCH`.
5. A lab that triggers it, with the audio captured.

## 7. After those (the backlog)

- **Effects: done 2026-09-29**, the Flash's full-body cannon included (geno-cannon: `model/geno_cannon.py`, the body
  group's option 1, joints CannonN/CannonBarrelN/CannonWheelN appended; the live model in `~/games/melee/work/art/model`
  now carries it, the previous files in `art/model_pre_cannon/`). Geno's own
  `EfGeData.dat` (`fx/efge.py`, `fx/efge_normals.py`, ids by name: `efge.gid`, `ftgeno_efge.h` from `efge.py --c`).
  Specials: the Finger Shot's bullets, the Beam (bigger, stepped by stars, the charge's draw-in stars), the Whirl, the
  Blast (with our own floor tell), the Flash sequence, the up throw's Star Gun stars. Every gun normal and aerial draws
  its hits (reach 0.82-0.99 of the hitboxes', the cast 0.90-1.01; `fx/gunfxmeasure.py`), weapon forms on the ledge
  and get-up blasts, the Double Punch's exhaust trail, and the forward throw's rocket launch and trail (Michael
  dropped its cannon flash, 2026-09-29). Open, Michael's calls: the look and linger of each weapon form's bursts, and
  the pummel's puff. System map: `fx/EFFECTS.md`.
- **Kirby's Geno hat:** done 2026-09-29 (Geno's own cap refitted; DESIGN §12). `rig/kirby_hat.py build --install` rebuilds it.
- **Menu art:** done 2026-09-28 (geno-menuart): the CSS portraits, stock icons, CSS icon and VS Records face are in-game
  renders of the production model, one portrait and stock icon per costume (DESIGN §12 "Art").
- **The announcer's "Geno!":** done earlier (Michael, 2026-09-28): it's in the game. Don't redo it.
- **The Forest Maze stage** (geno-stage; `projects/geno/stage/`): Michael's calls 2026-09-29: layout A, the Clearing (one
  mushroom cap at 28, ledges ±70); a proper stage-select slot; static assets only (no Wiggler for now); image-model style
  targets approved, kept to GameCube-era Melee aesthetics; music: Forest Maze metal draft 2 (not the GLADE version),
  cut to a stage loop. Milestones: M1 greybox in its real slot with the loop (done and merged 2026-09-30; Michael kept the
  layout and approved the stage select: the icon at the bottom row's left end, stage names scaled 0.84 to clear it), M2 style
  targets and M3 production art (done and merged 2026-09-30, overnight on the agent's own pick: t7, twilight umber and
  purple in 3D; runners-up t3 and t6; `stage/SCOPE.md`, `stage/DESIGN.md`). M3 passes every check (starter_lab 5/5, edges
  within 0.6 px, busy time under Battlefield's, matching) but the art is far plainer than t7: the stump is an extrusion of
  the collision, the textures are procedural and the background is flat. It uses 1.4k triangles and 127 KB against the vanilla
  stages' 8–14k and 0.45–1.5 MB. Michael confirmed t7 and asked for a richer pass: art pass 2 (merged 2026-09-30,
  `stage/forest_art2.py`: scripted Blender, baked vertex colour like the vanilla stages, a floating cap, layered
  background; 7.9k triangles, 550 KB, busy time 7.53 ms vs Battlefield's 8.26) is now the production art. Review pages:
  `~/games/melee/sandbox/geno-stage/board/m3/review_m2_m3.html` (M3), `.../board/m4/review_art2.html` (pass 2).
  `STAGE_ART` still builds the greybox and M3; `~/games/melee/work/stage/out/GrFm_m3.dat` is M3's file.
  The sky (merged 2026-09-30, Michael: "dull static purple skybox"): painted twilight, three twinkling star fields,
  three drifting cloud banks (150/180/240 s loops), two canopy ridges, fireflies and the Star Road shooting star (on by
  default, `STAR_ROAD=0` off), all from the map file's own animation set as the vanilla stages do it; the sky wraps the
  stage so orbits of ±60° show no void. 868 KB, 8,042 triangles, 7.67 ms busy (Battlefield 8.26); readability min
  0.283 at x25 over the whole cycle; flash 0.0017 (Battlefield 0.024). Review: `.../board/sky/review_sky.html`.
  Art pass 2's file is `GrFm_art2.dat` beside the production one.
- **Lag measurement:** `stage/director/run_perf.sh` (log-only, `--cpu` clock). At the console's clock every stage shows a
  LAGFRAME every 1000 frames: the 60 Hz pad clock drifting against NTSC's 59.94, not load. So compare stages by the
  per-frame busy time (PERF lines), not the lag count. Each run stalls 40 ms at frame 60 and must log a lag there, or the
  counter is dead (the 07:49 incident: a second hook's edit made build.py re-insert the plain flush block ahead of the lag
  call; build.py now keeps exactly one block).
- **KO and star-KO sound:** decided 2026-09-29: silence (Michael). Nothing to build; the shared KO sounds play.
- **Costumes:** done: six, Michael's set (2026-09-29; DESIGN §12 "Costumes"): Geno, Mario, Bowser, Mallow, Peach and
  Dark. The review page is `~/games/melee/sandbox/geno-menuart/board/review_menuart.html`.
- **Single-player modes** must not crash. Japanese menu files. **On hold** (Michael, 2026-09-29): don't start either.
- **Smaller items:**
  - done 2026-09-29: ItemBlind (no state in the game plays it; his is now a blinded grope, as the cast's; the director's
    `anim` cue plays it in items_lab) and the light throws (each retimed onto the frame its item leaves the hand, measured
    in game from the director's LETGO lines; the smash down throw has its own animation, as it lets go 2 frames earlier);
  - done 2026-09-29 (geno-cannon polish, DESIGN changelog): the low model's face (its own 64x64 CI8 face texture, the
    high nose; `director/lowface_lab.py` shows the magnifier bubbles) and the arms through the capelet's front panels
    (the panels ride the arm: `model/cape_clip.py` measures every action, `model/cape_fit.py` fits the weights,
    `director/capelet_lab.py` checks in game). Michael accepted the static
    skinning's trade (2026-09-29): no helper joint;
  - done 2026-09-29: the throws' victim animations, measured on Fox, Falco, Falcon, Bowser and Pichu against his holding
    hand and against Fox's own throws on Fox (`throws_lab.py --grip`). Authored where the donor didn't fit: the down
    throw's pin (Fox's frames 25-34 roll the body below its pivot, into the floor) and the up throw's overhead hold
    (Mario's lifted pose, for the new aim-before-release). The forward and back throws' donors fit (their release pops
    within Fox's own); Bowser's hurtboxes swallow the hand on every throw, as any fighter's hold does (one victim
    animation plays on every skeleton).
- **The original goal:** the in-engine reveal trailer (A NEW CHALLENGER APPROACHES, the fight, joining the battle, the
  CSS, then a montage with the FRAME PERFECT director), with the Forest Maze arrangement.
- **Housekeeping: done 2026-09-29.** Removed 17 merged repo worktrees (their branches stay; gitignored boards archived
  in `~/games/melee/work/archive/wt-<name>/`) and stripped the finished sandboxes to their boards, videos and review pages
  (decomp worktrees, disc clones, Dolphin profiles, runs and rig/movedata copies removed; 37 GB freed; all 685 review
  links still resolve). Kept: the geno-atk-air, geno-cannon, geno-fx, geno-fxnormals and geno-limbscale worktrees and
  sandboxes (agents that may be resumed), and geno-moves' worktree board. The demo worktree is gone: play the current
  build with `projects/geno/play.sh` from `~/animation-pipeline-geno`.

## 8. Transcripts

`~/games/melee/work/handoff/transcripts/` (local, 1.1 GB):
- `main-session.jsonl`: this whole session, 527 MB, including the summaries of earlier work;
- `agent-<name>.jsonl`: each agent, for throws, atk-air, fanfare, cheer, model, moves, walk, atk-ground, anim, kirby
  and cape.

Search them (`grep -a`, `jq`) for the reasoning behind a number or a fix. Don't try to read one whole.
