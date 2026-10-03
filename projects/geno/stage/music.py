"""The Forest Maze stage music: metal draft 2 (Michael, 2026-09-29) cut into a looping stage stream, gr_forestmaze.hps.
    .venv/bin/python projects/geno/stage/music.py build     # $MELEE_WORK/stage/music/: the stream, a report, seam audio
    .venv/bin/python projects/geno/stage/music.py levels    # the six starters' streams: loudness, peak, loop
    .venv/bin/python projects/geno/stage/music.py seam RUN  # the in-game capture's seam (dsp.wav from a menu test)
    .venv/bin/python projects/geno/stage/music.py review OLD.hps   # before/after seam audio, RMS, review_seam.html
The cut: the intro (0-9.6 s) plays once; the loop runs from Theme A's downbeat (9.6 s, bar 9) to the end of the final
chorus (91.2 s, bar 77), leaving out the final hit. The loop is 68 bars of 200 BPM, 81.6 s (NOTES.md's grid).
The loop's last bar is the stage's own: draft 2 stops everything for FINAL's last 8th so the trailer's final hit lands
on silence, and looped, that stop was a 150 ms dropout before every return to the theme (Michael, 2026-09-30: "a very
obvious gap"). music_loopend.py re-renders draft 2 without the stop, with the same instruments, mix and master gains, so
the drum fill runs through beat 4 into the theme's downbeat. The stream takes draft 2 up to FINAL's last bar (90.0 s)
and that render from there (the two match there to about -59 dBFS: measured at the splice), and the loop's last 4 ms
cross into the 4 ms before the theme's downbeat, so the waveform runs on across the jump.
Stage streams are 32 kHz stereo DSP-ADPCM (measured: every vanilla stage stream). The loop lands on the downbeat
exactly: 16 samples of silence lead the stream, so the loop start is 307216 = 5486 x 56 samples, and hps.write's
exact_loop cuts the block before it short (as HAL's own streams do). The level is the six starters' streams' median
integrated loudness, measured here, with the peak kept under theirs.
Game audio stays out of git: the stream, the decodes and the captures live under $MELEE_WORK.
"""
import html, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'machinima', 'melee', 'audio'))
import hps  # noqa: E402

WORK = os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work'))
DISC = os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc'))
MUSIC = os.path.expanduser(os.environ.get('GENO_MUSIC', '~/games/melee/work/music'))   # projects/geno/music/README.md
SRC = os.path.join(MUSIC, 'forest_maze_metal_draft2.wav')
LOOPEND = os.path.join(MUSIC, 'loopend', 'forest_maze_metal_draft2_loopend.wav')   # music_loopend.py
SPLICE_S = 90.0                       # FINAL's last bar: from here the stream takes the loop end
WRAP_XF_S = 0.004                     # the loop's end crossfades into the audio just before the loop start
OUT = os.path.join(WORK, 'stage', 'music')
RATE = 32000
BPM = 200.0
INTRO_S, END_S = 9.6, 91.2            # Theme A's downbeat, and the downbeat of the final hit (left out)
LEAD = 16                             # samples of silence first, so the loop start is a multiple of 56
STARTERS = {'Battlefield': 'sp_zako.hps', 'Final Destination': 'sp_end.hps', "Yoshi's Story": 'ystory.hps',
            'Dream Land': 'old_kb.hps', 'Fountain of Dreams': 'izumi.hps', 'Pokémon Stadium': 'pstadium.hps'}


def loudness(x, rate):
    import pyloudnorm as pyln
    return pyln.Meter(rate).integrated_loudness(x.astype(np.float64))


def true_peak_db(x, rate):
    from scipy.signal import resample_poly
    up = resample_poly(x, 4, 1, axis=0)
    return 20 * np.log10(max(1e-9, float(np.max(np.abs(up)))))


