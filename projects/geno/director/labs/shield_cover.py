"""Shield coverage from a shield_lab run's log: for each fighter and each logged frame, how far each hurtbox capsule reaches
outside the shield sphere (world units; > 0 means an attack can touch that hurtbox without meeting the shield, a poke).
    .venv/bin/python projects/geno/director/labs/shield_cover.py ~/games/dolphin-user/Logs/dolphin.log [NAME0 NAME1]
"""
import math, re, sys

def main(log, names=('p0', 'p1')):
    shield, hurts = {}, {}
    for l in open(log, errors='replace'):
        m = re.search(r'SHIELD (\d+) (\d) motion (\d+) health ([\d.]+) centre (\S+) (\S+) (\S+) radius (\S+) scale (\S+) pos (\S+) (\S+)', l)
        if m:
            s, p = int(m.group(1)), int(m.group(2))
            shield[(s, p)] = dict(motion=int(m.group(3)), health=float(m.group(4)), c=tuple(map(float, m.group(5, 6, 7))),
                                  R=float(m.group(8)), k=float(m.group(9)), pos=tuple(map(float, m.group(10, 11))))
        m = re.search(r'HURT (\d+) (\d) (\d+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+)', l)
        if m:
            s, p = int(m.group(1)), int(m.group(2))
            v = list(map(float, m.group(4, 5, 6, 7, 8, 9, 10)))
            hurts.setdefault((s, p), []).append((int(m.group(3)), v[0:3], v[3:6], v[6]))
    for (s, p), sh in sorted(shield.items()):
        c, R, k = sh['c'], sh['R'], sh['k']
        worst = []
        for i, a, b, r in hurts.get((s, p), []):
            rr = r * k
            out = max(math.dist(a, c), math.dist(b, c)) + rr - R
            worst.append((out, i))
        worst.sort(reverse=True)
        top = max((max(a[1], b[1]) + r * k) for _, a, b, r in hurts.get((s, p), [])) - sh['pos'][1]
        print(f"{names[p]:>8} s{s} motion {sh['motion']} health {sh['health']:.0f}: shield centre {c[1] - sh['pos'][1]:.2f} up, "
              f"{(c[0] - sh['pos'][0]):+.2f} x, radius {R:.2f}; body top {top:.2f}; worst {', '.join(f'#{i} {o:+.2f}' for o, i in worst[:4])}")

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:4] if len(sys.argv) > 3 else ('p0', 'p1'))
