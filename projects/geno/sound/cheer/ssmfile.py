"""HAL sound banks: .ssm (DSP-ADPCM samples) and smash2.sem (the sound scripts), read and written.

.ssm (big-endian): u32 entry_table_len, u32 data_len, u32 count, u32 base_sample_id; then per entry u32 nch, u32 rate and per
channel 0x40 bytes (u16 loop_flag, u16 format, u32 loop_start, u32 end, u32 current (nibble addresses from the data start),
s16 coefs[16], u16 gain, u16 ps, s16 yn1, s16 yn2, u16 loop_ps, s16 loop_yn1, s16 loop_yn2, u16 pad); the data at
align32(entry_table_len + 0x10). Entry i is global sample base + i.
smash2.sem: u32 0, u32 0, u32 bank_count, u32 first_script[bank_count], u32 total, u32 offset[total], u32 0, the scripts.
A script is 32-bit commands, opcode in the top byte (01 play a global sample id, 0E end, ...). Sound id = bank * 10000 + k
plays script first_script[bank] + k.
"""
import os, struct, sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'machinima',
                                'melee', 'audio'))
import dspadpcm  # noqa: E402


def align(n, a=32):
    return -(-n // a) * a


def parse_ssm(b):
    hlen, dlen, count, base = struct.unpack('>4I', b[:16])
    data_off = align(hlen + 0x10)
    assert data_off + dlen == len(b), 'not an .ssm'
    off, entries = 0x10, []
    for i in range(count):
        nch, rate = struct.unpack('>2I', b[off:off + 8]); off += 8
        ch = []
        for _ in range(nch):
            loop, fmt, ls, end, cur = struct.unpack('>2H3I', b[off:off + 16])
            coefs = struct.unpack('>16h', b[off + 16:off + 48])
            gain, ps, yn1, yn2, lps, lyn1, lyn2, pad = struct.unpack('>HHhhHhhH', b[off + 48:off + 64])
            ch.append(dict(loop=loop, fmt=fmt, lstart=ls, end=end, cur=cur, coefs=coefs, ps=ps, yn1=yn1, yn2=yn2,
                           raw=b[off:off + 64]))
            off += 64
        entries.append(dict(index=i, sample_id=base + i, nch=nch, rate=rate, ch=ch))
    return dict(hlen=hlen, dlen=dlen, count=count, base=base, data_off=data_off, entries=entries, data=b[data_off:])


def entry_samples(ch):
    """Number of PCM samples in a channel whose start is a frame boundary (current = 2 mod 16)."""
    assert ch['cur'] % 16 == 2
    nib = ch['end'] - ch['cur'] + 3                   # nibbles incl. the frame header pair, from the start frame
    full, rem = divmod(nib, 16)
    return full * 14 + (rem - 2 if rem else 0)


def decode_entry(bank, e, c=0):
    ch = bank['entries'][e]['ch'][c]
    n = entry_samples(ch)
    start = (ch['cur'] - 2) // 2
    coefs = [ch['coefs'][2 * k:2 * k + 2] for k in range(8)]
    return dspadpcm.decode(bank['data'][start:start + 8 * -(-n // 14)], coefs, n, ch['yn1'], ch['yn2'])


def entry_record(rate, start_byte, info):
    """One mono entry, as every retail and Geno entry is laid out (loop off, loop_start = start, gain and history 0)."""
    start = 2 * start_byte + 2
    end = 2 * start_byte + info['num_nibbles'] - 1
    rec = struct.pack('>II', 1, rate)
    rec += struct.pack('>HHIII', 0, 0, start, end, start)
    rec += struct.pack('>16h', *[v for pair in info['coefs'] for v in pair])
    rec += struct.pack('>HHhhHhhH', 0, info['ps'], 0, 0, 0, 0, 0, 0)
    return rec


def write_ssm(base, records, data):
    """records: the 0x48-byte entry records; data: the ADPCM data (padded here to a multiple of 32)."""
    hlen = sum(len(r) for r in records)
    dlen = align(len(data))
    f = struct.pack('>4I', hlen, dlen, len(records), base) + b''.join(records)
    f += b'\0' * (align(hlen + 0x10) - len(f))
    return f + data + b'\0' * (dlen - len(data))


def parse_sem(b):
    w = lambda o: struct.unpack('>I', b[o:o + 4])[0]
    assert w(0) == 0 and w(4) == 0
    nb = w(8); first = [w(12 + 4 * i) for i in range(nb)]; o = 12 + 4 * nb
    ns = w(o); o += 4; ptr = [w(o + 4 * i) for i in range(ns)]; o += 4 * ns
    assert w(o) == 0
    ends = ptr[1:] + [len(b)]
    return dict(nb=nb, first=first, ns=ns, ptr=ptr, data_start=o + 4, scripts=[b[p:e] for p, e in zip(ptr, ends)])


def write_sem(first, scripts):
    nb, ns = len(first), len(scripts)
    head = 4 * (3 + nb + 1 + ns + 1)
    ptrs, p = [], head
    for sc in scripts:
        ptrs.append(p); p += len(sc)
    return (struct.pack(f'>3I{nb}II{ns}II', 0, 0, nb, *first, ns, *ptrs, 0) + b''.join(scripts))


def script_cmds(sc):
    return [(w >> 24, w & 0xFFFFFF) for w in struct.unpack(f'>{len(sc) // 4}I', sc)]


def resolve(sem, sound_id):
    """The script a sound id plays, or None where HSD_AudioSFXStartParam rejects it (axdriver.c)."""
    bank, k = divmod(sound_id, 10000)
    if bank >= sem['nb']:
        return None
    i = sem['first'][bank] + k
    if i >= sem['ns'] or (bank < sem['nb'] - 1 and sem['first'][bank + 1] <= i):
        return None
    return i
