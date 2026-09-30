"""make_boards.py: the review boards for Geno's production model (Gate 1).

  python make_boards.py [OUT] [--lineup]      # OUT defaults to ~/games/melee/work/art/model (reads OUT/geno.blend)

Writes OUT/boards/:
  geno_views.png     front / 3/4 / side / back in the rest T-pose and in the relaxed pose (arms down, loose fists)
  geno_wire.png      every triangle edge over the textured model (rest and posed)
  geno_head.png      head close-ups: nearest-texel filtering (texel density) and the triangle wire (edge flow)
  geno_atlas.png     every texture at 1:1 (2x under 64 px) with size and GameCube format, and the six eye frames
  geno_rom.png       range of motion: idle, gun-arm stance, crouch, arms up, smash wind-up, kick (two angles each)
  geno_lod.png       high model vs the low model
  geno_target.png    the approved style target beside the model in the relaxed pose (local reference only)
  --lineup also runs the cast spec's boards tool with Geno added: lineup_front/side, views_Geno, wire_Geno
Everything under OUT is local (it sits beside game-derived boards); nothing here goes into git.
"""
import json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from paint_sizes import SIZES  # noqa: E402

BLENDER = os.environ.get('BLENDER', '/opt/homebrew/bin/blender')
OUT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/games/melee/work/art/model')
BD = os.path.join(OUT, 'boards'); RD = os.path.join(OUT, 'boards', 'renders')
os.makedirs(RD, exist_ok=True)
FONT = os.path.expanduser('~/animation-pipeline/engine/fonts/Archivo.ttf'); MONO = '/System/Library/Fonts/Menlo.ttc'
BG = (236, 236, 240); INK = (30, 30, 38); MUTE = (120, 120, 132)
SPEC = os.path.expanduser('~/games/melee/work/art/spec')
TARGET = os.path.expanduser('~/games/melee/work/art/target/turnaround_final.png')
SCRATCH_REF = os.environ.get('GENO_REF_DIR', '/private/tmp/claude-501/-Users-michaelbishop-animation-pipeline/7c22d831-c4d1-4516-b6ae-de77518b85b5/scratchpad')


def font(sz, mono=False):
    try: return ImageFont.truetype(MONO if mono else FONT, sz)
    except Exception: return ImageFont.load_default()


def label(img, xy, text, sz=22, fill=INK, mono=False, anchor='la'):
    ImageDraw.Draw(img).text(xy, text, font=font(sz, mono), fill=fill, anchor=anchor)


def stats_line():
    try:
        import qa  # noqa
        import geno_geo as G, geno_low as GL
        M = G.build(); L = [m for m in GL.build() if not m.option]      # the default low model
        return f"{sum(m.tris() for m in M)} tris high / {sum(m.tris() for m in L)} low, {len(M)} meshes, {len(G.JOINTS)} joints ({G.N_CONTRACT} contract + {len(G.JOINTS) - G.N_CONTRACT} added)"
    except Exception as e:
        return str(e)


def render(shots):
    job = os.path.join(RD, 'shots.json')
    json.dump({'out': RD, 'shots': shots}, open(job, 'w'))
    r = subprocess.run([BLENDER, '-b', os.path.join(OUT, 'geno.blend'), '--python', os.path.join(HERE, 'review.py'), '--', job],
                       capture_output=True, text=True)
    if r.returncode or 'Traceback' in r.stdout + r.stderr:
        print((r.stdout + r.stderr)[-3000:]); sys.exit(1)


