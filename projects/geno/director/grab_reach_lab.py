"""Grab reach lab: how far each grab really reaches in the game, the grapples included (Samus's grapple beam, Link's and
Young Link's hookshots and Yoshi's tongue grab with a thrown object or a long hitbox, which a move table reads badly).
LAB_GRABBER (samus, link, ylink, yoshi, marth, roy, geno, ...) grabs a standing Fox from each distance in LAB_RANGE
(first:last, one unit apart; LAB_KINDS picks stand, dash or both), standing (Z) and out of a dash (the stick forward two frames, then Z); the report finds the
farthest distance, centre to centre, from which each grab still catches him (his capture state within the slot).
    LAB_GRABBER=samus .venv/bin/python tools/machinima/melee/build.py projects/geno grab_reach_lab
    .venv/bin/python projects/geno/director/grab_reach_lab.py --report RUN [RUN ...]
The table's reach (the grab box's far edge) is this distance less Fox's front: calibrated on the plain grabs (Marth, Roy,
Geno), whose tables are sound.
"""
import json, os, sys

GRABBER, FOX = 0, 1
SLOT = 120
CAPTURE = {223, 224, 225, 226, 227, 228, 229, 230, 231}             # CapturePulledHi .. the capture states


def tests():
    a, b = (int(x) for x in os.environ.get('LAB_RANGE', '8:26').split(':'))
    kinds = os.environ.get('LAB_KINDS', 'stand,dash').split(',')
    return [dict(kind=k, d=d, label=f'{k}_{d}') for k in kinds for d in range(a, b + 1)]


def report(runs):
    out = {}
    for run in runs:
        plan = json.load(open(run.rstrip('/') + '.plan.json'))
        state = {}
        for l in open(os.path.join(run, 'osreport.log'), errors='replace'):
            q = l.split()
            if q[:1] == ['POS'] and len(q) >= 8 and q[2] == str(FOX): state[int(q[1])] = int(q[5])
        name = plan[0]['grabber']
        res = {}
        prev = out.get(name, {})
        for p in plan:
            got = any(state.get(s) in CAPTURE for s in range(p['t0'], p['t0'] + SLOT - 10))
            res.setdefault(p['kind'], []).append((p['d'], got))
        row = {}
        for k, v in res.items():
            hit = [d for d, g in v if g]
            row[k] = dict(max=max(hit) if hit else None, caught=[d for d, g in sorted(v) if g],
                          tried=(min(d for d, _ in v), max(d for d, _ in v)))
        for k, r in prev.items():                # a second run of the same grabber (a wider range) adds to the first
            if k in row:
                caught = sorted(set(r['caught']) | set(row[k]['caught']))
                row[k] = dict(max=max(caught) if caught else None, caught=caught,
                              tried=(min(r['tried'][0], row[k]['tried'][0]), max(r['tried'][1], row[k]['tried'][1])))
            else:
                row[k] = r
        out[name] = row
        print(name, {k: (r['max'], r['tried']) for k, r in row.items()})
    return out


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--report':
    a = sys.argv[2:]
    res = report([x for x in a if not x.endswith('.json')])
    js = [x for x in a if x.endswith('.json')]
    if js: json.dump(res, open(js[0], 'w'), indent=1)
    sys.exit()

from dsl import Film
T = tests()
who = os.environ.get('LAB_GRABBER', 'geno')
f = Film(len_s=(len(T) * SLOT + 110) / 60)
f.setup(players=[(who, dict(x=-10, face=1)), ('fox', dict(x=10, face=-1))], seed=5)
g, fox = f.port(GRABBER), f.port(FOX)
f.cam(0, eye=(0, 16, 140), at=(0, 10, 0), fov=34, ease='cut', track='mid')
plan, t0 = [], 70
for t in T:
    gx = -t['d'] / 2.0
    f.reset(t0 - 30, GRABBER, gx, 1); f.reset(t0 - 30, FOX, gx + t['d'], -1)
    f.percent(t0 - 26, GRABBER, 0); f.percent(t0 - 26, FOX, 0)
    f.mark(t0, len(plan), t['label'])
    if t['kind'] == 'stand':
        g.hold(t0, 2, btn='Z')
    else:
        g.hold(t0, 2, stick=(80, 0), dir=1)
        g.hold(t0 + 2, 2, stick=(80, 0), btn='Z', dir=1)
    fox.trace(t0 - 2, t0 + SLOT - 12)
    plan.append(dict(t0=t0, grabber=who, **t))
    t0 += SLOT
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
