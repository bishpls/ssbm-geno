"""ingame_board.py: in-game review crops of Geno's production model (Gate 1d), from runs rendered in a Melee sandbox with
the cast_look and model_look directors. Game renders stay local: the board goes to ~/games/melee/work/art/model/boards.

  python ingame_board.py RUNS_DIR TAG [OUT.png] [--before TAG0]   # expects TAG_feet, TAG_face, TAG_body, TAG_shield runs
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

RUNS = os.path.expanduser(sys.argv[1]); TAG = sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else os.path.expanduser(
    '~/games/melee/work/art/model/boards/geno_ingame_1d.png')
BG = (236, 236, 240); INK = (30, 30, 38); MUTE = (120, 120, 132)
FONT = os.path.expanduser('~/animation-pipeline/engine/fonts/Archivo.ttf')


def font(sz):
    try: return ImageFont.truetype(FONT, sz)
    except Exception: return ImageFont.load_default()


def frame(run, k, crop=None):
    p = os.path.join(RUNS, f'{TAG}_{run}', f'f{k:05d}.png')
    if not os.path.exists(p): return None
    im = Image.open(p).convert('RGB')
    return im.crop(crop) if crop else im


# (label, [(run, frame, crop)]): the orbits: cast_look side 0-79, 3/4 80-139, front-ish 140-199; model_look idle side 0-69,
# idle back-3/4 70-139, shield side 140-219, shield back-3/4 220-299
ROWS = [
    ('beside Mario at the feet: side, 3/4 (cast_look)', [('feet', 60, None), ('feet', 120, None)]),
    ('idle and shield, at the feet: idle side, idle back 3/4, shield side, shield back 3/4 (model_look)',
     [('shield', 40, (0, 300, 1280, 1056)), ('shield', 120, (0, 300, 1280, 1056)), ('shield', 200, (0, 300, 1280, 1056)),
      ('shield', 285, (0, 300, 1280, 1056))]),
    ('the nose: profile and head-on (CAST_AT 11, CAST_DIST 20)', [('face', 40, (0, 0, 900, 1056)), ('face', 120, (200, 0, 1100, 1056))]),
    ('full body: side, 3/4 (CAST_DIST 40)', [('body', 60, (0, 0, 760, 1056)), ('body', 120, (0, 0, 760, 1056))]),
]
H = 560
rows = []
for lab, items in ROWS:
    ims = [frame(r, k, c) for r, k, c in items]
    ims = [im.resize((int(im.width * H / im.height), H), Image.LANCZOS) for im in ims if im is not None]
    rows.append((lab, ims))
W = max(sum(i.width + 12 for i in ims) for _, ims in rows) + 30
out = Image.new('RGB', (W, 110 + len(rows) * (H + 46)), BG); d = ImageDraw.Draw(out)
d.text((24, 20), 'Geno Gate 1d in game (Final Destination, the game\'s lights), beside Mario', font=font(32), fill=INK)
d.text((24, 62), 'rendered in the geno-model sandbox (Dolphin, 2x); game renders, local only', font=font(18), fill=MUTE)
y = 110
for lab, ims in rows:
    d.text((24, y), lab, font=font(18), fill=MUTE)
    x = 20
    for im in ims:
        out.paste(im, (x, y + 26)); x += im.width + 12
    y += H + 46
out.save(OUT)
print('wrote', OUT)
