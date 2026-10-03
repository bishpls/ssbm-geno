"""SMRPG's Forest Maze as reference (local only: the output is ROM-derived, never commit it).
How: the title screen's attract demo plays two Forest Maze scenes (R257, the fight at Bowyer's pad, ~frame 4400-4750;
R260, Mario jumping on Wiggler, ~6350-6550). Mesen2's test runner plays it with no input (smrpg/drive_fm.lua under
$MELEE_WORK/stage), screenshots it, and dumps VRAM and CGRAM at chosen frames, so the game's own decompressor has
unpacked the area's tiles and palettes. This script decodes those dumps:
  - palettes.png: CGRAM's 256 BGR555 colours, one row per 16-colour palette (rows 0-7 background, 8-15 sprites);
  - tiles_<frame>_p<N>.png: VRAM's first 1024 4bpp 8x8 tiles drawn in background palette N (the tilemap's per-tile
    palette isn't dumped, so each sheet shows every tile in one palette; the forest's tiles read in their own);
  - motif crops from the screens at 3x.
    .venv/bin/python projects/geno/stage/smrpg_forest.py [DIR]      # DIR defaults to $MELEE_WORK/stage/smrpg
"""
import os, sys
import numpy as np
from PIL import Image

D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work')), 'stage', 'smrpg')


def cgram(path):
    b = open(path, 'rb').read()
    v = np.frombuffer(b, '<u2')
    r, g, bl = (v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31
    return np.stack([r, g, bl], 1).astype(np.uint8)            # (256, 3)


def tiles4(vram, n=1024):
    """-> (n, 8, 8) colour indices of 4bpp SNES tiles (planes 0/1 interleaved per row, then planes 2/3 at +16)."""
    out = np.zeros((n, 8, 8), np.uint8)
    for t in range(n):
        o = t * 32
        for y in range(8):
            p0, p1, p2, p3 = vram[o + 2 * y], vram[o + 2 * y + 1], vram[o + 16 + 2 * y], vram[o + 17 + 2 * y]
            for x in range(8):
                bit = 7 - x
                out[t, y, x] = (p0 >> bit & 1) | (p1 >> bit & 1) << 1 | (p2 >> bit & 1) << 2 | (p3 >> bit & 1) << 3
    return out


def main():
    os.makedirs(os.path.join(D, 'board'), exist_ok=True)
    dumps = sorted(f[5:11] for f in os.listdir(D) if f.startswith('vram_'))
    for fr in dumps:
        pal = cgram(os.path.join(D, f'cgram_{fr}.bin'))
        sw = np.repeat(np.repeat(pal.reshape(16, 16, 3), 16, 0), 16, 1)
        Image.fromarray(sw).save(os.path.join(D, 'board', f'palettes_{fr}.png'))
        t = tiles4(open(os.path.join(D, f'vram_{fr}.bin'), 'rb').read())
        for p in range(8):
            cols = pal[p * 16:(p + 1) * 16]
            img = cols[t]                                      # (1024, 8, 8, 3)
            sheet = img.reshape(32, 32, 8, 8, 3).transpose(0, 2, 1, 3, 4).reshape(256, 256, 3)
            Image.fromarray(sheet).resize((512, 512), Image.NEAREST).save(os.path.join(D, 'board', f'tiles_{fr}_p{p}.png'))
        print('decoded', fr)
    # the screens and motif crops (3x)
    for fr, crops in (('004560', [(0, 0, 256, 224)]), ('006450', [(0, 0, 256, 224)])):
        s = Image.open(os.path.join(D, f'shot_{fr}.png')).convert('RGB')
        s.resize((768, 672), Image.NEAREST).save(os.path.join(D, 'board', f'screen_{fr}.png'))


if __name__ == '__main__':
    main()
