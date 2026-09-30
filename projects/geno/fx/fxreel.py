"""An mp4 of lab runs stacked (before above after, say), logic frame for logic frame, with the first run's game audio.
    .venv/bin/python projects/geno/fx/fxreel.py OUT.mp4 --segs LABEL[:FROM:TO],... [--crop X,Y,W,H] [--w 960] NAME=RUN ...
Each segment of the lab's plan (RUN.plan.json) plays from FROM to TO logic frames after its start (default -12 to its
length), every run lined up on that segment's own sync slate (fxsync.py), so a dropped dump image can't shift one row
against another. The audio is cut by logic frame from the first run's dsp.wav (which drops nothing), so it stays in sync
too. Game data: keep the output out of the repo.
"""
import argparse, os, subprocess, tempfile

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw
from scipy.signal import resample

import fxsync


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('runs', nargs='+')
    ap.add_argument('--segs', required=True)
    ap.add_argument('--crop', default=''); ap.add_argument('--w', type=int, default=960); ap.add_argument('--crf', type=int, default=18)
    a = ap.parse_args()
    runs = [(n, fxsync.load(r)) for n, r in (x.split('=', 1) for x in a.runs)]
    for n, r in runs:
        print(n, 'segment offsets against the first:', r.check())
    plan = {seg['label']: seg for seg, _ in runs[0][1].offsets}
    segs = []
    for spec in a.segs.split(','):
        p = spec.split(':')
        seg = plan[p[0]]
        segs.append((p[0], int(p[1]) if len(p) > 1 else -12, int(p[2]) if len(p) > 2 else seg['frames']))
    crop = tuple(int(v) for v in a.crop.split(',')) if a.crop else None
    first = runs[0][1].path(segs[0][0], 0)
    cw0, ch0 = (crop[2], crop[3]) if crop else Image.open(first).size
    cw = a.w // 2 * 2; ch = int(cw * ch0 / cw0) // 2 * 2
    W, H = cw, (ch + 24) * len(runs)
    # the audio: each segment's logic frames cut from the first run's dump and joined
    clk, sr, y = fxsync.click(runs[0][1].run)
    wav = None
    if clk is not None:
        parts = []
        for label, f0, f1 in segs:
            s0 = plan[label]['start']
            i0, i1 = runs[0][1].audio_at(s0 + f0, clk, sr), runs[0][1].audio_at(s0 + f1, clk, sr)
            parts.append(y[max(0, i0):max(0, i1)])
        seg_audio = np.concatenate(parts)
        n_frames = sum(f1 - f0 for _, f0, f1 in segs)
        seg_audio = resample(seg_audio, int(round(n_frames / 60 * 48000)), axis=0)
        wav = os.path.join(tempfile.gettempdir(), f'fxreel_{os.getpid()}.wav')
        sf.write(wav, np.clip(seg_audio, -1, 1), 48000)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '60', '-i', '-']
    if wav:
        cmd += ['-i', wav, '-c:a', 'aac', '-b:a', '160k', '-shortest']
    cmd += ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', str(a.crf), a.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for label, f0, f1 in segs:
        for rel in range(f0, f1):
            frame = Image.new('RGB', (W, H), (18, 18, 24)); d = ImageDraw.Draw(frame)
            for k, (name, r) in enumerate(runs):
                p = r.path(label, rel)
                if p:
                    im = Image.open(p).convert('RGB')
                    if crop:
                        x, yy, w, h = crop; im = im.crop((x, yy, x + w, yy + h))
                    frame.paste(im.resize((cw, ch), Image.LANCZOS), (0, k * (ch + 24) + 24))
                d.text((8, k * (ch + 24) + 6), f'{name}   {label} {rel:+d}', fill=(255, 220, 90))
            ff.stdin.write(frame.tobytes())
    ff.stdin.close(); ff.wait()
    if wav:
        os.remove(wav)
    print(a.out, f'{W}x{H}', sum(f1 - f0 for _, f0, f1 in segs), 'frames')


if __name__ == '__main__':
    main()
