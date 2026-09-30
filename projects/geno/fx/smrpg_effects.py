"""Super Mario RPG's battle effects (the background-layer animations Lazy Shell's Effects editor shows: the Geno Whirl
disc, the five Geno Beam colours, ...) as reference images. Local only: the output is ROM-derived, never commit it.

The format, ported from Lazy Shell (~/games/smrpg/ext/LAZYSHELL-UPDATED: Effect.cs, E_Animation.cs, E_Tileset.cs,
E_Mold.cs): effect i is 4 bytes at 0x251000 (palette row, animation packet, x, y); packet p's 24-bit pointer is at
0x252C00 + 3p. A packet holds its graphics (4bpp, or 2bpp when the codec is 1), 8 palettes of 16 BGR555 colours, a
tileset of 16x16 tiles (four 8x8 subtiles each, laid out as a 16-wide tilemap), molds (width x height tile grids,
run-length packed: FE value count) and sequences (duration, mold pairs).
    .venv/bin/python projects/geno/fx/smrpg_effects.py OUTDIR 32,86,87,88,89,90 [--scale 2]
writes OUTDIR/ef<N>_molds.png and ef<N>_seq<K>.png.
"""
import os, sys

import numpy as np
from PIL import Image, ImageDraw

ROM = os.path.expanduser('~/games/smrpg/smrpg_usa.sfc')
NAMES = os.path.expanduser('~/games/smrpg/ext/smrpgpatchbuilder/config/battle_effect_names.input')


def u16(b, o): return b[o] | b[o + 1] << 8


def subtile(gfx, n, bpp, pal, status):
    size = 8 * bpp
    o = n * size
    if o + size > len(gfx):
        o = 0
    px = np.zeros((8, 8), np.uint8)
    for r in range(8):
        planes = [gfx[o + 2 * r], gfx[o + 2 * r + 1]]
        if bpp == 4:
            planes += [gfx[o + 16 + 2 * r], gfx[o + 17 + 2 * r]]
        for x in range(8):
            s = 7 - x
            px[r, x] = sum(((p >> s) & 1) << k for k, p in enumerate(planes))
    if status & 0x40: px = px[:, ::-1]
    if status & 0x80: px = px[::-1, :]
    rgba = np.zeros((8, 8, 4), np.uint8)
    for v in range(1, 16):
        m = px == v
        if m.any():
            rgba[m] = pal[v]
    return rgba


