"""Render an arrangement (list of section specs) to stems and a mix.
    python render.py test|draft OUTDIR"""
import sys, os, json, time, numpy as np, soundfile as sf
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
import arrange as A, instruments as I, mix as M, drumpat as D

SR = 48000


def sec_len(sec):
    return sec.get('ob', sec['src'][1] - sec['src'][0] + 1) * A.OB


def build_events(secs, tail=5.0):
    t0 = 0.0
    lead1, lead2, rL, rR, bass, drums, marks = [], [], [], [], [], [], []
    pads, risers, booms = [], [], []
    for i, sec in enumerate(secs):
        L = sec_len(sec)
        marks.append((round(t0, 3), sec['name']))
        if sec.get('src'):
            l1, l2 = A.lead_part(sec, t0); lead1 += l1; lead2 += l2
            ev = A.rhythm_part(sec, t0); rL += ev; rR += ev
            bass += A.bass_part(sec, t0)
        drums += D.pattern(sec.get('drums', 'skank8'), t0, int(round(L / A.OB)), fill=sec.get('fill', False),
                           crash=sec.get('crash', True), seed=i)
        drums += D.hits([h * A.STEP for h in sec.get('drumhits', [])], t0, china=True)
        if sec.get('pads'):
            for (t, d, rr, ivs, sym) in A.src_chords(*sec['src']):
                root = 54 + ((rr + sec.get('key', 0) - 54) % 12)          # F#3..F4
                pads.append((t0 + t * A.STEP, d * A.STEP, [root + i for i in ivs if i != 13] + [root + 12]))
        if sec.get('riser'): risers.append(t0)
        if sec.get('boom'): booms.append(t0)
        lead1 += [(t0 + t, d, p, v, f) for (t, d, p, v, f) in sec.get('extra_lead', [])]
        lead2 += [(t0 + t, d, p, v, f) for (t, d, p, v, f) in sec.get('extra_lead2', [])]
        drums += [(t0 + t, p, v) for (t, p, v) in sec.get('extra_drums', [])]
        t0 += L
    for e in sec.get('end', []):
        pass
    return dict(lead1=lead1, lead2=lead2, rL=rL, rR=rR, bass=bass, drums=drums, marks=marks, total=t0 + tail, end=t0,
                pads=pads, risers=risers, booms=booms)


