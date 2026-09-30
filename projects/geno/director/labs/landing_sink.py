"""Landing sink report for director/landing_sink_lab.py: on each fighter's last air frame before landing, the body's height
(TopN; the floor is 0) and each ankle's drop against its own standing height (negative: the foot is below the floor by
about that much; the ankle stands in for the sole, so a pointed toe can go a little lower).
    .venv/bin/python projects/geno/director/labs/landing_sink.py RUN [link,mewtwo,geno,fox]
"""
import collections, sys

run = sys.argv[1]
who = (sys.argv[2] if len(sys.argv) > 2 else 'link,mewtwo,geno,fox').split(',')
SEGS = [('plain short hop', 70, 70), ('short hop, B held through the landing', 160, 110)]   # the lab's T0 and slots
pos, feet = collections.defaultdict(dict), collections.defaultdict(dict)
for line in open(f'{run}/osreport.log'):
    w = line.split()
    if w and w[0] == 'POS': pos[int(w[2])][int(w[1])] = (float(w[4]), int(w[5]))
    if w and w[0] == 'FEET': feet[int(w[2])].setdefault(int(w[1]), {})[int(w[3])] = float(w[5])
for name, t0, dur in SEGS:
    print(f'== {name}')
    for p, name_p in enumerate(who):
        stand = feet[p][t0 - 2]
        fr = sorted(k for k in pos[p] if t0 + 4 <= k < t0 + dur)
        land = next((b for a, b in zip(fr, fr[1:]) if abs(pos[p][a][0]) > 1e-3 and abs(pos[p][b][0]) < 1e-3), None)
        if land is None:
            print(f'{name_p:7s} no landing'); continue
        la, fy = land - 1, feet[p][land - 1]
        d = [fy[s] - stand[s] for s in (0, 1)]
        print(f'{name_p:7s} ms {pos[p][la][1]:3d} -> {pos[p][land][1]:3d}: body {pos[p][la][0]:+.2f}, '
              f'ankles {d[0]:+.2f}/{d[1]:+.2f} against standing (lowest {min(d):+.2f})')
