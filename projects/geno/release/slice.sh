#!/bin/sh
# Rebuild the public ssbm-geno slice (github.com/bishpls/ssbm-geno) from this repo and the decomp, the same way every time:
#   projects/geno/release/slice.sh SLICE_DIR [GENO_REF] [EXT_REF]
# SLICE_DIR is a checkout of ssbm-geno. Its own top-level files (README.md, MAKING-OF.md, LICENSE, .gitignore,
# decomp/README.md, audio/README.md) are kept; everything generated is replaced:
#   - projects/geno and tools/machinima, from GENO_REF (default HEAD) by git archive (tracked files only), less the
#     trailer's production material (below);
#   - engine/fonts: Archivo (the review boards' typeface) and Big Shoulders Display (the Forest Maze's stage-select name,
#     stage/menu_art.py), with their licences;
#   - decomp/geno.patch: git diff --binary of the decomp from upstream doldecomp 64e41ca to EXT_REF (default ext);
#   - audio/: our own arrangements, rendered (Michael, 2026-10-02): the victory fanfare and the Forest Maze's stage track,
#     as the game plays them (.hps), from $MELEE_WORK.
# Then key-scan (projects/geno/release/keyscan.sh) and commit by hand. Never commit game data: the slice is public.
set -eu
OUT=${1:?usage: slice.sh SLICE_DIR [GENO_REF] [EXT_REF]}
REF=${2:-HEAD}
EXT=${3:-ext}
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
DECOMP=${MELEE_DECOMP:-$HOME/games/melee/decomp}
MW=${MELEE_WORK:-$HOME/games/melee/work}
BASE=64e41ca08ed93233816e8d4328d359546b3d4c55
[ -d "$OUT/.git" ] || { echo "slice.sh: $OUT is not a git checkout of ssbm-geno" >&2; exit 1; }

# The trailer is a film in production: its screenplay, treatment, notes, animatic, cut, score and shot labs stay private
# until it's out. What the game itself uses stays in: the challenger silhouette and prize screen builders and their labs,
# and the name tag's glyph tools.
TRAILER_KEEP='projects/geno/trailer/silhouette/ projects/geno/trailer/director/ projects/geno/trailer/lab/font_glyphs.py
projects/geno/trailer/lab/font_patch.py projects/geno/trailer/lab/font_check.py projects/geno/trailer/lab/font_mock.py'

rm -rf "$OUT/projects" "$OUT/tools" "$OUT/engine"
mkdir -p "$OUT/decomp" "$OUT/audio"
git -C "$ROOT" archive "$REF" projects/geno tools/machinima engine/fonts/Archivo.ttf engine/fonts/OFL-archivo.txt \
    engine/fonts/BigShouldersDisplay.ttf engine/fonts/OFL-bigshouldersdisplay.txt | tar -x -C "$OUT"
# the trailer: keep only the game's pieces
( cd "$OUT" && find projects/geno/trailer -type f | while read -r f; do
    keep=0
    for k in $TRAILER_KEEP; do case "$f" in "$k"|"$k"*) keep=1;; esac; done
    [ $keep = 1 ] || rm -f "$f"
  done && find projects/geno/trailer -type d -empty -delete )

git -C "$DECOMP" diff --binary "$BASE" "$EXT" > "$OUT/decomp/geno.patch"

# our rendered arrangements (game-ready HALPST streams); the sources are under projects/geno/music
for f in "$MW/music/fanfare/ff_geno.hps" "$MW/stage/music/gr_forestmaze.hps"; do
  if [ -f "$f" ]; then cp "$f" "$OUT/audio/"; else echo "slice.sh: missing $f (audio/ left without it)" >&2; fi
done

echo "slice: $(git -C "$ROOT" rev-parse --short "$REF") + decomp $(git -C "$DECOMP" rev-parse --short "$EXT") -> $OUT"
echo "next: sh $ROOT/projects/geno/release/keyscan.sh $OUT, then review and commit"
