# tools/machinima: decompiled games as a film backend

A decompiled game, rebuilt with a director compiled into it, is a deterministic renderer the film pipeline can drive. The
first backend is **Super Smash Bros. Melee** (NTSC 1.02, [doldecomp/melee](https://github.com/doldecomp/melee)), run in
Dolphin; the first film is `projects/frame-perfect`.

```
choreography (Python, dsl.py) -> script.c -> the decomp's non-matching build (hooks + director.c) -> main.dol
 -> Dolphin, headless: one PNG per game frame, the DSP audio, the game's OSReport log (dolphin.py)
 -> plates between the director's slates, audio cut between its clicks (plates.py)
 -> engine/plate.js composites them on the film clock; report.py checks every hit against the beat grid
```

## Game data: bring your own, never commit it

The repo holds tools and choreography only. The disc image, the extracted disc, the decomp's `orig/` DOL, build outputs and
captured plates all live outside it (`~/games/melee/` by default) or under gitignored paths (`projects/*/assets/plates`).
Use a dump of a disc you own. The right one is Game ID `GALE01`, revision 2, 1,459,978,240 bytes, and its `sys/main.dol`
has the SHA-1 in the decomp's README (`08e0bf20...6bb1a45`).

## Setup (macOS, Apple Silicon)

1. `brew install --cask dolphin`; ninja is already a dependency. Rosetta must be installed.
2. `git clone --depth=1 https://github.com/doldecomp/melee.git ~/games/melee/decomp`
3. wibo's macOS build runs the Metrowerks compilers (the README's wine-crossover cask is gone): download `wibo-macos` from
   decompals/wibo's releases to `~/games/melee/bin/`.
4. `sjiswrap.exe` does not run under wibo-macos (missing kernel32 calls). Instead, transcode the 15 sources that hold Japanese
   text to CP932 once and set `config.shift_jis = False` in `configure.py`. Under a non-Japanese code page the compiler reads
   a Shift-JIS lead byte as a lone character, so a trail byte of 0x5C (a backslash) must be written `\\` inside strings
   (two characters in `mnnamenew.c`). Keep these edits on a local branch.
5. Extract `sys/main.dol` from your disc (`build/tools/dtk vfs cp DISC.iso:sys/main.dol orig/GALE01/sys/main.dol`), run
   `python3 configure.py --wrapper ~/games/melee/bin/wibo-macos && ninja`: the byte-matching build, about 35 s.
6. Extract the whole disc (`dtk vfs cp DISC.iso: ~/games/melee/disc/`). Dolphin boots the folder around `sys/main.dol`, so
   a rebuilt DOL needs no ISO repack.

## Pieces

| File | What it does |
|---|---|
| `dolphin.py` | Runs Dolphin headless in an isolated user folder with pinned settings (single core, DSP HLE, no memory cards, custom RTC, the emulated CPU at 2x), dumps every frame and the audio, stops on a frame count or an OSReport line, collects the log |
| `plates.py` | Trims a capture to the frames between the director's magenta slates (refusing it if the count is off by one), resizes to the display aspect, cuts the game audio between the slate clicks and resamples it to the exact script length |
| `melee/director/` | The director (C89, compiled into the game): boots straight into a VS match, HUD and music off, writes the scripted pads, the camera and the cues every frame, runs closed-loop behaviours, logs hits. `dir_results_music = 1` (a lab's choice; films emit 0) turns the music back on when the scene leaves the match, so the results screen's victory fanfare plays |
| `melee/build.py` | Compiles a film's choreography, applies the hooks (all `#ifndef MUST_MATCH`, so the same tree still builds the matching DOL), adds the director to the non-matching link, rebuilds, installs the DOL |
| `melee/dsl.py` | The choreography language (below) |
| `melee/report.py` | Matches every intended hit to the logged one: frame error, beat error, misses; `--fix` runs the timing solve, `--calib` records measured frame data, `--hits-js` exports the hits for a composite |
| `melee/timeline.py` | A run as per-fighter action timelines (motion state, start, duration, position) per labelled segment |
| `melee/audio/hps.py` | Reads and writes Melee's HALPST music streams (`files/audio/*.hps`): DSP-ADPCM stereo in 0x10000-byte blocks, each block carrying the decoder state at its start; the last block's next pointer ends the stream or loops it. `check` proves a file against vgmstream and a re-encode. The game opens streams by path through the disc's file table, so a new `.hps` in an extracted disc's `files/audio/` is found by name |

## The director

Hooks (inserted by `build.py`):
- **Boot:** straight into the debug VS mode.
- **Match setup:** from `dir_setup` (stage, fighters, costumes, seed).
- **Hits:** fighter hits in `ftColl_8007891C`, item hits (lasers) in `ftColl_80078998`.
- **Laser spawns.**
- **One game frame per rendered image:** the game's loop runs one logic frame per queued pad sample, so a slow render would
  run two logic frames and dump one image. The director build drops the extra samples.

Per game frame it:
- writes `HSD_PadGameStatus` from the script;
- runs the closed-loop behaviours (approach, auto tech);
- drives the debug free camera (eye, interest, fov, roll; keys in world space or tracking the fighters, smoothed, snapping on
  cuts);
- fires cues: freeze (fighters stop, the camera keeps moving), stage visibility, clear colour, reset, set position, facing,
  motion state, percent, marks.

It reports through OSReport, which Dolphin logs from the IPL UART:
- `ATTR` and `LAG`: each fighter's attributes read from the disc;
- `MS s port msid x y`: motion-state changes;
- `HIT s attacker victim dmg move` and `IHIT`;
- `LASER s port x y angle speed`;
- `POS` traces, `MARK`s, and `DIRECTOR END`.

## The choreography language (dsl.py)

`Film(len_s, calib, fix)` is the script clock: frame `s` is film time `s / 60`, and plate frame `s + 1`. Its controls:

| Group | Calls |
|---|---|
| Moves | `port.move(t_hit, name, dir, mark=N)` schedules a move so its hit lands on `t_hit`. With `mark=N` the fighter walks onto the move's range first, closed loop |
| Tech | `waveshine`, `shine_chain(t0, [0, 22], finish='usmash', di_port=)`, `multishine(t, n, every=8 or 15)`, `wavedash`, `jc`, `airdodge`, `di(t_hit, stick)` (the victim crouches first) |
| Auto tech | `auto(t, fastfall, lcancel, lowlaser)` |
| Movement | `approach(t0, t1, range)`, `walk`, `dash`, `shield`, `taunt`, `trace` |
| Camera | `cam(t, eye, at, fov, roll, ease, track)`, `orbit(...)` |
| Cues | `freeze`, `reset`, `percent`, `setpos`, `face`, `mark(t, id, label)` |

## What the labs measured (projects/frame-perfect/director: calib.py, techlab.py, laserlab.py)

**Latency and timing**
- An input on frame `s` takes effect on `s + 1`.
- A-button moves hit 2 frames later than the frame-data tables say; C-stick smashes 1 frame later.
- An aerial's contact frame depends on spacing, so let the timing solve place it.

**Fox and Falco's own numbers, read from the disc**

| | Fox | Falco |
|---|---|---|
| Jumpsquat | 3 | 5 |
| Walk speed | 1.6 | 1.4 |
| Gravity | 0.23 | 0.17 |
| Fast-fall speed | 3.4 | 3.5 |

Both have aerial landing lag of 15 (nair), 22 (fair), 20 (bair) and 18 (up-air, dair). L-cancelled, those halve (15 → 7).

**Wavedash slide by stick angle:** about 21 units at (74, −30), 16 at 45°, 0 straight down, then 10 frames of landing lag.
Angles shallower than about 20° float as a plain air dodge.

**Jumpsquat accepts only rapid jab, grab, up-smash and the short-hop check.** So:
- a multishine presses the next shine on jumpsquat's last frame (an 8-frame cycle);
- a jump-cancelled up-smash out of a shine works.

**Shine jump-cancel:** frame 6 on a hit (its hitlag eats earlier presses; Melee has no buffer), frame 4 on a whiff.
- Air-dodge on jumpsquat's last frame for a wavedash with no airborne frames.
- A waveshine chain cycles in 22 frames hit to hit.

**Waveshines hold only while the victim crouch-cancels and holds down.**
- Fresh shines launch Falco on the second; stale ones (lower damage, lower set knockback) don't.
- Holding B keeps a reflector up, still jump-cancellable: that is how a pillar waits for the opponent to fall back into reach.

**Falco's laser leaves the gun 12 frames after B.**
- Fired before the 7th airborne frame of a short hop, it flies over a standing opponent.
- The laser animation blocks fast fall until it fires.
- Stale-move negation shows in the log (3.0% to 1.8% over repeats).

**Lag.** A capture one frame short of the script is real lag: two logic frames rendered once. The one-frame-per-render hook
fixed it; overclocking the emulated CPU did not, because the render waits on emulated video timing.

## New fighters and menus (datkit, projects/geno)

`melee/datkit.sh` runs a small C# tool over HSDRaw (Ploaj/HSDLib, vendored at `vendor/HSDLib`, .NET 8 SDK): `roots`,
`tree`, `jobjs`, `skel`, `rest`, `actions`, `figa`, `parts`, `lookups`, `texdump`, `animkeys`, `mscan`, `mdump` and
`mframes` inspect Melee's .dat files; `fighter-build`, `css-geno` and `menus-geno` write them. Outputs derived from the
disc stay in `$MELEE_WORK` (`~/games/melee/work`).
- **Menus key a character by frame.** Portraits, emblems, stock icons and name images are texture animations whose frame is
  the character's index (CSS: hud + costume * 30; results screen and HUD: gm_80168B34, 180 + costume for Geno; VS Records:
  SELKIND). A new character appends an image and keys its frame (and the frame after, back to what it showed).
  `projects/geno/menus/build.py` builds all four menu files (character select, results, VS Records, HUD) into
  `$MELEE_WORK/menus/out` with review sheets and an install script; `mscan` lists every texture animation in a file.
- **Re-saved files need their GPU buffers flagged.** HSDRaw writes blocks of 0x40 bytes or less on 4-byte boundaries unless
  flagged, so after any size change small palettes, tiny images and short display lists land off the GPU's 32-byte grid.
  css-geno and menus-geno flag every model's buffers before saving (`TexKit.AlignGX`); `projects/geno/menus/gxalign.py`
  checks a file.
- **A fighter is three files.** `PlXxNr.dat` is the model (a joint tree with inverse binds and the meshes on the root),
  `PlXxAJ.dat` the animations (one figatree archive per animation, 0x20-aligned), and `PlXx.dat` the fighter data
  (attributes, a 303-entry action table naming each animation's offset and size, move scripts, hurtboxes, engine bones,
  IK, hand-pose model parts (anims.json `part_poses`), visibility lookups). `fighter-build` assembles all three from a rig and an animation set
  (`projects/geno/rig/rig.py`, `anims.py`); a template supplies what the rig doesn't author yet.
- **A costume from a glTF** (`GltfModel.cs`): with `"model": {"high": ..., "low": ..., "eyes": [...]}` in rig.json,
  fighter-build keeps the rig's skeleton and takes the meshes from Blender: joints matched by name (`J%02d` through
  rig.json `jnames`), vertices re-bound to the rig's rest pose by their joints' positions, one DObj per primitive with
  Mario's material setup, glTF's counter-clockwise faces reversed for GX with the cast's cull bit, textures CMP (eyes CI8),
  eye frames as texture animations plus the material lookup the scripts' eye commands index, the metal model as one
  reflection-mapped copy per cull mode (the engine holds 32 metal DObjs, 124 costume DObjs), every GPU buffer aligned.
  `gltf-model` builds just the costume file; `art/gltf_compare.py` checks a round trip through `export`.
