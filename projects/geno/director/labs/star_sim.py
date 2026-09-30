"""star_sim.py: the up throw's Star Gun salvo against the opponents the throws lab logged, offline (DESIGN §6f).

The stars carry no knockback (rig/articles.py THROW_STAR: a hit adds damage and hitlag, not a launch), so the opponent's
flight after the release is the throw's alone, and a watched `stars` run (throws_lab.py LAB_SET=stars: the opponent's
hurtboxes every frame, with and without DI) records it. This replays any salvo against those flights: when each star
fires (frames after the release), from where (the muzzle, from Geno's position), at what angle (the barrel's, plus the
spray), how fast and how big. A star is the Beam article's state 3: two spheres of radius r along its flight (at its
centre and r behind), each swept from last frame's place to this frame's, as the engine interpolates hitboxes; it hits
the first frame a sphere comes within r of a hurtbox capsule (its segment less its radius). Hitlag is ignored (the
opponent's later frames come a frame or two later in the game).

    .venv/bin/python projects/geno/director/labs/star_sim.py RUN [RUN ...] [--check] [--fire 1,4,7] [--speed 5]
        [--r 6] [--muzzle X,Y] [--barrel DEG] [--spray 6] [--release-shift DX,DY] [--track SHARE,MAXDEG] [--toward]
--check replays the run's own salvo (the logged THROWSHOT muzzles, angles and frames; --release-anim, the release's
animation frame in the build that logged, default 11) and prints the logged hits beside the replay's, to calibrate.
Otherwise --fire gives the stars' animation frames after the release's, --muzzle the muzzle from Geno's start (x toward
his front, y up), --barrel the barrel's angle from straight up (+ toward his front), --spray the spray step (star k
leaves k x step off the barrel, odd toward his front), --toward sends the spray's widest stars the way the opponent
drifts, --track leans the salvo toward them (a share of the angle, at most MAXDEG), and --release-shift moves the logged
flights (a throw that lets go from elsewhere).

2026-09-29 (the salvo that links through DI): --fire 1,4,7 --speed 6.5 --toward --muzzle 2.05,13.8 predicted all three
stars at 0-60% on Fox, Falco and Falcon with full DI either side; the game agreed (DESIGN §6f The projectiles).
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import numpy as np

GENO, FOX = 0, 1
THROWN = (239, 240, 241, 242)


def seg_dist(p0, p1, q0, q1):
    p0, p1, q0, q1 = (np.array(x, float) for x in (p0, p1, q0, q1))
    d1, d2, r = p1 - p0, q1 - q0, p0 - q0
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    if a < 1e-9 and e < 1e-9: return float(np.linalg.norm(r))
    if a < 1e-9: s, t = 0.0, min(1.0, max(0.0, f / e))
    else:
        c = d1 @ r
        if e < 1e-9: s, t = min(1.0, max(0.0, -c / a)), 0.0
        else:
            b = d1 @ d2; den = a * e - b * b
            s = min(1.0, max(0.0, (b * f - c * e) / den)) if den > 1e-9 else 0.0
            t = (b * s + f) / e
            if t < 0: t, s = 0.0, min(1.0, max(0.0, -c / a))
            elif t > 1: t, s = 1.0, min(1.0, max(0.0, (b - c) / a))
    return float(np.linalg.norm((p0 + d1 * s) - (q0 + d2 * t)))


def load(run):
    """per try of a watched stars run: the release frame, Geno's start x and facing, the opponent's capsules by frame,
    the logged shots (anim frame, x, y, angle) and hits (frames)"""
    plan = json.load(open(run.rstrip('/') + '.plan.json'))
    caps, state, pos, shots, hits, marks = {}, {}, {}, [], [], []
    for i, l in enumerate(open(os.path.join(run, 'osreport.log'), errors='replace')):
        q = l.split()
        if not q: continue
        if q[0] == 'HURT' and len(q) >= 11 and q[2] == str(FOX):
            caps.setdefault(int(q[1]), []).append((tuple(float(x) for x in q[4:7]), tuple(float(x) for x in q[7:10]),
                                                    float(q[10])))
        elif q[0] == 'POS' and len(q) >= 8:
            if q[2] == str(FOX): state[int(q[1])] = int(q[5])
            else: pos[int(q[1])] = float(q[3])
        elif q[0] == 'MARK': marks.append(int(q[1]))
        elif q[:3] == ['GENO', 'THROWSHOT', 'star']:
            shots.append((marks[-1] if marks else 0, int(q[3]), float(q[4]), float(q[5]), int(q[6])))
        elif q[0] == 'IHIT' and q[2] == str(FOX): hits.append(int(q[1]))
    out = []
    for p in plan:
        if p['throw'] != 'uthrow': continue
        held = [s for s in range(p['t0'], p['t0'] + p['slot']) if state.get(s) in THROWN]
        if not held: continue
        rel = max(held) + 1
        out.append(dict(label=p['label'], face=p.get('face', 1), rel=rel, gx=pos.get(p['t0'], 0.0),
                        caps={s: caps[s] for s in caps if p['t0'] <= s < p['t0'] + p['slot']},
                        shots=[s[1:] for s in shots if s[0] == p['t0']],
                        hits=[h for h in hits if p['t0'] <= h < p['t0'] + p['slot']]))
    return out


def fly(t, fire, muzzle, angle, speed=5.0, r=6.0, life=26):
    """the frame a star fired on frame `fire` (game frame) from `muzzle` at `angle` (radians from +x) first hits the
    try's capsules, or None"""
    d = np.array([math.cos(angle), math.sin(angle), 0.0])
    m = np.array([muzzle[0], muzzle[1], 0.0])
    for k in range(0, life):
        s = fire + k
        if s not in t['caps']: continue
        c1 = m + d * speed * k
        c0 = m + d * speed * max(0, k - 1)
        for off in (0.0, -r):
            a0, a1 = c0 + d * off, c1 + d * off
            for va, vb, vr in t['caps'][s]:
                if seg_dist(a0, a1, va, vb) <= r + vr:
                    return s
    return None


