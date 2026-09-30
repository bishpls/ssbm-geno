"""Kill lab: Geno's kill moves on Fox at a sweep of percents, centre stage on Final Destination, at no DI and at full
perpendicular DI either side of the launch (the better of the two is optimal DI).
A kill counts only if Fox dies before he can act: after the hit he mashes jump, so the first frame hitstun lets him act
shows as a double jump (states 27/28), and a clean KO is a Dead state (0-10) logged before that. Deaths after he could
act (momentum he might have recovered from) are reported separately.
    .venv/bin/python tools/machinima/melee/build.py projects/geno kill_lab
    .venv/bin/python projects/geno/director/kill_lab.py --report RUN_DIR PLAN.json
"""
import json, math, os, sys

SLOT = int(os.environ.get('KILL_SLOT', '520'))   # a kill (even a late one), the respawn, and Fox off the platform before
# the next reset. A slow death (a KO* near +320) can still be respawning at the next reset, and that test then misses:
# KILL_SLOT=700 for moves that kill late (the Flash's late hit)
GENO, FOX = 0, 1
PERCENTS = [60, 80, 100, 120, 140, 160]
# (move, Geno's x, Geno's facing, inputs (frame offset, frames, stick, cstick, buttons; mirrored by facing),
#  about when it hits (frames from the input), the launch angle at kill knockback (degrees; 361 is ~44 on the ground))
MOVES = [
    ('beam3', -40, 1, [(0, 50, (0, 0), (0, 0), 'B')], 65, 44),
    # down B with the stick straight down (forward-down reads as side B), then forward by frame 10 so the Blast's
    # marks land far past Fox and only the Flash can hit him
    # (contact +102: the sun's first frame, measured 2026-09-29; it said 90, so its DI started 8 frames before the sun
    # appeared and Fox was already moving, tap-jumping for the upward DI)
    ('flash', -30, 1, [(0, 8, (0, -80), (0, 0), 'B'), (8, 92, (70, -20), (0, 0), 'B')], 102, 45),
    # the Flash's late hit (2026-09-29): Geno 24 further back, so the sun's centre is 24 left of Fox and its edge reaches
    # him only after the burst (the radius passes ~20 about 16 frames in, with either growth)
    ('flash_late', -54, 1, [(0, 8, (0, -80), (0, 0), 'B'), (8, 92, (70, -20), (0, 0), 'B')], 118, 45),
    ('fsmash', -22, 1, [(0, 3, (0, 0), (80, 0), '')], 15, 44),
    ('usmash', -3, 1, [(0, 3, (0, 0), (0, 80), '')], 9, 90),
    ('bair', -12, -1, [(0, 2, (0, 0), (0, 0), 'X'), (12, 2, (0, 0), (-80, 0), '')], 24, 44),
    ('dsmash', -12, 1, [(0, 3, (0, 0), (0, -80), '')], 7, 30),
]
DI = [('none', None), ('ccw', 90), ('cw', -90)]   # full stick at the launch angle +/-90 degrees (Fox flies to +x)
DEAD, JUMP_AERIAL = range(0, 11), (27, 28)


