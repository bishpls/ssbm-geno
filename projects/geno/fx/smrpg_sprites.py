"""Super Mario RPG's battle sprites as reference images (local only: the output is ROM-derived, never commit it).

Reads the smrpgpatchbuilder disassembly of the sprites (~/games/smrpg/ext/smrpgpatchbuilder/shell_sfc_sprites: every
sprite's molds as 16x16 tiles of SNES 4bpp 8x8 subtiles, and its animation sequences) and Michael's ROM for the palettes
(15 BGR555 colours at 0x253000 + 30 * (palette id + row)), and draws each mold and each sequence.
    .venv/bin/python projects/geno/fx/smrpg_sprites.py OUTDIR ID[,ID...] [--scale 3]
writes OUTDIR/spr<ID>_molds.png (every mold, labelled) and spr<ID>_seq<N>.png (a sequence as a strip, frame durations).
"""
import importlib.util, os, sys

from PIL import Image, ImageDraw

EXT = os.path.expanduser('~/games/smrpg/ext/smrpgpatchbuilder')
ROM = os.path.expanduser('~/games/smrpg/smrpg_usa.sfc')
PAL = 0x253000
sys.path.insert(0, os.path.join(EXT, 'src'))


def load(sid):
    path = os.path.join(EXT, 'shell_sfc_sprites', 'objects', f'sprite_{sid}.py')
    spec = importlib.util.spec_from_file_location(f'spr{sid}', path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    name = open(path).readline().strip('# \n')
    return m.sprite, name


def palette(rom, pid, row):
    o = PAL + 30 * (pid + row)
    cols = [(0, 0, 0, 0)]
    for i in range(15):
        v = rom[o + 2 * i] | rom[o + 2 * i + 1] << 8
        cols.append(((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31, 255))
    return cols


def subtile(b, pal):
    im = Image.new('RGBA', (8, 8))
    px = im.load()
    for r in range(8):
        p0, p1, p2, p3 = b[2 * r], b[2 * r + 1], b[16 + 2 * r], b[17 + 2 * r]
        for x in range(8):
            s = 7 - x
            c = (p0 >> s & 1) | (p1 >> s & 1) << 1 | (p2 >> s & 1) << 2 | (p3 >> s & 1) << 3
            px[x, r] = pal[c]
    return im


def mold_image(mold, pal):
    canvas = Image.new('RGBA', (288, 288))
    for t in mold.tiles:
        tile = Image.new('RGBA', (16, 16))
        for i, b in enumerate(t.subtile_bytes):
            if b:
                tile.alpha_composite(subtile(b, pal), ((i % 2) * 8, (i // 2) * 8))
        if t.mirror:
            tile = tile.transpose(Image.FLIP_LEFT_RIGHT)
        if t.invert:
            tile = tile.transpose(Image.FLIP_TOP_BOTTOM)
        canvas.alpha_composite(tile, (t.x + 16, t.y + 16))
    return canvas


def main():
    out, ids = sys.argv[1], [int(x) for x in sys.argv[2].split(',')]
    scale = int(sys.argv[sys.argv.index('--scale') + 1]) if '--scale' in sys.argv else 3
    row = int(sys.argv[sys.argv.index('--row') + 1]) if '--row' in sys.argv else None
    rom = open(ROM, 'rb').read()
    os.makedirs(out, exist_ok=True)
    for sid in ids:
        spr, name = load(sid)
        pal = palette(rom, spr.palette_id, spr.palette_offset if row is None else row)
        molds = [mold_image(m, pal) for m in spr.animation.properties.molds]
        boxes = [m.getbbox() for m in molds if m.getbbox()]
        if not boxes:
            print(sid, name, 'empty'); continue
        x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes); x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
        cw, ch = (x1 - x0) * scale, (y1 - y0) * scale
        def cell(m):
            c = Image.new('RGBA', (cw, ch), (24, 24, 32, 255))
            c.alpha_composite(m.crop((x0, y0, x1, y1)).resize((cw, ch), Image.NEAREST))
            return c
        cols = min(len(molds), 8)
        sheet = Image.new('RGBA', (cols * (cw + 4), ((len(molds) + cols - 1) // cols) * (ch + 14) + 14), (0, 0, 0, 255))
        d = ImageDraw.Draw(sheet); d.text((2, 1), f'{name} (palette {spr.palette_id}+{spr.palette_offset})', fill=(255, 255, 0))
        for i, m in enumerate(molds):
            x, y = (i % cols) * (cw + 4), 14 + (i // cols) * (ch + 14)
            sheet.paste(cell(m), (x, y + 12)); d.text((x + 2, y), f'mold {i}', fill=(200, 200, 200))
        sheet.convert('RGB').save(os.path.join(out, f'spr{sid:04d}_molds.png'))
        for si, seq in enumerate(spr.animation.properties.sequences):
            fr = seq.frames
            if not fr:
                continue
            strip = Image.new('RGBA', (len(fr) * (cw + 4), ch + 14), (0, 0, 0, 255)); d = ImageDraw.Draw(strip)
            for i, f in enumerate(fr):
                if f.mold_id < len(molds): strip.paste(cell(molds[f.mold_id]), (i * (cw + 4), 14))
                d.text((i * (cw + 4) + 2, 1), f'm{f.mold_id} x{f.duration}', fill=(200, 200, 200))
            strip.convert('RGB').save(os.path.join(out, f'spr{sid:04d}_seq{si}.png'))
        print(sid, name, len(molds), 'molds', len(spr.animation.properties.sequences), 'sequences')


if __name__ == '__main__':
    main()
