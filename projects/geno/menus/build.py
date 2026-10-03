"""Build Geno's menu files (never touching the disc): the character select screen, the results screen, the VS Records
faces and the in-match HUD, plus review sheets and an install script.
    .venv/bin/python projects/geno/menus/build.py [ART] [--out DIR]
ART is menus/portrait.py's output (the production model rendered in game): icon.png, csp_<costume>.png and
stock_<costume>.png for every costume, and face.png (default $MELEE_WORK/menuart). A folder with only icon.png and
csp_*.png (the blocky rig's placeholders, css3/geno) still works: art.py derives one stock icon and the Records face from
csp_0. The winner banner and name label are always spliced from the results screen's own lettering (art.py).
Reads the vanilla files (the work folder's backups, else the disc), writes DIR (default $MELEE_WORK/menus)/out/{MnSlChr,
GmRst,MnMaAll,IfAll}.usd and out/install.sh, and renders every new texture and every patched animation frame to
DIR/board/. Everything under menus/ is derived from game data: it stays out of git.
"""
import glob, hashlib, os, shutil, subprocess, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
DISC = os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc'))
WORK = os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work'))
M = os.path.join(WORK, 'menus')
if '--out' in sys.argv:
    M = os.path.abspath(sys.argv[sys.argv.index('--out') + 1]); del sys.argv[sys.argv.index('--out'):sys.argv.index('--out') + 2]
DATKIT = os.path.join(ROOT, 'tools', 'machinima', 'melee', 'datkit.sh')
sys.path.insert(0, HERE)
import sheet  # noqa: E402

# retail (NTSC 1.02) files, English
VANILLA = {
    'MnSlChr.usd': 'aa6e9062f51834717ce1fed6ec2e806316e3feb3',
    'GmRst.usd': '59211dd6f5ba60105ef2b036ae504ef783ef6456',
    'MnMaAll.usd': '46215adc465f2cba610991dab179930437cc28ab',
    'IfAll.usd': '18b8a643dcef0686e2dc1bc785c6b0200335723f',
}
# earlier Geno builds that may be on the disc and may be replaced: css-geno's first MnSlChr.usd (one portrait at frame 25),
# the blocky rig's placeholder menus (one costume; on the main and demo discs until the production art, 2026-09-28), and
# the production art's first build (five costumes, on the main disc 2026-09-28 until Dark's)
PREVIOUS = {'MnSlChr.usd': ['6aeebbb55da0fa8c2d2c96be740835c3ec5030e3', '65d9fcfd77932b6e04f8d30a2120d122bdb85d2f',
                            '329ce443b1131ef618af6e4db8ca1744c0fb2531'],
            'GmRst.usd': ['65cd1aef49f9405c16793adedf4b23fbc99e6bcd', '2713a3ebafb112b3be30a0afbdf6635d70ec52bf'],
            'MnMaAll.usd': ['5a2923bd52188fdf41017be8d5dad9379bd63b32'],
            'IfAll.usd': ['959aba2a96cb34f22e43af637b462e4cb0b6d954', 'f8d5c43d210f9667a2842ca4807e80a868299c3c']}


def sha1(p):
    return hashlib.sha1(open(p, 'rb').read()).hexdigest()


def dk(*args):
    r = subprocess.run([DATKIT, *map(str, args)], check=True, capture_output=True, text=True)
    return r.stdout


def vanilla(name):
    for p in (os.path.join(WORK, 'orig', name), os.path.join(WORK, 'orig', 'menus', name), os.path.join(DISC, 'files', name)):
        if os.path.exists(p) and sha1(p) == VANILLA[name]:
            return p
    sys.exit(f'no vanilla {name} (want SHA-1 {VANILLA[name]}) in the work backups or the disc')


def bgra(png, size, out):
    im = Image.open(png).convert('RGBA')
    assert im.size == size, f'{png}: {im.size}, want {size}'
    r, g, b, a = im.split()
    open(out, 'wb').write(Image.merge('RGBA', (b, g, r, a)).tobytes())
    return out


