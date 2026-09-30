"""Line a lab run's dumped images up with the director's logic frames, segment by segment.

Dolphin's dump can drop images on heavy frames (hits, effects, hitbox display), so one constant offset drifts. A lab that
shows a two-frame magenta sync slate before each segment (fx_lab, downb_lab; plan['sync'] = its logic frame) gets a
per-segment offset instead: the image of logic frame s is (the slate's first image) + (s - sync) + SYNC_CAL
(labs/aerials_strips.py's calibration). A drop inside a segment, after its slate, still shifts what follows it; `check`
reports each segment's offset against the first so a drift shows as a number.

Audio doesn't drop: the dump (dsp.wav) runs from emulator boot, and the director clicks on the opening slate's first
image, so logic frame s is heard at click + (opening slate length + s + AUDIO_LAG) / 60 s (aerials_reel.py's timing).
"""
import json, os, sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'machinima'))
from plates import is_slate  # noqa: E402

SYNC_CAL = -1
AUDIO_LAG = -1          # aerials_reel: LAG (-3) + the audio latency (+2)


def images(run):
    """Every dumped image of the run, sorted (file names f00001.png ...)."""
    return sorted(f for f in os.listdir(run) if f.startswith('f') and f.endswith('.png') and f[1:-4].isdigit())


def slates(run, fs):
    """(first, last) positions in fs of each magenta slate, cached in the run folder."""
    cache = os.path.join(run, 'slates.json')
    if os.path.exists(cache):
        c = json.load(open(cache))
        if c.get('n') == len(fs):
            return [tuple(r) for r in c['runs']]
    sl = [is_slate(os.path.join(run, f)) for f in fs]
    runs, i = [], 0
    while i < len(fs):
        if sl[i]:
            j = i
            while j + 1 < len(fs) and sl[j + 1]:
                j += 1
            runs.append((i, j)); i = j + 1
        else:
            i += 1
    json.dump(dict(n=len(fs), runs=runs), open(cache, 'w'))
    return runs


class Run:
    def __init__(self, run, plan):
        self.run, self.plan = run, plan
        self.fs = images(run)
        sl = slates(run, self.fs)
        self.opening = sl[0]                                   # the director's opening slate
        self.offsets = []                                      # per segment: (plan entry, image position - logic frame)
        segs = sl[1:1 + len(plan)]                             # the k-th slate after the opening is segment k's
        if len(segs) < len(plan):
            raise SystemExit(f'{run}: {len(segs)} sync slates for {len(plan)} segments')
        for seg, r in zip(plan, segs):
            off = r[0] - seg['sync'] + SYNC_CAL
            if self.offsets and not -12 <= off - self.offsets[-1][1] <= 2:
                raise SystemExit(f'{run}: segment {seg["label"]}\'s slate at image {r[0]} is off by {off - self.offsets[-1][1]}')
            self.offsets.append((seg, off))

    def segment(self, label):
        for seg, off in self.offsets:
            if seg['label'] == label:
                return seg, off
        raise KeyError(label)

    def path(self, label, rel):
        """The image of `rel` logic frames after the segment's start."""
        seg, off = self.segment(label)
        i = seg['start'] + rel + off
        return os.path.join(self.run, self.fs[i]) if 0 <= i < len(self.fs) else None

    def check(self):
        base = self.offsets[0][1]
        return {seg['label']: off - base for seg, off in self.offsets}

    def audio_at(self, s, click, sr):
        """The dump sample where logic frame s is heard."""
        n_open = self.opening[1] - self.opening[0] + 1
        return int(round(click + (n_open + s + AUDIO_LAG) / 60 * sr))


def click(run):
    """The opening slate's click in the run's dsp.wav: (samples, sample rate), or None."""
    import soundfile as sf
    src = os.path.join(run, 'dsp.wav')
    if not os.path.exists(src):
        return None, None, None
    y, sr = sf.read(src, always_2d=True)
    m = np.abs(y).max(axis=1); h = max(1, int(sr * 0.002))
    env = np.array([m[i:i + h].max() for i in range(0, len(m), h)])
    on = [i * h for i in range(1, len(env)) if env[i] > 0.02 and env[i - 1] <= 0.02]
    return (on[0] if on else None), sr, y


def load(run, plan_path=None):
    plan_path = plan_path or run.rstrip('/') + '.plan.json'
    return Run(run, json.load(open(plan_path)))
