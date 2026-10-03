"""Draft 2 renderer: band (Emilyguitar/Growlybass DI -> NAM amps, Aasimonster kit) + orchestra (VSCO 2 CE via sfizz) +
synths (Surge XT via pedalboard) + choir (GeneralUser GS via FluidSynth). Writes the mastered mix and stems at mix level
(each bus times the master gain, pre-limiter, 32-bit float) so the stems sum to the mix for the trailer mixer.
    python render2.py OUTDIR"""
import sys, os, json, time, numpy as np, soundfile as sf
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
import arrange as A, mix as M, drumpat as D, orch as O, sfz, guitars2 as G2, surgepatch as SP
import pretty_midi as pm

SR = 48000
PATCH = os.path.join(MUSIC, 'libs/surge_data/patches_factory/')
SURGE = {'arp': 'Plucks/Saw Pluck', 'pad': 'Polysynths/Tarnce', 'slead': 'Leads/Saw Octaves', 'sbass': 'Leads/Tight Bassline',
         'bell': 'Plucks/Magic Music Box'}
VSCO = {'vln_mel_s': 'ViolinEnsSpic', 'vln_mel': 'ViolinEnsSusVib_mel', 'fl_mel': 'FluteSusVib_mel', 'hn_mel': 'FHornSus_mel', 'vln': 'ViolinEnsSusVib', 'vla': 'ViolaEnsSusVib', 'vc': 'CelloEnsSusVib', 'cb': 'ContrabassSusVB',
        'vln_spic': 'ViolinEnsSpic', 'vla_spic': 'ViolaEnsSpic', 'vln_trem': 'ViolinEnsTrem', 'hn': 'FHornSus',
        'hn_stac': 'FHornStac', 'tbn': 'TromboneSus', 'tpt': 'TrumpetStac', 'glock': 'Glockenspiel', 'timp': 'Timpani',
        'timp_roll': 'TimpaniRolls'}
# (bus, level dB for the instrument's active RMS, pan)
LEVEL = {'vln_mel_s': ('orch', -6, -0.2), 'vln_mel': ('orch', -5, -0.2), 'fl_mel': ('orch', -8, 0.25), 'hn_mel': ('orch', -8, 0.3), 'vln': ('orch', -16, -0.35), 'vla': ('orch', -17, 0.3), 'vc': ('orch', -19, 0.45), 'cb': ('orch', -16, 0.2),
         'vln_spic': ('orch', -14, -0.45), 'vla_spic': ('orch', -17, 0.4), 'vln_trem': ('orch', -15, -0.3),
         'hn': ('orch', -8, 0.25), 'hn_stac': ('orch', -9, 0.2), 'tbn': ('orch', -13, 0.35), 'tpt': ('orch', -11, -0.15),
         'glock': ('orch', -10, 0.15), 'timp': ('orch', -7, 0.0), 'timp_roll': ('orch', -10, 0.0),
         'arp': ('synth', -12, 0.0), 'pad': ('synth', -15, 0.0), 'slead': ('synth', -8, 0.0), 'sbass': ('synth', -10, 0.0),
         'bell': ('synth', 1, 0.0), 'choir': ('choir', -18, 0.0)}


def act_rms(x, floor_db=-45):
    m = x if x.ndim == 1 else x.mean(0)
    fr = 4800
    k = len(m) // fr
    if k == 0: return 1e-9
    r = np.sqrt((m[:k * fr].reshape(k, fr) ** 2).mean(1))
    thr = r.max() * 10 ** (floor_db / 20)
    a = r[r > thr]
    return float(np.sqrt((a ** 2).mean())) if len(a) else 1e-9


def level(x, db):
    return x * (10 ** (db / 20) * 0.1 / act_rms(x))


def to_st(x, p=0.0):
    return M.pan(x, p) if x.ndim == 1 else x


def envelope(n, segs, ramp=0.05):
    """gain envelope from [(t0, t1, dB)] segments (1.0 elsewhere), with linear ramps"""
    g = np.zeros(n)
    for (a, b, dbv) in segs:
        i, j = int(a * SR), min(n, int(b * SR))
        g[i:j] += dbv
    from scipy.ndimage import uniform_filter1d
    g = uniform_filter1d(g, max(1, int(ramp * SR)))
    return 10 ** (g / 20)


