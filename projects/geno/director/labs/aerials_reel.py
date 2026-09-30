"""A reel of every move in aerials_lab captures of Geno alone (AERIALS_CAST=none): the runs side by side (e.g. the side
view, the 3/4 view and the side view with hitboxes; same lab, same inputs, so their frames line up), each cropped round
his logged position, labelled with the slot and his motion state, with the first run's game audio, as an mp4 at 60 fps.

    .venv/bin/python projects/geno/director/labs/aerials_reel.py OUT.mp4 RUN [RUN ...] [--w 400] [--from S --to S]
Each RUN is a dolphin.py folder with RUN.plan.json beside it (or director/build/aerials_lab.plan.json). Frames stream
straight into ffmpeg (no temporary images). The audio: the director clicks on the opening slate's first frame, so the
DSP dump (dsp.wav, from emulator boot) is cut from that click, script frame s at (slate + s + LAG) frames after it (the
image of logic frame s, as the strips place it), at the dump's measured rate when the closing slate's click is in the
capture, else its nominal rate. Game data: keep the output outside the repo.
"""
import argparse, json, math, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aerials_strips as A
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'machinima'))
from plates import is_slate


AUDIO_LATENCY = 2    # frames: a sound started on logic frame s is heard 2 frames after its image (measured: the jump and
                     # Hand Gun sounds of aerials_lab's fair, 186 and 198, onset at 188 and 200 with no correction)


def audio(run, d, s_from, s_to, out, fps=60, sr_out=48000):
    """The game audio for script frames s_from..s_to of this run, as a wav (None when the run has no usable dump)."""
    import soundfile as sf
    from scipy.signal import resample
    src = os.path.join(run, 'dsp.wav')
    if not os.path.exists(src): return None
    y, sr = sf.read(src, always_2d=True)
    m = np.abs(y).max(axis=1); h = max(1, int(sr * 0.002))
    env = np.array([m[i:i + h].max() for i in range(0, len(m), h)])
    on = [i * h for i in range(1, len(env)) if env[i] > 0.02 and env[i - 1] <= 0.02]
    if not on: return None
    fs = d['frames']; i0 = d['s0']                      # the first image after the opening slate
    k = i0 - 1
    while k >= 0 and is_slate(os.path.join(run, fs[k])): k -= 1
    slate = i0 - (k + 1)                                # the opening slate's length in images
    rate = sr                                           # dump samples per film second
    j = i0
    while j < len(fs) and not is_slate(os.path.join(run, fs[j])): j += 1
    if j < len(fs):                                     # the closing slate is in the capture: measure the rate
        want = (j - (k + 1)) / fps * sr
        c1 = min(on, key=lambda o: abs(o - on[0] - want))
        if abs(c1 - on[0] - want) < 0.02 * sr: rate = (c1 - on[0]) / ((j - (k + 1)) / fps)
    lag = A.LAG + AUDIO_LATENCY
    a0 = int(round(on[0] + (slate + s_from + lag) / fps * rate))
    a1 = int(round(on[0] + (slate + s_to + lag) / fps * rate))
    seg = y[max(0, a0):max(0, a1)]
    if len(seg) < 2: return None
    seg = resample(seg, int(round((s_to - s_from) / fps * sr_out)), axis=0)
    sf.write(out, np.clip(seg, -1, 1), sr_out)
    print(f'audio: click {on[0] / sr:.3f}s, slate {slate}, rate {rate:.1f}/s, script {s_from}..{s_to}')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('runs', nargs='+')
    ap.add_argument('--w', type=int, default=400); ap.add_argument('--dist', type=float, default=84)
    ap.add_argument('--at', type=float, default=22); ap.add_argument('--crf', type=int, default=20)
    ap.add_argument('--from', dest='s_from', type=int, default=0); ap.add_argument('--to', type=int, default=0)
    ap.add_argument('--ports', default='0', help="each run's ports to crop, side by side (cancel_lab: 0,1,2,3)")
    ap.add_argument('--names', default='', help='a label per column')
    ap.add_argument('--wide', action='store_true', help='whole frames, no crop (one column per run)')
    a = ap.parse_args()
    runs = [A.load(r) for r in a.runs]
    pp = a.runs[0].rstrip('/') + '.plan.json'
    plan = json.load(open(pp if os.path.exists(pp) else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build',
                                                                       'aerials_lab.plan.json')))
    W0, H0 = Image.open(os.path.join(a.runs[0], runs[0]['frames'][0])).size
    sc = H0 / (2 * a.dist * math.tan(math.radians(15)))
    hw, hh = 12.0, 14.0
    cw, ch = a.w, int(a.w * hh / hw) // 2 * 2
    if a.wide:
        ch = int(a.w * H0 / W0) // 2 * 2
    s0 = a.s_from or plan[0]['start'] - 10
    s1 = a.to or plan[-1]['start'] + plan[-1]['frames']
    s1 = min([s1] + [d['s0'] + len(d['frames']) - d['s0'] - A.LAG - 1 for d in runs])   # what every capture holds
    ports = [int(x) for x in a.ports.split(',')]
    cols = [(d, p) for d in runs for p in (ports if not a.wide else ports[:1])]
    names = a.names.split(',') if a.names else []
    W, H = cw * len(cols), ch + 28
    wav = audio(a.runs[0], runs[0], s0, s1, os.path.join(tempfile.gettempdir(), f'reel_{os.getpid()}.wav'))
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '60', '-i', '-']
    if wav: cmd += ['-i', wav, '-c:a', 'aac', '-b:a', '160k', '-shortest']
    cmd += ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', str(a.crf), a.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for s in range(s0, s1):
            slot = next((p['label'] for p in plan if p['start'] <= s < p['start'] + p['frames']), '')
            img = Image.new('RGB', (W, H), (22, 22, 30))
            dr = ImageDraw.Draw(img)
            cache = {}
            for i, (d, port) in enumerate(cols):
                idx = d['s0'] + s + A.LAG
                if not 0 <= idx < len(d['frames']): continue
                key = (d['run'], idx)
                if key not in cache: cache[key] = Image.open(os.path.join(d['run'], d['frames'][idx])).convert('RGB')
                im = cache[key]
                x, y = d['pos'][port].get(s, d['pos'][port].get(s - 1, (0.0, 0.0)))
                cx, cy = W0 / 2 + x * sc, H0 / 2 - (y + 7.5 - a.at) * sc
                box = (int(cx - hw * sc), int(cy - hh * sc), int(cx + hw * sc), int(cy + hh * sc))
                img.paste((im if a.wide else im.crop(box)).resize((cw, ch), Image.LANCZOS), (i * cw, 28))
                if i < len(names): dr.text((i * cw + 8, 32), names[i], fill=(255, 230, 120))
            st = A.state_at(runs[0]['ms'][0], s)
            dr.text((8, 7), f'{slot}   {A.MSNAME.get(st[1], st[1]) if st else ""}   (frame {s})', fill=(240, 235, 200))
            ff.stdin.write(img.tobytes())
        ff.stdin.close(); ff.wait()
        print('wrote', a.out, s1 - s0, 'frames', 'with audio' if wav else 'without audio')
    finally:
        if wav and os.path.exists(wav): os.remove(wav)


if __name__ == '__main__':
    main()
