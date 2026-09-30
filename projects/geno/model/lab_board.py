"""lab_board.py: the Gate 2 in-game boards from the sandbox runs (game renders: local only).

  python lab_board.py RUNS_DIR LAB_RUN PANEL_RUN [OUT_DIR]
Writes geno_forms_ingame.png (every weapon form on both hands, the four hand poses, the three cap poses; director/form_lab)
and geno_panels_ingame.png (the capelet's front panels through the forward and up tilts and smashes; director/panel_lab).
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rig'))
import rig

RUNS, LAB, PANEL = (os.path.expanduser(a) for a in sys.argv[1:4])
OUT = os.path.expanduser(sys.argv[4] if len(sys.argv) > 4 else '~/games/melee/work/art/model/boards')
BG = (236, 236, 240); INK = (30, 30, 38); MUTE = (120, 120, 132)
FONT = os.path.expanduser('~/animation-pipeline/engine/fonts/Archivo.ttf')


def font(sz):
    try: return ImageFont.truetype(FONT, sz)
    except Exception: return ImageFont.load_default()


def fr(run, k, crop):
    return Image.open(os.path.join(RUNS, run, f'f{k:05d}.png')).convert('RGB').crop(crop)


def board(title, sub, rows, cell_h, out):
    rows = [(lab, [(cap, im.resize((int(im.width * cell_h / im.height), cell_h), Image.LANCZOS)) for cap, im in ims]) for lab, ims in rows]
    W = max(sum(im.width + 12 for _, im in ims) for _, ims in rows) + 30
    H = 110 + len(rows) * (cell_h + 70)
    o = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(o)
    d.text((24, 20), title, font=font(32), fill=INK); d.text((24, 62), sub, font=font(18), fill=MUTE)
    y = 110
    for lab, ims in rows:
        d.text((24, y), lab, font=font(18), fill=MUTE)
        x = 20
        for cap, im in ims:
            o.paste(im, (x, y + 26)); d.text((x + 6, y + 30 + cell_h), cap, font=font(17), fill=INK); x += im.width + 12
        y += cell_h + 70
    o.save(out); print('wrote', out)


C = (190, 250, 1090, 850)         # the upper body, both hands
forms = [(f'{f}  (options {rig.FORM_ARM[f]} / {i})', fr(LAB, 21 + 30 * i + 22, C)) for i, f in enumerate(rig.FORMS)]
hands = [(f'{p} (pose {k})', fr(LAB, 231 + 30 * k + 22, C)) for k, p in enumerate(rig.HAND_POSE)]
caps = [(f'cap {p} (pose {k})', fr(LAB, 351 + 30 * k + 25, (340, 60, 940, 560))) for k, p in enumerate(rig.CAP_POSE)]
board('Geno Gate 2 in game: the weapon forms and the part poses (form lab)',
      'the lab taunt (GENO_FORM_LAB=1): Script.form on both hands, then Script.hand and Script.cap; his right (gun) hand is '
      'nearer the camera; game renders, local only',
      [('weapon forms, both hands (arm group / form group options)', forms[:4]), ('', forms[4:]),
       ('hand poses, both hands', hands), ('cap poses', caps)], 360, os.path.join(OUT, 'geno_forms_ingame.png'))
P = (200, 50, 1000, 850)
panels = [('forward tilt', [(f'f{k}', fr(PANEL, k, P)) for k in (22, 26, 30, 34, 38)]),
          ('up tilt', [(f'f{k}', fr(PANEL, k, P)) for k in (94, 98, 102, 106, 110)]),
          ('forward smash', [(f'f{k}', fr(PANEL, k, P)) for k in (166, 176, 186, 196, 206)]),
          ('up smash', [(f'f{k}', fr(PANEL, k, P)) for k in (236, 244, 252, 260, 268)])]
board('Geno Gate 2 in game: the capelet\'s front panels ride the upper arm (panel lab)',
      'the front panels\' inner edges weighted to the upper arm (up to 62%); the side panels on their chains; game renders, '
      'local only', panels, 300, os.path.join(OUT, 'geno_panels_ingame.png'))
