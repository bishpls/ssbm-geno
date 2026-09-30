"""Kirby trio lab: two Kirbys and Geno. Each Kirby copies Geno; both fire Kirby's Geno Beam at once; then Kirby B drops
his copy (taunt), inhales Kirby A, who holds Geno's copy, and swallows him: B takes the copy (as Kirby takes a copied
Kirby's power in the game: ftCo_800BD9E0 returns the victim's hat) and fires it, and A comes out without it (his B is
the inhale again). Logged by KBCOPY/KBLOSE, KBGE and the motion states (544-551 are the copy's).
    .venv/bin/python tools/machinima/melee/build.py projects/geno kirby_trio_lab
"""
import sys
from dsl import Film

A, B, GENO = 0, 1, 2
f = Film(len_s=2000 / 60)
f.setup(players=[('kirby', dict(x=-12, face=1)), ('kirby', dict(x=40, face=-1, color=1)), ('geno', dict(x=6, face=-1))],
        seed=7)
ka, kb, ge = f.port(A), f.port(B), f.port(GENO)
f.cam(0, eye=(0, 30, 230), at=(0, 14, 0), fov=30, ease='cut', track='mid')


def swallow(p, t0):
    p.hold(t0, 35, btn='B'); p.hold(t0 + 62, 6, stick=(0, -80))


def status(t):
    for k in (A, B, GENO):
        f.status(t + k, k)


t = 70                                       # A copies Geno
f.mark(t, 0, 'a_copies'); swallow(ka, t); status(t + 150)
t = 270                                      # B copies Geno
f.reset(t - 18, A, -45, 1); f.reset(t - 18, B, 24, -1); f.reset(t - 18, GENO, 6, 1)
f.mark(t, 1, 'b_copies'); swallow(kb, t); status(t + 150)
t = 470                                      # both fire: A a tap and a full charge, B a two-star Beam
f.reset(t - 18, A, -30, 1); f.reset(t - 18, B, 30, -1); f.reset(t - 18, GENO, -60, 1)
for k in (A, B, GENO):
    f.percent(t - 16, k, 0)
f.mark(t, 2, 'both_fire'); ka.hold(t, 3, btn='B'); kb.hold(t, 3, btn='B')     # Finger Shots cross
f.reset(t + 82, A, -30, 1); f.reset(t + 82, B, 30, -1)
ka.hold(t + 100, 45, btn='B'); kb.hold(t + 100, 45, btn='B')                        # two-star Beams cross
status(t + 200)
t = 800                                      # B drops his copy
f.reset(t - 18, A, -30, 1); f.reset(t - 18, B, 30, -1)
f.mark(t, 3, 'b_taunt'); kb.taunt(t); status(t + 120)
t = 1000                                     # B inhales A (who holds Geno's copy) and swallows him
f.reset(t - 18, A, 6, -1); f.reset(t - 18, B, -12, 1); f.reset(t - 18, GENO, 60, -1)
for k in (A, B):
    f.percent(t - 16, k, 0)
f.mark(t, 4, 'b_copies_a'); swallow(kb, t); status(t + 200)
t = 1450                                     # B fires the copy; A's B is his inhale again
f.reset(t - 18, A, 30, -1); f.reset(t - 18, B, -30, 1); f.reset(t - 18, GENO, 60, -1)
f.mark(t, 5, 'after'); kb.hold(t, 30, btn='B'); ka.hold(t + 150, 30, btn='B'); status(t + 60); status(t + 170)
f.emit(sys.argv[1])
