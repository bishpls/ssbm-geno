"""Super Mario RPG (SNES) music sequence reader, after Lazy Shell's SPCTrack.cs (read-only; the ROM stays local).

Track table: 24-bit pointers at ROM 0x042748 (index 0 = "current", 1..73 = songs).
Track header: delay, decay, echo, (sample, volume)* 0xFF, u16 length, then spcData loaded at ARAM $2000:
  percussion entries (5 bytes each) until 0xFF, then 8 u16 channel pointers (ARAM, 0 = unused), then channel scripts.
Notes: opcode < 0xC4: pitch = op % 14 (C..B, 12 = rest, 13 = tie), beat = op // 14; ticks from ROM table 0x042304
for beats 0..12, or the next byte for op >= 0xB6.
"""
import struct
ROM_PATH = __import__('os').path.expanduser(__import__('os').environ.get('SMRPG_ROM', '~/games/smrpg/smrpg_usa.sfc'))   # your own dump
ROM = open(ROM_PATH, 'rb').read()
LEN = [1]*0xB6 + [2]*(0xC4-0xB6) + [1,1,2,1, 2,1,1,1, 1,2,2,2,  # C4..CF
       1,2,2,2,2,1,1,1, 1,2,2,2,2,2,2,2,  # D0
       2,2,2,2,3,3,1,2, 3,3,1,1,2,2,1,1,  # E0
       3,4,2,1,3,1,2,1, 1,1,1,1,4,1,1,1]  # F0
assert len(LEN) == 256
NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B','r','~']
BEAT_TICKS = list(ROM[0x042304:0x042304+13])

def u16(b, o): return b[o] | (b[o+1] << 8)
def u24(b, o): return b[o] | (b[o+1] << 8) | (b[o+2] << 16)

def track(idx):
    off = u24(ROM, idx*3 + 0x042748) - 0xC00000
    delay, decay, echo = ROM[off], ROM[off+1], ROM[off+2]; off += 3
    samples = []
    while ROM[off] != 0xFF and len(samples) < 20:
        samples.append((ROM[off], ROM[off+1])); off += 2
    off += 1
    length = u16(ROM, off); off += 2
    data = ROM[off:off+length]
    o = 0; perc = []
    while data[o] != 0xFF:
        perc.append(tuple(data[o:o+5])); o += 5
    o += 1
    ptrs = [u16(data, o + 2*i) for i in range(8)]
    chans = []
    for p in ptrs:
        if p == 0: chans.append(None); continue
        q = p - 0x2000; cmds = []
        while True:
            op = data[q]; n = LEN[op]
            cmds.append(tuple(data[q:q+n])); q += n
            if op in (0xD0, 0xCE) or q >= len(data): break
        chans.append(cmds)
    return dict(idx=idx, rom=off, delay=delay, decay=decay, echo=echo, samples=samples, perc=perc, ptrs=ptrs,
                chans=chans, data=data)

