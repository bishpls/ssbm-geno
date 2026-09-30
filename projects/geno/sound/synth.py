"""Geno's movement sounds, synthesized from scratch (no samples): footsteps, landings, jumps, cape, ledge, tech, teeter,
star KO. Geno is a carved wooden doll: a hollow body with ball joints, big wooden/leather boots, a felt cap, a cloth cape.
Every WAV is a deterministic function of the seeds below.

    .venv/bin/python projects/geno/sound/synth.py            # writes wav/ here and ~/games/melee/work/sfxbank/synth/

Sound ids continue Geno's bank 55 after the 28 SNES-derived sounds: 550000 + k, k from 28 (the table S). Levels: every
sample is normalised to the same loudest-100 ms loudness (-19 LUFS, peaks <= -1.5 dBFS, click transients soft-limited),
and the loudness heard in the game is set by the sem script's volume byte, chosen so the effective level (sample x
script vol x a full-volume command) lands on a target measured against Melee's own movement sounds (melee_ref.py,
abtest.py): about their median, ~14 dB under the attacks. Retuning a level is a sem-only change (the bank is unchanged).
"""
import os, sys, json
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(__file__))
from dsp import *                      # noqa: F401,F403  (FS, modal, rattle, stick_slip, cloth helpers, finish ...)
from loud import measure, to32k

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.expanduser('~/games/melee/work/sfxbank/synth')
K0 = 28                                  # first new bank index: sound 550028

# ------------------------------------------------------------------------------------------------ the doll's materials
# (freq Hz, loss factor eta, energy dB). A mode's decay is tau = 1/(pi f eta); its gain is set from the energy share, so
# fast-decaying high modes still carry the clack. eta ~0.03-0.12: carved wood damped by leather, felt and loose joints.
def E(modes):
    return [(f, eta, np.sqrt(10 ** (db / 10) * np.pi * f * eta)) for f, eta, db in modes]

BOOT_HEEL = E([(185, 0.22, -13), (640, 0.036, 0), (1260, 0.050, 0), (1830, 0.055, -1), (2560, 0.060, -3),
               (3420, 0.070, -6), (4700, 0.080, -9), (6300, 0.090, -12), (8200, 0.100, -16)])
BOOT_TOE = E([(240, 0.25, -13), (780, 0.050, -1), (1520, 0.055, 0), (2250, 0.060, -2), (3050, 0.070, -5),
              (4300, 0.080, -9), (5900, 0.090, -13)])
BODY = E([(120, 0.28, -5), (310, 0.040, 0), (720, 0.050, -1), (1150, 0.055, -2), (1680, 0.060, -4),
          (2400, 0.070, -6), (3300, 0.080, -9), (4600, 0.090, -13)])
ARM = E([(820, 0.055, 0), (1650, 0.060, -1), (2700, 0.070, -3), (3900, 0.080, -6), (5400, 0.090, -10)])
HAND = E([(930, 0.045, -2), (1740, 0.050, 0), (2600, 0.060, -2), (3700, 0.070, -4), (5100, 0.080, -8),
          (7000, 0.090, -12)])
HEAD = E([(430, 0.090, 0), (980, 0.110, -6), (1900, 0.140, -14)])          # under the felt cap: muffled
CREAK_BIG = E([(640, 0.060, 0), (1320, 0.060, -2), (2250, 0.070, -6), (3400, 0.080, -11)])   # hip/knee
CREAK_SMALL = E([(760, 0.050, 0), (1500, 0.050, -2), (2600, 0.060, -6), (3600, 0.070, -11)])  # ankle

L_SCALE, R_SCALE = 1.0, 0.955            # the two boots are different pieces of wood: R sits ~0.8 semitone lower


def scaled(modes, s, rng=None, gj=0.0):
    return [(f * s, eta, g * (1 + gj * rng.standard_normal()) if rng is not None else g) for f, eta, g in modes]


