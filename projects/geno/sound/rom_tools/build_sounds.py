"""Build Geno's 28 bank sounds from the SNES clips catalogued in ~/games/melee/work/sfx (CATALOG.md).
Every sound is cut, faded, mixed, pitch-shifted (by resampling) or grain-retimed from those clips only.
Output: build/NN_NAME.wav (32 kHz mono int16, Mario's bank rate) + build/sounds.json (sources, edits, levels)."""
import os, sys, json, subprocess, tempfile
import numpy as np, soundfile as sf, librosa, pyloudnorm as pyln
from scipy.signal import butter, sosfiltfilt

HERE = os.path.expanduser(os.environ.get('SFXBANK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'sfxbank')))   # the bank's work folder (game audio: outside the repo)
SFX = os.path.join(os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work')), 'sfx')   # rounds 1-2's clips
CLIPS = os.path.join(SFX, 'clips')
SR_IN, SR = 48000, 32000
PY = sys.executable

# ---- loudness target: Mario's bank (measured: 31 of 32 clips at 32 kHz, peaks normalised to about -3 dBFS,
# max momentary loudness median -12.3 LUFS, range -21.5..-7.0)
PEAK_DB = -3.0
LUFS_MAX, LUFS_MIN = -8.0, -16.0

def load(name):
    x, sr = sf.read(os.path.join(CLIPS, name + '.wav'))
    assert sr == SR_IN
    return x.mean(1) if x.ndim > 1 else x

CLEAN = os.path.join(HERE, 'src_clean')

def loadc(name):
    """a clean SNES rip from superluigibros.com (44.1 kHz mono, no music), resampled to the 48 kHz working rate"""
    x, sr = sf.read(os.path.join(CLEAN, 'smrpg_' + name + '.wav'))
    x = x.mean(1) if x.ndim > 1 else x
    return librosa.resample(x, orig_sr=sr, target_sr=SR_IN, res_type='soxr_vhq')

def seg(x, a, b=None):
    return x[int(round(a * SR_IN)): (None if b is None else int(round(b * SR_IN)))].copy()

def fade_in(x, ms, sr=SR_IN):
    n = max(1, int(ms * sr / 1000)); x = x.copy(); x[:n] *= np.sin(np.linspace(0, np.pi / 2, n)) ** 2; return x

def fade_out(x, ms, sr=SR_IN):
    n = max(1, int(ms * sr / 1000)); x = x.copy(); x[-n:] *= np.cos(np.linspace(0, np.pi / 2, n)) ** 2; return x

def hp(x, fc=40, sr=SR_IN, order=2):
    return sosfiltfilt(butter(order, fc, 'highpass', fs=sr, output='sos'), x)

def xfade(a, b, ms, sr=SR_IN):
    n = int(ms * sr / 1000); t = np.sin(np.linspace(0, np.pi / 2, n)) ** 2
    return np.concatenate([a[:-n], a[-n:] * (1 - t) + b[:n] * t, b[n:]])

def mix(a, b, at, gain_db=0.0, sr=SR_IN):
    o = int(at * sr); n = max(len(a), o + len(b)); y = np.zeros(n)
    y[:len(a)] += a; y[o:o + len(b)] += b * 10 ** (gain_db / 20); return y

def pitch(x, semitones):
    """Resample so the clip plays `semitones` higher (and shorter) at the same rate: the SNES way to transpose."""
    if semitones == 0: return x
    return librosa.resample(x, orig_sr=SR_IN * 2 ** (semitones / 12), target_sr=SR_IN, res_type='soxr_vhq')

def trim_lead(x, rel_db=-40, pre_ms=2):
    thr = np.abs(x).max() * 10 ** (rel_db / 20)
    i = int(np.argmax(np.abs(x) > thr)); return x[max(0, i - int(pre_ms * SR_IN / 1000)):]

def to_bank(x):
    y = librosa.resample(x, orig_sr=SR_IN, target_sr=SR, res_type='soxr_vhq')
    return y

def momentary_max(y, sr=SR):
    m = pyln.Meter(sr, block_size=0.4); w = int(0.4 * sr); h = int(0.05 * sr)
    yy = np.pad(y, (0, max(0, w - len(y))))
    return max(m.integrated_loudness(yy[i:i + w]) for i in range(0, len(yy) - w + 1, h))

def level(y):
    """Peak to -3 dBFS (HAL's normalisation), then keep max momentary loudness inside Mario's middle range."""
    y = y * 10 ** (PEAK_DB / 20) / np.abs(y).max()
    L = momentary_max(y); g = 0.0
    if L > LUFS_MAX: g = LUFS_MAX - L
    elif L < LUFS_MIN: g = min(LUFS_MIN - L, -0.5 - PEAK_DB)       # never above -0.5 dBFS peak
    y = y * 10 ** (g / 20)
    return y, round(20 * np.log10(np.abs(y).max()), 2), round(momentary_max(y), 1), round(g, 1)

def grain_charge(target_s, x48=None):
    """Grain-drop retime of the SNES charge (the catalogue's method, its script work/scripts/grain_retime.py)."""
    with tempfile.TemporaryDirectory() as d:
        o = os.path.join(d, 'c.wav'); i = os.path.join(CLIPS, 'geno_charge_1.wav')
        if x48 is not None:
            i = os.path.join(d, 'in.wav'); sf.write(i, x48, SR_IN, subtype='PCM_16')
        r = subprocess.run([PY, os.path.join(SFX, 'work/scripts/grain_retime.py'), i, o, str(target_s)],
                           capture_output=True, text=True, check=True)
        x, sr = sf.read(o)
    return (x.mean(1) if x.ndim > 1 else x), r.stdout.strip()

# ------------------------------------------------------------------------------------------------ the sounds
S = []   # (name, builder -> (x at 48 kHz, sources, edits), script params, use)

def add(name, fn, use, vol=0xCC, prio=15, aux=1):
    S.append(dict(name=name, fn=fn, use=use, vol=vol, prio=prio, aux=aux))

def pulse():
    x = seg(loadc('geno_fingershot'), 0.115, 0.175)
    return fade_out(fade_in(x, 0.5), 10), ['CLEAN smrpg_geno_fingershot 0.115-0.175 (pulse 2 of 6)'], ['0.5 ms fade in', '10 ms fade out']
add('GENO_PULSE', pulse, 'jab 1/2 and each rapid-jab hit; down tilt (twice, 4 frames apart); pummel')

def handgun():
    x = seg(load('hand_gun_1'), 0.0, 0.58)
    return fade_out(x, 60), ['hand_gun_1 0.00-0.58 (the burst; the unconfirmed 0.6-1.35 s tail dropped)'], ['60 ms fade out']
add('GENO_HANDGUN', handgun, 'forward tilt, forward air')

def handcannon():
    x = trim_lead(seg(load('hand_cannon_1'), 0.25, 0.92))
    return fade_out(x, 200), ['hand_cannon_1 0.25-0.92 (boom at 0.27; arm-cock noise dropped)'], ['lead trimmed to the boom', '200 ms fade out']
add('GENO_HANDCANNON', handcannon, 'down smash (both sides), back air, down air')

def doublepunch():
    x = seg(load('rocket_punch_hit_1'), 0.0, 0.62)
    return fade_out(x, 220), ['rocket_punch_hit_1 0.00-0.62 (crack + start of the banded ring)'], ['ring shortened from 1.09 s', '220 ms fade out']
add('GENO_DOUBLEPUNCH', doublepunch, 'forward smash (on the hit frame)')

def stargun():
    x = trim_lead(seg(loadc('geno_stargun'), 0.0, 0.80))
    return fade_out(x, 140), ['CLEAN smrpg_geno_stargun 0.00-0.80 (the star cascade)'], ['lead trimmed', 'long 0.8-2.1 s tail dropped', '140 ms fade out']
add('GENO_STARGUN', stargun, 'up smash, up air')

def stargunhit():
    x = trim_lead(seg(loadc('geno_stargunfinish'), 0.0, 0.50))
    return fade_out(x, 150), ['CLEAN smrpg_geno_stargunfinish 0.00-0.50 (the Star Gun hit)'], ['lead trimmed', 'tail to 0.74 s dropped', '150 ms fade out']
add('GENO_STARGUN_HIT', stargunhit, 'up smash / up air on hit')

def nair():
    x = seg(load('geno_whirl_1'), 0.04, 0.44)
    x = pitch(x, 3)
    return fade_out(fade_in(x, 15), 80), ['geno_whirl_1 0.04-0.44 (the swirl)'], ['+3 semitones (resampled) to set it apart from the Whirl', '15 ms fade in', '80 ms fade out']
add('GENO_NAIR_SWIRL', nair, 'neutral air')

def cape():
    x = hp(seg(load('geno_whirl_1'), 0.02, 0.30), 1500, order=4)
    return fade_out(fade_in(x, 20), 90), ['geno_whirl_1 0.02-0.30 (swirl start; no cape sound in SNES)'], ['high-pass 1.5 kHz', '20 ms fade in', '90 ms fade out']
add('GENO_CAPE', cape, 'up tilt (cape swish)')

def projhit():
    x = seg(load('projectile_timed_hit_1'), 0.0, 0.46)
    return fade_out(x, 140), ['projectile_timed_hit_1 0.00-0.46 (median of 3 SNES instances)'], ['140 ms fade out']
add('GENO_PROJ_HIT', projhit, 'Finger Shot / Beam / Star Road hits (projectile hit)')

def fingershot():
    x = seg(loadc('geno_fingershot'), 0.045, 0.315)
    return fade_out(fade_in(x, 0.5), 10), ['CLEAN smrpg_geno_fingershot 0.045-0.315 (4 of the 6 pulses: the move fires four bullets)'], ['cut after pulse 4', '10 ms fade out']
add('GENO_FINGERSHOT', fingershot, 'neutral B tap: Finger Shot')

def charge():
    pu = loadc('geno_powerup')                           # clean: charge 0.05-1.64 s, then the release glide
    climb, log = grain_charge(0.75, seg(pu, 0.048, 1.64))
    top = seg(pu, 1.31, 1.64)                             # the last grains before the release, near the top
    x = xfade(climb, top, 6)
    x = fade_out(fade_in(x, 3), 40)
    return x, ['CLEAN smrpg_geno_powerup 0.048-1.64 (the charge): grain-dropped to 0.75 s', 'CLEAN smrpg_geno_powerup 1.31-1.64 (top grains)'], \
        [f'grain drop to 0.75 s (the catalogue method; {log})', 'then the top grains for the 20-frame grace', '6 ms crossfade', '3/40 ms fades']
add('GENO_BEAM_CHARGE', charge, 'neutral B hold: charge, frames 0-65 (45 to the third star + 20 grace)', vol=0xB2)

def star(n):
    def f():
        coin = loadc('coin')
        st = [0, 4, 7][n - 1]
        if n < 3:
            x = seg(coin, 0.183, 0.56)                    # the second, brighter ding (2.7 kHz)
            srcs = ['CLEAN smrpg_coin 0.183-0.56 (second ding, 2.7 kHz)']
            ed = [f'+{st} semitones (resampled)' if st else 'original pitch']
        else:
            x = seg(coin, 0.062, 0.56)                    # the whole two-step coin for the full charge
            srcs = ['CLEAN smrpg_coin 0.062-0.56 (both dings)']
            ed = [f'+{st} semitones (resampled): the full-charge ding-DING']
        x = pitch(x, st)
        return fade_out(fade_in(x, 2), 110), srcs, ed + ['stars rise 0/+4/+7 semitones (a major triad)', '2/110 ms fades']
    return f
for n in (1, 2, 3):
    add(f'GENO_BEAM_STAR{n}', star(n), f'Beam star {n} (frame {15 * n}); also the Blast/Flash hold stars', vol=0xB2)

def release():
    x = seg(loadc('geno_powerup'), 1.735, 2.00)
    return fade_out(fade_in(x, 3), 80), ['CLEAN smrpg_geno_powerup 1.735-2.00 (start of the release glide)'], ['glide trimmed from 0.55 s', '3/80 ms fades']
add('GENO_BEAM_RELEASE', release, 'charge stored with shield / cancelled')

def beamfire():
    x = trim_lead(seg(loadc('geno_genobeam'), 0.0, 0.445))
    return fade_out(x, 30), ['CLEAN smrpg_geno_genobeam 0.00-0.445 (the fire, before the hum)'], ['lead trimmed', '30 ms fade out']
add('GENO_BEAM_FIRE', beamfire, 'Beam fired with 1-2 stars (and a stored charge)')

def beamfull():
    x = trim_lead(seg(loadc('geno_genobeam'), 0.0, 1.02))
    return fade_out(x, 250), ['CLEAN smrpg_geno_genobeam 0.00-1.02 (fire, then the rise into the 2.7 kHz hum)'], \
        ['lead trimmed', 'hum cut at 1.02 s of 1.55', '250 ms fade out']
add('GENO_BEAM_FULL', beamfull, 'full 3-star Beam (and the auto-fire past the grace)', vol=0xE5, prio=17, aux=0x14)

def whirlthrow():
    x = seg(load('geno_whirl_1'), 0.0, 0.50)
    return fade_out(fade_in(x, 10), 120), ['geno_whirl_1 0.00-0.50 (the swirl)'], ['10/120 ms fades']
add('GENO_WHIRL_THROW', whirlthrow, 'side B: the disc leaves the hand')

def whirlhit():
    x = seg(load('geno_whirl_1'), 0.495, 0.90)
    return fade_out(fade_in(x, 2), 150), ['geno_whirl_1 0.495-0.90 (the bright hit section + tail start)'], ['2/150 ms fades']
add('GENO_WHIRL_HIT', whirlhit, 'Whirl hit (outbound, grind, hover)')

def whirlrecall():
    x = seg(load('geno_whirl_1'), 0.05, 0.50)[::-1]
    return fade_out(fade_in(x, 30), 40), ['geno_whirl_1 0.05-0.50 (the swirl)'], ['reversed, so it rises toward Geno', '30/40 ms fades']
add('GENO_WHIRL_RECALL', whirlrecall, 'Whirl recall (side B during the hover)')

def whirlcrit():
    th = seg(load('projectile_timed_hit_1'), 0.0, 0.54)
    wh = fade_out(seg(load('geno_whirl_1'), 0.495, 0.80), 90)
    x = mix(th, wh, 0.0, -4.0)
    return fade_out(x, 160), ['projectile_timed_hit_1 0.00-0.54 (the SNES timed-hit crack)', 'geno_whirl_1 0.495-0.80 (whirl hit, 90 ms fade), -4 dB'], \
        ['mixed: timed-hit crack over the whirl hit (the SNES 9999 itself is silent)', '160 ms fade out']
add('GENO_WHIRL_CRIT', whirlcrit, 'Whirl crit (the timed hit)', vol=0xE5, prio=17)

def blastmark():
    x = seg(load('geno_blast_skybeam_1'), 0.0, 0.70)
    return fade_out(fade_in(x, 20), 200), ['geno_blast_skybeam_1 0.00-0.70 (grade C: faint music under it)'], \
        ['cut to 0.70 s = 42 frames, so it ends on the strike', '20/200 ms fades']
add('GENO_BLAST_MARK', blastmark, 'down B: the mark appears (frame 10)')

def blastcolumns():
    c = load('geno_blast_columns_1')
    x = xfade(seg(c, 0.0, 0.62), seg(c, 1.78, 2.06), 50)
    return fade_out(fade_in(x, 3), 60), ['geno_blast_columns_1 0.00-0.62 and 1.78-2.06 (grade C)'], \
        ['3 of the zig-zag cycles, then the closing rise, 50 ms crossfade', '3/60 ms fades']
add('GENO_BLAST_COLUMNS', blastcolumns, 'Blast columns strike (mark + 32-42 frames)', aux=0x14)

def flashtransform():
    x = seg(load('geno_flash_transform_1'), 0.0, 0.78)
    return fade_out(fade_in(x, 10), 120), ['geno_flash_transform_1 0.00-0.78'], ['10/120 ms fades']
add('GENO_FLASH_TRANSFORM', flashtransform, 'Flash: the fold into the cannon (third star)')

def flashfire():
    x = trim_lead(seg(loadc('geno_transform'), 0.0, 0.86))
    return fade_out(x, 60), ['CLEAN smrpg_geno_transform 0.00-0.86 (the site calls it "transform"; it is the Flash cannon shot in the SNES video)'], \
        ['lead trimmed', '60 ms fade out']
add('GENO_FLASH_FIRE', flashfire, 'Flash fires (~frame 90)')

def flashexpl():
    x = trim_lead(seg(loadc('geno_genoblast'), 0.0, 1.66))
    return fade_out(x, 450), ['CLEAN smrpg_geno_genoblast 0.00-1.66 (the site calls it "genoblast"; it is the Flash explosion in the SNES video)'], \
        ['lead trimmed', 'shortened from 3.25 s (sun grows ~40 f, lingers ~30 f)', '450 ms fade out']
add('GENO_FLASH_EXPLOSION', flashexpl, 'Flash sun explodes (on spawn)', vol=0xE5, prio=17, aux=0x14)

def srfold():
    x = trim_lead(seg(loadc('geno_transform'), 0.0, 0.36))
    x = pitch(x, 2)
    return fade_out(fade_in(x, 3), 60), ['CLEAN smrpg_geno_transform 0.00-0.36 (the cannon\'s steady armed tone)'], \
        ['+2 semitones (resampled) to set it apart from the Flash', 'lead trimmed', '3/60 ms fades']
add('GENO_STARROAD_FOLD', srfold, 'up B: fold into the cannon (frame 6)')

def srlaunch():
    shot = pitch(seg(loadc('geno_transform'), 0.50, 0.86), 2)
    stars = trim_lead(seg(loadc('geno_stargun'), 0.0, 0.34))
    x = mix(fade_in(shot, 2), stars, 0.03, -6.0)
    return fade_out(x, 120), ['CLEAN smrpg_geno_transform 0.50-0.86 (the pulsed rising shot), +2 semitones',
                              'CLEAN smrpg_geno_stargun 0.00-0.34 (first star tones), -6 dB, +30 ms'], \
        ['mixed: the cannon shot with a star trail', '120 ms fade out']
add('GENO_STARROAD_LAUNCH', srlaunch, 'up B launch (frame ~18, after the 12-frame aim)')

# ------------------------------------------------------------------------------------------------ build
if __name__ == '__main__':
    out = os.path.join(HERE, 'build'); os.makedirs(out, exist_ok=True)
    meta = []
    for k, s in enumerate(S):
        x48, src, edits = s['fn']()
        x48 = hp(x48, 40) if 'high-pass 1.5 kHz' not in ' '.join(edits) else x48
        y = to_bank(x48)
        y -= np.linspace(y[0], y[-1], len(y)) * 0          # (DC is removed by the 40 Hz high-pass)
        n = int(0.002 * SR); y[-n:] *= np.cos(np.linspace(0, np.pi / 2, n)) ** 2; y[-1] = 0.0
        y, pk, lufs, g = level(y)
        q = np.clip(np.round(y * 32767), -32768, 32767).astype(np.int16)
        fn = os.path.join(out, f'{k:02d}_{s["name"]}.wav'); sf.write(fn, q, SR, subtype='PCM_16')
        meta.append(dict(k=k, name=s['name'], file=os.path.basename(fn), samples=len(q), dur=round(len(q) / SR, 3),
                         sources=src, edits=edits + ['40 Hz high-pass' if 'high-pass 1.5 kHz' not in ' '.join(edits) else '',
                                                    'resampled 48 -> 32 kHz, mono', 'peak -3 dBFS' + (f', then {g:+.1f} dB to Mario\'s loudness range' if g else '')],
                         peak_dbfs=pk, max_momentary_lufs=lufs, use=s['use'], vol=s['vol'], prio=s['prio'], aux=s['aux']))
        print(f'{k:2d} {s["name"]:22s} {len(q)/SR:5.3f}s pk {pk:5.1f} dBFS  mom {lufs:6.1f} LUFS  {s["use"]}')
    for m in meta: m['edits'] = [e for e in m['edits'] if e]
    json.dump(meta, open(os.path.join(out, 'sounds.json'), 'w'), indent=1)
    print('total', round(sum(m['dur'] for m in meta), 2), 's')
