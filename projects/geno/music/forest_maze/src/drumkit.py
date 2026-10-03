"""DrumGizmo kit sampler (the Aasimonster2 kit, CC-BY 4.0, drumgizmo.org): multi-mic samples mixed to six stereo buses
(kick, snare, toms, cymbal spot mics, overheads, room), each processed, then summed. Velocity picks the sample by power,
with round-robin among the nearest; double-kick alternates the two kick drums; open hi-hat is choked by the next closed one.
    kit = Kit(); st = kit.render(events, total_s)   events: (t, piece, velocity 0..1)"""
import os, glob, numpy as np, soundfile as sf
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
import xml.etree.ElementTree as ET
from pedalboard import Pedalboard, HighpassFilter, LowpassFilter, PeakFilter, Compressor, LowShelfFilter, HighShelfFilter, Gain

KIT = os.path.join(MUSIC, 'drums/aasimonster2')
SR = 48000
PIECES = {'kick': ['kick_r', 'kick_l'], 'snare': ['snare_on_center'], 'rim': ['snare_rim_shot'],
          'hat': ['hihat_closed1', 'hihat_closed2'], 'hatopen': ['hihat_open'], 'ride': ['ride'], 'bell': ['ride_bell1'],
          'crash1': ['crash1'], 'crash2': ['crash2'], 'china': ['china_18_inch'], 'tom1': ['tom_1'], 'tom2': ['tom_2'],
          'tom3': ['tom_3'], 'ftom': ['tom_4']}
# mic channel -> (bus, pan -1..1, gain, polarity)
MICS = {'Kick L': ('kick', 0.0, 1.0, 1), 'Kick R': ('kick', 0.0, 1.0, 1),
        'Snare top': ('snare', 0.0, 1.0, 1), 'Snare bottom': ('snare', 0.0, 0.45, -1),
        'Tom1': ('toms', -0.45, 1.0, 1), 'Tom2': ('toms', -0.15, 1.0, 1), 'Tom3': ('toms', 0.2, 1.0, 1), 'Tom4': ('toms', 0.5, 1.0, 1),
        'Hihat': ('spots', -0.55, 0.7, 1), 'Ride': ('spots', 0.55, 0.7, 1),
        'OH L': ('oh', -0.85, 1.0, 1), 'OH R': ('oh', 0.85, 1.0, 1), 'Amb L': ('room', -1.0, 1.0, 1), 'Amb R': ('room', 1.0, 1.0, 1)}
BUSES = ['kick', 'snare', 'toms', 'spots', 'oh', 'room']


def _pan(p):
    a = (p + 1) * np.pi / 4
    return np.array([np.cos(a), np.sin(a)], np.float32)