def decode(rom, idx):
    eo = 0x251000 + idx * 4
    pal_row, packet = rom[eo] & 7, rom[eo + 1]
    ao = (rom[0x252C00 + 3 * packet] | rom[0x252C01 + 3 * packet] << 8 | rom[0x252C02 + 3 * packet] << 16) - 0xC00000
    n = u16(rom, ao)
    buf = rom[ao:ao + n]
    gfx_p, pal_p, seq_p, mold_p = u16(buf, 2), u16(buf, 4), u16(buf, 6), u16(buf, 8)
    w, h, codec, tset_p = buf[12], buf[13], u16(buf, 14), u16(buf, 16)
    bpp = 2 if codec == 1 else 4
    gfx = buf[gfx_p:pal_p]
    pals = []
    for i in range(8):
        cols = [(0, 0, 0, 0)]
        for a in range(1, 16):
            c = u16(buf, pal_p + 32 * i + 2 * a) if pal_p + 32 * i + 2 * a + 1 < len(buf) else 0
            cols.append(((c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8, 255))
        pals.append(cols)
    pal = pals[pal_row]
    tsb = buf[tset_p:seq_p]
    tiles = []
    off = 0
    for i in range(64):
        if i > 0 and i % 8 == 0:
            off += 32
        if off + 1 >= len(tsb) or u16(tsb, off) == 0xFFFF:
            break
        t = np.zeros((16, 16, 4), np.uint8)
        for z, (dx, dy, o2) in enumerate(((0, 0, off), (8, 0, off + 2), (0, 8, off + 32), (8, 8, off + 34))):
            if o2 + 1 >= len(tsb):
                continue
            num = u16(tsb, o2) & 0x3FF
            t[dy:dy + 8, dx:dx + 8] = subtile(gfx, num, bpp, pal, tsb[o2 + 1])
        tiles.append(t)
        off += 4
    # molds
    molds = []
    o = mold_p
    ptrs = []
    while o + 1 < len(buf) and u16(buf, o) != 0:
        ptrs.append(u16(buf, o)); o += 2
    for k, p in enumerate(ptrs):
        if p == 0xFFFF:
            molds.append(None); continue
        end = next((q for q in ptrs[k + 1:] if q != 0xFFFF), len(buf))
        src = buf[p:end]
        dst = bytearray([0xFF] * 256)
        si = di = 0
        while si < len(src) and di < 256:
            if src[si] == 0xFE and si + 2 < len(src):
                for _ in range(src[si + 2]):
                    if di < 256: dst[di] = src[si + 1]; di += 1
                si += 3
            else:
                dst[di] = src[si]; di += 1; si += 1
        img = np.zeros((h * 16, w * 16, 4), np.uint8)
        for y in range(h):
            for x in range(w):
                v = dst[y * w + x] if y * w + x < 256 else 0xFF
                if v == 0xFF or (v & 0x3F) >= len(tiles):
                    continue
                t = tiles[v & 0x3F]
                if v & 0x40: t = t[:, ::-1]
                if v & 0x80: t = t[::-1, :]
                img[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16] = t
        molds.append(img)
    seqs = []
    o = seq_p
    while o + 1 < len(buf) and u16(buf, o) != 0:
        p = u16(buf, o); fr = []
        while p != 0xFFFF and p < len(buf) and buf[p] != 0:
            fr.append((buf[p], buf[p + 1])); p += 2
        seqs.append(fr); o += 2
    return dict(w=w, h=h, bpp=bpp, molds=molds, seqs=seqs, packet=packet, pal=pal_row)


def main():
    out, ids = sys.argv[1], [int(x) for x in sys.argv[2].split(',')]
    scale = int(sys.argv[sys.argv.index('--scale') + 1]) if '--scale' in sys.argv else 2
    rom = open(ROM, 'rb').read()
    names = {i: n.strip() for i, n in enumerate(open(NAMES))} if os.path.exists(NAMES) else {}
    os.makedirs(out, exist_ok=True)
    for idx in ids:
        e = decode(rom, idx)
        name = names.get(idx, f'EF{idx:04d}')
        ms = [m for m in e['molds'] if m is not None]
        if not ms:
            print(idx, name, 'no molds'); continue
        H, W = ms[0].shape[:2]
        cw, ch = W * scale, H * scale
        def cell(m):
            c = Image.new('RGBA', (cw, ch), (12, 12, 20, 255))
            if m is not None:
                c.alpha_composite(Image.fromarray(m, 'RGBA').resize((cw, ch), Image.NEAREST))
            return c
        cols = min(len(e['molds']), 6)
        rows = (len(e['molds']) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * (cw + 4), 16 + rows * (ch + 14)), (0, 0, 0, 255)); d = ImageDraw.Draw(sheet)
        d.text((2, 2), f'{name}: packet {e["packet"]}, {e["w"]}x{e["h"]} tiles, {e["bpp"]}bpp, palette {e["pal"]}', fill=(255, 255, 0))
        for i, m in enumerate(e['molds']):
            x, y = (i % cols) * (cw + 4), 16 + (i // cols) * (ch + 14)
            sheet.paste(cell(m), (x, y + 12)); d.text((x + 2, y), f'mold {i}', fill=(200, 200, 200))
        sheet.convert('RGB').save(os.path.join(out, f'ef{idx:04d}_molds.png'))
        for k, fr in enumerate(e['seqs']):
            if not fr:
                continue
            fr = fr[:12]
            st = Image.new('RGBA', (len(fr) * (cw + 4), ch + 14), (0, 0, 0, 255)); d = ImageDraw.Draw(st)
            for i, (dur, mo) in enumerate(fr):
                st.paste(cell(e['molds'][mo] if mo < len(e['molds']) else None), (i * (cw + 4), 14))
                d.text((i * (cw + 4) + 2, 1), f'm{mo} x{dur}', fill=(200, 200, 200))
            st.convert('RGB').save(os.path.join(out, f'ef{idx:04d}_seq{k}.png'))
        print(idx, name, len(e['molds']), 'molds', len(e['seqs']), 'sequences', f'{e["w"]}x{e["h"]}', f'{e["bpp"]}bpp')


if __name__ == '__main__':
    main()
