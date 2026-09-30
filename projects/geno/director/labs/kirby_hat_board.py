"""Stills and strips from a kirby_hat_lab run, each segment lined up on its own sync slate (aerials_strips.align: the
dump can drop images, so one constant offset drifts).
    .venv/bin/python projects/geno/director/labs/kirby_hat_board.py RUN OUT_DIR [--plan director/build/kirby_hat_lab.plan.json]
        [--still 60] [--cells 14] [--cols 7] [--crop 0.55] [--w 300]
Per segment: OUT_DIR/<label>.png (the frame at segment frame --still) and strip_<label>.png (--cells frames across the
segment, the centre --crop of each image, tagged with the segment frame and port 0's motion state), plus events.txt
(the copies gained and lost: KBCOPY/KBLOSE, and the states). Game renders: keep OUT_DIR outside the repo.
"""
import argparse, json, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aerials_strips import load, align, state_at

KB = {14: 'Wait', 17: 'WalkSlow', 24: 'KneeBend', 25: 'JumpF', 26: 'JumpB', 27: 'JumpAerF', 28: 'JumpAerB', 29: 'Fall',
      39: 'Squat', 40: 'SquatWait', 41: 'SquatRv', 42: 'Landing', 264: 'AppealR', 265: 'AppealL',
      544: 'GeNStart', 545: 'GeNLoop', 546: 'GeNEnd', 547: 'GeAirNStart', 548: 'GeAirNLoop', 549: 'GeAirNEnd',
      550: 'GeFinger', 551: 'GeAirFinger'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run'); ap.add_argument('out')
    ap.add_argument('--plan', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build', 'kirby_hat_lab.plan.json'))
    ap.add_argument('--still', type=int, default=60); ap.add_argument('--cells', type=int, default=14)
    ap.add_argument('--crop', type=float, default=0.55); ap.add_argument('--w', type=int, default=300)
    ap.add_argument('--cols', type=int, default=7); ap.add_argument('--sync', type=int, default=10)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    plan = json.load(open(a.plan)); segs = plan['segs']
    d = load(a.run); spans = align(d, segs)
    W, H = Image.open(os.path.join(a.run, d['frames'][0])).size
    ev = [l.rstrip() for l in open(os.path.join(a.run, 'osreport.log'), errors='replace') if l.split()[:1] and l.split()[0] in ('KBCOPY', 'KBLOSE', 'MARK') or 'KBGE hat' in l]
    open(os.path.join(a.out, 'events.txt'), 'w').write('\n'.join(ev) + '\n')

    def img(s):
        i = d['idx'](s)
        return Image.open(os.path.join(a.run, d['frames'][i])).convert('RGB') if 0 <= i < len(d['frames']) else None

    for sl in segs:
        t0, n = sl['start'], sl['frames']
        im = img(t0 + min(a.still, n - 5))
        if im: im.save(os.path.join(a.out, sl['label'] + '.png'))
        end = t0 + n - a.sync - 1                  # the next segment's slate starts SYNC frames before it
        step = max(1, (end - t0 - 2) // a.cells)
        frames = list(range(t0 + 2, end, step))[:a.cells]
        cw, ch = int(W * a.crop), int(H * a.crop)
        box = ((W - cw) // 2, (H - ch) // 2, (W + cw) // 2, (H + ch) // 2)
        h = int(a.w * ch / cw); cols = min(a.cols, len(frames)); rows = -(-len(frames) // cols)
        strip = Image.new('RGB', (a.w * cols, h * rows + 20), (30, 30, 38)); dr = ImageDraw.Draw(strip)
        dr.text((4, 4), f"{sl['label']}  ({os.path.basename(a.run)}; every {step} frames; synced on its slate)", fill=(230, 230, 240))
        for k, s in enumerate(frames):
            im = img(s)
            if im is None: continue
            r, c = divmod(k, cols)
            strip.paste(im.crop(box).resize((a.w, h), Image.LANCZOS), (c * a.w, 20 + r * h))
            st = state_at(d['ms'][0], s)
            dr.text((c * a.w + 4, 23 + r * h), f"{s - t0} {KB.get(st[1], st[1]) if st else ''}", fill=(255, 230, 120))
        strip.save(os.path.join(a.out, f"strip_{sl['label']}.png"))
    print(f"{len(segs)} segments -> {a.out}; synced {len(spans)} of {len(segs)}")


if __name__ == '__main__':
    main()
