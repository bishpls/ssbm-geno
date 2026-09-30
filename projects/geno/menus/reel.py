"""An mp4 of a Dolphin capture (tools/machinima/dolphin.py) with its game audio, for review pages.
    .venv/bin/python projects/geno/menus/reel.py OUT.mp4 RUN [--from F] [--to F] [--w 960] [--presses F,F,...] [--crf 20]
Frames F are the dump's (f00001.png is 1). The audio: the game's DSP dump (dsp.wav) starts at emulator boot, earlier than
the first image by a few seconds that vary run to run, so it is placed by measurement:
  - a director film opens on its magenta slate and clicks on the slate's first frame: the first onset in the dump is that
    frame (tools/machinima/plates.py);
  - a menu test has no slate, but its music starts with its first frames: image f00001 is MENU_LEAD after the dump's
    first sound. --presses (dump frames that make a sound: the lab's button presses; a menu run's dump frame is its loop
    frame) re-measures that lead: the offset where the high frequencies rise most sharply at every press (the music runs
    under them, so plain onsets drown).
Game renders and game audio: keep OUT outside the repo.
"""
import argparse, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'machinima'))
from plates import is_slate  # noqa: E402


def onsets(y, sr, th=0.02):
    m = np.abs(y).max(axis=1); h = max(1, int(sr * 0.002))
    env = np.array([m[i:i + h].max() for i in range(0, len(m) - h, h)])
    return np.array([i * h for i in range(1, len(env)) if env[i] > th and env[i - 1] <= th]) / sr


MENU_LEAD = 0.024   # s: a menu run's image f00001 after its music's first sample (measured on the costume CSS run with nine
                    # presses: --presses re-measures it)


def frame1_time(run, y, sr, presses):
    """The dump time (s) of image f00001."""
    on = onsets(y, sr)
    if len(on) == 0: return None, 'no sound'
    if is_slate(os.path.join(run, 'f00001.png')):
        return on[0], f'slate click at {on[0]:.3f}s'
    start = np.nonzero(np.abs(y).max(axis=1) > 0.01)[0][0] / sr      # a menu's music starts with its first frames
    if presses:
        # the menus play music under their sounds, so onsets drown: score each offset by how sharply the high frequencies
        # (the first difference) rise in the 60 ms after every press against the 60 ms before, and take the best
        d = np.diff(y.mean(axis=1)); h = int(sr * 0.005)
        env = np.sqrt(np.add.reduceat(d[:len(d) // h * h] ** 2, np.arange(0, len(d) // h * h, h)) / h)
        floor = np.median(env[env > 1e-5])
        want = (np.array(presses) - 1) / 60.0
        best = (0.0, None)
        for off in np.arange(max(0.0, start - 0.5), start + 0.5, 0.002):
            idx = ((off + want) / 0.005).astype(int)
            if idx.min() < 12 or idx.max() + 12 > len(env): continue
            score = sum(env[i:i + 12].max() / (env[i - 12:i].mean() + floor) for i in idx)
            if score > best[0]: best = (score, off)
        print(f'presses: frame 1 at {best[1]:.3f}s, {best[1] - start:+.3f}s from the music (MENU_LEAD {MENU_LEAD})')
    return start + MENU_LEAD, f'menu music starts at {start:.3f}s, frame 1 {MENU_LEAD}s after'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('run')
    ap.add_argument('--from', dest='f0', type=int, default=1); ap.add_argument('--to', type=int, default=0)
    ap.add_argument('--w', type=int, default=960); ap.add_argument('--crf', type=int, default=20)
    ap.add_argument('--presses', default='')
    a = ap.parse_args()
    n = len([f for f in os.listdir(a.run) if f.startswith('f') and f.endswith('.png')])
    f1 = min(a.to or n, n)
    W0, H0 = Image.open(os.path.join(a.run, f'f{a.f0:05d}.png')).size
    W = a.w // 2 * 2; H = int(round(W * H0 / W0)) // 2 * 2
    wav = None
    src = os.path.join(a.run, 'dsp.wav')
    if os.path.exists(src):
        import soundfile as sf
        y, sr = sf.read(src, always_2d=True)
        t1, why = frame1_time(a.run, y, sr, [int(x) for x in a.presses.split(',') if x])
        print('audio:', why)
        if t1 is not None:
            s0, s1 = int(round((t1 + (a.f0 - 1) / 60) * sr)), int(round((t1 + f1 / 60) * sr))
            seg = y[max(0, s0):max(0, s1)]
            if len(seg) > 1:
                wav = os.path.join(tempfile.gettempdir(), f'reel_{os.getpid()}.wav')
                sf.write(wav, np.clip(seg, -1, 1), sr)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '60', '-i', '-']
    if wav: cmd += ['-i', wav, '-c:a', 'aac', '-b:a', '160k', '-ar', '48000']
    cmd += ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', str(a.crf), '-movflags', '+faststart', a.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for k in range(a.f0, f1 + 1):
            ff.stdin.write(Image.open(os.path.join(a.run, f'f{k:05d}.png')).convert('RGB').resize((W, H), Image.LANCZOS).tobytes())
        ff.stdin.close(); ff.wait()
    finally:
        if wav and os.path.exists(wav): os.remove(wav)
    print(f'wrote {a.out}: frames {a.f0}-{f1} ({(f1 - a.f0 + 1) / 60:.1f} s) {W}x{H}', 'with audio' if wav else 'without audio')


if __name__ == '__main__':
    main()