def sheet(title, sub, rows, cell, names=None):
    """rows: list of (row label, [image paths]); names: column labels."""
    top = 110 + (30 if names else 0)
    ncol = max(len(r[1]) for r in rows)
    W = 20 + ncol * cell + 20; H = top + len(rows) * (cell + 40) + 10
    out = Image.new('RGB', (W, H), BG)
    label(out, (24, 20), title, 32); label(out, (24, 62), sub, 18, MUTE)
    if names:
        for i, n in enumerate(names): label(out, (20 + i * cell + cell // 2, top - 26), n, 20, MUTE, anchor='ma')
    for ri, (rl, ims) in enumerate(rows):
        y = top + ri * (cell + 40)
        label(out, (24, y + 4), rl, 18, MUTE)
        for i, p in enumerate(ims):
            if p and os.path.exists(p):
                out.paste(Image.open(p).convert('RGB').resize((cell, cell), Image.LANCZOS), (20 + i * cell, y + 30))
    return out


def main():
    S = stats_line()
    V = [('front', 0), ('q34', 35), ('side', 90), ('back', 180)]
    shots = []
    for pose in ('rest', 'idle'):
        for v, yaw in V:
            shots.append({'name': f'v_{pose}_{v}', 'pose': pose, 'yaw': yaw, 'ortho': 18.5, 'center': [0, 8.5, 0], 'size': [800, 800]})
    for pose in ('rest', 'idle'):
        for v, yaw in V[:3]:
            shots.append({'name': f'w_{pose}_{v}', 'pose': pose, 'yaw': yaw, 'ortho': 18.5, 'center': [0, 8.5, 0], 'size': [1200, 1200],
                          'wire': True, 'thick': 0.012})
    for v, yaw in V[:3]:
        c = [0, 13.3, -0.3]
        shots.append({'name': f'h_tex_{v}', 'pose': 'rest', 'yaw': yaw, 'ortho': 7.6, 'center': c, 'size': [900, 900], 'closest': True})
        shots.append({'name': f'h_wire_{v}', 'pose': 'rest', 'yaw': yaw, 'ortho': 7.6, 'center': c, 'size': [900, 900], 'wire': True, 'thick': 0.0065})
    for n, pose, yaw, elev, ortho, c in (('x_cape_front', 'idle', 0, 6, 10.5, [0, 9.6, 0]), ('x_cape_q34', 'idle', 35, 10, 10.5, [0, 9.6, 0]),
                                         ('x_collar', 'idle', -35, 15, 7.5, [0, 10.9, 0]), ('x_collar_back', 'idle', 180, 8, 7.5, [0, 10.9, 0]),
                                         ('x_face', 'idle', 0, 0, 5.4, [0, 12.1, 0.5]), ('x_nose', 'idle', 0, 0, 2.6, [0, 12.2, 1.5]),
                                         ('x_boot_side', 'rest', 90, 0, 4.2, [1.0, 1.6, 0.6]), ('x_boots', 'idle', 40, 10, 7.0, [0, 2.0, 0])):
        shots.append({'name': n, 'pose': pose, 'yaw': yaw, 'elev': elev, 'ortho': ortho, 'center': c, 'size': [800, 800]})
    # game scale: the 3/4 at true pixel size (Geno ~340 px as in the in-game review captures, and ~110 px at play distance)
    shots.append({'name': 'g_340', 'pose': 'idle', 'yaw': -35, 'elev': 8, 'ortho': 18.4, 'center': [0, 8.3, 0], 'size': [368, 368]})
    shots.append({'name': 'g_110', 'pose': 'idle', 'yaw': -35, 'elev': 8, 'ortho': 18.4, 'center': [0, 8.3, 0], 'size': [120, 120]})
    for form in ('hand', 'fshot', 'gun', 'stargun', 'cannon', 'beam', 'rocket'):
        p = 'aim_open' if form == 'fshot' else 'aim_fist'
        shots.append({'name': f'fz_{form}', 'pose': p, 'yaw': -80, 'elev': 10, 'ortho': 6.5, 'center': [-1.9, 10.0, 4.0],
                      'size': [600, 600], 'forms': {'R': form}, 'hide': ['cape', 'collar']})
        shots.append({'name': f'fq_{form}', 'pose': p, 'yaw': -25, 'elev': 10, 'ortho': 6.5, 'center': [-1.9, 10.0, 4.0],
                      'size': [600, 600], 'forms': {'R': form}, 'hide': ['cape', 'collar']})
    poses = ['idle', 'gun', 'crouch', 'arms_up', 'smash', 'kick']
    for p in poses:
        for yaw in (25, -110):
            shots.append({'name': f'r_{p}_{yaw}', 'pose': p, 'yaw': yaw, 'elev': 8, 'ortho': 19, 'center': [0, 8.2, 0], 'size': [700, 700]})
    for low in (False, True):
        for v, yaw in (('front', 20), ('side', 70)):
            shots.append({'name': f'l_{"lo" if low else "hi"}_{v}', 'pose': 'idle', 'yaw': yaw, 'elev': 5, 'ortho': 18.5,
                          'center': [0, 8.5, 0], 'size': [700, 700], 'low': low})
    render(shots)
    R = lambda n: os.path.join(RD, n + '.png')
    names = ['front', '3/4', 'side', 'back']
    sheet('Geno: production model (Gate 1)', S + '   |   Melee lighting convention of the cast boards, model units at ModelScale 1',
          [('rest T-pose (the skeleton contract)', [R(f'v_rest_{v}') for v, _ in V]),
           ('relaxed pose: the staggered stance (left foot 1.9 forward, right 2.1 back, toes out), arms down, loose fists', [R(f'v_idle_{v}') for v, _ in V])],
          700, names).save(os.path.join(BD, 'geno_views.png'))
    sheet('Geno: triangles', S + '   |   every triangle edge (quads split as exported)',
          [('rest', [R(f'w_rest_{v}') for v, _ in V[:3]]), ('relaxed pose', [R(f'w_idle_{v}') for v, _ in V[:3]])],
          900, names[:3]).save(os.path.join(BD, 'geno_wire.png'))
    sheet('Geno: head', 'top row nearest-texel filtered (face 128x128 CMP, eyes 128x128 CI8 x6, band 256x64, crown 256x128); bottom row the triangle wire',
          [('texels', [R(f'h_tex_{v}') for v, _ in V[:3]]), ('triangles', [R(f'h_wire_{v}') for v, _ in V[:3]])],
          700, names[:3]).save(os.path.join(BD, 'geno_head.png'))
    sheet('Geno: range of motion', 'posed with the rig\'s joints only (no correctives); ball joints stay closed, the capelet follows the arms, the cape chains are at rest (dynamics off)',
          [('front-left', [R(f'r_{p}_25') for p in poses]), ('back-right', [R(f'r_{p}_-110') for p in poses])],
          450, poses).save(os.path.join(BD, 'geno_rom.png'))
    FORMS7 = ['hand', 'fshot', 'gun', 'stargun', 'cannon', 'beam', 'rocket']
    sheet('Geno: the weapon forms (Gate 2)', 'his right (gun) hand, the arm aimed forward, the capelet hidden; each form is a visibility variant '
          '(rig.py FORMS; Script.form(side, name)); the left hand is the mirror',
          [('side', [R(f'fz_{f}') for f in FORMS7]), ('3/4 front', [R(f'fq_{f}') for f in FORMS7])], 400, FORMS7).save(
        os.path.join(BD, 'geno_forms.png'))
    sheet('Geno: high vs low model', 'the low model is drawn only in the off-screen magnifier bubble and in Fountain of Dreams\' reflections',
          [('high / low', [R('l_hi_front'), R('l_lo_front'), R('l_hi_side'), R('l_lo_side')])],
          600, ['high', 'low', 'high', 'low']).save(os.path.join(BD, 'geno_lod.png'))
    # atlas
    tex = os.path.join(OUT, 'geno_tex')
    names_t = sorted(n[:-4] for n in os.listdir(tex) if n.endswith('.png') and not n.startswith('eye_'))
    x = y = 20; rowh = 0; W = 2000
    cells = []
    for n in names_t:
        im = Image.open(os.path.join(tex, n + '.png')).convert('RGB')
        s = 2 if max(im.size) <= 64 else 1
        cells.append((n, im.resize((im.width * s, im.height * s), Image.NEAREST), im.size))
    cells.sort(key=lambda c: -c[1].height)
    pos = []
    y = 110
    for n, im, sz in cells:
        cw = max(im.width, 250)
        if x + cw > W - 20: x = 20; y += rowh + 50; rowh = 0
        pos.append((n, im, sz, x, y)); x += cw + 24; rowh = max(rowh, im.height)
    y_eyes = y + rowh + 70
    H = y_eyes + 40 + 2 * 128 + 90
    out = Image.new('RGB', (W, H), BG)
    kib = sum(w * h / 2 for n, (w, h) in SIZES.items() if os.path.exists(os.path.join(tex, n + '.png'))) / 1024
    label(out, (24, 20), f'Geno: textures ({len(names_t)} + the 6-frame eye set; {kib:.0f} KiB at CMP + {6 * (128 * 128 + 512) / 1024:.0f} KiB of CI8 eye frames)', 30)
    label(out, (24, 62), '1:1 texels (2x when 64 px or under); all original, painted procedurally in 3D by paint.py; AO baked in Blender', 18, MUTE)
    for n, im, sz, x, y in pos:
        out.paste(im, (x, y))
        fmt = 'CMP'
        label(out, (x, y + im.height + 4), f'{n}  {sz[0]}x{sz[1]} {fmt}', 15, INK, True)
    label(out, (24, y_eyes), 'Eye frames, 128x128 CI8, in Mario\'s order: 0 open, 1 half-lidded, 2 closed, 3 squint, 4 look toward -X, 5 toward +X (right eye: out, in; left eye: in, out)', 20)
    for i, f in enumerate(['open', 'half', 'closed', 'squint', 'out', 'in']):
        im = Image.open(os.path.join(tex, f'eye_{f}.png')).convert('RGB').resize((256, 256), Image.NEAREST)
        out.paste(im, (24 + i * 280, y_eyes + 40)); label(out, (24 + i * 280, y_eyes + 300), f'eye_{f}', 15, INK, True)
    out.save(os.path.join(BD, 'geno_atlas.png'))
    # Gate 1 vs Gate 1b (the Gate 1 renders were kept in OUT/gate1)
    g1 = os.path.join(OUT, 'gate1d', 'boards', 'renders')
    if os.path.exists(os.path.join(g1, 'v_idle_front.png')):
        sheet('Geno: Gate 1d (top) and Gate 2 (bottom)', 'Blender review lighting (the colours are calibrated for Melee\'s: judge them in '
              'game); Gate 2: a smooth barrel chest, the cuff\'s lip on the shin, the front panels on the upper arm, the emblem on '
              'the felt; the weapon forms are variants (geno_forms.png)',
              [('Gate 1d', [os.path.join(g1, f'v_idle_{v}.png') for v, _ in V]), ('Gate 2', [R(f'v_idle_{v}') for v, _ in V])],
              700, names).save(os.path.join(BD, 'geno_before_after.png'))
    # close-ups beside the reference crops (local only)
    ref = lambda n: os.path.join(SCRATCH_REF, n)
    def boot_ref():
        p = ref('boots_side.png')
        if not os.path.exists(p): return None
        im = Image.open(p).convert('RGB'); im = im.crop((0, 0, im.width // 2, im.height))
        q = os.path.join(RD, 'ref_boot_target.png'); im.save(q); return q
    rows = [('capelet front, 3/4 and the reference', [R('x_cape_front'), R('x_cape_q34'), ref('ref_cape.png')]),
            ('collar 3/4, collar back, face head-on, the reference', [R('x_collar'), R('x_collar_back'), R('x_face'), ref('ref_face.png')]),
            ('nose head-on, boot in profile, the target\'s boot, boots 3/4', [R('x_nose'), R('x_boot_side'), boot_ref(), R('x_boots')])]
    cell = 560
    out = Image.new('RGB', (3200, 110 + 3 * (cell + 50)), BG)
    label(out, (24, 20), 'Geno Gate 1c: capelet, collar, face, nose and boots beside the reference', 32)
    label(out, (24, 62), 'relaxed pose, the review lighting; the reference crops (ref_details.png, turnaround_final.png) are local only', 18, MUTE)
    xmax = 0
    for ri, (lab, row) in enumerate(rows):
        y = 110 + ri * (cell + 50); x = 20
        label(out, (24, y), lab, 18, MUTE)
        for p in row:
            if not p or not os.path.exists(p): continue
            im = Image.open(p).convert('RGB'); s = cell / im.height
            im = im.resize((int(im.width * s), cell), Image.LANCZOS)
            out.paste(im, (x, y + 26)); x += im.width + 16
        xmax = max(xmax, x)
    out.crop((0, 0, xmax + 10, out.height)).save(os.path.join(BD, 'geno_closeups.png'))
    # game scale
    g340 = Image.open(R('g_340')).convert('RGB'); g110 = Image.open(R('g_110')).convert('RGB')
    ig = os.path.join(BD, 'ingame_g1b_34.png')
    H2 = 736
    out = Image.new('RGB', (40 + 368 * 2 + 20 + 120 * 6 + 20 + 600, H2 + 130), BG)
    label(out, (24, 20), 'Geno Gate 1c at game pixel size (3/4, relaxed pose)', 32)
    label(out, (24, 62), 'left: rendered at ~340 px tall (as in the in-game review captures), shown 2x nearest; middle: ~110 px tall '
                          '(play distance), 6x nearest; right: Gate 1b in game (ingame_g1b_34.png)', 18, MUTE)
    out.paste(g340.resize((736, 736), Image.NEAREST), (20, 110))
    out.paste(g110.resize((720, 720), Image.NEAREST), (20 + 736 + 20, 110))
    if os.path.exists(ig):
        im = Image.open(ig).convert('RGB'); im = im.resize((int(im.width * H2 / im.height), H2), Image.LANCZOS)
        out.paste(im, (20 + 736 + 20 + 720 + 20, 110))
    out.save(os.path.join(BD, 'geno_gamescale.png'))
    # the style target beside the model (local reference; the target is derived art)
    if os.path.exists(TARGET):
        T = Image.open(TARGET).convert('RGB')
        panels = [(0, 700), (700, 1380), (1380, 2080), (2080, 2752)]
        Hh = 900
        out = Image.new('RGB', (4 * 2 * 340 + 40, Hh + 120), BG)
        label(out, (24, 20), 'Geno: the approved style target (left of each pair) and the model in the relaxed pose (right)', 30)
        label(out, (24, 62), 'target: turnaround_final.png (pass B, black eyes). The model keeps the rig\'s proportions (longer legs and torso than the target).', 18, MUTE)
        for i, (a, b) in enumerate(panels):
            t = T.crop((a, 60, b, 1460)); t = t.resize((int(t.width * Hh / t.height), Hh))
            t = t.crop(((t.width - 340) // 2, 0, (t.width - 340) // 2 + 340, Hh))
            r = Image.open(R(f'v_idle_{["front", "q34", "side", "back"][i]}')).convert('RGB')
            r = r.resize((Hh, Hh)).crop(((Hh - 340) // 2, 0, (Hh - 340) // 2 + 340, Hh))
            out.paste(t, (20 + i * 680, 110)); out.paste(r, (20 + i * 680 + 340, 110))
        out.save(os.path.join(BD, 'geno_target.png'))
    if '--lineup' in sys.argv:
        tmp = tempfile.mkdtemp(prefix='geno_spec_')
        shutil.copy(os.path.join(SPEC, 'summary.json'), tmp)
        for d in ('gltf', 'stats', 'tex'):
            os.symlink(os.path.join(SPEC, d), os.path.join(tmp, d))
        tool = os.path.join(HERE, '..', '..', '..', 'tools', 'machinima', 'melee', 'art', 'boards.py')
        py = os.path.expanduser('~/animation-pipeline/.venv/bin/python')
        subprocess.run([py, tool, '--out', tmp, '--steps', 'render,compose', '--extra', f'Geno={os.path.join(OUT, "geno.gltf")}:1.0'],
                       capture_output=True, text=True)
        for n in ('lineup_front', 'lineup_side', 'views_Geno', 'wire_Geno'):
            p = os.path.join(tmp, 'boards', n + '.png')
            if os.path.exists(p): shutil.copy(p, os.path.join(BD, n + '.png'))
        shutil.rmtree(tmp, ignore_errors=True)
    print('boards in', BD)


if __name__ == '__main__':
    main()
