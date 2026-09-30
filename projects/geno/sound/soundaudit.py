"""The gun normals' sounds against their moves (Michael: some "linger longer" than the move): for every gun move, each sound
its script plays (id, frame, the sample's length from the bank) against the move's active frames, its bursts' lifetimes
and the animation's end, and, from a lab run's game audio (director/gunfx_lab.py GUNFX_SET=sound), how long it is
actually heard in the game: the sound itself (within 15 dB of its peak) and Melee's reverb after it (to 30 dB down).
    .venv/bin/python projects/geno/sound/soundaudit.py [RUN] [--bank GENO.SSM] [--out OUT.json]
Script sounds are read from rig/moves.py as built (Script.sound calls, with their frames); bursts from moves.fx calls and
efge's generator lives (a root's longest child). The bank defaults to $MELEE_DISC's geno.ssm. In the game audio a move's
sound is heard until the last frame within 30 dB of its loudest (the dump is silent between moves: the lab has no
music): from the sound's script frame (after the audited action's first frame, from the director's MS lines), the run of
frames within 15 dB of its loudest, bridging dips of up to 3 frames (the rattle's), so a jump's or a landing's sound
around it isn't counted. Down air is left out: it's being redesigned as a rocket fist (Michael, 2026-09-29).
"""
import json, math, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'rig'))
sys.path.insert(0, os.path.join(HERE, '..', 'fx'))
sys.path.insert(0, os.path.join(HERE, 'cheer'))

FPS = 60.0
FLOOR_DB = 30.0         # a sample's audible end: its last 10 ms within 30 dB of its peak
HEARD_DB = 15.0         # in the game: the sound itself, within 15 dB of its peak (Melee's reverb then rings ~17 dB down
TAIL_DB = 30.0          # for ~18 frames: reported as the tail, within 30 dB)
# segment -> [(move, motion id)]: the actions whose sounds are audited (the last is the one the window follows)
SEGMENTS = {
    'jab': [('Attack11', 44)], 'jab123': [('Attack11', 44), ('Attack12', 45), ('Attack13', 46)],
    'ftilt': [('AttackS3S', 53)], 'ftilt_hi': [('AttackS3Hi', 51)], 'ftilt_lo': [('AttackS3Lw', 55)],
    'dtilt': [('AttackLw3', 57)], 'fair_fh': [('AttackAirF', 66)], 'bair_fh': [('AttackAirB', 67)],
    'uair_fh': [('AttackAirHi', 68)], 'usmash': [('AttackHi4', 63)],
    'dsmash': [('AttackLw4', 64)], 'ledge_quick': [('CliffAttackQuick', 257)], 'ledge_slow': [('CliffAttackSlow', 256)],
    'getup_u': [('DownAttackU', 187)], 'getup_d': [('DownAttackD', 195)],
    'bthrow': [('ThrowB', 220)],
}
LANDINGS = {42, 43, 70, 71, 72, 73, 74}


def script_events(hits=False):
    """move -> dict(frames, sounds [(frame, id)], fx [(frame, name)], and with hits: hits [frames a hitbox opens])"""
    import fcmd, moves
    log = {}

    def patch(cls):
        orig_sound, orig_raw = cls.sound, cls.raw

        def sound(self, sid, *a, **k):
            self.__dict__.setdefault('_ev', {'sounds': [], 'fx': [], 'hits': []})['sounds'].append((self.frame, sid))
            return orig_sound(self, sid, *a, **k)
        cls.sound = sound
        orig_hit = cls.hitbox

        def hitbox(self, *a, **k):
            self.__dict__.setdefault('_ev', {'sounds': [], 'fx': [], 'hits': []})['hits'].append(self.frame)
            return orig_hit(self, *a, **k)
        cls.hitbox = hitbox
    patch(fcmd.Script)
    orig_fx = moves.fx

    def fx(s, name, *a, **k):
        s.__dict__.setdefault('_ev', {'sounds': [], 'fx': [], 'hits': []})['fx'].append((s.frame, name))
        return orig_fx(s, name, *a, **k)
    moves.fx = fx
    for seg, acts in SEGMENTS.items():
        for mv, _ in acts:
            frames, fn = moves.MOVES[mv]
            s, _ = fn(None)
            ev = getattr(s, '_ev', {'sounds': [], 'fx': [], 'hits': []})
            log[mv] = dict(frames=frames, sounds=ev['sounds'], fx=ev['fx'], hits=sorted(set(ev['hits'])))
    moves.fx = orig_fx
    return log


def fx_lives():
    """root generator name -> the longest life of what it spawns (frames)"""
    import efge
    gens = efge.all_generators()
    ids = {efge.FIRST + i: g for i, g in enumerate(gens)}
    out = {}
    for name, hdr, cmd in gens:
        b = bytes(cmd.b)
        kids = [ids.get((b[i + 1] << 8) | b[i + 2]) for i in range(len(b) - 2) if b[i] == 0xA5]
        kids = [k for k in kids if k]
        out[name] = max((k[1].get('life', 0) for k in kids), default=hdr.get('life', 0))
    return out


def sample_lengths(bank_path, ids):
    """sound id -> (seconds, audible frames: the last 10 ms window within 30 dB of the peak)"""
    import ssmfile as S
    b = S.parse_ssm(open(bank_path, 'rb').read())
    out = {}
    for sid in ids:
        k = sid - 550000
        if not 0 <= k < b['count']:
            continue
        x = S.decode_entry(b, k).astype(np.float64)
        sr = b['entries'][k]['rate']
        h = int(sr * 0.01)
        env = np.array([np.sqrt(np.mean(x[j:j + h] ** 2)) for j in range(0, len(x) - h + 1, h)])
        db = 20 * np.log10(env / env.max() + 1e-12)
        last = (np.nonzero(db > -FLOOR_DB)[0].max() + 1) * 0.01
        out[sid] = (len(x) / sr, last * FPS)
    return out


