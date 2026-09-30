"""Kirby's Geno hat: check a hat file against the interface Kirby's copy of Geno loads (DESIGN.md §12), install it on the
disc, or make a clearly-labelled stand-in from a vanilla Kirby cap. The game looks for PlKbCpGe.dat once at boot
(decomp ftkirbyspecialgeno.c: ftKb_SpecialNGe_HatRow); with no file, Kirby wears no hat while he holds Geno's copy.
    .venv/bin/python projects/geno/rig/kirby_hat.py build [--install] [--model DIR] [--set K=V] [--out DIR]  # Geno's cap for Kirby ->
                                                                           # $MELEE_WORK/kirby_hat/PlKbCpGe.dat (below)
    .venv/bin/python projects/geno/rig/kirby_hat.py check FILE.dat
    .venv/bin/python projects/geno/rig/kirby_hat.py install FILE.dat       # -> $MELEE_DISC/files/PlKbCpGe.dat
    .venv/bin/python projects/geno/rig/kirby_hat.py standin [Lg]           # a vanilla cap (PlKbCp<Lg>.dat) renamed, in
                                                                           # $MELEE_WORK/kirby_hat/, then install it
    .venv/bin/python projects/geno/rig/kirby_hat.py remove                 # back to no hat
Disc files never enter the repo: the stand-in is derived from your own disc into $MELEE_WORK.
"""
import json, os, shutil, struct, subprocess, sys

HAT_FILE = 'PlKbCpGe.dat'
HAT_SYMBOL = 'ftDataKirbyCopyGeno'
DISC = os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc'))
WORK = os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work'))
MAX_DOBJS = 32        # ftParts_80075650: "fighter parts model dobj num over!"
MAX_MODELS = 11       # ftParts_8007487C: "fighter parts model num over!"
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# The build (DESIGN.md §12): Geno's cap from the production model (crown, band, curls, emblem; the low model's cap),
# posed, refitted to Kirby's head and decimated in Blender (kirby_hat_model.py), textures downscaled here, then written
# as rigid meshes on Luigi's cap's joint and material by datkit's kirby-hat (HatBuild.cs). Budgets: the vanilla caps
# (datkit meshstats PlKbCpLg.dat / PlKbCpMr.dat): 360 / 332 triangles normal, 78 low, 18.2 / 14.2 KiB of CMP textures.
FIT = dict(
    kirby_centre=[0, 5.579, 0], kirby_radius=4.998,  # his rest-pose body, a sphere (fitted to PlKbNr.dat's body mesh)
    scale=1.85,           # Geno's head is 2.56 in radius, Kirby's 5.0 (1.72 perches it like a beanie; 2.0 covers his eyes)
    tilt=26,              # degrees the band leans back (Luigi's band: y 9.43 in front over the eyes, 5.65 behind)
    inset=0.15,           # the band's lower edge this far inside his head, so no gap shows
    ring_band=0.35,       # the band's lower edge: vertices within this of its lowest point
    droop=12,             # degrees per joint of the point's chain (CapMidN, CapTipN, CapTip2N, CapTip3N): it hangs
    high={'cap_crown': 140, 'cap_band': 72, 'curls': 100, 'emblem': 48},
    low={'low_cap': 0, 'curls': 36},                  # 0 keeps the source (Geno's low cap: 40); curls: one layer
    symmetric=['cap_crown', 'cap_band', 'emblem'],
)
TEX = {'crown': (128, 64), 'band': (128, 32), 'emblem': (64, 32), 'curls': (16, 64)}   # from 256x128, 256x64, 128x64, 32x128


