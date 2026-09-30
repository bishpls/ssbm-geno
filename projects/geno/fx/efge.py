"""Geno's effect file, EfGeData.dat: his own particle effects, loaded with him (decomp: efasync.c slot 22, EF_GENO_BANK).

Melee's effect system (projects/geno/fx/EFFECTS.md has the map): each series has an effect file whose root table holds a
particle bank (generators: an emitter header plus a command list the particle system runs every frame), a texture bank
(groups of frames the particles draw) and model effects (animated joint trees). An effect id is file slot * 1000 + n,
so Geno's are 22000-22999: generators 22000-22499 (the bank's first id is 22000) and model effects 22500+m. Move scripts
spawn them with the graphic-effect command (datkit's `gfx`), and C with efSync_Spawn(id, gobj, &pos).

Everything here is our own art, drawn in code: Melee's particle look (white intensity-and-alpha textures tinted per
particle by a prim colour on the bright parts and an env colour on the dim ones) in Super Mario RPG's vocabulary. The
SNES references (local, ROM-derived: ~/games/melee/sandbox/geno-fx/fx/smrpg) are the defeated-enemy star burst (SPR0516:
a flash, then a ring of eight rainbow stars flying out, shrinking), the come-back rainbow star's white twinkles (SPR0522,
drawn with the timed-hit "ding", ROM sound 172) and the Geno Beam's charge star (SPR0798).

    .venv/bin/python projects/geno/fx/efge.py [--install] [--c HEADER]
        -> $MELEE_WORK/fx/efge/ (spec, PNGs, ids.json) and EfGeData.dat; --install copies it to $MELEE_DISC/files/;
           --c writes the decomp's generated header (src/melee/ft/kinds/ftGeno/ftgeno_efge.h): EFGE_<NAME> per generator

Generators are referred to by name, never by number, in C (the header's EFGE_<NAME>) and in move scripts (efge.gid(NAME)
at build time), so modules can add generators without renumbering anyone's. Extension modules (EXTENSIONS: the normals'
and aerials' muzzles and bursts, efge_normals.py) define TEXTURES (appended after these) and generators(tex, first_id)
(tex: every texture group's index by name; first_id: the id their first generator gets); theirs follow Geno's specials'.
Rebuild the header and the file after any change to the lists (a merge of two lanes' additions: rerun both).

Names (the ids follow the list's order from 22000; see ids.json):
    TIMED_STARS        the timed release's rainbow stars (the Beam's timed press), a burst at the barrel; its parts
                       TIMED_RING0-7, TIMED_FLASH, TIMED_TWINKLE
    DRAW<L>_INNER/OUTER/FLARE  the charge's draw-in for a wave arriving at star L (1-3): the inner and outer arcs and
                       the tip's flare, spawned on the hand joint (efLib_CreateGenerator_Attach_AddAppSRT)
"""
import importlib, json, math, os, shutil, struct, subprocess, sys

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BANK = 22
FIRST = BANK * 1000

# ---------------------------------------------------------------------------------------------------- command lists
# The particle command set (sysdolphin particle.c hsd_8039930C; HSDRaw's ptcl.yml names them). A particle runs its list
# from the top, one frame at a time: a wait ends the frame's run, 0xFF ends the particle.


class Cmd:
    def __init__(self):
        self.b = bytearray()

    @staticmethod
    def _cnt(n):          # a frame count: one byte, or two with the top bit set
        return bytes([n]) if n < 0x80 else bytes([0x80 | n >> 8, n & 0xFF])

    @staticmethod
    def _f(x):
        return struct.pack('>f', x)

    def wait(self, n):
        while n > 0:
            k = min(n, 0x1FFF)
            self.b += bytes([k]) if k < 0x20 else bytes([0x20 | k >> 8, k & 0xFF])
            n -= k
        return self

    def tex(self, i, wait=0):                     # 0x40: frame i of the generator's texture group (its header's texg)
        self.b += bytes([0x40 | wait, i]); return self

    def vel(self, x=None, y=None, z=None):        # 0x90: set velocity components
        m = 0; d = b''
        for k, v in enumerate((x, y, z)):
            if v is not None: m |= 1 << k; d += self._f(v)
        self.b += bytes([0x90 | m]) + d; return self

    def size(self, target, frames=0):             # 0xA0: size (world units), eased over frames
        self.b += bytes([0xA0]) + self._cnt(frames) + self._f(target); return self

    def size_rand(self, target, rnd, frames=0):   # 0xAC: size target + rnd * random
        self.b += bytes([0xAC]) + self._cnt(frames) + self._f(target) + self._f(rnd); return self

    def grav(self, g):                            # 0xA2
        self.b += bytes([0xA2]) + self._f(g); return self

    def fric(self, f):                            # 0xA3: velocity *= f each frame
        self.b += bytes([0xA3]) + self._f(f); return self

    def spawn(self, gid):                         # 0xA5: a generator of this bank at the particle
        self.b += bytes([0xA5, gid >> 8 & 0xFF, gid & 0xFF]); return self

    def primenv(self):                            # 0xAD: tint by prim (bright) and env (dim)
        self.b += bytes([0xAD]); return self

    def rotate(self, add, frames=0):              # 0xB6: add to the rotation (radians) over frames
        self.b += bytes([0xB6]) + self._cnt(frames) + self._f(add); return self

    def rot_rand(self, base, rng, steps=0):       # 0xED: rotation += base + rng * random
        self.b += bytes([0xED]) + self._f(base) + self._f(rng) + bytes([steps]); return self

    def speed(self, base, rng=0.0):               # 0xBD: speed = base + rng * random, same direction
        self.b += bytes([0xBD]) + self._f(base) + self._f(rng); return self

    def _col(self, op, rgba, frames):
        m = 0; d = b''
        for k, v in enumerate(rgba):
            if v is not None: m |= 1 << k; d += bytes([int(v)])
        self.b += bytes([op | m]) + self._cnt(frames) + d; return self

    def prim(self, r=None, g=None, b=None, a=None, frames=0):   # 0xC0: prim colour, eased over frames
        return self._col(0xC0, (r, g, b, a), frames)

    def env(self, r=None, g=None, b=None, a=None, frames=0):    # 0xD0: env colour
        return self._col(0xD0, (r, g, b, a), frames)

    def loop(self, n):                            # 0xFA ... 0xFB: n times
        self.b += bytes([0xFA, n]); return self

    def again(self):
        self.b += bytes([0xFB]); return self

    def end(self):                                # 0xFF: the particle ends
        self.b += bytes([0xFF]); return self

    def hex(self):
        return bytes(self.b).hex().upper()


# generator kinds (HSDRaw ParticleKind): per-particle flags the generator hands its particles
GRAVITY, FRICTION, PRIMENV, BLEND_ONE = 0x1, 0x2, 0x80, 0x400000
DISC = 0   # the emitter shapes; a disc emits in the plane across its velocity, which for (0, 0, v) is the stage's plane