def boot_step(rng, side, firm):
    """One footfall: heel strike then the toe/sole slap. firm=0 walking (softer contact, longer heel-toe gap), firm=1
    running (the wooden heel lands harder and brighter, the toe right behind). A contact click and a short sole scuff
    carry the top end."""
    s = L_SCALE if side == 'L' else R_SCALE
    j = lambda v, r: v * (1 + r * rng.uniform(-1, 1))
    heel_tau = j(0.00040 - 0.00020 * firm, 0.15)
    toe_tau = j(0.00070 - 0.00035 * firm, 0.15)
    gap = j(0.030 - 0.018 * firm, 0.18)
    toe_f = j(0.46 + 0.16 * firm, 0.12)
    dur = 0.12
    heel = modal(scaled(BOOT_HEEL, s, rng, 0.15), [(0.0, j(1.0, 0.08), heel_tau)], dur, rng, jitter=0.012, rough=0.3)
    toe = modal(scaled(BOOT_TOE, s, rng, 0.15), [(gap, toe_f, toe_tau)], dur, rng, jitter=0.012, rough=0.3)
    y = heel + toe
    y = mix_db(y, click(0.0005, rng, lo=2200 + 800 * firm), -15 + 6 * firm, 0.0)
    y = mix_db(y, scuff(0.009 - 0.003 * firm, rng, 1200 + 500 * firm, 4000 + 2000 * firm), -28 + 6 * firm, gap * 0.8)
    return y


def body_thok(rng, force=1.0, tau=0.0021, scale=1.0, dur=0.26):
    return modal(scaled(BODY, scale, rng, 0.12), [(0.0, force, tau)], dur, rng, jitter=0.01, rough=0.2)


def bounce_hits(t0, force, tau, e, n, d0, rng):
    hits, t, f, d = [], t0, force, d0
    for _ in range(n):
        hits.append((t, f * rng.uniform(0.85, 1.15), tau * rng.uniform(0.85, 1.2)))
        t += d * rng.uniform(0.85, 1.15); d *= e; f *= e
    return hits


def wander(n, rng, rate_hz, depth):
    """A smooth random wobble (low-passed noise), 1 +/- depth, for pressure and speed that never hold still."""
    k = max(4, int(n * rate_hz / FS) + 4)
    pts = rng.standard_normal(k)
    w = np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)
    return 1 + depth * w / (np.abs(pts).max() + 1e-9)


def creak(rng, dur, rate, normal, formants, jitter=0.01, rough=0.3, hiss_db=-22):
    """A creaking joint: stick-slip events (rate[] Hz under normal[]) exciting the joint's wood modes. The pressure and
    the driving speed wander, and the surface is rough, so the slips come irregularly (a creak, not a buzz); a little
    friction hiss rides on top."""
    n = n_(dur)
    normal = normal * wander(n, rng, 60, 0.25)
    speed = rate * (1.0 - 0.62) * normal * wander(n, rng, 45, 0.3)
    imp = stick_slip(dur, speed, normal, rng, rough=rough)
    exc = fftconvolve(imp, pulse(0.00018))[:len(imp)]
    h = modes_ir(scaled(formants, 1.0, rng, 0.1), 0.08, rng, jitter)
    y = fftconvolve(exc, h)[:len(exc)]
    return mix_db(y, bp(noise(dur, rng), 1500, 6000) * np.convolve(np.abs(imp), np.ones(n_(0.004)), 'same'), hiss_db)


def ramp(n, a, b, curve=1.0):
    return a + (b - a) * np.linspace(0, 1, n) ** curve


def whoosh(rng, dur, f0, f1, q, attack, decay, flutter=None, curve=1.0):
    """Cloth moving through air: noise through a resonant band sweeping f0 -> f1, an attack/decay envelope and an optional
    flutter (flapping) AM: (start Hz, end Hz, depth)."""
    n = n_(dur)
    x = tv_bandpass(noise(dur, rng), ramp(n, f0, f1, curve), q)
    e = env_ar(n, attack, decay, curve=1.5)
    if flutter:
        fa, fb, depth = flutter
        ph = 2 * np.pi * np.cumsum(ramp(n, fa, fb)) / FS
        e = e * (1 - depth * 0.5 * (1 + np.sin(ph + rng.uniform(0, 2 * np.pi))))
    return x * e


def snap(rng, amp=1.0, tau=0.0012, lo=1100):
    """Cloth pulled taut: a sharp broadband crack with a little body."""
    n = n_(tau * 6)
    x = noise(tau * 6, rng) * env_ar(n, tau * 0.15, tau)
    return amp * bp(x, lo, 9000, order=2)


def air_push(rng, dur, attack, decay, fc=260):
    """The low 'whump' of a cape displacing air."""
    n = n_(dur)
    return lp(lp(noise(dur, rng), fc), fc) * env_ar(n, attack, decay, curve=2.0)