def ticks(cmd):
    op = cmd[0]
    if op < 0xB6: return BEAT_TICKS[op // 14]
    if op < 0xC4: return cmd[1]
    return 0

def fmt(cmd):
    op = cmd[0]
    if op < 0xC4:
        return '%s:%d' % (NAMES[op % 14], ticks(cmd))
    return '%02X' % op + ('(' + ','.join('%d' % x for x in cmd[1:]) + ')' if len(cmd) > 1 else '')

if __name__ == '__main__':
    import sys
    print('beat ticks', BEAT_TICKS)
    sys.path.insert(0, '.')

# ---------------------------------------------------------------- interpreter
def flatten(cmds, loops_after_d7=1):
    """Expand repeats (D4 n .. [D6] .. D5, with the octave reset per pass), return the linear command list.
    D7 marks the infinite-loop start; D0 ends a pass; the loop body is emitted `loops_after_d7` extra times."""
    out = []
    def run(i, depth):
        # returns index after processing until D5 (if depth>0) or D0
        while i < len(cmds):
            c = cmds[i]; op = c[0]
            if op == 0xD4:
                n = c[1]; start = i + 1; end = None
                out.append(('rep_begin',))
                for p in range(n):
                    j = start
                    if p: out.append(('rep_again',))
                    while True:
                        cj = cmds[j]
                        if cj[0] == 0xD6 and p == n - 1:
                            # last pass: skip to after the matching D5
                            k = j; lvl = 0
                            while True:
                                k += 1
                                if cmds[k][0] == 0xD4: lvl += 1
                                elif cmds[k][0] == 0xD5:
                                    if lvl == 0: break
                                    lvl -= 1
                            end = k + 1; break
                        if cj[0] == 0xD5:
                            end = j + 1; break
                        if cj[0] == 0xD4:
                            j = run_one_repeat(j); continue
                        if cj[0] != 0xD6: out.append(cj)
                        j += 1
                out.append(('rep_end',))
                i = end; continue
            if op == 0xD5: return i + 1
            if op == 0xD0: out.append(c); return i + 1
            out.append(c); i += 1
        return i
    def run_one_repeat(j):
        # nested repeat: emit by recursion on a sub-list
        lvl = 0; k = j
        while True:
            k += 1
            if cmds[k][0] == 0xD4: lvl += 1
            elif cmds[k][0] == 0xD5:
                if lvl == 0: break
                lvl -= 1
        sub = flatten(cmds[j:k+1] + [(0xD0,)])
        out.extend(x for x in sub if x[0] != 0xD0)
        return k + 1
    run(0, 0)
    return out

def events(t, extra_loops=1, tempo0=None):
    """Linear note events per channel: dict(ch, t_tick, dur_tick, midi_seq, sample, vol, pan, perc, tie-merged).
    midi_seq = 12*(octave+1) + pitch + transpose (semitones, EC/ED in 1/4-semitone units) + fine/16 (CF).
    Tempo: D1 sets the timer-0 period; a tick lasts D1/8000 s. Returns (events, tempo_map[(tick, D1)], loop_tick)."""
    evs = []; tempo = []; loop_tick = None; chan_end = {}
    for ch, cmds in enumerate(t['chans']):
        if cmds is None: continue
        body = flatten(cmds)
        # D7 splits intro / loop
        if any(c[0] == 0xD7 for c in body):
            k = [c[0] for c in body].index(0xD7)
            lin = body[:k] + body[k+1:] + sum([body[k+1:] for _ in range(extra_loops)], [])
        else:
            k = None; lin = body
        tick = 0; octv = 6; stack = []; sample = None; vol = 100; pan = 128; perc = False; tr = 0; fine = 0
        last = None
        for idx, c in enumerate(lin):
            if k is not None and idx == k and ch == 0: pass
            op = c[0]
            # repeats: the octave is restored when a repeat loops back, and kept after its last pass (driver + Lazy Shell)
            if op == 'rep_begin': stack.append(octv); continue
            if op == 'rep_again': octv = stack[-1]; continue
            if op == 'rep_end': stack.pop(); continue
            if k is not None and idx == k: loop_tick = tick if loop_tick is None else loop_tick
            if op < 0xC4:
                p = op % 14; d = ticks(c)
                if p == 13:  # tie
                    if last is not None: last['dur'] += d
                elif p == 12:
                    last = None
                else:
                    e = dict(ch=ch, t=tick, dur=d, pitch=p, oct=octv, seq=12 * (octv + 1) + p, tr=tr, fine=fine,
                             sample=sample, vol=vol, pan=pan, perc=perc)
                    evs.append(e); last = e
                tick += d; continue
            if op == 0xC4: octv += 1
            elif op == 0xC5: octv -= 1
            elif op == 0xC6: octv = c[1]
            elif op == 0xDE: sample = c[1]
            elif op == 0xE2: vol = c[1]
            elif op == 0xE7: pan = c[1]
            elif op == 0xEE: perc = True
            elif op == 0xEF: perc = False
            elif op == 0xEC: tr = (c[1] - 256 if c[1] > 127 else c[1]) / 4.0
            elif op == 0xED: tr += (c[1] - 256 if c[1] > 127 else c[1]) / 4.0
            elif op == 0xCF: fine = (c[1] - 256 if c[1] > 127 else c[1]) / 16.0
            elif op == 0xD1: tempo.append((tick, c[1]))
            elif op == 0xD0: break
        chan_end[ch] = tick
    tempo = sorted(set(tempo))
    return evs, tempo, loop_tick, chan_end

def tick_to_sec(tick, tempo):
    """Integrate D1/8000 s per tick over the tempo map."""
    s = 0.0; prev_t, prev_v = 0, tempo[0][1]
    for tt, v in tempo[1:]:
        if tt >= tick: break
        s += (tt - prev_t) * prev_v / 8000.0; prev_t, prev_v = tt, v
    return s + (tick - prev_t) * prev_v / 8000.0

def brr_decode(sid):
    """Decode ROM BRR sample `sid` -> (pcm float array, loop_start_sample)."""
    off = u24(ROM, sid * 3 + 0x042333) - 0xC00000
    n = u16(ROM, off); data = ROM[off + 2: off + 2 + n]
    loop_bytes = u16(ROM, sid * 2 + 0x04248F)
    out = []; p1 = p2 = 0
    for b in range(0, len(data) - 8, 9):
        hdr = data[b]; shift = hdr >> 4; filt = (hdr >> 2) & 3
        for k in range(16):
            byte = data[b + 1 + k // 2]
            nib = (byte >> 4) if k % 2 == 0 else (byte & 0xF)
            if nib >= 8: nib -= 16
            s = (nib << shift) >> 1 if shift <= 12 else (-2048 if nib < 0 else 0)
            if filt == 1: s += p1 + ((-p1) >> 4)
            elif filt == 2: s += (p1 << 1) + ((-((p1 << 1) + p1)) >> 5) - p2 + (p2 >> 4)
            elif filt == 3: s += (p1 << 1) + ((-(p1 + (p1 << 2) + (p1 << 3))) >> 6) - p2 + (((p2 << 1) + p2) >> 4)
            s = max(-32768, min(32767, s)); s = ((s << 1) & 0xFFFF); s = s - 65536 if s >= 32768 else s; s >>= 1
            p2, p1 = p1, s; out.append(s)
        if hdr & 1: break
    return out, loop_bytes // 9 * 16

# sounding-pitch offset per sample for track 9 (measured: driver pitch register + BRR loop period + pyin; see NOTES)
K_SOUND = {30: 12, 44: -12, 20: -24, 78: -12, 17: -24}
SAMPLE_NAMES = {17: 'orchestra hit', 20: 'synth bass', 30: 'flute', 44: 'trumpet', 78: 'xylophone', 43: 'drum roll',
                51: 'bass drum', 42: 'fat snare', 33: 'tambourine', 52: 'pedal hi-hat', 53: 'closed hi-hat'}

def sounding(e, perc_map=None):
    if e['perc']:
        return None
    return int(round(e['seq'] + e['tr'] + e['fine'] + K_SOUND[e['sample']]))
