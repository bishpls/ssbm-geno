"""The Forest Maze stage music: metal draft 2 (Michael, 2026-09-29) cut into a looping stage stream, gr_forestmaze.hps.
    .venv/bin/python projects/geno/stage/music.py build     # $MELEE_WORK/stage/music/: the stream, a report, seam audio
    .venv/bin/python projects/geno/stage/music.py levels    # the six starters' streams: loudness, peak, loop
    .venv/bin/python projects/geno/stage/music.py seam RUN  # the in-game capture's seam (dsp.wav from a menu test)
The cut: the intro (0-9.6 s) plays once; the loop runs from Theme A's downbeat (9.6 s, bar 9) to the end of the final
chorus (91.2 s, bar 77), leaving out the final hit. The final chorus's last 8th note is the arrangement's own dropout
(-42 dBFS), so the loop breathes into the theme's downbeat. The loop is 81.6 s, 34 bars of 200 BPM (NOTES.md's grid).
Stage streams are 32 kHz stereo DSP-ADPCM (measured: every vanilla stage stream). The loop lands on the downbeat
exactly: 16 samples of silence lead the stream, so the loop start is 307216 = 5486 x 56 samples, and hps.write's
exact_loop cuts the block before it short (as HAL's own streams do). The level is the six starters' streams' median
integrated loudness, measured here, with the peak kept under theirs.
Game audio stays out of git: the stream, the decodes and the captures live under $MELEE_WORK.
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'machinima', 'melee', 'audio'))
import hps  # noqa: E402

WORK = os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work'))
DISC = os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc'))
SRC = os.path.expanduser('~/games/melee/work/music/forest_maze_metal_draft2.wav')
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


def build():
    import soundfile as sf
    from scipy.signal import resample_poly
    os.makedirs(OUT, exist_ok=True)
    src, sr = sf.read(SRC, dtype='float64')
    assert sr == 48000
    x = resample_poly(src, 2, 3, axis=0)                   # 48 -> 32 kHz
    n_end = int(round(END_S * RATE)); n_loop = int(round(INTRO_S * RATE))
    x = x[:n_end]
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
    sf.write(os.path.join(OUT, 'seam_listen.wav'), played[n - int(6 * RATE):n + int(4 * RATE)], RATE, subtype='PCM_16')
    sf.write(os.path.join(OUT, 'gr_forestmaze_decoded.wav'), dec, RATE, subtype='PCM_16')
    res = dict(source=SRC, cut=dict(intro_s=INTRO_S, end_s=END_S, loop_s=(END_S - INTRO_S), loop_bars=(END_S - INTRO_S) * BPM / 60 / 4),
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
                         decode_equal_after_wrap=bool(np.array_equal(played[n:n + 1000], dec[loop:loop + 1000]))))
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


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'levels':
        for r in levels(): print(r)
    elif cmd == 'build':
        build()
    elif cmd == 'seam':
        seam(sys.argv[2])
