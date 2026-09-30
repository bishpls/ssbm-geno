"""Geno's shield against his body: the guard pose's hurtbox capsules (rig.HURTBOXES through the rig's own FK) against the
shield sphere, a unit sphere on ThrowN scaled by the joint (radius 0.575 x ShieldSize at full health, measured in the
shield lab). Finds the centre that needs the smallest sphere, and reports each capsule's margin (negative = inside).
    .venv/bin/python projects/geno/rig/shieldfit.py [LOG]    # LOG: a shield_lab dolphin.log, to check the FK against the game
"""
import math, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import rig
from anims import Pose, base, guard_pose

FULL = 0.575            # full-health radius per unit of ShieldSize (shield lab: 7.88 at 59.7 health for 13.75)


def capsules(pose):
    sol = pose.solve() if pose else None
    W = rig.world_mats(pose={n: {'t': t, 'r': r} for n, (t, r) in sol.items()} if sol else None)
    out = []
    for j, a, b, r, h, g in rig.HURTBOXES:
        M = W[j]
        pw = lambda p: [sum(p[k] * M[k][c] for k in range(3)) + M[3][c] for c in range(3)]
        out.append((j, pw(a), pw(b), r))
    return out, W


def margins(caps, c, R):
    return [(max(math.dist(a, c), math.dist(b, c)) + r - R, j) for j, a, b, r in caps]


def enclose(caps):
    """The centre that minimises the largest capsule reach (a small minimax search in the body's plane and depth)."""
    pts = [(p, r) for _, a, b, r in caps for p in (a, b)]
    c = [sum(p[0][k] for p in pts) / len(pts) for k in range(3)]
    step = 2.0
    need = lambda c: max(math.dist(p, c) + r for p, r in pts)
    best = need(c)
    while step > 0.01:
        moved = False
        for d in ((step, 0, 0), (-step, 0, 0), (0, step, 0), (0, -step, 0), (0, 0, step), (0, 0, -step)):
            cc = [c[k] + d[k] for k in range(3)]
            n = need(cc)
            if n < best: best, c, moved = n, cc, True
        if not moved: step /= 2
    return c, best


if __name__ == '__main__':
    if len(sys.argv) > 1:                         # the FK against the game: rest pose (the old shield pose) at frame 40
        caps, _ = capsules(None)
        game = {}
        for l in open(sys.argv[1], errors='replace'):
            m = re.search(r'HURT 40 0 (\d+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+)', l)
            if m: game[int(m.group(1))] = list(map(float, m.group(2, 3, 4, 5, 6, 7, 8)))
        for i, (j, a, b, r) in enumerate(caps):
            g = game.get(i)
            if g: print(f'{j:12s} FK a {a[0]:6.2f} {a[1]:6.2f} {a[2]:6.2f}  game a {g[0] + 15:6.2f} {g[1]:6.2f} {g[2]:6.2f}   r {r} / {g[6]}')
        sys.exit()
    p = guard_pose()
    caps, W = capsules(p)
    c, need = enclose(caps)
    top = max(max(a[1], b[1]) + r for _, a, b, r in caps)
    hat = max(math.dist([W[j][3][k] for k in range(3)], c) for j in ('CapN', 'CapMidN', 'CapTipN'))
    y = W['YRotN'][3]
    print(f'guard pose: body top {top:.2f}; best centre ({c[0]:.2f}, {c[1]:.2f}, {c[2]:.2f}) needs radius {need:.2f} '
          f'= ShieldSize {need / FULL:.2f} at full health; ThrowN in YRotN\'s frame ({c[0] - y[0]:.2f}, {c[1] - y[1]:.2f}, {c[2] - y[2]:.2f}); '
          f'cap joints reach {hat:.2f}')
    R = FULL * rig.ATTRIBUTES['ShieldSize']
    for name, cc in (('centre now', [W['ThrowN'][3][k] for k in range(3)]), ('best', c)):
        m = sorted(margins(caps, cc, R), reverse=True)
        print(f'  {name} ({cc[1]:.2f} up, {cc[2]:.2f} fwd), full shield {R:.2f}: worst ' + ', '.join(f'{j} {o:+.2f}' for o, j in m[:5]))
