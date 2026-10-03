# How to play

There are two ways in:
- **[Players](#players-patch-your-own-iso):** download the patch from the release page and apply it to your own
  *Super Smash Bros. Melee* disc image. About ten minutes.
- **[Builders](#builders-build-it-from-source):** build the game and every asset yourself from this repository, the
  decompilation and your own disc. An afternoon, and a few assets need more than this repository (see the table).

Both need your own copy of Melee: NTSC, version 1.02. Nothing here contains the game.

## Players: patch your own ISO

### What you need

- **Your own Melee disc image, NTSC 1.02** (game ID `GALE01`, revision 2), as a plain `.iso`. It must match exactly:

  | | |
  |---|---|
  | Size | 1,459,978,240 bytes |
  | MD5 | `0e63d4223b01d9aba596259dc155a174` |
  | SHA-1 | `d4e70c064cc714ba8400a849cf299dbd1aa326fc` |

  These are the published values for NTSC 1.02 (SmashWiki's version list gives the MD5; Slippi Launcher checks the
  SHA-1). If your dump is compressed (`.rvz`, `.ciso`, `.gcz`), convert it back to a plain ISO first: in Dolphin,
  right-click the game, **Convert File...**, format **ISO**. A PAL disc or versions 1.00 and 1.01 won't work.
- **The patch:** `geno.xdelta` from this repository's release page.
- **An xdelta patcher:** xdelta UI or Delta Patcher on Windows, `xdelta3` on macOS and Linux.
- **[Dolphin](https://dolphin-emu.org/)**, the GameCube emulator. Tested with Dolphin 2606a on macOS.

### 1. Check your disc image

- Windows: `certutil -hashfile GALE01.iso MD5`
- macOS: `md5 GALE01.iso`
- Linux: `md5sum GALE01.iso`

The result must be `0e63d4223b01d9aba596259dc155a174`. If it isn't, the patch refuses to apply. It checks every block
of the source, so a wrong disc fails with an error rather than giving you a broken game.

### 2. Apply the patch

- **Windows:** open xdelta UI. *Patch:* `geno.xdelta`. *Source file:* your `GALE01.iso`. *Output file:*
  `Geno.iso`. Click **Patch**. (Delta Patcher works the same way.)
- **macOS:** `brew install xdelta`, then:
  `xdelta3 -d -s GALE01.iso geno.xdelta Geno.iso`
- **Linux:** install `xdelta3` from your distribution (`sudo apt install xdelta3` on Debian and Ubuntu), then the same
  command.

Patching takes a few seconds. The patch is uncompressed VCDIFF, so the older xdelta 3.0 that Windows tools bundle reads
it: we checked it with xdelta3 3.0.11 and 3.2.1. We haven't run the Windows programs themselves.

Check the result: `Geno.iso` should be 1,459,978,240 bytes with MD5 `12f3cd0f66dee1fa93b2932289694f80`.

### 3. Play in Dolphin

Add the folder holding `Geno.iso` to Dolphin's game list (or **Open** it directly) and start it. Set up your controller
once under **Controllers**: a GameCube controller adapter, or **Standard Controller** for a USB pad or keyboard.

### What's different from Melee

- **It starts at VS mode's character select.** There's no opening movie, title screen or main menu at boot. Hold B on
  the character select to reach VS mode's menu (Melee, Tournament Melee, Special Melee, Custom Rules, Name Entry), and
  back out again for the main menu and the other modes.
- **This build unlocks all characters and stages:** all 25 of Melee's characters and every stage, from the first boot.
  All-Star mode isn't part of that: it stays locked.
- **Nothing is saved, and your memory card is never touched.** The build starts past the game's own memory-card check,
  so it never reads or writes the card: your own Melee save is safe, and the unlocks, rules, name tags and records last
  only until you close the game. We measured it: with a memory card in slot A, a whole session (the character select, a
  match on the Forest Maze, the results screen) wrote nothing, while the game's own boot created its save file on the
  same card within a second.
- **Geno** is the right-hand cell of the character select's bottom row, below Young Link. He's in VS mode and Training;
  the single-player modes (Classic, Adventure, All-Star and the rest) don't offer him.
- **The Forest Maze** is the left end of the stage select's bottom row. Random can pick it, and it's in the Random Stage
  Switch list.
- **His name tag:** VS mode, **Name Entry**. The keyboard's third row has two new keys right after Z, ♡ and ♪, so you
  can type SMRPG's "♡♪!?" (! and ? are on the last row). Pick the name on your player panel at the character select.
- **Under slowdown,** the game runs one frame per controller sample instead of catching up, so if your machine can't
  hold full speed the game slows down rather than skipping frames, and an input that lands in a dropped sample is lost.
  At full speed this never happens.
- **Not tested:** a real GameCube or Wii (Nintendont, Swiss), Slippi's Dolphin, netplay, and Dolphin versions other than
  2606a.

## Builders: build it from source

Everything below was run on macOS 13 (Apple Silicon) on 2026-10-02, from a clean clone of this repository, a fresh
clone of doldecomp and a disc extracted from a retail ISO. The table at the end says what was verified that way, with
the numbers. Linux and Windows aren't tested: doldecomp supports both, and our scripts are POSIX shell and
Python, but `play.sh` assumes macOS's Dolphin.app.

### What you need

| Tool | Version we used | For |
|---|---|---|
| Your Melee disc image | NTSC 1.02, MD5 `0e63d4223b01d9aba596259dc155a174` | everything |
| Your *Super Mario RPG* cartridge dump | USA, SHA-1 `a4f7539054c359fe3f360b0e6b72e394439fe9df` | Geno's attack sounds only |
| git, Homebrew, Rosetta 2 | | |
| Python | 3.14.8, with `requirements.txt` | every tool |
| ninja | 1.13.2 | the decompilation |
| wibo for macOS | 1.2.0 (`wibo-macos` from [decompals/wibo](https://github.com/decompals/wibo/releases)) | runs the Metrowerks compilers |
| .NET SDK | 8.0.425 | datkit, which reads and writes Melee's files |
| [HSDLib](https://github.com/Ploaj/HSDLib) | `85567e40797de3c820a55476eca54c704921a848` | datkit |
| Blender | 5.2.2 LTS | the model, Kirby's cap, the stage |
| Dolphin | 2606a | the menu-art renders, and playing |
| vgmstream-cli | r2117 | the sound bank's decode check |
| Mesen2 | 2.1.1 | capturing the SNES sounds from your cartridge |

doldecomp's `configure.py` downloads the rest of its toolchain (dtk 1.8.3, the compilers) itself. The music's own
renderers and instrument libraries (about 7 GB) are needed only to re-render the music; the build uses `audio/`.

The tools share a working area, set by three environment variables (the defaults in brackets):
- `MELEE_DISC`: your extracted disc (`~/games/melee/disc`);
- `MELEE_DECOMP`: the patched decompilation (`~/games/melee/decomp`);
- `MELEE_WORK`: everything generated (`~/games/melee/work`).

Everything the build writes into `MELEE_WORK` and the disc is made from your game data: keep it out of git.

### 1. This repository and its Python

```sh
git clone https://github.com/bishpls/ssbm-geno.git && cd ssbm-geno
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
git clone https://github.com/Ploaj/HSDLib.git vendor/HSDLib
git -C vendor/HSDLib checkout 85567e40797de3c820a55476eca54c704921a848
tools/machinima/melee/datkit.sh        # builds datkit on first use, then prints its usage
```

The commands below run from the repository's root.

### 2. The decompilation, patched, and the matching check

```sh
git clone https://github.com/doldecomp/melee.git $MELEE_DECOMP && cd $MELEE_DECOMP
git checkout 64e41ca08ed93233816e8d4328d359546b3d4c55
git apply /path/to/ssbm-geno/decomp/geno.patch
python3 configure.py --wrapper ~/games/melee/bin/wibo-macos
ninja build/tools/dtk                  # downloads dtk (it then complains that the original DOL is missing: expected)
mkdir -p orig/GALE01/sys
build/tools/dtk vfs cp /path/to/GALE01.iso:sys/main.dol orig/GALE01/sys/main.dol
python3 configure.py --wrapper ~/games/melee/bin/wibo-macos && ninja -j6
shasum build/GALE01/main.dol           # 08e0bf20134dfcb260699671004527b2d6bb1a45: the retail game, byte for byte
```

The patch applies cleanly, and the last line must print the retail SHA-1: every change is inside `#ifndef MUST_MATCH`.
Keep `wibo-macos` at `~/games/melee/bin/` or set `MELEE_WRAPPER` to it. On Linux or Windows, follow doldecomp's own
README for the wrapper. `decomp/README.md` explains the patch's two toolchain changes.

### 3. Extract your disc

```sh
$MELEE_DECOMP/build/tools/dtk vfs cp /path/to/GALE01.iso: $MELEE_DISC/
```

Dolphin boots this folder around `sys/main.dol`, so a rebuilt game needs no ISO. Three steps below read vanilla menu
files, so run them before installing Geno's menus, or keep a copy of the vanilla disc and point `VANILLA_FILES` and
`MNSLCHR` at it.

### 4. Read your disc's inputs

```sh
.venv/bin/python projects/geno/rig/prepare.py
```

Mario's action table and root motion (Geno's template for frame counts and the actions that move by their animation),
and the character select's own icon frames and letters, into `MELEE_WORK`.

### 5. Build the assets

| Asset | Command | Needs |
|---|---|---|
| The model | `projects/geno/model/build.sh $MELEE_WORK/art/model` | Blender |
| Fighter files, six costumes, victory poses | `GENO_MODEL=$MELEE_WORK/art/model .venv/bin/python projects/geno/rig/rig.py $MELEE_WORK/rig/rig_model.json`, then `.venv/bin/python projects/geno/rig/anims.py $MELEE_WORK/rig/mr_actions.txt $MELEE_WORK/rig/anims.json`, then `tools/machinima/melee/datkit.sh fighter-build $MELEE_WORK/rig/rig_model.json $MELEE_WORK/rig/anims.json $MELEE_DISC/files/PlMr.dat $MELEE_DISC/files/PlCo.dat $MELEE_WORK/rig/out Ge Geno 0` | the model |
| Kirby's Geno cap | `.venv/bin/python projects/geno/rig/kirby_hat.py build --install` | Blender |
| Effects | `.venv/bin/python projects/geno/fx/efge.py --install` | |
| Sound bank (his attacks, movement sounds, timed-hit sounds, crowd chant) | `projects/geno/sound/capture/spcrender/build.sh` once, then `SMRPG_ROM=/path/to/smrpg.sfc projects/geno/sound/build_bank.sh` (installs) | your SMRPG dump, Mesen2 (`MESEN`), vgmstream |
| The announcer's "Geno!" | `projects/geno/sound/announcer/build.sh && projects/geno/sound/announcer/install.sh` | |
| The Forest Maze | `projects/geno/stage/build_stage.sh`, then `projects/geno/stage/build_menus.sh [ICON.png]` | Blender |
| The music | `mkdir -p $MELEE_WORK/music/fanfare $MELEE_WORK/stage/music && cp audio/ff_geno.hps $MELEE_WORK/music/fanfare/ && cp audio/gr_forestmaze.hps $MELEE_WORK/stage/music/` | (or re-render: `projects/geno/music/README.md`) |
| Menu art (character select, results, records, HUD) | two in-game renders, then `projects/geno/menus/portrait.py`, `projects/geno/menus/build.py` and `$MELEE_WORK/menus/out/install.sh` (below) | Dolphin |
| Challenger silhouette and prize screen | `projects/geno/trailer/silhouette/build.sh [SIL.bgra]` (without the in-game render it writes only the prize screen; its header has the commands) | Dolphin |

The menu art is rendered in the game itself, from the production model, then matted and cut to Melee's sizes:

```sh
PORTRAIT_LAB=0,1,2,3 .venv/bin/python tools/machinima/melee/build.py projects/geno portrait_lab
.venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol $MELEE_WORK/runs/portrait_a --until 'DIRECTOR END' --res 3 --quiet
PORTRAIT_LAB=4,5 .venv/bin/python tools/machinima/melee/build.py projects/geno portrait_lab
.venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol $MELEE_WORK/runs/portrait_b --until 'DIRECTOR END' --res 3 --quiet
.venv/bin/python projects/geno/menus/portrait.py $MELEE_WORK/menuart $MELEE_WORK/runs/portrait_a:0,1,2,3 $MELEE_WORK/runs/portrait_b:4,5
.venv/bin/python projects/geno/menus/build.py $MELEE_WORK/menuart && sh $MELEE_WORK/menus/out/install.sh
```

Without Dolphin, placeholder art makes the menus complete and the game playable (a drawn portrait in place of the
rendered ones):

```sh
.venv/bin/python projects/geno/css/placeholder.py $MELEE_WORK/css3
.venv/bin/python projects/geno/menus/build.py $MELEE_WORK/css3/geno && sh $MELEE_WORK/menus/out/install.sh
```

The stage-select icon is a render of the finished stage (`projects/geno/stage/director/icon_lab.py`; without one,
`build_menus.sh` draws a placeholder from the stage's spec).

**Rebuilding the sound bank** over one you built before: its installer only replaces files it recognises (the retail
ones and the release's builds), so first delete `files/audio/geno.ssm` and `files/audio/us/geno.ssm` from the disc and
copy the retail `smash2.sem` files back from `$MELEE_WORK/orig/audio/`. A capture is the same on every run, but not the
same bytes as the release's bank, which came from an earlier capture.

### 6. Install, build the game and play

```sh
projects/geno/play.sh
```

`play.sh` installs the fighter files, victory poses, fanfare, effects, challenger and prize screens and the stage (with
its music and stage-select files), builds the playable game (the patched decompilation with
`projects/geno/director/play.py`) into `$MELEE_DISC/sys/main.dol`, and opens Dolphin on it with its own profile
(`~/games/dolphin-play`). The sound bank, the announcer, Kirby's cap and the menus install in their own steps above.
`GENO_COLL=1 projects/geno/play.sh` shows hitboxes and hurtboxes.

To check your build still reproduces the retail game, run `.venv/bin/python tools/machinima/melee/build.py --matching`
(it leaves the retail DOL on the disc, so run `play.sh` again after it).

### What was verified

On 2026-10-02, from a clean clone of this repository, a fresh doldecomp clone and a disc extracted from a retail ISO
(macOS 13, Apple Silicon). "Identical" means byte for byte the same as the file in the playtest build the release
patch was made from.

| Step | Result | Measured |
|---|---|---|
| The patch on doldecomp `64e41ca` | Verified | applies cleanly (90 files) |
| The matching build | Verified | SHA-1 `08e0bf20134dfcb260699671004527b2d6bb1a45`, 1,133 of 1,133 units, 1 min 37 s at `-j6` |
| Extracting the disc (dtk 1.8.3) | Verified | 1,000 files, retail `main.dol` |
| Python from `requirements.txt`, HSDLib, datkit | Verified | 24 s; datkit builds on first use (.NET 8.0.425) |
| `prepare.py` | Verified | 252 animations, 35 root-motion paths, 4 s |
| The model (Blender 5.2.2) | Verified | identical model files, 51 s |
| Fighter files, six costumes, victory poses | Verified | all nine identical (the animations take 102 s) |
| Kirby's cap, effects | Verified | identical |
| Sound bank from the cartridge | Verified | 65 s end to end; two fresh captures give the same 522 sounds; both `smash2.sem` identical; `geno.ssm` differs from the release's (an earlier capture) |
| The announcer's "Geno!" | Verified | identical |
| The Forest Maze | Verified | identical (8,042 triangles, 867,618 bytes) |
| Stage select | Partly | `SdMenu.usd` identical; `MnSlMap.usd` has the placeholder icon (the in-game icon render wasn't run) |
| Prize screen | Verified | identical |
| Challenger silhouette | Not run | needs an in-game render; from the release's render, `build.sh` rebuilds `NtAppro.usd` identically |
| Music from `audio/` | Verified | both streams identical |
| Menu art | Partly | the in-game renders weren't run; the placeholder path builds and plays; from the release's renders, the four menu files rebuild identically |
| The play build (`play.sh`, without opening Dolphin) | Verified | compiles and installs in 1 min 19 s. With the playtest's director, a fresh clone rebuilds the release's game byte for byte (SHA-1 `83fbbc1f9a69…`) |
| Playing the clean build | Verified | Dolphin 2606a: the character select with Geno, the Forest Maze picked and loaded, no errors |
| Re-rendering the music | Not run | the instruments are about 7 GB; renders aren't bit-repeatable (`projects/geno/music/README.md`) |
| Linux, Windows | Not tested | |