class Dat:
    """An HSD archive: header, data, relocation table, root and reference tables, string table."""
    def __init__(self, raw):
        self.raw = bytearray(raw)
        self.fsize, self.dsize, self.nrel, self.nroot, self.nref = struct.unpack('>5I', raw[:20])
        self.d = self.raw[0x20:0x20 + self.dsize]
        ro = 0x20 + self.dsize
        self.rel = set(struct.unpack('>%dI' % self.nrel, raw[ro:ro + 4 * self.nrel]))
        self.tab = ro + 4 * self.nrel                   # root table, then reference table: (offset, string offset)
        self.strs = self.tab + 8 * (self.nroot + self.nref)
        self.syms = []
        for i in range(self.nroot + self.nref):
            off, so = struct.unpack('>2I', raw[self.tab + 8 * i:self.tab + 8 * i + 8])
            end = raw.index(b'\0', self.strs + so)
            self.syms.append([off, raw[self.strs + so:end].decode()])

    def roots(self):
        return {name: off for off, name in self.syms[:self.nroot]}

    def u32(self, o): return struct.unpack('>I', self.d[o:o + 4])[0]
    def f32(self, o): return struct.unpack('>f', self.d[o:o + 4])[0]
    def ptr(self, o): return self.u32(o) if o in self.rel else None

    def renamed(self, old, new):
        """The file with root `old` renamed `new` (the string table rebuilt, so any length works)."""
        names = [new if (i < self.nroot and n == old) else n for i, (o, n) in enumerate(self.syms)]
        head = self.raw[:self.tab]
        table, strings = bytearray(), bytearray()
        for (off, _), n in zip(self.syms, names):
            table += struct.pack('>2I', off, len(strings)); strings += n.encode() + b'\0'
        out = head + table + strings
        struct.pack_into('>I', out, 0, len(out))
        return bytes(out)


def dobjs(d, j):
    """DObjs over a joint tree (HSD_Joint: +4 flags, +8 child, +C next, +10 DObj unless the flags say spline/ptcl)."""
    n = 0
    while j is not None:
        if not d.u32(j + 4) & 0x4000:
            p = d.ptr(j + 0x10)
            while p is not None:
                n += 1; p = d.ptr(p + 4)
        n += dobjs(d, d.ptr(j + 8))
        j = d.ptr(j + 0xC)
    return n


def check(path):
    d = Dat(open(path, 'rb').read())
    errs, notes = [], []
    r = d.roots().get(HAT_SYMBOL)
    if r is None:
        return [f'no root symbol {HAT_SYMBOL} (roots: {", ".join(d.roots())})'], notes
    joint, model_num, vis = d.ptr(r), d.u32(r + 4), d.ptr(r + 8)
    if joint is None:
        errs.append('+0: no hat joint (HSD_Joint*)')
    if not 1 <= model_num <= MAX_MODELS:
        errs.append(f'+4: model_num {model_num}, want 1 (the vanilla caps) to {MAX_MODELS}')
    if vis is None:
        errs.append('+8: no visibility table')
    else:
        row = [d.ptr(vis + 4 * k) for k in range(4)]
        if row[0] is None:
            errs.append('+8: the visibility row has no normal-model lookup ([0])')
        notes.append('visibility row: normal %s, low detail %s, [2] %s, [3] %s' % tuple(
            'yes' if p is not None else '-' for p in row))
    if joint is not None:
        n = dobjs(d, joint)
        (errs if n > MAX_DOBJS else notes).append(f'{n} DObjs (at most {MAX_DOBJS})')
        notes.append('root joint translate %.2f %.2f %.2f (the vanilla caps: 0 5.62 0; drawn with the matrix of Kirby\'s '
                     'joint 6, the one every vanilla cap rides)' % tuple(d.f32(joint + 0x2C + 4 * k) for k in range(3)))
    extra = [k for k in range(5) if d.ptr(r + 0xC + 4 * k) is not None]
    if extra:
        notes.append(f'+0xC: extras in slots {extra} (unused: Geno\'s copy fires his own articles from PlGe.dat)')
    return errs, notes


def install(path):
    errs, notes = check(path)
    for n in notes: print('  ', n)
    if errs:
        sys.exit('not a Geno hat:\n  ' + '\n  '.join(errs))
    dst = os.path.join(DISC, 'files', HAT_FILE)
    shutil.copy(path, dst)
    print(f'installed {path} -> {dst} (the game reads it at boot)')


