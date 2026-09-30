"""Geno's costumes: colour variants of the production model's textures (DESIGN.md §12 "Costumes").

    .venv/bin/python projects/geno/model/costumes.py write MODEL_DIR OUT_DIR [CODES]   # a model folder per costume
    .venv/bin/python projects/geno/model/costumes.py board MODEL_DIR OUT.png [CODES]   # swatches + recoloured textures
    .venv/bin/python projects/geno/model/costumes.py --c OUT.h                         # the decomp's costume table
    .venv/bin/python projects/geno/model/costumes.py json                              # the palette table

A costume is the production model with some textures recoloured; wood (the body, the face, the hands) and the weapon
forms never change. Each recoloured texture is split into colour families by hue (the cap's blue, the ribbon's gold, the
curls' orange, the boots' brown) and each family is moved to its costume target in OKLab: the target sets the mean
lightness, chroma and hue, and each texel keeps its offset from its family's mean, so the felt mottle, the folds and the
painted shading survive. Targets are texture colours, not screen colours: Melee's lights brighten a texture by about 1.2
on its lit side (HANDOFF §5), so judge them in game.

`write` makes OUT_DIR/<Cc>/ for every costume but the first: the glTFs and eye frames linked, geno_tex/ recoloured.
rig.py calls it when it exports the production model, and lists the folders in rig.json's model "costumes", from which
datkit fighter-build writes PlGe<Cc>.dat next to PlGeNr.dat. The textures are derived art: they stay in the work folder.
"""
import json, os, sys
import numpy as np
from PIL import Image

# ---- the costumes, in the game's order (costume 0 is the model as painted). Targets are sRGB texture colours; a key
# left out keeps the default. Keys:
#   cap     the crown and the band (blue)            ribbon  the bow emblem and its tail on the crown (gold)
#   curls   the two paper curls (orange)             cape    the capelet (blue)
#   piping  the collar's blue piping (default: cape) lining  the capelet's lining (gold)
#   collar  the collar's flaps (default: lining)     clasp   the gold rope and brass grommets
#   boots   the boots' uppers and cuffs (brown)      sole    the boots' tan soles
COSTUMES = [
    dict(code='Nr', name='Geno', ref="his own colours: the blue cap and cape, the gold ribbon and lining"),
    dict(code='Re', name='Mario', ref="Mario's red cap and shirt, his cap's white badge, blue overalls, gold buttons",
         cap='#c8262a', cape='#c8262a', ribbon='#f2efe6', lining='#2f55c0', piping='#2f55c0'),
    dict(code='Gr', name='Bowser', ref="Bowser's green shell, red hair, cream belly and white horns",
         cap='#2f9a3c', cape='#2f9a3c', ribbon='#e8e2cf', curls='#e0452a', lining='#f0dc9a', collar='#f0dc9a',
         piping='#e0452a'),
    dict(code='Wh', name='Mallow', ref="Mallow (Michael's call): his off-yellow cloud body, pink hair and shoes, "
                                       "blue and white striped pants, light-blue buckle",
         cap='#ecdfa6', curls='#ff6fcf', ribbon='#ff6fcf', cape='#74bced', lining='#f4f4f0', collar='#ecdfa6',
         piping='#ff6fcf', boots='#e2509f', sole='#f4f4f0'),
    dict(code='Pi', name='Peach', ref="Princess Toadstool's pink dress, blonde hair, blue brooch, white gloves",
         cap='#f07fb0', cape='#f07fb0', ribbon='#3f78e0', curls='#f6d24a', lining='#f4f4f0', collar='#f4f4f0',
         piping='#c8407e'),
    dict(code='Bk', name='Dark', ref="the fans' dark outfit (Michael, 2026-09-29): black felt, collar and boots; red curls, "
                                     "ribbon, lining, clasp, collar piping and soles",
         cap='#2a2a34', cape='#2a2a34', ribbon='#d8302c', lining='#d8302c', collar='#2a2a34', piping='#d8302c',
         curls='#d8302c', clasp='#d8302c', boots='#2a2a34', sole='#8a2420'),
    # candidates, rendered for reviews only (GENO_COSTUMES=...): Dark's other split (the same at stock-icon size; at the
    # game's distance its brown boots read as Geno in a black cape rather than an outfit), and the first alternates
    dict(code='Bd', name='Dark (red collar, brown boots)', ref="Dark with the red on the collar's flaps and his own boots",
         cap='#2a2a34', cape='#2a2a34', ribbon='#d8302c', lining='#d8302c', collar='#d8302c', piping='#2a2a34',
         curls='#d8302c', clasp='#d8302c'),
    dict(code='Ye', name='Star', ref="Star Road: a Star Spirit's gold, with his blue moved to the trim",
         cap='#f0c03a', cape='#f0c03a', ribbon='#3a6fd8', lining='#3a6fd8', collar='#3a6fd8', piping='#f0c03a'),
]
# the costume each team plays in (the game's per-character row: red, blue, green)
TEAMS = dict(red='Re', blue='Nr', green='Gr')
# the set that ships, in the game's order (Michael, 2026-09-29: "the 5 from SMRPG are excellent", and Dark, black and
# red, for number 6: the fans' favourite). Six is Melee's maximum (Captain Falcon and Kirby have six).
SET = ['Nr', 'Re', 'Gr', 'Wh', 'Pi', 'Bk']

