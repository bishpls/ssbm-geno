"""Super Mario RPG's own timed-hit sounds for Geno's bank (bank 55), from the ROM renders in ~/games/smrpg/sfx (rendered
from the cartridge's sound driver; see its NOTES.md). The SNES battle scripts play two sounds on a successful timed
press (every PlaySound within a few commands after a TimingFor...ButtonPress in the disassembled battle animations):
  172 "weapon timing": 7 sites, the timed weapon hits (Geno's weapon wrapper 0x358B57 and the other allies'): a run of nine
      bright bell pings over 0.46 s, the timed-hit "ding" and its sparkle (the rainbow-star sprite it draws is silent);
  078 "timed stat boost": 5 sites, the timed specials (Geno Boost, the Whirl's 9999 with its blue flash, ...): a bright
      noise burst over 0.9 s. It is already in the bank as GENO_WHIRL_CRIT (550020, 0-0.80 s).
The Geno Beam itself (TimingForChargePress) plays nothing when a charge level lights; its stars are silent sprites.

Built the round-3 way (~/games/melee/work/sfxbank/tools/build_sounds_rom.py): mono (the renders are dual-mono), 40 Hz
high-pass, 32 kHz as rendered, peak -3 dBFS, max momentary loudness held inside Mario's bank range (-16..-8 LUFS).
    .venv/bin/python projects/geno/sound/timed.py [OUT]      # -> OUT (default ~/games/melee/work/sfxbank/timed)/*.wav + timed.json
"""
import json, os, sys

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

ROM = os.path.expanduser(os.environ.get('SMRPG_SFX', '~/games/smrpg/sfx'))   # capture/'s renders (SMRPG_SFX)
SR = 32000
PEAK_DB, LUFS_MAX, LUFS_MIN = -3.0, -8.0, -16.0


def load(rel):
    x, sr = sf.read(os.path.join(ROM, rel))
    assert sr == SR
    return x.mean(1) if x.ndim > 1 else x


def trim_lead(x, rel_db=-50):
    i = int(np.argmax(np.abs(x) > np.abs(x).max() * 10 ** (rel_db / 20)))
    return x[max(0, i - int(0.001 * SR)):]


def fade_out(x, ms):
    n = max(1, int(ms * SR / 1000)); x = x.copy(); x[-n:] *= np.cos(np.linspace(0, np.pi / 2, n)) ** 2; return x


def momentary_max(y):
    m = pyln.Meter(SR, block_size=0.4); w = int(0.4 * SR); h = int(0.05 * SR)
    yy = np.pad(y, (0, max(0, w - len(y))))
    return max(m.integrated_loudness(yy[i:i + w]) for i in range(0, len(yy) - w + 1, h))


def level(y):
    y = y * 10 ** (PEAK_DB / 20) / np.abs(y).max()
    L = momentary_max(y); g = 0.0
    if L > LUFS_MAX:
        g = LUFS_MAX - L
    elif L < LUFS_MIN:
        g = min(LUFS_MIN - L, -0.5 - PEAK_DB)
    y = y * 10 ** (g / 20)
    return y, round(20 * np.log10(np.abs(y).max()), 2), round(momentary_max(y), 1), round(g, 1)


# (sound id, name, source, how, script (vol, prio, aux), use)
SOUNDS = [
    (550054, 'GENO_TIMED_HIT', 'all/172.wav', 'whole (0.46 s: the nine pings); leading silence trimmed; 2 ms end fade',
     (0xCC, 0x11, 1), "the timed press: the Beam's timed release (+10% within 3 frames of a star's flash), Kirby's copy; "
                      "SMRPG plays it on every timed weapon hit"),
    (550055, 'GENO_TIMED_BOOST', 'geno/nosat/GENO_WHIRL_CRIT.wav',
     "0-0.40 s of 0.90 (the burst, before the long tail, so it doesn't bury what follows); 150 ms fade out",
     (0xE5, 0x11, 1), "SMRPG's timed-special sound, cut short: an alternative for the Beam's timed release (the full one "
                      "is 550020, the Whirl crit)"),
]


def build(out):
    os.makedirs(out, exist_ok=True)
    meta = []
    for sid, name, src, how, (vol, prio, aux), use in SOUNDS:
        x = trim_lead(load(src))
        if name == 'GENO_TIMED_BOOST':
            x = fade_out(x[:int(0.40 * SR)], 150)
        y = sosfiltfilt(butter(2, 40, 'highpass', fs=SR, output='sos'), x)
        n = int(0.002 * SR); y[-n:] *= np.cos(np.linspace(0, np.pi / 2, n)) ** 2; y[-1] = 0.0
        y, pk, lufs, g = level(y)
        q = np.clip(np.round(y * 32767), -32768, 32767).astype(np.int16)
        path = os.path.join(out, f'{sid}_{name}.wav')
        sf.write(path, q, SR, subtype='PCM_16')
        meta.append(dict(sound_id=sid, name=name, wav=path, rate=SR, samples=len(q), dur=round(len(q) / SR, 3),
                         source=f'ROM render {src}', edits=[how, '40 Hz high-pass', 'mono (dual-mono render)',
                                                           'peak -3 dBFS' + (f', then {g:+.1f} dB' if g else '')],
                         peak_dbfs=pk, max_momentary_lufs=lufs, vol=vol, prio=prio, aux=aux, use=use))
        print(f'{sid} {name:18s} {len(q) / SR:.3f} s  peak {pk:5.1f} dBFS  max momentary {lufs:5.1f} LUFS  <- {src}')
    json.dump(meta, open(os.path.join(out, 'timed.json'), 'w'), indent=1)
    return meta


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser(os.environ.get('SFXBANK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'sfxbank'))), 'timed'))
