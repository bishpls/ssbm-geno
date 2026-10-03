"""The gun normals' sounds fitted to their moves (Michael: "some of the gun normal sounds ... linger longer" than the move;
don't extend the animations, cut the sounds to fit). Three shorter versions of bank 55's gun sounds, cut from the
round-3 sources (~/games/melee/work/sfxbank/build: SMRPG ROM renders, game audio, kept local) at their own boundaries:

  550056 GENO_HANDGUN_SHORT    the Hand Gun's rattle (550001, ten 62 ms shots in 0.61 s) cut to its first four shots,
                               ending in the dip after the fourth: 0.242 s, 14.5 frames
  550057 GENO_HANDCANNON_SHORT the Hand Cannon (550002: cock, cock, the boom at 13 frames, then its ring) with the ring
                               faded from 22 frames to silence at 28 (0.467 s)
  550058 GENO_STARGUN_SHORT    the Star Gun's cascade (550004, 48 frames) faded from its second group's end (22 frames)
                               to silence at 27 (0.45 s)
  550059 GENO_HANDCANNON_COCK  the Hand Cannon's second trigger alone (0.098-0.200 s: the "arm-cock", 6 frames)
  550060 GENO_HANDCANNON_BOOM  its third trigger, the boom, and its ring (from 0.200 s; the ring faded out as 550057's)
  550061 GENO_HANDCANNON_SHOT  the back throw's one chunky single-shot blast (Michael, 2026-09-29: the Hand Cannon fires
                               several large shots and 550002's cock-cock-boom read as a double shot): SMRPG's Hand
                               Cannon shot fired once (ROM 109, the boom 550060 cuts from the triple), two semitones
                               lower, with a hard attack and a low thump of our own under it (shot(), below), 22050 Hz

The Hand Cannon is SMRPG's sound 109 triggered three times, 6 frames apart (0, 0.098, 0.200 s): two "arm-cocks", then the
boom that rings. Played whole on the shot's frame, its boom came 12 frames after the shot (Michael: "the sound is coming
out delayed"). Cut in two, the cock is cued 6 frames before the shot (5 on the down smash, whose charge sits between) and
the boom on the shot itself, so the boom lands on the first active frame and the cock-boom rhythm is the SNES's.

Each target is the shortest window its weapon form's moves leave between the sound's frame and the move's end (the
forward tilt's 23 frames for the Hand Gun, the back air's 28 for the Hand Cannon, the up air's 27 for the Star Gun).
The originals stay in the bank for anything else that plays them. Writes the WAVs and gunfit.json (with the timed
sounds' entries before them, so cheer/bank.py appends 550053-550058 in order) to OUT (default
~/games/melee/work/sfxbank/gunfit):
    .venv/bin/python projects/geno/sound/gunfit.py [OUT]
    .venv/bin/python projects/geno/sound/cheer/bank.py CHANT.wav OUT/gunfit.json --out OUT/bank     # the bank, the sems
    .venv/bin/python projects/geno/sound/cheer/bank.py --install OUT/bank                           # into $MELEE_DISC
The decomp's gate (lbaudio_ax.c LBAX_GENO_SFX_LAST) must reach 550058, or the new ids stay silent.
"""
import json, os, sys

import numpy as np
import soundfile as sf