def pump(n, beats, depth_db=-9.0, rel=0.16):
    """sidechain-style ducking on the given beat times"""
    g = np.zeros(n)
    L = int(0.3 * SR); tt = np.arange(L) / SR
    shape = depth_db * np.exp(-tt / (rel / 3)) * (tt < 0.3)
    for b in beats:
        i = int(b * SR)
        if i >= n: continue
        e = min(n, i + L)
        g[i:e] = np.minimum(g[i:e], shape[:e - i])
    return 10 ** (g / 20)


def clap_sample(seed=0):
    rng = np.random.default_rng(seed)
    L = int(0.35 * SR); y = np.zeros(L)
    for k, dt in enumerate([0.0, 0.009, 0.019, 0.03]):
        i = int(dt * SR); m = int(0.012 * SR) if k < 3 else L - i
        seg = rng.normal(0, 1, m) * np.exp(-np.arange(m) / (0.004 * SR if k < 3 else 0.07 * SR))
        y[i:i + m] += seg
    from scipy.signal import butter, sosfilt
    y = sosfilt(butter(2, [900, 3500], 'band', fs=SR, output='sos'), y)
    return (y / np.abs(y).max()).astype(np.float32)


def render_choir(notes, total):
    import subprocess, tempfile
    import sfguitar
    m = pm.PrettyMIDI(initial_tempo=200)
    for prog, vel in ((52, 1.0), (53, 0.75)):
        inst = pm.Instrument(prog)
        for (t, d, p, v) in notes: inst.notes.append(pm.Note(int(np.clip(v * vel * 110, 1, 127)), p, t, t + d))
        m.instruments.append(inst)
    with tempfile.TemporaryDirectory() as tdir:
        m.write(tdir + '/c.mid')
        subprocess.run(['fluidsynth', '-ni', '-g', '0.8', '-r', str(SR), '-o', 'synth.reverb.active=0', '-o', 'synth.chorus.active=0',
                        '-F', tdir + '/c.wav', sfguitar.SF2, tdir + '/c.mid'], check=True, capture_output=True)
        y, _ = sf.read(tdir + '/c.wav', dtype='float32')
    y = y.T; n = int(total * SR)
    return np.pad(y, ((0, 0), (0, max(0, n - y.shape[1]))))[:, :n]


def build(secs, final_hit):
    import render as R
    E = R.build_events(secs, tail=6.0)
    total = E['total']; end = E['end']
    layers = {}
    t0 = 0.0; pumps = []; bus_segs = []
    for sec in secs:
        L = R.sec_len(sec)
        for inst, ns in O.section_layers(sec, t0).items():
            layers.setdefault(inst, []).extend(ns)
        if sec.get('pump'):
            pumps += [t0 + k * 0.3 for k in range(int(round(L / 0.3)))]
        for bus, dbv in sec.get('bus_gain', {}).items():
            bus_segs.append((bus, t0, t0 + L, dbv))
        t0 += L
    # ---- final hit: band + orchestra on the new tonic (major: a bright Picardy ending)
    notes, bm, lm = final_hit
    end = round(end, 6); E['end'] = end
    t = end
    ring = 4.2
    E['rL'].append(dict(t=t, dur=ring, notes=notes, vel=1.0, mute=0.0)); E['rR'].append(dict(t=t, dur=ring, notes=notes, vel=1.0, mute=0.0))
    E['bass'].append((t, ring, bm, 1.0, 0.0))
    E['lead1'].append((t, 3.2, lm, 1.0, {'vib': 0.6}))
    E['drums'] += D.hits([0.0], t, china=True)
    E['booms'].append(t)
    tonic = bm % 12; maj = [tonic, (tonic + 4) % 12, (tonic + 7) % 12]
    for inst, lo, hi, n in (('vln', 67, 84, 3), ('vla', 55, 69, 2), ('vc', 43, 55, 2), ('cb', 27, 39, 1), ('hn', 55, 70, 3),
                            ('tbn', 43, 55, 2), ('choir', 57, 76, 4)):
        for p in O.voice(maj, lo, hi, None, n): layers.setdefault(inst, []).append((t, ring, p, 0.95))
    layers.setdefault('timp', []).append((t, ring, 39 if tonic == 3 else 37 + ((tonic - 37) % 12), 1.0))
    layers.setdefault('glock', []).append((t, 1.0, 75 + 12, 0.9))
    stop0 = t - 0.135
    E['drums'] = [e for e in E['drums'] if not (stop0 - 0.01 <= e[0] < t - 0.005)]
    E['stop'] = (stop0, t)
    return E, layers, pumps, bus_segs, total


