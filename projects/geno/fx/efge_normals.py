"""The gun normals' effects in Geno's effect file (EfGeData.dat): the muzzle bursts that show where his disjointed gun
blasts hit (geno-fxnormals). efge.py builds the file and takes this module as an extension: TEXTURES go after its own,
and generators(tex, first_id) after the specials', so every id and texture index is resolved by name at build time (the
move scripts spawn with efge.gid(NAME)), never hard-coded: the specials adding a generator shifts ours.

The bar (Michael, 2026-09-29): each burst shows the reach of its hitbox. The cast's drawn disjoints reach 0.9-1.0 of
their hitboxes' reach past the body and draw over ~30-60% of the disjoint area on the active frames (Ness's forward and
back air 0.94, Marth's forward smash 0.90, Falco's laser 1.01, Mewtwo's forward smash 1.38; fx/gunfxmeasure.py). So a
move script spawns a burst on each hitbox sphere (the same TopN offset, the same frame), sized by the sphere's radius
class, plus a flash at the muzzle. Every burst is round in the stage plane (a disc emitter with its axis toward the
camera, drifting up, never along the facing), so it reads the same facing either way with no facing-aware spawn.

One language per weapon form (ART.md "Weapon forms"), in SMRPG's vocabulary adapted to Melee's particles:
  GUN     Hand Gun: a crisp yellow-white puff with a small star, SMRPG's finger-shot puff (SPR0527: a mist puff that
          forms into a small gold star, then a smaller orange one); the tip burst forms the star
  TAP     the jab's finger taps: the same puff, smaller and quicker, so a jab string doesn't pile up
  STAR    Star Gun: a spray of small gold stars with white twinkles, flung up out of the hitbox and spinning out
  CANNON  Hand Cannon: a hot orange-white fire puff that turns to dark smoke and lingers; the muzzle gets a heavy flash
          and a shock ring
  EXHAUST the rocket fists' exhaust: a soft grey puff that stays put; moves.exhaust_trail lays them along each
          frame's flight, 2.2 units apart at most, so the trail is unbroken (Double Punch: 22 puffs)
Names: N_<FORM>_<radius class> (the burst on a hitbox of about that radius; the script picks the nearest class),
N_<FORM>_TIP_<class> (the tip's burst, GUN only: it forms the star), N_<FORM>_FLASH (the muzzle).
"""
import math

import numpy as np
from PIL import Image

# ------------------------------------------------------------------------------------------------------- textures
def tex_puff(n=64):
    """A soft puff of mist (SMRPG's SPR0527 cloud at Melee's resolution): round, its edge rippled by a few low bumps,
    alpha falling off softly to the rim; lit from the top left with a vapour's mottling, the underside darker (the env
    colour takes it)."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    dx, dy = (xx - c) / c, (yy - c) / c
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    edge = 0.8 + 0.035 * np.sin(3 * th + 0.6) + 0.04 * np.sin(5 * th + 2.1) + 0.025 * np.sin(7 * th + 4.0)
    alpha = np.clip((edge - r) / 0.22, 0, 1) ** 1.2
    rng = np.random.default_rng(527)
    noise = np.zeros((n, n), np.float32)
    for k, amp in ((4, 0.5), (8, 0.3), (16, 0.2)):
        g = rng.random((k + 1, k + 1)).astype(np.float32)
        noise += amp * np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC),
                                  np.float32) / 255
    hl = np.clip(1.0 - np.hypot(dx + 0.3, dy + 0.34) / 1.15, 0, 1)
    inten = np.clip(0.2 + 0.6 * hl + 0.25 * (noise - 0.5) + 0.2 * (1 - r), 0, 1)
    return _ia8(inten, alpha)


def tex_ring(n=64):
    """A shock ring: a bright thin band with a soft inner falloff (the cannon's blast front)."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot(xx - c, yy - c) / c
    band = np.clip(1.0 - np.abs(r - 0.8) / 0.13, 0, 1)
    inner = np.clip((r - 0.35) / 0.45, 0, 1) * (r < 0.8) * 0.35
    alpha = np.clip(band + inner, 0, 1)
    return _ia8(np.clip(0.4 + 0.6 * band, 0, 1), alpha)


TEXTURES = [('n_puff', 'IA8', [tex_puff]), ('n_ring', 'IA8', [tex_ring])]


def _ia8(inten, alpha):
    """intensity and alpha as a grey RGBA image (efge._ia's; here so the textures stand before efge is imported)"""
    i8 = (np.clip(inten, 0, 1) * 255).astype(np.uint8)
    a8 = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([i8, i8, i8, a8]), 'RGBA')


