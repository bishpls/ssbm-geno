#!/bin/bash
# Build the Forest Maze's stage file: stage_spec.py (STAGE_ART=forest2 by default; forest = M3, greybox) -> datkit
# stage-build on Battlefield's file as the template -> OUT (default $MELEE_WORK/stage/out/GrFm.dat), then stage-dump's
# budget line (bytes, triangles, meshes, texture bytes). Run inside the sandbox (eval "$(sh tools/machinima/melee/sandbox.sh NAME)").
#   projects/geno/stage/build_stage.sh [OUT.dat]
set -e
cd "$(dirname "$0")/../../.."
W=$MELEE_WORK/stage; OUT=${1:-$W/out/GrFm.dat}; SPEC=$W/forest_maze${SPEC_TAG}.spec.json
mkdir -p "$W/out"
.venv/bin/python projects/geno/stage/stage_spec.py "$SPEC" | head -1
tools/machinima/melee/datkit.sh stage-build "$SPEC" "$MELEE_DISC/files/GrNBa.dat" "$OUT" | tail -1
tools/machinima/melee/datkit.sh stage-dump "$OUT" "$OUT.dump.json" >/dev/null
.venv/bin/python - "$OUT" <<'PY'
import json, os, sys
d = json.load(open(sys.argv[1] + '.dump.json'))
g = d['gobjs']
print(f"BUDGET {os.path.basename(sys.argv[1])} bytes {os.path.getsize(sys.argv[1])} triangles {sum(x['triangles'] for x in g)} "
      f"meshes {sum(x['dobjs'] for x in g)} texture_bytes {sum(x['texture_bytes'] for x in g)}")
PY