def joint_click(rng, amp=1.0, f0=None):
    f0 = f0 or rng.uniform(1900, 2500)
    ms = [(f0 * 0.42, 0.06, 0.5), (f0, 0.05, 1.0), (f0 * 1.63, 0.06, 0.55), (f0 * 2.45, 0.07, 0.3)]
    return amp * modal(ms, [(0.0, 1.0, 0.00022)], 0.04, rng, jitter=0.01)


# ------------------------------------------------------------------------------------------------------------- sounds
def step(side, firm):
    def f(rng): return boot_step(rng, side, firm)
    return f


def land(rng):
    """A normal landing: both boots and the hollow body land together (a wooden thok), then the joints settle with a
    small rattle."""
    y = body_thok(rng, 1.6, 0.0009, dur=0.26)
    for at, sc in ((0.0, L_SCALE), (0.009 + rng.uniform(-0.002, 0.003), R_SCALE)):
        y += modal(scaled(BOOT_HEEL, sc, rng, 0.12), [(at, 0.4, 0.00035)], 0.26, rng, jitter=0.01, rough=0.3)
    y = mix_db(y, click(0.0006, rng, lo=2200), -14, 0.0)
    return mix_db(y, rattle(0.0, rng, n_joints=4, amp0=1.0, spread=0.025, bounces=(5, 8), dur=0.2), -11, 0.016)


def land_heavy(rng):
    """Knocked down: the body slams, then arms, boots and head hit and bounce, joints rattling."""
    dur = 0.46
    y = body_thok(rng, 1.25, 0.0014, 0.95, dur)
    y += modal(HEAD, [(0.028, 0.55, 0.004)], dur, rng, jitter=0.02)
    for t0 in (0.014, 0.041):
        y += modal(scaled(ARM, rng.uniform(0.92, 1.08), rng, 0.15),
                   bounce_hits(t0, 0.45, 0.0003, 0.45, 3, rng.uniform(0.05, 0.07), rng), dur, rng, jitter=0.012, rough=0.3)
    for sc, t0 in ((L_SCALE, 0.031), (R_SCALE, 0.058)):
        y += modal(scaled(BOOT_HEEL, sc, rng, 0.12),
                   bounce_hits(t0, 0.55, 0.0004, 0.5, 3, rng.uniform(0.06, 0.08), rng), dur, rng, jitter=0.012, rough=0.3)
    y = mix_db(y, rattle(0.0, rng, n_joints=4, amp0=1.0, bounces=(5, 9), spread=0.03, dur=0.3), -10, 0.03)
    return mix_db(y, click(0.0007, rng, lo=2000), -13, 0.0)


def jump(rng):
    """Take-off: the knees and a hip snap straight (quick ball-joint clicks), then a short, light creak as he rises."""
    dur = 0.13
    y = np.zeros(n_(dur))
    for at, amp in ((0.0, 1.0), (0.006 + rng.uniform(0, 0.002), 0.75), (0.013 + rng.uniform(0, 0.003), 0.4)):
        y = place(y, joint_click(rng, amp), at)
    n = n_(0.065)
    c = creak(rng, 0.065, ramp(n, 260, 480, 0.7), ramp(n, 1.0, 0.75), CREAK_BIG)
    c *= env_ar(n, 0.010, 0.022)
    return mix_db(y, c, -7, 0.014)


def jump_air(rng):
    """The double jump: the cape snaps open into a whump of air (flapping), the legs tuck with a joint click."""
    dur = 0.30
    y = np.zeros(n_(dur))
    y = place(y, joint_click(rng, 0.55), 0.0)
    y = place(y, air_push(rng, 0.24, 0.022, 0.055, 230), 0.004, 1.6)
    y = place(y, whoosh(rng, 0.26, 280, 950, 1.3, 0.035, 0.06, flutter=(17, 28, 0.55), curve=0.6), 0.006, 0.9)
    y = place(y, snap(rng, 0.5, 0.0014, 900), 0.092)
    return y


