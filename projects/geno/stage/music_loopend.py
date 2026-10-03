"""Forest Maze draft 2's loop end for the stage stream: FINAL's last bar without the stop, the drum fill running through
beat 4 into THEME A's downbeat.
    .venv/bin/python projects/geno/stage/music_loopend.py      # ~8 min -> $GENO_MUSIC/loopend/ (~/games/melee/work/music)
Why: draft 2 ends FINAL with an 8th-note stop (the band, orchestra and choir gated to -30 dB, the fill's last 16th cut)
so the trailer's final hit lands on silence. The stage loop jumps from 91.2 s back to THEME A (9.6 s), so the stop became
a 150 ms dropout on every pass (Michael, 2026-09-30: "a very obvious gap"). The stage needs its own last bar; draft 2's
master and stems stay as they are, for the trailer.
How: the arrangement's renderer (music/src/render2.py) normalises nearly every track by its whole-song peak or RMS: the
guitar and bass DI peaks set the NAM amps' drive, and each band stem, drum bus, orchestral layer and the master's
EQ and loudness gain are scaled by the whole song. A plain re-render without the stop would move every one of them.
So the renderer's mix path runs here twice, with each whole-song factor routed through `Freeze`:
  pass 1 is draft 2 as it was, checked against its master, and records every factor;
  pass 2 is the loop end, and replays pass 1's factors. It has no stop and no final hit: FINAL's last 8th plays as
  written (the tom fill's last 16th, the chugs, bass and held leads, violins and choir) and nothing follows it. The loop
  itself supplies THEME A: the stream wraps from 91.2 s to 9.6 s. (A THEME A rendered after FINAL here would sound
  early, since the players are humanised: its downbeat crash lands at 91.191 s, then the stream's own crash follows.)
Pass 2 then leaves pass 1 only at the stop (measured in the report). Pass 1 is not bit-exact with draft 2's master:
Surge XT starts its oscillators at a random phase on every render, so the sections with synths (INTRO build, TRANSITION,
GLADE) differ, and pass 2 reuses pass 1's synth renders. FINAL has no synths: there the re-render matches draft 2's stems
to -66 to -76 dB, which is why the stream takes draft 2 up to FINAL's last bar and this render only from there.
sfizz_render streams sample tails from disk on a background thread, and under load its output changes (measured: renders
beside other work differed from draft 2's guitars at -31 dB and its orchestra at -18 dB in FINAL, relative to the
signal; clean renders differ at -66 to -76 dB). So every sfizz render here
repeats until two runs agree sample for sample, and both passes are checked: a render that still misses stops before
writing anything.
Audio stays out of git: it lives under ~/games/melee/work/music/loopend/.
"""
import json, os, sys, time
import numpy as np

MUSIC = os.path.expanduser(os.environ.get('GENO_MUSIC', '~/games/melee/work/music'))   # the instruments and draft 2's renders
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'music', 'forest_maze', 'src'))   # the arrangement
import mix as M, orch as O, sfz, guitars2 as G2, surgepatch as SP                  # noqa: E402
import render as R, render2 as R2, draft2 as D2, drumkit as DK                      # noqa: E402

SR = R2.SR
OUT = os.path.join(MUSIC, 'loopend')
DRAFT2 = os.path.join(MUSIC, 'forest_maze_metal_draft2.wav')
STEMS2 = os.path.join(MUSIC, 'stems_draft2', 'draft2_stem_{}.wav')
LOOPEND = os.path.join(OUT, 'forest_maze_metal_draft2_loopend.wav')
GUARD_DB = -50.0                          # pass 1 must match draft 2's stems in FINAL at least this well (clean: -66 to -76)
STEM_WIN = (84.0, 97.0)                   # the stems written for pass 2: FINAL's second half and the ring after it


class Freeze:
    """Every whole-song normaliser, by name. Recording: store the value computed. Replaying: return the stored value,
    and keep what this pass would have computed, so the report shows how far a plain re-render would have moved it."""
    def __init__(self):
        self.vals, self.fresh, self.mode = {}, {}, 'record'

    def __call__(self, key, fn):
        if self.mode == 'record':
            assert key not in self.vals, key
            self.vals[key] = fn(); return self.vals[key]
        v = fn(); self.fresh[key] = v
        return self.vals[key]


