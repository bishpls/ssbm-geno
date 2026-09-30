"""The Geno Beam's own projectile model (route 1 of the effects study): replaces the donor Falco laser's mesh in PlGe.dat's
Beam article, built by fighter-build from this spec (datkit ArticleModel.cs; articles.py hands it over).

The look is Super Mario RPG's Geno Beam as the SNES battle draws it (the attract demo's Geno Beam, captured locally in
~/games/smrpg/work/fx/beam_frames.png): a thick beam with a wide white-hot core, a thin cyan rim and a soft blue glow,
blended over the scene, with a rounded, bright end. The SNES draws it flat (a background layer), so this is flat too:
textured ribbons facing the camera, not faceted shells (the first pass, 10-sided shells, read as a crystal lance).

In Melee it is a bolt, so it keeps the laser's behaviour: it flies along its +Z; the item code (decomp itgeno.c
itGe_BeamRay) turns the root along the flight and stretches only the trail joint's length as it leaves the barrel (by
the hitboxes' spacing: 0.58, 0.76, 1 at one, two, three stars, which ride that joint), and draws the trail's cross-section
and the head by `vis` (0.45, 0.70, 1): thickness is the level cue (Michael, 2026-09-29: all blue, as SMRPG). v2 made it
big (Michael: "a bit puny"): ~2x its hitbox's thickness in glow, ~1x in core, ~1.45x its length at three stars
(fx/scalemeasure.py; the cast's big charged shots glow 1.7-3.1x theirs).

Joints: 0 root; 3 the up throw's star (below); 1 trail (the body ribbon, from the nose at z = 0 back along -Z, fading out at its tail); 2 head (the
round cap and a flare, unstretched; every state's joint animation spins the flare about X). The ribbons lie in the
joints' YZ plane, which the root's quarter turn puts in the stage's plane, facing the camera.
    spec(out_dir) -> dict for articles.py (writes the textures into out_dir)
"""
import math, os

import numpy as np
from PIL import Image

LENGTH = 17.0          # the trail at scale 1; the article's ext +4 caps the stretch (articles.py). v2 (Michael: "a bit
                       # puny"): 12 -> 17, drawn ~1.4x its hitboxes' length (the hitboxes' spacing is the joint's, not this)
WIDTH = 10.0           # the body's half-width at three stars. v2: 4.8 -> 10, so the full Beam's glow is ~15 across (2x its
                       # hitbox's 7.6) and its white-cyan core ~7.8 (1x), inside the cast's own margins (projects/geno/fx/
                       # scalemeasure.py: Samus's full Charge Shot glows 3.1x its hitbox, its core 1.3x; Shadow Ball 1.7x).
                       # The item code steps it by level: 0.45, 0.70, 1 (itgeno.c `vis`, Michael: thickness is the level cue)
FLARE = 6.0            # the flare's half-width (v2: 3.2)
SPIN_FRAMES = 20       # one turn of the flare
CORE, RIM, BLUE = (1.0, 1.0, 1.0), (0.55, 0.92, 1.0), (0.18, 0.45, 1.0)


def _profile(p):
    """Across the beam, p = 0 at the centre to 1 at the edge: (rgb, alpha). A white core, a thin cyan rim, then the blue
    glow falling off softly (the SNES frames: core ~0.3 of the half-width, rim, glow). (A second, wider additive ribbon
    for bloom left a hard edge beside the cap and washed the blue out: dropped.)"""
    def mix(a, b, t):
        t = np.clip(t, 0, 1)[..., None]
        return np.asarray(a) * (1 - t) + np.asarray(b) * t
    rgb = np.where((p < 0.20)[..., None], np.asarray(CORE), mix(RIM, BLUE, (p - 0.30) / 0.15))
    rgb = np.where(((p >= 0.20) & (p < 0.30))[..., None], mix(CORE, RIM, (p - 0.20) / 0.10), rgb)
    alpha = np.where(p < 0.40, 1.0, np.clip((1.0 - p) / 0.60, 0, 1) ** 1.2)      # v2: a wider blue glow round the core
    return rgb, alpha