def render(secs, outdir, final_hit, kit):
    os.makedirs(outdir, exist_ok=True)
    E, layers, pumps, bus_segs, total = build(secs, final_hit)
    n = int(total * SR)
    tm = time.time()
    fit = lambda x: (x[..., :n] if x.shape[-1] >= n else np.pad(x, [(0, 0)] * (x.ndim - 1) + [(0, n - x.shape[-1])]))
    # ---- band
    st = {}
    st['rL'] = fit(M.rhythm_chain(G2.rhythm_di(E['rL'], total, seed=11)))
    st['rR'] = fit(M.rhythm_chain(G2.rhythm_di(E['rR'], total, seed=23, detune_cents=6), amp_name=M.RHYTHM_AMP_R))
    st['bass'] = fit(M.bass_chain(G2.bass_di(E['bass'], total, seed=5)))
    st['lead1'] = fit(M.lead_chain(G2.lead_di(E['lead1'], total, seed=3)))
    st['lead1b'] = fit(M.lead_chain(G2.lead_di(E['lead1'], total, seed=7, vib_rate=5.9)))
    st['lead2'] = fit(M.lead_chain(G2.lead_di(E['lead2'], total, seed=4, vib_rate=5.2))) if E['lead2'] else np.zeros(n, np.float32)
    print('band', round(time.time() - tm, 1), 's', flush=True)
    if E.get('stop'):
        a, b = int(E['stop'][0] * SR), int(E['stop'][1] * SR) - 48
        gate = np.ones(n, np.float32); r_ = 240; gate[a:b] = 0; gate[a - r_:a] = np.linspace(1, 0, r_)
        for k in st: st[k] = st[k] * gate
    # ---- orchestra, synths, choir
    inst_audio = {}
    for inst, ns in layers.items():
        if inst in VSCO:
            y = sfz.render(sfz.vsco(VSCO[inst]), sfz.notes_inst(ns), total)
        elif inst in SURGE:
            y = SP.render(PATCH + SURGE[inst] + '.fxp', ns, total)
        elif inst == 'choir':
            y = render_choir(ns, total)
        else:
            continue
        inst_audio[inst] = fit(y.astype(np.float32))
    print('orch/synth/choir', round(time.time() - tm, 1), 's', sorted(inst_audio), flush=True)
    # ---- drums (claps synthesized), fx
    claps = [e for e in E['drums'] if e[1] == 'clap']
    k808 = [e for e in E['drums'] if e[1] == 'kick808']
    dr = kit.render([e for e in E['drums'] if e[1] not in ('clap', 'kick808')], total)[:, :n]
    sub = np.zeros(n, np.float32)
    L8 = int(0.28 * SR); t8 = np.arange(L8) / SR
    f8 = 46 + 70 * np.exp(-t8 / 0.018); s8 = np.sin(2 * np.pi * np.cumsum(f8) / SR) * np.exp(-t8 / 0.11) * np.minimum(1, t8 / 0.002)
    for (t, p, v) in k808:
        i = int(t * SR); e = min(n, i + L8); sub[i:e] += v * s8[:e - i]
    cs = clap_sample()
    cl = np.zeros(n, np.float32)
    for (t, p, v) in claps:
        i = int(t * SR); e = min(n, i + len(cs)); cl[i:e] += v * cs[:e - i]
    cr = kit.render([(0.0, 'crash1', 1.0)], 2.2)[:, ::-1]
    fx = np.zeros((2, n), np.float32)
    for t in E['risers']:
        i1 = int(t * SR); i0 = max(0, i1 - cr.shape[1]); fx[:, i0:i1] += 0.8 * cr[:, cr.shape[1] - (i1 - i0):]
    for t in E['booms']:
        L = int(1.6 * SR); tt = np.arange(L) / SR
        f = 30 + 28 * np.exp(-tt / 0.25); ph = 2 * np.pi * np.cumsum(f) / SR
        b = np.sin(ph) * np.exp(-tt / 0.45) * np.minimum(1, tt / 0.004)
        i0 = int(t * SR); e = min(n, i0 + L); fx[:, i0:e] += 0.5 * b[None, :e - i0]
    # ---- buses
    g = lambda x, dbv: x * (10 ** (dbv / 20)) / (np.sqrt(np.mean(x ** 2)) + 1e-9) * 0.1
    bus = {k: np.zeros((2, n), np.float32) for k in ('guitars', 'bass', 'leads', 'drums', 'orch', 'synth', 'choir', 'fx')}
    bus['guitars'] += M.pan(g(st['rL'], -2.0), -0.95) + M.pan(g(st['rR'], -2.0), 0.95)
    bus['bass'] += M.pan(g(st['bass'], 0.0), 0.0)
    l1 = M.space(g(st['lead1'], -2.0)); l1b = M.space(g(st['lead1b'], -2.0))
    bus['leads'] += np.vstack([l1[0], l1[1] * 0.75]) + np.vstack([l1b[0] * 0.75, l1b[1]])
    if E['lead2']:
        l2 = M.space(g(st['lead2'], -4.5)); bus['leads'] += np.vstack([l2[0] * 0.55, l2[1]])
    from pedalboard import Pedalboard as PB, HighShelfFilter as HS, LowpassFilter as LP, HighpassFilter as HP, Reverb
    dr = PB([HS(8000, -4.0), LP(14000)])(dr.astype(np.float32), SR)
    bus['drums'] += dr * (10 ** (2.0 / 20)) / (np.sqrt(np.mean(dr ** 2)) + 1e-9) * 0.1
    if claps: bus['drums'] += M.pan(level(cl, -6.0), 0.0)
    if k808: bus['drums'] += M.pan(np.tanh(2.5 * level(sub, -6.0) / 0.1) * 0.1 * 10 ** (-6.0 / 20), 0.0)   # saturated: harmonics read on small speakers
    pumpg = pump(n, pumps, depth_db=-12.0) if pumps else np.ones(n)
    for inst, y in inst_audio.items():
        b_, dbv, p = LEVEL[inst]
        y = level(y, dbv)
        y = y if y.ndim == 2 else M.pan(y, p)
        if y.ndim == 2 and p != 0 and inst not in SURGE:   # narrow and place stereo orchestral samples
            mono = y.mean(0); y = 0.5 * y + 0.5 * M.pan(mono, p)
        if inst in ('arp', 'pad', 'sbass'): y = y * pumpg[None]
        if inst in ('pad',): y = PB([HP(180)])(y.astype(np.float32), SR)
        bus[b_] += y
    from pedalboard import PeakFilter as PK, Delay as DL
    bus['orch'] = PB([HP(250), PK(3000, -3.0, 1.0), Reverb(room_size=0.7, damping=0.5, wet_level=0.25, dry_level=0.85, width=1.0)])(bus['orch'], SR)
    bus['choir'] = PB([HP(250), PK(3500, -3.0, 1.0), Reverb(room_size=0.8, damping=0.5, wet_level=0.35, dry_level=0.75, width=1.0)])(bus['choir'], SR)
    bus['synth'] = PB([HP(120), DL(0.225, 0.25, 0.15), Reverb(room_size=0.55, damping=0.5, wet_level=0.18, dry_level=0.9, width=1.0)])(bus['synth'], SR)
    bus['fx'] += fx * 0.9
    # the stop before the final hit: everything drops out (tails to -30 dB), so the hit lands on near-silence
    if E.get('stop'):
        a, b = int(E['stop'][0] * SR), int(E['stop'][1] * SR) - 24
        gate = np.ones(n, np.float32); r_ = 360
        gate[a:b] = 0.03; gate[a - r_:a] = np.linspace(1, 0.03, r_)
        for name in bus:
            if name != 'fx': bus[name] = bus[name] * gate[None]
    # per-section bus automation
    for name in bus:
        segs = [(a, b, dbv) for (bn, a, b, dbv) in bus_segs if bn == name]
        if segs: bus[name] = bus[name] * envelope(n, segs)[None]
    y, stems_m, lufs = master_linear(bus)
    gain = 1.0
    # clean ring-out after the final hit, identical on mix and stems
    t = E['end']; tt = np.arange(n) / SR
    env = np.ones(n); a, b = t + 1.6, t + 5.6; msk = (tt >= a) & (tt < b)
    env[msk] = 10 ** (-60 * ((tt[msk] - a) / (b - a)) / 20); env[tt >= b] = 0
    cut = int((b + 0.2) * SR)
    y = (y * env[None])[:, :cut]
    sf.write(os.path.join(outdir, 'mix.wav'), y.T, SR, subtype='PCM_24')
    for name, x in stems_m.items():
        sf.write(os.path.join(outdir, f'stem_{name}.wav'), (x * env[None])[:, :cut].T.astype(np.float32), SR, subtype='FLOAT')
    json.dump({'marks': E['marks'], 'end': E['end'], 'lufs': lufs, 'bpm': A.BPM, 'master_gain': gain,
               'stems': sorted(bus)}, open(os.path.join(outdir, 'meta.json'), 'w'), indent=1)
    print('mix LUFS', round(lufs, 1), '->', outdir, flush=True)
    return E