class Kit:
    def __init__(self, kit=KIT, seed=0):
        self.inst = {}
        for name in set(sum(PIECES.values(), [])):
            x = ET.parse(os.path.join(kit, name, name + '.xml')).getroot()
            samples = []
            for s in x.iter('sample'):
                files = {}
                for af in s.iter('audiofile'):
                    files[af.get('channel')] = (os.path.join(kit, name, af.get('file')), int(af.get('filechannel')))
                samples.append((float(s.get('power')), files))
            samples.sort(key=lambda z: z[0])
            self.inst[name] = samples
        self.cache = {}
        self.rng = np.random.default_rng(seed)
        self.rr = {}

    def _sample(self, name, idx):
        key = (name, idx)
        if key not in self.cache:
            power, files = self.inst[name][idx]
            path = next(iter(files.values()))[0]
            data, sr = sf.read(path, dtype='float32', always_2d=True)
            if sr != SR:   # the kit is 44.1 kHz
                from scipy.signal import resample_poly
                from math import gcd
                gg = gcd(SR, sr); data = resample_poly(data, SR // gg, sr // gg, axis=0).astype(np.float32)
            buses = {}
            for ch, (p, fc) in files.items():
                if ch not in MICS: continue
                bus, pan, g, pol = MICS[ch]
                sig = data[:, fc - 1] * g * pol
                buses.setdefault(bus, np.zeros((2, len(sig)), np.float32))
                buses[bus] += _pan(pan)[:, None] * sig[None]
            self.cache[key] = (power, buses)
        return self.cache[key]

    def pick(self, name, vel):
        samples = self.inst[name]
        pw = np.array([s[0] for s in samples]); pw = pw / pw.max()
        target = vel ** 1.3
        order = np.argsort(np.abs(pw - target))[:3]
        k = self.rr.get(name, 0); self.rr[name] = k + 1
        idx = int(order[(k + self.rng.integers(0, 2)) % len(order)])
        return idx, target / max(pw[idx], 1e-3)

    def render(self, events, total):
        n = int(total * SR)
        bus = {b: np.zeros((2, n + SR * 6), np.float32) for b in BUSES}
        kick_alt = 0
        events = sorted(events, key=lambda e: e[0])
        open_hats = []   # (start index, name, idx) to choke
        for (t, piece, vel) in events:
            names = PIECES[piece]
            if piece == 'kick':
                name = names[kick_alt % 2]; kick_alt += 1
            else:
                name = names[self.rng.integers(0, len(names))]
            idx, corr = self.pick(name, vel)
            power, bz = self._sample(name, idx)
            i0 = max(0, int(round(t * SR)))
            g = float(np.clip(corr, 0.5, 1.6)) ** 0.5
            L = None
            if piece == 'hat' and open_hats:   # choke ringing open hats
                for (j0, oname, oidx, oL) in open_hats:
                    _, obz = self._sample(oname, oidx)
                    for b, sig in obz.items():
                        a = i0 - j0; rem = min(oL - a, 2400)
                        if 0 < a < oL:
                            fade = np.linspace(1, 0, min(1200, oL - a))
                            seg = sig[:, a:a + len(fade)] * (1 - fade)[None]   # subtract the tail progressively
                            bus[b][:, i0:i0 + len(fade)] -= seg[:, :bus[b].shape[1] - i0] if i0 + len(fade) > bus[b].shape[1] else seg
                            tail = sig[:, a + len(fade):]
                            e = min(bus[b].shape[1], i0 + len(fade) + tail.shape[1])
                            bus[b][:, i0 + len(fade):e] -= tail[:, :e - i0 - len(fade)]
                open_hats = []
            for b, sig in bz.items():
                e = min(bus[b].shape[1], i0 + sig.shape[1])
                bus[b][:, i0:e] += g * sig[:, :e - i0]
                L = sig.shape[1]
            if piece == 'hatopen':
                open_hats.append((i0, name, idx, L))
        return self.mixdown(bus, n)

    def mixdown(self, bus, n):
        chains = {
            'kick': Pedalboard([HighpassFilter(32), PeakFilter(62, 4.0, 1.0), PeakFilter(380, -7.0, 1.2), PeakFilter(4200, 6.0, 1.0),
                                Compressor(-20, 4, 2, 60), Gain(2)]),
            'snare': Pedalboard([HighpassFilter(90), PeakFilter(220, 3.0, 1.0), PeakFilter(900, -3, 1.0), PeakFilter(5500, 4.0, 0.8),
                                 Compressor(-18, 3.5, 3, 90), Gain(2)]),
            'toms': Pedalboard([HighpassFilter(60), PeakFilter(450, -5, 1.0), PeakFilter(4000, 3.0, 1.0), Compressor(-18, 3, 3, 120)]),
            'spots': Pedalboard([HighpassFilter(350), HighShelfFilter(9000, -2.0), LowpassFilter(15000)]),
            'oh': Pedalboard([HighpassFilter(250), PeakFilter(3000, -1.5, 1.0), HighShelfFilter(9000, -3.0), LowpassFilter(15000)]),
            'room': Pedalboard([HighpassFilter(120), Compressor(-26, 6, 5, 120), LowpassFilter(9000)]),
        }
        levels = {'kick': 0.0, 'snare': -1.0, 'toms': -3.0, 'spots': -9.0, 'oh': -3.0, 'room': -8.0}
        out = np.zeros((2, n), np.float32)
        for b in BUSES:
            x = chains[b](bus[b], SR)[:, :n]
            rms = np.sqrt(np.mean(x ** 2)) + 1e-9
            out += x * (10 ** (levels[b] / 20)) * (0.05 / rms if b in ('kick', 'snare') else 0.05 / max(rms, 1e-9) * 0.7)
        out = Pedalboard([Compressor(-14, 2.5, 8, 100)])(out, SR)
        return out


if __name__ == '__main__':
    import sys, time
    import drumpat as D
    k = Kit()
    ev = D.pattern('skank16', 0, 2, fill=True) + D.pattern('half16', 4.8, 1) + D.hits([0], 7.2, china=True)
    t0 = time.time(); st = k.render(ev, 10.0); print('rendered', round(time.time() - t0, 1), 's; peak', float(np.abs(st).max()))
    sf.write(os.path.join(MUSIC, 'analysis/drum_test.wav'), (st / np.abs(st).max() * 0.9).T, SR)