def frames(file, model, sub, specs, frs):
    d = os.path.join(M, 'frames', sub)
    shutil.rmtree(d, ignore_errors=True)
    dk('mframes', file, model, d, ','.join(specs), ','.join(map(str, frs)))
    return d


def f(d, j, fr, dobj=0):
    return os.path.join(d, f'j{j}_d{dobj}_f{fr:03d}.png')


def main():
    art = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, 'menuart')
    for sub in ('out', 'board', 'build', 'glyphs', 'art', 'src'):
        os.makedirs(os.path.join(M, sub), exist_ok=True)
    src = {n: vanilla(n) for n in VANILLA}
    for n in ('GmRst.usd', 'MnMaAll.usd', 'IfAll.usd'):
        shutil.copy(src[n], os.path.join(M, 'src', n))

    # the art: the stock icon and Records face from his CSS portrait, the lettering from the results screen's own glyphs
    dk('mdump', src['GmRst.usd'], 'pnlsce#0', os.path.join(M, 'glyphs'), '10,33')
    print(subprocess.run([sys.executable, os.path.join(HERE, 'art.py'), art, os.path.join(M, 'glyphs'), os.path.join(M, 'art')],
                         check=True, capture_output=True, text=True).stdout, end='')
    b = os.path.join(M, 'build')
    icon = bgra(os.path.join(art, 'icon.png'), (64, 56), os.path.join(b, 'icon.bgra'))
    ncos = len(glob.glob(os.path.join(art, 'csp_*.png')))
    csps = [bgra(os.path.join(art, f'csp_{c}.png'), (136, 188), os.path.join(b, f'csp_{c}.bgra')) for c in range(ncos)]
    # the rendered art's own stock icons (one per costume) and Records face replace art.py's derived ones
    for old in glob.glob(os.path.join(M, 'art', 'stock_*.*')): os.remove(old)
    if os.path.exists(os.path.join(art, 'stock_0.png')):
        for c in range(ncos):
            shutil.copy(os.path.join(art, f'stock_{c}.png'), os.path.join(M, 'art', f'stock_{c}.png'))
            bgra(os.path.join(art, f'stock_{c}.png'), (24, 24), os.path.join(M, 'art', f'stock_{c}.bgra'))
    if os.path.exists(os.path.join(art, 'face.png')):
        shutil.copy(os.path.join(art, 'face.png'), os.path.join(M, 'art', 'face.png'))
        bgra(os.path.join(art, 'face.png'), (64, 32), os.path.join(M, 'art', 'face.bgra'))
    stocks = sorted(glob.glob(os.path.join(M, 'art', 'stock_*.bgra')), key=lambda p: int(p.rsplit('_', 1)[1][:-5])) or [os.path.join(M, 'art', 'stock.bgra')]
    print(f'{ncos} costume(s), {len(stocks)} stock icon(s)')

    out = os.path.join(M, 'out')
    print(dk('css-geno', src['MnSlChr.usd'], os.path.join(out, 'MnSlChr.usd'), icon, *csps, *sum((['--stock', p] for p in stocks), [])), end='')
    print(dk('menus-geno', os.path.join(M, 'src'), out, os.path.join(M, 'art')), end='')
    subprocess.run([sys.executable, os.path.join(HERE, 'gxalign.py')] + [os.path.join(out, n) for n in VANILLA], check=True)

    # ---- review sheets: every new texture, and what every patched animation shows at the frames that matter
    A = lambda n: os.path.join(M, 'art', n + '.png')
    SA = [p[:-5] + '.png' for p in stocks]                                   # the stock icons as PNG, costume order
    rows = max(4, ncos)
    CF = [25 + 30 * c for c in range(rows)]                                 # his CSS frames, one per costume row
    HF = [180 + c for c in range(rows)]                                     # his HUD and results frames, 180 + costume
    cs = lambda xs: ' '.join(map(str, xs))
    sheet.rows(os.path.join(M, 'board', 'new_textures.png'), [
        ('css-geno inputs: icon face 64x56 | portraits 136x188, one per costume', 2,
         [os.path.join(art, 'icon.png')] + [os.path.join(art, f'csp_{c}.png') for c in range(ncos)]),
        ('stock icons 24x24 CI4, one per costume (IfAll HUD, results panels, 1P select)', 8, SA),
        ('VS Records face 64x32 CI8', 6, [A('face')]),
        ('results winner banner 256x28 I4', 3, [A('banner')]),
        ('results name label 120x24 I4', 4, [A('label')]),
    ])
    o = lambda n: os.path.join(out, n)
    # results screen
    g = frames(o('GmRst.usd'), 'pnlsce#0', 'gmrst', ['10:1', '25:1', '26:1', '27:1', '28:1', '33', '41', '49', '57', '66', '67', '68', '69'],
               sorted({7, 8, 11, 24, 179, 181, HF[-1] + 1} | set(HF)))
    sheet.rows(os.path.join(M, 'board', 'gmrst_frames.png'), [
        ('winner banner j0x0A dobj1: LUIGI 7, MARIO 8, NESS 11, GANONDORF 24 | 180 GENO | 181 RED TEAM', 2,
         [f(g, 10, x, 1) for x in (7, 8, 11, 24)]),
        ('', 2, [f(g, 10, x, 1) for x in (180, 181)]),
        (f'stock icons j0x19-0x1C dobj1: MARIO 8, GANONDORF 24, frames 179 | {cs(HF)} GENO (costumes) | {HF[-1] + 1}', 6,
         [f(g, 25, x, 1) for x in [8, 24, 179] + HF + [HF[-1] + 1]]),
        ('   ports 2-4 at 180', 6, [f(g, j, 180, 1) for j in (26, 27, 28)]),
        ('name labels j0x21/0x29/0x31/0x39: LUIGI 7, MARIO 8, NESS 11 | 180 GENO (each port) | 181', 3,
         [f(g, 33, x) for x in (7, 8, 11)] + [f(g, j, 180) for j in (33, 41, 49, 57)] + [f(g, 33, 181)]),
        ('emblems j0x42-0x45: MARIO 8 | 180 each port | 181', 2, [f(g, 66, 8)] + [f(g, j, 180) for j in (66, 67, 68, 69)] + [f(g, 66, 181)]),
    ])
    # VS Records faces
    r = frames(o('MnMaAll.usd'), 'MenMainFaceB_Top', 'mnma', ['2'], [0, 8, 23, 24, 25, 26])
    sheet.rows(os.path.join(M, 'board', 'mnmaall_frames.png'), [
        ('VS Records face j2 by SELKIND: C.FALCON 0, MARIO 8, PICHU 23, GANONDORF 24 | 25 GENO | 26 (past the list)', 5,
         [f(r, 2, x) for x in (0, 8, 23, 24, 25, 26)]),
    ])
    # HUD
    h = frames(o('IfAll.usd'), 'Stc_scemdls#0', 'ifall_stc', [str(j) for j in range(1, 8)], [8, 24, 179] + HF + [HF[-1] + 1])
    e = frames(o('IfAll.usd'), 'DmgMrk_scene_models#0', 'ifall_mrk', ['1'], [8, 24, 180, 181])
    sheet.rows(os.path.join(M, 'board', 'ifall_frames.png'), [
        (f'HUD stock icon Stc_scemdls#0 j1: MARIO 8, GANONDORF 24, 179 | {cs(HF)} GENO (costumes) | {HF[-1] + 1}', 8,
         [f(h, 1, x) for x in [8, 24, 179] + HF + [HF[-1] + 1]]),
        ('   j2-j7 at 180', 8, [f(h, j, 180) for j in range(2, 8)]),
        ('HUD emblem DmgMrk#0 j1 (read at frame + 0.5): MARIO 8, GANONDORF 24 | 180 GENO | 181', 2, [f(e, 1, x) for x in (8, 24, 180, 181)]),
    ])
    # character select
    fr = sorted({24, 26, 54, 116} | set(CF))
    vp = frames(o('MnSlChr.usd'), 'MnSelectChrDataTable:MenuModel', 'css_vs', ['51', '52', '53', '54', '46:1', '47:1', '48:1', '49:1'], fr)
    rp = frames(o('MnSlChr.usd'), 'MnSelectChrDataTable:SingleMenuModel', 'css_1p', ['45', '43:1', '53', '54', '55', '56', '57'], fr + [8])
    cp = frames(o('MnSlChr.usd'), 'MnSelectChrDataTable:PortraitModel', 'css_cpu', ['6', '4:1'], fr)
    dk('mdump', o('MnSlChr.usd'), 'MnSelectChrDataTable:MenuModel', os.path.join(M, 'frames', 'css_icon_vs'), '14,174')
    dk('mdump', o('MnSlChr.usd'), 'MnSelectChrDataTable:SingleMenuModel', os.path.join(M, 'frames', 'css_icon_1p'), '14,80')
    I = lambda d, n: os.path.join(M, 'frames', d, n)
    sheet.rows(os.path.join(M, 'board', 'mnslchr_frames.png'), [
        ('icons (face dobj): VS Roy j14 | VS Geno j174 | 1P Roy j14 | 1P Geno j80', 3,
         [I('css_icon_vs', 'j14_d1_t0.png'), I('css_icon_vs', 'j174_d1_t0.png'), I('css_icon_1p', 'j14_d1_t0.png'), I('css_icon_1p', 'j80_d1_t0.png')]),
        (f'VS door 1 portrait j51: 24 GANONDORF | {cs(CF)} GENO (costume rows) | 26, 54, 116 unchanged', 1,
         [f(vp, 51, x) for x in [24] + CF + [26, 54, 116]]),
        (f'VS doors 2-4 (j52-54) at {cs(CF)}', 1, [f(vp, j, x) for j in (52, 53, 54) for x in CF]),
        (f'VS emblems j46-49 at 24 | {cs(CF)} | 26', 1, [f(vp, 46, x, 1) for x in [24] + CF + [26]] + [f(vp, j, 25, 1) for j in (47, 48, 49)]),
        (f'1P player door portrait j0x2D and emblem j0x2B at 24 | {cs(CF)} | 26', 1,
         [f(rp, 45, x) for x in [24] + CF + [26]] + [f(rp, 43, x, 1) for x in [24] + CF + [26]]),
        (f'1P CPU door (door model) portrait j6 and emblem j4 at 24 | {cs(CF)}', 1,
         [f(cp, 6, x) for x in [24] + CF] + [f(cp, 4, x, 1) for x in [24] + CF]),
        (f'1P stock icons j0x35: MARIO 8, GANONDORF 24 | {cs(CF)} GENO | 26 54 116; j0x36-0x39 at 25', 6,
         [f(rp, 53, x) for x in [8, 24] + CF + [26, 54, 116]] + [f(rp, j, 25) for j in (54, 55, 56, 57)]),
    ])
    # every costume's stock icon everywhere it lands, beside Mario's and Ganondorf's
    sheet.rows(os.path.join(M, 'board', 'stock_everywhere.png'), [
        ('vanilla: HUD (IfAll 8 MARIO, 24 GANONDORF) | results (GmRst) | 1P select (MnSlChr)', 8,
         [f(h, 1, 8), f(h, 1, 24), f(g, 25, 8, 1), f(g, 25, 24, 1), f(rp, 53, 8), f(rp, 53, 24)]),
    ] + [(f'costume {c}: art | HUD {HF[c]} | results {HF[c]} | 1P select {CF[c]}', 8,
          [SA[min(c, len(SA) - 1)], f(h, 1, HF[c]), f(g, 25, HF[c], 1), f(rp, 53, CF[c])]) for c in range(ncos)])
    write_install(out)