def master_linear(bus, lufs=-10.0, ceiling=-1.0):
    """master chain made only of stages that can be shared by the stems: HPF, reference-matching FIR, gain, limiter gain
    curve. Returns (mix, stems) with sum(stems) == mix."""
    import pyloudnorm as pyln
    from pedalboard import Pedalboard, HighpassFilter
    from scipy.signal import fftconvolve
    meter = pyln.Meter(SR)
    hp = Pedalboard([HighpassFilter(32), HighpassFilter(32)])
    bus = {k: hp(v.astype(np.float32), SR) for k, v in bus.items()}
    h = M.match_eq_fir(sum(bus.values()))
    bus = {k: np.vstack([fftconvolve(ch, h, mode='same') for ch in v]).astype(np.float32) for k, v in bus.items()}
    s = sum(bus.values())
    k = 10 ** ((lufs - meter.integrated_loudness(s.T)) / 20)
    for _ in range(4):
        gcurve = M.limiter_gain(s * k, ceiling)
        Lz = meter.integrated_loudness((s * k * gcurve[None]).T)
        if abs(Lz - lufs) < 0.2: break
        k *= 10 ** ((lufs - Lz) / 20)
    stems = {name: (v * k * gcurve[None]).astype(np.float32) for name, v in bus.items()}
    mixo = sum(stems.values())
    c = 10 ** (ceiling / 20)
    return np.clip(mixo, -c, c), stems, Lz


def master_with_gain(mixst, lufs=-10.0, ceiling=-1.0):
    """M.master, but also returns the linear gain applied before the limiter (for stems at mix level). The reference
    EQ and bus compressor are skipped here so that stems sum to the mix; the mix gets them."""
    import pyloudnorm as pyln
    from pedalboard import Pedalboard, HighpassFilter, Compressor
    meter = pyln.Meter(SR)
    x = Pedalboard([HighpassFilter(32), HighpassFilter(32)])(mixst.astype(np.float32), SR)
    x, _ = M.match_eq(x)
    y = Pedalboard([Compressor(-16, 2.0, 25, 180)])(x.astype(np.float32), SR)
    L = meter.integrated_loudness(y.T)
    k = 10 ** ((lufs - L) / 20)
    y = y * k
    for _ in range(3):
        z = M.limiter(y, ceiling); Lz = meter.integrated_loudness(z.T)
        if abs(Lz - lufs) < 0.3: break
        y = y * 10 ** ((lufs - Lz) / 20); k *= 10 ** ((lufs - Lz) / 20)
    return z, Lz, float(k)
