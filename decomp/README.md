# The decompilation changes

`geno.patch` is every change this project makes to [doldecomp/melee](https://github.com/doldecomp/melee), as one diff
against upstream commit `64e41ca08ed93233816e8d4328d359546b3d4c55`.

```sh
git clone https://github.com/doldecomp/melee.git decomp
cd decomp
git checkout 64e41ca08ed93233816e8d4328d359546b3d4c55
git apply ../geno.patch
```

Every change sits inside `#ifndef MUST_MATCH`, so the matching build still reproduces the retail `main.dol`
(SHA-1 `08e0bf20134d...`). The patch adds Geno's fighter kind (`src/melee/ft/kinds/ftGeno/`), his items and effects,
the menu and results-screen support for a 27th fighter, the sound bank entries, and the lab director that
`tools/machinima/melee/build.py` compiles in for testing.

Follow the upstream README to set up the toolchain and your own disc image.
