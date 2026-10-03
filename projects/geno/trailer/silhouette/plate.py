"""A trailer plate from a Dolphin capture: OUT/take.mp4 (the frames at native size with the game audio), OUT/take.wav (the
same audio alone) and OUT/info.json, for the editor (~/games/melee/trailer_refs/production/plates/<shot>/).
    plate.py RUN OUT --shot 1.1 --from F --to F --anchor F [--pad-head N] [--in F] [--event NAME=F ...] [--note TEXT]
Frames F are the dump's (f00001.png is 1). The game's DSP dump starts at emulator boot, an unmeasured time before the first
image, so the audio is placed by an anchor: --anchor is the dump frame that started the capture's first sound (a menu's
music or jingle starts on the frame that asks for it: the challenger screen's on its first frame, the prize screen's on its
first message), and that sound's first audible sample (over 0.01) is put on it. A stream's own load latency is part of
what the game does either way. --pad-head N puts N frames of black (and silence) before F, for a handle where the game
has nothing before its first frame (a director boot goes straight into the screen). In info.json every frame number is
the take's (0 is its first frame) unless named dump_*.
"""
import argparse, json, os, subprocess, tempfile
import numpy as np
import soundfile as sf
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run'); ap.add_argument('out')
    ap.add_argument('--shot', required=True)
    ap.add_argument('--from', dest='f0', type=int, required=True); ap.add_argument('--to', type=int, required=True)
    ap.add_argument('--anchor', type=int, required=True)
    ap.add_argument('--pad-head', type=int, default=0)
    ap.add_argument('--in', dest='fin', type=int, required=True, help='dump frame: the first frame worth showing')
    ap.add_argument('--event', action='append', default=[], help='NAME=DUMP_FRAME')
    ap.add_argument('--note', default='')
    ap.add_argument('--crf', type=int, default=14)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    y, sr = sf.read(os.path.join(a.run, 'dsp.wav'), always_2d=True)
    loud = np.nonzero(np.abs(y).max(axis=1) > 0.01)[0]
    onset = loud[0] / sr
    t1 = onset - (a.anchor - 1) / 60.0                       # the dsp.wav time of image f00001
    pad = a.pad_head
    # the audio under the padding is the game's own (silence before the screen, or a sound's first instant), and the dump's
    # audio, which ends a little before its last images, is filled out with silence to the take's length
    s0 = int(round((t1 + (a.f0 - 1 - pad) / 60.0) * sr)); s1 = int(round((t1 + a.to / 60.0) * sr))
    seg = y[max(0, s0):min(s1, len(y))]
    if s0 < 0: seg = np.vstack([np.zeros((-s0, y.shape[1])), seg])
    want = s1 - s0
    if len(seg) < want: seg = np.vstack([seg, np.zeros((want - len(seg), y.shape[1]))])
    wav = os.path.join(a.out, 'take.wav')
    sf.write(wav, np.clip(seg, -1, 1), sr, subtype='PCM_16')
    W, H = Image.open(os.path.join(a.run, f'f{a.fin:05d}.png')).size   # (a boot's first images are 480-line XFBs, smaller)
    W2, H2 = W // 2 * 2, H // 2 * 2
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W2}x{H2}', '-r', '60', '-i', '-',
           '-i', wav, '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', str(a.crf),
           '-movflags', '+faststart', os.path.join(a.out, 'take.mp4')]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    black = bytes(W2 * H2 * 3)
    for _ in range(pad): ff.stdin.write(black)
    resized = []
    for k in range(a.f0, a.to + 1):
        im = Image.open(os.path.join(a.run, f'f{k:05d}.png')).convert('RGB')
        if im.size != (W, H): resized.append(k); im = im.resize((W, H), Image.LANCZOS)
        ff.stdin.write(im.crop((0, 0, W2, H2)).tobytes())
    ff.stdin.close(); ff.wait()
    take = lambda f: f - a.f0 + pad                          # dump frame -> take frame
    n = a.to - a.f0 + 1 + pad
    run_json = json.load(open(os.path.join(a.run, 'run.json'))) if os.path.exists(os.path.join(a.run, 'run.json')) else {}
    info = dict(shot=a.shot, fps=60, w=W2, h=H2, n=n, seconds=round(n / 60, 3),
                **{'in': take(a.fin)}, handle_head=take(a.fin), handle_tail=n - 1 - take(a.fin),
                events={k: take(int(v)) for k, v in (e.split('=') for e in a.event)},
                pad_head=pad, dump_from=a.f0, dump_to=a.to, run=os.path.abspath(a.run), res=run_json.get('res'),
                sync=dict(anchor_dump_frame=a.anchor, first_sound_s=round(onset, 4), rule='the first audible sample of the '
                          'capture is placed on the anchor frame (the frame that started it)'),
                audio=dict(file='take.wav', rate=sr, channels=y.shape[1]), resized_dump_frames=resized, note=a.note)
    json.dump(info, open(os.path.join(a.out, 'info.json'), 'w'), indent=1)
    print(json.dumps(info, indent=1))


if __name__ == '__main__':
    main()