def build(a):
    from PIL import Image
    model = a[a.index('--model') + 1] if '--model' in a else os.path.join(WORK, 'art', 'model')
    out = os.path.join(WORK, 'kirby_hat'); tex = os.path.join(out, 'tex'); os.makedirs(tex, exist_ok=True)
    fitp = json.loads(json.dumps(FIT))
    for kv in (a[i + 1] for i, x in enumerate(a) if x == '--set'):          # --set scale=1.9 --set high.cap_crown=150
        k, v = kv.split('='); d = fitp
        for part in k.split('.')[:-1]: d = d[part]
        d[k.split('.')[-1]] = json.loads(v)
    if '--out' in a: out = a[a.index('--out') + 1]; tex = os.path.join(out, 'tex'); os.makedirs(tex, exist_ok=True)
    for name, size in TEX.items():
        Image.open(os.path.join(model, 'geno_tex', name + '.png')).convert('RGB').resize(size, Image.LANCZOS).save(
            os.path.join(tex, name + '.png'))
    params = os.path.join(out, 'params.json'); json.dump(fitp, open(params, 'w'), indent=1)
    r = subprocess.run(['blender', '-b', '-P', os.path.join(REPO, 'projects/geno/rig/kirby_hat_model.py'), '--',
                        os.path.join(out, 'model'), model, tex, params], capture_output=True, text=True)
    fit = [l for l in r.stdout.splitlines() if l.startswith('FIT ')]
    if r.returncode or not fit:
        sys.exit(r.stdout[-3000:] + r.stderr[-3000:])
    fit = json.loads(fit[0][4:])
    for lod in ('high', 'low'):
        for k, v in fit[lod].items():
            print(f"  {lod:4} {k:10} {v['tris_source']:4} -> {v['tris']:4} tris   head clearance min {v['min']:6.2f} "
                  f"({v['inside']} of {v['verts']} verts inside)   y {v['lo'][1]:.2f}..{v['hi'][1]:.2f} z {v['lo'][2]:.2f}..{v['hi'][2]:.2f}")
    print('  seat', {k: [round(x, 3) for x in v] if isinstance(v, list) else v for k, v in fit['seat'].items()})
    dat = os.path.join(out, HAT_FILE)
    r = subprocess.run([os.path.join(REPO, 'tools/machinima/melee/datkit.sh'), 'kirby-hat', os.path.join(DISC, 'files', 'PlKbCpLg.dat'),
                        dat, '--high', os.path.join(out, 'model', 'hat_high.gltf'), '--low', os.path.join(out, 'model', 'hat_low.gltf'),
                        '--symbol', HAT_SYMBOL], capture_output=True, text=True)
    print(r.stdout.rstrip())
    if r.returncode:
        sys.exit(r.stderr[-3000:])
    errs, notes = check(dat)
    for n in notes: print('  ', n)
    if errs:
        sys.exit('FAIL\n  ' + '\n  '.join(errs))
    if '--install' in a:
        install(dat)


def main(a):
    if not a or a[0] not in ('build', 'check', 'install', 'standin', 'remove'):
        sys.exit(__doc__)
    if a[0] == 'build':
        build(a[1:])
    if a[0] == 'check':
        errs, notes = check(a[1])
        for n in notes: print('  ', n)
        print('OK' if not errs else 'FAIL\n  ' + '\n  '.join(errs)); sys.exit(1 if errs else 0)
    if a[0] == 'install':
        install(a[1])
    if a[0] == 'standin':
        kind = a[1] if len(a) > 1 else 'Lg'
        src = os.path.join(DISC, 'files', f'PlKbCp{kind}.dat')
        d = Dat(open(src, 'rb').read())
        old = next(iter(d.roots()))
        out_dir = os.path.join(WORK, 'kirby_hat'); os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, f'PlKbCpGe_standin_{kind}.dat')
        open(out, 'wb').write(d.renamed(old, HAT_SYMBOL))
        print(f'stand-in: {src} ({old}) -> {out} ({HAT_SYMBOL})')
        install(out)
    if a[0] == 'remove':
        dst = os.path.join(DISC, 'files', HAT_FILE)
        if os.path.exists(dst):
            os.remove(dst); print(f'removed {dst}: no hat')


if __name__ == '__main__':
    main(sys.argv[1:])