F = Freeze()
_ctx = {'name': '', 'i': 0}


def _norm_peak(x, p):                      # mix.norm_peak, frozen per chain and call
    key = f"peak:{_ctx['name']}:{_ctx['i']}"; _ctx['i'] += 1
    m = F(key, lambda: float(np.abs(x).max()))
    return x * (p / m) if m > 0 else x


M.norm_peak = _norm_peak


_sfz_render = sfz.render
SFIZZ = {'renders': 0, 'calls': 0, 'disagreed': 0}


def _sfz_agreed(*a, **kw):
    """sfz.render until two runs agree sample for sample. sfizz_render streams sample tails from disk on a background
    thread and, under load, renders some notes short (measured 2026-09-30: a loaded render differed from draft 2's
    orchestra at -18 dB in FINAL); unloaded, it is exact run to run."""
    SFIZZ['calls'] += 1; outs = []
    for _ in range(8):
        y = _sfz_render(*a, **kw); SFIZZ['renders'] += 1
        if any(o.shape == y.shape and np.array_equal(o, y) for o in outs):
            SFIZZ['disagreed'] += len(outs) > 1
            return y
        outs.append(y)
    raise RuntimeError('sfizz_render: 8 runs, no two agree')


sfz.render = _sfz_agreed


def chain(name, fn, *a, **kw):
    _ctx['name'], _ctx['i'] = name, 0
    return fn(*a, **kw)


def _rms(x): return float(np.sqrt(np.mean(x ** 2)))


class Kit(DK.Kit):
    tag = 'drums'                          # which render this is: the drum track, or the riser's one crash

    def mixdown(self, bus, n):             # drumkit.Kit.mixdown, with each bus's RMS frozen
        from pedalboard import (Pedalboard, HighpassFilter, PeakFilter, Compressor, Gain, HighShelfFilter,
                                LowpassFilter)
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
        for b in DK.BUSES:
            x = chains[b](bus[b], SR)[:, :n]
            rms = F(f'kit:{self.tag}:{b}', lambda: float(np.sqrt(np.mean(x ** 2)))) + 1e-9
            out += x * (10 ** (levels[b] / 20)) * (0.05 / rms if b in ('kick', 'snare') else 0.05 / max(rms, 1e-9) * 0.7)
        return Pedalboard([Compressor(-14, 2.5, 8, 100)])(out, SR)


def build_loopend(secs):
    """render2.build without the final hit and the stop: FINAL's last bar as written, fill and all."""
    E = R.build_events(secs, tail=6.0)
    layers, pumps, bus_segs, t0 = {}, [], [], 0.0
    for sec in secs:
        L = R.sec_len(sec)
        for inst, ns in O.section_layers(sec, t0).items():
            layers.setdefault(inst, []).extend(ns)
        if sec.get('pump'):
            pumps += [t0 + k * 0.3 for k in range(int(round(L / 0.3)))]
        for bus, dbv in sec.get('bus_gain', {}).items():
            bus_segs.append((bus, t0, t0 + L, dbv))
        t0 += L
    E['end'] = round(E['end'], 6)
    return E, layers, pumps, bus_segs, E['total']


