"""When each gun move's sound lands against its visible shot, in the game's own audio (Michael: some gun sounds "come out
delayed"). From a director/gunfx_lab.py GUNFX_SET=sound run, whose segments each open with a reference: the director
plays GENO_PULSE (550000, a 4-frame pulse whose attack is its first sample) on the segment's slate frame.
    .venv/bin/python projects/geno/sound/soundsync.py RUN [--bank GENO.SSM] [--out OUT.json]
For every gun sound a move's script cues:
  - its cue frame and the move's first active frame (the visible shot: the hitbox and the bursts spawn on it; both from
    rig/moves.py as built, Script.sound and Script.hitbox calls);
  - where the sample starts in the dump: the bank's decoded sample cross-correlated with the dump near its cue;
  - its key transient: the sample's own shot (KEY: the Hand Gun's first shot and the Star Gun's first burst at their
    start; the Hand Cannon's boom, its third trigger);
  - all in the frames of the images: the segment's reference pulse is played by the director with its magenta slate, and
    a director cue shows one image after its logic frame (fxsync's SYNC_CAL: the slate set on frame r is image r + 1),
    so the pulse is heard with image r + 1 and a sound heard at t is at image frame r + 1 + (t - t_ref) * 60. The
    dump's own audio latency (the same for every sound) cancels. Checked: the pulse's time after the opening click
    against the magenta image's index after the opening slate's (CAL, printed), and the jab 3's and down tilt's own
    pulses (a script sound on the frame of its hitbox) landing on their first active frame.
Reported: the cue's lead (first active - cue), the sample's start (should be its cue), the key transient, and the
offset = key transient - first active frame (0 = the shot's sound on the shot's frame). Down air is left out.
"""
import json, math, os, sys

import numpy as np
from scipy.signal import resample_poly, correlate

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'fx'))
sys.path.insert(0, os.path.join(HERE, 'cheer'))
import soundaudit as A  # noqa: E402

FPS = 60.0
REF = 550000
# the key transient's time in each sample (seconds from its start), and what it is
KEY = {550000: (0.0, 'the pulse'), 550001: (0.0, 'the first shot'), 550056: (0.0, 'the first shot'),
       550004: (0.0, 'the first burst'), 550058: (0.0, 'the first burst'),
       550002: (0.200, 'the boom (the third trigger, the one that rings; triggers at 0, 0.098, 0.200 s)'),
       550057: (0.200, 'the boom (the third trigger; triggers at 0, 0.098, 0.200 s)'),
       550060: (0.0, 'the boom'), 550059: (0.0, 'the cock (a lead-in: not the shot)'),
       550061: (0.002, 'the shot (its attack is its peak)')}
SHOT_FRAMES = {'ThrowB': 33}                              # moves with no hitbox on the shot: the blast's own frame (the BOOM)
LEAD_INS = {550059}                                       # sounds cued ahead of the shot on purpose


