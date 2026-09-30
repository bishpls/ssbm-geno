"""cape_fit.py: fit the capelet's arm-riding (geno_geo.CAPE_ARM) against cape_clip.py's measure.

    .venv/bin/python projects/geno/model/cape_fit.py FK_DIR OUT.json [--step 3] [--sweeps 3] [--start FIT.json] [--fine]
        [--regress W]

The objective, over every action (every STEP-th frame): the panel area the arms cut through (deeper than 0.1), with the
frames an arm is raised counted again (the brief's "full overhead reach"); plus penalties for stretching the panels
further than Gate 2's own worst (the 99th percentile edge growth), and for changing how the capelet hangs in the idle,
walk and run (its vertices' mean move against Gate 2's, past 0.12 units); and (--regress) for any action whose mean cut
area grows against Gate 2's, the growth, weighted by the action's frames, so the arms-down actions (the walk, the landing,
the shield) don't pay for the raised ones. Coordinate search over the rule's numbers
(the upper arm's and forearm's shares per row, their distance falloffs), each tried at a few values around the current
one, kept when the objective drops.
"""
import copy, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geno_geo as G  # noqa: E402
import cape_clip as CC  # noqa: E402

LOOK = ('Wait1', 'WalkMiddle', 'Run', 'Dash', 'Squat', 'JumpF', 'Fall')


def panels_for(P):
    keep = G.CAPE_ARM
    G.CAPE_ARM = P
    try:
        ms = G.build()
    finally:
        G.CAPE_ARM = keep
    return ms


def look_move(fk_dir, meshes, base_meshes, step=4):
    """Mean distance between the panels' vertices under these weights and Gate 2's, over the idle, walk and run."""
    new = {m.name: CC.Skinner(m) for m in meshes if m.name in CC.PANELS}
    old = {m.name: CC.Skinner(m) for m in base_meshes if m.name in CC.PANELS}
    ds = []
    for act in LOOK:
        p = os.path.join(fk_dir, act + '.json')
        if not os.path.exists(p): continue
        d = json.load(open(p))
        for pose in d['pose'][::step]:
            W4 = {n: CC.pose4(pose[i]) for i, n in enumerate(CC.NAMES)}
            for k in new:
                ds.append(np.linalg.norm(new[k](W4) - old[k](W4), axis=1).mean())
    return float(np.mean(ds))


def regression(res, base_act):
    """Frame-weighted mean, over the actions, of how much each one's mean cut area grew against Gate 2's."""
    num = den = 0.0
    for act, r in res.items():
        m = float(np.mean([p['area'] for p in r['per']]))
        num += len(r['per']) * max(0.0, m - base_act.get(act, m))
        den += len(r['per'])
    return num / max(den, 1.0)


def objective(fk_dir, P, base, step):
    ms = panels_for(P)
    res = CC.measure(fk_dir, None, quiet=True, meshes=ms, step=step)
    s = CC.summary(res)
    look = look_move(fk_dir, ms, base['meshes'])
    reg = regression(res, base['act']) if base.get('regress') else 0.0
    j = s['area_mean'] + s['raised_area_mean'] + 2.0 * max(0.0, s['stretch_p99'] - base['stretch_p99'] - 0.5) \
        + 10.0 * max(0.0, look - 0.12) + base.get('regress', 0.0) * reg
    return j, dict(s, look=round(look, 3), regress=round(reg, 3), J=round(j, 4))


def fit(fk_dir, out, step=3, sweeps=3, start=None, fine=False, regress=0.0):
    base_ms = panels_for(None)                                      # Gate 2's rule: the baseline
    b_res = CC.measure(fk_dir, None, quiet=True, meshes=base_ms, step=step)
    b = CC.summary(b_res)
    base = dict(meshes=base_ms, stretch_p99=b['stretch_p99'], regress=regress,
                act={a: float(np.mean([p['area'] for p in r['per']])) for a, r in b_res.items()})
    print('Gate 2', json.dumps(b), flush=True)
    P = start or dict(A=[0, 1.0, 1.0, 0.8, 0.4, 0.2], F=[0, 0.0, 0.0, 0.2, 0.3, 0.3], d0=1.1, d1=2.2, f0=1.0, f1=2.0)
    best, info = objective(fk_dir, P, base, step)
    print('start', json.dumps(info), flush=True)
    knobs = [('A', r) for r in range(1, 6)] + [('F', r) for r in range(1, 6)] + [('d0', None), ('d1', None), ('f0', None), ('f1', None)]
    for sweep in range(sweeps):
        for k, r in knobs:
            cur = P[k][r] if r is not None else P[k]
            deltas = (-0.3, -0.15, 0.15, 0.3) if k in ('A', 'F') else (-0.4, -0.2, 0.2, 0.4)
            if fine: deltas = tuple(d / 3 for d in deltas)
            for dv in deltas:
                v = cur + dv
                if k in ('A', 'F') and not 0.0 <= v <= 1.0: continue
                if k in ('d0', 'f0') and not 0.3 <= v < (P['d1'] if k == 'd0' else P['f1']) - 0.2: continue
                if k in ('d1', 'f1') and not (P['d0'] if k == 'd1' else P['f0']) + 0.2 < v <= 4.0: continue
                Q = copy.deepcopy(P)
                if r is not None: Q[k][r] = round(v, 3)
                else: Q[k] = round(v, 3)
                j, inf = objective(fk_dir, Q, base, step)
                if j < best - 1e-4:
                    best, P, info = j, Q, inf
                    print(f'sweep {sweep} {k}{"" if r is None else r} -> {v:.2f}: {json.dumps(inf)}', flush=True)
                    cur = v
        json.dump(dict(params=P, info=info, gate2=b), open(out, 'w'), indent=1)
    print('best', json.dumps(P), json.dumps(info))
    return P


if __name__ == '__main__':
    a = sys.argv[1:]
    step = int(a[a.index('--step') + 1]) if '--step' in a else 3
    sweeps = int(a[a.index('--sweeps') + 1]) if '--sweeps' in a else 3
    start = json.load(open(a[a.index('--start') + 1]))['params'] if '--start' in a else None
    regress = float(a[a.index('--regress') + 1]) if '--regress' in a else 0.0
    fit(a[0], a[1], step, sweeps, start, '--fine' in a, regress)