def render_pass(E, layers, pumps, bus_segs, total, kit):
    """render2.render's mix path (same order, same chains), with the whole-song normalisers frozen. Returns the mastered
    mix, the stems at mix level, the ring-out envelope, and the cut length."""
    n = int(total * SR)
    fit = lambda x: (x[..., :n] if x.shape[-1] >= n else np.pad(x, [(0, 0)] * (x.ndim - 1) + [(0, n - x.shape[-1])]))
    tm = time.time()
    st = {}
    st['rL'] = fit(chain('rL', M.rhythm_chain, G2.rhythm_di(E['rL'], total, seed=11)))
    st['rR'] = fit(chain('rR', M.rhythm_chain, G2.rhythm_di(E['rR'], total, seed=23, detune_cents=6), amp_name=M.RHYTHM_AMP_R))
    st['bass'] = fit(chain('bass', M.bass_chain, G2.bass_di(E['bass'], total, seed=5)))
    st['lead1'] = fit(chain('lead1', M.lead_chain, G2.lead_di(E['lead1'], total, seed=3)))
    st['lead1b'] = fit(chain('lead1b', M.lead_chain, G2.lead_di(E['lead1'], total, seed=7, vib_rate=5.9)))
    st['lead2'] = fit(chain('lead2', M.lead_chain, G2.lead_di(E['lead2'], total, seed=4, vib_rate=5.2))) if E['lead2'] else np.zeros(n, np.float32)
    print('band', round(time.time() - tm, 1), 's', flush=True)
    if E.get('stop'):
        a, b = int(E['stop'][0] * SR), int(E['stop'][1] * SR) - 48
        gate = np.ones(n, np.float32); r_ = 240; gate[a:b] = 0; gate[a - r_:a] = np.linspace(1, 0, r_)
        for k in st: st[k] = st[k] * gate
    inst_audio = {}
    for inst, ns in layers.items():
        if inst in R2.VSCO:
            y = sfz.render(sfz.vsco(R2.VSCO[inst]), sfz.notes_inst(ns), total)
        elif inst in R2.SURGE:              # random oscillator phase per render: pass 2 reuses pass 1's
            y = F(f'surge:{inst}', lambda: SP.render(R2.PATCH + R2.SURGE[inst] + '.fxp', ns, total))
        elif inst == 'choir':
            y = R2.render_choir(ns, total)
        else:
            continue
        inst_audio[inst] = fit(y.astype(np.float32))
    print('orch/synth/choir', round(time.time() - tm, 1), 's', flush=True)
    claps = [e for e in E['drums'] if e[1] == 'clap']
    k808 = [e for e in E['drums'] if e[1] == 'kick808']
    assert not claps and not k808            # draft 2 has neither (the electro GLADE did)
    kit.tag = 'drums'
    dr = kit.render([e for e in E['drums'] if e[1] not in ('clap', 'kick808')], total)[:, :n]
    kit.tag = 'riser'
    # the reverse crash for the risers: pass 2 renders more drum events first, so the kit's round-robin state differs
    cr = F('riser_crash', lambda: kit.render([(0.0, 'crash1', 1.0)], 2.2)[:, ::-1].copy())
    fx = np.zeros((2, n), np.float32)
    for t in E['risers']:
        i1 = int(t * SR); i0 = max(0, i1 - cr.shape[1]); fx[:, i0:i1] += 0.8 * cr[:, cr.shape[1] - (i1 - i0):]
    for t in E['booms']:
        L = int(1.6 * SR); tt = np.arange(L) / SR
        f = 30 + 28 * np.exp(-tt / 0.25); ph = 2 * np.pi * np.cumsum(f) / SR
        b = np.sin(ph) * np.exp(-tt / 0.45) * np.minimum(1, tt / 0.004)
        i0 = int(t * SR); e = min(n, i0 + L); fx[:, i0:e] += 0.5 * b[None, :e - i0]
    g = lambda name, x, dbv: x * (10 ** (dbv / 20)) / (F(f'rms:{name}', lambda: _rms(x)) + 1e-9) * 0.1
    bus = {k: np.zeros((2, n), np.float32) for k in ('guitars', 'bass', 'leads', 'drums', 'orch', 'synth', 'choir', 'fx')}
    bus['guitars'] += M.pan(g('rL', st['rL'], -2.0), -0.95) + M.pan(g('rR', st['rR'], -2.0), 0.95)
    bus['bass'] += M.pan(g('bass', st['bass'], 0.0), 0.0)
    l1 = M.space(g('lead1', st['lead1'], -2.0)); l1b = M.space(g('lead1b', st['lead1b'], -2.0))
    bus['leads'] += np.vstack([l1[0], l1[1] * 0.75]) + np.vstack([l1b[0] * 0.75, l1b[1]])
    if E['lead2']:
        l2 = M.space(g('lead2', st['lead2'], -4.5)); bus['leads'] += np.vstack([l2[0] * 0.55, l2[1]])
    from pedalboard import (Pedalboard as PB, HighShelfFilter as HS, LowpassFilter as LP, HighpassFilter as HP, Reverb,
                            PeakFilter as PK, Delay as DL)
    dr = PB([HS(8000, -4.0), LP(14000)])(dr.astype(np.float32), SR)
    bus['drums'] += dr * (10 ** (2.0 / 20)) / (F('rms:drums', lambda: _rms(dr)) + 1e-9) * 0.1
    pumpg = R2.pump(n, pumps, depth_db=-12.0) if pumps else np.ones(n)
    for inst, y in inst_audio.items():
        b_, dbv, p = R2.LEVEL[inst]
        y = y * (10 ** (dbv / 20) * 0.1 / F(f'act:{inst}', lambda: R2.act_rms(y)))
        y = y if y.ndim == 2 else M.pan(y, p)
        if y.ndim == 2 and p != 0 and inst not in R2.SURGE:
            mono = y.mean(0); y = 0.5 * y + 0.5 * M.pan(mono, p)
        if inst in ('arp', 'pad', 'sbass'): y = y * pumpg[None]
        if inst in ('pad',): y = PB([HP(180)])(y.astype(np.float32), SR)
        bus[b_] += y
    bus['orch'] = PB([HP(250), PK(3000, -3.0, 1.0), Reverb(room_size=0.7, damping=0.5, wet_level=0.25, dry_level=0.85, width=1.0)])(bus['orch'], SR)
    bus['choir'] = PB([HP(250), PK(3500, -3.0, 1.0), Reverb(room_size=0.8, damping=0.5, wet_level=0.35, dry_level=0.75, width=1.0)])(bus['choir'], SR)
    bus['synth'] = PB([HP(120), DL(0.225, 0.25, 0.15), Reverb(room_size=0.55, damping=0.5, wet_level=0.18, dry_level=0.9, width=1.0)])(bus['synth'], SR)
    bus['fx'] += fx * 0.9
    if E.get('stop'):
        a, b = int(E['stop'][0] * SR), int(E['stop'][1] * SR) - 24
        gate = np.ones(n, np.float32); r_ = 360
        gate[a:b] = 0.03; gate[a - r_:a] = np.linspace(1, 0.03, r_)
        for name in bus:
            if name != 'fx': bus[name] = bus[name] * gate[None]
    for name in bus:
        segs = [(a, b, dbv) for (bn, a, b, dbv) in bus_segs if bn == name]
        if segs: bus[name] = bus[name] * R2.envelope(n, segs)[None]
    y, stems = master_linear(bus)
    t = E['end']; tt = np.arange(n) / SR
    env = np.ones(n); a, b = t + 1.6, t + 5.6; msk = (tt >= a) & (tt < b)
    env[msk] = 10 ** (-60 * ((tt[msk] - a) / (b - a)) / 20); env[tt >= b] = 0
    cut = int((b + 0.2) * SR)
    print('mix', round(time.time() - tm, 1), 's', flush=True)
    return (y * env[None])[:, :cut], stems, env, cut


