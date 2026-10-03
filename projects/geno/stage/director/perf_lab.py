"""Performance lab: four level-9 CPUs (Geno, Fox, Pikachu, Ness: the effect-heavy cast) fight for a minute on PERF_STAGE.
Run log-only at the console's clock (run_perf.sh; dolphin.py --cpu 1.0). The director logs:
  - PERF s cpu draw total mtx every frame: the engine's own timings (HSD_PerfLastStat, 60ths of a second): the stage
    comparison. Busy = draw (cumulative: logic + draw submission); total also holds the wait for the retrace.
  - LAGFRAME s n for every loop frame that found more than one pad sample queued. It also catches Melee's polling drift
    (an extra sample every 1000 frames on every stage), so it proves little at the console's clock; at a lower one
    (--cpu 0.4) it's the slowdown test.
A 40 ms stall at frame 60 must log a lag frame, or the counter is dead (run_perf.sh aborts). Dolphin doesn't time the GPU,
so the triangle and texture budgets stand in for it.
    PERF_STAGE=forest_maze .venv/bin/python tools/machinima/melee/build.py projects/geno/stage perf_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --logonly --cpu 1.0 --until 'DIRECTOR END' --quiet
"""
import os, sys
from dsl import Film

N = 3600
PROBE = 60                        # the stall's frame: its LAGFRAME is at PROBE + 1..3, and doesn't count
f = Film(len_s=N / 60.0 + 0.5)
cast = [('geno', -45), ('fox', -15), ('pikachu', 15), ('ness', 45)]
f.setup(players=[(c, dict(x=x, face=1 if x < 0 else -1, cpu=9)) for c, x in cast], stage=os.environ.get('PERF_STAGE', 'battlefield'),
        seed=3, stocks=4)
f.game_camera()
f.perf(0)                         # the engine's own frame timings, every frame (PERF lines)
f.stall(PROBE, 40)                # the counter's positive control: one lag frame on purpose (run_perf.sh checks it)
f.cue(N, 'end')
f.emit(sys.argv[1])
