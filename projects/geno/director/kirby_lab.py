"""Kirby lab: Kirby copies Geno and uses Kirby's version of the Geno Beam (decomp ftKirby/ftkirbyspecialgeno.c).
One segment per check, with resets between them (the copy survives a reset, as it survives anything but a taunt, a
lost stock or an unlucky hit):
  spit            inhale Geno and spit him out (A): no copy
  swallow         inhale and swallow (stick down; B swallows too): the copy (KBCOPY kind 34)
  tap             a tapped B: Finger Shot (Kirby state 550), the shot on Geno's frame 10
  full            hold through the third star and release: a 3-star Beam (546), spawned on Geno's frame 8
  two             two stars, released
  auto            held past the third star and the grace: it fires itself (frame 80)
  store           one star, stored by the shield; the next B fires it at once
  air_tap         a short hop and a tap: an aerial Finger Shot (551)
  air_charge      a full hop, charge in the air (548), release (549)
  air_store       a full hop, store two stars in the air, land, fire them from the ground
  decay           store three stars, wait 320 frames (two fade), fire one
  geno_ref        Geno's own tap, full charge, store and stored fire, aerial tap and charge: the frame comparison
  taunt           the taunt takes the copy (KBLOSE ... star 1)
  reswallow       copy him again
  hits            Geno jabs Kirby until a hit takes the copy (1 in 32 per knockback hit)
The log: MS (states), KBCOPY/KBLOSE (copies), KBGE (the copy's stars, stores and spawns), GENO SPAWN, HIT/IHIT, LASER.
    .venv/bin/python tools/machinima/melee/build.py projects/geno kirby_lab
"""
import sys
from dsl import Film

KIRBY, GENO = 0, 1
SEGS = []           # (label, length in frames, function(t0))


def seg(label, n):
    def reg(fn):
        SEGS.append((label, n, fn)); return fn
    return reg


def far(t0):        # Kirby left, Geno right, facing each other: the shooting range
    f.reset(t0 - 18, KIRBY, -30, 1); f.reset(t0 - 18, GENO, 25, -1)
    f.percent(t0 - 16, KIRBY, 0); f.percent(t0 - 16, GENO, 0)


def near(t0):       # Geno in inhale reach
    f.reset(t0 - 18, KIRBY, -12, 1); f.reset(t0 - 18, GENO, 6, -1)
    f.percent(t0 - 16, KIRBY, 0); f.percent(t0 - 16, GENO, 0)


def status(t0, *ks):
    for k in ks:
        f.status(t0 + k, KIRBY)


@seg('spit', 200)
def _(t0):
    near(t0); kb.hold(t0, 35, btn='B'); kb.hold(t0 + 62, 3, btn='A'); status(t0, 40, 70, 150)


@seg('swallow', 200)
def _(t0):
    near(t0); kb.hold(t0, 35, btn='B'); kb.hold(t0 + 62, 6, stick=(0, -80)); status(t0, 40, 120, 190)


@seg('tap', 120)
def _(t0):
    far(t0); kb.hold(t0, 3, btn='B'); status(t0, 12, 60)


@seg('full', 190)
def _(t0):
    far(t0); kb.hold(t0, 70, btn='B'); status(t0, 30, 65, 110)


@seg('two', 150)
def _(t0):
    far(t0); kb.hold(t0, 45, btn='B')


@seg('auto', 180)
def _(t0):
    far(t0); kb.hold(t0, 110, btn='B')


@seg('store', 200)
def _(t0):
    far(t0); kb.hold(t0, 30, btn='B'); kb.hold(t0 + 28, 4, trig=140); kb.hold(t0 + 100, 3, btn='B'); status(t0, 40, 110)


@seg('air_tap', 120)
def _(t0):
    far(t0); kb.hold(t0, 2, btn='X'); kb.hold(t0 + 8, 3, btn='B')


@seg('air_charge', 160)
def _(t0):
    far(t0); kb.hold(t0, 6, btn='X'); kb.hold(t0 + 10, 26, btn='B')


@seg('air_store', 220)
def _(t0):
    far(t0); kb.hold(t0, 6, btn='X'); kb.hold(t0 + 8, 45, btn='B'); kb.hold(t0 + 51, 4, trig=140)
    kb.hold(t0 + 140, 3, btn='B'); status(t0, 60, 150)


@seg('decay', 520)
def _(t0):
    far(t0); kb.hold(t0, 70, btn='B'); kb.hold(t0 + 68, 4, trig=140); kb.hold(t0 + 390, 3, btn='B')


@seg('geno_ref', 760)
def _(t0):
    f.reset(t0 - 18, KIRBY, 30, -1); f.reset(t0 - 18, GENO, -25, 1)
    ge.hold(t0, 3, btn='B'); ge.hold(t0 + 90, 70, btn='B')
    f.reset(t0 + 250, KIRBY, 30, -1); f.reset(t0 + 250, GENO, -25, 1)
    ge.hold(t0 + 270, 30, btn='B'); ge.hold(t0 + 298, 4, trig=140); ge.hold(t0 + 370, 3, btn='B')
    f.reset(t0 + 450, KIRBY, 30, -1); f.reset(t0 + 450, GENO, -25, 1)
    ge.hold(t0 + 470, 2, btn='X'); ge.hold(t0 + 478, 3, btn='B')
    ge.hold(t0 + 600, 6, btn='X'); ge.hold(t0 + 610, 26, btn='B')


@seg('taunt', 200)
def _(t0):
    far(t0); kb.taunt(t0); status(t0, 60, 150)


@seg('reswallow', 200)
def _(t0):
    near(t0); kb.hold(t0, 35, btn='B'); kb.hold(t0 + 62, 6, stick=(0, -80)); status(t0, 120)


@seg('hits', 2400)
def _(t0):
    for k in range(0, 2400 - 60, 60):              # every second: back in jab range, percent cleared
        f.reset(t0 + k - 18, KIRBY, -4, 1); f.reset(t0 + k - 18, GENO, 4, -1)
        f.percent(t0 + k - 16, KIRBY, 0)
        for j in range(0, 40, 13):
            ge.hold(t0 + k + j, 3, btn='A')
    status(t0, 2300)


LEAD = 70
f = Film(len_s=(LEAD + sum(n for _, n, _ in SEGS) + 40) / 60)
f.setup(players=[('kirby', dict(x=-12, face=1)), ('geno', dict(x=6, face=-1))], seed=5, coll=0)
kb, ge = f.port(KIRBY), f.port(GENO)
f.cam(0, eye=(0, 25, 190), at=(0, 12, 0), fov=30, ease='cut', track='mid')
t = LEAD
for i, (label, n, fn) in enumerate(SEGS):
    f.mark(t, i, label)
    fn(t)
    t += n
f.emit(sys.argv[1])
