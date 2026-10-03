#!/bin/bash
# perf_lab on each named stage: lag frames in $MELEE_WORK/stage/perf/<name>_cpu<clock>.txt (the probe's own excluded).
# Aborts unless the source has the lag hook and the run's deliberate stall (frame 60) logged a lag frame.
#   PERF_CPU=1.0 projects/geno/stage/director/run_perf.sh battlefield fountain forest_maze forest_maze:GrFm_greybox.dat
# A name:FILE runs the Forest Maze with $MELEE_WORK/stage/out/FILE in place of the production GrFm.dat (put back after).
# PERF_CPU is the emulated CPU clock (1.0 the console's): below 1 it is a slower console, the measure's positive control
# (a stage must lag somewhere) and the headroom (the slowest clock a stage still runs clean at).
set -e
cd "$(dirname "$0")/../../../.."
eval "$(sh tools/machinima/melee/sandbox.sh geno-stage)"
CPU=${PERF_CPU:-1.0}
mkdir -p "$MELEE_WORK/stage/perf"
for ARG in "$@"; do
  S=${ARG%%:*}; F=${ARG#*:}; TAG=$S
  if [ "$F" != "$ARG" ]; then cp "$MELEE_WORK/stage/out/$F" "$MELEE_DISC/files/GrFm.dat"; TAG=${F%.dat}; fi
  PERF_STAGE=$S .venv/bin/python tools/machinima/melee/build.py projects/geno/stage perf_lab | tail -1
  # guard 1: the source has one director flush block, with the lag call in it (build.py enforces it too)
  G="$MELEE_DECOMP/src/melee/gm/gmscene.c"
  if [ "$(grep -c 'if (pad_queue_count > 1)' "$G")" != 1 ] || [ "$(grep -c 'director_on_lag(pad_queue_count);' "$G")" != 1 ]; then
    echo "ABORT: gmscene.c doesn't have exactly one flush block with the lag call"; exit 1; fi
  R="$MELEE_WORK/stage/runs/perf_${TAG}_cpu$CPU"; rm -rf "$R"
  DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run "$MELEE_DISC/sys/main.dol" "$R" --logonly --cpu "$CPU" --until 'DIRECTOR END' --timeout 1500 --quiet | tail -1
  [ "$F" != "$ARG" ] && cp "$MELEE_WORK/stage/out/GrFm.dat" "$MELEE_DISC/files/GrFm.dat"
  # guard 2: perf_lab's 40 ms stall at frame 60 must have logged a lag frame (60-63), or the counter is dead
  if ! grep -q '^STALL 60 ' $R/osreport.log || [ -z "$(awk '$1=="LAGFRAME" && $2>=60 && $2<=63' $R/osreport.log)" ]; then
    echo "ABORT: $TAG cpu $CPU: the stall at frame 60 logged no lag frame: the counter is dead"; exit 1; fi
  # the engine's frame timings (PERF s cpu draw total mtx, in 60ths of a second), the probe's frames left out, in ms: logic;
  # draw submission (draw - cpu: draw is cumulative); busy = logic + draw, the CPU's work in a 16.7 ms frame. (total also
  # holds the XFB copy's wait for the retrace, so it reads a full frame whatever the load: not used)
  NP=$(grep -c '^PERF ' $R/osreport.log || true)
  [ "$NP" -ge 3000 ] || { echo "ABORT: $TAG cpu $CPU: only $NP PERF lines"; exit 1; }
  STATS=$(.venv/bin/python - "$R/osreport.log" <<'PY'
import sys
rows = [l.split() for l in open(sys.argv[1]) if l.startswith('PERF ')]
rows = [[float(x) for x in r[1:6]] for r in rows if int(r[1]) >= 1 and not 60 <= int(r[1]) <= 63]
k = 1000 / 60; n = len(rows); busy = sorted(r[2] for r in rows)       # draw is cumulative: logic + draw submission
m = lambda i: sum(r[i] for r in rows) / n
print(f"logic_ms {m(1)*k:.2f} draw_ms {(m(2)-m(1))*k:.2f} busy_ms {m(2)*k:.2f} busy_p99_ms {busy[int(n*0.99)]*k:.2f} "
      f"busy_max_ms {busy[-1]*k:.2f} mtx {m(4):.0f}")
PY
)
  echo "$TAG cpu $CPU frames $(grep -m1 -o 'DIRECTOR END [0-9]*' $R/osreport.log | awk '{print $3}') probe ok lag_frames $(awk '$1=="LAGFRAME" && ($2<60 || $2>63)' $R/osreport.log | wc -l | tr -d ' ') first $(awk '$1=="LAGFRAME" && ($2<60 || $2>63) {print $2}' $R/osreport.log | head -5 | tr '\n' ' ')asserts $(grep -c assert $R/osreport.log || true) $STATS" | tee "$MELEE_WORK/stage/perf/${TAG}_cpu$CPU.txt"
done
echo PERF DONE
