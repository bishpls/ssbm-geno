#!/bin/sh
# Install the US announcer bank with "Geno!" (sound 510017) into the extracted disc, backing the retail file up once.
#   projects/geno/sound/announcer/install.sh            # after build.sh
#   projects/geno/sound/announcer/install.sh --restore  # put the retail file back
# Only files whose SHA-1 is the retail bank's or the patched bank's are touched.
set -eu
MW=${MELEE_WORK:-$HOME/games/melee/work}
SRC=${ANNOUNCER_WORK:-$MW/announcer}/out/nr_name.ssm
DST=${MELEE_DISC:-$HOME/games/melee/disc}/files/audio/us/nr_name.ssm
BAK_DIR=$MW/orig/audio/us
BAK=$BAK_DIR/nr_name.ssm
ORIG_SHA1=17d1619185bf043bebe205055ad241e183754c0b      # retail NTSC 1.02 audio/us/nr_name.ssm (339,328 B)
PATCH_SHA1=ba2e1d699dcad375b41028fc1544eae52cae43a5     # the patched bank build.sh makes (347,712 B)
sha1() { shasum -a 1 "$1" | cut -d' ' -f1; }
if [ "${1:-}" = "--restore" ]; then
    [ -f "$BAK" ] && [ "$(sha1 "$BAK")" = "$ORIG_SHA1" ] || { echo "no valid backup at $BAK" >&2; exit 1; }
    cp -p "$BAK" "$DST"; echo "restored the retail bank -> $DST"; exit 0
fi
[ -f "$SRC" ] || { echo "missing $SRC: run build.sh first" >&2; exit 1; }
[ "$(sha1 "$SRC")" = "$PATCH_SHA1" ] || echo "note: $SRC differs from the reference build (sha1 $(sha1 "$SRC")); installing it anyway" >&2
CUR=$(sha1 "$DST")
if [ ! -f "$BAK" ]; then
    [ "$CUR" = "$ORIG_SHA1" ] || { echo "$DST is not the retail bank (sha1 $CUR); refusing without a backup" >&2; exit 1; }
    mkdir -p "$BAK_DIR"; cp -p "$DST" "$BAK"; echo "backed up the retail bank -> $BAK"
fi
cp "$SRC" "$DST"
echo "installed nr_name.ssm with Geno's call -> $DST"