INSTALL = r'''#!/bin/sh
# Install Geno's menu files: the character select screen (MnSlChr.usd), the results screen (GmRst.usd), the VS Records
# faces (MnMaAll.usd) and the in-match HUD (IfAll.usd). Built by projects/geno/menus/build.py.
#   sh install.sh            back up the disc's files (once, to $MELEE_WORK/orig/menus/) and install ($MELEE_DISC, default ~/games/melee/disc)
#   sh install.sh --restore  put the backed-up files back
# Every file is checked by SHA-1 before and after copying; a disc file that is neither retail, a known earlier Geno build
# nor this build is refused, nothing unknown is overwritten.
set -eu

HERE="$(cd "$(dirname "$0")" && pwd)"
FILES="${MELEE_DISC:-$HOME/games/melee/disc}/files"
BAK="${MELEE_WORK:-$HOME/games/melee/work}/orig/menus"

sha1() { shasum -a 1 "$1" | cut -d' ' -f1; }
need() { [ -f "$1" ] && [ "$(sha1 "$1")" = "$2" ] || { echo "$1: missing or wrong SHA-1" >&2; exit 1; }; }
# name  new-sha1  known-sha1s (retail first, then earlier Geno builds)
TABLE='@TABLE@'

known() {  # $1 sha, $2 known list
    for h in $2; do [ "$1" = "$h" ] && return 0; done; return 1
}

if [ "${1:-}" = "--restore" ]; then
    echo "$TABLE" | while read -r name new olds; do
        [ -n "$name" ] || continue
        [ -f "$BAK/$name" ] || { echo "no backup of $name; left as is" >&2; continue; }
        known "$(sha1 "$BAK/$name")" "$olds" || { echo "$BAK/$name is not a known original; refusing" >&2; exit 1; }
        cp -p "$BAK/$name" "$FILES/$name"; echo "restored $name"
    done
    exit 0
fi

# check everything before touching anything
echo "$TABLE" | while read -r name new olds; do
    [ -n "$name" ] || continue
    need "$HERE/$name" "$new"
    cur="$(sha1 "$FILES/$name")"
    [ "$cur" = "$new" ] || known "$cur" "$olds" || { echo "$FILES/$name is neither retail, an earlier Geno build nor this build (sha1 $cur); refusing" >&2; exit 1; }
    [ ! -f "$BAK/$name" ] || known "$(sha1 "$BAK/$name")" "$olds" || { echo "$BAK/$name is not a known original; refusing" >&2; exit 1; }
done

echo "$TABLE" | while read -r name new olds; do
    [ -n "$name" ] || continue
    cur="$(sha1 "$FILES/$name")"
    if [ "$cur" = "$new" ]; then echo "already installed: $name"; continue; fi
    known "$cur" "$olds" || { echo "$FILES/$name is neither retail, an earlier Geno build nor this build (sha1 $cur); refusing" >&2; exit 1; }
    if [ ! -f "$BAK/$name" ]; then mkdir -p "$BAK"; cp -p "$FILES/$name" "$BAK/$name"; echo "backed up $name -> $BAK/"; fi
    cp "$HERE/$name" "$FILES/$name"; need "$FILES/$name" "$new"; echo "installed $name"
done
echo "done"
'''


def write_install(out):
    rows = []
    for n in VANILLA:
        rows.append(' '.join([n, sha1(os.path.join(out, n)), VANILLA[n], *PREVIOUS.get(n, [])]))
    p = os.path.join(out, 'install.sh')
    open(p, 'w').write(INSTALL.replace('@TABLE@', '\n'.join(rows)))
    os.chmod(p, 0o755)
    for row in rows: print('  ' + row)


if __name__ == '__main__':
    main()
