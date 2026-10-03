#!/bin/bash
# Mux a reel's dumped frames (60 fps) with its game audio. Dolphin's audio dump starts at boot while the frame dump
# starts with the first rendered frame, so the audio runs ~12.6 s longer; both end together, so the audio's head is
# skipped by the difference (from the start, as -shortest alone does, the first 12 s were silent and the music late).
#   projects/geno/stage/director/mux_reel.sh RUN_DIR OUT.mp4
set -e
RUN=$1; OUT=$2
N=$(ls "$RUN"/f[0-9]*.png | wc -l | tr -d ' ')
AD=$(ffprobe -v error -show_entries stream=duration -of csv=p=0 "$RUN/dsp.wav" | head -1)
OFF=$(python3 -c "print(max(0.0, round($AD * 32028 / 32000 - $N / 60.0, 3)))")   # the dump is labelled 32028 Hz; it is 32000
ffmpeg -loglevel error -y -framerate 60 -i "$RUN/f%05d.png" -ss "$OFF" -i "$RUN/dsp.wav" -c:v libx264 -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 160k -shortest "$OUT"
echo "muxed $OUT: $N frames, audio skipped $OFF s"
