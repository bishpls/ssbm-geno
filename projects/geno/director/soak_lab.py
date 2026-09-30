"""Soak: minutes of seeded random play for Geno and Fox, looking for asserts and freezes (deaths, respawns, ledges,
projectiles everywhere, specials mid-everything). SOAK_STAGE=final_destination|battlefield, SOAK_SEED, SOAK_MIN.
    SOAK_STAGE=battlefield .venv/bin/python tools/machinima/melee/build.py projects/geno soak_lab
"""
import json, os, random, sys
from dsl import Film

MIN = float(os.environ.get('SOAK_MIN', '5'))
STAGE = os.environ.get('SOAK_STAGE', 'final_destination')
rng = random.Random(int(os.environ.get('SOAK_SEED', '7')))
N = int(MIN * 3600)
f = Film(len_s=(N + 110) / 60)
f.setup(players=[('geno', dict(x=-30, face=1)), ('fox', dict(x=30, face=-1))], stage=STAGE, seed=rng.randrange(1 << 30), coll=0)
f.cam(0, eye=(0, 30, 300), at=(0, 20, 0), fov=40, ease='cut', track='mid')
STICKS = [(0, 0), (80, 0), (-80, 0), (0, 80), (0, -80), (60, 60), (-60, 60), (60, -60), (-60, -60), (40, 0), (-40, 0)]
CSTICKS = [(80, 0), (-80, 0), (0, 80), (0, -80)]


def random_play(port, bias_b):
    t = 70
    while t < N:
        n = rng.randint(2, 30)
        r = rng.random()
        stick = rng.choice(STICKS)
        if r < bias_b:                     # specials, held for a charge or tapped
            port.hold(t, n if rng.random() < 0.5 else 3, stick=stick, btn='B')
        elif r < bias_b + 0.2:             # attacks
            port.hold(t, 3, stick=stick, btn='A')
        elif r < bias_b + 0.3:             # c-stick smashes and aerials
            port.hold(t, 3, stick=stick, c=rng.choice(CSTICKS))
        elif r < bias_b + 0.45:            # jumps, often into an attack
            port.hold(t, 2, stick=stick, btn='X')
            if rng.random() < 0.6:
                port.hold(t + rng.randint(3, 15), 2, stick=rng.choice(STICKS), btn='A')
        elif r < bias_b + 0.55:            # shield, grabs, rolls
            port.hold(t, n, stick=stick, btn=rng.choice(['R', 'Z', 'R']))
        else:                              # movement
            port.hold(t, n, stick=stick)
        t += n + rng.randint(0, 12)


random_play(f.port(0), 0.35)
random_play(f.port(1), 0.15)
f.emit(sys.argv[1])
json.dump({'frames': N, 'stage': STAGE}, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'))