def run_from(lv, i0, thr, gap=3):
    """the last frame of the run of frames above thr from i0, bridging dips up to `gap` frames (the rattle's)"""
    i, last = i0, None
    while i < len(lv):
        if lv[i] > thr:
            last = i
        elif last is not None and i - last > gap:
            break
        i += 1
    return last


def game_audio(run, first_sound):
    """segment -> dict(start (logic frame of the audited action), end_heard (frames after the start), peak_db)"""
    import fxsync
    import soundfile as sf
    r = fxsync.load(run)
    clk, sr, y = fxsync.click(run)
    mono = y.mean(axis=1)
    ms = [l.split() for l in open(os.path.join(run, 'osreport.log'), errors='replace') if l.startswith('MS ')]
    ms = [(int(l[1]), int(l[2]), int(l[3])) for l in ms]
    out = {}
    for seg, off in r.offsets:
        label = seg['label']
        if label not in SEGMENTS:
            continue
        t0, t1 = seg['start'] - 5, seg['start'] + seg['frames']
        mine = [(f, m) for f, p, m in ms if p == 0 and t0 <= f < t1]
        want = [m for _, m in SEGMENTS[label]]
        starts = [f for f, m in mine if m == want[-1]]
        if not starts:
            out[label] = None; continue
        a0 = starts[0]
        lv = []
        for s in range(a0, t1):
            i0, i1 = r.audio_at(s, clk, sr), r.audio_at(s + 1, clk, sr)
            lv.append(20 * np.log10(np.sqrt(np.mean(mono[i0:i1] ** 2)) + 1e-12))
        lv = np.array(lv)
        f0 = first_sound[label] - 1                       # the sound's script frame, 0-based from the action's first
        pk = lv[f0:f0 + 20].max()                         # its loudest (the jump's or a landing's sound don't count)
        on = next(i for i in range(max(0, f0 - 2), len(lv)) if lv[i] > pk - HEARD_DB)
        out[label] = dict(start=a0, first_heard=on + 1, end_heard=run_from(lv, on, pk - HEARD_DB) + 1,
                          end_tail=run_from(lv, on, pk - TAIL_DB) + 1, peak_db=round(float(pk), 1), window=t1 - a0,
                          levels=[round(float(v), 1) for v in lv])
    return out


def main():
    run = next((a for a in sys.argv[1:] if not a.startswith('--') and os.path.isdir(a)), None)
    disc = os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc'))
    bank = sys.argv[sys.argv.index('--bank') + 1] if '--bank' in sys.argv else os.path.join(disc, 'files/audio/us/geno.ssm')
    ev = script_events()
    lives = fx_lives()
    ids = sorted({sid for e in ev.values() for _, sid in e['sounds']})
    lens = sample_lengths(bank, ids)
    first = {seg: min(f for f, _ in ev[acts[-1][0]]['sounds']) for seg, acts in SEGMENTS.items()}
    heard = game_audio(run, first) if run else {}
    rows = []
    for seg, acts in SEGMENTS.items():
        mv = acts[-1][0]
        e = ev[mv]
        gun = [(f, sid) for f, sid in e['sounds'] if sid in lens and lens[sid][0] > 0.1]
        snd = gun or [(f, sid) for f, sid in e['sounds'] if sid in lens]
        end_sample = max((f + lens[sid][0] * FPS for f, sid in snd), default=None)
        end_aud = max((f + lens[sid][1] for f, sid in snd), default=None)
        burst_end = max((f + lives.get(n, 0) for f, n in e['fx']), default=None)
        row = dict(segment=seg, move=mv, frames=e['frames'], sounds=[(f, sid, round(lens[sid][0] * FPS, 1)) for f, sid in snd],
                   sound_end=None if end_sample is None else round(end_sample, 1),
                   sound_end_audible=None if end_aud is None else round(end_aud, 1), burst_end=burst_end,
                   outlast=None if end_sample is None else round(end_sample - e['frames'], 1),
                   outlast_bursts=None if end_sample is None or burst_end is None else round(end_sample - burst_end, 1))
        h = heard.get(seg)
        if h:
            row.update(heard_start=h['first_heard'], heard_end=h['end_heard'], heard_outlast=h['end_heard'] - e['frames'],
                       tail_end=h['end_tail'], tail_outlast=h['end_tail'] - e['frames'], heard_peak_db=h['peak_db'],
                       levels=h['levels'])
        rows.append(row)
        snds = ', '.join(f'{sid} @{f} ({d} f)' for f, sid, d in row['sounds'])
        print(f"{seg:12s} {mv:16s} anim {e['frames']:3d}  bursts end {burst_end}  sounds {snds}  -> ends {row['sound_end']} "
              f"(outlasts the move by {row['outlast']}, the bursts by {row['outlast_bursts']})"
              + (f"  in game: heard {h['first_heard']}-{h['end_heard']} (by {h['end_heard'] - e['frames']:+d}), reverb to "
                 f"{h['end_tail']} ({h['end_tail'] - e['frames']:+d})" if h else ''))
    if '--out' in sys.argv:
        json.dump(dict(bank=bank, run=run, rows=rows), open(sys.argv[sys.argv.index('--out') + 1], 'w'), indent=1)


if __name__ == '__main__':
    main()