# ------------------------------------------------------------------------------------------------------- textures
# Drawn at 4x and reduced (antialiased). A channel = coverage, RGB = intensity (grey). With the prim/env tint on (psdisptev.c
# kind 0x480) the particle's colour is lerp(env, prim, texture intensity) and its alpha lerp(env.a, prim.a, texture alpha),
# so env alpha stays 0 (as every vanilla generator has it): the texture's alpha cuts the shape and prim alpha fades it.


def _poly_mask(n, pts, ss=4):
    from PIL import ImageDraw
    im = Image.new('L', (n * ss, n * ss), 0)
    ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return np.asarray(im.resize((n, n), Image.LANCZOS), dtype=np.float32) / 255.0


def star_points(cx, cy, R, r, n=5, rot=-math.pi / 2):
    pts = []
    for k in range(2 * n):
        a = rot + k * math.pi / n
        rr = R if k % 2 == 0 else r
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def tex_star(n=64):
    """SMRPG's plump five-point star (its inner radius about half the outer), lit from the top left: a pale highlight,
    a mid body and a darker rim the env colour takes."""
    c = n / 2
    cover = _poly_mask(n, star_points(c, c + 1.5, n * 0.47, n * 0.235))
    inner = _poly_mask(n, star_points(c, c + 1.5, n * 0.40, n * 0.19))
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    hl = np.clip(1.0 - np.hypot(xx - c * 0.80, yy - c * 0.78) / (n * 0.34), 0, 1)
    inten = 0.18 + 0.47 * inner + 0.35 * hl * inner
    return _ia(inten, cover)


def tex_flash(n=64):
    """The flash: a four-point sparkle with long concave points, a hot core and a soft halo."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    dx, dy = np.abs(xx - c) / c, np.abs(yy - c) / c
    astroid = (dx ** 0.5 + dy ** 0.5)          # < 1 inside the concave four-point shape
    shape = np.clip((1.0 - astroid) * 6.0, 0, 1)
    r = np.hypot(dx, dy)
    halo = np.clip(1.0 - r / 0.55, 0, 1) ** 2
    core = np.clip(1.0 - r / 0.22, 0, 1)
    alpha = np.clip(shape + 0.55 * halo, 0, 1)
    inten = np.clip(0.35 + 0.65 * core + 0.3 * shape, 0, 1)
    return _ia(inten, alpha)


def tex_twinkle(n=32):
    """A white twinkle: a thin cross with a bright centre (SMRPG's timed-hit twinkles)."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    dx, dy = np.abs(xx - c), np.abs(yy - c)
    arm = np.clip(1.2 - np.minimum(dx, dy), 0, 1) * np.clip(1.0 - np.maximum(dx, dy) / (c + 0.5), 0, 1)
    dot = np.clip(1.0 - np.hypot(dx, dy) / 3.0, 0, 1)
    alpha = np.clip(arm * 1.4 + dot, 0, 1)
    return _ia(np.clip(0.6 + 0.4 * dot, 0, 1), alpha)


def _ia(inten, alpha):
    i8 = (np.clip(inten, 0, 1) * 255).astype(np.uint8)
    a8 = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([i8, i8, i8, a8]), 'RGBA')


def tex_puff(n=32):
    """A soft round mist puff: dense in the middle, feathered at the edge (SMRPG's grey mist, SPR0527)."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot(xx - c, yy - c) / c
    lump = 0.12 * np.sin(5 * np.arctan2(yy - c, xx - c)) * r          # a slightly lumpy edge
    alpha = np.clip((1.0 - r + lump) / 0.55, 0, 1) ** 1.5
    return _ia(np.clip(0.75 + 0.25 * (1 - r), 0, 1), alpha)


def tex_ring(n=64, squash=0.67):
    """An oval ring (the Whirl's trail: the disc's outline at the SNES's angle), soft inside and out."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot((xx - c) / c, (yy - c) / (c * squash))
    band = np.exp(-((r - 0.82) / 0.1) ** 2)
    fill = np.clip(1.0 - r, 0, 1) * 0.35
    return _ia(np.clip(0.55 + 0.45 * band, 0, 1), np.clip(band + fill, 0, 1) * (r < 1.0))


def tex_bloom(n=64):
    """The red flash's shape: the sun's own silhouette (its disc and the flames' outline, flash_model.corona_rgba), on
    the same half-size as the fireball's texture (SUNBALL_Q disc radii), a little brighter at the heart."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import flash_model
    cor = np.asarray(flash_model.corona_rgba(n * 2).resize((n, n), Image.LANCZOS), np.float32)[..., 3] / 255.0
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    q = np.hypot(xx - c, yy - c) / c * flash_model.CORONA_Q          # disc radii
    alpha = np.maximum(cor, np.clip((1.02 - q) / 0.04, 0, 1))
    return _ia(np.clip(1.1 - 0.3 * q, 0.6, 1.0), alpha)


def tex_starflash(n=64):
    """The finishing flash's star: SMRPG's plump five-point star (the family of his other stars), glowing: a soft halo
    round it, white-hot at the heart."""
    from PIL import ImageFilter
    c = n / 2
    cover = _poly_mask(n, star_points(c, c + 1.0, n * 0.40, n * 0.20))
    halo = np.asarray(Image.fromarray((cover * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(n * 0.06)),
                      np.float32) / 255.0
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot(xx - c, yy - c) / c
    alpha = np.clip(np.maximum(cover, 0.8 * halo), 0, 1) * np.clip((1.0 - r) / 0.08, 0, 1)
    return _ia(np.clip(0.55 + 0.45 * (1.0 - r / 0.8) + 0.2 * cover, 0, 1), alpha)


def tex_sunring(n=64):
    """The finishing flash's ring: round (the old one was the Whirl's oval), a bright thin band, a faint glow inside."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot(xx - c, yy - c) / c
    band = np.clip(1.0 - np.abs(r - 0.86) / 0.09, 0, 1) ** 1.3
    inner = np.clip((r - 0.5) / 0.36, 0, 1) * (r < 0.86) * 0.25
    return _ia(np.clip(0.5 + 0.5 * band, 0, 1), np.clip(band + inner, 0, 1))


