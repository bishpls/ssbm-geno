"""Build ~/games/smrpg/sfx/geno/: Geno's sounds, rendered from the ROM's own sound driver, named like the Melee bank.
Dry (echo return muted) at the top level, battle echo in wet/. Everything 32 kHz, 16-bit, stereo, at the game's own level."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from spcharness import *
STATE = open(paths.STATE, 'rb').read()
OUT = os.path.join(paths.SFX, 'geno')
F = FRAME
C6, C4 = 0x08, 0x09      # script channel 6 (voices 6/7) and channel 4 (voices 4/5)
def trim(a):
    # start: first sample above 1 LSB, walked back to the first non-zero sample (at most 1 ms: the wet path has a 1-LSB floor)
    m = np.abs(a.astype(int)).max(axis=1)
    nz2 = np.nonzero(m > 1)[0]
    if len(nz2) == 0: return a[:0]
    i0 = nz2[0]
    k = 0
    while i0 > 0 and m[i0 - 1] > 0 and k < 32: i0 -= 1; k += 1
    return a[i0:min(len(a), nz2[-1] + int(0.01 * SR))]
def seg(a, t0, t1=None, fade_ms=2.0):
    """cut [t0, t1) seconds; short raised-cosine fades only at cut points inside the sound"""
    i0 = int(round(t0 * SR)); i1 = len(a) if t1 is None else int(round(t1 * SR))
    b = a[i0:i1].astype(float)
    n = int(fade_ms * SR / 1000)
    if i0 > 0 and n: b[:n] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n)))[:, None]
    if t1 is not None and i1 < len(a) and n: b[-n:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, n)))[:, None]
    return np.round(b).astype(np.int16)
# name -> (events, cut, rom ids, how)
S = {}
def add(name, events, cut=None, how=''):
    S[name] = dict(events=events, cut=cut, how=how)
one = lambda i, ch=C6: [(0, i, ch)]
add('GENO_PULSE', one(52), (0.068, 0.137), 'ROM 052 Finger Shot bullets, pulse 2 of 6 (0.068-0.137 s)')
add('GENO_HANDGUN', [(0, 148, C6), (36 * F, 0, C6)], None, 'ROM 148, cut by ROM 000 (silence) 36 frames later, exactly as the Hand Gun script does')
add('GENO_HANDCANNON', [(0, 109, C6), (6 * F, 109, C6), (12 * F, 109, C6)], None, 'ROM 109 triggered 3x, 6 frames apart (the Hand Cannon script); the last one rings out')
add('GENO_DOUBLEPUNCH', one(12), None, 'ROM 012 (Lazy Shell: "bomb explosion"): the Double Punch / unarmed hit sound from the weapon-sound table')
add('GENO_STARGUN', one(17), None, 'ROM 017 Star Gun shoot')
add('GENO_STARGUN_HIT', one(197), None, 'ROM 197 Geno Star Gun hit (weapon-sound table)')
add('GENO_NAIR_SWIRL', one(63), None, "ROM 063 (\"Geno Blast ignition\"): Geno's swirl, played by both Whirl (the disc) and Blast (the sky beam)")
add('GENO_CAPE', one(51), None, 'ROM 051 ("fire throw big"): the rocket-fist launch swoosh of Geno\'s unarmed attack and Double Punch; a real SNES Geno swish')
add('GENO_PROJ_HIT', one(113), None, 'ROM 113 Geno Finger Shot hit (weapon-sound table for Finger Shot, Hand Gun, Hand Cannon)')
add('GENO_FINGERSHOT', one(52), None, 'ROM 052 Finger Shot bullets (all 6 pulses; the first 4 end at 0.277 s)')
add('GENO_BEAM_CHARGE', one(69), (0.0, 1.63), 'ROM 069 Geno power up, charge part (0-1.63 s, up to the pitch peak)')
add('GENO_BEAM_STAR1', one(13), (0.091, None), 'no SNES star chime exists; ROM 013 coin, second ding (bank transposes 0 st)')
add('GENO_BEAM_STAR2', one(13), (0.091, None), 'no SNES star chime exists; ROM 013 coin, second ding (bank transposes +4 st)')
add('GENO_BEAM_STAR3', one(13), None, 'no SNES star chime exists; ROM 013 coin, both dings (bank transposes +7 st)')
add('GENO_BEAM_RELEASE', one(69), (1.63, None), 'ROM 069 Geno power up, release glide (from 1.63 s)')
add('GENO_BEAM_FIRE', one(70), (0.0, 0.37), 'ROM 070 Geno Beam, fire part (0-0.37 s; the hum starts at the retrigger at 0.37 s)')
add('GENO_BEAM_FULL', one(70), None, 'ROM 070 Geno Beam (fire + hum)')
add('GENO_WHIRL_THROW', one(63), None, 'ROM 063: the Whirl plays it with the flying disc (in game it is cut by ROM 000 when the disc hits)')
add('GENO_WHIRL_HIT', one(42, C4), None, 'ROM 042 ("blade"), channel 4: the Whirl\'s hit object (explosion sprite on the target)')
add('GENO_WHIRL_RECALL', one(63), None, 'ROM 063 again (the bank reverses it for the recall)')
add('GENO_WHIRL_CRIT', one(78, C4), None, 'ROM 078 ("timed stat boost"), channel 4: the Whirl\'s timed-press sound with the blue flash (the 9999 crit)')
add('GENO_BLAST_MARK', one(63), None, 'ROM 063 ("Geno Blast ignition"): the sky beam')
add('GENO_BLAST_COLUMNS', [(k * 6 * F, 118, C6) for k in range(18)], None, 'ROM 118 ("Geno Blast end") retriggered every 6 frames x18, as the Blast script loops it while the columns fall; the last one rings out')
add('GENO_FLASH_TRANSFORM', one(196), None, 'ROM 196 Geno Flash transformation')
add('GENO_FLASH_FIRE', one(185), None, 'ROM 185 Geno Flash shoot')
add('GENO_FLASH_EXPLOSION', one(186), None, 'ROM 186 Geno Flash explosion')
add('GENO_STARROAD_FOLD', one(196), None, 'no SNES Star Road move; ROM 196 (Geno morphing into a cannon)')
add('GENO_STARROAD_LAUNCH', one(185), None, 'no SNES Star Road move; ROM 185 (Geno cannon shot)')
EXTRA = {}
def xadd(name, events, cut=None, how=''): EXTRA[name] = dict(events=events, cut=cut, how=how)
xadd('SPECIAL_START', one(35), None, 'ROM 035 spell power up: every special starts with it (generic, not Geno-only)')
xadd('WEAPON_TIMING', one(172, C4), None, 'ROM 172 weapon timing, channel 4: plays on every timed weapon hit (generic)')
xadd('DOUBLEPUNCH_LAUNCH', one(51), None, 'ROM 051: fist launch (unarmed 1x, Double Punch 2x on the same frame)')
xadd('HANDCANNON_SINGLE', one(109), None, 'ROM 109 once')
xadd('HANDGUN_UNCUT', one(148), None, 'ROM 148 ("Smithy bullet fingers") uncut; the game cuts it at 36 frames')
xadd('BLAST_COLUMNS_SINGLE', one(118), None, 'ROM 118 once')
xadd('BLAST_GAME', [(0, 63, C6)] + [(100 * F + k * 6 * F, 118, C6) for k in range(18)], None, 'Blast as in battle: 063, then 118 x18 from 100 frames')
xadd('WHIRL_GAME_TIMED', [(0, 63, C6), (0.50, 78, C4), (0.52, 0, C6)], None, 'Whirl as in the SNES video (timed): 063, then 078 on ch4 with the blue flash and 000 cutting 063')
xadd('WHIRL_GAME_UNTIMED', [(0, 63, C6), (0.52, 0, C6), (0.52 + 2 * F, 42, C4)], None, 'Whirl without the timed press: 063 cut by 000, then 042')
xadd('BEAM_GAME', [(0, 69, C6), (2.52, 70, C6)], None, 'Beam as in the SNES video: 069, then 070 2.52 s later')
xadd('BOOST_SPARKLE', one(77), None, 'ROM 077 stat boost (multi): Geno Boost sparkles')
xadd('BOOST_TIMED', one(78, C4), None, 'ROM 078 timed stat boost (Boost timed press, same ID as the Whirl crit)')
xadd('BOOST_STATUP', one(6), None, 'ROM 006 bonus flower status up: rising sweep + 3.6 kHz chime (ATTACK UP / DEFENSE UP)')
xadd('COIN', one(13), None, 'ROM 013 coin')
xadd('ENEMY_DEFEAT', one(89), None, 'ROM 089 common monster explosion')
xadd('MENU_SELECT', one(1), None, 'ROM 001 menu select')
def build(table, outdir, nosat=False):
    man = {}
    for name, d in table.items():
        modes = (('dry', outdir), ('wet', outdir + '/wet')) + ((('nosat', outdir + '/nosat'),) if nosat else ())
        for mode, od in modes:
            a = render_sequence(STATE, d['events'], dry=(mode != 'wet'), nosat=(mode == 'nosat'))
            a = trim(a)
            if d['cut']: a = seg(a, d['cut'][0], d['cut'][1])
            write_wav('%s/%s.wav' % (od, name), a)
            if mode == 'nosat':
                man[name]['nosat_peak_dbfs'] = round(float(20 * np.log10(max(np.abs(a.astype(int)).max(), 1) / 32768)), 1)
                man[name]['clipped_samples_in_game_render'] = int(clipn)
            if mode == 'dry':
                pk = np.abs(a.astype(int)).max(); clipn = int((np.abs(a.astype(int)) >= 16383).sum())
                man[name] = dict(how=d['how'], rom_ids=sorted(set(e[1] for e in d['events'] if e[1])), events=[[round(t, 4), i, 'ch6' if c == C6 else 'ch4'] for t, i, c in d['events']],
                                 cut=d['cut'], dur_s=round(len(a) / SR, 3), peak_dbfs=round(float(20 * np.log10(max(pk, 1) / 32768)), 1))
        print(name, man[name]['dur_s'], man[name]['peak_dbfs'], flush=True)
    return man
if __name__ == '__main__':
    for d in (OUT, OUT + '/wet', OUT + '/nosat', OUT + '/extra', OUT + '/extra/wet'): os.makedirs(d, exist_ok=True)
    m = build(S, OUT, nosat=True)
    x = build(EXTRA, OUT + '/extra')
    json.dump(dict(bank=m, extra=x), open(OUT + '/manifest.json', 'w'), indent=1)
