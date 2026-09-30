"""Cheer lab: the crowd chants for Geno. The chant (crowdsfx.c un_80321EBC) starts when a human player at 100%+ lands a hit
whose knockback is 130+ within 60 frames of another 100+ knockback hit of theirs (the crowd config in PlCo.dat), at most
once per 1200 frames and never twice running for the same fighter. Here Geno (port 0, human, 120%) forward-smashes two
Foxes standing together (CHEER_FOX_PCT, default 80%): his double punch hits one, then the other 8 frames later, so the
second hit is the "string" and the crowd gasps, then plays PlGe.dat's chant (FtSFX+0x34) back to back, then cheers. The
director logs the crowd's state (CROWD lines: who, which sound, the play count) and the audio dump holds what it sounds
like.
    .venv/bin/python tools/machinima/melee/build.py projects/geno cheer_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol OUT --until 'DIRECTOR END' --res 1 --quiet
    .venv/bin/python projects/geno/director/cheer_lab.py --report OUT
After the closing cheer it plays Super Mario RPG's two timed-hit sounds (550054, 550055) with the director's sfx cue, so
the same capture checks them in game (SFX lines). CHEER_LEN (seconds, default 27) sets the length: the chant is 8 plays
of the sample after the gasp (about 19 s), then the closing cheer.
CHEER_WHO=mario puts Mario in Geno's place (a retail chant, for reference).
"""
import os, sys

GENO, FOX_A, FOX_B = 0, 1, 2
T_HIT = 70            # the smash input (it lands about 15 frames later)


def report(run):
    log = [l.split() for l in open(os.path.join(run, 'osreport.log'), errors='replace')]
    hits = [l for l in log if l and l[0] == 'HIT']
    crowd = [l for l in log if l and l[0] == 'CROWD']
    print('hits:', ' | '.join(' '.join(h[1:5]) for h in hits[:6]))
    for c in crowd:
        s, who, chant, count = int(c[1]), c[3], int(c[5]), int(c[7])
        print(f'  frame {s:5d} ({s / 60:6.2f} s)  fighter {who}  chant {chant}  count {count}')
    for l in log:
        if l and l[0] == 'SFX':
            print(f'  frame {int(l[1]):5d}  sound {l[3]}  voice {l[5]}')
    starts = [int(c[1]) for c in crowd if int(c[7]) >= 1 and int(c[5]) not in (540000,)]
    if len(starts) >= 2:
        gaps = [b - a for a, b in zip(starts, starts[1:])]
        print('frames between chant plays:', gaps)


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--report':
    report(sys.argv[2]); sys.exit()

from dsl import Film

who = os.environ.get('CHEER_WHO', 'geno')
f = Film(len_s=float(os.environ.get('CHEER_LEN', 27)))
f.setup(players=[(who, dict(x=-14, face=1)), ('fox', dict(x=4, face=-1)), ('fox', dict(x=7, face=-1, color=1))], seed=3)
g = f.port(GENO)
f.cam(0, eye=(-2, 24, 175), at=(-2, 14, 0), fov=30, ease='cut')
for k in (GENO, FOX_A, FOX_B):
    f.status(20 + k, k)
fox_pct = float(os.environ.get('CHEER_FOX_PCT', 80))
f.percent(30, GENO, 120); f.percent(30, FOX_A, fox_pct); f.percent(30, FOX_B, fox_pct)
f.mark(T_HIT, 0, 'fsmash')
g.hold(T_HIT, 3, c=(80, 0))                      # C-stick forward: an uncharged forward smash
f.status(T_HIT + 40, GENO)
if f.n > 1560:                                   # the timed-hit sounds, after the chant's closing cheer
    f.mark(1470, 1, 'timed_hit'); f.sfx(1470, 550054)
    f.mark(1540, 2, 'timed_boost'); f.sfx(1540, 550055)
f.emit(sys.argv[1])