# ---- which families each texture holds, and which target each family takes
BLUE, GOLD, ORANGE, BROWN, TAN, CLASP = 'blue', 'gold', 'orange', 'brown', 'tan', 'clasp'
TEXTURES = {
    'crown': {BLUE: 'cap', GOLD: 'ribbon'},
    'band': {BLUE: 'cap'},
    'emblem': {GOLD: 'ribbon'},
    'cape': {BLUE: 'cape'},
    'collar': {BLUE: 'piping'},
    'collarin': {GOLD: 'collar', BLUE: 'piping'},
    'lining': {GOLD: 'lining'},
    'clasp': {CLASP: 'clasp'},
    'curls': {ORANGE: 'curls'},
    'boot': {BROWN: 'boots', TAN: 'sole'},
    'cuff': {BROWN: 'boots'},
    # Geno Flash's cannon (geno_cannon.py): its blue follows the capelet (SMRPG's barrel is his capelet's blue, down to
    # the points of its hem); the brass, the knob and the carriage (wood, brass, iron) never change
    'fcbarrel': {BLUE: 'cape'},
}
# textures that follow a family's target without shaping its reference (the family means every costume moves by): the
# cannon's barrel joined the set after the costumes were judged in game, and must not shift the capelet's or cap's recolour
REF_SKIP = {'fcbarrel'}
DEFAULTS = dict(piping='cape', collar='lining')