def _rgba(rgb, alpha):
    return Image.fromarray(np.dstack([(np.clip(rgb, 0, 1) * 255).astype(np.uint8),
                                      (np.clip(alpha, 0, 1) * 255).astype(np.uint8)]), 'RGBA')


def body_texture(n=64):
    """x runs along the beam (0 the nose, right the tail), y across it. The tail narrows its core and fades out."""
    u = np.linspace(0, 1, n)[None, :].repeat(n, 0)
    v = np.linspace(-1, 1, n)[:, None].repeat(n, 1)
    p = np.abs(v) * (1.0 + 0.5 * np.clip((u - 0.3) / 0.7, 0, 1))
    rgb, a = _profile(p)
    fade = np.clip(1.0 - (u - 0.62) / 0.38, 0, 1) ** 1.3        # solid to ~12 units, the glow tail on to ~19
    ramp = np.clip(u / 0.14, 0, 1); ramp = ramp * ramp * (3 - 2 * ramp)   # fades in under the cap: no seam at the nose
    return _rgba(rgb, a * fade * ramp)


def cap_texture(n=64):
    """The round end: the same profile, radially."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    rgb, a = _profile(np.hypot(xx - c, yy - c) / c)
    return _rgba(rgb, a)


def flare_texture(n=64):
    """A white flare with four soft rays over the cap, spun by the animation."""
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    dx, dy = (xx - c) / c, (yy - c) / c
    r = np.hypot(dx, dy)
    rays = np.clip(1.0 - np.minimum(np.abs(dx), np.abs(dy)) / 0.06, 0, 1) * np.clip(1.0 - r, 0, 1) ** 1.2
    core = np.clip(1.0 - r / 0.25, 0, 1)
    a = np.clip(rays + core, 0, 1)
    i = np.ones_like(a)
    return Image.fromarray(np.dstack([(i * 255).astype(np.uint8)] * 3 + [(a * 255).astype(np.uint8)]), 'RGBA')


def _quad(z0, z1, w, u0=0.0, u1=1.0, col=(1, 1, 1), a=1.0):
    """A ribbon in the YZ plane from z0 to z1, half-width w: u along it (z0 -> z1), v across (-w -> +w)."""
    p = [(0, -w, z0, u0, 1), (0, w, z0, u0, 0), (0, w, z1, u1, 0), (0, -w, z1, u1, 1)]
    return [[x, y, z, col[0], col[1], col[2], a, u, v] for i in (0, 1, 2, 0, 2, 3) for x, y, z, u, v in [p[i]]]


def _square(s, col=(1, 1, 1), a=1.0, turn=0.0):
    """A square of half-width s in the YZ plane, turned about X."""
    c, n = math.cos(turn), math.sin(turn)
    p = [(-s, -s, 0, 1), (s, -s, 1, 1), (s, s, 1, 0), (-s, s, 0, 0)]
    out = []
    for i in (0, 1, 2, 0, 2, 3):
        y, z, u, v = p[i]
        out.append([0, y * c - z * n, y * n + z * c, col[0], col[1], col[2], a, u, v])
    return out


# ---- the up throw's Star Gun stars (the article's state 3, geno-fx): SMRPG's Star Gun fires streams of small gold stars
# (the demo's Geno weapon attack, ~/games/melee/sandbox/geno-fx/fx/refboard/stargun_frames.png). Joint 3: a gold star with
# a white highlight and a soft glow, facing the camera and spinning (RBILLBOARD, its own rotation about Z); the item
# code shows it only in state 3 and hides the Beam's trail and head there (and the star in the Beam's states), and
# drops a sparkle trail behind it (efge.py THROW_STAR_TRAIL)
STAR_R = 2.6            # the star's tip radius (its hitbox's is 6, Fox's throw lasers' size; the glow pads it)
STAR_GLOW = 5.0
STAR_SPIN = 12          # frames a turn


def throwstar_texture(n=64):
    """A plump gold star (SMRPG's), a white highlight top left, an orange rim."""
    ss = 4
    big = n * ss
    c = big / 2
    from PIL import ImageDraw
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = (0.96 if k % 2 == 0 else 0.5) * c
        pts.append((c + rr * math.cos(a), c + 2 * ss + rr * math.sin(a)))
    mask = Image.new('L', (big, big), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    inner = Image.new('L', (big, big), 0)
    ImageDraw.Draw(inner).polygon([(c + (x - c) * 0.8, c + 2 * ss + (y - c - 2 * ss) * 0.8) for x, y in pts], fill=255)
    m = np.asarray(mask, np.float32) / 255; mi = np.asarray(inner, np.float32) / 255
    yy, xx = np.mgrid[0:big, 0:big].astype(np.float32)
    hl = np.clip(1.0 - np.hypot(xx - c * 0.8, yy - c * 0.78) / (c * 0.45), 0, 1)
    rgb = np.asarray((0.95, 0.5, 0.05)) * (1 - mi[..., None]) + np.asarray((1.0, 0.86, 0.15)) * mi[..., None]
    rgb = rgb * (1 - hl[..., None] * mi[..., None]) + np.asarray((1.0, 1.0, 0.85)) * (hl[..., None] * mi[..., None])
    img = Image.fromarray(np.dstack([(np.clip(rgb, 0, 1) * 255).astype(np.uint8), (m * 255).astype(np.uint8)]), 'RGBA')
    return img.resize((n, n), Image.LANCZOS)


def throwglow_texture(n=32):
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot(xx - c, yy - c) / c
    a = np.clip(1.0 - r, 0, 1) ** 2
    return Image.fromarray(np.dstack([np.full((n, n), 255, np.uint8), np.full((n, n), 220, np.uint8),
                                      np.full((n, n), 90, np.uint8), (a * 255).astype(np.uint8)]), 'RGBA')


def spec(out_dir, states=4):
    os.makedirs(out_dir, exist_ok=True)
    body_texture().save(os.path.join(out_dir, 'body.png'))
    cap_texture().save(os.path.join(out_dir, 'cap.png'))
    flare_texture().save(os.path.join(out_dir, 'flare.png'))
    meshes = [
        dict(joint=1, blend='xlu', alpha=1.0, texture='body.png', tex_fmt='RGBA8', tris=_quad(0.0, -LENGTH, WIDTH)),
        dict(joint=2, blend='xlu', alpha=1.0, texture='cap.png', tex_fmt='RGBA8', tris=_square(WIDTH)),
        dict(joint=2, blend='add', alpha=0.9, texture='flare.png', tex_fmt='IA8', tris=_square(FLARE, turn=math.pi / 4)),
    ]
    throwstar_texture().save(os.path.join(out_dir, 'throwstar.png'))
    throwglow_texture().save(os.path.join(out_dir, 'throwglow.png'))
    meshes += [dict(joint=3, blend='add', alpha=0.6, texture='throwglow.png', tex_fmt='RGBA8', tris=_xy_square(STAR_GLOW)),
               dict(joint=3, blend='xlu', alpha=1.0, texture='throwstar.png', tex_fmt='RGBA8', tris=_xy_square(STAR_R))]
    spin = dict(joint=2, track='ROTX', end=SPIN_FRAMES, loop=True, keys=[[0, 0.0], [SPIN_FRAMES, 2 * math.pi]])
    star_spin = dict(joint=3, track='ROTZ', end=STAR_SPIN, loop=True, keys=[[0, 0.0], [STAR_SPIN, -2 * math.pi]])
    return dict(dir=out_dir,
                joints=[dict(parent=-1), dict(parent=0), dict(parent=0), dict(parent=0, flags=['RBILLBOARD'])],
                meshes=meshes,
                states=[dict(tracks=[spin]) for _ in range(states - 1)] + [dict(tracks=[star_spin])])


def _xy_square(s):
    """A square in the joint's XY plane (a camera-facing joint's), UVs 0..1."""
    p = [(-s, -s, 0, 1), (s, -s, 1, 1), (s, s, 1, 0), (-s, s, 0, 0)]
    return [[x, y, 0, 1, 1, 1, 1, u, v] for i in (0, 1, 2, 0, 2, 3) for x, y, u, v in [p[i]]]
