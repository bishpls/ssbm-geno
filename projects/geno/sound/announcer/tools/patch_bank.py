"""Build out/nr_name.ssm: the US announcer bank with "GENO!" appended and entry 17 (sound 510017, sample 1493)
repointed at it. Reads the disc copy, never writes it. Verifies the result and writes out/patch_report.json."""
import sys, os, struct, hashlib, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, soundfile as sf
import dspenc, ssm

HERE = os.path.expanduser(os.environ.get('ANNOUNCER_WORK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'announcer')))   # the work folder (game audio)
SRC_BANK = os.path.expanduser(os.environ.get('ANNOUNCER_SRC_BANK', os.path.join(
    os.environ.get('MELEE_DISC', '~/games/melee/disc'), 'files', 'audio', 'us', 'nr_name.ssm')))   # the retail bank
WAV = os.path.join(HERE, 'geno_CD_full.wav')
OUT = os.path.join(HERE, 'out')
SLOT = 17
BUDGET = 348160                          # DOL offsets_arr_803BC4E4[51][0]: ARAM the game books for nr_name

def sha1(b): return hashlib.sha1(b).hexdigest()

def main():
    orig = open(SRC_BANK, 'rb').read()
    bank = ssm.parse(SRC_BANK)
    hlen, dlen, count, base = struct.unpack('>4I', orig[:16])
    data_off = bank['data_off']
    pcm, sr = sf.read(WAV, dtype='int16')
    assert sr == 12000 and pcm.ndim == 1
    adpcm, info = dspenc.encode(pcm)
    n = len(pcm)
    # ---- layout
    B = -(-dlen // 32) * 32                              # append after the existing pad, 32-byte aligned
    padded = adpcm + b'\0' * (-(len(adpcm)) % 32)
    new_dlen = B + len(padded)
    assert new_dlen % 32 == 0 and new_dlen <= BUDGET, new_dlen
    start = 2 * B + 2
    end = 2 * B + dspenc.nibbles_for(n) - 1
    # ---- entry 17 (0x48 bytes at 0x10 + 17*0x48): nch, rate, then the channel block
    e = 0x10 + SLOT * 0x48
    nch, rate = struct.unpack('>2I', orig[e:e + 8])
    assert nch == 1 and rate == 12000
    chan = struct.pack('>HHIII', 0, 0, start, end, start)                       # loop_flag, format, sa, ea, ca
    chan += struct.pack('>16h', *[v for c in info['coefs'] for v in c])          # coefs
    chan += struct.pack('>HHhhHhhH', 0, info['ps'], 0, 0, 0, 0, 0, 0)          # gain, ps, yn1, yn2, lps, lyn1, lyn2, pad
    assert len(chan) == 0x40
    out = bytearray(orig[:data_off + dlen])
    struct.pack_into('>I', out, 4, new_dlen)
    out[e + 8:e + 0x48] = chan
    out += b'\0' * (B - dlen) + padded
    assert len(out) == data_off + new_dlen
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'nr_name.ssm'), 'wb').write(out)
    open(os.path.join(OUT, 'geno_CD_full.dsp'), 'wb').write(dspenc.dsp_header(info) + adpcm)

    # ---- verify: parse back with the independent reader, decode every entry
    pb = ssm.parse(os.path.join(OUT, 'nr_name.ssm'))
    ob = bank
    rep = dict(source=SRC_BANK, source_sha1=sha1(orig), patched_sha1=sha1(bytes(out)), source_size=len(orig),
               patched_size=len(out), data_off=hex(data_off), data_len=[dlen, new_dlen], budget=BUDGET,
               budget_left=BUDGET - new_dlen, append_at_data_byte=B, append_at_file_offset=hex(data_off + B),
               adpcm_bytes=len(adpcm), padded_bytes=len(padded), samples=n, frames=info['frames'],
               entry17=dict(file_offset=hex(e), start_nibble=start, loop_start_nibble=start, end_nibble=end,
                            ps=hex(info['ps']), coefs=info['coefs']))
    assert pb['count'] == ob['count'] == 52 and pb['start'] == ob['start'] == 1476
    y = ssm.decode_channel(pb, pb['sounds'][SLOT]['chans'][0])
    ref = dspenc.decode(adpcm, info['coefs'], n)
    rep['entry17_decode_samples'] = len(y)
    rep['entry17_decode_equals_encoder_decode'] = bool(len(y) == n and np.array_equal(y, ref))
    rep['entry17_snr_vs_wav_db'] = round(dspenc.snr_db(pcm, y), 2)
    same_entries, same_pcm = [], []
    for i in range(52):
        if i == SLOT: continue
        a = orig[0x10 + i * 0x48:0x10 + (i + 1) * 0x48]; b = bytes(out[0x10 + i * 0x48:0x10 + (i + 1) * 0x48])
        same_entries.append(a == b)
        same_pcm.append(np.array_equal(ssm.decode_channel(ob, ob['sounds'][i]['chans'][0]),
                                       ssm.decode_channel(pb, pb['sounds'][i]['chans'][0])))
    rep['other_entries_byte_identical'] = f'{sum(same_entries)}/51'
    rep['other_entries_decode_identical'] = f'{sum(same_pcm)}/51'
    rep['old_data_region_identical'] = orig[data_off:data_off + dlen] == bytes(out[data_off:data_off + dlen])
    # byte-level diff summary over the original's length, plus the appended tail
    diff = [k for k in range(len(orig)) if orig[k] != out[k]]
    ranges = []
    for k in diff:
        if ranges and k == ranges[-1][1] + 1: ranges[-1][1] = k
        else: ranges.append([k, k])
    rep['diff_ranges_within_original'] = [f'0x{a:X}-0x{b:X} ({b - a + 1} B)' for a, b in ranges]
    rep['appended'] = f'0x{len(orig):X}-0x{len(out) - 1:X} ({len(out) - len(orig)} B)'
    json.dump(rep, open(os.path.join(OUT, 'patch_report.json'), 'w'), indent=1, default=str)
    for k, v in rep.items():
        print(f'{k}: {v}')

if __name__ == '__main__':
    main()