def tex_cloud(n=64):
    """SMRPG's landing cloud: a cluster of round puffs, lit from the top left, a greyer underside and a soft darker rim."""
    ss = 4
    m = n * ss
    yy, xx = np.mgrid[0:m, 0:m].astype(np.float32) / m
    cover = np.zeros((m, m), np.float32)
    shade = np.ones((m, m), np.float32)
    for cx, cy, r in ((0.5, 0.52, 0.26), (0.3, 0.58, 0.19), (0.7, 0.58, 0.19), (0.38, 0.38, 0.17), (0.62, 0.36, 0.18),
                      (0.18, 0.66, 0.12), (0.82, 0.66, 0.12), (0.5, 0.7, 0.2)):
        d = np.hypot(xx - cx, yy - cy) / r
        inside = d < 1
        cover = np.maximum(cover, inside.astype(np.float32))
        lit = 1.0 - 0.35 * np.clip((xx - cx + yy - cy) / (2 * r) + 0.5, 0, 1)    # lighter to the top left
        shade = np.where(inside & (d < 0.92), np.minimum(shade, lit), shade)
    rim = cover - (np.asarray(Image.fromarray((cover * 255).astype(np.uint8)).resize((m, m)), np.float32) / 255)
    under = np.clip((yy - 0.55) / 0.3, 0, 1) * 0.25
    inten = np.clip(shade - under, 0.45, 1.0)
    big = Image.fromarray(np.dstack([(inten * 255).astype(np.uint8)] * 3 + [(cover * 255).astype(np.uint8)]), 'RGBA')
    edge = np.asarray(big.split()[3].resize((n, n), Image.LANCZOS), np.float32) / 255
    small = np.asarray(big.resize((n, n), Image.LANCZOS), np.float32) / 255
    inner = np.asarray(Image.fromarray((edge * 255).astype(np.uint8)).filter(__import__('PIL.ImageFilter', fromlist=['x']).MinFilter(3)), np.float32) / 255
    i = small[..., 0] * (1 - 0.35 * np.clip(edge - inner, 0, 1))          # the soft darker outline
    return _ia(i, edge)


def tex_floorring(n=64, squash=0.28):
    """A shock ring lying on the floor (seen from the side): a bright thin band, squashed."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot((xx - c) / c, (yy - c) / (c * squash))
    band = np.clip(1.0 - np.abs(r - 0.82) / 0.12, 0, 1) ** 1.2
    return _ia(np.clip(0.55 + 0.45 * band, 0, 1), band * (r < 1.0))


def tex_spikering(n=64):
    """The Whirl's trail ring (Michael, 2026-09-30, after the remake's): a ring edged with small straight spikes round its
    rim, a hollow, darker, translucent centre; squashed to the disc's own oval (whirl_model.LOOK)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import whirl_model
    squash = {'tilt': 0.67, 'face': 1.0}[whirl_model.LOOK]
    ss = 4
    m = n * ss
    c = m / 2
    yy, xx = np.mgrid[0:m, 0:m].astype(np.float32)
    x, y = (xx - c) / c, (yy - c) / (c * squash)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    k = whirl_model.SPIKES
    spike = np.clip(1 - np.abs(((th / (2 * math.pi) * k) % 1.0) - 0.5) * 2 / 0.55, 0, 1)   # 1 on a spike's axis
    outer = 0.8 + 0.17 * spike                                              # the rim, reaching out in straight points
    band = (r > 0.62) & (r < outer)
    inten = np.where(band, 0.85 + 0.15 * spike, 0.3)
    alpha = np.where(band, 1.0, np.where(r <= 0.62, 0.22, 0.0))
    img = Image.fromarray(np.dstack([(inten * 255).astype(np.uint8)] * 3 + [(alpha * 255).astype(np.uint8)]), 'RGBA')
    img = img.resize((n, n), Image.LANCZOS)
    a = np.asarray(img, np.float32) / 255
    return _ia(a[..., 0], a[..., 3])


_SUNBALL = []


def _sunball(k):
    """Geno Flash's fireball: the whole sun small, its corona turned a step each frame (flash_model.sunball_frames)."""
    if not _SUNBALL:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import flash_model
        _SUNBALL.extend(flash_model.sunball_frames(64))
    return _SUNBALL[k]


TEXTURES = [  # the texture groups, in order: (name, GX format, frames); new groups go at the end (their indices are ids)
    ('star', 'IA8', [tex_star]),
    ('flash', 'IA8', [tex_flash]),
    ('twinkle', 'IA8', [tex_twinkle]),
    ('puff', 'IA8', [tex_puff]),
    ('ring', 'IA8', [tex_ring]),
    ('sunball', 'RGBA8', [lambda k=k: _sunball(k) for k in range(3)]),   # Geno Flash's fireball: the sun, small
    ('bloom', 'IA8', [lambda: tex_bloom()]),                              # Geno Flash's red flash: the sun's shape
    ('starflash', 'IA8', [lambda: tex_starflash()]),                      # its finishing flash: a glowing star
    ('sunring', 'IA8', [lambda: tex_sunring()]),                          # and the round ring round it
    ('cloud', 'IA8', [lambda: tex_cloud()]),                              # the Blast's landing: SMRPG's white cloud
    ('spikering', 'IA8', [lambda: tex_spikering()]),                      # the Whirl's trail: a spiked ring
    ('floorring', 'IA8', [lambda: tex_floorring()]),                      # its shock ring on the floor
]
EXTENSIONS = ['efge_normals']      # appended after Geno's specials, in this order


def _extensions():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    mods = []
    for name in EXTENSIONS:
        try:
            mods.append(importlib.import_module(name))
        except ModuleNotFoundError as e:
            if e.name != name:
                raise
    return mods


def all_textures():
    out = list(TEXTURES)
    for m in _extensions():
        out += list(getattr(m, 'TEXTURES', []))
    names = [t[0] for t in out]
    dup = {n for n in names if names.count(n) > 1}
    if dup:
        raise SystemExit(f'efge: texture names used twice: {sorted(dup)}')
    return out


TEX = {name: i for i, (name, _, _) in enumerate(all_textures())}

# ------------------------------------------------------------------------------------------------------- generators
# SMRPG's ring order, clockwise from the top (SPR0516): red, purple, blue, teal, green, yellow-green, yellow, orange.
# Each is (prim: the lit face, env: the rim), pale and deep versions of the hue.
RAINBOW = [((255, 190, 170), (232, 16, 24)), ((236, 190, 255), (136, 40, 200)), ((180, 200, 255), (24, 56, 240)),
           ((170, 250, 240), (0, 150, 150)), ((190, 255, 180), (24, 176, 48)), ((230, 255, 160), (120, 208, 16)),
           ((255, 250, 170), (240, 200, 0)), ((255, 220, 170), (240, 112, 16))]

RING_SPEED = 2.3      # units a frame out of the barrel; friction eases it to ~14 units in 16 frames
RING_FRIC = 0.86
RING_LIFE = 26
STAR_SIZE = 2.2      # a particle's size is its half-width in units
FLASH_SIZE = 6.0
TWINKLE_SIZE = 1.4