# efge imports this module while it lists its textures (efge.TEX), so TEXTURES above must exist before efge is imported
import efge  # noqa: E402
from efge import Cmd, DISC, FRICTION, BLEND_ONE  # noqa: E402

GRAVITY = efge.GRAVITY
CLASSES = (3.0, 3.6, 4.4, 5.2)          # the hitbox radii the bursts are sized for (his gun blasts run 3.0-5.4)


def cls_name(r):
    """The radius class for a hitbox of radius r: its label in the generator names (3.6 -> '36')."""
    c = min(CLASSES, key=lambda k: abs(k - r))
    return f'{int(round(c * 10))}'


# ------------------------------------------------------------------------------------------------------- commands
class NCmd(Cmd):
    def add_vel(self, x=None, y=None, z=None):   # 0x98: add to velocity components
        m = 0; d = b''
        for k, v in enumerate((x, y, z)):
            if v is not None: m |= 1 << k; d += self._f(v)
        self.b += bytes([0x98 | m]) + d; return self

    def randpos(self, x, y, z):                   # 0xA8: move the particle by up to +-(x, y, z) at random
        self.b += bytes([0xA8]) + self._f(x) + self._f(y) + self._f(z); return self


# ------------------------------------------------------------------------------------------------------- palettes
# (prim: the lit face, env: the rim), env alpha always 0 (the texture's alpha cuts the shape)
GUN_POP = ((255, 255, 236), (255, 206, 80))      # the yellow-white pop
GUN_MIST = ((226, 222, 208), (150, 140, 120))    # SPR0527's grey mist as it fades
TAP_MIST = ((235, 235, 240), (140, 140, 155))    # the Finger Shot puff's mist (efge FINGER_PUFF): the taps match it
GUN_STAR = ((255, 246, 150), (236, 150, 24))     # the small gold star the puff forms
GUN_STAR_OUT = ((255, 196, 90), (200, 88, 16))   # ... ending as a smaller orange star (SPR0527 mold 4)
STAR_GOLD = ((255, 250, 190), (240, 176, 16))
STAR_WHITE = ((255, 255, 255), (170, 200, 255))
STAR_GLOW = ((255, 240, 170), (255, 186, 40))
FIRE = ((255, 236, 160), (245, 96, 12))
SMOKE = ((150, 142, 132), (58, 52, 48))
SMOKE_A = 210