def report(run, plan_path):
    plan = json.load(open(plan_path))
    log = [l.split() for l in open(os.path.join(run, 'osreport.log'), errors='replace')]
    ms = [l for l in log if l and l[0] == 'MS' and l[2] == '1']
    hits = [l for l in log if l and l[0] in ('IHIT', 'HIT')]
    res = {}
    for p in plan:
        t0 = p['input']
        inside = lambda f: t0 <= f < t0 + SLOT - 20
        hit = next((int(h[1]) for h in hits if inside(int(h[1]))), None)
        dead = next((int(m[1]) for m in ms if inside(int(m[1])) and int(m[3]) in DEAD), None)
        ctrl = next((int(m[1]) for m in ms if inside(int(m[1])) and int(m[3]) in JUMP_AERIAL and hit and int(m[1]) > hit), None)
        if hit is None: r = 'miss'
        elif dead is not None and (ctrl is None or dead < ctrl): r = 'KO'
        elif dead is not None: r = 'KO*'              # died, but only after he could act
        else: r = 'live'
        res.setdefault(p['move'], {}).setdefault(p['di'], []).append((p['percent'], r))
    pcts = sorted({p['percent'] for p in plan})               # the run's own sweep (KILL_PCTS), not the default
    # the first percent from which every higher one is a clean KO (a lone early KO between lives doesn't count)
    def first(rows, ok=('KO',)):
        rows = sorted(rows)
        for i, (q, r) in enumerate(rows):
            if all(rr in ok for _, rr in rows[i:]):
                return q
        return None
    fmt = lambda q: f'{q}%' if q is not None else f'>{pcts[-1]}%'
    print('Clean KO = dead before Fox could act; KO* = dead after he could act. Cells: no DI / DI ccw / DI cw.\n')
    print('| move | ' + ' | '.join(f'{q}%' for q in pcts) + ' | clean KO, no DI | clean KO, optimal DI | any KO, optimal DI |')
    print('|---|' + '---|' * (len(pcts) + 3))
    for mv, by in res.items():
        cells = []
        for q in pcts:
            cells.append(' / '.join(dict(by.get(d, [])).get(q, '?') for d, _ in DI))
        per_di = {d: first(by.get(d, [])) for d, _ in DI}
        any_di = {d: first(by.get(d, []), ('KO', 'KO*')) for d, _ in DI}
        opt = max(per_di.values(), key=lambda q: 999 if q is None else q)
        best = max(per_di, key=lambda d: 999 if per_di[d] is None else per_di[d])
        opt_any = max(any_di.values(), key=lambda q: 999 if q is None else q)
        print(f'| {mv} | ' + ' | '.join(cells) + f" | {fmt(per_di['none'])} | {fmt(opt)} ({best}) | {fmt(opt_any)} |")


if __name__ == '__main__' and sys.argv[1] == '--report':
    report(sys.argv[2], sys.argv[3]); sys.exit()

from dsl import Film
if os.environ.get('KILL_MOVES'):
    MOVES = [m for m in MOVES if m[0] in os.environ['KILL_MOVES'].split(',')]
if os.environ.get('KILL_PCTS'):
    PERCENTS = [int(q) for q in os.environ['KILL_PCTS'].split(',')]
tests = [(m, gx, face, steps, hit, ang, q, di, rot) for m, gx, face, steps, hit, ang in MOVES for q in PERCENTS
         for di, rot in DI]
f = Film(len_s=(len(tests) * SLOT + 110) / 60)
f.setup(players=[('geno', dict(x=-30, face=1)), ('fox', dict(x=0, face=-1))], seed=11, coll=0)
geno, fox = f.port(GENO), f.port(FOX)
f.cam(0, eye=(0, 40, 320), at=(0, 30, 0), fov=40, ease='cut', track='mid')
plan = []
for i, (m, gx, face, steps, hit, ang, q, di, rot) in enumerate(tests):
    t0 = 70 + i * SLOT
    f.reset(t0 - 18, GENO, gx, face)
    f.reset(t0 - 18, FOX, 0, -1 if gx < 0 else 1)
    f.percent(t0 - 16, GENO, 0); f.percent(t0 - 16, FOX, q)
    f.mark(t0, i, f'{m}@{q}/{di}')
    for at, n, stick, c, btn in steps:
        geno.hold(t0 + at, n, stick=stick, c=c, btn=btn, dir=face)
    di_stick = (0, 0) if rot is None else (round(80 * math.cos(math.radians(ang + rot))), round(80 * math.sin(math.radians(ang + rot))))
    for k in range(hit + 4, hit + 190):                # DI from after contact (input lands a frame late) through hitlag; earlier, the stick moves him
                                                       # before the hit), then mash jump to find the first actionable frame
        stick = di_stick if k <= hit + 30 else (0, 0)
        btn = 'X' if k >= hit + 12 and (k - hit) % 3 == 0 else ''
        fox.hold(t0 + k, 1, stick=stick, btn=btn)
    for k in range(210, SLOT - 70, 20):                # off the respawn platform whenever it arrives (standing: a crouch)
        fox.hold(t0 + k, 4, stick=(0, -80))
    plan.append(dict(move=m, percent=q, di=di, input=t0))
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
