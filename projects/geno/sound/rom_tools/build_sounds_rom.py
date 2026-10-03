"""Round 3: Geno's 28 bank sounds from the clean ROM captures (~/games/smrpg/sfx/geno/nosat/, 32 kHz, rendered from the
cartridge's own sound driver; see ~/games/smrpg/sfx/NOTES.md). Same sound IDs and the same Melee timing edits as the
earlier rounds; the game's own sequencing where the capture notes give it.
Output: build/NN_NAME.wav (32 kHz mono int16) + build/sounds.json, consumed by tools/build_bank.py."""
import os, sys, json, subprocess, tempfile
import numpy as np, soundfile as sf, librosa
sys.path.insert(0, os.path.dirname(__file__))
from build_sounds import fade_in as _fi, fade_out as _fo, hp as _hp, momentary_max, level, PY, SFX

HERE = os.path.expanduser(os.environ.get('SFXBANK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'sfxbank')))   # the bank's work folder (game audio: outside the repo)
ROM = os.path.join(os.path.expanduser(os.environ.get('SMRPG_SFX', '~/games/smrpg/sfx')), 'geno')   # capture/
SR = 32000
T6 = 6 / 60.0988                     # 6 NTSC frames (the driver's frame), the Hand Cannon / Blast retrigger period

def load(name, sub='nosat'):
    x, sr = sf.read(os.path.join(ROM, sub, name + '.wav') if sub else os.path.join(ROM, name + '.wav'))
    assert sr == SR
    return x.mean(1) if x.ndim > 1 else x          # the renders are dual-mono (L == R)

def extra(name):
    x, sr = sf.read(os.path.join(ROM, 'extra', name + '.wav')); assert sr == SR
    return x.mean(1) if x.ndim > 1 else x

def seg(x, a, b=None): return x[int(round(a * SR)): (None if b is None else int(round(b * SR)))].copy()
def fi(x, ms): return _fi(x, ms, SR)
def fo(x, ms): return _fo(x, ms, SR)
def xfade(a, b, ms):
    n = int(ms * SR / 1000); t = np.sin(np.linspace(0, np.pi / 2, n)) ** 2
    return np.concatenate([a[:-n], a[-n:] * (1 - t) + b[:n] * t, b[n:]])
def mix(a, b, at, gain_db=0.0):
    o = int(at * SR); n = max(len(a), o + len(b)); y = np.zeros(n); y[:len(a)] += a; y[o:o + len(b)] += b * 10 ** (gain_db / 20); return y
def pitch(x, st):
    return x if st == 0 else librosa.resample(x, orig_sr=SR * 2 ** (st / 12), target_sr=SR, res_type='soxr_vhq')
def trim_lead(x, rel_db=-40):
    i = int(np.argmax(np.abs(x) > np.abs(x).max() * 10 ** (rel_db / 20))); return x[max(0, i - int(0.001 * SR)):]

def grain_charge(x, target_s):
    with tempfile.TemporaryDirectory() as d:
        i, o = os.path.join(d, 'in.wav'), os.path.join(d, 'out.wav')
        sf.write(i, x, SR, subtype='PCM_16')
        r = subprocess.run([PY, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grain_retime.py'), i, o, str(target_s)],
                           capture_output=True, text=True, check=True)
        y, _ = sf.read(o)
    return (y.mean(1) if y.ndim > 1 else y), r.stdout.strip()

def retrigger_points(seq, single, n, period):
    """exact key-on sample of each retrigger in the captured sequence: cross-correlate the single's first 12 ms near k*period"""
    w = single[:int(0.012 * SR)]; pts = [0]
    for k in range(1, n):
        c = int(round(k * period * SR)); r = int(0.012 * SR)
        best, bi = -2, c
        for i in range(c - r, c + r):
            s = seq[i:i + len(w)]
            v = np.dot(s, w) / (np.linalg.norm(s) * np.linalg.norm(w) + 1e-12)
            if v > best: best, bi = v, i
        pts.append(bi)
    return pts

S = []
def add(name, fn, use, vol=0xCC, prio=15, aux=1):
    S.append(dict(name=name, fn=fn, use=use, vol=vol, prio=prio, aux=aux))

R = lambda rom, extra_='': f'ROM {rom} (nosat capture{extra_})'

add('GENO_PULSE', lambda: (fo(fi(load('GENO_PULSE'), 0.5), 10), [R('052', ': pulse 2 of 6, 0.068-0.137 s')], ['0.5/10 ms fades']),
    'jab 1/2 and each rapid-jab hit; down tilt; pummel')
add('GENO_HANDGUN', lambda: (fo(load('GENO_HANDGUN'), 8), [R('148', ', cut by 000 at 36 frames as the Hand Gun script does')],
    ['the game\'s own 0.6 s cut', '8 ms fade out']), 'forward tilt, forward air')
add('GENO_HANDCANNON', lambda: (fo(load('GENO_HANDCANNON'), 40), [R('109', ': triggered 3x, 6 frames apart, as the Hand Cannon script does')],
    ['the game\'s triple trigger baked into one sample (the last rings out)', '40 ms fade out']), 'down smash (both sides), back air, down air')
add('GENO_DOUBLEPUNCH', lambda: (fo(seg(load('GENO_DOUBLEPUNCH'), 0.0, 0.62), 220), [R('012', ': the unarmed/Double Punch hit from the weapon-sound table, 0-0.62 of 1.46 s')],
    ['ring shortened for Melee pacing (as before)', '220 ms fade out']), 'forward smash (on the hit frame)')
add('GENO_STARGUN', lambda: (fo(seg(load('GENO_STARGUN'), 0.0, 0.80), 140), [R('017', ': the star cascade, 0-0.80 of 1.10 s')],
    ['tail repeats dropped (as before)', '140 ms fade out']), 'up smash, up air')
add('GENO_STARGUN_HIT', lambda: (fo(seg(load('GENO_STARGUN_HIT'), 0.0, 0.50), 150), [R('197', ': Star Gun hit, 0-0.50 of 0.59 s')],
    ['150 ms fade out']), 'up smash / up air on hit')
add('GENO_NAIR_SWIRL', lambda: (fo(fi(pitch(seg(load('GENO_NAIR_SWIRL'), 0.04, 0.44), 3), 15), 80), [R('063', ': Geno\'s swirl, 0.04-0.44 s')],
    ['+3 semitones (resampled) to set it apart from the Whirl (as before)', '15/80 ms fades']), 'neutral air')
add('GENO_CAPE', lambda: (fo(load('GENO_CAPE'), 40), [R('051', ': the rocket-fist launch swoosh (a real SNES Geno swish; the SNES has no cape sound)')],
    ['40 ms fade out']), 'up tilt (cape swish)')
add('GENO_PROJ_HIT', lambda: (fo(load('GENO_PROJ_HIT'), 100), [R('113', ': the weapon-table hit for Finger Shot / Hand Gun / Hand Cannon')],
    ['100 ms fade out']), 'Finger Shot / Beam / Star Road hits (projectile hit)')
add('GENO_FINGERSHOT', lambda: (fo(fi(seg(load('GENO_FINGERSHOT'), 0.0, 0.277), 0.5), 8), [R('052', ': the first 4 of the 6 pulses (0-0.277 s)')],
    ['four bullets, as before', '0.5/8 ms fades']), 'neutral B tap: Finger Shot')

def charge():
    c = load('GENO_BEAM_CHARGE')                           # 069, 0-1.63 s (to the pitch peak)
    climb, log = grain_charge(c, 0.75)
    x = xfade(climb, seg(c, 1.30, 1.63), 6)
    return fo(fi(x, 3), 40), [R('069', ': the charge, 0-1.63 s'), R('069', ': top grains 1.30-1.63 s')], \
        [f'grain drop to 0.75 s so the climb peaks at frame 45 (the catalogue method; {log})', 'then the top grains for the 20-frame grace', '6 ms crossfade', '3/40 ms fades']
add('GENO_BEAM_CHARGE', charge, 'neutral B hold: charge, frames 0-65 (45 to the third star + 20 grace)', vol=0xB2)

def star(n):
    def f():
        st = [0, 4, 7][n - 1]
        if n < 3: x = seg(load('GENO_BEAM_STAR1'), 0.0, 0.37); src = R('013', ': coin, second ding (2.7 kHz), 0-0.37 s')
        else: x = seg(load('GENO_BEAM_STAR3'), 0.0, 0.50); src = R('013', ': coin, both dings, 0-0.50 s')
        return fo(fi(pitch(x, st), 1), 110), [src], [f'+{st} semitones (resampled): a rising triad over the stars (as before)', '1/110 ms fades']
    return f
for n in (1, 2, 3):
    add(f'GENO_BEAM_STAR{n}', star(n), f'Beam star {n} (frame {15 * n}); also the Blast/Flash hold stars', vol=0xB2)

add('GENO_BEAM_RELEASE', lambda: (fo(fi(seg(load('GENO_BEAM_RELEASE'), 0.0, 0.265), 3), 80), [R('069', ': release glide, first 0.265 s')],
    ['glide trimmed from 0.62 s (as before)', '3/80 ms fades']), 'charge stored with shield / cancelled')
add('GENO_BEAM_FIRE', lambda: (fo(load('GENO_BEAM_FIRE'), 20), [R('070', ': the fire, 0-0.37 s (the hum starts at its retrigger at 0.37 s)')],
    ['20 ms fade out']), 'Beam fired with 1-2 stars (and a stored charge)')
add('GENO_BEAM_FULL', lambda: (fo(seg(load('GENO_BEAM_FULL'), 0.0, 1.00), 250), [R('070', ': fire + hum, 0-1.00 of 1.42 s')],
    ['hum cut at 1.0 s (as before)', '250 ms fade out']), 'full 3-star Beam (and the auto-fire past the grace)', vol=0xE5, prio=17, aux=0x14)
add('GENO_WHIRL_THROW', lambda: (fo(fi(seg(load('GENO_WHIRL_THROW'), 0.0, 0.50), 10), 120), [R('063', ': the swirl the Whirl plays with the flying disc, 0-0.50 s')],
    ['10/120 ms fades (in game it is cut when the disc hits)']), 'side B: the disc leaves the hand')
add('GENO_WHIRL_HIT', lambda: (fo(load('GENO_WHIRL_HIT'), 60), [R('042', ': the Whirl\'s untimed hit (channel 4)')], ['60 ms fade out']),
    'Whirl hit (outbound, grind, hover)')
add('GENO_WHIRL_RECALL', lambda: (fo(fi(seg(load('GENO_WHIRL_RECALL'), 0.05, 0.50)[::-1], 30), 40), [R('063', ': the swirl, 0.05-0.50 s')],
    ['reversed, so it rises toward Geno (as before)', '30/40 ms fades']), 'Whirl recall (side B during the hover)')
add('GENO_WHIRL_CRIT', lambda: (fo(seg(load('GENO_WHIRL_CRIT'), 0.0, 0.80), 250), [R('078', ': the Whirl\'s timed press, the 9999 moment (channel 4), 0-0.80 of 0.90 s')],
    ['250 ms fade out']), 'Whirl crit (the timed hit)', vol=0xE5, prio=17)
add('GENO_BLAST_MARK', lambda: (fo(fi(seg(load('GENO_BLAST_MARK'), 0.0, 0.70), 20), 200), [R('063', ': the sky beam, 0-0.70 s')],
    ['cut to 0.70 s = 42 frames (as before)', '20/200 ms fades']), 'down B: the mark appears (frame 10)')

N_COLUMNS = 6
def columns():
    seq = load('GENO_BLAST_COLUMNS'); single = extra('BLAST_COLUMNS_SINGLE')
    pts = retrigger_points(seq, single, 18, T6)
    x = np.concatenate([seq[:pts[N_COLUMNS - 1]], seq[pts[17]:]])   # N retriggers; the last one rings out, as in game
    return fo(fi(x, 2), 40), [R('118', ': retriggered every 6 frames (x18 in the capture), the Blast script\'s own loop')], \
        [f'kept the game\'s 6-frame retriggers, {N_COLUMNS} of them (first {N_COLUMNS - 1} periods, then the final trigger\'s ring-out), '
         f'cut at the retrigger key-ons found by correlation (periods {np.round(np.diff(pts[:N_COLUMNS]) / SR * 1000, 1).tolist()} ms)', '2/40 ms fades']
add('GENO_BLAST_COLUMNS', columns, 'Blast columns strike (mark + 32-42 frames)', aux=0x14)
add('GENO_FLASH_TRANSFORM', lambda: (fo(load('GENO_FLASH_TRANSFORM'), 60), [R('196', ': Geno Flash transformation')], ['60 ms fade out']),
    'Flash: the fold into the cannon (third star)')
add('GENO_FLASH_FIRE', lambda: (fo(load('GENO_FLASH_FIRE'), 40), [R('185', ': Geno Flash shoot')], ['40 ms fade out']), 'Flash fires (~frame 90)')
add('GENO_FLASH_EXPLOSION', lambda: (fo(seg(load('GENO_FLASH_EXPLOSION'), 0.0, 1.66), 450), [R('186', ': Geno Flash explosion, 0-1.66 of 3.44 s')],
    ['shortened (sun grows ~40 f, lingers ~30 f), as before', '450 ms fade out']), 'Flash sun explodes (on spawn)', vol=0xE5, prio=17, aux=0x14)
add('GENO_STARROAD_FOLD', lambda: (fo(fi(pitch(seg(load('GENO_STARROAD_FOLD'), 0.0, 0.30), 2), 3), 60), [R('196', ': the morph into the cannon (its rising steps), 0-0.30 s')],
    ['+2 semitones (resampled): a quicker fold than the Flash', '3/60 ms fades']), 'up B: fold into the cannon (frame 6)')
def srlaunch():
    shot = pitch(seg(load('GENO_STARROAD_LAUNCH'), 0.45, 0.75), 2)
    stars = trim_lead(seg(load('GENO_STARGUN'), 0.0, 0.34))
    return fo(mix(fi(shot, 2), stars, 0.03, -6.0), 120), [R('185', ': the pulsed shot, 0.45-0.75 s, +2 st'), R('017', ': first star tones 0-0.34 s, -6 dB, +30 ms')], \
        ['mixed: the cannon shot with a star trail (as before; no SNES Star Road move exists)', '120 ms fade out']
add('GENO_STARROAD_LAUNCH', srlaunch, 'up B launch (frame ~18, after the 12-frame aim)')

if __name__ == '__main__':
    out = os.path.join(HERE, 'build'); os.makedirs(out, exist_ok=True)
    meta = []
    for k, s in enumerate(S):
        x, src, edits = s['fn']()
        y = _hp(x, 40, SR)                                  # DC / sub-bass clean-up only; already 32 kHz, no resampling
        n = int(0.002 * SR); y[-n:] *= np.cos(np.linspace(0, np.pi / 2, n)) ** 2; y[-1] = 0.0
        y, pk, lufs, g = level(y)
        q = np.clip(np.round(y * 32767), -32768, 32767).astype(np.int16)
        fn = os.path.join(out, f'{k:02d}_{s["name"]}.wav'); sf.write(fn, q, SR, subtype='PCM_16')
        meta.append(dict(k=k, name=s['name'], file=os.path.basename(fn), samples=len(q), dur=round(len(q) / SR, 3), sources=src,
                         edits=edits + ['40 Hz high-pass', 'mono (the renders are dual-mono)', 'peak -3 dBFS' + (f', then {g:+.1f} dB to Mario\'s loudness range' if g else '')],
                         peak_dbfs=pk, max_momentary_lufs=lufs, use=s['use'], vol=s['vol'], prio=s['prio'], aux=s['aux']))
        print(f'{k:2d} {s["name"]:22s} {len(q)/SR:5.3f}s pk {pk:5.1f} dBFS  mom {lufs:6.1f} LUFS  {src[0]}')
    json.dump(meta, open(os.path.join(out, 'sounds.json'), 'w'), indent=1)
    print('total', round(sum(m['dur'] for m in meta), 2), 's')
