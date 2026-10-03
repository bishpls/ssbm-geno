#!/bin/sh
# Build the SPC renderer the capture scripts load: blargg's snes_spc 0.9.0 (LGPL 2.1, the accurate DSP) with our three
# small changes (snes_spc_spcx.patch: a dry switch that mutes the echo return, a nosat switch that skips the voice-sum
# clamp, the DSP made reachable) and spcx.cpp's extra C calls (DSP and RAM access).
#   projects/geno/sound/capture/spcrender/build.sh [OUT_DIR]     # default $SMRPG_WORK/spcrender (~/games/smrpg/work/spcrender)
# Writes OUT_DIR/libspc.dylib (macOS) or libspc.so (Linux); point SPCRENDER_LIB at it if OUT_DIR isn't the default.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-${SMRPG_WORK:-$HOME/games/smrpg/work}/spcrender}
SRC=$OUT/snes_spc
mkdir -p "$OUT"
if [ ! -d "$SRC/.git" ]; then
  git clone -q https://github.com/blarggs-audio-libraries/snes_spc.git "$SRC"
fi
git -C "$SRC" checkout -q ec8ee2bbe30451614c1d02a83f7af1c97d497d45
git -C "$SRC" checkout -q -- .
git -C "$SRC" apply "$HERE/snes_spc_spcx.patch"
case "$(uname)" in
  Darwin) LIB=$OUT/libspc.dylib; FLAGS=-dynamiclib ;;
  *)      LIB=$OUT/libspc.so;    FLAGS="-shared -fPIC" ;;
esac
# shellcheck disable=SC2086
c++ -O2 $FLAGS -I"$SRC/snes_spc" -o "$LIB" "$SRC"/snes_spc/*.cpp "$HERE/spcx.cpp"
echo "built $LIB"
