"""Foot slide measured in the game. walk_lab logs each foot bone every frame (the director's FEET cue: world position and
the bone's local X and Y axes). Geno's boot rolls heel -> flat -> ball about two points of its sole, the heel 0.8 behind
the ankle and the ball 1.3 ahead, 0.95 below it (locomotion.HEEL/BALL/SOLE; the foot bone's X runs toe-ward and its Y
down, as in the bind pose). While one of those points is on the floor it must stay put.

    .venv/bin/python projects/geno/director/labs/footslide.py RUN [--from S --to S] [--csv OUT.csv]
A stance is a run of frames with the heel or the ball within `--floor` (0.025) of the floor. For each, the drift is the
largest horizontal travel of a sole point over the frames it was down; the slip the largest move in one frame. Reported
per motion state and phase (walks and the run: settled, or the entry frames the engine blends; Dash: drive, strike,
stop; TurnRun and RunBrake: the skid, which slides by design, then the push or the stand-up): stances, median length,
median and worst drift, worst slip, and where the worst was.
"""
import argparse, math, os, statistics
from collections import defaultdict

NAMES = {14: 'Wait', 15: 'WalkSlow', 16: 'WalkMiddle', 17: 'WalkFast', 18: 'Turn', 19: 'TurnRun', 20: 'Dash', 21: 'Run',
         23: 'RunBrake', 24: 'KneeBend', 39: 'Squat', 40: 'SquatWait', 41: 'SquatRv', 42: 'Landing', 43: 'LandingFallSpecial',
         245: 'Ottotto', 246: 'OttottoWait'}
HEEL, BALL, SOLE = 0.8, 1.3, 0.95


FRAME, CHANGE = {}, []                                      # the animation frame per script frame; motion changes


def parse(run):
    pos, feet = {}, defaultdict(dict)
    for l in open(os.path.join(run, 'osreport.log')):
        p = l.split()
        if not p: continue
        if p[0] == 'POS' and p[2] == '0':
            pos[int(p[1])] = (float(p[3]), float(p[4]), int(p[5]))
        elif p[0] == 'MS' and p[2] == '0':
            CHANGE.append(int(p[1]))
        elif p[0] == 'FEET' and p[2] == '0':
            v = [float(x) for x in p[4:13]]
            o, X, Y = v[0:3], v[3:6], v[6:9]
            pts = [tuple(o[i] + X[i] * a + Y[i] * SOLE for i in range(3)) for a in (-HEEL, BALL)]
            feet[int(p[3])][int(p[1])] = pts
            if len(p) > 14: FRAME[int(p[1])] = float(p[14])
    return pos, feet


# where a stance falls: walks and the run are 'settled' once 8 frames past the action change (the engine's 6-frame blends
# and the walk's speed changes come before); the one-shots by the animation frame the stance starts on
PHASES = {'Dash': ((0, 8, 'drive'), (8, 12, 'strike'), (12, 99, 'stop')), 'TurnRun': ((0, 10, 'skid'), (10, 99, 'push')),
          'RunBrake': ((0, 11.5, 'skid'), (11.5, 99, 'stand'))}


def phase(state, s):
    if state in PHASES:
        f = FRAME.get(s, 0.0)
        return next(name for a, b, name in PHASES[state] if a <= f < b)
    last = max([c for c in CHANGE if c <= s] or [0])
    return 'settled' if s - last >= 8 else 'entry'


def stances(foot, pos, floor):
    ss = sorted(s for s in foot if s in pos)
    runs, cur = [], []
    for s in ss:
        down = [pt[1] - pos[s][1] < floor for pt in foot[s]]
        if any(down) and pos[s][1] == 0.0 and (not cur or (s == cur[-1][0] + 1 and pos[s][2] == pos[cur[-1][0]][2])):
            cur.append((s, down))
        else:
            if len(cur) > 1: runs.append(cur)
            cur = [(s, down)] if any(down) and pos[s][1] == 0.0 else []
    if len(cur) > 1: runs.append(cur)
    out = []
    for r in runs:
        drift = slip = 0.0
        for k in range(2):
            xs = [(foot[s][k][0], foot[s][k][2]) for s, d in r if d[k]]
            if len(xs) > 1:
                drift = max(drift, max(math.hypot(x - xs[0][0], z - xs[0][1]) for x, z in xs))
                slip = max(slip, max(math.hypot(xs[i + 1][0] - xs[i][0], xs[i + 1][1] - xs[i][1]) for i in range(len(xs) - 1)))
        out.append(([s for s, _ in r], drift, slip))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run'); ap.add_argument('--floor', type=float, default=0.025)
    ap.add_argument('--min', type=int, default=2, help='shortest stance counted (frames)')
    ap.add_argument('--from', dest='start', type=int); ap.add_argument('--to', dest='end', type=int, default=10 ** 9)
    ap.add_argument('--csv')
    a = ap.parse_args()
    pos, feet = parse(os.path.expanduser(a.run))
    by, rows = defaultdict(list), []
    for side in (0, 1):
        for fr, drift, slip in stances(feet[side], pos, a.floor):
            if len(fr) < a.min: continue
            if a.start is not None and not (a.start <= fr[0] <= a.end): continue
            name = NAMES.get(pos[fr[0]][2], str(pos[fr[0]][2]))
            if name == 'Wait': continue                          # standing (and the resets between shots)
            ph = phase(name, fr[0])
            by[(name, ph)].append((drift, slip, len(fr), fr[0], 'LR'[side]))
            rows.append((fr[0], fr[-1], 'LR'[side], name, ph, drift, slip))
    print(f'{"state":10s} {"phase":8s} {"stances":>7s} {"frames":>6s} {"drift med":>9s} {"drift max":>9s} {"slip max":>8s}  worst at')
    order = list(NAMES.values())
    for key in sorted(by, key=lambda k: (order.index(k[0]) if k[0] in order else 99, k[1])):
        v = by[key]
        w = max(v)
        print(f'{key[0]:10s} {key[1]:8s} {len(v):7d} {statistics.median(x[2] for x in v):6.0f} '
              f'{statistics.median(x[0] for x in v):9.3f} {w[0]:9.3f} {max(x[1] for x in v):8.3f}  s{w[3]} {w[4]}')
    if a.csv:
        with open(a.csv, 'w') as f:
            f.write('first,last,foot,state,phase,drift,slip\n')
            for r in sorted(rows): f.write(','.join(str(round(x, 4)) if isinstance(x, float) else str(x) for x in r) + '\n')
    return by


if __name__ == '__main__':
    main()