# ---- OKLab (Björn Ottosson's), on arrays of sRGB in 0..1
def _lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def _gam(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def to_oklab(rgb):
    r, g, b = np.moveaxis(_lin(rgb), -1, 0)
    l = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return np.stack([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                     1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                     0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s], -1)


def from_oklab(lab):
    L, a, b = np.moveaxis(lab, -1, 0)
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = np.stack([4.0767416621 * l - 3.3077063380 * m + 0.2309699292 * s,
                    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                    -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s], -1)
    return np.clip(_gam(np.clip(rgb, 0, 1)), 0, 1)


def lch(lab):
    return lab[..., 0], np.hypot(lab[..., 1], lab[..., 2]), np.arctan2(lab[..., 2], lab[..., 1])


def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255


def load(path):
    return np.array(Image.open(path).convert('RGBA')).astype(np.float64) / 255


# ---- families: a texel's family by its OKLab hue (degrees) and lightness
def classify(name, lab):
    L, C, h = lch(lab)
    deg = np.degrees(h) % 360
    fams = TEXTURES[name]
    out = np.full(L.shape, '', object)
    if BLUE in fams: out[(deg > 200) & (deg < 300) & (C > 0.04)] = BLUE
    if GOLD in fams: out[(deg > 60) & (deg < 120) & (C > 0.06)] = GOLD
    if ORANGE in fams: out[(deg > 20) & (deg < 80) & (C > 0.06)] = ORANGE
    if CLASP in fams: out[:] = CLASP
    if BROWN in fams:
        warm = (deg > 20) & (deg < 110)
        out[warm] = BROWN
        if TAN in fams: out[warm & (L > 0.46)] = TAN
    return out


def reference(model_dir):
    """Each family's mean (L, C, hue) over the default textures: every texture moves by the same offset, so the
    differences between them (the collar a shade lighter than the cape) survive."""
    acc = {}
    for name in TEXTURES:
        if name in REF_SKIP: continue
        lab = to_oklab(load(os.path.join(model_dir, 'geno_tex', name + '.png'))[..., :3])
        fam = classify(name, lab)
        for f in set(fam.ravel()) - {''}:
            acc.setdefault(f, []).append(lab[fam == f])
    ref = {}
    for f, parts in acc.items():
        p = np.concatenate(parts)
        L, C, h = lch(p)
        ref[f] = (L.mean(), C.mean(), np.arctan2(np.sin(h).mean(), np.cos(h).mean()))
    return ref


def target(cos, key):
    while key not in cos and key in DEFAULTS: key = DEFAULTS[key]
    return cos.get(key)


def recolour(img, name, cos, ref):
    """One texture in one costume: every family with a target moves to it; the rest stays as painted."""
    rgb, a = img[..., :3], img[..., 3:]
    lab = to_oklab(rgb)
    fam = classify(name, lab)
    out = lab.copy()
    L, C, h = lch(lab)
    for f, key in TEXTURES[name].items():
        t = target(cos, key)
        if t is None: continue
        m = fam == f
        if not m.any(): continue
        tl = to_oklab(hexrgb(t))
        Lt, Ct, ht = float(tl[0]), float(np.hypot(tl[1], tl[2])), float(np.arctan2(tl[2], tl[1]))
        L0, C0, h0 = ref[f]
        # lightness: the target's, plus the texel's offset (compressed toward white and black, where there's no room)
        dL = L[m] - L0
        room = np.where(dL > 0, (1.0 - Lt) / max(1.0 - L0, 1e-3), Lt / max(L0, 1e-3))
        Ln = Lt + dL * np.clip(room, 0.35, 1.0)
        # chroma relative to the family's; the hue keeps half its local wobble
        Cn = Ct * np.clip(C[m] / max(C0, 1e-3), 0, 2.0)
        dh = np.angle(np.exp(1j * (h[m] - h0)))
        hn = ht + 0.5 * dh
        out[m] = np.stack([Ln, Cn * np.cos(hn), Cn * np.sin(hn)], -1)
    return np.concatenate([from_oklab(out), a], -1)


def by_code(code):
    return next(c for c in COSTUMES if c['code'] == code)


def write(model_dir, out_dir, codes=None):
    """A model folder per costume (all but the first): links to the glTFs and to every texture that doesn't change,
    recoloured copies of the rest. Returns [{code, dir}] in costume order."""
    model_dir, out_dir = os.path.abspath(os.path.expanduser(model_dir)), os.path.abspath(out_dir)
    ref = reference(model_dir)
    res = []
    for code in (codes or SET)[1:]:
        cos = by_code(code)
        d = os.path.join(out_dir, code)
        td = os.path.join(d, 'geno_tex')
        os.makedirs(td, exist_ok=True)
        for f in os.listdir(model_dir):
            if f.endswith(('.gltf', '.bin', '.json')):
                link(os.path.join(model_dir, f), os.path.join(d, f))
        for f in os.listdir(os.path.join(model_dir, 'geno_tex')):
            src, dst = os.path.join(model_dir, 'geno_tex', f), os.path.join(td, f)
            name = f[:-4]
            if name in TEXTURES and any(target(cos, k) for k in TEXTURES[name].values()):
                if os.path.islink(dst): os.remove(dst)
                im = recolour(load(src), name, cos, ref)
                Image.fromarray((im * 255).round().astype(np.uint8), 'RGBA').save(dst)
            else:
                link(src, dst)
        res.append(dict(code=code, dir=d))
    return res


def link(src, dst):
    if os.path.islink(dst) or os.path.exists(dst):
        if os.path.islink(dst) and os.readlink(dst) == src: return
        os.remove(dst)
    os.symlink(src, dst)


def board(model_dir, out, codes=None):
    """Every costume's recoloured textures in a row (the swatches at the left), for a quick look before the game."""
    from PIL import ImageDraw
    model_dir = os.path.expanduser(model_dir)
    ref = reference(model_dir)
    names = list(TEXTURES)
    codes = codes or [c['code'] for c in COSTUMES]
    T = 96
    W, H = 150 + len(names) * (T + 6), len(codes) * (T + 22) + 20
    S = Image.new('RGB', (W, H), (40, 40, 48))
    d = ImageDraw.Draw(S)
    for x, n in enumerate(names): d.text((150 + x * (T + 6), 4), n, fill=(200, 200, 200))
    for y, code in enumerate(codes):
        cos = by_code(code)
        y0 = 20 + y * (T + 22)
        d.text((4, y0), f"{code} {cos['name']}", fill=(255, 220, 120))
        for k, key in enumerate(['cap', 'cape', 'ribbon', 'curls', 'lining', 'boots']):
            t = target(cos, key)
            if t: d.rectangle([4 + (k % 3) * 46, y0 + 16 + (k // 3) * 40, 46 + (k % 3) * 46, y0 + 52 + (k // 3) * 40], fill=t)
        for x, n in enumerate(names):
            im = load(os.path.join(model_dir, 'geno_tex', n + '.png'))
            if code != COSTUMES[0]['code']: im = recolour(im, n, cos, ref)
            t = Image.fromarray((im[..., :3] * 255).round().astype(np.uint8)).resize((T, T), Image.BILINEAR)
            S.paste(t, (150 + x * (T + 6), y0 + 16))
    S.save(out)
    return out


def export_c(path, codes=None):
    """The decomp's costume table (ftGeno/ftgeno_costumes.h): file names, symbols, the count and the team rows."""
    codes = codes or SET
    ix = {c: i for i, c in enumerate(codes)}
    names = ', '.join(f'{i}:{c} {by_code(c)["name"]}' for i, c in enumerate(codes))
    open(path, 'w').write(
        '/* generated by animation-pipeline projects/geno/model/costumes.py --c: Geno\'s costumes, in the game\'s order */\n'
        f'/* {names} */\n'
        f'#define FTGE_COSTUME_COUNT {len(codes)}\n'
        f'#define FTGE_COSTUME_RED {ix.get(TEAMS["red"], 0)}\n'
        f'#define FTGE_COSTUME_BLUE {ix.get(TEAMS["blue"], 0)}\n'
        f'#define FTGE_COSTUME_GREEN {ix.get(TEAMS["green"], 0)}\n'
        f'#define FTGE_COSTUME_STRINGS \\\n' + ' \\\n'.join(
            f'    {{ "PlGe{c}.dat", "PlyGeno5K{"" if i == 0 else c}_Share_joint", "PlyGeno5K{"" if i == 0 else c}_Share_matanim_joint" }},'
            for i, c in enumerate(codes)) + '\n')
    print('wrote', path)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == '--c':
        export_c(a[1], a[2].split(',') if len(a) > 2 else None)
    elif a[0] == 'write':
        for r in write(a[1], a[2], a[3].split(',') if len(a) > 3 else None): print(r['code'], r['dir'])
    elif a[0] == 'board':
        print(board(a[1], a[2], a[3].split(',') if len(a) > 3 else None))
    elif a[0] == 'json':
        print(json.dumps(COSTUMES, indent=1))
