"""Ground truth for datkit movedata's reach: Mario jabs and Marth forward-smashes a standing Fox at a sweep of distances;
the farthest distance that still connects, minus Fox's own depth, is the move's measured reach."""
import json, os, sys
from dsl import Film

SLOT = 70
TESTS = [('mario', 'jab', d) for d in (8, 10, 12, 14, 16, 18, 20)] + [('marth', 'fsmash', d) for d in (14, 17, 20, 23, 26, 29)]
plan = []
attacker = os.environ.get('REACH_ATTACKER', 'mario')     # one attacker per build: REACH_ATTACKER=marth for the second
tests = [t for t in TESTS if t[0] == attacker]
f = Film(len_s=(len(tests) * SLOT + 110) / 60)
f.setup(players=[(attacker, dict(x=-10, face=1)), ('fox', dict(x=10, face=-1))], seed=2)
a, fox = f.port(0), f.port(1)
for i, (who, move, d) in enumerate(tests):
    t0 = 70 + i * SLOT
    f.reset(t0 - 18, 0, -d / 2, 1); f.reset(t0 - 18, 1, d / 2, -1)
    f.percent(t0 - 16, 1, 0)
    f.mark(t0, i, f'{who} {move} {d}')
    if move == 'jab':
        a.hold(t0, 2, btn='A')
    else:
        a.hold(t0, 3, c=(80, 0))
    plan.append(dict(who=who, move=move, d=d, input=t0))
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
