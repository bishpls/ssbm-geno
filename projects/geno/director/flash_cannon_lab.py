"""Flash cannon lab (geno-cannon): Geno Flash's full-body cannon (DESIGN §12, projects/geno/model/geno_cannon.py), each
segment one Flash (down B held to the third star) opening with a sync slate. Fox stands at the sun, or comes in to hit.
    CANNON_LAB=main      (default) the look and the resets, keyed cameras:
        side     close, side on: the fold in, the aim, the shot and its recoil, the fold out; Geno's hurtboxes logged every
                 2 frames (the director's shield cue: HURT lines), for the before/after hurtbox check
        front    close, three-quarter from in front (the muzzle, the wheels)
        back     close, three-quarter from behind (the breech, the trail)
        match    match distance, framed as flash_fx_lab's
        hit_in   Fox, behind him, forward tilts him on Flash frame ~36 (the cannon aimed): he must come back as Geno at once
        hit_out  the same on frame ~70 (the cannon folding)
        metal    a Metal Box, then the Flash: the metal cannon
        ko       at 400%, Fox's forward smash on frame ~40 KOs him; he respawns as Geno
        fold     close from three quarters in front, on him: the fold back (the capelet and the cap's point)
    CANNON_COLL=1        (main) with the game's collision display: his hurtboxes over the cannon
    CANNON_SEGS=side,... (main) only those segments
    CANNON_LAB=match     the game's own camera (the match framing), Geno and Fox 42 apart: two Flashes
    CANNON_LAB=costumes  COSTUME_SET (default 0,1,2,3) Genos side by side, all casting at once; the game frozen on Flash
                         frame 45 (aimed) for the line-up, each cannon close and the line-up from behind, then on 51
                         (the recoil)
    .venv/bin/python tools/machinima/melee/build.py projects/geno flash_cannon_lab
A plan (segment starts, the charge's first frame, slates) is written next to the script as flash_cannon_lab.plan.json;
copy it beside a run as RUN.plan.json for projects/geno/fx's fxsync.py, fxstrips.py and fxreel.py (and cannon_board.py).
"""
import json, os, sys
from dsl import Film

MODE = os.environ.get('CANNON_LAB', 'main')
GENO, FOX = 0, 1
GX = -30
DOWN = (0, -80)
SYNC = 10
FLASH_AT = 49          # the charge turns into the Flash this many frames after B goes down (BLAST_FLASH_FRAME 48, +1)


def slate(f, t):
    f.cue(t - SYNC, 'stage', a=0); f.cue(t - SYNC, 'bgcolor', a=255, b=0, c=255)
    f.cue(t - SYNC + 2, 'stage', a=1); f.cue(t - SYNC + 2, 'bgcolor', a=0, b=0, c=0)


def main():
    CLOSE_SIDE = dict(eye=(GX + 4, 7, 46), at=(GX + 4, 6, 0))
    FOLD = dict(eye=(GX + 12, 9, 36), at=(GX + 0.5, 7.5, 0))          # three quarters, close on him as he folds back
    FRONT = dict(eye=(GX + 30, 11, 34), at=(GX + 2, 5, 0))
    BACK = dict(eye=(GX - 30, 12, 34), at=(GX + 1, 5, 0))
    MATCH = dict(eye=(5, 14, 150), at=(5, 12, 0))
    WIDE = dict(eye=(-60, 30, 330), at=(-60, 20, 0))
    SEGS = [('side', 200, CLOSE_SIDE, 'sun'), ('front', 200, FRONT, 'sun'), ('back', 200, BACK, 'sun'),
            ('match', 200, MATCH, 'sun'), ('hit_in', 190, CLOSE_SIDE, 36), ('hit_out', 190, CLOSE_SIDE, 70),
            ('metal', 330, CLOSE_SIDE, 'metal'), ('ko', 420, WIDE, 40), ('fold', 200, FOLD, 'sun')]
    if os.environ.get('CANNON_SEGS'):                        # a subset, e.g. CANNON_SEGS=side (a dynamics trace)
        SEGS = [g for g in SEGS if g[0] in os.environ['CANNON_SEGS'].split(',')]
    f = Film(len_s=(70 + sum(s[1] for s in SEGS) + 40) / 60)
    f.setup(players=[('geno', dict(x=GX, face=1)), ('fox', dict(x=GX + 30, face=-1))], seed=5,
            coll=int(os.environ.get('CANNON_COLL', '0')))
    geno, fox = f.port(GENO), f.port(FOX)
    t, plan = 70, []
    for label, n, cam, what in SEGS:
        # Fox at the sun, or behind Geno to hit him (clear of the sun, which would hit him first)
        fx, fd = (GX + 30, -1) if what in ('sun', 'metal') else (GX - 13, 1)
        if label == 'fold':
            fx = GX + 70                                       # out of the shot
        f.reset(t - 20, GENO, GX, 1); f.reset(t - 20, FOX, fx, fd)
        f.percent(t - 18, FOX, 0); f.percent(t - 18, GENO, 400 if label == 'ko' else 0)
        f.cam(t - 20, fov=30, ease='cut', **cam)
        slate(f, t)
        b = t
        if what == 'metal':
            f.item(t, 'metal', GX + 1.5)                      # the Metal Box at his feet; A picks it up
            geno.hold(t + 20, 3, btn='A')
            b = t + 120                                        # the metal transformation plays first
        geno.hold(b, 55, stick=DOWN, btn='B')
        if isinstance(what, int):                              # Fox's forward tilt (smash for the KO) lands on that frame
            fox.move(b + FLASH_AT + what, 'fsmash' if label == 'ko' else 'ftilt', dir=fd)
        if label == 'side':                                    # his hurtboxes, every 2 frames of the Flash
            for k in range(0, 96, 2):
                f.shield(b + FLASH_AT + k, GENO)
        f.mark(t, len(plan), label)
        plan.append(dict(label=label, start=t, b=b, flash=b + FLASH_AT, frames=n, sync=t - SYNC))
        t += n
    return f, plan