def render(secs, outdir, final_hit=None, kit=None, lead_src='add', rhythm_src='ks'):
    import sfguitar as G
    os.makedirs(outdir, exist_ok=True)
    E = build_events(secs)
    total = E['total']
    if final_hit is not None:  # (chord pcs as rhythm notes, bass midi, lead midi)
        notes, bm, lm = final_hit
        t = E['end']
        E['rL'].append(dict(t=t, dur=3.8, notes=notes, vel=1.0, mute=0.0)); E['rR'].append(dict(t=t, dur=3.8, notes=notes, vel=1.0, mute=0.0))
        E['bass'].append((t, 3.8, bm, 1.0, 0.0))
        if lm: E['lead1'].append((t, 3.0, lm, 1.0, {'vib': 0.6}))
        # a stop before the hit: the band drops out for the last 8th so the hit lands on silence
        stop0 = t - 0.135
        E['drums'] = [e for e in E['drums'] if not (stop0 - 0.01 <= e[0] < t - 0.005)]
        E['stop'] = (stop0, t)
        E['drums'] += D.hits([0.0], t, china=True)
        E['booms'].append(t)
        E['pads'] += [(t, 2.4, [p + 12 for p in notes] + [notes[0] + 24])] if E['pads'] else []
    t_ = time.time()
    stems = {}
    if rhythm_src == 'sf2':   # different guitar samples, detune and amp per side (a real double-track, not a copy)
        stems['rL'] = M.rhythm_chain(G.rhythm_sf(E['rL'], total, seed=11, open_prog=27, mute_prog=28))
        stems['rR'] = M.rhythm_chain(G.rhythm_sf(E['rR'], total, seed=23, open_prog=26, mute_prog=28, detune_cents=6), amp_name=M.RHYTHM_AMP_R)
    elif rhythm_src == 'sf':
        stems['rL'] = M.rhythm_chain(G.rhythm_sf(E['rL'], total, seed=11))
        stems['rR'] = M.rhythm_chain(G.rhythm_sf(E['rR'], total, seed=23))
    else:
        stems['rL'] = M.rhythm_chain(I.guitar_di(E['rL'], total, seed=11))
        stems['rR'] = M.rhythm_chain(I.guitar_di(E['rR'], total, seed=23, tuning_cents=4))
    stems['bass'] = M.bass_chain(G.bass_sf(E['bass'], total, seed=5) if rhythm_src == 'sf2' else I.bass_di(E['bass'], total, seed=5))
    LD = (lambda ns, tot, seed, **kw: G.lead_sf(ns, tot, seed=seed, **kw)) if lead_src == 'sf' else (lambda ns, tot, seed, **kw: I.lead_di(ns, tot, seed=seed, **kw))
    stems['lead1'] = M.lead_chain(LD(E['lead1'], total, 3)) if E['lead1'] else np.zeros(int(total * SR), np.float32)
    stems['lead2'] = M.lead_chain(LD(E['lead2'], total, 4, vib_rate=5.2)) if E['lead2'] else np.zeros(int(total * SR), np.float32)
    stems['lead1b'] = M.lead_chain(LD(E['lead1'], total, 7, vib_rate=5.9)) if (E['lead1'] and lead_src == 'sf') else np.zeros(int(total * SR), np.float32)
    print('pitched stems', round(time.time() - t_, 1), 's', flush=True)
    n = int(total * SR)
    for k in stems: stems[k] = stems[k][:n] if len(stems[k]) >= n else np.pad(stems[k], (0, n - len(stems[k])))
    if E.get('stop'):
        a, b = int(E['stop'][0] * SR), int(E['stop'][1] * SR) - 48
        gate = np.ones(n, np.float32); r_ = 240
        gate[a:b] = 0; gate[a - r_:a] = np.linspace(1, 0, r_)
        for k in stems: stems[k] = stems[k] * gate
    if kit is not None:
        dr = kit.render(E['drums'], total)          # (2, n)
        # reverse-cymbal risers ending on the section downbeats
        cr = kit.render([(0.0, 'crash1', 1.0)], 2.2)[:, ::-1]
        for t in E['risers']:
            i1 = int(t * SR); i0 = max(0, i1 - cr.shape[1])
            dr[:, i0:i1] += 0.8 * cr[:, cr.shape[1] - (i1 - i0):]
    else:
        dr = np.zeros((2, n), np.float32)
    fx = np.zeros((2, n), np.float32)
    for t in E['booms']:                               # sub boom: 58 -> 30 Hz sweep, 1.4 s decay
        L = int(1.6 * SR); tt = np.arange(L) / SR
        f = 30 + 28 * np.exp(-tt / 0.25); ph = 2 * np.pi * np.cumsum(f) / SR
        b = np.sin(ph) * np.exp(-tt / 0.45) * np.minimum(1, tt / 0.004)
        i0 = int(t * SR); e = min(n, i0 + L); fx[:, i0:e] += 0.5 * b[None, :e - i0]
    padst = np.zeros((2, n), np.float32)
    if E['pads']:
        import pretty_midi as pm, subprocess, tempfile
        mm = pm.PrettyMIDI(initial_tempo=200)
        for prog, vel in ((52, 70), (48, 64)):
            inst = pm.Instrument(prog)
            for (t, d, ps) in E['pads']:
                for p in ps: inst.notes.append(pm.Note(vel, int(p), t, t + d))
            mm.instruments.append(inst)
        with tempfile.TemporaryDirectory() as tdir:
            mm.write(tdir + '/p.mid')
            subprocess.run(['fluidsynth', '-ni', '-g', '0.8', '-r', str(SR), '-F', tdir + '/p.wav', G.SF2, tdir + '/p.mid'], check=True, capture_output=True)
            import soundfile as _sf
            pw, _ = _sf.read(tdir + '/p.wav', dtype='float32')
        pw = pw.T[:, :n]; padst[:, :pw.shape[1]] = pw
        padst = M.space(padst.mean(0), delay_s=0.3, fb=0.2, mix=0.1, room=0.8, wet=0.35)[:, :n]
    # ---- mix
    g = lambda x, dbv: x * 10 ** (dbv / 20) / (np.sqrt(np.mean(x ** 2)) + 1e-9) * 0.1
    mixst = np.zeros((2, n), np.float32)
    mixst += M.pan(g(stems['rL'], -2.0), -0.95) + M.pan(g(stems['rR'], -2.0), 0.95)
    mixst += M.pan(g(stems['bass'], 0.0), 0.0)
    if stems['lead1b'].any():   # the lead double-tracked: two takes a little left and right
        l1 = M.space(g(stems['lead1'], -3.5)); l1b = M.space(g(stems['lead1b'], -3.5))
        mixst += np.vstack([l1[0] * 1.0, l1[1] * 0.75]) + np.vstack([l1b[0] * 0.75, l1b[1] * 1.0])
    else:
        l1 = M.space(g(stems['lead1'], -3.0)); mixst += l1 * np.array([[1.0], [1.0]])
    if E['lead2']:
        l2 = M.space(g(stems['lead2'], -6.0)); mixst += np.vstack([l2[0] * 0.55, l2[1] * 1.0])
    if dr.any():
        from pedalboard import Pedalboard as _PB, HighShelfFilter as _HS, LowpassFilter as _LP
        dr = _PB([_HS(8000, -4.0), _LP(14000)])(dr.astype(np.float32), SR)
        mixst += dr[:, :n] * (10 ** (2.0 / 20)) / (np.sqrt(np.mean(dr ** 2)) + 1e-9) * 0.1
    if fx.any():
        mixst += fx * 0.9
    if padst.any():
        mixst += padst * (10 ** (-6.0 / 20)) / (np.sqrt(np.mean(padst[:, padst.any(0)] ** 2)) + 1e-9) * 0.1 * 0.6
    y, lufs = M.master(mixst)
    fade = int(0.8 * SR); y[:, -fade:] *= np.linspace(1, 0, fade)[None] ** 2     # clean tail, no click at the end
    sf.write(os.path.join(outdir, 'mix.wav'), y.T, SR, subtype='PCM_24')
    for k, v in stems.items():
        sf.write(os.path.join(outdir, f'stem_{k}.wav'), (v / (np.abs(v).max() + 1e-9) * 0.8).astype(np.float32), SR, subtype='PCM_24')
    if dr.any():
        sf.write(os.path.join(outdir, 'stem_drums.wav'), (dr / (np.abs(dr).max() + 1e-9) * 0.8).T, SR, subtype='PCM_24')
    json.dump({'marks': E['marks'], 'end': E['end'], 'lufs': lufs, 'bpm': A.BPM}, open(os.path.join(outdir, 'meta.json'), 'w'), indent=1)
    print('mix LUFS', round(lufs, 1), '->', outdir)
    return E
