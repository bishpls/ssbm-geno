# The decompilation changes

`geno.patch` is every change this project makes to [doldecomp/melee](https://github.com/doldecomp/melee), as one diff
against upstream commit `64e41ca08ed93233816e8d4328d359546b3d4c55` (this refresh: our decomp branch at `cfb27b1`).

```sh
git clone https://github.com/doldecomp/melee.git decomp
cd decomp
git checkout 64e41ca08ed93233816e8d4328d359546b3d4c55
git apply ../geno.patch
```

Every change sits inside `#ifndef MUST_MATCH`, so the matching build still reproduces the retail `main.dol`
(SHA-1 `08e0bf20134dfcb260699671004527b2d6bb1a45`). The patch adds:
- Geno's fighter kind (`src/melee/ft/kinds/ftGeno/`), his items (`it/kinds/itgeno.c`), Kirby's copy of him, and the
  per-character tables a 27th fighter reads;
- the Forest Maze (`gr/grforest.c`) in the dummied VS-range stage slot, and the stage select, Random and Random Stage
  Switch entries for it;
- the menus, results screen, challenger and prize screens for him, and the sound-bank entries;
- the ♡ and ♪ glyphs in the game's font and on the name-entry keyboard;
- the lab director (`src/melee/director/`) and its hooks, which `tools/machinima/melee/build.py` compiles in.

Two things in it are about the toolchain, not the game:
- **Shift-JIS sources, pre-transcoded.** `sjiswrap.exe` doesn't run under wibo on macOS, so the patch converts the
  sources that hold Japanese text to Shift-JIS once and sets `config.shift_jis = False` in `configure.py`. The matching
  build is unaffected. Search these files with `grep -a`: plain grep skips them as binary.
- **The non-matching build links the director,** including a `script.c` that `build.py` writes from a director script
  (`projects/geno/director/play.py` for the game you play). So build the playable game with `build.py` (or
  `projects/geno/play.sh`), not with a bare `configure.py --non-matching`.

Verified from a fresh clone on 2026-10-02 (macOS, Apple Silicon): the patch applies cleanly to `64e41ca`; the matching
build gives `08e0bf20134dfcb260699671004527b2d6bb1a45` (1,133 of 1,133 units, 1 min 37 s at `ninja -j6`); and the
non-matching play build compiles and links (1 min 18 s). The full procedure is in [HOW-TO-PLAY.md](../HOW-TO-PLAY.md).
