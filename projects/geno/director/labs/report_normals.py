"""Measured frame data from a normals-lab run: for each try, Geno's first hit (startup, from the input frame, calibrated
by Fox's frame-2 jab), every hit's frame and damage, and Geno's action states. Compares against moves.py's intent.
    .venv/bin/python projects/geno/director/labs/report_normals.py RUN_DIR PLAN.json
"""
import json, re, sys
from collections import defaultdict

OSR = re.compile(r'\[OSREPORT(?:_HLE)?\]:\s?(.*)$')
INTENT = {                     # (first active frame, damage of the first hitbox) as moves.py writes them
    'jab1': (3, 3), 'jab123': (3, 3), 'ftilt': (7, 10), 'utilt': (6, 9), 'dtilt': (6, 7), 'dash': (6, 9),
    'fsmash': (15, 16), 'usmash': (9, 15), 'dsmash': (7, 12), 'dsmash_back': (13, 12), 'nair': (3, 12), 'fair': (9, 13),
    'bair': (10, 14), 'uair': (5, 10), 'dair': (9, 12), 'fthrow': (None, 8), 'bthrow': (None, 10),
    'uthrow': (None, 7), 'dthrow': (None, 5),
    'jab_tip': (3, 3), 'ftilt_tip': (7, 10), 'dtilt_tip': (6, 7), 'fsmash_tip': (15, 16), 'dsmash_tip': (7, 12), 'grab_tip': (7, 0), 'grab_close': (7, 0),
}


def lines(run):
    try:
        text = open(f'{run}/osreport.log', errors='replace').read().splitlines()
    except FileNotFoundError:
        text = []
    out = []
    for l in text:
        m = OSR.search(l)
        out.append(m.group(1) if m else l)
    return out


def main(run, plan_path):
    plan = json.load(open(plan_path))
    hits, ms, status = [], defaultdict(list), []
    for l in lines(run):
        p = l.split()
        if not p: continue
        if p[0] == 'HIT':
            hits.append(dict(s=int(p[1]), a=int(p[2]), v=int(p[3]), dmg=float(p[4])))
        elif p[0] == 'MS':
            ms[int(p[2])].append((int(p[1]), int(p[3])))
        elif p[0] == 'STATUS':
            status.append(dict(s=int(p[1]), port=int(p[2]), pct=float(p[3]), x=float(p[4]), y=float(p[5]), ms=int(p[6])))
    windows = [(t['input'], plan[i + 1]['input'] if i + 1 < len(plan) else 10 ** 9, t) for i, t in enumerate(plan)]
    fox_cal = next((h for h in hits if h['a'] == 1 and windows[0][0] <= h['s'] < windows[0][1]), None)
    offset = (fox_cal['s'] - windows[0][0]) - 1 if fox_cal else 0     # frame 2 lands at input + 1 + offset
    print(f'calibration: Fox jab input {windows[0][0]}, hit {fox_cal and fox_cal["s"]}, offset {offset}')
    print(f'{"move":13s} {"startup":>8s} {"intent":>7s}  hits (frame from input: damage)')
    rows = []
    for a, b, t in windows[1:]:
        mine = [h for h in hits if h['a'] == 0 and a <= h['s'] < b]
        at = t.get('attack', a)                         # frames count from the attack input, not the setup
        startup = (mine[0]['s'] - at - offset + 1) if mine else None
        st = next((x for x in status if a <= x['s'] < b and x['port'] == 1), None)
        want = INTENT.get(t['label'], (None, None))
        hs = ' '.join(f'{h["s"] - at - offset + 1}:{h["dmg"]:g}' for h in mine)
        if st: hs += f'   [Fox after: {st["pct"]:g}% at ({st["x"]:.0f},{st["y"]:.0f}) state {st["ms"]}]'
        states = ' '.join(str(m) for f, m in ms[0] if a <= f < b)
        flag = '' if (want[0] is None or startup == want[0]) else '  <-- off'
        if not mine and not (st and st['pct'] > 0): flag = '  <-- no hit'
        print(f'{t["label"]:13s} {str(startup):>8s} {str(want[0]):>7s}  {hs}{flag}')
        print(f'{"":13s} states: {states}')
        rows.append(dict(move=t['label'], startup=startup, intent=want[0], hits=[(h['s'] - at - offset + 1, h['dmg']) for h in mine],
                         fox_after=st))
    json.dump(rows, open(f'{run}/normals.json', 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