- **Joint indices are depth-first positions** in the joint tree (ftParts_SetupParts, figatree nodes, part-pose trees and
  the metal model's joints all walk it that way), so a joint added under the neck or head renumbers everything after it.
  That is safe while everything is generated from rig.py by name (rig.json, anims.json, moves.py's parts, the C parts
  table `ftgeno_rig.inc`, which must be regenerated and the game rebuilt: its joint count must match the model's).
- **The skeleton contract is the parts table**, not joint indices: about 54 engine parts (TopN, TransN, XRotN, YRotN,
  HipN, the legs, arms, fingers, NeckN, HeadN, ThrowN, TransN2) mapped per kind (PlCo.dat, or C for a new kind). The engine
  retargets between kinds through it (thrown victims, for one). Keep Melee's local conventions: a T-pose facing +Z, each
  limb chain running down its bones' local X.
- **Vertices bound to one bone are stored in that bone's frame;** only multi-weight envelopes use world positions.
- **Action flags' low 6 bits are the authored kind.** Author a new kind's animations with its own id, or they retarget
  rotation-only and the model collapses.
- **The OnDeath callback must switch the body model on** (`ftParts_80074A4C(gobj, 0, 0)`), or every mesh stays hidden.
- **Costume textures:** scripts drive eye-blink texture animations by index; a model without them needs the guard in
  `ftAnim_80070458` (non-matching builds only), or the game asserts "texture no exist!".
- **HSDRaw gotchas:** accessors are fresh wrappers on every read (compare `_s`, not objects), and array properties such as
  an action table's `Commands` return copies (edit, then assign back).
- **Kirby's copy of a new kind** (Geno: decomp `ftKirby/ftkirbyspecialgeno.c`): Kirby's per-kind tables stop at 0x20,
  so each gets rows for 0x21 and the new kind: the hat load/unload pairs (`ftKb_Init_803C9CC8`, indexed `kind * 2`), the
  ground and air neutral-B entries (`ftKb_Init_803C9DD0`, `ftKb_Init_803C9E54`), and the hat file, costume and effect
  rows (already `Ft_Kind_Max`-sized). The copy's states go before `ftKb_MS_Count`, and the copy-move range in
  `ftKb_SpecialN_800F5C34` reads to it. `ftCo_800BD9E0` decides what a swallow copies. A hat archive lands in
  `((KirbyHatStruct**) &ft_80459B88)[kind]`: the decomp's `hats[k]` names are one kind off. Kirby plays copies on his
  own actions (PlKb.dat), so a new copy borrows the nearest vanilla copy's and retimes them with the animation rate.
- **Menu tests:** a `Menu` script (dsl.py) boots into a game mode (`boot='vs'`), unlocks the roster, writes pads into the
  master status and steers CSS tokens closed-loop (`goto`), so the real menus can be driven and checked.
- **Move scripts** are assembled in Python (`projects/geno/rig/fcmd.py`) with the decomp's own layouts (HSDRaw's table
  differs: the hitbox's first word, the smash charge's size). `at(n)` then a hitbox means active from frame n (1-based
  frame data); hitboxes address engine parts through the common-bone flag, so scripts never depend on joint order.
- **Animations must not key the engine's joints:** TopN carries the facing (key it and the fighter faces the camera),
  TransN2 is the origin, and the JA joints hold each limb's rest frame.
- **A character's own states** read `cmd_vars[0]` for "interruptible" (fcmd `interruptible()`); `allow_interrupt` is the
  common attacks' flag and survives into a new state, which interrupts a special on its first frame.
- **Labs:** `projects/geno/director/normals_lab.py` and `specials_lab.py` run every move against a standing Fox with
  resets between tries (after the entry: a reset needs ground under the fighter), `labs/report_normals.py` turns the hit
  log into measured frame data, and `setup(coll=1)` turns on the developer hitbox and hurtbox display.

### Items (a new fighter's projectiles)

- **New item kinds go after the last one** (`It_Kind_Kyasarin_Egg`), with their own article, logic and render tables
  (`decomp src/melee/it/kinds/itgeno.c`); every place that picks a table by kind range gets one more branch (`item.c`
  article/logic lookup, render link and hold kind; `itmaplib.c` collision class). Inserting into the character range
  would shift the stage and Pokémon kinds that data files reference by number. The character-article pointer array is
  loaded from the item file at a fixed size, so new kinds can't write past it.
- **Articles are data in the fighter's own file** (`ftData+0x48`): common attributes, special attributes (a float
  block the item code reads), per-state scripts, a model. `datkit fighter-build` copies them from donor fighters and
  overrides attributes, scripts and states (`projects/geno/rig/articles.py`); `datkit articles` dumps any fighter's.
- **Item scripts are their own command set** (`it_803F22A8`, from 0x0A): create-hitbox is six words (the fighter's five
  plus a word whose top byte is the **re-hit interval**, frames before a victim can be hit again, 0 = once; Falco's laser
  uses 16), 0x0C sets a hitbox's damage, 0x0E removes one, 0x0F clears all. Word 4's last two bits are hit-grounded and
  hit-aerial (aerial-only meteors, grounded-only pop-ups). `fcmd.ItemScript` encodes them.
- **Item scripts run on the item's animation clock:** a wait longer than the state's animation never ends. Drive timed
  behaviour (multi-hits, growth) in the item's code instead: clear a live hitbox's victims to re-hit (`it_8026FCF8`), set
  its radius (`hit->scale` then `it_80275594`) or damage (`it_80272460`).
- **A state change resets hitboxes and their victim lists.** To carry victims from one phase to the next (a projectile
  that stops after a hit and must not hit that victim again), stay in the state and change the live hitbox's numbers.
- **Shields push back:** something meant to grind a shield has to keep pressing forward, or the first hit's pushback
  leaves it out of reach.
