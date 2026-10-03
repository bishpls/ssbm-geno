"""Build bank 55: out/geno.ssm (same file for audio/ and audio/us/) and patched smash2.sem copies (US and JP).
Reads the disc files, never writes them. Verifies everything and writes out/bank_report.json."""
import os, sys, json, struct, hashlib, glob, subprocess, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'announcer', 'tools'))   # dspenc, ssm
import numpy as np, soundfile as sf
import dspenc, ssm

HERE = os.path.expanduser(os.environ.get('SFXBANK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'sfxbank')))   # the bank's work folder (game audio: outside the repo)
DISC = os.path.join(os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc')), 'files', 'audio')
OUT = os.path.join(HERE, 'out')
BANK = 55
SFX_BASE = BANK * 10000                  # sound IDs 550000 + k
BASE_SAMPLE = 1551                       # first free global sample ID in BOTH language sets (US max 1533, JP max 1550)
RATE = 32000
BUDGET = 586208                          # data_len cap: the current 4th-largest fighter bank (Kirby), see NOTES
BOOKED = 327680                          # LBAX_GENO_BYTES in the decomp (lbaudio_ax_geno_bytes.patch): must be >= data_len
VGM = os.environ.get('VGMSTREAM', 'vgmstream-cli')   # vgmstream's CLI, the independent decoder the checks use

def sha1(b): return hashlib.sha1(b).hexdigest()
def align(n, a): return -(-n // a) * a

def build_ssm(pcms):
    enc = [dspenc.encode(p) for p in pcms]
    count = len(pcms)
    hlen = count * 0x48
    data_off = align(0x10 + hlen, 0x20)
    data = bytearray(); table = bytearray()
    for (adpcm, info), p in zip(enc, pcms):
        B = len(data)                                  # frames are packed back to back, as in every retail bank
        assert B % 8 == 0
        start = 2 * B + 2; end = 2 * B + dspenc.nibbles_for(len(p)) - 1
        table += struct.pack('>II', 1, RATE)
        table += struct.pack('>HHIII', 0, 0, start, end, start)
        table += struct.pack('>16h', *[v for c in info['coefs'] for v in c])
        table += struct.pack('>HHhhHhhH', 0, info['ps'], 0, 0, 0, 0, 0, 0)
        data += adpcm
    dlen = align(len(data), 0x20)
    data += b'\0' * (dlen - len(data))
    f = struct.pack('>4I', hlen, dlen, count, BASE_SAMPLE) + table
    f += b'\0' * (data_off - len(f)) + data
    return bytes(f), enc

def parse_sem(b):
    w = lambda o: struct.unpack('>I', b[o:o + 4])[0]
    o = 0; c0 = w(o); assert c0 == 0; o += 4; c1 = w(o); assert c1 == 0; o += 4
    nb = w(o); o += 4; first = [w(o + 4 * i) for i in range(nb)]; o += 4 * nb
    ns = w(o); o += 4; ptr = [w(o + 4 * i) for i in range(ns)]; o += 4 * ns
    c4 = w(o); assert c4 == 0; o += 4
    ends = ptr[1:] + [len(b)]
    return dict(nb=nb, first=first, ns=ns, ptr=ptr, data_start=o, scripts=[b[p:e] for p, e in zip(ptr, ends)])

def script(sample, vol, prio, aux):
    # the shape of most retail fighter scripts: play, FD, aux send, priority, volume, end
    return struct.pack('>6I', 0x01000000 | sample, 0xFD000000 | sample, 0x10000000 | aux, 0x04000000 | prio,
                       0x06000000 | vol, 0x0E000000)

def patch_sem(orig, new_scripts):
    s = parse_sem(orig)
    assert s['nb'] == 55 and s['ns'] == 4035 and s['data_start'] == 0x3FFC
    M = len(new_scripts)
    delta = 4 * (1 + M)
    out = bytearray(struct.pack('>III', 0, 0, s['nb'] + 1))
    out += struct.pack(f'>{s["nb"] + 1}I', *(s['first'] + [s['ns']]))
    out += struct.pack('>I', s['ns'] + M)
    old_ptrs = [p + delta for p in s['ptr']]
    new_ptrs = []; p = len(orig) + delta
    for sc in new_scripts:
        new_ptrs.append(p); p += len(sc)
    out += struct.pack(f'>{s["ns"] + M}I', *(old_ptrs + new_ptrs))
    out += struct.pack('>I', 0)
    assert len(out) == s['data_start'] + delta
    out += orig[s['data_start']:]
    for sc in new_scripts: out += sc
    return bytes(out)

def vgm_decode(path, subsong):
    with tempfile.TemporaryDirectory() as d:
        o = os.path.join(d, 'x.wav')
        subprocess.run([VGM, '-i', '-s', str(subsong), '-o', o, path], check=True, capture_output=True)
        x, sr = sf.read(o, dtype='int16')
    return x, sr

def main():
    meta = json.load(open(os.path.join(HERE, 'build', 'sounds.json')))
    pcms = []
    for m in meta:
        x, sr = sf.read(os.path.join(HERE, 'build', m['file']), dtype='int16'); assert sr == RATE; pcms.append(x)
    geno, enc = build_ssm(pcms)
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'geno.ssm'), 'wb').write(geno)
    scripts = [script(BASE_SAMPLE + m['k'], m['vol'], m['prio'], m['aux']) for m in meta]
    rep = dict(geno_ssm=dict(size=len(geno), sha1=sha1(geno)))
    sems = {}
    RETAIL = {'us': '169b94078cba0f1da66c6a3947a080b971085ceb', 'jp': '12e17f7c54ee0ff005aeed8b7993663c6bdc27bd'}
    BACKUP = os.path.join(os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work')), 'orig', 'audio')
    for tag, rel in (('us', 'us/smash2.sem'), ('jp', 'smash2.sem')):
        # the retail sem: the disc copy if it is still retail, else install.sh's backup (the bank may be installed)
        src = next(p for p in (os.path.join(DISC, rel), os.path.join(BACKUP, rel))
                   if os.path.exists(p) and sha1(open(p, 'rb').read()) == RETAIL[tag])
        orig = open(src, 'rb').read()
        new = patch_sem(orig, scripts)
        fn = os.path.join(OUT, f'smash2_{tag}.sem'); open(fn, 'wb').write(new)
        sems[tag] = (orig, new)
        rep[f'smash2_{tag}'] = dict(source=src, source_size=len(orig), source_sha1=sha1(orig), size=len(new), sha1=sha1(new))

    # ---------------------------------------------------------------- verify geno.ssm
    b = ssm.parse(os.path.join(OUT, 'geno.ssm'))            # asserts data_off + data_len == file size
    assert b['count'] == len(meta) and b['start'] == BASE_SAMPLE
    assert b['dlen'] <= BUDGET and b['dlen'] <= BOOKED and b['dlen'] % 32 == 0
    rows = []
    for m, s, (adpcm, info), p in zip(meta, b['sounds'], enc, pcms):
        c = s['chans'][0]
        ours = ssm.decode_channel(b, c)
        same_enc = np.array_equal(ours, dspenc.decode(adpcm, info['coefs'], len(p)))
        v, vsr = vgm_decode(os.path.join(OUT, 'geno.ssm'), s['index'] + 1)
        n = min(len(v), len(ours))
        rows.append(dict(k=m['k'], name=m['name'], sample_id=BASE_SAMPLE + m['k'], sound_id=SFX_BASE + m['k'],
                         samples=len(p), adpcm_bytes=len(adpcm), rate=s['rate'], start_nibble=c['cur'], end_nibble=c['end'],
                         ps=hex(c['ps']), decode_equals_encoder=bool(same_enc and len(ours) == len(p)),
                         snr_db=round(dspenc.snr_db(p, ours), 2), vgmstream_rate=vsr,
                         vgmstream_bit_exact=bool(np.array_equal(v[:n], ours[:n])), vgmstream_len_diff=len(v) - len(ours)))
    rep['geno_ssm'].update(count=b['count'], base_sample=b['start'], data_off=hex(b['data_off']), data_len=b['dlen'],
                           budget=BUDGET, budget_left=BUDGET - b['dlen'], booked=BOOKED, samples=rows)
    # ---------------------------------------------------------------- verify the sems
    for tag, (orig, new) in sems.items():
        so, sn = parse_sem(orig), parse_sem(new)
        ok_old = all(a == c for a, c in zip(so['scripts'], sn['scripts'][:so['ns']]))
        ok_first = sn['first'][:55] == so['first'] and sn['first'][55] == so['ns']
        resolved = []
        for k in range(len(meta)):
            sid = SFX_BASE + k; bank, mem = divmod(sid, 10000)
            idx = sn['first'][bank] + mem                     # HSD_AudioSFXStartParam
            assert bank < sn['nb'] and idx < sn['ns']
            sc = sn['scripts'][idx]
            resolved.append(int.from_bytes(sc[1:4], 'big'))
        rep[f'smash2_{tag}'].update(banks=[so['nb'], sn['nb']], scripts=[so['ns'], sn['ns']], first_script_55=sn['first'][55],
                                    old_scripts_identical=ok_old, old_first_script_identical=ok_first,
                                    sound_ids_resolve_to_samples=resolved == [BASE_SAMPLE + k for k in range(len(meta))])
    json.dump(rep, open(os.path.join(OUT, 'bank_report.json'), 'w'), indent=1)
    g = rep['geno_ssm']
    print(f"geno.ssm: {g['size']} B, sha1 {g['sha1']}, {g['count']} samples from ID {g['base_sample']}, data_off {g['data_off']}, "
          f"data_len {g['data_len']} (budget {BUDGET}, left {g['budget_left']})")
    print('  decode == encoder:', sum(r['decode_equals_encoder'] for r in rows), '/', len(rows),
          '  vgmstream bit-exact:', sum(r['vgmstream_bit_exact'] for r in rows), '/', len(rows),
          '  vgmstream rate', sorted(set(r['vgmstream_rate'] for r in rows)),
          '  SNR dB min/median %.1f/%.1f' % (min(r['snr_db'] for r in rows), np.median([r['snr_db'] for r in rows])))
    for tag in sems:
        r = rep[f'smash2_{tag}']
        print(f"smash2_{tag}.sem: {r['source_size']} -> {r['size']} B, sha1 {r['sha1']}; banks {r['banks']}, scripts {r['scripts']}, "
              f"first_script[55]={r['first_script_55']}, old scripts identical={r['old_scripts_identical']}, "
              f"old first_script identical={r['old_first_script_identical']}, 550000+k -> 1551+k: {r['sound_ids_resolve_to_samples']}")

if __name__ == '__main__':
    main()