def cape(variant):
    def f(rng):
        dur = 0.19
        y = np.zeros(n_(dur))
        if variant == 1:        # a turn: swish up, one snap as it goes taut, a quick flutter
            y = place(y, whoosh(rng, 0.08, 700, 2600, 1.5, 0.03, 0.025, curve=0.8), 0.0, 1.0)
            y = place(y, snap(rng, 0.9, 0.0011, 1200), 0.052)
            y = place(y, whoosh(rng, 0.12, 1500, 800, 1.2, 0.004, 0.035, flutter=(32, 22, 0.8)), 0.056, 0.55)
        else:                   # a dash: lower and longer, two snaps
            y = place(y, whoosh(rng, 0.09, 500, 1900, 1.4, 0.035, 0.03, curve=0.7), 0.0, 1.0)
            y = place(y, snap(rng, 0.7, 0.0013, 1000), 0.043)
            y = place(y, snap(rng, 0.45, 0.0010, 1300), 0.083)
            y = place(y, whoosh(rng, 0.11, 1200, 650, 1.2, 0.004, 0.035, flutter=(26, 18, 0.8)), 0.086, 0.5)
        return y
    return f


def ledge(rng):
    """Both wooden hands clack onto the edge, fingers rattling; a small jolt through the body."""
    dur = 0.14
    t2 = 0.015 + rng.uniform(0, 0.004)
    y = modal(scaled(HAND, 1.0, rng, 0.12), [(0.0, 1.0, 0.00018)], dur, rng, jitter=0.012, rough=0.3)
    y += modal(scaled(HAND, 0.94, rng, 0.12), [(t2, 0.8, 0.0002)], dur, rng, jitter=0.012, rough=0.3)
    y += 0.3 * body_thok(rng, 0.6, 0.0015, 1.1, dur)
    y = mix_db(y, rattle(0.0, rng, n_joints=3, amp0=1.0, d0=(0.008, 0.014), dur=0.1, modes_base=2600), -13, 0.008)
    y = mix_db(y, click(0.0005, rng, lo=2500), -11, 0.0)
    return mix_db(y, click(0.0005, rng, lo=2500), -14, t2)


def tech(rng):
    """A tech, roll or get-up: shoulder, hip, then both boots knock as he tumbles, joints rattling, a brush of cape."""
    dur = 0.25
    tb, t1 = rng.uniform(0.028, 0.042), rng.uniform(0.060, 0.075)
    t2 = t1 + rng.uniform(0.018, 0.032)
    y = modal(scaled(ARM, rng.uniform(0.85, 0.95), rng, 0.15), [(0.0, 0.7, 0.0004)], dur, rng, jitter=0.012, rough=0.3)
    y = place(y, 0.8 * body_thok(rng, 0.8, 0.0013, rng.uniform(1.0, 1.1), dur - tb), tb)[:n_(dur)]
    for sc, t0, fz in ((L_SCALE, t1, 0.5), (R_SCALE, t2, 0.4)):
        y += modal(scaled(BOOT_HEEL, sc, rng, 0.12), [(t0, fz, 0.00035)], dur, rng, jitter=0.012, rough=0.3)
    y = mix_db(y, rattle(0.0, rng, n_joints=3, amp0=1.0, spread=0.05, dur=0.2), -12, 0.01)
    y = mix_db(y, whoosh(rng, dur, 500, 1800, 1.2, 0.03, 0.05), -14, 0.0)
    return mix_db(y, click(0.0006, rng, lo=2200), -15, 0.0)


def teeter(rng):
    """On the edge: the ankles rock, small nervous creaks back and forth."""
    dur = 0.33
    y = np.zeros(n_(dur))
    for t0, d, r0, r1, a in ((0.0, 0.085, 200, 340, 1.0), (0.11, 0.075, 320, 190, 0.8), (0.205, 0.07, 230, 310, 0.55)):
        n = n_(d)
        wob = 1 + 0.08 * np.sin(2 * np.pi * rng.uniform(9, 14) * np.arange(n) / FS)
        c = creak(rng, d, ramp(n, r0, r1) * wob, ramp(n, 0.9, 1.1) * wob, CREAK_SMALL, rough=0.35)
        c *= env_ar(n, 0.015, d * 0.45) * a
        y = place(y, c, t0)
    return y[:n_(dur)]