def ring_star(prim, env):
    """One of the ring's stars: pops in, spins a little, flies out and shrinks, then blinks away."""
    c = Cmd().tex(0).primenv()
    c.prim(*prim, 255).env(*env, 0)
    c.size(0.5).size(STAR_SIZE, 4).rot_rand(-0.35, 0.7).rotate(0.9, RING_LIFE)
    c.wait(10).size(STAR_SIZE * 0.4, 14).wait(10)
    c.prim(a=0, frames=6).wait(6).end()
    return c


def flash():
    """The flash at the barrel: a sparkle that pops big, turns 45 degrees into an X (SMRPG's three-frame flash) and fades."""
    c = Cmd().tex(0).primenv().prim(255, 255, 255, 255).env(255, 176, 24, 0)
    c.size(2.0).size(FLASH_SIZE, 2).wait(2).rotate(math.pi / 4).size(FLASH_SIZE * 0.75, 3).wait(3)
    c.size(1.5, 4).prim(a=0, frames=4).wait(4).end()
    return c


def twinkle():
    """White twinkles scattered round the burst, blinking twice after the ring has gone out (SPR0522)."""
    c = Cmd().tex(0).primenv().prim(255, 255, 255, 255).env(150, 200, 255, 0).size(0.0)
    c.wait(5)
    for _ in range(3):
        c.size(TWINKLE_SIZE, 3).wait(3).size(0.2, 3).wait(3)
    return c.end()


# ---- the Beam's charge: energy drawn into the barrel (Michael: "the SNES animation draws energy into him"). The SNES
# (the attract demo's Beam, frames 27388-27512): waves of 3-5 single-pixel twinkles in an arc ahead of and above the tip,
# converging on it over ~8-10 frames while the whole wave shimmers blue, white, lavender (two frames each); the tip flares
# lavender as they arrive; a new wave every ~10-16 frames. Ours: small stars from the star art, in a tight wedge (two
# arcs at different distances, jittered, so it isn't a circle), arriving together, a flare at the tip; each lit star
# adds stars to the wave and grows them and the flare, so the charge level reads.
DRAW_T = 9                 # frames from the arc to the tip
DRAW_ARC = (-0.35, 1.75)   # radians from the barrel's forward direction (facing right), up past vertical
DRAW_R = (3.2, 5.6)        # the inner and outer arc's distance from the tip
DRAW_JITTER = 0.55         # each star starts up to this far off its arc
# per level, the star count a wave arrives at (the charge's frames 11, 21, 31, 41, 51 spawn one each, arriving at 20-60:
# every star lights as a wave lands): stars on the inner and outer arc, the stars' half-width, the flare's
DRAW_LEVELS = [(2, 1, 0.7, 1.8), (3, 2, 0.85, 2.4), (3, 3, 1.0, 3.1)]
DRAW_COLS = [(255, 255, 255), (206, 176, 255), (96, 120, 255)]      # white, lavender, blue: the SNES wave's shimmer


def draw_star(size):
    c = Cmd().tex(0).primenv().prim(255, 255, 255, 255).env(150, 140, 255, 0)
    c.b += bytes([0xA8]) + Cmd._f(DRAW_JITTER) + Cmd._f(DRAW_JITTER) + Cmd._f(0.0)      # 0xA8: start off the arc
    c.size(0.2).size(size, 3).rot_rand(-0.4, 0.8).rotate(1.4, DRAW_T + 1)
    k = 0
    for t in range(0, DRAW_T - 1, 2):                              # the wave's shimmer, in step for all its stars
        if t == 4:                                                 # after the 3-frame pop-in
            c.size(size * 0.55, DRAW_T - 5)                        # drawn in: shrinking as they close on the tip
        c.prim(*DRAW_COLS[k % 3]).wait(2); k += 1
    c.size(size * 0.25, 2).prim(*DRAW_COLS[1]).wait(2)
    return c.end()


def draw_flare(size):
    """The tip flares lavender as the wave arrives, turns 45 degrees and fades (the SNES tip's lavender flash)."""
    c = Cmd().tex(0).primenv().prim(236, 220, 255, 0).env(150, 120, 255, 0).size(0.0)
    c.wait(DRAW_T - 2)
    c.prim(a=255).size(size, 2).wait(2).rotate(math.pi / 4).size(size * 0.7, 3).wait(3)
    c.prim(a=0, frames=3).size(size * 0.3, 3).wait(3)
    return c.end()


# ---- the Finger Shot's muzzle puff (SMRPG's SPR0527: a grey mist at the fingertips that condenses into a small yellow
# star as the bullets leave). Spawned by the C with each shot (FINGER_PUFF, at the fingertips), the down throw's too
PUFF_STAR = 1.0             # the star's half-width


def puff_mist():
    c = Cmd().tex(0).primenv().prim(235, 235, 240, 220).env(140, 140, 155, 0)
    c.size(0.5).size(1.7, 4).rot_rand(0.0, 6.28)
    c.wait(3).prim(a=0, frames=5).wait(5)
    return c.end()


def puff_star():
    c = Cmd().tex(0).primenv().prim(255, 246, 150, 0).env(236, 150, 20, 0).size(0.0)
    c.wait(3).prim(a=255).size(PUFF_STAR, 2).rot_rand(-0.3, 0.6).rotate(0.8, 12).wait(6)
    c.size(PUFF_STAR * 0.4, 5).prim(a=0, frames=5).wait(5)
    return c.end()


# ---- the Geno Whirl (SMRPG: a white-yellow disc trailing fading yellow ovals; the hit explodes, SPR0517: a yellow-white
# ball and scattered orange dots; the timed press flashes the screen blue). The item code drops a trail ring every few
# frames of the throw, and spawns the hit bursts
def whirl_ring():
    c = Cmd().tex(0).primenv().prim(255, 240, 150, 230).env(200, 140, 20, 0).size(4.4)
    c.size(3.6, 12).wait(3).prim(255, 200, 60, frames=6).wait(4).prim(a=0, frames=6).wait(6)
    return c.end()


def whirl_ball(size, cols):
    """The explosion's ball: pops yellow-white, swells, cools to orange and fades (SPR0517's six molds)."""
    c = Cmd().tex(0).primenv().prim(*cols[0], 255).env(*cols[1], 0).size(size * 0.3)
    c.size(size, 3).wait(3).prim(*cols[2], frames=5).size(size * 1.15, 6).wait(4).prim(a=0, frames=5).wait(5)
    return c.end()


