"""Curves and arcs of a solved locomotion animation, to catch kinks, pops and dead spots the strips hide: world-frame paths
of the ankles, knees, wrists and head (one dot per frame, so the spacing shows the easing), and per-frame curves of the
pelvis height and yaw, each knee's bend, thigh and upper-arm swing, the boots' pitch and the joints' angular speed.

    .venv/bin/python projects/geno/rig/locoplot.py OUT.png --anim WalkMiddle [--cycles 2] [--json anims.json]
"""
import argparse, json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig


def sample(anim, frames):
    import preview
    out = []
    for f in frames:
        W = rig.world_mats(pose=preview.anim_frame(anim, f))
        out.append(W)
    return out


def ang(u, v):
    c = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-9)
    return math.degrees(math.acos(max(-1, min(1, c))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--anim', required=True); ap.add_argument('--cycles', type=int, default=2)
    ap.add_argument('--json'); ap.add_argument('--speed', type=float)
    a = ap.parse_args()
    if a.json:
        anim = json.load(open(a.json))['anims'][a.anim]
    else:
        import anims, locomotion
        got = locomotion.anim(a.anim)
        if got is None:                                   # a state registered in moves.MOVES (states_air, states, moves)
            import moves, states_air
            states_air.register()
            n_, fn = moves.MOVES[a.anim]
            got = (n_, fn(None)[1])
        anim = anims.solve_keys(*got)
    import locomotion
    n = anim['frames']
    v = a.speed if a.speed is not None else locomotion.SPEED.get(a.anim, 0.0)
    cyc = a.cycles if a.anim in locomotion.SPEED else 1
    frames = [f for f in range(n * cyc + 1)]
    Ws = sample(anim, [f % n if cyc > 1 else f for f in frames])
    P = lambda W, j: np.array(W[j][3][:3])
    fig = plt.figure(figsize=(18, 11))
    ax = fig.add_axes([0.04, 0.55, 0.92, 0.4])
    for j, col in (('LFootJ', 'tab:blue'), ('RFootJ', 'tab:red'), ('LKneeJ', 'lightsteelblue'), ('RKneeJ', 'lightsalmon'),
                   ('LHandN', 'navy'), ('RHandN', 'darkred'), ('HeadN', 'k'), ('HipN', 'gray')):
        pts = np.array([P(W, j) + np.array([0, 0, v * f]) for f, W in zip(frames, Ws)])
        ax.plot(pts[:, 2], pts[:, 1], '-', color=col, lw=1)
        ax.plot(pts[:, 2], pts[:, 1], '.', color=col, ms=4, label=j)
    for f, W in zip(frames, Ws):
        if f % max(1, n // 8): continue
        o = np.array([0, 0, v * f])
        for chain in (('HipN', 'LLegJ', 'LKneeJ', 'LFootJ', 'LToeN'), ('HipN', 'RLegJ', 'RKneeJ', 'RFootJ', 'RToeN'),
                      ('HipN', 'WaistN', 'NeckN', 'HeadN'), ('WaistN', 'LShoulderJ', 'LArmJ', 'LHandN'),
                      ('WaistN', 'RShoulderJ', 'RArmJ', 'RHandN')):
            pts = np.array([P(W, j) + o for j in chain])
            ax.plot(pts[:, 2], pts[:, 1], '-', color=(0.6, 0.6, 0.6, 0.5), lw=0.8)
    ax.axhline(0, color='k', lw=0.5); ax.set_aspect('equal'); ax.legend(fontsize=7, ncol=8, loc='upper left')
    ax.set_title(f'{a.anim}: world paths (body carried at {v:g}/frame), one dot per frame')
    # curves
    def seg(W, a_, b_): return P(W, b_) - P(W, a_)
    rows = []
    for W in Ws:
        r = {}
        r['pelvis y'] = P(W, 'HipN')[1]
        x = np.array(W['HipN'][0][:3]); r['pelvis yaw'] = math.degrees(math.atan2(-x[2], x[0]))
        x = np.array(W['WaistN'][0][:3]); r['chest yaw'] = math.degrees(math.atan2(-x[2], x[0]))
        for s in 'LR':
            th, sh = seg(W, f'{s}LegJ', f'{s}KneeJ'), seg(W, f'{s}KneeJ', f'{s}FootJ')
            r[f'{s} knee'] = ang(th, sh)
            r[f'{s} thigh'] = math.degrees(math.atan2(th[2], -th[1]))
            f_ = np.array(W[f'{s}FootJ'][0][:3]); r[f'{s} boot pitch'] = math.degrees(math.asin(max(-1, min(1, f_[1]))))
            ua = seg(W, f'{s}ShoulderJ', f'{s}ArmJ'); fa = seg(W, f'{s}ArmJ', f'{s}HandN')
            r[f'{s} arm'] = math.degrees(math.atan2(ua[2], -ua[1])); r[f'{s} elbow'] = ang(ua, fa)
        rows.append(r)
    keys = [('pelvis y',), ('pelvis yaw', 'chest yaw'), ('L knee', 'R knee'), ('L thigh', 'R thigh'),
            ('L boot pitch', 'R boot pitch'), ('L arm', 'R arm', 'L elbow', 'R elbow')]
    for i, ks in enumerate(keys):
        axc = fig.add_axes([0.04 + (i % 3) * 0.32, 0.06 + (1 - i // 3) * 0.24, 0.28, 0.19])
        for k in ks:
            axc.plot(frames, [r[k] for r in rows], '.-', ms=3, lw=1, label=k)
        axc.legend(fontsize=7); axc.grid(alpha=0.3)
        if cyc > 1:
            for c in range(1, cyc): axc.axvline(c * n, color='k', lw=0.5)
    fig.savefig(a.out, dpi=90)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