def star_ko(rng):
    """Star KO: far away, the doll tumbles, limbs clattering and joints rattling, falling in pitch as it flies off."""
    dur = 0.55
    y = np.zeros(n_(dur))
    t, f = 0.0, 1.0
    parts = [ARM, BOOT_HEEL, BODY, ARM, BOOT_TOE, HAND, BOOT_HEEL, ARM]
    taus = (0.0003, 0.0007)
    for m in parts:
        y += modal(scaled(m, rng.uniform(0.9, 1.1), rng, 0.15), [(t, f * rng.uniform(0.7, 1.0), rng.uniform(*taus))],
                   dur, rng, jitter=0.015, rough=0.3)
        t += rng.uniform(0.024, 0.048); f *= 0.86
    y += rattle(0.01, rng, n_joints=4, amp0=0.25, spread=0.12, bounces=(5, 9), dur=dur)
    y += rattle(0.16, rng, n_joints=3, amp0=0.15, spread=0.08, dur=dur)
    # distance: air absorption and a few room reflections
    y = lp(y, 4200)
    out = y.copy()
    for d, g in ((0.019, 0.45), (0.031, 0.35), (0.047, 0.28), (0.071, 0.2), (0.103, 0.14), (0.149, 0.09)):
        out = place(out, lp(y, 3000) * g, d)[:len(y)]
    # fly away: a slow Doppler fall (~ -1.3 semitones) and a fade
    n = len(out)
    rate = ramp(n, 1.0, 0.925)
    pos = np.cumsum(rate); pos = pos[pos < n - 1]
    out = np.interp(pos, np.arange(n), out)
    return out * np.exp(-np.arange(len(out)) / FS / 0.22)


def rattle_hit(rng):
    """Shaken by a hit: the joints rattle in their sockets (a light-hit layer)."""
    dur = 0.18
    y = rattle(0.0, rng, n_joints=5, amp0=1.0, spread=0.02, bounces=(4, 8), dur=dur)
    return mix_db(y, body_thok(rng, 0.5, 0.0008, 1.2, dur), -4, 0.0)


# ---------------------------------------------------------------------------------------------------------- the table
# name, generator, bank rate, seed, target effective loudness (loud.short: the loudest 100 ms, K-weighted, at a
# full-volume command; Melee's own movement sounds measured the same way in melee_ref.py), family (variants of one
# family get a small random level spread), sem prio, sem aux (reverb send; Melee's steps use 5, its landing 2, its jump
# 4, Samus's star KO 0x3C), tail (dB under the peak where the decay is cut)
S = []
def add(name, fn, rate, seed, target, fam=None, prio=14, aux=5, use='', tail=-42):
    S.append(dict(name=name, fn=fn, rate=rate, seed=seed, target=target, fam=fam or name, prio=prio, aux=aux, use=use, tail=tail))

for firm, kind, tgt in ((0, 'WALK', -29.0), (1, 'RUN', -26.0)):
    for side in 'LR':
        for v in (1, 2, 3):
            add(f'GENO_STEP_{kind}_{side}{v}', step(side, firm), 22050, 1000 + 100 * firm + 10 * (side == 'R') + v, tgt,
                fam=f'STEP_{kind}', tail=-52, use=f'{"walk" if not firm else "run/dash"} footfall, {"left" if side == "L" else "right"} boot, variant {v}')
add('GENO_LAND', land, 22050, 2001, -26.0, fam='LAND', prio=15, aux=2, tail=-45, use='landing: wooden thok + joint rattle (variant 1)')
add('GENO_LAND2', land, 22050, 2012, -26.0, fam='LAND', prio=15, aux=2, tail=-45, use='landing: wooden thok + joint rattle (variant 2)')
add('GENO_LAND_HEAVY', land_heavy, 16000, 2002, -21.0, prio=15, aux=2, use='knocked down / heavy landing: limbs clatter')
add('GENO_JUMP', jump, 16000, 2003, -25.0, prio=15, aux=4, use='jump: joint click + light creak')
add('GENO_JUMP_AIR', jump_air, 16000, 2004, -23.0, prio=15, aux=4, use='double jump: cape whump + click')
add('GENO_CAPE1', cape(1), 16000, 2005, -29.0, fam='CAPE', aux=4, use='cape flutter (turn)')
add('GENO_CAPE2', cape(2), 16000, 2006, -29.0, fam='CAPE', aux=4, use='cape flutter (dash)')
add('GENO_LEDGE', ledge, 22050, 2007, -22.0, prio=15, aux=2, use='ledge grab: hands clack on the edge')
add('GENO_TECH', tech, 16000, 2008, -23.0, fam='TECH', prio=15, aux=2, use='tech / roll / get-up: short clatter (variant 1)')
add('GENO_TECH2', tech, 16000, 2013, -23.0, fam='TECH', prio=15, aux=2, use='tech / roll / get-up: short clatter (variant 2)')
add('GENO_TEETER', teeter, 16000, 2009, -28.0, aux=2, use='teeter: small nervous creak')
add('GENO_STARKO', star_ko, 16000, 2010, -21.0, prio=16, aux=0x3C, use='star KO: distant tumbling rattle')
add('GENO_RATTLE', rattle_hit, 16000, 2011, -24.0, prio=15, aux=2, use='joint rattle (hit reaction layer)')