SFXBANK = os.path.expanduser(os.environ.get('SFXBANK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'sfxbank')))
SRC = os.path.join(SFXBANK, 'build')
TIMED = os.path.join(SFXBANK, 'timed', 'timed.json')
FPS = 60.0

# (sound id, name, source, keep seconds, fade start seconds, the source's id, why[, start seconds])
CUTS = [
    (550056, 'GENO_HANDGUN_SHORT', '01_GENO_HANDGUN.wav', 0.242, 0.228, 550001,
     'the first four of the rattle\'s ten 62 ms shots, ending in the dip after the fourth (14 ms fade)'),
    (550057, 'GENO_HANDCANNON_SHORT', '02_GENO_HANDCANNON.wav', 28 / FPS, 22 / FPS, 550002,
     'cock, cock and the boom (13 frames) whole; the ring faded out over frames 22-28'),
    (550058, 'GENO_STARGUN_SHORT', '04_GENO_STARGUN.wav', 27 / FPS, 22 / FPS, 550004,
     'the cascade\'s first two groups whole; faded out over frames 22-27'),
    (550059, 'GENO_HANDCANNON_COCK', '02_GENO_HANDCANNON.wav', 0.200, 0.197, 550002,
     'the second trigger alone, between the retrigger dips at 0.098 and 0.200 s (3 ms fade)', 0.098),
    (550060, 'GENO_HANDCANNON_BOOM', '02_GENO_HANDCANNON.wav', 28 / FPS, 22 / FPS, 550002,
     'the third trigger (the boom) from its retrigger dip at 0.200 s and its ring, faded over the original\'s frames '
     '22-28 as 550057', 0.200),
]
VOL, PRIO, AUX = 204, 15, 1          # the originals' script: 01 smp | FD smp | 10 01 | 04 0F | 06 CC | 0E


def cut(x, sr, keep, fade0, start=0.0):
    """x from `start` to `keep` seconds (the source's times), faded out from fade0 (a raised cosine)"""
    a, n, f0 = int(round(start * sr)), int(round(keep * sr)), int(round(fade0 * sr))
    y = x[a:n].astype(np.float64).copy()
    k = n - f0
    y[f0 - a:] *= 0.5 * (1 + np.cos(np.linspace(0, np.pi, k)))
    return y


# ---- 550061: one chunky single-shot blast (the back throw)
SINGLE = os.path.join(os.path.expanduser(os.environ.get('SMRPG_SFX', '~/games/smrpg/sfx')), 'geno', 'extra', 'HANDCANNON_SINGLE.wav')   # ROM 109 fired once (the boom)
SHOT_RATE = 22050             # Melee's rate for its short hits; the bank has 8000 bytes of its booking left
SHOT = dict(pitch=-2.0,       # semitones: the SMRPG boom a little heavier, its falling ring kept
            thump=(92.0, 44.0, 0.055, 0.30), thump_db=-1.0,   # a sine sweeping 92 -> 44 Hz, 55 ms decay, 0.30 s long
            click_ms=4.0, click_db=-4.0,                      # a 4 ms noise click on the first sample: the hard attack
            attack_db=6.0, attack_ms=20.0,                    # the boom's first 20 ms lifted 6 dB, easing to 0 ...
            swell_db=-4.0, swell=(0.03, 0.14),                # ... and its swell (30-140 ms, where it peaked) eased 4 dB
            keep=0.40, fade0=0.30)                            # to 0.40 s, faded out from 0.30 s (the ring)


def shot(p=SHOT):
    """The single shot: ROM 109 (mono, pitched), a low thump and a noise click on its first sample, the attack lifted,
    faded out; peak -3 dBFS. Returns (samples at SHOT_RATE, float)."""
    from scipy.signal import resample_poly
    x, sr = sf.read(SINGLE)
    x = x.mean(axis=1) if x.ndim > 1 else x
    lo = np.nonzero(np.abs(x) > 1e-3)[0][0]                    # from its first sound
    x = x[lo:]
    ratio = 2 ** (p['pitch'] / 12.0)                          # slower playback lowers the pitch
    up, dn = int(round(SHOT_RATE / ratio)), sr
    g = np.gcd(up, dn)
    y = resample_poly(x, up // g, dn // g)
    t = np.arange(len(y)) / SHOT_RATE
    y *= 1 + (10 ** (p['attack_db'] / 20) - 1) * np.clip(1 - t / (p['attack_ms'] / 1000), 0, 1)
    a, b = p['swell']                                         # a raised-cosine dip over the swell, so the attack is the peak
    w = np.where((t > a) & (t < b), 0.5 * (1 - np.cos(2 * np.pi * (t - a) / (b - a))), 0.0)
    y *= 10 ** (p['swell_db'] * w / 20)
    f0, f1, tau, length = p['thump']
    nt = int(length * SHOT_RATE)
    tt = np.arange(nt) / SHOT_RATE
    freq = f1 + (f0 - f1) * np.exp(-tt / 0.06)
    th = np.sin(2 * np.pi * np.cumsum(freq) / SHOT_RATE) * np.exp(-tt / tau) * (1 - np.exp(-tt / 0.0015))
    rng = np.random.default_rng(61)
    nc = int(p['click_ms'] / 1000 * SHOT_RATE)
    click = rng.standard_normal(nc) * np.exp(-np.arange(nc) / (nc / 3))
    pk = np.abs(y).max()
    out = np.zeros(max(len(y), nt))
    out[:len(y)] += y
    out[:nt] += th * pk * 10 ** (p['thump_db'] / 20)
    out[:nc] += click / np.abs(click).max() * pk * 10 ** (p['click_db'] / 20)
    n, f0i = int(p['keep'] * SHOT_RATE), int(p['fade0'] * SHOT_RATE)
    out = out[:n]
    out[f0i:] *= 0.5 * (1 + np.cos(np.linspace(0, np.pi, n - f0i)))
    return out / np.abs(out).max() * 10 ** (-3 / 20)


def main():
    out = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else os.path.join(SFXBANK, 'gunfit'))
    os.makedirs(out, exist_ok=True)
    entries = json.load(open(TIMED))
    for sid, name, src, keep, fade0, orig, why, *start in CUTS:
        x, sr = sf.read(os.path.join(SRC, src), dtype='int16')
        y = cut(x, sr, keep, fade0, *start)
        wav = os.path.join(out, f'{sid}_{name}.wav')
        sf.write(wav, np.round(y).astype(np.int16), sr, subtype='PCM_16')
        peak = 20 * np.log10(np.abs(y).max() / 32768)
        entries.append(dict(sound_id=sid, name=name, wav=wav, rate=sr, samples=len(y), dur=round(len(y) / sr, 3),
                            frames=round(len(y) / sr * FPS, 1), source=os.path.join(SRC, src), source_id=orig,
                            edits=[why], peak_dbfs=round(float(peak), 2), vol=VOL, prio=PRIO, aux=AUX))
        print(f'{sid} {name:22s} {len(x) / sr:.3f} s -> {len(y) / sr:.3f} s ({len(y) / sr * FPS:.1f} frames), peak {peak:.1f} dBFS')
    y = shot()
    wav = os.path.join(out, '550061_GENO_HANDCANNON_SHOT.wav')
    sf.write(wav, np.round(y * 32767).astype(np.int16), SHOT_RATE, subtype='PCM_16')
    entries.append(dict(sound_id=550061, name='GENO_HANDCANNON_SHOT', wav=wav, rate=SHOT_RATE, samples=len(y),
                        dur=round(len(y) / SHOT_RATE, 3), frames=round(len(y) / SHOT_RATE * FPS, 1), source=SINGLE,
                        source_id=550002, edits=[f'the back throw\'s single shot: {SHOT}'], peak_dbfs=-3.0, vol=VOL,
                        prio=PRIO, aux=AUX))
    print(f'550061 GENO_HANDCANNON_SHOT     {len(y) / SHOT_RATE:.3f} s ({len(y) / SHOT_RATE * FPS:.1f} frames), {SHOT_RATE} Hz')
    json.dump(entries, open(os.path.join(out, 'gunfit.json'), 'w'), indent=1)
    print(os.path.join(out, 'gunfit.json'), [e['sound_id'] for e in entries])


if __name__ == '__main__':
    main()