# ------------------------------------------------------------------------------------------------------- particles
def puff(r, pop, mist, hold, fade, grow=1.2, rise=0.05, a0=255, vary=0.35):
    """A puff that's on the hitbox's first frame at about `r` (half-width, +- vary*r at random), holds its colour for
    `hold` frames, then turns to `mist` and fades out over `fade`, growing to grow*r and rising a little."""
    c = NCmd().tex(0).primenv().prim(*pop[0], a0).env(*pop[1], 0)
    c.size_rand(r * (1 - vary), 2 * vary * r).rot_rand(-3.1416, 6.2832)
    c.add_vel(y=rise)
    c.wait(hold)
    c.prim(*mist[0], frames=fade // 2).env(*mist[1], frames=fade // 2)
    c.size(r * grow, fade).rotate(0.4, fade)
    c.wait(fade // 2).prim(a=0, frames=fade - fade // 2).wait(fade - fade // 2)
    return c.end()


def glow(r, pop, life):
    """The hot core of a burst: a soft puff drawn additively at `r`, bright on its first frame, fading out over `life`."""
    c = NCmd().tex(0).primenv().prim(*pop[0], 255).env(*pop[1], 0)
    c.size(r).rot_rand(-3.1416, 6.2832).wait(1)
    c.size(r * 1.1, life - 1).prim(a=0, frames=life - 1).wait(life - 1)
    return c.end()


def star(size, wait=0, life=16, spin=1.2, cols=(GUN_STAR, GUN_STAR_OUT)):
    """SPR0527's forming star: after `wait` it pops in, spins a little, holds, shrinks to a smaller orange star and
    blinks out."""
    c = NCmd().tex(0).primenv().prim(*cols[0][0], 0).env(*cols[0][1], 0).size(size * 0.3)
    if wait:
        c.wait(wait)
    c.prim(a=255).size(size, 2).rot_rand(-0.3, 0.6).rotate(spin, life)
    c.wait(life // 2)
    c.prim(*cols[1][0], frames=4).env(*cols[1][1], frames=4).size(size * 0.6, 4).wait(life // 2 - 3)
    c.prim(a=0, frames=3).wait(3)
    return c.end()


def flash(size, prim, env, life=5):
    """A muzzle flash: SMRPG's three-frame flash (a four-point sparkle that turns 45 degrees), additive."""
    c = NCmd().tex(0).primenv().prim(*prim, 255).env(*env, 0)
    c.size(size).wait(2).rotate(math.pi / 4).size(size * 0.8, 2).wait(2)
    c.size(size * 0.3, life - 4).prim(a=0, frames=life - 4).wait(life - 4)
    return c.end()


def ring(size, prim, env, life=6):
    """The cannon's shock ring: from the muzzle out to `size`, fading, additive."""
    c = NCmd().tex(0).primenv().prim(*prim, 230).env(*env, 0).size(size * 0.3)
    c.size(size, life).prim(a=0, frames=life).wait(life)
    return c.end()


def spray_star(size, cols, up, life):
    """A Star Gun star: flung up out of the hitbox (the emitter's in-plane scatter plus `up`), easing out, spinning,
    shrinking and fading."""
    c = NCmd().tex(0).primenv().prim(*cols[0], 255).env(*cols[1], 0)
    c.size(size).rot_rand(-3.1416, 6.2832).rotate(3.0, life).add_vel(y=up)
    c.wait(life - 6).size(size * 0.4, 6).prim(a=0, frames=6).wait(6)
    return c.end()


def root(children):
    return efge.root(children)


NO_Z = 0x10000000               # HSD_ParticleKind NoZComp: drawn without the depth test (over the body)


def rocket_flare():
    """efge.rocket_launch()'s four-point star (white, a blue rim, turning 45 degrees), in 6 frames rather than 10"""
    c = NCmd().tex(0).primenv().prim(255, 255, 255, 255).env(200, 220, 255, 0).size(1.5)
    c.size(4.4, 1).wait(1).rotate(math.pi / 4).size(3.4, 2).wait(2).size(1.0, 3).prim(a=0, frames=3).wait(3)
    return c.end()


def pop_star(size, cols, life, spin=1.2):
    """a star that pops to `size` on its first frame, spins, shrinks and fades over `life`"""
    c = NCmd().tex(0).primenv().prim(*cols[0], 255).env(*cols[1], 0).size(size).rot_rand(-0.4, 0.8).rotate(spin, life)
    c.wait(max(1, life // 3)).size(size * 0.35, life - life // 3).prim(a=0, frames=life - life // 3).wait(life - life // 3)
    return c.end()


# ------------------------------------------------------------------------------------------------------- generators
def generators(tex, first):
    """(name, header, command list) for ids first, first + 1, ... (after efge's own); tex: every texture group's index
    by name."""
    gens = []

    def add(name, hdr, cmd):
        gens.append((name, hdr, cmd))
        return first + len(gens) - 1

    def disc(texg, n, radius, speed, life, kind=0, fric=1.0, size=0.2):
        """a disc in the stage plane (axis toward the camera): n particles at once, within `radius` (a negative radius:
        on that circle, evenly spaced from a random start), drifting out at `speed`"""
        return dict(type=DISC, texg=tex[texg], genlife=1, life=life, kind=kind | (FRICTION if fric != 1.0 else 0),
                    fric=fric, v=[0, 0, max(speed, 1e-3)], radius=radius, angle=-math.pi / 2 if radius < 0 else math.pi / 2,
                    random=-n, size=size, params=[0.0, 2 * math.pi, 0.0])

    def rootgen(name, kids):
        return add(name, dict(type=DISC, genlife=1, life=1, random=-1, size=1), root(kids))

    for r in CLASSES:
        k = f'{int(round(r * 10))}'
        # ---- Hand Gun: on the hitbox's first frame a hot glow over the sphere (additive, gone in 5) and a ring of
        # mist puffs round it that turn grey, drift up and fade over ~12 frames
        core = add(f'n_gun_core_{k}', disc('n_puff', 1, 0.0, 0.0, 6, kind=BLEND_ONE), glow(r * 0.85, GUN_POP, 5))
        side = add(f'n_gun_side_{k}', disc('n_puff', 4, r * 0.55, r * 0.03, 14, fric=0.85),
                   puff(r * 0.5, GUN_POP, GUN_MIST, 2, 10, grow=1.3, a0=235))
        rootgen(f'N_GUN_{k}', [core, side])
        st = add(f'n_gun_star_{k}', disc('star', 1, 0.0, 0.0, 22), star(r * 0.55, wait=3, life=18))
        rootgen(f'N_GUN_TIP_{k}', [core, side, st])
        # ---- the jab's taps: the same, smaller and quicker, and a small star
        tcore = add(f'n_tap_core_{k}', disc('n_puff', 1, 0.0, 0.0, 5, kind=BLEND_ONE), glow(r * 0.85, GUN_POP, 4))
        tside = add(f'n_tap_side_{k}', disc('n_puff', 3, -r * 0.42, r * 0.02, 10, fric=0.8),
                    puff(r * 0.5, GUN_POP, TAP_MIST, 2, 7, grow=1.25, a0=235))
        tstar = add(f'n_tap_star_{k}', disc('star', 1, 0.0, 0.0, 12), star(r * 0.4, wait=2, life=9, spin=0.8))
        rootgen(f'N_TAP_{k}', [tcore, tside, tstar])
        # ---- Star Gun: a spray of small stars, gold with white twinkles, flung up out of the sphere and spinning out,
        # over a brief gold glow that fills it on the first frame
        sgl = add(f'n_star_glow_{k}', disc('n_puff', 1, 0.0, 0.0, 5, kind=BLEND_ONE), glow(r * 0.8, STAR_GLOW, 4))
        sg = add(f'n_star_gold_{k}', disc('star', 4, r * 0.8, 0.35, 16, fric=0.82),
                 spray_star(r * 0.27, STAR_GOLD, 0.6, 16))
        sw = add(f'n_star_white_{k}', disc('twinkle', 2, r * 0.9, 0.3, 12, fric=0.82),
                 spray_star(r * 0.32, STAR_WHITE, 0.5, 12))
        sc = add(f'n_star_core_{k}', disc('star', 1, 0.0, 0.0, 12), spray_star(r * 0.5, STAR_GOLD, 0.25, 12))
        rootgen(f'N_STAR_{k}', [sgl, sg, sw, sc])
        # ---- Hand Cannon: a hot orange-white glow over the sphere (additive, gone in 6), and fire puffs that blacken
        # to smoke, rise and linger ~24 frames
        fc = add(f'n_can_core_{k}', disc('n_puff', 1, 0.0, 0.0, 7, kind=BLEND_ONE), glow(r * 0.9, FIRE, 6))
        fs = add(f'n_can_side_{k}', disc('n_puff', 5, r * 0.55, r * 0.035, 28, fric=0.86),
                 puff(r * 0.55, FIRE, SMOKE, 3, 22, grow=1.45, rise=0.08, a0=240))
        rootgen(f'N_CANNON_{k}', [fc, fs])
    # ---- the muzzles
    gf = add('n_gun_flash', dict(type=DISC, texg=tex['flash'], genlife=1, life=6, kind=BLEND_ONE, random=-1,
                                 size=0.2), flash(2.4, (255, 255, 230), (255, 200, 60)))
    rootgen('N_GUN_FLASH', [gf])
    sf = add('n_star_flash', dict(type=DISC, texg=tex['flash'], genlife=1, life=6, kind=BLEND_ONE, random=-1,
                                  size=0.2), flash(2.2, (255, 255, 240), (150, 200, 255)))
    rootgen('N_STAR_FLASH', [sf])
    cf = add('n_can_flash', dict(type=DISC, texg=tex['flash'], genlife=1, life=7, kind=BLEND_ONE, random=-1,
                                 size=0.2), flash(4.2, (255, 250, 220), (255, 130, 30), life=7))
    cr = add('n_can_ring', dict(type=DISC, texg=tex['n_ring'], genlife=1, life=7, kind=BLEND_ONE, random=-1,
                                size=0.2), ring(4.5, (255, 226, 170), (255, 120, 30)))
    cs = add('n_can_smoke', disc('n_puff', 3, 1.2, 0.08, 34, fric=0.9),
             puff(1.4, SMOKE, SMOKE, 4, 28, grow=2.0, rise=0.08, a0=SMOKE_A))
    rootgen('N_CANNON_FLASH', [cf, cr, cs])
    # the rocket fists' exhaust: one soft grey-white puff (~1.9 across, growing to ~3) that stays where it's spawned;
    # moves.exhaust_trail lays them EXHAUST_STEP (2.2) apart along a frame's flight, so they overlap into a trail
    ex = add('n_exhaust', disc('n_puff', 1, 0.0, 0.0, 16), puff(1.2, ((240, 236, 226), (150, 140, 128)), SMOKE, 1, 14,
                                                                 grow=1.6, rise=0.05, a0=200, vary=0.15))
    rootgen('N_EXHAUST', [ex])
    exq = add('n_exhaust_quick', disc('n_puff', 1, 0.0, 0.0, 7), puff(1.2, ((240, 236, 226), (150, 140, 128)), SMOKE, 1, 5,
                                                                     grow=1.4, rise=0.05, a0=200, vary=0.15))
    rootgen('N_EXHAUST_QUICK', [exq])      # (the dash grab's: gone in 6 frames, before his slide carries him through it)
    # ---- round 6 (Michael's playtest)
    # the grabs' rocket fists: the forward throw's launch star (efge ROCKET_LAUNCH's look), shorter and drawn over the
    # body (no depth test), so the far fist's reads and the dash grab's doesn't trail behind him as he slides on
    fl = add('n_rocket_flare', dict(type=DISC, texg=tex['flash'], genlife=1, life=6, kind=BLEND_ONE | NO_Z, random=-1,
                                    size=0.8), rocket_flare())
    rootgen('N_ROCKET_FLARE', [fl])
    # the up tilt's glints in his own stars: a plump gold star popping on each arc sphere over a warm glow, a star burst
    # at the top of the arc, and twinkles shed from the twirling hands (in place of the engine's 1010-1012)
    ug = add('n_utilt_glow', disc('n_puff', 1, 0.0, 0.0, 4, kind=BLEND_ONE), glow(3.6, STAR_GLOW, 3))
    us = add('n_utilt_star', disc('star', 1, 0.0, 0.0, 8), pop_star(3.0, STAR_GOLD, 7))
    rootgen('N_UTILT_GLINT', [ug, us])
    ur = add('n_utilt_ring', dict(type=DISC, texg=tex['star'], genlife=1, life=14, kind=FRICTION, fric=0.84,
                                  v=[0, 0, 0.9], radius=-1.0, angle=-math.pi / 2, random=-6, size=0.2,
                                  params=[0.0, 2 * math.pi, 0.0]), spray_star(1.3, STAR_GOLD, 0.05, 14))
    uc = add('n_utilt_big', disc('star', 1, 0.0, 0.0, 12), pop_star(4.4, STAR_GOLD, 11))
    rootgen('N_UTILT_TOP', [ug, uc, ur])
    ut = add('n_utilt_twinkle', disc('twinkle', 2, 0.6, 0.12, 10, fric=0.88), spray_star(0.9, STAR_WHITE, 0.05, 10))
    rootgen('N_UTILT_TRAIL', [ut])
    # the neutral air's spinning star core: a pair of small gold stars placed round the core frame by frame (the script
    # turns them 45 degrees a frame, so they wheel round him with the spin), a warm glow at the core on the clean hit,
    # and white twinkles for the late hit
    nc = add('n_nair_core', disc('n_puff', 1, 0.0, 0.0, 6, kind=BLEND_ONE), glow(4.4, STAR_GLOW, 5))
    rootgen('N_NAIR_CORE', [nc])
    ns = add('n_nair_star', disc('star', 1, 0.0, 0.0, 7), pop_star(1.7, STAR_GOLD, 6, spin=2.0))
    rootgen('N_NAIR_STAR', [ns])
    nt = add('n_nair_twinkle', disc('twinkle', 1, 0.0, 0.0, 6), pop_star(1.4, STAR_WHITE, 5, spin=1.0))
    rootgen('N_NAIR_TWINKLE', [nt])
    # ---- round 7 (the moves round): the up smash's back sourspot, a smaller and lighter spray (pale stars and white
    # twinkles, no glow) than the Star Gun's full bursts; the Cannon Charge's heavier blast; smoke curling from a barrel
    ss = add('n_star_sour', disc('star', 3, 3.0, 0.3, 12, fric=0.82), spray_star(1.0, STAR_WHITE, 0.4, 12))
    sw2 = add('n_star_sour_tw', disc('twinkle', 3, 3.4, 0.3, 10, fric=0.82), spray_star(1.1, STAR_WHITE, 0.35, 10))
    rootgen('N_STAR_SOUR', [ss, sw2])
    hf = add('n_can_flash_heavy', dict(type=DISC, texg=tex['flash'], genlife=1, life=8, kind=BLEND_ONE, random=-1,
                                       size=0.2), flash(5.6, (255, 250, 220), (255, 130, 30), life=8))
    hr = add('n_can_ring_heavy', dict(type=DISC, texg=tex['n_ring'], genlife=1, life=8, kind=BLEND_ONE, random=-1,
                                      size=0.2), ring(6.4, (255, 226, 170), (255, 120, 30), life=8))
    rootgen('N_CANNON_HEAVY', [hf, hr, cs])
    bs = add('n_barrel_smoke', disc('n_puff', 1, 0.3, 0.05, 11, fric=0.9),
             puff(0.9, SMOKE, SMOKE, 2, 9, grow=1.9, rise=0.12, a0=SMOKE_A))
    rootgen('N_BARREL_SMOKE', [bs])
    return gens