def master_linear(bus, lufs=-10.0, ceiling=-1.0):
    """render2.master_linear with its EQ (FIR) and gain frozen; the limiter's gain curve is local (1.5 ms lookahead,
    60 ms release), so it is computed on this pass's own sum."""
    import pyloudnorm as pyln
    from pedalboard import Pedalboard, HighpassFilter
    from scipy.signal import fftconvolve
    meter = pyln.Meter(SR)
    hp = Pedalboard([HighpassFilter(32), HighpassFilter(32)])
    bus = {k: hp(v.astype(np.float32), SR) for k, v in bus.items()}
    h = F('master:fir', lambda: M.match_eq_fir(sum(bus.values())))
    bus = {k: np.vstack([fftconvolve(ch, h, mode='same') for ch in v]).astype(np.float32) for k, v in bus.items()}
    s = sum(bus.values())

    def gain():
        k = 10 ** ((lufs - meter.integrated_loudness(s.T)) / 20)
        for _ in range(4):
            kg = k
            gcurve = M.limiter_gain(s * k, ceiling)
            Lz = meter.integrated_loudness((s * k * gcurve[None]).T)
            if abs(Lz - lufs) < 0.2: break
            k *= 10 ** ((lufs - Lz) / 20)
        return (k, kg)
    k, kg = F('master:gain', gain)
    gcurve = M.limiter_gain(s * kg, ceiling)
    stems = {name: (v * k * gcurve[None]).astype(np.float32) for name, v in bus.items()}
    c = 10 ** (ceiling / 20)
    return np.clip(sum(stems.values()), -c, c), stems


