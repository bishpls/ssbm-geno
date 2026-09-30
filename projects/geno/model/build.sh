#!/bin/bash
# Build Geno's production model end to end: bake AO -> paint the textures -> build the .blend and the glTFs.
#   projects/geno/model/build.sh [OUT]        (OUT defaults to ~/games/melee/work/art/model)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
OUT="${1:-$HOME/games/melee/work/art/model}"
BLENDER="${BLENDER:-/opt/homebrew/bin/blender}"
PY="${PY:-$ROOT/.venv/bin/python}"
[ -x "$PY" ] || PY="$HOME/animation-pipeline/.venv/bin/python"
WORK="$OUT/work"; rm -rf "$OUT/geno_tex"; mkdir -p "$WORK/ao" "$OUT/geno_tex"
"$BLENDER" -b --python "$HERE/build_model.py" -- --out "$WORK" --preview --bake "$WORK/ao" 2>&1 | grep -E "Error|Traceback" && exit 1
"$PY" "$HERE/paint.py" "$OUT/geno_tex" --ao "$WORK/ao"
"$BLENDER" -b --python "$HERE/build_model.py" -- --out "$OUT" --tex "$OUT/geno_tex" 2>&1 | grep -E "Error|Traceback|skeleton check"
rm -rf "$WORK"
echo "built $OUT/geno.gltf, geno_low.gltf, geno.blend"