def match():
    f = Film(len_s=(60 + 2 * 230 + 30) / 60)
    f.setup(players=[('geno', dict(x=-21, face=1)), ('fox', dict(x=21, face=-1))], seed=5)
    f.game_camera()
    geno = f.port(GENO)
    t, plan = 60, []
    for i in range(2):
        f.reset(t - 20, GENO, -21, 1); f.reset(t - 20, FOX, 21, -1); f.percent(t - 18, FOX, 0)
        slate(f, t)
        geno.hold(t, 55, stick=DOWN, btn='B')
        f.mark(t, i, f'match{i}')
        plan.append(dict(label=f'match{i}', start=t, b=t, flash=t + FLASH_AT, frames=230, sync=t - SYNC))
        t += 230
    return f, plan


def costumes():
    cos = [int(c) for c in os.environ.get('COSTUME_SET', '0,1,2,3').split(',')]
    X = [-51, -17, 17, 51][:len(cos)]
    t0 = 60
    fl = t0 + FLASH_AT
    # (Flash frame to hold, label, camera: an orbit about `at`): the line-up aimed, each cannon close from three quarters
    # in front, the line-up from behind, and the recoil
    shots = [(45, 'lineup', dict(at=(0, 5, 0), dist=235, yaw=8, pitch=6))]
    shots += [(45, f'close{i}', dict(at=(x + 2, 4.5, 0), dist=36, yaw=32, pitch=10)) for i, x in enumerate(X)]
    shots += [(45, 'behind', dict(at=(0, 5, 0), dist=235, yaw=-165, pitch=12)),
              (51, 'recoil', dict(at=(0, 6, 0), dist=235, yaw=8, pitch=6))]
    n = t0 + FLASH_AT + 60 + 30 * len(shots) + 30
    f = Film(len_s=n / 60)
    f.setup(players=[('geno', dict(x=x, face=1, color=c)) for x, c in zip(X, cos)], seed=5)
    f.orbit(0, at=(0, 6, 0), dist=235, yaw=0, pitch=6, fov=30, ease='cut')
    slate(f, t0)
    for i in range(len(cos)):
        f.port(i).hold(t0, 55, stick=DOWN, btn='B')
    plan, cur, t, since, held = [], None, 0, 0, 0      # held: director frames spent frozen so far (the game's clock stops)
    for fr, label, o in shots:
        if cur != fr:
            if cur is not None:
                f.freeze(t, False); held += t - since          # run on to the next frame to hold
            t = since = fl + fr + held
            f.freeze(t, True); cur = fr
        f.orbit(t, fov=30, ease='cut', **o)
        f.mark(t, len(plan), label)
        plan.append(dict(label=label, start=t, flash_frame=fr, frames=30, costume=cos[int(label[5:])] if label.startswith('close') else None))
        t += 30
    f.freeze(t, False)
    return f, plan


f, plan = {'main': main, 'match': match, 'costumes': costumes}[MODE]()
f.emit(sys.argv[1])
json.dump(plan, open(os.path.splitext(sys.argv[1])[0] + '.plan.json', 'w'), indent=1)     # fx/fxsync.py's plan: a list