def whirl_spark(size, life):
    c = Cmd().tex(0).primenv().prim(255, 220, 90, 255).env(230, 70, 20, 0).size(size)
    c.wait(life // 2).prim(240, 110, 30, frames=life // 2).size(size * 0.4, life // 2).wait(life // 2)
    return c.end()


def whirl_crit_flash():
    """The crit's blue flash: SMRPG flashes the whole screen blue; ours is a big blue-white bloom at the hit (additive)."""
    c = Cmd().tex(0).primenv().prim(220, 235, 255, 255).env(40, 90, 255, 0).size(6.0)
    c.size(26.0, 3).wait(3).prim(a=0, frames=6).size(30.0, 6).wait(6)
    return c.end()


def whirl_crit_ring():
    c = Cmd().tex(0).primenv().prim(200, 225, 255, 255).env(40, 90, 255, 0).size(3.0)
    c.size(16.0, 10).wait(4).prim(a=0, frames=6).wait(6)
    return c.end()


# ---- the Geno Blast (SMRPG: blue four-point sparkles rising at his hand as he casts, the columns each landing in a white
# cloud). The tell's sparkles rise from the mark; the landing cloud is spawned where each column meets the floor. A disc
# emits along its velocity within `angle` of it, from a disc across it: (0, v, 0) rises from a flat disc on the floor
def blast_sparkle(size, life):
    c = Cmd().tex(0).primenv().prim(235, 245, 255, 255).env(70, 110, 255, 0).size(0.2)
    c.size(size, 4).rot_rand(0.0, 0.8).wait(life - 8).size(0.2, 8).prim(a=0, frames=8).wait(8)
    return c.end()


def blast_cloud(size):
    """SMRPG's white landing cloud (texture group cloud): pops, billows out and fades, shaded grey-blue underneath."""
    c = Cmd().tex(0).primenv().prim(255, 255, 255, 255).env(150, 165, 205, 0).size(size * 0.35)
    c.size(size, 4).rot_rand(-0.25, 0.5).wait(9).size(size * 1.25, 12).prim(a=0, frames=12).wait(12)
    return c.end()


def blast_ring():
    """The landing's shock ring on the floor: runs out from under the column and fades."""
    c = Cmd().tex(0).primenv().prim(255, 255, 245, 255).env(150, 200, 255, 0).size(5.0)
    c.size(22.0, 11).wait(4).prim(a=0, frames=7).wait(7)
    return c.end()


def blast_vanish_ring():
    """A cancelled mark (the cannon committed, a ledge grab): the floor ring closes in and is gone."""
    c = Cmd().tex(0).primenv().prim(220, 235, 255, 230).env(90, 130, 255, 0).size(11.0)
    c.size(2.0, 7).prim(a=0, frames=7).wait(7)
    return c.end()


def sr_star(size, life):
    """Star Road's no-damage stars: small, cream-white with a blue rim (the hitting moves' stars are gold), spinning as
    they shrink and fade (after the Flash's finishing stars)."""
    c = Cmd().tex(0).primenv().prim(255, 250, 228, 255).env(110, 160, 255, 0).size(size * 0.3).rot_rand(0.0, 6.28)
    c.size(size, 3).rotate(4.5, life).wait(3).size(size * 0.3, life - 3).wait(life - 9).prim(a=0, frames=6).wait(6)
    return c.end()


# ---- Geno Flash (SMRPG: Geno glows in a yellow column as he becomes the cannon; the cannon fires a fireball, which becomes
# the sun (the article's own model: flash_model.py); the screen flashes red). The glow is spawned by the move script
# (frame 1, at his hips); the fireball by the C, from the cannon's muzzle toward the sun (its velocity set to arrive as the
# sun appears); the red flash as the sun ends. One sun for the whole move (Michael, 2026-09-29): the fireball is the sun
# itself, small (texture group sunball), growing to the sun's first size as it flies
FIREBALL_T = 5              # frames from the muzzle to the sun's centre
FIREBALL_R0 = 4.5           # its disc's radius leaving the muzzle, and arriving: the sun's first (hitbox 14.3 x FIT 0.98)
FIREBALL_R1 = 14.0
SUNBALL_Q = 1.5             # the texture's half-size in disc radii (flash_model.CORONA_Q)
FLASH_SUN_Q = 28.0 * 0.98 * SUNBALL_Q   # the red flash's half-size: the grown sun's (hitbox 28, disc 0.98x)
FLASH_BURST_Q = 14.3 * 0.98 * SUNBALL_Q  # the burst's: the sun's first (hitbox 14.3)
FLASH_BURST_T = 8                        # its frames: the sweetspot's (rig/articles.py FLASH_EXT 0x18)


def flash_glow_core():
    """SMRPG's yellow column as he becomes the cannon: a soft yellow glow over his whole body, pulsing, then fading."""
    c = Cmd().tex(0).primenv().prim(255, 245, 170, 0).env(255, 200, 50, 0).size(5.0)
    c.prim(a=150, frames=4).size(8.0, 4).wait(4)
    for _ in range(3):
        c.size(7.0, 3).prim(a=110, frames=3).wait(3).size(8.0, 3).prim(a=150, frames=3).wait(3)
    c.prim(a=0, frames=6).size(6.0, 6).wait(6)
    return c.end()


def flash_glow_rise():
    c = Cmd().tex(0).primenv().prim(255, 250, 200, 220).env(255, 190, 40, 0).size(0.9)
    c.wait(8).size(0.3, 8).prim(a=0, frames=8).wait(8)
    return c.end()


def flash_fireball(trail_id):
    """The fireball: the sun, small (its disc, face and corona on one texture), growing to the sun's first size as it
    flies and stepping through the corona's frames so the flames churn; embers drop behind it. Drawn in its own colours
    (prim white, env black: the tint passes the texture through) and blended normally, so the face stays dark."""
    c = Cmd().tex(0).primenv().prim(255, 255, 255, 255).env(0, 0, 0, 0).size(FIREBALL_R0 * SUNBALL_Q)
    c.size(FIREBALL_R1 * SUNBALL_Q, FIREBALL_T)
    for k in range(FIREBALL_T + 1):
        c.tex(k % 3).spawn(trail_id).wait(1)
    return c.end()


def flash_ember():
    c = Cmd().tex(0).primenv().prim(255, 200, 80, 220).env(230, 60, 10, 0).size(1.8)
    c.size(0.6, 8).prim(a=0, frames=8).wait(8)
    return c.end()


def flash_red():
    """SMRPG's red flash as the sun ends: the sun's own silhouette (the disc and its flames) flashes red over it as it
    goes (additive), then swells a little and fades (its edge 1.13-1.18x the full hitbox). Since 2026-09-29: it was a
    four-point flash inside an oval ring, which read as the star Michael had the sun lose; a plain round bloom ended on
    the pure circle he found off."""
    c = Cmd().tex(0).primenv().prim(255, 110, 70, 225).env(215, 25, 10, 0).size(FLASH_SUN_Q)
    c.wait(2).size(FLASH_SUN_Q * 1.14, 12).rotate(0.25, 12).prim(a=0, frames=12).wait(12)
    return c.end()


# ---- Geno Flash's finishing flash (Michael, 2026-09-29: the old ending's "neat little flash effect ... as were the rotating
# stars; ... a similar finishing flash ... with a star instead of a diamond alongside the circular effect"): as the sun
# goes, a glowing star spins out of it over its red silhouette (FLASH_RED), a round ring runs out round it, and small
# gold stars spin away. Sized to the full sun (hitbox 28). Spawned with FLASH_END (itgeno.c)
FLASH_FIN_R = 28.0


def flash_fin_star():
    """The star, where the old ending had its four-point flash: it pops at about half the sun, pink-hot like the red
    silhouette under it, and swells past the sun's edge while it spins a sixth of a turn, then fades."""
    c = Cmd().tex(0).primenv().prim(255, 190, 155, 235).env(225, 45, 35, 0).size(FLASH_FIN_R * 0.55)
    c.size(FLASH_FIN_R * 1.3, 11).rotate(-1.05, 16).wait(6).prim(a=0, frames=10).wait(10)
    return c.end()


def flash_fin_ring():
    """The ring: from the sun's edge out to ~1.7x, fading as it goes."""
    c = Cmd().tex(0).primenv().prim(255, 235, 185, 255).env(255, 110, 40, 0).size(FLASH_FIN_R * 1.1)
    c.size(FLASH_FIN_R * 2.0, 14).wait(5).prim(a=0, frames=9).wait(9)
    return c.end()


def flash_fin_spark():
    """A small gold star thrown from the sun, spinning as it slows and shrinks away."""
    c = Cmd().tex(0).primenv().prim(255, 250, 200, 255).env(240, 150, 20, 0).size(3.4).rot_rand(0.0, 6.28)
    c.rotate(5.5, 24).size(1.4, 24).wait(14).prim(a=0, frames=10).wait(10)
    return c.end()


def flash_burst():
    """The burst, the sun's sweetspot (Michael, 2026-09-29: the small first sun is the kill hit): the sun's silhouette in
    white heat over it (additive) for the burst's frames, growing with it, then gone as the hit turns weak. It took the
    unspawned FLASH_RING's slot, so no id after it moved."""
    c = Cmd().tex(0).primenv().prim(255, 250, 225, 235).env(255, 200, 90, 0).size(FLASH_BURST_Q * 0.9)
    c.size(FLASH_BURST_Q * 1.2, FLASH_BURST_T).wait(FLASH_BURST_T - 3).prim(a=0, frames=3).wait(3)
    return c.end()


# ---- the up throw's Star Gun stars: a sparkle trail behind each (the item code drops one every other frame)
def throwstar_sparkle():
    c = Cmd().tex(0).primenv().prim(255, 250, 200, 255).env(255, 170, 30, 0).size(0.9).rot_rand(0.0, 0.8)
    c.wait(4).size(0.2, 8).prim(a=0, frames=8).wait(8)
    return c.end()


# ---- the forward throw's Rocket Fist: the launch, a small white four-point star at the wrist that pops, turns into an X
# and fades (the exhaust is the normals' N_EXHAUST, shared with the forward smash's rocket fists)
def rocket_launch():
    c = Cmd().tex(0).primenv().prim(255, 255, 255, 255).env(200, 220, 255, 0).size(1.5)
    c.size(4.8, 1).wait(2).rotate(math.pi / 4).size(3.6, 3).wait(3).size(1.2, 4).prim(a=0, frames=4).wait(4)
    return c.end()


def root(children):
    """The id the game spawns: one particle that starts the burst's generators where it stands, then ends."""
    c = Cmd()
    for gid in children:
        c.spawn(gid)
    return c.end()


def generators():
    """(name, header, command list) in id order from 22000."""
    gens = []
    ring_ids = [FIRST + 1 + k for k in range(len(RAINBOW))]
    flash_id = FIRST + 1 + len(RAINBOW)
    twinkle_id = flash_id + 1
    gens.append(('TIMED_STARS', dict(type=DISC, genlife=1, life=1, random=-1, size=1), root(ring_ids + [flash_id, twinkle_id])))
    for k, (prim, env) in enumerate(RAINBOW):
        az = math.pi / 2 - k * 2 * math.pi / len(RAINBOW)       # clockwise from the top
        az = az if abs(az) > 1e-4 else 1e-4                       # (0, 0) would mean "any direction"
        gens.append((f'TIMED_RING{k}', dict(type=DISC, texg=TEX['star'], genlife=1, life=RING_LIFE, kind=FRICTION, fric=RING_FRIC,
                                      v=[0, 0, RING_SPEED], radius=-0.8, angle=math.pi / 2, random=-1,
                                      size=STAR_SIZE, params=[az, az, 0]), ring_star(prim, env)))
    gens.append(('TIMED_FLASH', dict(type=DISC, texg=TEX['flash'], genlife=1, life=10, kind=BLEND_ONE, random=-1, size=2), flash()))
    gens.append(('TIMED_TWINKLE', dict(type=DISC, texg=TEX['twinkle'], genlife=1, life=24, kind=FRICTION, fric=0.9, v=[0, 0, 0.5],
                                 radius=9.0, angle=math.pi / 2, random=-6, size=0.1), twinkle()))
    # the charge's draw-in (22011+): a disc with a fixed radius (negative) and a spread angle of 3pi/2 emits on the arc
    # with its speed pointing at the centre, so every star of an arc reaches the tip on frame DRAW_T. The C sets the
    # generator's centre to the tip (in the hand joint's space) and mirrors the arc when he faces left
    for lv, (n_in, n_out, size, flare) in enumerate(DRAW_LEVELS, start=1):
        for k, (n, r) in enumerate(((n_in, DRAW_R[0]), (n_out, DRAW_R[1]))):
            gens.append((f'DRAW{lv}_{"INNER" if k == 0 else "OUTER"}',
                         dict(type=DISC, texg=TEX['star'], genlife=1, life=DRAW_T + 2, v=[0, 0, r / DRAW_T], radius=-r,
                              angle=3 * math.pi / 2, random=-n, size=0.2, params=[DRAW_ARC[0], DRAW_ARC[1], 0]),
                         draw_star(size)))
        gens.append((f'DRAW{lv}_FLARE', dict(type=DISC, texg=TEX['flash'], genlife=1, life=DRAW_T + 9, kind=BLEND_ONE,
                                             random=-1, size=0.1), draw_flare(flare)))
    # the Whirl: the trail ring (the item code drops one every few frames of the throw), the hit burst,
    # the shield grind's sparks, the crit's blue flash
    gens.append(('WHIRL_RING', dict(type=DISC, texg=TEX['spikering'], genlife=1, life=16, random=-1, size=4.4),
                 whirl_ring()))
    ball, sparks = FIRST + len(gens), FIRST + len(gens) + 1
    gens.append(('WHIRL_HIT_BALL', dict(type=DISC, texg=TEX['puff'], genlife=1, life=15, kind=BLEND_ONE, random=-1, size=1),
                 whirl_ball(5.5, ((255, 255, 235), (255, 200, 60), (255, 150, 40)))))
    gens.append(('WHIRL_HIT_SPARKS', dict(type=DISC, texg=TEX['puff'], genlife=1, life=16, kind=FRICTION, fric=0.86,
                                          v=[0, 0, 1.6], radius=0.6, angle=math.pi / 2, random=-12, size=0.6),
                 whirl_spark(0.7, 16)))
    gens.append(('WHIRL_HIT', dict(type=DISC, genlife=1, life=1, random=-1, size=1), root([ball, sparks])))
    gens.append(('WHIRL_GRIND', dict(type=DISC, texg=TEX['puff'], genlife=1, life=10, kind=FRICTION, fric=0.84,
                                     v=[0, 0, 1.1], radius=0.4, angle=math.pi / 2, random=-5, size=0.45),
                 whirl_spark(0.5, 10)))
    cflash, cring = FIRST + len(gens), FIRST + len(gens) + 1
    gens.append(('WHIRL_CRIT_FLASH', dict(type=DISC, texg=TEX['flash'], genlife=1, life=10, kind=BLEND_ONE, random=-1, size=1),
                 whirl_crit_flash()))
    gens.append(('WHIRL_CRIT_RING', dict(type=DISC, texg=TEX['ring'], genlife=1, life=11, kind=BLEND_ONE, random=-1, size=1),
                 whirl_crit_ring()))
    gens.append(('WHIRL_CRIT', dict(type=DISC, genlife=1, life=1, random=-1, size=1), root([cflash, cring, ball, sparks])))
    # the Blast: the cast's sparkles at his hand, the tell's at the mark, the landing cloud and sparkles at each column
    gens.append(('BLAST_CAST', dict(type=DISC, texg=TEX['flash'], genlife=1, life=26, kind=FRICTION, fric=0.93,
                                    v=[0, 0.9, 0], radius=2.5, angle=0.5, random=-7, size=0.3), blast_sparkle(1.3, 26)))
    gens.append(('BLAST_TELL', dict(type=DISC, texg=TEX['flash'], genlife=1, life=20, kind=FRICTION, fric=0.95,
                                    v=[0, 0.7, 0], radius=5.0, angle=0.25, random=-2, size=0.3), blast_sparkle(1.0, 20)))
    cloud, lspark = FIRST + len(gens), FIRST + len(gens) + 1
    gens.append(('BLAST_LAND_CLOUD', dict(type=DISC, texg=TEX['cloud'], genlife=1, life=23, kind=FRICTION, fric=0.88,
                                          v=[0, 0.5, 0], radius=5.0, angle=math.pi / 2, random=-7, size=1.0),
                 blast_cloud(6.0)))          # as wide as the column, as SMRPG's clouds are
    gens.append(('BLAST_LAND_SPARK', dict(type=DISC, texg=TEX['flash'], genlife=1, life=18, kind=FRICTION | GRAVITY,
                                          grav=0.04, fric=0.9, v=[0, 1.4, 0], radius=1.0, angle=0.9, random=-6, size=0.3),
                 blast_sparkle(0.9, 18)))
    gens.append(('BLAST_LAND', dict(type=DISC, genlife=1, life=1, random=-1, size=1), root([cloud, lspark])))
    # Geno Flash: the transform's glow, the fireball and its trail, the red flash as the sun ends
    gcore, grise = FIRST + len(gens), FIRST + len(gens) + 1
    gens.append(('FLASH_GLOW_CORE', dict(type=DISC, texg=TEX['puff'], genlife=1, life=34, kind=BLEND_ONE, random=-1,
                                         size=5.0), flash_glow_core()))
    gens.append(('FLASH_GLOW_RISE', dict(type=DISC, texg=TEX['flash'], genlife=26, life=16, kind=BLEND_ONE,
                                         v=[0, 1.1, 0], radius=4.5, angle=0.1, random=-2, size=0.9), flash_glow_rise()))
    gens.append(('FLASH_GLOW', dict(type=DISC, genlife=1, life=1, random=-1, size=1), root([gcore, grise])))
    ember = FIRST + len(gens)
    gens.append(('FLASH_EMBER', dict(type=DISC, texg=TEX['puff'], genlife=1, life=8, kind=BLEND_ONE, random=-1, size=1.8),
                 flash_ember()))
    gens.append(('FLASH_FIREBALL', dict(type=DISC, texg=TEX['sunball'], genlife=1, life=FIREBALL_T + 1, kind=0,
                                        v=[0, 0, 1], random=-1, size=FIREBALL_R0 * SUNBALL_Q), flash_fireball(ember)))
    red = FIRST + len(gens)
    gens.append(('FLASH_RED', dict(type=DISC, texg=TEX['bloom'], genlife=1, life=15, kind=BLEND_ONE, random=-1,
                                   size=FLASH_SUN_Q),
                 flash_red()))
    gens.append(('FLASH_BURST', dict(type=DISC, texg=TEX['bloom'], genlife=1, life=FLASH_BURST_T + 1, kind=BLEND_ONE,
                                     random=-1, size=FLASH_BURST_Q), flash_burst()))
    gens.append(('FLASH_END', dict(type=DISC, genlife=1, life=1, random=-1, size=1), root([red])))
    # the up throw's stars: their sparkle trail
    gens.append(('THROW_STAR_TRAIL', dict(type=DISC, texg=TEX['flash'], genlife=1, life=12, kind=FRICTION, fric=0.9,
                                          v=[0, 0, 0.3], radius=0.8, angle=math.pi / 2, random=-2, size=0.9),
                 throwstar_sparkle()))
    # the forward throw's Rocket Fist launch
    gens.append(('ROCKET_LAUNCH', dict(type=DISC, texg=TEX['flash'], genlife=1, life=10, kind=BLEND_ONE, random=-1,
                                       size=0.8), rocket_launch()))
    # the Finger Shot's muzzle puff: the mist and the star, and the root the C spawns
    mist_id, star_id = FIRST + len(gens), FIRST + len(gens) + 1
    gens.append(('FINGER_PUFF_MIST', dict(type=DISC, texg=TEX['puff'], genlife=1, life=9, kind=FRICTION, fric=0.85,
                                          v=[0, 0.12, 0], random=-1, size=0.5), puff_mist()))
    gens.append(('FINGER_PUFF_STAR', dict(type=DISC, texg=TEX['star'], genlife=1, life=17, random=-1, size=0.1), puff_star()))
    gens.append(('FINGER_PUFF', dict(type=DISC, genlife=1, life=1, random=-1, size=1), root([mist_id, star_id])))
    # Geno Flash's finishing flash (2026-09-29; at the end of the list, so no special's id moved)
    fstar, fring, fsparks = FIRST + len(gens), FIRST + len(gens) + 1, FIRST + len(gens) + 2
    gens.append(('FLASH_FIN_STAR', dict(type=DISC, texg=TEX['starflash'], genlife=1, life=17, kind=BLEND_ONE, random=-1,
                                        size=FLASH_FIN_R * 0.55), flash_fin_star()))
    gens.append(('FLASH_FIN_RING', dict(type=DISC, texg=TEX['sunring'], genlife=1, life=15, kind=BLEND_ONE, random=-1,
                                        size=FLASH_FIN_R * 1.1), flash_fin_ring()))
    gens.append(('FLASH_FIN_SPARKS', dict(type=DISC, texg=TEX['star'], genlife=1, life=25, kind=FRICTION, fric=0.9,
                                          v=[0, 0, 3.2], radius=FLASH_FIN_R * 0.7, angle=math.pi / 2, random=-7, size=3.4),
                 flash_fin_spark()))
    gens.append(('FLASH_FINISH', dict(type=DISC, genlife=1, life=1, random=-1, size=1), root([fstar, fring, fsparks])))
    # the Blast, richer (2026-09-30): the landing's floor ring (added to BLAST_LAND below)
    bring = FIRST + len(gens)
    gens.append(('BLAST_LAND_RING', dict(type=DISC, texg=TEX['floorring'], genlife=1, life=11, kind=BLEND_ONE, random=-1,
                                         size=5.0), blast_ring()))
    k = next(i for i, g in enumerate(gens) if g[0] == 'BLAST_LAND')
    kids = [FIRST + i for i, g in enumerate(gens) if g[0] in ('BLAST_LAND_CLOUD', 'BLAST_LAND_SPARK')] + [bring]
    gens[k] = ('BLAST_LAND', gens[k][1], root(kids))
    # a cancelled mark's vanish (itgeno.c itGe_BlastVanish): the ring closes in, a few blue sparkles lift away
    vring = FIRST + len(gens)
    gens.append(('BLAST_VANISH_RING', dict(type=DISC, texg=TEX['floorring'], genlife=1, life=7, kind=BLEND_ONE, random=-1,
                                           size=11.0), blast_vanish_ring()))
    gens.append(('BLAST_VANISH_SPARK', dict(type=DISC, texg=TEX['flash'], genlife=1, life=14, kind=FRICTION, fric=0.9,
                                            v=[0, 0.9, 0], radius=6.0, angle=0.3, random=-4, size=0.8),
                 blast_sparkle(0.8, 14)))
    gens.append(('BLAST_VANISH', dict(type=DISC, genlife=1, life=1, random=-1, size=1), root([vring, vring + 1])))
    # Star Road (2026-09-30): no-damage stars, a burst at the launch from each hand and a light trail in flight
    gens.append(('SR_BURST', dict(type=DISC, texg=TEX['star'], genlife=1, life=20, kind=FRICTION, fric=0.87,
                                  v=[0, 0, 1.5], radius=0.8, angle=math.pi / 2, random=-5, size=1.6), sr_star(1.6, 20)))
    gens.append(('SR_TRAIL', dict(type=DISC, texg=TEX['star'], genlife=1, life=16, kind=FRICTION, fric=0.9,
                                  v=[0, 0, 0.25], radius=0.6, angle=math.pi / 2, random=-1, size=1.2), sr_star(1.2, 16)))
    return gens


def all_generators():
    """Geno's specials' generators, then each extension's, as (name, header, command list), in id order from FIRST."""
    gens = generators()
    for m in _extensions():
        gens += m.generators(TEX, FIRST + len(gens))
    names = [g[0] for g in gens]
    dup = {n for n in names if names.count(n) > 1}
    if dup:
        raise SystemExit(f'efge: generator names used twice: {sorted(dup)}')
    if len(gens) > 500:
        raise SystemExit(f'efge: {len(gens)} generators; 22000-22499 is the generator range (22500+ are model effects)')
    return gens


def ids():
    """Every generator's id by name."""
    return {g[0]: FIRST + i for i, g in enumerate(all_generators())}


def gid(name):
    """A generator's effect id by name, for move scripts (the graphic-effect command) at build time."""
    m = ids()
    if name not in m:
        raise KeyError(f'efge: no generator {name!r}')
    return m[name]


def write_header(path):
    m = ids()
    L = ['/* generated by projects/geno/fx/efge.py --c: EfGeData.dat\'s generator ids by name. Don\'t edit: rerun it after any',
         ' * change to its lists (efge.py, efge_normals.py). Spawn with efSync_Spawn(EFGE_<NAME>, gobj, &pos), or on a joint',
         ' * with efLib_CreateGenerator_Attach_AddAppSRT. */', '#ifndef FTGENO_EFGE_H', '#define FTGENO_EFGE_H', '']
    L += [f'#define EFGE_{n} {i}' for n, i in m.items()]
    L += ['', f'#define EFGE_COUNT {len(m)}', '', '#endif', '']
    open(path, 'w').write('\n'.join(L))
    print('wrote', path, len(m), 'generators')


def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    tex = []
    for name, fmt, frames in all_textures():
        paths = []
        for i, fn in enumerate(frames):
            p = f'{name}_{i}.png'
            fn().save(os.path.join(out_dir, p))
            paths.append(p)
        tex.append(dict(fmt=fmt, frames=paths))
    gens = []
    for name, hdr, cmd in all_generators():
        g = dict(hdr); g['cmd'] = cmd.hex(); g['name'] = name
        gens.append(g)
    json.dump(ids(), open(os.path.join(out_dir, 'ids.json'), 'w'), indent=1)
    spec = dict(root='effGenoDataTable', bank=BANK, first_id=FIRST, textures=tex, generators=gens)
    sp = os.path.join(out_dir, 'efge.json')
    json.dump(spec, open(sp, 'w'), indent=1)
    dat = os.path.join(os.path.dirname(out_dir), 'EfGeData.dat')
    subprocess.run([os.path.join(REPO, 'tools/machinima/melee/datkit.sh'), 'ef-build', sp, dat], check=True)
    return dat


def main():
    work = os.environ.get('MELEE_WORK', os.path.expanduser('~/games/melee/work'))
    if '--c' in sys.argv:
        write_header(sys.argv[sys.argv.index('--c') + 1])
    dat = build(os.path.join(work, 'fx', 'efge'))
    if '--install' in sys.argv:
        disc = os.environ.get('MELEE_DISC', os.path.expanduser('~/games/melee/disc'))
        shutil.copy(dat, os.path.join(disc, 'files', 'EfGeData.dat'))
        print('installed', os.path.join(disc, 'files', 'EfGeData.dat'))


if __name__ == '__main__':
    main()