SAMPLE_SHORT = -19.0                     # every sample's loudest 100 ms (the script's vol byte sets the level heard)
CEIL_DB = -1.5                           # sample peak ceiling; transients above it are soft-limited


def softlimit(x, ceil_db=CEIL_DB, knee=0.7):
    c = 10 ** (ceil_db / 20); k = knee * c
    a = np.abs(x)
    y = np.where(a <= k, a, k + (c - k) * np.tanh((a - k) / (c - k)))
    return np.sign(x) * y


def short_of(y, rate):
    return measure(to32k(y, rate))['short']


def render():
    os.makedirs(os.path.join(WORK, 'wav'), exist_ok=True); os.makedirs(os.path.join(HERE, 'wav'), exist_ok=True)
    meta = []
    for k, s in enumerate(S):
        rng = np.random.default_rng(s['seed'])
        x = s['fn'](rng)
        off = rng.uniform(-0.8, 0.8) if s['fam'] != s['name'] else 0.0      # variants: a little natural level spread
        y0 = finish(x, s['rate'], tail_db=s['tail'])
        g = 10 ** ((SAMPLE_SHORT + off - short_of(y0, s['rate'])) / 20)
        y = finish(softlimit(g * x), s['rate'], tail_db=s['tail'])
        y *= min(1.0, 10 ** ((CEIL_DB + 0.5) / 20) / np.abs(y).max())         # resampling overshoot
        q = np.clip(np.round(y * 32767), -32768, 32767).astype(np.int16)
        m = measure(to32k(q / 32768.0, s['rate']))
        vol = int(round(255 * 10 ** ((s['target'] - m['short']) / 20)))
        assert 1 <= vol <= 255, (s['name'], vol)
        sv = 20 * np.log10(vol / 255)
        fn = f'{K0 + k:02d}_{s["name"]}.wav'
        for d in (os.path.join(WORK, 'wav'), os.path.join(HERE, 'wav')):
            sf.write(os.path.join(d, fn), q, s['rate'], subtype='PCM_16')
        meta.append(dict(k=K0 + k, sound_id=550000 + K0 + k, name=s['name'], file=fn, rate=s['rate'], samples=len(q),
                         dur=round(len(q) / s['rate'], 3), seed=s['seed'], use=s['use'], vol=vol, prio=s['prio'], aux=s['aux'],
                         target_eff_short=s['target'], **m, script_db=round(sv, 2),
                         eff_peak=round(m['peak'] + sv, 2), eff_lufs=round(m['lufs'] + sv, 2), eff_short=round(m['short'] + sv, 2)))
    json.dump(meta, open(os.path.join(WORK, 'sounds4.json'), 'w'), indent=1)
    json.dump(meta, open(os.path.join(HERE, 'sounds4.json'), 'w'), indent=1)
    adpcm = sum(-(-m['samples'] // 14) * 8 for m in meta)
    print(f'{"k":>3} {"name":22s} {"rate":>5} {"dur":>5} | {"peak":>5} {"LUFS":>6} {"short":>6} {"cent":>5} {"hf":>6} {"harsh":>6} | '
          f'{"vol":>4} {"effLU":>6} {"effSh":>6} {"effPk":>6} | octaves 125..8k')
    for m in meta:
        print(f'{m["k"]:3d} {m["name"]:22s} {m["rate"]:5d} {m["dur"]:5.3f} | {m["peak"]:5.1f} {m["lufs"]:6.1f} {m["short"]:6.1f} '
              f'{m["centroid"]:5.0f} {m["hf"]:6.1f} {m["harsh"]:6.1f} | {m["vol"]:4d} {m["eff_lufs"]:6.1f} {m["eff_short"]:6.1f} {m["eff_peak"]:6.1f} | ' + ' '.join(f'{b:5.1f}' for b in m['bands']))
    print(f'total {sum(m["dur"] for m in meta):.2f} s; ADPCM ~{adpcm} B (round-3 data_len 289536 -> ~{289536 + adpcm} of 327680)')
    return meta


if __name__ == '__main__':
    render()
