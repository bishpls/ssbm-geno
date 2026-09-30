"""Patch the character select screen's data for Geno and install it in the extracted disc.
    .venv/bin/python projects/geno/css/install.py [ART]      # ART: icon.png + csp_0.png... (default: the placeholder output)
The vanilla file is kept once under $MELEE_WORK/orig and every install starts from it, so re-running is safe.
projects/geno/menus/build.py supersedes this: it builds this file with the 1P screen's stock icons too, plus the results,
VS Records and HUD files, into $MELEE_WORK/menus/out with an install script that checks SHA-1s.
"""
import glob, os, shutil, subprocess, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DISC = os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc'))
WORK = os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work'))
DATKIT = os.path.join(ROOT, 'tools', 'machinima', 'melee', 'datkit.sh')


def bgra(png, size, out):
    im = Image.open(png).convert('RGBA')
    assert im.size == size, f'{png}: {im.size}, want {size}'
    r, g, b, a = im.split()
    open(out, 'wb').write(Image.merge('RGBA', (b, g, r, a)).tobytes())
    return out


def main():
    art = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, 'css3', 'geno')
    orig = os.path.join(WORK, 'orig'); os.makedirs(orig, exist_ok=True)
    name = 'MnSlChr.usd'
    if not os.path.exists(os.path.join(orig, name)):
        shutil.copy(os.path.join(DISC, 'files', name), os.path.join(orig, name))
    tmp = os.path.join(WORK, 'css_build'); os.makedirs(tmp, exist_ok=True)
    icon = bgra(os.path.join(art, 'icon.png'), (64, 56), os.path.join(tmp, 'icon.bgra'))
    csps = [bgra(p, (136, 188), os.path.join(tmp, os.path.basename(p)[:-4] + '.bgra'))
            for p in sorted(glob.glob(os.path.join(art, 'csp_*.png')))]
    subprocess.run([DATKIT, 'css-geno', os.path.join(orig, name), os.path.join(DISC, 'files', name), icon, *csps], check=True)


if __name__ == '__main__':
    main()
