"""Every challenger's NEW CHALLENGER screen from one challenger_lab build, for the before/after identity check of Geno's
silhouette: the lab's DOL is copied once per challenger with the director's challenger record (dir_setup.ckind[1],
found by symbol in main.elf) patched, booted, and its frames kept.
    challenger_sweep.py run OUT [--res 2] [--frames 150] [--kinds gnw,luigi,...,geno]
        needs a challenger_lab build in $MELEE_DECOMP / $MELEE_DISC (sandbox.sh); restores the built DOL afterwards.
        OUT/<kind>/ gets the run (f00001.png ...); OUT/sweep.json the runs.
    challenger_sweep.py compare BEFORE AFTER [--json OUT]
        frame-for-frame comparison of two sweeps: per challenger, the frames that differ and the most pixels that differ in
        one, over the whole frame and over the silhouette panel.
"""
import json, os, shutil, struct, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'machinima', 'melee'))
from dsl import CKIND  # noqa: E402

KINDS = ['gnw', 'luigi', 'marth', 'mewtwo', 'puff', 'falco', 'ylink', 'doc', 'roy', 'pichu', 'ganon', 'geno']
PANEL = (0.655, 0.225, 0.98, 0.755)          # the silhouette panel, fractions of the frame (res 2: x 843-1252, y 244-790 of 1280x1056)


def symbol(elf, name):
    nm = os.path.join(os.path.dirname(elf), '..', 'binutils', 'powerpc-eabi-nm')
    for line in subprocess.run([nm, elf], capture_output=True, text=True, check=True).stdout.splitlines():
        p = line.split()
        if len(p) == 3 and p[2] == name: return int(p[0], 16)
    sys.exit(f'{elf}: no symbol {name}')


def dol_offset(dol, addr):
    h = dol[:0x100]
    offs, addrs, sizes = struct.unpack('>18I', h[0:72]), struct.unpack('>18I', h[0x48:0x90]), struct.unpack('>18I', h[0x90:0xD8])
    for o, a, s in zip(offs, addrs, sizes):
        if s and a <= addr < a + s: return o + addr - a
    sys.exit(f'0x{addr:08X} is in no DOL section')


def run(out, res=2, frames=150, kinds=KINDS):
    decomp, disc = os.environ['MELEE_DECOMP'], os.environ['MELEE_DISC']
    elf = os.path.join(decomp, 'build', 'GALE01', 'main.elf')
    target = os.path.join(disc, 'sys', 'main.dol')
    built = open(target, 'rb').read()
    off = dol_offset(built, symbol(elf, 'dir_setup')) + 5        # DirSetup: u16 stage, u8 nplayers, u8 entry, s8 ckind[4]
    os.makedirs(out, exist_ok=True)
    log = {}
    try:
        for k in kinds:
            d = bytearray(built); d[off] = CKIND[k]
            open(target, 'wb').write(d)
            r = os.path.join(out, k)
            shutil.rmtree(r, ignore_errors=True)
            p = subprocess.run([os.path.join(ROOT, '.venv', 'bin', 'python'), os.path.join(ROOT, 'tools', 'machinima', 'dolphin.py'),
                                'run', target, r, '--frames', str(frames), '--res', str(res), '--quiet'],
                               capture_output=True, text=True, env=dict(os.environ, DOLPHIN_SLOTS=os.environ.get('DOLPHIN_SLOTS', '3')))
            last = (p.stdout.strip().splitlines() or [''])[-1]
            log[k] = dict(ckind=CKIND[k], result=last)
            ch = [l for l in open(os.path.join(r, 'osreport.log'), errors='replace') if 'DIRECTOR CHALLENGER' in l]
            print(k, CKIND[k], ch[0].strip() if ch else 'no challenger line', last[:120], flush=True)
    finally:
        open(target, 'wb').write(built)
    json.dump(log, open(os.path.join(out, 'sweep.json'), 'w'), indent=1)


def frames_of(d):
    return sorted(f for f in os.listdir(d) if f.startswith('f') and f.endswith('.png'))


def compare(a, b, out=None):
    res = {}
    for k in sorted(set(os.listdir(a)) & set(os.listdir(b))):
        da, db = os.path.join(a, k), os.path.join(b, k)
        if not os.path.isdir(da): continue
        fa, fb = frames_of(da), frames_of(db)
        n = min(len(fa), len(fb))
        diff, panel_diff, worst = [], [], 0
        for f in fa[:n]:
            A = np.asarray(Image.open(os.path.join(da, f)).convert('RGB'))
            B = np.asarray(Image.open(os.path.join(db, f)).convert('RGB'))
            if A.shape != B.shape: diff.append(f); continue
            m = (A != B).any(axis=2)
            if m.any():
                diff.append(f); worst = max(worst, int(m.sum()))
                H, W = m.shape
                x0, y0, x1, y1 = int(PANEL[0] * W), int(PANEL[1] * H), int(PANEL[2] * W), int(PANEL[3] * H)
                if m[y0:y1, x0:x1].any(): panel_diff.append(f)
        res[k] = dict(frames=n, frames_before=len(fa), frames_after=len(fb), differ=len(diff), panel_differ=len(panel_diff),
                      worst_pixels=worst, first=diff[:3])
        print(f'{k:7s} {n:4d} frames ({len(fa)}/{len(fb)}): {len(diff)} differ ({len(panel_diff)} in the panel), worst {worst} px')
    if out: json.dump(res, open(out, 'w'), indent=1)
    return res


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = {}
    for k in ('--res', '--frames', '--kinds', '--json'):
        if k in a:
            j = a.index(k); opt[k] = a[j + 1]; del a[j:j + 2]
    if a[0] == 'run':
        run(a[1], int(opt.get('--res', 2)), int(opt.get('--frames', 150)), opt.get('--kinds', ','.join(KINDS)).split(','))
    elif a[0] == 'compare':
        compare(a[1], a[2], opt.get('--json'))
    else:
        sys.exit(__doc__)
