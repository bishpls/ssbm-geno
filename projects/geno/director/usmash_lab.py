"""Up smash lab (Michael, 2026-09-30: it "can't hit through a Battlefield platform to hit someone standing on it"): on
Battlefield, Geno up smashes (uncharged) at a Fox standing on the right side platform (27.2 up) above him, from under
its middle and 5 and 10 units to either side, and at a Fox on the ground in front of him and behind him (the wrists'
flares: the front one strong, the back one the sourspot). Each try logs the hits (damage, the hitbox) and Fox's launch.
Sync slates and his animation frame (FEET) for strips; LAB_CAM=game films on the game's own camera, else a close side one.
    .venv/bin/python tools/machinima/melee/build.py projects/geno usmash_lab
    .venv/bin/python projects/geno/director/usmash_lab.py --report RUN
"""
import json, math, os, sys

GENO, FOX = 0, 1
SLOT = 150
SYNC = 20
PX = 38.0                    # the right side platform's middle (it runs ~18.8 to ~57.6 at 27.2 up)
TESTS = [('ground_front', -3.0, 4.0, 0.0), ('ground_back', -3.0, -10.0, 0.0),
         # beyond the column's reach to the side (it takes anyone within ~7): the wrists' flares alone
         ('flare_front', -3.0, 7.0, 0.0), ('flare_back', -3.0, -13.0, 0.0),
         ('plat_0', PX, PX, 35.0), ('plat_front5', PX, PX + 5, 35.0), ('plat_back5', PX, PX - 5, 35.0),
         ('plat_front10', PX, PX + 10, 35.0), ('plat_back10', PX, PX - 10, 35.0)]


def report(run):
    plan = json.load(open(run.rstrip('/') + '.plan.json'))
    log = [l.split() for l in open(os.path.join(run, 'osreport.log'), errors='replace')]
    pos = {}
    for q in log:
        if q[:1] == ['POS'] and len(q) >= 8 and q[2] == str(FOX): pos[int(q[1])] = (float(q[3]), float(q[4]), int(q[5]))
    out = {}
    for p in plan:
        hits = [(int(q[1]), float(q[4])) for q in log if q[:1] == ['HIT'] and len(q) >= 6 and q[2] == str(GENO)
                and q[3] == str(FOX) and p['t0'] <= int(q[1]) < p['t0'] + SLOT]
        r = dict(label=p['label'], fox=pos.get(p['t0'], (0, 0))[:2], hits=[(s - p['t0'], d) for s, d in hits])
        if hits:
            s = hits[0][0]
            # the launch: Fox's speed over the first frames of flight after the hitlag (his position's steps)
            steps = [(pos[k + 1][0] - pos[k][0], pos[k + 1][1] - pos[k][1]) for k in range(s + 8, s + 12)
                     if k in pos and k + 1 in pos]
            if steps:
                vx = sum(a for a, _ in steps) / len(steps); vy = sum(b for _, b in steps) / len(steps)
                r['speed'] = round(math.hypot(vx, vy), 2); r['angle'] = round(math.degrees(math.atan2(vy, vx)), 1)
        out[p['label']] = r
        print(r)
    json.dump(out, open(os.path.join(run, 'usmash_report.json'), 'w'), indent=1)
    return out


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--report':
    report(sys.argv[2]); sys.exit()

from dsl import Film
f = Film(len_s=(len(TESTS) * SLOT + 180) / 60)
f.setup(players=[('geno', dict(x=-62, face=1)), ('fox', dict(x=62, face=-1))], stage='battlefield', seed=5)
geno, fox = f.port(GENO), f.port(FOX)
if os.environ.get('LAB_CAM') == 'game':
    f.game_camera()
plan, t0 = [], 160                                    # the match has begun: resets hold
for label, gx, fx, fy in TESTS:
    f.reset(t0 - 50, GENO, gx, 1); f.reset(t0 - 50, FOX, fx, -1 if fx > gx else 1)
    # both dropped from just above where they stand (a reset alone keeps a fighter on the floor or platform he was on)
    f.setpos(t0 - 48, GENO, gx, 4.0); f.cue(t0 - 48, 'motion', GENO, a=29)      # airborne (Fall): off any platform
    f.setpos(t0 - 48, FOX, fx, fy or 4.0); f.cue(t0 - 48, 'motion', FOX, a=29)
    f.percent(t0 - 40, GENO, 0); f.percent(t0 - 40, FOX, 0)
    if os.environ.get('LAB_CAM') != 'game':
        f.cam(t0 - 30, eye=(gx, 22, 110), at=(gx, 20, 0), fov=34, ease='cut')
    f.cue(t0 - SYNC, 'stage', a=0); f.cue(t0 - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t0 - SYNC + 2, 'stage', a=1); f.cue(t0 - SYNC + 2, 'bgcolor', a=0, b=0, c=0)
    f.mark(t0, len(plan), label)
    geno.hold(t0, 3, c=(0, 80))
    for k in range(-2, 45):
        f.feet(t0 + k, GENO)
    fox.trace(t0 - 4, t0 + SLOT - 12)
    plan.append(dict(t0=t0, label=label, gx=gx, fx=fx, sync=t0 - SYNC, start=t0 - 2, frames=50))
    t0 += SLOT
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)