def drift_side(t):
    """which way the opponent's launch carries them: +1 toward his front, -1 toward his back, 0 hardly (under 0.4 a
    frame: no DI), from their hurtboxes' centre over the flight's first frames (rel+1 to rel+6: the release frame's
    own step is the pose's jump into the flight, not the flight; the game knows it at once, the launch velocity)"""
    cx = lambda s: float(np.mean([(a[0] + b[0]) / 2 for a, b, _ in t['caps'][s]]))
    v = t['face'] * (cx(t['rel'] + 6) - cx(t['rel'] + 1)) / 5.0
    return 0 if abs(v) < 0.4 else (1 if v > 0 else -1)


def replay(t, fire, muzzle, barrel, spray, speed, r, shift=(0.0, 0.0), track=0.0, track_max=0.0, toward=False):
    """the given salvo against the try: fire (animation frames after the release's), muzzle (from Geno's start, x toward
    his front), barrel and spray (degrees; + toward his front). track leans each star's base line that share of the way
    from the barrel toward the opponent's body (their hurtboxes' centre on the frame it fires), at most track_max
    degrees; the spray goes on top. toward: the spray's even stars (the widest) go the way the opponent drifts by the
    first star, the odd stars the other way (no drift: odd toward his front). The flight is moved by shift."""
    f = t['face']
    tt = dict(t)
    if shift != (0.0, 0.0):
        dx, dy = shift[0] * f, shift[1]
        tt = dict(t, caps={s: [((a[0] + dx, a[1] + dy, a[2]), (b[0] + dx, b[1] + dy, b[2]), rr) for a, b, rr in cs]
                           for s, cs in t['caps'].items()})
    out = []
    mz = (t['gx'] + f * muzzle[0], muzzle[1])
    side = (-drift_side(tt) or 1) if toward else 1     # the odd stars' side
    for k, fr in enumerate(fire):
        s0 = t['rel'] + fr - 1
        off = side * spray * k * (1 if k % 2 else -1) if k else 0.0
        lean = 0.0
        if track and s0 in tt['caps']:
            c = np.mean([[(a[0] + b[0]) / 2, (a[1] + b[1]) / 2] for a, b, _ in tt['caps'][s0]], axis=0)
            to = math.degrees(math.atan2(f * (c[0] - mz[0]), c[1] - mz[1]))        # from straight up, + toward his front
            lean = max(-track_max, min(track_max, track * (to - barrel)))
        ang = math.radians(90.0 - f * (barrel + lean + off))
        out.append(fly(tt, s0, mz, ang, speed, r))
    return out


def main():
    a = sys.argv[1:]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    runs = [x for x in a if not x.startswith('--') and (a.index(x) == 0 or not a[a.index(x) - 1].startswith('--'))]
    fire = [int(x) for x in opt('--fire', '14,17,20').split(',')]
    speed, r = float(opt('--speed', 5)), float(opt('--r', 6))
    muzzle = tuple(float(x) for x in opt('--muzzle', '1.9,13.3').split(','))
    barrel, spray = float(opt('--barrel', 4)), float(opt('--spray', 6))
    shift = tuple(float(x) for x in opt('--release-shift', '0,0').split(','))
    track, track_max = (float(x) for x in opt('--track', '0,0').split(','))
    for run in runs:
        name = os.path.basename(run.rstrip('/'))
        for t in load(run):
            if '--check' in a:
                # a star logged on animation frame A leaves on game frame rel + (A - R) - 1 (R: the release's animation
                # frame, 11 in the build that logged; calibrated: the replay's hits then land on the logged frames)
                fires = [t['rel'] + (anim - int(opt('--release-anim', 11))) - 1 for anim, *_ in t['shots']]
                sim = [fly(t, fs, (x, y), math.radians(deg), speed, r) for fs, (anim, x, y, deg) in zip(fires, t['shots'])]
                print(f"{name} {t['label']}: logged hits {[h - t['rel'] for h in t['hits']]}, replay "
                      f"{[(s - t['rel']) if s else None for s in sim]} (frames after the release)")
            else:
                res = replay(t, fire, muzzle, barrel, spray, speed, r, shift, track, track_max, '--toward' in a)
                n = sum(1 for x in res if x is not None)
                print(f"{name} {t['label']}: {n}/3 {[(s - t['rel']) if s else None for s in res]}")


if __name__ == '__main__':
    main()