def db(x): return round(float(20 * np.log10(max(x, 1e-12))), 2)


def main():
    import soundfile as sf
    import pyloudnorm as pyln
    os.makedirs(OUT, exist_ok=True)
    rep = dict(draft2=DRAFT2, loopend=LOOPEND)
    kit = Kit()
    # ---- pass 1: draft 2 as it was, recording every whole-song factor
    F.mode = 'record'
    y1, stems1, env1, cut1 = render_pass(*R2.build(D2.SECTIONS, D2.FINAL_HIT), kit)
    ref, sr = sf.read(DRAFT2, dtype='float64'); ref = ref.T
    assert sr == SR and ref.shape == y1.shape, (sr, ref.shape, y1.shape)
    d = np.abs(y1 - ref)
    blocks = []
    for t0 in range(int(ref.shape[1] / SR)):
        x, yb = ref[:, t0 * SR:(t0 + 1) * SR], y1[:, t0 * SR:(t0 + 1) * SR]
        blocks.append((t0, db(float(np.sqrt(np.mean((yb - x) ** 2)) / (np.sqrt(np.mean(x ** 2)) + 1e-12)))))
    rep['pass1_vs_draft2'] = dict(max_abs_diff=float(d.max()), max_abs_diff_db=db(d.max()),
                                  residual_rms_db=db(float(np.sqrt(np.mean((y1 - ref) ** 2)))),
                                  seconds_over_minus40db_rel=[b for b in blocks if b[1] > -40],
                                  final_worst_rel_db=max(v for t, v in blocks if 82 <= t < 90),
                                  note='Surge XT renders with a random oscillator phase: the synth sections differ; '
                                       'FINAL (82-90 s) has no synths',
                                  stems_max_abs_diff_db={})
    fin = slice(int(82.0 * SR), int(90.9 * SR)); rep['pass1_vs_draft2']['final_stems_rel_db'] = {}
    for name, x in stems1.items():          # draft 2's stems are float32, written with the ring-out envelope
        s2, _ = sf.read(STEMS2.format(name), dtype='float32'); s2 = s2.T; x = (x * env1[None])[:, :cut1]
        rep['pass1_vs_draft2']['stems_max_abs_diff_db'][name] = db(float(np.abs(x - s2).max()))
        e = float(np.sqrt(np.mean(s2[:, fin].astype(np.float64) ** 2)))
        if e > 1e-5:                         # the stems that play in FINAL
            rep['pass1_vs_draft2']['final_stems_rel_db'][name] = db(float(np.sqrt(np.mean((x[:, fin] - s2[:, fin]) ** 2))) / e)
    del stems1
    bad = {k: v for k, v in rep['pass1_vs_draft2']['final_stems_rel_db'].items() if v > GUARD_DB}
    if bad:                                  # sfizz_render streams sample tails on a background thread and, under load,
        raise SystemExit(f'pass 1 misses draft 2 in FINAL {bad} dB (sfizz {SFIZZ})')
    print('pass 1 vs draft 2:', rep['pass1_vs_draft2'], flush=True)
    # ---- pass 2: the loop end, replaying pass 1's factors (a fresh round-robin state for the kit, as pass 1 had)
    F.mode = 'replay'
    kit.rng = np.random.default_rng(0); kit.rr = {}
    E2 = build_loopend(D2.SECTIONS)
    y2, stems2, env2, cut2 = render_pass(*E2, kit)
    # the master EQ convolves the whole song in one FFT (float32), so any change spreads round-off everywhere: the
    # change's onset is where the difference reaches audible scale (-40 dBFS); before it, the largest difference
    dd = np.abs(y2 - y1).max(0)
    loud = int(np.argmax(dd > 1e-2))
    rep['pass2_vs_pass1'] = dict(first_over_40db_s=round(loud / SR, 4), max_abs_diff_before_91s_db=db(float(dd[:int(91.0 * SR)].max())),
                                 note="the stop's gate began at 91.0575 s (91.065 s, less its 7.5 ms ramp); before it the passes differ "
                                      "only through the master EQ (its 43 ms reach, and FFT round-off)")
    del y1
    if rep['pass2_vs_pass1']['first_over_40db_s'] < 91.0 or rep['pass2_vs_pass1']['max_abs_diff_before_91s_db'] > -60:
        raise SystemExit(f"pass 2 leaves pass 1 before the stop {rep['pass2_vs_pass1']} (sfizz {SFIZZ})")
    sf.write(LOOPEND, y2.T, SR, subtype='PCM_24')
    a, b = (int(t * SR) for t in STEM_WIN)
    os.makedirs(os.path.join(OUT, 'stems'), exist_ok=True)
    for name, x in stems2.items():
        sf.write(os.path.join(OUT, 'stems', f'loopend_stem_{name}.wav'), (x * env2[None])[:, a:b].T, SR, subtype='FLOAT')
    # ---- how far a plain re-render would have moved each factor
    moved = {}
    for key, v in F.vals.items():
        f = F.fresh.get(key)
        if isinstance(v, float) and f is not None:
            moved[key] = round(float(20 * np.log10(max(f, 1e-12) / max(v, 1e-12))), 3)
    k1, k2 = F.vals['master:gain'][0], F.fresh['master:gain'][0]
    moved['master:gain'] = round(float(20 * np.log10(k2 / k1)), 3)
    rep['frozen_factors_moved_db'] = dict(sorted(moved.items(), key=lambda kv: -abs(kv[1])))
    # ---- where pass 2 leaves draft 2
    y2r, _ = sf.read(LOOPEND, dtype='float64'); y2r = y2r.T
    m = min(y2r.shape[1], ref.shape[1])
    dd = np.abs(y2r[:, :m] - ref[:, :m]).max(0)
    first = int(np.argmax(dd > 1e-6))
    fin = slice(int(81.6 * SR), int(90.9 * SR)); sp = slice(int(89.5 * SR), int(90.5 * SR))
    rel = lambda s_: db(float(np.sqrt(np.mean((y2r[:, s_] - ref[:, s_]) ** 2)) / np.sqrt(np.mean(ref[:, s_] ** 2))))
    rep['pass2_vs_draft2'] = dict(final_rel_db=rel(fin), final_max_abs_diff_db=db(float(dd[fin].max())),
                                  at_90s_splice_max_abs_diff_db=db(float(dd[sp].max())),
                                  note='FINAL, 81.6-90.9 s: the part the stream keeps from draft 2 ends at 90.0 s')
    # ---- the last bar, level by level: draft 2 and the loop end (RMS dBFS)
    meter = pyln.Meter(SR)
    def seg_db(x, t0, t1): return db(float(np.sqrt(np.mean(x[:, int(t0 * SR):int(t1 * SR)] ** 2))))
    rep['last_bar'] = dict(
        draft2=dict(beats_1_3=seg_db(ref, 90.0, 90.9), beat_4_first_8th=seg_db(ref, 90.9, 91.05), last_8th=seg_db(ref, 91.05, 91.2)),
        loopend=dict(beats_1_3=seg_db(y2r, 90.0, 90.9), beat_4_first_8th=seg_db(y2r, 90.9, 91.05), last_8th=seg_db(y2r, 91.05, 91.2),
                     ),
        final_lufs=dict(draft2=round(meter.integrated_loudness(ref[:, int(81.6 * SR):int(91.05 * SR)].T), 2),
                        loopend=round(meter.integrated_loudness(y2r[:, int(81.6 * SR):int(91.2 * SR)].T), 2)))
    rep['stems'] = dict(dir=os.path.join(OUT, 'stems'), window_s=STEM_WIN)
    rep['sfizz'] = dict(SFIZZ, note='renders per call until two agree; disagreed = calls whose first two runs differed')
    json.dump(rep, open(os.path.join(OUT, 'report.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