def levels():
    rows = []
    for name, f in STARTERS.items():
        h = hps.read(os.path.join(DISC, 'files', 'audio', f))
        x = h['pcm'].astype(np.float64) / 32768.0
        spb = hps.BLOCK_CH // 8 * 14
        lb = h['loop_block']
        # the loop's sample: the sum of the blocks before it (vanilla blocks vary in size)
        loop_sample = 0
        for b in h['blocks'][:lb or 0]:
            nib = b['lastnib'] + 1
            loop_sample += (nib // 16) * 14 + max(0, nib % 16 - 2)
        rows.append(dict(stage=name, file=f, seconds=round(len(x) / h['rate'], 3), rate=h['rate'],
                         lufs=round(loudness(x, h['rate']), 2), true_peak_db=round(true_peak_db(x, h['rate']), 2),
                         loop_s=round(loop_sample / h['rate'], 3), loop_block=lb,
                         block_sizes=sorted({b['size'] // h['channels'] for b in h['blocks']})))
    return rows


def seam_metric(x, i, rate, win=0.010):
    """How much a boundary at sample i stands out: the high-passed energy in the 10 ms after it against the 50 ms around
    it (excluding it), in dB; and the sample step at i against the median step nearby."""
    from scipy.signal import butter, sosfilt
    sos = butter(4, 4000, 'hp', fs=rate, output='sos')
    hp = sosfilt(sos, x.mean(1) if x.ndim == 2 else x)
    w = int(win * rate)
    at = hp[i:i + w]
    ctx = np.concatenate([hp[i - 5 * w:i - w], hp[i + 2 * w:i + 6 * w]])
    e_at = 10 * np.log10(np.mean(at ** 2) + 1e-12); e_ctx = 10 * np.log10(np.mean(ctx ** 2) + 1e-12)
    m = x.mean(1) if x.ndim == 2 else x
    step = abs(m[i] - m[i - 1]); steps = np.abs(np.diff(m[i - 5 * w:i + 5 * w]))
    return dict(hf_burst_db=round(e_at - e_ctx, 2), step=round(float(step), 5), step_vs_median=round(float(step / (np.median(steps) + 1e-9)), 2),
                step_vs_p99=round(float(step / (np.percentile(steps, 99) + 1e-9)), 3))


def played_wrap(dec, loop, after_s=10.0):
    """The stream as the game plays it through the first wrap: the whole first pass, then the loop start again."""
    return np.concatenate([dec, dec[loop:loop + int(after_s * RATE)]])


def listen(dec, loop, seam_path, full_path=None):
    """Listening files: the seam (the loop's last 8 s, then the first 8 s after the loop point) and, optionally, the
    stream's first loop and a half (the intro, the whole loop, then half the loop again)."""
    import soundfile as sf
    n = len(dec)
    sf.write(seam_path, played_wrap(dec, loop)[n - 8 * RATE:n + 8 * RATE], RATE, subtype='PCM_16')
    if full_path:
        half = (n - loop) // 2
        sf.write(full_path, np.concatenate([dec, dec[loop:loop + half]]), RATE, subtype='PCM_16')


def seam_rms(dec, loop, win=0.010, ctx_s=0.3, span=(90.9, 9.8), chart=(90.6, 10.0)):
    """The seam's level as the game plays it: RMS (both channels' power) in 10 ms windows from `span[0]` s through the
    wrap to `span[1]` s of the next pass, windows aligned to the wrap. A window's dip is its level against the median
    of the windows within `ctx_s` either side (one quarter note either way: a 150 ms stop can't pull that median
    down). FINAL's own windows, away from its last bar (81.9-90.6 s, context inside 81.6-90.9), give the normal
    between-note dip; the seam passes when its deepest dip is no deeper than FINAL's deepest."""
    n = len(dec); w = int(round(win * RATE)); c = int(round(ctx_s / win))
    p = played_wrap(dec, loop)
    def levels(i0, k):                      # k windows from sample i0
        seg = p[i0:i0 + k * w].reshape(k, w, -1)
        return 10 * np.log10(np.mean(seg ** 2, axis=(1, 2)) + 1e-12)
    def dips(L):                            # L padded by c windows each side -> dips of the middle
        return np.array([L[i] - np.median(np.concatenate([L[i - c:i], L[i + 1:i + c + 1]])) for i in range(c, len(L) - c)])
    # FINAL, first pass: windows on the bar grid (the stream's sample for song time t is LEAD + t * RATE)
    f0 = LEAD + int(round(81.9 * RATE)); kf = int(round((90.6 - 81.9) / win))
    Lf = levels(f0 - c * w, kf + 2 * c); df = dips(Lf); Lf = Lf[c:-c]
    # the seam: k windows either side of the wrap (window 0 starts on it); song time before it counts back from 91.2
    def around(t_before, t_after):
        kb, ka = int(round((END_S - t_before) / win)), int(round((t_after - INTRO_S) / win))
        L = levels(n - (kb + c) * w, kb + ka + 2 * c)
        t = [round(END_S - (kb - i) * win, 3) if i < kb else round(INTRO_S + (i - kb) * win, 3) for i in range(kb + ka)]
        return t, L[c:-c], dips(L)
    t, L, d = around(*span)
    i = int(np.argmin(d)); j = int(np.argmin(L)); kb = t.index(INTRO_S)
    tc, Lc, dc = around(*chart)
    return dict(window_ms=win * 1000, context_s=ctx_s, span_s=span,
                final=dict(level_db=dict(median=round(float(np.median(Lf)), 2), p5=round(float(np.percentile(Lf, 5)), 2),
                                         p95=round(float(np.percentile(Lf, 95)), 2), min=round(float(Lf.min()), 2)),
                           dip_db=dict(p5=round(float(np.percentile(df, 5)), 2), p1=round(float(np.percentile(df, 1)), 2),
                                       min=round(float(df.min()), 2))),
                seam=dict(level_min_db=round(float(L[j]), 2), level_min_at_s=t[j],
                          dip_min_db=round(float(d[i]), 2), dip_min_at_s=t[i],
                          loop_end_dip_min_db=round(float(d[:kb].min()), 2), loop_end_level_min_db=round(float(L[:kb].min()), 2),
                          after_wrap_dip_min_db=round(float(d[kb:].min()), 2),
                          surrounding_median_db=round(float(np.median(L)), 2)),
                passes=bool(d.min() >= df.min()),
                chart=dict(t=tc, level_db=[round(float(v), 2) for v in Lc], dip_db=[round(float(v), 2) for v in dc]))


def build():
    import soundfile as sf
    from scipy.signal import resample_poly
    os.makedirs(OUT, exist_ok=True)
    src, sr = sf.read(SRC, dtype='float64')
    end, sr2 = sf.read(LOOPEND, dtype='float64')
    assert sr == sr2 == 48000
    # the splice: draft 2, then the loop end from FINAL's last bar, crossfaded over 10 ms (music_loopend.py checks that
    # its render matches draft 2 through FINAL; the report says how far apart the two are at the splice)
    s0 = int(round(SPLICE_S * sr)); xf = int(0.010 * sr)
    near = slice(s0 - sr // 2, s0 + sr // 2)
    splice = dict(at_s=SPLICE_S, loopend=LOOPEND, max_abs_diff_near=float(np.abs(src[near] - end[near]).max()))
    ramp = np.linspace(0, 1, xf)[:, None]
    src = np.concatenate([src[:s0 - xf // 2], src[s0 - xf // 2:s0 + xf - xf // 2] * (1 - ramp) + end[s0 - xf // 2:s0 + xf - xf // 2] * ramp,
                          end[s0 + xf - xf // 2:int(round(END_S * sr)) + sr]])
    x = resample_poly(src, 2, 3, axis=0)                   # 48 -> 32 kHz
    n_end = int(round(END_S * RATE)); n_loop = int(round(INTRO_S * RATE))
    x = x[:n_end]
    # the wrap: the loop's last 4 ms cross into the 4 ms before the loop start (equal power), so the waveform runs on
    # across the jump as it does on the first pass (without it the jump is a 0.27 full-scale step, measured)
    k = int(round(WRAP_XF_S * RATE)); wp = np.sin(0.5 * np.pi * (np.arange(k) + 0.5) / k)[:, None]
    x[n_end - k:] = x[n_end - k:] * np.sqrt(1 - wp ** 2) + x[n_loop - k:n_loop] * wp
    x = np.concatenate([np.zeros((LEAD, 2)), x])
    loop = n_loop + LEAD
    assert loop % 56 == 0, loop
    # the level: the starters' median loudness, the peak under the loudest starter's
    lv = levels()
    target = float(np.median([r['lufs'] for r in lv]))
    peak_cap = min(-1.0, max(r['true_peak_db'] for r in lv))
    l0 = loudness(x, RATE)
    g = 10 ** ((target - l0) / 20)
    y = x * g
    tp = true_peak_db(y, RATE)
    if tp > peak_cap:                                      # never louder than a starter's peak: lower the whole cut
        y *= 10 ** ((peak_cap - tp) / 20)
    pcm = np.clip(np.round(y * 32767), -32768, 32767).astype(np.int16)
    path = os.path.join(OUT, 'gr_forestmaze.hps')
    _, rep = hps.write(path, pcm, RATE, loop_start=loop, exact_loop=True)
    # the stream as the game plays it: decode, then the first pass and a second pass through the seam
    h = hps.read(path)
    dec = h['pcm'].astype(np.float64) / 32768.0
    n = len(dec)
    played = np.concatenate([dec, dec[loop:loop + int(8 * RATE)]])
    listen(dec, loop, os.path.join(OUT, 'seam_listen.wav'), os.path.join(OUT, 'loop_and_a_half.wav'))
    sf.write(os.path.join(OUT, 'gr_forestmaze_decoded.wav'), dec, RATE, subtype='PCM_16')
    res = dict(source=SRC, splice=splice,
               cut=dict(intro_s=INTRO_S, end_s=END_S, loop_s=(END_S - INTRO_S), loop_bars=(END_S - INTRO_S) * BPM / 60 / 4,
                        wrap_crossfade_ms=WRAP_XF_S * 1000),
               stream=dict(file=path, rate=RATE, samples=n, seconds=round(n / RATE, 4), loop_sample=loop, loop_s=round(loop / RATE, 6),
                           loop_block=h['loop_block'], blocks=len(h['blocks']), bytes=rep['bytes'], snr_db=rep['snr_db'],
                           block_sizes=sorted({b['size'] // 2 for b in h['blocks']})),
               level=dict(source_lufs=round(l0, 2), target_lufs=round(target, 2), gain_db=round(20 * np.log10(g), 2),
                          result_lufs=round(loudness(dec, RATE), 2), result_true_peak_db=round(true_peak_db(dec, RATE), 2),
                          peak_cap_db=peak_cap),
               starters=lv,
               # the seam: the played stream at the wrap (sample n of `played`) against the same loop start reached
               # through the intro on the first pass (sample `loop`), and against an ordinary downbeat mid-loop
               seam=dict(wrap=seam_metric(played, n, RATE), first_pass=seam_metric(dec, loop, RATE),
                         mid_downbeat=seam_metric(dec, loop + int(19.2 * RATE), RATE),
                         decode_equal_after_wrap=bool(np.array_equal(played[n:n + 1000], dec[loop:loop + 1000]))),
               seam_rms={k: v for k, v in seam_rms(dec, loop).items() if k not in ('chart',)})
    json.dump(res, open(os.path.join(OUT, 'report.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'starters'}, indent=1))
    for r in lv: print(r)
    return res


def seam(run):
    """The in-game capture (dsp.wav from a menu test): where the stream starts, that it wraps to the loop start, and how
    the wrap measures against the arrangement's own downbeats in the same capture. Dolphin labels its DSP dump 32028 Hz,
    but the 32 kHz streams play at 32000 samples per second of it (resampling by the label drifts 26.4 samples a second,
    measured), so the capture is read as 32000."""
    import soundfile as sf
    from scipy.signal import fftconvolve
    cap, sr = sf.read(os.path.join(run, 'dsp.wav'), dtype='float64')
    dec, _ = sf.read(os.path.join(OUT, 'gr_forestmaze_decoded.wav'), dtype='float64')
    rep = json.load(open(os.path.join(OUT, 'report.json')))
    loop = rep['stream']['loop_sample']; n = rep['stream']['samples']
    c, d = cap.mean(1), dec.mean(1)
    def ncc(seg, ref):
        r = fftconvolve(seg, ref[::-1], 'valid')
        cs = np.concatenate([[0], np.cumsum(seg ** 2)]); e = np.sqrt(cs[len(ref):] - cs[:-len(ref)])
        z = r / (e * np.linalg.norm(ref) + 1e-12); k = int(np.argmax(z)); return k, float(z[k])
    k, z = ncc(c[:60 * RATE], d[5 * RATE:13 * RATE]); start = k - 5 * RATE
    out = dict(capture_label_rate=sr, read_as=RATE, stream_start_s=round(start / RATE, 4), start_corr=round(z, 3), checks=[])
    for pos in (30, 60, 85):
        kk, zz = ncc(c[start + pos * RATE - RATE:start + pos * RATE + 9 * RATE], d[pos * RATE:pos * RATE + 8 * RATE])
        out['checks'].append(dict(at_s=pos, offset_samples=kk - RATE, corr=round(zz, 3)))
    wrap = start + n
    if wrap + 12 * RATE < len(c):
        kk, zz = ncc(c[wrap - RATE:wrap + 9 * RATE], d[loop:loop + 8 * RATE])
        seam_at = wrap + (kk - RATE)
        out.update(wrap_s=round(wrap / RATE, 4), after_wrap_offset_samples=kk - RATE, after_wrap_corr=round(zz, 3))
        # the wrap against the capture's own downbeats (every bar of the first pass's loop body)
        bars = [start + LEAD + int(round((INTRO_S + 1.2 * b) * RATE)) for b in range(1, 60)]
        vals = [seam_metric(cap, i, RATE)['hf_burst_db'] for i in bars]
        w = seam_metric(cap, seam_at, RATE)
        out.update(capture_seam=w, capture_downbeats_hf_db=dict(median=round(float(np.median(vals)), 2),
                   p90=round(float(np.percentile(vals, 90)), 2), max=round(float(max(vals)), 2)),
                   seam_rank=round(float(np.mean(np.array(vals) > w['hf_burst_db'])), 3))
        sf.write(os.path.join(run, 'seam_capture.wav'), cap[seam_at - 6 * RATE:seam_at + 4 * RATE], RATE, subtype='PCM_16')
    json.dump(out, open(os.path.join(run, 'seam.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))
    return out


def review(old_path):
    """The seam before and after, for Michael's listen: the two seam clips, the RMS through the wrap for both, and the
    numbers, on one local page (OUT/review_seam.html; not opened)."""
    import html
    new_path = os.path.join(OUT, 'gr_forestmaze.hps')
    rows = {}
    for tag, path in (('before', old_path), ('after', new_path)):
        h = hps.read(path)
        dec = h['pcm'].astype(np.float64) / 32768.0
        loop = LEAD + int(round(INTRO_S * RATE))
        listen(dec, loop, os.path.join(OUT, f'seam_{tag}.wav'))
        spectrogram(dec, loop, os.path.join(OUT, f'seam_{tag}.png'), f'{tag}: {os.path.basename(path)}')
        rows[tag] = dict(path=path, rms=seam_rms(dec, loop), lufs=round(loudness(dec, RATE), 2),
                         true_peak_db=round(true_peak_db(dec, RATE), 2))
    rep = json.load(open(os.path.join(OUT, 'report.json')))
    le = json.load(open(os.path.join(os.path.dirname(LOOPEND), 'report.json')))
    # each part through the last bar: RMS dBFS per 8th, draft 2's stems against the loop end's (at 48 kHz, mix level)
    import soundfile as sf
    d2 = os.path.join(os.path.dirname(SRC), 'stems_draft2', 'draft2_stem_{}.wav')
    le_dir = le['stems']['dir']; w0 = le['stems']['window_s'][0]
    parts = {}
    for name in ('guitars', 'bass', 'leads', 'drums', 'orch', 'choir'):
        a, sr = sf.read(d2.format(name), dtype='float64'); b, _ = sf.read(os.path.join(le_dir, f'loopend_stem_{name}.wav'), dtype='float64')
        lv = lambda x, t0, t1, off=0.0: round(float(10 * np.log10(np.mean(x[int((t0 - off) * sr):int((t1 - off) * sr)] ** 2) + 1e-12)), 1)
        parts[name] = dict(draft2=[lv(a, 90.9, 91.05), lv(a, 91.05, 91.2)], loopend=[lv(b, 90.9, 91.05, w0), lv(b, 91.05, 91.2, w0)])
    rows['parts_last_bar_db'] = parts
    json.dump(rows, open(os.path.join(OUT, 'seam_rms.json'), 'w'), indent=1)
    page = review_page(rows, rep, le)
    open(os.path.join(OUT, 'review_seam.html'), 'w').write(page)
    for tag in ('before', 'after'):
        r = rows[tag]; print(tag, {k: v for k, v in r['rms'].items() if k != 'chart'}, r['lufs'], r['true_peak_db'])
    print(parts)
    print(os.path.join(OUT, 'review_seam.html'))


def spectrogram(dec, loop, path, title, before_s=0.6, after_s=0.6):
    """The seam's spectrogram as the game plays it: `before_s` of the loop's end, then `after_s` past the loop point."""
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scipy.signal import stft
    n = len(dec); p = played_wrap(dec, loop).mean(1)
    seg = p[n - int(before_s * RATE):n + int(after_s * RATE)]
    f, t, Z = stft(seg, RATE, nperseg=512, noverlap=448)
    S = 20 * np.log10(np.abs(Z) + 1e-9)
    fig, ax = plt.subplots(figsize=(7.6, 2.6), dpi=110)
    ax.pcolormesh(t - before_s, f / 1000, S, vmin=S.max() - 90, vmax=S.max(), cmap='magma', shading='auto')
    ax.axvline(0, color='white', lw=1)
    ticks = np.arange(-before_s, after_s + 1e-9, 0.2)
    ax.set_xticks(ticks, [f'{END_S + v:.1f}' if v < -1e-9 else f'{INTRO_S + v:.1f}' if v > 1e-9 else f'{END_S:.1f} | {INTRO_S:.1f}'
                          for v in ticks])
    ax.set_xlim(-before_s + 0.01, after_s - 0.01)          # the STFT's edge frames are zero-padded
    ax.set_xlabel('song time (s): the loop point at the white line'); ax.set_ylabel('kHz'); ax.set_ylim(0, 16)
    ax.set_title(title, fontsize=10, loc='left')
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def _chart_svg(cid, t, series, band=None, rule=None, ylabel='', yr=None):
    """A line chart through the wrap (window index on x, since song time jumps from 91.2 to 9.6 there), with a hover
    readout. series: [(name, css var, values)]."""
    W, H, l, r, tp, b = 760, 280, 56, 16, 14, 34
    k = len(t); wrap = t.index(INTRO_S)
    allv = [v for _, _, vs in series for v in vs] + ([band[0], band[1]] if band else []) + ([rule[0]] if rule else [])
    lo, hi = yr if yr else (np.floor(min(allv) / 5) * 5, np.ceil(max(allv) / 5) * 5)
    X = lambda i: l + (W - l - r) * i / (k - 1)
    Y = lambda v: tp + (H - tp - b) * (hi - v) / (hi - lo)
    out = [f'<svg viewBox="0 0 {W} {H}" class="chart" id="{cid}" role="img" aria-label="{html.escape(ylabel)}">']
    for v in np.arange(lo, hi + 0.01, 10 if hi - lo > 30 else 5):
        out.append(f'<line x1="{l}" x2="{W - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="grid"/>'
                   f'<text x="{l - 8}" y="{Y(v) + 4:.1f}" class="tick" text-anchor="end">{v:g}</text>')
    if band:
        out.append(f'<rect x="{l}" width="{W - l - r}" y="{Y(band[1]):.1f}" height="{Y(band[0]) - Y(band[1]):.1f}" class="band"/>'
                   f'<text x="{W - r - 6}" y="{Y(band[1]) - 5:.1f}" class="note" text-anchor="end">{html.escape(band[2])}</text>')
    if rule:
        out.append(f'<line x1="{l}" x2="{W - r}" y1="{Y(rule[0]):.1f}" y2="{Y(rule[0]):.1f}" class="rule"/>'
                   f'<text x="{W - r - 6}" y="{Y(rule[0]) + 14:.1f}" class="note" text-anchor="end">{html.escape(rule[1])}</text>')
    xw = X(wrap) - (X(1) - X(0)) / 2
    out.append(f'<line x1="{xw:.1f}" x2="{xw:.1f}" y1="{tp}" y2="{H - b}" class="wrap"/>'
               f'<text x="{xw + 6:.1f}" y="{tp + 10}" class="note">loop point: 91.2 s → 9.6 s</text>')
    for i in range(0, k, 10):
        out.append(f'<text x="{X(i):.1f}" y="{H - b + 18}" class="tick" text-anchor="middle">{t[i]:.1f}</text>')
    out.append(f'<text x="{(l + W - r) / 2}" y="{H - 2}" class="tick" text-anchor="middle">song time (s), 10 ms windows</text>')
    for name, var, vs in series:
        pts = ' '.join(f'{X(i):.1f},{Y(max(lo, v)):.1f}' for i, v in enumerate(vs))
        out.append(f'<polyline points="{pts}" fill="none" stroke="var({var})" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
    out.append(f'<line class="xhair" y1="{tp}" y2="{H - b}" x1="-10" x2="-10"/>')
    out.append(f'<rect x="{l}" y="{tp}" width="{W - l - r}" height="{H - tp - b}" fill="transparent" class="hit"/></svg>')
    data = json.dumps(dict(t=t, s=[dict(name=nm, var=v, v=vs) for nm, v, vs in series], l=l, r=r, W=W, k=k))
    return '\n'.join(out) + f'<div class="tip" id="{cid}-tip" hidden></div><script>hover("{cid}", {data})</script>'


def review_page(rows, rep, le):
    import html
    b, a = rows['before'], rows['after']
    fin = a['rms']['final']
    ser = lambda key: [('before: draft 2 cut as is', '--s1', b['rms']['chart'][key]), ('after: the loop end', '--s2', a['rms']['chart'][key])]
    t = a['rms']['chart']['t']
    level = _chart_svg('lvl', t, ser('level_db'), band=(fin['level_db']['p5'], fin['level_db']['p95'], "FINAL's level, 5th-95th percentile"),
                       ylabel='RMS level through the wrap (dBFS)', yr=(-60, -5))
    dip = _chart_svg('dip', t, ser('dip_db'), rule=(fin['dip_db']['min'], f"FINAL's deepest between-note dip: {fin['dip_db']['min']} dB"),
                     ylabel='dip against the median of the 0.3 s either side (dB)', yr=(-40, 10))
    rel = lambda p: os.path.relpath(p, OUT)
    def card(tag, r, title, what):
        s = r['rms']['seam']
        ok = 'passes' if r['rms']['passes'] else 'fails'
        return (f'<figure class="card"><h3>{title}</h3><audio src="seam_{tag}.wav" controls preload="metadata"></audio>'
                f'<figcaption><p>{what}</p><table>'
                f'<tr><td>deepest dip in the seam</td><td><b>{s["dip_min_db"]} dB</b> at {s["dip_min_at_s"]} s ({ok}: FINAL\'s deepest is {fin["dip_db"]["min"]} dB)</td></tr>'
                f'<tr><td>the loop\'s last 0.3 s / the first 0.2 s after the wrap</td><td>deepest dip {s["loop_end_dip_min_db"]} / {s["after_wrap_dip_min_db"]} dB</td></tr>'
                f'<tr><td>quietest 10 ms window</td><td>{s["level_min_db"]} dBFS at {s["level_min_at_s"]} s</td></tr>'
                f'<tr><td>seam median</td><td>{s["surrounding_median_db"]} dBFS (FINAL {fin["level_db"]["median"]})</td></tr>'
                f'<tr><td>stream</td><td>{r["lufs"]} LUFS, true peak {r["true_peak_db"]} dBTP</td></tr></table>'
                f'<a href="seam_{tag}.wav">seam_{tag}.wav</a> · <a href="{html.escape(rel(r["path"]))}">{html.escape(os.path.basename(r["path"]))}</a>'
                f'</figcaption></figure>')
    p1 = le['pass1_vs_draft2']; p2 = le['pass2_vs_draft2']; p21 = le['pass2_vs_pass1']; lb = le['last_bar']
    names = {'act:vc': 'the cellos', 'act:vla': 'the violas', 'act:choir': 'the choir', 'act:vln': 'the violins', 'act:cb': 'the basses',
             'act:hn': 'the horns', 'act:tbn': 'the trombones', 'act:timp': 'the timpani', 'act:glock': 'the glockenspiel'}
    moved = ', '.join(f'{names[k]} {abs(v):.1f} dB' for k, v in le['frozen_factors_moved_db'].items() if k in names and abs(v) >= 1)
    sp = rep['splice']
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Forest Maze loop seam</title><style>
:root{{--bg:#fcfcfb;--card:#ffffff;--ink:#0b0b0b;--mute:#52514e;--line:#e4e3df;--grid:#ecebe7;--band:#efeeea;--s1:#2a78d6;--s2:#eb6834;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#1a1a19;--card:#232322;--ink:#ffffff;--mute:#c3c2b7;--line:#3a3a37;--grid:#2e2e2c;--band:#2c2c2a;--s1:#3987e5;--s2:#d95926;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#1a1a19;--card:#232322;--ink:#ffffff;--mute:#c3c2b7;--line:#3a3a37;--grid:#2e2e2c;--band:#2c2c2a;--s1:#3987e5;--s2:#d95926;color-scheme:dark}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,system-ui,sans-serif}}
main{{max-width:1040px;margin:0 auto;padding:24px 16px 64px}}h1{{font-size:24px;margin:0 0 4px}}h2{{font-size:18px;margin:36px 0 10px}}
h3{{font-size:16px;margin:0 0 10px}}p{{margin:6px 0}}.mute{{color:var(--mute)}}a{{color:inherit}}
.pair{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}
.card{{margin:0;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px}}
audio{{width:100%;margin:4px 0 8px}}table{{border-collapse:collapse;width:100%;font-size:14px;margin:6px 0}}
td,th{{border-top:1px solid var(--line);padding:5px 8px 5px 0;text-align:left;vertical-align:top}}td:first-child{{color:var(--mute);width:42%}}
.chart{{width:100%;height:auto;display:block}}.grid{{stroke:var(--grid);stroke-width:1}}.band{{fill:var(--band)}}
.rule{{stroke:var(--mute);stroke-width:1}}.wrap{{stroke:var(--ink);stroke-width:1}}.tick,.note{{fill:var(--mute);font-size:12px}}
.xhair{{stroke:var(--mute);stroke-width:1}}.legend{{display:flex;gap:18px;font-size:14px;margin:4px 0 8px;flex-wrap:wrap}}
.key{{display:inline-block;width:18px;height:2px;vertical-align:middle;margin-right:6px}}
.tip{{position:absolute;background:var(--card);border:1px solid var(--line);border-radius:6px;padding:6px 9px;font-size:13px;pointer-events:none;white-space:nowrap}}
.wrapbox{{position:relative}}ul{{margin:6px 0;padding-left:20px}}code{{font-size:13px}}
</style><script>
function hover(id, d){{const svg=document.getElementById(id),tip=document.getElementById(id+'-tip'),x=svg.querySelector('.xhair'),hit=svg.querySelector('.hit');
hit.addEventListener('mousemove',e=>{{const p=svg.createSVGPoint();p.x=e.clientX;p.y=e.clientY;const q=p.matrixTransform(svg.getScreenCTM().inverse());
const i=Math.max(0,Math.min(d.k-1,Math.round((q.x-d.l)/((d.W-d.l-d.r)/(d.k-1)))));const X=d.l+(d.W-d.l-d.r)*i/(d.k-1);x.setAttribute('x1',X);x.setAttribute('x2',X);
tip.hidden=false;tip.innerHTML='<b>'+d.t[i].toFixed(2)+' s</b>'+(i>=d.t.indexOf(9.6)?' (after the wrap)':'')+d.s.map(s=>'<br><span class="key" style="background:var('+s.var+')"></span>'+s.name+': '+s.v[i].toFixed(1)+' dB').join('');
const box=svg.parentElement.getBoundingClientRect();tip.style.left=Math.min(e.clientX-box.left+14,box.width-tip.offsetWidth-4)+'px';tip.style.top=(e.clientY-box.top+14)+'px';}});
hit.addEventListener('mouseleave',()=>{{tip.hidden=true;x.setAttribute('x1',-10);x.setAttribute('x2',-10);}});}}
</script></head><body><main>
<h1>Forest Maze: the loop seam</h1>
<p class="mute">Stage stream <code>gr_forestmaze.hps</code>: the intro plays once (0 to 9.6 s), then the loop runs 9.6 to 91.2 s and jumps back to THEME A's downbeat. In a match the jump comes about 1:31 in.</p>
<p><b>What changed.</b> Draft 2 stops everything for FINAL's last 8th (91.05 to 91.2 s) so the trailer's final hit lands on silence. The stage loop kept that stop, so every pass had a 150 ms hole before the theme came back. The stage stream now has its own version of FINAL's last bar, re-rendered from the arrangement with no stop: the tom fill plays its last 16th through beat 4, the chugs, bass, held twin leads, violins and choir play the last 8th as written, and the wrap lands them on THEME A's crash (the last 4 ms cross into the audio before THEME A, so the jump has no step). Draft 2's master and stems are untouched; the trailer keeps its stop and hit.</p>

<h2>Listen: the seam</h2>
<p class="mute">Each clip is the loop's last 8 s, then the first 8 s after the loop point. The wrap is at 0:08.</p>
<div class="pair">{card('before', b, 'Before: draft 2 cut as is', 'The stop kept: 150 ms at −45 to −55 dBFS, then THEME A.')}
{card('after', a, 'After: the stage loop end', "FINAL's last bar without the stop, flowing into THEME A's downbeat.")}</div>

<h2>Spectrogram through the wrap</h2>
<p class="mute">0.6 s either side of the loop point (white line), both channels summed, 90 dB range.</p>
<div class="pair"><figure class="card"><a href="seam_before.png"><img src="seam_before.png" alt="spectrogram of the old seam" style="width:100%"></a><figcaption class="mute">before: the 150 ms gap before the line</figcaption></figure>
<figure class="card"><a href="seam_after.png"><img src="seam_after.png" alt="spectrogram of the new seam" style="width:100%"></a><figcaption class="mute">after: the fill's last 16th runs to the line</figcaption></figure></div>

<h2>RMS through the wrap</h2>
<div class="legend"><span><span class="key" style="background:var(--s1)"></span>before: draft 2 cut as is</span><span><span class="key" style="background:var(--s2)"></span>after: the loop end</span></div>
<p class="mute">Level in 10 ms windows (both channels' power), from beat 3 of FINAL's last bar through the loop point into THEME A.</p>
<div class="wrapbox">{level}</div>
<p class="mute" style="margin-top:18px">Each window's dip: its level against the median of the windows 0.3 s either side. The line is the deepest dip anywhere else in FINAL (81.9 to 90.6 s), a normal gap between notes.</p>
<div class="wrapbox">{dip}</div>

<h2>Each part through the last bar</h2>
<p class="mute">RMS (dBFS, stems at mix level before the stream's −2.8 dB) in beat 4's first 8th (90.9 to 91.05 s) and in the last 8th (91.05 to 91.2 s).</p>
<table><tr><th>part</th><th>draft 2: 8th before</th><th>draft 2: last 8th</th><th>loop end: 8th before</th><th>loop end: last 8th</th></tr>
{''.join(f'<tr><td>{k}</td><td>{v["draft2"][0]}</td><td>{v["draft2"][1]}</td><td>{v["loopend"][0]}</td><td><b>{v["loopend"][1]}</b></td></tr>' for k, v in rows['parts_last_bar_db'].items())}</table>

<h2>Listen: the whole stream, a loop and a half</h2>
<p class="mute">The intro, the whole loop, then half the loop again: the first wrap is at 1:31.2 in this file.</p>
<div class="card"><audio src="loop_and_a_half.wav" controls preload="metadata"></audio><a href="loop_and_a_half.wav">loop_and_a_half.wav</a></div>

<h2>How the last bar was made, and checked</h2>
<ul>
<li><b>Re-rendered, not spliced.</b> <code>projects/geno/stage/music_loopend.py</code> runs the arrangement's own renderer (<code>music/src/render2.py</code>: Emilyguitar and Growlybass through the NAM amps, the Aasimonster kit, VSCO 2 strings, the GeneralUser choir) twice. The renderer scales almost every track by the whole song (the guitar DI peak sets the amp drive; each band stem, drum bus, orchestral layer, and the master EQ and gain), so pass 1 renders draft 2 and records all of them, and pass 2 renders without the stop and replays them. Left free, the whole song would have shifted: {moved} (the final hit's chords count toward those layers' levels), the master gain {abs(le['frozen_factors_moved_db']['master:gain']):.2f} dB.</li>
<li><b>Pass 1 reproduces draft 2 through FINAL:</b> within {p1['final_worst_rel_db']} dB of it in every second of 82 to 90 s. It isn't bit-exact elsewhere: Surge XT starts its oscillators at a random phase on every render, so the sections with synths (the intro build, TRANSITION, GLADE) differ. So the stream keeps draft 2 itself up to FINAL's last bar. (sfizz, which plays the guitars, bass and orchestra, renders notes short when the machine is busy, so each of its renders repeated until two runs agreed: {le['sfizz']['calls']} parts, {le['sfizz']['renders']} renders.)</li>
<li><b>Pass 2 leaves pass 1 only at the stop:</b> the difference first reaches −40 dBFS at {p21['first_over_40db_s']} s, where the stop's gate began (91.0575 s); before 91 s the two differ by at most {p21['max_abs_diff_before_91s_db']} dBFS, only through the master EQ (its 43 ms reach, and round-off). Against draft 2, FINAL is within {p2['final_rel_db']} dB. The stream switches to it at {sp['at_s']} s (FINAL's last downbeat) with a 10 ms crossfade, where the two differ by at most {20 * np.log10(sp['max_abs_diff_near']):.1f} dBFS.</li>
<li><b>The wrap itself:</b> the loop's last {rep['cut']['wrap_crossfade_ms']:g} ms cross into the {rep['cut']['wrap_crossfade_ms']:g} ms before the loop start, so the waveform runs on across the jump as it does on the first pass. Without it, the jump was a single-sample step of 0.27 full scale; with it, the step is {rep['seam']['wrap']['step']:.3f} ({rep['seam']['wrap']['step_vs_median']}× the median step nearby; the first pass's intro-to-theme join is {rep['seam']['first_pass']['step_vs_median']}×), and the high-frequency burst after the wrap is {rep['seam']['wrap']['hf_burst_db']} dB (a mid-loop downbeat {rep['seam']['mid_downbeat']['hf_burst_db']}; before the fix +1.74).</li>
<li><b>The last bar's level</b> (RMS dBFS, draft 2 → loop end): beats 1-3 {lb['draft2']['beats_1_3']} → {lb['loopend']['beats_1_3']}; beat 4's first 8th {lb['draft2']['beat_4_first_8th']} → {lb['loopend']['beat_4_first_8th']}; the last 8th {lb['draft2']['last_8th']} → {lb['loopend']['last_8th']}.</li>
<li><b>The stream:</b> the same cut (intro 9.6 s, loop 9.6 to 91.2 s), the same level target ({rep['level']['target_lufs']} LUFS, now {rep['level']['result_lufs']}) and true-peak cap ({rep['level']['peak_cap_db']} dBTP, now {rep['level']['result_true_peak_db']}).</li>
</ul>

<h2>Files</h2>
<ul class="mute">
<li>stream: <a href="gr_forestmaze.hps">gr_forestmaze.hps</a> (decoded: <a href="gr_forestmaze_decoded.wav">gr_forestmaze_decoded.wav</a>); the old one: <a href="{html.escape(rel(b['path']))}">{html.escape(rel(b['path']))}</a></li>
<li>reports: <a href="report.json">report.json</a> (the stream), <a href="seam_rms.json">seam_rms.json</a> (both seams, every window), <a href="{html.escape(rel(os.path.join(os.path.dirname(LOOPEND), 'report.json')))}">loopend/report.json</a> (the re-render)</li>
<li>the loop end: <a href="{html.escape(rel(LOOPEND))}">{html.escape(os.path.basename(LOOPEND))}</a> and its stems (84 to 97 s) in <a href="{html.escape(rel(os.path.join(os.path.dirname(LOOPEND), 'stems')))}">loopend/stems</a>; draft 2: <a href="{html.escape(rel(SRC))}">{html.escape(os.path.basename(SRC))}</a></li>
</ul>
</main></body></html>'''


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'levels':
        for r in levels(): print(r)
    elif cmd == 'build':
        build()
    elif cmd == 'seam':
        seam(sys.argv[2])
    elif cmd == 'review':
        review(sys.argv[2])