def samples(bank_path, ids, rate):
    import ssmfile as S
    b = S.parse_ssm(open(bank_path, 'rb').read())
    out = {}
    for sid in ids:
        k = sid - 550000
        x = S.decode_entry(b, k).astype(np.float64) / 32768
        sr = b['entries'][k]['rate']
        up, dn = int(round(rate)), int(sr)
        g = math.gcd(up, dn)
        out[sid] = resample_poly(x, up // g, dn // g)
    return out


def find(mono, tmpl, i0, i1):
    """the dump sample where tmpl starts, searched in [i0, i1): the normalised cross-correlation's peak"""
    i0, i1 = max(0, i0), min(len(mono), i1 + len(tmpl))
    seg = mono[i0:i1]
    c = correlate(seg, tmpl, mode='valid')
    e = np.sqrt(np.convolve(seg ** 2, np.ones(len(tmpl)), mode='valid')) + 1e-12
    r = c / e / (np.linalg.norm(tmpl) + 1e-12)
    k = int(np.argmax(r))
    return i0 + k, float(r[k])


def main():
    import fxsync, soundfile as sf
    run = sys.argv[1]
    disc = os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc'))
    bank = sys.argv[sys.argv.index('--bank') + 1] if '--bank' in sys.argv else os.path.join(disc, 'files/audio/us/geno.ssm')
    r = fxsync.load(run)
    clk, sr, y = fxsync.click(run)
    mono = y.mean(axis=1)
    ms = [l.split() for l in open(os.path.join(run, 'osreport.log'), errors='replace') if l.startswith('MS ')]
    ms = [(int(l[1]), int(l[2]), int(l[3])) for l in ms]
    sfx = [l.split() for l in open(os.path.join(run, 'osreport.log'), errors='replace') if l.startswith('SFX ')]
    sfx = [(int(l[1]), int(l[3])) for l in sfx]
    ev = A.script_events(hits=True)
    ids = sorted({REF} | {sid for e in ev.values() for _, sid in e['sounds'] if sid in KEY})
    rate = sr                                             # the dump's samples per second (nominal: a segment is short)
    tm = samples(bank, ids, rate)
    rows = []
    # the calibration: each reference pulse's time after the opening click against its slate image's after the opening's
    cal = []
    for seg, off in r.offsets:
        refs = [f for f, sid in sfx if sid == REF and seg['sync'] - 2 <= f <= seg['sync'] + 2]
        if refs:
            ia = r.audio_at(refs[0], clk, sr)
            t, _ = find(mono, tm[REF], ia - int(0.1 * sr), ia + int(0.1 * sr))
            slate_i = off + seg['sync'] - fxsync.SYNC_CAL
            cal.append((t - clk) / rate * FPS - (slate_i - r.opening[0]))
    print(f'calibration: the reference pulse is heard {np.mean(cal):+.2f} frames (sd {np.std(cal):.2f}, n {len(cal)}) from '
          f'its magenta image, both counted from the opening slate (its click and its first image)')
    for seg, off in r.offsets:
        label = seg['label']
        if label not in A.SEGMENTS:
            continue
        refs = [f for f, sid in sfx if sid == REF and seg['sync'] - 2 <= f <= seg['sync'] + 2]
        if not refs:
            print(label, 'no reference cue'); continue
        rf = refs[0]
        ia = r.audio_at(rf, clk, sr)
        t_ref, q_ref = find(mono, tm[REF], ia - int(0.1 * sr), ia + int(0.1 * sr))
        mv, mot = A.SEGMENTS[label][-1]
        starts = [f for f, p, m in ms if p == 0 and m == mot and seg['start'] - 5 <= f < seg['start'] + seg['frames']]
        if not starts:
            print(label, 'no action'); continue
        a0 = starts[0]
        e = ev[mv]
        for cue, sid in e['sounds']:
            if sid not in KEY:
                continue
            shot = SHOT_FRAMES.get(mv) or min((h for h in e['hits'] if h >= cue), default=None)
            c_logic = a0 + cue - 1
            want = t_ref + (c_logic - rf - 1) / FPS * rate
            t0, q = find(mono, tm[sid], int(want - 0.07 * rate), int(want + 0.07 * rate))
            start_f = rf + 1 + (t0 - t_ref) / rate * FPS - a0 + 1   # in the move's frames (image r + 1 = the pulse)
            key_s, key_what = KEY[sid]
            key_f = start_f + key_s * FPS
            row = dict(segment=label, move=mv, sound=sid, lead_in=sid in LEAD_INS, cue=cue, first_active=shot,
                       lead=None if shot is None else shot - cue,
                       sample_start=round(start_f, 2), key=round(key_f, 2), key_what=key_what,
                       offset=None if shot is None else round(key_f - shot, 2), match=round(q, 2), ref_match=round(q_ref, 2),
                       ref_frame=rf, action_start=a0, t_ref=int(t_ref), rate=rate)
            rows.append(row)
            print(f"{label:12s} {mv:16s} {sid} cue {cue:2d}  first active {shot}  sample starts {start_f:5.1f}  "
                  f"key ({key_what.split(' (')[0]}) {key_f:5.1f}  offset {row['offset']:+.1f} frames  "
                  f"(match {q:.2f}, reference {q_ref:.2f})")
    if '--out' in sys.argv:
        json.dump(dict(run=run, bank=bank, calibration=dict(mean=float(np.mean(cal)), sd=float(np.std(cal)), n=len(cal)),
                       rows=rows), open(sys.argv[sys.argv.index('--out') + 1], 'w'), indent=1)


if __name__ == '__main__':
    main()
